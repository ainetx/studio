---
cf: true
type: workflow
name: cf-explain
description: "Invoke for requests to explain, walk through, teach, onboard, give a code tour, produce a source-grounded narrative, or summarize a decision."
version: 1.0
purpose: Standalone explain command; pass-through to analyze.md with EXPLAIN mode
---

```text
UNIT ExplainProxy

PURPOSE:
  Pass through to analyze.md with EXPLAIN mode active.

DO:
  LOAD skill `cf` IN ANALYZE + EXPLAIN mode, EXPLAIN_MODE=true
  The target analyze workflow MUST apply
  {cf-studio-path}/.core/workflows/shared/explore-brainstorm-gate.md;
  cf-explore is required when explanation targets are not explicit.

ON_ERROR:
  load_failed -> EMIT "Cannot load target workflow — check that {cf-studio-path} is correctly set." STOP_TURN
```
