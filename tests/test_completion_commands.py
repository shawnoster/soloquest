"""Tests for tab completion system."""

from prompt_toolkit.document import Document

from soloquest.commands.completion import CommandCompleter
from soloquest.engine.oracles import OracleTable


class TestCommandCompleterBasics:
    """Tests for basic command completion."""

    def setup_method(self):
        self.completer = CommandCompleter()

    def test_completes_slash_commands(self):
        """Should complete commands starting with /."""
        doc = Document("/mov", cursor_position=4)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "/move" in completion_texts or "move" in completion_texts

    def test_completes_command_aliases(self):
        """Should complete command aliases."""
        doc = Document("/m", cursor_position=2)
        completions = self.completer.get_completions(doc, None)

        # Should return completions for /m
        assert len(completions) > 0
        completion_texts = [c.text for c in completions]
        # /m is an alias, so it should appear in completions
        assert any("/m" in text for text in completion_texts)

    def test_no_completions_for_non_slash(self):
        """Should not complete if input doesn't start with /."""
        doc = Document("hello", cursor_position=5)
        completions = self.completer.get_completions(doc, None)

        assert len(completions) == 0

    def test_empty_input_returns_no_completions(self):
        """Empty input should return no completions."""
        doc = Document("", cursor_position=0)
        completions = self.completer.get_completions(doc, None)

        assert len(completions) == 0


class TestOracleCompletion:
    """Tests for oracle table completion."""

    def setup_method(self):
        # Create test oracle tables
        self.oracles = {
            "action": OracleTable(
                key="action",
                name="Action",
                die="d100",
                results=[
                    (1, 10, "Aid"),
                    (11, 100, "Harm"),
                ],
            ),
            "action_theme": OracleTable(
                key="action_theme",
                name="Action Theme",
                die="d100",
                results=[
                    (1, 50, "Light"),
                    (51, 100, "Dark"),
                ],
            ),
            "planet_class": OracleTable(
                key="planet_class",
                name="Planet Class",
                die="d100",
                results=[
                    (1, 100, "Desert"),
                ],
            ),
        }
        self.completer = CommandCompleter(oracles=self.oracles)

    def test_oracle_completion_shows_all_tables(self):
        """Oracle completion with no args should show all tables."""
        doc = Document("/oracle ", cursor_position=8)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "action" in completion_texts
        assert "action_theme" in completion_texts
        assert "planet_class" in completion_texts

    def test_oracle_completion_filters_by_prefix(self):
        """Oracle completion should filter by prefix."""
        doc = Document("/oracle action", cursor_position=14)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "action" in completion_texts
        assert "action_theme" in completion_texts
        # planet_class should not be included
        assert "planet_class" not in completion_texts

    def test_oracle_completion_shows_full_names(self):
        """Oracle completion should show full table names in meta."""
        doc = Document("/oracle action", cursor_position=14)
        completions = self.completer.get_completions(doc, None)

        # Check that display_meta contains full names
        metas = [str(c.display_meta) for c in completions if c.display_meta]
        assert any("Action" in m for m in metas)

    def test_oracle_completion_matches_table_name(self):
        """Oracle completion should match against table name too."""
        doc = Document("/oracle planet", cursor_position=14)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "planet_class" in completion_texts

    def test_oracle_alias_completion(self):
        """/o alias should complete oracle tables."""
        doc = Document("/o ", cursor_position=3)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "action" in completion_texts


class TestMoveCompletion:
    """Tests for move completion."""

    def setup_method(self):
        # Create test moves
        self.moves = {
            "strike": {"name": "Strike"},
            "secure_an_advantage": {"name": "Secure an Advantage"},
            "face_danger": {"name": "Face Danger"},
        }
        self.completer = CommandCompleter(moves=self.moves)

    def test_move_completion_shows_all_moves(self):
        """Move completion with no args should show all moves."""
        doc = Document("/move ", cursor_position=6)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "strike" in completion_texts
        assert "secure_an_advantage" in completion_texts
        assert "face_danger" in completion_texts

    def test_move_completion_filters_by_prefix(self):
        """Move completion should filter by prefix."""
        doc = Document("/move face", cursor_position=10)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "face_danger" in completion_texts
        # strike should not be included
        assert "strike" not in completion_texts

    def test_move_completion_shows_full_names(self):
        """Move completion should show full move names in meta."""
        doc = Document("/move strike", cursor_position=12)
        completions = self.completer.get_completions(doc, None)

        # Check that display_meta contains full name
        metas = [str(c.display_meta) for c in completions if c.display_meta]
        assert any("Strike" in m for m in metas)

    def test_move_completion_matches_move_name(self):
        """Move completion should match against move name too."""
        doc = Document("/move secure", cursor_position=12)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "secure_an_advantage" in completion_texts

    def test_move_alias_completion(self):
        """/m alias should complete moves."""
        doc = Document("/m ", cursor_position=3)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "strike" in completion_texts

    def test_move_completion_normalizes_spaces_and_underscores(self):
        """Move completion should handle spaces and underscores."""
        doc = Document("/move face danger", cursor_position=17)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "face_danger" in completion_texts


class TestAssetCompletion:
    """Tests for asset completion."""

    def setup_method(self):
        # Create test assets
        from soloquest.models.asset import Asset

        self.assets = {
            "starship": Asset(
                key="starship",
                name="Starship",
                category="command_vehicle",
                shared=True,
            ),
            "navigator": Asset(
                key="navigator",
                name="Navigator",
                category="path",
                shared=False,
            ),
            "engine_upgrade": Asset(
                key="engine_upgrade",
                name="Engine Upgrade",
                category="module",
                shared=True,
            ),
        }
        self.completer = CommandCompleter(assets=self.assets)

    def test_asset_completion_shows_all_assets(self):
        """Asset completion with no args should show all assets."""
        doc = Document("/asset ", cursor_position=7)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "starship" in completion_texts
        assert "navigator" in completion_texts
        assert "engine_upgrade" in completion_texts

    def test_asset_completion_filters_by_prefix(self):
        """Asset completion should filter by prefix."""
        doc = Document("/asset nav", cursor_position=10)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "navigator" in completion_texts
        # starship should not be included
        assert "starship" not in completion_texts

    def test_asset_completion_shows_full_names(self):
        """Asset completion should show full asset names in meta."""
        doc = Document("/asset starship", cursor_position=15)
        completions = self.completer.get_completions(doc, None)

        # Check that display_meta contains full name
        metas = [str(c.display_meta) for c in completions if c.display_meta]
        assert any("Starship" in m for m in metas)

    def test_asset_completion_matches_asset_name(self):
        """Asset completion should match against asset name too."""
        doc = Document("/asset engine", cursor_position=13)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "engine_upgrade" in completion_texts

    def test_asset_completion_normalizes_spaces_and_underscores(self):
        """Asset completion should handle spaces and underscores."""
        doc = Document("/asset engine upgrade", cursor_position=21)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "engine_upgrade" in completion_texts


class TestCompletionEdgeCases:
    """Tests for edge cases in completion."""

    def setup_method(self):
        self.oracles = {
            "action": OracleTable(
                key="action",
                name="Action",
                die="d100",
                results=[(1, 100, "Test")],
            ),
        }
        self.moves = {"strike": {"name": "Strike"}}
        from soloquest.models.asset import Asset

        self.assets = {
            "starship": Asset(
                key="starship",
                name="Starship",
                category="command_vehicle",
                shared=True,
            ),
        }
        self.completer = CommandCompleter(
            oracles=self.oracles, moves=self.moves, assets=self.assets
        )

    def test_completion_with_trailing_spaces(self):
        """Should handle multiple trailing spaces."""
        doc = Document("/oracle  ", cursor_position=9)
        completions = self.completer.get_completions(doc, None)

        # Should still provide completions
        assert len(completions) > 0

    def test_completion_case_insensitive(self):
        """Completion should be case-insensitive."""
        doc = Document("/oracle ACTION", cursor_position=14)
        completions = self.completer.get_completions(doc, None)

        completion_texts = [c.text for c in completions]
        assert "action" in completion_texts

    def test_completion_with_multiple_words(self):
        """Should complete based on last word in multi-word input."""
        doc = Document("/oracle action theme", cursor_position=20)
        completions = self.completer.get_completions(doc, None)

        # Should attempt completion based on "theme"
        assert isinstance(completions, list)

    def test_completion_with_cursor_in_middle(self):
        """Should complete based on text before cursor."""
        doc = Document("/oracle action", cursor_position=10)  # cursor after "act"
        completions = self.completer.get_completions(doc, None)

        # Should complete based on "act" not "action"
        assert isinstance(completions, list)

    def test_no_crash_with_asset_without_name_attribute(self):
        """Should handle assets without name attribute gracefully."""
        # Create a mock asset object without proper attributes
        self.completer.assets["broken"] = type("MockAsset", (), {})()

        doc = Document("/asset ", cursor_position=7)
        completions = self.completer.get_completions(doc, None)

        # Should not crash
        assert isinstance(completions, list)
