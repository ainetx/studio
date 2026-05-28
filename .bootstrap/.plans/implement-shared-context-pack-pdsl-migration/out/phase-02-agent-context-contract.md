# Phase 02 Agent Context Contract

## Purpose

This document defines the target contract for shared-context-pack-aware
controllers and prompt-consuming sub-agents.

## Roles

| Role | May load prompt assets from disk | Required behavior |
| --- | --- | --- |
| Dispatching controller | Yes | Resolve task context, reuse or extend the session pack, revalidate candidate reused assets by `etag`, refresh stale assets before selection, derive one `prompt_context_view` per dispatch, and block dispatch on missing required prompt context. |
| Dedicated shared-context-pack builder | Yes, but only on behalf of a dispatching controller or explicitly designated top-level runtime controller | Load only the prompt assets delegated by that controller, classify them by content and usage, compute `etag`, and return them for insertion or replacement in the session pack. |
| Top-level runtime controller | Yes | Perform bootstrap/config/runtime prompt discovery, reuse or extend the session pack, revalidate reused prompt assets, and hand the resulting assets to the dispatching controller without granting prompt-loader authority to leaf consumers. |
| Prompt-consuming sub-agent | No | Consume prompt instructions only from `prompt_context_view`, read task resources only when its task contract names them, and fail closed when required prompt context is absent. |

No other role is allowed to discover or reload prompt assets from disk.

## Required Agent Declaration

Every prompt-consuming sub-agent must declare
`prompt_context_requirements` semantically rather than as file-open steps.

Minimum contract:

```json
{
  "prompt_context_requirements": {
    "requires_shared_context_pack": true,
    "required_assets": [
      {
        "asset_key": "<semantic name>",
        "accepted_origins": ["core", "kit", "project"],
        "accepted_types": ["workflow", "skill", "requirement", "checklist", "rule", "system", "instruction"],
        "match_tags": ["<tag>", "..."],
        "section_tags": ["<tag>", "..."],
        "required_when": "<condition or null>"
      }
    ],
    "optional_assets": []
  }
}
```

Required rules:

- `requires_shared_context_pack` must be `true` for any prompt-consuming
  sub-agent.
- `required_assets` must cover every prompt asset class needed to execute the
  contract safely.
- `optional_assets` may be used for kit-provided or mode-specific prompt
  additions, but they do not weaken required assets.
- Declarations must describe prompt needs semantically; they must not say
  "open file X before acting."

## Required Prompt Context View Behavior

Before dispatch, the dispatching controller must provide:

```json
{
  "prompt_context_view": {
    "agent_id": "<string>",
    "assets": [
      {
        "asset_id": "<stable asset id>",
        "asset_type": "<workflow|skill|requirement|checklist|rule|system|instruction>",
        "origin": "<core|kit|project>",
        "kit_id": "<string|null>",
        "path": "<source path recorded for provenance>",
        "etag": "<deterministic freshness token>",
        "tags": ["<tag>", "..."],
        "body": "<full prompt text used when the whole asset is selected>",
        "sections": [
          {
            "section_id": "<stable section id>",
            "title": "<section title>",
            "tags": ["<tag>", "..."],
            "body": "<section text supplied to the agent>"
          }
        ]
      }
    ],
    "asset_refs": [
      {
        "asset_id": "<stable asset id>",
        "section_ids": ["<section id>", "..."]
      }
    ]
  }
}
```

Rules:

- The view must satisfy every required asset declaration before dispatch.
- The view must contain only the prompt assets needed for that sub-agent and
  task.
- Each delivered asset must preserve provenance metadata from the session
  pack, including `asset_id`, `origin`, `kit_id`, `path`, `etag`, and
  applicable asset/section tags.
- The view must include executable prompt text, either as whole-asset `body`
  content or as populated `sections[].body` slices. Opaque references alone are
  not sufficient.
- The sub-agent must treat `prompt_context_view` as its sole prompt and
  instruction source.
- The sub-agent may still read non-prompt task resources explicitly named by
  its task contract.
- `asset_refs` remain an audit/provenance index. They do not replace the
  executable prompt text carried in `assets`.
- A controller may pass whole assets or section-scoped slices, but the
  selection must be deterministic, executable, and auditable.

## Controller Responsibilities

Controllers that dispatch prompt-consuming sub-agents must:

1. Determine the current dispatch context, including methodology, target type,
   active rules/mode inputs, and active kit context.
2. Reuse the existing session `SHARED_CONTEXT_PACK` before discovering new
   prompt assets.
3. Revalidate by `etag` every candidate reused asset needed for the current
   dispatch.
4. Refresh or replace any asset found stale before it may contribute to
   `prompt_context_view`.
5. Load only the missing prompt assets required to satisfy declared semantic
   needs.
6. Preserve `origin`, `kit_id`, `asset_type`, tags, and `etag` metadata.
7. Build the smallest valid `prompt_context_view` for each dispatch, including
   executable prompt text slices and provenance.
8. Stop dispatch if any required prompt asset remains unresolved.

## Deterministic Failure Semantics

Missing prompt context must fail closed.

Required failure behavior:

- Do not dispatch the sub-agent when a required prompt asset is missing.
- Do not silently degrade to direct prompt-file reads.
- Report the missing semantic asset key or missing resolved asset id.
- Report which controller role attempted the dispatch.
- Preserve checkpoint or partial-return semantics when the surrounding
  workflow/agent contract already uses them.

Accepted failure forms:

- pre-dispatch validation failure returned to the controller
- partial/checkpoint return with unresolved prompt-context details
- dispatching-controller-owned repair prompt or recovery branch

Forbidden failure form:

- letting the sub-agent open `SKILL.md`, workflow files, requirement files,
  specs, `AGENTS.md`, sysprompts, generated out-phase instruction contracts, or
  kit prompt files on its own

## Migration Notes For Later Phases

- `agents.toml` should become the durable home for prompt-context declarations
  or references to them.
- Project-local prompt surfaces, including instruction-bearing
  `.codex/agents/**` files of any extension, remain controller-loaded prompt
  assets when used as instructions; registry metadata stays outside the prompt
  pack unless it embeds executable prompt text.
- Agents that currently forbid `SKILL.md` reads but still read controller
  references, such as plan-specialized contracts, need explicit
  content-and-usage classification plus controller or minimal-context decisions
  in their migration phase.
- Review-only agents and write-capable agents follow the same prompt-context
  loading rule; write authority does not imply prompt-loader authority.
