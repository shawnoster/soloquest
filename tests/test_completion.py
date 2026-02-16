"""Tests for command tab completion."""

from __future__ import annotations

from prompt_toolkit.document import Document

from soloquest.commands.completion import CommandCompleter
from soloquest.engine.oracles import OracleTable


class TestCommandCompleter:
    def test_completes_move_command(self):
        completer = CommandCompleter()
        doc = Document("/mov", cursor_position=4)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) == 1
        assert completions[0].text == "/move"

    def test_completes_alias(self):
        completer = CommandCompleter()
        doc = Document("/m", cursor_position=2)
        completions = list(completer.get_completions(doc, None))

        # Should match /m (alias for move) and /move and /momentum
        assert len(completions) == 3
        commands = {c.text for c in completions}
        assert "/m" in commands
        assert "/move" in commands
        assert "/momentum" in commands

    def test_shows_meta_for_commands(self):
        completer = CommandCompleter()
        doc = Document("/help", cursor_position=5)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) == 1
        assert completions[0].text == "/help"
        # display_meta is a FormattedText, check if it contains the string
        assert "show help" in str(completions[0].display_meta)

    def test_shows_alias_meta(self):
        completer = CommandCompleter()
        doc = Document("/h", cursor_position=2)
        completions = list(completer.get_completions(doc, None))

        # Find /h completion
        h_completion = [c for c in completions if c.text == "/h"][0]
        # display_meta is a FormattedText, check if it contains the string
        assert "alias for /help" in str(h_completion.display_meta)

    def test_no_completions_without_slash(self):
        completer = CommandCompleter()
        doc = Document("move", cursor_position=4)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) == 0

    def test_no_completions_after_space(self):
        completer = CommandCompleter()
        doc = Document("/move face", cursor_position=10)
        completions = list(completer.get_completions(doc, None))

        # Don't complete arguments, only the command itself
        assert len(completions) == 0

    def test_completes_all_commands_with_slash_only(self):
        completer = CommandCompleter()
        doc = Document("/", cursor_position=1)
        completions = list(completer.get_completions(doc, None))

        # Should get all commands + aliases
        assert len(completions) > 15  # At least 15 commands available

    def test_case_insensitive_completion(self):
        completer = CommandCompleter()
        doc = Document("/MOV", cursor_position=4)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) == 1
        assert completions[0].text == "/move"

    def test_completion_replaces_entire_slash_command(self):
        """Regression test: ensure completion replaces the full /cmd, not just cmd."""
        completer = CommandCompleter()
        # Simulate typing "/or" and tab-completing to "/oracle"
        doc = Document("/or", cursor_position=3)
        completions = list(completer.get_completions(doc, None))

        # Find the /oracle completion (if it exists)
        oracle_completions = [c for c in completions if c.text == "/oracle"]
        if oracle_completions:
            completion = oracle_completions[0]
            # start_position should be -3 to replace all of "/or"
            # This prevents the double-slash bug (//oracle)
            assert completion.start_position == -3

    def test_completions_are_alphabetically_sorted(self):
        """Test that command completions are returned in alphabetical order."""
        completer = CommandCompleter()
        doc = Document("/", cursor_position=1)
        completions = list(completer.get_completions(doc, None))

        # Extract completion texts
        completion_texts = [c.text for c in completions]

        # Verify they are sorted
        assert completion_texts == sorted(completion_texts)


class TestOracleTableCompletion:
    def test_completes_oracle_table_names(self):
        # Create mock oracle tables
        oracles = {
            "action": OracleTable(
                key="action",
                name="Action",
                die="d100",
                results=[(1, 100, "Test")],
            ),
            "theme": OracleTable(
                key="theme",
                name="Theme",
                die="d100",
                results=[(1, 100, "Test")],
            ),
        }
        completer = CommandCompleter(oracles=oracles)
        doc = Document("/oracle act", cursor_position=11)
        completions = list(completer.get_completions(doc, None))

        # Should match "action"
        assert len(completions) >= 1
        action_completions = [c for c in completions if c.text == "action"]
        assert len(action_completions) == 1
        # display_meta is a FormattedText, check if it contains the string
        assert "Action" in str(action_completions[0].display_meta)

    def test_completes_with_alias(self):
        oracles = {
            "pay_the_price": OracleTable(
                key="pay_the_price",
                name="Pay the Price",
                die="d100",
                results=[(1, 100, "Test")],
            ),
        }
        completer = CommandCompleter(oracles=oracles)
        # Using /o alias for /oracle
        doc = Document("/o pay", cursor_position=6)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) >= 1
        pay_completions = [c for c in completions if c.text == "pay_the_price"]
        assert len(pay_completions) == 1

    def test_no_oracle_completion_for_other_commands(self):
        oracles = {
            "action": OracleTable(
                key="action",
                name="Action",
                die="d100",
                results=[(1, 100, "Test")],
            ),
        }
        completer = CommandCompleter(oracles=oracles)
        # /move should not complete oracle tables
        doc = Document("/move act", cursor_position=9)
        completions = list(completer.get_completions(doc, None))

        # Should not get any completions for oracle tables after /move
        assert len(completions) == 0

    def test_oracle_completion_with_space_after_command(self):
        oracles = {
            "action": OracleTable(
                key="action",
                name="Action",
                die="d100",
                results=[(1, 100, "Test")],
            ),
        }
        completer = CommandCompleter(oracles=oracles)
        # Space after /oracle, cursor ready for table name
        doc = Document("/oracle ", cursor_position=8)
        completions = list(completer.get_completions(doc, None))

        # Should show all oracle tables
        assert len(completions) >= 1
        action_completions = [c for c in completions if c.text == "action"]
        assert len(action_completions) == 1

    def test_oracle_completion_matches_by_name(self):
        oracles = {
            "pay_the_price": OracleTable(
                key="pay_the_price",
                name="Pay the Price",
                die="d100",
                results=[(1, 100, "Test")],
            ),
        }
        completer = CommandCompleter(oracles=oracles)
        # Search by part of the display name
        doc = Document("/oracle price", cursor_position=13)
        completions = list(completer.get_completions(doc, None))

        # Should match because "price" is in "Pay the Price"
        assert len(completions) >= 1
        pay_completions = [c for c in completions if c.text == "pay_the_price"]
        assert len(pay_completions) == 1

    def test_oracle_completions_are_sorted(self):
        """Test that oracle table completions are returned in alphabetical order."""
        oracles = {
            "theme": OracleTable(
                key="theme",
                name="Theme",
                die="d100",
                results=[(1, 100, "Test")],
            ),
            "action": OracleTable(
                key="action",
                name="Action",
                die="d100",
                results=[(1, 100, "Test")],
            ),
            "descriptor": OracleTable(
                key="descriptor",
                name="Descriptor",
                die="d100",
                results=[(1, 100, "Test")],
            ),
        }
        completer = CommandCompleter(oracles=oracles)
        doc = Document("/oracle ", cursor_position=8)
        completions = list(completer.get_completions(doc, None))

        # Extract completion texts
        completion_texts = [c.text for c in completions]

        # Verify they are sorted
        assert completion_texts == sorted(completion_texts)
        # Verify order: action, descriptor, theme
        assert completion_texts == ["action", "descriptor", "theme"]


class TestMoveCompletion:
    def test_completes_move_names(self):
        # Create mock moves
        moves = {
            "face_danger": {
                "name": "Face Danger",
                "category": "adventure",
            },
            "strike": {
                "name": "Strike",
                "category": "combat",
            },
        }
        completer = CommandCompleter(moves=moves)
        doc = Document("/move face", cursor_position=10)
        completions = list(completer.get_completions(doc, None))

        # Should match "face_danger"
        assert len(completions) >= 1
        face_completions = [c for c in completions if c.text == "face_danger"]
        assert len(face_completions) == 1
        # display_meta is a FormattedText, check if it contains the string
        assert "Face Danger" in str(face_completions[0].display_meta)

    def test_completes_move_with_alias(self):
        moves = {
            "secure_an_advantage": {
                "name": "Secure an Advantage",
                "category": "adventure",
            },
        }
        completer = CommandCompleter(moves=moves)
        # Using /m alias for /move
        doc = Document("/m secure", cursor_position=9)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) >= 1
        secure_completions = [c for c in completions if c.text == "secure_an_advantage"]
        assert len(secure_completions) == 1

    def test_move_completion_normalizes_spaces(self):
        moves = {
            "face_danger": {
                "name": "Face Danger",
                "category": "adventure",
            },
        }
        completer = CommandCompleter(moves=moves)
        # Search with spaces instead of underscores
        doc = Document("/move face danger", cursor_position=17)
        completions = list(completer.get_completions(doc, None))

        # Should still match because normalization handles spaces/underscores
        assert len(completions) >= 1
        face_completions = [c for c in completions if c.text == "face_danger"]
        assert len(face_completions) == 1

    def test_move_completion_matches_by_display_name(self):
        moves = {
            "strike": {
                "name": "Strike",
                "category": "combat",
            },
        }
        completer = CommandCompleter(moves=moves)
        # Search by display name
        doc = Document("/move strike", cursor_position=12)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) >= 1
        strike_completions = [c for c in completions if c.text == "strike"]
        assert len(strike_completions) == 1

    def test_move_completion_with_space_after_command(self):
        moves = {
            "face_danger": {
                "name": "Face Danger",
                "category": "adventure",
            },
        }
        completer = CommandCompleter(moves=moves)
        # Space after /move, cursor ready for move name
        doc = Document("/move ", cursor_position=6)
        completions = list(completer.get_completions(doc, None))

        # Should show all moves
        assert len(completions) >= 1
        face_completions = [c for c in completions if c.text == "face_danger"]
        assert len(face_completions) == 1

    def test_no_move_completion_for_other_commands(self):
        moves = {
            "strike": {
                "name": "Strike",
                "category": "combat",
            },
        }
        completer = CommandCompleter(moves=moves)
        # /oracle should not complete move names
        doc = Document("/oracle strike", cursor_position=14)
        completions = list(completer.get_completions(doc, None))

        # Should not get move completions for /oracle
        assert len(completions) == 0

    def test_move_completions_are_sorted(self):
        """Test that move completions are returned in alphabetical order."""
        moves = {
            "strike": {
                "name": "Strike",
                "category": "combat",
            },
            "face_danger": {
                "name": "Face Danger",
                "category": "adventure",
            },
            "aid_your_ally": {
                "name": "Aid Your Ally",
                "category": "adventure",
            },
        }
        completer = CommandCompleter(moves=moves)
        doc = Document("/move ", cursor_position=6)
        completions = list(completer.get_completions(doc, None))

        # Extract completion texts
        completion_texts = [c.text for c in completions]

        # Verify they are sorted
        assert completion_texts == sorted(completion_texts)
        # Verify order: aid_your_ally, face_danger, strike
        assert completion_texts == ["aid_your_ally", "face_danger", "strike"]


class TestAssetCompletion:
    class MockAsset:
        """Simple mock asset for testing."""

        def __init__(self, name: str):
            self.name = name

    def test_completes_asset_names(self):
        assets = {
            "sword": self.MockAsset("Sword"),
            "shield": self.MockAsset("Shield"),
        }
        completer = CommandCompleter(assets=assets)
        doc = Document("/asset sw", cursor_position=9)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) >= 1
        sword_completions = [c for c in completions if c.text == "sword"]
        assert len(sword_completions) == 1

    def test_asset_completion_matches_by_display_name(self):
        assets = {
            "battle_scarred": self.MockAsset("Battle-Scarred"),
        }
        completer = CommandCompleter(assets=assets)
        # Search by display name
        doc = Document("/asset battle", cursor_position=13)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) >= 1
        battle_completions = [c for c in completions if c.text == "battle_scarred"]
        assert len(battle_completions) == 1

    def test_asset_completion_with_space_after_command(self):
        assets = {
            "sword": self.MockAsset("Sword"),
        }
        completer = CommandCompleter(assets=assets)
        # Space after /asset, cursor ready for asset name
        doc = Document("/asset ", cursor_position=7)
        completions = list(completer.get_completions(doc, None))

        # Should show all assets
        assert len(completions) >= 1
        sword_completions = [c for c in completions if c.text == "sword"]
        assert len(sword_completions) == 1

    def test_no_asset_completion_for_other_commands(self):
        assets = {
            "sword": self.MockAsset("Sword"),
        }
        completer = CommandCompleter(assets=assets)
        # /oracle should not complete asset names
        doc = Document("/oracle sword", cursor_position=13)
        completions = list(completer.get_completions(doc, None))

        # Should not get asset completions for /oracle
        assert len(completions) == 0

    def test_asset_completions_are_sorted(self):
        """Test that asset completions are returned in alphabetical order."""
        assets = {
            "sword": self.MockAsset("Sword"),
            "bow": self.MockAsset("Bow"),
            "shield": self.MockAsset("Shield"),
            "armor": self.MockAsset("Armor"),
        }
        completer = CommandCompleter(assets=assets)
        doc = Document("/asset ", cursor_position=7)
        completions = list(completer.get_completions(doc, None))

        # Extract completion texts
        completion_texts = [c.text for c in completions]

        # Verify they are sorted
        assert completion_texts == sorted(completion_texts)
        # Verify order: armor, bow, shield, sword
        assert completion_texts == ["armor", "bow", "shield", "sword"]
