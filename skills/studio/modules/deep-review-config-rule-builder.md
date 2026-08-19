# Deep Review Config Rule Builder

This plain Markdown module defines the interactive rule-selection contract for `cf-deep-review-config`. It operates on rule candidates from project discovery, existing-plan mining, post-mortem findings, or user-authored rules, and produces a deterministic project review config.

It never writes the config until the user finalizes the rule set.

## Candidate rule schema

```json
{
  "batch": 1,
  "number": 1,
  "fingerprint": "normalized semantic key",
  "id": "tenant-scoped-orm",
  "condition": { "source": "path", "regexp": "(?i)(secureorm|tenant|accessscope)" },
  "prompt": "Verify tenant scoping, authorization parity, fail-closed behavior, and policy propagation.",
  "category": "security",
  "provenance": {
    "kind": "llm-suggestion|user-custom|plan-pattern|finding-pattern|reverse-engineering",
    "source": "project path pattern",
    "evidence": "src/auth/secureorm.rs:40, src/tenant/scope.rs:12"
  }
}
```

`condition` is either the string `always` or an object with `source` and `regexp`.

## Candidate batch rules

- Generate ten rule candidates when ten distinct useful candidates remain.
- Use only the active source (manual, discover, plans, postmortem) and compact prior state.
- Avoid exact and semantic duplicates across proposed, selected, rejected, removed, and custom rules.
- Each candidate must be grounded: show the file/path pattern, plan item, or finding evidence that motivated it.
- Avoid generic boilerplate; prefer project-specific patterns discovered via reverse engineering.
- Later batches prioritize categories and sources not yet covered by selected rules.
- When fewer than ten distinct useful candidates remain, show the smaller batch and explain why.
- Candidate generation never writes files or executes commands.

## Review category pool

Use the same categories as `cf-deep-review` plus a `conventions` category:

- functional correctness and invariants;
- architecture and component boundaries;
- errors, retries, idempotency, deadlines, cancellation;
- security, authorization, tenancy, privacy, safety;
- concurrency, state, consistency, transactions;
- data, schema, migration, versioning, compatibility;
- performance, capacity, resource bounds, abuse resistance;
- lifecycle, recovery, operations, observability;
- API, SDK, protocol, dependency and integration contracts;
- tests, evidence, CI, traceability, documentation consistency;
- conventions, naming, project structure.

## Batch rendering

```text
Batch 1 — proposed review rules

1. tenant-scoped-orm
   Condition: path matches (?i)(secureorm|tenant|accessscope)
   Prompt: Verify tenant scoping, authorization parity, fail-closed behavior, and policy propagation.
   Category: security
   Evidence: src/auth/secureorm.rs:40, src/tenant/scope.rs:12

...

Selected rules: 2

Propose 10 more rules? Reply `yes` or `no`.

Other commands remain available by name:
- `add: id=... condition=... prompt="..." category=...`
- `remove: <rule id>`
- `show`
- `reset-batch`
- `done`
- `cancel`
```

Keep each candidate concise enough for terminal use.

## Selection command grammar

```text
selection      = numbers | all | more | add | remove | show | reset-batch | done | cancel
numbers        = number { separator number }
separator      = space | comma
all            = "all"
more           = "more" | "yes"
add            = "add:" rule-fields
remove         = "remove:" id { separator id }
show           = "show"
reset-batch    = "reset-batch"
done           = "done" | "no"
cancel         = "cancel"

rule-fields    = field { separator field }
field          = id=<id> | condition=<condition> | prompt="<text>" | category=<category>
condition      = "always" | <source>:<regexp>
source         = title | body | path | diff | any
```

## Add rule grammar

`add:` accepts a compact rule. Examples:

```text
add: id=tenant-scope condition=path:(?i)(tenant|accessscope) prompt="Verify tenant isolation." category=security
add: id=quality condition=always prompt="Verify public contract correctness." category=correctness
```

Missing fields are asked for before the rule is accepted. The system validates the rule against the schema and rejects duplicates.

## Selection behavior

### Numbers

- Accept `1 2 7 4`, `1,2,7,4`, or mixed spaces/commas.
- Selection order follows the user's order.
- Ignore duplicate numbers.
- Keep valid selections when some numbers are invalid and report the invalid values.
- Reject numbers outside the current batch without changing prior selections.

### All

- Select every still-unselected candidate in the current batch in ascending displayed-number order.
- Do not affect rules selected from prior batches.
- Mark unselected candidates in the current batch as rejected for duplicate prevention.

### More

- Mark unselected canonical current-batch candidates as rejected.
- Clear `RULE_BUILDER_STATE.current_batch` and generate the next batch.
- If the source has no more candidates, say so and remain in the more-checks view.

### Add

- Parse fields from the text after `add:`.
- Convert any bare condition such as `always` or `path:(?i)foo` into the canonical condition form.
- Ask for missing fields one at a time.
- Validate the rule: unique id, valid regex, known source, non-empty prompt and category.
- Add it to `RULE_BUILDER_STATE.selected_rules` with provenance `user-custom`.
- Return to the more-checks view.

### Remove

- Remove a selected or custom rule by id.
- Reject removal of rules that came from the existing config and have not been modified; they can be retired only by writing a new config version without them.
- Report invalid ids.

### Show

Show the current selected rule table: id, condition, category, prompt.

### Reset batch

Remove only selections made from the current batch. Preserve prior batches and custom rules. Retain the same current batch for redisplay.

### Done

- If selected rules exist, mark unselected current-batch candidates rejected, clear the current batch, and proceed to write the config.
- If no rule is selected and a config already exists, ask whether to keep the existing config unchanged.
- If no rule is selected and no config exists, ask the user to add at least one rule or cancel.

### Cancel

Return cancelled without writing any file.

## More-checks gate

After a successful numeric/all selection, custom addition, or removal, show:

```text
Selected rules: 7

Propose 10 more rules? Reply `yes` or `no`.

Other commands remain available by name:
- `add: id=... condition=... prompt="..." category=...`
- `remove: <rule id>`
- `show`
- `reset-batch`
- `done`
- `cancel`
```

Bare numeric input is rejected in this view.

## Canonical builder actions

| Input result | BUILDER_ACTION | Next view |
|---|---|---|
| valid numbers/all | `selected` | more |
| more/yes | `generate-batch` | batch |
| add succeeds | `custom-added` | more |
| remove succeeds | `removed` | more |
| show | `shown` | more |
| reset-batch | `batch-reset` | same batch |
| done with selected rules | `finalize` | write config |
| done empty with existing config | `finalize-unchanged` | show config / menu |
| done empty without config | `needs-rules` | batch (or manual prompt) |
| invalid command | `correction` | preserve current view |
| cancel | `cancel` | terminal |

## Compact builder state

```json
{
  "batch_number": 1,
  "current_batch": [],
  "selected_rules": [],
  "custom_rules": [],
  "proposed_fingerprints": [],
  "rejected_fingerprints": [],
  "covered_categories": [],
  "source": "manual|discover|plans|postmortem"
}
```

`RULE_BUILDER_STATE.current_batch` is the single canonical batch state. Only this compact state is carried between turns.

## Config handoff

When the user finishes selection, the writer receives:

- selected rules in the order they were added/selected;
- custom rules with provenance;
- rejected/proposed fingerprints for history;
- target project identity and canonical config path.

Every written rule must have `required = true`.
