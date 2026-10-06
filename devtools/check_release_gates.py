"""Require executed exact-tag source gates before a PyPI build.

The component selects required jobs from its maintained release plan. The
accepted shared provider owns native GitHub acquisition and executed-step
verification. This command makes no Conda-coordinate or publication mutation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from check_dependency_routes import INVENTORY, ROOT, checked_tool


def load_gate_reader(suite_root: Path):
    """Load the existing acquisition operation from the checked provider."""
    path = suite_root.resolve() / "devtools/scripts/preflight_conda_release.py"
    sys.path.insert(0, str(suite_root.resolve()))
    spec = importlib.util.spec_from_file_location("suite_source_preflight", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.acquire_gates


def verify_release_gates(root, suite_root, repository, tag, token):
    """Bind the tag to this checkout, then delegate exact native gate checks."""
    if repository != "uibcdf/pytest-receptor" or not re.fullmatch(
        r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", tag
    ):
        raise ValueError("expected this repository and a canonical public version tag")
    inventory = tomllib.loads((root / INVENTORY).read_text())
    commit = inventory["shared_tool"]["commit"]
    checked_tool(suite_root, commit)

    def git(*arguments):
        return subprocess.check_output(["git", *arguments], cwd=root, text=True).strip()

    candidate = git("rev-parse", "HEAD")
    tag_source = git("rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
    if not re.fullmatch(r"[0-9a-f]{40}", candidate) or tag_source != candidate:
        raise ValueError("release tag differs from the immutable checkout source")
    plan = tomllib.loads((root / "devtools/conda-build/release_plan.toml").read_text())
    workflows, jobs = plan["required_workflows"], plan["gate_jobs"]
    if (
        not workflows
        or set(workflows) != set(jobs)
        or any(not jobs[path] for path in workflows)
    ):
        raise ValueError(
            "every required source workflow needs executed-job requirements"
        )
    gates = load_gate_reader(suite_root)(repository, candidate, workflows, token, jobs)
    return {
        "schema": "pytest-receptor.source-gates@1",
        "repository": repository,
        "tag": tag,
        "candidate_sha": candidate,
        "tag_sha": tag_source,
        "provider_commit": commit,
        "gates": gates,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--suite-root", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        proof = verify_release_gates(
            args.root,
            args.suite_root,
            args.repository,
            args.tag,
            os.environ.get("GH_TOKEN", ""),
        )
        args.output.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(f"PyPI source gates rejected: {error}", file=sys.stderr)
        return 1
    print("Exact-tag executed source gates verified; publication remains separate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
