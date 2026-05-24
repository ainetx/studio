---
cf-constructor: true
type: workflow
parent: workflows/workspace.md
description: "Invoke when the workspace workflow enters Phase 3 to write standalone or inline workspace configuration via CLI."
---

<!-- toc -->

- [Phase 3: Generate](#phase-3-generate)

<!-- /toc -->

## Phase 3: Generate

**Goal**: write the workspace config.

Set CF_PHASE_GATE=released_for_orchestrator_write with scope =
`{workspace_config_path}` (typically `.cf-constructor-workspace.toml` and
`config/core.toml` `[workspace]` section) before invoking the workspace CLI.

| Action | Command |
|---|---|
| Initialize workspace | `{cfc_cmd} --json workspace-init [--root <super-root>] [--output <path>] [--inline] [--force] [--dry-run]` |
| Add one source | `{cfc_cmd} --json workspace-add --name <name> (--path <path> \| --url <url>) [--branch <branch>] [--role <role>] [--adapter <path>] [--inline]` |

`workspace-init` writes standalone config by default; `--inline` writes
`[workspace]` into `config/core.toml`. `workspace-add` auto-detects workspace
type unless `--inline` forces inline mode. Git URL sources are not supported
inline.

Reset CF_PHASE_GATE=armed immediately after the CLI returns — success or
failure.

**On CLI failure**: Report the CLI exit code and error message to the user. Do NOT continue to `workflows/workspace/phase-4-validate.md`. Offer the user a structured choice:

| Option | Action |
|---|---|
| 1 | Retry the workspace generate CLI command (suggested for transient failures) |
| 2 | Reconfigure — return to Phase 2 to adjust the workspace config |
| 3 | Stop workspace setup |

Suggested: 1 because CLI failures during workspace generation are usually transient (path collisions, locked files).

Reply `1`, `2`, or `3` (per `workflows/shared/stop-token-policy.md`). No partial-write rollback is needed — the CLI itself handles atomicity.
