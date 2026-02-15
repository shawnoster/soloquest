"""Starforged CLI entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.prompt import Prompt

from soloquest.engine.dice import DiceMode
from soloquest.models.character import Character, Stats
from soloquest.models.vow import Vow, VowRank
from soloquest.state.save import list_saves, load_game, load_most_recent
from soloquest.ui import display


def new_character() -> tuple[Character, list[Vow], DiceMode]:
    """Walk through simple character creation."""
    display.rule("New Character")
    display.console.print()

    name = Prompt.ask("  Character name")
    homeworld = Prompt.ask("  Homeworld or origin")

    display.console.print()
    display.info("  Assign stats (Edge, Heart, Iron, Shadow, Wits).")
    display.info("  Distribute these values: 3, 2, 2, 1, 1")
    display.console.print()

    stat_pool = [3, 2, 2, 1, 1]
    stat_names = ["edge", "heart", "iron", "shadow", "wits"]
    assigned: dict[str, int] = {}
    remaining = list(stat_pool)

    for stat in stat_names:
        display.info(f"  Remaining values: {sorted(remaining, reverse=True)}")
        while True:
            raw = Prompt.ask(f"  {stat.capitalize()}")
            try:
                val = int(raw)
                if val in remaining:
                    assigned[stat] = val
                    remaining.remove(val)
                    break
                display.error(f"  Value {val} not in remaining pool.")
            except ValueError:
                display.error("  Enter a number.")

    stats = Stats(**assigned)

    display.console.print()
    display.info("  Choose 3 assets (type names, e.g. 'ace', 'empath', 'command_ship'):")
    assets: list[str] = []
    while len(assets) < 3:
        raw = Prompt.ask(f"  Asset {len(assets) + 1}")
        if raw.strip():
            assets.append(raw.strip().lower().replace(" ", "_"))

    character = Character(
        name=name,
        homeworld=homeworld,
        stats=stats,
        assets=assets,
    )

    # Background vow
    display.console.print()
    display.info("  Every character begins with a background vow (Epic rank).")
    bg_vow_text = Prompt.ask("  Your background vow")
    vows = [Vow(description=bg_vow_text, rank=VowRank.EPIC)]

    # Dice mode
    display.console.print()
    display.info("  Dice mode:")
    display.info("    [1] Digital — CLI rolls for you")
    display.info("    [2] Physical — you roll, CLI prompts for values")
    display.info("    [3] Mixed — digital by default, --manual flag per command")
    raw = Prompt.ask("  Choose", default="1")
    mode_map = {"1": DiceMode.DIGITAL, "2": DiceMode.PHYSICAL, "3": DiceMode.MIXED}
    dice_mode = mode_map.get(raw, DiceMode.DIGITAL)

    display.console.print()
    display.success(f"Character created: {name}")

    return character, vows, dice_mode


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
        character, vows, session_count, dice_mode = most_recent
        display.console.print(
            f"  [dim]Last played:[/dim] [bold]{character.name}[/bold]  Session {session_count}"
        )
        display.console.print()
        display.console.print("  +-- Choose an action ----------------------------+", markup=False)
        display.console.print("  |                                                |", markup=False)
        display.console.print("  |  [r] Resume last session                       |", markup=False)
        display.console.print("  |  [n] New character                             |", markup=False)
        if len(saves) > 1:
            display.console.print(
                "  |  [l] Load different character                  |", markup=False
            )
        display.console.print("  |                                                |", markup=False)
        display.console.print("  +------------------------------------------------+", markup=False)
        display.console.print()

        choice = (
            Prompt.ask("  Choice (r/n" + ("/l" if len(saves) > 1 else "") + ")", default="r")
            .strip()
            .lower()
        )

        if choice == "r":
            pass  # use loaded character
        elif choice == "n":
            character, vows, dice_mode = new_character()
            session_count = 0
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
                character, vows, session_count, dice_mode = load_game(char_name)
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
        character, vows, dice_mode = new_character()
        session_count = 0

    # Start the session
    from soloquest.loop import run_session

    run_session(character, vows, session_count, dice_mode)


if __name__ == "__main__":
    main()
