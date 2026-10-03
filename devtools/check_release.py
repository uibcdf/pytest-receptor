"""Reject distributions that do not exactly match the release tag."""

from __future__ import annotations

import argparse
import ast
import email
import tarfile
import tomllib
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
# it likes (26.2 emits `<3.15,>=3.11`), so an exact-text match rejected a wheel
# whose constraint was in fact identical.
REQUIRED_PYTHON = SpecifierSet(">=3.11,<3.15")
ROOT = Path(__file__).resolve().parents[1]


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
            "release must support exactly Python 3.11-3.14; got "
            f"Requires-Python: {requires_python}"
        )
    return expected


def validate_runtime_payload(dist: Path, version: str) -> None:
    """Reject missing resources or a stale version in either PyPI archive."""
    inventory = tomllib.loads(
        (ROOT / "devtools/conda-build/resources.toml").read_text()
    )
    required = [
        name.removeprefix("site-packages/") for name in inventory["required_paths"]
    ]
    version_file = inventory["version_file"].removeprefix("site-packages/")

    def check_payload(read, route):
        for name in required:
            try:
                contents = read(name)
            except (KeyError, FileNotFoundError) as error:
                raise ValueError(
                    f"{route} is missing runtime resource {name}"
                ) from error
            if name == version_file:
                values = [
                    node.value.value
                    for node in ast.parse(contents).body
                    if isinstance(node, ast.Assign)
                    and any(
                        isinstance(target, ast.Name) and target.id == "__version__"
                        for target in node.targets
                    )
                    and isinstance(node.value, ast.Constant)
                ]
                if values != [version]:
                    raise ValueError(
                        f"{route} embedded version does not match {version}"
                    )
            elif contents != (ROOT / name).read_bytes():
                raise ValueError(
                    f"{route} runtime resource differs from source: {name}"
                )

    wheel = next(dist.glob("*.whl"))
    with ZipFile(wheel) as archive:
        check_payload(archive.read, "wheel")
    sdist = next(dist.glob("*.tar.gz"))
    prefix = sdist.name.removesuffix(".tar.gz")
    with tarfile.open(sdist, "r:gz") as archive:

        def read(name):
            member = archive.getmember(f"{prefix}/{name}")
            if not member.isfile() or member.size > 1024 * 1024:
                raise ValueError(
                    f"sdist resource is not a bounded regular file: {name}"
                )
            with archive.extractfile(member) as stream:
                return stream.read()

        check_payload(read, "sdist")
        metadata = email.message_from_bytes(read("PKG-INFO"))
        if metadata.get("Version") != version:
            raise ValueError("sdist metadata version does not match the tag")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    version = validate_release(args.dist, args.tag)
    validate_runtime_payload(args.dist, version)
    print(f"release artifacts verified: pytest-receptor {version}")


if __name__ == "__main__":
    main()
