"""Integration tests for asset system with character and game state.

Tests the full flow of assets from loading to display to character ownership.
"""

from pathlib import Path

from wyrd.engine.assets import load_assets
from wyrd.models.asset import CharacterAsset
from wyrd.models.character import Character, Stats

DATA_DIR = Path(__file__).parent.parent / "wyrd" / "data"


class TestAssetLoading:
    """Test comprehensive asset loading from dataforged."""

    def setup_method(self):
        self.assets = load_assets(DATA_DIR)

    def test_loads_minimum_number_of_assets(self):
        """Should load at least 80 assets from dataforged."""
        assert len(self.assets) >= 80

    def test_starship_asset_exists(self):
        """The starship asset should be present (it's a core asset)."""
        assert "starship" in self.assets
        starship = self.assets["starship"]
        assert starship.name == "Starship"

    def test_all_assets_have_required_fields(self):
        """All assets should have key, name, and category."""
        for key, asset in self.assets.items():
            assert asset.key == key
            assert asset.name
            assert asset.category
            assert isinstance(asset.abilities, list)

    def test_assets_have_valid_categories(self):
        """All assets should have valid category types."""
        categories_found = {asset.category for asset in self.assets.values()}

        # All categories should be strings
        for category in categories_found:
            assert isinstance(category, str)
            assert category  # Not empty

    def test_assets_with_tracks_have_valid_ranges(self):
        """Assets with condition meters should have valid min/max ranges."""
        for asset in self.assets.values():
            for _track_name, (min_val, max_val) in asset.tracks.items():
                assert isinstance(min_val, int)
                assert isinstance(max_val, int)
                assert min_val <= max_val
                assert min_val >= 0  # Tracks shouldn't have negative minimums

    def test_starship_has_integrity_track(self):
        """Starship should have an integrity condition meter."""
        starship = self.assets.get("starship")
        if starship:
            assert "integrity" in starship.tracks
            min_val, max_val = starship.tracks["integrity"]
            assert min_val == 0
            assert max_val == 5

    def test_starship_has_multiple_abilities(self):
        """Starship should have exactly 3 abilities."""
        starship = self.assets.get("starship")
        if starship:
            assert len(starship.abilities) == 3

    def test_starship_is_shared(self):
        """Starship should be marked as a shared asset."""
        starship = self.assets.get("starship")
        if starship:
            assert starship.shared is True

    def test_path_assets_exist(self):
        """There should be multiple path assets."""
        path_assets = [a for a in self.assets.values() if a.category == "path"]
        assert len(path_assets) > 10  # Should have many paths

    def test_companion_assets_exist(self):
        """There should be companion assets."""
        companion_assets = [a for a in self.assets.values() if a.category == "companion"]
        assert len(companion_assets) > 0

    def test_module_assets_exist(self):
        """There should be module assets for starship."""
        module_assets = [a for a in self.assets.values() if a.category == "module"]
        assert len(module_assets) > 10


class TestCharacterAssetIntegration:
    """Test how assets integrate with the character system."""

    def test_character_can_have_multiple_assets(self):
        """Character should be able to own multiple assets."""
        char = Character(name="Test", stats=Stats())
        char.assets = [
            CharacterAsset(asset_key="starship", abilities_unlocked=[True, False, False]),
            CharacterAsset(asset_key="navigator", abilities_unlocked=[True]),
            CharacterAsset(asset_key="diplomat", abilities_unlocked=[True, True, False]),
        ]

        assert len(char.assets) == 3
        assert all(isinstance(a, CharacterAsset) for a in char.assets)

    def test_character_asset_progression(self):
        """Character assets should track ability progression."""
        asset = CharacterAsset(
            asset_key="navigator",
            abilities_unlocked=[True, True, False],
            track_values={},
        )

        assert asset.abilities_unlocked[0] is True
        assert asset.abilities_unlocked[1] is True
        assert asset.abilities_unlocked[2] is False

    def test_character_asset_with_tracks(self):
        """Character assets should track condition meter values."""
        asset = CharacterAsset(
            asset_key="companion",
            abilities_unlocked=[True],
            track_values={"health": 3},
        )

        assert asset.track_values["health"] == 3

    def test_character_asset_with_inputs(self):
        """Character assets should store custom input values."""
        asset = CharacterAsset(
            asset_key="starship",
            abilities_unlocked=[True, False, False],
            input_values={"name": "The Wanderer"},
        )

        assert asset.input_values["name"] == "The Wanderer"

    def test_character_serialization_with_assets(self):
        """Character with assets should serialize and deserialize correctly."""
        char = Character(name="Test", stats=Stats())
        char.assets = [
            CharacterAsset(
                asset_key="starship",
                abilities_unlocked=[True, True, False],
                track_values={"integrity": 4},
                input_values={"name": "The Wanderer"},
            )
        ]

        # Serialize to dict
        data = char.to_dict()

        # Deserialize back
        restored = Character.from_dict(data)

        # Verify assets were preserved
        assert len(restored.assets) == 1
        assert restored.assets[0].asset_key == "starship"
        assert restored.assets[0].abilities_unlocked == [True, True, False]
        assert restored.assets[0].track_values["integrity"] == 4
        assert restored.assets[0].input_values["name"] == "The Wanderer"

    def test_character_with_no_assets(self):
        """Character with no assets should handle correctly."""
        char = Character(name="Test", stats=Stats())
        assert char.assets == []

        data = char.to_dict()
        restored = Character.from_dict(data)
        assert restored.assets == []


class TestAssetAbilityProgression:
    """Test asset ability unlocking and progression."""

    def test_all_abilities_start_disabled_by_default(self):
        """New character assets should have all abilities locked initially."""
        asset = CharacterAsset(asset_key="test")
        assert asset.abilities_unlocked == []

    def test_progressive_ability_unlock(self):
        """Abilities should be unlockable in order."""
        # Simulate unlocking abilities progressively
        abilities = [True, False, False]
        asset = CharacterAsset(asset_key="test", abilities_unlocked=abilities)
        assert asset.abilities_unlocked == [True, False, False]

        # Unlock second ability
        abilities[1] = True
        asset = CharacterAsset(asset_key="test", abilities_unlocked=abilities)
        assert asset.abilities_unlocked == [True, True, False]

    def test_all_abilities_unlocked(self):
        """Should support having all abilities unlocked."""
        asset = CharacterAsset(asset_key="test", abilities_unlocked=[True, True, True, True])
        assert all(asset.abilities_unlocked)


class TestAssetDataQuality:
    """Test the quality and consistency of loaded asset data."""

    def setup_method(self):
        self.assets = load_assets(DATA_DIR)

    def test_no_duplicate_asset_keys(self):
        """Asset keys should be unique."""
        keys = list(self.assets.keys())
        assert len(keys) == len(set(keys))

    def test_all_asset_names_are_non_empty(self):
        """All assets should have non-empty names."""
        for asset in self.assets.values():
            assert asset.name
            assert len(asset.name.strip()) > 0

    def test_asset_keys_are_normalized(self):
        """Asset keys should be lowercase with underscores."""
        for key in self.assets:
            assert key == key.lower()
            assert " " not in key
            assert "-" not in key or "_" in key  # Prefer underscores

    def test_abilities_have_text(self):
        """All abilities should have descriptive text."""
        for asset in self.assets.values():
            for ability in asset.abilities:
                assert ability.text
                assert len(ability.text.strip()) > 0

    def test_track_names_are_valid(self):
        """All track names should be non-empty strings."""
        for asset in self.assets.values():
            for track_name in asset.tracks:
                assert isinstance(track_name, str)
                assert track_name  # Not empty

    def test_shared_status_is_boolean(self):
        """Shared status should always be a boolean."""
        for asset in self.assets.values():
            assert isinstance(asset.shared, bool)


class TestAssetLookupPerformance:
    """Test that asset lookups are efficient."""

    def setup_method(self):
        self.assets = load_assets(DATA_DIR)

    def test_asset_lookup_by_key_is_fast(self):
        """Direct key lookup should be O(1)."""
        import time

        start = time.time()
        for _ in range(1000):
            _ = self.assets.get("starship")
        elapsed = time.time() - start

        # Should be very fast (< 0.1 seconds for 1000 lookups)
        assert elapsed < 0.1

    def test_fuzzy_matching_completes_quickly(self):
        """Fuzzy matching should complete in reasonable time."""
        import time

        from wyrd.engine.assets import fuzzy_match_asset

        start = time.time()
        for query in ["star", "nav", "module", "companion", "path"]:
            fuzzy_match_asset(query, self.assets)
        elapsed = time.time() - start

        # Should complete quickly (< 0.5 seconds for multiple searches)
        assert elapsed < 0.5
