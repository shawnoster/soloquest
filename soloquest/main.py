"""Starforged CLI entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.prompt import Prompt

from soloquest.engine.dice import DiceMode
from soloquest.models.character import Character
from soloquest.models.vow import Vow
from soloquest.state.save import list_saves, load_game, load_most_recent
from soloquest.ui import display


def new_character() -> tuple[Character, list[Vow], DiceMode] | None:
    """Walk through the full 11-step character creation wizard. Returns None if cancelled."""
    from soloquest.commands.new_character import run_creation_wizard

    data_dir = Path(__file__).parent / "data"
    return run_creation_wizard(data_dir)


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
    return parser.parse_args()


def main() -> None:
    from soloquest.config import get_adventures_dir, set_adventures_dir

    # Parse command-line arguments
    args = parse_args()

    # Set adventures directory from CLI argument if provided
    if args.adventures_dir:
        set_adventures_dir(args.adventures_dir)

    display.splash()

    # Show adventures directory location
    adventures_dir = get_adventures_dir()
    display.console.print(f"  [dim]Adventures directory:[/dim] {adventures_dir}", markup=True)
    display.console.print()

    saves = list_saves()
    most_recent = load_most_recent()

    if most_recent:
        character, vows, session_count, dice_mode, session = most_recent

        # Check if there's an active session to resume
        has_active_session = session is not None and len(session.entries) > 0

        if has_active_session:
            display.console.print(
                f"  [dim]Last played:[/dim] [bold]{character.name}[/bold]  "
                f"Session {session.number} ({len(session.entries)} entries)"
            )
        else:
            display.console.print(
                f"  [dim]Last played:[/dim] [bold]{character.name}[/bold]  Session {session_count}"
            )

        display.console.print()
        display.console.print("  +-- Choose an action ----------------------------+", markup=False)
        display.console.print("  |                                                |", markup=False)

        if has_active_session:
            display.console.print(
                "  |  [r] Resume session (continue)                 |", markup=False
            )
            display.console.print(
                "  |  [s] Start new session                         |", markup=False
            )
        else:
            display.console.print(
                "  |  [r] Continue (new session)                    |", markup=False
            )

        display.console.print("  |  [n] New character                             |", markup=False)
        if len(saves) > 1:
            display.console.print(
                "  |  [l] Load different character                  |", markup=False
            )
        display.console.print("  |                                                |", markup=False)
        display.console.print("  +------------------------------------------------+", markup=False)
        display.console.print()

        choice_options = (
            "r/n" + ("/s" if has_active_session else "") + ("/l" if len(saves) > 1 else "")
        )
        choice = Prompt.ask(f"  Choice ({choice_options})", default="r").strip().lower()

        if choice == "r":
            pass  # use loaded character and session (if any)
        elif choice == "s" and has_active_session:
            # User wants to start a new session, clear the current one
            session = None
        elif choice == "n":
            result = new_character()
            if result is None:
                # User cancelled, resume last session instead
                display.console.print()
                display.info("  Resuming last session...")
            else:
                character, vows, dice_mode = result
                session_count = 0
                session = None
        elif choice == "l" and len(saves) > 1:
            display.console.print()
            display.console.print(
                "  +-- Saved Characters ----------------------------+", markup=False
            )
            display.console.print(
                "  |                                                |", markup=False
            )
            for i, name in enumerate(saves, 1):
                display.console.print(f"  |  [{i}] {name:<43} |", markup=False)
            display.console.print(
                "  |                                                |", markup=False
            )
            display.console.print(
                "  +------------------------------------------------+", markup=False
            )
            display.console.print()
            raw = Prompt.ask("  Choose character (1-" + str(len(saves)) + ")")
            try:
                idx = int(raw) - 1
                char_name = saves[idx]
                character, vows, session_count, dice_mode, session = load_game(char_name)
            except (ValueError, IndexError):
                display.error("Invalid choice, resuming last session.")
        else:
            pass  # default to resume

    else:
        # No existing saves
        display.console.print("  +-- No saves found ------------------------------+", markup=False)
        display.console.print("  |                                                |", markup=False)
        display.console.print("  |  Let's create your character.                  |", markup=False)
        display.console.print("  |                                                |", markup=False)
        display.console.print("  +------------------------------------------------+", markup=False)
        display.console.print()
        result = new_character()
        if result is None:
            # User cancelled but there are no saves to resume
            display.console.print()
            display.error("  Character creation cancelled. No saves to resume. Exiting.")
            return
        character, vows, dice_mode = result
        session_count = 0
        session = None

    # Start the session
    from soloquest.loop import run_session

    run_session(character, vows, session_count, dice_mode, session)


if __name__ == "__main__":
    main()
