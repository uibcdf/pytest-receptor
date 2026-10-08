"""Reap direct benchmark children on wait failure without real workloads (#41)."""

from __future__ import annotations

import os
import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
PERFORMANCE = runpy.run_path(str(ROOT / "devtools/benchmarks/run_performance.py"))
pytestmark = pytest.mark.skipif(not hasattr(os, "wait4"), reason="POSIX RSS benchmark")


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt])
def test_failed_wait_reaps_owned_child_before_propagating(tmp_path, failure):
    original = subprocess.Popen
    children = []
    sentinel = tmp_path / "caller.txt"
    sentinel.write_text("preserve caller evidence")

    def launch(_command, **kwargs):
        child = original(
            [sys.executable, "-S", "-c", "import time; time.sleep(30)"], **kwargs
        )
        children.append(child)
        return child

    try:
        with (
            patch.object(subprocess, "Popen", side_effect=launch),
            patch.object(os, "wait4", side_effect=failure("controlled wait failure")),
            pytest.raises(failure, match="controlled wait failure"),
        ):
            PERFORMANCE["_run"](tmp_path, ())
        assert len(children) == 1
        assert children[0].returncode is not None, "owned child was not awaited"
        with pytest.raises(ChildProcessError):
            os.waitpid(children[0].pid, os.WNOHANG)
        assert sentinel.read_text() == "preserve caller evidence"
    finally:
        # Reclaim failing-before children without hiding the failed assertion.
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)


@pytest.mark.parametrize("exit_code", [0, 7])
def test_completed_child_preserves_status_and_rss(tmp_path, exit_code):
    original = subprocess.Popen
    children = []

    def launch(_command, **kwargs):
        child = original(
            [sys.executable, "-S", "-c", f"raise SystemExit({exit_code})"], **kwargs
        )
        children.append(child)
        return child

    try:
        with patch.object(subprocess, "Popen", side_effect=launch):
            result = PERFORMANCE["_run"](tmp_path, ())
        assert result.returncode == exit_code
        assert result.seconds >= 0
        assert result.peak_mib >= 0
        assert children[0].returncode == exit_code
        with pytest.raises(ChildProcessError):
            os.waitpid(children[0].pid, os.WNOHANG)
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)
