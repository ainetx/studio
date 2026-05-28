---
description: "Invoke when the brainstorm session ends (user wrap-up, stop-token, or BRAINSTORM_MAX_ROUNDS cap) and the wrap-up summary + handoff to Phase 1 must run."
name: phase-0.7-wrap-handoff
purpose: Brainstorm loop exit — consolidated design block, approve/iterate/discard branches, stop-token semantics, Phase 1 hand-off
loaded_by: workflows/generate/phase-0.7/index.md
version: 1.1
---

<!-- toc -->

- [Consolidated design block (loop exit)](#consolidated-design-block-loop-exit)
- [Contributions shape and orchestration modes](#contributions-shape-and-orchestration-modes)
- [Hand-off to `workflows/generate/phase-1-collect.md`](#hand-off-to-workflowsgeneratephase-1-collectmd)

<!-- /toc -->

### Consolidated design block (loop exit)

```text
UNIT BrainstormWrapHandoff

PURPOSE:
  Emit consolidated design block on loop exit; route to Phase 1 based on user choice.

DO:
  WHEN state.topic_current becomes None:
    IF rules_mode == RELAXED:
      PREPEND "⚠ Brainstorm without kit rules (reduced quality assurance)"
    EMIT exactly:
---
Brainstorm complete after {N} rounds.
Panel: {personas}
Topics covered: {topic_history}

Decisions:
- {section_or_key}: {value}

Open questions (carry into inputs):
- {open_question}

Reply `approve` (suggested) to hand decisions to input collection,
`iterate` to reopen a specific topic for another round, or `discard handoff`
to ignore brainstorm decisions and proceed from scratch. In `save` mode, the
saved brainstorm cache remains on disk and follows manual retention.
---
    WAIT user.reply
    STOP_TURN

MENU WrapHandoffMenu:
  TITLE: Brainstorm wrap-up
  OPTIONS:
    approve ->
      SET PRE_RESOLVED_INPUTS = state.decisions
      SET CARRYOVER_QUESTIONS = state.open_questions
      CONTINUE workflows/generate/phase-1-collect.md
    iterate ->
      EMIT "Which topic gap should be reopened?"
      WAIT user.reply
      STOP_TURN
      APPEND as forced topic
      SET pending_round_kind = "topic"
      RESUME round loop (first iteration of resumed loop is always topic-round)
    discard | discard handoff ->
      SET PRE_RESOLVED_INPUTS = {}
      SET CARRYOVER_QUESTIONS = []
      NOTE: if session used save, do NOT delete cache artifacts
      CONTINUE workflows/generate/phase-1-collect.md
  stop_token (stop / enough / done) ->
    NOTE: unanswered questions become open_questions;
          current decisions carry forward
    CONTINUE workflows/generate/phase-1-collect.md

RULES:
  - MUST prepend RELAXED brainstorm warning when rules_mode == RELAXED
    per the contract declared in save-and-rules.md § Rules respect
  - MUST NOT delete cache artifacts on discard when session used save
```

### Contributions shape and orchestration modes

```text
UNIT BrainstormWrapContributionsShape

PURPOSE:
  Clarify that wrap-up logic is protocol-agnostic; both modes produce
  identical contributions[] shape.

NOTES:
  Fan-out mode (rounds[].panel_mode == "fan-out"):
    All relevant experts dispatched in parallel; each independently produces
    questions and critique; orchestrator collects and flattens before persisting.

  Single-agent panel (rounds[].panel_mode == "single-agent"):
    One expert runs full round logic; other panelists provide structured critique
    per protocol; panel renderer emits envelope; orchestrator flattens before persisting.

  Semantic equivalence post-flatten:
    Both modes produce identical state.rounds[].contributions[] shape.
    Each entry has expert_id, relevant, questions[], critique, next_topic_proposal.
    Dissent computations remain valid regardless of dispatch shape.

  Single-pass protocol behavior:
    When rounds[].protocol == "single-pass" (only valid under single-agent mode),
    critique field in non-primary panelists is absent or empty.
    Dissent computations remain sound.

  Wrap-up evaluation notes:
    High status="degraded" rate may warrant user review before approve.
    rounds[].panel_mode presence enables auditing which rounds used single-agent
    pooling vs. fan-out parallelism.
```

### Hand-off to `workflows/generate/phase-1-collect.md`

```text
UNIT BrainstormPhase1Handoff

PURPOSE:
  Define the handoff contract to Phase 1.

DO:
  CONTINUE workflows/generate/phase-1-collect.md
  WITH:
    pre_resolved_inputs = PRE_RESOLVED_INPUTS
    open_questions = CARRYOVER_QUESTIONS

NOTES:
  The collector marks pre-filled sections [from brainstorm] and surfaces
  a Carryover Questions mini-section.
  Open, load, and follow {cf-studio-path}/.core/workflows/generate/phase-1-collect.md.
```
