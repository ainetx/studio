---
cf: true
type: workflow-fragment
parent: workflows/generate/phase-1.5-author-plan.md
description: Canonical state contract for Generate Phase 1.5 author-plan offer resolution, continuation states, and terminal cancellation states.
---

<!-- toc -->

- [State Contract](#state-contract)
  - [Mandatory-Decompose Branch](#mandatory-decompose-branch)
  - [Downstream Requirements](#downstream-requirements)

<!-- /toc -->

## State Contract

```text
UNIT Phase15StateContract

PURPOSE:
  Define canonical AUTHOR_PLAN_OFFER_RESOLVED values, state families,
  and derived state variables.

STATE:
  AUTHOR_PLAN_OFFER_RESOLVED:
    memory
    | disk
    | declined
    | auto_skipped_no_author_plan_flag
    | auto_skipped_rules_disabled
    | cancelled_by_stop_token
    | cancelled_planner_failure
    | cancelled_partial_write

  AUTHOR_EXECUTION_PLAN: parsed author_plan JSON | null
  AUTHOR_PLAN_CACHE_DIR: directory path | null (only when AUTHOR_PLAN_OFFER_RESOLVED=disk
    AND cache render completed successfully)

RULES:
  Continuation states:
    memory | disk | declined | auto_skipped_no_author_plan_flag |
    auto_skipped_rules_disabled

  Terminal cancellation states:
    cancelled_by_stop_token | cancelled_planner_failure | cancelled_partial_write

  AUTHOR_EXECUTION_PLAN:
    - MUST be set to parsed author_plan JSON ONLY when
      AUTHOR_PLAN_OFFER_RESOLVED is memory or disk
    - MUST be null otherwise

  AUTHOR_PLAN_CACHE_DIR:
    - MUST be set ONLY when AUTHOR_PLAN_OFFER_RESOLVED=disk AND cache
      render completed successfully
    - MUST NOT be claimed unless successfully written subset is explicitly
      reported to the user when disk-mode cache writes fail

  Auto-skip conditions:
    - user passed --no-author-plan in the invocation
    - KIND's rules.md explicitly sets author_plan = "disabled"
```

### Mandatory-Decompose Branch

```text
UNIT Phase15MandatoryDecomposeBranch

PURPOSE:
  Define behavior when SUB_AGENT_SESSION_APPROVED=true AND INLINE_FALLBACK=false
  AND no auto-skip condition applies.

WHEN:
  SUB_AGENT_SESSION_APPROVED == true
  AND INLINE_FALLBACK == false
  AND auto_skip_condition == false

RULES:
  - Initial user choice is ONLY plan storage (memory vs disk)
  - FORBID direct user-decline from the offer itself
  - auto_skipped_* states are unreachable in this branch
  - Planner dispatch is unconditional
  - AUTHOR_EXECUTION_PLAN is expected non-null on successful planner exit
  - declined REMAINS reachable through planner-failure recovery ONLY when
    planner validation fails and user explicitly chooses "Skip author plan"
    recovery option; that path is a valid continuation state to Phase 3
```

### Downstream Requirements

```text
UNIT Phase15DownstreamRequirements

PURPOSE:
  Enforce Phase 3 / Phase 4 entry guards based on AUTHOR_PLAN_OFFER_RESOLVED.

RULES:
  - Phase 3 and Phase 4 MUST only run when AUTHOR_PLAN_OFFER_RESOLVED
    is a continuation state
  - IF a later phase observes a terminal cancellation state:
    MUST fail-stop without dispatching write-capable author
    MUST leave target files untouched
  - Plan-cache files written under disk mode are not target-file writes;
    cleanup/resume handling defined by disk-mode.md and error-handling.md
```
