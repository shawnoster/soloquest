"""Tests for the 11-step character creation wizard."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from soloquest.commands.new_character import (
    BACKGROUND_PATHS_TABLE,
    BACKSTORY_TABLE,
    STARSHIP_HISTORY_TABLE,
    STARSHIP_QUIRK_TABLE,
    _roll_table,
    run_creation_wizard,
    run_new_character_flow,
)
from soloquest.engine.dice import DiceMode

DATA_DIR = Path(__file__).parent.parent / "soloquest" / "data"


class TestRollTable:
    def test_roll_returns_matching_row(self):
        # Use a simple table with known entries
        table = [(1, 50, "first half"), (51, 100, "second half")]
        # Patch random.randint to return a specific value
        with patch("soloquest.commands.new_character.random.randint", return_value=25):
            result = _roll_table(table)
        assert result == (25, "first half")

    def test_roll_returns_last_row_on_100(self):
        table = BACKSTORY_TABLE
        with patch("soloquest.commands.new_character.random.randint", return_value=100):
            result = _roll_table(table)
        assert result[0] == 100
        # Should match the last entry (96-100)
        assert "Forge" in result[1]

    def test_backstory_table_covers_1_to_100(self):
        for i in range(1, 101):
            with patch("soloquest.commands.new_character.random.randint", return_value=i):
                result = _roll_table(BACKSTORY_TABLE)
            assert result[0] == i
            assert isinstance(result[1], str)

    def test_starship_history_table_covers_1_to_100(self):
        for i in range(1, 101):
            with patch("soloquest.commands.new_character.random.randint", return_value=i):
                result = _roll_table(STARSHIP_HISTORY_TABLE)
            assert result[0] == i

    def test_starship_quirk_table_covers_1_to_100(self):
        for i in range(1, 101):
            with patch("soloquest.commands.new_character.random.randint", return_value=i):
                result = _roll_table(STARSHIP_QUIRK_TABLE)
            assert result[0] == i

    def test_background_paths_table_covers_1_to_100(self):
        for i in range(1, 101):
            with patch("soloquest.commands.new_character.random.randint", return_value=i):
                result = _roll_table(BACKGROUND_PATHS_TABLE)
            assert result[0] == i


class TestRunCreationWizard:
    """Integration tests for run_creation_wizard — mocking all I/O.

    All prompts go through a single PromptSession.prompt() call.
    Prompt order (25 entries for a minimal run):
      [0]  inspiration (enter "" to skip)
      [1]  path 1 (e.g. "ace")
      [2]  path 2 (e.g. "navigator")
      [3]  backstory oracle confirm ("" → False, default=False)
      [4]  backstory text
      [5]  background vow text
      [6]  ship name
      [7]  starship history oracle confirm ("" → False, default=False)
      [8]  starship quirk oracle confirm ("" → False, default=False)
      [9]  final asset (e.g. "empath")
      [10] edge
      [11] heart
      [12] iron
      [13] shadow
      [14] wits
      [15] look
      [16] act
      [17] wear
      [18] name
      [19] pronouns
      [20] callsign
      [21] homeworld
      [22] gear item 1 ("" → done)
      [23] dice mode ("1" = digital)
      [24] begin journey confirm ("" → True, default=True)
    """

    def _base_answers(self):
        """Return the minimal 25-prompt answer list for a default wizard run."""
        return [
            "",  # [0]  inspiration (skip)
            "ace",  # [1]  path 1
            "navigator",  # [2]  path 2
            "",  # [3]  backstory oracle confirm (default=False → skip)
            "",  # [4]  backstory
            "Find the truth",  # [5]  background vow
            "",  # [6]  ship name
            "",  # [7]  starship history oracle confirm (default=False → skip)
            "",  # [8]  starship quirk oracle confirm (default=False → skip)
            "empath",  # [9]  final asset
            "3",  # [10] edge
            "2",  # [11] heart
            "2",  # [12] iron
            "1",  # [13] shadow
            "1",  # [14] wits
            "",  # [15] look
            "",  # [16] act
            "",  # [17] wear
            "Kael",  # [18] name
            "",  # [19] pronouns
            "",  # [20] callsign
            "",  # [21] homeworld
            "",  # [22] gear (done immediately)
            "1",  # [23] dice mode (digital)
            "",  # [24] begin journey confirm (default=True → yes)
        ]

    def _run_wizard_with_answers(self, all_prompt_answers):
        """Run the wizard with all session.prompt() answers in sequence."""
        with patch("soloquest.commands.new_character.PromptSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.prompt.side_effect = all_prompt_answers
            mock_session_class.return_value = mock_session
            result = run_creation_wizard(DATA_DIR)
        return result

    def test_wizard_returns_character_vows_dice_mode(self):
        """Successful completion returns a 3-tuple."""
        answers = self._base_answers()
        answers[6] = "Stellar Drift"
        answers[21] = "The Rift"
        result = self._run_wizard_with_answers(answers)
        assert result is not None
        character, vows, dice_mode = result
        assert character.name == "Kael"
        assert character.homeworld == "The Rift"
        assert dice_mode == DiceMode.DIGITAL

    def test_wizard_grants_starship_and_two_paths(self):
        """Character must have starship + 2 path assets + 1 free asset."""
        answers = self._base_answers()
        answers[6] = "Rusty"
        result = self._run_wizard_with_answers(answers)
        assert result is not None
        character, vows, dice_mode = result

        asset_keys = [a.asset_key for a in character.assets]
        # Must have starship
        assert "starship" in asset_keys
        # Must have the two paths
        assert "ace" in asset_keys
        assert "navigator" in asset_keys
        # Must have final asset
        assert "empath" in asset_keys
        # Total: 4 assets
        assert len(character.assets) == 4

    def test_wizard_stores_ship_name_in_input_values(self):
        """STARSHIP asset input_values should contain the ship name."""
        answers = self._base_answers()
        answers[6] = "Stellar Drift"
        result = self._run_wizard_with_answers(answers)
        assert result is not None
        character, _, _ = result
        starship = next(a for a in character.assets if a.asset_key == "starship")
        assert starship.input_values.get("name") == "Stellar Drift"

    def test_wizard_creates_epic_background_vow(self):
        """Background vow must be Epic rank."""
        from soloquest.models.vow import VowRank

        answers = self._base_answers()
        answers[5] = "Avenge my homeworld"
        result = self._run_wizard_with_answers(answers)
        assert result is not None
        _, vows, _ = result
        assert len(vows) == 1
        assert vows[0].rank == VowRank.EPIC
        assert vows[0].description == "Avenge my homeworld"

    def test_wizard_stores_narrative_fields(self):
        """Narrative fields (look, act, wear, pronouns, callsign, backstory) are stored."""
        answers = self._base_answers()
        answers[4] = "Fled the war"  # backstory
        answers[6] = "Ghost"  # ship name
        answers[15] = "Tall with red hair"  # look
        answers[16] = "Calm and decisive"  # act
        answers[17] = "Worn leather jacket"  # wear
        answers[19] = "they/them"  # pronouns
        answers[20] = "Shadow"  # callsign
        answers[21] = "Drift Station"  # homeworld
        result = self._run_wizard_with_answers(answers)
        assert result is not None
        character, _, _ = result
        assert character.backstory == "Fled the war"
        assert character.look == "Tall with red hair"
        assert character.act == "Calm and decisive"
        assert character.wear == "Worn leather jacket"
        assert character.pronouns == "they/them"
        assert character.callsign == "Shadow"

    def test_wizard_stores_gear(self):
        """Personal gear items are stored on the character."""
        answers = [
            "",  # [0]  inspiration
            "ace",  # [1]  path 1
            "navigator",  # [2]  path 2
            "",  # [3]  backstory oracle confirm
            "",  # [4]  backstory
            "Find the truth",  # [5]  vow
            "",  # [6]  ship name
            "",  # [7]  history oracle confirm
            "",  # [8]  quirk oracle confirm
            "empath",  # [9]  final asset
            "3",  # [10] edge
            "2",  # [11] heart
            "2",  # [12] iron
            "1",  # [13] shadow
            "1",  # [14] wits
            "",  # [15] look
            "",  # [16] act
            "",  # [17] wear
            "Kael",  # [18] name
            "",  # [19] pronouns
            "",  # [20] callsign
            "",  # [21] homeworld
            "Data pad",  # [22] gear 1
            "Lucky coin",  # [23] gear 2
            "",  # [24] gear done
            "1",  # [25] dice mode
            "",  # [26] confirm
        ]
        result = self._run_wizard_with_answers(answers)
        assert result is not None
        character, _, _ = result
        assert "Data pad" in character.gear
        assert "Lucky coin" in character.gear

    def test_wizard_supply_starts_at_5(self):
        """Character supply should start at 5 per rulebook."""
        result = self._run_wizard_with_answers(self._base_answers())
        assert result is not None
        character, _, _ = result
        assert character.supply == 5

    def test_wizard_cancellation_returns_none_on_back(self):
        """Typing 'back' at name prompt returns None."""
        answers = self._base_answers()
        answers[18] = "back"  # name → cancel
        result = self._run_wizard_with_answers(answers)
        assert result is None

    def test_wizard_cancellation_returns_none_on_keyboard_interrupt(self):
        """KeyboardInterrupt at any step returns None."""
        with patch("soloquest.commands.new_character.PromptSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session.prompt.side_effect = KeyboardInterrupt
            mock_session_class.return_value = mock_session
            result = run_creation_wizard(DATA_DIR)
        assert result is None

    def test_wizard_dice_mode_physical(self):
        """Selecting '2' sets physical dice mode."""
        answers = self._base_answers()
        answers[23] = "2"  # physical dice mode
        result = self._run_wizard_with_answers(answers)
        assert result is not None
        _, _, dice_mode = result
        assert dice_mode == DiceMode.PHYSICAL

    def test_wizard_confirm_no_returns_none(self):
        """Declining the final confirmation returns None."""
        answers = self._base_answers()
        answers[24] = "n"  # decline (default=True, so "n" → False)
        result = self._run_wizard_with_answers(answers)
        assert result is None


class TestRunNewCharacterFlow:
    """Tests for run_new_character_flow — truths then character wizard."""

    def _make_truth_categories(self):
        """Return a minimal truth categories dict with one category."""
        from soloquest.models.truths import TruthCategory, TruthOption

        option = TruthOption(
            roll_range=(1, 100),
            summary="All is well",
            text="The universe is fine.",
            quest_starter="",
        )
        category = TruthCategory(
            name="The Cataclysm",
            description="What caused the cataclysm?",
            order=1,
            options=[option],
        )
        return {"The Cataclysm": category}

    def test_truths_attached_to_character(self):
        """Truths returned by run_truths_wizard are attached to the character."""
        from soloquest.models.truths import ChosenTruth

        chosen = [ChosenTruth(category="The Cataclysm", option_summary="All is well")]
        truth_categories = self._make_truth_categories()

        answers = [
            "",  # [0]  inspiration
            "ace",  # [1]  path 1
            "navigator",  # [2]  path 2
            "",  # [3]  backstory oracle confirm
            "",  # [4]  backstory
            "Find the truth",  # [5]  vow
            "Ghost",  # [6]  ship name
            "",  # [7]  history oracle confirm
            "",  # [8]  quirk oracle confirm
            "empath",  # [9]  final asset
            "3",  # [10] edge
            "2",  # [11] heart
            "2",  # [12] iron
            "1",  # [13] shadow
            "1",  # [14] wits
            "",  # [15] look
            "",  # [16] act
            "",  # [17] wear
            "Kael",  # [18] name
            "",  # [19] pronouns
            "",  # [20] callsign
            "",  # [21] homeworld
            "",  # [22] gear done
            "1",  # [23] dice mode
            "",  # [24] confirm
        ]

        with (
            patch(
                "soloquest.commands.new_character.run_truths_wizard",
                return_value=chosen,
            ),
            patch("soloquest.commands.new_character.PromptSession") as mock_session_class,
        ):
            mock_session = MagicMock()
            mock_session.prompt.side_effect = answers
            mock_session_class.return_value = mock_session
            result = run_new_character_flow(DATA_DIR, truth_categories)

        assert result is not None
        character, vows, dice_mode = result
        assert character.truths == chosen

    def test_cancel_during_truths_returns_none(self):
        """Cancelling at the truths wizard returns None."""
        truth_categories = self._make_truth_categories()

        with patch(
            "soloquest.commands.new_character.run_truths_wizard",
            return_value=None,
        ):
            result = run_new_character_flow(DATA_DIR, truth_categories)

        assert result is None

    def test_cancel_during_character_creation_returns_none(self):
        """Cancelling during character creation returns None."""
        from soloquest.models.truths import ChosenTruth

        chosen = [ChosenTruth(category="The Cataclysm", option_summary="All is well")]
        truth_categories = self._make_truth_categories()

        with (
            patch(
                "soloquest.commands.new_character.run_truths_wizard",
                return_value=chosen,
            ),
            patch(
                "soloquest.commands.new_character.run_creation_wizard",
                return_value=None,
            ),
        ):
            result = run_new_character_flow(DATA_DIR, truth_categories)

        assert result is None
