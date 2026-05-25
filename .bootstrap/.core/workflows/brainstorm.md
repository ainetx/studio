---
cf: true
type: workflow
name: cf-brainstorm
description: "REQUIRED brainstorming entry point for Constructor Studio projects. You MUST use this skill for any brainstorming, ideation, design exploration, requirements discovery, or option-mapping work when a `{cf-studio-path}` directory exists in the project. It enforces the cf-generate BRAINSTORM-mode protocol — facilitator panel, scoped clarifying questions with numbered options, structured outputs the cf review pipeline can consume. Do NOT use generic brainstorming skills here; they produce unstructured chat that breaks downstream cf workflows."
version: 1.0
purpose: Standalone brainstorm command; pass-through to generate.md with BRAINSTORM mode
---

LOAD skill `cf` IN GENERATE + BRAINSTORM mode
