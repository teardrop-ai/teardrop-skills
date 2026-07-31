# teardrop-skills

Agent instruction packs for [Teardrop](https://teardrop.dev) CLI workflows.

Each skill is a thin orchestration layer over verified `teardrop-cli` commands.
Skills tell an AI harness *what to run and in what order*; they do not duplicate
the full CLI reference.

```bash
pip install teardrop-skills
teardrop-skills            # prints installed skills path + next steps
teardrop-skills --list     # lists skill names
```

Requires Python ≥ 3.11. `teardrop-cli` is installed automatically as a dependency (compatible with `teardrop-cli >=0.3.2, <0.4`).

---

## Skills

| Skill | Purpose | Primary CLI surface |
|-------|---------|---------------------|
| `install` | Install CLI, signup/login, session checks | `auth`, `quickstart` |
| `publish-tool` | Scaffold, probe, publish, manage tools | `tools`, `agent-tools` |
| `run-agent` | One-shot runs, chat, schedules, event triggers | `run`, `chat`, `schedules`, `event-triggers` |
| `manage-billing` | Balance + usage; dashboard top-up link | `balance`, `usage` |
| `discover-marketplace` | Browse/search/subscribe marketplace tools | `marketplace` |
| `manage-org` | LLM/BYOK, MCP servers, benchmarks, config | `llm-config`, `mcp`, `models`, `config` |
| `withdraw-earnings` | Author earnings balance and USDC withdrawals | `earnings` |

**Not included:** A2A delegation — no `teardrop a2a ...` CLI surface exists yet.

---

## Install

```bash
pip install teardrop-skills
```

This also installs `teardrop-cli` automatically. Verify:

```bash
teardrop --version
teardrop-skills --version
```

From a source checkout:

```bash
pip install -e ".[dev]"
```

### Locate skills on disk

```bash
teardrop-skills
# e.g. .../site-packages/teardrop_skills/skills
```

Or from Python:

```python
from teardrop_skills import skills_path, list_skills

print(skills_path())
print(list_skills())
```

### Wire into an agent harness

Symlink or copy the skills tree into your harness skills directory:

```bash
# example: link the whole pack
ln -s "$(teardrop-skills)" /path/to/harness/skills/teardrop

# or copy a single skill
cp -r "$(teardrop-skills)/install" /path/to/harness/skills/install
```

On Windows (PowerShell):

```powershell
$src = teardrop-skills
New-Item -ItemType Junction -Path ".\harness-skills\teardrop" -Target $src
```

Each skill is a folder containing `SKILL.md` with YAML frontmatter
(`name`, `description`, `applyTo`).

---

## First-time publish chain

For a user publishing their first tool, the skills chain in order:

1. **`install`** — install CLI, authenticate (SIWE preferred — generates a wallet)
2. **`publish-tool`** — scaffold, probe, publish with settlement wallet
3. **`run-agent`** — test the tool with a quick agent run
4. **`manage-billing`** — check credits if runs fail
5. **`withdraw-earnings`** — only after earnings accumulate

---

## SKILL format

```markdown
---
name: skill-name
description: One-line purpose
applyTo: "**/*"
---

## Purpose
...

## Prerequisites
...

## Workflow
1. ...

## Reference
- CLI anchors only (no doc duplication)

## Troubleshooting
...
```

Rules:

- Every `teardrop` command referenced must exist in the current CLI release.
- Link CLI docs by anchor; do not paste full flag tables.
- Exit codes: `0` success, `1` error, `2` invalid input.

---

## Source of truth

- CLI README: https://github.com/teardrop-ai/teardrop-cli/blob/main/README.md
- CLI reference: https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md

| Skill | Doc anchors |
|-------|-------------|
| `install` | [#authentication](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#authentication) |
| `publish-tool` | [#tool-management](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#tool-management) |
| `run-agent` | [#running-agents](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#running-agents), [#chat-sessions](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#chat-sessions), [#schedules](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#schedules), [#event-triggers](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#event-triggers) |
| `manage-billing` | [#billing--credits](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#billing--credits) |
| `discover-marketplace` | [#marketplace](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#marketplace) |
| `manage-org` | [#llm-configuration](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#llm-configuration), [#mcp-servers](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#mcp-servers), [#models--benchmarks](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#models--benchmarks), [#configuration-file](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#configuration-file) |
| `withdraw-earnings` | [#earnings--withdrawals](https://github.com/teardrop-ai/teardrop-cli/blob/main/docs/cli-reference.md#earnings--withdrawals) |

---

## Development

```bash
pip install -e ".[dev]"
pytest
```

Smoke tests assert all seven `SKILL.md` files exist, YAML frontmatt2r parses, and
required keys (`name`, `description`) are present.

---

## Versioning

Independent semver from `teardrop-cli`. Current version: **0.2.0**.

---

## License

MIT. See [LICENSE](LICENSE).
