# cf-skill UX scenario evals (promptfoo pilot)

End-to-end UX tests for the `cf` skill, running real `claude` and `codex` CLIs
inside isolated, freshly-`cfs init`-ed `tempfile.mkdtemp()` sandboxes built
from the **local repo source** (not `.bootstrap/`, not GitHub).

## Run

```bash
cd tests/prompts/cf-ux
REQUEST_TIMEOUT_MS=900000 npx promptfoo@latest eval
npx promptfoo@latest view     # HTML report
```

Each scenario:
1. Creates `$TMPDIR/cf-ux-XXXXXX/`, `git init`, and runs the in-tree
   `studio.commands.init.cmd_init` with `CACHE_DIR` patched to repo root
   and the kit-install prompt stubbed out (no network calls).
2. Runs `cfs generate-agents --agent claude` and `--agent openai`.
3. Invokes `claude -p` or `codex exec` in that sandbox.
4. Tears the sandbox down (unless `CF_UX_KEEP_SANDBOX=1`).

A grader (`grader_claude.py` — `claude -p --disable-slash-commands`) drives
the `llm-rubric` asserts; sub-100ms text guards catch skill-load failures.

## Env knobs

| Env | Effect |
|---|---|
| `REQUEST_TIMEOUT_MS=900000` | promptfoo python-worker timeout (default 300s is too short for sandbox init + cold codex). |
| `CF_UX_SHARED_SANDBOX=/path` | Reuse a pre-initialized sandbox; skip setup/teardown. |
| `CF_UX_KEEP_SANDBOX=1` | Keep the sandbox after the run; print its path. |

## Layout

```
tests/prompts/cf-ux/
├── promptfooconfig.yaml
├── providers/
│   ├── _sandbox.py          — tmpdir + local cfs init context manager
│   ├── claude_provider.py   — claude -p, JSON output, returns metadata
│   ├── codex_provider.py    — codex exec, approval=never, workspace-write
│   └── grader_claude.py     — claude -p --disable-slash-commands (judge)
└── README.md
```

## Current baseline (pilot)

3 scenarios × 2 providers = 6 cases, ~3-4 min total wall-clock.

| Scenario | claude-code | codex |
|---|---|---|
| ADR routing → cf-generate inputs flow | ✅ | ❌ silently writes ADR file |
| Brainstorm topic → cf-brainstorm framing | ✅ | ❌ free-form ideation, no panel |
| Analyze missing artifact → refuse cleanly | ✅ | ✅ |

The codex failures are **real UX gaps**, not test miscalibration:
`cfs generate-agents --agent openai` produces `.codex/agents/*.toml` but
codex has no auto-routing layer equivalent to Claude Code's skill loader,
so the model defaults to free-agent behavior and ignores the cf flow.

## Next steps

- Parse `claude -p --output-format stream-json` to capture tool-call traces
  and assert directly on `Skill` invocations / sub-agent dispatches.
- Cover write-paths (`cf-generate` actually creating an ADR after inputs)
  with `--sandbox workspace-write` + per-test fresh sandbox.
- Add `make ux-quick` that reuses one shared sandbox via
  `CF_UX_SHARED_SANDBOX` for fast iteration on assertion text.
- Wire into CI as a non-blocking job; promote to gating once stable.
