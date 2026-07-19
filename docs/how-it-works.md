# How it works

Worth knowing before you trust it with your suite. Several of these decisions
look wrong until you know what they are avoiding.

## It does not replace pytest's reporter

An earlier version unregistered pytest's `TerminalReporter` and substituted a
subclass of it. This one leaves it in place — so any plugin that looks it up
still finds it — and quietens it through documented options: `verbose = -2`,
`no_header`, an emptied `reportchars`, colour off, plus a wrapper around
`pytest_report_teststatus` that drops the progress characters while preserving
pytest's own categorization.

Two of those are deliberate avoidances rather than obvious choices.

**`no_summary` is not used**, although it looks like the switch for the job. It
gates the whole `pytest_terminal_summary` hook, which is where third-party
plugins write, so setting it swallowed pytest-cov's coverage table entirely.
Silencing pytest must not silence everyone else. Reported upstream as
[pytest#14724](https://github.com/pytest-dev/pytest/issues/14724).

**`tbstyle` is not set at configure time.** Setting it to `"no"` looks like the
clean way to suppress tracebacks, and it is: it also impoverishes `longrepr` at
*construction* time — the same failure renders to 145 characters under `short`
and 21 under `no` — which destroys the frame data this plugin exists to
summarize. Suppression happens at session finish instead, once every `longrepr`
has been built. Reported upstream as
[pytest#14720](https://github.com/pytest-dev/pytest/issues/14720).

## It collects from public hooks

`pytest_runtest_logreport` for phase results, `pytest_collectreport` for
collection failures, `pytest_warning_recorded` for warnings, and
`pytest_sessionfinish` to render.

Rendering happens in `sessionfinish` rather than `terminal_summary` because
pytest does not call the latter for `INTERNAL_ERROR` — which is exactly when a
consumer most needs to be told what happened.

## Grouping is call-site aware

The key is exception type, phase, crash location, and cause chain.

The **message is deliberately excluded**. Keying on it fragmented a parametrized
test into one group per input, which defeats grouping precisely where suites are
most repetitive. Differing messages are kept as variants inside the group and
shown.

Using the **crash location** rather than the test line is what makes this
correct: a bug in `merge.py:117` groups every caller, wherever their tests live.

The **cause chain** is part of the key, so one wrapper over two different
underlying failures stays two bugs.

Warnings are grouped separately, by category and normalized message, with
numbers and shapes normalized but names left alone — a size mismatch is the same
warning at any size, while a different attribute is different information.

## Tracebacks keep the decisive frame

Every local frame survives, because that is the code you can change. External
frames are pruned to the boundary where you entered the dependency and the frame
that actually broke, with elisions marked:

```text
frames: tests/test_merge.py:12 -> molsysmt/merge.py:41 -> numpy/core/shape.py:88 (ext) -> ... -> numpy/core/_methods.py:52 (ext)
```

Dropping external frames entirely is cheaper and wrong: when a failure
originates inside NumPy or a serializer, the external frame *is* the answer.

## Nothing is deferred to a second run

Grouping is a presentation decision. Every occurrence keeps its node ID, phase,
and location, and the complete report is written to the pytest cache while the
run is still going.

Detail is only ever held back when that file exists to hold it — with
`-p no:cacheprovider` nothing is withheld at all, because there would be nowhere
to recover it from. A consumer can never be left with information reachable only
by running the suite again.

## Paths resolve from where you invoked pytest

Not from `rootpath`. Naming a test outside the project sets pytest's rootdir to
the common ancestor, and paths relative to *that* resolve from nowhere: a rerun
command came back `file or directory not found`, and `mypkg/__init__.py`
rendered as `mypkg/mypkg/__init__.py`.

Everything printed — crash locations, the frame chain, rerun commands, and the
node IDs in occurrence lists — is relative to `invocation_params.dir`. A test far
outside the tree is printed absolute rather than as a chain of `../..`, so the
contract is that a path *resolves*, not that it is relative.

## Distributed runs

The plugin is instantiated in every xdist worker as well as the controller. Each
worker collects the whole suite but finishes only its share, so left alone all
twelve announce their own progress at their own pace.

Only the controller emits, and it takes the collected total from
`pytest_xdist_node_collection_finished`, declared optional so the plugin still
loads where xdist is absent.

Reports arrive in whatever order workers finish, so occurrences and groups are
given a total order before rendering. A distributed run therefore produces
**byte-identical output to a serial one**.

## It degrades rather than fails

The whole render is wrapped. Any receptor exception produces `RECEPTOR_ERROR`,
the underlying traceback, the raw pytest evidence, and pytest's original exit
status.

The worst case of enabling this plugin is standard pytest plus one line of
noise. That is what makes it safe to put in `addopts`.
