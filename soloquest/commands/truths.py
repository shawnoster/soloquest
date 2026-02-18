"""Truths command — Choose Your Truths campaign setup wizard."""

from __future__ import annotations

import contextlib
import random
import re
from typing import TYPE_CHECKING

from prompt_toolkit.shortcuts import prompt
from rich.padding import Padding
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from soloquest.engine.truths import get_ordered_categories
from soloquest.models.truths import ChosenTruth, TruthCategory, TruthOption
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState


def handle_truths(state: GameState, args: list[str], flags: set[str]) -> None:
    """Interactive wizard for choosing campaign truths.

    Usage:
        /truths - Show current truths or start wizard if none set
        /truths start - (Re)start the truth selection wizard
        /truths show - Display current truths
        /truths edit [category] - Edit a specific truth (future enhancement)
    """
    if args and args[0].lower() == "start":
        _start_truths_wizard(state)
        return

    if args and args[0].lower() == "show":
        _show_truths(state)
        return

    # Default behavior: show truths if set, otherwise start wizard
    if state.character.truths:
        _show_truths(state)
    else:
        _prompt_to_start_wizard(state)


def _prompt_to_start_wizard(state: GameState) -> None:
    """Prompt the user to start the truths wizard."""
    display.rule("Choose Your Truths")
    display.console.print()
    display.console.print("  [bold]You haven't chosen your campaign truths yet.[/bold]")
    display.console.print()
    display.console.print(
        "  Truths establish the fundamental facts about your version of the Forge. "
        "You'll answer 14 questions about your setting, from the nature of the "
        "cataclysm to the existence of magic and alien life."
    )
    display.console.print()
    display.console.print("  [dim]This exercise takes about 45-60 minutes.[/dim]")
    display.console.print()

    try:
        if Confirm.ask("  Would you like to start choosing your truths now?", default=True):
            _start_truths_wizard(state)
        else:
            display.info("You can start later with: /truths start")
    except (KeyboardInterrupt, EOFError):
        display.console.print()
        display.info("You can start later with: /truths start")


def run_truths_wizard(truth_categories: dict[str, TruthCategory]) -> list[ChosenTruth] | None:
    """Run the interactive truths wizard. Returns chosen truths or None if cancelled."""
    display.rule("Choose Your Truths — Campaign Setup")
    display.console.print()

    _show_introduction()

    categories = get_ordered_categories(truth_categories)

    if not categories:
        display.error("No truth categories found. Check data files.")
        return None

    chosen_truths: list[ChosenTruth] = []

    try:
        # Walk through each category
        for idx, category in enumerate(categories, start=1):
            display.console.print()
            display.console.print("  " + "─" * 76)
            display.console.print()

            display.console.print(
                f"  [bold cyan]Truth {idx} of {len(categories)}: {category.name.upper()}[/bold cyan]"
            )
            display.console.print()

            # Show options
            for option_idx, option in enumerate(category.options, start=1):
                roll_range = f"[{option.roll_range[0]}-{option.roll_range[1]}]"
                display.console.print(
                    f"  [bold][{option_idx}][/bold] {option.summary} [dim]{roll_range}[/dim]"
                )

            # Get user choice
            chosen_truth = _get_truth_choice(category)
            if chosen_truth:
                chosen_truths.append(chosen_truth)

        # Show summary
        display.console.print()
        display.console.print("  " + "═" * 76)
        display.console.print()
        _show_summary(chosen_truths)

        # Confirm
        display.console.print()
        if Confirm.ask("  [bold]Save these truths?[/bold]", default=True):
            return chosen_truths
        else:
            display.info("Truths not saved. Run /truths start to try again.")
            return None

    except (KeyboardInterrupt, EOFError):
        display.console.print()
        display.console.print()
        display.info("Truth selection cancelled. Run /truths start to begin again.")
        return None


def _start_truths_wizard(state: GameState) -> None:
    """Start the interactive truths wizard."""
    # If truths already exist, confirm overwrite
    if state.character.truths:
        display.console.print()
        try:
            if not Confirm.ask(
                "  You already have truths set. Start over and replace them?",
                default=False,
            ):
                display.info("Keeping existing truths.")
                return
        except (KeyboardInterrupt, EOFError):
            display.console.print()
            display.info("Keeping existing truths.")
            return

    result = run_truths_wizard(state.truth_categories)
    if result is not None:
        state.character.truths = result
        display.success("Campaign truths saved!")
        display.console.print()
        state.session.add_note(f"Campaign truths established ({len(result)} categories)")
        display.info("  Truths have been added to your session log.")


def _show_introduction() -> None:
    """Show the introduction to choosing truths."""
    intro = """[bold]Welcome to Choose Your Truths[/bold]

You'll answer 14 questions to establish the fundamental facts about
your version of the Forge — the galaxy where Ironsworn: Starforged
takes place.

[bold cyan]How it works:[/bold cyan]
  • For each truth category, you'll see 3 options
  • Choose a number [1-3] to select that option
  • Type [bold]r[/bold] to roll randomly (d100)
  • Type [bold]c[/bold] to write your own custom truth
  • Type [bold]s[/bold] to skip (you can come back later)

[dim]Press Enter to continue...[/dim]
"""
    display.console.print(Panel(intro, border_style="cyan", padding=(1, 2)))
    with contextlib.suppress(KeyboardInterrupt, EOFError):
        prompt("")
    display.console.print()


def _get_subchoice(subchoices: list[str]) -> str:
    """Prompt user to select a subchoice.

    Returns the chosen subchoice text (without roll range).
    """
    while True:
        try:
            display.console.print()
            choice = Prompt.ask(
                f"  Choose (1-{len(subchoices)}), or roll (r)",
                default="r",
            ).lower()

            # Handle roll
            if choice == "r":
                # Parse roll ranges from subchoices to determine the roll
                roll = random.randint(1, 100)
                display.console.print()
                display.console.print(f"  [cyan]Rolled: {roll}[/cyan]")

                # Find matching subchoice by roll range
                for subchoice_text in subchoices:
                    # Extract roll range like [1-25]
                    match = re.search(r"\[(\d+)-(\d+)\]", subchoice_text)
                    if match:
                        low, high = int(match.group(1)), int(match.group(2))
                        if low <= roll <= high:
                            # Remove the roll range from the text
                            clean_text = re.sub(r"\s*\[\d+-\d+\]", "", subchoice_text)
                            display.console.print(f"  [bold]Result:[/bold] {clean_text}")
                            return clean_text
                else:
                    # No match found for the roll
                    display.error(f"  No subchoice found for roll {roll}. Please try again.")
                    continue

            # Handle numbered choice
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(subchoices):
                    # Remove roll range from selected subchoice
                    clean_text = re.sub(r"\s*\[\d+-\d+\]", "", subchoices[idx])
                    display.console.print(f"  [bold]Chosen:[/bold] {clean_text}")
                    return clean_text

            display.error("  Invalid choice. Try again.")

        except (KeyboardInterrupt, EOFError):
            display.console.print()
            # Return empty string if cancelled
            return ""


def _prompt_note() -> str:
    """Prompt for an optional personal note about this truth."""
    try:
        note = Prompt.ask(
            "  [dim italic]What does this truth mean for your story?[/dim italic]",
            default="",
            show_default=False,
        )
        return note
    except (KeyboardInterrupt, EOFError):
        return ""


def _create_chosen_truth(
    category: TruthCategory, option: TruthOption, subchoice: str = "", note: str = ""
) -> ChosenTruth:
    """Create a ChosenTruth from a category and option."""
    return ChosenTruth(
        category=category.name,
        option_summary=option.summary,
        option_text=option.text,
        quest_starter=option.quest_starter,
        subchoice=subchoice,
        note=note,
    )


def _get_truth_choice(category: TruthCategory) -> ChosenTruth | None:
    """Get the user's choice for a truth category."""
    while True:
        try:
            display.console.print()
            choice = Prompt.ask(
                "  Choose (1-3), roll (r), custom (c), or skip (s)",
                default="r",
            ).lower()

            # Handle skip
            if choice == "s":
                display.info(f"  Skipped {category.name}")
                # Return a placeholder truth
                return ChosenTruth(
                    category=category.name,
                    option_summary="[To be determined]",
                    option_text="",
                    custom_text="",
                    quest_starter="",
                )

            # Handle roll
            if choice == "r":
                roll = random.randint(1, 100)
                option = category.get_option_by_roll(roll)
                if option:
                    display.console.print()
                    display.console.print(f"  [cyan]Rolled: {roll}[/cyan]")
                    display.console.print(f"  [bold]Result:[/bold] {option.summary}")
                    display.console.print()
                    subchoice = _show_option_details(option)
                    note = _prompt_note()
                    return _create_chosen_truth(category, option, subchoice, note)
                else:
                    display.error(f"  No option found for roll {roll}. Please try again.")
                    continue

            # Handle custom
            if choice == "c":
                display.console.print()
                display.console.print("  [bold]Write your custom truth:[/bold]")
                custom = Prompt.ask("  ")
                if custom:
                    display.console.print()
                    display.console.print(f"  [bold]Your truth:[/bold] {custom}")
                    display.console.print()
                    note = _prompt_note()
                    return ChosenTruth(
                        category=category.name,
                        option_summary=custom,
                        custom_text=custom,
                        note=note,
                    )
                else:
                    display.error("  Custom truth cannot be empty. Please try again.")
                    continue

            # Handle numbered choice
            if choice in ["1", "2", "3"]:
                idx = int(choice) - 1
                if 0 <= idx < len(category.options):
                    option = category.options[idx]
                    display.console.print()
                    display.console.print(f"  [bold]You chose:[/bold] {option.summary}")
                    display.console.print()
                    subchoice = _show_option_details(option)
                    note = _prompt_note()
                    return _create_chosen_truth(category, option, subchoice, note)

            display.error("  Invalid choice. Try again.")

        except (KeyboardInterrupt, EOFError):
            display.console.print()
            raise


def _show_option_details(option: TruthOption) -> str:
    """Show detailed information about a chosen option.

    Returns the chosen subchoice if applicable, empty string otherwise.
    """
    display.console.print(Padding(f"[dim]{option.text}[/dim]", (0, 0, 0, 2)))

    chosen_subchoice = ""
    if option.subchoices:
        display.console.print()
        display.console.print("  [bold cyan]Choose a subchoice:[/bold cyan]")
        display.console.print()
        for idx, subchoice in enumerate(option.subchoices, start=1):
            styled = re.sub(r"\[(\d+-\d+)\]", r"[dim][\1][/dim]", subchoice)
            display.console.print(f"  [bold][{idx}][/bold] {styled}")

        chosen_subchoice = _get_subchoice(option.subchoices)

    if option.quest_starter:
        display.console.print()
        display.console.print("  [bold cyan]Quest Starter:[/bold cyan]")
        display.console.print()
        display.console.print(Padding(f"[dim]{option.quest_starter}[/dim]", (0, 0, 0, 2)))

    display.console.print()
    return chosen_subchoice


def _show_summary(truths: list[ChosenTruth]) -> None:
    """Show a summary of all chosen truths."""
    display.rule("Your Campaign Truths")
    display.console.print()

    for truth in truths:
        display.console.print(f"  [bold]• {truth.category}:[/bold] {truth.display_text()}")
        if truth.note:
            display.console.print(f"    [dim italic]{truth.note}[/dim italic]")

    display.console.print()


def _show_truths(state: GameState) -> None:
    """Display the character's current truths."""
    if not state.character.truths:
        display.info("No truths set yet. Use /truths start to begin.")
        return

    display.rule("Your Campaign Truths")
    display.console.print()

    for truth in state.character.truths:
        display.console.print(f"  [bold]• {truth.category}:[/bold] {truth.display_text()}")
        if truth.note:
            display.console.print(f"    [dim italic]{truth.note}[/dim italic]")

    display.console.print()
    display.console.print("  [dim]Commands:[/dim]")
    display.console.print("    [cyan]/truths start[/cyan] - Restart truth selection")
    display.console.print()
