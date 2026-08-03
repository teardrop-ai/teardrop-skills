"""CLI contract tests: skill commands must match the installed teardrop-cli.

These tests prevent CLI drift — a skill referencing a renamed or removed
command/flag would fail here. Validation is done **in-process** against the
Click/Typer command tree; skill text is never executed.

The live-CLI tests skip automatically when ``teardrop-cli`` is not installed
(CI always installs it). A fake Click tree is used for offline unit coverage.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
FIXTURE_REF = ROOT / "tests" / "fixtures" / "cli-reference.md"

EXPECTED_SKILLS = (
    "install",
    "publish-tool",
    "run-agent",
    "manage-billing",
    "discover-marketplace",
    "manage-org",
    "withdraw-earnings",
)


# ---------------------------------------------------------------------------
# Offline unit tests against a fake Click tree
# ---------------------------------------------------------------------------


def _make_fake_tree() -> "object":
    """Build a minimal fake command tree mirroring teardrop-cli's surface.

    Uses :class:`Node` directly (no Click import) so offline unit tests do not
    depend on ``teardrop-cli``/``click`` being installed.
    """
    from teardrop_skills.cli_surface import Node

    root = Node("teardrop", is_group=True, options={"--help", "--version"})
    auth = Node("auth", is_group=True, options=set())
    auth.children["login"] = Node(
        "login",
        is_group=False,
        options={
            "--email",
            "--siwe",
            "--key-file",
            "--token",
            "--client-id",
            "--client-secret",
        },
    )
    auth.children["status"] = Node("status", is_group=False, options={"--json"})
    auth.children["logout"] = Node("logout", is_group=False, options=set())
    root.children["auth"] = auth

    tools = Node("tools", is_group=True, options=set())
    tools.children["publish"] = Node(
        "publish", is_group=False, options={"--from-file", "--settlement-wallet"}
    )
    tools.children["list"] = Node("list", is_group=False, options={"--json"})
    root.children["tools"] = tools

    run = Node(
        "run",
        is_group=False,
        options={"--thread", "--context", "--json", "--no-stream"},
    )
    root.children["run"] = run
    return root


def test_extract_ignores_prose() -> None:
    from teardrop_skills.cli_surface import extract_skill_commands

    md = (
        "# Title\n"
        "Use `teardrop auth status` to check login (prose, ignored).\n"
        "```bash\nteardrop auth login --email you@example.com\n```\n"
    )
    cmds = extract_skill_commands(md)
    assert len(cmds) == 1
    assert cmds[0].subcommands == ["auth", "login"]
    assert "--email" in cmds[0].flags


def test_extract_drops_placeholders_and_json() -> None:
    from teardrop_skills.cli_surface import extract_skill_commands

    md = "```bash\nteardrop tools publish --from-file tool.json --settlement-wallet 0xABC\n```"
    cmds = extract_skill_commands(md)
    assert cmds[0].subcommands == ["tools", "publish"]
    assert "--from-file" in cmds[0].flags
    assert "--settlement-wallet" in cmds[0].flags
    # 0xABC is a positional value, not a flag — must be dropped.
    assert all(not f.startswith("0x") for f in cmds[0].flags)


def test_validate_accepts_known_command() -> None:
    from teardrop_skills.cli_surface import validate_commands

    from teardrop_skills.cli_surface import extract_skill_commands

    tree = _make_fake_tree()
    cmds = extract_skill_commands("```bash\nteardrop auth login --email x\n```")
    assert validate_commands(cmds, tree) == []


def test_validate_flags_unknown_flag() -> None:
    from teardrop_skills.cli_surface import validate_commands

    from teardrop_skills.cli_surface import extract_skill_commands

    tree = _make_fake_tree()
    cmds = extract_skill_commands("```bash\nteardrop auth login --bogus\n```")
    findings = validate_commands(cmds, tree)
    assert len(findings) == 1
    assert "unknown flag" in findings[0].message


def test_validate_flags_unknown_subcommand() -> None:
    from teardrop_skills.cli_surface import validate_commands

    from teardrop_skills.cli_surface import extract_skill_commands

    tree = _make_fake_tree()
    cmds = extract_skill_commands("```bash\nteardrop auth frobnicate\n```")
    findings = validate_commands(cmds, tree)
    assert len(findings) == 1
    assert "unknown subcommand" in findings[0].message


def test_validate_accepts_flag_with_inline_value() -> None:
    from teardrop_skills.cli_surface import validate_commands

    from teardrop_skills.cli_surface import extract_skill_commands

    tree = _make_fake_tree()
    cmds = extract_skill_commands(
        "```bash\nteardrop tools publish --from-file=tool.json\n```"
    )
    assert validate_commands(cmds, tree) == []


# ---------------------------------------------------------------------------
# Live CLI contract (skipped if teardrop-cli not installed)
# ---------------------------------------------------------------------------


def _have_cli() -> bool:
    try:
        import teardrop_cli  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.fixture(scope="module")
def cli_tree():
    if not _have_cli():
        pytest.skip("teardrop-cli not installed")
    from teardrop_skills.cli_surface import load_cli_tree

    return load_cli_tree()


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_skill_commands_exist_in_cli(name: str, cli_tree) -> None:
    from teardrop_skills.cli_surface import (
        extract_skill_commands,
        validate_commands,
    )

    text = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
    cmds = extract_skill_commands(text, source_file=SKILLS_DIR / name / "SKILL.md")
    findings = validate_commands(cmds, cli_tree)
    assert not findings, f"CLI drift in skill {name!r}:\n" + "\n".join(
        f"  - {f.message}  (from: {f.command.raw!r})" for f in findings
    )


# ---------------------------------------------------------------------------
# Doc anchor validation against pinned cli-reference.md fixture
# ---------------------------------------------------------------------------


def _github_slug(heading: str) -> str:
    """Convert a markdown heading to its GitHub anchor slug.

    GitHub's algorithm: lowercase, strip, remove punctuation (including ``&``)
    but keep word chars / spaces / hyphens, then spaces become hyphens. This
    yields ``earnings--withdrawals`` from ``Earnings & Withdrawals`` (the ``&``
    is dropped, leaving two spaces that collapse to ``--``).
    """
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = s.strip().replace(" ", "-")
    return s


def _fixture_anchors() -> set[str]:
    if not FIXTURE_REF.is_file():
        pytest.skip(f"pinned fixture missing: {FIXTURE_REF}")
    text = FIXTURE_REF.read_text(encoding="utf-8")
    anchors: set[str] = set()
    for line in text.splitlines():
        if line.startswith("## "):
            anchors.add(_github_slug(line[3:]))
    return anchors


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_skill_doc_anchors_in_fixture(name: str) -> None:
    import re

    anchors = _fixture_anchors()
    text = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
    used = set(re.findall(r"cli-reference\.md#([a-z0-9-]+)", text, re.IGNORECASE))
    unknown = {u for u in used if u not in anchors}
    assert not unknown, f"Skill {name!r} references unknown doc anchors: {unknown}"
