"""Sandbox lifecycle helpers for cf-ux promptfoo providers.

Initializes a fresh cf-studio project in `$TMPDIR/cf-ux-sandboxes/<id>/` using
the **local** repo as the source of truth.

Cleanup is hardened: each sandbox is registered in a process-wide set wiped
by `atexit` and by SIGTERM/SIGINT handlers, so a killed promptfoo worker
does not leak the directory. On startup, any sandbox older than 24h under
the parent dir is also swept.

Env overrides:
  CF_UX_SHARED_SANDBOX  — reuse an already-initialized path (no setup/teardown).
  CF_UX_KEEP_SANDBOX=1  — skip teardown on success and print the path.
"""

from __future__ import annotations

import atexit
import contextlib
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Iterator


REPO_ROOT = Path(__file__).resolve().parents[4]
STUDIO_SCRIPTS = REPO_ROOT / "skills" / "studio" / "scripts"

_SANDBOX_PARENT = Path(tempfile.gettempdir()) / "cf-ux-sandboxes"
_STALE_AFTER_SECONDS = 24 * 60 * 60  # 24h

_LIVE_SANDBOXES: set[Path] = set()
_HANDLERS_INSTALLED = False


class SandboxError(RuntimeError):
    pass


def _wipe(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _atexit_cleanup() -> None:
    for p in list(_LIVE_SANDBOXES):
        _wipe(p)
        _LIVE_SANDBOXES.discard(p)


def _signal_cleanup(signum, _frame) -> None:  # noqa: ANN001
    _atexit_cleanup()
    # Re-raise via default handler so the process actually exits.
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


def _install_handlers_once() -> None:
    global _HANDLERS_INSTALLED  # noqa: PLW0603
    if _HANDLERS_INSTALLED:
        return
    atexit.register(_atexit_cleanup)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(sig, _signal_cleanup)
        except (ValueError, OSError):
            pass  # not available in this thread/platform
    _HANDLERS_INSTALLED = True


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists but not ours
    return True


def _sweep_stale_sandboxes() -> None:
    """Wipe leftover sandboxes from dead promptfoo workers or stale runs.

    Sandbox name pattern is `<pid>-<rand>`. If the pid is no longer running,
    the dir cannot belong to a live worker — safe to remove. Also wipes
    anything older than _STALE_AFTER_SECONDS regardless of pid.
    """
    if not _SANDBOX_PARENT.exists():
        return
    cutoff = time.time() - _STALE_AFTER_SECONDS
    for child in _SANDBOX_PARENT.iterdir():
        try:
            owner_pid = int(child.name.split("-", 1)[0])
        except (ValueError, IndexError):
            owner_pid = None
        try:
            mtime = child.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            _wipe(child); continue
        if owner_pid is not None and not _pid_alive(owner_pid):
            _wipe(child); continue


def _new_sandbox_path() -> Path:
    _SANDBOX_PARENT.mkdir(parents=True, exist_ok=True)
    return _SANDBOX_PARENT / f"{os.getpid()}-{uuid.uuid4().hex[:8]}"


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> None:
    proc = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True,
        timeout=180, check=False, env=env,
    )
    if proc.returncode != 0:
        raise SandboxError(
            f"cmd failed: {' '.join(cmd)}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )


def _git_bootstrap(root: Path) -> None:
    _run(["git", "init", "-q", "-b", "main"], cwd=root)
    _run(
        ["git", "-c", "user.email=ux@test", "-c", "user.name=ux",
         "commit", "--allow-empty", "-q", "-m", "init"],
        cwd=root,
    )


def _local_cfs_init(project_root: Path) -> None:
    bootstrap = (
        "import sys\n"
        f"sys.path.insert(0, {str(STUDIO_SCRIPTS)!r})\n"
        "from studio.commands import init as _init\n"
        f"_init.CACHE_DIR = __import__('pathlib').Path({str(REPO_ROOT)!r})\n"
        "_init._prompt_kit_install_flag = lambda interactive: False\n"
        "from studio.cli import main\n"
        "sys.argv = ['studio', 'init', '--yes',\n"
        "            '--migrate-from-cypilot=no',\n"
        "            '--update-legacy-studio=no']\n"
        "raise SystemExit(main())\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", bootstrap],
        cwd=project_root, capture_output=True, text=True,
        timeout=300, check=False,
    )
    if proc.returncode != 0:
        raise SandboxError(
            "local cfs init failed:\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )


def _local_generate_agents(project_root: Path, agent: str) -> None:
    bootstrap = (
        "import sys\n"
        f"sys.path.insert(0, {str(STUDIO_SCRIPTS)!r})\n"
        "from studio.cli import main\n"
        f"sys.argv = ['studio', 'generate-agents', '--agent', {agent!r}, '-y']\n"
        "raise SystemExit(main())\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", bootstrap],
        cwd=project_root, capture_output=True, text=True,
        timeout=180, check=False,
    )
    if proc.returncode != 0:
        raise SandboxError(
            f"generate-agents --agent {agent} failed:\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )


def _init_sandbox(root: Path) -> None:
    _git_bootstrap(root)
    _local_cfs_init(root)
    _local_generate_agents(root, "claude")
    _local_generate_agents(root, "openai")


@contextlib.contextmanager
def sandbox() -> Iterator[Path]:
    _install_handlers_once()
    _sweep_stale_sandboxes()

    shared = os.environ.get("CF_UX_SHARED_SANDBOX")
    if shared:
        path = Path(shared)
        if not path.exists():
            raise SandboxError(f"CF_UX_SHARED_SANDBOX does not exist: {path}")
        yield path
        return

    path = _new_sandbox_path()
    path.mkdir(parents=True, exist_ok=False)
    _LIVE_SANDBOXES.add(path)
    keep = os.environ.get("CF_UX_KEEP_SANDBOX") == "1"
    try:
        _init_sandbox(path)
        yield path
    finally:
        if keep:
            print(f"[cf-ux] kept sandbox: {path}", file=sys.stderr)
            _LIVE_SANDBOXES.discard(path)  # do not wipe on atexit
        else:
            _wipe(path)
            _LIVE_SANDBOXES.discard(path)
