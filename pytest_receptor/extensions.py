"""Producer-neutral extension events for the receptor-owned pytest artifact.

The public service is deliberately inert with the human profile. A producer
passes a pytest Config explicitly so background work cannot inherit another
test's context through a process global.
"""

from __future__ import annotations

import json
import math
import re
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Mapping

_NAMESPACE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*@\d+$")
_CURRENT: ContextVar[ExecutionContext | None] = ContextVar(
    "pytest_receptor_extension_context", default=None
)
MAX_EVENT_BYTES = 16 * 1024
MAX_STRING = 2048
MAX_ITEMS = 128
MAX_DEPTH = 6


@dataclass(frozen=True)
class ExecutionContext:
    """The active pytest phase in this context, or no context outside it."""

    nodeid: str
    phase: str
    worker_id: str
    attempt: int


def current_context() -> ExecutionContext | None:
    """Return a read-only snapshot of the active pytest phase."""
    return _CURRENT.get()


def emit(
    config: Any,
    namespace: str,
    payload: Mapping[str, Any],
    *,
    relationships: tuple[str, ...] | list[str] = (),
) -> str | None:
    """Queue a bounded JSON event; return its producer reference if accepted.

    Namespaces include a major version (for example ``org.example.timer@1``).
    Data is pattern-redacted before it crosses a worker boundary or reaches an
    artifact. Producers remain responsible for excluding opaque secrets: the
    receptor cannot infer whether an arbitrary string is confidential.
    Rejection does not change the native pytest outcome.
    """
    plugin = config.pluginmanager.getplugin("receptor-renderer")
    if plugin is None:
        return None
    return plugin._emit_extension(namespace, payload, relationships)


def mark_incomplete(config: Any) -> None:
    """Declare a producer-side gap without changing pytest's outcome."""
    plugin = config.pluginmanager.getplugin("receptor-renderer")
    if plugin is not None:
        plugin._mark_extension_incomplete()


def _prepare(
    namespace: str,
    payload: Mapping[str, Any],
    relationships: tuple[str, ...] | list[str],
    sanitize,
) -> dict[str, Any]:
    if not isinstance(namespace, str) or not _NAMESPACE.fullmatch(namespace):
        raise ValueError("extension namespace must have a major version")
    if not isinstance(payload, Mapping):
        raise ValueError("extension payload must be a mapping")
    if not isinstance(relationships, (tuple, list)) or len(relationships) > MAX_ITEMS:
        raise ValueError("extension relationships exceed the limit")
    if any(not isinstance(value, str) for value in relationships):
        raise ValueError("extension relationships must be strings")
    if any(len(value) > MAX_STRING for value in relationships):
        raise ValueError("extension relationship exceeds the string limit")
    safe = {
        "namespace": namespace,
        "payload": _safe_value(payload, sanitize, 0),
        "relationships": [sanitize(value) for value in relationships],
        "producer_ref": uuid.uuid4().hex,
        "trust": "producer_untrusted",
        "redaction": "pattern",
    }
    encoded = json.dumps(safe, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(encoded) > MAX_EVENT_BYTES:
        raise ValueError("extension event exceeds the byte limit")
    return safe


def _safe_value(value: Any, sanitize, depth: int) -> Any:
    if depth > MAX_DEPTH:
        raise ValueError("extension payload exceeds the depth limit")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("extension payload has a non-finite number")
        return value
    if isinstance(value, str):
        if len(value) > MAX_STRING:
            raise ValueError("extension string exceeds the limit")
        return sanitize(value)
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_ITEMS:
            raise ValueError("extension payload array exceeds the limit")
        return [_safe_value(item, sanitize, depth + 1) for item in value]
    if isinstance(value, Mapping):
        if len(value) > MAX_ITEMS or any(not isinstance(key, str) for key in value):
            raise ValueError("extension payload object exceeds the limit")
        if any(len(key) > MAX_STRING for key in value):
            raise ValueError("extension key exceeds the limit")
        result = {}
        for key, item in value.items():
            safe_key = sanitize(key)
            if safe_key in result:
                raise ValueError("extension keys collide after redaction")
            result[safe_key] = _safe_value(item, sanitize, depth + 1)
        return result
    raise ValueError("extension payload contains a non-JSON value")
