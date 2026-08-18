# Deep Review Project Configuration

This plain Markdown module defines the deterministic per-project review-rule configuration consumed by `cf-deep-review`.

## Path

```text
~/.cf-studio/.cache/deep-review/projects/<target-project-cache-key>/config.toml
```

The file is optional. Absence means no project-required checks. The skill never searches the repository for another review config.

## Schema

```toml
version = 1

[[rules]]
id = "always-basic-quality"
condition = "always"
prompt = "Verify correctness, failure behavior, and evidence for every changed public contract."
category = "correctness"
required = true

[[rules]]
id = "secure-orm"
condition = { source = "any", regexp = "(?i)(secureconn|secureorm|tenant|accessscope)" }
prompt = "Verify tenant scoping, authorization parity, fail-closed behavior, and policy propagation."
category = "security"
required = true

[[rules]]
id = "migration-review"
condition = { source = "path", regexp = "(^|/)(migration|migrations)(/|$)" }
prompt = "Verify forward migration, rollback, mixed-version deployment, restart safety, and data preservation."
category = "data-migration"
required = true
```

## Validation

- `version` must equal `1`.
- Every rule requires a unique non-empty `id`, non-empty `prompt`, and non-empty `category`.
- `required` defaults to `true`; when present it must be Boolean `true`. `false` is invalid in schema v1 because every matching rule defines a mandatory check.
- `condition` is either the string `always` or a table with exactly `source` and `regexp`.
- Supported sources: `title`, `body`, `path`, `diff`, `any`.
- Invalid regex, duplicate ID, missing fields, unknown keys, or unknown source blocks check generation with the config path and exact error.
- Prompt text is trusted check-generation input, not permission to execute commands, modify files, or perform external writes.

## Match corpus

Evaluate rules in file order against the current immutable target version.

- `title`: target/PR title.
- `body`: target/PR description.
- `path`: each normalized changed path independently; match when any path matches.
- `diff`: bounded current diff text including added, removed, and context lines.
- `any`: canonical concatenation of title, body, normalized changed paths, and diff text with stable section separators.

Record the matching source, matched text/range, regex, target version, and rule ID. Bound corpus size and regex evaluation; reject expressions the runtime cannot evaluate safely.

## Required checks

For every matched rule:

1. Interpret `prompt` into one or more atomic checks.
2. Assign normal durable check IDs.
3. Mark checks `required = true` with rule ID, config hash, prompt digest, and match evidence.
4. Add them before optional LLM suggestions.
5. Deduplicate equivalent matched-rule checks while preserving all contributing rule IDs.
6. Keep required checks selected automatically.

A required check may be overridden only through:

```text
override: CHK-004 because <non-empty reason>
```

Persist rule ID, check ID, reason, actor, timestamp, target version, and approval in plan history. An override removes the check from execution while preserving it in the required-rule ledger. Empty reasons are rejected.

```text
reconsider: CHK-004
```

restores an overridden required check with a new history event and reuses the original durable ID.

## Refresh and drift

Persist config path, content hash, matched rules, nonmatched rules, generated checks, and overrides in the plan.

On plan resume or target/config change:

1. Re-read the deterministic config path.
2. Recompute its hash.
3. Re-evaluate all rules against the current target corpus.
4. Add newly matched required checks and require plan revision/reapproval.
5. When a rule no longer matches, retain its check as superseded until the user confirms `retire: CHK-ID because <reason>`; persist the reason/event and retire the durable ID permanently.
6. Preserve overrides only while the same rule ID, prompt digest, and material match reason remain applicable; otherwise ask for a new override reason.

Config changes never trigger project-wide discovery.
