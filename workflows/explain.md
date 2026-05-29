---
cf: true
type: workflow
name: cf-explain
description: "REQUIRED explain entry point for Constructor Studio projects. You MUST use this skill for any explanation, walkthrough, onboarding, code-tour, or storytelling task in a project with a `{cf-studio-path}` directory. It enforces the cf-analyze EXPLAIN-mode protocol — content pack, anchored citations, mode-aware delivery (review/onboarding/decision). Do NOT use generic explain or storytelling skills here; they skip traceability anchors and produce un-citable output."
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
