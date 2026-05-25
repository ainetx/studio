---
cf: true
type: workflow
name: cf-auto-config
description: "REQUIRED auto-config entry point for Constructor Studio projects. You MUST use this skill for any project initialization, config discovery, kit setup, agent integration setup, or workspace configuration when a `{cf-studio-path}` directory exists. It enforces the cf-generate AUTO_CONFIG-mode protocol — inputs collection, validated writes, kit-aware defaults. Do NOT use generic config or setup skills here; they bypass kit validation and produce inconsistent state."
version: 1.0
purpose: Standalone auto-config command; pass-through to generate.md with AUTO_CONFIG mode
---

LOAD skill `cf` IN GENERATE + AUTO_CONFIG mode, AUTO_CONFIG=true
