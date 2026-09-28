"""Parse and validate issue-backed developer-guide reports."""

from __future__ import annotations

import ast
import datetime as dt
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVGUIDE = ROOT / "devguide"
REPOSITORY = "uibcdf/pytest-receptor"
OPEN_STATUSES = ("active", "partial", "blocked", "open")
CLOSED_STATUSES = ("resolved", "withdrawn", "superseded")
VERIFICATIONS = {"reproduced", "measured", "inspected", "upstream", "asserted"}
SEVERITIES = {"critical", "high", "medium", "low"}
OWN_ISSUE = re.compile(rf"^{re.escape(REPOSITORY)}#[1-9]\d*$")
ISSUE = re.compile(r"^[\w.-]+/[\w.-]+#[1-9]\d*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GUARD = re.compile(
    r"^(?:tests|devtools/tests)/(?:[A-Za-z0-9_]+/)*test_[A-Za-z0-9_]+\.py"
    r"(?:::[A-Za-z_][A-Za-z0-9_]*){0,2}$"
)
LOCATIONS = (
    ("pending_bugs", "bug", False),
    ("pending_proposals", "proposal", False),
    ("resolved_bugs", "bug", True),
    ("resolved_proposals", "proposal", True),
)
LEGACY_MANIFEST = DEVGUIDE / "legacy_report_manifest.toml"


@dataclass(frozen=True)
class Report:
    path: Path
    fields: dict[str, object]
    kind: str
    archived: bool

    @property
    def relative_path(self) -> str:
        return self.path.relative_to(ROOT).as_posix()


@dataclass(frozen=True)
class LegacyReport:
    path: Path
    register: str
    resolved: str
    issue: str


def load_legacy_reports() -> tuple[list[LegacyReport], list[str]]:
    errors: list[str] = []
    try:
        data = tomllib.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [], [f"legacy report manifest cannot be read: {error}"]
    if data.get("owner") != "uibcdf/pytest-receptor#10":
        errors.append("legacy report manifest needs owning issue #10")
    due = str(data.get("review_due", ""))
    try:
        if dt.date.fromisoformat(due) < dt.date.today():
            errors.append("legacy report exception review is overdue")
    except ValueError:
        errors.append("legacy report exception needs an ISO review_due date")
    legacy: list[LegacyReport] = []
    seen: set[Path] = set()
    for entry in data.get("legacy-reports", []):
        relative = str(entry.get("path", ""))
        path = ROOT / relative
        if (
            not relative.startswith(
                ("devguide/resolved_bugs/", "devguide/resolved_proposals/")
            )
            or ".." in Path(relative).parts
            or path in seen
        ):
            errors.append(f"invalid or duplicate legacy path: {relative!r}")
            continue
        seen.add(path)
        if not path.is_file():
            errors.append(f"missing legacy report: {relative}")
            continue
        if path.read_text(encoding="utf-8").startswith("---\n"):
            errors.append(
                f"legacy report has front matter and must leave manifest: {relative}"
            )
        register = str(entry.get("register", ""))
        resolved = str(entry.get("resolved", ""))
        issue = str(entry.get("issue", ""))
        if not register or not DATE.fullmatch(resolved) or resolved > "2026-09-27":
            errors.append(f"legacy report needs register and resolved date: {relative}")
        if issue and not OWN_ISSUE.fullmatch(issue):
            errors.append(f"legacy report has invalid issue: {relative}")
        legacy.append(LegacyReport(path, register, resolved, issue))
    if len(legacy) > 17:
        errors.append("legacy manifest cannot grow beyond its 17 pre-protocol records")
    return legacy, errors


def _value(raw: str) -> object:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [] if not inner else [item.strip() for item in inner.split(",")]
    return raw


def read_front_matter(path: Path) -> tuple[dict[str, object], list[str]]:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(ROOT).as_posix()
    if not text.startswith("---\n") or text.count("---\n") < 2:
        return {}, [f"{relative}: missing YAML front matter"]
    fields: dict[str, object] = {}
    for line in text.split("---\n", 2)[1].splitlines():
        if ":" not in line or line.startswith((" ", "#")):
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = _value(value)
    return fields, []


def load_reports() -> tuple[list[Report], list[str]]:
    reports: list[Report] = []
    legacy, errors = load_legacy_reports()
    legacy_paths = {entry.path for entry in legacy}
    for relative, kind, archived in LOCATIONS:
        directory = DEVGUIDE / relative
        if not directory.is_dir():
            errors.append(f"devguide/{relative}: directory is missing")
            continue
        for path in sorted(directory.rglob("*.md")):
            if path.name == "README.md":
                continue
            if path in legacy_paths:
                continue
            fields, header_errors = read_front_matter(path)
            errors.extend(header_errors)
            if fields:
                reports.append(Report(path, fields, kind, archived))
    return reports, errors


def validate_guard(guard: str) -> list[str]:
    if not GUARD.fullmatch(guard):
        return [f"guard has an unsupported pytest selector: {guard!r}"]
    path_text, *nodes = guard.split("::")
    path = ROOT / path_text
    if not path.is_file():
        return [f"guard target does not exist: {guard!r}"]
    try:
        module = ast.parse(path.read_text(encoding="utf-8"), filename=path_text)
    except SyntaxError as error:
        return [f"guard target cannot be parsed: {error}"]
    functions = (ast.FunctionDef, ast.AsyncFunctionDef)
    if len(nodes) == 2:
        classes = [
            item
            for item in module.body
            if isinstance(item, ast.ClassDef) and item.name == nodes[0]
        ]
        exists = any(
            isinstance(item, functions) and item.name == nodes[1]
            for klass in classes
            for item in klass.body
        )
    elif len(nodes) == 1:
        exists = any(
            isinstance(item, functions) and item.name == nodes[0]
            for item in module.body
        )
    else:
        exists = any(
            isinstance(item, functions) and item.name.startswith("test_")
            for item in module.body
        ) or any(
            isinstance(item, ast.ClassDef)
            and item.name.startswith("Test")
            and any(
                isinstance(method, functions) and method.name.startswith("test_")
                for method in item.body
            )
            for item in module.body
        )
    return [] if exists else [f"guard target does not declare a test: {guard!r}"]


def validate_report(report: Report) -> list[str]:
    fields = report.fields
    prefix = report.relative_path
    errors = [
        f"{prefix}: {key} is missing or empty"
        for key in ("summary", "issue", "status", "opened", "verification", "area")
        if not fields.get(key)
    ]
    if not OWN_ISSUE.fullmatch(str(fields.get("issue", ""))):
        errors.append(f"{prefix}: issue must be {REPOSITORY}#<positive integer>")
    if not DATE.fullmatch(str(fields.get("opened", ""))):
        errors.append(f"{prefix}: opened must be an ISO date")

    status = str(fields.get("status", ""))
    if status not in OPEN_STATUSES + CLOSED_STATUSES:
        errors.append(f"{prefix}: unknown status {status!r}")
    if report.archived and status not in CLOSED_STATUSES:
        errors.append(f"{prefix}: archived reports require a closed status")
    if not report.archived and status in CLOSED_STATUSES:
        errors.append(
            f"{prefix}: closed reports belong in resolved_bugs or resolved_proposals"
        )
    closed = str(fields.get("closed", ""))
    if status in CLOSED_STATUSES and not DATE.fullmatch(closed):
        errors.append(f"{prefix}: a closed status requires an ISO closed date")
    if status in OPEN_STATUSES and closed:
        errors.append(f"{prefix}: an open status cannot have a closed date")
    if str(fields.get("verification", "")) not in VERIFICATIONS:
        errors.append(f"{prefix}: unknown verification value")
    area = fields.get("area")
    if not isinstance(area, list) or not area:
        errors.append(f"{prefix}: area must be a non-empty inline list")
    if report.kind == "bug" and fields.get("severity") not in SEVERITIES:
        errors.append(f"{prefix}: bugs require a valid severity")
    for key in ("blocked_by", "supersedes"):
        references = fields.get(key, [])
        if not isinstance(references, list):
            errors.append(f"{prefix}: {key} must be an inline list")
            continue
        for reference in references:
            if not ISSUE.fullmatch(reference):
                errors.append(f"{prefix}: invalid {key} reference {reference!r}")
    if status == "blocked" and not fields.get("blocked_by"):
        errors.append(f"{prefix}: blocked requires at least one blocked_by issue")
    if status == "resolved" and not (fields.get("guard") or fields.get("normative")):
        errors.append(f"{prefix}: resolved requires guard or normative")
    guard = str(fields.get("guard", ""))
    if guard:
        errors.extend(f"{prefix}: {error}" for error in validate_guard(guard))
    return errors


def validate_all() -> tuple[list[Report], list[str]]:
    reports, errors = load_reports()
    for report in reports:
        errors.extend(validate_report(report))
    return reports, errors
