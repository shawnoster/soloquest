"""Tests for the save/load system."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from starforged.engine.dice import DiceMode
from starforged.models.character import Character, Stats
from starforged.models.vow import Vow, VowRank
from starforged.state import save as save_module
from starforged.state.save import autosave, load_game, save_game


@pytest.fixture
def tmp_saves(tmp_path, monkeypatch):
    """Redirect saves to a temp directory."""
    tmp_saves_dir = tmp_path / "saves"
    # Monkeypatch where the function is used, not where it's defined
    monkeypatch.setattr(save_module, "_saves_dir", lambda: tmp_saves_dir)
    return tmp_saves_dir


@pytest.fixture
def sample_character():
    return Character(
        name="Kael Morrow",
        homeworld="Drift Station",
        stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3),
        health=4,
        spirit=3,
        supply=2,
        momentum=5,
    )


@pytest.fixture
def sample_vows():
    return [
        Vow("Find the Andurath survivors", VowRank.FORMIDABLE, ticks=8),
        Vow("Pay debt to Erebus", VowRank.TROUBLESOME),
    ]


class TestSaveGame:
    def test_creates_save_file(self, tmp_saves, sample_character, sample_vows):
        path = save_game(sample_character, sample_vows, 3, DiceMode.DIGITAL)
        assert path.exists()

    def test_save_file_has_correct_character_name(self, tmp_saves, sample_character, sample_vows):
        path = save_game(sample_character, sample_vows, 3, DiceMode.DIGITAL)
        data = json.loads(path.read_text())
        assert data["character"]["name"] == "Kael Morrow"

    def test_save_persists_session_count(self, tmp_saves, sample_character, sample_vows):
        save_game(sample_character, sample_vows, 7, DiceMode.DIGITAL)
        path = tmp_saves / "kael_morrow.json"
        data = json.loads(path.read_text())
        assert data["session_count"] == 7

    def test_save_persists_dice_mode(self, tmp_saves, sample_character, sample_vows):
        save_game(sample_character, sample_vows, 1, DiceMode.PHYSICAL)
        path = tmp_saves / "kael_morrow.json"
        data = json.loads(path.read_text())
        assert data["settings"]["dice_mode"] == "physical"

    def test_save_persists_vows(self, tmp_saves, sample_character, sample_vows):
        save_game(sample_character, sample_vows, 1, DiceMode.DIGITAL)
        path = tmp_saves / "kael_morrow.json"
        data = json.loads(path.read_text())
        assert len(data["vows"]) == 2
        assert data["vows"][0]["description"] == "Find the Andurath survivors"

    def test_save_persists_debilities(self, tmp_saves, sample_vows):
        char = Character(name="Test Char", stats=Stats())
        char.toggle_debility("wounded")
        char.toggle_debility("shaken")
        save_game(char, sample_vows, 1, DiceMode.DIGITAL)
        path = tmp_saves / "test_char.json"
        data = json.loads(path.read_text())
        assert "wounded" in data["character"]["debilities"]
        assert "shaken" in data["character"]["debilities"]


class TestLoadGame:
    def test_roundtrip(self, tmp_saves, sample_character, sample_vows):
        save_game(sample_character, sample_vows, 5, DiceMode.MIXED)
        char, vows, count, mode = load_game("Kael Morrow")
        assert char.name == "Kael Morrow"
        assert char.health == 4
        assert char.momentum == 5
        assert count == 5
        assert mode == DiceMode.MIXED

    def test_vow_progress_survives_roundtrip(self, tmp_saves, sample_character, sample_vows):
        save_game(sample_character, sample_vows, 1, DiceMode.DIGITAL)
        _, vows, _, _ = load_game("Kael Morrow")
        assert vows[0].ticks == 8

    def test_debilities_survive_roundtrip(self, tmp_saves, sample_vows):
        char = Character(name="Test Char", stats=Stats())
        char.toggle_debility("corrupted")
        save_game(char, sample_vows, 1, DiceMode.DIGITAL)
        restored, _, _, _ = load_game("Test Char")
        assert "corrupted" in restored.debilities
        assert restored.momentum_max == 9  # 10 - 1

    def test_momentum_max_computed_not_stored(self, tmp_saves, sample_character, sample_vows):
        """momentum_max should be computed from debilities, not read from JSON."""
        save_game(sample_character, sample_vows, 1, DiceMode.DIGITAL)
        path = tmp_saves / "kael_morrow.json"
        data = json.loads(path.read_text())
        # Should not be stored as a field
        assert "momentum_max" not in data["character"]
        assert "momentum_reset" not in data["character"]


class TestAutosave:
    def test_autosave_writes_file(self, tmp_saves, sample_character, sample_vows):
        autosave(sample_character, sample_vows, 2, DiceMode.DIGITAL)
        path = tmp_saves / "kael_morrow.json"
        assert path.exists()

    def test_autosave_does_not_raise_on_error(self, tmp_saves, sample_character, sample_vows):
        """Autosave must never crash the caller."""
        with patch("starforged.state.save.save_game", side_effect=OSError("disk full")):
            # Should not raise
            autosave(sample_character, sample_vows, 1, DiceMode.DIGITAL)
