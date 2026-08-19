---
cf: true
type: workflow
name: cf-deep-review-config
description: "Configure project-specific review rules for cf-deep-review via batch-based selection from discovery, plan mining, post-mortem, or manual authoring."
version: 0.1
purpose: Help the user build and write a deterministic per-project deep-review config.toml with the same batch UX as cf-deep-review check selection.
---

# cf-deep-review-config

`cf-deep-review-config` does not execute reviews. It only creates or updates the project review configuration consumed by `cf-deep-review`.

```pdsl
UNIT DeepReviewConfigBootstrap
PURPOSE: Load shared bootstrap and route to target resolution.
DO:
  LOAD {cf-studio-path}/.core/skills/studio/modules/runtime/workflow-bootstrap.md
  RUN WorkflowBootstrapCoreSession
  RUN WorkflowBootstrapSimpleModeGate
  RUN WorkflowBootstrapCommandWorkflowResolution
  SET ORIGINAL_INTENT = the triggering request verbatim
  SET CURRENT_WORKFLOW = cf-deep-review-config
  CONTINUE DeepReviewConfigPrecheck
RULES:
  NEVER modify the review target or execute review checks during configuration
```

```pdsl
UNIT DeepReviewConfigPrecheck
PURPOSE: Resolve target project and canonical config path.
STATE:
  SET TARGET_PROJECT_ID: string | unset
  SET TARGET_PROJECT_CACHE_KEY: string | unset
  SET TARGET_PROJECT_ROOT: absolute path | remote-only | unset
  SET REVIEW_CONFIG_PATH: absolute path | unset
DO:
  RUN resolve TARGET_PROJECT_ID and TARGET_PROJECT_ROOT from explicit input or prompt
  RUN set TARGET_PROJECT_CACHE_KEY per deep-review-project-config.md Project cache key algorithm from TARGET_PROJECT_ID and TARGET_PROJECT_ROOT
  SET REVIEW_CONFIG_PATH = ~/.cf-studio/.cache/deep-review/projects/{TARGET_PROJECT_CACHE_KEY}/config.toml
  RUN ensure parent directory exists
  LOAD {cf-studio-path}/.core/skills/studio/modules/deep-review-project-config.md
  CONTINUE DeepReviewConfigMigrationCheck
RULES:
  ALWAYS treat deep-review-project-config.md as the authoritative schema reference
  NEVER fall back to a different config path
```

```pdsl
UNIT DeepReviewConfigMigrationCheck
PURPOSE: Detect legacy configs and offer migration before editing or replacing.
STATE:
  SET LEGACY_CONFIG_PATH: absolute path | unset
  SET LEGACY_CONFIG_DETECTED: boolean = false
DO:
  RUN compute LEGACY_CONFIG_PATH from TARGET_PROJECT_ID:
    - GitHub target github.com/<owner>/<repo> -> legacy candidate ~/.cf-studio/.cache/deep-review/projects/<owner>__<repo>/config.toml
    - local or other targets -> no standard legacy candidate
  RUN check if REVIEW_CONFIG_PATH is absent and LEGACY_CONFIG_PATH exists
  WHEN LEGACY_CONFIG_DETECTED == true:
    EMIT "Canonical config missing at {REVIEW_CONFIG_PATH}; legacy config found at {LEGACY_CONFIG_PATH}."
    EMIT_MENU DeepReviewConfigMigrationMenu
    WAIT user.reply
    STOP_TURN
  WHEN LEGACY_CONFIG_DETECTED == false:
    CONTINUE DeepReviewConfigMenu
MENU DeepReviewConfigMigrationMenu:
  TITLE: "Legacy project review config found."
  OPTIONS:
    1 migrate legacy config to canonical path -> RUN atomically move LEGACY_CONFIG_PATH to REVIEW_CONFIG_PATH; CONTINUE DeepReviewConfigMenu
    2 start from scratch -> CONTINUE DeepReviewConfigMenu
    3 cancel -> RETURN status = cancelled
  INVALID:
    EMIT "Reply with 1 to migrate, 2 to ignore, or 3 to cancel."
    EMIT_MENU DeepReviewConfigMigrationMenu
    WAIT user.reply
    STOP_TURN
RULES:
  NEVER silently use a legacy config path
  NEVER overwrite an existing canonical config
```

```pdsl
UNIT DeepReviewConfigMenu
PURPOSE: Choose rule source and mode.
DO:
  RUN read REVIEW_CONFIG_PATH when it exists; count existing rules; emit config status
  EMIT_MENU DeepReviewConfigActions
  WAIT user.reply
  STOP_TURN
MENU DeepReviewConfigActions:
  TITLE: "Project review config — choose a starting point."
  OPTIONS:
    1 build rules manually -> SET RULE_SOURCE = manual; CONTINUE DeepReviewConfigRuleBuilderInit
    2 discover rules from project files -> SET RULE_SOURCE = discover; CONTINUE DeepReviewConfigRuleBuilderInit
    3 mine patterns from existing review plans -> SET RULE_SOURCE = plans; CONTINUE DeepReviewConfigRuleBuilderInit
    4 post-mortem: propose rules from a finished review -> SET RULE_SOURCE = postmortem; CONTINUE DeepReviewConfigRuleBuilderInit
    5 show current config -> CONTINUE DeepReviewConfigShow
    6 cancel -> RETURN status = cancelled
  INVALID:
    EMIT "Reply with 1, 2, 3, 4, 5, or 6."
    EMIT_MENU DeepReviewConfigActions
    WAIT user.reply
    STOP_TURN
```

```pdsl
UNIT DeepReviewConfigRuleBuilderInit
PURPOSE: Initialize the rule builder and load the active source module.
STATE:
  SET RULE_BUILDER_STATE: object | unset
  SET RULE_SOURCE: manual | discover | plans | postmortem
DO:
  LOAD {cf-studio-path}/.core/skills/studio/modules/deep-review-config-rule-builder.md
  LOAD source module based on RULE_SOURCE:
    discover -> {cf-studio-path}/.core/skills/studio/modules/deep-review-config-discovery.md
    plans -> {cf-studio-path}/.core/skills/studio/modules/deep-review-config-plan-mining.md
    postmortem -> {cf-studio-path}/.core/skills/studio/modules/deep-review-config-postmortem.md
    manual -> no extra load
  RUN initialize RULE_BUILDER_STATE:
    batch_number = 1,
    current_batch = [],
    selected_rules = existing config rules when editing,
    custom_rules = [],
    proposed_fingerprints = existing rule fingerprints,
    rejected_fingerprints = [],
    covered_categories = categories from existing rules,
    source = RULE_SOURCE
  RUN generate first batch when RULE_SOURCE != manual
  SET BUILDER_VIEW = batch
  CONTINUE DeepReviewConfigRuleBuilderTurn
RULES:
  ALWAYS preserve existing config rules as selected rules when editing
  NEVER delete existing rules unless the user explicitly removes them
```

```pdsl
UNIT DeepReviewConfigRuleBuilderTurn
PURPOSE: Render the current builder view and collect one command.
DO:
  RUN render the current batch with numbers, evidence, and selection summary WHEN BUILDER_VIEW == batch
  RUN render the more-checks view with selected count and named commands WHEN BUILDER_VIEW == more
  WAIT user.reply
  STOP_TURN
RULES:
  ALWAYS resume the next turn at DeepReviewConfigRuleCommandApply with the exact reply
  NEVER auto-select candidates or claim unsupplied guidance was checked
```

```pdsl
UNIT DeepReviewConfigRuleCommandApply
PURPOSE: Apply one builder command using the rule-builder contract.
DO:
  RUN parse and apply user.reply per deep-review-config-rule-builder.md, preserving valid partial selections and compact state; return BUILDER_ACTION
  SET RULE_BUILDER_STATE.selected_rules from the applied action
  RETURN status = cancelled WHEN BUILDER_ACTION == cancel
  CONTINUE DeepReviewConfigWrite WHEN BUILDER_ACTION == finalize AND RULE_BUILDER_STATE.selected_rules is not empty
  CONTINUE DeepReviewConfigShow WHEN BUILDER_ACTION == finalize-unchanged
  CONTINUE DeepReviewConfigRuleBuilderTurn with BUILDER_VIEW = batch WHEN BUILDER_ACTION == generate-batch or batch-reset
  CONTINUE DeepReviewConfigRuleBuilderTurn with BUILDER_VIEW = more WHEN BUILDER_ACTION == selected, custom-added, shown, removed, or correction
  CONTINUE DeepReviewConfigRuleBuilderTurn with BUILDER_VIEW = batch WHEN BUILDER_ACTION == needs-rules
RULES:
  NEVER interpret arbitrary prose as approval or a selected rule
  ALWAYS validate custom-added rules against the schema before adding them
```

```pdsl
UNIT DeepReviewConfigGenerateBatch
PURPOSE: Produce the next batch of rule candidates from the active source.
DO:
  RUN generate up to 10 new candidates based on RULE_SOURCE:
    discover -> RUN DeepReviewConfigDiscovery and take next candidates
    plans -> RUN DeepReviewConfigPlanMining and take next candidates
    postmortem -> RUN DeepReviewConfigPostmortem and take next candidates
    manual -> current batch remains empty
  DEDUPLICATE against RULE_BUILDER_STATE.proposed/rejected/selected/custom fingerprints
  SET RULE_BUILDER_STATE.current_batch = new candidates
  INCREMENT RULE_BUILDER_STATE.batch_number when new batch is non-empty
  RETURN empty WHEN no new candidates remain
RULES:
  ALWAYS stop generating when no new candidates remain; do not repeat rejected candidates
  NEVER mix sources within one batch
```

```pdsl
UNIT DeepReviewConfigShow
PURPOSE: Display the current config without writing.
DO:
  RUN read REVIEW_CONFIG_PATH when it exists; otherwise emit "No config at {REVIEW_CONFIG_PATH}"
  EMIT path, version, rule count, and a compact rule table
  CONTINUE DeepReviewConfigMenu
```

```pdsl
UNIT DeepReviewConfigWrite
PURPOSE: Validate and write the config.toml atomically.
DO:
  RUN schema validation per deep-review-project-config.md:
    - version == 1
    - every rule has unique id, non-empty prompt, non-empty category
    - condition is either "always" or {source, regexp} with known source and valid regex
    - required = true for every rule
  RUN compute hash of the validated config content
  WRITE REVIEW_CONFIG_PATH atomically
  EMIT result: path, rule count, hash
  RETURN status = complete with config path and hash
RULES:
  NEVER write without at least one selected rule when the config was previously absent
  ALWAYS validate before writing
  ALWAYS preserve the existing config path
```
