---
name: analyze-phase-4-output-index
description: "Invoke when entering Analyze Phase 4 to select the output schema sub-file matching the active mode and route the remediation handoff."
purpose: Phase 4 output dispatcher — selects the schema sub-file matching the active mode and routes the remediation handoff
loaded_by: workflows/analyze.md
version: 1.0
---

```text
UNIT AnalyzePhase4OutputDispatcher

PURPOSE:
  Select the output schema sub-file matching the active mode and route the
  remediation handoff when applicable.

RULES:
  - MUST print to chat only; MUST_NOT create files
  - MUST load exactly one output sub-file
  - MUST append remediation-handoff.md after the selected schema when actionable
    findings exist AND EXPLAIN_MODE=false
  - MUST_NOT emit Fix Prompt or Plan Prompt from this unit (those are emitted by
    remediation-handoff.md on demand)
  - MUST render Prompt Review Partial Checkpoint block (not full schema) when
    PROMPT_REVIEW=true AND checkpoint.type=PARTIAL_CHECKPOINT
  - MUST return to router after all sub-files emit output; continue with Phase 5,
    Key Principles, Agent Self-Test, and Validation Criteria as applicable

DO:
  IF EXPLAIN_MODE == false AND PROMPT_REVIEW == false AND PROMPT_BUG_REVIEW == false:
    LOAD workflows/analyze/phase-4-output/output-standard.md
  IF PROMPT_REVIEW == true OR PROMPT_BUG_REVIEW == true:
    LOAD workflows/analyze/phase-4-output/output-prompt-review.md
  IF EXPLAIN_MODE == true:
    LOAD workflows/analyze/phase-4-output/output-storytelling.md
  IF actionable findings exist AND EXPLAIN_MODE == false:
    LOAD workflows/analyze/phase-4-output/remediation-handoff.md
```

## Phase 4: Output

Print to chat only; create no files. This file is the mode → schema selector; load exactly one output sub-file plus the remediation handoff when applicable.

| Mode | Sub-file |
|------|----------|
| Standard / Semantic-Only (`EXPLAIN_MODE=false`, `PROMPT_REVIEW=false`, `PROMPT_BUG_REVIEW=false`) | `workflows/analyze/phase-4-output/output-standard.md` |
| `PROMPT_REVIEW=true` or `PROMPT_BUG_REVIEW=true` | `workflows/analyze/phase-4-output/output-prompt-review.md` |
| `EXPLAIN_MODE=true` (storytelling) | `workflows/analyze/phase-4-output/output-storytelling.md` |
| Actionable findings (any mode except `EXPLAIN_MODE=true`) | `workflows/analyze/phase-4-output/remediation-handoff.md` (appended after the selected output schema) |

`enforceRemediationPrompts` policy and the `EXPLAIN_MODE` override live in the standard output sub-file and the remediation-handoff sub-file; load both together when the active mode requires the handoff menu.

prompt-review partial checkpoints satisfy Phase 4 by rendering the `Prompt
Review Partial Checkpoint` block from
`workflows/analyze/phase-4-output/output-prompt-review.md`; do not force the
full prompt-review schema when `checkpoint.type = "PARTIAL_CHECKPOINT"`.

After all sub-files have emitted their output (selected schema + remediation
handoff when applicable), the orchestrator returns to the router to continue
with Phase 5, Key Principles, Agent Self-Test, and Validation Criteria as
applicable.
