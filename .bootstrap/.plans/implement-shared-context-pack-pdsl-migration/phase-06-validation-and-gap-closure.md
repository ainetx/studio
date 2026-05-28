```toml
[phase]
plan = "implement-shared-context-pack-pdsl-migration"
number = 6
total = 6
type = "implement"
title = "Validation and gap closure"
depends_on = [5]
input_manifest = ""
input_signature = ""
input_files = ["workflows", "skills", "requirements", "architecture/specs", "skills/studio/agents.toml"]
output_files = ["workflows", "skills", "requirements", "architecture/specs", "skills/studio/agents.toml"]
outputs = ["out/phase-06-validation-report.md", "out/phase-06-remaining-findings.md"]
inputs = ["out/phase-01-prompt-inventory.md", "out/phase-01-load-path-findings.md", "out/phase-05-path-prefix-remediation.md"]
```

## Preamble

This is a self-contained phase file. All rules, constraints, and kit content
are included below. Project files listed in the Task section must be read
at runtime. Follow the instructions exactly, run any EXECUTE commands as
written, and report results against the acceptance criteria at the end.

## What

Validate the migrated prompt-bearing corpus and close any remaining
deterministic migration gaps across `workflows/`, `skills/`, `requirements/`,
`architecture/specs/`, and `skills/studio/agents.toml`. This phase verifies
shared-context-pack compliance, removes residual direct prompt-loading and
missing `.bootstrap` path-prefix issues, and confirms that prompt-bearing files
use PDSL where required. The prior `out/*` entries listed under `inputs` are
required runtime dependencies from earlier phases, not compile-time blockers
for generating this phase file.

## Prior Context

This is phase 6 of 6 in
`implement-shared-context-pack-pdsl-migration`.
Phase 5 completed the main requirements-and-specs migration and path-prefix
remediation work that this phase depends on.
The plan brief classifies
`out/phase-01-prompt-inventory.md`,
`out/phase-01-load-path-findings.md`, and
`out/phase-05-path-prefix-remediation.md`
as runtime artifacts produced by earlier phases.
Those files were absent during compilation of this phase file, which did not
block compilation.
At execution time they are required validation inputs and must be read before
making final in-scope remediation decisions.
Execution produces `out/phase-06-validation-report.md` and
`out/phase-06-remaining-findings.md`.

## User Decisions

### Already Decided (pre-resolved during planning)

- **Execution scope**: `workflows/`, `skills/`, `requirements/`,
  `architecture/specs/`, and `skills/studio/agents.toml`
- **Primary validation targets**: forbidden prompt-load patterns, missing
  `.bootstrap` path prefixes, and non-PDSL prompt-bearing files still in scope
- **Runtime dependency policy**: `out/*` files listed under `inputs` are
  earlier-phase runtime dependencies that must be preserved as Task reads, not
  treated as compile-time blockers
- **Fallback for unresolved cases**: keep the file unchanged and record the gap
  in `out/phase-06-remaining-findings.md`

### Decisions Needed During This Phase

None. Apply deterministic fixes directly and record ambiguous or speculative
items as remaining findings.

## Rules

### Execution Contract

- MUST treat this phase as validation and deterministic gap closure only
- MUST read project files only from the runtime-read paths listed in the Task
  section
- MUST keep all changes within `workflows/`, `skills/`, `requirements/`,
  `architecture/specs/`, `skills/studio/agents.toml`,
  `out/phase-06-validation-report.md`, and
  `out/phase-06-remaining-findings.md`
- MUST preserve semantics when applying any deterministic remediation
- MUST NOT guess when a remaining issue requires new design intent; leave the
  file unchanged and record the issue
- MUST self-verify against every acceptance criterion before reporting

### Runtime Dependency Handling

- `out/phase-01-prompt-inventory.md`,
  `out/phase-01-load-path-findings.md`, and
  `out/phase-05-path-prefix-remediation.md`
  are required runtime inputs produced by earlier phases
- Those `out/*` inputs are runtime dependencies, not compile-time blockers for
  generating this phase file
- At execution time, MUST read all three runtime dependency files before using
  them to scope PDSL candidates or compare remaining findings
- If any required runtime dependency is missing at execution time, MUST stop and
  report the exact missing path as a runtime dependency failure
- MUST NOT replace a missing runtime dependency with ad hoc rescans or inferred
  baseline data

### Shared Context Pack Compliance

- Any sub-agent that uses prompt assets MUST declare
  `prompt_context_requirements`
- `requires_shared_context_pack` MUST be `true` for any sub-agent that uses
  prompt assets
- `required_assets` MUST list every prompt asset class necessary to execute the
  contract safely
- Agents MUST declare prompt needs semantically, not as imperative file-open
  instructions
- `prompt_context_view` MUST contain all required assets declared by the agent
- `prompt_context_view` MUST contain only the prompt assets needed by that
  agent for the current task
- The agent MUST treat `prompt_context_view` as its sole prompt or instruction
  source
- Prompt-consuming sub-agents MUST consume prompt and instruction context
  exclusively via `prompt_context_view`
- Prompt-consuming sub-agents MUST NOT load prompt assets from the filesystem
  directly
- Prompt-consuming sub-agents MUST NOT instruct themselves to open
  `SKILL.md`, `workflows/*.md`, `requirements/*.md`, `AGENTS.md`, or kit
  prompt files directly
- Prompt-consuming sub-agents MUST treat missing required prompt context as an
  orchestration error
- Sub-agents MAY still read non-prompt resource inputs such as target files,
  code, or artifact documents according to their task contract
- Validator checks MUST detect direct `Open and follow ...SKILL.md`
- Validator checks MUST detect direct `Open and follow ...workflows/...`
- Validator checks MUST detect direct `Open and follow ...requirements/...`
- Validator checks MUST detect direct `Open and follow ...AGENTS.md`
- Validator checks MUST detect imperative self-bootstrap for prompt assets
- The forbidden prompt-loading patterns are allowed only for the workflow
  orchestrator, a dedicated shared-context-pack builder, or another explicitly
  designated top-level controller whose role is prompt asset discovery and pack
  construction
- The orchestrator MUST NOT silently degrade to direct prompt file reads when
  required prompt assets cannot be resolved
- Invalid failure handling includes telling the agent to load the missing
  prompt file itself

### PDSL Compliance

- PDSL MUST be compact enough to replace repetitive prose
- PDSL MUST be readable by humans without a parser
- PDSL MUST be explicit about state, branches, and stop points
- PDSL MUST be easy for an LLM to follow as an execution contract
- PDSL MUST be stable under copy, review, and partial editing
- PDSL MUST NOT depend on hidden semantics
- If a state change, menu choice, or stop condition matters, it MUST be written
  explicitly
- Use PDSL for workflow phases, state gates, approval menus, UX prompts, error
  handling, required and forbidden actions, and handoff rules
- Keep prose for context and rationale; use PDSL for behavior
- Use `MUST` and `MUST_NOT` inside `RULES` and `INVARIANTS`
- A `PATTERNS:` block MUST appear before the first `UNIT` that references it
- Pattern names MUST be unique within a file
- Patterns shared across multiple files MUST be registered in
  `requirements/pdsl-patterns.md`
- A `matches()` call MUST reference a name defined in a local `PATTERNS:` block
  or in `requirements/pdsl-patterns.md`
- Every menu option MUST have an action
- Invalid menu input MUST be specified
- If a menu is a hard interaction boundary, it MUST end with `STOP_TURN`
- Defaults MUST be explicit when missing state changes behavior
- Reset rules MUST be explicit when state is scoped to a turn, workflow, or
  session
- LLMs MUST NOT infer executable behavior from `NOTES` unless another
  executable block references it

### Scope And Reporting Rules

- MUST treat `architecture/specs/` as validation reference material first; do
  not flag prose specification files solely because they are not written in
  PDSL
- MUST validate PDSL usage only for prompt-bearing files in scope, using
  `out/phase-01-prompt-inventory.md` as the baseline for prompt-bearing status
- MUST validate path-prefix compliance against the repo's configured
  `cf-studio-path`, which is `.bootstrap`
- MUST record every unresolved or intentionally deferred finding in
  `out/phase-06-remaining-findings.md`
- MUST write a validation report that records scans run, files modified,
  findings closed, remaining findings count, and final pass or fail status

## Input

### Validation Law

- Prompt assets for sub-agents must come from `prompt_context_view`, not direct
  disk reads
- Direct prompt-load instructions are invalid in prompt-consuming sub-agents
  even when the referenced files exist
- Allowed direct prompt loading is limited to orchestrators or explicit
  shared-context-pack builders
- Missing prompt context is a deterministic validation failure, not a reason to
  fall back to ad hoc file opening

### Forbidden Pattern Set

- `Open and follow .bootstrap/.core/skills/studio/SKILL.md`
- `Open and follow .bootstrap/.core/workflows/...`
- `Open and follow .bootstrap/.core/requirements/...`
- `Open and follow .bootstrap/config/AGENTS.md`
- `Open and follow .bootstrap/config/sysprompts/...`
- `Open and follow` instructions that bootstrap kit prompt-asset paths from
  disk when the target is a prompt asset
- Equivalent imperative instructions that tell a prompt-consuming sub-agent to
  bootstrap its own prompt context from disk

### PDSL Conformance Checklist

- Prompt-bearing behavior in `workflows/`, `skills/`, and `requirements/` uses
  explicit PDSL blocks instead of prose-only execution contracts
- Executable behavior uses visible block headers such as `UNIT`, `DO`, `RULES`,
  `MENU`, `WHEN`, `STATE`, and `ON_ERROR` as needed
- Menus, state transitions, and stop points are explicit instead of implied
- Reusable patterns referenced by `matches()` are defined locally or in
  `requirements/pdsl-patterns.md`
- Context and rationale may stay in prose, but behavior-bearing instructions
  must not rely on prose-only hidden semantics

### Runtime Dependencies

- Required earlier-phase outputs:
  `out/phase-01-prompt-inventory.md`,
  `out/phase-01-load-path-findings.md`,
  `out/phase-05-path-prefix-remediation.md`
- These files are required at execution time to define the prompt-bearing
  baseline and prior remediation state
- Their absence during phase compilation did not invalidate this phase file

### Corpus Under Validation

- `workflows/`
- `skills/`
- `requirements/`
- `architecture/specs/`
- `skills/studio/agents.toml`

### Deliverables

- `out/phase-06-validation-report.md`
- `out/phase-06-remaining-findings.md`

## Task

1. Read the required runtime dependency files from earlier phases:
   `out/phase-01-prompt-inventory.md`,
   `out/phase-01-load-path-findings.md`, and
   `out/phase-05-path-prefix-remediation.md`.
   If any file is missing at execution time, stop immediately and report the
   exact missing runtime dependency instead of continuing validation.
2. Read the validation corpus with targeted scans:
   `workflows/`, `skills/`, `requirements/`, `architecture/specs/`, and
   `skills/studio/agents.toml`.
3. Build the validation baseline and capture raw findings with deterministic
   scans.
   EXECUTE:
   ```bash
   rg -n \
     -e 'Open and follow .*SKILL\.md' \
     -e 'Open and follow .*workflows/' \
     -e 'Open and follow .*requirements/' \
     -e 'Open and follow .*AGENTS\.md' \
     -e 'Open and follow .*sysprompts/' \
     workflows skills requirements architecture/specs skills/studio/agents.toml
   ```
   EXECUTE:
   ```bash
   rg -n \
     -e 'Open and follow (\.core/|config/AGENTS\.md|config/sysprompts/)' \
     -e 'prompt_context_requirements' \
     -e 'prompt_context_view' \
     workflows skills requirements architecture/specs skills/studio/agents.toml
   ```
   EXECUTE:
   ```bash
   rg -L '^UNIT ' workflows skills requirements -g '*.md'
   ```
   Use `out/phase-01-prompt-inventory.md` to identify which files are
   prompt-bearing before classifying non-PDSL files as conversion candidates.
4. Close every deterministic remaining gap in place.
   Replace residual forbidden prompt-load instructions in prompt-consuming
   contracts with shared-context-pack-compliant wording.
   Add missing `.bootstrap` path prefixes for Studio prompt-asset references
   that still target bootstrap-managed assets.
   Convert residual prompt-bearing behavior blocks in `workflows/`, `skills/`,
   and `requirements/` to compact PDSL when the conversion is mechanical and
   semantics-preserving.
   Do not rewrite prose specification content in `architecture/specs/` unless
   the issue is a concrete prompt-path or validation-law defect.
5. Re-run the same scans from step 3 and confirm that every deterministic issue
   class is either resolved or explicitly justified as an allowed
   orchestrator/controller exception.
   Any remaining prompt-consuming forbidden-pattern hit MUST be recorded as an
   unresolved finding.
6. Write `out/phase-06-validation-report.md` with the scans run, files
   modified, findings closed, remaining findings count, and final `PASS` or
   `FAIL` status.
   Write `out/phase-06-remaining-findings.md` with every unresolved or
   intentionally deferred finding, including the blocking reason and why it was
   not safely fixable in this phase.
7. Self-verify against the acceptance criteria before reporting completion.
   Confirm the runtime dependency reads happened first, the deliverables exist,
   the phase result is evidence-backed, this file remains within the line
   budget, and there are no unresolved placeholder variables outside code
   fences.

## Acceptance Criteria

- All three earlier-phase `out/*` runtime dependency files were read before
  validation decisions were made; if any was missing, execution stopped with an
  explicit missing-runtime-dependency failure
- The deterministic scans from Task step 3 and Task step 5 were run against
  `workflows/`, `skills/`, `requirements/`, `architecture/specs/`, and
  `skills/studio/agents.toml`
- Every deterministic forbidden prompt-load or missing `.bootstrap` prefix
  issue in scope was either fixed or recorded in
  `out/phase-06-remaining-findings.md` with a concrete justification
- Only files identified as prompt-bearing by
  `out/phase-01-prompt-inventory.md` were treated as PDSL conversion
  candidates, and any non-mechanical conversion need was recorded as a
  remaining finding
- `out/phase-06-validation-report.md` and
  `out/phase-06-remaining-findings.md` both exist and contain the required
  summary information
- This phase file is `<= 600` lines and contains no unresolved placeholder
  variables outside code fences

## Output Format

When complete, report results in this exact format:
```text
PHASE {N}/{M} COMPLETE
Status: PASS | FAIL
Files created: {list}
Files modified: {list}
Acceptance criteria:
  [x] Criterion 1 — PASS
  [ ] Criterion 2 — FAIL: {reason}
  ...
Line count: {actual}/{budget}
Notes: {any issues or decisions made}
```

If this is the **last phase**, instead of a next-phase prompt output:

```text
ALL PHASES COMPLETE ({M}/{M})
Plan: {cf-studio-path}/.plans/{task-slug}/plan.toml
Lifecycle: {lifecycle_strategy}
```

Then ask: `Continue in this chat? [y/n]`
