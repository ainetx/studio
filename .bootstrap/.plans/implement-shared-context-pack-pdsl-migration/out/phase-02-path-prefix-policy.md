# Phase 02 Path Prefix Policy

## Purpose

This document classifies prompt-asset path families, the controller-only load
surfaces that may read them from disk, and the runtime resource paths that
remain legal for ordinary task execution.

## Core Policy

- Prompt-consuming sub-agents must not use path references as self-bootstrap
  instructions for prompt assets.
- Controller surfaces that still perform prompt-asset loads must use runtime
  `{cf-studio-path}`-prefixed references when a runtime mirror exists.
- Canonical source paths may appear in specs or migration notes, but not as
  imperative prompt-load steps for prompt-consuming sub-agents.
- Non-prompt task resources remain ordinary runtime inputs and are outside the
  shared-context-pack prohibition set.

## Path Family Classification

| Path family | Classification | Allowed disk-loader roles | Consumer rule |
| --- | --- | --- | --- |
| `workflows/**/*.md` | Core prompt assets | Dispatching controller, dedicated prompt-pack builder, top-level runtime controller | Prompt-consuming sub-agents receive executable workflow text through `prompt_context_view`; they do not reopen workflow files. |
| `skills/studio/{SKILL.md,protocol.md,routing.md,sub-agent-dispatch.md,migrate-from-cypilot.md}` | Core prompt assets | Dispatching controller, dedicated prompt-pack builder, top-level runtime controller | Leaf prompt consumers must not open these files directly. |
| `skills/studio/agents/**/*.md` | Agent prompt assets | Dispatching controller, dedicated prompt-pack builder, top-level runtime controller | Agents do not self-bootstrap from sibling or parent prompt files. |
| `requirements/**/*.md` | Core prompt assets | Dispatching controller, dedicated prompt-pack builder, top-level runtime controller | Read from disk only to populate the pack; later consumers use semantic asset selection plus executable prompt slices. |
| Prompt-bearing `architecture/specs/**/*.md` | Core prompt assets when used as instructions | Dispatching controller, dedicated prompt-pack builder, top-level runtime controller | Specs may remain resource material when they are the analysis target, but they are prompt assets when loaded as agent instructions. |
| `AGENTS.md` and runtime AGENTS mirrors | Prompt assets | Dispatching controller, dedicated prompt-pack builder, top-level runtime controller | Prompt-consuming sub-agents must not open AGENTS surfaces directly. |
| Instruction-bearing runtime prompt surfaces under `{cf-studio-path}/.gen/**` | Runtime prompt assets when the generated file carries executable agent instructions | Top-level runtime controller, dispatching controller, dedicated prompt-pack builder | Treat generated runtime mirrors as prompt assets only when they deliver agent-operating instructions; leaf prompt consumers still receive the needed text through `prompt_context_view` rather than reopening generated files. |
| Instruction-bearing runtime prompt surfaces under `{cf-studio-path}/config/**` | Runtime prompt assets when the file carries executable agent instructions | Top-level runtime controller, dispatching controller, dedicated prompt-pack builder | Treat runtime config files as prompt assets only when they function as instructions, rules, checklists, sysprompts, or workflow contracts; registry/config data stays outside prompt-asset loading. |
| Mixed-content families under `{cf-studio-path}/.gen/**` or `{cf-studio-path}/config/**` | Content-and-usage classified | Dispatching controller, dedicated prompt-pack builder, or top-level runtime controller when extracting prompt-bearing sections; otherwise any contract that explicitly names them as task content | Do not classify these trees by path alone. When a file mixes instruction-bearing prompt text with non-prompt content, extract only the prompt-bearing sections into the session pack and treat the original file as a runtime resource for the remaining content. |
| Kit prompt assets under `{cf-studio-path}/config/kits/**` | Kit prompt assets | Top-level runtime controller, dispatching controller, dedicated prompt-pack builder | Kits enter the session pack as first-class assets with `origin = "kit"`; leaf agents do not read kit prompt files directly. |
| `.github/prompts/**/*.md` | Project prompt assets | Top-level runtime controller, dispatching controller, dedicated prompt-pack builder | These prompt bodies may be loaded only to populate the session pack and executable `prompt_context_view`; prompt-consuming sub-agents must not reopen them. |
| `.claude/agents/**/*.md` | Project prompt assets | Top-level runtime controller, dispatching controller, dedicated prompt-pack builder | Controller-owned mirrors only; leaf consumers must receive the needed text through `prompt_context_view`. |
| `.claude/skills/**/SKILL.md` | Project prompt assets | Top-level runtime controller, dispatching controller, dedicated prompt-pack builder | Treat as project prompt surfaces when used as instructions; prompt-consuming sub-agents must not self-load them. |
| `.cursor/agents/**/*.md` | Project prompt assets | Top-level runtime controller, dispatching controller, dedicated prompt-pack builder | Controller-owned mirrors only; leaf consumers must receive the needed text through `prompt_context_view`. |
| `.cursor/commands/**/*.md` | Project prompt assets | Top-level runtime controller, dispatching controller, dedicated prompt-pack builder | Command prompt surfaces are controller-loaded only and become executable view content, not self-bootstrap paths. |
| `.codex/agents/**` | Project prompt assets when the file instructs agent behavior | Top-level runtime controller, dispatching controller, dedicated prompt-pack builder | Treat instruction-bearing Codex agent surfaces as project prompt assets regardless of extension; load only for controller-owned extraction into executable `prompt_context_view`, and do not let prompt-consuming sub-agents reopen them. |
| `skills/studio/agents.toml` | Registry metadata, not a prompt asset | Any workflow that needs registry metadata | Safe to read as metadata, but not a prompt body and not a substitute for `prompt_context_view`. |
| `.bootstrap/.plans/**/out/*.md` | Content-and-usage classified: prompt asset when later phases follow the file as an instruction contract; runtime task resource otherwise | Dispatching controller, dedicated prompt-pack builder, or top-level runtime controller when the file is an instruction asset; otherwise any contract that explicitly names it as task content | Do not classify these files by path alone. Controller roles may load instruction-bearing out-phase docs into the session pack, but ordinary consumers may read them directly only when they are task resources rather than prompt surfaces. |
| Source code, target docs, artifacts under review, manifests, diffs | Runtime task resources | Any contract that explicitly names them | These remain ordinary task inputs outside the shared context pack. |

## Prefix Normalization Rules

### When A Runtime Mirror Exists

- Use `{cf-studio-path}/.core/...` for mirrored core prompt assets loaded by a
  controller at runtime.
- Use `{cf-studio-path}/config/...` or `{cf-studio-path}/.gen/...` only for
  runtime surfaces that are first classified by content and usage as
  instruction-bearing prompt assets.
- Use `{cf-studio-path}/config/kits/...` for runtime kit prompt assets.
- Use project-local families such as `.github/prompts/**`, `.claude/agents/**`,
  `.claude/skills/**`, `.cursor/agents/**`, `.cursor/commands/**`, and
  `.codex/agents/**` only from controller-owned loader paths. These surfaces
  may populate the pack and `prompt_context_view`, but they are never legal
  self-bootstrap paths for prompt-consuming sub-agents.
- For mixed trees under `{cf-studio-path}/config/**` or `{cf-studio-path}/.gen/**`,
  classify each file by content and usage; when prompt and non-prompt material
  coexist, extract only the instruction-bearing sections for the session pack
  and leave the remaining content in ordinary runtime resource handling.
- For `.bootstrap/.plans/**/out/*.md`, first classify by content and usage. If
  the file is serving as a later-phase instruction contract, treat it like any
  other prompt surface and route it through controller-owned loading into the
  session pack; if it is serving as task content, leave it in ordinary runtime
  inputs.

### When No Runtime Mirror Exists

- A canonical source path may be named in documentation, inventories, or
  planning artifacts.
- A prompt-consuming contract still may not use that source path as an
  imperative file-open instruction.
- If a controller truly needs that prompt asset at runtime, later migration
  phases should either introduce the correct runtime mirror or route the load
  through an existing controller-safe path.

## Explicit Exceptions

The following exception class is allowed:

- controller-owned prompt discovery and pack construction
- controller-owned extraction of executable prompt text from project-local
  prompt surfaces into `prompt_context_view`
- controller-owned `etag` revalidation plus refresh/replacement of reused
  session-pack assets before prompt-context-view derivation

The following exception classes are not allowed:

- leaf agents reading prompt assets because the controller omitted them
- read-only reviewer agents reopening prompt files to compensate for missing
  prompt context
- write-capable agents treating write permission as prompt-loader permission
