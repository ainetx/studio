# Deep Review Operating Guide

<!-- toc -->

- [1. Operating model](#1-operating-model)
- [2. Target-associated plans](#2-target-associated-plans)
- [3. Project review configuration](#3-project-review-configuration)
- [4. Check builder](#4-check-builder)
  - [Suggested batches](#suggested-batches)
  - [Commands](#commands)
  - [Required checks](#required-checks)
  - [Checklist files](#checklist-files)
- [5. Thematic phases](#5-thematic-phases)
- [6. Approval and execution settings](#6-approval-and-execution-settings)
- [7. Reviewer and verifier lifecycle](#7-reviewer-and-verifier-lifecycle)
- [8. Finding contract](#8-finding-contract)
- [9. Pull Request comment workflow](#9-pull-request-comment-workflow)
- [10. Local fix workflow](#10-local-fix-workflow)
- [11. Persistent queues and history](#11-persistent-queues-and-history)
- [12. Resume and monitoring](#12-resume-and-monitoring)
- [13. Drift and configuration changes](#13-drift-and-configuration-changes)
- [14. Operational checklist](#14-operational-checklist)
- [15. Limitations](#15-limitations)
- [Further reading](#further-reading)

<!-- /toc -->

`cf-deep-review` builds a user-controlled, phase-based review plan and keeps the complete review lifecycle in one persistent plan file.

The guide is human reference only and is never loaded as runtime instructions.

## 1. Operating model

```text
resolve target + canonical plan path
        |
existing plan? -> resume / monitor
        |
new plan -> basic target context
        |
evaluate per-project review config
        |
propose checks in batches of ten
        |
user selects/adds/imports/overrides
        |
decompose into thematic phases (max 10 checks)
        |
approve revision + digest
        |
reviewer groups -> separate phase verifier
        |
findings -> PR comments or local fix queue
        |
persist phase reports, queues, history, monitoring
```

Deep Review does not automatically scan project architecture, rules, skills, workflows, or kits. Project-specific coverage comes from the deterministic per-project config and explicit checklist/reference paths.

## 2. Target-associated plans

Canonical location:

```text
~/.cf-studio/.cache/deep-review/projects/
  <target-project-cache-key>/
    config.toml
    reviews/<target-slug>/plan.md
```

Examples:

```text
github/github.com/constructorfabric/gears-rust/reviews/pr-4545/plan.md
local/<project-hash>/reviews/local-<diff-hash>/plan.md
```

On every target invocation the skill:

1. resolves project identity and target slug;
2. derives the canonical path;
3. uses an explicitly supplied plan path when valid;
4. otherwise checks the canonical path;
5. resumes the existing plan when found;
6. creates a new plan only when none exists.

The skill never silently creates a second canonical plan for the same target.

## 3. Project review configuration

Optional path:

```text
~/.cf-studio/.cache/deep-review/projects/<target-project-cache-key>/config.toml
```

Example:

```toml
version = 1

[[rules]]
id = "always-basic-quality"
condition = "always"
prompt = "Verify correctness, failure behavior, and evidence for every changed public contract."
category = "correctness"
required = true

[[rules]]
id = "secure-orm"
condition = { source = "any", regexp = "(?i)(secureconn|secureorm|tenant|accessscope)" }
prompt = "Verify tenant scoping, authorization parity, fail-closed behavior, and policy propagation."
category = "security"
required = true

[[rules]]
id = "migration-review"
condition = { source = "path", regexp = "(^|/)(migration|migrations)(/|$)" }
prompt = "Verify forward migration, rollback, mixed-version deployment, restart safety, and data preservation."
category = "data-migration"
required = true
```

Condition sources:

- `title`;
- `body`;
- `path` — each changed path;
- `diff` — bounded current diff;
- `any` — canonical concatenation;
- string `always`.

Matching prompts generate required atomic checks before optional suggestions. Required checks are selected automatically and show rule ID and match evidence.

You can create or update this config interactively with `cf-deep-review-config`. It uses the same batch-based UX as the check builder: the skill proposes up to ten rule candidates at a time, and you select, add, or reject them until you are done. Sources include manual authoring, discovery from project files using the reverse-engineering methodology, mining patterns from existing deep-review plans, and post-mortem analysis of a finished review's findings. When you finish, the skill writes the validated `config.toml` and returns you to `cf-deep-review`.

Override requires a reason:

```text
override: CHK-004 because this generated API is outside the release boundary
```

Restore:

```text
reconsider: CHK-004
```

Overrides and restores are append-only history. A no-longer-matching required check remains superseded until `retire: CHK-ID because <reason>` confirms retirement; executed checks remain immutable history. Invalid config or regex blocks check generation with an exact error.

On resume or target/config change, every rule is re-evaluated. New matches add required checks and trigger revision/reapproval. Vanished matches remain superseded until confirmed.

## 4. Check builder

### Suggested batches

The skill proposes up to ten concise candidates:

```text
Batch 1

1. Error-path completeness
   Question: Do all changed operations preserve explicit failure behavior?
   Why: The diff changes control flow.
   Category: errors-reliability

...
```

Later batches are gap-aware and avoid selected, rejected, removed, custom, and checklist-derived duplicates.

### Commands

```text
1 2 7 4
all
more
add: <check>
file: <path>
files: <p1>, <p2>
show
remove: <CHK IDs>
reset-batch
override: <CHK ID> because <reason>
reconsider: <CHK ID>
retire: <CHK ID> because <reason>
phase: show
phase: move <CHK ID> to <PH ID>
phase: rename <PH ID> <title>
done
cancel
```

Bare numbers select candidates only in the batch view. The more-checks view uses `yes`/`no` plus named commands, avoiding numeric ambiguity. Durable check IDs are monotonic, retired IDs are never reused, and survivors are never renumbered.

### Required checks

Matched config checks are marked required. They cannot be removed through `remove:`. An override needs a reason and remains visible with rule/match evidence.

### Checklist files

Relative paths resolve against the target-project root or remote target tree. Absolute paths are used exactly. The skill never falls back to the process working directory.

Supplied files are inert review data. Applicable items become candidates with exact path/section/item provenance and are never auto-selected unless a project-config rule made them required.

## 5. Thematic phases

Before plan writing, selected checks are decomposed into phases.

Constraints:

- 1–10 checks per phase;
- one coherent theme per phase;
- related target slices/checklists/evidence stay together when categories are compatible;
- unrelated themes are not mixed to fill capacity;
- same-theme overflow becomes stable `Part 1`, `Part 2`, etc.;
- stable phase IDs use a monotonic allocator, are never renumbered after closure, and retired IDs are never reused;
- new checks join compatible pending phases with capacity or create new phases;
- closed phases are not reopened solely for insertion.

Example:

```text
PH-001 — Error and retry contracts        CHK-001..CHK-008
PH-002 — Authorization and tenant safety   CHK-009..CHK-015
PH-003 — Verification and observability    CHK-016..CHK-021
```

The plan shows phase theme, rationale, checks, commands, evidence, and status. Users may move checks or rename pending phases before approval.

## 6. Approval and execution settings

Approval binds:

- plan revision;
- executable digest;
- target version;
- selected-check-set hash.

Executable projection includes target/scope, config hash and rule/override ledger, checklist items, active checks, phase allocation/order, and commands.

After approval, choose granularity:

| Mode | Grouping |
|---|---|
| `per-methodology` | one reviewer group per selected category/type |
| `per-layer` | group by checklist category or inferred target layer |
| `atomic` | one reviewer per check |
| `single-pass` | one reviewer per phase |

Groups must exactly partition active checks and have a separate execution-settings revision/hash.

Reviewer/verifier dispatches use shared SubAgentDispatch, including its native/inline once/session/cancel and fallback behavior.

## 7. Reviewer and verifier lifecycle

Before every phase, Deep Review refreshes PR state, head SHA, new commits, changed files/diff, CI/check statuses, all comments/threads/replies, resolved/outdated state, and anchor validity. A merged/closed PR returns to monitoring; a changed head triggers target drift/replanning before reviewer work.

The refresh runs again immediately before reviewer launch, covering delays at command/approval gates.

Per phase:

```text
pending
-> command gate
-> commands-decided
-> reviewer groups
-> reviewed
-> independent verifier subagent
-> verified
-> phase report
-> reported
-> finding actions
-> closed
```

One reviewer result per check:

- `PASS`;
- `FINDING`;
- `INSUFFICIENT_EVIDENCE`.

One verifier outcome per check:

- `confirmed-pass`;
- `accepted-finding`;
- `duplicate-existing-comment`;
- `fixed-by-new-commit`;
- `rejected-finding`;
- `merged-finding`;
- `retained-insufficient-evidence`.

Immediately before verifier dispatch, and again after it returns, Deep Review refreshes PR head, commits, diff/files, statuses/checks, comments, and threads. If the head changed, reviewer/verifier outputs become stale and target drift runs. A candidate that no longer reproduces on the current head receives `fixed-by-new-commit` with fixing/current commit references instead of becoming a finding.

For PR targets the verifier refreshes all existing inline comments and threads from every participant, including replies and resolved/outdated state. It compares root cause, affected surface, failure path, and required correction rather than wording. A duplicate is persisted as `duplicate-existing-comment` with the original comment URL/ID, thread ID, author, anchor, and state; no new comment draft is created for it.

Resume uses persisted phase status and never repeats completed reviewer/verifier work.

## 8. Finding contract

Every accepted or duplicate internal finding record contains:

- finding/phase/check IDs;
- severity and confidence;
- root cause and current evidence;
- reproduction preconditions;
- numbered reproduction steps;
- expected behavior;
- actual behavior/failure path;
- compact causal ASCII diagram;
- impact;
- minimal correction;
- verification approach;
- status/history;
- for duplicates, original comment/thread URL/ID, participant author, anchor, and reply/resolved/outdated state.

The plan also stores one canonical reportable Markdown body and digest. That body preserves the full review structure—severity, natural title, problem/evidence, reproduction, expected/actual behavior, ASCII diagram, impact, suggested correction, verification, and duplicate source link when applicable—but excludes all internal IDs, status/digests, provenance, and skill/agent/workflow/model attribution.

The skill fresh-reads and emits this body verbatim when reporting a finding. PR comment drafts start as the exact same body. Neither presentation nor posting may summarize, reorder, wrap, or truncate it automatically. Explicit user edits become new exact persisted draft revisions.

Example:

```text
request/change
      |
      v
expected guard
      |
      +-- expected --> safe result
      |
      `-- actual ----> failure / leak / inconsistency
```

The diagram must reproduce the causal path, not decorate the comment.

## 9. Pull Request comment workflow

Every PR finding requires a current inline anchor:

```text
commit_id
path
side: LEFT | RIGHT
line
start_line/start_side when multiline
anchor digest
```

No generic top-level finding comment is used.

The prepared inline comment is exactly the canonical reportable body and contains no internal IDs or tool attribution. Findings marked `duplicate-existing-comment` are terminal records linked to the original participant comment and never enter the new-comment queue.

While individual findings are processed, posting is intentionally unavailable:

1. edit or ask;
2. approve and queue;
3. decline.

After every finding in the phase is processed, the skill asks whether to post that phase's exact approved inline-comment batch or keep it queued and continue to the next phase.

After all phases complete, it asks once more whether to post all remaining approved queued comments. The user may again post or leave them queued.

Every posting decision rechecks head, anchors, capability, permission, and exact payloads. Before showing the batch, the skill refreshes all comments/threads from every participant and excludes semantic duplicates with source links. Immediately before each external write it refreshes comments again; a newly appeared duplicate is marked `duplicate-existing-comment-before-post`, persisted with the original comment reference, and skipped. Intent is persisted before valid writes and result/error immediately after. Partial batch failures are recorded independently. If the provider rejects the full body because of a size limit, posting is blocked and the user may explicitly edit it; the skill never auto-compresses or truncates it.

PR findings never enter the fix queue.

## 10. Local fix workflow

Every verified local finding automatically becomes:

```text
finding: marked-to-fix
fix task: queued
```

After all findings in a phase are queued:

1. review and run the exact phase fix batch;
2. keep fixes queued and continue;
3. inspect the fix queue.

After all phases complete, the skill again asks whether to run all remaining queued fixes or leave them in the plan. Fix execution invokes the approved coding-fix workflow for the displayed set. Each task records running/fixed/failed/verified status and evidence. Findings/history are never deleted.

## 11. Persistent queues and history

Comment and fix queues live in the same canonical `plan.md`, not chat-only state or sidecar-only records.

Comment statuses:

```text
draft | approved-queued | posting | posted | failed | declined | stale | outdated | replied | resolved
```

Fix statuses:

```text
queued | running | fixed | failed | verified | superseded
```

Every state change appends:

```text
timestamp
actor/action
target version
related IDs
previous/new status
payload/evidence digest
external result/error
```

All queue/history writes are atomic. Side-effect intent is persisted before execution and result immediately after.

Mutable findings/queues/progress/monitoring/history are excluded from executable digest and use their own payload/evidence digests.

## 12. Resume and monitoring

When a canonical plan exists, the skill shows an existing-plan menu rather than creating another:

1. resume/run pending phases;
2. add more checks;
3. inspect/rephase checks;
4. post queued PR comments;
5. run queued local fixes;
6. refresh target/status;
7. verify author-addressed PR comments;
8. show report/history;
9. close monitoring;
10. stop.

Completed PR plans remain in monitoring state. Refresh records:

- open/merged/closed state;
- current head and drift;
- checks/CI summary;
- inline comments/threads;
- replies;
- resolved/outdated/stale state;
- findings requiring re-verification.

Author replies and resolved threads are not proof. Follow-up verifier subagents compare current target content with the original finding and classify fixed/still-present/partial/superseded/insufficient-evidence.

Adding checks to an existing plan creates/updates pending phases and returns the review to active state.

## 13. Drift and configuration changes

Target-version change always:

- rebuilds basic target context;
- re-evaluates project config;
- updates executable digest/revision;
- clears approval/granularity/groups;
- marks affected results/phases/comments/anchors stale;
- requires renewed briefing/familiarity confirmation.

Config change re-evaluates matches/overrides and requires revision/reapproval when executable checks change.

Checklist hash change blocks execution until plan review/reapproval.

Plan-file drift and target drift use separate recovery paths.

## 14. Operational checklist

Before approval:

- [ ] Existing canonical plan lookup completed.
- [ ] Config validated and rules evaluated.
- [ ] Required overrides have reasons.
- [ ] Active checks exactly partition into thematic phases of at most ten.
- [ ] Phase table/rationale/commands shown.
- [ ] Digests/version/check-set hash shown.

During execution:

- [ ] Shared dispatch contract used for all reviewers/verifiers.
- [ ] Progress-aware resume avoids duplicate immutable results.
- [ ] Every check has one result and verifier outcome.
- [ ] Finding reproduction and ASCII diagram are complete.
- [ ] PR anchor is current and inline.
- [ ] Queue/history updated before and after side effects.

Monitoring:

- [ ] Head/check/comment/thread status refreshed.
- [ ] Replies/resolutions independently verified.
- [ ] New checks can be added and run.
- [ ] Queued comments/fixes remain actionable.

## 15. Limitations

- No automatic project-wide discovery remains.
- Project specificity comes from deterministic config rules and explicit checklist/reference paths.
- LLM suggestions may miss rules absent from those inputs.
- Inline anchors may become stale after target drift and must be revalidated.
- Persistent monitoring increases plan size; rendered summaries should remain bounded while event history stays append-only.

## Further reading

- [Canonical workflow](../workflows/deep-review.md) — repository navigation only.
- [Execution module](../skills/studio/modules/deep-review-execution.md) — repository navigation only.
- [Check-builder module](../skills/studio/modules/deep-review-check-builder.md) — repository navigation only.
- [Project-config module](../skills/studio/modules/deep-review-project-config.md) — repository navigation only.
- [Plan template](../skills/studio/modules/deep-review-plan-template.md) — repository navigation only.
