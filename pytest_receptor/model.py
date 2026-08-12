"""Normalized, renderer-independent evidence for one pytest run.

This is an internal model while the ``pytest-receptor.events@1`` contract is
being proven.  It deliberately contains only Python and JSON-friendly values:
pytest report objects must not cross this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CapturedSection:
    """One captured section, preserving pytest's original name and contents."""

    name: str
    kind: str
    content: str


@dataclass(frozen=True)
class ExceptionEvidence:
    """Exception evidence and how its type was obtained."""

    type_name: str
    qualified_type: str
    type_source: str
    message: str
    location: str
    cause: str = ""
    frames: tuple[str, ...] = ()
    raw_longrepr: str = ""


@dataclass(frozen=True)
class SubtestIdentity:
    """One subtest within a logical pytest item and execution attempt."""

    index: int
    description: str
    message: str = ""
    parameters: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PhaseEvent:
    """The outcome of one setup/call/teardown or collection phase."""

    sequence: int
    nodeid: str
    phase: str
    outcome: str
    duration: float | None = None
    worker_id: str = ""
    attempt: int = 1
    reason: str = ""
    exception: ExceptionEvidence | None = None
    sections: tuple[CapturedSection, ...] = ()
    subtest: SubtestIdentity | None = None


@dataclass(frozen=True)
class WarningEvent:
    category: str
    message: str
    origin: str
    nodeid: str = ""
    when: str = ""
    sequence: int = 0


@dataclass
class SessionEvidence:
    """Single mutable collection target for one session's normalized evidence."""

    schema: str = "pytest-receptor.events@1"
    phases: list[PhaseEvent] = field(default_factory=list)
    warnings: list[WarningEvent] = field(default_factory=list)
    outcomes: dict[str, str] = field(default_factory=dict)
    errors: set[str] = field(default_factory=set)
    skipped: dict[str, str] = field(default_factory=dict)
    xfailed: dict[str, str] = field(default_factory=dict)
    xpassed: list[tuple[str, str]] = field(default_factory=list)
    collected: int = 0
    deselected: int = 0
    finished: int = 0
    _sequence: int = 0
    _current_attempt: dict[str, int] = field(default_factory=dict)
    _subtest_indexes: dict[tuple[str, int], int] = field(default_factory=dict)

    def next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence

    def attempt_for(self, nodeid: str, phase: str) -> int:
        """Return the execution attempt, not the number of call-like reports."""
        if phase == "setup":
            self._current_attempt[nodeid] = self._current_attempt.get(nodeid, 0) + 1
        return self._current_attempt.get(nodeid, 1)

    def next_subtest_index(self, nodeid: str, attempt: int) -> int:
        key = (nodeid, attempt)
        index = self._subtest_indexes.get(key, 0) + 1
        self._subtest_indexes[key] = index
        return index

    def add_phase(self, event: PhaseEvent) -> None:
        self.phases.append(event)
        nodeid = event.nodeid
        if event.phase == "teardown":
            self.finished += 1

        # Subtests are occurrences inside one collected logical item. A failed
        # subtest fails that item, but a pass/skip/xfail must not turn the parent
        # into a separately passed/skipped item; its ordinary call report owns
        # the final logical outcome.
        if event.subtest is not None:
            if event.outcome == "failed":
                self.outcomes[nodeid] = "failed"
            return

        if event.outcome == "failed":
            if event.phase in ("setup", "teardown"):
                self.errors.add(nodeid)
            else:
                self.outcomes[nodeid] = "failed"
            return

        if event.phase == "call":
            if event.outcome == "xpassed":
                self.xpassed.append((nodeid, event.reason))
                self.outcomes[nodeid] = "xpassed"
            elif event.outcome == "xfailed":
                self.xfailed[nodeid] = event.reason
                self.outcomes[nodeid] = "xfailed"
            elif event.outcome == "skipped":
                self.skipped[nodeid] = event.reason
                self.outcomes[nodeid] = "skipped"
            elif event.outcome == "passed":
                self.outcomes.setdefault(nodeid, "passed")
        elif event.phase == "setup" and event.outcome == "skipped":
            self.skipped[nodeid] = event.reason
            self.outcomes.setdefault(nodeid, "skipped")

    @property
    def failures(self) -> tuple[PhaseEvent, ...]:
        """Failures that determine the terminal diagnosis.

        A rerun can carry exception evidence from a transient failed attempt,
        but it must not be rendered as a final failure after a later pass.
        """
        return tuple(
            event
            for event in self.phases
            if event.exception is not None and event.outcome == "failed"
        )

    @property
    def exception_events(self) -> tuple[PhaseEvent, ...]:
        """All exception evidence, including transient rerun attempts."""
        return tuple(event for event in self.phases if event.exception is not None)

    @property
    def executed(self) -> int:
        return len(set(self.outcomes) | self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def reruns(self) -> int:
        return sum(event.outcome == "rerun" for event in self.phases)

    @property
    def subtest_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for event in self.phases:
            if event.subtest is not None:
                counts[event.outcome] = counts.get(event.outcome, 0) + 1
        return counts
