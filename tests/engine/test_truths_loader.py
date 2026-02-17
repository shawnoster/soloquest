"""Tests for truth category loading."""

from pathlib import Path

import pytest

from soloquest.engine.truths import (
    get_ordered_categories,
    get_truth_category,
    load_truth_categories,
)


@pytest.fixture
def data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent.parent.parent / "soloquest" / "data"


def test_load_truth_categories(data_dir):
    """Test loading truth categories from TOML."""
    categories = load_truth_categories(data_dir)

    assert len(categories) > 0
    assert "Cataclysm" in categories
    assert "Exodus" in categories
    assert "Magic" in categories


def test_truth_category_structure(data_dir):
    """Test that loaded categories have correct structure."""
    categories = load_truth_categories(data_dir)

    cataclysm = categories.get("Cataclysm")
    assert cataclysm is not None
    assert cataclysm.name == "Cataclysm"
    assert len(cataclysm.description) > 0
    assert cataclysm.order > 0
    assert len(cataclysm.options) == 3  # Each truth has 3 options


def test_truth_options_have_roll_ranges(data_dir):
    """Test that options have valid roll ranges."""
    categories = load_truth_categories(data_dir)

    for category in categories.values():
        for option in category.options:
            low, high = option.roll_range
            assert low >= 1
            assert high <= 100
            assert low <= high
            assert len(option.summary) > 0
            assert len(option.text) > 0


def test_get_truth_category_case_insensitive(data_dir):
    """Test getting category by name is case-insensitive."""
    categories = load_truth_categories(data_dir)

    assert get_truth_category(categories, "cataclysm") is not None
    assert get_truth_category(categories, "CATACLYSM") is not None
    assert get_truth_category(categories, "Cataclysm") is not None


def test_get_truth_category_missing(data_dir):
    """Test getting non-existent category returns None."""
    categories = load_truth_categories(data_dir)

    assert get_truth_category(categories, "NonExistent") is None


def test_get_ordered_categories(data_dir):
    """Test getting categories in order."""
    categories = load_truth_categories(data_dir)
    ordered = get_ordered_categories(categories)

    assert len(ordered) == len(categories)
    # Check that order values are increasing
    for i in range(len(ordered) - 1):
        assert ordered[i].order <= ordered[i + 1].order


def test_all_14_categories_present(data_dir):
    """Test that all 14 truth categories are loaded."""
    categories = load_truth_categories(data_dir)

    expected_categories = [
        "Cataclysm",
        "Exodus",
        "Communities",
        "Iron",
        "Laws",
        "Religion",
        "Magic",
        "Communication and Data",
        "Medicine",
        "Artificial Intelligence",
        "War",
        "Lifeforms",
        "Precursors",
        "Horrors",
    ]

    for name in expected_categories:
        assert name in categories, f"Missing category: {name}"


def test_quest_starters_present(data_dir):
    """Test that options have quest starters."""
    categories = load_truth_categories(data_dir)

    for category in categories.values():
        for option in category.options:
            # Quest starters should be present (can be empty string, but field exists)
            assert hasattr(option, "quest_starter")


def test_load_from_nonexistent_path():
    """Test loading from non-existent path returns empty dict."""
    fake_path = Path("/nonexistent/path")
    categories = load_truth_categories(fake_path)

    assert categories == {}
