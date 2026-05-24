---
description: "Invoke when Phase 1 inputs are approved and the author-plan offer gate must run (mandatory when sub-agents approved; offered otherwise) before Phase 3 summary."
name: generate-phase-1.5-author-plan
purpose: Generate Phase 1.5 — mandatory lightweight author-plan offer, in-memory/disk plan modes, and AUTHOR_EXECUTION_PLAN state
loaded_by: workflows/generate.md
version: 1.0
---

# Phase 1.5: Author Plan

<!-- toc -->

- [State](#state)
  - [Mandatory-Decompose Under Sub-Agent Approval](#mandatory-decompose-under-sub-agent-approval)
- [Offer](#offer)
- [Planner Dispatch](#planner-dispatch)
- [Disk Mode Rendering](#disk-mode-rendering)
- [Handoff](#handoff)

<!-- /toc -->

## State

This phase is a mandatory offer gate after Phase 1 inputs are approved and
before Phase 3 summary. The plan itself is optional for the user; the offer is
not optional for the orchestrator unless an explicit auto-skip condition
applies.

Set `AUTHOR_PLAN_OFFER_RESOLVED` to exactly one of:

- `memory`
- `disk`
- `declined`
- `auto_skipped_no_author_plan_flag`
- `auto_skipped_rules_disabled`

Set `AUTHOR_EXECUTION_PLAN` to the parsed `author_plan` JSON when
`AUTHOR_PLAN_OFFER_RESOLVED` is `memory` or `disk`; otherwise set it to `null`.
Set `AUTHOR_PLAN_CACHE_DIR` only in disk mode.

Auto-skip the offer only when one of these conditions applies:

- the user passed `--no-author-plan` in the invocation
- the KIND's `rules.md` explicitly sets `author_plan = "disabled"`

### Mandatory-Decompose Under Sub-Agent Approval

When `SUB_AGENT_SESSION_APPROVED=true` AND `INLINE_FALLBACK=false` AND no auto-skip condition applies, the author plan is **mandatory**. The `declined` / `auto_skipped_*` states are unreachable in this branch. The offer reduces to choosing the plan storage mode (memory vs disk); the planner runs unconditionally and `AUTHOR_EXECUTION_PLAN` is always non-null on exit.

Use the **mandatory offer** below in that branch. Use the **legacy optional offer** further down only when sub-agents are unapproved or inline fallback is active.

```text
Author plan (mandatory — sub-agents approved): pick storage.

I will decompose this generate task into author-worker sub-tasks, assign each
to a specialist sub-agent, and group them for parallel dispatch in Phase 4.

Reply `enter` or `memory` for in-memory plan (default), or `disk` to also save
a Markdown plan pack under `{cf-constructor-path}/.cache/generate-plans/`.

Choose `disk` if the session may be long or context may compact (plan survives compaction); choose `memory` for short sessions (no disk I/O, plan is in-context only).
```

Reply parsing (mandatory branch):

| User input | Meaning |
|---|---|
| empty / `memory` / `1` | Set `AUTHOR_PLAN_OFFER_RESOLVED=memory`; run Planner Dispatch |
| `disk` / `save` / `2` | Set `AUTHOR_PLAN_OFFER_RESOLVED=disk`; run Planner Dispatch + Disk Mode Rendering |
| stop token | Set `AUTHOR_PLAN_OFFER_RESOLVED=cancelled_by_stop_token`. Reset CF_PHASE_GATE=armed. THEN open and follow `workflows/shared/stop-token-policy.md`. Phase 4 treats this state as a valid terminal cancellation (no further author dispatch; emit the cancel message and route to the Remediation Handoff) |
| `no` / `skip` / `3` | Reject with `Decomposition is mandatory while sub-agents are approved. Reply enter/memory or disk.` and ask again |
| anything else | Reject with `Reply not recognized. Expected enter/memory or disk.` and ask again |

After parsing, skip the legacy offer and continue at § Planner Dispatch.

## Offer

Unless auto-skipped or the mandatory branch above already resolved
`AUTHOR_PLAN_OFFER_RESOLVED`, ask:

```text
Want a lightweight author plan before the final summary?

I can decompose this generate task into author-worker tasks, recommend which
author should handle each task, and mark which tasks can run in parallel.

Reply `enter` or `memory` for an in-memory plan (default), `disk` to also save
a Markdown plan pack under `{cf-constructor-path}/.cache/generate-plans/`, or
`no` to skip the author plan.
```

Reply parsing:

| User input | Meaning |
|---|---|
| empty / `memory` / `1` | Set `AUTHOR_PLAN_OFFER_RESOLVED=memory`; run Planner Dispatch |
| `disk` / `save` / `2` | Set `AUTHOR_PLAN_OFFER_RESOLVED=disk`; run Planner Dispatch, then Disk Mode Rendering |
| `no` / `skip` / `3` | Set `AUTHOR_PLAN_OFFER_RESOLVED=declined`; set `AUTHOR_EXECUTION_PLAN=null`; proceed to Phase 3 |
| stop token | Reset CF_PHASE_GATE=armed. Open and follow `workflows/shared/stop-token-policy.md`; cancel the current generate sub-flow without proceeding |
| anything else | Reject with `Reply not recognized. Expected enter/memory, disk, or no.` and ask again |

Choosing `disk` is explicit approval to write only the plan cache files
described in Disk Mode Rendering. It is NOT approval to write the target
artifact/code files; Phase 3 `yes` is still required before Phase 4 writes.

## Planner Dispatch

Requires: `workflows/shared/inline-fallback-probe.md` before any
`cf-constructor-*` sub-agent dispatch. Pre-dispatch fail-stop and Mode B
degradation rules are defined in
`{cf-constructor-path}/.core/skills/cypilot/sub-agent-dispatch.md`.

Dispatch read-only sub-agent `cf-constructor-generate-planner` with the JSON
contract documented in
`{cf-constructor-path}/.core/skills/cypilot/agents/cf-constructor-generate-planner.md`.
Orchestrator-supplied values:

- `plan_mode` = `"memory"` or `"disk"` from the user's reply
- `target_type`, `mode`, `kind`, `name`, `rules_mode`, `system`
- `template_path`, `example_path`, `kit_rules_path`, `checklist_path`
- `design_artifact_path` for code mode, otherwise `null`
- `target_paths` = the full list of paths expected to be written in Phase 4
- `inputs` = the approved Phase 1 `proposed_inputs` with user edits merged in
- `findings` = `[]` in create mode; Phase 5 fix loops do not use this offer gate
- `brainstorm_decisions` = Phase 0.7 decisions or `{}`
- `open_questions` = Phase 0.7 open questions or `[]`
- `available_authors` = the registered write-capable author worker agents from
  `workflows/generate/phase-4-write.md` § Author Selection and Dispatch

Parse the marker `<!-- author_plan -->` and the following JSON block. Validate:

- every task's `recommended_author` is one of the registered author worker agents
- every target path is covered by at least one task
- tasks in the same `parallel_group` have disjoint `target_paths`
- no parallel group contains more than one task with `updates_artifacts_toml=true`
- every `parallel_groups[].task_ids` entry names an existing task

If validation fails, emit the following structured menu and wait for a reply:

```text
Planner validation failed: {reason}.

| Option | Action |
|---|---|
| 1 | Rerun planner — try decomposition again with the same inputs |
| 2 | Skip author plan — proceed to Phase 3 with AUTHOR_PLAN_OFFER_RESOLVED=declined |
| 3 | Cancel — stop the generate workflow now (AUTHOR_PLAN_OFFER_RESOLVED=cancelled_planner_failure) |

Suggested: 1 because most validation failures are transient (incomplete plan, missing field) and a rerun resolves them.

Reply `1`, `2`, or `3`.
```

On `1`: re-dispatch `cf-constructor-generate-planner` with the same inputs; re-validate the returned plan. On `2`: set `AUTHOR_PLAN_OFFER_RESOLVED=declined`, `AUTHOR_EXECUTION_PLAN=null`, proceed to Phase 3. On `3`: set `AUTHOR_PLAN_OFFER_RESOLVED=cancelled_planner_failure`, `AUTHOR_EXECUTION_PLAN=null`. Reset CF_PHASE_GATE=armed. Stop the generate workflow.

## Disk Mode Rendering

When `AUTHOR_PLAN_OFFER_RESOLVED=disk`, render the validated
`AUTHOR_EXECUTION_PLAN` to:

Set CF_PHASE_GATE=released_for_orchestrator_write with scope = {cf-constructor-path}/.cache/generate-plans/{slug}-{ISO}/** immediately before writing these cache files.

```text
{cf-constructor-path}/.cache/generate-plans/{slug}-{ISO}/index.md
{cf-constructor-path}/.cache/generate-plans/{slug}-{ISO}/plan.json
{cf-constructor-path}/.cache/generate-plans/{slug}-{ISO}/agents/{author_agent}.md
{cf-constructor-path}/.cache/generate-plans/{slug}-{ISO}/tasks/{task_id}.md
```

`index.md` contains the summary, risk flags, ordered parallel groups, and a
task table. `plan.json` is the exact parsed `AUTHOR_EXECUTION_PLAN`. Each
`agents/{author_agent}.md` file contains the subset of tasks assigned to that
author, grouped by parallel group and dependency order. Each task file contains
task title, intent, target paths, recommended author, dependencies, parallel
group, rationale, input keys, and acceptance criteria.

After writing cache files, set `AUTHOR_PLAN_CACHE_DIR` to the directory path
and emit:

```text
Author plan saved: {AUTHOR_PLAN_CACHE_DIR}
```

Reset CF_PHASE_GATE=armed immediately after the named writes complete or fail. If any cache file write fails: emit a structured error block to the user listing files that were written and files that failed; do NOT silently proceed to Handoff with a partial cache. Offer the user a choice:

```text
Partial cache write failure. Some plan cache files could not be written.

Written: {list of successfully written files, one per line, or "none"}
Failed:  {list of files that failed with error reason, one per line}

How do you want to proceed?

| Option | Action |
|---|---|
| 1 | Retry disk mode — re-attempt the failed writes |
| 2 | Continue in memory mode — discard the partial cache files and proceed with `AUTHOR_EXECUTION_PLAN` in-context |
| 3 | Cancel the author plan (`AUTHOR_PLAN_OFFER_RESOLVED=cancelled_partial_write`) |

Suggested: 1

Reply `1`, `2`, or `3`.
```

On `1`: re-attempt the failed writes only (do not re-write already-successful files); if still failing, re-emit this menu. On `2`: set `AUTHOR_PLAN_OFFER_RESOLVED=memory`, discard any partially written cache files, and proceed to Handoff with `AUTHOR_EXECUTION_PLAN` in-context. On `3`: set `AUTHOR_PLAN_OFFER_RESOLVED=cancelled_partial_write`, set `AUTHOR_EXECUTION_PLAN=null`. Reset CF_PHASE_GATE=armed. Proceed to Phase 3.

## Handoff

After `AUTHOR_PLAN_OFFER_RESOLVED` is set, proceed to
`workflows/generate/phase-3-summary.md`.

Phase 3 and Phase 4 MUST NOT run while `AUTHOR_PLAN_OFFER_RESOLVED` is unset.
If a later phase sees it unset, fail-stop and route back to this file's Offer
section.
