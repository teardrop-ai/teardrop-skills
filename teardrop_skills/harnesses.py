"""Harness detection and installation for teardrop-skills.

Native skill harnesses receive one symlink/junction (or copy) per skill
directory under their skills root:

    <skills-root>/<skill-name>/SKILL.md

Cursor receives converted ``.mdc`` rule files under ``.cursor/rules/``.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

# ---------------------------------------------------------------------------
# Harness registry
# ---------------------------------------------------------------------------

_HARNESSES: dict[str, type["Harness"]] = {}


def _register(cls: type["Harness"]) -> type["Harness"]:
    _HARNESSES[cls.name] = cls
    return cls


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class Harness(ABC):
    """Base class for a supported agent harness."""

    name: str
    description: str
    # "skills" installs SKILL.md directories; "cursor-rules" writes .mdc files.
    install_mode: str = "skills"

    @classmethod
    @abstractmethod
    def detect(cls, cwd: Path = Path.cwd()) -> str | None:
        """Return a label if this harness is detected, else None."""

    @classmethod
    @abstractmethod
    def install_path(cls, cwd: Path = Path.cwd(), user: bool = False) -> Path:
        """Return the target directory for this harness."""

    @classmethod
    def install(
        cls,
        source: Path,
        cwd: Path = Path.cwd(),
        user: bool = False,
        dry_run: bool = False,
    ) -> Path:
        """Install *source* skills into this harness. Returns the target path."""
        target = cls.install_path(cwd=cwd, user=user)
        skills = _iter_skill_dirs(source)

        if dry_run:
            _log_dry_run(source, target, skills, mode=cls.install_mode)
            return target

        target.mkdir(parents=True, exist_ok=True)

        if cls.install_mode == "cursor-rules":
            _install_cursor_rules(skills, target)
        else:
            _install_skill_dirs(skills, target)

        print(f"✓ Installed {len(skills)} teardrop skill(s) → {target}")
        return target


# ---------------------------------------------------------------------------
# Concrete harnesses — native SKILL.md layout
# ---------------------------------------------------------------------------


@_register
class ClaudeCodeHarness(Harness):
    name = "claude-code"
    description = "Claude Code (Anthropic) — .claude/skills/"

    @classmethod
    def detect(cls, cwd: Path = Path.cwd()) -> str | None:
        for parent in _walk_up(cwd):
            path = parent / ".claude" / "skills"
            if path.is_dir():
                return f"Claude Code project skills ({path})"
        personal = Path.home() / ".claude" / "skills"
        if personal.is_dir():
            return f"Claude Code personal skills ({personal})"
        return None

    @classmethod
    def install_path(cls, cwd: Path = Path.cwd(), user: bool = False) -> Path:
        if user:
            return Path.home() / ".claude" / "skills"
        for parent in _walk_up(cwd):
            candidate = parent / ".claude" / "skills"
            if candidate.is_dir():
                return candidate
        return cwd / ".claude" / "skills"


@_register
class ClineHarness(Harness):
    name = "cline"
    description = "Cline — .cline/skills/"

    @classmethod
    def detect(cls, cwd: Path = Path.cwd()) -> str | None:
        for parent in _walk_up(cwd):
            path = parent / ".cline" / "skills"
            if path.is_dir():
                return f"Cline project skills ({path})"
        return None

    @classmethod
    def install_path(cls, cwd: Path = Path.cwd(), user: bool = False) -> Path:
        for parent in _walk_up(cwd):
            candidate = parent / ".cline" / "skills"
            if candidate.is_dir():
                return candidate
        return cwd / ".cline" / "skills"


@_register
class CopilotHarness(Harness):
    name = "copilot"
    description = "GitHub Copilot — .github/skills/ or ~/.copilot/skills/"

    @classmethod
    def detect(cls, cwd: Path = Path.cwd()) -> str | None:
        for parent in _walk_up(cwd):
            for rel in (
                Path(".github") / "skills",
                Path(".agents") / "skills",
            ):
                path = parent / rel
                if path.is_dir():
                    return f"GitHub Copilot project skills ({path})"
            if (parent / ".github").is_dir():
                return f"GitHub Copilot project (.github present at {parent})"
        personal = Path.home() / ".copilot" / "skills"
        if personal.is_dir():
            return f"GitHub Copilot personal skills ({personal})"
        agents = Path.home() / ".agents" / "skills"
        if agents.is_dir():
            return f"GitHub Copilot personal skills ({agents})"
        return None

    @classmethod
    def install_path(cls, cwd: Path = Path.cwd(), user: bool = False) -> Path:
        if user:
            personal = Path.home() / ".copilot" / "skills"
            if personal.is_dir() or not (Path.home() / ".agents" / "skills").is_dir():
                return personal
            return Path.home() / ".agents" / "skills"
        for parent in _walk_up(cwd):
            for rel in (
                Path(".github") / "skills",
                Path(".agents") / "skills",
            ):
                candidate = parent / rel
                if candidate.is_dir():
                    return candidate
            if (parent / ".github").is_dir():
                return parent / ".github" / "skills"
        return cwd / ".github" / "skills"


@_register
class PiHarness(Harness):
    name = "pi"
    description = "Pi coding agent — .pi/skills/ or ~/.pi/agent/skills/"

    @classmethod
    def detect(cls, cwd: Path = Path.cwd()) -> str | None:
        for parent in _walk_up(cwd):
            for rel in (
                Path(".pi") / "skills",
                Path(".agents") / "skills",
            ):
                path = parent / rel
                if path.is_dir():
                    return f"Pi project skills ({path})"
            if (parent / ".pi").is_dir():
                return f"Pi project (.pi present at {parent})"
        personal = Path.home() / ".pi" / "agent" / "skills"
        if personal.is_dir():
            return f"Pi personal skills ({personal})"
        agents = Path.home() / ".agents" / "skills"
        if agents.is_dir():
            return f"Pi personal skills ({agents})"
        return None

    @classmethod
    def install_path(cls, cwd: Path = Path.cwd(), user: bool = False) -> Path:
        if user:
            personal = Path.home() / ".pi" / "agent" / "skills"
            if personal.is_dir() or not (Path.home() / ".agents" / "skills").is_dir():
                return personal
            return Path.home() / ".agents" / "skills"
        for parent in _walk_up(cwd):
            for rel in (
                Path(".pi") / "skills",
                Path(".agents") / "skills",
            ):
                candidate = parent / rel
                if candidate.is_dir():
                    return candidate
            if (parent / ".pi").is_dir():
                return parent / ".pi" / "skills"
        return cwd / ".pi" / "skills"


@_register
class OpenCodeHarness(Harness):
    name = "opencode"
    description = "OpenCode — .opencode/skills/ or ~/.config/opencode/skills/"

    @classmethod
    def detect(cls, cwd: Path = Path.cwd()) -> str | None:
        for parent in _walk_up(cwd):
            path = parent / ".opencode" / "skills"
            if path.is_dir():
                return f"OpenCode project skills ({path})"
            if (parent / ".opencode").is_dir():
                return f"OpenCode project (.opencode present at {parent})"
        personal = Path.home() / ".config" / "opencode" / "skills"
        if personal.is_dir():
            return f"OpenCode personal skills ({personal})"
        return None

    @classmethod
    def install_path(cls, cwd: Path = Path.cwd(), user: bool = False) -> Path:
        if user:
            return Path.home() / ".config" / "opencode" / "skills"
        for parent in _walk_up(cwd):
            candidate = parent / ".opencode" / "skills"
            if candidate.is_dir():
                return candidate
            if (parent / ".opencode").is_dir():
                return parent / ".opencode" / "skills"
        return cwd / ".opencode" / "skills"


@_register
class CursorHarness(Harness):
    name = "cursor"
    description = "Cursor — .cursor/rules/*.mdc (converted from SKILL.md)"
    install_mode = "cursor-rules"

    @classmethod
    def detect(cls, cwd: Path = Path.cwd()) -> str | None:
        for parent in _walk_up(cwd):
            path = parent / ".cursor" / "rules"
            if path.is_dir():
                return f"Cursor project rules ({path})"
            if (parent / ".cursor").is_dir():
                return f"Cursor project (.cursor present at {parent})"
        return None

    @classmethod
    def install_path(cls, cwd: Path = Path.cwd(), user: bool = False) -> Path:
        # Cursor project rules are project-scoped; --user still writes project rules.
        for parent in _walk_up(cwd):
            candidate = parent / ".cursor" / "rules"
            if candidate.is_dir():
                return candidate
            if (parent / ".cursor").is_dir():
                return parent / ".cursor" / "rules"
        return cwd / ".cursor" / "rules"


@_register
class GenericPathHarness(Harness):
    name = "path"
    description = "Custom path (explicit --path argument)"

    _custom_path: Path | None = None

    @classmethod
    def detect(cls, cwd: Path = Path.cwd()) -> str | None:
        return None

    @classmethod
    def install_path(cls, cwd: Path = Path.cwd(), user: bool = False) -> Path:
        if cls._custom_path is not None:
            return cls._custom_path
        raise ValueError(
            "GenericPathHarness requires --path. "
            "Use: teardrop-skills install --path /custom/location"
        )

    @classmethod
    def configure_path(cls, path: Path) -> None:
        cls._custom_path = path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_harnesses() -> list[dict[str, str]]:
    """Return metadata for all registered harnesses."""
    return [
        {"name": cls.name, "description": cls.description}
        for cls in _HARNESSES.values()
    ]


def detect_harness(
    name: str | None = None, cwd: Path = Path.cwd()
) -> type[Harness] | None:
    """Detect the active harness, or return a named harness class."""
    if name is not None:
        cls = _HARNESSES.get(name)
        if cls is None:
            valid = ", ".join(_HARNESSES)
            print(f"Unknown harness {name!r}. Valid: {valid}", file=sys.stderr)
            return None
        return cls

    for cls in _HARNESSES.values():
        if cls.detect(cwd=cwd) is not None:
            return cls
    return None


def install_skills(
    harness_name: str | None = None,
    path: Path | None = None,
    cwd: Path = Path.cwd(),
    user: bool = False,
    dry_run: bool = False,
) -> bool:
    """Install teardrop skills into the target harness.

    Returns True on success, False on failure.
    """
    from teardrop_skills import skills_path as _pkg_skills_path

    try:
        source = _pkg_skills_path()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return False

    if path is not None:
        GenericPathHarness.configure_path(path)
        harness_cls: type[Harness] = GenericPathHarness
    elif harness_name is not None:
        cls = _HARNESSES.get(harness_name)
        if cls is None:
            valid = ", ".join(_HARNESSES)
            print(
                f"Unknown harness {harness_name!r}. Valid: {valid}",
                file=sys.stderr,
            )
            return False
        harness_cls = cls
    else:
        detected = detect_harness(cwd=cwd)
        if detected is None:
            print(
                "No harness detected. Specify one with:\n"
                "  teardrop-skills install --harness <name>\n"
                "  teardrop-skills install --path /custom/location\n"
                f"\nSupported harnesses: {', '.join(_HARNESSES)}",
                file=sys.stderr,
            )
            return False
        harness_cls = detected

    harness_cls.install(source, cwd=cwd, user=user, dry_run=dry_run)
    return True


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _walk_up(cwd: Path) -> list[Path]:
    return [cwd, *list(cwd.parents)]


def _iter_skill_dirs(source: Path) -> list[Path]:
    return sorted(
        p for p in source.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )


def _log_dry_run(source: Path, target: Path, skills: list[Path], mode: str) -> None:
    action = (
        "write .mdc rule files"
        if mode == "cursor-rules"
        else f"create {'junctions' if platform.system() == 'Windows' else 'symlinks'} per skill"
    )
    print("[dry-run] Would install skills from:")
    print(f"  source: {source}")
    print(f"  target: {target}")
    print(f"  action: {action}")
    print()
    print("Skills:")
    for skill in skills:
        if mode == "cursor-rules":
            print(f"  • teardrop-{skill.name}.mdc")
        else:
            print(f"  • {skill.name}/")


def _install_skill_dirs(skills: list[Path], target: Path) -> None:
    """Link each skill directory into *target* as <name>/."""
    for skill in skills:
        dest = target / skill.name
        if _is_link(dest):
            _safe_remove(dest)
        elif dest.exists():
            print(
                f"⚠  {dest} already exists and is not a link. Skipping.",
                file=sys.stderr,
            )
            continue
        _create_link(skill, dest)


def _install_cursor_rules(skills: list[Path], target: Path) -> None:
    """Convert each SKILL.md into a Cursor .mdc rule file."""
    for skill in skills:
        skill_md = skill / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        meta, body = _split_frontmatter(text)
        description = meta.get("description") or f"Teardrop skill: {skill.name}"
        content = (
            "---\n"
            f"description: {_yaml_quote(description)}\n"
            "alwaysApply: false\n"
            "---\n\n"
            f"{body.lstrip()}"
        )
        out = target / f"teardrop-{skill.name}.mdc"
        out.write_text(content, encoding="utf-8")


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.DOTALL)
    if not match:
        return {}, text
    data: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data, match.group(2)


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _create_link(source: Path, target: Path) -> None:
    """Create a symlink (Unix) or junction (Windows) from *target* → *source*."""
    source = source.resolve()
    if platform.system() == "Windows":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target), str(source)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(
                f"⚠  Junction creation failed for {target.name}: "
                f"{result.stderr.strip() or result.stdout.strip()}",
                file=sys.stderr,
            )
            print("   Falling back to directory copy...", file=sys.stderr)
            _copy_skills(source, target)
    else:
        target.symlink_to(source, target_is_directory=True)


def _copy_skills(source: Path, target: Path) -> None:
    shutil.copytree(source, target, dirs_exist_ok=True)


def _is_link(path: Path) -> bool:
    """Check if *path* is a symlink or Windows junction (cross-Python)."""
    if path.is_symlink():
        return True
    if platform.system() == "Windows" and path.exists():
        try:
            attrs = os.lstat(str(path)).st_file_attributes  # type: ignore[attr-defined]
            return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
        except (AttributeError, OSError):
            return False
    return False


def _safe_remove(path: Path) -> None:
    """Remove a symlink, junction, or directory."""
    if platform.system() == "Windows" and _is_link(path):
        subprocess.run(["cmd", "/c", "rmdir", str(path)], capture_output=True)
    elif path.is_symlink():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()
