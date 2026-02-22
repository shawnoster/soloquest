"""Tests for string resource loader."""

from __future__ import annotations

import pytest

from soloquest.ui.strings import get_string, get_strings_section


class TestGetString:
    """Test get_string function."""

    def test_simple_key(self):
        result = get_string("display.splash_title")
        assert result == "SOLOQUEST"

    def test_nested_key(self):
        result = get_string("character_creation.wizard_steps.step1_title")
        assert result == "Step 1 — Choose 2 Paths"

    def test_with_formatting(self):
        result = get_string("oracle.not_found", query="action")
        assert result == "Oracle table not found: 'action'"

    def test_with_multiple_format_vars(self):
        result = get_string("character_creation.errors.path_invalid", path="invalid")
        assert result == "'invalid' is not a valid path. Try TAB for options."

    def test_invalid_key_raises_key_error(self):
        with pytest.raises(KeyError):
            get_string("nonexistent.key")

    def test_non_string_value_raises_value_error(self):
        # Trying to get a section as a string should fail
        with pytest.raises(ValueError):
            get_string("oracle")


class TestGetStringsSection:
    """Test get_strings_section function."""

    def test_get_section(self):
        section = get_strings_section("oracle")
        assert isinstance(section, dict)
        assert "panel_title" in section
        assert "not_found" in section

    def test_get_nested_section(self):
        section = get_strings_section("character_creation.wizard_steps")
        assert isinstance(section, dict)
        assert "step1_title" in section
        assert "step2_title" in section

    def test_invalid_section_raises_key_error(self):
        with pytest.raises(KeyError):
            get_strings_section("nonexistent.section")


class TestStringContent:
    """Test that actual string content matches expected format."""

    def test_character_creation_steps_complete(self):
        steps = get_strings_section("character_creation.wizard_steps")
        # Should have all 10 steps plus dice mode
        assert len(steps) == 11
        assert "step1_title" in steps
        assert "step10_title" in steps
        assert "dice_mode_title" in steps

    def test_dice_mode_options_complete(self):
        options = get_strings_section("character_creation.dice_modes")
        assert len(options) == 3
        assert "option1" in options
        assert "option2" in options
        assert "option3" in options

    def test_character_creation_errors_complete(self):
        errors = get_strings_section("character_creation.errors")
        assert "path_empty" in errors
        assert "path_invalid" in errors
        assert "asset_empty" in errors
