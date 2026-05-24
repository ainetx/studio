---
name: analyze-phase-0-change-review-scope
description: "Invoke when CHANGE_REVIEW=true to resolve the change-review diff scope via cf-constructor-diff-scope-resolver before Phase 1 file checks."
purpose: Resolve change-review diff scope before file checks
loaded_by: workflows/analyze/phase-0-dependencies.md
version: 1.0
---

When `CHANGE_REVIEW=true`, dispatch sub-agent
`cf-constructor-diff-scope-resolver` immediately after the inline-fallback-probe
(`workflows/shared/inline-fallback-probe.md`) and before Phase 1 file checks.

Supply:
- `worktree_path` = explicit repo/worktree path, or resolved workspace source
- `commit_sha` = requested commit SHA, or `null`
- `base_ref` = explicit base, or `null` (agent uses `<commit_sha>^`)
- `include_uncommitted` = `true` for worktree/dirty/staged/unstaged changes
- `direct_targets` = explicit paths named by the user
- `review_intent` = original review request text

Store returned JSON as `diff_scope`. Set `{PATHS} = diff_scope.review_targets`
for downstream file checks and semantic review. If empty, stop and report no
reviewable targets.

After `diff_scope` is stored, derive prompt_targets from review targets matching
`workflows/**`, `skills/cypilot/**/*.md`, `requirements/**/*.md`, `AGENTS.md`,
`SKILL.md`, agent prompt files, or prompt config files. If prompt_targets is non-empty, set
`PROMPT_REVIEW=true`; when review_intent is change-review, defect-oriented, or
generic code-review wording, also set `PROMPT_BUG_REVIEW=true`.

The orchestrator MUST NOT run `git diff`, changed-file triage, hotspot mapping,
or semantic search over the diff itself; those operations belong to the
resolver and downstream semantic reviewer agents.
