"""Full 10-step character creation wizard for Ironsworn: Starforged (p.103–112)."""

from __future__ import annotations

import random
import tomllib
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from rich.panel import Panel

from soloquest.commands.asset import display_asset_card
from soloquest.commands.truths import run_truths_wizard
from soloquest.engine.assets import fuzzy_match_asset, load_assets
from soloquest.engine.dice import DiceMode
from soloquest.models.asset import Asset, CharacterAsset
from soloquest.models.character import Character, Stats
from soloquest.models.vow import Vow, VowRank
from soloquest.ui import display
from soloquest.ui.strings import get_string
from soloquest.ui.theme import BORDER_ACTION, BORDER_ORACLE, RANK_EPIC


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


def _wprompt(session: PromptSession, label: str, default: str = "") -> str:
    """Plain-text prompt via prompt_toolkit. Returns stripped input or default."""
    suffix = f" [{default}]" if default else ""
    result = session.prompt(f"{label}{suffix}: ")
    return result.strip() or default


def _wconfirm(session: PromptSession, label: str, default: bool = True) -> bool:
    """Yes/no prompt via prompt_toolkit."""
    hint = "[Y/n]" if default else "[y/N]"
    while True:
        raw = session.prompt(f"{label} {hint}: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False


def _prompt_oracle_roll(table: list[tuple], table_name: str, session: PromptSession) -> None:
    """Offer to roll on an oracle table and display the result."""
    roll_it = _wconfirm(session, f"  Roll on the {table_name} table?", default=False)
    if roll_it:
        result = _roll_table(table)
        roll = result[0]
        text = result[1]
        display.oracle_result_panel(table_name, roll, text)


def _parse_suggestion_defaults(suggestion: str, paths: dict[str, Asset]) -> list[str]:
    """Parse a suggestion string like 'Ace + Navigator' into default display names.

    Returns a two-element list [default1, default2].  An empty string means no
    default for that slot (e.g., when the suggestion is 'Choose any two paths').
    """
    if " + " not in suggestion:
        return ["", ""]
    parts = suggestion.split(" + ", 1)
    # Handle "or" alternatives (e.g., "Archer or Blademaster") — take the first option
    name1 = parts[0].split(" or ")[0].strip()
    name2 = parts[1].strip()

    def best_name(query: str) -> str:
        matches = fuzzy_match_asset(query, paths)
        return matches[0].name if matches else query

    return [best_name(name1), best_name(name2)]


def _prompt_paths(
    available_assets: dict[str, Asset], session: PromptSession
) -> list[CharacterAsset] | None:
    """Prompt for 2 path assets. Returns None if cancelled."""
    paths = {k: v for k, v in available_assets.items() if v.category == "path"}
    path_completer = AssetCompleter(paths)

    display.console.print()
    display.console.print(
        f"  [dim]{get_string('character_creation.instructions.paths_intro')}[/dim]"
    )
    display.console.print()
    display.info(f"  {get_string('character_creation.instructions.paths_categories')}")

    # Show the full background paths table
    display.console.print()
    for idx, (_lo, _hi, background, suggestion) in enumerate(BACKGROUND_PATHS_TABLE, start=1):
        display.console.print(f"  [dim][{idx:>2}][/dim]  {background:<28}[dim]{suggestion}[/dim]")
    display.console.print()

    # Inspiration prompt
    try:
        raw = (
            session.prompt(
                f"  {get_string('character_creation.instructions.inspiration_prompt')}: "
            )
            .strip()
            .lower()
        )
    except (KeyboardInterrupt, EOFError):
        return None

    path_defaults: list[str] = ["", ""]

    if raw == "r":
        result = _roll_table(BACKGROUND_PATHS_TABLE)
        roll, background, suggestion = result
        display.console.print(
            Panel(
                f"[dim]{roll}[/dim]  →  [bold]{background}[/bold]\n[dim]Suggested paths: {suggestion}[/dim]",
                title="[bold]BACKGROUND PATHS[/bold]",
                border_style=BORDER_ORACLE,
            )
        )
        path_defaults = _parse_suggestion_defaults(suggestion, paths)
    elif raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(BACKGROUND_PATHS_TABLE):
            lo, hi, background, suggestion = BACKGROUND_PATHS_TABLE[idx]
            display.console.print(
                Panel(
                    f"[bold]{background}[/bold]\n[dim]Suggested paths: {suggestion}[/dim]",
                    title="[bold]BACKGROUND PATHS[/bold]",
                    border_style=BORDER_ORACLE,
                )
            )
            path_defaults = _parse_suggestion_defaults(suggestion, paths)

    chosen_paths: list[str] = []
    for i in range(1, 3):
        while True:
            try:
                raw = session.prompt(
                    f"  Path {i}: ",
                    completer=path_completer,
                    default=path_defaults[i - 1],
                )
            except (KeyboardInterrupt, EOFError):
                return None
            key = raw.strip().lower().replace(" ", "_").replace("-", "_")
            if not key:
                display.error(f"  {get_string('character_creation.errors.path_empty')}")
                continue
            if key not in paths:
                display.error(
                    f"  {get_string('character_creation.errors.path_invalid', path=raw.strip())}"
                )
                continue
            if key in chosen_paths:
                display.error(
                    f"  {get_string('character_creation.errors.path_duplicate', existing=paths[key].name)}"
                )
                continue
            chosen_paths.append(key)
            break

    # Show the chosen asset cards
    display.console.print()
    for key in chosen_paths:
        display_asset_card(paths[key])

    return [CharacterAsset(asset_key=k) for k in chosen_paths]


def _prompt_final_asset(
    available_assets: dict[str, Asset], session: PromptSession
) -> CharacterAsset | None:
    """Prompt for one final asset (path/module/companion/support_vehicle). Returns None if cancelled."""
    valid_categories = {"path", "module", "companion", "support_vehicle"}
    eligible = {k: v for k, v in available_assets.items() if v.category in valid_categories}
    asset_completer = AssetCompleter(eligible)

    display.console.print()
    display.info(f"  {get_string('character_creation.instructions.final_asset_prompt')}")

    while True:
        try:
            raw = session.prompt("  Final asset: ", completer=asset_completer)
        except (KeyboardInterrupt, EOFError):
            return None
        key = raw.strip().lower().replace(" ", "_").replace("-", "_")
        if not key:
            display.error(f"  {get_string('character_creation.errors.asset_empty')}")
            continue
        if key not in eligible:
            display.error(
                f"  {get_string('character_creation.errors.asset_invalid', asset=raw.strip())}"
            )
            continue
        return CharacterAsset(asset_key=key)


def _prompt_stats(session: PromptSession) -> Stats | None:
    """Distribute [3,2,2,1,1] across stats. Returns None if cancelled."""
    display.console.print()
    display.info(f"  {get_string('character_creation.instructions.stats_assign')}")
    display.info(f"  {get_string('character_creation.instructions.stats_distribute')}")
    display.console.print()

    stat_pool = [3, 2, 2, 1, 1]
    stat_names = ["edge", "heart", "iron", "shadow", "wits"]
    assigned: dict[str, int] = {}
    remaining = list(stat_pool)

    for stat in stat_names:
        display.info(f"  Remaining values: {sorted(remaining, reverse=True)}")
        while True:
            try:
                raw = session.prompt(f"  {stat.capitalize()}: ")
            except (KeyboardInterrupt, EOFError):
                return None
            try:
                val = int(raw.strip())
                if val in remaining:
                    assigned[stat] = val
                    remaining.remove(val)
                    break
                display.error(f"  Value {val} not in remaining pool.")
            except ValueError:
                display.error(f"  {get_string('character_creation.errors.not_a_number')}")

    return Stats(**assigned)


def run_new_character_flow(
    data_dir: Path,
    truth_categories: dict,
    include_truths: bool = True,
) -> tuple[Character, list[Vow], DiceMode] | None:
    """Run the full new-game flow: (optionally Truths →) character wizard.

    Returns (character, vows, dice_mode) or None if cancelled.
    Set include_truths=False for co-op joiners who skip world setup.
    """
    if include_truths:
        truths = run_truths_wizard(truth_categories)
        if truths is None:
            return None  # cancelled during truths
    else:
        truths = []

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
    display.console.print(f"  [dim]{get_string('character_creation.instructions.tab_hint')}[/dim]")

    # Single session for the entire wizard — avoids mixing prompt_toolkit with
    # Rich's input()-based Prompt.ask/Confirm.ask, which leaves the terminal in
    # application-keypad mode between prompts and breaks numpad arrow keys.
    session: PromptSession = PromptSession()

    try:
        available_assets = load_assets(data_dir)

        # ── Step 1: Choose 2 paths ──────────────────────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.step1_title"))
        display.console.print()
        path_assets = _prompt_paths(available_assets, session)
        if path_assets is None:
            display.console.print()
            return None
        for ca in path_assets:
            _init_asset_tracks(ca, available_assets)

        # ── Step 2: Backstory ───────────────────────────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.step2_title"))
        display.console.print()
        _prompt_oracle_roll(BACKSTORY_TABLE, "Backstory", session)
        display.console.print()
        backstory = _wprompt(
            session, f"  {get_string('character_creation.prompts.backstory_prompt')}"
        )

        # ── Step 3: Background vow ──────────────────────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.step3_title"))
        display.console.print()
        display.info(f"  {get_string('character_creation.prompts.background_vow_intro')}")
        bg_vow_text = _wprompt(
            session, f"  {get_string('character_creation.prompts.background_vow_prompt')}"
        )
        vows = [Vow(description=bg_vow_text, rank=VowRank.EPIC)]

        # ── Step 4: STARSHIP ────────────────────────────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.step4_title"))
        display.console.print()
        display.info(f"  {get_string('character_creation.prompts.starship_auto_grant')}")
        ship_name = _wprompt(
            session, f"  {get_string('character_creation.prompts.starship_name_prompt')}"
        )
        _prompt_oracle_roll(STARSHIP_HISTORY_TABLE, "Starship History", session)
        _prompt_oracle_roll(STARSHIP_QUIRK_TABLE, "Starship Quirk", session)
        starship_asset = CharacterAsset(
            asset_key="starship",
            input_values={"name": ship_name} if ship_name else {},
        )
        _init_asset_tracks(starship_asset, available_assets)

        # ── Step 5: Final asset ─────────────────────────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.step5_title"))
        display.console.print()
        final_asset = _prompt_final_asset(available_assets, session)
        if final_asset is None:
            display.console.print()
            return None
        _init_asset_tracks(final_asset, available_assets)

        assets = path_assets + [starship_asset, final_asset]

        # ── Step 6: Set stats ───────────────────────────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.step6_title"))
        display.console.print()
        stats = _prompt_stats(session)
        if stats is None:
            display.console.print()
            return None

        # ── Step 7: Condition meters (display only) ─────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.step7_title"))
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
        display.rule(get_string("character_creation.wizard_steps.step8_title"))
        display.console.print()
        display.info(f"  {get_string('character_creation.instructions.envision_optional')}")
        look = _wprompt(session, "  Look (appearance, one or two facts)")
        act = _wprompt(session, "  Act (how you behave)")
        wear = _wprompt(session, "  Wear (what you wear)")

        # ── Step 9: Name your character ────────────────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.step9_title"))
        display.console.print()
        name = _wprompt(
            session, f"  {get_string('character_creation.prompts.character_name_prompt')}"
        )
        if name.lower() in {"back", "cancel", "quit", "exit"}:
            return None
        pronouns = _wprompt(
            session, f"  {get_string('character_creation.prompts.pronouns_prompt')}"
        )
        callsign = _wprompt(
            session, f"  {get_string('character_creation.prompts.callsign_prompt')}"
        )
        homeworld = _wprompt(
            session, f"  {get_string('character_creation.prompts.homeworld_prompt')}"
        )

        # ── Step 10: Gear up ────────────────────────────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.step10_title"))
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
        display.info(f"  {get_string('character_creation.prompts.gear_prompt')}")
        gear: list[str] = []
        while len(gear) < 5:
            item = _wprompt(session, f"  Personal item {len(gear) + 1} (or Enter when done)")
            if not item:
                break
            gear.append(item)

        # ── Dice mode ───────────────────────────────────────────────────────
        display.console.print()
        display.rule(get_string("character_creation.wizard_steps.dice_mode_title"))
        display.console.print()
        display.info(f"  {get_string('character_creation.instructions.dice_mode_question')}")
        display.info(f"    {get_string('character_creation.dice_modes.option1')}")
        display.info(f"    {get_string('character_creation.dice_modes.option2')}")
        display.info(f"    {get_string('character_creation.dice_modes.option3')}")
        raw = _wprompt(session, "  Choose", default="1")
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
        lines.append(f"Vow ([bold {RANK_EPIC}]Epic[/bold {RANK_EPIC}]): {bg_vow_text}")

        display.console.print(
            Panel(
                "\n".join(lines), title="[bold]CHARACTER SUMMARY[/bold]", border_style=BORDER_ACTION
            )
        )

        if not _wconfirm(
            session, f"  {get_string('character_creation.prompts.begin_journey')}", default=True
        ):
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
