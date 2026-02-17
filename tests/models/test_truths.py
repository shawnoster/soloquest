"""Tests for truth models."""

from soloquest.models.truths import ChosenTruth, TruthCategory, TruthOption


class TestTruthOption:
    """Tests for TruthOption model."""

    def test_matches_roll(self):
        """Test roll matching logic."""
        option = TruthOption(
            roll_range=(1, 33),
            summary="Test option",
            text="Test text",
        )

        assert option.matches_roll(1)
        assert option.matches_roll(17)
        assert option.matches_roll(33)
        assert not option.matches_roll(0)
        assert not option.matches_roll(34)

    def test_with_subchoices(self):
        """Test option with subchoices."""
        option = TruthOption(
            roll_range=(1, 33),
            summary="Test",
            text="Test",
            subchoices=["Sub 1", "Sub 2"],
        )

        assert len(option.subchoices) == 2
        assert "Sub 1" in option.subchoices


class TestTruthCategory:
    """Tests for TruthCategory model."""

    def test_get_option_by_roll(self):
        """Test getting option by roll value."""
        options = [
            TruthOption(roll_range=(1, 33), summary="Low", text="Low range"),
            TruthOption(roll_range=(34, 67), summary="Mid", text="Mid range"),
            TruthOption(roll_range=(68, 100), summary="High", text="High range"),
        ]

        category = TruthCategory(name="Test Category", description="Test", order=1, options=options)

        assert category.get_option_by_roll(1).summary == "Low"
        assert category.get_option_by_roll(50).summary == "Mid"
        assert category.get_option_by_roll(100).summary == "High"
        assert category.get_option_by_roll(0) is None
        assert category.get_option_by_roll(101) is None


class TestChosenTruth:
    """Tests for ChosenTruth model."""

    def test_to_dict(self):
        """Test serialization to dict."""
        truth = ChosenTruth(
            category="Cataclysm",
            option_summary="The sun plague",
            option_text="Full text here",
            quest_starter="Quest text",
        )

        data = truth.to_dict()
        assert data["category"] == "Cataclysm"
        assert data["option_summary"] == "The sun plague"
        assert data["option_text"] == "Full text here"
        assert data["quest_starter"] == "Quest text"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "category": "Exodus",
            "option_summary": "Generation ships",
            "option_text": "Millennia-long journey",
            "custom_text": "",
            "quest_starter": "A lost ship appears",
        }

        truth = ChosenTruth.from_dict(data)
        assert truth.category == "Exodus"
        assert truth.option_summary == "Generation ships"
        assert truth.option_text == "Millennia-long journey"
        assert truth.quest_starter == "A lost ship appears"

    def test_display_text_uses_custom(self):
        """Test that display_text prefers custom text."""
        truth = ChosenTruth(
            category="Test",
            option_summary="Original",
            custom_text="Custom version",
        )

        assert truth.display_text() == "Custom version"

    def test_display_text_falls_back_to_summary(self):
        """Test that display_text falls back to summary."""
        truth = ChosenTruth(
            category="Test",
            option_summary="Original",
            custom_text="",
        )

        assert truth.display_text() == "Original"

    def test_roundtrip(self):
        """Test serialization roundtrip."""
        original = ChosenTruth(
            category="Magic",
            option_summary="Magic exists",
            option_text="Full description",
            custom_text="My custom version",
            quest_starter="Quest",
        )

        data = original.to_dict()
        restored = ChosenTruth.from_dict(data)

        assert restored.category == original.category
        assert restored.option_summary == original.option_summary
        assert restored.option_text == original.option_text
        assert restored.custom_text == original.custom_text
        assert restored.quest_starter == original.quest_starter
