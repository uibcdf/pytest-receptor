"""Reject distributions that do not exactly match the release tag."""

from __future__ import annotations

import argparse
import email
from pathlib import Path
from zipfile import ZipFile

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.utils import (
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)

# The supported interpreter range, compared as a version set rather than a
# string: packaging serializes an equivalent `SpecifierSet` in whatever order
# it likes (26.2 emits `<3.14,>=3.11`), so an exact-text match rejected a wheel
# whose constraint was in fact identical.
REQUIRED_PYTHON = SpecifierSet(">=3.11,<3.14")


def validate_release(dist: Path, tag: str) -> str:
    expected = tag.removeprefix("v")
    if not expected or "+" in expected:
        raise ValueError(f"release tag is not a public version: {tag}")

    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError("expected exactly one wheel and one .tar.gz sdist")

    wheel_name, wheel_version, _build, _tags = parse_wheel_filename(wheels[0].name)
    sdist_name, sdist_version = parse_sdist_filename(sdists[0].name)
    expected_name = canonicalize_name("pytest-receptor")
    if wheel_name != expected_name or sdist_name != expected_name:
        raise ValueError(
            f"unexpected project names: wheel={wheel_name}, sdist={sdist_name}"
        )
    versions = {str(wheel_version), str(sdist_version)}
    if versions != {expected}:
        raise ValueError(
            f"distribution versions {sorted(versions)} do not match tag {tag}"
        )
    with ZipFile(wheels[0]) as archive:
        metadata_path = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        metadata = email.message_from_bytes(archive.read(metadata_path))
    requires_python = metadata.get("Requires-Python")
    try:
        declared = SpecifierSet(requires_python) if requires_python else None
    except InvalidSpecifier:
        declared = None
    if declared != REQUIRED_PYTHON:
        raise ValueError(
            "release must support exactly Python 3.11-3.13; got "
            f"Requires-Python: {requires_python}"
        )
    return expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    version = validate_release(args.dist, args.tag)
    print(f"release artifacts verified: pytest-receptor {version}")


if __name__ == "__main__":
    main()
