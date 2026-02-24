"""Tests for command registry — parsing and command matching."""

from wyrd.commands.registry import (
    COMMAND_ALIASES,
    fuzzy_match_command,
    parse_command,
)


class TestParseCommand:
    """Tests for parse_command function."""

    def test_basic_command_parses(self):
        """Basic /command should parse correctly."""
        result = parse_command("/move strike")
        assert result is not None
        assert result.name == "move"
        assert result.args == ["strike"]
        assert result.flags == set()
        assert result.raw == "/move strike"

    def test_alias_resolution(self):
        """Short aliases should resolve to full command names."""
        result = parse_command("/m strike")
        assert result is not None
        assert result.name == "move"

    def test_all_aliases_resolve(self):
        """All defined aliases should resolve correctly."""
        for alias, expected in COMMAND_ALIASES.items():
            result = parse_command(f"/{alias} test")
            assert result is not None, f"Alias {alias} failed to parse"
            assert result.name == expected, (
                f"Alias {alias} resolved to {result.name}, expected {expected}"
            )

    def test_flags_extracted(self):
        """Flags (--flag) should be extracted from args."""
        result = parse_command("/move strike --burn")
        assert result is not None
        assert result.args == ["strike"]
        assert result.flags == {"burn"}

    def test_multiple_flags(self):
        """Multiple flags should all be extracted."""
        result = parse_command("/move strike --burn --verbose")
        assert result.flags == {"burn", "verbose"}

    def test_flag_case_insensitive(self):
        """Flag names should be lowercased."""
        result = parse_command("/move strike --BURN")
        assert "burn" in result.flags

    def test_quoted_args_preserved(self):
        """Quoted arguments should preserve spaces."""
        result = parse_command("/move 'arg with space'")
        assert result is not None
        assert result.args == ["arg with space"]

    def test_double_quoted_args(self):
        """Double quoted arguments should also work."""
        result = parse_command('/move "arg with space"')
        assert result is not None
        assert result.args == ["arg with space"]

    def test_mixed_quotes(self):
        """Mixed quoted and unquoted args should work."""
        result = parse_command("/move 'first' second")
        assert result.args == ["first", "second"]

    def test_no_command_after_slash(self):
        """Just "/" should return None."""
        result = parse_command("/")
        assert result is None

    def test_empty_string(self):
        """Empty string should return None."""
        result = parse_command("")
        assert result is None

    def test_non_command_returns_none(self):
        """Non-command (no leading slash) should return None."""
        result = parse_command("move strike")
        assert result is None

    def test_command_name_lowercased(self):
        """Command name should be lowercased."""
        result = parse_command("/MOVE strike")
        assert result is not None
        assert result.name == "move"

    def test_whitespace_handling(self):
        """Extra whitespace should be handled."""
        result = parse_command("  /move   strike  ")
        assert result is not None
        assert result.name == "move"
        assert result.args == ["strike"]

    def test_flags_mixed_with_args(self):
        """Flags and regular args should be separated correctly."""
        result = parse_command("/move first --burn second")
        assert result.args == ["first", "second"]
        assert result.flags == {"burn"}

    def test_flag_without_value(self):
        """Flag with no following value stays in flags."""
        result = parse_command("/move --burn")
        assert result.args == []
        assert result.flags == {"burn"}


class TestFuzzyMatchCommand:
    """Tests for fuzzy_match_command function."""

    def test_exact_match_returns_name(self):
        """Exact match should return the command name."""
        known = ["move", "oracle", "vow"]
        result = fuzzy_match_command("move", known)
        assert result == "move"

    def test_prefix_match_returns_match(self):
        """Prefix match should return the matching command."""
        known = ["move", "oracle", "vow"]
        result = fuzzy_match_command("mov", known)
        assert result == "move"

    def test_ambiguous_prefix_returns_none(self):
        """Multiple prefix matches should return None."""
        known = ["vow", "vow_progress", "view"]
        result = fuzzy_match_command("v", known)
        assert result is None

    def test_no_match_returns_none(self):
        """No match should return None."""
        known = ["move", "oracle", "vow"]
        result = fuzzy_match_command("xyz", known)
        assert result is None

    def test_case_insensitive(self):
        """Matching should be case insensitive."""
        known = ["move", "oracle", "vow"]
        result = fuzzy_match_command("MOVE", known)
        assert result == "move"

    def test_case_insensitive_prefix(self):
        """Query is lowercased before prefix matching against known list."""
        known = ["move", "oracle", "vow"]
        result = fuzzy_match_command("MOV", known)
        assert result == "move"

    def test_empty_known_list(self):
        """Empty known list should return None."""
        result = fuzzy_match_command("move", [])
        assert result is None
