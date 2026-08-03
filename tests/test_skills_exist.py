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
    assert meta.get("license") == "MIT", f"{name}: frontmatter license must be MIT"


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_skill_has_required_sections(name: str, skill_files: dict[str, Path]) -> None:
    text = skill_files[name].read_text(encoding="utf-8")
    for heading in ("## Purpose", "## Prerequisites", "## Workflow", "## Reference"):
        assert heading in text, f"{name}: missing section {heading}"


@pytest.mark.parametrize("name", EXPECTED_SKILLS)
def test_skill_has_missing_inputs_section(
    name: str, skill_files: dict[str, Path]
) -> None:
    text = skill_files[name].read_text(encoding="utf-8")
    assert "## Missing inputs" in text, (
        f"{name}: missing 'Missing inputs & fallbacks' section"
    )


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


# ---------------------------------------------------------------------------
# Harness detection & installation tests
# ---------------------------------------------------------------------------


class TestHarnessDetection:
    """Test harness detection logic using temporary directories."""

    def test_list_harnesses_returns_expected(self) -> None:
        from teardrop_skills.harnesses import list_harnesses

        result = list_harnesses()
        names = {h["name"] for h in result}
        assert {
            "claude-code",
            "cline",
            "copilot",
            "pi",
            "opencode",
            "cursor",
            "path",
        }.issubset(names)

    def test_detect_none_when_no_harness(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import detect_harness

        assert detect_harness(cwd=tmp_path) is None

    def test_detect_claude_code_project(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import ClaudeCodeHarness, detect_harness

        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        detected = detect_harness(cwd=tmp_path)
        assert detected is ClaudeCodeHarness

    def test_detect_claude_code_personal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from teardrop_skills.harnesses import ClaudeCodeHarness, detect_harness

        home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: home)
        skills_dir = home / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        detected = detect_harness(cwd=tmp_path)
        assert detected is ClaudeCodeHarness

    def test_detect_cline(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import ClineHarness, detect_harness

        skills_dir = tmp_path / ".cline" / "skills"
        skills_dir.mkdir(parents=True)

        detected = detect_harness(cwd=tmp_path)
        assert detected is ClineHarness

    def test_detect_copilot(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import CopilotHarness, detect_harness

        (tmp_path / ".github" / "skills").mkdir(parents=True)
        assert detect_harness(cwd=tmp_path) is CopilotHarness

    def test_detect_pi(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import PiHarness, detect_harness

        (tmp_path / ".pi" / "skills").mkdir(parents=True)
        assert detect_harness(cwd=tmp_path) is PiHarness

    def test_detect_opencode(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import OpenCodeHarness, detect_harness

        (tmp_path / ".opencode" / "skills").mkdir(parents=True)
        assert detect_harness(cwd=tmp_path) is OpenCodeHarness

    def test_detect_cursor(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import CursorHarness, detect_harness

        (tmp_path / ".cursor" / "rules").mkdir(parents=True)
        assert detect_harness(cwd=tmp_path) is CursorHarness

    def test_detect_by_name(self) -> None:
        from teardrop_skills.harnesses import (
            ClaudeCodeHarness,
            ClineHarness,
            CopilotHarness,
            CursorHarness,
            OpenCodeHarness,
            PiHarness,
            detect_harness,
        )

        assert detect_harness(name="claude-code") is ClaudeCodeHarness
        assert detect_harness(name="cline") is ClineHarness
        assert detect_harness(name="copilot") is CopilotHarness
        assert detect_harness(name="pi") is PiHarness
        assert detect_harness(name="opencode") is OpenCodeHarness
        assert detect_harness(name="cursor") is CursorHarness
        assert detect_harness(name="unknown") is None

    def test_claude_code_install_path_project(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import ClaudeCodeHarness

        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        result = ClaudeCodeHarness.install_path(cwd=tmp_path)
        assert result == skills_dir

    def test_claude_code_install_path_user(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from teardrop_skills.harnesses import ClaudeCodeHarness

        home = tmp_path / "home"
        monkeypatch.setattr(Path, "home", lambda: home)

        result = ClaudeCodeHarness.install_path(cwd=tmp_path, user=True)
        assert result == home / ".claude" / "skills"

    def test_cline_install_path(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import ClineHarness

        skills_dir = tmp_path / ".cline" / "skills"
        skills_dir.mkdir(parents=True)

        result = ClineHarness.install_path(cwd=tmp_path)
        assert result == skills_dir

    def test_opencode_install_path(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import OpenCodeHarness

        assert (
            OpenCodeHarness.install_path(cwd=tmp_path)
            == tmp_path / ".opencode" / "skills"
        )


class TestHarnessInstall:
    """Test the install flow."""

    def _make_source(self, tmp_path: Path) -> Path:
        source = tmp_path / "source-skills"
        for name in ("install", "run-agent"):
            skill = source / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Test {name}\n---\n# {name}\n",
                encoding="utf-8",
            )
        return source

    def test_dry_run_prints_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        from teardrop_skills.harnesses import ClaudeCodeHarness

        source = self._make_source(tmp_path)
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        ClaudeCodeHarness.install(source, cwd=tmp_path, dry_run=True)
        captured = capsys.readouterr()
        assert "dry-run" in captured.out
        assert "install/" in captured.out
        assert "run-agent/" in captured.out

    def test_install_creates_per_skill_links(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import ClaudeCodeHarness

        source = self._make_source(tmp_path)
        target_dir = tmp_path / ".claude" / "skills"
        target_dir.mkdir(parents=True)

        ClaudeCodeHarness.install(source, cwd=tmp_path)

        # Must be top-level skill dirs, NOT nested under teardrop/
        assert not (target_dir / "teardrop").exists()
        for name in ("install", "run-agent"):
            skill_path = target_dir / name
            assert skill_path.exists(), f"Expected {skill_path}"
            assert (skill_path / "SKILL.md").is_file()

    def test_install_opencode_layout(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import OpenCodeHarness

        source = self._make_source(tmp_path)
        OpenCodeHarness.install(source, cwd=tmp_path)
        target = tmp_path / ".opencode" / "skills"
        assert (target / "install" / "SKILL.md").is_file()
        assert (target / "run-agent" / "SKILL.md").is_file()

    def test_install_cursor_writes_mdc(self, tmp_path: Path) -> None:
        from teardrop_skills.harnesses import CursorHarness

        source = self._make_source(tmp_path)
        CursorHarness.install(source, cwd=tmp_path)
        rules = tmp_path / ".cursor" / "rules"
        install_mdc = rules / "teardrop-install.mdc"
        assert install_mdc.is_file()
        text = install_mdc.read_text(encoding="utf-8")
        assert "alwaysApply: false" in text
        assert "description:" in text
        assert "# install" in text

    def test_install_skills_api_dry_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test the top-level install_skills() with dry_run."""
        from teardrop_skills.harnesses import install_skills

        source = self._make_source(tmp_path)
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        def fake_skills_path() -> Path:
            return source

        import teardrop_skills

        monkeypatch.setattr(teardrop_skills, "skills_path", fake_skills_path)

        result = install_skills(cwd=tmp_path, dry_run=True)
        assert result is True


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
