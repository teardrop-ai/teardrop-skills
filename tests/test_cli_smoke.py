"""Safe CLI smoke tests (marker: ``smoke``).

These tests confirm the installed ``teardrop-cli`` binary is runnable and that
every top-level command group referenced by the skills responds to ``--help``.

Safety guarantees:

* Only ``--version`` and ``--help`` are ever invoked — no authentication,
  no network calls, no mutating operations (no login/publish/withdraw/run).
* The subprocess runs with a sanitized environment (no ``TEARDROP_*`` secrets
  forwarded) and a short timeout.
* Skipped automatically when ``teardrop-cli`` is not installed.

Run with: ``pytest -m smoke`` (or just ``pytest`` when the CLI is present).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

# Top-level groups that skills reference. We only probe these via --help.
PROBED_GROUPS = (
    "auth",
    "quickstart",
    "init",
    "config",
    "run",
    "chat",
    "schedules",
    "balance",
    "usage",
    "agent-tools",
    "event-triggers",
    "marketplace",
    "tools",
    "earnings",
    "llm-config",
    "models",
    "mcp",
)

TIMEOUT_SECONDS = 30


def _clean_env() -> dict[str, str]:
    """Return a copy of the environment with Teardrop secrets stripped."""
    env = dict(os.environ)
    for key in list(env):
        if key.upper().startswith("TEARDROP_"):
            del env[key]
    return env


def _teardrop_exe() -> str | None:
    """Return the path to the ``teardrop`` console script, if installed.

    We check ``PATH`` first, then the active virtualenv's ``Scripts``/``bin``
    directory, because invoking ``python -m pytest`` does not always put the
    venv ``Scripts`` dir on ``PATH`` even though the console script exists.
    """
    from shutil import which

    found = which("teardrop")
    if found:
        return found
    # Fall back to the interpreter's own environment (venv) layout.
    import sys
    from pathlib import Path

    candidates = [
        Path(sys.prefix) / "Scripts" / "teardrop.exe",
        Path(sys.prefix) / "Scripts" / "teardrop",
        Path(sys.prefix) / "bin" / "teardrop",
    ]
    for cand in candidates:
        if cand.is_file():
            return str(cand)
    return None


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    exe = _teardrop_exe()
    if exe is None:
        pytest.skip("teardrop console script not on PATH")
    return subprocess.run(
        [exe, *args],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        env=_clean_env(),
        cwd=str(ROOT),
    )


def _have_cli() -> bool:
    return _teardrop_exe() is not None


pytestmark = pytest.mark.smoke


@pytest.fixture(scope="module", autouse=True)
def require_cli():
    if not _have_cli():
        pytest.skip("teardrop-cli not installed")


def test_cli_version_runs() -> None:
    proc = _run(["--version"])
    assert proc.returncode == 0, proc.stderr
    assert "teardrop" in proc.stdout.lower()


def test_root_help_runs() -> None:
    proc = _run(["--help"])
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("group", PROBED_GROUPS)
def test_group_help_runs(group: str) -> None:
    proc = _run([group, "--help"])
    assert proc.returncode == 0, (
        f"`teardrop {group} --help` failed (rc={proc.returncode}): {proc.stderr}"
    )


def test_smoke_never_invokes_mutating_commands() -> None:
    """Guard: ensure the probed set contains no mutating subcommands."""
    forbidden = {"login", "publish", "withdraw", "delete", "subscribe", "set"}
    overlap = forbidden & set(PROBED_GROUPS)
    assert not overlap, f"smoke must not probe mutating groups: {overlap}"
