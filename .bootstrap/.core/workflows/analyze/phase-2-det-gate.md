---
name: analyze-phase-2-det-gate
description: "Invoke when running Analyze Phase 2 to dispatch cf-deterministic-validator and gate semantic review on its result."
purpose: Analyze Phase 2 — dispatch cf-deterministic-validator sub-agent and gate semantic review on result
loaded_by: workflows/analyze.md
version: 1.0
---

```text
UNIT AnalyzePhase2DeterministicGate

PURPOSE:
  Dispatch cf-deterministic-validator and gate semantic review on its result.

WHEN:
  SEMANTIC_ONLY == false AND EXPLAIN_MODE == false

DO:
  IF SEMANTIC_ONLY == true OR EXPLAIN_MODE == true:
    CONTINUE workflows/analyze/phase-3-semantic.md
  REQUIRE inline-fallback-probe.md has run (workflows/shared/inline-fallback-probe.md)
  DISPATCH cf-deterministic-validator with:
    target_paths    = diff_scope.review_targets when CHANGE_REVIEW=true, else {PATHS}
    target_kinds    = per-path map from artifacts.toml (default {TARGET_TYPE} when unmapped)
    rules_mode      = "{STRICT|RELAXED}"
    language_check_configured = true|false from .studio-workspace.toml
  Embed returned Validation Results block verbatim into Phase 4 output.
  Carry det_findings JSON forward into remediation-handoff.md when applicable.
  IF gate result == FAIL:
    CONTINUE workflows/analyze/phase-4-output/index.md
    REQUIRE remediation-handoff.md when actionable issues exist
  IF gate result == PASS OR SKIPPED (with Validator availability proof):
    CONTINUE workflows/analyze/phase-3-semantic.md

RULES:
  - MUST run inline-fallback-probe.md before any cf-* sub-agent dispatch
  - MUST skip this unit when SEMANTIC_ONLY=true OR EXPLAIN_MODE=true
  - MUST embed Validation Results block verbatim; MUST_NOT redefine the field set
  - MUST_NOT use the agent's own checklist walkthrough as a substitute for the
    dispatched validator (anti-pattern SIMULATED_VALIDATION)
  - MUST emit remediation-handoff.md when FAIL produces actionable issues

NOTES:
  Validation Results block schema is owned by:
    {cf-studio-path}/.core/skills/studio/agents/cf-deterministic-validator.md § Output
  Always reproduce the template from the agent file verbatim.
  Pre-dispatch fail-stop and Mode B degradation rules are in:
    {cf-studio-path}/.core/skills/studio/sub-agent-dispatch.md
  The dispatched sub-agent executes the actual resolved validator command
  from the target bootstrap (e.g. `cpt` in a Studio .bootstrap, or `cfs`
  in a Constructor Studio adapter) for validate / validate-artifact /
  validate-toc / check-language routes.
```

## Phase 2: Deterministic Gate

<!-- The `Validation Results` block schema is owned by the deterministic-validator agent file (`{cf-studio-path}/.core/skills/studio/agents/cf-deterministic-validator.md` § Output). Workflows reference it by name only; do NOT redefine the field set here — always reproduce the template from the agent file verbatim. -->

If `SEMANTIC_ONLY=true` OR `EXPLAIN_MODE=true`, skip this sub-file and go to `workflows/analyze/phase-3-semantic.md`.

Requires: `workflows/shared/inline-fallback-probe.md` before any `cf-*` sub-agent dispatch. Pre-dispatch fail-stop and Mode B degradation rules are defined in `{cf-studio-path}/.core/skills/studio/sub-agent-dispatch.md`.

Dispatch sub-agent `cf-deterministic-validator` with the JSON contract documented in `{cf-studio-path}/.core/skills/studio/agents/cf-deterministic-validator.md`. Inputs: see "Inputs (dispatched-prompt contract)" in that agent file (mandatory vs optional listed there). Orchestrator-supplied values for this dispatch:

- `target_paths` = `diff_scope.review_targets when CHANGE_REVIEW=true, otherwise {PATHS}`
- `target_kinds` = per-path map keyed by each entry in `target_paths`, value from `artifacts.toml` (default `{TARGET_TYPE}` when unmapped)
- `rules_mode` = `"{STRICT|RELAXED}"`
- `language_check_configured` = `true|false` from `.studio-workspace.toml` (`[validation] allowed_content_languages`)

The agent returns the canonical `Validation Results` block plus a `det_findings` JSON array. Embed the block verbatim into `workflows/analyze/phase-4-output/index.md` output; carry `det_findings` forward into the `workflows/analyze/phase-4-output/remediation-handoff.md` menu when applicable.

Gate behavior:
- If the overall deterministic gate is `FAIL`, skip `workflows/analyze/phase-3-semantic.md` and jump to `workflows/analyze/phase-4-output/index.md` to report blocking issues; the `workflows/analyze/phase-4-output/remediation-handoff.md` menu is mandatory when actionable issues exist.
- If `PASS` or `SKIPPED` (with `Validator availability proof`), continue to `workflows/analyze/phase-3-semantic.md`.

> **⛔ CRITICAL**: The agent's own checklist walkthrough is **NOT** a substitute for the deterministic validator. See anti-pattern `SIMULATED_VALIDATION`. The dispatched sub-agent executes the actual resolved validator command from the target bootstrap (for example `cpt` in a Studio `.bootstrap`, or `cfs` in a Constructor Studio adapter) for validate / validate-artifact / validate-toc / check-language routes.
