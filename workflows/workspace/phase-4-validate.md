---
cf-constructor: true
type: workflow
parent: workflows/workspace.md
description: "Invoke when the workspace workflow enters Phase 4 to validate workspace reachability, adapters, and cross-repo behavior."
---

## Phase 4: Validate

**Goal**: verify reachability, adapters, and cross-repo behavior.

| Check | Command / Expectation |
|---|---|
| Workspace status | `{cfc_cmd} --json workspace-info` |
| Source health | path exists; adapter found if expected; `artifacts.toml` valid when adapter exists; at least one system if adapter exists |
| Cross-repo IDs | `{cfc_cmd} --json list-ids` |
| Cross-repo validation | `{cfc_cmd} --json validate` |

Report total sources, reachable sources, sources with adapters, and available
cross-repo IDs.

**Graceful degradation**:

- missing repos emit warnings, not errors
- available sources continue working
- remote IDs from missing sources are unavailable
- explicit `source` entries targeting missing repos resolve to `None`
- scan failures warn on stderr without blocking the operation

After validation, continue to `workflows/workspace/next-steps.md`.
