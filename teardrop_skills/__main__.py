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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
