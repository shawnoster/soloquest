"""Asset loading and lookup."""

from __future__ import annotations

import json
from pathlib import Path

from soloquest.models.asset import Asset, AssetAbility


def load_assets(data_dir: Path) -> dict[str, Asset]:
    """Load all assets from dataforged JSON."""
    path = data_dir / "dataforged" / "assets.json"
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assets: dict[str, Asset] = {}

    # Recursively extract assets from nested structure
    def extract_assets(item: dict | list) -> None:
        if isinstance(item, list):
            for sub_item in item:
                extract_assets(sub_item)
        elif isinstance(item, dict) and "Assets" in item:
            # If this has "Assets" key, iterate them
            category_name = item.get("Name", "general").lower().replace(" ", "_")

            for asset_data in item["Assets"]:
                if "$id" not in asset_data or "Name" not in asset_data:
                    continue

                # Create simplified key
                asset_id = asset_data["$id"]
                key_parts = asset_id.split("/")
                key = key_parts[-1].lower().replace(" ", "_").replace("-", "_")

                # Extract abilities
                abilities = []
                for ability_data in asset_data.get("Abilities", []):
                    text = ability_data.get("Text", "")
                    enabled = ability_data.get("Enabled", False)
                    abilities.append(AssetAbility(text=text, enabled=enabled))

                # Extract condition meters/tracks
                tracks: dict[str, tuple[int, int]] = {}
                if "Condition Meter" in asset_data:
                    meter = asset_data["Condition Meter"]
                    track_name = meter.get("Name", "health").lower()
                    min_val = meter.get("Min", 0)
                    max_val = meter.get("Max", 5)
                    tracks[track_name] = (min_val, max_val)

                # Extract input fields
                inputs = []
                for input_data in asset_data.get("Inputs", []):
                    inputs.append(input_data.get("Name", ""))

                # Determine if shared
                shared = asset_data.get("Usage", {}).get("Shared", False)

                # Create Asset
                assets[key] = Asset(
                    key=key,
                    name=asset_data.get("Name", key),
                    category=category_name,
                    description=asset_data.get("Asset Type", ""),
                    abilities=abilities,
                    tracks=tracks,
                    inputs=inputs,
                    shared=shared,
                )

    extract_assets(data)
    return assets


def fuzzy_match_asset(query: str, assets: dict[str, Asset]) -> list[Asset]:
    """Find assets matching a partial query string.

    Prioritizes exact matches, then prefix matches, then substring matches.
    """
    q = query.lower().replace(" ", "_").replace("-", "_")

    # Empty query returns no matches
    if not q:
        return []

    exact_matches = []
    prefix_matches = []
    substring_matches = []

    for key, asset in assets.items():
        name_norm = asset.name.lower().replace(" ", "_")

        # Check for exact match first
        if q in (key, name_norm):
            exact_matches.append(asset)
        # Then check for prefix match
        elif key.startswith(q) or name_norm.startswith(q):
            prefix_matches.append(asset)
        # Finally check for substring match
        elif q in key or q in name_norm:
            substring_matches.append(asset)

    # Return in priority order: exact > prefix > substring
    return exact_matches or prefix_matches or substring_matches
