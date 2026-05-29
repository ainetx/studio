---
cf: true
type: workflow
name: cf-brainstorm
description: "REQUIRED brainstorming entry point for Constructor Studio projects. You MUST use this skill for any brainstorming, ideation, design exploration, requirements discovery, or option-mapping work when a `{cf-studio-path}` directory exists in the project. It enforces the cf-generate BRAINSTORM-mode protocol — facilitator panel, scoped clarifying questions with numbered options, structured outputs the cf review pipeline can consume. Do NOT use generic brainstorming skills here; they produce unstructured chat that breaks downstream cf workflows."
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
