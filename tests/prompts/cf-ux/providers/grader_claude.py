"""Lightweight Claude grader for promptfoo llm-rubric assertions.

`claude -p --disable-slash-commands` — uses the existing Claude Code auth
(keychain / subscription) but disables every skill so cf can't hijack the
grader. This is the *judge*; it must reason about the response, not act.

`--bare` is avoided because it requires ANTHROPIC_API_KEY (refuses keychain).
"""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any

CLAUDE_BIN = "claude"
CALL_TIMEOUT_S = 180

GRADER_MODEL = os.environ.get("CF_UX_GRADER_MODEL", "claude-haiku-4-5")
GRADER_EFFORT = os.environ.get("CF_UX_GRADER_EFFORT", "low")


def call_api(prompt: str, options: dict | None = None, context: dict | None = None) -> dict:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [
                CLAUDE_BIN, "-p",
                "--model", GRADER_MODEL,
                "--effort", GRADER_EFFORT,
                "--disable-slash-commands",
                "--output-format", "text",
                "--max-budget-usd", "0.20",
                prompt,
            ],
            capture_output=True, text=True,
            timeout=CALL_TIMEOUT_S, check=False,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"grader timed out after {CALL_TIMEOUT_S}s"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"grader unexpected: {type(exc).__name__}: {exc}"}

    duration = time.monotonic() - started
    if proc.returncode != 0:
        return {
            "error": f"grader exited {proc.returncode}: {proc.stderr.strip()[:400]}",
            "metadata": {"duration_s": round(duration, 2)},
        }
    return {
        "output": proc.stdout.strip(),
        "metadata": {"duration_s": round(duration, 2)},
    }
