import json
from typing import List, Dict, Any, Optional


class EventReader:
    """Public reader API for pytest-receptor JSONL event artifacts."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.events: List[Dict[str, Any]] = []
        self._load_events()

    def _load_events(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            self.events.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except FileNotFoundError:
            pass

    def get_session_start(self) -> Optional[Dict[str, Any]]:
        """Return the session start event if present."""
        for event in self.events:
            if event.get("schema") == "pytest-receptor.event.session_start@1":
                return event
        return None

    def get_session_finish(self) -> Optional[Dict[str, Any]]:
        """Return the session finish event if present."""
        for event in self.events:
            if event.get("schema") == "pytest-receptor.event.session_finish@1":
                return event
        return None

    def get_test_phases(
        self,
        nodeid: Optional[str] = None,
        phase: Optional[str] = None,
        outcome: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return all test phase events, optionally filtered by nodeid, phase, or

        outcome.
        """
        phases = []
        for event in self.events:
            if event.get("schema") == "pytest-receptor.event.test_phase@1":
                if nodeid and nodeid not in event.get("nodeid", ""):
                    continue
                if phase and event.get("phase") != phase:
                    continue
                if outcome and event.get("outcome") != outcome:
                    continue
                phases.append(event)
        return phases

    def get_warnings(self) -> List[Dict[str, Any]]:
        """Return all warning events."""
        return [
            ev
            for ev in self.events
            if ev.get("schema") == "pytest-receptor.event.warning@1"
        ]

    def get_extension_events(
        self, namespace: Optional[str] = None, kind: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return namespaced extension events, optionally filtered by namespace or

        kind.
        """
        ext_events = []
        for event in self.events:
            if event.get("schema") == "pytest-receptor.extension-event@1":
                if namespace and event.get("namespace") != namespace:
                    continue
                if kind and event.get("kind") != kind:
                    continue
                ext_events.append(event)
        return ext_events

    def get_failures(self) -> List[Dict[str, Any]]:
        """Return all failed test phase events."""
        return self.get_test_phases(outcome="failed")
