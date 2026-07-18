# Original Upstream Feature Request

**Status:** historical record. This is the pytest issue that started the project,
preserved as written.

> **Note.** The problem statement still holds and remains the clearest summary of
> why the project exists. Three parts of the proposed solution do not, and the
> author has said so publicly rather than leaving the record uncorrected:
> [a follow-up comment](https://github.com/pytest-dev/pytest/issues/14710#issuecomment-5012232396)
> on the issue itself retracts the minified-XML syntax, the "token attention
> optimization" rationale behind it, and the `OK: {count} passed in {time}s`
> output line, which is the specification of the defect that motivated 0.6.
>
> The upstream position also changed. `--receptor` in core is no longer sought;
> an external plugin is sufficient, and the comment invites the issue to be
> closed. What the implementation surfaced instead were two pytest API problems
> that outlive the proposal, and those are what we are pursuing upstream:
>
> - [pytest-dev/pytest#14720](https://github.com/pytest-dev/pytest/issues/14720)
>   — `--tb` affects how `longrepr` is *built*, not only how it is displayed, so
>   a plugin cannot suppress traceback output without destroying the data it
>   wanted to summarise. Our own suppression is a workaround that exploits this.
> - `--no-summary` gates the whole `pytest_terminal_summary` hook, so a plugin
>   quietening pytest silences every other plugin too. Reported in the same
>   comment; not yet a separate issue.
>
> See `superseded_proposals.md` entries 1 and 9.

---

#### What's the problem this feature will solve?
With the massive adoption of terminal-based AI Agents (such as Claude Code, Codex CLI, Aider, and custom LLM-driven TDD loops), pytest is increasingly being executed by non-human actors. 

Currently, agents parse stdout or rely on heavy workarounds. Standard human-readable layouts (verbosity, ANSI colors, repeated source code blocks in tracebacks, progress bars) consume an immense amount of context tokens unnecessarily, increasing API costs and execution latency. 

Conversely, using aggressive existing flags like --tb=line -q drops crucial failure context (such as complex multi-line dictionary or object diffs), forcing the agent to run blind, hallucinate fixes, and fall into loops. Relying only on process exit codes (0/1) tells the agent THAT something failed, but not WHAT failed, requiring extra tool calls to read secondary logs.

#### Describe the solution you'd like
We propose introducing a native --receptor (recipient/sink) architecture to decouple the consumer profile from the framework's core reporting logic. Instead of just a cosmetics-based --output-format, a --receptor flag tells pytest WHO is digesting the data, allowing the framework to optimize for token density, semantic structure, and context windows.

Example command:
pytest --receptor=llm

##### Behavior and Technical Specifications by Receptor
To protect backward compatibility, --receptor=human remains the default, preserving 100% of the current pytest behavior. The framework will switch its rendering heuristics completely when --receptor=llm is active:

* On Success (Green Suite): Completely suppress test lists, headers, and environment blocks. Output a single, atomic, token-efficient string: OK: {count} passed in {time}s.
* On Failure (Red Suite):
  * Strip all visual text-decorations (no ====, no horizontal lines, no progress percentages, no ANSI colors).
  * No source code redundancy: Do not print the surrounding lines of code where the exception occurred (the AI agent already has the source files in its context window or can inspect them independently).
  * High semantic density: Provide only the file path, line number, exception type, and the exact raw comparison diff wrapped in clean, lightweight semantic delimiters (like minified XML tags) that maximize Transformer attention efficiency.

##### Proposed Taxonomy
* --receptor=human (Default: Rich terminal UI, tracebacks, progress bars)
* --receptor=llm (Ultra-dense, zero-redundancy, token-optimized for AI)
* --receptor=machine / ci (Optimized for standard CI/CD logging systems without interactive noise)

#### Alternative Solutions
We have considered using pytest-json-report or custom shell wrappers (pytest -q --tb=line | grep ...). However, these approaches either blind the agent to complex assert diffs or introduce heavy token overhead by forcing the agent to ingest entire JSON structures back into its prompt context. 

While plugins can dump JSON or custom logs, forcing every AI CLI developer or team to maintain custom intermediary wrappers to clean stdout is inefficient, fragmented, and error-prone. A native, zero-config --receptor=llm would establish pytest as the gold standard for AI-native test runners.

#### Additional context
##### Phased Rollout Strategy (Starting as a Community Plugin)
We understand and respect pytest's strict core-minimization philosophy. Therefore, this architecture doesn't necessarily need to land in the core codebase on day one. 

We propose a phased approach:
1. Phase 1 (Proof of Concept): Implement this design as an external plugin (pytest-receptor or pytest-llm-output) to refine the --receptor=llm token-saving heuristics and gather real-world telemetry from AI CLI users.
2. Phase 2 (Core Hook/Flag Adoption): Once stabilized and widely adopted by the community/AI tools, evaluate upstreaming the --receptor flag or providing a native hook so that third-party plugins can register custom receptors smoothly without hacking the TerminalReporter.

##### Implementation Strategy (How it could work underneath)
Instead of adding heavy formatting logic to the core or relying on string post-processing, pytest could decouple its terminal reporter hook (_pytest.terminal.TerminalReporter).
* The Receptor Hook Interface: When pytest_runtest_logreport fires, the framework queries the active receptor strategy.
* Short-circuiting the Traceback Generator: Under --receptor=llm, the traceback formatting bypasses _pytest._code.code.ReprTraceback's heavy layout builder. It directly extracts the raw ExceptionInfo attributes (err.type, err.value, and the exact failing frame location) and serializes them in a compact format.
* Token Attention Optimization: Failure reports can be wrapped in plain text markup tags (like <test_failure>...</test_failure>). Modern Transformers are natively trained on massive datasets containing HTML/XML; they process these boundaries with significantly lower attention-mechanism noise than arbitrary lines of dashes (-----).

