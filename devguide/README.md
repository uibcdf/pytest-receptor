# Development Guide

Internal design and planning documents for `pytest-receptor`. Public
documentation lives in `docs/`.

## Read this first

If you are picking the project up, read in this order:

1. **`scope_0.6.md`** — what the next release is, and why it is deliberately
   small. Start here.
2. **`audit_action_register_2026-07-17.md`** — the complete work queue. Every
   task in the project has an identifier here.
3. **`critical_audit_2026-07-17.md`** — why the plan looks the way it does.

If you are here because you are piloting the receptor on another project, read
**`molsysmt_pilot.md`** instead; it is written for you and assumes none of the
above.

Everything else is reference material for work that comes later.

## Documents

| Document | Kind | Status |
| --- | --- | --- |
| `scope_0.6.md` | Plan | **Authority for the next release.** Defines the objective function, what ships, what does not, the output design, and acceptance criteria. |
| `audit_action_register_2026-07-17.md` | Queue | **Live.** 43 identified items with severity, release, phase, and status. The single place where nothing may be missing. |
| `critical_audit_2026-07-17.md` | Assessment | Historical record, still accurate. The 2026-07-17 read-only review that found the correctness defects. Not updated as items are fixed; the register tracks that. |
| `evidence_preserving_architecture_proposal.md` | Proposal | Post-0.6 reference. Its ambition is intact but its sequencing was superseded by `scope_0.6.md`. See the header note in that file. |
| `trust_and_adoption_criteria.md` | Criteria | Post-0.6 reference. Adoption levels, trust invariants, promotion gates, and the MolSysMT dogfooding program. |
| `smonitor_and_molsyssuite_integration.md` | Exploration | Post-0.6, gated. Not an accepted contract. Nothing in it may be implemented before the extension protocol is designed against a neutral dummy producer. |
| `molsysmt_pilot.md` | Brief | **Active.** What the MolSysMT team needs in order to run the receptor on their suite, what we need back from them, and what the plugin does not do yet. |
| `pending_bugs/` | Inbox | **Active.** Untriaged defect reports. A disagreement with pytest about a run's outcome jumps the queue. |
| `resolved_bugs/` | History | Field reports that have been fixed, kept with their resolution and reproducer. Moved out of the inbox rather than deleted. |
| `pending_proposals/` | Inbox | **Active.** Untriaged design input from pilots and other projects. Everything here is either given a register identifier or moved to `superseded_proposals.md`. |
| `superseded_proposals.md` | History | Rejected and replaced proposals, preserved with the reason each was dropped. Includes the original development guide verbatim. |
| `prior_art_2026-07-19.md` | Survey | **Current.** The two other plugins with the same thesis, what they do and do not do, measured rather than read. Includes where we are *not* better, and the decision not to publish a comparative benchmark. |
| `original_issue_in_pytest.md` | History | The upstream pytest feature request that started the project. See the header note for which parts no longer hold. |

## Release model

| Release | Meaning |
| --- | --- |
| 0.6 | Correctness floor plus the agent renderer. Reliable, but the output format may still change. |
| 0.7-0.9 | Format stabilization driven by real use, plus delta mode. |
| 1.0 | Output format frozen, validated against a large real suite. |

The output format is this plugin's public API, so 1.0 is deliberately held until
dogfooding has had a chance to change it. A 0.x number communicates that the
format may move — never that a run may be lost. The reliability floor applies in
full from 0.6.

## Branches

| Branch | Why it exists | When it may go |
| --- | --- | --- |
| `main` | The project. | — |
| `event-model-v0.5` | A parallel implementation that was on `origin/main` until 0.6 replaced it. Preserved rather than deleted; five things were salvaged from it, three of them after it had been declared exhausted. | Only when all three conditions in [`pending_proposals/salvage_from_event_model_branch.md`](pending_proposals/salvage_from_event_model_branch.md) hold. Not on a date. |

## Conventions

- Every proposal must have an identifier in the register. A proposal that exists
  only in prose is untracked work.
- Superseded proposals move to `superseded_proposals.md`. They are not deleted;
  knowing why an idea was rejected is worth keeping.
- Input from outside the project lands in `pending_bugs/` (defects) or
  `pending_proposals/` (design), and is triaged into the register at release
  planning.
- Documents record decisions and evidence. Progress is tracked by status in the
  register, not by rewriting the assessments.
