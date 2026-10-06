"""Run Pytest Receptor's inventory through the pinned shared dependency-route tool.

Use --suite-root for the separately checked out MolSysSuite tool. Its commit
and unmodified script bytes must match the member's reviewed tool pin.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = "devtools/dependency_routes.toml"


def checked_tool(suite_root: Path, commit: str) -> Path:
    """Refuse a changed or dirty provider before executing its shared operation."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("shared dependency tool needs a reviewed full commit")
    suite_root = suite_root.resolve()
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=suite_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if head != commit:
        raise ValueError(f"shared tool checkout is {head}; expected {commit}")
    changed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "devtools"],
        cwd=suite_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if changed:
        raise ValueError("shared tool's devtools inputs are modified or untracked")
    tool = suite_root / "devtools/scripts/dependency_routes.py"
    if not tool.is_file():
        raise ValueError("pinned checkout does not provide dependency_routes.py")
    return tool


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite-root", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        inventory = tomllib.loads((args.root / INVENTORY).read_text())
        tool = checked_tool(args.suite_root, inventory["shared_tool"]["commit"])
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(
            f"Pytest Receptor dependency preflight rejected: {error}", file=sys.stderr
        )
        return 1
    return subprocess.run(
        [
            sys.executable,
            "-B",
            str(tool),
            "--root",
            str(args.root),
            "--inventory",
            INVENTORY,
        ],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
