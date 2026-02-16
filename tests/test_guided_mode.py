"""Tests for guided mode functionality."""

from unittest.mock import MagicMock

import pytest

from soloquest.commands.guided_mode import (
    advance_phase,
    get_guided_prompt,
    start_guided_mode,
    stop_guided_mode,
)
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
    state.moves = {}
    state.oracles = {}
    state.assets = {}
    state.guided_mode = False
    state.guided_phase = "envision"
    return state


class TestGuidedMode:
    """Test guided mode functionality."""

    def test_start_guided_mode_enables_mode(self, mock_state, capsys):
        """Test that starting guided mode enables it."""
        start_guided_mode(mock_state)
        assert mock_state.guided_mode is True
        assert mock_state.guided_phase == "envision"
        captured = capsys.readouterr()
        assert "Guided Mode Started" in captured.out

    def test_stop_guided_mode_when_not_in_mode(self, mock_state, capsys):
        """Test stopping guided mode when not in it."""
        mock_state.guided_mode = False
        stop_guided_mode(mock_state)
        captured = capsys.readouterr()
        assert "not in guided mode" in captured.out.lower()

    def test_get_guided_prompt_normal_mode(self, mock_state):
        """Test prompt in normal mode."""
        mock_state.guided_mode = False
        prompt = get_guided_prompt(mock_state)
        assert prompt == "> "

    def test_get_guided_prompt_envision_phase(self, mock_state):
        """Test prompt in envision phase."""
        mock_state.guided_mode = True
        mock_state.guided_phase = "envision"
        prompt = get_guided_prompt(mock_state)
        assert "[ENVISION]" in prompt

    def test_get_guided_prompt_oracle_phase(self, mock_state):
        """Test prompt in oracle phase."""
        mock_state.guided_mode = True
        mock_state.guided_phase = "oracle"
        prompt = get_guided_prompt(mock_state)
        assert "[ORACLE]" in prompt

    def test_get_guided_prompt_move_phase(self, mock_state):
        """Test prompt in move phase."""
        mock_state.guided_mode = True
        mock_state.guided_phase = "move"
        prompt = get_guided_prompt(mock_state)
        assert "[MOVE]" in prompt

    def test_get_guided_prompt_outcome_phase(self, mock_state):
        """Test prompt in outcome phase."""
        mock_state.guided_mode = True
        mock_state.guided_phase = "outcome"
        prompt = get_guided_prompt(mock_state)
        assert "[OUTCOME]" in prompt

    def test_advance_phase_not_in_guided_mode(self, mock_state, capsys):
        """Test advancing phase when not in guided mode."""
        mock_state.guided_mode = False
        advance_phase(mock_state)
        captured = capsys.readouterr()
        assert "not in guided mode" in captured.out.lower()

    def test_advance_phase_envision_to_oracle(self, mock_state, capsys):
        """Test advancing from envision to oracle."""
        mock_state.guided_mode = True
        mock_state.guided_phase = "envision"
        advance_phase(mock_state)
        assert mock_state.guided_phase == "oracle"
        captured = capsys.readouterr()
        assert "ORACLE" in captured.out.upper()

    def test_advance_phase_oracle_to_move(self, mock_state, capsys):
        """Test advancing from oracle to move."""
        mock_state.guided_mode = True
        mock_state.guided_phase = "oracle"
        advance_phase(mock_state)
        assert mock_state.guided_phase == "move"

    def test_advance_phase_move_to_outcome(self, mock_state, capsys):
        """Test advancing from move to outcome."""
        mock_state.guided_mode = True
        mock_state.guided_phase = "move"
        advance_phase(mock_state)
        assert mock_state.guided_phase == "outcome"

    def test_advance_phase_outcome_to_envision(self, mock_state, capsys):
        """Test advancing from outcome back to envision (loop)."""
        mock_state.guided_mode = True
        mock_state.guided_phase = "outcome"
        advance_phase(mock_state)
        assert mock_state.guided_phase == "envision"

    def test_phase_cycle(self, mock_state):
        """Test complete phase cycle."""
        mock_state.guided_mode = True
        mock_state.guided_phase = "envision"

        phases = ["envision", "oracle", "move", "outcome", "envision"]
        for i in range(len(phases) - 1):
            assert mock_state.guided_phase == phases[i]
            advance_phase(mock_state)
        assert mock_state.guided_phase == "envision"  # Back to start
