"""Starforged CLI entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from soloquest.models.session import Session
from soloquest.state.save import list_saves, load_most_recent
from soloquest.ui import display
from soloquest.ui.strings import get_string


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="soloquest",
        description="A solo journaling CLI for tabletop RPGs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  soloquest                                    # Use default directory
  soloquest -d ~/my-campaigns                  # Use custom directory
  soloquest --adventures-dir ./test-campaign   # Use relative path
  soloquest --new                              # Start a new character

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
    return parser.parse_args()


def _show_resume_context(session: Session | None) -> None:
    """Show recent session log on resume."""
    if session and session.entries:
        display.recent_log(session.entries, n=3)


def main() -> None:
    from soloquest.config import config

    args = parse_args()

    if args.adventures_dir:
        config.set_adventures_dir(args.adventures_dir)

    # Determine startup path
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
        from soloquest.engine.dice import DiceMode
        from soloquest.models.character import Character

        character = Character("Wanderer")
        vows, session_count, dice_mode, session = [], 0, DiceMode.DIGITAL, None
        display.splash()
        display.console.print(get_string("startup.no_save_line1"))
        display.console.print(get_string("startup.no_save_line2"))
        display.console.print()

    # Start the session
    from soloquest.loop import run_session

    run_session(character, vows, session_count, dice_mode, session)


if __name__ == "__main__":
    main()
