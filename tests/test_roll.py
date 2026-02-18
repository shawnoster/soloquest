"""Tests for the /roll command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soloquest.commands.roll import DICE_PATTERN, handle_roll
from soloquest.models.session import Session


class TestDicePattern:
    """Test the dice expression regex parser."""

    def test_simple_d6(self):
        m = DICE_PATTERN.match("d6")
        assert m is not None
        assert m.group(1) == ""
        assert m.group(2) == "6"

    def test_1d6(self):
        m = DICE_PATTERN.match("1d6")
        assert m is not None
        assert m.group(1) == "1"
        assert m.group(2) == "6"

    def test_2d10(self):
        m = DICE_PATTERN.match("2d10")
        assert m is not None
        assert m.group(1) == "2"
        assert m.group(2) == "10"

    def test_d100(self):
        m = DICE_PATTERN.match("d100")
        assert m is not None
        assert m.group(2) == "100"

    def test_uppercase_D(self):
        m = DICE_PATTERN.match("D6")
        assert m is not None

    def test_invalid_no_d(self):
        assert DICE_PATTERN.match("6") is None

    def test_invalid_empty(self):
        assert DICE_PATTERN.match("") is None

    def test_invalid_text(self):
        assert DICE_PATTERN.match("dice") is None

    def test_3d6(self):
        m = DICE_PATTERN.match("3d6")
        assert m is not None
        assert m.group(1) == "3"
        assert m.group(2) == "6"


class TestRollCounts:
    """Test that parsed counts and sides are within valid ranges."""

    @pytest.mark.parametrize(
        "expr,count,sides",
        [
            ("d6", 1, 6),
            ("2d10", 2, 10),
            ("d100", 1, 100),
            ("4d6", 4, 6),
            ("20d6", 20, 6),
        ],
    )
    def test_parsed_values(self, expr, count, sides):
        m = DICE_PATTERN.match(expr)
        assert m is not None
        parsed_count = int(m.group(1)) if m.group(1) else 1
        parsed_sides = int(m.group(2))
        assert parsed_count == count
        assert parsed_sides == sides


class TestHandleRollNote:
    """Test the optional trailing note on /roll."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.dice = MagicMock()
        self.state.dice.roll.return_value = 42
        self.state.session = Session(number=1)

    @patch("soloquest.commands.roll.display.console")
    def test_note_displayed_before_result(self, mock_console):
        """Note is shown with a │ pipe above the └ result line."""
        handle_roll(self.state, ["d100", "inciting", "incident"], flags=set())

        calls = [c[0][0] for c in mock_console.print.call_args_list]
        assert any("inciting incident" in c for c in calls)
        assert any("│" in c for c in calls)
        # Note line (│) comes before the result line (└)
        note_idx = next(i for i, c in enumerate(calls) if "│" in c)
        result_idx = next(i for i, c in enumerate(calls) if "🎲" in c)
        assert note_idx < result_idx

    @patch("soloquest.commands.roll.display.console")
    def test_note_appended_to_session_log(self, mock_console):
        """Note is appended to session log entry with ' — ' separator."""
        handle_roll(self.state, ["d100", "inciting", "incident"], flags=set())

        assert len(self.state.session.entries) == 1
        assert "inciting incident" in self.state.session.entries[0].text
        assert " — " in self.state.session.entries[0].text

    @patch("soloquest.commands.roll.display.console")
    def test_no_note_no_dim_italic_line(self, mock_console):
        """With no trailing note, no extra dim italic line is printed."""
        handle_roll(self.state, ["d6"], flags=set())

        calls = [c[0][0] for c in mock_console.print.call_args_list]
        assert not any("dim italic" in c for c in calls)

    @patch("soloquest.commands.roll.display.console")
    def test_no_note_log_has_no_separator(self, mock_console):
        """With no note, session log entry has no ' — ' separator."""
        handle_roll(self.state, ["d6"], flags=set())

        assert " — " not in self.state.session.entries[0].text

    @patch("soloquest.commands.roll.display.console")
    def test_multiword_note(self, mock_console):
        """Multi-word notes are joined with spaces."""
        handle_roll(self.state, ["d6", "what", "caused", "the", "fire"], flags=set())

        log_text = self.state.session.entries[0].text
        assert "what caused the fire" in log_text
