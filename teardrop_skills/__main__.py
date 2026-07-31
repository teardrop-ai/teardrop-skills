"""CLI entry: print the installed skills path (and optional listing)."""

from __future__ import annotations

import argparse
import sys

from teardrop_skills import __version__, list_skills, skills_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="teardrop-skills",
        description="Locate and list Teardrop agent skills installed with this package.",
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
    args = parser.parse_args(argv)

    try:
        path = skills_path()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(path)
    if args.list:
        for name in list_skills():
            print(name)

    # Post-install hint on first run (no flags).
    if not args.list and not any(a.startswith("--version") for a in argv or []):
        print(file=sys.stderr)
        print("--- Next steps ---", file=sys.stderr)
        print("1. Run:  teardrop quickstart", file=sys.stderr)
        print("2. Symlink or copy this skills folder into your agent harness.", file=sys.stderr)
        print("   Example:  ln -s <path> /path/to/harness/skills/teardrop", file=sys.stderr)
        print("   Windows:  New-Item -ItemType Junction -Path .\\harness\\teardrop -Target <path>", file=sys.stderr)
        print(file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
