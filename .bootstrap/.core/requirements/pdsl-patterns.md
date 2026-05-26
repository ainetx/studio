---
name: PDSL Patterns Registry
version: 0.1
purpose: Canonical named-pattern registry for the PDSL matches() operator
---

# PDSL Patterns Registry

This file is the canonical registry for named patterns used with the
`matches(<value>, <pattern-name>)` operator in PDSL condition blocks.

When a pattern name used in a `matches()` call cannot be resolved to a local
`PATTERNS:` block in the same file, it MUST be defined here.

Add a new entry whenever you introduce a pattern that is intended for
cross-file reuse. Patterns that are only used in a single file SHOULD be
declared in a local `PATTERNS:` block in that file instead.

## Registry

This registry is currently empty pending first use.

When adding an entry, follow this format:

```text
### <pattern-name>

- **Pattern:** `<regex>`
- **Description:** <one sentence explaining what the pattern matches>
- **Used by:** <list of files that reference this pattern name>
- **Added:** <YYYY-MM-DD>
```

## Usage Reference

See `.bootstrap/.core/architecture/specs/PDSL.md` §Conditions for the
`matches()` operator definition and the resolution rules that govern when
this registry is consulted.
