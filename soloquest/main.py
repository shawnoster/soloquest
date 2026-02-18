"""Starforged CLI entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from soloquest.models.character import Character
from soloquest.models.session import Session
from soloquest.state.save import list_saves, load_most_recent, save_game
from soloquest.ui import display


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


def _new_game_flow(data_dir: Path):
    from soloquest.commands.new_character import run_new_character_flow
    from soloquest.engine.truths import load_truth_categories

    truth_categories = load_truth_categories(data_dir)
    return run_new_character_flow(data_dir, truth_categories)


def _show_resume_context(character: Character, session: Session | None) -> None:
    """Show a compact welcome-back snapshot."""
    display.console.print(
        f"  [bold]{character.name}[/bold]"
        + (f"  [dim]«{character.callsign}»[/dim]" if character.callsign else "")
    )
    display.console.print(
        f"  [dim]Health[/dim] {character.health}/5  "
        f"[dim]Spirit[/dim] {character.spirit}/5  "
        f"[dim]Supply[/dim] {character.supply}/5  "
        f"[dim]Momentum[/dim] {character.momentum:+d}"
    )
    display.console.print()
    if session and session.entries:
        display.recent_log(session.entries, n=3)


def main() -> None:
    from soloquest.config import set_adventures_dir

    # Parse command-line arguments
    args = parse_args()

    # Set adventures directory from CLI argument if provided
    if args.adventures_dir:
        set_adventures_dir(args.adventures_dir)

    display.splash()

    data_dir = Path(__file__).parent / "data"

    # Determine startup path
    if args.new or not list_saves():
        if not list_saves():
            display.console.print("  [dim]No saves found. Let's build your world.[/dim]")
            display.console.print()
        result = _new_game_flow(data_dir)
        if result is None:
            display.error("  Character creation cancelled. Exiting.")
            return
        character, vows, dice_mode = result
        session_count = 0
        session = None
        # Save immediately so next launch auto-resumes
        save_game(character, vows, session_count, dice_mode)
    else:
        # Auto-resume most recent save
        most_recent = load_most_recent()
        if most_recent is None:
            display.error("  Save file corrupted. Use --new to start fresh.")
            return
        character, vows, session_count, dice_mode, session = most_recent
        _show_resume_context(character, session)

    # Start the session
    from soloquest.loop import run_session

    run_session(character, vows, session_count, dice_mode, session)


if __name__ == "__main__":
    main()
