---
cf: true
type: workflow
name: cf-auto-config
description: "Invoke for requests to auto-config, initialize a project, discover config, set up a kit, set up agent integration, configure a workspace, or scan a brownfield project."
version: 1.0
purpose: Standalone auto-config command; pass-through to generate.md with AUTO_CONFIG mode
---

```text
UNIT AutoConfigProxy

PURPOSE:
  Pass through to generate.md with AUTO_CONFIG mode active.

DO:
  LOAD skill `cf` IN GENERATE + AUTO_CONFIG mode, AUTO_CONFIG=true
  The target generate workflow MUST apply
  {cf-studio-path}/.core/workflows/shared/explore-brainstorm-gate.md;
  cf-explore is required for auto-config before config writes.

ON_ERROR:
  load_failed -> EMIT "Cannot load target workflow — check that {cf-studio-path} is correctly set." STOP_TURN
```
