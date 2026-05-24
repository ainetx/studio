---
cf-constructor: true
type: workflow
name: cf-constructor-plan
description: Invoke when the user asks to plan, create a plan, decompose, break down, or organize a large or multi-step task into phases — produces self-contained phase files with brief + compiled forms.
version: 1.0
purpose: Universal workflow for generating execution plans with phased delivery
---

# Plan

<!-- toc -->

- [Overview](#overview)
- [Context Budget & Overflow Prevention (CRITICAL)](#context-budget--overflow-prevention-critical)
- [Phase 0: Resolve Variables & Discover Tools](#phase-0-resolve-variables--discover-tools)
- [Phase 1: Assess Scope](#phase-1-assess-scope)
- [Phase 2: Decompose](#phase-2-decompose)
- [Phase 3: Compile Phase Files](#phase-3-compile-phase-files)
- [Phase 4: Finalize Plan](#phase-4-finalize-plan)
- [Plan Lifecycle](#plan-lifecycle)
- [Plan Reference](#plan-reference)

<!-- /toc -->

> **⛔ CRITICAL CONSTRAINT**: This workflow ONLY generates execution plans and related handoff artifacts. It NEVER executes the underlying task (generate, analyze, implement) directly. Even if the task seems small, this workflow's job is to produce phase files — not to do the work itself. If the task is small enough for direct execution, tell the user to use `/cf-constructor-generate` or `/cf-constructor-analyze` instead. The reference appendices below define the runtime contract that generated plans MUST support; they are not steps performed by this workflow.
> **⛔ CRITICAL CONSTRAINT — COMPLETE COVERAGE, COMPACT LOADING**: Before generating ANY plan, you MUST discover and process ALL navigation rules (`ALWAYS open`, `OPEN and follow`, `ALWAYS open and follow`) from the **target workflow** (generate.md, analyze.md, or the relevant workflow). Every applicable file referenced by those directives MUST be opened at least once, but you MUST retain only the specific sections/ranges needed for decomposition, interaction extraction, and compilation. Completeness is proven by a loaded-file manifest with paths and sections/ranges, not by keeping every dependency fully resident in context. Skipping ANY navigation rule still produces incomplete context and broken plans. This is the #1 source of plan quality failures.
> **⛔ CRITICAL CONSTRAINT — KIT RULES ARE LAW** *(highest priority)*: Every rule in the kit's `rules.md` for the target artifact kind MUST be enforced in the generated plan — **completely, without omission or summarization**. Rules are inlined verbatim into phase files. If the full rules don't fit in a single phase, split the phase so each sub-phase gets ALL rules relevant to its scope — but NEVER trim, summarize, or selectively skip rules to fit a budget. The `checklist.md` items are equally mandatory for analyze tasks. A plan that drops kit rules produces artifacts that fail validation.
> **⛔ CRITICAL CONSTRAINT — DETERMINISTIC FIRST**: Every phase step that CAN be done by a deterministic tool (`{cfc_cmd}` subcommand, script, shell command) MUST use that tool instead of LLM reasoning. Discover available tools dynamically in Phase 0 — do NOT assume a fixed set of commands. Tool capabilities change between versions. The CLISPEC file is the source of truth for what commands exist and what they can do.
> **⛔ CRITICAL CONSTRAINT — INTERACTIVE QUESTIONS COMPLETENESS** *(mandatory)*: You MUST find ALL interactive questions, user input requests, confirmation gates, review requests, and decision points from: (1) the target workflow, (2) `rules.md` for the target artifact kind, (3) `checklist.md`, (4) `template.md`, AND (5) **every file referenced by navigation rules** (`ALWAYS open`, `OPEN and follow`) in those files — recursively. Every interaction point found MUST appear in the compiled plan: pre-resolvable questions asked BEFORE plan generation, phase-bound questions embedded in phase files. Inspect every applicable dependency, record the source path plus section/range for each interaction point, and carry forward only the extracted interaction data needed by later phases. **Missing even ONE interaction point = plan is INVALID.** Open, load, and follow `{cf-constructor-path}/.core/requirements/plan-checklist.md` Section 2 for the complete extraction procedure.
> **⛔ CRITICAL CONSTRAINT — BRIEF BEFORE COMPILE**: Phase files MUST NOT be written directly. Every phase file MUST be compiled from a corresponding compilation brief (`brief-{NN}-{slug}.md`) that was written to disk in Phase 3.2. The brief is the contract between decomposition (what to include) and compilation (how to assemble). Skipping briefs produces phase files that silently omit kit content, miss load instructions, or inline wrong sections. **If you find yourself writing a phase file without first reading its brief from disk — STOP, you are violating the workflow.** Write the brief first, write it to disk, THEN compile from it. A phase file without a corresponding brief file on disk = INVALID plan.

ALWAYS open and follow `{cf-constructor-path}/.core/skills/cypilot/SKILL.md` FIRST WHEN {cfc_mode} is `off`

**Type**: Operation

ALWAYS open and follow `{cf-constructor-path}/.core/skills/cypilot/protocol.md` FIRST

ALWAYS open and follow `{cf-constructor-path}/.core/requirements/plan-template.md` WHEN compiling phase files

ALWAYS open and follow `{cf-constructor-path}/.core/requirements/plan-decomposition.md` WHEN decomposing tasks into phases

OPEN and follow `{cf-constructor-path}/.core/requirements/prompt-engineering.md` WHEN compiling phase files (phase files ARE agent instructions)

OPEN and follow `{cf-constructor-path}/.core/requirements/plan-checklist.md` WHEN validating plans (Phase 4.1 self-validation or /cf-constructor-analyze on plan)

For context compaction recovery during multi-phase workflows, follow `{cf-constructor-path}/.core/skills/cypilot/protocol.md` Section "Compaction Recovery".

## Overview

This workflow generates execution plans, not direct results. Use it when work exceeds a single-context window, requires a long checklist, or involves multi-block implementation. Do **not** use it for small edits, direct execution, or work that fits in ~500 compiled lines. Output: `plan.toml` + `N` phase files in `{cf-constructor-path}/.plans/{task-slug}/`.

## Context Budget & Overflow Prevention (CRITICAL)

- Open every applicable dependency file to inspect required sections, but do NOT retain full file bodies once the needed slices are extracted.
- Do NOT load all kit dependencies at once; load incrementally per phase.
- Do NOT hold all phase files in context simultaneously; compile and write one at a time.
- If a phase compilation would exceed current context budget, checkpoint and use Compaction Recovery.
- The plan manifest (`plan.toml`) is the recovery checkpoint and MUST be written before compilation.
- If the raw task input itself exceeds `500` lines, materialize it under `{cf-constructor-path}/.plans/{task-slug}/input/`, chunk it to `<= 300` lines per file, and treat the resulting chunk files as the authoritative raw-input package for the plan. When the source includes direct prompt text, preserve that raw prompt as `input/direct-prompt.md` before chunking. (Open, load, and follow `{cf-constructor-path}/.core/requirements/raw-input-overflow.md` for the shared overflow rule.)

Budget targets: Phase 0-1 `~200` lines, Phase 2 `~300`, Phase 3 `~500` per phase file, Phase 4 `~50`. The reference appendices below are runtime guidance only and do not consume plan-generation budget unless the user explicitly asks about execution behavior.

## Phase 0: Resolve Variables & Discover Tools

Open, load, and follow `workflows/plan/phase-0-discover.md` to resolve runtime variables and build the dynamic tool map from the CLISPEC.

## Phase 1: Assess Scope

Open, load, and follow `workflows/plan/phase-1-assess.md` to identify task type, extract target-workflow navigation rules, estimate compiled size, scan for all user interaction points, and identify the target artifact and its slug.

## Phase 2: Decompose

Open, load, and follow `workflows/plan/phase-2-decompose.md` to select the plan lifecycle, run intermediate-results analysis, add review gates, and predict execution-context budget per phase.

## Phase 3: Compile Phase Files

Open, load, and follow `workflows/plan/phase-3-compile.md` to write the plan manifest (`plan.toml`), generate compilation briefs, present the post-brief choice menu, produce phase files or phase-generation prompts, and validate compiled phase files. The Phase 3.3 dispatch payload MUST include `git_commit_mode`, `contributing_guide`, and `git_constraint` as specified in `phase-3-compile.md` § 3.3.

## Phase 4: Finalize Plan

Open, load, and follow `workflows/plan/phase-4-finalize.md` WHEN the user selected option `[1]` or `[3]` in Phase 3.2A and all `phase-*` files were produced. Contains Phase 4.1 self-validation, Phase 4.2 next-steps menu (`[1]`–`[5]`), and the New-Chat Startup Prompt.

## Plan Lifecycle

Open and follow `workflows/plan/plan-lifecycle.md` WHEN Phase 2.1 requires the user to select a plan lifecycle strategy.

## Plan Reference

Open and follow `workflows/plan/plan-reference.md` WHEN the user asks about plan execution, status, storage format, or the execution log (post-plan-creation reference).

## Completion Invariants

Open and follow `{cf-constructor-path}/.core/skills/cypilot/SKILL.md` § Completion Invariants before ending any response.
