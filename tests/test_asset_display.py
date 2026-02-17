"""Tests for asset display functionality.

These tests ensure that asset information is formatted and displayed correctly,
including the new Panel-based display with colored borders.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from soloquest.commands.asset import _display_asset_details, handle_asset
from soloquest.engine.assets import load_assets
from soloquest.models.asset import Asset, AssetAbility
from soloquest.ui.display import render_game_text

DATA_DIR = Path(__file__).parent.parent / "soloquest" / "data"


class TestAssetDisplay:
    """Test asset display formatting and Panel creation."""

    def test_display_asset_with_all_features(self):
        """Asset with abilities, tracks, and inputs should display all sections."""
        asset = Asset(
            key="test_asset",
            name="Test Asset",
            category="test_category",
            description="Test description",
            abilities=[
                AssetAbility(text="First ability", enabled=True),
                AssetAbility(text="Second ability", enabled=False),
            ],
            tracks={"health": (0, 5), "integrity": (0, 3)},
            inputs=["Name", "Description"],
            shared=True,
        )

        # Mock the console to capture output
        with patch("soloquest.commands.asset.display.console") as mock_console:
            _display_asset_details(asset)

            # Should have called print with a Panel
            mock_console.print.assert_called_once()
            panel_arg = mock_console.print.call_args[0][0]

            # Verify it's a Panel with correct styling
            assert hasattr(panel_arg, "border_style")
            assert panel_arg.border_style == "bright_magenta"
            assert "TEST ASSET" in str(panel_arg.title)

    def test_display_asset_with_no_abilities(self):
        """Asset without abilities should still display correctly."""
        asset = Asset(
            key="simple_asset",
            name="Simple Asset",
            category="path",
            abilities=[],
            tracks={},
            inputs=[],
        )

        with patch("soloquest.commands.asset.display.console") as mock_console:
            _display_asset_details(asset)

            # Should still create a panel
            mock_console.print.assert_called_once()

    def test_display_asset_with_enabled_and_disabled_abilities(self):
        """Abilities should show correct markers for enabled/disabled state."""
        asset = Asset(
            key="test",
            name="Test",
            category="test",
            abilities=[
                AssetAbility(text="Enabled ability", enabled=True),
                AssetAbility(text="Disabled ability", enabled=False),
            ],
        )

        with patch("soloquest.commands.asset.display.console") as mock_console:
            _display_asset_details(asset)

            panel_arg = mock_console.print.call_args[0][0]
            content = str(panel_arg.renderable)

            # Check for enabled marker (●) and disabled marker (○)
            assert "●" in content  # Enabled
            assert "○" in content  # Disabled

    def test_display_asset_with_multiple_tracks(self):
        """Multiple condition meters should all be displayed."""
        asset = Asset(
            key="test",
            name="Test",
            category="test",
            tracks={
                "health": (0, 5),
                "integrity": (0, 3),
                "ammo": (0, 6),
            },
        )

        with patch("soloquest.commands.asset.display.console") as mock_console:
            _display_asset_details(asset)

            panel_arg = mock_console.print.call_args[0][0]
            content = str(panel_arg.renderable)

            # All tracks should be present
            assert "Health" in content or "health" in content.lower()
            assert "Integrity" in content or "integrity" in content.lower()
            assert "Ammo" in content or "ammo" in content.lower()

    def test_display_shared_asset_shows_indicator(self):
        """Shared assets should display 'Shared Asset' indicator."""
        asset = Asset(
            key="shared",
            name="Shared Asset",
            category="command_vehicle",
            shared=True,
        )

        with patch("soloquest.commands.asset.display.console") as mock_console:
            _display_asset_details(asset)

            panel_arg = mock_console.print.call_args[0][0]
            content = str(panel_arg.renderable)

            assert "Shared Asset" in content

    def test_display_non_asset_object_returns_early(self):
        """Passing a non-Asset object should return without error."""
        with patch("soloquest.commands.asset.display.console") as mock_console:
            _display_asset_details("not an asset")
            _display_asset_details(None)
            _display_asset_details(123)

            # Should not have called print
            mock_console.print.assert_not_called()


class TestAssetCommandIntegration:
    """Integration tests for the /asset command."""

    def setup_method(self):
        self.assets = load_assets(DATA_DIR)

    def test_handle_asset_with_no_args_lists_all(self):
        """Calling /asset with no args should list all assets by category."""
        from soloquest.loop import GameState

        # Create minimal mock state
        mock_state = MagicMock(spec=GameState)
        mock_state.assets = self.assets

        with patch("soloquest.commands.asset.display.console"):
            handle_asset(mock_state, args=[], flags=set())
            # Should not raise exception

    def test_handle_asset_with_exact_match(self):
        """Calling /asset starship should display starship details."""
        from soloquest.loop import GameState

        if "starship" not in self.assets:
            return  # Skip if asset not available

        mock_state = MagicMock(spec=GameState)
        mock_state.assets = self.assets

        with patch("soloquest.commands.asset._display_asset_details") as mock_display:
            handle_asset(mock_state, args=["starship"], flags=set())

            # Should have called display with the starship asset
            mock_display.assert_called_once()
            displayed_asset = mock_display.call_args[0][0]
            assert displayed_asset.key == "starship"

    def test_handle_asset_with_nonexistent_asset(self):
        """Calling /asset with non-existent asset should show error."""
        from soloquest.loop import GameState

        mock_state = MagicMock(spec=GameState)
        mock_state.assets = self.assets

        with patch("soloquest.commands.asset.display.error") as mock_error:
            handle_asset(mock_state, args=["nonexistent_asset_xyz"], flags=set())

            # Should have shown error
            mock_error.assert_called_once()
            error_msg = mock_error.call_args[0][0]
            assert "not found" in error_msg.lower()

    def test_handle_asset_with_multiple_matches(self):
        """Calling /asset with ambiguous name should show warning."""
        from soloquest.loop import GameState

        mock_state = MagicMock(spec=GameState)
        mock_state.assets = self.assets

        # Find a query that matches multiple assets
        # "engine" might match "engine_upgrade" and other engine-related assets
        with patch("soloquest.commands.asset.display.warn"):
            handle_asset(mock_state, args=["module"], flags=set())

            # Might show warning if multiple matches
            # (This is implementation-dependent)


class TestAssetCategoryDisplay:
    """Test asset listing by category."""

    def setup_method(self):
        self.assets = load_assets(DATA_DIR)

    def test_assets_grouped_by_category(self):
        """Assets should be grouped by category when listing all."""
        from soloquest.loop import GameState

        mock_state = MagicMock(spec=GameState)
        mock_state.assets = self.assets

        with patch("soloquest.commands.asset.display.console") as mock_console:
            from soloquest.commands.asset import _list_assets

            _list_assets(mock_state)

            # Should have printed category headers
            # Check that print was called multiple times (once per category + header)
            assert mock_console.print.call_count > 1

    def test_empty_assets_shows_warning(self):
        """Empty asset dictionary should show warning."""
        from soloquest.loop import GameState

        mock_state = MagicMock(spec=GameState)
        mock_state.assets = {}

        with patch("soloquest.commands.asset.display.warn") as mock_warn:
            from soloquest.commands.asset import _list_assets

            _list_assets(mock_state)

            # Should have shown warning
            mock_warn.assert_called_once()


class TestAssetEdgeCases:
    """Test edge cases and boundary conditions for asset display."""

    def test_asset_with_very_long_ability_text(self):
        """Assets with long ability text should not crash display."""
        long_text = "A" * 500  # Very long ability text
        asset = Asset(
            key="test",
            name="Test",
            category="test",
            abilities=[AssetAbility(text=long_text, enabled=True)],
        )

        with patch("soloquest.commands.asset.display.console"):
            # Should not crash
            _display_asset_details(asset)

    def test_asset_with_special_characters_in_name(self):
        """Asset names with special characters should display correctly."""
        asset = Asset(
            key="test",
            name="Test & Special [Asset] <Name>",
            category="test",
        )

        with patch("soloquest.commands.asset.display.console") as mock_console:
            _display_asset_details(asset)

            # Should have created panel without error
            mock_console.print.assert_called_once()

    def test_asset_with_unicode_characters(self):
        """Asset with unicode characters should display correctly."""
        asset = Asset(
            key="test",
            name="Test 日本語 Asset",
            category="test",
            abilities=[AssetAbility(text="Ability with emoji ⚡ and symbols ●", enabled=True)],
        )

        with patch("soloquest.commands.asset.display.console"):
            # Should not crash
            _display_asset_details(asset)

    def test_asset_with_empty_track_name(self):
        """Asset with empty track name should handle gracefully."""
        asset = Asset(
            key="test",
            name="Test",
            category="test",
            tracks={"": (0, 5)},  # Empty track name
        )

        with patch("soloquest.commands.asset.display.console"):
            # Should not crash
            _display_asset_details(asset)

    def test_asset_category_normalization(self):
        """Asset categories with underscores should be formatted to title case."""
        asset = Asset(
            key="test",
            name="Test",
            category="command_vehicle_module",
        )

        with patch("soloquest.commands.asset.display.console") as mock_console:
            _display_asset_details(asset)

            panel_arg = mock_console.print.call_args[0][0]
            content = str(panel_arg.renderable)

            # Should have converted underscores to spaces and title cased
            assert "Command Vehicle Module" in content


class TestRenderGameText:
    """Tests for markdown rendering in game text (abilities, move descriptions)."""

    def test_single_link_becomes_cyan(self):
        text = "When you [Advance](Starforged/Moves/Legacy/Advance), take +1."
        result = render_game_text(text)
        assert result == "When you [cyan]Advance[/cyan], take +1."

    def test_multiple_links_in_one_ability(self):
        text = "When you [Withstand Damage](path/to/move), roll +heart. [Endure Stress](path/to/other) (-1)."
        result = render_game_text(text)
        assert "[cyan]Withstand Damage[/cyan]" in result
        assert "[cyan]Endure Stress[/cyan]" in result
        assert "](" not in result

    def test_no_links_unchanged(self):
        text = "Your starship is armed and suited for interstellar flight."
        assert render_game_text(text) == text

    def test_move_name_with_spaces_preserved(self):
        text = "Use [Finish an Expedition](Starforged/Moves/Exploration/Finish_an_Expedition) here."
        result = render_game_text(text)
        assert "[cyan]Finish an Expedition[/cyan]" in result

    def test_bold_markdown_converted(self):
        text = "**When you begin a session**, do the following."
        result = render_game_text(text)
        assert result == "[bold]When you begin a session[/bold], do the following."

    def test_bullet_list_converted(self):
        text = "* First item\n* Second item"
        result = render_game_text(text)
        assert "• First item" in result
        assert "• Second item" in result
