"""Tests for the truths markdown serializer / deserializer."""

from __future__ import annotations

from pathlib import Path

import pytest

from soloquest.models.truths import ChosenTruth
from soloquest.state.truths_md import (
    read_adventure_truths,
    read_truths_md,
    truths_from_markdown,
    truths_md_path,
    truths_to_markdown,
    write_adventure_truths,
    write_truths_md,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def standard_truth() -> ChosenTruth:
    return ChosenTruth(
        category="The Cataclysm",
        option_summary="Promises of a new age",
        option_text="The galaxy is scarred by the Sundering.",
        quest_starter="Some believe they know the true cause.",
        subchoice="The cities of bone",
        note="This resonates with Kira.",
    )


@pytest.fixture
def custom_truth() -> ChosenTruth:
    return ChosenTruth(
        category="Exodus",
        option_summary="They were driven out.",
        custom_text="They were driven out.",
        note="",
    )


@pytest.fixture
def minimal_truth() -> ChosenTruth:
    return ChosenTruth(
        category="Magic",
        option_summary="Magic does not exist",
    )


# ── truths_md_path ───────────────────────────────────────────────────────────


class TestTruthsMdPath:
    def test_replaces_json_extension(self, tmp_path: Path) -> None:
        save = tmp_path / "kira.json"
        assert truths_md_path(save) == tmp_path / "kira.truths.md"

    def test_works_with_campaign_player_path(self, tmp_path: Path) -> None:
        save = tmp_path / "players" / "kira.json"
        assert truths_md_path(save) == tmp_path / "players" / "kira.truths.md"


# ── truths_to_markdown ───────────────────────────────────────────────────────


class TestTruthsToMarkdown:
    def test_includes_character_name_in_header(self, standard_truth: ChosenTruth) -> None:
        md = truths_to_markdown([standard_truth], "Kira")
        assert md.startswith("# Campaign Truths — Kira")

    def test_header_without_name(self, standard_truth: ChosenTruth) -> None:
        md = truths_to_markdown([standard_truth])
        assert md.startswith("# Campaign Truths\n")

    def test_standard_truth_fields(self, standard_truth: ChosenTruth) -> None:
        md = truths_to_markdown([standard_truth])
        assert "## The Cataclysm — Promises of a new age" in md
        assert "**Choice:**" not in md
        assert "### Detail" not in md
        assert "The galaxy is scarred by the Sundering." in md
        assert "### Quest Starter" in md
        assert "Some believe they know the true cause." in md
        assert "- **Subchoice:** The cities of bone" in md
        assert "### Notes" in md
        assert "- This resonates with Kira." in md
        assert "- **Note:**" not in md

    def test_custom_truth_uses_custom_tag(self, custom_truth: ChosenTruth) -> None:
        md = truths_to_markdown([custom_truth])
        assert "## Exodus — They were driven out." in md
        assert "**Custom**" in md
        assert "**Choice:**" not in md

    def test_notes_section_always_written(self, minimal_truth: ChosenTruth) -> None:
        md = truths_to_markdown([minimal_truth])
        assert "### Notes" in md

    def test_subchoice_omitted_when_empty(self, minimal_truth: ChosenTruth) -> None:
        md = truths_to_markdown([minimal_truth])
        assert "**Subchoice:**" not in md

    def test_detail_omitted_when_empty(self, minimal_truth: ChosenTruth) -> None:
        md = truths_to_markdown([minimal_truth])
        assert "**Detail:**" not in md

    def test_sections_separated_by_hr(
        self, standard_truth: ChosenTruth, custom_truth: ChosenTruth
    ) -> None:
        md = truths_to_markdown([standard_truth, custom_truth])
        assert "---" in md

    def test_multiple_truths_all_present(
        self, standard_truth: ChosenTruth, custom_truth: ChosenTruth
    ) -> None:
        md = truths_to_markdown([standard_truth, custom_truth])
        assert "## The Cataclysm" in md
        assert "## Exodus" in md


# ── truths_from_markdown ─────────────────────────────────────────────────────


class TestTruthsFromMarkdown:
    def test_roundtrip_standard_truth(self, standard_truth: ChosenTruth) -> None:
        md = truths_to_markdown([standard_truth])
        result = truths_from_markdown(md)
        assert result is not None
        assert len(result) == 1
        t = result[0]
        assert t.category == "The Cataclysm"
        assert t.option_summary == "Promises of a new age"
        assert t.option_text == "The galaxy is scarred by the Sundering."
        assert t.quest_starter == "Some believe they know the true cause."
        assert t.subchoice == "The cities of bone"
        assert t.note == "This resonates with Kira."
        assert t.custom_text == ""

    def test_roundtrip_custom_truth(self, custom_truth: ChosenTruth) -> None:
        md = truths_to_markdown([custom_truth])
        result = truths_from_markdown(md)
        assert result is not None
        t = result[0]
        assert t.category == "Exodus"
        assert t.custom_text == "They were driven out."
        assert t.option_summary == "They were driven out."

    def test_roundtrip_multiple_truths(
        self, standard_truth: ChosenTruth, custom_truth: ChosenTruth, minimal_truth: ChosenTruth
    ) -> None:
        md = truths_to_markdown([standard_truth, custom_truth, minimal_truth])
        result = truths_from_markdown(md)
        assert result is not None
        assert len(result) == 3
        assert result[0].category == "The Cataclysm"
        assert result[1].category == "Exodus"
        assert result[2].category == "Magic"

    def test_returns_none_for_empty_string(self) -> None:
        assert truths_from_markdown("") is None

    def test_returns_none_for_header_only(self) -> None:
        assert truths_from_markdown("# Campaign Truths\n") is None

    def test_preserves_blank_note(self, minimal_truth: ChosenTruth) -> None:
        md = truths_to_markdown([minimal_truth])
        result = truths_from_markdown(md)
        assert result is not None
        assert result[0].note == ""

    def test_hand_edited_note_is_picked_up(self, minimal_truth: ChosenTruth) -> None:
        md = truths_to_markdown([minimal_truth])
        md = md.replace("### Notes\n\n", "### Notes\n\n- Hand-written note here.\n")
        result = truths_from_markdown(md)
        assert result is not None
        assert result[0].note == "Hand-written note here."

    def test_multiple_note_bullets_joined(self, minimal_truth: ChosenTruth) -> None:
        md = truths_to_markdown([minimal_truth])
        md = md.replace("### Notes\n\n", "### Notes\n\n- First note.\n- Second note.\n")
        result = truths_from_markdown(md)
        assert result is not None
        assert result[0].note == "First note.\nSecond note."

    def test_hand_edited_custom_text(self) -> None:
        md = "# Campaign Truths\n\n## Exodus\n\n**Custom:** Original text.\n**Note:**\n\n---\n"
        md = md.replace("Original text.", "Edited text.")
        result = truths_from_markdown(md)
        assert result is not None
        assert result[0].custom_text == "Edited text."
        assert result[0].option_summary == "Edited text."


# ── write / read helpers ─────────────────────────────────────────────────────


class TestWriteReadHelpers:
    def test_write_creates_file(self, tmp_path: Path, standard_truth: ChosenTruth) -> None:
        save_path = tmp_path / "kira.json"
        write_truths_md([standard_truth], save_path, "Kira")
        md_path = tmp_path / "kira.truths.md"
        assert md_path.exists()

    def test_read_returns_none_when_file_missing(self, tmp_path: Path) -> None:
        assert read_truths_md(tmp_path / "ghost.json") is None

    def test_roundtrip_via_file(self, tmp_path: Path, standard_truth: ChosenTruth) -> None:
        save_path = tmp_path / "kira.json"
        write_truths_md([standard_truth], save_path, "Kira")
        result = read_truths_md(save_path)
        assert result is not None
        assert result[0].category == "The Cataclysm"
        assert result[0].option_summary == "Promises of a new age"

    def test_read_returns_none_for_corrupt_file(self, tmp_path: Path) -> None:
        save_path = tmp_path / "kira.json"
        md_path = tmp_path / "kira.truths.md"
        md_path.write_text("# Campaign Truths\n", encoding="utf-8")
        assert read_truths_md(save_path) is None


# ── Integration with save/load ────────────────────────────────────────────────


class TestSaveLoadIntegration:
    """Verify adventure-level truths markdown is written and read."""

    def test_write_adventure_truths_creates_file(self, tmp_path: Path) -> None:

        truths = [
            ChosenTruth(
                category="The Cataclysm",
                option_summary="Promises of a new age",
                note="Test note",
            )
        ]
        write_adventure_truths(truths, tmp_path, "Kira")

        md_path = tmp_path / "truths.md"
        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "## The Cataclysm" in content
        assert "### Notes" in content
        assert "- Test note" in content

    def test_read_adventure_truths_roundtrip(self, tmp_path: Path) -> None:

        truths = [ChosenTruth(category="The Cataclysm", option_summary="Original summary")]
        write_adventure_truths(truths, tmp_path, "Kira")

        md_path = tmp_path / "truths.md"
        content = md_path.read_text(encoding="utf-8")
        content = content.replace("Original summary", "Edited summary")
        md_path.write_text(content, encoding="utf-8")

        loaded = read_adventure_truths(tmp_path)
        assert loaded is not None
        assert loaded[0].option_summary == "Edited summary"

    def test_save_game_no_longer_writes_character_truths_md(self, tmp_path: Path) -> None:
        """save_game should not write a character-level .truths.md any more."""
        import unittest.mock as mock

        from soloquest.engine.dice import DiceMode
        from soloquest.models.character import Character
        from soloquest.state import save as save_module
        from soloquest.state.save import save_game

        char = Character(name="Kira")
        saves_dir = tmp_path / "saves"

        with mock.patch.object(save_module, "_saves_dir", return_value=saves_dir):
            save_game(char, [], 1, DiceMode.DIGITAL)

        assert not (saves_dir / "kira.truths.md").exists()
