---
cf-constructor: true
type: workflow-phase
name: plan-phase-4-finalize
description: "Invoke when /cf-constructor-plan enters Phase 4 to validate the completed plan, report the result, offer next-steps, and emit the new-chat startup prompt when the user chooses execution handoff."
loaded_by: workflows/plan.md
version: 1.0
---

# Phase 4: Finalize Plan

> **Note**: `plan.toml` was already written in Phase 3.1 and briefs were written in Phase 3.2. Enter Phase 4 only if the user selected option `[1]` or `[3]` and all `phase-*` files were produced in Phase 3.3. If the user selected option `[2]` or `[4]`, stop after the brief checkpoint and do not emit `Plan created`.

Status model in `plan.toml`:
- `phases[].status`: `pending`, `in_progress`, `done`, `failed`
- `plan.execution_status`: aggregate phase execution state, independent of lifecycle handling
- `plan.lifecycle_status`: plan-file lifecycle state, independent of whether all phases are already complete

Update rules:
- all phases `pending` → `plan.execution_status = "not_started"`
- user chose option `[4]` at brief checkpoint → `plan.execution_status = "briefs_only"` (valid stop state; resume by presenting `[1]-[4]` menu)
- any phase `in_progress`, or any mix of `done` and `pending`, → `plan.execution_status = "in_progress"`
- any phase `failed` → `plan.execution_status = "failed"` until explicitly reopened or downgraded
- all phases `done` → `plan.execution_status = "done"`; `plan.lifecycle_status` may still be `ready`, `in_progress`, or `manual_action_required`

## 4.1 Validate Plan Before Handoff (MANDATORY)

> **⛔ CRITICAL**: Offer plan validation as the FIRST next step.

Before generating the startup prompt or offering execution handoff:
1. Self-validate against `{cf-constructor-path}/.core/requirements/plan-checklist.md`.
2. Report:
```text
═══════════════════════════════════════════════
Plan Self-Validation: {task-slug}
───────────────────────────────────────────────
| Category | Status |
|----------|--------|
| 1. Structural | PASS/FAIL |
| 2. Interactive Questions | PASS/FAIL |
| 3. Rules Coverage | PASS/FAIL |
| 4. Context Completeness | PASS/FAIL |
| 5. Phase Independence | PASS/FAIL |
| 6. Budget Compliance | PASS/FAIL |
| 7. Lifecycle & Handoff | PASS/FAIL |
Overall: PASS/FAIL
═══════════════════════════════════════════════
```
If any category FAILs: list issues and offer to fix them.

## 4.2 Report Plan & Offer Next Steps

If all categories PASS, report:
```text
Plan created: {cf-constructor-path}/.plans/{task-slug}/
  Phases: {N}
  Files: {file_count}
  Lifecycle: {lifecycle}
```

You may emit `Plan created` only after Phase 3.4 PASS confirms that `plan.toml`, every `brief-*`, and every compiled `phase-*` file already exist on disk. If the run stopped after brief generation or produced only downstream prompts, omit this section.

Then immediately report:
```text
Native execution options available:
  This plan can be delegated to ralphex using Cyber Constructor's native delegation feature.
  Command: {cfc_cmd} delegate "{cf-constructor-path}/.plans/{task-slug}"

Delegation prompt:
  I have a Cyber Constructor execution plan ready at:
    {cf-constructor-path}/.plans/{task-slug}

  Please delegate this plan to ralphex using Cyber Constructor's native delegation flow.

Native phase execution prompt:
  I have a Cyber Constructor execution plan ready at:
    {cf-constructor-path}/.plans/{task-slug}/plan.toml

  Please execute the next phase using Cyber Constructor's native phase runner.
```

Then present ALL of these next steps and wait for user choice before generating the startup prompt:
```text
What would you like to do next?

  [1] Validate plan thoroughly — run /cf-constructor-analyze on the plan
  [2] Execute Phase 1 natively — use Cyber Constructor's dedicated phase-runner subagent
  [3] Prepare execution handoff — generate the Phase 1 startup prompt for a downstream execution chat
  [4] Review plan files — inspect phase files before execution
  [5] Modify plan — adjust phases, add/remove content
Reply with `1`, `2`, `3`, `4`, or `5`.
[1] Suggested default before execution — verify the plan thoroughly with `/cf-constructor-analyze`.
[2] Start executing the first phase now with the native phase runner.
[3] Generate a handoff prompt for a separate execution chat.
[4] Inspect the plan files manually before deciding what to do next.
[5] Rework the plan structure or contents before execution.
```

## New-Chat Startup Prompt

When the user chooses execution handoff, emit the entire startup prompt inside a **single fenced code block**:
```text
I have a Cyber Constructor execution plan ready at:
  {cf-constructor-path}/.plans/{task-slug}/plan.toml

Please read the plan manifest, then execute Phase 1.
The phase file is self-contained — follow its instructions exactly.
After completion, report results and generate the prompt for Phase 2.
```
No explanatory text may be mixed into that code fence.
