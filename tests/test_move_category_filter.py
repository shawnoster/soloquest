"""Tests for move category filtering and tab-completion."""

from pathlib import Path

from prompt_toolkit.document import Document

from soloquest.commands.completion import CommandCompleter
from soloquest.commands.move import fuzzy_match_move
from soloquest.loop import load_move_data

DATA_DIR = Path(__file__).parent.parent / "soloquest" / "data"


class TestMoveCategoryFiltering:
    """Test category filtering in move command."""

    def setup_method(self):
        """Load moves for testing."""
        self.moves = load_move_data()

    def test_category_filter_returns_only_category_moves(self):
        """Filtering by category should return only moves in that category."""
        matches = fuzzy_match_move("", self.moves, category_filter="combat")

        # All matches should be combat moves
        assert len(matches) > 0
        for key in matches:
            assert self.moves[key]["category"] == "combat"

    def test_category_filter_with_query(self):
        """Category filter with search query should work together."""
        # Search for "gain" in combat category
        matches = fuzzy_match_move("gain", self.moves, category_filter="combat")

        # Should find "gain_ground"
        assert "gain_ground" in matches
        # All matches should be combat moves
        for key in matches:
            assert self.moves[key]["category"] == "combat"

    def test_category_filter_adventure(self):
        """Adventure category should have expected moves."""
        matches = fuzzy_match_move("", self.moves, category_filter="adventure")

        assert len(matches) > 0
        assert "face_danger" in matches
        assert "secure_an_advantage" in matches

    def test_category_filter_vow(self):
        """Vow category should have vow-related moves."""
        matches = fuzzy_match_move("", self.moves, category_filter="vow")

        assert len(matches) > 0
        assert "swear_an_iron_vow" in matches
        assert "fulfill_your_vow" in matches

    def test_category_filter_invalid_category(self):
        """Invalid category should return no matches."""
        matches = fuzzy_match_move("", self.moves, category_filter="nonexistent")

        assert len(matches) == 0

    def test_category_filter_case_insensitive(self):
        """Category filter should be case-insensitive."""
        matches_lower = fuzzy_match_move("", self.moves, category_filter="combat")
        matches_upper = fuzzy_match_move("", self.moves, category_filter="COMBAT")

        assert len(matches_lower) == len(matches_upper)
        assert set(matches_lower) == set(matches_upper)

    def test_no_query_no_category_returns_empty(self):
        """No query and no category filter should return empty list."""
        matches = fuzzy_match_move("", self.moves, category_filter=None)

        assert len(matches) == 0

    def test_query_without_category_filter(self):
        """Query without category filter should work as before."""
        matches = fuzzy_match_move("strike", self.moves, category_filter=None)

        # Should find moves with "strike" in the name
        assert len(matches) > 0

    def test_all_categories_have_moves(self):
        """All known categories should return at least one move."""
        known_categories = [
            "adventure",
            "combat",
            "connection",
            "exploration",
            "fate",
            "legacy",
            "recover",
            "scene_challenge",
            "session",
            "suffer",
            "threshold",
            "vow",
        ]

        for category in known_categories:
            matches = fuzzy_match_move("", self.moves, category_filter=category)
            assert len(matches) > 0, f"Category '{category}' has no moves"


class TestMoveCategoryCompletion:
    """Test tab-completion for category filters."""

    def setup_method(self):
        """Set up completer with move data."""
        self.moves = load_move_data()
        self.completer = CommandCompleter(moves=self.moves, oracles={}, assets={})

    def test_complete_category_prefix(self):
        """Typing 'category:' should suggest category names."""
        doc = Document("/move category:", cursor_position=15)
        completions = list(self.completer.get_completions(doc, None))

        # Should have multiple category suggestions
        assert len(completions) > 5

        # Should include known categories
        category_texts = [c.text for c in completions]
        assert "adventure" in category_texts
        assert "combat" in category_texts
        assert "vow" in category_texts

    def test_complete_type_prefix(self):
        """Typing 'type:' should suggest category names."""
        doc = Document("/move type:", cursor_position=11)
        completions = list(self.completer.get_completions(doc, None))

        # Should have multiple category suggestions
        assert len(completions) > 5

        # Should include known categories
        category_texts = [c.text for c in completions]
        assert "adventure" in category_texts
        assert "combat" in category_texts

    def test_complete_cat_prefix(self):
        """Typing 'cat:' should suggest category names."""
        doc = Document("/move cat:", cursor_position=10)
        completions = list(self.completer.get_completions(doc, None))

        # Should have multiple category suggestions
        assert len(completions) > 5

        # Should include known categories
        category_texts = [c.text for c in completions]
        assert "adventure" in category_texts

    def test_complete_partial_category(self):
        """Typing 'category:adv' should filter to matching categories."""
        doc = Document("/move category:adv", cursor_position=18)
        completions = list(self.completer.get_completions(doc, None))

        # Should filter to categories containing "adv"
        category_texts = [c.text for c in completions]
        assert "adventure" in category_texts
        # Should not include unrelated categories
        assert "combat" not in category_texts
        assert "vow" not in category_texts

    def test_category_completions_are_sorted(self):
        """Category completions should be alphabetically sorted."""
        doc = Document("/move category:", cursor_position=15)
        completions = list(self.completer.get_completions(doc, None))

        # Extract category names
        category_texts = [c.text for c in completions]

        # Should be sorted
        assert category_texts == sorted(category_texts)

    def test_regular_move_completion_still_works(self):
        """Regular move name completion should still work."""
        doc = Document("/move stri", cursor_position=10)
        completions = list(self.completer.get_completions(doc, None))

        # Should find moves with "stri" in name/key
        assert len(completions) > 0

        # Should not be category completions
        move_texts = [c.text for c in completions]
        # Categories shouldn't show up in regular move search
        assert all(":" not in text for text in move_texts)

    def test_completion_without_colon(self):
        """Completion without colon should suggest move names."""
        doc = Document("/move face", cursor_position=10)
        completions = list(self.completer.get_completions(doc, None))

        # Should find moves with "face" in name
        assert len(completions) > 0

        # Should include face_danger, face_death, face_desolation
        move_texts = [c.text for c in completions]
        assert any("face" in text for text in move_texts)

    def test_empty_category_value_shows_all_categories(self):
        """Empty value after 'category:' should show all categories."""
        doc = Document("/move category:", cursor_position=15)
        completions = list(self.completer.get_completions(doc, None))

        # Should show all categories
        assert len(completions) >= 12  # We know there are 12 categories

    def test_category_completion_display_meta(self):
        """Category completions should show full filter syntax in meta."""
        doc = Document("/move category:", cursor_position=15)
        completions = list(self.completer.get_completions(doc, None))

        # Find a completion
        completion = next((c for c in completions if c.text == "combat"), None)
        assert completion is not None

        # Should have display_meta showing the full syntax
        assert completion.display_meta
        meta_str = str(completion.display_meta)
        assert "category:combat" in meta_str or "combat" in meta_str
