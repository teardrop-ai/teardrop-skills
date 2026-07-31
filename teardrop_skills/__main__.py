"""CLI entry: print the installed skills path, list skills, or install into a harness."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from teardrop_skills import __version__, list_harnesses, list_skills, skills_path
from teardrop_skills.harnesses import install_skills


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="teardrop-skills",
        description="Locate, list, and install Teardrop agent skills.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"teardrop-skills {__version__}",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List skill names under the skills path.",
    )

    # Install subcommand.
    subparsers = parser.add_subparsers(dest="command")
    install_parser = subparsers.add_parser(
        "install",
        help="Install skills into an agent harness.",
        description=(
            "Install each teardrop skill into your agent harness "
            "(symlink/junction on native skill harnesses; .mdc conversion for Cursor). "
            "Auto-detects Claude Code, Cline, Copilot, Pi, OpenCode, and Cursor."
        ),
    )
    install_parser.add_argument(
        "--harness",
        "-H",
        help="Target harness name (auto-detected if omitted).",
    )
    install_parser.add_argument(
        "--path",
        "-p",
        type=Path,
        help="Explicit target directory (bypasses harness detection).",
    )
    install_parser.add_argument(
        "--user",
        action="store_true",
        help="Install to the user-level skills directory (e.g. ~/.claude/skills/).",
    )
    install_parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Print what would be done without making changes.",
    )
    install_parser.add_argument(
        "--list-harnesses",
        action="store_true",
        help="List supported agent harnesses and exit.",
    )

    args = parser.parse_args(argv)

    # --- install subcommand ---
    if args.command == "install":
        if args.list_harnesses:
            print("Supported harnesses:")
            for h in list_harnesses():
                print(f"  {h['name']:20s} {h['description']}")
            return 0

        ok = install_skills(
            harness_name=args.harness,
            path=args.path,
            user=args.user,
            dry_run=args.dry_run,
        )
        return 0 if ok else 1

    # --- default: print path ---
    try:
        path = skills_path()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(path)
    if args.list:
        for name in list_skills():
            print(name)

    # Post-install hint on bare invocation (no flags).
    if not args.list and not any(a.startswith("--version") for a in argv or []):
        print(file=sys.stderr)
        print("--- Next steps ---", file=sys.stderr)
        print("1. Run:  teardrop quickstart", file=sys.stderr)
        print("2. Install skills into your agent harness:", file=sys.stderr)
        print("   teardrop-skills install", file=sys.stderr)
        print("   teardrop-skills install --list-harnesses", file=sys.stderr)
        print("   teardrop-skills install --harness claude-code", file=sys.stderr)
        print(file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
