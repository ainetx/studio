---
name: analyze-phase-0.1-plan-escalation-gate
description: "Invoke when running Analyze Phase 0.1 to evaluate the analyze-specific plan escalation gate (thresholds and dispatch route differ from generate)."
purpose: Analyze Phase 0.1 — analyze-specific plan escalation gate (thresholds and dispatch route differ from generate)
loaded_by: workflows/analyze.md
version: 1.0
---

<!-- toc -->
<!-- /toc -->

```text
UNIT AnalyzePlanEscalationGate

PURPOSE:
  Evaluate context size estimate and either bypass escalation (sub-agents
  approved) or offer plan escalation to the user.

STATE:
  PLANNER_ESCALATION_RESULT: bypassed | proceed_small | proceed_medium_warn | escalated
    default: unset

WHEN:
  After all Phase 0 dependencies are loaded

DO:
  IF raw-input-overflow.md has already fired for direct input over 500 lines:
    EMIT explicit plan-vs-continue choice from that rule before applying bypass
  IF SUB_AGENT_SESSION_APPROVED == true AND INLINE_FALLBACK == false:
    EMIT "Plan-escalation: estimate={N} lines, decomposition deferred to Phase 2.5 (sub-agents approved)"
    SET PLANNER_ESCALATION_RESULT = bypassed
    CONTINUE next phase
  ELSE:
    Estimate total context: rules.md Validation + checklist.md + artifact +
      related cross-refs + expected analysis output + ~30% reasoning overhead
    IF estimate <= 1200:
      SET PLANNER_ESCALATION_RESULT = proceed_small
      CONTINUE next phase
    IF estimate is 1201-2000:
      SET PLANNER_ESCALATION_RESULT = proceed_medium_warn
      EMIT "This is a medium-sized analysis. Activating chunked loading — will output PARTIAL if context runs low."
      CONTINUE next phase
    IF estimate > 2000:
      EMIT_MENU PlanEscalationMenu
      WAIT user.reply
      STOP_TURN

MENU PlanEscalationMenu:
  TITLE: |
    ⚠️ This analysis is large — estimated ~{N} lines of context needed:
      - checklist.md:  ~{n} lines
      - rules.md:      ~{n} lines
      - artifact:      ~{n} lines
      - cross-refs:    ~{n} lines
      - output:        ~{n} lines (estimated)

    This exceeds the safe single-context budget (~2000 lines).
    The plan workflow can decompose this into focused analysis phases (≤500 lines each)
    that ensure every checklist item is checked and nothing is skipped.

    Suggested: 1 because plan decomposition is the safer default for >2000-line budgets.
  OPTIONS:
    1 -> SET PLANNER_ESCALATION_RESULT = escalated
         EMIT "Switch to /cf-plan analyze {KIND} with the same parameters."
         STOP_TURN
    2 -> EMIT "Proceeding in single-context mode — some checks may be missed for large artifacts."
         CONTINUE next phase
  INVALID:
    EMIT "Reply 1 or 2."
    WAIT user.reply
    STOP_TURN

RULES:
  - MUST run this gate before any further Phase-0 or Phase-1 work
  - MUST_NOT propose /cf-plan when SUB_AGENT_SESSION_APPROVED=true AND INLINE_FALLBACK=false
  - MUST apply raw-input-overflow rule at higher precedence than the bypass
  - MUST run legacy size-based escalation only when SUB_AGENT_SESSION_APPROVED is
    unset/false OR INLINE_FALLBACK=true
```
