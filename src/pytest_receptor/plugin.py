"""Consumer-profile output for pytest.

The receptor renders one pytest run for one kind of consumer. ``human`` is a
true passthrough: the plugin registers nothing and pytest behaves exactly as it
does without it installed. ``llm`` and ``ci`` share a single renderer and differ
only in their defaults; see ``Profile``.

Design notes that are easy to undo by accident:

* The standard terminal reporter is silenced through its **public** options and
  a wrapper around ``pytest_report_teststatus``. It is never unregistered and
  never subclassed, so plugins that look it up still find it (PR-ARCH-003).
* Rendering happens in ``pytest_sessionfinish``, not ``pytest_terminal_summary``,
  because pytest does not call the latter for ``INTERNAL_ERROR``.
* The outcome comes from ``pytest.ExitCode``, never from the absence of failure
  reports (PR-CRIT-001/002/003).
"""

from __future__ import annotations

import re
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path

import pytest

__all__ = ["Profile", "PROFILES"]

# Anything that is not printable text is stripped before it reaches the
# consumer. Test output is untrusted input (PR-SEC-001).
_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Non-semantic values that would otherwise split one root cause into many.
_HEX_ADDR = re.compile(r"0x[0-9a-fA-F]+")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?")

_MAX_MESSAGE = 1500
_SLOW_TEST_SECONDS = 0.5
_SLOW_TEST_COUNT = 3
_SHOWN_TESTS = 3


@dataclass(frozen=True)
class Profile:
    """Defaults for one consumer. Not a separate renderer (PR-OPS-010)."""

    name: str
    #: How many root causes get full detail. ``None`` means all of them.
    detailed_groups: int | None
    #: Whether to point at the on-disk report. False where it will not survive.
    show_report_path: bool


PROFILES = {
    # An agent can read the file, so only the first causes need expanding.
    "llm": Profile("llm", detailed_groups=3, show_report_path=True),
    # A CI runner is destroyed at job end and the log gets one shot, so the
    # on-disk report is unreachable and nothing may be held back.
    "ci": Profile("ci", detailed_groups=None, show_report_path=False),
}


def pytest_addoption(parser):
    group = parser.getgroup("receptor")
    group.addoption(
        "--receptor",
        action="store",
        default="human",
        choices=["human", "llm", "ci"],
        help="Who consumes this output: human (default, unchanged pytest), "
        "llm (compact, for coding agents), ci (compact, nothing held back).",
    )
    group.addoption(
        "--receptor-full",
        action="store_true",
        help="Expand every failure group instead of the first few.",
    )
    group.addoption(
        "--receptor-stats",
        action="store_true",
        help="Append what this run cost compared with pytest as you normally "
        "run it, so you can judge on your own suite whether this is worth it.",
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    receptor = config.getoption("receptor")
    if receptor == "human":
        # PR-OPS-009: register nothing at all, so output is byte-identical to
        # pytest without the plugin.
        return
    plugin = ReceptorPlugin(config, PROFILES[receptor])
    if plugin.stats:
        # Measuring: leave every option exactly as the user set it and let the
        # reporter render into a temp file. The baseline has to be what *they*
        # would otherwise have read, not a configuration we picked for them.
        plugin.start_baseline_capture()
    else:
        _silence_standard_reporter(config)
    # "receptor" is taken by this module's own pytest11 entry point.
    config.pluginmanager.register(plugin, "receptor-renderer")


def _silence_standard_reporter(config):
    """Quieten pytest's reporter using only documented options.

    ``verbose = -2`` is what ``-qq`` sets, and it is the switch that suppresses
    the trailing ``N passed in Xs`` line, which would otherwise duplicate our
    own verdict. ``no_summary`` is what stops the failure sections from being
    printed.

    Deliberately **not** set: ``tbstyle``. Setting it to ``"no"`` looks like the
    obvious way to suppress tracebacks, but it impoverishes ``longrepr`` at
    construction time -- the same failure renders to 145 characters under
    ``short`` and 21 under ``no`` -- which destroys the frame information this
    plugin exists to summarize. Suppression belongs to the reporter, not to the
    evidence.
    """
    config.option.verbose = -2
    config.option.no_header = True
    config.option.no_summary = True


@dataclass
class Occurrence:
    """One failing test within a group. Never collapsed away (PR-FID-001)."""

    nodeid: str
    phase: str
    location: str
    sections: dict = field(default_factory=dict)


@dataclass
class Group:
    """One root cause."""

    exc_type: str
    phase: str
    message: str
    location: str
    frames: list = field(default_factory=list)
    occurrences: list = field(default_factory=list)


class ReceptorPlugin:
    def __init__(self, config, profile):
        self.config = config
        self.profile = profile
        self.full = config.getoption("receptor_full")
        self.stats = config.getoption("receptor_stats")
        self._baseline = None
        self._terminal = None
        self._shown = ""
        self._start = time.monotonic()  # PR-OPS-006
        self._failures = []
        self._durations = {}
        self._outcomes = {}
        self._collected = 0
        self._warnings = 0
        self._skipped = set()
        self._xfailed = set()
        self._xpassed = []

    # ------------------------------------------------------------------ hooks

    @pytest.hookimpl(wrapper=True)
    def pytest_report_teststatus(self, report, config):
        """Keep pytest's categorization, drop the progress characters.

        Left alone while measuring a baseline: those characters are part of
        what pytest would have printed, and they are going to a file anyway.
        """
        outcome = yield
        if self.stats:
            return outcome
        category, _letter, _word = outcome
        return (category, "", "")

    def pytest_collection_modifyitems(self, items):
        self._collected = len(items)

    def pytest_warning_recorded(self, warning_message, when, nodeid, location):
        self._warnings += 1

    def pytest_collectreport(self, report):
        if report.failed:
            self._failures.append(report)

    def pytest_runtest_logreport(self, report):
        nodeid = report.nodeid
        self._durations[nodeid] = self._durations.get(nodeid, 0.0) + report.duration

        if report.failed:
            self._failures.append(report)
            # A logical test that fails in any phase is a failure, even if its
            # call phase passed (PR-FID-008).
            self._outcomes[nodeid] = "failed"
        elif report.when == "call":
            if hasattr(report, "wasxfail"):
                if report.passed:
                    self._xpassed.append((nodeid, report.wasxfail or ""))
                    self._outcomes[nodeid] = "xpassed"
                else:
                    self._xfailed.add(nodeid)
                    self._outcomes[nodeid] = "xfailed"
            elif report.skipped:
                self._skipped.add(nodeid)
                self._outcomes[nodeid] = "skipped"
            else:
                self._outcomes.setdefault(nodeid, "passed")
        elif report.skipped and report.when == "setup":
            self._skipped.add(nodeid)
            self._outcomes.setdefault(nodeid, "skipped")

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session, exitstatus):
        tw = self._terminal or self.config.get_terminal_writer()
        try:
            groups = self._build_groups()
            summary = self._summary_line(session, exitstatus, groups)
            full_report = self._render(summary, groups, expand_all=True)
            path = self._write_full_report(full_report)
            if self.full or self.profile.detailed_groups is None:
                shown = full_report
            else:
                shown = self._render(summary, groups, expand_all=False, path=path)
            tw.line("")
            tw.write(shown)
            self._shown = shown
        except Exception as exc:  # pragma: no cover - exercised via tests
            self._emergency(tw, exitstatus, exc)

    # ------------------------------------------------------------- collection

    def _build_groups(self):
        groups = {}
        for report in self._failures:
            exc_type, message, location, phase = self._describe(report)
            # Fingerprint the complete message, before any truncation, so two
            # failures differing only inside a cut region cannot merge
            # (PR-FID-004). Grouping is call-site aware on purpose: equal
            # messages from unrelated places are different causes.
            key = (exc_type, phase, _normalize(message), location)
            group = groups.get(key)
            if group is None:
                group = Group(
                    exc_type=exc_type,
                    phase=phase,
                    message=_truncate(message),
                    location=location,
                    frames=self._frames(report),
                )
                groups[key] = group
            group.occurrences.append(
                Occurrence(
                    nodeid=report.nodeid,
                    phase=phase,
                    location=location,
                    sections=self._sections(report),
                )
            )
        # Largest blast radius first: that is the one worth fixing.
        return sorted(groups.values(), key=lambda g: len(g.occurrences), reverse=True)

    def _describe(self, report):
        phase = getattr(report, "when", None) or "collection"
        longrepr = report.longrepr
        message = ""
        location = ""

        crash = getattr(longrepr, "reprcrash", None)
        if crash is not None:
            message = crash.message or ""
            location = f"{self._relative(crash.path)}:{crash.lineno}"
        elif longrepr is not None:
            message = str(longrepr)
            location = self._relative(getattr(report, "fspath", "") or "")

        message = _sanitize(message)
        return _exception_type(message), message, location, phase

    def _frames(self, report):
        """Local frames only, labelled honestly.

        pytest's ``reprfileloc.message`` is the failure message, not a function
        name, so it is not presented as one (PR-FID-007). External frames are
        dropped here and remain in the on-disk report.
        """
        reprtraceback = getattr(report.longrepr, "reprtraceback", None)
        if reprtraceback is None:
            return []
        frames = []
        for entry in getattr(reprtraceback, "reprentries", []):
            loc = getattr(entry, "reprfileloc", None)
            if loc is None:
                continue
            path = str(loc.path)
            if "site-packages" in path or "lib/python" in path:
                continue
            relative = self._relative(path)
            if relative.startswith(".."):
                continue
            frames.append(f"{relative}:{loc.lineno}")
        return frames

    def _sections(self, report):
        sections = {}
        for name, content in getattr(report, "sections", []):
            lowered = name.lower()
            for marker in ("stdout", "stderr", "log"):
                if marker in lowered:
                    text = _sanitize(content).strip()
                    if text:
                        sections[marker] = _truncate(text)
                    break
        return sections

    def _relative(self, path):
        root = getattr(self.config, "rootpath", None)
        if not path or root is None:
            return str(path)
        try:
            return str(Path(path).relative_to(root))
        except ValueError:
            return str(path)

    # ---------------------------------------------------------------- render

    def _summary_line(self, session, exitstatus, groups):
        counts = {}
        for outcome in self._outcomes.values():
            counts[outcome] = counts.get(outcome, 0) + 1
        executed = len(self._outcomes)
        duration = time.monotonic() - self._start

        verdict, note = _verdict(exitstatus)
        # pytest raises Interrupted for collection errors, so exit status alone
        # cannot tell them apart from a real interrupt.
        if verdict == "INTERRUPTED" and any(g.phase == "collect" for g in groups):
            verdict = "COLLECTION_ERROR"
        parts = [f"{verdict} exit={int(exitstatus)}"]

        detail = []
        for label in ("failed", "passed", "skipped", "xfailed", "xpassed"):
            if counts.get(label):
                detail.append(f"{counts[label]} {label}")
        if detail:
            parts.append(", ".join(detail))
        elif verdict == "PASS":
            parts.append("0 tests")

        # PR-CRIT-003: an incomplete run must never read as a clean pass.
        incomplete = self._stop_reason(session, exitstatus, executed)
        if incomplete:
            parts.append(incomplete)

        parts.append(f"{duration:.2f}s")
        if self._warnings:
            parts.append(f"{self._warnings} warnings")
        if len(groups) > 1:
            parts.append(f"{len(groups)} root causes")
        if note:
            parts.append(note)
        return " | ".join(parts)

    def _stop_reason(self, session, exitstatus, executed):
        if exitstatus == pytest.ExitCode.INTERRUPTED:
            return f"incomplete: {executed} of {self._collected} executed"
        shouldstop = getattr(session, "shouldstop", False)
        shouldfail = getattr(session, "shouldfail", False)
        if shouldstop or shouldfail:
            reason = "maxfail" if shouldfail else "stopped"
            return f"incomplete ({reason}): {executed} of {self._collected} executed"
        if self._collected and executed < self._collected:
            return f"incomplete: {executed} of {self._collected} executed"
        return ""

    def _render(self, summary, groups, expand_all, path=None):
        lines = [summary]
        limit = None if expand_all else self.profile.detailed_groups

        for index, group in enumerate(groups, start=1):
            if limit is not None and index > limit:
                lines.append("")
                lines.append(
                    f"[{index}] {group.exc_type} | {_tests(group)} | "
                    f"{group.phase} | {group.location}"
                )
                continue
            lines.append("")
            lines.extend(self._render_group(index, group, expand_all))

        if self._xpassed:
            lines.append("")
            lines.append("unexpected passes:")
            for nodeid, reason in self._xpassed:
                suffix = f" - {_sanitize(reason)}" if reason else ""
                lines.append(f"  {nodeid}{suffix}")

        slow = self._slow_tests()
        if slow:
            lines.append("")
            lines.append("slowest:")
            for nodeid, duration in slow:
                lines.append(f"  {nodeid} ({duration:.2f}s)")

        held_back = (
            limit is not None and len(groups) > limit and self.profile.show_report_path
        )
        if held_back:
            lines.append("")
            if path is not None:
                lines.append(f"full report: {path}")
            else:
                lines.append("full report: rerun with --receptor-full")

        return "\n".join(lines) + "\n"

    def _render_group(self, index, group, expand_all):
        lines = [
            f"[{index}] {group.exc_type} | {_tests(group)} | {group.phase}",
            f"    {group.location}",
        ]
        for line in group.message.splitlines():
            lines.append(f"    {line}")
        if len(group.frames) > 1:
            lines.append("    frames: " + " -> ".join(group.frames))

        for occurrence in self._section_sources(group, expand_all):
            for name, content in occurrence.sections.items():
                lines.append(f"    captured {name} ({occurrence.nodeid}):")
                for line in content.splitlines():
                    lines.append(f"      {line}")

        if len(group.occurrences) > 1:
            lines.append("    tests:")
            shown = (
                group.occurrences if expand_all else group.occurrences[:_SHOWN_TESTS]
            )
            for occurrence in shown:
                lines.append(f"      {occurrence.nodeid}")
            remaining = len(group.occurrences) - len(shown)
            if remaining:
                lines.append(f"      +{remaining} more")
        lines.append(f"    rerun: {_rerun(group)}")
        return lines

    def _section_sources(self, group, expand_all):
        """Occurrences whose captured output is worth printing.

        Captured output usually differs per test even when the exception does
        not, so it must not be collapsed to the first occurrence (PR-FID-001).
        In compact mode only the first few are printed; every one of them is in
        the full report.
        """
        with_sections = [item for item in group.occurrences if item.sections]
        if expand_all:
            return with_sections
        return with_sections[:_SHOWN_TESTS]

    def _slow_tests(self):
        slow = [
            (nodeid, duration)
            for nodeid, duration in self._durations.items()
            if duration >= _SLOW_TEST_SECONDS
        ]
        slow.sort(key=lambda item: item[1], reverse=True)
        return slow[:_SLOW_TEST_COUNT]

    def _write_full_report(self, text):
        cache = getattr(self.config, "cache", None)
        if cache is None:
            return None
        try:
            path = cache.mkdir("receptor") / "last-run.txt"
            path.write_text(text, encoding="utf-8")
        except Exception:
            # Losing the report must never cost the run.
            return None
        try:
            return path.relative_to(Path.cwd())
        except ValueError:
            return path

    def pytest_unconfigure(self, config):
        """Emit statistics only once pytest has finished writing the baseline.

        The reporter's ``pytest_sessionfinish`` is a hook *wrapper*, so its
        summary is written after every plain implementation, including ours.
        Reading the baseline from ``pytest_sessionfinish`` would capture only
        the progress line.
        """
        if not self.stats:
            return
        try:
            line = self._stats_line(self._shown)
        except Exception:
            return
        if line and self._terminal is not None:
            self._terminal.write(line)

    # ----------------------------------------------------------------- stats

    def start_baseline_capture(self):
        """Point the standard reporter at a temp file instead of the terminal.

        This is how ``--receptor-stats`` gets a *measured* comparison rather
        than an estimate: pytest genuinely renders its quiet output, in this
        same run, and we count the bytes it produced. The reporter is otherwise
        untouched, and our own report goes to the real terminal.

        Any failure here degrades to no statistics at all. It must never affect
        the run.
        """
        try:
            from _pytest.config import create_terminal_writer

            reporter = self.config.pluginmanager.getplugin("terminalreporter")
            if reporter is None:
                return
            handle = tempfile.NamedTemporaryFile(
                "w+",
                encoding="utf-8",
                prefix="pytest-receptor-baseline-",
                suffix=".log",
                delete=False,
            )
            self._baseline = handle
            self._terminal = create_terminal_writer(self.config, sys.stdout)
            reporter._tw = create_terminal_writer(self.config, handle)
        except Exception:
            self._baseline = None
            self._terminal = None

    def _read_baseline(self):
        if self._baseline is None:
            return None
        try:
            self._baseline.flush()
            text = Path(self._baseline.name).read_text(encoding="utf-8")
        except Exception:
            return None
        finally:
            try:
                self._baseline.close()
                Path(self._baseline.name).unlink()
            except Exception:
                pass
            self._baseline = None
        return text

    def _stats_line(self, shown):
        """Compare our output against the baseline pytest actually rendered.

        The baseline is the user's own pytest configuration, untouched. A
        published benchmark should pick a strict opponent, but this flag answers
        a personal question -- "against how I actually run pytest, what did this
        save me?" -- and only their real settings answer it. The docs explain why
        this number and the published table differ.
        """
        baseline = self._read_baseline()
        if not baseline:
            return ""
        try:
            mine, unit = _count_tokens(shown)
            theirs, _ = _count_tokens(baseline)
        except Exception:
            return ""
        if not theirs:
            return ""
        # One convention for both numbers: they describe the change in output
        # size, and they carry the same sign. Reporting an absolute count next
        # to a signed *saving* reads as a contradiction -- "cost 12 (-46.2%)"
        # looks like the cost went down.
        change = mine - theirs
        percent = change / theirs * 100
        direction = "fewer" if change < 0 else "more"
        return (
            f"\nreceptor stats: {mine} tokens vs {theirs} for pytest as you "
            f"configured it | {abs(change)} {direction} ({percent:+.1f}%) | "
            f"{unit}\n"
        )

    # ------------------------------------------------------------- fallback

    def _emergency(self, tw, exitstatus, exc):
        """Never lose a run because the renderer broke (PR-OPS-008)."""
        tw.line("")
        tw.line(
            f"RECEPTOR_ERROR | pytest exit={int(exitstatus)} | "
            f"{type(exc).__name__}: {exc} | raw pytest evidence follows"
        )
        tw.line("".join(traceback.format_exception(exc)).rstrip())
        for report in self._failures:
            tw.line("")
            tw.line(str(getattr(report, "nodeid", "?")))
            tw.line(str(getattr(report, "longrepr", "")))


def _count_tokens(text):
    """Token count, with a clearly labelled fallback when tiktoken is absent."""
    try:
        import tiktoken
    except ImportError:
        return len(text) // 4, "approx (4 chars/token)"
    return len(tiktoken.get_encoding("cl100k_base").encode(text)), "cl100k_base"


def _verdict(exitstatus):
    code = int(exitstatus)
    if code == int(pytest.ExitCode.OK):
        return "PASS", ""
    if code == int(pytest.ExitCode.TESTS_FAILED):
        return "FAIL", ""
    if code == int(pytest.ExitCode.INTERRUPTED):
        return "INTERRUPTED", ""
    if code == int(pytest.ExitCode.INTERNAL_ERROR):
        return "ERROR", "internal error"
    if code == int(pytest.ExitCode.USAGE_ERROR):
        return "USAGE_ERROR", ""
    if code == int(pytest.ExitCode.NO_TESTS_COLLECTED):
        return "NO_TESTS", ""
    if code == int(pytest.ExitCode.MAX_WARNINGS_ERROR):
        return "FAIL", "max warnings exceeded"
    return "UNKNOWN", f"unrecognized exit status {code}"


_EXC_NAME = re.compile(r"^([A-Za-z_][\w.]*(?:Error|Exception|Warning|Interrupt))\b")


def _exception_type(message):
    """Best-effort exception name from pytest's crash message.

    Structured exception data is a post-0.6 concern (PR-ARCH-001). Until then
    this reads the leading token rather than scanning for ``E   `` prefixes,
    which also works for collection failures where the message is a plain
    string.
    """
    head = message.split("\n", 1)[0].strip()
    match = _EXC_NAME.match(head)
    if match:
        return match.group(1)
    if ":" in head:
        candidate = head.split(":", 1)[0].strip()
        if candidate and all(part.isidentifier() for part in candidate.split(".")):
            return candidate
    return "Failure"


def _tests(group):
    count = len(group.occurrences)
    return f"{count} test" if count == 1 else f"{count} tests"


def _rerun(group):
    """A command that actually selects the group (PR-UX-003)."""
    nodeids = [occurrence.nodeid for occurrence in group.occurrences]
    if len(nodeids) == 1:
        return f"pytest {nodeids[0]} -q"
    files = {nodeid.split("::", 1)[0] for nodeid in nodeids}
    return "pytest " + " ".join(sorted(files)) + " -q"


def _sanitize(text):
    """Test output is untrusted input, so strip anything non-textual."""
    if not text:
        return ""
    return _CONTROL.sub("", _ANSI.sub("", str(text)))


def _normalize(message):
    message = _HEX_ADDR.sub("[ADDR]", message)
    return _TIMESTAMP.sub("[TIME]", message)


def _truncate(message, limit=_MAX_MESSAGE):
    if len(message) <= limit:
        return message
    head = message[: limit - 400]
    tail = message[-400:]
    omitted = len(message) - len(head) - len(tail)
    return f"{head}\n... [{omitted} characters omitted; see full report] ...\n{tail}"
