"""Truth category loading and lookup for campaign setup."""

from __future__ import annotations

import tomllib
from pathlib import Path

from soloquest.models.truths import TruthCategory, TruthOption


def load_truth_categories(data_dir: Path) -> dict[str, TruthCategory]:
    """Load truth categories from TOML file.

    Returns a dictionary mapping category names to TruthCategory objects.
    Categories are loaded from soloquest/data/truths.toml.
    """
    path = data_dir / "truths.toml"
    if not path.exists():
        return {}

    with path.open("rb") as f:
        data = tomllib.load(f)

    categories: dict[str, TruthCategory] = {}

    for truth_data in data.get("truth", []):
        name = truth_data["name"]
        description = truth_data["description"]
        order = truth_data.get("order", 0)

        # Use comprehension for options
        options = [
            TruthOption(
                roll_range=tuple(opt_data["roll_range"]),
                summary=opt_data["summary"],
                text=opt_data["text"],
                quest_starter=opt_data.get("quest_starter", ""),
                subchoices=opt_data.get("subchoices", []),
            )
            for opt_data in truth_data.get("option", [])
        ]

        category = TruthCategory(name=name, description=description, order=order, options=options)
        categories[name] = category

    return categories


def get_truth_category(categories: dict[str, TruthCategory], name: str) -> TruthCategory | None:
    """Get a specific truth category by name (case-insensitive)."""
    name_lower = name.lower()
    return next(
        (category for cat_name, category in categories.items() if cat_name.lower() == name_lower),
        None,
    )


def get_ordered_categories(categories: dict[str, TruthCategory]) -> list[TruthCategory]:
    """Get truth categories sorted by their order field."""
    return sorted(categories.values(), key=lambda c: c.order)
