---
cf: true
type: workflow-fragment
name: explore-brainstorm-gate
description: "Shared applicability gate for deciding when cf-explore and cf-brainstorm are required or should be offered before a cf workflow continues."
version: 0.1
---

# Explore / Brainstorm Gate

```text
UNIT ExploreBrainstormGate

PURPOSE:
  Decide whether the active workflow needs resource discovery, design
  exploration, or both before it continues.

STATE:
  EXPLORE_DECISION: unset | required | suggested | skipped | complete
  BRAINSTORM_DECISION: unset | required | suggested | skipped | complete
  RESOURCE_CONTEXT: null | cf-explorer result JSON
  BRAINSTORM_CONTEXT: null | brainstorm handoff JSON

ORDER:
  1. Resolve required/suggested explore.
  2. Resolve required/suggested brainstorm.
  3. If both apply, run explore before brainstorm unless RESOURCE_CONTEXT is
     already complete for the current task.

RESOURCE BOUNDARY:
  - cf-explore discovers non-prompt project resources only: code, docs,
    artifacts, architecture specs as task subject, diffs, configs, examples,
    and generated runtime outputs.
  - cf-explore MUST NOT add resource contents to SHARED_CONTEXT_PACK.
  - Prompt assets remain controller-owned instruction context and are handled
    only through SHARED_CONTEXT_PACK.

REQUIRE_EXPLORE WHEN:
  - Active workflow is cf-brainstorm and panel personas have been selected.
  - Active workflow is cf-auto-config.
  - Active workflow is cf-workspace setup or workspace config generation.
  - Active workflow is cf-plan for an existing project, brownfield change,
    architecture-affecting work, multi-file implementation, or unclear target
    surface.
  - Active workflow is cf-generate and task touches existing code/docs,
    architecture, prompts, workflows, skills, requirements, multi-file behavior,
    integrations, or an unspecified target path.
  - Active workflow is cf-analyze or cf-explain and the user did not provide
    explicit target paths, asks about project/architecture behavior, asks "where",
    "impact", "consistency", "what uses", or requests cross-file reasoning.

SUGGEST_EXPLORE WHEN:
  - Active workflow is cf-pdsl transform/review and related prompt dependencies
    are not explicit.
  - Active workflow is cf-generate for a small isolated edit but neighboring
    context may affect correctness.
  - Active workflow is cf-analyze with explicit targets but likely cross-refs
    or architectural context would improve findings.

SKIP_EXPLORE WHEN:
  - User supplied exact target files and all required surrounding context.
  - Active workflow is cf-map generating a graph; map performs its own scan.
  - Active workflow is a pure prompt/proxy route with no project-resource need.

REQUIRE_BRAINSTORM WHEN:
  - User explicitly asks to brainstorm, ideate, explore options, decide,
    compare approaches, design requirements, or map tradeoffs.
  - Active workflow is cf-generate and implementation depends on unresolved
    product, architecture, UX, safety, compatibility, or workflow-policy
    decisions.
  - Active workflow is cf-plan and phase decomposition depends on unresolved
    strategy, milestones, ownership boundaries, or acceptance semantics.

SUGGEST_BRAINSTORM WHEN:
  - Active workflow is cf-generate and the change is broad but a safe default
    exists.
  - Active workflow is cf-plan and there are multiple valid decomposition
    strategies.
  - Active workflow is cf-auto-config, cf-workspace, or cf-pdsl new/transform
    and user-facing defaults, precedence, or policy choices are ambiguous.
  - Active workflow is cf-analyze and findings require choosing a remediation
    strategy rather than simply reporting defects.

SKIP_BRAINSTORM WHEN:
  - User asks for direct execution, review, explanation, mapping, or deterministic
    validation and no design choice is unresolved.
  - User passes --no-brainstorm or active rules explicitly disable brainstorm.
  - The task is a narrow mechanical edit with explicit target and outcome.
```

```text
UNIT ExploreBrainstormAction

PURPOSE:
  Execute the decision without hiding workflow control from the user.

DO:
  IF EXPLORE_DECISION == required:
    LOAD {cf-studio-path}/.core/workflows/explore.md
    run with intent = active workflow name
    SET RESOURCE_CONTEXT = explorer result JSON
    SET EXPLORE_DECISION = complete

  IF EXPLORE_DECISION == suggested:
    EMIT_MENU ExploreOfferMenu
    WAIT user.reply
    STOP_TURN

  IF BRAINSTORM_DECISION == required:
    LOAD {cf-studio-path}/.core/workflows/brainstorm.md
    seed brainstorm with active task and RESOURCE_CONTEXT when present
    SET BRAINSTORM_DECISION = complete after wrap handoff

  IF BRAINSTORM_DECISION == suggested:
    EMIT_MENU BrainstormOfferMenu
    WAIT user.reply
    STOP_TURN

MENU ExploreOfferMenu:
  TITLE: Additional project context may improve this workflow. What should I do?
  OPTIONS:
    1 run-explore -> LOAD {cf-studio-path}/.core/workflows/explore.md
                     run with intent = active workflow name
    2 continue -> SET EXPLORE_DECISION = skipped
                  continue active workflow
    3 narrow-scope -> ask one scoped question for paths or limits
                      WAIT user.reply
                      STOP_TURN
  INVALID:
    EMIT "Reply with 1, 2, or 3."
    WAIT user.reply
    STOP_TURN

MENU BrainstormOfferMenu:
  TITLE: This task has design choices. What should I do before continuing?
  OPTIONS:
    1 run-brainstorm -> LOAD {cf-studio-path}/.core/workflows/brainstorm.md
                        seed with active task and RESOURCE_CONTEXT when present
    2 continue -> SET BRAINSTORM_DECISION = skipped
                  continue active workflow
    3 ask-scope-question -> ask one scoped decision question
                            WAIT user.reply
                            STOP_TURN
  INVALID:
    EMIT "Reply with 1, 2, or 3."
    WAIT user.reply
    STOP_TURN
```

```text
UNIT ExploreBrainstormWorkflowMatrix

PURPOSE:
  Provide compact workflow-specific defaults.

MATRIX:
  cf-brainstorm:
    explore: required after panel selection
    brainstorm: current workflow
  cf-explore:
    explore: current workflow
    brainstorm: offer in terminal menu only
  cf-generate:
    explore: required for brownfield/broad/unclear; suggested for narrow edits
    brainstorm: required for unresolved decisions; suggested for broad work
  cf-plan:
    explore: required for brownfield/architecture/multi-file/unclear
    brainstorm: required for unresolved strategy; suggested for multiple valid decompositions
  cf-analyze:
    explore: required for missing targets or cross-file/project questions; suggested for explicit targets with likely cross-refs
    brainstorm: never before findings; offer only as remediation strategy next-step
  cf-explain:
    explore: required when target is unspecified; otherwise inherited from analyze
    brainstorm: skip
  cf-auto-config:
    explore: required
    brainstorm: suggested when defaults/policies are ambiguous
  cf-workspace:
    explore: required for setup/config generation
    brainstorm: suggested for precedence, federation policy, or rollout choices
  cf-pdsl:
    explore: suggested for transform/review with implicit dependencies
    brainstorm: suggested for new prompt architecture or policy changes
  cf-map:
    explore: skip
    brainstorm: skip
```
