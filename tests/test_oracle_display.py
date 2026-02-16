"""Tests for oracle display and command handling.

Tests the visual presentation, command parsing, and Panel-based display
of oracle results.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from soloquest.commands.oracle import handle_oracle
from soloquest.engine.oracles import OracleResult, OracleTable, load_oracles
from soloquest.ui.display import oracle_result_panel, oracle_result_panel_combined

DATA_DIR = Path(__file__).parent.parent / "soloquest" / "data"


class TestOracleDisplay:
    """Test oracle result panel display formatting."""

    def test_oracle_result_panel_creates_colored_panel(self):
        """Oracle results should be displayed in a bright cyan Panel."""
        with patch("soloquest.ui.display.console") as mock_console:
            oracle_result_panel("Action", 42, "Advance")

            # Should have called print with a Panel
            mock_console.print.assert_called_once()
            panel_arg = mock_console.print.call_args[0][0]

            # Verify it's a Panel with correct styling
            assert hasattr(panel_arg, "border_style")
            assert panel_arg.border_style == "bright_cyan"
            assert "ACTION" in str(panel_arg.title)

    def test_oracle_result_shows_roll_and_result(self):
        """Oracle panel should show both the roll number and result text."""
        with patch("soloquest.ui.display.console") as mock_console:
            oracle_result_panel("Theme", 67, "Mystery")

            panel_arg = mock_console.print.call_args[0][0]
            content = str(panel_arg.renderable)

            # Should contain both the roll and the result
            assert "67" in content
            assert "Mystery" in content

    def test_oracle_result_with_long_result_text(self):
        """Oracle results with long text should display correctly."""
        long_result = "A very long oracle result that spans multiple lines and contains detailed information about the narrative outcome"

        with patch("soloquest.ui.display.console") as mock_console:
            oracle_result_panel("Descriptor", 89, long_result)

            # Should not crash
            mock_console.print.assert_called_once()

    def test_oracle_result_with_special_characters(self):
        """Oracle results with special characters should display correctly."""
        result_with_chars = "Test & Result [with] <special> characters!"

        with patch("soloquest.ui.display.console") as mock_console:
            oracle_result_panel("Test", 50, result_with_chars)

            # Should not crash
            mock_console.print.assert_called_once()

    def test_oracle_result_panel_combined_displays_multiple_results(self):
        """Combined oracle panel should display all results in one panel."""
        results = [
            OracleResult(table_name="Action", roll=42, result="Advance"),
            OracleResult(table_name="Theme", roll=67, result="Mystery"),
        ]

        with patch("soloquest.ui.display.console") as mock_console:
            oracle_result_panel_combined(results)

            # Should have called print once with a Panel
            mock_console.print.assert_called_once()
            panel_arg = mock_console.print.call_args[0][0]

            # Verify it's a Panel with correct styling
            assert hasattr(panel_arg, "border_style")
            assert panel_arg.border_style == "bright_cyan"
            assert "ORACLE RESULTS" in str(panel_arg.title)

            # Content should include both results
            content = str(panel_arg.renderable)
            assert "Action" in content
            assert "42" in content
            assert "Advance" in content
            assert "Theme" in content
            assert "67" in content
            assert "Mystery" in content

    def test_oracle_result_panel_combined_with_single_result(self):
        """Combined panel with single result should still work."""
        results = [
            OracleResult(table_name="Action", roll=42, result="Advance"),
        ]

        with patch("soloquest.ui.display.console") as mock_console:
            oracle_result_panel_combined(results)

            # Should not crash
            mock_console.print.assert_called_once()


class TestOracleCommand:
    """Test the /oracle command handler."""

    def setup_method(self):
        self.oracles = load_oracles(DATA_DIR)

    def test_oracle_with_no_args_shows_error(self):
        """Calling /oracle with no args should show usage error."""
        from soloquest.loop import GameState

        mock_state = MagicMock(spec=GameState)
        mock_state.oracles = self.oracles
        mock_state.dice = MagicMock()

        with patch("soloquest.commands.oracle.display.error") as mock_error:
            handle_oracle(mock_state, args=[], flags=set())

            # Should have shown error
            mock_error.assert_called_once()
            error_msg = mock_error.call_args[0][0]
            assert "Usage" in error_msg or "oracle" in error_msg.lower()

    def test_oracle_with_single_table(self):
        """Calling /oracle action should roll on action table."""
        from soloquest.loop import GameState

        mock_state = MagicMock(spec=GameState)
        mock_state.oracles = self.oracles
        mock_state.dice = MagicMock()
        mock_state.session = MagicMock()

        with (
            patch("soloquest.commands.oracle.roll_oracle", return_value=42),
            patch("soloquest.commands.oracle.display.oracle_result_panel"),
        ):
            handle_oracle(mock_state, args=["action"], flags=set())

            # Should have logged the result
            assert mock_state.session.add_oracle.called

    def test_oracle_with_multiple_tables(self):
        """Calling /oracle action theme should roll both tables."""
        from soloquest.loop import GameState

        mock_state = MagicMock(spec=GameState)
        mock_state.oracles = self.oracles
        mock_state.dice = MagicMock()
        mock_state.session = MagicMock()

        with (
            patch("soloquest.commands.oracle.roll_oracle", return_value=42),
            patch("soloquest.commands.oracle.display.oracle_result_panel_combined") as mock_combined,
        ):
            handle_oracle(mock_state, args=["action", "theme"], flags=set())

            # Should have displayed combined results
            mock_combined.assert_called_once()
            # Should have rolled both tables
            assert mock_state.session.add_oracle.call_count >= 2

    def test_oracle_with_nonexistent_table(self):
        """Calling /oracle with non-existent table should show warning."""
        from soloquest.loop import GameState

        mock_state = MagicMock(spec=GameState)
        mock_state.oracles = self.oracles
        mock_state.dice = MagicMock()

        with patch("soloquest.commands.oracle.display.warn") as mock_warn:
            handle_oracle(mock_state, args=["nonexistent_table"], flags=set())

            # Should have shown warning
            mock_warn.assert_called()
            warn_msg = mock_warn.call_args[0][0]
            assert "not found" in warn_msg.lower()

    def test_oracle_with_ambiguous_name(self):
        """Calling /oracle with ambiguous name should handle gracefully."""
        from soloquest.loop import GameState

        mock_state = MagicMock(spec=GameState)
        mock_state.oracles = self.oracles
        mock_state.dice = MagicMock()
        mock_state.session = MagicMock()

        with (
            patch("soloquest.commands.oracle.roll_oracle", return_value=50),
            patch("soloquest.commands.oracle.display"),
        ):
            # "planet" might match multiple tables
            handle_oracle(mock_state, args=["planet"], flags=set())

            # Should have warned about multiple matches or used first match
            # Either way, should not crash


class TestOracleTableEdgeCases:
    """Test edge cases in oracle table lookups."""

    def test_lookup_with_gaps_in_ranges(self):
        """Oracle table with gaps should return Unknown for gap values."""
        table = OracleTable(
            key="gapped",
            name="Gapped Table",
            die="d100",
            results=[
                (1, 40, "Low"),
                # Gap from 41-60
                (61, 100, "High"),
            ],
        )

        assert table.lookup(1) == "Low"
        assert table.lookup(40) == "Low"
        assert table.lookup(50) == "Unknown"  # In the gap
        assert table.lookup(61) == "High"

    def test_lookup_with_single_result(self):
        """Oracle table with single result should work."""
        table = OracleTable(
            key="single",
            name="Single",
            die="d100",
            results=[(1, 100, "Only Result")],
        )

        assert table.lookup(1) == "Only Result"
        assert table.lookup(50) == "Only Result"
        assert table.lookup(100) == "Only Result"

    def test_lookup_with_narrow_ranges(self):
        """Oracle table with narrow ranges (1-2, 3-4, etc.) should work."""
        table = OracleTable(
            key="narrow",
            name="Narrow",
            die="d100",
            results=[
                (1, 1, "One"),
                (2, 2, "Two"),
                (3, 3, "Three"),
            ],
        )

        assert table.lookup(1) == "One"
        assert table.lookup(2) == "Two"
        assert table.lookup(3) == "Three"
        assert table.lookup(4) == "Unknown"

    def test_lookup_with_out_of_range_values(self):
        """Oracle lookup with values outside table range should return Unknown."""
        table = OracleTable(
            key="test",
            name="Test",
            die="d100",
            results=[(1, 100, "Result")],
        )

        assert table.lookup(0) == "Unknown"
        assert table.lookup(-1) == "Unknown"
        assert table.lookup(101) == "Unknown"
        assert table.lookup(1000) == "Unknown"

    def test_lookup_with_empty_results(self):
        """Oracle table with no results should always return Unknown."""
        table = OracleTable(
            key="empty",
            name="Empty",
            die="d100",
            results=[],
        )

        assert table.lookup(1) == "Unknown"
        assert table.lookup(50) == "Unknown"
        assert table.lookup(100) == "Unknown"

    def test_oracle_table_is_immutable(self):
        """Oracle tables should be frozen dataclasses."""
        table = OracleTable(
            key="test",
            name="Test",
            die="d100",
            results=[(1, 100, "Result")],
        )

        # Should not be able to modify
        try:
            table.key = "modified"
            raise AssertionError("Should not be able to modify frozen dataclass")
        except AttributeError:
            pass  # Expected


class TestOracleDataQuality:
    """Test the quality of oracle data loaded from dataforged."""

    def setup_method(self):
        self.oracles = load_oracles(DATA_DIR)

    def test_loads_minimum_number_of_oracles(self):
        """Should load at least 90 oracles from dataforged + TOML."""
        assert len(self.oracles) >= 90

    def test_all_oracles_have_required_fields(self):
        """All oracles should have key, name, die, and results."""
        for key, oracle in self.oracles.items():
            assert oracle.key == key
            assert oracle.name
            assert oracle.die
            assert isinstance(oracle.results, list)

    def test_all_oracle_names_are_non_empty(self):
        """All oracles should have non-empty names."""
        for oracle in self.oracles.values():
            assert oracle.name
            assert len(oracle.name.strip()) > 0

    def test_no_duplicate_oracle_keys(self):
        """Oracle keys should be unique."""
        keys = list(self.oracles.keys())
        assert len(keys) == len(set(keys))

    def test_oracle_results_have_valid_structure(self):
        """All oracle results should have (low, high, text) tuples."""
        for oracle in self.oracles.values():
            for result in oracle.results:
                assert isinstance(result, tuple)
                assert len(result) == 3
                low, high, text = result
                assert isinstance(low, int)
                assert isinstance(high, int)
                assert isinstance(text, str)

    def test_oracle_ranges_are_valid(self):
        """All oracle ranges should have low <= high."""
        for oracle in self.oracles.values():
            for low, high, _ in oracle.results:
                assert low <= high, f"Invalid range in {oracle.key}: {low}-{high}"

    def test_oracle_ranges_are_positive(self):
        """All oracle ranges should have positive bounds."""
        for oracle in self.oracles.values():
            for low, high, _ in oracle.results:
                assert low > 0, f"Non-positive low bound in {oracle.key}: {low}"
                assert high > 0, f"Non-positive high bound in {oracle.key}: {high}"

    def test_d100_oracles_cover_full_range(self):
        """All d100 oracles should cover 1-100 (allowing gaps is OK)."""
        for key, oracle in self.oracles.items():
            if oracle.die == "d100":
                # Check that 1 and 100 are covered
                result_1 = oracle.lookup(1)
                result_100 = oracle.lookup(100)

                # Both should return something (not Unknown)
                assert result_1 != "Unknown", f"{key}: doesn't cover 1"
                assert result_100 != "Unknown", f"{key}: doesn't cover 100"

    def test_oracle_results_have_non_empty_text(self):
        """All oracle results should have non-empty text."""
        for oracle in self.oracles.values():
            for _, _, text in oracle.results:
                assert text
                assert len(text.strip()) > 0


class TestOracleRangeCoverage:
    """Test that oracle ranges have proper coverage."""

    def test_detect_overlapping_ranges(self):
        """Should be able to detect if oracle ranges overlap."""
        table = OracleTable(
            key="test",
            name="Test",
            die="d100",
            results=[
                (1, 50, "Low"),
                (45, 100, "High"),  # Overlaps with previous!
            ],
        )

        # Both should match for 45-50
        assert table.lookup(45) in ("Low", "High")
        assert table.lookup(50) in ("Low", "High")

    def test_calculate_coverage_percentage(self):
        """Should be able to calculate what percentage of range is covered."""

        def coverage_percentage(table: OracleTable, max_roll: int = 100) -> float:
            """Calculate what percentage of 1-max_roll is covered by results."""
            covered = set()
            for low, high, _ in table.results:
                covered.update(range(low, high + 1))

            # Intersect with valid range
            valid_range = set(range(1, max_roll + 1))
            covered_in_range = covered.intersection(valid_range)

            return (len(covered_in_range) / max_roll) * 100

        # Full coverage
        full_table = OracleTable(
            key="full",
            name="Full",
            die="d100",
            results=[(1, 100, "Result")],
        )
        assert coverage_percentage(full_table) == 100.0

        # Partial coverage
        partial_table = OracleTable(
            key="partial",
            name="Partial",
            die="d100",
            results=[(1, 50, "Half")],
        )
        assert coverage_percentage(partial_table) == 50.0

    def test_oracles_have_good_coverage(self):
        """Most oracles should have >90% coverage of their range."""
        oracles = load_oracles(DATA_DIR)

        poor_coverage = []
        for key, oracle in oracles.items():
            if oracle.die != "d100":
                continue

            # Check coverage
            covered = set()
            for low, high, _ in oracle.results:
                covered.update(range(low, high + 1))

            valid_range = set(range(1, 101))
            coverage = len(covered.intersection(valid_range)) / 100

            if coverage < 0.9:  # Less than 90% coverage
                poor_coverage.append((key, coverage))

        # Most oracles should have good coverage
        # Allow some flexibility for specialized tables
        assert len(poor_coverage) < len(oracles) * 0.1, (
            f"Too many oracles with poor coverage: {poor_coverage}"
        )


class TestOraclePerformance:
    """Test oracle lookup performance."""

    def setup_method(self):
        self.oracles = load_oracles(DATA_DIR)

    def test_oracle_lookup_is_fast(self):
        """Oracle lookups should be very fast."""
        import time

        # Get a table
        action_table = self.oracles.get("action")
        if not action_table:
            return

        start = time.time()
        for i in range(10000):
            _ = action_table.lookup(i % 100 + 1)
        elapsed = time.time() - start

        # 10,000 lookups should be very fast (< 0.1s)
        assert elapsed < 0.1

    def test_fuzzy_match_is_fast(self):
        """Fuzzy matching should complete quickly."""
        import time

        from soloquest.engine.oracles import fuzzy_match_oracle

        start = time.time()
        for query in ["action", "theme", "planet", "character", "location"]:
            fuzzy_match_oracle(query, self.oracles)
        elapsed = time.time() - start

        # Should be fast (< 0.5s for multiple searches)
        assert elapsed < 0.5
