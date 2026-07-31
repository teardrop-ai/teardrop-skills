"""Smoke tests: shipped skills exist and have valid YAML frontmatter."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

EXPECTED_SKILLS = (
    "install",
    "publish-tool",
    "run-agent",
    "manage-billing",
    "discover-marketplace",
    "manage-org",
    "withdraw-earnings",
)

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_simple_yaml_frontmatter(text: str) -> dict[str, str]:
    """Parse the minimal key: value frontmatter used by SKILL.md files."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise AssertionError("Missing or malformed YAML frontmatter (--- ... ---)")

    data: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise AssertionError(f"Invalid frontmatter line: {raw_line!r}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data


@pytest.fixture(scope="module")
def skill_files() -> dict[str, Path]:
    files = {name: SKILLS_DIR / name / "SKILL.md" for name in EXPECTED_SKILLS}
    return files


def test_expected_skill_count() -> None:
    assert len(EXPECTED_SKILLS) == 7


def test_skills_directory_exists() -> None:
    assert SKILLS_DIR.is_dir(), f"Missing skills directory: {SKILLS_DIR}"


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_skill_file_exists(name: str, skill_files: dict[str, Path]) -> None:
    path = skill_files[name]
    assert path.is_file(), f"Missing SKILL.md for {name}: {path}"


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_skill_frontmatter_valid(name: str, skill_files: dict[str, Path]) -> None:
    text = skill_files[name].read_text(encoding="utf-8")
    meta = _parse_simple_yaml_frontmatter(text)

    assert "name" in meta, f"{name}: frontmatter missing 'name'"
    assert "description" in meta, f"{name}: frontmatter missing 'description'"
    assert meta["name"] == name, f"{name}: name field {meta['name']!r} != directory"
    assert meta["description"], f"{name}: description must be non-empty"
    assert "applyTo" in meta, f"{name}: frontmatter missing 'applyTo'"


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_skill_has_required_sections(name: str, skill_files: dict[str, Path]) -> None:
    text = skill_files[name].read_text(encoding="utf-8")
    for heading in ("## Purpose", "## Prerequisites", "## Workflow", "## Reference"):
        assert heading in text, f"{name}: missing section {heading}"


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_skill_has_missing_inputs_section(name: str, skill_files: dict[str, Path]) -> None:
    text = skill_files[name].read_text(encoding="utf-8")
    assert "## Missing inputs" in text, f"{name}: missing 'Missing inputs & fallbacks' section"


def test_no_unexpected_top_level_skills() -> None:
    if not SKILLS_DIR.is_dir():
        pytest.skip("skills dir missing")
    found = sorted(p.name for p in SKILLS_DIR.iterdir() if p.is_dir())
    assert found == sorted(EXPECTED_SKILLS), f"Unexpected skills dirs: {found}"


def test_package_skills_path_importable() -> None:
    from teardrop_skills import __version__, list_skills, skills_path

    assert __version__
    path = skills_path()
    assert path.is_dir()
    names = list_skills()
    assert set(EXPECTED_SKILLS).issubset(set(names))
    for name in EXPECTED_SKILLS:
        assert (path / name / "SKILL.md").is_file()


def test_version_consistency() -> None:
    """pyproject.toml version matches teardrop_skills.__version__."""
    import tomllib

    from teardrop_skills import __version__ as pkg_version

    pyproject = ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["version"] == pkg_version, (
        f"pyproject.toml version {data['project']['version']} != "
        f"__version__ {pkg_version}"
    )


def test_cli_anchors_are_documented_slugs() -> None:
    """Every cli-reference.md#anchor used in skills must be a known ToC slug."""
    known = {
        "authentication",
        "running-agents",
        "chat-sessions",
        "schedules",
        "event-triggers",
        "billing--credits",
        "tool-management",
        "marketplace",
        "earnings--withdrawals",
        "llm-configuration",
        "mcp-servers",
        "models--benchmarks",
        "configuration-file",
        "exit-codes",
        "development",
    }
    anchor_re = re.compile(
        r"cli-reference\.md#([a-z0-9-]+)",
        re.IGNORECASE,
    )
    unknown: list[str] = []
    for name in EXPECTED_SKILLS:
        text = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
        for slug in anchor_re.findall(text):
            if slug not in known:
                unknown.append(f"{name}: #{slug}")
    assert not unknown, f"Unknown CLI doc anchors: {unknown}"
