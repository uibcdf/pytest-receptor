"""The actual documentation clean target must preserve neighboring work (#44)."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("make") is None, reason="make is not installed")
@pytest.mark.parametrize("build_name", ["scratch output", "-output"])
def test_docs_clean_removes_only_the_selected_build_contents(tmp_path, build_name):
    caller = tmp_path / "scratch"
    caller.mkdir()
    sentinel = caller / "caller.txt"
    sentinel.write_text("other caller's active work")
    build = tmp_path / build_name
    build.mkdir()
    generated = build / "index.html"
    generated.write_text("generated build output")

    result = subprocess.run(
        ["make", "-f", str(ROOT / "docs/Makefile"), "clean", f"BUILDDIR={build_name}"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert sentinel.read_text() == "other caller's active work"
    assert not generated.exists()
