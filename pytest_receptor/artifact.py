"""Versioned JSONL evidence artifacts and their supported reader API."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .model import PhaseEvent, WarningEvent

SCHEMA = "pytest-receptor.events@1"
_SCHEMA_PATTERN = re.compile(r"^pytest-receptor\.events@(\d+)$")
_SUPPORTED_MAJOR = 1
_KNOWN_TYPES = {
    "session_start",
    "phase",
    "warning",
    "root_cause",
    "evidence_limit",
    "session_finish",
}
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
DEFAULT_MAX_BYTES = 50 * 1024 * 1024
MIN_MAX_BYTES = 64 * 1024
_FINAL_RESERVE = 32 * 1024


class ArtifactError(Exception):
    """Base class for artifact read/write failures."""


class UnsupportedSchemaError(ArtifactError):
    """The artifact uses a schema major this reader cannot interpret."""


class ArtifactFormatError(ArtifactError):
    """The artifact is malformed rather than merely unfinished."""


class ArtifactIntegrityError(ArtifactError):
    """A finalized artifact does not match its integrity metadata."""


@dataclass(frozen=True)
class ArtifactRecord:
    """One record, including unknown types without destructive coercion."""

    type: str
    data: Mapping[str, Any]
    known: bool


@dataclass(frozen=True)
class Artifact:
    schema: str
    records: tuple[ArtifactRecord, ...]
    complete: bool
    integrity_valid: bool | None
    issue: str = ""

    @property
    def events(self) -> tuple[ArtifactRecord, ...]:
        return tuple(
            record
            for record in self.records
            if record.type not in ("session_start", "session_finish")
        )

    @property
    def final(self) -> ArtifactRecord | None:
        if self.records and self.records[-1].type == "session_finish":
            return self.records[-1]
        return None


class JsonlArtifactWriter:
    """Append normalized events and make completion cryptographically evident."""

    def __init__(
        self,
        path: Path,
        start_record: Mapping[str, Any],
        *,
        max_bytes: int = DEFAULT_MAX_BYTES,
    ):
        if max_bytes < MIN_MAX_BYTES:
            raise ArtifactError(f"artifact max bytes must be at least {MIN_MAX_BYTES}")
        self.path = path
        self.max_bytes = max_bytes
        self._digest = hashlib.sha256()
        self._record_count = 0
        self._bytes_written = 0
        self._truncated = False
        self._dropped_records = 0
        self._closed = False
        self._schema = str(start_record.get("schema", SCHEMA))
        self._run_id = str(start_record.get("run_id", ""))
        if path.is_symlink():
            raise ArtifactError(f"refusing symlink: {path}")
        try:
            descriptor = os.open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC | _NOFOLLOW,
                0o600,
            )
            self._handle = os.fdopen(descriptor, "wb")
            os.chmod(path, 0o600)
        except OSError as exc:
            raise ArtifactError(str(exc)) from exc
        self.write(start_record)

    def write(self, record: Mapping[str, Any]) -> bool:
        if self._closed:
            raise ArtifactError("artifact is closed")
        if self._truncated:
            self._dropped_records += 1
            return False
        payload = _encode_record(record)
        if self._bytes_written + len(payload) + _FINAL_RESERVE > self.max_bytes:
            self._truncated = True
            self._dropped_records = 1
            marker = _encode_record(
                {
                    "schema": self._schema,
                    "type": "evidence_limit",
                    "run_id": self._run_id,
                    "reason": "max_bytes",
                    "max_bytes": self.max_bytes,
                }
            )
            if self._bytes_written + len(marker) + _FINAL_RESERVE <= self.max_bytes:
                self._append(marker)
            return False
        self._append(payload)
        return True

    def _append(self, payload: bytes) -> None:
        try:
            self._handle.write(payload)
            self._handle.flush()
        except OSError as exc:
            self.close()
            raise ArtifactError(str(exc)) from exc
        self._digest.update(payload)
        self._record_count += 1
        self._bytes_written += len(payload)

    def write_phase(self, run_id: str, event: PhaseEvent) -> None:
        record = asdict(event)
        record.update(
            {
                "schema": SCHEMA,
                "type": "phase",
                "event_id": f"{run_id}:{event.sequence}",
            }
        )
        self.write(record)

    def write_warning(self, run_id: str, event: WarningEvent) -> None:
        record = asdict(event)
        record.update(
            {
                "schema": SCHEMA,
                "type": "warning",
                "event_id": f"{run_id}:{event.sequence}",
            }
        )
        self.write(record)

    def finalize(self, record: Mapping[str, Any]) -> None:
        if self._closed:
            raise ArtifactError("artifact is closed")
        final = dict(record)
        final["artifact_policy"] = {
            "max_bytes": self.max_bytes,
            "truncated": self._truncated,
            "dropped_records": self._dropped_records,
        }
        final["integrity"] = {
            "algorithm": "sha256",
            "records": self._record_count,
            "digest": self._digest.hexdigest(),
        }
        payload = _encode_record(final)
        if self._bytes_written + len(payload) > self.max_bytes:
            raise ArtifactError("final record exceeds artifact max bytes")
        try:
            self._handle.write(payload)
            self._handle.flush()
            os.fsync(self._handle.fileno())
            self._bytes_written += len(payload)
        except OSError as exc:
            raise ArtifactError(str(exc)) from exc
        finally:
            self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._handle.close()
        except OSError:
            pass


def read_artifact(path: str | os.PathLike[str]) -> Artifact:
    """Read and validate an events artifact without discarding unknown events."""
    source = Path(path)
    try:
        lines = source.read_bytes().splitlines(keepends=True)
    except OSError as exc:
        raise ArtifactError(str(exc)) from exc
    if not lines:
        raise ArtifactFormatError("artifact is empty")

    records = []
    decoded = []
    issue = ""
    for index, line in enumerate(lines):
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            if index == len(lines) - 1:
                issue = "truncated final record"
                break
            raise ArtifactFormatError(f"invalid JSON on line {index + 1}") from exc
        if not isinstance(value, dict):
            raise ArtifactFormatError(f"line {index + 1} is not a JSON object")
        decoded.append((line, value))

    if not decoded:
        raise ArtifactFormatError("artifact has no complete record")
    schema = str(decoded[0][1].get("schema", ""))
    _validate_schema(schema)
    for index, (_line, value) in enumerate(decoded, start=1):
        if value.get("schema") != schema:
            raise ArtifactFormatError(f"schema mismatch on line {index}")
        record_type = str(value.get("type", ""))
        if not record_type:
            raise ArtifactFormatError(f"missing record type on line {index}")
        records.append(
            ArtifactRecord(record_type, dict(value), record_type in _KNOWN_TYPES)
        )

    complete = records[-1].type == "session_finish" and not issue
    if not complete:
        return Artifact(
            schema,
            tuple(records),
            complete=False,
            integrity_valid=None,
            issue=issue or "missing session_finish",
        )

    integrity = records[-1].data.get("integrity")
    if not isinstance(integrity, dict) or integrity.get("algorithm") != "sha256":
        raise ArtifactIntegrityError("missing or unsupported integrity metadata")
    expected_records = len(decoded) - 1
    if integrity.get("records") != expected_records:
        raise ArtifactIntegrityError("record count mismatch")
    digest = hashlib.sha256()
    for line, _value in decoded[:-1]:
        digest.update(line)
    if integrity.get("digest") != digest.hexdigest():
        raise ArtifactIntegrityError("digest mismatch")
    return Artifact(schema, tuple(records), complete=True, integrity_valid=True)


def _validate_schema(schema: str) -> None:
    match = _SCHEMA_PATTERN.fullmatch(schema)
    if match is None:
        raise ArtifactFormatError(f"invalid schema: {schema or '(missing)'}")
    major = int(match.group(1))
    if major != _SUPPORTED_MAJOR:
        raise UnsupportedSchemaError(
            f"unsupported schema major {major}; supported: {_SUPPORTED_MAJOR}"
        )


def _encode_record(record: Mapping[str, Any]) -> bytes:
    try:
        text = json.dumps(
            record,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ArtifactError(f"record is not JSON serializable: {exc}") from exc
    return (text + "\n").encode("utf-8")
