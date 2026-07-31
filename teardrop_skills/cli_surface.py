"""CLI surface introspection for teardrop-skills.

This module is the security- and drift-critical core of the production
readiness gates. It answers two questions without ever executing skill text:

1. Which ``teardrop ...`` commands does a skill reference?
2. Do those commands (and their flags) actually exist in the *installed*
   ``teardrop-cli`` command tree?

We introspect the Click/Typer application **in-process** (importing
``teardrop_cli.cli.app``) rather than shelling out to ``teardrop --help`` and
parsing text. This avoids:

* shell interpolation of untrusted skill content (no ``shell=True``),
* network calls, authentication, or any mutating side effects,
* dependence on help-text formatting that can drift independently of the CLI.

The CLI is a Click ``LazyGroup``: subcommands are imported only when invoked.
Our walker force-resolves lazy subcommands so option tables are complete.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Command extraction from skill markdown
# ---------------------------------------------------------------------------

# Only fenced ```bash / ```sh / ``` blocks are scanned. Prose references to
# "teardrop auth status" inside sentences are intentionally ignored — they are
# not executable instructions and would create false positives.
_FENCE_RE = re.compile(
    r"```(?:bash|sh|console|shell|zsh)?\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

# A teardrop invocation begins with "teardrop" (optionally after a shell
# prompt char). We capture the full command line.
_CMD_RE = re.compile(r"(?:^|\n)\s*[$>]?\s*(teardrop\b.*?)(?=\n|$)")

# Tokens that are clearly not part of the command surface.
_PLACEHOLDER_RE = re.compile(r"^<.*>$")
_INLINE_COMMENT_RE = re.compile(r"\s+#.*$")


@dataclass
class SkillCommand:
    """A normalized teardrop command referenced by a skill."""

    raw: str
    tokens: list[str]
    subcommands: list[str]  # e.g. ["auth", "login"]
    flags: list[str]  # e.g. ["--email", "--siwe"]
    source_file: Path | None = None
    line: int = 0


def _strip_inline_comment(line: str) -> str:
    # Only strip a trailing comment if there is whitespace before '#'.
    return _INLINE_COMMENT_RE.sub("", line).rstrip()


def extract_skill_commands(text: str, source_file: Path | None = None) -> list[SkillCommand]:
    """Extract normalized ``teardrop`` commands from skill markdown *text*.

    Only fenced code blocks are scanned. Placeholders (``<...>``), quoted
    JSON literals, and inline comments are dropped so the resulting surface
    reflects command/flag structure, not example values.
    """
    commands: list[SkillCommand] = []
    for fence in _FENCE_RE.findall(text):
        for line in fence.splitlines():
            line = _strip_inline_comment(line)
            m = _CMD_RE.search(line)
            if not m:
                continue
            raw = m.group(1).strip()
            if not raw.startswith("teardrop"):
                continue
            tokens = _tokenize(raw)
            if not tokens:
                continue
            subcommands, flags = _split_tokens(tokens[1:])
            commands.append(
                SkillCommand(
                    raw=raw,
                    tokens=tokens,
                    subcommands=subcommands,
                    flags=flags,
                    source_file=source_file,
                )
            )
    return commands


def _tokenize(raw: str) -> list[str]:
    """Split a command line into tokens, dropping placeholders and literals."""
    out: list[str] = []
    for tok in raw.split():
        # Drop shell continuation backslashes.
        tok = tok.rstrip("\\")
        if not tok:
            continue
        # Drop quoted JSON / string literals and angle-bracket placeholders.
        if tok.startswith("{") or tok.startswith("'{"):
            continue
        if _PLACEHOLDER_RE.match(tok):
            continue
        # Keep flags and bare words; strip surrounding single quotes only for
        # value tokens (flags must keep their leading dashes).
        if tok.startswith("-"):
            out.append(tok)
        else:
            out.append(tok.strip("'\""))
    return out


def _split_tokens(args: list[str]) -> tuple[list[str], list[str]]:
    """Partition args into subcommand words vs. flag tokens.

    Heuristic: a token starting with ``-`` is a flag. A token containing ``=``
    whose left side starts with ``-`` is a flag with inline value. The first
    run of non-flag tokens after ``teardrop`` are subcommands; later non-flag
    tokens are positional arguments and are ignored for surface validation.
    """
    subcommands: list[str] = []
    flags: list[str] = []
    seen_subcommand = False
    for tok in args:
        if tok.startswith("-"):
            # Normalize "--flag=value" to "--flag".
            flag = tok.split("=", 1)[0]
            flags.append(flag)
            seen_subcommand = True
        else:
            if not seen_subcommand:
                subcommands.append(tok)
            # else: positional argument — ignored
    return subcommands, flags


# ---------------------------------------------------------------------------
# In-process Click/Typer tree walking
# ---------------------------------------------------------------------------


@dataclass
class Node:
    """A node in the resolved CLI command tree."""

    name: str
    is_group: bool
    children: dict[str, "Node"] = field(default_factory=dict)
    options: set[str] = field(default_factory=set)


def _collect_option_names(cmd: Any) -> set[str]:
    """Return the set of long/short option strings declared by *cmd*."""
    opts: set[str] = set()
    params = getattr(cmd, "params", None) or []
    for p in params:
        for opt in getattr(p, "opts", []) or []:
            opts.add(opt)
        for opt in getattr(p, "secondary_opts", []) or []:
            opts.add(opt)
    return opts


def _resolve_lazy_subcommands(cmd: Any) -> None:
    """Force-import every lazy subcommand declared on a Click LazyGroup.

    ``teardrop-cli`` uses a ``LazyGroup`` whose ``commands`` mapping stays
    empty until a subcommand is resolved via ``get_command``. We drive the
    public ``list_commands`` / ``get_command`` API with a throwaway context so
    the group's ``commands`` dict is populated and option tables are complete
    for validation.
    """
    if not hasattr(cmd, "list_commands") or not hasattr(cmd, "get_command"):
        return
    try:
        import click
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolation():
            ctx = click.Context(cmd)  # type: ignore[arg-type]
            for name in cmd.list_commands(ctx):
                try:
                    sub = cmd.get_command(ctx, name)
                except Exception:
                    # A subcommand that fails to load is skipped; validation
                    # will then report it as missing rather than crashing.
                    continue
                if sub is not None:
                    # LazyGroup does not cache the resolved command, so we
                    # populate ``commands`` ourselves for the walker.
                    cmd.commands[name] = sub
    except Exception:
        pass


def build_cli_tree(app: Any) -> Node:
    """Build a :class:`Node` tree from a Click/Typer application *app*."""
    root = Node(name="teardrop", is_group=True)
    root.options = _collect_option_names(app)
    _resolve_lazy_subcommands(app)
    _walk(app, root)
    return root


def _walk(cmd: Any, node: Node) -> None:
    """Recursively populate *node*'s children from *cmd*'s subcommands."""
    _resolve_lazy_subcommands(cmd)
    commands = getattr(cmd, "commands", None)
    if not commands:
        return
    for name, sub in commands.items():
        _resolve_lazy_subcommands(sub)
        child = Node(
            name=name,
            is_group=bool(getattr(sub, "commands", None)),
            options=_collect_option_names(sub),
        )
        node.children[name] = child
        if child.is_group:
            _walk(sub, child)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@dataclass
class DriftFinding:
    command: SkillCommand
    message: str


def validate_commands(commands: list[SkillCommand], tree: Node) -> list[DriftFinding]:
    """Validate *commands* against the resolved CLI *tree*.

    Returns a list of :class:`DriftFinding` for every command whose
    subcommand path or flags are not present in the installed CLI.
    """
    findings: list[DriftFinding] = []
    for cmd in commands:
        # Greedily walk the subcommand path. We consume tokens as subcommands
        # only while they resolve to a child of a *group* node. Once we reach a
        # leaf command (is_group=False), every remaining non-flag token is a
        # positional argument (e.g. a prompt string, an amount, a tool name) and
        # must NOT be treated as a subcommand. This avoids false positives on
        # commands like ``teardrop run "What is the price?"`` or
        # ``teardrop earnings withdraw 10.00``.
        node = tree
        path: list[str] = []
        i = 0
        n = len(cmd.subcommands)
        while i < n and node.is_group:
            tok = cmd.subcommands[i]
            child = node.children.get(tok)
            if child is None:
                break
            path.append(tok)
            node = child
            i += 1

        # If we stopped because a token did not resolve while we were still
        # inside a group, that token is a genuinely unknown subcommand.
        if i < n and node.is_group:
            unknown = cmd.subcommands[i]
            findings.append(
                DriftFinding(
                    command=cmd,
                    message=(
                        f"unknown subcommand path 'teardrop {' '.join(path + [unknown])}' "
                        f"(stopped at {unknown!r})"
                    ),
                )
            )
            continue

        # Path resolved (or ended at a leaf). Check flags against the deepest
        # resolved node's options.
        for flag in cmd.flags:
            if flag not in node.options:
                findings.append(
                    DriftFinding(
                        command=cmd,
                        message=(
                            f"unknown flag {flag!r} for "
                            f"'teardrop {' '.join(cmd.subcommands)}'"
                        ),
                    )
                )
    return findings


def load_cli_tree() -> Node:
    """Import the installed ``teardrop-cli`` app and build its tree.

    Raises ``ImportError`` if ``teardrop-cli`` is not installed.
    """
    from teardrop_cli import cli as _cli  # type: ignore

    return build_cli_tree(_cli.app)
