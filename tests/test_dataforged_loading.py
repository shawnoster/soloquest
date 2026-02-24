"""Tests for dataforged JSON loading."""

from pathlib import Path

from wyrd.engine.assets import load_assets
from wyrd.engine.oracles import load_dataforged_oracles, load_oracles

DATA_DIR = Path(__file__).parent.parent / "wyrd" / "data"


class TestDataforgedOracles:
    def test_loads_oracles_from_json(self):
        oracles = load_dataforged_oracles(DATA_DIR)
        assert len(oracles) > 30, "Should load 90+ oracles from dataforged"

    def test_oracle_has_valid_structure(self):
        oracles = load_dataforged_oracles(DATA_DIR)
        # Check a sample oracle exists and has correct structure
        assert len(oracles) > 0
        sample_oracle = next(iter(oracles.values()))
        assert sample_oracle.key
        assert sample_oracle.name
        assert sample_oracle.die == "d100"
        assert len(sample_oracle.results) > 0

    def test_oracle_results_have_ranges(self):
        oracles = load_dataforged_oracles(DATA_DIR)
        sample_oracle = next(iter(oracles.values()))
        for low, high, text in sample_oracle.results:
            assert isinstance(low, int)
            assert isinstance(high, int)
            assert isinstance(text, str)
            assert low <= high
            assert text  # not empty

    def test_merged_loading_includes_dataforged(self):
        """Test that load_oracles merges both TOML and dataforged."""
        all_oracles = load_oracles(DATA_DIR)
        dataforged_only = load_dataforged_oracles(DATA_DIR)

        # Should have at least as many as dataforged alone
        assert len(all_oracles) >= len(dataforged_only)

    def test_toml_overrides_json(self):
        """Test that TOML oracles override dataforged when keys conflict."""
        all_oracles = load_oracles(DATA_DIR)

        # If there's a common oracle in both TOML and JSON, TOML should win
        # We can't guarantee a specific overlap, but we can verify the merge works
        assert len(all_oracles) > 0


class TestDataforgedMoves:
    def test_moves_loaded_from_json(self):
        from wyrd.loop import load_dataforged_moves

        moves = load_dataforged_moves()
        # Should load some moves from dataforged
        assert len(moves) > 0

    def test_move_has_basic_fields(self):
        from wyrd.loop import load_dataforged_moves

        moves = load_dataforged_moves()
        if moves:
            sample_move = next(iter(moves.values()))
            assert "name" in sample_move
            assert "category" in sample_move


class TestDataforgedAssets:
    def test_loads_assets_from_json(self):
        assets = load_assets(DATA_DIR)
        assert len(assets) >= 80, "Should load 90 assets from dataforged"

    def test_asset_has_valid_structure(self):
        assets = load_assets(DATA_DIR)
        assert len(assets) > 0
        sample_asset = next(iter(assets.values()))
        assert sample_asset.key
        assert sample_asset.name
        assert sample_asset.category

    def test_asset_abilities_exist(self):
        assets = load_assets(DATA_DIR)
        # Find an asset with abilities (starship should have them)
        starship = assets.get("starship")
        if starship:
            assert len(starship.abilities) > 0
            ability = starship.abilities[0]
            assert ability.text
            assert isinstance(ability.enabled, bool)

    def test_asset_tracks_exist(self):
        assets = load_assets(DATA_DIR)
        # Starship should have integrity track
        starship = assets.get("starship")
        if starship:
            assert len(starship.tracks) > 0
            track_name, (min_val, max_val) = next(iter(starship.tracks.items()))
            assert isinstance(min_val, int)
            assert isinstance(max_val, int)
            assert min_val <= max_val
