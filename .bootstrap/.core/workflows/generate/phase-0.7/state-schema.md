---
description: "Invoke when the brainstorm state object must be initialized, inspected, or persisted — defines the canonical JSON schema including BRAINSTORM_MAX_ROUNDS."
name: phase-0.7-state-schema
purpose: Brainstorm state object schema (held by orchestrator, persisted between rounds) and default-location rule
loaded_by: workflows/generate/phase-0.7/index.md
version: 1.1
---

<!-- toc -->

- [State (held by orchestrator, persisted between rounds)](#state-held-by-orchestrator-persisted-between-rounds)
- [Round Field Reference](#round-field-reference)
  - [panel_mode (orchestration strategy)](#panel_mode-orchestration-strategy)
  - [protocol (single-agent interaction pattern)](#protocol-single-agent-interaction-pattern)
  - [status (round outcome)](#status-round-outcome)
  - [health (round resilience tracking)](#health-round-resilience-tracking)
  - [envelope (wire-level blocks, orchestrator-internal)](#envelope-wire-level-blocks-orchestrator-internal)
- [Loader Lazy-Normalization Rule](#loader-lazy-normalization-rule)
- [Run Config Sibling Pattern](#run-config-sibling-pattern)
- [Default Location](#default-location)

<!-- /toc -->

### State (held by orchestrator, persisted between rounds)

```json
{
  "session_id": "{slug}-{ISO}",
  "kind": "{KIND}",
  "rules_loaded": false,
  "kit_rules_path": null,
  "template_path": "{path or null}",
  "example_path": "{path or null}",
  "panel": [
    { "id": "E1", "persona": "...", "focus": ["..."], "rationale": "..." }
  ],
  "rounds": [
    {
      "n": 1,
      "kind": "topic",
      "panel_mode": "single-agent",
      "protocol": "independent-then-critique",
      "status": "ok",
      "health": {
        "degraded": false,
        "reason": null,
        "attempts_used": 1
      },
      "topic": { "id": "T1", "text": "...", "section": "<template-section or null>" },
      "contributions": [
        { "expert_id": "E1", "relevant": true,
          "questions": [{ "id": "E1Q1", "text": "...",
                          "decision_key": "<section-or-topic>:<expert-id>:<question-key>",
                          "proposed_default": "...", "rationale": "..." }],
          "critique": "...",
          "next_topic_proposal": { "text": "...", "why": "..." } },
        { "expert_id": "E2", "relevant": false, "reason": "..." }
      ],
      "answers": [{ "question_id": "E1Q1",
                    "decision_key": "<section-or-topic>:<expert-id>:<question-key>",
                    "value": "..." }],
      "answer_keys": ["<section-or-topic>:<expert-id>:<question-key>"],
      "next_topic_chosen": "T2"
    },
    {
      "n": 2,
      "kind": "challenge",
      "panel_mode": "single-agent",
      "protocol": "independent-then-critique",
      "status": "degraded",
      "health": {
        "degraded": true,
        "reason": "One expert agent timeout; critique completed within limits",
        "attempts_used": 2
      },
      "topic": { "id": "T1", "text": "...", "section": "<template-section or null>" },
      "challenged_decisions": { "<key>": "<prior-value-at-challenge-start>" },
      "contributions": [
        { "expert_id": "E1", "relevant": true,
          "questions": [{ "id": "E1Q1", "text": "<counter-question>",
                          "decision_key": "<key>",
                          "proposed_default": "<counter-proposal>", "rationale": "..." }],
          "critique": "...",
          "next_topic_proposal": null }
      ],
      "answers": [{ "question_id": "E1Q1", "decision_key": "<key>",
                    "value": "<accept|keep-prior|custom>" }],
      "answer_keys": ["<template-section-or-key-touched>"],
      "next_topic_chosen": null
    }
  ],
  "topic_history": ["T1", "T2"],
  "topic_current": { "id": "T2", "text": "...", "section": "<template-section or null>" },
  "next_topic_proposals": [
    { "text": "...", "proposed_by": ["E1"] }
  ],
  "decisions": { "<template-section-or-key>": "<resolved-value>" },
  "open_questions": [ "<unanswered or skipped>" ],
  "round_count": 0,
  "BRAINSTORM_MAX_ROUNDS": 10
}
```

```text
UNIT BrainstormStateRules

PURPOSE:
  Define canonical rules for state field semantics and update behavior.

RULES:
  round_count:
    - MUST be incremented by orchestrator after every completed round
      (both kind="topic" and kind="challenge")
  BRAINSTORM_MAX_ROUNDS:
    - default: 10
    - configurable: SET to N when user replies yes:N to offer
  rules_loaded:
    - MUST be set true ONLY when kit_rules_path was resolved and loaded
    - MUST be false for RELAXED/no-kit sessions or chat-only exploratory runs
    - MUST include kit_rules_path alongside rules_loaded in every brainstorm
      facilitator or expert dispatch
  topic_current:
    - MUST store full topic object {id, text, section}; MUST NOT store only id
    - topic_history stores id-only history
    - null before first topic is chosen
  rounds[].kind:
    - "topic": normal exploratory; appends to topic_history;
      refreshes next_topic_proposals
    - "challenge": re-opens preceding round's decisions; reuses same topic;
      does NOT append to topic_history; does NOT refresh next_topic_proposals
  rounds[].answer_keys:
    - topic-rounds: lists decisions keys written (skip answers excluded)
    - challenge-rounds: lists ONLY keys overwritten by accept/<custom>;
      keep/skip excluded; empty list when user skipped/kept every question
      (suppresses option C on next post-round menu)
  rounds[].challenged_decisions:
    - set ONLY on kind="challenge" rounds
    - snapshot of {key: value} at challenge start, scoped to
      state.rounds[-1].answer_keys (the preceding answer-writing round)
    - later overwrites do NOT retro-edit it
  next_topic_proposals:
    - deduped/merged list from most recent kind="topic" round
    - survives subsequent kind="challenge" rounds
  decisions overwrite semantics:
    - challenge-round accept/custom OVERWRITES state.decisions[key] in place
    - prior values not versioned at decisions level
    - rounds[] array preserves audit trail
```

---

### Round Field Reference

#### panel_mode (orchestration strategy)

```text
UNIT BrainstormPanelModeField

PURPOSE:
  Define rounds[].panel_mode field semantics.

STATE:
  rounds[].panel_mode: fan-out | single-agent
    default: single-agent

RULES:
  single-agent:
    - MUST dispatch cf-brainstorm-panel once per round (not per expert)
    - One expert is primary; secondary experts deliberate inside same agent
    - One cohesive sub-agent context per round; host-independent; INLINE_FALLBACK is a no-op
    - protocol field MUST be non-null
  fan-out:
    - MUST dispatch all relevant panel members in parallel via cf-brainstorm-expert
    - No inter-expert live communication
    - Requires host with native sub-agent parallelism
    - protocol field MUST be null
  INVARIANTS:
    - MUST NOT mix strategies within a single round
```

#### protocol (single-agent interaction pattern)

```text
UNIT BrainstormProtocolField

PURPOSE:
  Define rounds[].protocol field semantics.

STATE:
  rounds[].protocol: independent-then-critique | single-pass | null

RULES:
  - Non-null ONLY when panel_mode == "single-agent"
  - null ONLY when panel_mode == "fan-out"
  independent-then-critique:
    - Primary expert produces questions independently
    - Secondary members review primary output and provide structured critique
  single-pass:
    - Primary expert produces full round output
    - Secondary members have read-only visibility; do not produce critique
    - Minimal latency; suitable for time-sensitive scenarios
```

#### status (round outcome)

```text
UNIT BrainstormStatusField

PURPOSE:
  Define rounds[].status field semantics.

STATE:
  rounds[].status: ok | degraded | skipped

NOTES:
  ok: all experts completed within SLA; no fallback needed
  degraded: one or more experts exceeded SLA; round completed with partial output;
    review health.reason before accepting decisions
  skipped: round not executed; contributions array is empty or omitted
```

#### health (round resilience tracking)

```text
UNIT BrainstormHealthField

PURPOSE:
  Define rounds[].health field semantics for troubleshooting and retry logic.

STATE:
  rounds[].health:
    degraded: bool
    reason: string or null
    attempts_used: positive integer
    default: { degraded: false, reason: null, attempts_used: 1 }

NOTES:
  degraded: true if one or more agents failed within SLA
  reason: human-readable explanation; null when degraded=false
  attempts_used: count of execution attempts for this round; resets per round
```

#### envelope (wire-level blocks, orchestrator-internal)

```text
UNIT BrainstormEnvelopeField

PURPOSE:
  Define the transient envelope wire structure used during agent dispatch.

RULES:
  - MUST NOT persist envelope in rounds[] — transient wire-level only
  - Orchestrator canonicalizes block order before flattening

NOTES:
  Envelope schema:
    { "kind": "independent", "rows": [{ "expert_id": "E1", "block": "...", "metadata": {...} }] }
    OR
    { "kind": "critique", "rows": [{ "expert_id": "E2", "block": "...", "metadata": {...} }] }
  kind "independent": primary contributions
  kind "critique": secondary reviews
  rows: flattened into contributions[] after canonicalization
```

---

### Loader Lazy-Normalization Rule

```text
UNIT BrainstormLoaderNormalization

PURPOSE:
  Normalize missing fields in loaded state.json on next save (backward compatibility).

DO:
  IF rounds[].panel_mode is missing (pre-1.1 state files):
    SET rounds[].panel_mode = "fan-out"
    SET rounds[].protocol = null

  IF rounds[].health is missing:
    SET rounds[].health = { degraded: false, reason: null, attempts_used: 1 }

  IF rounds[].status is missing:
    IF round_count > n: SET status = "ok"
    ELIF round_count == n AND contributions.length > 0: SET status = "ok"
    ELIF contributions.length == 0: SET status = "skipped"

RULES:
  - MUST apply normalization before state is operational
  - MUST NOT load state with missing required fields without normalizing first
```

---

### Run Config Sibling Pattern

```text
UNIT BrainstormRunConfigPattern

PURPOSE:
  Define the run_config.json sibling file structure and panel mode fields.

NOTES:
  File layout:
    {cf-studio-path}/.cache/brainstorm/{session_id}/
    ├── state.json        # Persisted round-by-round state (this schema)
    └── run_config.json   # Environment + execution config (separate schema)

  Contents of run_config.json:
    {
      "environment": {
        "cpt_path": "/path/to/.cf",
        "python_version": "3.11",
        "agent_timeout_seconds": 120,
        "model": "claude-opus-4.1",
        "temperature": 0.7
      },
      "session_metadata": {
        "created_at": "2025-05-23T14:30:00Z",
        "user_email": "user@example.com"
      },
      "PANEL_MODE_TOPIC": "single-agent",
      "PANEL_MODE_CHALLENGE": "single-agent"
    }

  PANEL_MODE_TOPIC / PANEL_MODE_CHALLENGE:
    enum {"single-agent", "fan-out"} or null
    Set from offer reply; parsing contract owned by offer.md § Reply parsing.
    null (or absent) means "no offer-time override"; round loop falls back to env
    var then to workflow default "single-agent".
    mode= modifier always sets both fields to same value;
    use env vars to set independently.

  Config drift detection:
    Compare current runtime env against saved run_config.json.
    DEFAULT: current environment wins; log drift for user inspection.
    WITH --reconfigure flag: reload and use saved config.
```

---

### Default Location

```text
UNIT BrainstormStateLocation

PURPOSE:
  Define where brainstorm state is kept and when it is persisted.

RULES:
  - MUST keep state in-memory by orchestrator across rounds
  - MUST persist to {cf-studio-path}/.cache/brainstorm/{session_id}/state.json
    ONLY when user picked explicit save mode AND current output destination
    allows file writes
  - MUST NOT write cache artifacts for chat-only/no-write sessions
  - MUST use in-chat checkpoint for compaction recovery in chat-only mode
```
