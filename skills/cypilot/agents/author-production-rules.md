---
description: Invoke when loading the shared Content Production Rules for Cyber Constructor author workers — single source of truth for content-production constraints applied before any file is written.
---

## Content Production Rules

The author MUST satisfy every rule below before returning. These rules are the
single source of truth for content-production constraints.

- No placeholder markers (`TODO`, `TBD`, `[Description]`, `FIXME`, etc.) in
  any written file.
- All IDs are valid (format matches the kind's ID schema) and unique within
  the target file.
- Every template H2 section is filled (no empty sections, no "see above"
  punts).
- Parent artifacts are referenced correctly (registered paths, matching kind,
  no dangling links).
- Conventions defined in the kit's `rules.md` are followed (naming, ordering,
  casing).
- All approved `inputs` are implemented in the generated content; nothing is
  silently dropped.
- Tests are emitted when the kind / rules require them.
- Traceability markers (e.g. `@cpt-...`) are emitted when `to_code="true"` on
  the kind.
- Behavioral sections use CDSL (Constructor Domain-Specific Language) per the
  kit's rules; no free-form prose where CDSL is required.
- `DESIGN.md` artifacts contain no executable code examples (CDSL only).
- Markdown quality: empty lines between headings / paragraphs / lists; fenced
  code blocks include a language tag.
