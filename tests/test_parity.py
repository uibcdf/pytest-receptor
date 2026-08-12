"""Differential semantic parity against plain pytest's JUnit artifact."""

from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from xml.etree import ElementTree

import pytest

from pytest_receptor import read_artifact


@dataclass(frozen=True)
class SemanticCounts:
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    xfailed: int = 0
    xpassed: int = 0

    @property
    def logical_tests(self):
        return sum(
            (
                self.passed,
                self.failed,
                self.errors,
                self.skipped,
                self.xfailed,
                self.xpassed,
            )
        )


SCENARIOS = {
    "green": "def test_a(): assert 1\ndef test_b(): assert 1\n",
    "call_failure": "def test_a(): assert 1\ndef test_b(): assert 0\n",
    "setup_error": (
        "import pytest\n"
        "@pytest.fixture\n"
        "def broken(): raise RuntimeError('setup broke')\n"
        "def test_bad(broken): pass\n"
        "def test_ok(): assert 1\n"
    ),
    "teardown_error": (
        "import pytest\n"
        "@pytest.fixture\n"
        "def broken_after():\n"
        "    yield\n"
        "    raise RuntimeError('teardown broke')\n"
        "def test_bad(broken_after): pass\n"
        "def test_ok(): assert 1\n"
    ),
    "skip": (
        "import pytest\n"
        "@pytest.mark.skip(reason='not available')\n"
        "def test_skip(): pass\n"
        "def test_ok(): assert 1\n"
    ),
    "xfail": (
        "import pytest\n"
        "@pytest.mark.xfail(reason='known defect')\n"
        "def test_expected_failure(): assert 0\n"
        "def test_ok(): assert 1\n"
    ),
    "xpass": (
        "import pytest\n"
        "@pytest.mark.xfail(reason='possibly fixed')\n"
        "def test_unexpected_pass(): assert 1\n"
        "def test_ok(): assert 1\n"
    ),
    "collection_error": "raise RuntimeError('collection broke')\n",
}

_COUNT = re.compile(
    r"\b(\d+) (failed|errors|passed|skipped|xfailed|xpassed|deselected)\b"
)


def _receptor_model(output):
    summary = next(line for line in output.splitlines() if line.strip())
    values = {label: int(count) for count, label in _COUNT.findall(summary)}
    return SemanticCounts(
        passed=values.get("passed", 0),
        failed=values.get("failed", 0),
        errors=values.get("errors", 0),
        skipped=values.get("skipped", 0),
        xfailed=values.get("xfailed", 0),
        xpassed=values.get("xpassed", 0),
    )


def _junit_model(path):
    root = ElementTree.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    assert suite is not None
    tests = int(suite.get("tests", 0))
    failed = int(suite.get("failures", 0))
    errors = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    return {
        "tests": tests,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "passed": tests - failed - errors - skipped,
    }


def _artifact_model(path):
    """Collapse phase evidence to JUnit's one-result-per-logical-test model."""
    artifact = read_artifact(path)
    by_node = {}
    for record in artifact.events:
        if record.type != "phase":
            continue
        event = record.data
        nodeid = event["nodeid"]
        state = by_node.setdefault(
            nodeid, {"error": False, "failed": False, "skipped": False}
        )
        outcome = event["outcome"]
        phase = event["phase"]
        if outcome == "failed" and phase in ("setup", "teardown", "collect"):
            state["error"] = True
        elif outcome == "failed":
            state["failed"] = True
        elif outcome in ("skipped", "xfailed"):
            state["skipped"] = True

    model = {"tests": len(by_node), "failed": 0, "errors": 0, "skipped": 0}
    for state in by_node.values():
        if state["error"]:
            model["errors"] += 1
        elif state["failed"]:
            model["failed"] += 1
        elif state["skipped"]:
            model["skipped"] += 1
    model["passed"] = (
        model["tests"] - model["failed"] - model["errors"] - model["skipped"]
    )
    return model, artifact


@pytest.mark.parametrize("distributed", [False, True], ids=["serial", "xdist"])
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_receptor_has_semantic_parity_with_pytest_and_junit(
    pytester, scenario, distributed
):
    """PR-REL-005: formatting may differ; outcomes and counts may not."""
    if distributed and importlib.util.find_spec("xdist") is None:
        pytest.skip("pytest-xdist is not installed")
    pytester.makepyfile(test_parity=SCENARIOS[scenario])
    junit_path = pytester.path / "plain-pytest.xml"
    artifact_path = pytester.path / "receptor.jsonl"
    mode = ("-n", "2") if distributed else ()

    plain = pytester.runpytest_subprocess("-q", f"--junitxml={junit_path}", *mode)
    receptor = pytester.runpytest_subprocess(
        "--receptor=llm", f"--receptor-events={artifact_path}", *mode
    )

    assert receptor.ret == plain.ret
    artifact_model, artifact = _artifact_model(artifact_path)
    junit = _junit_model(junit_path)
    if scenario == "collection_error" and distributed:
        # xdist asks every worker to collect the module, so JUnit emits the
        # same import error once per worker. Receptor intentionally reports one
        # logical node/cause while retaining both worker observations below.
        assert artifact_model == {
            "tests": 1,
            "failed": 0,
            "errors": 1,
            "skipped": 0,
            "passed": 0,
        }
        collection_events = [
            event.data
            for event in artifact.events
            if event.type == "phase" and event.data["phase"] == "collect"
        ]
        assert len(collection_events) == junit["errors"] == 2
    else:
        assert artifact_model == junit
    # Reader completeness means the integrity-protected final record exists.
    assert artifact.complete is True

    # Keep the user-visible summary independently checked for scenarios where
    # pytest's terminal categories are mutually exclusive. Teardown errors are
    # the exception: pytest reports both a passed call and an error, while
    # JUnit correctly stores one logical test with an error.
    if scenario not in ("teardown_error", "collection_error"):
        got = _receptor_model(receptor.stdout.str())
        assert got.logical_tests == junit["tests"]
        assert got.failed == junit["failed"]
        assert got.errors == junit["errors"]
        assert got.skipped + got.xfailed == junit["skipped"]
        assert got.passed + got.xpassed == junit["passed"]


@pytest.mark.parametrize("distributed", [False, True], ids=["serial", "xdist"])
def test_empty_run_has_parity_with_pytest_and_junit(pytester, distributed):
    """The zero-test edge has no counts to infer from ordinary reports."""
    if distributed and importlib.util.find_spec("xdist") is None:
        pytest.skip("pytest-xdist is not installed")
    junit_path = pytester.path / "plain-pytest.xml"
    mode = ("-n", "2") if distributed else ()
    plain = pytester.runpytest_subprocess("-q", f"--junitxml={junit_path}", *mode)
    receptor = pytester.runpytest_subprocess("--receptor=llm", *mode)

    assert plain.ret == receptor.ret == 5
    assert receptor.stdout.str().lstrip().startswith("NO_TESTS exit=5")
    assert _junit_model(junit_path)["tests"] == 0


@pytest.mark.parametrize("distributed", [False, True], ids=["serial", "xdist"])
def test_maxfail_preserves_executed_prefix_and_marks_run_incomplete(
    pytester, distributed
):
    if distributed and importlib.util.find_spec("xdist") is None:
        pytest.skip("pytest-xdist is not installed")
    pytester.makepyfile(
        test_maxfail="""
        def test_a(): assert False
        def test_b(): assert False
        def test_c(): assert False
        """
    )
    junit_path = pytester.path / "plain-pytest.xml"
    artifact_path = pytester.path / "receptor.jsonl"
    mode = ("-n", "1") if distributed else ()

    plain = pytester.runpytest_subprocess(
        "-q", "--maxfail=1", f"--junitxml={junit_path}", *mode
    )
    receptor = pytester.runpytest_subprocess(
        "--receptor=llm",
        "--maxfail=1",
        f"--receptor-events={artifact_path}",
        *mode,
    )

    expected_exit = (
        pytest.ExitCode.INTERRUPTED if distributed else pytest.ExitCode.TESTS_FAILED
    )
    assert plain.ret == receptor.ret == expected_exit
    model, artifact = _artifact_model(artifact_path)
    assert model == _junit_model(junit_path)
    assert artifact.final is not None
    assert artifact.final.data["complete"] is False
    assert artifact.final.data["stop_reason"].startswith("incomplete")
    assert artifact.final.data["counts"]["executed"] == 1
    assert artifact.final.data["counts"]["not_executed"] == 2


@pytest.mark.parametrize("returncode", [0, 2])
def test_controlled_interruption_is_never_a_complete_pass(pytester, returncode):
    pytester.makepyfile(
        test_interrupt=f"""
        import pytest

        def test_stop():
            pytest.exit('controlled stop', returncode={returncode})

        def test_never_reached():
            assert True
        """
    )
    artifact_path = pytester.path / "receptor.jsonl"

    result = pytester.runpytest_subprocess(
        "--receptor=llm", f"--receptor-events={artifact_path}"
    )

    assert result.ret == returncode
    artifact = read_artifact(artifact_path)
    assert artifact.final is not None
    assert artifact.final.data["complete"] is False
    assert artifact.final.data["counts"]["not_executed"] == 2
    assert "PASS exit=0" not in result.stdout.str()


def test_rerun_parity_keeps_transient_evidence_without_changing_final_result(
    pytester,
):
    pytest.importorskip("pytest_rerunfailures")
    pytester.makepyfile(
        test_flaky="""
        attempts = 0

        def test_flaky():
            global attempts
            attempts += 1
            assert attempts == 2
        """
    )
    junit_path = pytester.path / "plain-pytest.xml"
    artifact_path = pytester.path / "receptor.jsonl"

    plain = pytester.runpytest_subprocess(
        "-q", "--reruns=1", f"--junitxml={junit_path}"
    )
    receptor = pytester.runpytest_subprocess(
        "--receptor=llm",
        "--reruns=1",
        f"--receptor-events={artifact_path}",
    )

    assert plain.ret == receptor.ret == pytest.ExitCode.OK
    model, artifact = _artifact_model(artifact_path)
    assert model == _junit_model(junit_path)
    calls = [
        event.data
        for event in artifact.events
        if event.type == "phase" and event.data["phase"] == "call"
    ]
    assert [(event["attempt"], event["outcome"]) for event in calls] == [
        (1, "rerun"),
        (2, "passed"),
    ]
    assert calls[0]["exception"] is not None
    assert artifact.final is not None
    assert artifact.final.data["counts"]["reruns"] == 1


@pytest.mark.parametrize("distributed", [False, True], ids=["serial", "xdist"])
def test_subtest_parity_preserves_junit_occurrences_and_logical_parent(
    pytester, distributed
):
    pytest.importorskip("pytest_subtests")
    if distributed and importlib.util.find_spec("xdist") is None:
        pytest.skip("pytest-xdist is not installed")
    pytester.makepyfile(
        test_subtests="""
        def test_cases(subtests):
            for case in ('alpha', 'beta'):
                with subtests.test(case=case):
                    assert False, case
        """
    )
    junit_path = pytester.path / "plain-pytest.xml"
    artifact_path = pytester.path / "receptor.jsonl"
    mode = ("-n", "2") if distributed else ()

    plain = pytester.runpytest_subprocess("-q", f"--junitxml={junit_path}", *mode)
    receptor = pytester.runpytest_subprocess(
        "--receptor=llm", f"--receptor-events={artifact_path}", *mode
    )

    assert plain.ret == receptor.ret == pytest.ExitCode.TESTS_FAILED
    junit = _junit_model(junit_path)
    artifact = read_artifact(artifact_path)
    # pytest 9's built-in subtests adds a synthetic failed parent to JUnit;
    # pytest 8 + pytest-subtests may only emit the two occurrences. Both encode
    # the same two subtest failures, but neither is a logical-test count.
    assert junit["failed"] in (2, 3)
    assert artifact.final is not None
    assert artifact.final.data["counts"]["failed"] == 1
    assert artifact.final.data["counts"]["executed"] == 1
    assert artifact.final.data["counts"]["subtests"] == {"failed": 2}
