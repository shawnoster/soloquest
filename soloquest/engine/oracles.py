"""Oracle table loading and lookup."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


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
    results: list[tuple[int, int, str]]  # (low, high, text)

    def lookup(self, roll: int) -> str:
        for low, high, text in self.results:
            if low <= roll <= high:
                return text
        return "Unknown"


def load_oracles(data_dir: Path) -> dict[str, OracleTable]:
    """Load all oracle tables from oracles.toml."""
    path = data_dir / "oracles.toml"
    with path.open("rb") as f:
        raw = tomllib.load(f)

    tables: dict[str, OracleTable] = {}
    for key, data in raw.items():
        results = [(int(r[0]), int(r[1]), str(r[2])) for r in data["results"]]
        tables[key] = OracleTable(
            key=key,
            name=data["name"],
            die=data["die"],
            results=results,
        )
    return tables


def fuzzy_match_oracle(query: str, tables: dict[str, OracleTable]) -> list[OracleTable]:
    """Find oracle tables matching a partial query string."""
    q = query.lower().replace(" ", "_").replace("-", "_")
    matches = []
    for key, table in tables.items():
        name_norm = table.name.lower().replace(" ", "_")
        if q in key or q in name_norm:
            matches.append(table)
    return matches
