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

import os
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

# A conservative net for the obvious shapes of leaked credential. Anchored on a
# keyword and a minimum length so ordinary test data is not mangled. This is not
# a security boundary -- it cannot catch a secret that does not look like one --
# and it is documented as such rather than sold as a guarantee (PR-SEC-002).
_SECRETS = [
    (
        re.compile(
            r"(?i)\b(api[_-]?key|token|password|passwd|secret|credential|auth)"
            r"(\s*[=:]\s*)['\"]?([A-Za-z0-9_\-./+]{12,})['\"]?"
        ),
        r"\1\2[REDACTED]",
    ),
    (
        re.compile(
            r"(?i)\b(Authorization:\s*Basic\s+|Bearer\s+)[A-Za-z0-9_\-./+=]{10,}"
        ),
        r"\1[REDACTED]",
    ),
]

# Non-semantic values that would otherwise split one root cause into many.
_HEX_ADDR = re.compile(r"0x[0-9a-fA-F]+")
# Sizes, shapes, counters, byte totals and percentages. Endorsed as safe to
# normalize by the MolSysMT pilot after inspecting sixty real warning groups:
# `Size mismatch for 'atom_index': (1441,) vs (605,)` and the same message with
# (1289,) are one warning, and keying on the numbers made them two. Names are
# deliberately *not* normalized -- an atom name or attribute carries meaning the
# pilot asked us to preserve.
_SHAPE = re.compile(r"\(\s*\d+(?:\s*,\s*\d*)*\s*\)")
_NUMBER = re.compile(r"(?<![\w.])\d+(?![\w.])")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?")

_MAX_MESSAGE = 1500
_SLOW_TEST_SECONDS = 0.5
_SLOW_TEST_COUNT = 3
_SHOWN_TESTS = 3
_MAX_LOCAL_FRAMES = 8
# Above this many distinct root causes, expanding all of them stops being
# cheaper than pointing at the file.
_MANY_CAUSES = 10

# A long run must not look like a hung one. pytest streams progress characters;
# suppressing them without replacement means a consumer -- an agent with a tool
# timeout, a human, a CI job with an idle limit -- cannot tell a working suite
# from a stalled one, and learns nothing at all if the process is killed.
#
# Reported by decile, not by clock, so the cost is bounded by nothing at all:
# nine lines whether the suite takes five minutes or three hours. The elapsed
# time on each line also exposes pace -- if 10% took thirty seconds and the next
# 10% took five minutes, that is worth seeing.
#
# A minimum elapsed time still applies, so ordinary runs stay silent.
_PROGRESS_AFTER = 20.0
_PROGRESS_STEP = 10  # percent

# A warning line exists to let you recognize the warning and decide whether it
# is new. Scientific messages run to several hundred characters, which made a
# single group cost 68 tokens and the section unbounded. This bounds it without
# hiding any group: every distinct warning is still listed.
_WARNING_MESSAGE = 110

# O_NOFOLLOW is POSIX-only; on Windows the symlink check above is what we get.
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


@dataclass(frozen=True)
class Profile:
    """Defaults for one consumer. Not a separate renderer (PR-OPS-010)."""

    name: str
    #: How many root causes get full detail. ``None`` means all of them.
    detailed_groups: int | None
    #: Whether to point at the on-disk report. False where it will not survive.
    show_report_path: bool


PROFILES = {
    # Show every root cause. Grouping has already collapsed the volume -- a
    # thousand failures become a handful of causes -- so withholding on top of
    # it saves almost nothing and risks costing double. Measured on distinct
    # causes: at five, holding back saves 40 tokens and costs 200 more if the
    # consumer then has to read the file. Only a pathological spread makes the
    # trade worth taking, which is what the threshold is for.
    "llm": Profile("llm", detailed_groups=_MANY_CAUSES, show_report_path=True),
    # A CI runner is destroyed at job end and the log gets one shot, so the
    # on-disk report is unreachable and nothing may be held back.
    "ci": Profile("ci", detailed_groups=None, show_report_path=False),
}


def pytest_addoption(parser):
    parser.addini(
        "receptor_normalizers",
        type="linelist",
        default=[],
        help="Extra `regex -> replacement` rules applied before grouping, so "
        "project-specific dynamic values do not split one root cause into many. "
        "Example: `shape \\(\\d+, \\d+\\) -> shape (N, M)`",
    )
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
    # Deliberately *not* no_summary: that option gates the whole
    # pytest_terminal_summary hook, and third-party plugins write their reports
    # there. Setting it swallowed pytest-cov's coverage table entirely. Emptying
    # reportchars stops pytest's own short summary without silencing anyone else.
    reporter = config.pluginmanager.getplugin("terminalreporter")
    if reporter is not None:
        reporter.reportchars = ""
    _silence_xdist_startup(config)


def _silence_xdist_startup(config):
    """Stop `bringing up nodes...` landing in front of the verdict.

    This is infrastructure chatter, the distributed equivalent of the progress
    characters already suppressed -- not a report. The distinction matters:
    pytest-cov's table is a report and is deliberately preserved, and silencing
    that by accident is a mistake already made once here.

    So this neuters exactly one method rather than unregistering the plugin,
    because the same object also carries `pytest_testnodedown`, which announces
    a worker dying. That is a completeness signal and must survive.
    """
    dist = config.pluginmanager.getplugin("terminaldistreporter")
    if dist is None:
        return
    try:
        dist.ensure_show_status = lambda: None
    except Exception:
        pass


@dataclass
class Occurrence:
    """One failing test within a group. Never collapsed away (PR-FID-001)."""

    nodeid: str
    phase: str
    location: str
    sections: dict = field(default_factory=dict)
    #: How many times this test ran before its final outcome. Above one means a
    #: rerun plugin retried it.
    attempts: int = 1


@dataclass
class Group:
    """One root cause."""

    exc_type: str
    phase: str
    message: str
    location: str
    cause: str = ""
    frames: list = field(default_factory=list)
    #: Keyed by node ID so a retried test stays one occurrence.
    by_nodeid: dict = field(default_factory=dict)
    #: Distinct normalized messages seen at this call site. A parametrized test
    #: failing on twenty inputs is one bug with twenty messages, not twenty bugs.
    variants: dict = field(default_factory=dict)
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
        # pytest's states are per phase, not per test: a test that passes and
        # then fails its teardown counts as both `passed` and `error`. A single
        # value per node ID cannot represent that, and folding it into `failed`
        # disagrees with pytest about what happened.
        self._outcomes = {}
        self._errors = set()
        # Where the reader ran pytest. Every path we print has to resolve from
        # here, or they cannot act on it.
        self._invocation = Path(
            getattr(config, "invocation_params", None).dir
            if getattr(config, "invocation_params", None) is not None
            else Path.cwd()
        )
        self._collected = 0
        self._finished = 0
        self._next_decile = _PROGRESS_STEP
        self._last_progress = self._start
        # Under xdist the plugin is instantiated in every worker as well as the
        # controller. Each worker sees the whole collected list but only its own
        # share of finished tests, so every one of them announced 10% at its own
        # pace -- twelve interleaved streams, milestones repeating and appearing
        # to go backwards. Only the controller has the global view, so only the
        # controller speaks.
        self._is_worker = hasattr(config, "workerinput")
        self._warnings = 0
        self._warning_groups = {}
        self._skipped = {}
        self._xfailed = {}
        self._xpassed = []
        self._project_normalizers = _compile_normalizers(config)

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

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(self, node, ids):
        """The controller's only route to the collected total.

        `pytest_collection_modifyitems` fires in the workers, never here, so
        without this the controller has no denominator and falls back to a bare
        count. Declared optional so the plugin still loads when xdist is absent.
        """
        self._collected = max(self._collected, len(ids))

    def _emit_progress(self):
        """A sign of life on stdout's quieter sibling.

        Deliberately *not* a hang detector: it fires when a test finishes, so a
        genuinely stuck test produces no further lines. That is still useful --
        the last line printed says how far the run got -- but claiming more
        would repeat the mistake of the heartbeat this replaces, which advertised
        periodic output it could not deliver.

        It goes to stderr so the report on stdout stays exactly as parseable as
        it was.
        """
        if self._is_worker:
            return
        elapsed = time.monotonic() - self._start
        if elapsed < _PROGRESS_AFTER:
            return

        if self._collected:
            percent = self._finished * 100 // self._collected
            if percent < self._next_decile or percent >= 100:
                return
            # Skip past any deciles crossed while we were still under the
            # minimum elapsed time, so the first line is not stale.
            self._next_decile = (percent // _PROGRESS_STEP + 1) * _PROGRESS_STEP
            marker = f"{percent}% {self._finished}/{self._collected}"
        else:
            # Nothing was collected up front -- fall back to a clock, since some
            # liveness beats none.
            if elapsed - (self._last_progress - self._start) < _PROGRESS_AFTER:
                return
            self._last_progress = time.monotonic()
            marker = str(self._finished)

        try:
            sys.stderr.write(f"receptor: {marker} {elapsed:.0f}s\n")
            sys.stderr.flush()
        except Exception:
            pass

    def pytest_collection_modifyitems(self, items):
        self._collected = len(items)

    def pytest_warning_recorded(self, warning_message, when, nodeid, location):
        """Group warnings as they arrive.

        pytest hands over the real ``warnings.WarningMessage``, so the category
        and origin are structured data and there is no need to parse them back
        out of a formatted string.
        """
        self._warnings += 1
        category = getattr(warning_message, "category", None)
        name = getattr(category, "__name__", None) or "Warning"
        text = _sanitize(str(getattr(warning_message, "message", "")))
        filename = getattr(warning_message, "filename", "")
        lineno = getattr(warning_message, "lineno", 0)
        origin = f"{self._display_path(filename)}:{lineno}" if filename else ""

        key = (name, _normalize_warning(self._normalize(text)))
        group = self._warning_groups.get(key)
        if group is None:
            group = {
                "category": name,
                "message": text,
                "origin": origin,
                "count": 0,
                "variants": set(),
            }
            self._warning_groups[key] = group
        group["count"] += 1
        # Normalizing numbers merges `(1441,) vs (605,)` with `(1441,) vs
        # (1289,)`. That is right -- one warning -- but the reader should know
        # the numbers differed rather than have them silently replaced by
        # whichever arrived first.
        group["variants"].add(text)

    def pytest_collectreport(self, report):
        if report.failed:
            self._failures.append(report)

    def pytest_runtest_logreport(self, report):
        nodeid = report.nodeid
        self._durations[nodeid] = self._durations.get(nodeid, 0.0) + report.duration
        if report.when == "teardown":
            self._finished += 1
            self._emit_progress()

        if report.failed:
            self._failures.append(report)
            # pytest_report_teststatus in _pytest/runner.py: a failure outside
            # the call phase is an *error*, not a failed test.
            if report.when in ("setup", "teardown"):
                self._errors.add(nodeid)
            else:
                self._outcomes[nodeid] = "failed"
        elif report.when == "call":
            if hasattr(report, "wasxfail"):
                if report.passed:
                    self._xpassed.append((nodeid, report.wasxfail or ""))
                    self._outcomes[nodeid] = "xpassed"
                else:
                    self._xfailed[nodeid] = _sanitize(report.wasxfail or "")
                    self._outcomes[nodeid] = "xfailed"
            elif report.skipped:
                self._skipped[nodeid] = _skip_reason(report)
                self._outcomes[nodeid] = "skipped"
            else:
                self._outcomes.setdefault(nodeid, "passed")
        elif report.skipped and report.when == "setup":
            self._skipped[nodeid] = _skip_reason(report)
            self._outcomes.setdefault(nodeid, "skipped")

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session, exitstatus):
        # Every longrepr has been built by now, so switching the traceback style
        # off here suppresses the reporter's failure sections without having
        # impoverished the evidence while it was being collected. Doing it at
        # configure time is what destroyed the frame data.
        if not self.stats:
            self.config.option.tbstyle = "no"
        tw = self._terminal or self.config.get_terminal_writer()
        try:
            groups = self._build_groups()
            summary = self._summary_line(session, exitstatus, groups)
            full_report = self._render(summary, groups, limit=None, list_all=True)
            path = self._write_full_report(full_report)
            if self.full:
                shown = full_report
            else:
                # Two independent decisions. Every root cause is rendered in
                # full unless there is a pathological spread of them, and that
                # summarizing only happens when the report exists to hold what
                # is left out. Occurrence lists are always truncated: that is
                # where the volume is, and the rerun command already selects
                # what was cut, so nothing becomes unreachable.
                limit = self.profile.detailed_groups if path is not None else None
                shown = self._render(
                    summary, groups, limit=limit, list_all=False, path=path
                )
            # No leading blank: the verdict is the first thing on stdout, so a
            # consumer reading line one gets the answer.
            tw.write(shown)
            self._shown = shown
        except Exception as exc:  # pragma: no cover - exercised via tests
            self._emergency(tw, exitstatus, exc)

    # ------------------------------------------------------------- collection

    def _build_groups(self):
        groups = {}
        for report in self._failures:
            exc_type, message, location, phase = self._describe(report)
            cause = self._cause(report)
            # One exception type raised from one line in one phase is one bug.
            # The message is deliberately *not* part of the key: a parametrized
            # test failing on twenty inputs produces twenty messages, and keying
            # on them fragments a single cause into twenty groups. Differing
            # messages are kept as variants instead. The cause chain is part of
            # the key, because the same outer error wrapping two different
            # underlying failures really is two bugs.
            key = (exc_type, phase, location, cause)
            group = groups.get(key)
            if group is None:
                group = Group(
                    exc_type=exc_type,
                    phase=phase,
                    message=_truncate(message),
                    location=location,
                    cause=cause,
                    frames=self._frames(report),
                )
                groups[key] = group
            # Normalized so non-semantic values do not inflate the variant
            # count, and computed on the complete message, before truncation
            # (PR-FID-004).
            group.variants.setdefault(self._normalize(message), message)
            # One logical test, however many times it was retried. Appending
            # per report made a test rerun three times read as three tests,
            # which is simply false, and false counts are the one thing this
            # project exists to prevent.
            existing = group.by_nodeid.get(report.nodeid)
            if existing is None:
                group.by_nodeid[report.nodeid] = Occurrence(
                    nodeid=report.nodeid,
                    phase=phase,
                    location=location,
                    sections=self._sections(report),
                )
            else:
                existing.attempts += 1
                existing.sections = self._sections(report) or existing.sections
        # Under xdist, reports arrive in whatever order the workers finish, so
        # both levels need an explicit total order or the same failure renders
        # differently between runs.
        for group in groups.values():
            group.occurrences = sorted(
                group.by_nodeid.values(), key=lambda o: _natural(o.nodeid)
            )
        # Largest blast radius first -- that is the one worth fixing -- then a
        # stable tiebreak.
        return sorted(
            groups.values(),
            key=lambda g: (-len(g.occurrences), g.location, g.exc_type, g.message),
        )

    def _cause(self, report):
        """The exception that actually started it, for `raise X from Y`.

        Scientific code wraps low-level errors constantly, and the outer message
        is frequently the least informative part of the failure.
        """
        chain = getattr(report.longrepr, "chain", None)
        if not chain or len(chain) < 2:
            return ""
        crash = chain[0][1]
        if crash is None or not crash.message:
            return ""
        return _sanitize(crash.message).splitlines()[0]

    def _describe(self, report):
        phase = getattr(report, "when", None) or "collection"
        longrepr = report.longrepr
        message = ""
        location = ""

        declared = ""
        crash = getattr(longrepr, "reprcrash", None)
        located = getattr(longrepr, "reprlocation_lines", None)
        if crash is not None:
            message = crash.message or ""
            location = f"{self._display_path(crash.path)}:{crash.lineno}"
        elif located:
            # Doctests carry a ReprFailDoctest, which has no reprcrash but does
            # name its own location and failure type. Falling through to
            # str(longrepr) lost both: the line number, and the fact that this
            # was a DocTestFailure rather than an unnamed "Failure".
            where, lines = located[-1]
            location = f"{self._display_path(where.path)}:{where.lineno}"
            message = "\n".join(str(line) for line in lines).strip()
            declared = str(where.message or "")
        elif longrepr is not None:
            message = str(longrepr)
            location = self._display_path(getattr(report, "fspath", "") or "")

        message = _sanitize(message)
        exc_type = _exception_type(message)
        if exc_type == "Failure" and declared:
            exc_type = declared.split(":", 1)[0].strip() or exc_type
        return exc_type, message, location, phase

    def _frames(self, report):
        """Local frames only, labelled honestly.

        pytest's ``reprfileloc.message`` is the failure message, not a function
        name, so it is not presented as one (PR-FID-007). External frames are
        dropped here and remain in the on-disk report.
        """
        reprtraceback = getattr(report.longrepr, "reprtraceback", None)
        if reprtraceback is None:
            return []

        raw = []
        for entry in getattr(reprtraceback, "reprentries", []):
            loc = getattr(entry, "reprfileloc", None)
            if loc is None:
                continue
            path = str(loc.path)
            external = "site-packages" in path or "lib/python" in path
            raw.append((self._display_path(path), loc.lineno, external))

        return _prune_frames(raw)

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

    def _normalize(self, message):
        """Built-in normalizers plus whatever the project declared."""
        message = _normalize(message)
        for pattern, replacement in self._project_normalizers:
            try:
                message = pattern.sub(replacement, message)
            except Exception:
                continue
        return message

    def _display_path(self, path):
        """A path that resolves from where pytest was actually invoked.

        The reference is the invocation directory, not ``rootpath``. When a test
        outside the project is passed on the command line, pytest sets rootdir
        to the common ancestor, and paths relative to *that* resolve from
        nowhere: `mypkg/__init__.py` came out as `proj/mypkg/__init__.py`, which
        looks like a duplicated directory and does not exist from the shell the
        reader is sitting in.
        """
        if not path:
            return ""
        absolute = self._absolute(path)
        text = str(absolute)
        if "site-packages" in text or "lib/python" in text:
            # A dependency: recognizable beats resolvable, and the reader is not
            # going to open it anyway.
            return _short_path(text)
        try:
            relative = os.path.relpath(absolute, self._invocation)
        except ValueError:  # different drive on Windows
            return text
        # `../ext/test_x.py` still resolves; a chain of them stops being useful.
        return text if relative.startswith("../../..") else relative

    def _absolute(self, path):
        """Best effort at the real location of a path pytest handed us."""
        candidate = Path(str(path))
        if candidate.is_absolute():
            return candidate
        root = getattr(self.config, "rootpath", None)
        if root is not None and (root / candidate).exists():
            return root / candidate
        return (self._invocation / candidate).resolve()

    # ---------------------------------------------------------------- render

    def _summary_line(self, session, exitstatus, groups):
        counts = {}
        for outcome in self._outcomes.values():
            counts[outcome] = counts.get(outcome, 0) + 1
        if self._errors:
            counts["errors"] = len(self._errors)
        executed = len(set(self._outcomes) | self._errors)
        duration = time.monotonic() - self._start

        verdict, note = _verdict(exitstatus)
        # pytest raises Interrupted for collection errors, so exit status alone
        # cannot tell them apart from a real interrupt.
        if verdict == "INTERRUPTED" and any(g.phase == "collect" for g in groups):
            verdict = "COLLECTION_ERROR"
        parts = [f"{verdict} exit={int(exitstatus)}"]

        detail = []
        for label in ("failed", "errors", "passed", "skipped", "xfailed", "xpassed"):
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
        if groups:
            # Stated even when there is only one: "38 failed | 1 root cause" is
            # the whole point, and suppressing it hides the best news in the
            # report.
            noun = "root cause" if len(groups) == 1 else "root causes"
            parts.append(f"{len(groups)} {noun}")
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

    def _render(self, summary, groups, limit, list_all, path=None):
        lines = [summary]

        for index, group in enumerate(groups, start=1):
            if limit is not None and index > limit:
                lines.append("")
                lines.append(
                    f"[{index}] {group.exc_type} | {_tests(group)} | "
                    f"{group.phase} | {group.location}"
                )
                continue
            lines.append("")
            lines.extend(self._render_group(index, group, list_all))

        if self._warning_groups:
            lines.append("")
            # Every distinct warning, always. Truncating by frequency is
            # exactly backwards: the group that appears once is the one most
            # likely to be new, and a reader cannot tell whether a hidden group
            # matters without going to read another artefact. The list is
            # bounded by how many *kinds* of warning a suite emits, not by how
            # many tests it has -- a pilot run of 9,332 tests produced 216
            # warnings in 60 groups.
            groups_shown = sorted(
                self._warning_groups.values(),
                key=lambda g: (-g["count"], g["category"], g["origin"]),
            )
            lines.append(
                f"warnings: {self._warnings} in {len(self._warning_groups)} groups"
            )
            for group in groups_shown:
                # One line per group. Two read better, but this section is pure
                # overhead on an otherwise clean run and the whole point is that
                # it stays cheap enough to leave on.
                head = group["message"].splitlines()[0] if group["message"] else ""
                if not list_all and len(head) > _WARNING_MESSAGE:
                    head = head[:_WARNING_MESSAGE].rstrip() + "..."
                variants = len(group.get("variants", ()))
                spread = f" ({variants} variants)" if variants > 1 else ""
                parts_ = [f"  {group['category']} x{group['count']}{spread}"]
                if group["origin"]:
                    parts_.append(group["origin"])
                if head:
                    parts_.append(head)
                lines.append(" | ".join(parts_))

        # A scientific suite skips heavily for missing optional dependencies,
        # and "412 skipped" does not tell you which capability is absent. The
        # reasons are bounded by their variety, not by the number of tests.
        for label, reasons in (("skipped", self._skipped), ("xfailed", self._xfailed)):
            grouped = {}
            for reason in reasons.values():
                grouped[reason] = grouped.get(reason, 0) + 1
            if not grouped:
                continue
            ordered = sorted(grouped.items(), key=lambda item: -item[1])
            limit = None if list_all else _SHOWN_TESTS
            lines.append("")
            lines.append(
                f"{label}: {len(reasons)} in {len(ordered)} "
                f"group{'s' if len(ordered) != 1 else ''}"
            )
            for reason, count in ordered[:limit]:
                # A skip with no declared reason is itself worth reporting: it
                # means tests are switched off and nobody wrote down why.
                lines.append(f"  x{count} | {reason or '(no reason declared)'}")
            remaining = len(ordered) - len(ordered[:limit])
            if remaining:
                lines.append(f"  +{remaining} more")

        if self._xpassed:
            lines.append("")
            lines.append("unexpected passes:")
            for nodeid, reason in self._xpassed:
                suffix = f" - {_sanitize(reason)}" if reason else ""
                lines.append(f"  {self._selector(nodeid)}{suffix}")

        slow = self._slow_tests()
        if slow:
            lines.append("")
            lines.append("slowest:")
            for nodeid, duration in slow:
                lines.append(f"  {nodeid} ({duration:.2f}s)")

        held_back = (
            limit is not None and len(groups) > limit and self.profile.show_report_path
        )
        if held_back and path is not None:
            lines.append("")
            lines.append(f"full report: {path}")

        return "\n".join(lines) + "\n"

    def _render_group(self, index, group, list_all):
        lines = [
            f"[{index}] {group.exc_type} | {_tests(group)} | {group.phase}",
            f"    {group.location}",
        ]
        for line in group.message.splitlines():
            # rstrip only: pytest pads its assertion explanations with
            # whitespace-only lines, which cost a token and read as corruption.
            # Genuinely empty lines are kept, since a diff of multi-line strings
            # can contain them as content.
            lines.append(f"    {line}".rstrip())
        if group.cause:
            lines.append(f"    caused by: {group.cause}")
        extra = len(group.variants) - 1
        if extra > 0:
            shown = [v for v in group.variants.values()][1 : 1 + _SHOWN_TESTS]
            lines.append(f"    {extra} other message{'s' if extra > 1 else ''}:")
            for variant in shown:
                lines.append(f"      {variant.splitlines()[0]}")
            if extra > len(shown):
                lines.append(f"      +{extra - len(shown)} more")
        if len(group.frames) > 1:
            lines.append("    frames: " + " -> ".join(group.frames))

        for occurrence in self._section_sources(group, list_all):
            for name, content in occurrence.sections.items():
                lines.append(f"    captured {name} ({occurrence.nodeid}):")
                for line in content.splitlines():
                    lines.append(f"      {line}")

        if len(group.occurrences) > 1:
            lines.append("    tests:")
            shown = group.occurrences if list_all else group.occurrences[:_SHOWN_TESTS]
            for occurrence in shown:
                retried = (
                    f" (after {occurrence.attempts} attempts)"
                    if occurrence.attempts > 1
                    else ""
                )
                lines.append(f"      {self._selector(occurrence.nodeid)}{retried}")
            remaining = len(group.occurrences) - len(shown)
            if remaining:
                lines.append(f"      +{remaining} more")
        lines.append(f"    rerun: {self._rerun(group)}")
        return lines

    def _section_sources(self, group, list_all):
        """Occurrences whose captured output is worth printing.

        Captured output usually differs per test even when the exception does
        not, so it must not be collapsed to the first occurrence (PR-FID-001).
        In compact mode only the first few are printed; every one of them is in
        the full report.
        """
        with_sections = [item for item in group.occurrences if item.sections]
        if list_all:
            return with_sections
        return with_sections[:_SHOWN_TESTS]

    def _selector(self, nodeid):
        """A node ID whose path resolves from the invocation directory.

        Node IDs are rootdir-relative. A reader who copies one out of the list
        should be able to paste it straight back, exactly as with the rerun
        command.
        """
        path, sep, rest = nodeid.partition("::")
        return self._display_path(path) + sep + rest

    def _rerun(self, group):
        """A command that selects the group *and* runs from where they are.

        Node IDs are relative to rootdir, which is not necessarily where pytest
        was invoked. Pasting one back produced `file or directory not found`.
        """
        nodeids = [occurrence.nodeid for occurrence in group.occurrences]
        if len(nodeids) == 1:
            return f"pytest {self._selector(nodeids[0])} -q"
        files = sorted({nodeid.split("::", 1)[0] for nodeid in nodeids})
        return "pytest " + " ".join(self._display_path(f) for f in files) + " -q"

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
            # The report carries whatever the tests printed, which can include
            # credentials, tokens, or private paths. Refuse to follow a symlink
            # and keep it owner-only (PR-SEC-002). Redaction is still to come:
            # this bounds who can read it, not what it contains.
            if path.is_symlink():
                return None
            with os.fdopen(
                os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | _NOFOLLOW, 0o600),
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(text)
            os.chmod(path, 0o600)
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


def _compile_normalizers(config):
    """Project-declared `regex -> replacement` rules from the ini file.

    Scientific suites carry array shapes, dtypes, device names, and temporary
    paths in their failure messages, and any of those can split one root cause
    into dozens of groups. We cannot guess them, so the project declares them --
    and what a project needed is exactly the evidence required before deciding
    on built-in defaults.
    """
    rules = []
    try:
        declared = config.getini("receptor_normalizers") or []
    except Exception:
        return rules
    for rule in declared:
        pattern, separator, replacement = str(rule).partition("->")
        if not separator:
            continue
        try:
            rules.append((re.compile(pattern.strip()), replacement.strip()))
        except re.error:
            # A broken rule in someone's config must not break their run.
            continue
    return rules


_DIGITS = re.compile(r"(\d+)")


def _natural(text):
    """Sort key that reads runs of digits as numbers.

    Parametrized node IDs are the common case here, and plain string order puts
    ``test[10]`` between ``test[0]`` and ``test[2]``, which looks like a bug to
    anyone reading a cascade.
    """
    return [int(part) if part.isdigit() else part for part in _DIGITS.split(text)]


def _skip_reason(report):
    """The reason a test was skipped, from pytest's (path, lineno, text) tuple."""
    longrepr = getattr(report, "longrepr", None)
    if not isinstance(longrepr, tuple) or len(longrepr) != 3:
        return ""
    text = _sanitize(str(longrepr[2])).strip()
    if text.startswith("Skipped: "):
        text = text.split(":", 1)[1].strip()
    # pytest writes a bare "Skipped" when no reason was given; grouping on that
    # produces a line that says nothing.
    return "" if text == "Skipped" else text


def _short_path(path):
    """Enough of an external path to recognize the library, and no more."""
    parts = Path(path).parts
    return "/".join(parts[-3:]) if len(parts) > 3 else str(path)


def _prune_frames(raw):
    """Keep the frames that decide a failure, drop the ones that pad it.

    Dropping every external frame is cheaper but destructive: when a failure
    originates inside NumPy, OpenMM, or a serializer, the decisive frame is
    external. What matters is the shape of the call, so this keeps

    * the local frame that started it,
    * the last local frame,
    * every local-to-external boundary,
    * and the terminal frame, always -- that is where it actually broke,

    and marks each elision so nobody mistakes the summary for the whole stack.
    """
    if not raw:
        return []

    # Local frames are the signal: they are the code the reader can actually
    # change, so they are all kept unless the stack is pathological. External
    # runs are the noise, and only their entry and end points survive.
    locals_ = [index for index, frame in enumerate(raw) if not frame[2]]
    if len(locals_) > _MAX_LOCAL_FRAMES:
        half = _MAX_LOCAL_FRAMES // 2
        locals_ = locals_[:half] + locals_[-half:]

    keep = set(locals_)
    keep.add(len(raw) - 1)
    for index in range(1, len(raw)):
        if not raw[index - 1][2] and raw[index][2]:
            keep.add(index)

    rendered = []
    previous = None
    for index in sorted(keep):
        if previous is not None and index > previous + 1:
            rendered.append("...")
        path, lineno, external = raw[index]
        rendered.append(f"{path}:{lineno}{' (ext)' if external else ''}")
        previous = index
    return rendered


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
    # A bare `assert 0` crashes with the message "assert 0" and no exception
    # name at all, which would otherwise be filed under a useless "Failure".
    if head.startswith("assert "):
        return "AssertionError"
    return "Failure"


def _tests(group):
    count = len(group.occurrences)
    return f"{count} test" if count == 1 else f"{count} tests"


def _sanitize(text):
    """Test output is untrusted input, so strip anything non-textual.

    Redaction happens here, before anything else sees the text, so a secret
    cannot reach the terminal, the on-disk report, or a fingerprint. Doing it
    this early also means two failures differing only in the credential value
    group together, which is right: it is the same bug.
    """
    if not text:
        return ""
    text = _CONTROL.sub("", _ANSI.sub("", str(text)))
    for pattern, replacement in _SECRETS:
        text = pattern.sub(replacement, text)
    return text


def _normalize(message):
    message = _HEX_ADDR.sub("[ADDR]", message)
    return _TIMESTAMP.sub("[TIME]", message)


def _normalize_warning(message):
    """Warnings additionally lose their numbers.

    Deliberately not applied to failures. A warning saying a size mismatched is
    the same warning whatever the sizes were, but `assert 3.0 == 3.5` and
    `assert 3.0 == 4.5` are different failures, and collapsing them would hide
    which value was wrong.
    """
    message = _SHAPE.sub("(N)", _normalize(message))
    return _NUMBER.sub("N", message)


def _truncate(message, limit=_MAX_MESSAGE):
    if len(message) <= limit:
        return message
    head = message[: limit - 400]
    tail = message[-400:]
    omitted = len(message) - len(head) - len(tail)
    return f"{head}\n... [{omitted} characters omitted; see full report] ...\n{tail}"
