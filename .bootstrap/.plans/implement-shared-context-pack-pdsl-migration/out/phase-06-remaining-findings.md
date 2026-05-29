# Phase 06 Remaining Findings

## Summary

Unresolved or intentionally deferred findings remaining after Phase 6 validation: 3

## Findings

| ID | Paths | Evidence | Blocking reason | Why not safely fixable in Phase 6 |
| --- | --- | --- | --- | --- |
| F1 | `.bootstrap/config/kits/sdlc/workflows/pr-review.md:12`, `.bootstrap/config/kits/sdlc/workflows/pr-status.md:12` | Both runtime kit workflows still reference `{cf-studio-path}/.core/skills/cf-studio/SKILL.md`; `test -e .bootstrap/.core/skills/cf-studio/SKILL.md` returned `MISSING`. | Real runtime path defect in SDLC kit workflow copies. | These files are outside the phase's allowed edit set, which permits `.bootstrap/config/kits/sdlc/AGENTS.md` and `.bootstrap/.core/` but not `.bootstrap/config/kits/sdlc/workflows/*.md`. Editing them here would violate the phase contract. |
| F2 | `.bootstrap/config/kits/sdlc/workflows/migrate-openspec.md:899`, `:915`, `:923` | The runtime kit workflow still invokes `python3 {cf-studio-path}/.core/skills/cf-studio/scripts/cfs.py ...`; `test -e .bootstrap/.core/skills/cf-studio/scripts/cfs.py` returned `MISSING`. | Real runtime script-path defect in an SDLC kit workflow copy. | The invalid path lives in the same out-of-scope runtime workflow surface as F1, so Phase 6 cannot patch it without exceeding the declared write boundary. |
| F3 | `requirements/storytelling-modes.md`, `requirements/storytelling-phases.md`, `requirements/storytelling-preferences.md`, `requirements/storytelling-export.md` | These prompt-bearing files were surfaced by the no-`UNIT` helper triage and remain prose-heavy interactive execution contracts. Phase 05 explicitly deferred the storytelling deeper-module tranche. | Non-mechanical PDSL migration remains. | Converting these files safely would require a substantive semantics-preserving rewrite of the storytelling methodology, not deterministic validation-gap cleanup. That exceeds Phase 6's "mechanical and semantics-preserving" conversion allowance. |

## Explicit Non-Findings

- Top-level workflow/orchestrator prompt-loading surfaces already documented by
  earlier phases were not reclassified as violations. This currently includes
  `skills/studio/protocol.md`, `workflows/{plan,workspace,pdsl}.md`, and
  `workflows/analyze*.md`.
- The canonical controller-agent tranche previously deferred by earlier phases
  (`cf-codegen`, `cf-pr-review`, `cf-ralphex`, `cf-phase-runner`,
  `cf-phase-compiler`) was remediated during the final canonical review loop
  and therefore is not part of the remaining-findings set.
- Reference-oriented prompt-bearing files such as checklists, templates, and registry/spec examples were not treated as PDSL-conversion failures solely because they lack `UNIT` headers.
