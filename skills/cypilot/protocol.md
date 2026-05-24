---
description: "Invoke when loading Cyber Constructor Protocol Guard, CLI resolution, logging, language, and write-confirmation rules."
---

# Cyber Constructor Protocol

Run CLI resolution before workflow work: prefer `cfc`; otherwise use
`python3 {cf-constructor-path}/.core/skills/cypilot/scripts/cypilot.py`.
ALWAYS use `{cfc_cmd}` for later CLI invocations.

ALWAYS provide execution visibility with `- [CONTEXT]: MESSAGE` when entering
Cyber Constructor prompt sections and completing checklist tasks.

Protocol Guard:
1. Run `{cfc_cmd} --json info`.
2. Store the returned `variables` map.
3. Open and follow `{cf-constructor-path}/.gen/AGENTS.md` when present.
4. Open and follow `{cf-constructor-path}/config/AGENTS.md` when present.
5. Open and follow `{cf-constructor-path}/.gen/SKILL.md` when present.
6. Open and follow `{cf-constructor-path}/config/SKILL.md` when present.
7. Resolve registry, intent, target, rules, and matched WHEN-clause specs.
8. Open and follow `{cf-constructor-path}/.core/requirements/language-complexity.md`.

Before code edits include:
```text
Cyber Constructor Context:
- Cyber Constructor: {path}
- Target: {artifact|codebase}
- Specs loaded: {list paths or "none required"}
```

Agent-safe invocation: use `{cfc_cmd} --json <subcommand>` except `init`,
`delegate`, and `update`, which run without `--json`. Obtain explicit user
confirmation before any write-capable command, and do not add `--yes`, `-y`,
or `--force` unless the user explicitly requested it. Phase-Skip Gate (SKILL.md) MUST be in a released_for_* state AND the write-confirmation MUST be obtained from the user before any write-capable command runs. Gate-release does not replace the confirmation step; both are required.
