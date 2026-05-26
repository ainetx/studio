---
cf: true
type: workflow
name: map
description: Build interactive dependency maps — scan markdown, source code, cpt references; detect cross-repo edges and phantom cpts; render HTML viewer or JSON
version: 1.0
purpose: Guide cfs map workflow from pre-flight through validation
---

# Constructor Studio Map Workflow

<!-- toc -->

- [Overview](#overview)
- [Phase 1: Pre-flight](#phase-1-pre-flight)
- [Phase 2: Configure](#phase-2-configure)
- [Phase 3: Generate](#phase-3-generate)
- [Phase 4: Validate](#phase-4-validate)
- [Quick Reference](#quick-reference)
- [Next Steps](#next-steps)

<!-- /toc -->

```text
UNIT MapBootstrap

PURPOSE:
  Load required agent context before any map phase work begins.

DO:
  REQUIRE {cf-studio-path}/config/AGENTS.md is loaded and followed FIRST
  REQUIRE {cf-studio-path}/.gen/AGENTS.md is loaded and followed after config/AGENTS.md

NOTES:
  Type: Operation. Role: Any. Output: Interactive HTML map or JSON graph export.
```

## Overview

```text
UNIT MapOverview

PURPOSE:
  Define map workflow routing by user intent.

MENU MapIntentRouter:
  TITLE: Route by user intent (machine reference)
  OPTIONS:
    Generate map of current project -> CONTINUE MapPhase1
    Analyze map for dangling cpts   -> LOAD analyze.md with map target
    Export map data for tooling     -> Use JSON format via --format json
  INVALID:
    EMIT "Unrecognised intent. Reply with: Generate map of current project, Analyze map for dangling cpts, or Export map data for tooling."
    WAIT user.reply
    STOP_TURN

NOTES:
  Scans markdown files and source code for dependencies; builds interactive map
  of connections (file links, cpt identifiers, cross-repo references); detects
  dangling references. Reveals architecture, traceability gaps, federation boundaries.
```

## Phase 1: Pre-flight

```text
UNIT MapPhase1

PURPOSE:
  Detect what will be scanned before generating the map.

DO:
  RUN python3 {cf-studio-path}/.core/skills/studio/scripts/studio.py --json info
    (look for [[systems.codebase]] entries in artifacts.toml)
  CHECK for .studio-workspace.toml in project root
  EMIT discovered state:
    "Local markdown only" OR list all workspace sources that will be scanned
    List [[systems.codebase]] from artifacts.toml (or "no artifact registry found")
  EMIT_MENU MapScopeMenu
  WAIT user.reply
  STOP_TURN

MENU MapScopeMenu:
  TITLE: >
    Why this input is needed: decide whether to scan workspace sources and include
    source code in the map. Reply with the scope: local-only, include-workspace, or no-source.
    Suggested default: include-workspace if workspace config exists, else local-only.
  OPTIONS:
    local-only ->
      SET map.scope = local-only
      CONTINUE MapPhase2
    include-workspace ->
      REQUIRE .studio-workspace.toml exists
      SET map.scope = include-workspace
      CONTINUE MapPhase2
    no-source ->
      SET map.scope = no-source
      CONTINUE MapPhase2
  INVALID:
    EMIT "Reply with local-only, include-workspace, or no-source."
    WAIT user.reply
    STOP_TURN
```

## Phase 2: Configure

```text
UNIT MapPhase2

PURPOSE:
  Confirm map settings before scanning.

DO:
  EMIT proposed settings:
    Output format: html (interactive viewer) or json (machine-readable)
    Output file: ./md-map.html or ./md-map.json (use --out PATH to override)
    Category config: auto-detect or provide md-map.toml for custom categorization
    Inline data: for HTML, embed JSON into file (no .js sidecar) or keep separate
  EMIT_MENU MapConfigMenu
  WAIT user.reply
  STOP_TURN

MENU MapConfigMenu:
  TITLE: >
    Why this input is needed: confirm map output settings before scanning.
    Reply with `approve` to accept defaults, or list only the fields to change.
    Suggested defaults: HTML output to ./md-map.html, auto-detect categories, keep data separate.
  OPTIONS:
    approve ->
      CONTINUE MapPhase3
    field edits ->
      SET map.config_pending_edits = user.named_fields
      RE-EMIT updated proposal with map.config_pending_edits applied
      WAIT user.reply
      STOP_TURN
  INVALID:
    EMIT "Reply with approve or list fields to change."
    WAIT user.reply
    STOP_TURN
```

## Phase 3: Generate

```text
UNIT MapPhase3

PURPOSE:
  Invoke cfs map and produce output.

DO:
  WHEN map.scope == local-only:
    RUN python3 {cf-studio-path}/.core/skills/studio/scripts/studio.py --json map --no-source [--out PATH] [--format html|json]
  WHEN map.scope == include-workspace:
    RUN python3 {cf-studio-path}/.core/skills/studio/scripts/studio.py --json map [--out PATH] [--format html|json]
  WHEN map.scope == no-source:
    RUN python3 {cf-studio-path}/.core/skills/studio/scripts/studio.py --json map --local-only [--out PATH] [--format html|json]
  VERIFY output file exists and size is reasonable
  IF format == html:
    EMIT file path; note that it opens in a browser
  IF format == json:
    EMIT note that it can be piped to other tools (e.g., jq)
  CONTINUE MapPhase4
```

## Phase 4: Validate

```text
UNIT MapPhase4

PURPOSE:
  Inspect the map for completeness and phantom references.

DO:
  CHECK: Open generated .html in a browser; verify vis-network graph renders without errors
  COUNT: nodes/edges via JSON or browser DevTools (markdown nodes, source nodes, cross-repo edges)
  CHECK: Search JSON for phantom:<cpt-id> nodes or dangling_cpt_uses array (dangling references)
  VERIFY: nodes are color-coded by category; check if md-map.toml override helped
  IF dangling cpts found:
    SUGGEST `cfs where-used <cpt-id>` or `cfs list-ids` for cross-repo IDs
  CONTINUE MapNextSteps
```

## Quick Reference

| Intent | Flags |
|---|---|
| Markdown-only quick map | `cfs map --no-source` |
| Single-repo map (skip federation) | `cfs map --local-only` |
| Machine-readable graph | `cfs map --format json --out map.json` |
| Custom categories | `cfs map --config md-map.toml` |
| Self-contained HTML (no sidecar) | `cfs map --inline-data` |
| Debug layout | `cfs map -v` or `cfs map --verbose` |

## Next Steps

```text
UNIT MapNextSteps

PURPOSE:
  Present post-generation next steps with a suggested default and explicit reply contract.

DO:
  EMIT_MENU MapNextStepsMenu
  WAIT user.reply
  STOP_TURN

MENU MapNextStepsMenu:
  TITLE: >
    What would you like to do next?
    Reply with the option number or a short custom instruction.
  OPTIONS:
    1 ->
      EMIT "Opening the map in a browser — explore the interactive graph."
      (Suggested default)
    2 ->
      EMIT "Export JSON and analyze with jq — for programmatic access to nodes/edges."
    3 ->
      EMIT "Check for dangling cpts — run cfs where-used <cpt-id> to diagnose phantom references."
    4 ->
      EMIT "Update categorization — create or refine md-map.toml for better node grouping."
    5 ->
      WAIT user description of next map action
  INVALID:
    EMIT "Reply with 1, 2, 3, 4, or 5."
    WAIT user.reply
    STOP_TURN

NOTES:
  After successful map generation:
  - Use HTML viewer to explore architecture visually or export images for documentation
  - Export JSON and pipe to downstream tools (e.g., GraphQL queries, traceability reports)
  - For dangling cpts, use `cfs where-used <cpt-id>` to find missing definitions
  - Update md-map.toml if categorization needs adjustment
  - Share the map with team for architecture review
```
