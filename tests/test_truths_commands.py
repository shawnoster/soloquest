"""Tests for commands/truths.py - truth selection wizard."""

from __future__ import annotations

from unittest.mock import ANY, MagicMock, patch

import pytest

from soloquest.commands.truths import (
    _create_chosen_truth,
    _get_subchoice,
    _get_truth_choice,
    _prompt_note,
    _prompt_to_start_wizard,
    _show_option_details,
    _show_summary,
    _show_truths,
    _start_truths_wizard,
    handle_truths,
    run_truths_wizard,
)
from soloquest.models.character import Character, Stats
from soloquest.models.session import Session
from soloquest.models.truths import ChosenTruth, TruthCategory, TruthOption


@pytest.fixture
def mock_state():
    """Create a mock game state for testing."""
    state = MagicMock()
    state.character = Character(
        name="Test Character",
        homeworld="Test World",
        stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3),
    )
    state.character.truths = []
    state.session = Session(number=1)
    state.truth_categories = _make_test_categories()
    state.campaign = None
    return state


def _make_test_categories() -> dict[str, TruthCategory]:
    """Create test truth categories."""
    return {
        "Cataclysm": TruthCategory(
            name="Cataclysm",
            description="What ended the old world?",
            order=1,
            options=[
                TruthOption(
                    roll_range=(1, 33),
                    summary="The Sun Plague",
                    text="Stars dimmed across the galaxy.",
                    quest_starter="A lone star still burns. Why?",
                    subchoices=[
                        "Temporal distortions [1-25]",
                        "Dark matter decay [26-50]",
                        "Superweapon [51-75]",
                        "Experiment gone wrong [76-100]",
                    ],
                ),
                TruthOption(
                    roll_range=(34, 67),
                    summary="Interdimensional entities",
                    text="Beings from another realm invaded.",
                ),
                TruthOption(
                    roll_range=(68, 100),
                    summary="Catastrophic war",
                    text="We fought ourselves to the brink.",
                ),
            ],
        ),
        "Exodus": TruthCategory(
            name="Exodus",
            description="How did we reach the Forge?",
            order=2,
            options=[
                TruthOption(
                    roll_range=(1, 50),
                    summary="Generation ships",
                    text="A millennia-long journey.",
                ),
                TruthOption(
                    roll_range=(51, 100),
                    summary="Alien gates",
                    text="Instantaneous passage through wormholes.",
                ),
            ],
        ),
    }


# ── handle_truths router tests ────────────────────────────────────────────


class TestHandleTruths:
    """Test the main handle_truths command router."""

    @patch("soloquest.commands.truths._start_truths_wizard")
    def test_handle_truths_start_subcommand(self, mock_start, mock_state):
        """Test /truths start calls wizard."""
        handle_truths(mock_state, ["start"], set())
        mock_start.assert_called_once_with(mock_state)

    @patch("soloquest.commands.truths._show_truths")
    def test_handle_truths_show_subcommand(self, mock_show, mock_state):
        """Test /truths show displays truths."""
        handle_truths(mock_state, ["show"], set())
        mock_show.assert_called_once_with(mock_state)

    @patch("soloquest.commands.truths._handle_truth_propose")
    def test_handle_truths_propose_subcommand(self, mock_propose, mock_state):
        """Test /truths propose routes correctly."""
        handle_truths(mock_state, ["propose", "Cataclysm"], set())
        mock_propose.assert_called_once_with(mock_state, ["Cataclysm"])

    @patch("soloquest.commands.truths._handle_truth_review")
    def test_handle_truths_review_subcommand(self, mock_review, mock_state):
        """Test /truths review routes correctly."""
        handle_truths(mock_state, ["review"], set())
        mock_review.assert_called_once_with(mock_state)

    @patch("soloquest.commands.truths._handle_truth_accept")
    def test_handle_truths_accept_subcommand(self, mock_accept, mock_state):
        """Test /truths accept routes correctly."""
        handle_truths(mock_state, ["accept", "Cataclysm"], set())
        mock_accept.assert_called_once_with(mock_state, ["Cataclysm"])

    @patch("soloquest.commands.truths._handle_truth_counter")
    def test_handle_truths_counter_subcommand(self, mock_counter, mock_state):
        """Test /truths counter routes correctly."""
        handle_truths(mock_state, ["counter", "option"], set())
        mock_counter.assert_called_once_with(mock_state, ["option"])

    @patch("soloquest.commands.truths._show_truths")
    def test_handle_truths_no_args_with_existing_truths(self, mock_show, mock_state):
        """Test /truths with no args shows truths if they exist."""
        mock_state.character.truths = [
            ChosenTruth(category="Cataclysm", option_summary="The Sun Plague")
        ]
        handle_truths(mock_state, [], set())
        mock_show.assert_called_once_with(mock_state)

    @patch("soloquest.commands.truths._prompt_to_start_wizard")
    def test_handle_truths_no_args_without_truths(self, mock_prompt, mock_state):
        """Test /truths with no args prompts to start wizard if no truths."""
        mock_state.character.truths = []
        handle_truths(mock_state, [], set())
        mock_prompt.assert_called_once_with(mock_state)


# ── Prompt to start wizard tests ──────────────────────────────────────────


class TestPromptToStartWizard:
    """Test the initial prompt to start the truths wizard."""

    @patch("soloquest.commands.truths.display")
    @patch("soloquest.commands.truths.Confirm.ask", return_value=False)
    def test_prompt_to_start_wizard_declined(self, mock_confirm, mock_display, mock_state):
        """Test declining to start wizard shows info message."""
        _prompt_to_start_wizard(mock_state)
        mock_confirm.assert_called_once()
        mock_display.info.assert_called_once()

    @patch("soloquest.commands.truths._start_truths_wizard")
    @patch("soloquest.commands.truths.display")
    @patch("soloquest.commands.truths.Confirm.ask", return_value=True)
    def test_prompt_to_start_wizard_accepted(
        self, mock_confirm, mock_display, mock_start, mock_state
    ):
        """Test accepting prompt starts wizard."""
        _prompt_to_start_wizard(mock_state)
        mock_confirm.assert_called_once()
        mock_start.assert_called_once_with(mock_state)

    @patch("soloquest.commands.truths.display")
    @patch("soloquest.commands.truths.Confirm.ask", side_effect=KeyboardInterrupt)
    def test_prompt_to_start_wizard_keyboard_interrupt(
        self, mock_confirm, mock_display, mock_state
    ):
        """Test keyboard interrupt during prompt."""
        _prompt_to_start_wizard(mock_state)
        mock_display.info.assert_called_once()

    @patch("soloquest.commands.truths.display")
    @patch("soloquest.commands.truths.Confirm.ask", side_effect=EOFError)
    def test_prompt_to_start_wizard_eof_error(self, mock_confirm, mock_display, mock_state):
        """Test EOF error during prompt."""
        _prompt_to_start_wizard(mock_state)
        mock_display.info.assert_called_once()


# ── Start truths wizard tests ─────────────────────────────────────────────


class TestStartTruthsWizard:
    """Test starting the truths wizard."""

    @patch("soloquest.commands.truths.run_truths_wizard")
    @patch("soloquest.commands.truths.display")
    def test_start_wizard_with_no_existing_truths(self, mock_display, mock_run_wizard, mock_state):
        """Test starting wizard when no truths exist."""
        chosen_truths = [ChosenTruth(category="Cataclysm", option_summary="The Sun Plague")]
        mock_run_wizard.return_value = chosen_truths

        _start_truths_wizard(mock_state)

        mock_run_wizard.assert_called_once_with(
            mock_state.truth_categories, existing_truths=None, on_truth_saved=ANY
        )
        assert mock_state.character.truths == chosen_truths
        mock_display.success.assert_called_once()

    @patch("soloquest.commands.truths.run_truths_wizard")
    @patch("soloquest.commands.truths.display")
    @patch("soloquest.commands.truths.Confirm.ask", return_value=True)
    def test_start_wizard_with_existing_truths_overwrite_confirmed(
        self, mock_confirm, mock_display, mock_run_wizard, mock_state
    ):
        """Test starting wizard with existing truths and confirming overwrite."""
        mock_state.character.truths = [ChosenTruth(category="Old", option_summary="Old truth")]
        new_truths = [ChosenTruth(category="Cataclysm", option_summary="The Sun Plague")]
        mock_run_wizard.return_value = new_truths

        _start_truths_wizard(mock_state)

        mock_confirm.assert_called_once()
        mock_run_wizard.assert_called_once()
        assert mock_state.character.truths == new_truths

    @patch("soloquest.commands.truths.display")
    @patch("soloquest.commands.truths.Confirm.ask", return_value=False)
    def test_start_wizard_with_existing_truths_overwrite_declined(
        self, mock_confirm, mock_display, mock_state
    ):
        """Test declining to resume and declining to start over keeps existing truths."""
        original_truths = [ChosenTruth(category="Old", option_summary="Old truth")]
        mock_state.character.truths = original_truths.copy()

        _start_truths_wizard(mock_state)

        # is_partial path: "Resume?" (False) → "Start over?" (False) → keep truths
        assert mock_confirm.call_count == 2
        mock_display.info.assert_called_once()
        assert mock_state.character.truths == original_truths

    @patch("soloquest.commands.truths.display")
    @patch("soloquest.commands.truths.Confirm.ask", side_effect=KeyboardInterrupt)
    def test_start_wizard_keyboard_interrupt_on_overwrite_prompt(
        self, mock_confirm, mock_display, mock_state
    ):
        """Test keyboard interrupt during resume/overwrite prompt keeps existing truths."""
        original_truths = [ChosenTruth(category="Old", option_summary="Old truth")]
        mock_state.character.truths = original_truths.copy()

        _start_truths_wizard(mock_state)

        mock_display.info.assert_called_once_with("Keeping existing truths.")
        assert mock_state.character.truths == original_truths

    @patch("soloquest.commands.truths.run_truths_wizard", return_value=None)
    @patch("soloquest.commands.truths.display")
    def test_start_wizard_cancelled_during_wizard(self, mock_display, mock_run_wizard, mock_state):
        """Test wizard returning None (cancelled)."""
        original_truths = []
        mock_state.character.truths = original_truths

        _start_truths_wizard(mock_state)

        # Truths should remain unchanged
        assert mock_state.character.truths == original_truths
        # Success should not be called
        mock_display.success.assert_not_called()


# ── Truth choice tests ────────────────────────────────────────────────────


class TestGetTruthChoice:
    """Test the truth choice selection logic."""

    def setup_method(self):
        self.category = TruthCategory(
            name="Cataclysm",
            description="What ended the old world?",
            order=1,
            options=[
                TruthOption(
                    roll_range=(1, 33),
                    summary="The Sun Plague",
                    text="Stars dimmed.",
                ),
                TruthOption(
                    roll_range=(34, 67),
                    summary="Entities",
                    text="Beings invaded.",
                ),
                TruthOption(
                    roll_range=(68, 100),
                    summary="War",
                    text="We fought.",
                ),
            ],
        )

    @patch("soloquest.commands.truths.Prompt.ask", return_value="1")
    @patch("soloquest.commands.truths._show_option_details", return_value="")
    @patch("soloquest.commands.truths._prompt_note", return_value="")
    @patch("soloquest.commands.truths.display")
    def test_get_truth_choice_numbered_option_1(
        self, mock_display, mock_note, mock_details, mock_prompt
    ):
        """Test selecting option 1."""
        result = _get_truth_choice(self.category)

        assert result is not None
        assert result.category == "Cataclysm"
        assert result.option_summary == "The Sun Plague"
        mock_details.assert_called_once()
        mock_note.assert_called_once()

    @patch("soloquest.commands.truths.Prompt.ask", return_value="2")
    @patch("soloquest.commands.truths._show_option_details", return_value="")
    @patch("soloquest.commands.truths._prompt_note", return_value="My note")
    @patch("soloquest.commands.truths.display")
    def test_get_truth_choice_numbered_option_2_with_note(
        self, mock_display, mock_note, mock_details, mock_prompt
    ):
        """Test selecting option 2 with a note."""
        result = _get_truth_choice(self.category)

        assert result is not None
        assert result.option_summary == "Entities"
        assert result.note == "My note"

    @patch("soloquest.commands.truths.Prompt.ask", return_value="3")
    @patch("soloquest.commands.truths._show_option_details", return_value="subchoice text")
    @patch("soloquest.commands.truths._prompt_note", return_value="")
    @patch("soloquest.commands.truths.display")
    def test_get_truth_choice_numbered_option_3_with_subchoice(
        self, mock_display, mock_note, mock_details, mock_prompt
    ):
        """Test selecting option 3 with subchoice."""
        result = _get_truth_choice(self.category)

        assert result is not None
        assert result.option_summary == "War"
        assert result.subchoice == "subchoice text"

    @patch("soloquest.commands.truths.Prompt.ask", return_value="s")
    @patch("soloquest.commands.truths.display")
    def test_get_truth_choice_skip(self, mock_display, mock_prompt):
        """Test skipping a truth."""
        result = _get_truth_choice(self.category)

        assert result is not None
        assert result.category == "Cataclysm"
        assert result.option_summary == "[To be determined]"
        mock_display.info.assert_called_once()

    def test_get_truth_choice_custom(self):
        """Test entering a custom truth."""
        # Mock Prompt.ask to return "c" first (for choice), then the custom text
        with (
            patch("soloquest.commands.truths.Prompt.ask") as mock_ask,
            patch("soloquest.commands.truths._prompt_note", return_value="Custom note"),
            patch("soloquest.commands.truths.display"),
        ):
            mock_ask.side_effect = ["c", "My custom truth"]

            result = _get_truth_choice(self.category)

            assert result is not None
            assert result.category == "Cataclysm"
            assert result.option_summary == "My custom truth"
            assert result.custom_text == "My custom truth"
            assert result.note == "Custom note"

    @patch("soloquest.commands.truths._prompt_note", return_value="")
    @patch("soloquest.commands.truths.display")
    def test_get_truth_choice_custom_empty_retry(self, mock_display, mock_note):
        """Test entering empty custom truth retries."""
        # First return "c" for custom, then empty string triggers error,
        # then "c" again, then valid custom text
        with patch("soloquest.commands.truths.Prompt.ask") as mock_ask:
            mock_ask.side_effect = ["c", "", "c", "Valid custom text"]

            result = _get_truth_choice(self.category)

            assert result is not None
            assert result.custom_text == "Valid custom text"
            mock_display.error.assert_called_once()

    @patch("soloquest.commands.truths.Prompt.ask", return_value="r")
    @patch("soloquest.commands.truths.random.randint", return_value=50)
    @patch("soloquest.commands.truths._show_option_details", return_value="")
    @patch("soloquest.commands.truths._prompt_note", return_value="")
    @patch("soloquest.commands.truths.display")
    def test_get_truth_choice_roll(
        self, mock_display, mock_note, mock_details, mock_randint, mock_prompt
    ):
        """Test rolling for a truth."""
        result = _get_truth_choice(self.category)

        assert result is not None
        assert result.option_summary == "Entities"  # roll 50 matches 34-67
        mock_randint.assert_called_once_with(1, 100)

    @patch("soloquest.commands.truths.Prompt.ask")
    @patch("soloquest.commands.truths.random.randint")
    @patch("soloquest.commands.truths._show_option_details", return_value="")
    @patch("soloquest.commands.truths._prompt_note", return_value="")
    @patch("soloquest.commands.truths.display")
    def test_get_truth_choice_invalid_then_valid(
        self, mock_display, mock_note, mock_details, mock_randint, mock_prompt
    ):
        """Test invalid choice followed by valid choice."""
        mock_prompt.side_effect = ["invalid", "1"]

        result = _get_truth_choice(self.category)

        assert result is not None
        assert result.option_summary == "The Sun Plague"
        mock_display.error.assert_called_once()

    @patch("soloquest.commands.truths.Prompt.ask", side_effect=KeyboardInterrupt)
    @patch("soloquest.commands.truths.display")
    def test_get_truth_choice_keyboard_interrupt(self, mock_display, mock_prompt):
        """Test keyboard interrupt raises exception."""
        with pytest.raises(KeyboardInterrupt):
            _get_truth_choice(self.category)


# ── Subchoice tests ───────────────────────────────────────────────────────


class TestGetSubchoice:
    """Test subchoice selection logic."""

    def setup_method(self):
        self.subchoices = [
            "Temporal distortions [1-25]",
            "Dark matter decay [26-50]",
            "Superweapon [51-75]",
            "Experiment gone wrong [76-100]",
        ]

    @patch("soloquest.commands.truths.Prompt.ask", return_value="1")
    @patch("soloquest.commands.truths.display")
    def test_get_subchoice_numbered_selection(self, mock_display, mock_prompt):
        """Test selecting a subchoice by number."""
        result = _get_subchoice(self.subchoices)

        assert result == "Temporal distortions"

    @patch("soloquest.commands.truths.Prompt.ask", return_value="4")
    @patch("soloquest.commands.truths.display")
    def test_get_subchoice_last_option(self, mock_display, mock_prompt):
        """Test selecting the last subchoice."""
        result = _get_subchoice(self.subchoices)

        assert result == "Experiment gone wrong"

    @patch("soloquest.commands.truths.Prompt.ask", return_value="r")
    @patch("soloquest.commands.truths.random.randint", return_value=30)
    @patch("soloquest.commands.truths.display")
    def test_get_subchoice_roll(self, mock_display, mock_randint, mock_prompt):
        """Test rolling for a subchoice."""
        result = _get_subchoice(self.subchoices)

        assert result == "Dark matter decay"  # roll 30 matches 26-50
        mock_randint.assert_called_once_with(1, 100)

    @patch("soloquest.commands.truths.Prompt.ask", return_value="r")
    @patch("soloquest.commands.truths.random.randint", return_value=1)
    @patch("soloquest.commands.truths.display")
    def test_get_subchoice_roll_first_range(self, mock_display, mock_randint, mock_prompt):
        """Test rolling matches first range."""
        result = _get_subchoice(self.subchoices)

        assert result == "Temporal distortions"

    @patch("soloquest.commands.truths.Prompt.ask", return_value="r")
    @patch("soloquest.commands.truths.random.randint", return_value=100)
    @patch("soloquest.commands.truths.display")
    def test_get_subchoice_roll_last_range(self, mock_display, mock_randint, mock_prompt):
        """Test rolling matches last range."""
        result = _get_subchoice(self.subchoices)

        assert result == "Experiment gone wrong"

    @patch("soloquest.commands.truths.Prompt.ask")
    @patch("soloquest.commands.truths.display")
    def test_get_subchoice_invalid_then_valid(self, mock_display, mock_prompt):
        """Test invalid choice followed by valid choice."""
        mock_prompt.side_effect = ["invalid", "2"]

        result = _get_subchoice(self.subchoices)

        assert result == "Dark matter decay"
        mock_display.error.assert_called_once()

    @patch("soloquest.commands.truths.Prompt.ask", side_effect=KeyboardInterrupt)
    @patch("soloquest.commands.truths.display")
    def test_get_subchoice_keyboard_interrupt(self, mock_display, mock_prompt):
        """Test keyboard interrupt returns empty string."""
        result = _get_subchoice(self.subchoices)

        assert result == ""


# ── Note prompt tests ─────────────────────────────────────────────────────


class TestPromptNote:
    """Test note prompt functionality."""

    @patch("soloquest.commands.truths.Prompt.ask", return_value="My personal note")
    def test_prompt_note_with_text(self, mock_prompt):
        """Test entering a note."""
        result = _prompt_note()

        assert result == "My personal note"

    @patch("soloquest.commands.truths.Prompt.ask", return_value="")
    def test_prompt_note_empty(self, mock_prompt):
        """Test skipping note entry."""
        result = _prompt_note()

        assert result == ""

    @patch("soloquest.commands.truths.Prompt.ask", side_effect=KeyboardInterrupt)
    def test_prompt_note_keyboard_interrupt(self, mock_prompt):
        """Test keyboard interrupt returns empty string."""
        result = _prompt_note()

        assert result == ""

    @patch("soloquest.commands.truths.Prompt.ask", side_effect=EOFError)
    def test_prompt_note_eof_error(self, mock_prompt):
        """Test EOF error returns empty string."""
        result = _prompt_note()

        assert result == ""


# ── Show option details tests ─────────────────────────────────────────────


class TestShowOptionDetails:
    """Test showing option details."""

    @patch("soloquest.commands.truths._get_subchoice", return_value="chosen sub")
    @patch("soloquest.commands.truths.display")
    def test_show_option_details_with_subchoices_and_quest_starter(
        self, mock_display, mock_subchoice
    ):
        """Test showing option with subchoices and quest starter."""
        option = TruthOption(
            roll_range=(1, 33),
            summary="Test",
            text="Test description",
            quest_starter="Test quest",
            subchoices=["Choice 1 [1-50]", "Choice 2 [51-100]"],
        )

        result = _show_option_details(option)

        assert result == "chosen sub"
        mock_subchoice.assert_called_once_with(option.subchoices)

    @patch("soloquest.commands.truths.display")
    def test_show_option_details_without_subchoices(self, mock_display):
        """Test showing option without subchoices."""
        option = TruthOption(
            roll_range=(1, 33),
            summary="Test",
            text="Test description",
            quest_starter="Test quest",
        )

        result = _show_option_details(option)

        assert result == ""

    @patch("soloquest.commands.truths.display")
    def test_show_option_details_without_quest_starter(self, mock_display):
        """Test showing option without quest starter."""
        option = TruthOption(
            roll_range=(1, 33),
            summary="Test",
            text="Test description",
        )

        result = _show_option_details(option)

        assert result == ""


# ── Show truths tests ─────────────────────────────────────────────────────


class TestShowTruths:
    """Test displaying truths."""

    @patch("soloquest.commands.truths.display")
    def test_show_truths_with_no_truths(self, mock_display, mock_state):
        """Test showing truths when none are set."""
        mock_state.character.truths = []

        _show_truths(mock_state)

        mock_display.info.assert_called_once()

    @patch("soloquest.commands.truths.display")
    def test_show_truths_with_truths(self, mock_display, mock_state):
        """Test showing truths when they exist."""
        mock_state.character.truths = [
            ChosenTruth(category="Cataclysm", option_summary="The Sun Plague"),
            ChosenTruth(
                category="Exodus",
                option_summary="Generation ships",
                note="Personal note",
            ),
        ]

        _show_truths(mock_state)

        mock_display.rule.assert_called_once()


# ── Show summary tests ────────────────────────────────────────────────────


class TestShowSummary:
    """Test showing truth summary."""

    @patch("soloquest.commands.truths.display")
    def test_show_summary_with_truths(self, mock_display):
        """Test showing summary of truths."""
        truths = [
            ChosenTruth(category="Cataclysm", option_summary="The Sun Plague"),
            ChosenTruth(
                category="Exodus",
                option_summary="Generation ships",
                note="My note",
            ),
        ]

        _show_summary(truths)

        mock_display.rule.assert_called_once()


# ── Create chosen truth tests ─────────────────────────────────────────────


class TestCreateChosenTruth:
    """Test creating chosen truth objects."""

    def test_create_chosen_truth_basic(self):
        """Test creating basic chosen truth."""
        category = TruthCategory(name="Test", description="Test", order=1, options=[])
        option = TruthOption(
            roll_range=(1, 100),
            summary="Test summary",
            text="Test text",
            quest_starter="Test quest",
        )

        result = _create_chosen_truth(category, option)

        assert result.category == "Test"
        assert result.option_summary == "Test summary"
        assert result.option_text == "Test text"
        assert result.quest_starter == "Test quest"
        assert result.subchoice == ""
        assert result.note == ""

    def test_create_chosen_truth_with_subchoice_and_note(self):
        """Test creating chosen truth with subchoice and note."""
        category = TruthCategory(name="Test", description="Test", order=1, options=[])
        option = TruthOption(
            roll_range=(1, 100),
            summary="Test",
            text="Test",
        )

        result = _create_chosen_truth(category, option, subchoice="My subchoice", note="My note")

        assert result.subchoice == "My subchoice"
        assert result.note == "My note"


# ── Run truths wizard integration tests ───────────────────────────────────


class TestRunTruthsWizard:
    """Test the full truths wizard flow."""

    @patch("soloquest.commands.truths.display")
    def test_run_truths_wizard_no_categories(self, mock_display):
        """Test wizard with no categories returns None."""
        result = run_truths_wizard({})

        assert result is None
        mock_display.error.assert_called_once()

    @patch("soloquest.commands.truths.Confirm.ask", return_value=False)
    @patch("soloquest.commands.truths._get_truth_choice")
    @patch("soloquest.commands.truths.display")
    def test_run_truths_wizard_declined_confirmation(
        self, mock_display, mock_get_choice, mock_confirm
    ):
        """Test declining final confirmation returns None."""
        categories = _make_test_categories()
        mock_get_choice.return_value = ChosenTruth(category="Cataclysm", option_summary="Test")

        result = run_truths_wizard(categories)

        assert result is None
        mock_display.info.assert_called_once()

    @patch("soloquest.commands.truths.Confirm.ask", return_value=True)
    @patch("soloquest.commands.truths._get_truth_choice")
    @patch("soloquest.commands.truths.display")
    @patch("soloquest.commands.truths._show_introduction")
    def test_run_truths_wizard_success(
        self, mock_intro, mock_display, mock_get_choice, mock_confirm
    ):
        """Test successful wizard completion."""
        categories = _make_test_categories()

        # Return different truth for each category
        mock_get_choice.side_effect = [
            ChosenTruth(category="Cataclysm", option_summary="The Sun Plague"),
            ChosenTruth(category="Exodus", option_summary="Generation ships"),
        ]

        result = run_truths_wizard(categories)

        assert result is not None
        assert len(result) == 2
        assert result[0].category == "Cataclysm"
        assert result[1].category == "Exodus"

    @patch("soloquest.commands.truths._get_truth_choice", side_effect=KeyboardInterrupt)
    @patch("soloquest.commands.truths.display")
    @patch("soloquest.commands.truths._show_introduction")
    def test_run_truths_wizard_keyboard_interrupt(self, mock_intro, mock_display, mock_get_choice):
        """Test keyboard interrupt during wizard returns None."""
        categories = _make_test_categories()

        result = run_truths_wizard(categories)

        assert result is None
        mock_display.info.assert_called_once()
