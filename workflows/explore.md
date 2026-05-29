---
cf: true
type: workflow
name: cf-explore
description: "Explore a Constructor Studio project for task-relevant resource context before planning, brainstorming, review, or generation. Uses cf-explorer to find project files, architecture docs, artifacts, and code references without treating them as prompt assets."
version: 1.0
purpose: Standalone explore command; discovers resource context and returns a controller-owned resource map
---

# Explore Workflow

```text
UNIT ExploreWorkflow

PURPOSE:
  Discover project/resource context relevant to a task without loading those
  resources into SHARED_CONTEXT_PACK.

DO:
  REQUIRE `{cf-studio-path}/.core/workflows/shared/inline-fallback-probe.md` loaded before cf-explorer dispatch
  DISPATCH cf-explorer with generator contract from
    {cf-studio-path}/.core/skills/studio/agents/cf-explorer.md
  WITH orchestrator-supplied values:
    task = user's explore request or parent workflow task
    intent = "standalone" | "brainstorm" | "generate" | "analyze" | "plan" | "workspace" | "pdsl"
    panel = null unless called from brainstorm after panel selection
    known_paths = paths already resolved by parent workflow
    search_roots = project roots allowed for read-only discovery
    constraints = relevant scope, system, KIND, and user-provided limits

  RECEIVE explorer result JSON
  EMIT resource map and context summary
  EMIT numbered next-actions menu:
    1. Use this context in brainstorm
    2. Use this context in plan
    3. Use this context in generate
    4. Use this context in analyze/review
    5. Refine exploration scope
    6. Stop

RULES:
  - MUST NOT put source code, docs, artifacts, diffs, or architecture files into
    SHARED_CONTEXT_PACK
  - MUST treat explorer output as resource_context, not prompt_context
  - MUST NOT write files
  - MUST NOT dispatch prompt-consuming sub-agents with resource paths only when
    the task requires resolved resource summaries or excerpts
```
