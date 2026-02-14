"""Tests for oracle table loading and lookup."""

from pathlib import Path

from soloquest.engine.oracles import OracleTable, fuzzy_match_oracle, load_oracles

DATA_DIR = Path(__file__).parent.parent / "soloquest" / "data"


class TestOracleTable:
    def setup_method(self):
        self.table = OracleTable(
            key="test",
            name="Test Table",
            die="d100",
            results=[
                (1, 25, "Alpha"),
                (26, 50, "Beta"),
                (51, 75, "Gamma"),
                (76, 100, "Delta"),
            ],
        )

    def test_lookup_first_range(self):
        assert self.table.lookup(1) == "Alpha"
        assert self.table.lookup(25) == "Alpha"

    def test_lookup_middle_range(self):
        assert self.table.lookup(26) == "Beta"
        assert self.table.lookup(50) == "Beta"

    def test_lookup_boundary(self):
        assert self.table.lookup(76) == "Delta"
        assert self.table.lookup(100) == "Delta"

    def test_lookup_unknown(self):
        assert self.table.lookup(0) == "Unknown"


class TestLoadOracles:
    def test_loads_from_toml(self):
        tables = load_oracles(DATA_DIR)
        assert "action" in tables
        assert "theme" in tables
        assert "planet_class" in tables

    def test_action_table_has_results(self):
        tables = load_oracles(DATA_DIR)
        table = tables["action"]
        assert len(table.results) > 0

    def test_all_tables_cover_1_to_100(self):
        tables = load_oracles(DATA_DIR)
        for key, table in tables.items():
            if table.die == "d100":
                assert table.lookup(1) != "Unknown", f"{key}: no result for 1"
                assert table.lookup(100) != "Unknown", f"{key}: no result for 100"


class TestFuzzyMatchOracle:
    def setup_method(self):
        self.tables = load_oracles(DATA_DIR)

    def test_exact_key_match(self):
        results = fuzzy_match_oracle("action", self.tables)
        assert any(t.key == "action" for t in results)

    def test_partial_name_match(self):
        results = fuzzy_match_oracle("planet", self.tables)
        assert any("planet" in t.key for t in results)

    def test_no_match_returns_empty(self):
        results = fuzzy_match_oracle("xyznotreal", self.tables)
        assert results == []
