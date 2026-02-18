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


def _make_path_session_prompt(paths):
    """Create a mock PromptSession that returns paths in sequence."""
    mock_session = MagicMock()
    mock_session.prompt.side_effect = paths
    return mock_session


class TestRunCreationWizard:
    """Integration tests for run_creation_wizard — mocking all I/O."""

    def _run_wizard_with_answers(self, prompt_answers, confirm_answers=None):
        """Run the wizard with mocked Prompt.ask and Confirm.ask answers."""
        if confirm_answers is None:
            # Default: skip all optional oracle rolls, confirm at end
            confirm_answers = [False, False, False, True]

        with (
            patch("soloquest.commands.new_character.Prompt.ask", side_effect=prompt_answers),
            patch("soloquest.commands.new_character.Confirm.ask", side_effect=confirm_answers),
            patch("soloquest.commands.new_character.PromptSession") as mock_session_class,
        ):
            # Make PromptSession().prompt() return values for asset prompts
            mock_session = MagicMock()
            # path1, path2, final_asset
            mock_session.prompt.side_effect = ["ace", "navigator", "empath"]
            mock_session_class.return_value = mock_session

            result = run_creation_wizard(DATA_DIR)

        return result

    def test_wizard_returns_character_vows_dice_mode(self):
        """Successful completion returns a 3-tuple."""
        prompt_answers = [
            # Step 1 inspiration (skip)
            "",
            # Step 3 backstory
            "",
            # Step 4 background vow
            "Find the truth",
            # Step 5 ship name
            "Stellar Drift",
            # Step 7 stats: edge=3, heart=2, iron=2, shadow=1, wits=1
            "3",
            "2",
            "2",
            "1",
            "1",
            # Step 9 envision
            "",
            "",
            "",
            # Step 10 name/pronouns/callsign/homeworld
            "Kael",
            "",
            "",
            "The Rift",
            # Step 11 gear (skip immediately)
            "",
            # Dice mode
            "1",
        ]
        result = self._run_wizard_with_answers(prompt_answers)
        assert result is not None
        character, vows, dice_mode = result
        assert character.name == "Kael"
        assert character.homeworld == "The Rift"
        assert dice_mode == DiceMode.DIGITAL

    def test_wizard_grants_starship_and_two_paths(self):
        """Character must have starship + 2 path assets + 1 free asset."""
        prompt_answers = [
            "",  # inspiration (skip)
            "",  # backstory
            "Find the truth",  # vow
            "Rusty",  # ship name
            "3",
            "2",
            "2",
            "1",
            "1",  # stats
            "",
            "",
            "",  # envision
            "Kael",
            "",
            "",
            "",  # name/pronouns/callsign/homeworld
            "",  # gear done
            "1",  # dice mode
        ]
        result = self._run_wizard_with_answers(prompt_answers)
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
        prompt_answers = [
            "",  # inspiration (skip)
            "",
            "Find the truth",
            "Stellar Drift",
            "3",
            "2",
            "2",
            "1",
            "1",
            "",
            "",
            "",
            "Kael",
            "",
            "",
            "",
            "",
            "1",
        ]
        result = self._run_wizard_with_answers(prompt_answers)
        assert result is not None
        character, _, _ = result
        starship = next(a for a in character.assets if a.asset_key == "starship")
        assert starship.input_values.get("name") == "Stellar Drift"

    def test_wizard_creates_epic_background_vow(self):
        """Background vow must be Epic rank."""
        from soloquest.models.vow import VowRank

        prompt_answers = [
            "",  # inspiration (skip)
            "",
            "Avenge my homeworld",
            "",
            "3",
            "2",
            "2",
            "1",
            "1",
            "",
            "",
            "",
            "Kael",
            "",
            "",
            "",
            "",
            "1",
        ]
        result = self._run_wizard_with_answers(prompt_answers)
        assert result is not None
        _, vows, _ = result
        assert len(vows) == 1
        assert vows[0].rank == VowRank.EPIC
        assert vows[0].description == "Avenge my homeworld"

    def test_wizard_stores_narrative_fields(self):
        """Narrative fields (look, act, wear, pronouns, callsign, backstory) are stored."""
        prompt_answers = [
            "",  # inspiration (skip)
            "Fled the war",  # backstory
            "Find the truth",  # vow
            "Ghost",  # ship name
            "3",
            "2",
            "2",
            "1",
            "1",  # stats
            "Tall with red hair",  # look
            "Calm and decisive",  # act
            "Worn leather jacket",  # wear
            "Kael",  # name
            "they/them",  # pronouns
            "Shadow",  # callsign
            "Drift Station",  # homeworld
            "",  # gear done
            "1",  # dice mode
        ]
        result = self._run_wizard_with_answers(prompt_answers)
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
        prompt_answers = [
            "",  # inspiration (skip)
            "",  # backstory
            "Find the truth",  # vow
            "",  # ship name
            "3",
            "2",
            "2",
            "1",
            "1",  # stats
            "",
            "",
            "",  # envision
            "Kael",
            "",
            "",
            "",  # name etc.
            "Data pad",  # gear 1
            "Lucky coin",  # gear 2
            "",  # gear done
            "1",  # dice mode
        ]
        result = self._run_wizard_with_answers(prompt_answers)
        assert result is not None
        character, _, _ = result
        assert "Data pad" in character.gear
        assert "Lucky coin" in character.gear

    def test_wizard_supply_starts_at_5(self):
        """Character supply should start at 5 per rulebook."""
        prompt_answers = [
            "",  # inspiration (skip)
            "",
            "Find the truth",
            "",
            "3",
            "2",
            "2",
            "1",
            "1",
            "",
            "",
            "",
            "Kael",
            "",
            "",
            "",
            "",
            "1",
        ]
        result = self._run_wizard_with_answers(prompt_answers)
        assert result is not None
        character, _, _ = result
        assert character.supply == 5

    def test_wizard_cancellation_returns_none_on_back(self):
        """Typing 'back' at name prompt returns None."""
        prompt_answers = [
            "",  # inspiration (skip)
            "",  # backstory
            "Find the truth",  # vow
            "",  # ship name
            "3",
            "2",
            "2",
            "1",
            "1",  # stats
            "",
            "",
            "",  # envision
            "back",  # name → cancel
        ]
        result = self._run_wizard_with_answers(prompt_answers)
        assert result is None

    def test_wizard_cancellation_returns_none_on_keyboard_interrupt(self):
        """KeyboardInterrupt at any step returns None."""
        mock_session = MagicMock()
        mock_session.prompt.side_effect = KeyboardInterrupt
        with (
            patch(
                "soloquest.commands.new_character.Prompt.ask",
                side_effect=KeyboardInterrupt,
            ),
            patch("soloquest.commands.new_character.Confirm.ask", return_value=False),
            patch(
                "soloquest.commands.new_character.PromptSession",
                return_value=mock_session,
            ),
        ):
            result = run_creation_wizard(DATA_DIR)
        assert result is None

    def test_wizard_dice_mode_physical(self):
        """Selecting '2' sets physical dice mode."""
        prompt_answers = [
            "",  # inspiration (skip)
            "",
            "Find the truth",
            "",
            "3",
            "2",
            "2",
            "1",
            "1",
            "",
            "",
            "",
            "Kael",
            "",
            "",
            "",
            "",
            "2",  # physical dice mode
        ]
        result = self._run_wizard_with_answers(prompt_answers)
        assert result is not None
        _, _, dice_mode = result
        assert dice_mode == DiceMode.PHYSICAL

    def test_wizard_confirm_no_returns_none(self):
        """Declining the final confirmation returns None."""
        prompt_answers = [
            "",  # inspiration (skip)
            "",
            "Find the truth",
            "",
            "3",
            "2",
            "2",
            "1",
            "1",
            "",
            "",
            "",
            "Kael",
            "",
            "",
            "",
            "",
            "1",
        ]
        # Last confirm=False means cancel
        confirm_answers = [False, False, False, False]
        result = self._run_wizard_with_answers(prompt_answers, confirm_answers)
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

    def _wizard_prompt_answers(self):
        return [
            "",  # inspiration (skip)
            "",  # backstory
            "Find the truth",  # vow
            "Ghost",  # ship name
            "3",
            "2",
            "2",
            "1",
            "1",  # stats
            "",
            "",
            "",  # envision
            "Kael",
            "",
            "",
            "",  # name/pronouns/callsign/homeworld
            "",  # gear done
            "1",  # dice mode
        ]

    def test_truths_attached_to_character(self):
        """Truths returned by run_truths_wizard are attached to the character."""
        from soloquest.models.truths import ChosenTruth

        chosen = [ChosenTruth(category="The Cataclysm", option_summary="All is well")]
        truth_categories = self._make_truth_categories()

        mock_session = MagicMock()
        mock_session.prompt.side_effect = ["ace", "navigator", "empath"]

        with (
            patch(
                "soloquest.commands.new_character.run_truths_wizard",
                return_value=chosen,
            ),
            patch(
                "soloquest.commands.new_character.Prompt.ask",
                side_effect=self._wizard_prompt_answers(),
            ),
            patch(
                "soloquest.commands.new_character.Confirm.ask",
                side_effect=[False, False, False, True],
            ),
            patch(
                "soloquest.commands.new_character.PromptSession",
                return_value=mock_session,
            ),
        ):
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
