---
cf-constructor: true
type: workflow-phase
name: plan-phase-1-assess
description: "Invoke when /cf-constructor-plan enters Phase 1 to assess task scope: identify task type, extract navigation rules, estimate compiled size, scan for interaction points, and identify the target artifact."
loaded_by: workflows/plan.md
version: 1.0
---

# Phase 1: Assess Scope

## 1.1 Identify Task Type

| Signal | Task Type | Target Workflow |
|--------|-----------|----------------|
| `create` / `generate` / `write` / `update` / `draft` + artifact kind | `generate` | `generate.md` |
| `validate` / `review` / `check` / `audit` / `analyze` + artifact kind | `analyze` | `analyze.md` |
| `implement` / `code` / `build` / `develop` + feature name | `implement` | `generate.md` (code mode) |

## 1.1b Extract Target Workflow Navigation Rules (CRITICAL)

Open `{cf-constructor-path}/.core/workflows/{target_workflow}` and: scan all navigation directives, list referenced files + `WHEN` conditions, evaluate them, open every applicable file, extract only the sections/ranges needed for plan generation, and record a loaded-file manifest with `path`, `reason`, `sections/ranges`, and `line_count`.

Report:
```text
Context loaded for plan generation:
  Workflow: {target_workflow} ({N} navigation rules processed)
  Files inspected: {M} files
  Loaded manifest: {path — sections/ranges — reason}
  Total retained context: ~{L} lines
  All navigation rules processed? [YES/NO]
```
**Gate**: do NOT proceed until ALL applicable navigation rules are processed, every required file referenced by navigation rules has been opened, and every retained slice needed for planning is captured in the manifest.

## 1.2 Estimate Compiled Size

Estimate `template_lines + rules_lines + checklist_lines + existing_content_lines`.

1. If oversized raw input already has an approved or reusable plan package, remain on the plan path even when the compiled estimate is `≤ 500`.
2. Otherwise, if the estimate is `≤ 500`, continue to Phase 1.4 so `{task-slug}` can be resolved before checking for any existing authoritative raw-input package.
3. If the estimate is `> 500`, continue planning.

## 1.3 Scan for User Interaction Points (CRITICAL)

> **⛔ MANDATORY**: Missing interaction points is the #2 source of plan failures after missing rules.

Recursively scan the target workflow, `rules.md`, `checklist.md`, `template.md`, and every applicable navigation-linked file for:

- `question`: `ask the user`, `ask user`, `what is`, `which`, trailing `?`
- `input`: `user provides`, `user specifies`, `user enters`, `input from user`
- `confirm`: `wait for`, `confirm`, `approval`, `before proceeding`
- `review`: `review`, `present for`, `show to user`, `user inspects`
- `decision`: `choose`, `select`, `option A or B`, `decide`

Collect findings, classify each as **Pre-resolvable**, **Phase-bound**, or **Cross-phase**, ask all pre-resolvable and cross-phase questions now, record answers in a `decisions` block, then verify:
```text
Interaction points scan complete:
  Files scanned: {N}
  Interaction points found: {M}
    - Pre-resolvable: {count}
    - Phase-bound: {count}
    - Cross-phase: {count}
  All source files scanned? [YES/NO]
  All interaction points classified? [YES/NO]
```
**Gate**: do NOT proceed if any source file was not scanned or any interaction point remains unclassified. If zero are found, report `No interaction points detected — task is fully autonomous` and omit User Decisions from phase files.

## 1.4 Identify Target

Resolve generate/analyze → artifact kind, file path, and kit; implement → FEATURE spec path and CDSL blocks. Also compute `plan.target_key`, the canonical target identity used for deterministic plan-directory naming and reuse:
- generate artifact target: prefer the single resolved output artifact path as `artifact-path:{absolute path}`; otherwise use `artifact:{artifact kind}:{explicit artifact name}`
- analyze path target: use `path:{absolute path}` for the primary file/directory target; analyze artifact target follows the generate artifact-target rule
- implement target: prefer `feature-path:{absolute FEATURE path}`; otherwise `feature-id:{FEATURE ID}`; otherwise `feature-title:{normalized FEATURE title}`

Also compute `plan.input_signature`, the canonical raw-input identity derived from the current direct prompt text plus every provided file path/content pair. The signature is derived exclusively from each source's kind, path, and content hash — presentation-only metadata such as stdin display labels are excluded so that relabeling does not break reuse. To obtain the signature without writing any files, run:
  `{cfc_cmd} --json chunk-input ... --output-dir {cf-constructor-path}/.plans/{task-slug}/input --dry-run`
  (add `--include-stdin` when direct prompt text must be included).
This signature is authoritative for raw-input package reuse; `plan.target_key` is not sufficient when the raw task input changes.

Then report:
```text
Plan scope:
  Type: {generate|analyze|implement}
  Target: {artifact kind or feature name}
  Target key: {canonical target identity}
  Input signature: {sha256 of direct prompt + provided file contents}
  Estimated size: ~{N} lines
```
After target identification, compute `{task-slug}` immediately for deterministic plan-directory naming and reuse.

If `{cf-constructor-path}/.plans/{task-slug}/input/manifest.json` already exists, read its `input_signature` and compare it to the `input_signature` returned by the `--dry-run` invocation above. If they match exactly, remain on the plan path and reuse that authoritative raw-input package even when the compiled estimate is `≤ 500`.

Otherwise, if the compiled estimate is `≤ 500` and oversized raw input does not already have an approved or reusable plan package, STOP and direct the user to `/cf-constructor-generate` or `/cf-constructor-analyze`.

If the direct prompt text plus all provided files exceeds `500` total lines and no authoritative raw-input package with the same `plan.input_signature` exists yet, present:
```text
Oversized raw input detected (~{N} lines total).
Preparing the plan will write chunk files under {cf-constructor-path}/.plans/{task-slug}/input/ by running:
  {cfc_cmd} --json chunk-input ... --output-dir {cf-constructor-path}/.plans/{task-slug}/input --max-lines 300 --threshold-lines 500
  Add --include-stdin when direct prompt text must be packaged together with provided files.
  The command also writes {cf-constructor-path}/.plans/{task-slug}/input/manifest.json with `input_signature` and only replaces the existing package after the full replacement package is staged successfully.
Proceed with raw-input materialization? [y/n]
Reply with `y` or `n`.
`y` → Suggested when you want full plan guarantees; materialize the raw-input package and continue planning from chunk files.
`n` → Stop here without writing the raw-input package.
```
Wait for explicit user confirmation before creating `{cf-constructor-path}/.plans/{task-slug}/input/` or executing `chunk-input` (without `--dry-run`). If the user approves (`y`), materialize the raw input there, record the emitted chunk paths plus `manifest.json`, and stop carrying the full raw input in active chat context once the package exists. If the user rejects (`n`), do not create any files or directories, report `Raw-input materialization declined — continue with direct workflow if you prefer reduced guarantees`, and stop. This is a valid completion state for `/cf-constructor-plan`.
