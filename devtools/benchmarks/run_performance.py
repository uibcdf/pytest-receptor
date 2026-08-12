"""Measure pytest-receptor wall time and peak resident memory.

This is deliberately separate from the token benchmark: redirecting output to
``DEVNULL`` removes terminal volume from the timing, and ``wait4`` attributes
peak RSS to each individual pytest child instead of the benchmark process.

Run: python devtools/benchmarks/run_performance.py
     python devtools/benchmarks/run_performance.py --tests 8000 --repeat 5
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Measurement:
    seconds: float
    peak_mib: float
    returncode: int


MODES = {
    "pytest quiet": ("-q", "--no-header", "--tb=short"),
    "receptor": ("--receptor=llm",),
    "receptor + JSONL": (
        "--receptor=llm",
        "--receptor-events=events.jsonl",
    ),
}


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("FORCE_COLOR", None)
    env.pop("PY_COLORS", None)
    env["NO_COLOR"] = "1"
    # Benchmark pytest itself plus receptor, not whichever unrelated plugins
    # happen to be installed in the caller's development environment.
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


def _peak_mib(maxrss: int) -> float:
    # Linux and the BSDs report KiB; macOS reports bytes.
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return maxrss / divisor


def _run(directory: Path, args: tuple[str, ...]) -> Measurement:
    started = time.monotonic()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "pytest",
            *args,
            "-p",
            "pytest_receptor.plugin",
            "-p",
            "no:cacheprovider",
        ],
        cwd=directory,
        env=_environment(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _pid, status, usage = os.wait4(process.pid, 0)
    process.returncode = os.waitstatus_to_exitcode(status)
    return Measurement(
        seconds=time.monotonic() - started,
        peak_mib=_peak_mib(usage.ru_maxrss),
        returncode=process.returncode,
    )


def _diagnose(directory: Path, args: tuple[str, ...]) -> str:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *args,
            "-p",
            "pytest_receptor.plugin",
            "-p",
            "no:cacheprovider",
        ],
        cwd=directory,
        env=_environment(),
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout + result.stderr).strip()


def _write_scenario(directory: Path, name: str, tests: int) -> int:
    if name == "green":
        source = (
            "import pytest\n"
            f"@pytest.mark.parametrize('case', range({tests}))\n"
            "def test_ok(case): assert True\n"
        )
        expected = 0
    else:
        source = (
            "import pytest\n"
            "@pytest.fixture\n"
            "def broken(): raise RuntimeError('shared setup failure')\n"
            f"@pytest.mark.parametrize('case', range({tests}))\n"
            "def test_bad(broken, case): pass\n"
        )
        expected = 1
    (directory / "test_scale.py").write_text(source, encoding="utf-8")
    return expected


def measure(tests: int, repeat: int):
    # Unique so two developers or CI jobs can benchmark concurrently without
    # deleting each other's active working directory.
    directory = Path(tempfile.mkdtemp(prefix="receptor-performance-"))
    results = {}
    try:
        for scenario in ("green", "setup cascade"):
            expected = _write_scenario(directory, scenario, tests)
            samples = {mode: [] for mode in MODES}
            # One unreported warm-up avoids charging import and bytecode-cache
            # creation to whichever mode happens to run first.
            warmup = _run(directory, MODES["pytest quiet"])
            if warmup.returncode != expected:
                detail = _diagnose(directory, MODES["pytest quiet"])
                raise RuntimeError(
                    f"{scenario} warm-up exited {warmup.returncode}:\n{detail}"
                )
            for iteration in range(repeat):
                labels = list(MODES)
                labels = labels[iteration % len(labels) :] + labels[: iteration % 3]
                for mode in labels:
                    sample = _run(directory, MODES[mode])
                    if sample.returncode != expected:
                        detail = _diagnose(directory, MODES[mode])
                        raise RuntimeError(
                            f"{scenario}/{mode} exited {sample.returncode}:\n{detail}"
                        )
                    samples[mode].append(sample)
            results[scenario] = {
                mode: Measurement(
                    seconds=statistics.median(item.seconds for item in values),
                    peak_mib=statistics.median(item.peak_mib for item in values),
                    returncode=expected,
                )
                for mode, values in samples.items()
            }
    finally:
        shutil.rmtree(directory, ignore_errors=True)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests", type=int, default=4000)
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    if args.tests < 1 or args.repeat < 1:
        parser.error("--tests and --repeat must be positive")

    results = measure(args.tests, args.repeat)
    print(f"Platform: {platform.platform()}")
    print(f"Python: {platform.python_version()}")
    print(f"Workload: {args.tests} tests, median of {args.repeat} runs")
    print()
    print("| Scenario | Mode | Wall time | Peak RSS | Time vs quiet | RSS vs quiet |")
    print("| :--- | :--- | ---: | ---: | ---: | ---: |")
    for scenario, modes in results.items():
        baseline = modes["pytest quiet"]
        for mode, value in modes.items():
            time_delta = (value.seconds / baseline.seconds - 1) * 100
            rss_delta = value.peak_mib - baseline.peak_mib
            print(
                f"| {scenario} | {mode} | {value.seconds:.3f}s | "
                f"{value.peak_mib:.1f} MiB | {time_delta:+.1f}% | "
                f"{rss_delta:+.1f} MiB |"
            )


if __name__ == "__main__":
    main()
