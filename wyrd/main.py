"""Starforged CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wyrd.models.session import Session
from wyrd.state.save import (
    list_saves,
    list_saves_paths,
    load_by_name,
    load_most_recent,
    saves_path,
)
from wyrd.state.truths_md import read_adventure_truths, read_truths_md, write_adventure_truths
from wyrd.ui import display
from wyrd.ui.strings import get_string


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="wyrd",
        description="A solo journaling CLI for tabletop RPGs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wyrd                                    # Use default directory
  wyrd -d ~/my-campaigns                  # Use custom directory
  wyrd --adventures-dir ./test-campaign   # Use relative path
  wyrd --new                              # Start a new character
  wyrd oracle action                      # One-liner: roll oracle
  wyrd roll d100                          # One-liner: roll dice
  wyrd --char Robin move "face danger"    # One-liner with named character

For more information: https://github.com/shawnoster/solo-cli
        """,
    )
    parser.add_argument(
        "-d",
        "--adventures-dir",
        type=Path,
        metavar="PATH",
        help="path to adventures directory (saves, sessions, journal)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="start with a new character",
    )
    parser.add_argument(
        "-c",
        "--char",
        metavar="NAME",
        help="character name to load (one-liner mode only)",
    )
    parser.add_argument(
        "oneshot",
        nargs=argparse.REMAINDER,
        help="command + args for one-liner mode, e.g.: oracle action",
    )
    return parser.parse_args()


def _show_resume_context(session: Session | None) -> None:
    """Show recent session log on resume."""
    if session and session.entries:
        display.recent_log(session.entries, n=3)


def main() -> None:
    from wyrd.config import config

    args = parse_args()

    if args.adventures_dir:
        config.set_adventures_dir(args.adventures_dir)

    # --- One-liner mode ---
    if args.oneshot:
        tokens = args.oneshot
        command = tokens[0]
        cmd_args = [t for t in tokens[1:] if not t.startswith("--")]
        cmd_flags = {t.lstrip("-") for t in tokens[1:] if t.startswith("--")}

        if args.char:
            result = load_by_name(args.char, config.saves_dir())
            if result is None:
                saves = list_saves_paths(config.saves_dir())
                names = [s.stem.replace("_", " ").title() for s in saves]
                display.console.print(f"[red]Character '{args.char}' not found.[/red]")
                display.console.print(f"Available: {', '.join(names) or 'none'}")
                sys.exit(1)
            character, vows, session_count, dice_mode, session = result
        else:
            most_recent = load_most_recent()
            if most_recent is None:
                display.error(get_string("startup.corrupted_save"))
                sys.exit(1)
            character, vows, session_count, dice_mode, session = most_recent

        from wyrd.loop import run_oneshot

        sys.exit(
            run_oneshot(
                character, vows, session_count, dice_mode, session, command, cmd_args, cmd_flags
            )
        )

    # --- Interactive session mode ---
    has_saves = bool(list_saves())

    if not args.new and has_saves:
        # Fast path: auto-resume most recent save
        most_recent = load_most_recent()
        if most_recent is None:
            display.splash()
            display.error(get_string("startup.corrupted_save"))
            return
        character, vows, session_count, dice_mode, session = most_recent
        display.splash(character, vows)
        _show_resume_context(session)
    else:
        # Sandbox mode: drop straight into the loop with a placeholder character
        from wyrd.engine.dice import DiceMode
        from wyrd.models.character import Character

        character = Character("Wanderer")
        vows, session_count, dice_mode, session = [], 0, DiceMode.DIGITAL, None
        display.splash()
        display.console.print(get_string("startup.no_save_line1"))
        display.console.print(get_string("startup.no_save_line2"))
        display.console.print()

    # Load truths from adventure directory (campaign-level); migrate from old character save if needed
    truths = read_adventure_truths(config.adventures_dir)
    if truths is None:
        truths = read_truths_md(saves_path(character.name)) or character.truths or []
        if truths:
            write_adventure_truths(truths, config.adventures_dir, character.name)

    # Start the session
    from wyrd.loop import run_session

    run_session(character, vows, session_count, dice_mode, session, truths=truths)


if __name__ == "__main__":
    main()
