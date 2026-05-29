# Phase 01 Prompt Inventory

## Summary

| Corpus area | Included prompt-bearing surfaces | Notes |
| --- | ---: | --- |
| `workflows/` | 90 | All workflow root files and all workflow sub-phase files are prompt assets. |
| `skills/studio/` | 47 | 5 core prompt docs, 40 registered agent prompt files, 2 prompt-bearing shared contracts excluded from `agents.toml`. |
| `requirements/` | 24 | All files are methodology, checklist, template, or prompt-review requirements. |
| `architecture/specs/` | 14 | Technical specs that directly instruct agent behavior or are loaded by prompt surfaces. |
| `AGENTS.md` surfaces | 4 | Source, bootstrap runtime, generated runtime, and kit prompt surfaces. |
| `.bootstrap` runtime skill/workflow surfaces | 6 | Active runtime prompt chain loaded from bootstrap `SKILL.md` surfaces into kit-specific workflows. |
| Total included | 185 | Prompt-bearing or prompt-surface files that later phases must consider. |

## Included Prompt-Bearing Files

### Workflows

All 90 Markdown files under `workflows/` are prompt assets.

| Group | Count | Included paths |
| --- | ---: | --- |
| Workflow roots | 10 | `workflows/{analyze,auto-config,brainstorm,explain,generate,map,pdsl,plan,studio,workspace}.md` |
| Analyze subtree | 25 | `workflows/analyze/**/*.md` |
| Generate subtree | 36 | `workflows/generate/**/*.md` |
| PDSL subtree | 3 | `workflows/pdsl/{new,review,transform}.md` |
| Plan subtree | 7 | `workflows/plan/**/*.md` |
| Shared helpers | 4 | `workflows/shared/{inline-fallback-probe,mode-resolution,plan-escalation-gate,stop-token-policy}.md` |
| Workspace subtree | 5 | `workflows/workspace/**/*.md` |

Reason: each file's primary purpose is to instruct workflow behavior, routing, state handling, output formatting, or phase execution.

### Skills And Agent Contracts

| Group | Count | Included paths |
| --- | ---: | --- |
| Core skill prompts | 5 | `skills/studio/{SKILL.md,protocol.md,routing.md,sub-agent-dispatch.md,migrate-from-cypilot.md}` |
| Registered agent prompt files | 40 | `skills/studio/agents/{cf-codegen,cf-pr-review,cf-ralphex,cf-phase-runner,cf-phase-compiler,cf-migrate-scanner,cf-migrate-planner,cf-migrate-migrator,cf-migrate-verifier,cf-diff-scope-resolver,cf-deterministic-validator,cf-semantic-reviewer-artifact,cf-semantic-reviewer-code,cf-code-bug-finder,cf-semantic-reviewer-prompt,cf-prompt-bug-finder,cf-pdsl-author,cf-pdsl-transformer,cf-pdsl-reviewer,cf-semantic-reviewer-consistency,cf-brainstorm-facilitator,cf-brainstorm-expert,cf-brainstorm-panel,cf-generate-collector,cf-analyze-planner,cf-generate-planner,cf-generate-author,cf-generate-author-junior,cf-generate-author-middle,cf-generate-author-senior,cf-generate-author-lead,cf-generate-coder-casual,cf-generate-coder-smart,cf-generate-prompt-engineer-casual,cf-generate-prompt-engineer-smart,storytelling-preflight,storytelling-gate,storytelling-context-pack,storytelling-wrap,storytelling-export}.md` |
| Prompt-bearing shared contracts excluded from agent registration | 2 | `skills/studio/agents/{cf-generate-author-worker.md,author-production-rules.md}` |

Reason: these files directly instruct the skill runtime or one sub-agent's behavior.

### Requirements

All 24 Markdown files under `requirements/` are prompt assets because they are checklists, templates, methodology docs, or execution rules consumed by workflows and reviewers.

Included paths:

`requirements/{agent-compliance,auto-config,brief-template,bug-finding,code-checklist,consistency-checklist,execution-protocol,language-complexity,map,pdsl-patterns,plan-checklist,plan-decomposition,plan-template,prompt-bug-finding,prompt-engineering,raw-input-overflow,reverse-engineering,storytelling,storytelling-export,storytelling-modes,storytelling-phases,storytelling-preferences,storytelling-shared,workspace}.md`

### Architecture Specs

Included prompt-bearing or mixed prompt/spec surfaces:

`architecture/specs/{artifacts-registry,CDSL,CLISPEC,PDSL,cli,shared-context-pack,sysprompts,traceability}.md`

`architecture/specs/kit/{checklist,constraints,example,kit,rules,template}.md`

Reason: these files either contain explicit "open and follow" guidance, define prompt-facing DSL and shared-context contracts, or are kit-authored instruction/spec formats used by agent workflows.

### AGENTS.md Surfaces

| Path | Classification | Reason |
| --- | --- | --- |
| `AGENTS.md` | Source prompt asset | Canonical root bootstrap surface; currently only sets `cf-studio-path`, but it is the source instruction surface for bootstrap discovery. |
| `.bootstrap/config/AGENTS.md` | Runtime prompt asset | Bootstrap adapter prompt surface with navigation and development rules. |
| `.bootstrap/.gen/AGENTS.md` | Generated runtime prompt asset | Generated quick-reference prompt surface consumed during Protocol Guard. |
| `.bootstrap/config/kits/sdlc/AGENTS.md` | Kit prompt asset | Kit-specific prompt surface summarizing artifact usage and references. |

### Bootstrap Runtime Skill And Workflow Surfaces

| Path | Classification | Reason |
| --- | --- | --- |
| `.bootstrap/.gen/SKILL.md` | Generated runtime skill prompt surface | Active runtime skill surface; it instructs the agent to invoke `{cf-studio-path}/config/kits/sdlc/SKILL.md` first. |
| `.bootstrap/config/SKILL.md` | Runtime skill prompt surface | Bootstrap prompt surface loaded alongside `.gen/SKILL.md`; currently small, but still part of the active runtime skill chain. |
| `.bootstrap/config/kits/sdlc/SKILL.md` | Kit runtime skill prompt surface | Active kit extension surface that routes PR review, PR status, and OpenSpec migration requests into dedicated workflows. |
| `.bootstrap/config/kits/sdlc/workflows/pr-review.md` | Kit runtime workflow prompt asset | Runtime workflow contract for PR review requests; directly instructs analysis steps, output paths, and checklist loading. |
| `.bootstrap/config/kits/sdlc/workflows/pr-status.md` | Kit runtime workflow prompt asset | Runtime workflow contract for PR status requests; directly instructs fetch, audit, and severity-triage behavior. |
| `.bootstrap/config/kits/sdlc/workflows/migrate-openspec.md` | Kit runtime workflow prompt asset | Runtime workflow contract for OpenSpec migration; governs multi-phase artifact generation and validation behavior. |

## Mixed Prompt And Resource Surfaces

| Path | Mixed reason |
| --- | --- |
| `AGENTS.md` | Prompt surface is limited to the managed bootstrap block; no broader behavioral contract yet. |
| `.bootstrap/.gen/AGENTS.md` | Prompt-ish navigation rules plus placeholder-heavy quick-reference content. |
| `.bootstrap/.gen/SKILL.md` | Generated routing prompt surface; tiny but active, and primarily a bootstrap handoff into the kit skill. |
| `.bootstrap/config/SKILL.md` | Runtime extension surface with minimal project-specific content today, but still loaded as part of the active skill chain. |
| `.bootstrap/config/kits/sdlc/SKILL.md` | Active kit skill surface, but much of its content is routing, command reference, and workflow lookup rather than a pure PDSL contract. |
| `.bootstrap/config/kits/sdlc/AGENTS.md` | Kit prompt surface, but primarily a reference index with unresolved `{...}` placeholders. |
| `architecture/specs/artifacts-registry.md` | Technical registry spec that also embeds direct AGENTS load instructions. |
| `architecture/specs/{CDSL,CLISPEC,cli,traceability}.md` | Technical specs whose primary content is reference material, but they are also explicitly loaded as agent instructions in current prompt surfaces. |

## Representative Exclusions

| Path | Exclusion reason |
| --- | --- |
| `skills/studio/README.md` | Project documentation, not an agent-behavior contract. |
| `skills/studio/agents.toml` | Registry/support surface used to map prompt files; not itself a prompt asset. |
| `skills/studio/scripts/studio/commands/map/assets/vendor/PROVENANCE.md` | Vendor provenance document, not runtime prompt content. |
| `architecture/specs/kit/blueprint.md` | Deprecated legacy reference retained for historical compatibility, not a migration-priority prompt contract. |
| `architecture/specs/kit/examples/{blueprint-prd.md,blueprint-minimal.md,blueprint-structure.md}` | Content-reference examples rather than active prompt assets. |
| `architecture/specs/kit/examples/constraints-prd.toml` | Example data file, not a prompt asset. |

## Inventory Notes

- All 40 `prompt_file` targets declared in `skills/studio/agents.toml` are covered above.
- The explicitly excluded shared contracts `skills/studio/agents/cf-generate-author-worker.md` and `skills/studio/agents/author-production-rules.md` are prompt-bearing and must remain visible in later migration phases even though they are not registered dispatch targets.
- The runtime bootstrap skill chain adds 6 active prompt surfaces that were previously omitted: `.bootstrap/.gen/SKILL.md`, `.bootstrap/config/SKILL.md`, `.bootstrap/config/kits/sdlc/SKILL.md`, and the three SDLC kit workflow files.
- The largest migration surface is `workflows/` plus `skills/studio/agents/`; those two areas still account for 132 of the 185 included prompt-bearing files.
