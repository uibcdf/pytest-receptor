import os
import tempfile
import subprocess
import tiktoken

# Define the suite content
SUITES = {
    "Green Suite (10 passed)": """
def test_1(): assert True
def test_2(): pass
def test_3(): assert 1 + 1 == 2
def test_4(): assert 2 + 2 == 4
def test_5(): pass
def test_6(): assert True
def test_7(): pass
def test_8(): assert True
def test_9(): assert True
def test_10(): pass
""",
    "Red Suite (1 failed)": """
def test_fail():
    x = 1
    y = 2
    assert x == y
""",
    "Warnings Suite": """
import warnings
def test_warns():
    warnings.warn("Deprecation warning content", DeprecationWarning)
    warnings.warn("User warning content", UserWarning)
""",
    "Mixed States Suite": """
import pytest
def test_pass(): assert True
@pytest.mark.skip(reason="skipped case")
def test_skip(): pass
@pytest.mark.xfail(reason="expected fail")
def test_xfail(): assert False
@pytest.mark.xfail(reason="unexpected pass")
def test_xpass(): assert True
""",
    "Multiple Failures Suite": """
import pytest
@pytest.fixture
def broken(): raise RuntimeError("fixture setup error")
def test_setup_err(broken): pass
def test_call_err(): raise ValueError("execution error")
""",
    "Cascade Failures (20 error)": """
import pytest
@pytest.fixture
def broken(): raise RuntimeError("shared database error")
"""
    + "\n".join(f"def test_{i}(broken): pass" for i in range(20)),
}

ENCODINGS = {
    "cl100k_base (GPT-4/3.5)": "cl100k_base",
    "o200k_base (GPT-4o)": "o200k_base",
    "p50k_base (Codex)": "p50k_base",
    "r50k_base (GPT-3/2)": "r50k_base",
}


def count_tokens(text: str, enc_name: str) -> int:
    try:
        encoding = tiktoken.get_encoding(enc_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback rough estimation
        return len(text) // 4


def run_suite(suite_code: str) -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = os.path.join(tmp_dir, "test_benchmark.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(suite_code)

        # Run human (default)
        res_human = subprocess.run(
            ["pytest", test_file],
            capture_output=True,
            text=True,
        )
        # Run LLM
        res_llm = subprocess.run(
            ["pytest", test_file, "--receptor=llm"],
            capture_output=True,
            text=True,
        )
        return res_human.stdout, res_llm.stdout


def main():
    print("# pytest-receptor Tokenizer Benchmark Results\n")
    print(
        "This report benchmarks the token savings achieved by `pytest-receptor`'s LLM reporter compared to pytest's standard human-readable reporter across multiple popular tokenizer families.\n"
    )

    # Table Header
    print("| Suite Name | Tokenizer | Human Tokens | LLM Tokens | Savings % |")
    print("|---|---|---|---|---|")

    for name, code in SUITES.items():
        human_out, llm_out = run_suite(code)

        # Clean outputs (e.g. remove dynamic warnings about python versions if any, or duration lines to be consistent)
        # Actually, running raw outputs is the most realistic evaluation!

        first = True
        for label, enc_name in ENCODINGS.items():
            h_tok = count_tokens(human_out, enc_name)
            l_tok = count_tokens(llm_out, enc_name)
            savings = (1 - (l_tok / h_tok)) * 100 if h_tok > 0 else 0.0

            suite_label = name if first else ""
            print(f"| {suite_label} | {label} | {h_tok} | {l_tok} | {savings:.2f}% |")
            first = False
        print("| | | | | |")  # empty line separator in table


if __name__ == "__main__":
    main()
