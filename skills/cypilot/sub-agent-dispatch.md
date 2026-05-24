---
description: "Invoke when about to dispatch a cf-constructor-* sub-agent — applies dispatch protocol and selects Mode A (native) or Mode B (inline)."
---

# Sub-Agent Dispatch

Workflows reference named `cf-constructor-*` sub-agents. Each contract lives in
`{cf-constructor-path}/.core/skills/cypilot/agents/<name>.md`.

Mode A: when native dispatch is approved for this session, dispatch the named
agent and consume its declared output. Pass approval state in the dispatch
context; sub-agents loading `SKILL.md` do not ask the session approval prompt
unless they will dispatch another `cf-constructor-*` sub-agent.

Mode B: when the user explicitly declined native dispatch for this workflow or
the host has no native sub-agent support, inline the named agent contract:
open and follow the agent file, substitute dispatch inputs, satisfy its
Response Completion Gate, and return the declared output shape. If the named agent file has no explicit Response Completion Gate section, apply the default completion criterion: return the full declared output shape with no required field empty or null.

Pre-dispatch discipline:
- First apply the Session Sub-Agent Approval Gate in `SKILL.md`.
- Probe once per workflow run.
- Never switch modes silently mid-workflow. If a mid-workflow re-probe (triggered by an external-entry handoff or unset INLINE_FALLBACK at a dispatch site) yields a different result from the prior probe (Mode A → Mode B or vice versa), the orchestrator MUST surface the change to the user before continuing.
- If a dispatch site finds `INLINE_FALLBACK` unset, stop and run
  `workflows/shared/inline-fallback-probe.md`.

When `INLINE_FALLBACK=true`, the orchestrator MUST warn the user before entering
any of these high-risk dispatch contexts (brainstorm fan-out, long review loops,
generate-author writes, deterministic-validator subprocess context). The warning
MUST state which guarantees are reduced: parallelism, context isolation,
subprocess separation. Workflows specify the exact warning text inline at the
dispatch site; if no inline text is provided, use this canonical wording:
"Inline-fallback mode active — isolation, parallelism, and subprocess separation
guarantees are reduced for this dispatch. Continue? [y/n]"

If the user replies "n" (or any non-affirmative), abort the dispatch and offer the user the choice of (a) retry with inline-fallback acknowledged, (b) switch back to the parent workflow's plan-escalation menu, or (c) stop. Do not silently continue.
