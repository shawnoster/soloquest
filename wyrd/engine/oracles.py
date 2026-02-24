"""Oracle table loading and lookup."""

from __future__ import annotations

import json
import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OracleCategory:
    name: str
    keys: tuple[str, ...]


@dataclass(frozen=True)
class OracleInspiration:
    label: str
    cmd: str


def _load_category(data: dict) -> OracleCategory | None:
    name = data.get("name")
    keys = data.get("keys")
    if not isinstance(name, str):
        logger.warning("Skipping category with missing/invalid 'name': %s", data)
        return None
    if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
        logger.warning("Skipping category with missing/invalid 'keys': %s", data)
        return None
    return OracleCategory(name=name, keys=tuple(keys))


def _load_inspiration(data: dict) -> OracleInspiration | None:
    label = data.get("label")
    cmd = data.get("cmd")
    if not isinstance(label, str):
        logger.warning("Skipping inspiration with missing/invalid 'label': %s", data)
        return None
    if not isinstance(cmd, str):
        logger.warning("Skipping inspiration with missing/invalid 'cmd': %s", data)
        return None
    return OracleInspiration(label=label, cmd=cmd)


def load_oracle_display(data_dir: Path) -> tuple[list[OracleCategory], list[OracleInspiration]]:
    """Load oracle display config (categories and inspirations) from oracles.toml."""
    toml_path = data_dir / "oracles.toml"
    if not toml_path.exists():
        return [], []
    with toml_path.open("rb") as f:
        raw = tomllib.load(f)
    display = raw.get("display", {})
    categories = [
        c for c in (_load_category(cat) for cat in display.get("categories", [])) if c is not None
    ]
    inspirations = [
        i
        for i in (_load_inspiration(ins) for ins in display.get("inspirations", []))
        if i is not None
    ]
    return categories, inspirations


@dataclass(frozen=True)
class OracleResult:
    table_name: str
    roll: int
    result: str


@dataclass(frozen=True)
class OracleTable:
    key: str
    name: str
    die: str
    results: list[tuple[int, int, str]]

    def lookup(self, roll: int) -> str:
        for low, high, text in self.results:
            if low <= roll <= high:
                return text
        return "Unknown"


def load_dataforged_oracles(data_dir: Path) -> dict[str, OracleTable]:
    """Load oracle tables from dataforged JSON files."""
    path = data_dir / "dataforged" / "oracles.json"
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    tables: dict[str, OracleTable] = {}

    # Recursively extract oracles from nested structure
    def extract_oracles(item: dict | list, parent_prefix: str = "") -> None:
        if isinstance(item, list):
            for sub_item in item:
                extract_oracles(sub_item, parent_prefix)
        elif isinstance(item, dict):
            # If this has a "Table" key, it's an oracle
            if "Table" in item and "$id" in item:
                oracle_id = item["$id"]
                # Create a simplified key from the ID
                key_parts = oracle_id.split("/")
                # Use last part as key, make it lowercase with underscores
                key = key_parts[-1].lower().replace(" ", "_").replace("-", "_")

                # Extract table rows
                results = []
                for row in item["Table"]:
                    floor = row.get("Floor", row.get("Chance", {}).get("Min", 1))
                    ceiling = row.get("Ceiling", row.get("Chance", {}).get("Max", 100))
                    result = row.get("Result", "")
                    # Skip if floor/ceiling are None or result is empty
                    if result and floor is not None and ceiling is not None:
                        results.append((floor, ceiling, result))

                if results:  # Only add if there are valid results
                    tables[key] = OracleTable(
                        key=key,
                        name=item.get("Name", key),
                        die="d100",  # Dataforged typically uses d100
                        results=results,
                    )

            # Recurse into nested oracles
            if "Oracles" in item:
                extract_oracles(item["Oracles"], parent_prefix)

    extract_oracles(data)
    return tables


def load_oracles(data_dir: Path) -> dict[str, OracleTable]:
    """Load all oracle tables from both TOML and dataforged JSON.

    TOML tables take priority over JSON to allow custom overrides.
    """
    # Start with dataforged data
    tables = load_dataforged_oracles(data_dir)

    # Load and overlay TOML (custom/override)
    toml_path = data_dir / "oracles.toml"
    if toml_path.exists():
        with toml_path.open("rb") as f:
            raw = tomllib.load(f)

        for key, data in raw.items():
            # Skip non-oracle-table sections (e.g. [display])
            if not isinstance(data, dict) or "results" not in data:
                continue
            results = [(int(r[0]), int(r[1]), str(r[2])) for r in data["results"]]
            tables[key] = OracleTable(
                key=key,
                name=data["name"],
                die=data["die"],
                results=results,
            )

    return tables


def fuzzy_match_oracle(query: str, tables: dict[str, OracleTable]) -> list[OracleTable]:
    """Find oracle tables matching a partial query string.

    Prioritizes exact matches, then prefix matches, then substring matches.
    """
    q = query.lower().replace(" ", "_").replace("-", "_")

    # Empty query returns no matches
    if not q:
        return []

    exact_matches = []
    prefix_matches = []
    substring_matches = []

    for key, table in tables.items():
        name_norm = table.name.lower().replace(" ", "_")

        # Check for exact match first
        if q in (key, name_norm):
            exact_matches.append(table)
        # Then check for prefix match
        elif key.startswith(q) or name_norm.startswith(q):
            prefix_matches.append(table)
        # Finally check for substring match
        elif q in key or q in name_norm:
            substring_matches.append(table)

    # Return in priority order: exact > prefix > substring
    return exact_matches or prefix_matches or substring_matches
