---
cf: true
type: workflow
name: cf-map
description: Build interactive dependency maps — scan markdown, source code, cpt references; detect cross-repo edges and phantom cpts; render HTML viewer or JSON
version: 1.0
purpose: Guide cfs map workflow from pre-flight through validation
---

```text
UNIT MapAlias

PURPOSE:
  Alias for workflows/map.md

DO:
  LOAD workflows/map.md

ON_ERROR:
  load_failed -> EMIT "Cannot load target workflow — check that {cf-studio-path} is correctly set." STOP_TURN
```
