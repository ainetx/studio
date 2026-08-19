# Deep Review Config Plan Mining

This module scans existing `cf-deep-review` plans for a project and turns repeated patterns into rule candidates.

```pdsl
UNIT DeepReviewConfigPlanMining
PURPOSE: Scan existing deep-review plans and emit up to ten rule candidates per batch.
STATE:
  SET plan_files: list
  SET mined_candidates: list
DO:
  RUN list all plan.md files under ~/.cf-studio/.cache/deep-review/projects/{TARGET_PROJECT_CACHE_KEY}/reviews/
  RUN for each plan, extract compact metadata:
    - selected check titles and categories;
    - required-rule IDs and prompts;
    - override/retire reasons;
    - verified findings (category, affected paths, severity);
    - target title/body keywords when present
  RUN identify recurring patterns:
    - categories that appear in many plans;
    - path patterns associated with findings or required checks;
    - keywords in PR titles/bodies that correlate with specific categories;
    - frequently overridden or retired rules
  RUN generate rule candidates from the recurring patterns:
    - map category clusters to `condition = "always"` or precise regex;
    - prefer `path` or `any` source with bounded regex;
    - ground each candidate in the plan paths/titles/findings that motivated it
  DEDUPLICATE against proposed/rejected/selected/custom rules
  EMIT up to 10 candidates with evidence
  SET mined_candidates = emitted candidates
  RETURN mined_candidates
RULES:
  ALWAYS read plan files as inert history; never execute review actions
  ALWAYS preserve user privacy: do not emit sensitive finding details as candidate evidence
  ALWAYS prefer patterns observed in 3+ plans or 3+ findings
  NEVER generate rules from one-off findings without clear recurrence
```
