"""Neutral producer contract: no SMonitor import or domain-specific payload."""

from __future__ import annotations

import pytest

from pytest_receptor import read_artifact


@pytest.mark.parametrize("distributed", [False, True])
def test_dummy_producer_correlates_phase_events_and_preserves_namespace(
    pytester, distributed
):
    if distributed:
        pytest.importorskip("xdist")
    pytester.makeconftest(
        """
        from pytest_receptor.extensions import current_context, emit

        def pytest_sessionfinish(session, exitstatus):
            emit(session.config, 'org.example.clock@1', {'kind': 'session'})

        def pytest_runtest_setup(item):
            context = current_context()
            assert context.phase == 'setup'
            emit(item.config, 'org.example.clock@1', {'kind': 'setup'})

        def pytest_runtest_teardown(item):
            context = current_context()
            assert context.phase == 'teardown'
            emit(item.config, 'org.example.clock@1', {'kind': 'teardown'})
        """
    )
    pytester.makepyfile(
        test_dummy="""
        from pytest_receptor.extensions import current_context, emit

        def test_first(pytestconfig):
            assert current_context().phase == 'call'
            assert emit(pytestconfig, 'org.example.clock@1', {'kind': 'call'})

        def test_second(pytestconfig):
            assert emit(pytestconfig, 'org.example.clock@1', {'kind': 'call'})
        """
    )
    args = ["--receptor=llm", "--receptor-events=events.jsonl"]
    if distributed:
        args.extend(("-n", "2"))
    result = pytester.runpytest(*args)

    assert result.ret == pytest.ExitCode.OK
    artifact = read_artifact(pytester.path / "events.jsonl")
    assert artifact.complete and artifact.integrity_valid
    extensions = [event.data for event in artifact.events if event.type == "extension"]
    assert len([event for event in extensions if event["phase"] != "session"]) == 6
    assert any(event["phase"] == "session" and not event["nodeid"] for event in extensions)
    if distributed:
        assert len({
            event["worker_id"] for event in extensions
            if event["phase"] == "session" and event["worker_id"]
        }) == 2
    assert {event["namespace"] for event in extensions} == {"org.example.clock@1"}
    assert {event["payload"]["kind"] for event in extensions} >= {
        "setup", "call", "teardown", "session"
    }
    phases = {
        event.data["event_id"]: event.data
        for event in artifact.events
        if event.type == "phase"
    }
    for event in extensions:
        if event["phase"] == "session":
            assert event["emitted_during"] is None
            continue
        phase = phases[event["emitted_during"]]
        assert (event["nodeid"], event["phase"], event["attempt"]) == (
            phase["nodeid"], phase["phase"], phase["attempt"]
        )
        assert event["worker_id"] == phase["worker_id"]
    assert artifact.final.data["extensions"]["recorded"] == len(extensions)
    assert artifact.final.data["extensions"]["incomplete"] is False


def test_dummy_producer_redacts_and_bounds_without_changing_outcome(pytester):
    pytester.makepyfile(
        test_dummy="""
        from pytest_receptor.extensions import emit

        def test_payload(pytestconfig):
            assert emit(pytestconfig, 'org.example.clock@1',
                        {'token': 'token=abcdefghijklmnop'})
            assert emit(pytestconfig, 'org.example.clock@1',
                        {'too_large': 'x' * 20000}) is None
            assert emit(pytestconfig, 'invalid', {'value': 1}) is None
        """
    )
    result = pytester.runpytest("--receptor=llm", "--receptor-events=events.jsonl")

    assert result.ret == pytest.ExitCode.OK
    serialized = (pytester.path / "events.jsonl").read_text()
    assert "abcdefghijklmnop" not in serialized
    artifact = read_artifact(pytester.path / "events.jsonl")
    extensions = [event.data for event in artifact.events if event.type == "extension"]
    assert len(extensions) == 1
    assert extensions[0]["payload"]["token"] == "token=[REDACTED]"
    assert artifact.final.data["extensions"] == {
        "recorded": 1, "dropped": 2, "incomplete": True
    }


def test_human_profile_leaves_extension_service_inert(pytester):
    pytester.makepyfile(
        test_dummy="""
        from pytest_receptor.extensions import emit

        def test_no_artifact(pytestconfig):
            assert emit(pytestconfig, 'org.example.clock@1', {'kind': 'call'}) is None
        """
    )
    result = pytester.runpytest()
    assert result.ret == pytest.ExitCode.OK
    assert not (pytester.path / "events.jsonl").exists()


def test_dummy_producer_preserves_rerun_attempt(pytester):
    pytest.importorskip("pytest_rerunfailures")
    pytester.makepyfile(
        test_flaky="""
        from pytest_receptor.extensions import emit

        attempt = 0

        def test_retry(pytestconfig):
            global attempt
            attempt += 1
            emit(pytestconfig, 'org.example.clock@1', {'attempt': attempt})
            assert attempt == 2
        """
    )
    result = pytester.runpytest(
        "--receptor=llm", "--receptor-events=events.jsonl", "--reruns", "1"
    )

    assert result.ret == pytest.ExitCode.OK
    artifact = read_artifact(pytester.path / "events.jsonl")
    calls = [
        event.data for event in artifact.events
        if event.type == "extension" and event.data["phase"] == "call"
    ]
    assert [(event["attempt"], event["payload"]["attempt"]) for event in calls] == [
        (1, 1), (2, 2)
    ]


def test_session_event_after_test_does_not_inherit_nodeid(pytester):
    pytester.makeconftest(
        """
        from pytest_receptor.extensions import current_context, emit

        def pytest_sessionfinish(session, exitstatus):
            assert current_context() is None
            emit(session.config, 'org.example.clock@1', {'kind': 'finished'})
        """
    )
    pytester.makepyfile("def test_ok(): assert True")
    result = pytester.runpytest("--receptor=llm", "--receptor-events=events.jsonl")

    assert result.ret == pytest.ExitCode.OK
    artifact = read_artifact(pytester.path / "events.jsonl")
    extensions = [event.data for event in artifact.events if event.type == "extension"]
    assert len(extensions) == 1
    assert extensions[0]["nodeid"] == ""
    assert extensions[0]["phase"] == "session"


def test_worker_loss_keeps_received_extensions_and_marks_gap(pytester):
    pytest.importorskip("xdist")
    pytester.makeconftest(
        """
        from pytest_receptor.extensions import emit

        def pytest_runtest_setup(item):
            emit(item.config, 'org.example.clock@1', {'kind': 'setup'})
        """
    )
    pytester.makepyfile(
        test_worker="""
        import os

        def test_survives():
            assert True

        def test_crashes_worker():
            os._exit(3)
        """
    )
    result = pytester.runpytest(
        "--receptor=llm", "--receptor-events=events.jsonl",
        "-n", "2", "--max-worker-restart=0",
    )

    assert result.ret != pytest.ExitCode.OK
    artifact = read_artifact(pytester.path / "events.jsonl")
    assert artifact.complete and artifact.integrity_valid
    extensions = [event.data for event in artifact.events if event.type == "extension"]
    assert any("test_crashes_worker" in event["nodeid"] for event in extensions)
    assert artifact.final.data["extensions"]["incomplete"] is True


def test_producer_failure_marker_preserves_native_success(pytester):
    pytester.makepyfile(
        test_dummy="""
        from pytest_receptor.extensions import mark_incomplete

        def test_recording_gap(pytestconfig):
            mark_incomplete(pytestconfig)
            assert True
        """
    )
    result = pytester.runpytest("--receptor=llm", "--receptor-events=events.jsonl")

    assert result.ret == pytest.ExitCode.OK
    artifact = read_artifact(pytester.path / "events.jsonl")
    assert artifact.final.data["extensions"] == {
        "recorded": 0, "dropped": 1, "incomplete": True
    }
