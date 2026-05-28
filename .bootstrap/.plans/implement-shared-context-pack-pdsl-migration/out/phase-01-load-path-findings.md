# Phase 01 Load-Path Findings

## Summary

- `workflows/pdsl.md` still contains root-relative prompt loads that bypass the `{cf-studio-path}`-prefixed contract Phase 2 must normalize.
- Search across `skills/studio/agents.toml`, `skills/studio/agents/`, `workflows/`, and `.bootstrap/` found zero occurrences of `prompt_context_requirements` and zero occurrences of `prompt_context_view`.
- The bootstrap runtime skill chain is broader than the original Phase 1 inventory captured: `protocol.md` loads `.gen/SKILL.md` and `config/SKILL.md`, `.gen/SKILL.md` routes into the kit skill, and the kit skill routes active requests into three SDLC workflow prompt files.
- Shared-context-pack violations are concentrated in prompt-consuming sub-agents that still instruct themselves to load `SKILL.md`, `workflows/*.md`, `requirements/*.md`, or prompt-facing specs directly from disk.

## Findings

| Path | Evidence | Finding | Classification |
| --- | --- | --- | --- |
| `workflows/pdsl.md:25-28` | Loads `{cf-studio-path}/.core/skills/studio/SKILL.md`, then root-relative `skills/studio/protocol.md` and `workflows/shared/stop-token-policy.md`. | Mixed path semantics; the latter two loads are missing `{cf-studio-path}` / `.bootstrap`-prefixed access. | Missing prefix in orchestrator workflow |
| `workflows/pdsl.md:59-66` | Menu options load `workflows/pdsl/{new,transform,review}.md` via root-relative paths. | Mode-file loads still use root-relative paths instead of a `{cf-studio-path}`-prefixed prompt reference. | Missing prefix in orchestrator workflow |
| `skills/studio/protocol.md:47-56` | Protocol Guard opens `.gen/AGENTS.md`, `config/AGENTS.md`, `.gen/SKILL.md`, `config/SKILL.md`, and `.core/requirements/language-complexity.md`. | Central bootstrap still directly loads prompt assets from disk; this is the most likely shared-context-pack builder/orchestrator exception surface. | Orchestrator-only exception candidate |
| `.bootstrap/.gen/SKILL.md:1-5` | Generated runtime skill surface routes directly to `{cf-studio-path}/config/kits/sdlc/SKILL.md`. | Active runtime skill handoff was omitted from the earlier inventory; later phases must treat it as a live bootstrap prompt surface and not just generated support text. | Runtime bootstrap prompt surface |
| `.bootstrap/config/SKILL.md:1-4` | Declares project-specific skill instructions loaded alongside `.gen/SKILL.md`. | Even with minimal current content, this file is part of the runtime bootstrap load path because Protocol Guard loads `config/SKILL.md` directly. | Runtime bootstrap prompt surface |
| `.bootstrap/config/kits/sdlc/SKILL.md:73-133` | Routes PR review/status requests to `{workflow_pr_review}` / `{workflow_pr_status}` and OpenSpec migration requests to `{workflow_migrate_openspec}`. | The kit skill is an active runtime router, not just reference prose; it is a prompt-bearing surface and the parent of three additional workflow prompt files. | Runtime bootstrap prompt surface |
| `.bootstrap/config/kits/sdlc/workflows/pr-review.md:12-165` | Runtime workflow defines review routing, fetch requirements, prompt/checklist loading, and `.prs/{ID}/review.md` output behavior. | Missing from the original inventory even though it is an active prompt contract reachable via the kit skill router. | Runtime bootstrap workflow surface |
| `.bootstrap/config/kits/sdlc/workflows/pr-status.md:12-149` | Runtime workflow defines status routing, auto-fetch behavior, severity audit rules, and `.prs/{ID}/status.md` output behavior. | Active runtime workflow surface omitted from the original inventory; later phases must account for its prompt loading and output contract. | Runtime bootstrap workflow surface |
| `.bootstrap/config/kits/sdlc/workflows/migrate-openspec.md:91-260` | Runtime workflow governs OpenSpec migration phases, review gates, configuration discovery, and validation rules. | Active runtime workflow surface omitted from the original inventory; it expands the runtime prompt corpus beyond `.core/workflows/`. | Runtime bootstrap workflow surface |
| `workflows/plan.md:33-49` | Plan bootstrap requires `SKILL.md`, `protocol.md`, `stop-token-policy.md`, and multiple requirements files directly. | Direct prompt loading is expected today, but the workflow is a top-level orchestrator and should become the shared-context-pack builder for plan execution. | Orchestrator-only exception candidate |
| `workflows/workspace.md:27-31` | Workspace bootstrap requires `config/AGENTS.md`, `.gen/AGENTS.md`, and `SKILL.md` directly. | Direct prompt loading from runtime prompt surfaces remains in the workspace orchestrator. | Orchestrator-only exception candidate |
| `skills/studio/agents/cf-pr-review.md:25-39` | Loads `SKILL.md`, inline-fallback probe, then `workflows/analyze.md`. | Prompt-consuming sub-agent directly loads prompt assets from disk; violates the shared-context-pack target model. | Violation candidate |
| `skills/studio/agents/cf-codegen.md:26-42` | Loads `SKILL.md`, inline-fallback probe, then `workflows/generate.md`. | Same direct-load pattern as `cf-pr-review`, but for generate/code execution. | Violation candidate |
| `skills/studio/agents/{cf-code-bug-finder,cf-prompt-bug-finder}.md` | `cf-code-bug-finder.md:26-40` and `cf-prompt-bug-finder.md:27-41` load `SKILL.md`, a bug-finding requirement, and `agent-compliance.md`. | Reviewer-style prompt-consuming agents still read requirement prompt assets directly from disk. | Violation candidate |
| `skills/studio/agents/{cf-semantic-reviewer-prompt,cf-semantic-reviewer-code,cf-semantic-reviewer-artifact,cf-semantic-reviewer-consistency}.md` | Representative lines: `cf-semantic-reviewer-prompt.md:23-30`, `cf-semantic-reviewer-code.md:21-29`, `cf-semantic-reviewer-consistency.md:23-27`. | Semantic reviewers directly load `SKILL.md`, requirements, and specs; these should later be supplied via `prompt_context_view`. | Violation candidate |
| `skills/studio/agents/{cf-pdsl-author,cf-pdsl-transformer,cf-pdsl-reviewer}.md` | `cf-pdsl-author.md:21-24`, `cf-pdsl-transformer.md:20-25`, `cf-pdsl-reviewer.md:19-23` all load `SKILL.md` and `architecture/specs/PDSL.md` directly. | PDSL sub-agents are prompt-consuming and currently bypass the shared-context-pack model. | Violation candidate |
| `skills/studio/agents/{cf-analyze-planner,cf-generate-planner}.md` | `cf-analyze-planner.md:23-25` and `cf-generate-planner.md:23-25` both load `SKILL.md` directly. | Planner sub-agents are lighter than reviewers but still lack shared-context consumption. | Violation candidate |
| `skills/studio/agents/{cf-phase-runner,cf-phase-compiler}.md` | `cf-phase-runner.md:27-49` and `cf-phase-compiler.md:24-49` explicitly forbid `SKILL.md` but still load plan workflow/reference files. | Special-case contracts already break the "load SKILL first" pattern; they likely need explicit migration exceptions or dedicated prompt-context rules. | Ambiguous special-case exception |

## Agent-Registry Findings

| Finding | Evidence | Impact |
| --- | --- | --- |
| No prompt-context declarations anywhere in the inventoried runtime prompt corpus | `rg -n 'prompt_context_requirements|prompt_context_view' skills/studio/agents.toml skills/studio/agents workflows .bootstrap` returned no matches. | Phase 4 will need to add prompt-context declarations rather than only cleaning up direct-load prose. |
| Every registered `prompt_file` remains disk-load oriented | `skills/studio/agents.toml` declares 40 prompt files, and representative families above still load prompt assets directly. | Cleanup must be systemic across agent families, not limited to one workflow. |
| Shared contracts excluded from registration still participate in prompt loading | `skills/studio/agents/{cf-generate-author-worker.md,author-production-rules.md}` are excluded from `agents.toml` but remain prompt-bearing contracts. | Phase 4 cannot rely on `agents.toml` alone; it must cover these shared contracts explicitly. |

## Orchestrator Exceptions To Preserve Deliberately

These current-state direct loads look intentional and should be treated as orchestrator/shared-pack-builder exceptions unless Phase 2 rules decide otherwise:

- `skills/studio/protocol.md`
- `.bootstrap/.gen/SKILL.md`
- `.bootstrap/config/SKILL.md`
- `.bootstrap/config/kits/sdlc/SKILL.md`
- `workflows/{plan,workspace}.md`
- Proxy workflows that immediately route into another orchestrator: `workflows/{auto-config,brainstorm}.md`
- `skills/studio/agents/{cf-phase-runner,cf-phase-compiler}.md`

## Ambiguities For Later Phases

- `AGENTS.md` surfaces are prompt sources, but only `AGENTS.md` itself is canonical; the bootstrap copies are runtime-managed mirrors that may need path cleanup without full PDSL conversion.
- The omitted bootstrap `SKILL.md` chain mixes canonical runtime surfaces (`config/SKILL.md`, kit `SKILL.md`) with generated routing (`.gen/SKILL.md`); Phase 2 should decide which stay orchestrator/runtime exceptions versus full shared-context consumers.
- `architecture/specs/{artifacts-registry,CDSL,CLISPEC,cli,traceability}.md` are specs first and prompt assets second; Phase 2 needs a rule for whether they become full PDSL contracts or remain prose specs with normalized load references.
