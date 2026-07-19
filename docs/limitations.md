# Limitations

What the receptor does not do, and why. Kept in one place so nothing is a
surprise discovered in the middle of a debugging session.

## Not implemented

| Gap | Detail |
| :--- | :--- |
| **Worker identity** | You are told a group has 38 occurrences and which tests they are, but not which worker ran each. See below — this is a decision, not a backlog item. |
| **Warning baselines** | Warnings are grouped, but there is no accepted-baseline comparison, so you cannot yet ask "what is *new* since last week". |
| **A machine-readable artifact** | The complete report is plain text, not JSON. A structured artifact is deferred until `pytest-reportlog`, which already streams per-report JSONL, has been evaluated. |
| **Cause chains beyond one link** | `raise X from Y` reports Y. A longer chain reports only the first cause. |
| **Semantic truncation budgets** | Long messages are cut at a fixed length with the omission stated, rather than at a structural boundary. |

## Deliberately not done

### Worker identity under xdist

The signal it would provide — a group of failures landing entirely on one worker
— is confounded by the distribution mode. Under `--dist loadfile` or
`loadscope`, failures from one file land on one worker *by construction*, so
"all on gw3" would be an artifact of scheduling rather than a finding about your
code.

The bare identifier without execution order also does not help you reproduce
anything. If you suspect worker-local state, `-n0` is the check.

### A periodic heartbeat

The progress line fires when a test finishes, so a genuinely stuck test produces
no further output. It is a liveness signal, not a hang detector, and it says so.

Its predecessor claimed to be a periodic heartbeat and was not — it could only
fire between tests either — so it was removed rather than fixed. What survives a
kill is the last line printed, which tells you how far the run got.

### CI annotation syntax

`::error file=...` would make failures appear inline on a GitHub pull request.
It is vendor syntax with no demonstrated demand yet, and the `ci` profile is the
one that can least afford extra lines. Waiting on a project that wants it.

## Bounded, not absolute

### Credential redaction

Values that look like credentials are redacted before anything is rendered or
written:

```text
ValueError: connect failed: api_key=[REDACTED] rejected
```

```{warning}
This is a conservative net, not a security boundary. It matches keyword-anchored
shapes — `api_key=`, `token:`, `Bearer ...` — above a minimum length. It cannot
catch a secret that does not look like one. Do not rely on it to make a log safe
to publish.
```

The on-disk report is created owner-only and refuses to follow a symlink, which
bounds who can read it rather than what goes into it.

### Untrusted test output

ANSI escapes and control characters are stripped, and no text produced by a test
can forge a verdict line. Escaping protects structure; it does not make
test-produced text trustworthy. The receptor never presents captured output as
an instruction and never suggests a command that mutates your environment.

## Known rough edges

- Under xdist, one blank line from xdist itself precedes the report. It is
  written outside pytest's terminal writer, and removing it would mean reaching
  further into another plugin than a cosmetic gain justifies.
- Interrupting a run with Ctrl-C leaves pytest's own `KeyboardInterrupt` block
  after the receptor's verdict. Suppressing it has no public mechanism.

## Untested combinations

Covered by CI: Python 3.11–3.13, pytest 8 and 9, serial and distributed,
`pytest-cov`, `pytest-rerunfailures`, and pytest's built-in subtests.

Everything else in your plugin stack is unknown territory. If a plugin you rely
on goes quiet under `--receptor=llm`, that is a defect on our side — silencing
pytest once swallowed pytest-cov's report by accident, and the same mistake could
be hiding elsewhere.
