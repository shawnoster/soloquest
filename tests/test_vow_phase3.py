"""Tests for Phase 3 vow additions — SPIRIT_COST, forsake."""

from __future__ import annotations

from soloquest.models.vow import SPIRIT_COST, Vow, VowRank


class TestSpiritCost:
    def test_troublesome_costs_1(self):
        assert SPIRIT_COST[VowRank.TROUBLESOME] == 1

    def test_dangerous_costs_2(self):
        assert SPIRIT_COST[VowRank.DANGEROUS] == 2

    def test_formidable_costs_3(self):
        assert SPIRIT_COST[VowRank.FORMIDABLE] == 3

    def test_extreme_costs_4(self):
        assert SPIRIT_COST[VowRank.EXTREME] == 4

    def test_epic_costs_5(self):
        assert SPIRIT_COST[VowRank.EPIC] == 5

    def test_all_ranks_have_cost(self):
        for rank in VowRank:
            assert rank in SPIRIT_COST, f"{rank} missing from SPIRIT_COST"


class TestVowFulfillment:
    def test_vow_fulfilled_flag(self):
        vow = Vow("Find the signal", VowRank.DANGEROUS)
        assert vow.fulfilled is False
        vow.fulfilled = True
        assert vow.fulfilled is True

    def test_fulfilled_vow_serialization(self):
        vow = Vow("Find the signal", VowRank.DANGEROUS, fulfilled=True)
        data = vow.to_dict()
        restored = Vow.from_dict(data)
        assert restored.fulfilled is True

    def test_progress_score_at_max(self):
        from soloquest.models.vow import MAX_TICKS

        vow = Vow("Epic quest", VowRank.EPIC, ticks=MAX_TICKS)
        assert vow.progress_score == 10
