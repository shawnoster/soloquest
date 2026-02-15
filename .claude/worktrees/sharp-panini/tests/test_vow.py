"""Tests for the Vow model."""

from starforged.models.vow import MAX_TICKS, Vow, VowRank, fuzzy_match_vow


class TestVow:
    def test_troublesome_marks_12_ticks(self):
        vow = Vow(description="test", rank=VowRank.TROUBLESOME)
        vow.mark_progress()
        assert vow.ticks == 12

    def test_epic_marks_1_tick(self):
        vow = Vow(description="test", rank=VowRank.EPIC)
        vow.mark_progress()
        assert vow.ticks == 1

    def test_progress_score_is_boxes(self):
        vow = Vow(description="test", rank=VowRank.FORMIDABLE)
        vow.ticks = 16  # 4 boxes
        assert vow.progress_score == 4

    def test_progress_score_capped_at_10(self):
        vow = Vow(description="test", rank=VowRank.TROUBLESOME)
        vow.ticks = MAX_TICKS
        assert vow.progress_score == 10

    def test_ticks_capped_at_max(self):
        vow = Vow(description="test", rank=VowRank.TROUBLESOME, ticks=36)
        vow.mark_progress()  # would add 12 → 48, should cap at 40
        assert vow.ticks == MAX_TICKS

    def test_boxes_filled(self):
        vow = Vow(description="test", rank=VowRank.DANGEROUS)
        vow.ticks = 10  # 2 full boxes + 2 partial ticks
        assert vow.boxes_filled == 2
        assert vow.partial_ticks == 2

    def test_serialization_roundtrip(self):
        vow = Vow(description="Find the Andurath survivors", rank=VowRank.FORMIDABLE, ticks=8)
        data = vow.to_dict()
        restored = Vow.from_dict(data)
        assert restored.description == vow.description
        assert restored.rank == vow.rank
        assert restored.ticks == vow.ticks


class TestFuzzyMatchVow:
    def setup_method(self):
        self.vows = [
            Vow("Find the Andurath survivors", VowRank.FORMIDABLE),
            Vow("Pay my debt to Station Erebus", VowRank.TROUBLESOME),
            Vow("Discover the origin of the signal", VowRank.DANGEROUS),
        ]

    def test_partial_match(self):
        results = fuzzy_match_vow("andurath", self.vows)
        assert len(results) == 1
        assert results[0].description == "Find the Andurath survivors"

    def test_no_match(self):
        results = fuzzy_match_vow("zzzzz", self.vows)
        assert results == []

    def test_case_insensitive(self):
        results = fuzzy_match_vow("SIGNAL", self.vows)
        assert len(results) == 1
