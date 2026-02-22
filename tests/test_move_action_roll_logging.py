"""Tests for action roll logging to session."""

from unittest.mock import MagicMock, patch

from soloquest.commands.move import _log_move, handle_move
from soloquest.engine.moves import MoveResult, OutcomeTier
from soloquest.models.character import Character, Stats
from soloquest.models.session import Session


class TestLogMove:
    """Tests for _log_move function."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(name="Test", stats=Stats(iron=3, edge=2, heart=1))
        self.state.session = Session(number=1)

    def test_log_move_strong_hit(self):
        """Should log strong hit with correct format."""
        result = MoveResult(
            action_die=5,
            stat=3,
            adds=1,
            action_score=9,
            challenge_1=4,
            challenge_2=7,
            outcome=OutcomeTier.STRONG_HIT,
            match=False,
            burned_momentum=False,
            momentum_used=0,
        )

        _log_move(self.state, "Strike", "iron", 3, result, 4, 7)

        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert entry.kind == "move"
        assert "Strike" in entry.text
        assert "d6(5)" in entry.text
        assert "iron(3)" in entry.text
        assert "adds(1)" in entry.text
        assert "= 9" in entry.text
        assert "[4, 7]" in entry.text
        assert "STRONG HIT" in entry.text
        assert "MATCH" not in entry.text

    def test_log_move_with_match(self):
        """Should log match indicator when challenge dice match."""
        result = MoveResult(
            action_die=2,
            stat=3,
            adds=0,
            action_score=5,
            challenge_1=8,
            challenge_2=8,
            outcome=OutcomeTier.MISS,
            match=True,
            burned_momentum=False,
            momentum_used=0,
        )

        _log_move(self.state, "Face Danger", "wits", 3, result, 8, 8)

        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert "MISS" in entry.text
        assert "⚡MATCH" in entry.text
        assert "[8, 8]" in entry.text

    def test_log_move_weak_hit(self):
        """Should log weak hit with correct format."""
        result = MoveResult(
            action_die=4,
            stat=2,
            adds=0,
            action_score=6,
            challenge_1=5,
            challenge_2=9,
            outcome=OutcomeTier.WEAK_HIT,
            match=False,
            burned_momentum=False,
            momentum_used=0,
        )

        _log_move(self.state, "Secure an Advantage", "edge", 2, result, 5, 9)

        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert entry.kind == "move"
        assert "Secure an Advantage" in entry.text
        assert "WEAK HIT" in entry.text

    def test_log_move_with_burned_momentum(self):
        """Should log momentum burn instead of dice roll."""
        result = MoveResult(
            action_die=2,
            stat=3,
            adds=0,
            action_score=5,
            challenge_1=4,
            challenge_2=7,
            outcome=OutcomeTier.STRONG_HIT,
            match=False,
            burned_momentum=True,
            momentum_used=6,
        )

        _log_move(self.state, "Compel", "heart", 1, result, 4, 7)

        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert "momentum(+6)" in entry.text
        assert "d6" not in entry.text  # Should not show action die when burning momentum

    def test_log_move_no_adds(self):
        """Should not include adds in log when adds is 0."""
        result = MoveResult(
            action_die=6,
            stat=3,
            adds=0,
            action_score=9,
            challenge_1=5,
            challenge_2=7,
            outcome=OutcomeTier.STRONG_HIT,
            match=False,
            burned_momentum=False,
            momentum_used=0,
        )

        _log_move(self.state, "Clash", "iron", 3, result, 5, 7)

        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert "adds" not in entry.text
        assert "d6(6)+iron(3)" in entry.text or "d6(6)" in entry.text and "iron(3)" in entry.text



