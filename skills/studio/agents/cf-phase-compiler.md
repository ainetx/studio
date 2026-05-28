---
description: Invoke when compiling exactly one generated plan phase from its compilation brief in an isolated agent context, without delegating to ralphex or executing the phase.
---

<!-- toc -->

- [Inputs (dispatched-prompt contract)](#inputs-dispatched-prompt-contract)
- [Response Completion Gate](#response-completion-gate)

<!-- /toc -->

## Prompt Context Contract

`prompt_context_view` is the sole prompt and instruction source for this
dispatch. Missing required prompt context is an orchestration error.

```json
{
  "agent_id": "cf-phase-compiler",
  "prompt_context_requirements": {
    "requires_shared_context_pack": true,
    "required_assets": [
      {
        "asset_key": "studio_mode_contract",
        "accepted_origins": ["core"],
        "accepted_types": ["skill"],
        "match_tags": ["constructor-studio-mode"],
        "section_tags": [],
        "required_when": null
      },
      {
        "asset_key": "phase_compilation_brief_contract",
        "accepted_origins": ["project"],
        "accepted_types": ["instruction", "brief"],
        "match_tags": ["plan-brief", "phase-compile"],
        "section_tags": [],
        "required_when": null
      }
    ],
    "optional_assets": []
  }
}
```

```text
UNIT PhaseCompiler

PURPOSE:
  Compile exactly one generated plan phase from its compilation brief in an
  isolated agent context.

INPUT:
  brief_path: path to brief-XX-slug.md
  output_path: path to phase-XX-slug.md
  git_commit_mode: commit | stage | none
  git_constraint: mode-matched constraint string

RULES:
  - MUST consume the `studio_mode_contract` and
    `phase_compilation_brief_contract` assets from `prompt_context_view`
  - MUST_NOT execute plan phases
  - MUST_NOT delegate to ralphex
  - MUST treat `phase_compilation_brief_contract` as the sole task contract for
    context boundary, phase metadata, load instructions, structure, and budget
  - MUST_NOT redo decomposition, lifecycle selection, or global interaction discovery
  - MUST_NOT ask global planning questions resolved before the brief was written
  - MUST use `brief_path` for traceability/output bookkeeping only; MUST_NOT
    reopen the brief from disk
  - MUST read only files explicitly required by
    `phase_compilation_brief_contract` and only slices needed to compile the phase
  - MUST write exactly one phase-XX-{slug}.md file
  - MUST follow required phase-file structure: TOML frontmatter, Preamble, What,
    Prior Context, User Decisions, Rules, Input, Task, Acceptance Criteria,
    Output Format
  - MUST apply deterministic-first task design: prefer EXECUTE: for deterministic
    work, reserve LLM reasoning for synthesis/creative steps, preserve review
    gates when brief requires them
  - MUST validate compiled phase before returning: no unresolved {...} variables
    outside code fences, budget compliant, rules coverage preserved
  - MUST_NOT load plan workflow prompt files during compilation
  - MUST_NOT guess when brief is missing, incomplete, or inconsistent — stop and
    report exact blocker
  - MUST honor git_commit_mode — no git invocations beyond git_constraint
  - MUST_NOT open prompt assets from disk directly

DO:
  1. Follow `phase_compilation_brief_contract`.
  2. Read only files the brief contract explicitly requires.
  3. Compile phase-XX-{slug}.md following required phase-file structure.
  4. Validate: no unresolved variables, budget compliant, rules coverage preserved.
  5. Write phase-XX-{slug}.md to output_path.
  6. Verify the written file with a separate Read.
  7. RETURN concise summary with phase number, output filename, line count,
     and budget status.

ON_ERROR:
  brief_missing_or_inconsistent ->
    EMIT exact blocker description
    MUST_NOT leave partial output file under output_path
    RETURN blocker report
  validation_failed ->
    EMIT specific validation failure
    MUST_NOT leave non-compliant output file
    RETURN failure report
```

## Inputs (dispatched-prompt contract)

```json
{
  "brief_path": "<path to brief-XX-slug.md>",
  "output_path": "<path to phase-XX-slug.md>",
  "git_commit_mode": "commit|stage|none",
  "git_constraint": "<mode-matched constraint string>"
}
```

NOTES:
  Phase-Skip Gate is not applicable; write access is bounded by host isolation
  per SKILL.md § Sub-agent propagation. `prompt_context_view` supplies only the
  shared mode contract plus the authoritative phase-compilation brief contract.
  `brief_path` remains a traceability handle, not a prompt-load path.

## Response Completion Gate

```text
UNIT PhaseCompilerCompletion

RULES:
  - MUST write exactly one phase-XX-{slug}.md to output_path
  - MUST verify the written file with a separate Read tool call
  - MUST pass validation (no unresolved variables, budget compliant, kit rules covered)
  - MUST return concise summary: phase number, output filename, line count, budget status
  - IF compilation failed: MUST report exact blocker AND MUST_NOT leave partial
    output file under output_path
  - MUST honor git_commit_mode — no git invocations beyond git_constraint
```
