---
name: plan-escalation-gate
description: "Invoke when running the generate Phase 0.1 plan-escalation gate (generate.md only; analyze.md uses its own gate with different thresholds/route)."
purpose: Canonical Phase 0.1 plan-escalation gate for generate.md only; analyze.md uses workflows/analyze/phase-0.1-plan-escalation-gate.md (different thresholds/route).
loaded_by: workflows/generate.md
version: 1.0
---

## Phase 0.1: Plan Escalation Gate

```text
UNIT PlanEscalationGate

PURPOSE:
  Decide whether to escalate to /cf-plan or proceed inline,
  based on sub-agent approval state and estimated context size.

STATE:
  SUB_AGENT_SESSION_APPROVED: unset | true
    scope: session
  INLINE_FALLBACK: unset | true | false
    scope: workflow_run
  ESCALATION_ESTIMATE: integer (lines)

WHEN:
  entering Phase 0.1 of generate workflow

DO:
  SET ESCALATION_ESTIMATE = computed line count

  IF raw-input-overflow rule has already fired for direct prompt/provided-file
  input over 500 lines:
    EMIT raw-input-overflow plan-vs-continue choice (higher precedence — resolve first)
    STOP_TURN

  IF SUB_AGENT_SESSION_APPROVED == true AND INLINE_FALLBACK == false:
    CONTINUE SubAgentDecompositionBypass

  IF SUB_AGENT_SESSION_APPROVED == true AND INLINE_FALLBACK == unset:
    RUN workflows/shared/inline-fallback-probe.md
    CONTINUE PlanEscalationGate (re-evaluate after resolution)

  CONTINUE LegacySizeBasedEscalation

NOTES:
  raw-input-overflow rule defined in the calling workflow's Phase 0 raw-input check
  (generate.md Phase 0).
```

```text
UNIT SubAgentDecompositionBypass

PURPOSE:
  Skip plan escalation when sub-agents are approved; defer decomposition
  to Phase 1.5.

RULES:
  - MUST NOT propose /cf-plan when SUB_AGENT_SESSION_APPROVED == true
    AND INLINE_FALLBACK == false
  - MUST compute and log estimate for telemetry:
    "Plan-escalation: estimate={ESCALATION_ESTIMATE} lines, decomposition deferred to Phase 1.5 (sub-agents approved)"
  - MUST NOT emit any user-facing escalation menu
  - MUST proceed to the next phase

NOTES:
  Decomposition is handled in-workflow by workflows/generate/phase-1.5-author-plan.md,
  which always produces an AUTHOR_EXECUTION_PLAN (parallel sub-agent dispatch in
  Phase 4) regardless of estimated size.
```

```text
UNIT LegacySizeBasedEscalation

PURPOSE:
  Apply size-based escalation for the inline-fallback path.

WHEN:
  SUB_AGENT_SESSION_APPROVED != true
  OR INLINE_FALLBACK == true

DO:
  REQUIRE estimate of total context from:
    rules.md
    generation-phase dependencies needed for this run
      (e.g. template.md, example.md, checklist.md only when explicitly required before writing)
    expected output size
    project context
    ~30% reasoning overhead

  IF ESCALATION_ESTIMATE <= 1500:
    CONTINUE next phase (optimal zone)

  IF ESCALATION_ESTIMATE >= 1501 AND ESCALATION_ESTIMATE <= 2500:
    EMIT "This is a medium-sized task. Activating chunked loading — will checkpoint if context runs low."
    CONTINUE next phase

  IF ESCALATION_ESTIMATE > 2500:
    EMIT_MENU PlanEscalationMenu
    WAIT user.reply
    STOP_TURN

MENU PlanEscalationMenu:
  TITLE: |
    ⚠️ This task is large — estimated ~{ESCALATION_ESTIMATE} lines of context needed (`rules.md`, active generation dependencies, output, project ctx).
    This exceeds the safe single-context budget (~2500 lines). The plan workflow can decompose this into focused phases (≤500 lines each) that ensure every kit rule is followed and nothing is skipped.

    Options:
    1. Switch to /cf-plan (recommended for full quality)
    2. Continue here (risk: context overflow, rules may be partially applied)

    Suggested: 1 because plan decomposition is the safer default for large tasks.
    Reply with `1` or `2`.
  OPTIONS:
    1 ->
      EMIT "Run /cf-plan generate {KIND} with the same parameters."
      STOP_TURN
    2 ->
      EMIT "Proceeding in single-context mode — quality may be reduced for large artifacts."
      CONTINUE next phase
  INVALID:
    EMIT "Reply with 1 or 2."
    WAIT user.reply
    STOP_TURN

NOTES:
  Why these thresholds: rule-following quality drops above ~2000 lines of active
  constraints; SDLC kit files plus output and reasoning can easily exceed 2500.

  Per-option rationale (not part of user-facing prompt):
    Option 1 (Switch to /cf-plan): decomposes the task into focused phases,
      reduces context-overflow risk.
    Option 2 (Continue here): faster, but context overflow may reduce rule coverage.
```
