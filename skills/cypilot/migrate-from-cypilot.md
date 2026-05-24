---
cf-constructor: true
type: skill
name: cf-constructor-migrate-from-cypilot
description: "Post-deterministic migration cleanup orchestrator. Coordinates four sub-agents (scanner, planner, migrator, verifier) to find and resolve residual cypilot/cpt/Cypilot/Cyber Pilot references that the mechanical cfc init --migrate-from-cypilot=yes did NOT touch (source code, CI, docs, agent configs, workspaces, build files). Asks the user before each sub-agent dispatch; loops migrator ↔ verifier until clean or until the iteration cap (3) is hit."
version: 1.0
purpose: Finish the migration from Cyber Pilot to Cyber Constructor after the deterministic mechanical run
---

# Migrate from Cypilot — Post-Deterministic Cleanup Orchestrator


<!-- toc -->

- [Goal](#goal)
- [Preconditions](#preconditions)
- [Hard Rules](#hard-rules)
- [Phases](#phases)
  - [E0: Preconditions check](#e0-preconditions-check)
  - [E1: Scanner dispatch (user-gated)](#e1-scanner-dispatch-user-gated)
  - [E2: Planner dispatch (user-gated)](#e2-planner-dispatch-user-gated)
  - [E3: Migrator dispatch (user-gated, plan-aware)](#e3-migrator-dispatch-user-gated-plan-aware)
  - [E4: Verifier dispatch (user-gated)](#e4-verifier-dispatch-user-gated)
  - [E5: Migrator ↔ Verifier loop](#e5-migrator--verifier-loop)
  - [E6: Final report](#e6-final-report)
- [Sub-agent dispatch contract](#sub-agent-dispatch-contract)
- [Validation Criteria](#validation-criteria)

<!-- /toc -->

ALWAYS open and follow `{cf-constructor-path}/.core/skills/cypilot/SKILL.md` FIRST WHEN `{cfc_mode}` is `off`

**Type**: Orchestrator skill (loaded by the workflow-routing keyword `migrate from cypilot` / `migrate-from-cypilot`)

## Goal

After `cfc init --migrate-from-cypilot=yes` (or `cfc update --migrate-from-cypilot=yes`, or `cfc migrate-from-cypilot`) runs the **deterministic mechanical migration** — directory copy, root managed-block swap (`@cpt:root-agents` → `@cf:root-agents`), config TOML/Markdown rewrites in a fixed list — this skill picks up everything ELSE:

- Source code files (`*.py`, `*.ts`, `*.js`, `*.go`, etc.) referencing `cypilot` / `cpt` / `Cypilot` / `Cyber Pilot`
- CI configurations (`.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/`, `azure-pipelines.yml`)
- Build files (`pyproject.toml`, `package.json`, `Makefile`, `Dockerfile`)
- Documentation outside the deterministic fixed list (`CONTRIBUTING.md`, `ARCHITECTURE.md`, `CHANGELOG.md`, `docs/`)
- Shell scripts, `.envrc`, direnv configs
- Agent integration directories (`.agents/`, `.claude/`, `.cursor/`, `.codex/`, `.windsurf/`) — typically need `cfc generate-agents` to regenerate
- Multi-repo workspaces (`.cypilot-workspace.toml` → `.cf-constructor-workspace.toml`; member repos may need cascading migration)

The orchestrator does NOT do the work itself. It coordinates four sub-agents:

1. **Scanner** — read-only; scans the project and emits a structured findings list
2. **Planner** — read-only; categorizes findings into A (auto-fixable) / B (needs-review) / C (cascade operation)
3. **Migrator** — write-capable; applies the plan
4. **Verifier** — read-only; re-scans and compares to the manifest, reporting residue

Between each dispatch, the orchestrator **asks the user explicitly** whether to proceed. The migrator ↔ verifier loop is bounded (max 3 verifier iterations).

## Preconditions

The deterministic migration MUST have completed before this skill runs:

- Root `AGENTS.md` contains `<!-- @cf:root-agents -->` (not the legacy `<!-- @cpt:root-agents -->`)
- `{cf-constructor-path}/config/core.toml` exists
- If the user just ran `cfc init --migrate-from-cypilot=yes`, the success message recommended this skill — proceed
- If unclear, ask the user to confirm: _"Has the deterministic migration (`cfc init --migrate-from-cypilot=yes` or equivalent) completed successfully? [y/N]"_

If the precondition fails, STOP at E0 and direct the user to run the deterministic migration first.

## Hard Rules

- **MUST** ask the user before EACH sub-agent dispatch (E1, E2, E3, E4, and each E5 loop iteration). Never dispatch silently.
- **MUST NOT** dispatch the Migrator (write-capable) without explicit user approval AND a Plan from the Planner. Skipping straight from Scanner to Migrator is forbidden.
- **MUST** present the Planner's plan to the user in full before asking for Migrator approval.
- **MUST** cap the migrator ↔ verifier loop at 3 verifier iterations. After that, halt and surface remaining issues for human review.
- **MUST NOT** modify files outside the project root.
- **MUST NOT** modify files inside `{cf-constructor-path}/.core/` (those are kit-managed; `cfc update` owns them).
- **MUST** respect project memories: `project_markdown_rewriter_conservative.md` (preserve `cpt.` / line-start `cpt` in cyber-constructor source), `project_cypilot_lifecycle.md` (cypilot EOL at 3.10.0; frozen support set is final), `project_json_mode_fixture.md` (existing fixture is correct), `project_kit_format_field.md` (`format = "Cypilot"` in `[kits.<slug>]` TOML tables is a technical kit-format identifier — preserve verbatim).
- **MUST** treat `@cpt-*` / `@cpt:*` markers in source code as **needs-review** by default — per v4.0.0 design they're intentionally preserved in cyber-constructor's own source code.
- **MUST NOT** rewrite `format = "Cypilot"` inside `[kits.<slug>]` (or `[kit.<slug>]`) TOML tables. It is the kit-bundle format identifier, not the brand name — rewriting it breaks kit-format detection.

## Phases

### E0: Preconditions check

1. Read root `AGENTS.md`. Confirm `<!-- @cf:root-agents -->` is present (not `<!-- @cpt:root-agents -->`).
2. Confirm `{cf-constructor-path}/config/core.toml` exists.
3. If both pass, log `- [migrate-from-cypilot]: E0 preconditions PASS` and continue to E1.
4. If either fails, STOP with the message:

   ```text
   The deterministic migration has not completed (or was not detected).
   Run one of:
       cfc init --migrate-from-cypilot=yes              # fresh install
       cfc update --migrate-from-cypilot=yes            # existing install
       cfc migrate-from-cypilot                          # direct command
   Then re-invoke this skill: cf-constructor migrate from cypilot
   ```

### E1: Scanner dispatch (user-gated)

Ask the user:

```text
Phase E1 — Scanner

Scanner is read-only. It scans the project for residual cypilot/cpt/
Cypilot/Cyber Pilot references in:
  - Source code (*.py, *.ts, *.js, *.go, *.rs, etc.)
  - CI configs (.github/workflows, .gitlab-ci.yml, etc.)
  - Build files (pyproject.toml, package.json, Makefile, Dockerfile)
  - Docs outside the deterministic fixed list (CONTRIBUTING.md,
    ARCHITECTURE.md, CHANGELOG.md, docs/)
  - Shell scripts
  - Agent configs (.agents/, .claude/, .cursor/, .codex/, .windsurf/)
  - Workspaces (.cypilot-workspace.toml + member repos)

It produces a structured findings list. No files are modified.

Run Scanner agent now? [y/N]
→ suggested: y
```

WAIT for user input. On `y` / `yes` / `да`: dispatch.

Dispatch contract:
- Use the `Agent` tool with `subagent_type="cf-constructor-codegen"` (existing registered type)
- The prompt body MUST start with the full content of `{cf-constructor-path}/.core/skills/cypilot/agents/cf-constructor-migrate-scanner.md` followed by a `## Task Inputs` section providing:
  - `project_root`: absolute path
  - `cf_constructor_path`: absolute path
  - `exclude_dirs`: list of well-known paths to skip (`.git`, `{cf-constructor-path}`, `.cf-constructor-workspace`, build caches)

Receive the agent's findings list. Store as `scan_findings`.

If user replies `N`, STOP at E1 with: _"E1 declined. Re-invoke when you want to scan."_

### E2: Planner dispatch (user-gated)

Ask the user:

```text
Phase E2 — Planner

Scanner returned N findings. Planner is read-only. It categorizes the
findings into:
  A. Auto-fixable — well-defined string substitutions with no ambiguity
  B. Needs-review — substitutions where context matters
  C. Cascade   — non-substitution operations (rename .cypilot-workspace.toml,
                  cascade `cfc init --migrate-from-cypilot=yes` to workspace
                  members, run `cfc generate-agents` to regenerate IDE
                  integrations)

It produces a structured plan grouped by category. No files are modified.

Run Planner agent now? [y/N]
→ suggested: y
```

WAIT. On `y`, dispatch.

Dispatch contract:
- Same `Agent` tool, `subagent_type="cf-constructor-codegen"`
- Prompt body: content of `cf-constructor-migrate-planner.md` + `## Task Inputs` with:
  - `scan_findings`: full output of the Scanner phase

Store the agent's output as `plan`.

### E3: Migrator dispatch (user-gated, plan-aware)

Present the plan to the user IN FULL (the entire output from Planner), then ask:

```text
Phase E3 — Migrator

Review the plan above. The Migrator agent applies changes to disk.

  1. y       — apply category A (auto-fixable) only
  2. y+B     — apply A AND walk through B interactively
  3. y+C     — apply A AND walk B AND start C (cascade — prints commands;
                does not auto-execute cross-repo operations)
  4. select  — interactively pick specific items from A/B/C
  5. N       — skip Migrator; the plan stays in memory for this session
                only (re-invoke E2 to regenerate)
→ suggested: 1
```

WAIT. On any "run" branch, dispatch Migrator.

Dispatch contract:
- `Agent` tool, `subagent_type="cf-constructor-codegen"`
- Prompt body: content of `cf-constructor-migrate-migrator.md` + `## Task Inputs`:
  - `plan`: full Planner output
  - `selection`: which categories/items the user approved (`A` / `AB` / `ABC` / explicit list)
  - `project_root`, `cf_constructor_path`
  - `git_commit_mode`: `GIT_COMMIT_MODE` (MUST be included; set from the session-scoped flag)
  - `contributing_guide`: `CONTRIBUTING_GUIDE` (MUST be included; `null` when not found)
  - `git_constraint`: the mode-matched constraint block from `workflows/generate/phase-4-write.md` § Git constraint blocks

Store the agent's `migration_manifest` (the list of changes actually applied).

### E4: Verifier dispatch (user-gated)

Ask the user:

```text
Phase E4 — Verifier

Migrator applied N changes. Verifier is read-only. It re-runs Scanner's
patterns and diffs against the migration manifest. Output:
  - "All clean" — no residue detected
  - Residue list — findings that should have been fixed but weren't,
                    or new findings that appeared

Run Verifier agent now? [y/N]
→ suggested: y
```

WAIT. On `y`, dispatch.

Dispatch contract:
- `Agent` tool, `subagent_type="cf-constructor-codegen"`
- Prompt body: content of `cf-constructor-migrate-verifier.md` + `## Task Inputs`:
  - `plan`: full Planner output
  - `migration_manifest`: Migrator's output
  - `project_root`, `cf_constructor_path`

Store `verification_result`.

### E5: Migrator ↔ Verifier loop

If `verification_result` reports residue (regressions OR un-applied items that should have been):

1. Increment `verifier_iteration` counter (starts at 1 after E4).
2. If `verifier_iteration >= 3`, STOP — emit `"Verifier-loop iteration cap (3) reached"` with the residue list, and continue to E6.
3. Else, ask the user:

   ```text
   Phase E5 — Migrator (iteration {N})

   Verifier found {K} unresolved issues:
     <truncated preview, max 10 items>

   Run Migrator again to fix these issues? [y/N]
   → suggested: y
   ```

4. WAIT. On `y`, dispatch Migrator with the verifier's residue as the new task. Then GOTO E4.
5. On `N`, continue to E6 with the residue surfaced.

Else (all clean): continue to E6.

### E6: Final report

Emit a single structured summary:

```text
## Migrate from Cypilot — Final Report

Phases run:
  E0 preconditions:  PASS
  E1 scanner:        {N findings}
  E2 planner:        {A_count auto-fixable / B_count needs-review / C_count cascade}
  E3 migrator:       {M applied / Q skipped} (selection: {A|AB|ABC|select})
  E4 verifier (×{T iterations}): {clean | K residue}
  E5 loop:           {hit iteration cap | resolved on iteration N | not needed}

Outstanding work (if any):
  - {file:line — description — recommended manual action}
  ...

Cascade operations to run manually (if any):
  - {command}
  ...

Suggested next steps:
  - {context-appropriate}
```

## Sub-agent dispatch contract

All four sub-agents are dispatched via the same mechanism:

- Tool: `Agent`
- `subagent_type`: `"cf-constructor-codegen"` (use the existing registered type; future evolution may register dedicated types like `cf-constructor-migrate-scanner` — for now we parametrize codegen with the role file content)
- Prompt: concatenation of `{role-file-content}` + `\n\n## Task Inputs\n\n{role-specific JSON / key-value inputs}`
- Run in foreground (default) so the orchestrator can chain to the next phase

Each role file is self-contained: it declares purpose, expected inputs, procedure, output format, and hard rules. The orchestrator does not need to interpret the agent's internal logic; it just passes inputs and consumes the structured output.

## Validation Criteria

- [ ] Preconditions verified at E0 (legitimate deterministic migration completed)
- [ ] User explicitly approved EACH sub-agent dispatch (E1, E2, E3, E4, every E5 iteration)
- [ ] Migrator never dispatched without a Planner-produced plan in hand
- [ ] Plan presented to user IN FULL before asking for Migrator approval
- [ ] Migrator ↔ Verifier loop respects the 3-iteration cap
- [ ] Final report emitted (E6) regardless of whether E5 hit clean or cap
- [ ] No files modified outside `project_root`
- [ ] No files modified inside `{cf-constructor-path}/.core/` (kit-managed)
- [ ] Project memories respected (conservative markdown rewriter, cypilot EOL, json_mode fixture)
- [ ] `@cpt-*` markers in source code treated as needs-review (per v4.0.0 rebrand design)
