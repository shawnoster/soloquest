"""Tests for the ChosenTruth model, including the note field."""

from wyrd.models.truths import ChosenTruth


class TestChosenTruthNote:
    def test_note_defaults_to_empty_string(self):
        truth = ChosenTruth(category="The Exodus", option_summary="Humanity fled")
        assert truth.note == ""

    def test_note_round_trips_through_dict(self):
        truth = ChosenTruth(
            category="The Exodus",
            option_summary="Humanity fled",
            note="This resonates with my character's backstory.",
        )
        restored = ChosenTruth.from_dict(truth.to_dict())
        assert restored.note == "This resonates with my character's backstory."

    def test_empty_note_round_trips(self):
        truth = ChosenTruth(category="The Exodus", option_summary="Humanity fled")
        restored = ChosenTruth.from_dict(truth.to_dict())
        assert restored.note == ""

    def test_from_dict_missing_note_defaults_to_empty(self):
        """Existing saves without 'note' key should load without error."""
        data = {
            "category": "The Exodus",
            "option_summary": "Humanity fled",
            "option_text": "",
            "custom_text": "",
            "quest_starter": "",
            "subchoice": "",
        }
        truth = ChosenTruth.from_dict(data)
        assert truth.note == ""

    def test_display_text_unaffected_by_note(self):
        """display_text() returns summary+subchoice, note is kept separate."""
        truth = ChosenTruth(
            category="The Exodus",
            option_summary="Humanity fled",
            subchoice="via generation ships",
            note="A personal aside.",
        )
        assert truth.display_text() == "Humanity fled (via generation ships)"

    def test_custom_truth_display_text_unaffected(self):
        truth = ChosenTruth(
            category="Magic",
            option_summary="Custom: no magic",
            custom_text="Custom: no magic",
            note="My campaign is hard sci-fi.",
        )
        assert truth.display_text() == "Custom: no magic"
