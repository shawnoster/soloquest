"""Full 10-step character creation wizard for Ironsworn: Starforged (p.103–112)."""

from __future__ import annotations

import random
import tomllib
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from soloquest.commands.truths import run_truths_wizard
from soloquest.engine.assets import load_assets
from soloquest.engine.dice import DiceMode
from soloquest.models.asset import Asset, CharacterAsset
from soloquest.models.character import Character, Stats
from soloquest.models.vow import Vow, VowRank
from soloquest.ui import display


def _init_asset_tracks(char_asset: CharacterAsset, assets: dict[str, Asset]) -> None:
    """Initialise track_values to max for all tracks not yet set."""
    defn = assets.get(char_asset.asset_key)
    if defn:
        for track_name, (_, max_val) in defn.tracks.items():
            if track_name not in char_asset.track_values:
                char_asset.track_values[track_name] = max_val


# ── Oracle tables (loaded from TOML data file) ────────────────────────────────

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_creation_tables() -> dict[str, list[tuple]]:
    """Load character creation oracle tables from TOML."""
    toml_path = _DATA_DIR / "character_creation.toml"
    with open(toml_path, "rb") as f:
        raw = tomllib.load(f)
    tables: dict[str, list[tuple]] = {}
    for key, section in raw.items():
        tables[key] = [tuple(row) for row in section["results"]]
    return tables


_TABLES = _load_creation_tables()
BACKSTORY_TABLE: list[tuple[int, int, str]] = _TABLES["backstory"]
STARSHIP_HISTORY_TABLE: list[tuple[int, int, str]] = _TABLES["starship_history"]
STARSHIP_QUIRK_TABLE: list[tuple[int, int, str]] = _TABLES["starship_quirk"]
BACKGROUND_PATHS_TABLE: list[tuple[int, int, str, str]] = _TABLES["background_paths"]


def _roll_table(table: list[tuple]) -> tuple:
    """Roll d100 and return the matching row from a table."""
    roll = random.randint(1, 100)
    for row in table:
        if row[0] <= roll <= row[1]:
            return (roll, *row[2:])
    return (roll, *table[-1][2:])


class AssetCompleter(Completer):
    """Completer for asset names during character creation."""

    def __init__(self, assets: dict[str, Asset]):
        self.assets = assets

    def get_completions(self, document, complete_event):
        current_arg = document.text_before_cursor.strip()

        completions = []
        for key, asset in self.assets.items():
            asset_name = asset.name if hasattr(asset, "name") else key
            key_normalized = key.replace("_", " ").replace("-", " ")
            name_normalized = asset_name.lower().replace("_", " ").replace("-", " ")
            arg_normalized = current_arg.lower().replace("_", " ").replace("-", " ")

            if (
                not current_arg
                or arg_normalized in key_normalized
                or arg_normalized in name_normalized
            ):
                completions.append(
                    Completion(
                        text=asset_name,
                        start_position=-len(current_arg) if current_arg else 0,
                    )
                )

        yield from sorted(completions, key=lambda c: c.text)


def _prompt_oracle_roll(table: list[tuple], table_name: str) -> None:
    """Offer to roll on an oracle table and display the result."""
    roll_it = Confirm.ask(f"  Roll on the {table_name} table?", default=False)
    if roll_it:
        result = _roll_table(table)
        roll = result[0]
        text = result[1]
        display.oracle_result_panel(table_name, roll, text)


def _prompt_paths(available_assets: dict[str, Asset]) -> list[CharacterAsset] | None:
    """Prompt for 2 path assets. Returns None if cancelled."""
    paths = {k: v for k, v in available_assets.items() if v.category == "path"}
    path_completer = AssetCompleter(paths)
    path_session = PromptSession(completer=path_completer)

    display.console.print()
    display.console.print(
        "  [dim]Paths represent your background. Modules and companions come later.[/dim]"
    )
    display.console.print()
    display.info(
        "  Available path categories include: Archer, Ace, Empath, Infiltrator, and many more."
    )

    # Show the full background paths table
    display.console.print()
    for idx, (_lo, _hi, background, suggestion) in enumerate(BACKGROUND_PATHS_TABLE, start=1):
        display.console.print(f"  [dim][{idx:>2}][/dim]  {background:<28}[dim]{suggestion}[/dim]")
    display.console.print()

    # Inspiration prompt
    try:
        raw = (
            Prompt.ask(
                "  Need inspiration? (1–20, r to roll, Enter to skip)",
                default="",
                show_default=False,
            )
            .strip()
            .lower()
        )
    except (KeyboardInterrupt, EOFError):
        return None

    if raw == "r":
        result = _roll_table(BACKGROUND_PATHS_TABLE)
        roll, background, suggestion = result
        display.console.print(
            Panel(
                f"[dim]{roll}[/dim]  →  [bold]{background}[/bold]\n[dim]Suggested paths: {suggestion}[/dim]",
                title="[bold]BACKGROUND PATHS[/bold]",
                border_style="bright_cyan",
            )
        )
    elif raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(BACKGROUND_PATHS_TABLE):
            lo, hi, background, suggestion = BACKGROUND_PATHS_TABLE[idx]
            display.console.print(
                Panel(
                    f"[bold]{background}[/bold]\n[dim]Suggested paths: {suggestion}[/dim]",
                    title="[bold]BACKGROUND PATHS[/bold]",
                    border_style="bright_cyan",
                )
            )

    chosen_paths: list[str] = []
    for i in range(1, 3):
        while True:
            try:
                raw = path_session.prompt(f"  Path {i}: ")
            except (KeyboardInterrupt, EOFError):
                return None
            key = raw.strip().lower().replace(" ", "_").replace("-", "_")
            if not key:
                display.error("  Path cannot be empty.")
                continue
            if key not in paths:
                display.error(f"  '{raw.strip()}' is not a valid path. Try TAB for options.")
                continue
            if key in chosen_paths:
                display.error(f"  You already chose '{paths[key].name}'. Pick a different path.")
                continue
            chosen_paths.append(key)
            break

    return [CharacterAsset(asset_key=k) for k in chosen_paths]


def _prompt_final_asset(available_assets: dict[str, Asset]) -> CharacterAsset | None:
    """Prompt for one final asset (path/module/companion/support_vehicle). Returns None if cancelled."""
    valid_categories = {"path", "module", "companion", "support_vehicle"}
    eligible = {k: v for k, v in available_assets.items() if v.category in valid_categories}
    asset_completer = AssetCompleter(eligible)
    asset_session = PromptSession(completer=asset_completer)

    display.console.print()
    display.info("  Choose your final asset — a path, module, companion, or support vehicle.")

    while True:
        try:
            raw = asset_session.prompt("  Final asset: ")
        except (KeyboardInterrupt, EOFError):
            return None
        key = raw.strip().lower().replace(" ", "_").replace("-", "_")
        if not key:
            display.error("  Asset cannot be empty.")
            continue
        if key not in eligible:
            display.error(
                f"  '{raw.strip()}' is not available. Choose a path, module, companion, or support vehicle."
            )
            continue
        return CharacterAsset(asset_key=key)


def _prompt_stats() -> Stats | None:
    """Distribute [3,2,2,1,1] across stats. Returns None if cancelled."""
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
            try:
                raw = Prompt.ask(f"  {stat.capitalize()}")
            except (KeyboardInterrupt, EOFError):
                return None
            try:
                val = int(raw)
                if val in remaining:
                    assigned[stat] = val
                    remaining.remove(val)
                    break
                display.error(f"  Value {val} not in remaining pool.")
            except ValueError:
                display.error("  Enter a number.")

    return Stats(**assigned)


def run_new_character_flow(
    data_dir: Path,
    truth_categories: dict,
) -> tuple[Character, list[Vow], DiceMode] | None:
    """Run the full new-game flow: Truths → character wizard.

    Returns (character, vows, dice_mode) or None if cancelled.
    """
    truths = run_truths_wizard(truth_categories)
    if truths is None:
        return None  # cancelled during truths

    result = run_creation_wizard(data_dir)
    if result is None:
        return None  # cancelled during character creation

    character, vows, dice_mode = result
    character.truths = truths
    return character, vows, dice_mode


def run_creation_wizard(data_dir: Path) -> tuple[Character, list[Vow], DiceMode] | None:
    """Full 10-step character creation wizard (Starforged p.103–112).

    Returns (Character, vows, dice_mode) on success, or None if cancelled.
    """
    display.rule("New Character")
    display.console.print()
    display.console.print("  You begin with:")
    display.console.print("    • [bold]2 path assets[/bold] (your background and training)")
    display.console.print("    • [bold]STARSHIP[/bold] (auto-granted command vehicle)")
    display.console.print(
        "    • [bold]1 final asset[/bold] (path, module, companion, or support vehicle)"
    )
    display.console.print("  [dim]Press TAB at any asset prompt to browse options.[/dim]")

    try:
        available_assets = load_assets(data_dir)

        # ── Step 1: Choose 2 paths ──────────────────────────────────────────
        display.console.print()
        display.rule("Step 1 — Choose 2 Paths")
        display.console.print()
        path_assets = _prompt_paths(available_assets)
        if path_assets is None:
            display.console.print()
            return None
        for ca in path_assets:
            _init_asset_tracks(ca, available_assets)

        # ── Step 2: Backstory ───────────────────────────────────────────────
        display.console.print()
        display.rule("Step 2 — Backstory")
        display.console.print()
        _prompt_oracle_roll(BACKSTORY_TABLE, "Backstory")
        display.console.print()
        backstory = Prompt.ask("  Your backstory (or Enter to skip)", default="")

        # ── Step 3: Background vow ──────────────────────────────────────────
        display.console.print()
        display.rule("Step 3 — Background Vow")
        display.console.print()
        display.info("  Every character begins with an Epic background vow.")
        bg_vow_text = Prompt.ask("  Your background vow")
        vows = [Vow(description=bg_vow_text, rank=VowRank.EPIC)]

        # ── Step 4: STARSHIP ────────────────────────────────────────────────
        display.console.print()
        display.rule("Step 4 — Board Your STARSHIP")
        display.console.print()
        display.info("  Your STARSHIP is auto-granted as a command vehicle.")
        ship_name = Prompt.ask("  Name your starship", default="")
        _prompt_oracle_roll(STARSHIP_HISTORY_TABLE, "Starship History")
        _prompt_oracle_roll(STARSHIP_QUIRK_TABLE, "Starship Quirk")
        starship_asset = CharacterAsset(
            asset_key="starship",
            input_values={"name": ship_name} if ship_name else {},
        )
        _init_asset_tracks(starship_asset, available_assets)

        # ── Step 5: Final asset ─────────────────────────────────────────────
        display.console.print()
        display.rule("Step 5 — Choose Final Asset")
        display.console.print()
        final_asset = _prompt_final_asset(available_assets)
        if final_asset is None:
            display.console.print()
            return None
        _init_asset_tracks(final_asset, available_assets)

        assets = path_assets + [starship_asset, final_asset]

        # ── Step 6: Set stats ───────────────────────────────────────────────
        display.console.print()
        display.rule("Step 6 — Set Stats")
        display.console.print()
        stats = _prompt_stats()
        if stats is None:
            display.console.print()
            return None

        # ── Step 7: Condition meters (display only) ─────────────────────────
        display.console.print()
        display.rule("Step 7 — Condition Meters")
        display.console.print()
        display.console.print(
            Panel(
                "Health [bold]5[/bold]  ●●●●●\n"
                "Spirit [bold]5[/bold]  ●●●●●\n"
                "Supply [bold]5[/bold]  ●●●●●\n"
                "Momentum [bold]+2[/bold]  (max +10, reset +2)",
                title="[bold]STARTING VALUES[/bold]",
                border_style="dim",
            )
        )
        display.info("  These are set automatically.")

        # ── Step 8: Envision your character ─────────────────────────────────
        display.console.print()
        display.rule("Step 8 — Envision Your Character")
        display.console.print()
        display.info("  All fields optional — press Enter to skip.")
        look = Prompt.ask("  Look (appearance, one or two facts)", default="")
        act = Prompt.ask("  Act (how you behave)", default="")
        wear = Prompt.ask("  Wear (what you wear)", default="")

        # ── Step 9: Name your character ────────────────────────────────────
        display.console.print()
        display.rule("Step 9 — Name Your Character")
        display.console.print()
        name = Prompt.ask("  Character name (or 'back' to cancel)")
        if name.lower() in {"back", "cancel", "quit", "exit"}:
            return None
        pronouns = Prompt.ask("  Pronouns (optional, e.g. she/her)", default="")
        callsign = Prompt.ask("  Callsign (optional)", default="")
        homeworld = Prompt.ask("  Homeworld or origin", default="")

        # ── Step 10: Gear up ────────────────────────────────────────────────
        display.console.print()
        display.rule("Step 10 — Gear Up")
        display.console.print()
        display.console.print(
            Panel(
                "Your spacer kit includes:\n"
                "  • Pressure suit with integrated comms\n"
                "  • Flashlights and a handlamp\n"
                "  • Toolkit (multipurpose)\n"
                "  • Medkit (basic)\n"
                "  • Communicator",
                title="[bold]SPACER KIT (INCLUDED)[/bold]",
                border_style="dim",
            )
        )
        display.info("  Add up to 5 personal items (Enter when done).")
        gear: list[str] = []
        while len(gear) < 5:
            item = Prompt.ask(f"  Personal item {len(gear) + 1} (or Enter when done)", default="")
            if not item:
                break
            gear.append(item)

        # ── Dice mode ───────────────────────────────────────────────────────
        display.console.print()
        display.rule("Dice Mode")
        display.console.print()
        display.info("  How should dice be handled?")
        display.info("    [1] Digital — CLI rolls for you")
        display.info("    [2] Physical — you roll, CLI prompts for values")
        display.info("    [3] Mixed — digital by default, --manual flag per command")
        raw = Prompt.ask("  Choose", default="1")
        mode_map = {"1": DiceMode.DIGITAL, "2": DiceMode.PHYSICAL, "3": DiceMode.MIXED}
        dice_mode = mode_map.get(raw, DiceMode.DIGITAL)

        # ── Confirmation summary ─────────────────────────────────────────────
        display.console.print()
        asset_summary = "\n".join(
            f"  • {available_assets[a.asset_key].name if a.asset_key in available_assets else a.asset_key.replace('_', ' ').title()}"
            + (f" ({a.input_values.get('name', '')})" if a.input_values.get("name") else "")
            for a in assets
        )
        stats_summary = "  ".join(f"{k.capitalize()} {v}" for k, v in stats.as_dict().items())
        lines = [
            f"[bold]{name}[/bold]" + (f"  [dim]({pronouns})[/dim]" if pronouns else ""),
        ]
        if callsign:
            lines.append(f"Callsign: [dim]{callsign}[/dim]")
        if homeworld:
            lines.append(f"Homeworld: [dim]{homeworld}[/dim]")
        lines.append("")
        lines.append(f"Stats: [dim]{stats_summary}[/dim]")
        lines.append("")
        lines.append("Assets:")
        lines.append(asset_summary)
        if backstory:
            lines.append("")
            lines.append(f"Backstory: [dim]{backstory}[/dim]")
        if look or act or wear:
            lines.append("")
            if look:
                lines.append(f"Look: [dim]{look}[/dim]")
            if act:
                lines.append(f"Act:  [dim]{act}[/dim]")
            if wear:
                lines.append(f"Wear: [dim]{wear}[/dim]")
        if gear:
            lines.append("")
            lines.append("Gear: " + ", ".join(gear))
        lines.append("")
        lines.append(f"Vow ([bold red]Epic[/bold red]): {bg_vow_text}")

        display.console.print(
            Panel("\n".join(lines), title="[bold]CHARACTER SUMMARY[/bold]", border_style="blue")
        )

        if not Confirm.ask("  Begin your journey?", default=True):
            return None

        character = Character(
            name=name,
            homeworld=homeworld,
            stats=stats,
            assets=assets,
            pronouns=pronouns,
            callsign=callsign,
            backstory=backstory,
            look=look,
            act=act,
            wear=wear,
            gear=gear,
        )

        display.console.print()
        display.success(f"Character created: {name}")
        return character, vows, dice_mode

    except (KeyboardInterrupt, EOFError):
        display.console.print()
        return None
