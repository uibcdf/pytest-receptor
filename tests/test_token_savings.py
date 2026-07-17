import tiktoken


def count_tokens(text: str) -> int:
    # Use cl100k_base which is used by gpt-4, gpt-3.5-turbo, etc.
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def test_token_savings_green_suite(pytester):
    # Create a passing test suite with 10 tests to show scaling savings
    pytester.makepyfile("""
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
    """)

    # Run with human receptor (default)
    result_human = pytester.runpytest()
    stdout_human = result_human.stdout.str()
    tokens_human = count_tokens(stdout_human)

    # Run with llm receptor
    result_llm = pytester.runpytest("--receptor=llm")
    stdout_llm = result_llm.stdout.str()
    tokens_llm = count_tokens(stdout_llm)

    # Calculate savings
    savings_percent = (1 - (tokens_llm / tokens_human)) * 100

    print("\n--- GREEN SUITE TOKEN BENCHMARK ---")
    print(f"Human stdout tokens: {tokens_human}")
    print(f"LLM stdout tokens:   {tokens_llm}")
    print(f"Token savings:       {savings_percent:.2f}%")
    print("-----------------------------------")

    # Assert a minimum of 60% savings for green suites
    assert savings_percent >= 60.0


def test_token_savings_red_suite(pytester):
    # Create a failing test suite with 1 failing test and 5 passing tests
    pytester.makepyfile("""
        def test_pass_1(): assert True
        def test_pass_2(): pass
        def test_fail():
            a = {"foo": "bar", "baz": [1, 2, 3]}
            b = {"foo": "bar", "baz": [1, 2, 4]}
            assert a == b
        def test_pass_3(): pass
        def test_pass_4(): assert True
        def test_pass_5(): pass
    """)

    # Run with human receptor (default)
    result_human = pytester.runpytest()
    stdout_human = result_human.stdout.str()
    tokens_human = count_tokens(stdout_human)

    # Run with llm receptor
    result_llm = pytester.runpytest("--receptor=llm")
    stdout_llm = result_llm.stdout.str()
    tokens_llm = count_tokens(stdout_llm)

    # Calculate savings
    savings_percent = (1 - (tokens_llm / tokens_human)) * 100

    print("\n--- RED SUITE TOKEN BENCHMARK ---")
    print(f"Human stdout tokens: {tokens_human}")
    print(f"LLM stdout tokens:   {tokens_llm}")
    print(f"Token savings:       {savings_percent:.2f}%")
    print("---------------------------------")

    # Assert a minimum of 15% savings for red suites
    assert savings_percent >= 15.0


def test_token_savings_warnings_suite(pytester):
    # Test suite that generates python deprecation warnings
    pytester.makepyfile("""
        import warnings
        def test_with_warning():
            warnings.warn("This is a test warning", DeprecationWarning)
            assert True
    """)

    # Run with human receptor (default)
    result_human = pytester.runpytest("-W", "always")
    stdout_human = result_human.stdout.str()
    tokens_human = count_tokens(stdout_human)

    # Run with llm receptor
    result_llm = pytester.runpytest("--receptor=llm", "-W", "always")
    stdout_llm = result_llm.stdout.str()
    tokens_llm = count_tokens(stdout_llm)

    savings_percent = (1 - (tokens_llm / tokens_human)) * 100

    print("\n--- WARNINGS SUITE TOKEN BENCHMARK ---")
    print(f"Human stdout tokens: {tokens_human}")
    print(f"LLM stdout tokens:   {tokens_llm}")
    print(f"Token savings:       {savings_percent:.2f}%")
    print("--------------------------------------")

    # Assert a minimum of 40% savings
    assert savings_percent >= 40.0


def test_token_savings_mixed_states_suite(pytester):
    # Test suite with passed, skipped, xfail, and xpass
    pytester.makepyfile("""
        import pytest
        def test_pass(): assert True
        @pytest.mark.skip(reason="skipped for compatibility")
        def test_skip(): pass
        @pytest.mark.xfail(reason="expected failure")
        def test_xfail(): assert False
        @pytest.mark.xfail(reason="passes unexpectedly")
        def test_xpass(): assert True
    """)

    result_human = pytester.runpytest()
    stdout_human = result_human.stdout.str()
    tokens_human = count_tokens(stdout_human)

    result_llm = pytester.runpytest("--receptor=llm")
    stdout_llm = result_llm.stdout.str()
    tokens_llm = count_tokens(stdout_llm)

    savings_percent = (1 - (tokens_llm / tokens_human)) * 100

    print("\n--- MIXED STATES SUITE TOKEN BENCHMARK ---")
    print(f"Human stdout tokens: {tokens_human}")
    print(f"LLM stdout tokens:   {tokens_llm}")
    print(f"Token savings:       {savings_percent:.2f}%")
    print("------------------------------------------")

    assert savings_percent >= 5.0


def test_token_savings_multiple_failures_suite(pytester):
    # Test suite with failures in both 'call' and 'setup' (fixture) phase
    pytester.makepyfile("""
        import pytest
        @pytest.fixture
        def broken_fixture():
            raise RuntimeError("setup error in fixture")
        def test_setup_error(broken_fixture):
            pass
        def test_call_error():
            raise ValueError("error in execution")
    """)

    result_human = pytester.runpytest()
    stdout_human = result_human.stdout.str()
    tokens_human = count_tokens(stdout_human)

    result_llm = pytester.runpytest("--receptor=llm")
    stdout_llm = result_llm.stdout.str()
    tokens_llm = count_tokens(stdout_llm)

    savings_percent = (1 - (tokens_llm / tokens_human)) * 100

    print("\n--- MULTIPLE FAILURES SUITE TOKEN BENCHMARK ---")
    print(f"Human stdout tokens: {tokens_human}")
    print(f"LLM stdout tokens:   {tokens_llm}")
    print(f"Token savings:       {savings_percent:.2f}%")
    print("-----------------------------------------------")

    assert savings_percent >= 4.0


def test_token_savings_collection_error_suite(pytester):
    # Create one valid test file and one broken file with syntax/import error
    pytester.makepyfile(
        test_valid="""
            def test_ok(): pass
        """,
        test_invalid="""
            import nonexistent_module_xyz
            def test_bad(): pass
        """,
    )

    result_human = pytester.runpytest()
    stdout_human = result_human.stdout.str()
    tokens_human = count_tokens(stdout_human)

    result_llm = pytester.runpytest("--receptor=llm")
    stdout_llm = result_llm.stdout.str()
    tokens_llm = count_tokens(stdout_llm)

    savings_percent = (1 - (tokens_llm / tokens_human)) * 100

    print("\n--- COLLECTION ERROR SUITE TOKEN BENCHMARK ---")
    print(f"Human stdout tokens: {tokens_human}")
    print(f"LLM stdout tokens:   {tokens_llm}")
    print(f"Token savings:       {savings_percent:.2f}%")
    print("----------------------------------------------")

    assert savings_percent >= 5.0


def test_token_savings_cascade_failures_suite(pytester):
    # Create a suite with a shared fixture that fails, used by 20 tests
    test_methods = "\n".join(f"def test_{i}(broken_resource): pass" for i in range(20))
    pytester.makepyfile(
        f"""
import pytest
@pytest.fixture
def broken_resource():
    raise RuntimeError("Database connection timed out at localhost:5432")

{test_methods}
"""
    )

    # Run with human receptor (default)
    result_human = pytester.runpytest()
    stdout_human = result_human.stdout.str()
    tokens_human = count_tokens(stdout_human)

    # Run with llm receptor
    result_llm = pytester.runpytest("--receptor=llm")
    stdout_llm = result_llm.stdout.str()
    tokens_llm = count_tokens(stdout_llm)

    # Calculate savings
    savings_percent = (1 - (tokens_llm / tokens_human)) * 100

    print("\n--- CASCADE FAILURES SUITE TOKEN BENCHMARK ---")
    print(f"Human stdout tokens: {tokens_human}")
    print(f"LLM stdout tokens:   {tokens_llm}")
    print(f"Token savings:       {savings_percent:.2f}%")
    print("----------------------------------------------")

    # Assert a minimum of 75% savings due to deduplication
    assert savings_percent >= 75.0
