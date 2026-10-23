"""Owned runtime stream lifetimes and nonfatal cleanup diagnostics (#43)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from pytest_receptor import extensions, read_artifact
from pytest_receptor.artifact import SCHEMA, ArtifactError, JsonlArtifactWriter
from pytest_receptor.plugin import ReceptorPlugin


def stats_plugin():
    reporter = SimpleNamespace(_tw=object())
    plugin = object.__new__(ReceptorPlugin)
    plugin.config = SimpleNamespace(
        pluginmanager=SimpleNamespace(getplugin=lambda _name: reporter)
    )
    plugin._baseline = None
    plugin._terminal = None
    return plugin, reporter


@pytest.mark.parametrize("failed_writer", [1, 2])
def test_failed_stats_setup_closes_and_removes_owned_baseline(tmp_path, failed_writer):
    plugin, reporter = stats_plugin()
    borrowed = reporter._tw
    handles = []
    original = tempfile.NamedTemporaryFile

    def create(*args, **kwargs):
        handle = original(*args, dir=tmp_path, **kwargs)
        handles.append(handle)
        return handle

    writers = 0

    def writer(*_args):
        nonlocal writers
        writers += 1
        if writers == failed_writer:
            raise RuntimeError("controlled writer setup failure")
        return object()

    try:
        with (
            patch("tempfile.NamedTemporaryFile", side_effect=create),
            patch("_pytest.config.create_terminal_writer", side_effect=writer),
        ):
            plugin.start_baseline_capture()
        assert len(handles) == 1
        assert handles[0].closed
        assert not Path(handles[0].name).exists()
        assert plugin._baseline is None
        assert plugin._terminal is None
        assert reporter._tw is borrowed
    finally:
        for handle in handles:
            handle.close()


@pytest.mark.parametrize("read_fails", [False, True])
@pytest.mark.parametrize("remove_fails", [False, True])
def test_stats_read_cleans_scratch_and_reports_removal_failure(
    tmp_path, capsys, read_fails, remove_fails
):
    plugin, _reporter = stats_plugin()
    sentinel = tmp_path / "caller.txt"
    sentinel.write_text("caller evidence")
    handle = tempfile.NamedTemporaryFile("w+", dir=tmp_path, delete=False)
    handle.write("controlled baseline")
    plugin._baseline = handle
    path = Path(handle.name)
    original_unlink, original_read = Path.unlink, Path.read_text

    def unlink(target, *args, **kwargs):
        if target == path and remove_fails:
            raise PermissionError("controlled removal failure")
        return original_unlink(target, *args, **kwargs)

    def read(target, *args, **kwargs):
        if target == path and read_fails:
            raise OSError("controlled read failure")
        return original_read(target, *args, **kwargs)

    with patch.object(Path, "unlink", unlink), patch.object(Path, "read_text", read):
        result = plugin._read_baseline()

    assert result == (None if read_fails else "controlled baseline")
    assert handle.closed and plugin._baseline is None
    assert path.exists() == remove_fails
    assert sentinel.read_text() == "caller evidence"
    diagnostic = capsys.readouterr().err
    if remove_fails:
        assert "receptor resource:" in diagnostic
        assert "controlled removal failure" in diagnostic
        assert str(path) in diagnostic
    else:
        assert diagnostic == ""


def test_stats_close_failure_is_visible_and_still_removes_owned_file(tmp_path, capsys):
    plugin, _reporter = stats_plugin()
    handle = tempfile.NamedTemporaryFile("w+", dir=tmp_path, delete=False)
    handle.write("controlled baseline")
    path = Path(handle.name)
    plugin._baseline = CloseFailure(handle)
    assert plugin._read_baseline() == "controlled baseline"
    assert handle.closed and not path.exists()
    assert "controlled artifact close failure" in capsys.readouterr().err


def test_cached_report_removal_failure_is_visible_without_deleting_caller_files(
    tmp_path, capsys
):
    plugin, _reporter = stats_plugin()
    plugin.stats = True
    plugin._is_worker = False
    plugin._start_artifact = lambda: None
    plugin.config.cache = SimpleNamespace(mkdir=lambda _name: tmp_path)
    cached = tmp_path / "last-run.txt"
    cached.write_text("PASS exit=0 | previous run\n")
    with patch.object(
        Path, "unlink", side_effect=PermissionError("controlled cache removal failure")
    ):
        try:
            plugin.pytest_sessionstart(None)
        finally:
            extensions._CURRENT.reset(plugin._session_context_token)
    assert cached.read_text() == "PASS exit=0 | previous run\n"
    diagnostic = capsys.readouterr().err
    assert "receptor resource:" in diagnostic
    assert "controlled cache removal failure" in diagnostic


@pytest.mark.parametrize("failed", [False, True])
def test_stats_cleanup_warning_preserves_real_pytest_exit(pytester, failed):
    baseline_dir = pytester.mkdir("baselines")
    sentinel = baseline_dir / "caller.txt"
    sentinel.write_text("caller evidence")
    pytester.makeconftest(
        "import tempfile\nfrom pathlib import Path\n"
        f"tempfile.tempdir = {str(baseline_dir)!r}\n"
        "original_unlink = Path.unlink\n"
        "def unlink(self, *args, **kwargs):\n"
        "    if self.name.startswith('pytest-receptor-baseline-'):\n"
        "        raise PermissionError('controlled baseline removal failure')\n"
        "    return original_unlink(self, *args, **kwargs)\n"
        "Path.unlink = unlink\n"
    )
    pytester.makepyfile(f"def test_value(): assert {not failed}\n")
    result = pytester.runpytest_subprocess("--receptor=llm", "--receptor-stats")
    assert result.ret == int(failed)
    result.stdout.fnmatch_lines([f"{'FAIL' if failed else 'PASS'} exit={int(failed)}*"])
    assert "controlled baseline removal failure" in result.stderr.str()
    assert "receptor resource:" in result.stderr.str()
    assert sentinel.read_text() == "caller evidence"
    assert len(list(baseline_dir.glob("pytest-receptor-baseline-*.log"))) == 1


class CloseFailure:
    def __init__(self, handle):
        self.handle = handle

    def __getattr__(self, name):
        return getattr(self.handle, name)

    def close(self):
        self.handle.close()
        raise OSError("controlled artifact close failure")


def test_artifact_close_exposes_error_and_preserves_caller_output(tmp_path):
    path = tmp_path / "events.jsonl"
    writer = JsonlArtifactWriter(path, {"schema": SCHEMA, "type": "session_start"})
    handle = writer._handle
    writer._handle = CloseFailure(handle)
    with pytest.raises(ArtifactError, match="controlled artifact close failure"):
        writer.close()
    assert handle.closed
    assert path.exists()


def test_artifact_write_failure_retains_primary_and_close_errors(tmp_path):
    path = tmp_path / "partial.jsonl"
    writer = JsonlArtifactWriter(path, {"schema": SCHEMA, "type": "session_start"})
    handle = writer._handle

    class WriteCloseFailure(CloseFailure):
        def write(self, _payload):
            raise OSError("controlled primary write failure")

    writer._handle = WriteCloseFailure(handle)
    with pytest.raises(ArtifactError) as error:
        writer.write({"type": "controlled"})
    assert "controlled primary write failure" in str(error.value)
    assert "controlled artifact close failure" in str(error.value)
    assert handle.closed and path.exists()


def test_failed_artifact_constructor_closes_partial_output(tmp_path):
    handles = []

    def fail(writer, _record):
        handles.append(writer._handle)
        raise ArtifactError("controlled initial write failure")

    path = tmp_path / "partial.jsonl"
    with (
        patch.object(JsonlArtifactWriter, "write", fail),
        pytest.raises(ArtifactError, match="controlled initial write failure"),
    ):
        JsonlArtifactWriter(path, {})
    assert len(handles) == 1 and handles[0].closed
    assert path.exists(), "partial caller output is retained, not rolled back"


def test_failed_artifact_fdopen_closes_raw_descriptor(tmp_path):
    import os

    descriptors = []

    def fail(descriptor, *_args):
        descriptors.append(descriptor)
        raise OSError("controlled fdopen failure")

    with (
        patch("os.fdopen", side_effect=fail),
        pytest.raises(ArtifactError, match="controlled fdopen failure"),
    ):
        JsonlArtifactWriter(tmp_path / "partial.jsonl", {})
    assert len(descriptors) == 1
    try:
        with pytest.raises(OSError):
            os.fstat(descriptors[0])
    finally:
        try:
            os.fstat(descriptors[0])
        except OSError:
            pass
        else:
            os.close(descriptors[0])


def test_failed_artifact_finalization_closes_partial_output(tmp_path):
    path = tmp_path / "partial.jsonl"
    writer = JsonlArtifactWriter(path, {"schema": SCHEMA, "type": "session_start"})
    handle = writer._handle
    with pytest.raises(ArtifactError, match="final record exceeds"):
        writer.finalize({"payload": "x" * writer.max_bytes})
    assert handle.closed
    assert path.exists()
    assert read_artifact(path).complete is False


@pytest.mark.parametrize("stage", ["constructor", "finalization"])
def test_cleanup_failure_cannot_replace_artifact_interrupt(tmp_path, stage):
    path = tmp_path / "partial.jsonl"
    interrupt = KeyboardInterrupt("controlled stop")
    handles = []

    def fail(writer, _record):
        handles.append(writer._handle)
        writer._handle = CloseFailure(writer._handle)
        raise interrupt

    if stage == "constructor":
        with (
            patch.object(JsonlArtifactWriter, "write", fail),
            pytest.raises(KeyboardInterrupt) as error,
        ):
            JsonlArtifactWriter(path, {})
    else:
        writer = JsonlArtifactWriter(path, {"schema": SCHEMA, "type": "session_start"})
        handles.append(writer._handle)
        writer._handle = CloseFailure(writer._handle)
        with (
            patch("pytest_receptor.artifact._encode_record", side_effect=interrupt),
            pytest.raises(KeyboardInterrupt) as error,
        ):
            writer.finalize({})
    assert error.value is interrupt
    assert any(
        "controlled artifact close failure" in note for note in interrupt.__notes__
    )
    assert handles[0].closed and path.exists()


@pytest.mark.parametrize("exitstatus", [0, 1, 3])
def test_artifact_cleanup_warning_preserves_real_pytest_exit(pytester, exitstatus):
    pytester.makeconftest(
        "import pytest\n"
        "from pytest_receptor.artifact import JsonlArtifactWriter\n"
        "original_init = JsonlArtifactWriter.__init__\n"
        "class CloseFailure:\n"
        "    def __init__(self, handle): self.handle = handle\n"
        "    def __getattr__(self, name): return getattr(self.handle, name)\n"
        "    def close(self):\n"
        "        self.handle.close()\n"
        "        raise OSError('controlled artifact close failure')\n"
        "def init(self, *args, **kwargs):\n"
        "    original_init(self, *args, **kwargs)\n"
        "    self._handle = CloseFailure(self._handle)\n"
        "JsonlArtifactWriter.__init__ = init\n"
        + (
            "@pytest.hookimpl(tryfirst=True)\n"
            "def pytest_sessionfinish():\n"
            "    raise RuntimeError('controlled session failure')\n"
            if exitstatus == 3
            else ""
        )
    )
    pytester.makepyfile(f"def test_value(): assert {exitstatus != 1}\n")
    native = pytester.runpytest_subprocess("--receptor=human")
    result = pytester.runpytest_subprocess(
        "--receptor=llm", "--receptor-events=events.jsonl"
    )
    assert result.ret == native.ret
    assert "receptor artifact: unavailable:" in result.stderr.str()
    assert "controlled artifact close failure" in result.stderr.str()
    artifact = read_artifact(pytester.path / "events.jsonl")
    assert artifact.complete is (exitstatus != 3)
    if exitstatus != 3:
        assert artifact.integrity_valid
        assert artifact.final.data["exitstatus"] == exitstatus


@pytest.mark.parametrize("failed", [False, True])
def test_discard_close_warning_preserves_real_pytest_exit(pytester, failed):
    pytester.makeconftest(
        "from pytest_receptor.plugin import ReceptorPlugin\n"
        "original_silence = ReceptorPlugin._silence_late_terminal\n"
        "class CloseFailure:\n"
        "    def __init__(self, handle): self.handle = handle\n"
        "    def close(self):\n"
        "        self.handle.close()\n"
        "        raise OSError('controlled discard close failure')\n"
        "def silence(self, reporter):\n"
        "    original_silence(self, reporter)\n"
        "    if self._sink is not None:\n"
        "        self._sink = CloseFailure(self._sink)\n"
        "ReceptorPlugin._silence_late_terminal = silence\n"
    )
    pytester.makepyfile(f"def test_value(): assert {not failed}\n")
    result = pytester.runpytest_subprocess("--receptor=llm")
    assert result.ret == int(failed)
    result.stdout.fnmatch_lines([f"{'FAIL' if failed else 'PASS'} exit={int(failed)}*"])
    assert "controlled discard close failure" in result.stderr.str()
    assert "receptor resource:" in result.stderr.str()
