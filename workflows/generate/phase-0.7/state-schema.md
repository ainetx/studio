---
description: "Invoke when the brainstorm state object must be initialized, inspected, or persisted — defines the canonical JSON schema including BRAINSTORM_MAX_ROUNDS."
name: phase-0.7-state-schema
purpose: Brainstorm state object schema (held by orchestrator, persisted between rounds) and default-location rule
loaded_by: workflows/generate/phase-0.7/index.md
version: 1.0
---

<!-- toc -->

- [State (held by orchestrator, persisted between rounds)](#state-held-by-orchestrator-persisted-between-rounds)

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

`round_count` is incremented by the orchestrator after every completed round
(both `kind="topic"` and `kind="challenge"`). `BRAINSTORM_MAX_ROUNDS` defaults
to `10`. It is configurable: when the user replies `yes:N` to the offer (e.g.
`yes:15`), the orchestrator sets `BRAINSTORM_MAX_ROUNDS = N` before entering
the round loop. The cap-check and cap-prompt behavior live in
`workflows/generate/phase-0.7/round-loop.md` § Round loop.

`rules_loaded` is a boolean, not an implied constant. Set it to `true` only
when `kit_rules_path` was resolved and loaded for this brainstorm session; set
it to `false` for RELAXED/no-kit sessions or any chat-only exploratory run
without kit rules. When dispatching brainstorm facilitator or expert agents,
include `kit_rules_path` alongside `rules_loaded` so the receiver can
distinguish "rules intentionally absent" from "rules required but missing".

`topic_current` is the full topic object used by the round-loop dispatch
contract, or `null` before the first topic is chosen. Do not store only the
topic id string; `topic_history` is the id-only history.

`rounds[].kind` is `"topic"` (default) for normal exploratory rounds.
`kind="challenge"` rounds re-open the immediately-preceding answer-writing round's
decisions for cross-expert pushback. Challenge rounds may challenge the
accepted/custom answers from a prior challenge round. Only `kind="topic"`
rounds append to `topic_history` and refresh `next_topic_proposals`;
`kind="challenge"` rounds reuse the same `topic` as the round they are
challenging and leave `topic_history` untouched.

`rounds[].answer_keys` lists the `decisions` keys whose value was actually
written by that round (used by the next iteration to compute the challenge
scope without re-walking the answers list). On `kind="challenge"` rounds,
`answer_keys` lists ONLY keys overwritten by an `accept` / `<custom>` answer;
`keep` / `skip` answers are excluded (the value was re-affirmed, not
rewritten). On `kind="topic"` rounds, `skip` answers are excluded for the
same reason (no write happened). The field is the empty list when the user
skipped/kept every question, which suppresses option `C` on the next
post-round menu.

`rounds[].challenged_decisions` is set only on `kind="challenge"` rounds: a
snapshot of `{ key: value }` pairs from `state.decisions` *at the moment the
challenge round started*, scoped to the keys written by the immediately-preceding
answer-writing round (i.e. `state.rounds[-1].answer_keys` when the user chose
`C`). The snapshot is what the panel saw; later overwrites do not retro-edit it.

`next_topic_proposals` is the deduped/merged list emitted by the most recent
`kind="topic"` round. It survives subsequent `kind="challenge"` rounds so the
post-round menu can keep offering the same next-topic options without
re-dispatching the panel just to refresh proposals.

Decision overwrite semantics: when a challenge-round's answer accepts a
counter-proposal (or the user supplies a custom value), `state.decisions[key]`
is **overwritten** in place — prior values are not versioned at the
`decisions` level. The `rounds[]` array preserves the audit trail
(every value the panel produced and the user accepted lives in
`rounds[*].answers`).

Default location: kept in-memory by the orchestrator across rounds. Persist to
`{cf-constructor-path}/.cache/brainstorm/{session_id}/state.json` only when
the user picked explicit `save` mode and the current output destination allows
file writes. Chat-only/no-write sessions must use an in-chat checkpoint for
compaction recovery and must not write cache artifacts.
