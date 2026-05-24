---
cf-constructor: true
type: workflow-phase
name: plan-phase-0-discover
description: "Invoke when /cf-constructor-plan enters Phase 0 to resolve runtime variables and build a dynamic tool map from the CLISPEC."
loaded_by: workflows/plan.md
version: 1.0
---

# Phase 0: Resolve Variables & Discover Tools

Run `EXECUTE: {cfc_cmd} --json info`; store `{cf-constructor-path}`, `{project_root}`, and the returned `variables` dict for later path resolution.

Variable checkpoint: after resolving `{cfc_cmd}`, `{cf-constructor-path}`, and `{project_root}`, carry them forward to Phase 3.1, where they MUST be written into the `[meta]` TOML table at the top of `plan.toml` so they survive context compaction and the runtime can read them on resume. On context loss or new-chat resume, parse `plan.toml`'s `[meta]` table first, then re-run `{cfc_cmd} --json info` to verify (or refresh) the resolved values before any path-dependent step.

## 0.1 Discover Available Tools

Read `READ: {cf-constructor-path}/.core/skills/cypilot/cypilot.clispec` and build a dynamic tool map from each `COMMAND` block as `{command_name} — {DESCRIPTION line} [outputs: {OUTPUT format}]`. Also inspect the resolved `variables` dict for script directories (for example `{scripts}` when present), scan each such directory for `*.py`, `*.sh` files, and add kit scripts with inferred purpose.
