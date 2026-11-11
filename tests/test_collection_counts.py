"""Collection diagnostics never count as executed test items (#46)."""

import pytest

from pytest_receptor import read_artifact
from pytest_receptor.model import PhaseEvent, SessionEvidence


def test_collection_errors_do_not_enter_runtime_outcomes():
    evidence = SessionEvidence(collected=1)
    for sequence in (1, 2):
        evidence.add_phase(PhaseEvent(sequence, "test_bad.py", "collection", "failed"))
    evidence.add_phase(PhaseEvent(3, "test_ok.py::test_ok", "call", "passed"))
    assert evidence.executed == 1
    assert evidence.outcomes == {"test_ok.py::test_ok": "passed"}
    assert evidence.collection_errors == {"test_bad.py"}
    assert evidence.errors == set()
    assert len(evidence.phases) == 3


@pytest.mark.parametrize(
    "bad_source", ["def test_bad(: pass", "import absent_46_module"]
)
def test_collection_failure_with_no_items_matches_native_counts(pytester, bad_source):
    pytester.makepyfile(test_bad=bad_source)
    native = pytester.runpytest("--receptor=human", "-x")
    native.assert_outcomes(errors=1)
    compact = pytester.runpytest(
        "--receptor=llm", "--receptor-events=events.jsonl", "-x"
    )
    assert compact.ret == native.ret == 2
    final = read_artifact(pytester.path / "events.jsonl").final.data
    assert final["counts"]["collected"] == final["counts"]["executed"] == 0
    assert final["counts"]["failed"] == 0
    assert final["counts"]["errors"] == 1
    compact.stdout.fnmatch_lines(["COLLECTION_ERROR exit=2 | 1 errors | *"])


@pytest.mark.parametrize(
    "bad_source", ["def test_bad(: pass", "import absent_46_module"]
)
@pytest.mark.parametrize(
    "options,executed,failed,exitstatus",
    [
        ([], 0, 0, 2),
        (["-x"], 0, 0, 2),
        (["--maxfail=1"], 0, 0, 2),
        (["--collect-only"], 0, 0, 2),
        (["--continue-on-collection-errors"], 2, 1, 1),
    ],
)
def test_collection_counts_match_phase_evidence(
    pytester, bad_source, options, executed, failed, exitstatus
):
    pytester.makepyfile(
        test_a_valid="def test_ok(): pass\ndef test_fail(): assert False",
        test_z_bad=bad_source,
    )
    result = pytester.runpytest(
        "--receptor=llm", "--receptor-events=events.jsonl", *options
    )
    assert result.ret == exitstatus
    artifact = read_artifact(pytester.path / "events.jsonl")
    assert artifact.complete and artifact.integrity_valid
    counts = artifact.final.data["counts"]
    assert counts["executed"] == executed
    assert counts["failed"] == failed
    assert counts["errors"] == 1
    assert counts["not_executed"] == max(counts["collected"] - executed, 0)
    assert counts["executed"] <= counts["collected"]
    summary = next(line for line in result.stdout.lines if " exit=" in line)
    assert "1 errors" in summary
    assert f"{failed} failed" in summary if failed else "failed" not in summary
    assert "| 1 collector | collect" in result.stdout.str()
    runtime = {
        record.data["nodeid"]
        for record in artifact.events
        if record.type == "phase"
        and record.data["phase"] not in ("collect", "collection")
    }
    assert len(runtime) == executed


def test_successful_collection_only_keeps_execution_incomplete(pytester):
    pytester.makepyfile("def test_ok(): pass")
    result = pytester.runpytest(
        "--receptor=llm", "--receptor-events=events.jsonl", "--collect-only"
    )
    assert result.ret == 0
    artifact = read_artifact(pytester.path / "events.jsonl")
    assert artifact.final.data["counts"]["collected"] == 1
    assert artifact.final.data["counts"]["executed"] == 0
    assert artifact.final.data["complete"] is False
    assert any(line.startswith("INCOMPLETE exit=0") for line in result.stdout.lines)
    assert "collection only: 1 collected, 0 executed" in result.stdout.str()


@pytest.mark.parametrize(
    "bad_source", ["def test_bad(: pass", "import absent_46_module"]
)
def test_xdist_collection_error_is_deduplicated_without_executing_it(
    pytester, bad_source
):
    pytest.importorskip("xdist")
    pytester.makepyfile(
        test_a_valid="def test_ok(): pass\ndef test_fail(): assert False",
        test_z_bad=bad_source,
    )
    result = pytester.runpytest(
        "--receptor=llm", "--receptor-events=events.jsonl", "-n", "2"
    )
    assert result.ret == 1
    counts = read_artifact(pytester.path / "events.jsonl").final.data["counts"]
    assert counts["executed"] == 2
    assert counts["collected"] == 2
    assert counts["failed"] == 1
    assert counts["errors"] == 1
    assert "1 collector | collect" in result.stdout.str()
