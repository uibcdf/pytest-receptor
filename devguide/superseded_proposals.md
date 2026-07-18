# Superseded Proposals

**Recorded:** 2026-07-18

**Status:** historical. Nothing in this file is a current plan.

## Why this file exists

Proposals that were rejected or replaced are preserved here rather than deleted.
They record why the project once believed something, which is useful when the
same idea resurfaces. Each entry states what was proposed, why it no longer
applies, and what replaced it.

Superseding decisions live in `scope_0.6.md` and in the decisions table of
`audit_action_register_2026-07-17.md`.

---

## 1. Minified XML as the agent output syntax

**Superseded by:** compact plain text (SCOPE design rule 2; PR-FID-002).

**Original claim**, from the initial development guide:

> Instead of formatting tables or dashes (`----`), we wrap failures in lightweight
> structural tags (e.g., `<test_failures>`, `<failure_group>`). Modern language
> models have been heavily trained on web data (HTML/XML); their attention
> mechanisms identify and process the boundaries of these tags with drastically
> less context noise than arbitrary plain text.

The same claim appeared in the upstream pytest issue as "Token Attention
Optimization".

**Why it was dropped:**

- The attention claim is unevidenced. No measurement in this repository or
  elsewhere was produced to support "drastically less context noise".
- XML costs *more* tokens than plain text for identical content, which
  contradicts the project's primary goal.
- Unescaped values made the advertised XML structurally invalid (`<`, `&`, and
  quotes in messages and captured output). Escaping was possible but added
  serialization machinery in service of a benefit that was never demonstrated.

Deleting XML resolved the malformed-output defect by construction instead of by
repair.

---

## 2. Adaptive dependency-installation hints

**Superseded by:** the exact rerun command (PR-UX-001, PR-UX-003).

**Original behavior:** detect Poetry, UV, PDM, or Pipenv and emit a repair
command, for example `<hint>poetry add requests</hint>` on `ModuleNotFoundError`.

**Why it was dropped:**

- Import names and distribution names differ (`sklearn` / `scikit-learn`).
- The dependency may be deliberately optional.
- pytest may simply be running in the wrong environment.
- Test dependencies usually belong in a development group, not the main one.
- The project's dependency policy may prohibit direct installation.

The audit's recommendation was to make hints conservative. The 0.6 decision went
further and removed them, because a conservative hint is close to useless while
still carrying the risk of an agent acting on it. A rerun command is always
correct and always actionable.

---

## 3. The CI heartbeat

**Superseded by:** deletion (PR-OPS-002).

**Original claim:** in suites running longer than five seconds, emit a flat
progress heartbeat every five seconds to keep a CI job alive.

**Why it was dropped:**

- It never worked as documented. The check ran only inside
  `pytest_runtest_logreport`, so it could not fire while a test or fixture was
  still running. A single six-second test produced no heartbeat at all.
- CI runners already own timeout and keepalive behavior.
- A correct implementation needs a monitored background thread tested against
  xdist, hanging fixtures, interruption, and shutdown — significant cost for a
  problem that mostly is not the plugin's.

---

## 4. `CiTerminalReporter` as a separate reporter implementation

**Superseded by:** a profile of the single renderer (PR-OPS-010).

**Note:** `--receptor=ci` itself is **not** superseded. It was briefly proposed
for deletion on 2026-07-18 and that proposal was reversed the same day; the entry
below covers only the duplicated implementation.

**Why the separate class was dropped:** `CiTerminalReporter` duplicated the
slow-test reporting, summary construction, and outcome counters of
`LlmTerminalReporter` across 116 lines. Two copies of the same logic means two
places to fix every future defect.

**Why the mode itself was kept:** the initial argument for deleting it was that
its only differences were the absence of ANSI and of progress output, which are
options rather than a consumer profile. That argument was wrong. In CI the runner
is destroyed when the job ends, so `.pytest_cache/receptor/last-run.txt` is
unreachable by the time anyone reads the log. Progressive disclosure depends on
that file being reachable, so the CI profile must expand every group instead.
That is a substantive difference in consumer, and it is exactly the distinction
the receptor concept exists to express.

The receptor concept allows several profiles. It does not require each one to be
a separate reporter implementation.

---

## 5. Replacing pytest's `TerminalReporter`

**Superseded by:** public hooks (PR-ARCH-003).

**Original approach:** unregister pytest's terminal reporter in
`pytest_configure` and register a subclass of `_pytest.terminal.TerminalReporter`,
with a `DummyTerminalWriter` swallowing the standard output.

**Why it was dropped:** it depends on a private implementation surface across
pytest 8 and 9, xdist, and any plugin that looks up the terminal reporter by
identity. It also created three separate defects on its own: unbounded in-memory
retention of suppressed output, an undefined capture boundary for the human dump,
and ambiguity about which output channel is authoritative.

Silencing the standard reporter through its public options and rendering from
`pytest_terminal_summary` removes all three as a side effect.

---

## 6. A bespoke versioned JSONL event schema for the first release

**Superseded by:** a plain-text report on disk for 0.6; evaluation of
`pytest-reportlog` before any bespoke schema post-0.6.

**Original proposal:** define `pytest-receptor.events@1` and implement a lossless
normalized event collector writing a versioned JSONL artifact, as the foundation
under all renderers.

**Why it was deferred and narrowed:** `pytest-reportlog` already streams one JSON
object per report to a file, including collection reports and session finish, and
already works under xdist. Before building a bespoke schema the project must
demonstrate that it is insufficient. The architecture proposal remains the
reference for this work; only the assumption that it must be built from scratch,
and built first, was superseded.

For 0.6 the same need — omitted detail must be recoverable without re-running the
suite — is met by writing the complete agent-format report to
`.pytest_cache/receptor/last-run.txt`.

---

## 7. "Lossless" as a durability claim

**Superseded by:** "evidence-preserving during normal pytest lifecycle
operation" (PR-DOC-004).

No pytest plugin can guarantee complete evidence after `SIGKILL`, a segmentation
fault, host loss, or storage exhaustion. The narrower claim is defensible; the
original one was not.

---

## 8. The original token-savings benchmark baseline

**Superseded by:** a configured-pytest baseline (PR-REL-002).

The published table compared the receptor against pytest's *default* output and
reported figures such as 87.94% savings on warnings and 87.88% on a green suite.
Measured against `pytest -q --no-header --tb=short`, a green two-test suite emits
roughly twelve tokens under stock pytest and roughly nine under the receptor. The
headline savings were an artifact of the baseline.

The green case is largely solved by pytest's own flags. The project's real and
unique saving is the failure cascade, which the original table showed at its
weakest (27-48%) because it was measured per-scenario rather than at realistic
scale.

---

## 9. Upstreaming `--receptor` into pytest core as a project goal

**Superseded by:** an explicit non-goal for 0.6.

The original issue proposed a phased path: prove the idea as a plugin, then
evaluate adopting the flag or a receptor hook into pytest core. Given pytest's
core-minimization philosophy this is unlikely to be accepted, and planning around
it distorts priorities. The plugin path is the product. If core adoption ever
happens it will be a consequence of adoption, not a milestone to design for.

---

## Appendix: the original development guide

Preserved verbatim. This was `draft_ideas.md`. Sections 1 and 2 remain an
accurate statement of the project's motivation and are still worth reading.
Section 3 is superseded: entries 1 and 5 above replaced its technical pillars,
and the proposal to extract raw `ExceptionInfo` attributes was never implemented
— the plugin instead parsed formatted `longrepr` text, which is the architectural
defect recorded as PR-ARCH-001.

---

### Development Guide: `pytest-receptor`

#### 1. The Why (The Vision)

The software development ecosystem is undergoing a paradigm shift. It is increasingly common for `pytest` to be executed not by a human in their terminal, but by **AI Agents and LLM-native CLIs** (such as Claude Code, Codex CLI, Aider, or autonomous TDD loops).

##### The Current Problem

`pytest` was designed at its core for human eyes. Its standard output (`stdout`) includes progress bars, visual decorations (`====`), ANSI colors, and redundant source code blocks in *tracebacks*.

* For a human, this is visual ergonomics.
* For a Language Model (LLM), this is **semantic noise and a massive waste of context tokens**, increasing the cost and latency of the development loop.

On the other hand, current "tricks" like `--tb=line -q` shorten the text but **blind the agent**, as they remove critical structural details (such as complex diffs of dictionaries or objects that failed in an `assert`), causing the AI to hallucinate corrections in loops.

---

#### 2. The What (The Goal)

The goal of `pytest-receptor` is to introduce the concept of a **Receptor (Consumer Profile)** to the Python testing ecosystem. We want to decouple the internal execution logic of tests from the cosmetic way they are reported, optimizing the output based on *who* will digest the information.

The plugin exposes a new CLI flag:

```bash
pytest --receptor=[human|llm|ci]
```

* **`--receptor=human` (Default):** Preserves pytest's classic, visual, and user-friendly behavior.
* **`--receptor=llm`:** An output designed purely for Transformer architectures. It aims for maximum **semantic information density** at the lowest possible token cost.
* **`--receptor=ci`:** A clean and flat output optimized for traditional log engines (Jenkins, GitHub Actions) without interactive animations.

---

#### 3. The How (Initial Implementation Ideas)

To build the `--receptor=llm` variant in a solid and efficient way, we base it on the following technical pillars:

##### A. Efficient Output Heuristics

* **Silence on Success (Green Suite):** If all tests pass, no files or environments are listed. The plugin responds with a single atomic string: `OK: 42 passed in 1.4s`. Zero tokens wasted on successful regressions.
* **Mutilating Redundant Code:** In case of failure, we **do not** print the surrounding source code lines of the exception. The AI agent already has the source files indexed in its workspace context; printing the code back into `stdout` is pure redundancy.

##### B. Semantic Density via Minified XML/Markdown

Instead of formatting tables or dashes (`----`), we wrap failures in lightweight structural tags (e.g., `<test_failures>`, `<failure_group>`). Modern language models have been heavily trained on web data (HTML/XML); their attention mechanisms identify and process the boundaries of these tags with drastically less context noise than arbitrary plain text.

##### C. Injection Strategy via Hooks

We will not clean the text using string post-processing (which wastes CPU cycles). Instead, we intercept the `pytest` lifecycle using its native hooks:

1. Use `pytest_addoption` to register the flag.
2. Intercept `TerminalReporter` in `pytest_configure`.
3. Override or short-circuit `pytest_runtest_logreport` when `--receptor=llm` is active, extracting the raw attributes of `ExceptionInfo` (`err.type`, `err.value`, and the exact frame location) to serialize them directly into our token-optimized format.
