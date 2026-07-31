"""teardrop-skills: agent instruction packs for Teardrop CLI workflows."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

__version__ = "0.2.0"

__all__ = ["__version__", "skills_path", "list_skills"]

_SKILL_NAMES = (
    "install",
    "publish-tool",
    "run-agent",
    "manage-billing",
    "discover-marketplace",
    "manage-org",
    "withdraw-earnings",
)


def skills_path() -> Path:
    """Return the filesystem path to the installed skills directory.

    Skills ship inside the package as ``teardrop_skills/skills/<name>/SKILL.md``.
    Symlink or copy that tree into your agent harness skills folder.
    """
    # Prefer the packaged location (installed wheel / editable with force-include).
    try:
        root = resources.files("teardrop_skills").joinpath("skills")
        path = Path(str(root))
        if path.is_dir():
            return path.resolve()
    except (TypeError, FileNotFoundError, ModuleNotFoundError):
        pass

    # Editable / source checkout: repo-root skills/ next to the package dir.
    repo_skills = Path(__file__).resolve().parent.parent / "skills"
    if repo_skills.is_dir():
        return repo_skills

    raise FileNotFoundError(
        "Could not locate teardrop-skills data. Reinstall with: pip install teardrop-skills"
    )


def list_skills() -> list[str]:
    """Return the canonical skill directory names shipped with this package."""
    root = skills_path()
    found = sorted(
        p.name for p in root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )
    return found if found else list(_SKILL_NAMES)
