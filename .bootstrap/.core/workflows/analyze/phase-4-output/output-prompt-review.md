---
name: analyze-phase-4-output-prompt-review
description: "Invoke when PROMPT_REVIEW=true to render the Phase 4 Prompt Review output schema merging prompt-engineering and optional prompt-bug-finder sub-agent reports."
purpose: Phase 4 Prompt Review output schema (PROMPT_REVIEW=true) — merges prompt-engineering and optional prompt-bug-finder sub-agent reports
loaded_by: workflows/analyze.md
version: 1.0
---

```text
UNIT AnalyzePhase4PromptReview

PURPOSE:
  Render Phase 4 prompt-review output, merging prompt-engineering and
  optional prompt-bug-finder sub-agent reports.

WHEN:
  PROMPT_REVIEW == true OR PROMPT_BUG_REVIEW == true

DO:
  IF checkpoint.type == "PARTIAL_CHECKPOINT":
    Render Prompt Review Partial Checkpoint block (see below)
    Append Remediation Handoff menu when checkpoint or findings require follow-up
    STOP (do not render the full prompt-review schema)
  IF PROMPT_REVIEW == true:
    Render cf-semantic-reviewer-prompt report in section order:
      1. Summary
      2. Context Budget & Evidence
      3. Compact-Prompts Findings
      4. Layer Summaries
      5. Issues Found
      6. Recommended Fixes
      7. Verification Checklist
  IF PROMPT_BUG_REVIEW == true:
    Append cf-prompt-bug-finder report after the prompt-engineering report.
    IF PROMPT_REVIEW == false:
      Render only the prompt-bug-finder report under this schema.
      Summary MUST begin with prompt-bug-finding status block:
        Review status | Deterministic gate | Scope reviewed | Review basis |
        Environment snapshot | Coverage summary
      IF deterministic gate is SKIPPED:
        State why and explicitly state "no validator-backed evidence for this review path"

RULES:
  - MUST_NOT use the standard analysis template (output-standard.md) for prompt review
  - MUST_NOT mark prompt-review checks N/A unless the reviewed document explicitly
    makes them inapplicable; report FAIL or PARTIAL when applicability is unresolved
  - MUST render Partial Checkpoint block (not full schema) when
    checkpoint.type=PARTIAL_CHECKPOINT
  - MUST append Remediation Handoff when partial checkpoint or findings require follow-up

NOTES:
  Prompt Review Partial Checkpoint block MUST include:
    - checkpoint.type = "PARTIAL_CHECKPOINT"
    - reviewed target paths and covered layers
    - uncovered layers / resume anchors
    - findings backed by already-covered evidence
    - checkpoint JSON needed to resume the prompt review
  This is a valid partial output, not a clean pass.
```
