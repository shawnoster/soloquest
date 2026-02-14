"""Tests for the /roll command."""

from __future__ import annotations

import pytest

from soloquest.commands.roll import DICE_PATTERN


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
