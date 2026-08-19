# Deep Review Config Discovery

This module generates rule candidates by reverse-engineering the target project. It is read-only: it activates the `ReverseEngineeringActivation` contract from `{cf-studio-path}/.core/requirements/reverse-engineering.md`, progresses through every layer, and turns L8 pattern/convention findings plus L9 synthesis into review-rule candidates.

```pdsl
UNIT DeepReviewConfigDiscovery
PURPOSE: Scan the target project read-only and emit up to ten rule candidates per batch.
STATE:
  SET resource_context: object (default empty, scope workflow_run)
  SET re_layer_findings: object (default empty, scope workflow_run)
  SET discovery_candidates: list (default empty)
DO:
  LOAD {cf-studio-path}/.core/requirements/reverse-engineering.md as the active methodology
  LOAD {cf-studio-path}/.core/requirements/auto-config.md for AutoConfigQualityRules
  RUN ReverseEngineeringActivation: SET REVERSE_ENGINEERING_MODE = true
  LOAD {cf-studio-path}/.core/skills/studio/modules/subagents/dispatch.md
  SET SUB_AGENT_GROUP_DECISION = approve-once
  RUN SubAgentDispatch with agent=cf-explorer and prompt="Load {cf-studio-path}/.core/requirements/reverse-engineering.md as the active methodology. Activate ReverseEngineeringActivation and execute ReverseEngineeringLayerOrder from L1 through L9. Return resource_context that contains the checkpoint for every layer, with extra detail for L8 Pattern Recognition (L8.1 code patterns, L8.2 project conventions, L8.3 testing conventions) and L9 Knowledge Synthesis (carry-forward patterns and gaps). Ground every layer checkpoint in real file/path evidence. Do not generate review rules; only return the methodology checkpoints and project evidence."
  SET resource_context = the resource_context returned by cf-explorer
  SET re_layer_findings = the layer checkpoints inside resource_context
  RUN derive rule candidates from L8 pattern/convention findings and L9 carry-forward knowledge:
    - map each recurring convention, boundary, or high-risk pattern to a precise regex condition (title/body/path/diff/any);
    - prefer `path` and `any` sources with bounded, project-specific regex;
    - ground every candidate in file:line or path-cluster evidence from the checkpoints;
    - avoid generic rules that would match any project;
    - apply AutoConfigQualityRules (activity-based WHEN, L2 clarity, L5 anti-patterns, <=120-line prompt target);
    - deduplicate by fingerprint against proposed/rejected/selected/custom rules
  EMIT up to 10 candidates with evidence and layer source
  SET discovery_candidates = emitted candidates
  RETURN discovery_candidates
RULES:
  ALWAYS activate ReverseEngineeringActivation before layer work
  ALWAYS progress layers in order L1..L9 and carry prior findings forward
  ALWAYS scan via cf-explore in return-context mode; never write during discovery
  ALWAYS prefer project-specific patterns over generic boilerplate
  ALWAYS ground every candidate in evidence from re_layer_findings
  NEVER generate rules that overlap with already proposed/rejected/selected/custom rules
  NEVER emit sensitive details from L1-L7 as rule evidence
```
