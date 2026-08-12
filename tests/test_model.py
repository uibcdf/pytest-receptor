"""Unit contracts for the normalized evidence boundary."""

from _pytest.reports import (
    TestReport,
    pytest_report_from_serializable,
    pytest_report_to_serializable,
)

from pytest_receptor.model import (
    CapturedSection,
    ExceptionEvidence,
    PhaseEvent,
    SessionEvidence,
    SubtestIdentity,
)


def _phase(model, nodeid, phase, outcome, **extra):
    model.add_phase(PhaseEvent(model.next_sequence(), nodeid, phase, outcome, **extra))


def test_session_evidence_keeps_phase_and_logical_outcomes_separate():
    model = SessionEvidence(collected=3)
    _phase(model, "test_a.py::test_ok", "call", "passed")
    _phase(model, "test_a.py::test_ok", "teardown", "passed")
    _phase(model, "test_a.py::test_error", "setup", "failed")
    _phase(model, "test_a.py::test_error", "teardown", "passed")
    _phase(model, "test_a.py::test_skip", "setup", "skipped", reason="GPU")
    _phase(model, "test_a.py::test_skip", "teardown", "passed")

    assert model.outcomes == {
        "test_a.py::test_ok": "passed",
        "test_a.py::test_skip": "skipped",
    }
    assert model.errors == {"test_a.py::test_error"}
    assert model.executed == 3
    assert model.finished == 3
    assert model.skipped == {"test_a.py::test_skip": "GPU"}


def test_failure_preserves_all_captured_sections_and_type_provenance():
    model = SessionEvidence()
    exception = ExceptionEvidence(
        type_name="DomainError",
        qualified_type="package.errors.DomainError",
        type_source="structured",
        message="bad value",
        location="test_domain.py:7",
    )
    sections = (
        CapturedSection("Captured stdout call", "stdout", "hello"),
        CapturedSection("plugin diagnostics", "other", "opaque evidence"),
    )
    _phase(
        model,
        "test_domain.py::test_value",
        "call",
        "failed",
        exception=exception,
        sections=sections,
    )

    failure = model.failures[0]
    assert failure.exception == exception
    assert failure.sections == sections
    assert model.outcomes == {"test_domain.py::test_value": "failed"}


def test_attempt_identity_follows_setup_cycles_not_subtest_reports():
    model = SessionEvidence()

    assert model.attempt_for("test_a.py::test_value", "setup") == 1
    assert model.attempt_for("test_a.py::test_value", "call") == 1
    assert model.attempt_for("test_a.py::test_value", "call") == 1
    assert model.attempt_for("test_a.py::test_value", "teardown") == 1
    assert model.attempt_for("test_a.py::test_value", "setup") == 2
    assert model.attempt_for("test_a.py::test_value", "call") == 2
    assert model.attempt_for("test_a.py::test_other", "call") == 1


def test_subtest_outcomes_do_not_replace_parent_logical_outcome():
    model = SessionEvidence()
    subtest = SubtestIdentity(1, "(case='optional')")
    _phase(
        model,
        "test_a.py::test_cases",
        "call",
        "skipped",
        subtest=subtest,
        reason="optional",
    )
    _phase(model, "test_a.py::test_cases", "call", "passed")

    assert model.outcomes == {"test_a.py::test_cases": "passed"}
    assert model.skipped == {}
    assert model.subtest_counts == {"skipped": 1}


def test_structured_exception_identity_survives_pytest_xdist_round_trip():
    report = TestReport(
        nodeid="test_domain.py::test_value",
        location=("test_domain.py", 6, "test_value"),
        keywords={},
        outcome="failed",
        longrepr="DomainError: bad value",
        when="call",
        receptor_exception_type="DomainError",
        receptor_exception_qualified_type="package.errors.DomainError",
        receptor_exception_type_source="structured",
    )

    restored = pytest_report_from_serializable(pytest_report_to_serializable(report))

    assert restored is not None
    assert restored.receptor_exception_type == "DomainError"
    assert restored.receptor_exception_qualified_type == "package.errors.DomainError"
    assert restored.receptor_exception_type_source == "structured"
