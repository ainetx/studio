---
description: "Invoke when the user accepted the brainstorm offer and the expert panel must be selected / edited before the round loop begins."
name: phase-0.7-panel-selection
purpose: Brainstorm session setup — facilitator dispatch, proposed-panel rendering, panel-edit forms, seed-topic confirmation
loaded_by: workflows/generate/phase-0.7/index.md
version: 1.0
---

<!-- toc -->

- [Session setup (panel selection)](#session-setup-panel-selection)

<!-- /toc -->

### Session setup (panel selection)

```text
UNIT Phase07PanelSelection

PURPOSE:
  Dispatch facilitator, render proposed panel, manage panel edits, confirm seed topic.

DO:
  REQUIRE `{cf-studio-path}/.core/workflows/shared/inline-fallback-probe.md` loaded before any cf-* sub-agent dispatch
  DISPATCH cf-brainstorm-facilitator with JSON contract from
    {cf-studio-path}/.core/skills/studio/agents/cf-brainstorm-facilitator.md
  WITH orchestrator-supplied values:
    initial_topic = one-paragraph summary of user's original request
    kind = {KIND}
    rules_loaded = true ONLY when kit rules actually loaded for this brainstorm session,
                   else false
    kit_rules_path = resolved from rules.md or null
    template_path = resolved from rules.md or null
    example_path = resolved from rules.md or null
    NOTE: non-null kit_rules_path alone does NOT make rules_loaded=true;
          orchestrator must have opened and applied the rules
    project_ctx = 2-3-sentence summary covering: selected system (Phase 0.5),
                  KIND and its kit (STRICT + kit-mapped), most-relevant existing
                  artifact paths from Phase 0.5 parent/sibling discovery

  RECEIVE { proposed_panel: [...3..6 entries], seed_topic: {...} }

  EMIT exactly:
---
Proposed panel for `{KIND}: {name}`:

E1. Domain Architect      — focus: domain model, actor boundaries
                            why: <rationale>
E2. Security Reviewer     — focus: auth, data-handling
                            why: <rationale>
...

Seed topic for round 1:
`{seed_topic.text}`

Choose exactly one action:
1. `start` — use this panel and this seed topic, then begin round 1.
2. `seed: <topic>` — replace only the seed topic, then show this screen again.
3. `drop E2,E4` — remove listed panel members. Min 3 participants.
4. `swap E2: <new persona> (<focus>)` — replace one panel member.
5. `add: <persona> (<focus>)` — add one panel member. Max 6 participants.
W. `wrap` — stop setup and open the wrap/save menu.

One reply form per turn. Compound replies such as
`drop E2; add: X (focus)` are refused with a one-line clarifier.
After every edit, re-render the full panel plus seed topic.
---
  WAIT user.reply

MENU PanelEditLoop:
  TITLE: Panel setup loop (reply start to begin, or edit one thing)
  OPTIONS:
    start ->
      SET state.panel = confirmed_list
      SET state.topic_current = confirmed_seed_topic
      CONTINUE Phase07ExplorePanelContext
    accept ->
      Treat as backwards-compatible alias for start.
      SET state.panel = confirmed_list
      SET state.topic_current = confirmed_seed_topic
      CONTINUE Phase07ExplorePanelContext
    drop E{N},E{M} ->
      REMOVE listed experts from proposed panel
      REQUIRE min 3 remain
      EMIT re-rendered panel
      WAIT user.reply
    swap E{N}: <new persona> (<focus>) ->
      REPLACE E{N} with new persona
      EMIT re-rendered panel
      WAIT user.reply
    add: <persona> (<focus>) ->
      REQUIRE panel size < 6
      ADD new persona to panel
      EMIT re-rendered panel
      WAIT user.reply
    seed: <topic> ->
      SET confirmed_seed_topic = <topic>
      EMIT re-rendered panel and seed topic with the same action menu
      WAIT user.reply
    W | wrap | stop | done ->
      SET state.panel = confirmed_list
      SET state.topic_current = None
      CONTINUE wrap-handoff.md WITH reason="panel-setup-wrap"
  INVALID (compound reply):
    EMIT one-line clarifier asking for single edit form
    WAIT user.reply
    STOP_TURN

RULES:
  - MUST refuse compound replies with a one-line clarifier
  - MUST require min 3 panel members; MUST NOT allow more than 6
  - MUST re-render proposed panel and seed topic after every edit until user
    replies start
  - MUST treat accept as an alias for start but SHOULD NOT show accept in the
    primary user-facing action list
  - MUST always show wrap as a user-facing option in the panel setup menu
  - MUST set state.panel = confirmed_list and state.topic_current before
    entering round loop
```

```text
UNIT Phase07ExplorePanelContext

PURPOSE:
  After the panel is confirmed, determine what project/resource knowledge the
  experts need and materialize it before the first round dispatch.

DO:
  BUILD context_requirements from:
    state.topic_current
    confirmed_list personas, focus, rationale
    KIND, name, system, rules_mode
    known artifact paths from Phase 0.5 parent/sibling discovery

  DISPATCH cf-explorer with generator contract from
    {cf-studio-path}/.core/skills/studio/agents/cf-explorer.md
  WITH:
    task = state.topic_current.text
    intent = "brainstorm"
    panel = state.panel
    known_paths = artifact paths from Phase 0.5 parent/sibling discovery
    search_roots = resolved project/workspace roots in scope
    constraints.kind = {KIND}
    constraints.system = {system or null}

  RECEIVE explorer resource_context
  SET state.context_requirements = derived context_requirements
  SET state.resource_context = explorer.resource_context
  SET state.resource_context.exploration_status = explorer.exploration_status
  CONTINUE phase-0.7/round-loop.md

RULES:
  - MUST run before the first brainstorm round after panel confirmation
  - MUST NOT put docs/code/artifacts into SHARED_CONTEXT_PACK
  - MUST pass resource_context to every brainstorm panel/expert dispatch
  - IF cf-explorer returns exploration_status == "insufficient":
      still enter the round loop, but downstream panel/expert agents MUST ask
      for missing context instead of inventing project-specific proposals
```
