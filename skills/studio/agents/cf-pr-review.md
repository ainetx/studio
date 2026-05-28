---
description: Invoke when reviewing a GitHub pull request with structured checklist-based analysis in a separate context — keeps detailed review output isolated from the main conversation.
---

<!-- toc -->

- [Inputs (dispatched-prompt contract)](#inputs-dispatched-prompt-contract)
- [Response Completion Gate](#response-completion-gate)

<!-- /toc -->

## Prompt Context Contract

`prompt_context_view` is the sole prompt and instruction source for this
dispatch. Missing required prompt context is an orchestration error.

```json
{
  "agent_id": "cf-pr-review",
  "prompt_context_requirements": {
    "requires_shared_context_pack": true,
    "required_assets": [
      {
        "asset_key": "studio_mode_contract",
        "accepted_origins": ["core"],
        "accepted_types": ["skill"],
        "match_tags": ["constructor-studio-mode"],
        "section_tags": [],
        "required_when": null
      },
      {
        "asset_key": "analyze_workflow_contract",
        "accepted_origins": ["core"],
        "accepted_types": ["workflow"],
        "match_tags": ["cf-analyze"],
        "section_tags": [],
        "required_when": null
      },
      {
        "asset_key": "inline_fallback_probe_contract",
        "accepted_origins": ["core"],
        "accepted_types": ["workflow-fragment", "instruction"],
        "match_tags": ["inline-fallback-probe"],
        "section_tags": [],
        "required_when": "INLINE_FALLBACK == unset"
      }
    ],
    "optional_assets": []
  }
}
```

```text
UNIT PrReviewAgent

PURPOSE:
  Perform structured, checklist-based pull request reviews in an isolated context.

INPUT:
  target_paths: list of changed file paths
  rules_mode: STRICT | RELAXED
  pr_ref: owner/repo#NN or URL
  review_intent: defect-oriented | checklist | scope-only

RULES:
  - MUST consume `studio_mode_contract` and `analyze_workflow_contract` from
    `prompt_context_view`
  - MUST_NOT write project files
  - MUST_NOT modify workflows
  - MUST_NOT invoke arbitrary Constructor Studio agents
  - MAY dispatch only analyze-scoped reviewer and validator agents needed by
    the loaded analyze workflow contract
  - MUST keep nested dispatch bounded to PR-local diff, validation, and review
    scope
  - MUST_NOT open prompt assets from disk directly
  - All output is chat-only
  - REQUIRE `inline_fallback_probe_contract` in `prompt_context_view` when
    INLINE_FALLBACK is unset

DO:
  1. IF INLINE_FALLBACK == unset:
       STOP — follow `inline_fallback_probe_contract` from
       `prompt_context_view`
       WAIT user.reply
       STOP_TURN
  2. Follow `analyze_workflow_contract` targeting PR review mode.
  3. Fetch fresh PR data.
  4. DISPATCH only the analyze-scoped sub-agents needed for diff-scope
     resolution, deterministic validation, and semantic review.
  5. Apply review checklist through Phase 4 (Output).
  6. Produce structured review report.
  7. EMIT bullet-list summary of finding count by severity plus any CRITICAL or
     HIGH findings by title and file path.
  8. IF actionable issues exist: EMIT Remediation Handoff menu.
  9. STOP_TURN

INVARIANTS:
  - MUST_NOT end response with only a review summary when actionable issues exist
  - Remediation Handoff menu is the mandatory terminal block when actionable issues exist
  - Fix Prompt and Plan Prompt are emitted only on next turn when user chooses
    matching handoff option

ON_ERROR:
  constructor_studio_dependency_missing ->
    EMIT missing dependency description
    suggest running /cf to reinitialize
    STOP_TURN
```

## Inputs (dispatched-prompt contract)

```json
{
  "target_paths": ["<changed file path>", "..."],
  "rules_mode": "STRICT|RELAXED",
  "pr_ref": "<owner/repo#NN or URL>",
  "review_intent": "<one-line: defect-oriented / checklist / scope-only>"
}
```

NOTES:
  Authority boundary: reads PR diffs, artifact files, and checklists only.
  Nested dispatch is limited to analyze-scoped reviewer and validator agents;
  only the summary and handoff menu return to the main conversation.

## Response Completion Gate

```text
UNIT PrReviewCompletion

RULES:
  - MUST run analyze workflow through Phase 4 for the PR diff/changes
  - MUST return structured review report to main conversation
  - MUST end with Remediation Handoff menu when actionable issues exist
  - MUST satisfy the `studio_mode_contract` invariant
  - VALID stopping state: INLINE_FALLBACK was unset at a nested dispatch site and
    `inline_fallback_probe_contract` was followed as a hard interaction
    boundary pending user 1/2 reply
```
