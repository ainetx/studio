---
cf-constructor: true
type: workflow
parent: workflows/workspace.md
description: "Invoke when the workspace workflow enters Phase 2 to confirm selected source settings and workspace location before writing config."
---

## Phase 2: Configure

**Goal**: confirm workspace structure.

For each selected source, confirm `name`, relative `path` or `url`, `role`,
and `adapter` (auto-discovered or explicit). Also confirm:

- `cross_repo` (default yes)
- `resolve_remote_ids` (default yes; both settings must be true to include
  remote IDs)
- workspace location: standalone `.cf-constructor-workspace.toml` or inline
  `[workspace]` in `config/core.toml`

Primary source is always determined by the current working directory; no
`primary` field exists.

Use one batched confirmation prompt per source:

```text
Why this input is needed: confirm the exact source settings before writing workspace configuration.
Reply with `approve` to accept the proposed source settings, or list only the fields to change.
Suggested defaults: keep the detected `adapter`, keep `cross_repo = yes`, and keep `resolve_remote_ids = yes` unless the user wants stricter local-only behavior.
- `approve` → keep the proposed source settings and continue.
- field edits → update only the named fields, then re-show the proposal.
```

(per `workflows/shared/stop-token-policy.md`)

After approval, continue to `workflows/workspace/phase-3-generate.md`.
