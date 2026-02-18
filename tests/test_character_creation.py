"""Tests for character creation flow and asset tab-completion."""

from pathlib import Path

from prompt_toolkit.document import Document

from soloquest.commands.new_character import AssetCompleter
from soloquest.engine.assets import load_assets

DATA_DIR = Path(__file__).parent.parent / "soloquest" / "data"


class TestAssetCompleter:
    """Test asset tab-completion during character creation."""

    def setup_method(self):
        """Load assets for testing."""
        self.assets = load_assets(DATA_DIR)
        self.completer = AssetCompleter(self.assets)

    def test_completer_shows_all_assets_with_empty_input(self):
        """Empty input should show all available assets."""
        doc = Document("", cursor_position=0)
        completions = list(self.completer.get_completions(doc, None))

        # Should have many completions (at least 80 assets)
        assert len(completions) >= 80

    def test_completer_filters_by_partial_match(self):
        """Partial input should filter to matching assets."""
        doc = Document("ace", cursor_position=3)
        completions = list(self.completer.get_completions(doc, None))

        # Should have some matches for "ace"
        assert len(completions) > 0
        # All matches should contain "ace" in key or name
        for completion in completions:
            assert "ace" in completion.text.lower() or (
                completion.display_meta and "ace" in completion.display_meta.lower()
            )

    def test_completer_matches_asset_key(self):
        """Should match against asset keys."""
        doc = Document("starship", cursor_position=8)
        completions = list(self.completer.get_completions(doc, None))

        # Should find starship
        assert any(c.text == "starship" for c in completions)

    def test_completer_matches_asset_name(self):
        """Should match against asset display names."""
        # "Starship" is the display name for "starship" key
        doc = Document("star", cursor_position=4)
        completions = list(self.completer.get_completions(doc, None))

        # Should find starship by matching the name
        assert any("starship" in c.text or "star" in c.text.lower() for c in completions)

    def test_completions_are_alphabetically_sorted(self):
        """Completions should be returned in alphabetical order."""
        doc = Document("", cursor_position=0)
        completions = list(self.completer.get_completions(doc, None))

        # Extract completion texts
        completion_texts = [c.text for c in completions]

        # Should be sorted
        assert completion_texts == sorted(completion_texts)

    def test_completer_handles_underscores(self):
        """Should handle underscores in asset names."""
        doc = Document("crew_commander", cursor_position=14)
        completions = list(self.completer.get_completions(doc, None))

        # Should find crew_commander
        assert len(completions) > 0
        assert any(c.text == "crew_commander" for c in completions)

    def test_completer_shows_display_meta(self):
        """Completions should include display names as meta."""
        doc = Document("starship", cursor_position=8)
        completions = list(self.completer.get_completions(doc, None))

        # Find starship completion
        starship_completion = next(c for c in completions if c.text == "starship")

        # Should have display meta showing full name
        assert starship_completion.display_meta
        # display_meta can be a string or FormattedText, convert to string
        meta_str = str(starship_completion.display_meta)
        assert "Starship" in meta_str or "starship" in meta_str

    def test_completer_case_insensitive(self):
        """Completion matching should be case-insensitive."""
        doc_lower = Document("ace", cursor_position=3)
        doc_upper = Document("ACE", cursor_position=3)

        completions_lower = list(self.completer.get_completions(doc_lower, None))
        completions_upper = list(self.completer.get_completions(doc_upper, None))

        # Should return same results regardless of case
        assert len(completions_lower) == len(completions_upper)
        assert set(c.text for c in completions_lower) == set(c.text for c in completions_upper)

    def test_completer_handles_spaces_in_input(self):
        """Should normalize spaces to underscores for matching."""
        doc = Document("crew commander", cursor_position=14)
        completions = list(self.completer.get_completions(doc, None))

        # Should find crew_commander even with spaces
        assert len(completions) > 0
        assert any(c.text == "crew_commander" for c in completions)

    def test_completer_with_no_matches(self):
        """Should return empty list when no assets match."""
        doc = Document("zzzznonexistent", cursor_position=15)
        completions = list(self.completer.get_completions(doc, None))

        # Should have no matches
        assert len(completions) == 0

    def test_completer_partial_match_multiple_results(self):
        """Partial match should return multiple relevant results."""
        doc = Document("ar", cursor_position=2)
        completions = list(self.completer.get_completions(doc, None))

        # Should have multiple assets matching "ar" (archer, armored, artist, etc.)
        assert len(completions) >= 3
        # All should be sorted
        completion_texts = [c.text for c in completions]
        assert completion_texts == sorted(completion_texts)
