---
cf: true
type: workflow-fragment
parent: workflows/pdsl.md
description: Invoke when cf-pdsl intent is transforming existing prompt files into PDSL.
version: 0.1
---

# PDSL Transform Mode

Open, load, and follow this file only when `PDSL_MODE == transform`
or the user intent clearly asks to convert, rewrite, or migrate existing prompt
files into PDSL.

```text
UNIT TransformPromptMode

PURPOSE:
  Convert one or more existing prose prompt files into PDSL.

STATE:
  PDSL_MODE: new | transform | review
    scope: inherited_from_parent

WHEN:
  PDSL_MODE == transform

REQUIRE:
  target_paths is non-empty

DO:
  EMIT write_summary(target_paths, source_paths)
  EMIT_MENU TransformWriteConfirmMenu
  WAIT user.reply
  STOP_TURN

MENU TransformWriteConfirmMenu:
  TITLE: Confirm write to target path(s) listed above
  OPTIONS:
    1 proceed -> SET CF_PHASE_GATE = released_for_dispatch
                 DISPATCH cf-pdsl-transformer WITH TransformPromptInputs
                 RETURN manifest
    2 cancel  -> EMIT "Write cancelled. No files written."
                 STOP_TURN
  INVALID:
    EMIT "Reply with 1 (proceed) or 2 (cancel)."
    WAIT user.reply
    STOP_TURN

RULES:
  - MUST set CF_PHASE_GATE = released_for_dispatch immediately before DISPATCH
  - MUST reset CF_PHASE_GATE to armed on dispatch return or error
  SEE_ALSO: {cf-studio-path}/.core/skills/studio/SKILL.md §Phase-Skip Gate

ON_ERROR:
  missing_target_paths ->
    EMIT "Provide one or more prompt/workflow/skill files to transform."
    WAIT user.reply
    CONTINUE TransformPromptMode

  dispatch_failed ->
    SET CF_PHASE_GATE = armed
    EMIT failure_summary
    STOP_TURN
```

Dispatch payload:

```json
{
  "target_paths": ["<prompt/workflow/skill path>", "..."],
  "source_paths": ["<optional cross-reference paths>"],
  "transform_policy": "in_place",
  "pdsl_spec_path": "{cf-studio-path}/.core/architecture/specs/PDSL.md",
  "rules_mode": "STRICT|RELAXED"
}
```

Transform mode MUST preserve behavior before compacting wording. If a prompt
contains ambiguous behavior that cannot be preserved safely, the transformer
MUST either keep the original prose in `NOTES` with an `OPEN_QUESTIONS` block
or return `TRANSFORM_BLOCKED` with the unresolved questions.

ALWAYS follow the authoritative preservation definition in
`.bootstrap/.core/architecture/specs/PDSL.md` §Transform Equivalence when
assessing whether a transformed file is equivalent to its prose source.

```text
UNIT EquivalenceSelfCheck

PURPOSE:
  Verify that the PDSL output preserves every executable rule from the prose source.

WHEN:
  PDSL_MODE == transform
  AND CF_PHASE_GATE == armed
  AND dispatch returned TransformManifest

DO:
  1. For each written target path:
       a. Extract the set of executable rules from the prose source:
            collect all MUST / MUST_NOT / FORBID / REQUIRE / STOP_TURN sentences.
       b. Extract the equivalent set from the PDSL output:
            collect all RULES entries, INVARIANTS entries, FORBID statements.
       c. Compare the two sets:
            - prose rules with no PDSL counterpart → `missing_in_pdsl`
            - PDSL rules with no prose source → `invented_in_pdsl`
       d. Emit an `EQUIVALENCE_REPORT` block in the transformer manifest for this path.
  2. IF any path has non-empty `missing_in_pdsl` or `invented_in_pdsl`:
       SET TRANSFORM_INCOMPLETE = true
       EMIT EQUIVALENCE_REPORT to orchestrator before claiming PASS
  3. RETURN updated manifest with `equivalence_report` and `transform_incomplete` fields.

RULES:
  - MUST surface TRANSFORM_INCOMPLETE = true to the orchestrator when any discrepancy exists
  - MUST_NOT mark a transform as PASS when `missing_in_pdsl` is non-empty
  - MUST_NOT treat `invented_in_pdsl` entries as errors — flag them for author review only
```

Completion: return the `cf-pdsl-transformer` manifest or a
`TRANSFORM_BLOCKED` payload.
