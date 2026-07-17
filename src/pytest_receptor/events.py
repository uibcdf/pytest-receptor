import dataclasses
from typing import Dict, List, Optional, Any


@dataclasses.dataclass
class ExceptionInfo:
    exc_type: str
    message: str
    traceback: List[str]  # frames list
    assertion_diff: Optional[str] = None
    cause: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}


@dataclasses.dataclass
class TestPhaseEvent:
    nodeid: str
    phase: str  # "setup", "call", "teardown"
    outcome: str  # "passed", "failed", "skipped"
    duration: float
    timestamp: float  # monotonic timestamp
    worker: str = "local"
    reason: Optional[str] = None
    exception: Optional[ExceptionInfo] = None
    captured_stdout: Optional[str] = None
    captured_stderr: Optional[str] = None
    captured_log: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "schema": "pytest-receptor.event.test_phase@1",
            "nodeid": self.nodeid,
            "phase": self.phase,
            "outcome": self.outcome,
            "duration": self.duration,
            "timestamp": self.timestamp,
            "worker": self.worker,
        }
        if self.reason:
            d["reason"] = self.reason
        if self.exception:
            d["exception"] = self.exception.to_dict()
        if self.captured_stdout:
            d["captured_stdout"] = self.captured_stdout
        if self.captured_stderr:
            d["captured_stderr"] = self.captured_stderr
        if self.captured_log:
            d["captured_log"] = self.captured_log
        return d


@dataclasses.dataclass
class WarningEvent:
    category: str
    message: str
    filename: str
    lineno: int
    timestamp: float
    nodeid: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "schema": "pytest-receptor.event.warning@1",
            "category": self.category,
            "message": self.message,
            "filename": self.filename,
            "lineno": self.lineno,
            "timestamp": self.timestamp,
        }
        if self.nodeid:
            d["nodeid"] = self.nodeid
        return d


@dataclasses.dataclass
class SessionStartEvent:
    run_id: str
    timestamp_iso: str
    pytest_version: str
    python_version: str
    plugins: Dict[str, str]
    command_line: List[str]
    root_dir: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "pytest-receptor.event.session_start@1",
            **dataclasses.asdict(self),
        }


@dataclasses.dataclass
class SessionFinishEvent:
    run_id: str
    timestamp_iso: str
    exitstatus: int
    outcome: str  # "OK", "FAILED", "INTERRUPTED", "INTERNAL_ERROR", "USAGE_ERROR", "NO_TESTS"
    duration: float
    complete: bool
    counts: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "pytest-receptor.event.session_finish@1",
            **dataclasses.asdict(self),
        }
