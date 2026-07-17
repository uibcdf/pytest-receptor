def test_receptor_option(pytester):
    # Verify that the --receptor option is registered
    result = pytester.runpytest("--help")
    result.stdout.fnmatch_lines(
        [
            "*--receptor*",
        ]
    )


def test_receptor_human_default(pytester):
    # Default is human, prints normal dots/headers
    pytester.makepyfile("""
        def test_pass():
            assert True
    """)
    result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        [
            "*test session starts*",
        ]
    )
    # The output should NOT start with OK:
    assert not result.stdout.str().startswith("OK:")


def test_receptor_llm_green(pytester):
    pytester.makepyfile("""
        def test_pass_1():
            assert True
        def test_pass_2():
            pass
    """)
    result = pytester.runpytest("--receptor=llm")
    stdout = result.stdout.str().strip()

    # It should look like: OK: 2 passed in 0.00s
    assert stdout.startswith("OK: 2 passed in")
    # Verify that we don't have standard session start headers or dots
    assert "test session starts" not in stdout
    assert "==" not in stdout


def test_receptor_llm_red(pytester):
    pytester.makepyfile("""
        def test_fail():
            a = {"x": 1}
            b = {"x": 2}
            assert a == b
    """)
    result = pytester.runpytest("--receptor=llm")
    stdout = result.stdout.str().strip()

    # Verify that we don't have standard tracebacks, headers, or progress percentages
    assert "test session starts" not in stdout
    assert "test_fail" in stdout

    # Should contain the XML delimiters
    assert "<test_failures>" in stdout
    assert "</test_failures>" in stdout
    assert (
        '<failure_group exception="AssertionError" file="test_receptor_llm_red.py" line="4">'
        in stdout
    )
    assert "<message>" in stdout
    assert "</message>" in stdout
    assert "Differing items:" in stdout
    assert "{'x': 1} != {'x': 2}" in stdout


def test_receptor_llm_captured_output(pytester):
    pytester.makepyfile(
        """
import logging
import sys

def test_outputs():
    print("PRINT_OUTPUT_123")
    sys.stderr.write("STDERR_OUTPUT_456\\n")
    logging.warning("LOG_OUTPUT_789")
    assert False
"""
    )
    result = pytester.runpytest("--receptor=llm")
    stdout = result.stdout.str().strip()

    # Check for the captured XML tags
    assert "<captured_stdout>" in stdout
    assert "PRINT_OUTPUT_123" in stdout
    assert "</captured_stdout>" in stdout

    assert "<captured_stderr>" in stdout
    assert "STDERR_OUTPUT_456" in stdout
    assert "</captured_stderr>" in stdout

    assert "<captured_log>" in stdout
    assert "LOG_OUTPUT_789" in stdout
    assert "</captured_log>" in stdout


def test_receptor_llm_deduplication(pytester):
    pytester.makepyfile(
        """
def test_fail_1():
    raise ValueError("common error")
def test_fail_2():
    raise ValueError("common error")
"""
    )
    result = pytester.runpytest("--receptor=llm")
    stdout = result.stdout.str().strip()

    # Should contain only one failure_group for ValueError
    assert stdout.count("<failure_group") == 1
    assert 'exception="ValueError"' in stdout
    assert "common error" in stdout

    # But lists both tests inside
    assert 'test name="test_fail_1"' in stdout
    assert 'test name="test_fail_2"' in stdout


def test_receptor_llm_hints(pytester):
    pytester.makepyfile(
        """
def test_import():
    raise ModuleNotFoundError("No module named 'nonexistent_lib'")
"""
    )
    result = pytester.runpytest("--receptor=llm")
    stdout = result.stdout.str().strip()

    assert "<hint>pip install nonexistent_lib</hint>" in stdout


def test_receptor_llm_stats(pytester):
    pytester.makepyfile(
        """
def test_pass():
    pass
"""
    )
    result = pytester.runpytest("--receptor=llm", "--receptor-stats")
    stdout = result.stdout.str().strip()

    assert "[Receptor Stats]" in stdout
    assert "Saved:" in stdout
    assert "-->" in stdout


def test_receptor_llm_dump_dir(pytester, tmp_path):
    pytester.makepyfile(
        """
def test_ok():
    pass
"""
    )
    dump_dir = tmp_path / "my_logs"
    pytester.runpytest("--receptor=llm", f"--receptor-dump-dir={dump_dir}")

    # Check that the directory was created and contains the two logs
    assert dump_dir.exists()
    files = list(dump_dir.glob("*.log"))
    assert len(files) == 2

    human_files = list(dump_dir.glob("pytest_human_*.log"))
    llm_files = list(dump_dir.glob("pytest_llm_*.log"))

    assert len(human_files) == 1
    assert len(llm_files) == 1

    # Verify contents
    with open(human_files[0], "r", encoding="utf-8") as f:
        human_content = f.read()
    with open(llm_files[0], "r", encoding="utf-8") as f:
        llm_content = f.read()

    assert "test session starts" in human_content
    assert "OK: 1 passed in" in llm_content


def test_receptor_ci_green(pytester):
    pytester.makepyfile(
        """
def test_pass_1():
    assert True
def test_pass_2():
    pass
"""
    )
    result = pytester.runpytest("--receptor=ci")
    stdout = result.stdout.str().strip()

    # Should only print the final atomic CI summary line
    assert stdout.startswith("CI: 2 passed in")
    assert "test session starts" not in stdout
    assert "==" not in stdout


def test_receptor_ci_red(pytester):
    pytester.makepyfile(
        """
def test_fail():
    assert 1 == 2
"""
    )
    result = pytester.runpytest("--receptor=ci")
    stdout = result.stdout.str().strip()

    # Verify that we don't have standard session start headers, dots or progress percentages
    assert "test session starts" not in stdout

    # Should contain the clean flat failures header and traceback
    assert "FAILURES" in stdout
    assert "def test_fail():" in stdout
    assert "assert 1 == 2" in stdout

    # Should end with the final status line
    assert "CI: 1 failed in" in stdout


def test_receptor_llm_slow_tests(pytester):
    pytester.makepyfile(
        """
import time
def test_slow():
    time.sleep(0.55)
"""
    )
    result = pytester.runpytest("--receptor=llm")
    stdout = result.stdout.str().strip()

    assert "<slow_tests>" in stdout
    assert 'test name="test_receptor_llm_slow_tests.py::test_slow"' in stdout
    assert 'duration="' in stdout
    assert "</slow_tests>" in stdout


def test_receptor_ci_slow_tests(pytester):
    pytester.makepyfile(
        """
import time
def test_slow():
    time.sleep(0.55)
"""
    )
    result = pytester.runpytest("--receptor=ci")
    stdout = result.stdout.str().strip()

    assert "Slowest tests (>0.5s):" in stdout
    assert "- test_receptor_ci_slow_tests.py::test_slow (" in stdout


def test_receptor_llm_normalization(pytester):
    pytester.makepyfile(
        """
def test_fail_1():
    raise ValueError("error at memory 0x7f83ad910 at 2026-07-17 09:15:47.123")
def test_fail_2():
    raise ValueError("error at memory 0x0000021a at 2026-07-17 09:15:59")
"""
    )
    result = pytester.runpytest("--receptor=llm")
    stdout = result.stdout.str().strip()

    # The messages should normalize to the same key and group together
    assert stdout.count("<failure_group") == 1
    assert 'exception="ValueError"' in stdout
    assert "error at memory 0x7f83ad910" in stdout
    # Lists both tests inside
    assert 'test name="test_fail_1"' in stdout
    assert 'test name="test_fail_2"' in stdout


def test_receptor_llm_adaptive_hints(pytester):
    pytester.makepyfile(
        """
def test_import():
    raise ModuleNotFoundError("No module named 'nonexistent_lib'")
"""
    )
    # Create a dummy poetry.lock file in the test workspace
    poetry_lock = pytester.path / "poetry.lock"
    poetry_lock.write_text("dummy poetry content")

    result = pytester.runpytest("--receptor=llm")
    stdout = result.stdout.str().strip()

    assert "<hint>poetry add nonexistent_lib</hint>" in stdout
