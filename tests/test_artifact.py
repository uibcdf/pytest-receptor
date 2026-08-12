"""Contracts for the versioned JSONL artifact and supported reader."""

from __future__ import annotations

import json
import os
import stat

import pytest

from pytest_receptor import (
    ArtifactIntegrityError,
    UnsupportedSchemaError,
    read_artifact,
)
from pytest_receptor.artifact import MIN_MAX_BYTES, SCHEMA, JsonlArtifactWriter


def _start(run_id="run-1"):
    return {"schema": SCHEMA, "type": "session_start", "run_id": run_id}


def _finish(run_id="run-1"):
    return {
        "schema": SCHEMA,
        "type": "session_finish",
        "run_id": run_id,
        "exitstatus": 0,
        "complete": True,
    }


def test_reader_preserves_unknown_events_and_validates_finalization(tmp_path):
    path = tmp_path / "events.jsonl"
    writer = JsonlArtifactWriter(path, _start())
    writer.write(
        {
            "schema": SCHEMA,
            "type": "org.example.observation",
            "payload": {"future": "value"},
        }
    )
    writer.finalize(_finish())

    artifact = read_artifact(path)

    assert artifact.complete is True
    assert artifact.integrity_valid is True
    assert artifact.events[0].known is False
    assert artifact.events[0].data["payload"] == {"future": "value"}


def test_reader_marks_stream_without_final_record_incomplete(tmp_path):
    path = tmp_path / "events.jsonl"
    writer = JsonlArtifactWriter(path, _start())
    writer.write({"schema": SCHEMA, "type": "future", "value": "kept"})
    writer.close()

    artifact = read_artifact(path)

    assert artifact.complete is False
    assert artifact.integrity_valid is None
    assert artifact.issue == "missing session_finish"
    assert artifact.events[0].data["value"] == "kept"


def test_reader_marks_truncated_tail_incomplete(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(json.dumps(_start()) + '\n{"schema":')

    artifact = read_artifact(path)

    assert artifact.complete is False
    assert artifact.issue == "truncated final record"


def test_reader_rejects_unsupported_major(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"schema":"pytest-receptor.events@2","type":"session_start"}\n')

    with pytest.raises(UnsupportedSchemaError, match="unsupported schema major 2"):
        read_artifact(path)


def test_reader_detects_changes_to_finalized_evidence(tmp_path):
    path = tmp_path / "events.jsonl"
    writer = JsonlArtifactWriter(path, _start())
    writer.finalize(_finish())
    path.write_bytes(path.read_bytes().replace(b'"run-1"', b'"run-X"', 1))

    with pytest.raises(ArtifactIntegrityError, match="digest mismatch"):
        read_artifact(path)


def test_writer_creates_owner_only_file_and_refuses_symlink(tmp_path):
    target = tmp_path / "target"
    target.write_text("do not replace")
    link = tmp_path / "events.jsonl"
    link.symlink_to(target)

    with pytest.raises(Exception, match="refusing symlink"):
        JsonlArtifactWriter(link, _start())
    assert target.read_text() == "do not replace"

    safe = tmp_path / "safe.jsonl"
    writer = JsonlArtifactWriter(safe, _start())
    writer.close()
    assert stat.S_IMODE(os.stat(safe).st_mode) == 0o600


def test_writer_caps_size_and_audits_dropped_records(tmp_path):
    path = tmp_path / "bounded.jsonl"
    writer = JsonlArtifactWriter(path, _start(), max_bytes=MIN_MAX_BYTES)

    assert (
        writer.write(
            {
                "schema": SCHEMA,
                "type": "future",
                "payload": "x" * MIN_MAX_BYTES,
            }
        )
        is False
    )
    assert writer.write({"schema": SCHEMA, "type": "future"}) is False
    writer.finalize(_finish())

    assert path.stat().st_size <= MIN_MAX_BYTES
    artifact = read_artifact(path)
    assert artifact.complete is True
    assert [event.type for event in artifact.events] == ["evidence_limit"]
    assert artifact.events[0].known is True
    assert artifact.final is not None
    assert artifact.final.data["artifact_policy"] == {
        "max_bytes": MIN_MAX_BYTES,
        "truncated": True,
        "dropped_records": 2,
    }


def test_events_size_limit_has_a_safe_minimum(pytester):
    result = pytester.runpytest(
        "--receptor=llm",
        "--receptor-events=events.jsonl",
        "--receptor-events-max-bytes=1024",
    )

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(
        ["*--receptor-events-max-bytes must be at least 65536*"]
    )
    assert not (pytester.path / "events.jsonl").exists()


def test_events_option_requires_collecting_profile(pytester):
    result = pytester.runpytest("--receptor-events=events.jsonl")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(
        ["*--receptor-events requires --receptor=llm or --receptor=ci*"]
    )
    assert not (pytester.path / "events.jsonl").exists()


def test_unavailable_destination_warns_without_changing_pytest_result(pytester):
    pytester.makepyfile("def test_ok(): assert True")

    result = pytester.runpytest(
        "--receptor=llm", "--receptor-events=missing/events.jsonl"
    )

    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(["PASS exit=0 | 1 passed | *"])
    result.stderr.fnmatch_lines(["receptor artifact: unavailable: *"])


@pytest.mark.parametrize("distributed", [False, True])
def test_artifact_preserves_subtest_identity(pytester, distributed):
    pytest.importorskip("pytest_subtests")
    pytester.makepyfile(
        test_subtests="""
        def test_cases(subtests):
            for case in ("alpha", "beta"):
                with subtests.test(msg="case check", case=case):
                    assert case == "neither"
        """
    )
    args = ["--receptor=llm", "--receptor-events=events.jsonl"]
    if distributed:
        pytest.importorskip("xdist")
        args.extend(("-n", "2"))

    result = pytester.runpytest(*args)

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    artifact = read_artifact(pytester.path / "events.jsonl")
    subtests = [
        event.data["subtest"]
        for event in artifact.events
        if event.type == "phase" and event.data.get("subtest") is not None
    ]
    assert [subtest["index"] for subtest in subtests] == [1, 2]
    assert [subtest["description"] for subtest in subtests] == [
        "[case check] (case='alpha')",
        "[case check] (case='beta')",
    ]
    assert artifact.final is not None
    assert artifact.final.data["counts"]["failed"] == 1
    assert artifact.final.data["counts"]["subtests"] == {"failed": 2}


@pytest.mark.parametrize("distributed", [False, True])
def test_pytest_writes_readable_normalized_artifact(pytester, distributed):
    pytester.makepyfile(
        test_events="""
        import warnings

        def test_ok():
            warnings.warn("token=abcdefghijklmnop")

        def test_bad():
            print("secret=abcdefghijklmnop")
            raise LookupError("missing π")
        """
    )
    args = ["--receptor=llm", "--receptor-events=events.jsonl"]
    if distributed:
        pytest.importorskip("xdist")
        args.extend(("-n", "2"))

    result = pytester.runpytest(*args)

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    artifact = read_artifact(pytester.path / "events.jsonl")
    assert artifact.complete is True
    final = artifact.final
    assert final is not None
    assert final.data["exitstatus"] == 1
    assert final.data["counts"]["executed"] == 2
    assert final.data["counts"]["not_executed"] == 0
    assert final.data["counts"]["skipped"] == 0
    failures = [
        record.data
        for record in artifact.events
        if record.type == "phase" and record.data.get("exception")
    ]
    assert len(failures) == 1
    assert failures[0]["exception"]["type_name"] == "LookupError"
    assert failures[0]["exception"]["qualified_type"] == "builtins.LookupError"
    assert failures[0]["exception"]["type_source"] == "structured"
    serialized = (pytester.path / "events.jsonl").read_text()
    assert "abcdefghijklmnop" not in serialized
    assert "[REDACTED]" in serialized


def test_artifact_preserves_failed_rerun_attempt(pytester):
    pytest.importorskip("pytest_rerunfailures")
    pytester.makepyfile(
        test_flaky="""
        attempts = 0

        def test_eventually_passes():
            global attempts
            attempts += 1
            assert attempts == 2, "first attempt failed"
        """
    )

    result = pytester.runpytest(
        "--receptor=llm", "--receptor-events=events.jsonl", "--reruns", "1"
    )

    assert result.ret == pytest.ExitCode.OK
    assert result.stdout.str().lstrip().startswith("PASS exit=0")
    artifact = read_artifact(pytester.path / "events.jsonl")
    calls = [
        event.data
        for event in artifact.events
        if event.type == "phase" and event.data["phase"] == "call"
    ]
    assert [(event["attempt"], event["outcome"]) for event in calls] == [
        (1, "rerun"),
        (2, "passed"),
    ]
    assert calls[0]["exception"]["type_name"] == "AssertionError"
    assert calls[1]["exception"] is None
    assert artifact.final is not None
    assert artifact.final.data["counts"]["passed"] == 1
    assert artifact.final.data["counts"]["reruns"] == 1


def test_root_cause_fingerprint_is_stable_across_serial_and_xdist(pytester):
    pytest.importorskip("xdist")
    pytester.makepyfile(
        test_failure="""
        def test_a(): raise ValueError('variant alpha')
        def test_b(): raise ValueError('variant beta')
        """
    )

    serial = pytester.runpytest("--receptor=llm", "--receptor-events=serial.jsonl")
    distributed = pytester.runpytest(
        "--receptor=llm", "--receptor-events=xdist.jsonl", "-n", "2"
    )

    assert serial.ret == distributed.ret == pytest.ExitCode.TESTS_FAILED
    serial_final = read_artifact(pytester.path / "serial.jsonl").final
    xdist_final = read_artifact(pytester.path / "xdist.jsonl").final
    assert serial_final is not None
    assert xdist_final is not None
    serial_groups = [
        event.data
        for event in read_artifact(pytester.path / "serial.jsonl").events
        if event.type == "root_cause"
    ]
    xdist_groups = [
        event.data
        for event in read_artifact(pytester.path / "xdist.jsonl").events
        if event.type == "root_cause"
    ]
    assert [group["fingerprint"] for group in serial_groups] == [
        group["fingerprint"] for group in xdist_groups
    ]
    assert all(group["fingerprint"].startswith("sha256:") for group in serial_groups)
