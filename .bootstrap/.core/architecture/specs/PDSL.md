---
studio: true
type: spec
name: PDSL Specification
version: 0.2
purpose: Define a compact instruction language for human-readable and LLM-readable workflow, skill, and requirement files
---

# PDSL Specification

PDSL is a compact notation for writing agent instructions in
`skills/`, `workflows/`, and `requirements/`.

The goal is not to create a programming language. The goal is to make
mandatory behavior clear, reviewable, and hard to misread.

Use PDSL for:

- workflow phases
- state gates
- approval menus
- UX prompts
- error handling
- required and forbidden actions
- handoff rules

Keep prose for context and rationale. Use PDSL for behavior.

---

## Design Goals

PDSL MUST be:

- compact enough to replace repetitive prose
- readable by humans without a parser
- explicit about state, branches, and stop points
- easy for an LLM to follow as an execution contract
- stable under copy, review, and partial editing

PDSL MUST NOT depend on hidden semantics. If a state change,
menu choice, or stop condition matters, write it explicitly.

---

## Core Shape

Use uppercase block headers. Each block describes one concern.

```text
UNIT <name>

PURPOSE:
  <one sentence>

STATE:
  <name>: <allowed values>

WHEN:
  <condition>

DO:
  <ordered actions>

MENU <name>:
  <choice> -> <actions>

RULES:
  - MUST <rule>
  - MUST_NOT <rule>

ON_ERROR:
  <error> -> <actions>
```

Blocks MAY be omitted when not relevant. `PURPOSE`, `WHEN`, and `DO` are the
default minimum for executable behavior.

---

## Keywords

Use this small keyword set before inventing new words.

| Keyword | Meaning |
| --- | --- |
| `UNIT` | Named instruction unit, phase, gate, or reusable rule |
| `PURPOSE` | Why this unit exists |
| `INPUT` | Required inputs or context |
| `OUTPUT` | Expected result or handoff |
| `STATE` | State variables and allowed values |
| `WHEN` | Entry condition |
| `DO` | Ordered required actions |
| `SET` | Assign state |
| `EMIT` | Show user-facing text |
| `EMIT_MENU` | Show a named `MENU` block |
| `MENU` | User choice surface |
| `WAIT` | Stop for user input |
| `STOP_TURN` | End assistant turn immediately |
| `CONTINUE` | Move to named unit or phase — see §CONTINUE Target Resolution |
| `DISPATCH` | Invoke a named sub-agent or worker contract |
| `RETURN` | Return a manifest, report, checkpoint, or handoff |
| `FORBID` | Disallowed action |
| `REQUIRE` | Required precondition |
| `RULES` | Mandatory constraints |
| `ON_ERROR` | Error recovery |
| `INVARIANTS` | Conditions that must always hold |
| `NOTES` | Non-executable explanation |
| `SEE_ALSO` | Declares that NOTES or an external resource carries load-bearing context — see §Prose Boundary |
| `PATTERNS` | Named pattern declarations for use with `matches()` — see §Conditions |

Prefer `MUST` and `MUST_NOT` inside `RULES` and `INVARIANTS`.

---

## Conditions

Conditions use plain expressions, not code syntax.

```text
WHEN:
  SUB_AGENT_SESSION_APPROVED == unset
  AND host.supports_native_subagents == true
```

Allowed operators:

- `==`, `!=`
- `AND`, `OR`, `NOT`
- `exists(<name>)`
- `contains(<value>, <token>)`
- `matches(<value>, <pattern-name>)`

Pattern names used with `matches()` MUST be defined in one of:

1. A `PATTERNS:` block in the same file (declared before use).
2. The canonical pattern registry at
   `.bootstrap/.core/requirements/pdsl-patterns.md`.

If a pattern name cannot be resolved to either location, the use of
`matches()` is invalid and the block MUST be rewritten to use a different
operator or an inline condition.

### PATTERNS Block

Use a `PATTERNS:` block in the same file to declare patterns locally.

```text
PATTERNS:
  slug: ^[a-z0-9]+(?:-[a-z0-9]+)*$
  semver: ^\d+\.\d+\.\d+$
```

Pattern names in a `PATTERNS:` block are scoped to the file in which they
appear. Add them to the canonical registry when you want cross-file reuse.

---

## Naming Scope

`UNIT`, `MENU`, and `STATE` names are **file-local by default**. A name
declared in one file creates no obligation or alias in any other file.

Cross-file references require one of:

- An explicit path qualifier: `<workflows/foo.md>:<UnitName>` or
  `<workflows/foo.md>:<MenuName>`.
- A `SEE_ALSO` line in the referencing unit's executable blocks, pointing
  to the file that declares the target name.

Without one of the above, two files that happen to declare the same `UNIT`
or `MENU` name are independent and do not collide.

This subsection is **normative from v0.3**. For v0.2, treat it as a strong
authoring recommendation: prefer unique names across files to avoid
reader confusion even though no collision exists at the execution level.

---

## Actions

Actions are imperative and one per line.

```text
DO:
  REQUIRE workflow_target is known
  SET INLINE_FALLBACK = true
  EMIT_MENU ApprovalMenu
  WAIT user.reply
  STOP_TURN
```

Use `SET` only for state changes. Use `EMIT` or `EMIT_MENU` only for visible
UX output. Use `STOP_TURN` whenever the next step must wait for the user.

---

## Menus

Menus are first-class behavior, not prose.

```text
MENU ApprovalMenu:
  TITLE: Approve sub-agent use for this session
  OPTIONS:
    1 -> SET SUB_AGENT_SESSION_APPROVED = true
         SET INLINE_FALLBACK = false
         CONTINUE CurrentWorkflow
    2 -> SET INLINE_FALLBACK = true
         CONTINUE CurrentWorkflow
  INVALID:
    EMIT "Reply with 1 or 2."
    WAIT user.reply
    STOP_TURN
```

Menu rules:

- Every option MUST have an action.
- Invalid input MUST be specified.
- If the menu is a hard interaction boundary, it MUST end with `STOP_TURN`.
- Suggested options belong in `TITLE` or `NOTES`, not hidden in prose.

---

## State

State declarations list allowed values and default behavior.

```text
STATE:
  CF_PHASE_GATE: armed | released_for_dispatch | released_for_inline_write
    default: armed
    reset: start_of_assistant_turn

  INLINE_FALLBACK: unset | true | false
    default: unset
```

State rules:

- Every referenced state variable SHOULD be declared in the nearest relevant
  `STATE` block.
- Defaults MUST be explicit when missing state changes behavior.
- Reset rules MUST be explicit when state is scoped to a turn, workflow, or
  session.

---

## Invariants And Forbids

Use `INVARIANTS` for always-on rules.

```text
INVARIANTS:
  - MUST keep CF_PHASE_GATE = armed outside released write windows
  - MUST reset CF_PHASE_GATE to armed after dispatch returns
  - MUST_NOT write files while CF_PHASE_GATE == armed
```

Use `FORBID` inside `DO` when a prohibition is local to that unit.

```text
DO:
  FORBID apply_patch while CF_PHASE_GATE == armed
```

---

## Error Handling

Error handling must be part of the same unit when failure changes control flow.

```text
ON_ERROR:
  invalid_menu_reply ->
    EMIT "Reply with 1 or 2."
    WAIT user.reply
    STOP_TURN

  dispatch_failed ->
    SET CF_PHASE_GATE = armed
    EMIT failure_summary
    CONTINUE RecoveryMenu
```

Avoid vague recovery text such as "handle gracefully". Name the next action.

---

## Prose Boundary

PDSL is executable guidance. Prose is explanatory.

Use `NOTES` for explanation that does not create behavior.

```text
NOTES:
  Native sub-agents preserve context isolation and parallelism. Inline fallback
  is slower and weaker, but allows the workflow to continue without host
  support.
```

`NOTES` are advisory-only UNLESS the unit's executable blocks (`DO` / `RULES` /
`INVARIANTS` / `ON_ERROR`) include a `SEE_ALSO` line referencing the NOTES
content. Authors MUST add a `SEE_ALSO` line whenever NOTES carry load-bearing
context (for example: a cross-reference whose omission would cause an LLM to
miss a required behavior).

`SEE_ALSO` syntax inside an executable block:

```text
SEE_ALSO: <unit-name | relative-path>
```

Example — `NOTES` carry a load-bearing cross-reference, so the executable
block declares it:

```text
UNIT PdslDispatchGate

RULES:
  - MUST apply Sub-Agent Approval Gate before any DISPATCH
  - MUST apply dispatch protocol from sub-agent-dispatch.md before any DISPATCH
  SEE_ALSO: sub-agent-dispatch.md

NOTES:
  Full approval gate semantics defined in SKILL.md § Session Sub-Agent
  Approval Gate and sub-agent-dispatch.md.
```

LLMs MUST treat any `NOTES` content without a corresponding `SEE_ALSO` in the
same unit's executable blocks as advisory-only context that does not create
additional obligations.

---

## CONTINUE Target Resolution

`CONTINUE <target>` transfers control to a named destination. The following
magic targets are pre-defined and always valid:

| Magic target | Meaning |
| --- | --- |
| `CurrentWorkflow` | Resume the active workflow from the point after the current unit completes |
| `Bootstrap` | Re-enter the workflow's top-level bootstrap unit |
| `CurrentTurn` | Stay in the current turn; re-evaluate entry condition of current unit |

Every other `CONTINUE <target>` MUST resolve to a `UNIT <target>` declared in
one of:

1. The same file, appearing before or after the referencing unit.
2. A workflow or spec file that is explicitly loaded or referenced by the
   current file.

If a `CONTINUE` target cannot be resolved by either rule, it is invalid and
MUST be replaced with a magic target or a declared `UNIT` name.

Authors MUST NOT invent private magic names. If a new workflow-level
convention is needed, add it to this table in a spec revision.

---

## Example

Prose instruction:

```text
If sub-agent use has not been approved, ask the user whether to use native
sub-agents or inline fallback. If they choose native sub-agents, remember that
for this session. If they choose inline fallback, continue without native
dispatch. Do not assume inline fallback just because the user did not answer.
```

PDSL:

```text
UNIT SubAgentApprovalGate

PURPOSE:
  Resolve whether this workflow may use native sub-agents.

STATE:
  SUB_AGENT_SESSION_APPROVED: unset | true
    default: unset
    scope: session

  INLINE_FALLBACK: unset | true | false
    default: unset
    scope: workflow_run

WHEN:
  SUB_AGENT_SESSION_APPROVED == unset

DO:
  EMIT_MENU SubAgentApprovalMenu
  WAIT user.reply
  STOP_TURN

MENU SubAgentApprovalMenu:
  OPTIONS:
    1 -> SET SUB_AGENT_SESSION_APPROVED = true
         SET INLINE_FALLBACK = false
         CONTINUE CurrentWorkflow
    2 -> SET INLINE_FALLBACK = true
         CONTINUE CurrentWorkflow
  INVALID:
    EMIT "Reply with 1 or 2."
    WAIT user.reply
    STOP_TURN

INVARIANTS:
  - MUST_NOT set INLINE_FALLBACK = true from missing approval
  - MUST_NOT set INLINE_FALLBACK = false unless SUB_AGENT_SESSION_APPROVED == true
```

---

## Authoring Rules

When converting prose instructions to PDSL:

1. Identify state first.
2. Convert every "when/if/unless" sentence into `WHEN` or `ON_ERROR`.
3. Convert every visible user interaction into `MENU`, `EMIT`, `WAIT`, and
   `STOP_TURN`.
4. Convert every "must/never/always" sentence into `RULES` or `INVARIANTS`.
5. Keep rationale in `NOTES`.
6. Do not hide required behavior in paragraphs after the DSL block.

If behavior is too complex for one unit, split it into multiple `UNIT` blocks
and connect them with `CONTINUE <unit-name>`.

---

## Transform Equivalence

A PDSL unit is **transform-equivalent** to its prose source iff every
observable agent behavior — trigger condition, action ordering, stop boundary,
recovery branch, user prompt content, and state mutation — is preserved.
Rationale and prose ordering are not part of the equivalence. Load-bearing
cross-references are (they must appear as `SEE_ALSO` lines).

Use this table when assessing whether a transformed file is equivalent to its
prose source:

| Prose form | PDSL artifact | Preserved |
| --- | --- | --- |
| "If X, do Y." | `WHEN: X` + `DO: Y` | trigger condition + action |
| "Always X." / "Never X." | `RULES` (`MUST` / `MUST_NOT`) or `INVARIANTS` | universal quantification |
| "Ask user to pick A or B." | `MENU` with `OPTIONS` + `STOP_TURN` | UX surface + branch outcomes |
| "Stop and wait." | `WAIT` + `STOP_TURN` | turn boundary |
| "On error E, recover by R." | `ON_ERROR: E -> R` | typed recovery |
| "Because / for context: ..." | `NOTES` | rationale only (non-behavioral) |
| Cross-reference to another doc | `SEE_ALSO` line in executable block | dependency disclosure |

Transform equivalence does NOT require preserving:

- sentence order or paragraph structure
- explanatory rationale that has no effect on actions
- redundant restatements of the same rule

Transform equivalence FAILS if any of the following are missing from the PDSL
output:

- a `WHEN` or `ON_ERROR` for every if/when/unless condition in the prose
- a `STOP_TURN` for every prose "stop and wait" or hard turn boundary
- a `MENU` for every prose "ask the user to choose" interaction
- a `RULES` or `INVARIANTS` entry for every "always/never/must" statement
- a `SEE_ALSO` for every cross-reference in `NOTES` that carries load-bearing
  context

The authoritative preservation definition for the `transform` workflow is this
section. See also: `.bootstrap/.core/workflows/pdsl/transform.md`.

---

## Formal Grammar (informative BNF)

This grammar is **informative** for PDSL v0.1.x. It will be promoted to
normative from PDSL v0.2.

The grammar captures the conventions used across all converted files. When in
doubt, prefer the grammar over an example.

```ebnf
(* Top-level structure *)
file         ::= (prose | unit | menu | patterns)*
prose        ::= <any text outside declared blocks>

(* UNIT block *)
unit         ::= "UNIT" SP name NL unit-body
unit-body    ::= (purpose | input | output | state | when | do-block
                  | menu | rules | on-error | invariants | notes
                  | see-also)*

(* MENU block — may appear inside or outside a UNIT *)
menu         ::= "MENU" SP name ":" NL menu-body
menu-body    ::= title? options invalid?
title        ::= IND "TITLE:" SP text NL
options      ::= IND "OPTIONS:" NL option+
option       ::= IND IND opt-key SP "->" SP action NL
                 (IND IND IND action NL)*
invalid      ::= IND "INVALID:" NL (IND IND action NL)+

(* PATTERNS block *)
patterns     ::= "PATTERNS:" NL (IND pat-name ":" SP regex NL)+
pat-name     ::= name
regex        ::= <pattern string, interpreted as extended regex>

(* Common sub-blocks *)
purpose      ::= IND "PURPOSE:" NL (IND IND text NL)+
state        ::= IND "STATE:" NL state-var+
state-var    ::= IND IND name ":" SP values NL state-attr*
state-attr   ::= IND IND IND ("default:" | "reset:" | "scope:") SP text NL
when         ::= IND "WHEN:" NL condition+
condition    ::= IND IND expr NL
do-block     ::= IND "DO:" NL action+
action       ::= IND IND stmt NL
rules        ::= IND "RULES:" NL rule+
rule         ::= IND IND "-" SP ("MUST" | "MUST_NOT" | "ALWAYS") SP text NL
invariants   ::= IND "INVARIANTS:" NL rule+
on-error     ::= IND "ON_ERROR:" NL error-case+
error-case   ::= IND IND name SP "->" NL (IND IND IND action NL)+
notes        ::= IND "NOTES:" NL (IND IND text NL)+
see-also     ::= IND IND "SEE_ALSO:" SP ref NL
input        ::= IND "INPUT" NL (IND IND text NL)+
output       ::= IND "OUTPUT" NL (IND IND text NL)+

(* Expressions *)
expr         ::= term ((SP "AND" SP | SP "OR" SP) term)* | "NOT" SP term
term         ::= name SP "==" SP value
               | name SP "!=" SP value
               | "exists(" name ")"
               | "contains(" value "," SP token ")"
               | "matches(" value "," SP pat-name ")"

(* Terminals *)
name         ::= [A-Za-z_][A-Za-z0-9_]*
value        ::= name | quoted-string | "true" | "false" | "unset"
text         ::= <non-empty, non-blank line content>
ref          ::= name | path
path         ::= <relative or absolute file path>
opt-key      ::= [0-9]+ (SP name)?
stmt         ::= keyword (SP text)?
keyword      ::= "SET" | "EMIT" | "EMIT_MENU" | "WAIT" | "STOP_TURN"
               | "CONTINUE" | "DISPATCH" | "RETURN" | "FORBID"
               | "REQUIRE" | "LOAD" | "IF" | "ELSE"
SP           ::= " "+
NL           ::= "\n"
IND          ::= "  "   (* exactly 2 spaces; nesting adds multiples of 2 *)
```

Lexical rules:

- Keywords are **case-sensitive** and **uppercase**.
- Block headers (`UNIT`, `MENU`, `STATE`, `PATTERNS`, etc.) start at
  **column 0** (no leading whitespace).
- Block bodies are indented **exactly 2 spaces**. Each additional nesting
  level adds another 2 spaces. Tab characters are not permitted.
- Multi-action option bodies in `MENU` use **line-aligned continuation**
  under the `->` arrow (as shown in §Menus and §Example).
- One statement per line. No semicolons. No line-continuation characters.
- Comments are not part of the executable surface. Anything outside a
  declared block is treated as surrounding prose and does not create
  obligations.
- Blank lines between blocks are allowed and encouraged for readability.

---

## Adoption Guidance

Use PDSL first in files with high control-flow risk:

- phase gates
- approval prompts
- recovery menus
- state reset rules
- validation and review loops
- workflow handoffs

Do not rewrite stable narrative sections just to make them look algorithmic.
The value comes from reducing ambiguity in behavior, not from removing all
natural language.
