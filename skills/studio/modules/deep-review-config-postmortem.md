# Deep Review Config Post-Mortem

This module reads a finished deep-review plan and proposes rules that could have caught the findings earlier.

```pdsl
UNIT DeepReviewConfigPostmortem
PURPOSE: Read a finished review plan and emit up to ten rule candidates per batch.
STATE:
  SET postmortem_plan_path: absolute path
  SET postmortem_candidates: list
DO:
  ASK user for a plan path; default to the latest closed plan under ~/.cf-studio/.cache/deep-review/projects/{TARGET_PROJECT_CACHE_KEY}/reviews/
  READ the chosen plan as inert review history
  RUN extract findings: category, affected paths/target slices, severity, root-cause description
  RUN cluster findings:
    - by category;
    - by affected path pattern;
    - by recurring root-cause theme
  RUN generate rule candidates from clusters:
    - each candidate targets the path/title/diff pattern that produced the cluster;
    - each prompt reflects the specific failure mode observed;
    - evidence cites plan phase/check and affected paths, not sensitive data
  DEDUPLICATE against proposed/rejected/selected/custom rules
  EMIT up to 10 candidates with evidence
  SET postmortem_candidates = emitted candidates
  RETURN postmortem_candidates
RULES:
  ALWAYS read the plan as history; never modify it
  ALWAYS ask the user before using a non-default plan path
  ALWAYS preserve privacy: do not include secret values or proprietary details in evidence
  NEVER propose a rule that duplicates an existing selected or config rule
```
