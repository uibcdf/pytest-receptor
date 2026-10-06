"""Consumer dispatch preserves the shared tool's identity and rejection outcome."""

import importlib.util
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "devtools/check_dependency_routes.py"
spec = importlib.util.spec_from_file_location(
    "pytest_receptor_dependency_routes", SCRIPT
)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


@pytest.fixture
def provider(tmp_path):
    root = tmp_path / "provider"
    tool = root / "devtools/scripts/dependency_routes.py"
    tool.parent.mkdir(parents=True)
    tool.write_text(
        "import argparse\n"
        "from pathlib import Path\n"
        "p = argparse.ArgumentParser()\n"
        "p.add_argument('--root', type=Path)\n"
        "p.add_argument('--inventory')\n"
        "a = p.parse_args()\n"
        "assert a.inventory == 'devtools/dependency_routes.toml'\n"
        "print('shared rejection: ' + str(a.root.resolve()))\n"
        "raise SystemExit(1)\n"
    )

    def git(*arguments):
        return subprocess.check_output(["git", *arguments], cwd=root, text=True).strip()

    git("init", "-q")
    git("add", "devtools")
    git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "Reviewed tool",
    )
    return root, git("rev-parse", "HEAD"), tool


def test_different_provider_commit_is_refused(provider):
    root, _, _ = provider
    with pytest.raises(ValueError, match="expected"):
        check.checked_tool(root, "0" * 40)


@pytest.mark.parametrize("change", ["modified", "untracked"])
def test_changed_provider_code_is_refused_before_execution(provider, change):
    root, commit, tool = provider
    if change == "modified":
        tool.write_text("raise SystemExit(0)\n")
    else:
        (tool.parent / "noarch_conda.py").write_text("unreviewed = True\n")
    with pytest.raises(ValueError, match="modified or untracked"):
        check.checked_tool(root, commit)


def test_shared_failure_exit_and_consumer_root_are_retained(provider, tmp_path):
    root, commit, _ = provider
    consumer = tmp_path / "consumer"
    (consumer / "devtools").mkdir(parents=True)
    (consumer / "devtools/dependency_routes.toml").write_text(
        f'[shared_tool]\ncommit = "{commit}"\n'
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCRIPT),
            "--suite-root",
            str(root),
            "--root",
            str(consumer),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert f"shared rejection: {consumer.resolve()}" in result.stdout


def test_dependency_audit_precedes_expensive_tests_and_builds():
    workflows = ROOT / ".github/workflows"
    workflow = (workflows / "tests.yml").read_text()
    for name in ("test", "benchmarks", "packaging"):
        assert re.search(rf"^  {name}:\n    needs: dependency-routes$", workflow, re.M)
    plan = tomllib.loads((ROOT / "devtools/conda-build/release_plan.toml").read_text())
    assert plan["gate_jobs"][".github/workflows/tests.yml"][
        "Dependency and runtime routes"
    ] == ["Check reviewed dependency and runtime routes"]

    release = (workflows / "release.yml").read_text()
    assert release.index(
        "name: Check reviewed dependency and runtime routes"
    ) < release.index("name: Build release artifacts")
    assert release.index(
        "name: Verify exact-tag executed source gates"
    ) < release.index("name: Build release artifacts")
    assert "  publish:\n    name: Publish to PyPI\n    needs: build\n" in release
    archive = release.split("name: Store distributions for the publishing job", 1)[1]
    assert "path: dist/" in archive.split("  publish:", 1)[0]


@pytest.fixture
def release_adapter(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(ROOT / "devtools"))
    spec = importlib.util.spec_from_file_location(
        "receptor_release_gates", ROOT / "devtools/check_release_gates.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    consumer = tmp_path / "consumer"
    for relative in (
        "devtools/dependency_routes.toml",
        "devtools/conda-build/release_plan.toml",
    ):
        destination = consumer / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
    calls = []
    source = "a" * 40
    monkeypatch.setattr(
        module, "checked_tool", lambda root, commit: calls.append(commit)
    )
    monkeypatch.setattr(
        module.subprocess, "check_output", lambda *args, **kwargs: source + "\n"
    )

    def acquire(*arguments):
        calls.append(arguments)
        return [
            {"workflow": path, "candidate_sha": source, "run_id": 123}
            for path in arguments[2]
        ]

    monkeypatch.setattr(module, "load_gate_reader", lambda root: acquire)
    return module, consumer, source, calls


def test_pypi_delegates_exact_source_and_all_executed_job_requirements(release_adapter):
    module, root, source, calls = release_adapter
    proof = module.verify_release_gates(
        root, root, "uibcdf/pytest-receptor", "1.2.1", "test-token"
    )
    plan = tomllib.loads((root / "devtools/conda-build/release_plan.toml").read_text())
    assert calls[-1] == (
        "uibcdf/pytest-receptor",
        source,
        plan["required_workflows"],
        "test-token",
        plan["gate_jobs"],
    )
    assert proof["candidate_sha"] == proof["tag_sha"] == source
    assert proof["provider_commit"] == calls[0]


def test_pypi_rejects_a_tag_for_another_source_before_acquisition(
    release_adapter, monkeypatch
):
    module, root, source, calls = release_adapter
    monkeypatch.setattr(
        module.subprocess,
        "check_output",
        lambda arguments, **kwargs: source if arguments[-1] == "HEAD" else "b" * 40,
    )
    with pytest.raises(ValueError, match="tag differs"):
        module.verify_release_gates(
            root, root, "uibcdf/pytest-receptor", "1.2.1", "test-token"
        )
    assert len(calls) == 1


def test_pypi_rejects_an_unprotected_workflow_before_acquisition(release_adapter):
    module, root, _, calls = release_adapter
    path = root / "devtools/conda-build/release_plan.toml"
    path.write_text(
        'required_workflows = [".github/workflows/tests.yml"]\n[gate_jobs]\n'
    )
    with pytest.raises(ValueError, match="executed-job requirements"):
        module.verify_release_gates(
            root, root, "uibcdf/pytest-receptor", "1.2.1", "test-token"
        )
    assert len(calls) == 1


def test_pypi_retains_shared_gate_rejection(release_adapter, monkeypatch):
    module, root, _, _ = release_adapter

    def reject(*arguments):
        raise ValueError("no successful executed native jobs")

    monkeypatch.setattr(module, "load_gate_reader", lambda root: reject)
    with pytest.raises(ValueError, match="no successful executed native jobs"):
        module.verify_release_gates(
            root, root, "uibcdf/pytest-receptor", "1.2.1", "test-token"
        )
