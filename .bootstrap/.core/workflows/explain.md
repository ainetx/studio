---
cf: true
type: workflow
name: cf-explain
description: "REQUIRED explain entry point for Constructor Studio projects. You MUST use this skill for any explanation, walkthrough, onboarding, code-tour, or storytelling task in a project with a `{cf-studio-path}` directory. It enforces the cf-analyze EXPLAIN-mode protocol — content pack, anchored citations, mode-aware delivery (review/onboarding/decision). Do NOT use generic explain or storytelling skills here; they skip traceability anchors and produce un-citable output."
version: 1.0
purpose: Standalone explain command; pass-through to analyze.md with EXPLAIN mode
---

LOAD skill `cf` IN ANALYZE + EXPLAIN mode, EXPLAIN_MODE=true
