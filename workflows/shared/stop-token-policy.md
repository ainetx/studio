---
name: stop-token-policy
description: "Invoke when loading the canonical stop-token (stop/enough/done) routing policy applicable to every workflow prompt."
purpose: Canonical stop-token (stop/enough/done) routing for every workflow prompt
loaded_by: workflows/generate.md, workflows/analyze.md, workflows/plan.md, workflows/workspace.md, workflows/workspace/phase-1-discover.md, workflows/workspace/phase-2-configure.md, workflows/workspace/phase-3-generate.md, workflows/workspace/phase-4-validate.md, workflows/workspace/next-steps.md
version: 1.0
---

<!-- toc -->

- [Stop-Token Policy (canonical)](#stop-token-policy-canonical)

<!-- /toc -->

## Stop-Token Policy (canonical)

At any user-input prompt in this workflow, the tokens `stop`, `enough`, or `done` (case-insensitive, exact-match — not as substrings of a longer reply) end the current interactive sub-flow and route to the safest exit for the phase that emitted the prompt:

- `workflows/generate/phase-0.7/round-loop.md` and `workflows/generate/phase-0.7/wrap-handoff.md` (brainstorm round loop or wrap-up prompt) → set `state.topic_current = None`; carry current `state.decisions` forward; unanswered questions become `open_questions`; proceed to `workflows/generate/phase-1-collect.md` with whatever was already approved.
- `workflows/generate/phase-5/phase-5.3-findings.md` (all-mechanical fast-path announcement, before auto-fix dispatch) → treat as `workflows/generate/phase-5/phase-5.4-approval.md` option `4`: skip the auto-fix dispatch, set `remaining_findings = all_findings`, `loop_exit = "manual-handoff"`, proceed to `workflows/generate/phase-6/index.md`.
- `workflows/generate/phase-5/phase-5.4-approval.md` (mixed-iteration approval gate) → treat as option `4`: no fixes this iteration, `remaining_findings = all_findings ∪ carry_forward`, `loop_exit = "manual-handoff"`, proceed to `workflows/generate/phase-6/index.md`.
- Any other prompt (`workflows/generate/phase-0.2-review-loop-cfg.md`, `workflows/generate/phase-5/index.md` § Pre-Phase-Setup, `workflows/generate/phase-0.5-clarify.md`, `workflows/generate/phase-0.7/offer.md`, `workflows/generate/phase-1-collect.md`, `workflows/generate/phase-1.5-author-plan.md`, `workflows/generate/phase-3-summary.md`, `workflows/generate/phase-6/index.md` menus, the Review-Loop Iteration Cap Prompt, the `workflows/generate/phase-5/phase-5.2-semantic.md` inline-mode `reduce:` prompt) → cancel the current sub-flow with a one-line acknowledgement, leave any already-written files untouched, and return control to the user without proceeding further.

This block is the single source of truth for stop-token behavior. Other workflow files reference it by path (`see workflows/shared/stop-token-policy.md`) instead of restating; existing per-phase stop-token mentions are non-normative reminders only.

## Plan Workflow Stop Tokens

For `workflows/plan.md` prompts — raw-input materialization `[y/n]`, decomposition `[y/n]`, Phase 3.2A brief-checkpoint `[1]`–`[4]`, and Phase 4.2 next-steps `[1]`–`[5]` — a stop token (`stop`, `enough`, or `done`) cancels the *current sub-flow only* (the prompt at hand) and routes back to the prior phase's choice point:

- Raw-input materialization `[y/n]` prompt → treat as `n`; report `Raw-input materialization declined — continue with direct workflow if you prefer reduced guarantees` and stop (valid completion state, no further routing).
- Decomposition `[y/n]` prompt → treat as `n`; report `Decomposition declined — rework the phase boundaries and re-run /cf-constructor-plan when ready` and stop (valid completion state, no further routing).
- Phase 3.2A brief-checkpoint `[1]`–`[4]` prompt → treat as option `[4]`; set `plan.execution_status = "briefs_only"` and stop after the brief package.
- Phase 4.2 next-steps `[1]`–`[5]` prompt → cancel the current next-step sub-flow; leave already-written files untouched and return control to the user without proceeding further.
- `workflows/plan/plan-lifecycle.md` lifecycle selection prompt `[1]`–`[4]` → treat stop as option `[4]` (Manual); defer lifecycle decision to post-execution.

## Workspace Workflow Stop Tokens

For `workflows/workspace.md` prompts, a stop token (`stop`, `enough`, or `done`) routes to the safest exit for the phase that emitted the prompt:

- Phase 1 (`workflows/workspace/phase-1-discover.md`) zero-results menu `[1]`–`[3]` → treat as `[3]` (stop workspace setup); preserve scan results in state and end cleanly; no files written.
- Phase 1 standalone-vs-inline decision prompt → cancel workspace setup; no files written.
- Phase 2 (`workflows/workspace/phase-2-configure.md`) approval prompt → cancel before writing workspace config; no files written.
- Phase 3 (`workflows/workspace/phase-3-generate.md`) CLI failure recovery `[1]`–`[3]` → treat as `[3]` (abort); leave whatever partial state exists for user inspection.
- Phase 4 (`workflows/workspace/phase-4-validate.md`) validation decision point (if any) → cancel validation; report partial result.
- Post-setup next-steps menu (`workflows/workspace/next-steps.md`) → silent exit; no further menus.
