---
name: analyze-phase-3-semantic
description: "Invoke when running Analyze Phase 3 to dispatch the selected semantic reviewer sub-agents and merge their findings."
purpose: Analyze Phase 3 — dispatch selected semantic reviewers and merge findings
loaded_by: workflows/analyze.md
version: 1.0
---

<!-- toc -->

- [Phase 3: Semantic Review](#phase-3-semantic-review)
  - [Planned Multi-Reviewer Dispatch](#planned-multi-reviewer-dispatch)
  - [Legacy Single-Dispatch-Per-Methodology Matrix](#legacy-single-dispatch-per-methodology-matrix)

<!-- /toc -->

```text
UNIT AnalyzePhase3Semantic

PURPOSE:
  Dispatch selected semantic reviewer sub-agents and merge findings, using
  either a planned execution plan or the legacy per-methodology matrix.

STATE:
  PARTIAL: false | true
    default: false
    note: may be set by an earlier phase; do not reset to false if already true

WHEN:
  deterministic gate is PASS OR SKIPPED (with validator availability proof)
  OR SEMANTIC_ONLY == true

DO:
  REQUIRE REVIEWER_PLAN_RESOLVED is set by phase-2.5-reviewer-plan.md
    IF REVIEWER_PLAN_RESOLVED is unset:
      EMIT "Reviewer plan is unset. Routing back to Phase 2.5 to rebuild the plan."
      CONTINUE workflows/analyze/phase-2.5-reviewer-plan.md § Storage Choice
  IF REVIEWER_PLAN_RESOLVED == cancelled_partial_cache:
    EMIT disclosed reviewer-plan cache state from Phase 2.5
    STOP_TURN (do not enter Phase 3)
  IF PARTIAL != true:
    SET PARTIAL = false
  REQUIRE inline-fallback-probe.md has run before any cf-* dispatch
  IF REVIEWER_EXECUTION_PLAN is non-null:
    CONTINUE PlannedMultiReviewerDispatch
  IF REVIEWER_PLAN_RESOLVED is one of:
      auto_skipped_inline_fallback | auto_skipped_no_methodology | auto_skipped_explain_mode:
    CONTINUE LegacySingleDispatch
  ELSE:
    EMIT "Reviewer plan is in an unexpected state (REVIEWER_PLAN_RESOLVED={value}). Routing back to Phase 2.5 to rebuild the plan."
    CONTINUE workflows/analyze/phase-2.5-reviewer-plan.md

UNIT PlannedMultiReviewerDispatch

PURPOSE:
  Execute REVIEWER_EXECUTION_PLAN in dependency order with optional parallelism.

DO:
  Re-validate plan immediately before dispatch:
    - every active methodology has at least one task
    - union of path_partition per methodology covers every applicable input path
    - partitions for same methodology are disjoint
    - every reviewer matches task's methodology
    - every parallel_groups[].task_ids names an existing task
    - every parallel_groups[].depends_on references an earlier group
    - each parallel_groups[].depends_on group has completed before its group runs
  IF re-validation fails:
    EMIT failure details
    Route back to phase-2.5-reviewer-plan.md: ask whether to rerun planner or stop
    FORBID entering legacy single-dispatch matrix from a failed or stale plan
    STOP_TURN
  FOR each parallel group in dependency order:
    Build one reviewer dispatch payload per task (replace path inputs with task's path_partition):
      artifact tasks          -> target_paths = task.path_partition
      code / code-bug tasks   -> code_paths   = task.path_partition
      prompt / prompt-bug     -> target_paths = task.path_partition (already filtered)
      consistency tasks       -> target_paths = task.path_partition (planner emits at most one)
    IF INLINE_FALLBACK == false: dispatch tasks in same group in parallel
    IF INLINE_FALLBACK == true:  run tasks sequentially; EMIT one-line parallelism-degraded warning
    Parse each reviewer return:
      IF review_result.type == "VALIDATION_REPORT":
        REQUIRE matching "Validation Report — <Section>" block and findings JSON
      IF checkpoint.type == "PARTIAL_CHECKPOINT":
        REQUIRE matching "Partial Checkpoint — <Section>" block, checkpoint JSON, findings JSON
        Mark task partial; SET PARTIAL = true
        Store checkpoint in semantic_partial_checkpoints
        Merge only findings backed by already-covered evidence
        FORBID requiring Validation Report block for that task
        FORBID treating missing validation-report block as reviewer failure
    IF any planned task fails:
      Surface failing task id and reviewer; keep collected findings
      Mark task's parallel group as failed
      Before dispatching each later group:
        Compute transitive dependency set from parallel_groups[].depends_on
        Mark BLOCKED_BY_FAILED_DEP any group depending on a failed group
        Continue only with groups whose transitive dependency set has no failed group
      When all unblocked groups complete:
        CONTINUE workflows/analyze/phase-3-to-4-checkpoint.md with PARTIAL=true
    IF any task returned PARTIAL_CHECKPOINT:
      Finish independent unblocked groups
      CONTINUE workflows/analyze/phase-3-to-4-checkpoint.md with PARTIAL=true
        carry semantic_partial_checkpoints, completed findings, dispatch statuses, resume inputs
  Merge findings per namespace: V, Ra, Rc, Rcb, Rp, Rpb, Rcons
  Renumber within each namespace from 001 after merge (contiguous IDs)
  CONTINUE workflows/analyze/phase-3-to-4-checkpoint.md

UNIT LegacySingleDispatch

PURPOSE:
  Dispatch one sub-agent per active methodology and merge findings.

DO:
  For each applicable condition, dispatch the named sub-agent and merge findings:
    PROMPT_REVIEW=true AND PROMPT_BUG_REVIEW=true ->
      DISPATCH cf-semantic-reviewer-prompt AND cf-prompt-bug-finder in parallel
      Merge under Rp (prompt-reviewer) and Rpb (bug-finder) namespaces
    PROMPT_REVIEW=true AND PROMPT_BUG_REVIEW=false ->
      DISPATCH cf-semantic-reviewer-prompt
    PROMPT_BUG_REVIEW=true AND PROMPT_REVIEW=false ->
      DISPATCH cf-prompt-bug-finder
    ARTIFACT_REVIEW=true OR (TARGET_TYPE == artifact AND no prompt/code methodology owns target) ->
      DISPATCH cf-semantic-reviewer-artifact
    TARGET_TYPE == code OR CODE_REVIEW=true ->
      DISPATCH cf-semantic-reviewer-code
    CODE_BUG_REVIEW=true ->
      DISPATCH cf-code-bug-finder
    CONSISTENCY_REVIEW=true AND len(target_paths) >= 2 ->
      DISPATCH cf-semantic-reviewer-consistency
      IF fewer than two paths available:
        EMIT "consistency-skipped: single-target"
  For PARTIAL_CHECKPOINT returns:
    SET PARTIAL = true
    Store in semantic_partial_checkpoints; merge supported findings
    CONTINUE workflows/analyze/phase-3-to-4-checkpoint.md with PARTIAL=true
    FORBID claiming clean semantic coverage until checkpoint resumed and completed
  Merge findings per namespace: V, Ra, Rc, Rcb, Rp, Rpb, Rcons (numbering from 001)

RULES:
  - MUST run inline-fallback-probe.md before any cf-* sub-agent dispatch
  - MUST set PARTIAL=false on entry unless already set by an earlier phase
  - MUST REQUIRE REVIEWER_PLAN_RESOLVED is set before entering
  - MUST_NOT enter Phase 3 when REVIEWER_PLAN_RESOLVED=cancelled_partial_cache
  - MUST_NOT enter legacy single-dispatch matrix from a failed or stale plan
  - MUST_NOT silently degrade a failed plan to REVIEWER_PLAN_RESOLVED=auto_skipped_inline_fallback
  - MUST support PARTIAL_CHECKPOINT only for reviewers whose contract declares it
  - MUST_NOT invent a partial shape for artifact or consistency reviewers unless
    their agent prompt defines it
  - MUST renumber findings within each namespace from 001 after merge
  - MUST_NOT dispatch Phase 3 semantic reviewers when EXPLAIN_MODE=true

NOTES:
  Dispatch inputs per methodology:
    artifact reviewer:  target_paths={PATHS}, kit rules, checklist, template,
                        examples/example.md, cross refs, rules_mode, traceability_mode
    code reviewer:      design_artifact_path, code_paths=code_targets,
                        diff_scope, cross refs, rules_mode, traceability_mode, kit_rules_path
    code bug finder:    design_artifact_path, code_paths, diff_scope, cross refs,
                        rules_mode, kit_rules_path
    prompt reviewer:    target_paths=prompt_targets, kit_rules_path, rules_mode, cross refs
    prompt bug finder:  same prompt_targets, kit_rules_path, rules_mode, cross refs
    consistency:        target_paths={PATHS}, baseline_path, kit_rules_path,
                        rules_mode, namespace_prefix="Rcons"

  For change-review code dispatch: code_paths = diff_scope.review_targets filtered to code-only.
  For change-review prompt dispatch: filter diff_scope.review_targets to prompt-typed targets.

  Pre-dispatch fail-stop and Mode B degradation rules:
    {cf-studio-path}/.core/skills/studio/sub-agent-dispatch.md
```

## Phase 3: Semantic Review

Run when the gate is `PASS`, if it is `SKIPPED` with Validator availability proof, or when `SEMANTIC_ONLY=true`.
Requires: `workflows/shared/inline-fallback-probe.md` before any
`cf-*` sub-agent dispatch. Pre-dispatch fail-stop and Mode B
degradation rules are defined in
`{cf-studio-path}/.core/skills/studio/sub-agent-dispatch.md`.

Set `PARTIAL = false` on entry to this phase unless already set by an
earlier phase in the same session.

Prerequisite: `REVIEWER_PLAN_RESOLVED` MUST be set by
`workflows/analyze/phase-2.5-reviewer-plan.md`. If unset, fail-stop and route
back to that file's Storage Choice section.

If `REVIEWER_PLAN_RESOLVED=cancelled_partial_cache`, do NOT enter Phase 3.
Stop the current analyze sub-flow and leave the saved-or-partial reviewer-plan
cache state exactly as disclosed by Phase 2.5.

### Planned Multi-Reviewer Dispatch

If `REVIEWER_EXECUTION_PLAN` is non-null (Phase 2.5 produced a plan), execute
it instead of the single-dispatch-per-methodology matrix below:

1. Re-validate the plan immediately before dispatch:
   - every active methodology has at least one task
   - the union of `path_partition` for each methodology covers every applicable
     input path
   - partitions for the same methodology are disjoint
   - every `reviewer` matches the task's `methodology`
   - every `parallel_groups[].task_ids` entry names an existing task
   - every `parallel_groups[].depends_on` reference names an earlier group
   - each `parallel_groups[].depends_on` group has completed before its group runs
   If plan re-validation fails, fail-stop before dispatching any reviewer and
   route back to `workflows/analyze/phase-2.5-reviewer-plan.md` to ask whether
   to rerun the planner or stop with the validation errors. Do not clear the
   plan into `REVIEWER_PLAN_RESOLVED=auto_skipped_inline_fallback`, and do not
   enter the single-dispatch matrix from a failed or stale plan.
2. For each parallel group in dependency order, build one reviewer dispatch
   payload per task by taking the methodology's canonical dispatch inputs from
   the matrix below and replacing the path inputs with the task's
   `path_partition`:
   - artifact tasks → `target_paths = task.path_partition`
   - code / code-bug tasks → `code_paths = task.path_partition`
   - prompt / prompt-bug tasks → `target_paths = task.path_partition`
     (already filtered to prompt files by the planner)
   - consistency tasks → `target_paths = task.path_partition` with the full
     set (planner emits at most one consistency task)
3. If `INLINE_FALLBACK=false`, tasks in the same group MAY be dispatched in
   parallel. If `INLINE_FALLBACK=true`, run the tasks sequentially in listed
   order and emit a one-line warning that planned parallelism degraded to
   sequential inline execution.
4. Parse each reviewer return before merging:
   - `review_result.type = "VALIDATION_REPORT"`: require the matching
     `Validation Report — <Section>` block and findings JSON.
   - `checkpoint.type = "PARTIAL_CHECKPOINT"`: require the matching
     `Partial Checkpoint — <Section>` block, checkpoint JSON, and findings
     JSON. Mark the task `partial`, set `PARTIAL=true`, preserve the
     checkpoint under `semantic_partial_checkpoints`, and merge only findings
     backed by already-covered evidence. Do not require a
     `Validation Report — <Section>` block for that task, and do not treat the
     missing validation-report block as a reviewer failure.
5. Merge findings across tasks per namespace (`Ra`, `Rc`, `Rcb`, `Rp`, `Rpb`,
   `Rcons`, `V`). Renumber within each namespace from `001` after the merge
   so finding IDs remain contiguous in the final output.
6. If any planned task fails, surface the failing task id and reviewer, keep
   already-collected findings, and mark that task's parallel group as failed.
   Before dispatching each later group, compute the transitive dependency set
   from `parallel_groups[].depends_on`. Skip and mark `BLOCKED_BY_FAILED_DEP`
   any group that depends, directly or indirectly, on a failed group. Continue
   only with groups whose transitive dependency set contains no failed group.
   When all unblocked groups are complete, route to
   `workflows/analyze/phase-3-to-4-checkpoint.md` with `PARTIAL=true`,
   carrying the completed findings plus the failed/skipped group state. If the
   failed group has no downstream dependents, independent groups still run.
7. If any task returned `PARTIAL_CHECKPOINT`, finish any independent
   unblocked groups, then route to
   `workflows/analyze/phase-3-to-4-checkpoint.md` with `PARTIAL=true`,
   carrying `semantic_partial_checkpoints`, completed findings, dispatch
   statuses, and resume inputs. Phase 4 MUST surface the result as partial
   unless the checkpoint is resumed and completed.

When `REVIEWER_EXECUTION_PLAN` is null and `REVIEWER_PLAN_RESOLVED` is one of
`auto_skipped_inline_fallback`, `auto_skipped_no_methodology`, or `auto_skipped_explain_mode`,
fall through to the legacy single-dispatch-per-methodology matrix below. If the
plan is null for any other `REVIEWER_PLAN_RESOLVED` value, emit to the user:
"Reviewer plan is in an unexpected state (REVIEWER_PLAN_RESOLVED={value}). Routing back to Phase 2.5 to rebuild the plan."
Then fail-stop and route back to `workflows/analyze/phase-2.5-reviewer-plan.md`; a missing, failed, or
partial planner result must not silently degrade to the legacy matrix.

### Legacy Single-Dispatch-Per-Methodology Matrix

Each sub-agent owns exactly one review methodology. If multiple flags apply,
dispatch multiple sub-agents and merge findings.

| Condition | Dispatched sub-agent |
|---|---|
| `PROMPT_REVIEW=true` AND `PROMPT_BUG_REVIEW=true` | dispatch BOTH `cf-semantic-reviewer-prompt` AND `cf-prompt-bug-finder` in parallel; merge findings under a single namespaced ID prefix (`Rp` for prompt-reviewer, `Rpb` for bug-finder) |
| `PROMPT_REVIEW=true` AND `PROMPT_BUG_REVIEW=false` | `cf-semantic-reviewer-prompt` |
| `PROMPT_BUG_REVIEW=true` AND `PROMPT_REVIEW=false` | `cf-prompt-bug-finder` |
| `ARTIFACT_REVIEW=true` or (`TARGET_TYPE == artifact` and no prompt/code methodology owns the target) | `cf-semantic-reviewer-artifact` |
| `TARGET_TYPE == code` or `CODE_REVIEW=true` | `cf-semantic-reviewer-code` |
| `CODE_BUG_REVIEW=true` | `cf-code-bug-finder` |
| `CONSISTENCY_REVIEW=true` and `len(target_paths) >= 2` | `cf-semantic-reviewer-consistency` |

Dispatch inputs:
- artifact reviewer: `target_paths={PATHS}`, kit rules, checklist, template,
  `examples/example.md`, cross refs, `rules_mode`, `traceability_mode`.
- code reviewer: `design_artifact_path`, `code_paths = code_targets`, where
  `code_targets` is the Phase 0 typed code target set derived from
  `diff_scope.changed_files` for change review, otherwise `{PATHS}` filtered to
  code files; when dispatching the code reviewer for change-review, set
  `code_paths = diff_scope.review_targets` filtered to code-only targets;
  `diff_scope` from Phase 0, cross refs, `rules_mode`,
  `traceability_mode`, `kit_rules_path`.
- code bug finder: `design_artifact_path`, `code_paths`, `diff_scope`, cross
  refs, `rules_mode`, `kit_rules_path`.
- prompt reviewer: `target_paths = prompt_targets`, where `prompt_targets`
  filters `diff_scope.review_targets` (when `CHANGE_REVIEW=true`) or
  `{PATHS}` to instruction/workflow/prompt files; for change-review prompt
  dispatch, the orchestrator filters `diff_scope.review_targets` to
  prompt-typed targets and uses them as `paths`; prompt-typed targets are paths
  matching `workflows/**`, `skills/studio/**/*.md`, `requirements/**/*.md`,
  `AGENTS.md`, `SKILL.md`, agent prompt files, and prompt config files;
  `kit_rules_path`, `rules_mode`, cross refs.
- prompt bug finder: same `prompt_targets`, `kit_rules_path`, `rules_mode`,
  cross refs.
- consistency reviewer: `target_paths={PATHS}`, `baseline_path`,
  `kit_rules_path`, `rules_mode`, `namespace_prefix="Rcons"`; skip and log
  `consistency-skipped: single-target` if fewer than two paths are available.

Each reviewer returns exactly one caller-visible shape:

- `VALIDATION_REPORT`: `review_result.type = "VALIDATION_REPORT"`, a
  `Validation Report — <Section>` block, and findings JSON.
- `PARTIAL_CHECKPOINT`: `checkpoint.type = "PARTIAL_CHECKPOINT"`, a
  `Partial Checkpoint — <Section>` block, checkpoint JSON, and findings JSON
  limited to already-covered evidence.

`PARTIAL_CHECKPOINT is supported only by reviewers whose contract declares it` (declared via the agent's "Output" section under "PARTIAL_CHECKPOINT support" — see e.g. `skills/studio/agents/cf-semantic-reviewer-prompt.md`).
For reviewers without that contract, budget exhaustion is a blocking reviewer
failure or requires the Phase 3 → Phase 4 checkpoint; do not invent a partial
shape for artifact or consistency reviewers unless their agent prompt defines it.

For `PARTIAL_CHECKPOINT`, set `PARTIAL=true`, store the checkpoint in
`semantic_partial_checkpoints`, merge any supported findings, and route through
`workflows/analyze/phase-3-to-4-checkpoint.md` before Phase 4 output. The
orchestrator MUST NOT dead-end on the absence of `Validation Report —
<Section>` for that reviewer and MUST NOT claim clean semantic coverage until
the checkpoint is resumed and completed.

Merge and namespace findings: `V`, `Ra`, `Rc`, `Rcb`, `Rp`, `Rpb`, `Rcons`,
numbering from `001` within each namespace.

When `EXPLAIN_MODE=true`, storytelling phases replace this file and no semantic
reviewer sub-agents are dispatched.
