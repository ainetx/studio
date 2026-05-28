# Phase 01 PDSL Scope Map

## Bucket Summary

| Bucket | Count | Notes |
| --- | ---: | --- |
| Already PDSL | 129 | All workflow files, most core skill/agent contracts, and `architecture/specs/PDSL.md`. |
| Mixed or partial PDSL / special runtime prompt surfaces | 4 | AGENTS surfaces that are prompt-bearing but not primary PDSL rewrite targets. |
| Prose-first rewrite candidates | 46 | Requirements set, prompt-bearing specs, and skill/agent contracts that still rely on prose structure. |
| Out of scope or excluded | 8 | Support docs, registry-only files, deprecated references, and content-reference examples. |

## Already PDSL

| Group | Included paths | Follow-up note |
| --- | --- | --- |
| Workflow system | `workflows/**/*.md` | Phase 3 should normalize shared-context loading and path prefixes without first needing wholesale PDSL conversion. |
| Core skill prompts | `skills/studio/{SKILL.md,protocol.md,routing.md,migrate-from-cypilot.md}` | Mostly structural cleanup and shared-context-pack adoption, not syntax migration. |
| PDSL-shaped agent contracts | `skills/studio/agents/{author-production-rules,cf-analyze-planner,cf-brainstorm-expert,cf-brainstorm-facilitator,cf-brainstorm-panel,cf-code-bug-finder,cf-codegen,cf-deterministic-validator,cf-diff-scope-resolver,cf-generate-author,cf-generate-author-worker,cf-generate-collector,cf-generate-planner,cf-migrate-migrator,cf-migrate-planner,cf-migrate-scanner,cf-migrate-verifier,cf-pdsl-author,cf-pdsl-reviewer,cf-pdsl-transformer,cf-phase-compiler,cf-phase-runner,cf-pr-review,cf-prompt-bug-finder,cf-ralphex,cf-semantic-reviewer-artifact,cf-semantic-reviewer-code,cf-semantic-reviewer-consistency,cf-semantic-reviewer-prompt,storytelling-context-pack,storytelling-export,storytelling-gate,storytelling-preflight,storytelling-wrap}.md` | These agents still need prompt-context declarations and direct-load cleanup even though their block structure is already PDSL-shaped. |
| Normative PDSL spec | `architecture/specs/PDSL.md` | Keep as the baseline reference spec; do not treat it as a conversion target in early phases. |

## Mixed Or Partial PDSL / Special Runtime Prompt Surfaces

| Path | Why it is not a normal PDSL rewrite target | Migration note |
| --- | --- | --- |
| `AGENTS.md` | Managed bootstrap locator block only; not a full behavioral contract. | Keep as source prompt surface; normalize only if path syntax changes. |
| `.bootstrap/config/AGENTS.md` | Runtime adapter prompt with imperative rules but not PDSL block structure. | In scope for shared-context-pack classification and path review, not for early full rewrite. |
| `.bootstrap/.gen/AGENTS.md` | Generated quick-reference prompt surface with placeholders. | Treat as generated runtime surface; avoid canonical editing. |
| `.bootstrap/config/kits/sdlc/AGENTS.md` | Kit prompt quick-reference, mostly lookup content. | In scope for path/shared-context review, not primary PDSL migration. |

## Prose-First Rewrite Candidates

| Group | Included paths | Why it matters |
| --- | --- | --- |
| Skill/runtime prose contract | `skills/studio/sub-agent-dispatch.md` | Central dispatch contract is still prose-first and will need explicit state/menu/error blocks if fully normalized. |
| Leaf author tiers | `skills/studio/agents/{cf-generate-author-junior,cf-generate-author-middle,cf-generate-author-senior,cf-generate-author-lead}.md` | Registered prompt files with no PDSL block markers; likely Phase 4 rewrite targets. |
| Leaf code/prompt author tiers | `skills/studio/agents/{cf-generate-coder-casual,cf-generate-coder-smart,cf-generate-prompt-engineer-casual,cf-generate-prompt-engineer-smart}.md` | Same as above; these are prompt-bearing and still prose-first. |
| Requirements corpus | `requirements/*.md` | Entire requirement corpus is instruction-heavy but prose-first today. |
| Prompt-bearing specs | `architecture/specs/{artifacts-registry,CDSL,CLISPEC,cli,shared-context-pack,sysprompts,traceability}.md` and `architecture/specs/kit/{checklist,constraints,example,kit,rules,template}.md` | These specs are in scope because workflows or AGENTS surfaces explicitly load them as instructions, but they still read as prose specs rather than executable PDSL. |

## Out Of Scope Or Excluded

| Path | Reason |
| --- | --- |
| `skills/studio/README.md` | Documentation only. |
| `skills/studio/agents.toml` | Registry/support metadata, not prompt body content. |
| `skills/studio/scripts/studio/commands/map/assets/vendor/PROVENANCE.md` | Vendor provenance note. |
| `architecture/specs/kit/blueprint.md` | Deprecated legacy reference. |
| `architecture/specs/kit/examples/{blueprint-prd.md,blueprint-minimal.md,blueprint-structure.md}` | Content-reference examples. |
| `architecture/specs/kit/examples/constraints-prd.toml` | Example data file. |

## Agent-Contract Migration Notes

- All 40 registered `prompt_file` contracts in `skills/studio/agents.toml` need `prompt_context_requirements`; none are present yet.
- Families with the clearest prompt-load cleanup need are:
  - `cf-pr-review`, `cf-codegen`
  - reviewer and bug-finder agents
  - PDSL agents
  - planner agents
- `cf-phase-runner` and `cf-phase-compiler` are special cases: they already bypass `SKILL.md`, so later rules must decide whether they are explicit shared-context-pack exceptions or get a minimal plan-only prompt-context contract.
- The excluded shared contracts `cf-generate-author-worker.md` and `author-production-rules.md` must be handled alongside registered agents even though they are not in `agents.toml`.

## Runtime And Bootstrap Notes

- `AGENTS.md` is canonical source; `.bootstrap/config/AGENTS.md` and `.bootstrap/.gen/AGENTS.md` are runtime mirrors and should not be treated as canonical rewrite targets.
- `workflows/pdsl.md` is already PDSL-shaped but still points at root-relative prompt paths, so it belongs in the path-normalization tranche rather than the syntax-conversion tranche.
- Proxy workflows `workflows/{auto-config,brainstorm}.md` are already compact PDSL wrappers; their main migration need is shared-context-pack-safe loading through the routed orchestrator.

## Initial Sequencing Hints

1. Phase 2 should define when prose specs remain prose and when they must become PDSL.
2. Phase 3 should fix orchestrators and shared loaders first, because leaf agents currently depend on those load paths.
3. Phase 4 should then update agent contracts with `prompt_context_requirements` plus direct-load cleanup.
4. Phase 5 can migrate the prose-first requirement/spec corpus with the agent-context contract already fixed.
