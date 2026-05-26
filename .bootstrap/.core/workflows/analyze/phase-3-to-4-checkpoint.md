---
name: analyze-phase-3-to-4-checkpoint
description: "Invoke when transitioning from Analyze Phase 3 to Phase 4 to evaluate the context-budget recovery checkpoint (continue-or-resume gate)."
purpose: Analyze Phase 3 → Phase 4 context-budget recovery checkpoint (continue-or-resume gate)
loaded_by: workflows/analyze.md
version: 1.0
---

```text
UNIT AnalyzePhase3To4Checkpoint

PURPOSE:
  Evaluate context budget after semantic review; emit a checkpoint and offer
  continue-in-chat or fresh-chat-resume when budget is low or PARTIAL=true.

WHEN:
  Before entering Phase 4 Output

DO:
  Estimate remaining context budget.
  IF budget >= 30% of original capacity AND PARTIAL == false:
    CONTINUE workflows/analyze/phase-4-output/index.md (no stop)
  ELSE:
    Emit checkpoint (see required fields below)
    EMIT_MENU Phase3To4Menu
    WAIT user.reply
    STOP_TURN

MENU Phase3To4Menu:
  TITLE: |
    Context budget is low after semantic review. Continue to Phase 4 (Output +
    remediation prompts) in this chat, or start a fresh chat with the checkpoint above?

    Suggested: 1 when enough context remains for Phase 4; 2 when context pressure is high.
  OPTIONS:
    1 -> CONTINUE workflows/analyze/phase-4-output/index.md
    2 -> Emit a fresh-chat resume prompt as the final section (must include
         target_paths, deterministic gate summary, methodology dispatch status,
         findings JSON, semantic report inventory, and resume fingerprints)
         STOP_TURN
  INVALID:
    EMIT "Reply `1` or `2`."
    WAIT user.reply
    STOP_TURN

RULES:
  - MUST emit checkpoint when budget < 30% of original capacity OR PARTIAL=true
  - MUST include target_paths / analyzed_paths grouped by methodology
    (artifact, code, code_bug, prompt, prompt_bug, consistency)
    and including diff/change-review scope when present
  - MUST include deterministic gate status, validator output summary, and gate result
    (PASS / FAIL / SKIPPED / unavailable)
  - MUST include methodology dispatch status per planned or legacy reviewer:
    completed | failed | blocked_by_failed_dep | skipped | not_applicable
    with task/group ids when a reviewer execution plan was used
  - MUST include complete findings JSON accumulated so far (namespaced and renumbered
    per phase-3-semantic.md)
  - MUST include semantic report block inventory: one entry per
    "Validation Report — <Section>" block with source reviewer, target paths, and status
  - MUST include prompt/code/artifact review state: loaded methodology files, kit rules path,
    checklist/template/example paths when applicable, traceability mode,
    cross-reference paths, failed/skipped reviewer reason
  - MUST include deterministic resume gate: file fingerprints or mtimes for every
    target_path, cross_ref_path, design_artifact_path, loaded methodology file,
    and rules/checklist file that affected the review
  - MUST_NOT infer a default when the user replies anything other than 1 or 2
  - MUST re-read target set and all referenced rules/methodology files on fresh-chat resume
  - MUST verify deterministic resume gate against checkpoint including methodology-file fingerprints on resume
  - MUST reload findings JSON and semantic report inventory on resume
  - MUST skip to Phase 4 only when gate matches on resume
  - MUST_NOT reuse the checkpoint silently when any fingerprint changed on resume;
    rerun the affected deterministic/semantic review groups or ask the user

NOTES:
  The checkpoint fields above are target-set centric (not single-artifact centric)
  to support multi-path and multi-methodology analyze runs.
  Fresh-chat resume prompt MUST start with "Invoke skill cf" and embed the checkpoint.
```

### Phase 3 → Phase 4 Checkpoint (Context Budget Recovery)

Before proceeding to Phase 4 Output, estimate remaining context budget. If
budget is below ~30% of original capacity, or if Phase 3 ended with
`PARTIAL=true`, emit a checkpoint that is target-set centric rather than
single-artifact centric.

The checkpoint MUST include:

- `target_paths` / `analyzed_paths` exactly as used by Phase 3, grouped by
  methodology (`artifact`, `code`, `code_bug`, `prompt`, `prompt_bug`,
  `consistency`) and including diff/change-review scope when present.
- Deterministic gate status, validator output summary, and whether the gate
  was `PASS`, `FAIL`, `SKIPPED`, or unavailable.
- Methodology dispatch status for every planned or legacy reviewer:
  `completed`, `failed`, `blocked_by_failed_dep`, `skipped`, or `not_applicable`,
  with task/group ids when a reviewer execution plan was used.
- The complete findings JSON accumulated so far, already namespaced and
  renumbered per `workflows/analyze/phase-3-semantic.md`.
- Semantic report block inventory: one entry per `Validation Report — <Section>`
  block, with source reviewer, target paths, and status.
- Prompt/code/artifact review state: loaded methodology files, kit rules path
  or `null`, checklist/template/example paths when applicable, traceability
  mode, cross-reference paths, and any failed/skipped reviewer reason.
- Deterministic resume gate: file fingerprints or mtimes for every
  `target_path`, `cross_ref_path`, `design_artifact_path`, loaded methodology
  file, and rules/checklist file that affected the review.

After emitting the checkpoint, ask:

```text
Context budget is low after semantic review. Continue to Phase 4 (Output + remediation prompts) in this chat, or start a fresh chat with the checkpoint above?

1. Continue in this chat — proceed to Phase 4 with the checkpoint state already loaded
2. Emit a fresh-chat resume prompt — produce a self-contained prompt that starts with `Invoke skill cf` and embeds the checkpoint

Suggested: 1 when enough context remains for Phase 4; 2 when context pressure is high.

Reply `1` or `2`.
```

Next-turn parser:

- `1` → continue in this chat and enter `workflows/analyze/phase-4-output/index.md`.
- `2` → emit a fresh-chat resume prompt as the final section; the prompt must include `target_paths`, deterministic gate summary, methodology dispatch status, findings JSON, semantic report inventory, and resume fingerprints.
- Anything else re-prompts with the same two choices; do not infer a default.

On resume in a fresh chat, re-read the target set and all referenced rules /
methodology files, verify the deterministic resume gate against the checkpoint
including methodology-file fingerprints, reload the findings JSON and semantic
report inventory, and skip to Phase 4 only when the gate matches. If any
fingerprint changed, do not reuse the checkpoint silently; rerun the affected
deterministic/semantic review groups or ask the user which changed targets to
re-analyze.

If budget is sufficient (≥30% remaining) and Phase 3 is not partial, proceed
directly to Phase 4 without stopping.
