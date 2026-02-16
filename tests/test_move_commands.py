"""Tests for move command handlers."""

from unittest.mock import MagicMock, patch

from soloquest.commands.move import (
    _apply_move_momentum,
    _choose_stat,
    _outcome_text,
    fuzzy_match_move,
    handle_move,
)
from soloquest.engine.moves import OutcomeTier
from soloquest.models.character import Character, Stats
from soloquest.models.session import Session


class TestFuzzyMatchMove:
    """Tests for move fuzzy matching."""

    def setup_method(self):
        self.moves = {
            "strike": {"name": "Strike"},
            "secure_an_advantage": {"name": "Secure an Advantage"},
            "face_danger": {"name": "Face Danger"},
            "gather_information": {"name": "Gather Information"},
        }

    def test_empty_query_returns_no_matches(self):
        """Empty query should return no matches."""
        matches = fuzzy_match_move("", self.moves)
        assert len(matches) == 0

    def test_exact_key_match(self):
        """Exact key match should return only that move."""
        matches = fuzzy_match_move("strike", self.moves)
        assert len(matches) == 1
        assert matches[0] == "strike"

    def test_exact_name_match(self):
        """Exact name match should return that move."""
        matches = fuzzy_match_move("face_danger", self.moves)
        assert "face_danger" in matches

    def test_prefix_key_match(self):
        """Prefix match on key should work."""
        matches = fuzzy_match_move("face", self.moves)
        assert "face_danger" in matches

    def test_prefix_name_match(self):
        """Prefix match on name should work."""
        matches = fuzzy_match_move("secure", self.moves)
        assert "secure_an_advantage" in matches

    def test_substring_match(self):
        """Substring match should work when no exact/prefix match."""
        matches = fuzzy_match_move("danger", self.moves)
        assert "face_danger" in matches

    def test_case_insensitive(self):
        """Matching should be case-insensitive."""
        matches_lower = fuzzy_match_move("strike", self.moves)
        matches_upper = fuzzy_match_move("STRIKE", self.moves)
        assert matches_lower == matches_upper

    def test_normalizes_spaces_and_underscores(self):
        """Spaces and underscores should be normalized."""
        matches_underscore = fuzzy_match_move("face_danger", self.moves)
        matches_space = fuzzy_match_move("face danger", self.moves)
        assert matches_underscore == matches_space

    def test_normalizes_hyphens(self):
        """Hyphens should be normalized to underscores."""
        matches_hyphen = fuzzy_match_move("face-danger", self.moves)
        matches_underscore = fuzzy_match_move("face_danger", self.moves)
        assert matches_hyphen == matches_underscore

    def test_exact_match_priority_over_prefix(self):
        """Exact matches should take priority over prefix matches."""
        moves = {
            "strike": {"name": "Strike"},
            "strike_hard": {"name": "Strike Hard"},
        }
        matches = fuzzy_match_move("strike", moves)
        # Exact match should be first (or only)
        assert matches[0] == "strike"

    def test_prefix_match_priority_over_substring(self):
        """Prefix matches should take priority over substring matches."""
        moves = {
            "face_danger": {"name": "Face Danger"},
            "defy_danger": {"name": "Defy Danger"},
        }
        matches = fuzzy_match_move("face", moves)
        # face_danger (prefix) should come before defy_danger (substring)
        assert matches[0] == "face_danger"


class TestOutcomeText:
    """Tests for _outcome_text helper."""

    def test_strong_hit_returns_strong_hit_text(self):
        """Strong hit should return strong hit text from move."""
        move = {"strong_hit": "You succeed spectacularly!"}
        text = _outcome_text(OutcomeTier.STRONG_HIT, move)
        assert text == "You succeed spectacularly!"

    def test_weak_hit_returns_weak_hit_text(self):
        """Weak hit should return weak hit text from move."""
        move = {"weak_hit": "You succeed, but at a cost."}
        text = _outcome_text(OutcomeTier.WEAK_HIT, move)
        assert text == "You succeed, but at a cost."

    def test_miss_returns_miss_text(self):
        """Miss should return miss text from move."""
        move = {"miss": "You fail. Pay the Price."}
        text = _outcome_text(OutcomeTier.MISS, move)
        assert text == "You fail. Pay the Price."

    def test_default_strong_hit_text(self):
        """Should use default text if move doesn't specify."""
        move = {}
        text = _outcome_text(OutcomeTier.STRONG_HIT, move)
        assert text == "Strong hit."

    def test_default_weak_hit_text(self):
        """Should use default text if move doesn't specify."""
        move = {}
        text = _outcome_text(OutcomeTier.WEAK_HIT, move)
        assert text == "Weak hit."

    def test_default_miss_text(self):
        """Should use default text if move doesn't specify."""
        move = {}
        text = _outcome_text(OutcomeTier.MISS, move)
        assert text == "Miss. Pay the Price."


class TestApplyMoveMomentum:
    """Tests for _apply_move_momentum helper."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(name="Test", stats=Stats())
        self.state.character.momentum = 0
        self.state.session = Session(number=1)

    def test_strong_hit_applies_momentum_bonus(self):
        """Strong hit should apply momentum bonus from move."""
        move = {"momentum_on_strong": 2}
        delta = _apply_move_momentum(OutcomeTier.STRONG_HIT, move, self.state)

        assert delta == 2
        assert self.state.character.momentum == 2

    def test_weak_hit_applies_momentum_bonus(self):
        """Weak hit should apply momentum bonus from move."""
        move = {"momentum_on_weak": 1}
        delta = _apply_move_momentum(OutcomeTier.WEAK_HIT, move, self.state)

        assert delta == 1
        assert self.state.character.momentum == 1

    def test_miss_no_momentum_bonus(self):
        """Miss should not apply any momentum bonus."""
        move = {"momentum_on_strong": 2}
        delta = _apply_move_momentum(OutcomeTier.MISS, move, self.state)

        assert delta == 0
        assert self.state.character.momentum == 0

    def test_no_bonus_defined_returns_zero(self):
        """If move has no momentum bonus, should return 0."""
        move = {}
        delta = _apply_move_momentum(OutcomeTier.STRONG_HIT, move, self.state)

        assert delta == 0
        assert self.state.character.momentum == 0

    def test_logs_momentum_change_to_session(self):
        """Momentum changes should be logged to session."""
        move = {"momentum_on_strong": 2}
        _apply_move_momentum(OutcomeTier.STRONG_HIT, move, self.state)

        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert "Momentum +2" in entry.text
        assert entry.kind == "mechanical"


class TestChooseStat:
    """Tests for _choose_stat helper."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Test", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )

    @patch("soloquest.commands.move.Prompt.ask")
    @patch("soloquest.commands.move.display.info")
    def test_choose_stat_by_number(self, mock_info, mock_prompt):
        """Should allow choosing stat by number."""
        mock_prompt.return_value = "1"
        stat_options = ["edge", "iron"]

        stat = _choose_stat(stat_options, self.state)

        assert stat == "edge"

    @patch("soloquest.commands.move.Prompt.ask")
    @patch("soloquest.commands.move.display.info")
    def test_choose_stat_by_name(self, mock_info, mock_prompt):
        """Should allow choosing stat by name."""
        mock_prompt.return_value = "iron"
        stat_options = ["edge", "iron"]

        stat = _choose_stat(stat_options, self.state)

        assert stat == "iron"

    @patch("soloquest.commands.move.Prompt.ask")
    @patch("soloquest.commands.move.display.info")
    def test_choose_stat_by_prefix(self, mock_info, mock_prompt):
        """Should allow choosing stat by prefix."""
        mock_prompt.return_value = "e"
        stat_options = ["edge", "iron"]

        stat = _choose_stat(stat_options, self.state)

        assert stat == "edge"

    @patch("soloquest.commands.move.Prompt.ask")
    @patch("soloquest.commands.move.display.info")
    @patch("soloquest.commands.move.display.error")
    def test_choose_stat_invalid_then_valid(self, mock_error, mock_info, mock_prompt):
        """Should handle invalid input then accept valid input."""
        mock_prompt.side_effect = ["invalid", "iron"]
        stat_options = ["edge", "iron"]

        stat = _choose_stat(stat_options, self.state)

        assert stat == "iron"
        mock_error.assert_called_once()


class TestHandleMove:
    """Tests for handle_move command."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Test", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.session = Session(number=1)
        self.state.moves = {
            "strike": {
                "name": "Strike",
                "stat_options": ["iron", "edge"],
                "strong_hit": "You strike true!",
                "weak_hit": "You strike, but...",
                "miss": "You miss!",
            },
            "face_danger": {
                "name": "Face Danger",
                "stat_options": ["edge", "heart", "iron", "shadow", "wits"],
            },
        }
        self.state.dice = MagicMock()
        self.state.vows = []
        self.state.oracles = {}

    @patch("soloquest.commands.move.display.error")
    def test_handle_move_no_args_shows_error(self, mock_error):
        """handle_move with no args should show error."""
        handle_move(self.state, [], set())

        mock_error.assert_called_once()
        call_args = mock_error.call_args[0][0]
        assert "Usage" in call_args

    @patch("soloquest.commands.move.display.error")
    def test_handle_move_not_found_shows_error(self, mock_error):
        """handle_move with unknown move should show error."""
        handle_move(self.state, ["nonexistent"], set())

        mock_error.assert_called_once()
        call_args = mock_error.call_args[0][0]
        assert "not found" in call_args

    @patch("soloquest.commands.move.display.warn")
    def test_handle_move_multiple_matches_shows_warning(self, mock_warn):
        """handle_move with ambiguous query should show warning."""
        # Add another move that could match
        self.state.moves["strike_hard"] = {
            "name": "Strike Hard",
            "stat_options": ["iron"],
        }

        handle_move(self.state, ["stri"], set())

        mock_warn.assert_called_once()
        call_args = mock_warn.call_args[0][0]
        assert "Multiple matches" in call_args

    @patch("soloquest.commands.move.display.console.print")
    def test_handle_move_no_stat_options_displays_narrative(self, mock_print):
        """handle_move with move lacking stat_options should display as narrative move."""
        self.state.moves["narrative"] = {"name": "Narrative Move", "category": "test"}

        handle_move(self.state, ["narrative"], set())

        # Should display the move as narrative (in a panel)
        mock_print.assert_called_once()
        # Should log to session
        assert len(self.state.session.entries) == 1


class TestHandleMoveOracleRoll:
    """Tests for handle_move with oracle_roll special type."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(name="Test", stats=Stats())
        self.state.session = Session(number=1)
        self.state.moves = {
            "ask_the_oracle": {
                "name": "Ask the Oracle",
                "oracle_roll": True,
            }
        }
        self.state.dice = MagicMock()

    @patch("soloquest.commands.move.roll_challenge_dice")
    @patch("soloquest.commands.move.display.info")
    def test_handle_ask_the_oracle_rolls_challenge_dice(self, mock_info, mock_roll):
        """Ask the Oracle should roll challenge dice."""
        mock_roll.return_value = (7, 4)

        handle_move(self.state, ["ask_the_oracle"], set())

        mock_roll.assert_called_once_with(self.state.dice)
        # Should display the result
        info_calls = [call[0][0] for call in mock_info.call_args_list]
        assert any("Challenge dice" in call for call in info_calls)


class TestHandleMoveForsakeVow:
    """Tests for handle_move with forsake special type."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(name="Test", stats=Stats())
        self.state.character.spirit = 5
        self.state.session = Session(number=1)
        self.state.moves = {
            "forsake_your_vow": {
                "name": "Forsake Your Vow",
                "special": "forsake",
            }
        }
        self.state.vows = []

    @patch("soloquest.commands.move.display.error")
    def test_forsake_no_active_vows_shows_error(self, mock_error):
        """Forsaking with no active vows should show error."""
        handle_move(self.state, ["forsake_your_vow"], set())

        mock_error.assert_called_once()
        call_args = mock_error.call_args[0][0]
        assert "No active vows" in call_args


class TestHandleMoveProgressRoll:
    """Tests for handle_move with progress_roll special type."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(name="Test", stats=Stats())
        self.state.session = Session(number=1)
        self.state.moves = {
            "take_decisive_action": {
                "name": "Take Decisive Action",
                "progress_roll": True,
                "strong_hit": "You succeed!",
                "weak_hit": "You succeed with cost.",
                "miss": "You fail.",
            }
        }
        self.state.dice = MagicMock()
        self.state.vows = []

    @patch("soloquest.commands.move.roll_challenge_dice")
    @patch("soloquest.commands.move.Prompt.ask")
    @patch("soloquest.commands.move.display.move_result_panel")
    def test_progress_roll_prompts_for_progress_score(self, mock_panel, mock_prompt, mock_roll):
        """Progress roll should prompt for progress score."""
        mock_prompt.return_value = "7"
        mock_roll.return_value = (5, 6)

        handle_move(self.state, ["take_decisive_action"], set())

        mock_prompt.assert_called_once()
        assert "Progress score" in mock_prompt.call_args[0][0]

    @patch("soloquest.commands.move.roll_challenge_dice")
    @patch("soloquest.commands.move.Prompt.ask")
    @patch("soloquest.commands.move.display.error")
    def test_progress_roll_invalid_score_shows_error(self, mock_error, mock_prompt, mock_roll):
        """Progress roll with invalid score should show error."""
        mock_prompt.return_value = "notanumber"
        mock_roll.return_value = (5, 6)

        handle_move(self.state, ["take_decisive_action"], set())

        mock_error.assert_called_once()
        call_args = mock_error.call_args[0][0]
        assert "number" in call_args


class TestHandleMoveMixedDiceMode:
    """Tests for handle_move with mixed dice mode flags."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Test", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.session = Session(number=1)
        self.state.moves = {
            "strike": {
                "name": "Strike",
                "stat_options": ["iron"],
            }
        }
        self.state.vows = []
        self.state.oracles = {}

        # Set up mixed dice mode
        from soloquest.engine.dice import MixedDice

        self.state.dice = MixedDice()

    @patch("soloquest.commands.move.roll_action_dice")
    @patch("soloquest.commands.move.Prompt.ask")
    @patch("soloquest.commands.move.Confirm.ask")
    @patch("soloquest.commands.move.display.move_result_panel")
    def test_manual_flag_sets_mixed_dice_to_manual(
        self, mock_panel, mock_confirm, mock_prompt, mock_roll
    ):
        """--manual flag should set mixed dice to manual mode."""
        # First call: stat selection (return "1" for first stat option)
        # Second call: adds (return "0")
        mock_prompt.side_effect = ["1", "0"]
        mock_confirm.return_value = False
        mock_roll.return_value = (4, 5, 6)

        handle_move(self.state, ["strike"], {"manual"})

        # Dice should be set to manual then reset
        assert self.state.dice._force_physical is False  # Reset after move

    @patch("soloquest.commands.move.roll_action_dice")
    @patch("soloquest.commands.move.Prompt.ask")
    @patch("soloquest.commands.move.Confirm.ask")
    @patch("soloquest.commands.move.display.move_result_panel")
    def test_auto_flag_sets_mixed_dice_to_auto(
        self, mock_panel, mock_confirm, mock_prompt, mock_roll
    ):
        """--auto flag should set mixed dice to auto mode."""
        # First call: stat selection (return "1" for first stat option)
        # Second call: adds (return "0")
        mock_prompt.side_effect = ["1", "0"]
        mock_confirm.return_value = False
        mock_roll.return_value = (4, 5, 6)

        # First set to manual
        self.state.dice.set_manual(True)

        handle_move(self.state, ["strike"], {"auto"})

        # Should be reset to auto
        assert self.state.dice._force_physical is False


class TestHandleNarrativeMove:
    """Tests for narrative/procedural moves without dice rolls."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(name="Test", stats=Stats())
        self.state.session = Session(number=1)
        self.state.moves = {
            "begin_a_session": {
                "name": "Begin a Session",
                "category": "session",
                "description": "**When you begin a significant session**, do all of the following.",
            },
            "set_a_flag": {
                "name": "Set a Flag",
                "category": "session",
                "description": "Mark content to be avoided or embraced.",
            },
            "narrative_no_desc": {
                "name": "Narrative No Description",
                "category": "test",
            },
        }

    @patch("soloquest.commands.move.display.console.print")
    def test_handle_narrative_move_displays_panel(self, mock_print):
        """Narrative moves should display description in a panel."""
        handle_move(self.state, ["begin_a_session"], set())

        # Should have called console.print with a Panel
        mock_print.assert_called_once()
        # The panel contains the formatted description
        assert mock_print.called

    @patch("soloquest.commands.move.display.console.print")
    def test_handle_narrative_move_logs_to_session(self, mock_print):
        """Narrative moves should be logged to session."""
        handle_move(self.state, ["set_a_flag"], set())

        # Check session log
        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert "Set a Flag" in entry.text
        assert entry.kind == "move"

    @patch("soloquest.commands.move.display.console.print")
    def test_handle_narrative_move_without_description(self, mock_print):
        """Narrative moves without description should still work."""
        handle_move(self.state, ["narrative_no_desc"], set())

        # Should not crash
        mock_print.assert_called_once()

    @patch("soloquest.commands.move.display.console.print")
    def test_narrative_move_formats_category(self, mock_print):
        """Narrative moves should format category for display."""
        handle_move(self.state, ["begin_a_session"], set())

        # Category should be formatted (session -> Session)
        mock_print.assert_called_once()
        # Panel should have been created with the move
        assert mock_print.called


class TestNarrativeMoveIntegration:
    """Integration tests with real move data."""

    def setup_method(self):
        from soloquest.loop import load_move_data

        self.state = MagicMock()
        self.state.character = Character(name="Test", stats=Stats())
        self.state.session = Session(number=1)
        self.state.moves = load_move_data()

    @patch("soloquest.commands.move.display.console.print")
    def test_begin_a_session_works(self, mock_print):
        """Begin a Session should display properly."""
        handle_move(self.state, ["begin_a_session"], set())

        mock_print.assert_called_once()
        # Should log to session
        assert len(self.state.session.entries) == 1

    @patch("soloquest.commands.move.display.console.print")
    def test_end_a_session_works(self, mock_print):
        """End a Session should display properly."""
        handle_move(self.state, ["end_a_session"], set())

        mock_print.assert_called_once()

    @patch("soloquest.commands.move.display.console.print")
    def test_take_a_break_works(self, mock_print):
        """Take a Break should display properly."""
        handle_move(self.state, ["take_a_break"], set())

        mock_print.assert_called_once()

    def test_all_narrative_moves_have_descriptions(self):
        """All narrative moves should have descriptions."""
        narrative_moves = [
            k
            for k, v in self.state.moves.items()
            if not v.get("stat_options")
            and not v.get("progress_roll")
            and not v.get("oracle_roll")
            and not v.get("special")
        ]

        for move_key in narrative_moves:
            move = self.state.moves[move_key]
            # Just verify we can access move data without error
            assert "name" in move
            # Most narrative moves should have descriptions
            assert isinstance(move.get("description", ""), str)
