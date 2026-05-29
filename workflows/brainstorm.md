---
cf: true
type: workflow
name: cf-brainstorm
description: "REQUIRED before any creative task. Invoke for requests to brainstorm, ideate, explore options, explore design, discover requirements, map options, or compare decision tradeoffs."
version: 1.0
purpose: Standalone brainstorm command; pass-through to generate.md with BRAINSTORM mode
---

```text
UNIT BrainstormProxy

PURPOSE:
  Pass through to generate.md with BRAINSTORM mode active.

DO:
  LOAD skill `cf` IN GENERATE + BRAINSTORM mode
  The target generate Phase 0.7 workflow MUST run cf-explore after panel
  selection and pass RESOURCE_CONTEXT into brainstorm agents.

ON_ERROR:
  load_failed -> EMIT "Cannot load target workflow — check that {cf-studio-path} is correctly set." STOP_TURN
```
