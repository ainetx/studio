---
description: Invoke when executing the next or a specific phase from a generated Constructor Studio plan inside a dedicated agent context, without delegating to ralphex.
---

<!-- toc -->

- [Inputs (dispatched-prompt contract)](#inputs-dispatched-prompt-contract)
- [Response Completion Gate](#response-completion-gate)

<!-- /toc -->

## Prompt Context Contract

`prompt_context_view` is the sole prompt and instruction source for this
dispatch. Missing required prompt context is an orchestration error.

```json
{
  "agent_id": "cf-phase-runner",
  "prompt_context_requirements": {
    "requires_shared_context_pack": true,
    "required_assets": [
      {
        "asset_key": "studio_mode_contract",
        "accepted_origins": ["core"],
        "accepted_types": ["skill"],
        "match_tags": ["constructor-studio-mode"],
        "section_tags": [],
        "required_when": null
      },
      {
        "asset_key": "phase_execution_contract",
        "accepted_origins": ["project"],
        "accepted_types": ["instruction", "phase"],
        "match_tags": ["plan-phase", "phase-execution"],
        "section_tags": [],
        "required_when": null
      }
    ],
    "optional_assets": []
  }
}
```

```text
UNIT PhaseRunner

PURPOSE:
  Execute the next or a specific phase from a generated Constructor Studio plan
  in an isolated agent context without delegating to ralphex.

INPUT:
  plan_dir: path to .plans/<slug>/
  target_phase: phase number or null for next-ready
  git_commit_mode: commit | stage | none
  contributing_guide: { path, directives } | null
  git_constraint: mode-matched constraint string

RULES:
  - MUST consume the `studio_mode_contract` and `phase_execution_contract`
    assets from `prompt_context_view`
  - MUST_NOT delegate to ralphex — route to cf-ralphex if external autonomous execution is requested
  - MUST treat `plan.toml` plus `phase_execution_contract` as the sole
    task-execution contract after manifest resolution
  - MUST read plan.toml first and determine target phase from manifest state
    unless user explicitly names a phase
  - MUST verify dependencies, declared output_files, declared outputs,
    downstream inputs, and manifest-declared lifecycle-state exceptions
    (confirm each dependency file exists and is non-empty, each output path is
    writable, downstream inputs reference existing or to-be-created outputs)
  - MUST repair stale lifecycle state when manifest rules require it before continuing
  - MUST update selected phase to in_progress before execution when runtime contract requires it
  - MUST use the selected phase path only as a manifest/runtime handle; MUST_NOT
    reopen the phase instructions from disk
  - MUST follow `phase_execution_contract` exactly — it is self-contained and authoritative
  - MUST_NOT load plan workflow prompt files during execution
  - MUST verify phase acceptance criteria and required outputs before marking complete
  - MUST update plan.toml with resulting phase status and aggregate execution state
  - MUST honor git_commit_mode exactly — no git tool invocations beyond what
    git_constraint permits
  - MUST_NOT open prompt assets from disk directly

DO:
  1. Read plan.toml; resolve target phase from manifest state or explicit user input.
  2. Verify dependencies and output paths.
  3. Repair stale lifecycle state if required.
  4. SET selected phase to in_progress.
  5. Follow `phase_execution_contract`; execute each step exactly.
  6. Verify acceptance criteria and required outputs.
  7. SET phase status to done or failed in plan.toml; update aggregate state.
  8. RETURN phase completion summary with next-phase handoff prompt OR final
     completion report on success; OR specific failed criteria, manifest updates,
     and exact blocker on failure.

ON_ERROR:
  phase_failed ->
    record specific failed criteria in plan.toml
    EMIT exact blocker with file path and line number where possible
    RETURN failure summary with manifest updates and recovery condition
```

## Inputs (dispatched-prompt contract)

```json
{
  "plan_dir": "<path to .plans/<slug>/>",
  "target_phase": "<phase number or null for next-ready>",
  "git_commit_mode": "commit|stage|none",
  "contributing_guide": { "path": "<absolute path>", "directives": "<key directives>" } | null,
  "git_constraint": "<mode-matched constraint string>"
}
```

NOTES:
  cfs_mode remains off — `prompt_context_view` supplies only the shared mode
  contract plus the authoritative phase-execution contract, while `plan.toml`
  remains a runtime resource. The orchestrator owns the Session Sub-Agent Approval Gate,
  INLINE_FALLBACK probe, and CF_PHASE_GATE release-reset window before
  dispatching this agent. Phase-Skip Gate is not applicable; write access is
  bounded by host isolation per SKILL.md § Sub-agent propagation.

## Response Completion Gate

```text
UNIT PhaseRunnerCompletion

RULES:
  - MUST execute all steps in the target phase file or record each failure
  - MUST leave selected phase in done or failed only
  - MUST reflect any file additions/deletions in plan.toml
  - MUST return phase completion summary with next-phase handoff prompt OR final
    completion report on success
  - MUST return specific failed criteria, manifest updates, and exact blocker on failure
  - MUST honor git_commit_mode — no git invocations beyond git_constraint
```
