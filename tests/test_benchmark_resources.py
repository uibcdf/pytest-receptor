"""Protect benchmark ownership and cleanup without the large workloads (#40)."""

from __future__ import annotations

import re
import runpy
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOKEN = runpy.run_path(str(ROOT / "devtools/benchmarks/run_benchmarks.py"))
PERFORMANCE = runpy.run_path(str(ROOT / "devtools/benchmarks/run_performance.py"))


def tokens(text):
    return {"fixture": len(text)}, "fixture"


def token_measure():
    return TOKEN["measure"](
        {"toy": {"test_toy.py": "def test_ok(): assert True\n"}},
        {"baseline": []},
        [],
    )


def performance_sample(directory, _args):
    failed = "def test_bad" in (directory / "test_scale.py").read_text()
    return PERFORMANCE["Measurement"](0.1, 1.0, int(failed))


@pytest.mark.parametrize("occupied_is_file", [False, True])
def test_token_benchmark_preserves_an_occupied_path(tmp_path, occupied_is_file):
    directory = tmp_path / "receptor-bench"
    if occupied_is_file:
        directory.write_text("other caller's active work")
        sentinel = directory
    else:
        directory.mkdir()
        sentinel = directory / "active.txt"
        sentinel.write_text("other caller's active work")
    with (
        patch.object(tempfile, "gettempdir", return_value=str(tmp_path)),
        patch.dict(
            TOKEN["measure"].__globals__,
            _run=lambda *_args: "toy",
            _count_tokens=tokens,
        ),
        pytest.raises(FileExistsError),
    ):
        token_measure()
    assert sentinel.read_text() == "other caller's active work"


def test_token_benchmark_refuses_concurrent_owner(tmp_path):
    entered, release = threading.Event(), threading.Event()
    seen = []

    def run(directory, _args):
        seen.append(directory)
        entered.set()
        assert release.wait(5), "test did not release the first benchmark"
        assert (directory / "test_toy.py").exists()
        return "toy"

    with (
        patch.object(tempfile, "gettempdir", return_value=str(tmp_path)),
        patch.dict(TOKEN["measure"].__globals__, _run=run, _count_tokens=tokens),
        ThreadPoolExecutor(max_workers=1) as executor,
    ):
        first = executor.submit(token_measure)
        try:
            assert entered.wait(5), "first benchmark did not claim its directory"
            with pytest.raises(FileExistsError):
                token_measure()
            assert (tmp_path / "receptor-bench/test_toy.py").exists()
        finally:
            release.set()
        first.result(timeout=5)
    assert seen and not seen[0].exists()


@pytest.mark.parametrize("kind", ["token", "performance"])
@pytest.mark.parametrize("fail", [False, True])
def test_benchmarks_clean_owned_resources_after_both_outcomes(tmp_path, kind, fail):
    namespace = TOKEN if kind == "token" else PERFORMANCE
    seen = []

    def run(directory, args):
        seen.append(directory)
        if fail:
            raise RuntimeError("controlled child failure")
        return "toy" if kind == "token" else performance_sample(directory, args)

    with (
        patch.object(tempfile, "tempdir", str(tmp_path)),
        patch.dict(namespace["measure"].__globals__, _run=run, _count_tokens=tokens),
    ):
        if fail:
            with pytest.raises(RuntimeError, match="controlled child failure"):
                token_measure() if kind == "token" else PERFORMANCE["measure"](1, 1)
        else:
            token_measure() if kind == "token" else PERFORMANCE["measure"](1, 1)
    assert seen
    assert all(not directory.exists() for directory in seen)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("kind", ["token", "performance"])
@pytest.mark.parametrize("fail", [False, True])
def test_benchmarks_expose_cleanup_failure(tmp_path, kind, fail):
    namespace = TOKEN if kind == "token" else PERFORMANCE

    def run(directory, args):
        if fail:
            raise RuntimeError("controlled child failure")
        return "toy" if kind == "token" else performance_sample(directory, args)

    def remove(_directory, *args, **kwargs):
        if not kwargs.get("ignore_errors", False):
            raise PermissionError("controlled cleanup failure")

    with (
        patch.object(tempfile, "tempdir", str(tmp_path)),
        patch.dict(namespace["measure"].__globals__, _run=run, _count_tokens=tokens),
        patch("shutil.rmtree", side_effect=remove),
        pytest.raises(PermissionError, match="controlled cleanup failure") as error,
    ):
        token_measure() if kind == "token" else PERFORMANCE["measure"](1, 1)
    if fail:
        assert isinstance(error.value.__context__, RuntimeError)
    assert list(tmp_path.iterdir()), "fixture must demonstrate the failed removal"


def test_token_benchmark_keeps_real_pytest_rootdir_stable(tmp_path):
    original = TOKEN["_run"]
    headers = []

    def run(directory, _args):
        output = original(directory, ["--color=no"])
        rootdir = re.search(r"^rootdir: (.+)$", output, re.MULTILINE)
        assert rootdir, output
        headers.append(rootdir.group(1))
        return output

    with (
        patch.object(tempfile, "gettempdir", return_value=str(tmp_path)),
        patch.dict(TOKEN["measure"].__globals__, _run=run, _count_tokens=tokens),
    ):
        token_measure()
        token_measure()
    assert len(headers) == 4
    assert set(headers) == {str(tmp_path / "receptor-bench")}
    assert not (tmp_path / "receptor-bench").exists()
