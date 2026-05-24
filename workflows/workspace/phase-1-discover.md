---
cf-constructor: true
type: workflow
parent: workflows/workspace.md
description: "Invoke when the workspace workflow enters Phase 1 to discover candidate repositories and handle zero-result scans."
---

## Phase 1: Discover

**Goal**: find candidate repos.

| Step | Action |
|---|---|
| Identify root | `{cfc_cmd} --json info` |
| Scan nested repos | `{cfc_cmd} --json workspace-init --dry-run` |
| Present results | show repo name/path, adapter found or not, and inferred role |

### Zero Results

If discovery returns zero candidate repos, do not proceed to configuration or
write an empty workspace config. Emit:

```text
No workspace sources were discovered under {root}.

Reply with one of:
1. Provide a parent directory to scan.
2. Add a source manually with name + path or URL.
3. Stop workspace setup.
```

(per `workflows/shared/stop-token-policy.md`)

Only continue after the user supplies a new scan root or at least one manual
source. If the new scan also returns zero results, repeat the same branch; do
not infer sources from unrelated directories.

### Decision Point

After presenting discovered repos, ask one explicit question that covers both
inclusion and workspace location.

```text
Why this input is needed: choose which repositories become workspace sources and where the workspace config should live.
Reply with the selected repo numbers or names, then `standalone` or `inline`.
Suggested default: include reachable repos that have the expected adapter, and use `standalone` unless the user specifically wants workspace config inside `config/core.toml`.
- `standalone` → write `.cf-constructor-workspace.toml` and keep workspace config separate from `config/core.toml`.
- `inline` → write `[workspace]` inside `config/core.toml`.
```

(per `workflows/shared/stop-token-policy.md`)
