---
cf: true
type: workflow
name: cf-auto-config
description: Chat-only auto-config entry point — delegates to generate.md in AUTO_CONFIG mode.
version: 1.0
purpose: Standalone auto-config command; pass-through to generate.md with AUTO_CONFIG mode
---

LOAD skill `cf` IN GENERATE + AUTO_CONFIG mode, AUTO_CONFIG=true
