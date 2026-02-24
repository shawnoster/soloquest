"""Tests for soloquest/commands/wizard_oracle.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soloquest.commands.wizard_oracle import check_oracle_prefix


@pytest.fixture
def mock_state():
    state = MagicMock()
    state.oracles = {}
    state.dice = MagicMock()
    state.character = MagicMock()
    state.session = MagicMock()
    state.sync = MagicMock()
    return state


class TestCheckOraclePrefix:
    def test_plain_input_passthrough(self, mock_state):
        assert check_oracle_prefix("1", mock_state) == "1"
        assert check_oracle_prefix("r", mock_state) == "r"
        assert check_oracle_prefix("", mock_state) == ""
        assert check_oracle_prefix("my custom truth", mock_state) == "my custom truth"

    def test_plain_input_passthrough_no_state(self):
        assert check_oracle_prefix("hello", None) == "hello"
        assert check_oracle_prefix("1", None) == "1"

    def test_bare_question_mark_shows_hint_returns_none(self, mock_state):
        with patch("soloquest.ui.display.info") as mock_info:
            result = check_oracle_prefix("?", mock_state)
        assert result is None
        mock_info.assert_called_once()

    def test_bare_oracle_command_shows_hint(self, mock_state):
        with patch("soloquest.ui.display.info") as mock_info:
            result = check_oracle_prefix("/oracle", mock_state)
        assert result is None
        mock_info.assert_called_once()

    def test_bare_o_alias_shows_hint(self, mock_state):
        with patch("soloquest.ui.display.info") as mock_info:
            result = check_oracle_prefix("/o", mock_state)
        assert result is None
        mock_info.assert_called_once()

    def test_question_prefix_calls_run_inline_oracle(self, mock_state):
        with patch("soloquest.commands.wizard_oracle._run_inline_oracle") as mock_run:
            result = check_oracle_prefix("?action theme", mock_state)
        assert result is None
        mock_run.assert_called_once_with(mock_state, ["action", "theme"])

    def test_oracle_command_prefix_calls_run_inline_oracle(self, mock_state):
        with patch("soloquest.commands.wizard_oracle._run_inline_oracle") as mock_run:
            result = check_oracle_prefix("/oracle action", mock_state)
        assert result is None
        mock_run.assert_called_once_with(mock_state, ["action"])

    def test_o_alias_prefix_calls_run_inline_oracle(self, mock_state):
        with patch("soloquest.commands.wizard_oracle._run_inline_oracle") as mock_run:
            result = check_oracle_prefix("/o action", mock_state)
        assert result is None
        mock_run.assert_called_once_with(mock_state, ["action"])

    def test_none_state_with_oracle_prefix_shows_warning(self):
        with patch("soloquest.ui.display.warn") as mock_warn:
            result = check_oracle_prefix("?action", None)
        assert result is None
        mock_warn.assert_called_once()

    def test_none_state_with_bare_oracle_shows_hint_not_warning(self):
        """Bare ?/oracle with no state still shows usage hint (checked before state guard)."""
        with (
            patch("soloquest.ui.display.info") as mock_info,
            patch("soloquest.ui.display.warn") as mock_warn,
        ):
            result = check_oracle_prefix("?", None)
        assert result is None
        mock_info.assert_called_once()
        mock_warn.assert_not_called()

    def test_case_insensitive_oracle_command(self, mock_state):
        with patch("soloquest.commands.wizard_oracle._run_inline_oracle") as mock_run:
            result = check_oracle_prefix("/Oracle action", mock_state)
        assert result is None
        mock_run.assert_called_once()

    def test_case_insensitive_o_alias(self, mock_state):
        with patch("soloquest.commands.wizard_oracle._run_inline_oracle") as mock_run:
            result = check_oracle_prefix("/O action", mock_state)
        assert result is None
        mock_run.assert_called_once()

    def test_question_with_only_spaces_shows_hint(self, mock_state):
        with patch("soloquest.ui.display.info") as mock_info:
            result = check_oracle_prefix("?  ", mock_state)
        assert result is None
        mock_info.assert_called_once()

    def test_oracle_with_only_spaces_shows_hint(self, mock_state):
        with patch("soloquest.ui.display.info") as mock_info:
            result = check_oracle_prefix("/oracle  ", mock_state)
        assert result is None
        mock_info.assert_called_once()

    def test_multi_table_query(self, mock_state):
        with patch("soloquest.commands.wizard_oracle._run_inline_oracle") as mock_run:
            result = check_oracle_prefix("?action theme descriptor focus", mock_state)
        assert result is None
        mock_run.assert_called_once_with(mock_state, ["action", "theme", "descriptor", "focus"])

    def test_whitespace_stripped_from_input(self, mock_state):
        """Leading/trailing whitespace in raw_input is handled correctly."""
        assert check_oracle_prefix("  hello  ", mock_state) == "  hello  "  # passthrough unchanged

    def test_returns_exact_original_string_on_passthrough(self, mock_state):
        """Passthrough returns the exact original raw_input, not stripped."""
        original = "  some input  "
        assert check_oracle_prefix(original, mock_state) is original
