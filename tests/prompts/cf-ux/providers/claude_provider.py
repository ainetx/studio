"""promptfoo native python provider — Claude Code CLI in a cf-studio sandbox."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from _sandbox import SandboxError, sandbox

CLAUDE_BIN = "claude"
CALL_TIMEOUT_S = 850  # under promptfoo worker timeout (900s)

# Cheap-by-default model + low reasoning. Override via env if a scenario
# legitimately needs a stronger model.
#
# Note on 1M context: the 1M-token window is a beta enabled via
# `--betas context-1m-2025-08-07` and only on Opus/Sonnet. Haiku 4.5 has the
# standard 200K window — by selecting Haiku we implicitly opt out of 1M, and
# we never pass --betas here.
DEFAULT_MODEL = os.environ.get("CF_UX_CLAUDE_MODEL", "claude-haiku-4-5")
DEFAULT_EFFORT = os.environ.get("CF_UX_CLAUDE_EFFORT", "low")


def _parse_json_output(raw: str) -> dict[str, Any]:
    """`claude -p --output-format json` returns one JSON object on stdout."""
    raw = raw.strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def call_api(prompt: str, options: dict | None = None, context: dict | None = None) -> dict:
    started = time.monotonic()
    try:
        with sandbox() as cwd:
            return _invoke(prompt, cwd, started)
    except SandboxError as exc:
        return {"error": f"sandbox setup failed: {exc}"}
    except subprocess.TimeoutExpired:
        return {"error": f"claude timed out after {CALL_TIMEOUT_S}s"}
    except Exception as exc:  # noqa: BLE001 — surface unexpected errors to promptfoo
        return {"error": f"unexpected: {type(exc).__name__}: {exc}"}


def _invoke(prompt: str, cwd: Path, started: float) -> dict:
    # Explicit skill invocation: Claude Code uses `/cf <prompt>`.
    invoked = f"/cf {prompt}"
    cmd = [
        CLAUDE_BIN, "-p",
        "--model", DEFAULT_MODEL,
        "--effort", DEFAULT_EFFORT,
        "--output-format", "json",
        "--max-budget-usd", "0.30",
        invoked,
    ]
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=CALL_TIMEOUT_S, check=False,
        stdin=subprocess.DEVNULL,
    )
    duration = time.monotonic() - started

    if proc.returncode != 0:
        return {
            "error": f"claude exited {proc.returncode}: {proc.stderr.strip()[:500]}",
            "metadata": {"duration_s": round(duration, 2)},
        }

    payload = _parse_json_output(proc.stdout)
    output_text = (
        payload.get("result")
        or payload.get("text")
        or payload.get("_raw")
        or proc.stdout.strip()
    )

    metadata = {
        "duration_s": round(duration, 2),
        "sandbox": str(cwd),
        "session_id": payload.get("session_id"),
        "num_turns": payload.get("num_turns"),
        "total_cost_usd": payload.get("total_cost_usd"),
        # Heuristic — actual skill-loading detection refined later via stream-json.
        "skill_load_warning": "skills failed to load" in output_text.lower(),
    }
    cost = payload.get("total_cost_usd")
    result: dict[str, Any] = {"output": output_text, "metadata": metadata}
    if isinstance(cost, (int, float)):
        result["cost"] = float(cost)
    return result
