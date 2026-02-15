"""Regression tests for fuzzy matching improvements.

These tests ensure that fuzzy matching prioritizes:
1. Exact matches first
2. Prefix matches second
3. Substring matches last
"""

from pathlib import Path

from soloquest.commands.move import fuzzy_match_move
from soloquest.engine.assets import fuzzy_match_asset, load_assets
from soloquest.engine.oracles import fuzzy_match_oracle, load_oracles
from soloquest.loop import load_move_data

DATA_DIR = Path(__file__).parent.parent / "soloquest" / "data"


class TestAssetFuzzyMatching:
    """Regression tests for asset fuzzy matching prioritization."""

    def setup_method(self):
        self.assets = load_assets(DATA_DIR)

    def test_exact_match_takes_priority_over_substring(self):
        """Regression: /asset seer should return only Seer, not Overseer."""
        matches = fuzzy_match_asset("seer", self.assets)
        assert len(matches) == 1
        assert matches[0].name == "Seer"

    def test_exact_match_overseer(self):
        """Exact match for overseer should return only Overseer."""
        matches = fuzzy_match_asset("overseer", self.assets)
        assert len(matches) == 1
        assert matches[0].name == "Overseer"

    def test_prefix_match_takes_priority_over_substring(self):
        """Prefix matches should come before substring matches."""
        # Find an asset that could match as both prefix and substring
        # For example, if there's "Navigator" and "Lore Navigator"
        matches = fuzzy_match_asset("nav", self.assets)
        if matches:
            # Navigator should come before any asset containing "nav" in the middle
            first_match = matches[0]
            assert first_match.key.startswith("nav") or first_match.name.lower().startswith("nav")

    def test_empty_query_returns_no_matches(self):
        """Empty query should return no matches."""
        matches = fuzzy_match_asset("", self.assets)
        assert len(matches) == 0

    def test_nonexistent_asset_returns_empty(self):
        """Non-existent asset should return empty list."""
        matches = fuzzy_match_asset("xyznotreal", self.assets)
        assert len(matches) == 0


class TestOracleFuzzyMatching:
    """Regression tests for oracle fuzzy matching prioritization."""

    def setup_method(self):
        self.oracles = load_oracles(DATA_DIR)

    def test_exact_match_takes_priority(self):
        """Exact match should be returned first."""
        # Find an oracle that exists
        if "action" in self.oracles:
            matches = fuzzy_match_oracle("action", self.oracles)
            assert len(matches) >= 1
            assert matches[0].key == "action"

    def test_prefix_match_over_substring(self):
        """Prefix matches should take priority over substring matches."""
        # Test with "planet" - should match "planet_*" before "*planet*"
        matches = fuzzy_match_oracle("planet", self.oracles)
        if matches:
            first_match = matches[0]
            # First match should start with "planet"
            assert first_match.key.startswith("planet") or first_match.name.lower().startswith(
                "planet"
            )

    def test_case_insensitive_matching(self):
        """Matching should be case-insensitive."""
        matches_lower = fuzzy_match_oracle("action", self.oracles)
        matches_upper = fuzzy_match_oracle("ACTION", self.oracles)
        matches_mixed = fuzzy_match_oracle("Action", self.oracles)

        # All should return the same results
        assert len(matches_lower) == len(matches_upper) == len(matches_mixed)

    def test_normalized_matching_with_underscores(self):
        """Underscores and spaces should be normalized."""
        # If there's an oracle like "first_look", searching "first look" should match
        matches_underscore = fuzzy_match_oracle("first_look", self.oracles)
        matches_space = fuzzy_match_oracle("first look", self.oracles)

        # Both should return same results
        assert len(matches_underscore) == len(matches_space)


class TestMoveFuzzyMatching:
    """Regression tests for move fuzzy matching prioritization."""

    def setup_method(self):
        self.moves = load_move_data()

    def test_exact_match_takes_priority(self):
        """Exact match should be returned first."""
        if "strike" in self.moves:
            matches = fuzzy_match_move("strike", self.moves)
            assert len(matches) >= 1
            assert "strike" in matches[0]

    def test_prefix_match_over_substring(self):
        """Prefix matches should take priority over substring matches."""
        # Test with "face" - should match "face_*" before "*face*"
        matches = fuzzy_match_move("face", self.moves)
        if matches:
            first_match = matches[0]
            # First match should start with "face"
            assert first_match.startswith("face") or self.moves[first_match][
                "name"
            ].lower().startswith("face")

    def test_substring_still_works(self):
        """Substring matches should still work when no exact/prefix matches exist."""
        # Search for a substring that's not at the start
        # For example, "danger" should match "face_danger"
        matches = fuzzy_match_move("danger", self.moves)
        if matches:
            # Should find moves containing "danger"
            assert any("danger" in match for match in matches)

    def test_normalized_matching(self):
        """Spaces and underscores should be normalized."""
        matches_underscore = fuzzy_match_move("face_danger", self.moves)
        matches_space = fuzzy_match_move("face danger", self.moves)

        # Both should return same results
        assert len(matches_underscore) == len(matches_space)


class TestFuzzyMatchingEdgeCases:
    """Edge cases and special scenarios for fuzzy matching."""

    def setup_method(self):
        self.assets = load_assets(DATA_DIR)
        self.oracles = load_oracles(DATA_DIR)
        self.moves = load_move_data()

    def test_single_character_query(self):
        """Single character queries should work but likely return many matches."""
        asset_matches = fuzzy_match_asset("s", self.assets)
        oracle_matches = fuzzy_match_oracle("a", self.oracles)
        move_matches = fuzzy_match_move("f", self.moves)

        # Should not crash, but might return many results
        assert isinstance(asset_matches, list)
        assert isinstance(oracle_matches, list)
        assert isinstance(move_matches, list)

    def test_special_characters_normalized(self):
        """Special characters like hyphens should be normalized to underscores."""
        # Test that "test-name" is treated same as "test_name"
        asset_matches_hyphen = fuzzy_match_asset("engine-upgrade", self.assets)
        asset_matches_underscore = fuzzy_match_asset("engine_upgrade", self.assets)

        assert len(asset_matches_hyphen) == len(asset_matches_underscore)

    def test_multiple_exact_matches_if_duplicate_keys(self):
        """If somehow there are duplicate keys, all exact matches should be returned."""
        # This is a sanity check - normally keys should be unique
        matches = fuzzy_match_asset("starship", self.assets)
        if matches:
            # Should get at least the starship
            assert any(m.key == "starship" for m in matches)
