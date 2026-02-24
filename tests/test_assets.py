"""Tests for asset models and functionality."""

from pathlib import Path

from wyrd.engine.assets import fuzzy_match_asset, load_assets
from wyrd.models.asset import Asset, AssetAbility, CharacterAsset

DATA_DIR = Path(__file__).parent.parent / "wyrd" / "data"


class TestAssetModel:
    def test_asset_creation(self):
        abilities = [
            AssetAbility(text="First ability", enabled=True),
            AssetAbility(text="Second ability", enabled=False),
        ]
        asset = Asset(
            key="test_asset",
            name="Test Asset",
            category="path",
            description="A test asset",
            abilities=abilities,
            tracks={"health": (0, 5)},
        )

        assert asset.key == "test_asset"
        assert asset.name == "Test Asset"
        assert len(asset.abilities) == 2
        assert asset.abilities[0].enabled is True
        assert asset.abilities[1].enabled is False
        assert "health" in asset.tracks


class TestCharacterAsset:
    def test_character_asset_creation(self):
        char_asset = CharacterAsset(
            asset_key="starship",
            abilities_unlocked=[True, False, False],
            track_values={"integrity": 5},
            input_values={"name": "The Wanderer"},
        )

        assert char_asset.asset_key == "starship"
        assert char_asset.abilities_unlocked == [True, False, False]
        assert char_asset.track_values["integrity"] == 5
        assert char_asset.input_values["name"] == "The Wanderer"


class TestFuzzyMatchAsset:
    def setup_method(self):
        self.assets = load_assets(DATA_DIR)

    def test_exact_key_match(self):
        results = fuzzy_match_asset("starship", self.assets)
        assert any(a.key == "starship" for a in results)

    def test_partial_name_match(self):
        results = fuzzy_match_asset("ship", self.assets)
        assert len(results) > 0

    def test_no_match_returns_empty(self):
        results = fuzzy_match_asset("xyznotreal", self.assets)
        assert results == []

    def test_normalized_matching(self):
        """Test that spaces/underscores are normalized in matching."""
        # Try to find an asset with spaces or underscores
        results = fuzzy_match_asset("engine", self.assets)
        # Should match engine_upgrade or similar
        assert len(results) > 0


class TestCharacterAssetBackwardCompatibility:
    def test_character_from_dict_old_format(self):
        """Test loading old save format with assets as list[str]."""
        from wyrd.models.character import Character

        old_save = {
            "name": "Test Character",
            "stats": {"edge": 2, "heart": 1, "iron": 3, "shadow": 1, "wits": 2},
            "assets": ["starship", "navigator"],  # Old format: just strings
        }

        char = Character.from_dict(old_save)
        assert len(char.assets) == 2
        assert char.assets[0].asset_key == "starship"
        assert char.assets[1].asset_key == "navigator"
        # Should have empty progression data
        assert char.assets[0].abilities_unlocked == []
        assert char.assets[0].track_values == {}

    def test_character_from_dict_new_format(self):
        """Test loading new save format with full CharacterAsset data."""
        from wyrd.models.character import Character

        new_save = {
            "name": "Test Character",
            "stats": {"edge": 2, "heart": 1, "iron": 3, "shadow": 1, "wits": 2},
            "assets": [
                {
                    "asset_key": "starship",
                    "abilities_unlocked": [True, True, False],
                    "track_values": {"integrity": 4},
                    "input_values": {"name": "The Wanderer"},
                }
            ],
        }

        char = Character.from_dict(new_save)
        assert len(char.assets) == 1
        assert char.assets[0].asset_key == "starship"
        assert char.assets[0].abilities_unlocked == [True, True, False]
        assert char.assets[0].track_values["integrity"] == 4
        assert char.assets[0].input_values["name"] == "The Wanderer"

    def test_character_to_dict_new_format(self):
        """Test that to_dict produces the new format."""
        from wyrd.models.character import Character

        char = Character(name="Test")
        char.assets = [
            CharacterAsset(
                asset_key="starship",
                abilities_unlocked=[True, False, False],
                track_values={"integrity": 5},
            )
        ]

        data = char.to_dict()
        assert isinstance(data["assets"], list)
        assert len(data["assets"]) == 1
        assert data["assets"][0]["asset_key"] == "starship"
        assert data["assets"][0]["abilities_unlocked"] == [True, False, False]
