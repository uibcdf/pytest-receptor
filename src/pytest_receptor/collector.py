import os
import sys
import time
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any

import pytest
from _pytest.config import Config

from pytest_receptor.events import (
    SessionStartEvent,
    SessionFinishEvent,
    TestPhaseEvent,
    WarningEvent,
    ExceptionInfo,
    ExtensionEvent,
)


import re


def strip_ansi(text: str) -> str:
    if not text:
        return text
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def redact_secrets(text: str) -> str:
    if not text:
        return text
    # 1. Redact API keys, tokens, passwords
    text = re.sub(
        r"(?i)(api[_-]?key|token|password|secret|credential|passwd|auth)[ \t]*[=:][ \t]*['\"]?([a-zA-Z0-9_\-\.]{12,})['\"]?",
        r"\1=[REDACTED_SECRET]",
        text,
    )
    # 2. General auth headers
    text = re.sub(
        r"(?i)(Authorization:\s*Basic\s+|Bearer\s+)[a-zA-Z0-9_\-\.\+/=]{10,}",
        r"\1[REDACTED_SECRET]",
        text,
    )
    return text


class EventCollector:
    def __init__(self, config: Config):
        self.config = config
        self.run_id = str(uuid.uuid4())
        self.start_time = time.monotonic()
        self.start_time_iso = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

        self.session_started = False
        self.session_finished = False

        self.events: List[Any] = []
        self.test_phases: List[TestPhaseEvent] = []
        self.warnings: List[WarningEvent] = []

        self.current_nodeid = None
        self.current_phase = None
        self.current_worker = "local"
        self.current_attempt = 1

        # Determine artifact path
        self.artifact_path = self.config.getoption("--receptor-artifact", None)
        if not self.artifact_path:
            # Fallback default path if receptor is active
            receptor_mode = self.config.getoption("--receptor", None)
            if receptor_mode in ("llm", "ci"):
                self.artifact_path = ".pytest-receptor.jsonl"

        self.artifact_file = None
        if self.artifact_path:
            try:
                abs_path = os.path.abspath(self.artifact_path)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                self.artifact_file = open(
                    abs_path, "w", encoding="utf-8", buffering=1
                )  # line-buffered
            except Exception as e:
                # Safe degradation: print a warning to stderr
                sys.stderr.write(
                    f"Warning: pytest-receptor failed to open artifact path '{self.artifact_path}': {e}\n"
                )

    def _write_event(self, event: Any):
        self.events.append(event)
        if self.artifact_file:
            try:
                d = event.to_dict()
                self.artifact_file.write(json.dumps(d) + "\n")
            except Exception:
                pass

    def close(self):
        if self.artifact_file:
            try:
                self.artifact_file.close()
            except Exception:
                pass
            self.artifact_file = None

    def log_session_start(self):
        if self.session_started:
            return
        self.session_started = True

        # Extract plugins
        plugins = {}
        try:
            for dist, _ in self.config.pluginmanager.list_plugin_distinfo():
                name = getattr(dist, "project_name", getattr(dist, "name", str(dist)))
                version = getattr(dist, "version", "unknown")
                plugins[name] = version
        except Exception:
            pass

        root_dir = str(
            getattr(self.config, "rootpath", getattr(self.config, "rootdir", ""))
        )

        event = SessionStartEvent(
            run_id=self.run_id,
            timestamp_iso=self.start_time_iso,
            pytest_version=pytest.__version__,
            python_version=sys.version,
            plugins=plugins,
            command_line=sys.argv,
            root_dir=root_dir,
        )
        self._write_event(event)

    def log_session_finish(self, exitstatus: int, session: Any = None):
        if self.session_finished:
            return
        self.session_finished = True

        duration = time.monotonic() - self.start_time
        timestamp_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Calculate counts
        counts = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": 0,
            "xfailed": 0,
            "xpassed": 0,
            "warnings": len(self.warnings),
        }

        # We determine counts from test_phases
        # Note: a test phase has outcome "passed", "failed", "skipped"
        # Let's map outcomes accurately based on finished logical tests.
        # But wait, terminal reporter stats contains the definitive categories.
        # To match pytest exactly, let's extract counts from self.config (or the terminal reporter stats if available)
        # or fall back to phase counts.
        tr = self.config.pluginmanager.get_plugin("terminalreporter")
        if tr and hasattr(tr, "stats"):
            counts["passed"] = len(tr.stats.get("passed", []))
            counts["failed"] = len(tr.stats.get("failed", []))
            counts["skipped"] = len(tr.stats.get("skipped", []))
            counts["error"] = len(tr.stats.get("error", []))
            counts["xfailed"] = len(tr.stats.get("xfailed", []))
            counts["xpassed"] = len(tr.stats.get("xpassed", []))
        else:
            for p in self.test_phases:
                if p.outcome == "passed":
                    counts["passed"] += 1
                elif p.outcome == "failed":
                    counts["failed"] += 1
                elif p.outcome == "skipped":
                    counts["skipped"] += 1

        # Populate collected count
        collected = 0
        if session:
            collected = getattr(session, "testscollected", 0)
        elif tr and hasattr(tr, "_numtests"):
            collected = tr._numtests
        counts["collected"] = collected

        exit_val = int(exitstatus)
        if exit_val == 0:
            outcome = "OK"
        elif exit_val == 1:
            outcome = "FAILED"
        elif exit_val == 2:
            outcome = "INTERRUPTED"
        elif exit_val == 3:
            outcome = "INTERNAL_ERROR"
        elif exit_val == 4:
            outcome = "USAGE_ERROR"
        elif exit_val == 5:
            outcome = "NO_TESTS"
        else:
            outcome = "FAILED"

        # completeness: complete=false if exitstatus is interrupted (2) or internal_error (3) or shouldstop is set
        complete = exit_val not in (2, 3)
        stop_reason = None
        if session and getattr(session, "shouldstop", False):
            complete = False
            stop_reason = str(session.shouldstop)

        event = SessionFinishEvent(
            run_id=self.run_id,
            timestamp_iso=timestamp_iso,
            exitstatus=exit_val,
            outcome=outcome,
            duration=duration,
            complete=complete,
            counts=counts,
            stop_reason=stop_reason,
        )
        self._write_event(event)
        self.close()

    def log_test_phase(self, report: Any):
        # We only log completed setup/call/teardown phases
        if not hasattr(report, "when"):
            return

        nodeid = report.nodeid
        if hasattr(report, "subtest") and report.subtest:
            nodeid = f"{nodeid}[{report.subtest}]"

        phase = report.when
        outcome = report.outcome
        duration = getattr(report, "duration", 0.0)

        # Calculate attempt
        existing_count = sum(
            1 for p in self.test_phases if p.nodeid == nodeid and p.phase == phase
        )
        attempt = existing_count + 1

        # Check for xfailed/xpassed
        reason = None
        if hasattr(report, "wasxfail") and report.wasxfail:
            reason = str(report.wasxfail)
            # Adjust outcome if xfailed / xpassed
            if outcome == "skipped":
                outcome = "xfailed"
            elif outcome == "passed":
                outcome = "xpassed"
        elif (
            outcome == "skipped"
            and isinstance(report.longrepr, tuple)
            and len(report.longrepr) == 3
        ):
            reason = str(report.longrepr[2])
        elif outcome == "skipped":
            reason = str(getattr(report, "longrepr", ""))

        if reason is not None:
            reason = redact_secrets(strip_ansi(reason))

        # Exception details
        exception_info = None
        if outcome in ("failed", "error") or (report.failed and outcome != "skipped"):
            root_dir = getattr(
                self.config, "rootpath", getattr(self.config, "rootdir", None)
            )
            exception_info = self._extract_exception_info(report, root_dir)

        # Captured output sections
        captured_stdout = None
        captured_stderr = None
        captured_log = None

        sections = getattr(report, "sections", [])
        for section_name, section_content in sections:
            tag_name = section_name.lower().replace(" ", "_")
            if "stdout" in tag_name:
                captured_stdout = redact_secrets(strip_ansi(section_content.strip()))
            elif "stderr" in tag_name:
                captured_stderr = redact_secrets(strip_ansi(section_content.strip()))
            elif "log" in tag_name:
                captured_log = redact_secrets(strip_ansi(section_content.strip()))

        # Worker identifier (support xdist)
        worker = "local"
        if hasattr(report, "node") and report.node:
            worker = getattr(report.node, "gateway", {}).get("id", "gw")
            if not isinstance(worker, str):
                worker = getattr(
                    report.node, "gateway", getattr(report.node, "name", "gw")
                )

        # Update correlation state
        self.current_nodeid = nodeid
        self.current_phase = phase
        self.current_worker = str(worker)
        self.current_attempt = attempt

        event = TestPhaseEvent(
            nodeid=nodeid,
            phase=phase,
            outcome=outcome,
            duration=duration,
            timestamp=time.monotonic(),
            worker=str(worker),
            attempt=attempt,
            reason=reason,
            exception=exception_info,
            captured_stdout=captured_stdout,
            captured_stderr=captured_stderr,
            captured_log=captured_log,
        )
        self.test_phases.append(event)
        self._write_event(event)

    def log_warning(
        self,
        warning_message: Any,
        when: str,
        nodeid: Optional[str],
        location: Optional[Any],
    ):
        category = getattr(warning_message, "category", Warning)
        if hasattr(category, "__name__"):
            cat_name = category.__name__
        else:
            cat_name = str(category)

        message = str(getattr(warning_message, "message", warning_message))
        message = redact_secrets(strip_ansi(message))

        filename = ""
        lineno = 0
        if location:
            filename, lineno = location[0], location[1]
        elif hasattr(warning_message, "filename"):
            filename = warning_message.filename
            lineno = warning_message.lineno

        event = WarningEvent(
            category=cat_name,
            message=message,
            filename=str(filename),
            lineno=int(lineno) if lineno else 0,
            timestamp=time.monotonic(),
            nodeid=nodeid,
        )
        self.warnings.append(event)
        self._write_event(event)

    def _extract_exception_info(
        self, report: Any, root_dir: Optional[Any]
    ) -> Optional[ExceptionInfo]:
        message = ""

        if (
            hasattr(report.longrepr, "reprcrash")
            and report.longrepr.reprcrash is not None
        ):
            message = report.longrepr.reprcrash.message
        elif report.longrepr:
            message = str(report.longrepr)

        message = redact_secrets(strip_ansi(message))

        # Extract exception type
        exc_type = "Exception"
        for line in message.splitlines():
            line_str = line.strip()
            if line_str.startswith("E   ") and ":" in line_str:
                parts = line_str[4:].split(":", 1)
                first_part = parts[0].strip()
                if first_part.isidentifier() or all(
                    p.isidentifier() for p in first_part.split(".")
                ):
                    exc_type = first_part
                    break
            elif line_str.startswith("E ") and ":" in line_str:
                parts = line_str[2:].split(":", 1)
                first_part = parts[0].strip()
                if first_part.isidentifier() or all(
                    p.isidentifier() for p in first_part.split(".")
                ):
                    exc_type = first_part
                    break
        if exc_type == "Exception" and ":" in message:
            first_line = message.split("\n", 1)[0]
            if ":" in first_line:
                first_part = first_line.split(":", 1)[0].strip()
                if first_part.isidentifier() or all(
                    p.isidentifier() for p in first_part.split(".")
                ):
                    exc_type = first_part

        # Extract traceback
        frames = []
        if (
            hasattr(report.longrepr, "reprtraceback")
            and report.longrepr.reprtraceback is not None
        ):
            for entry in report.longrepr.reprtraceback.reprentries:
                if hasattr(entry, "reprfileloc") and entry.reprfileloc is not None:
                    fpath = entry.reprfileloc.path
                    floc = entry.reprfileloc.lineno
                    fmsg = redact_secrets(strip_ansi(entry.reprfileloc.message))

                    if root_dir and os.path.isabs(fpath):
                        try:
                            rel = os.path.relpath(fpath, start=root_dir)
                            if not rel.startswith(".."):
                                fpath = rel
                        except ValueError:
                            pass
                    frames.append(f"  at {fpath}:{floc} -> {fmsg}")

        # Assertion explanation / diff
        assertion_diff = None
        if (
            hasattr(report.longrepr, "reprtraceback")
            and report.longrepr.reprtraceback is not None
        ):
            # We can capture more details from the traceback lines if available
            pass

        return ExceptionInfo(
            exc_type=exc_type,
            message=message,
            traceback=frames,
            assertion_diff=assertion_diff,
        )

    # Pytest Hooks
    def pytest_runtest_logreport(self, report):
        self.log_test_phase(report)

    def pytest_warning_recorded(self, warning_message, when, nodeid, location):
        self.log_warning(warning_message, when, nodeid, location)

    def pytest_sessionfinish(self, session, exitstatus):
        self.log_session_finish(exitstatus, session)

    def pytest_runtest_setup(self, item):
        self.current_nodeid = item.nodeid
        self.current_phase = "setup"
        existing_count = sum(
            1
            for p in self.test_phases
            if p.nodeid == item.nodeid and p.phase == "setup"
        )
        self.current_attempt = existing_count + 1

    def pytest_runtest_call(self, item):
        self.current_phase = "call"

    def pytest_runtest_teardown(self, item, nextitem):
        self.current_phase = "teardown"

    def get_current_correlation(self) -> dict:
        return {
            "run_id": self.run_id,
            "nodeid": self.current_nodeid,
            "phase": self.current_phase,
            "worker": self.current_worker,
            "attempt": self.current_attempt,
        }

    def pytest_receptor_extension_event(
        self, namespace: str, kind: str, payload: dict, relationships: dict = None
    ):
        event = ExtensionEvent(
            namespace=namespace,
            kind=kind,
            payload=payload,
            relationships=relationships or {},
            timestamp=time.monotonic(),
        )
        self._write_event(event)
