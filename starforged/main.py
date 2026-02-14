"""Starforged CLI entry point."""

from __future__ import annotations

from rich.prompt import Prompt

from starforged.engine.dice import DiceMode
from starforged.models.character import Character, Stats
from starforged.models.vow import Vow, VowRank
from starforged.state.save import list_saves, load_game, load_most_recent
from starforged.ui import display


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


def main() -> None:
    display.splash()

    saves = list_saves()
    most_recent = load_most_recent()

    if most_recent:
        character, vows, session_count, dice_mode = most_recent
        display.console.print(
            f"  [dim]Last played:[/dim] [bold]{character.name}[/bold]  Session {session_count}"
        )
        display.console.print()
        display.info("  [r] Resume last session")
        display.info("  [n] New character")
        if len(saves) > 1:
            display.info("  [l] Load different character")
        display.console.print()

        choice = Prompt.ask("  >", default="r").strip().lower()

        if choice == "r":
            pass  # use loaded character
        elif choice == "n":
            character, vows, dice_mode = new_character()
            session_count = 0
        elif choice == "l" and len(saves) > 1:
            for i, name in enumerate(saves, 1):
                display.info(f"  [{i}] {name}")
            raw = Prompt.ask("  Choose character")
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
        display.info("  No saves found. Let's create your character.")
        display.console.print()
        character, vows, dice_mode = new_character()
        session_count = 0

    # Start the session
    from starforged.loop import run_session

    run_session(character, vows, session_count, dice_mode)


if __name__ == "__main__":
    main()
