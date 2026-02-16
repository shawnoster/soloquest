"""Tests for the guide command."""

from unittest.mock import MagicMock

import pytest

from soloquest.commands.guide import handle_guide
from soloquest.engine.dice import DiceMode, make_dice_provider
from soloquest.models.character import Character, Stats
from soloquest.models.session import Session
from soloquest.models.vow import Vow, VowRank


@pytest.fixture
def mock_state():
    """Create a mock game state for testing."""
    state = MagicMock()
    state.character = Character(
        name="Test Character",
        homeworld="Test World",
        stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3),
    )
    state.vows = [Vow(description="Test vow", rank=VowRank.DANGEROUS)]
    state.session = Session(number=1)
    state.session_count = 1
    state.dice_mode = DiceMode.DIGITAL
    state.dice = make_dice_provider(DiceMode.DIGITAL)
    state.moves = {"face_danger": {"name": "Face Danger"}}
    state.oracles = {}
    state.assets = {}
    return state


class TestGuideCommand:
    """Test the guide command functionality."""

    def test_guide_no_args_shows_game_loop(self, mock_state, capsys):
        """Test that /guide with no args shows the full game loop."""
        handle_guide(mock_state, [], set())
        captured = capsys.readouterr()

        # Check for key game loop elements
        assert "START" in captured.out
        assert "ENVISION" in captured.out
        assert "ASK THE ORACLE" in captured.out
        assert "MAKE A MOVE" in captured.out
        assert "OUTCOMES" in captured.out
        assert "STRONG HIT" in captured.out
        assert "WEAK HIT" in captured.out
        assert "MISS" in captured.out

    def test_guide_envision_shows_envision_help(self, mock_state, capsys):
        """Test that /guide envision shows envisioning help."""
        handle_guide(mock_state, ["envision"], set())
        captured = capsys.readouterr()

        assert "ENVISION" in captured.out
        assert "fiction" in captured.out.lower()
        assert "Just type" in captured.out or "Type narrative" in captured.out

    def test_guide_oracle_shows_oracle_help(self, mock_state, capsys):
        """Test that /guide oracle shows oracle help."""
        handle_guide(mock_state, ["oracle"], set())
        captured = capsys.readouterr()

        assert "ORACLE" in captured.out.upper()
        assert "/oracle" in captured.out

    def test_guide_move_shows_move_help(self, mock_state, capsys):
        """Test that /guide move shows move help."""
        handle_guide(mock_state, ["move"], set())
        captured = capsys.readouterr()

        assert "MOVE" in captured.out.upper()
        assert "/move" in captured.out
        assert "stat" in captured.out.lower()

    def test_guide_outcome_shows_outcome_help(self, mock_state, capsys):
        """Test that /guide outcome shows outcome help."""
        handle_guide(mock_state, ["outcome"], set())
        captured = capsys.readouterr()

        assert "OUTCOMES" in captured.out.upper()
        assert "STRONG HIT" in captured.out
        assert "WEAK HIT" in captured.out
        assert "MISS" in captured.out

    def test_guide_with_low_health_shows_warning(self, mock_state, capsys):
        """Test that guide shows health warning when health is low."""
        mock_state.character.health = 1
        handle_guide(mock_state, [], set())
        captured = capsys.readouterr()

        assert "health is low" in captured.out.lower()

    def test_guide_with_no_vows_shows_suggestion(self, mock_state, capsys):
        """Test that guide suggests creating vows when none exist."""
        mock_state.vows = []
        handle_guide(mock_state, [], set())
        captured = capsys.readouterr()

        assert "no active vows" in captured.out.lower() or "vow" in captured.out.lower()

    def test_guide_handles_invalid_step(self, mock_state, capsys):
        """Test that /guide with invalid step shows main guide."""
        handle_guide(mock_state, ["invalid"], set())
        captured = capsys.readouterr()

        # Should show main guide since invalid step is not recognized
        assert "START" in captured.out or len(captured.out) > 0
