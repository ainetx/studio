---
name: generate-phase-0.5-clarify
description: "Invoke when the generate workflow reaches Phase 0.5 to clarify output destination and system context before input collection."
purpose: Generate Phase 0.5 — clarify output destination and system context
loaded_by: workflows/generate.md
version: 1.0
---

<!-- toc -->

- [Phase 0.5: Clarify Output & Context](#phase-05-clarify-output--context)

<!-- /toc -->




## Phase 0.5: Clarify Output & Context

```text
UNIT Phase05ClarifyContext

PURPOSE:
  Clarify system context and output destination before Phase 0.7 / Phase 1.

DO:
  IF system context is unclear:
    EMIT exactly:
---
Why this input is needed: system selection controls registry placement, ID prefixes, and traceability boundaries.

Which system does this artifact/code belong to?
- {list systems from artifacts.toml}
- Create new system
Suggested: the current or nearest registered system when one owns the target path; otherwise `Create new system`.
Reply with the system name or `Create new system`.
---
    WAIT user.reply
    SET selected_system = user.reply
    STOP_TURN

  IF output destination is unclear:
    EMIT exactly:
---
Why this input is needed: destination controls whether this workflow writes files, updates the registry, or returns a chat-only preview.

Where should the result go?
- File (will be written to disk and registered)
- Chat only (preview, no file created)
- MCP tool / external system (specify as `MCP: <tool>` or `External: <system>`)
Suggested: File for durable artifacts/code changes; Chat only for previews.
Reply with `File`, `Chat only`, `MCP: <tool>`, or `External: <system>`.
---
    WAIT user.reply
    SET output_destination = user.reply
    STOP_TURN

  SET selected_system (store for registry placement)
  IF file output AND using rules:
    DETERMINE path
    PLAN artifacts.toml entry
    CHECK UPDATE vs CREATE
  IF artifacts:
    IDENTIFY parent references
  IF code:
    IDENTIFY design artifacts + requirement IDs + traceability markers
  FOR new IDs:
    USE cpt-{system}-{kind}-{slug}
    VERIFY uniqueness with `{cfs_cmd} --json list-ids`

RULES:
  - MUST clarify system context when unclear before proceeding
  - MUST clarify output destination when unclear before proceeding
  - MUST store selected system for registry placement
```
