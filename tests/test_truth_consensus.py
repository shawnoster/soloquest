"""Tests for co-op truth consensus (/truths propose, review, accept, counter)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from soloquest.models.campaign import CampaignState, TruthProposal
from soloquest.models.session import Session
from soloquest.models.truths import ChosenTruth, TruthCategory, TruthOption
from soloquest.sync import LocalAdapter


def _make_truth_category(name: str = "Cataclysm") -> TruthCategory:
    return TruthCategory(
        name=name,
        description="What ended the old world?",
        order=1,
        options=[
            TruthOption(roll_range=(1, 33), summary="The Sun Plague", text="Stars dimmed."),
            TruthOption(roll_range=(34, 66), summary="The Iron Blight", text="Machines turned."),
            TruthOption(roll_range=(67, 100), summary="The Exodus War", text="Humanity fled."),
        ],
    )


def _make_state(campaign=None, campaign_dir=None):
    from soloquest.loop import GameState

    character = MagicMock()
    character.name = "Kira"
    character.truths = []

    state = GameState(
        character=character,
        vows=[],
        session=Session(number=1),
        session_count=0,
        dice_mode=MagicMock(),
        dice=MagicMock(),
        moves={},
        oracles={},
        assets={},
        truth_categories={"cataclysm": _make_truth_category("Cataclysm")},
        sync=LocalAdapter("Kira"),
        campaign=campaign,
        campaign_dir=campaign_dir,
    )
    return state


def _make_campaign():
    return CampaignState(
        name="Test Campaign",
        slug="test-campaign",
        created="2026-01-01T00:00:00+00:00",
    )


# ---------------------------------------------------------------------------
# TruthProposal model
# ---------------------------------------------------------------------------


class TestTruthProposal:
    def test_round_trip(self):
        p = TruthProposal(
            category="Cataclysm",
            option_summary="The Sun Plague",
            proposer="Kira",
            proposed_at="2026-01-01T00:00:00+00:00",
        )
        restored = TruthProposal.from_dict(p.to_dict())
        assert restored.category == "Cataclysm"
        assert restored.option_summary == "The Sun Plague"
        assert restored.proposer == "Kira"

    def test_custom_text_omitted_when_empty(self):
        p = TruthProposal(
            category="Cataclysm",
            option_summary="The Sun Plague",
            proposer="Kira",
            proposed_at="2026-01-01T00:00:00+00:00",
        )
        assert "custom_text" not in p.to_dict()

    def test_custom_text_included_when_set(self):
        p = TruthProposal(
            category="Cataclysm",
            option_summary="Custom",
            proposer="Kira",
            proposed_at="2026-01-01T00:00:00+00:00",
            custom_text="My custom truth",
        )
        assert p.to_dict()["custom_text"] == "My custom truth"


# ---------------------------------------------------------------------------
# CampaignState truth fields
# ---------------------------------------------------------------------------


class TestCampaignStateTruths:
    def test_truths_defaults_empty(self):
        assert _make_campaign().truths == []

    def test_pending_proposals_defaults_empty(self):
        assert _make_campaign().pending_truth_proposals == {}

    def test_truths_serialized_only_when_nonempty(self):
        d = _make_campaign().to_dict()
        assert "truths" not in d
        assert "pending_truth_proposals" not in d

    def test_truths_round_trip(self):
        campaign = _make_campaign()
        campaign.truths.append(ChosenTruth(category="Cataclysm", option_summary="The Sun Plague"))
        restored = CampaignState.from_dict(campaign.to_dict())
        assert len(restored.truths) == 1
        assert restored.truths[0].option_summary == "The Sun Plague"

    def test_pending_proposals_round_trip(self):
        campaign = _make_campaign()
        campaign.pending_truth_proposals["Cataclysm"] = TruthProposal(
            category="Cataclysm",
            option_summary="The Sun Plague",
            proposer="Kira",
            proposed_at="2026-01-01T00:00:00+00:00",
        )
        restored = CampaignState.from_dict(campaign.to_dict())
        assert "Cataclysm" in restored.pending_truth_proposals
        p = restored.pending_truth_proposals["Cataclysm"]
        assert p.option_summary == "The Sun Plague"

    def test_backward_compat_no_truths_key(self):
        data = {
            "campaign": {"name": "T", "slug": "t", "created": "2026-01-01T00:00:00+00:00"},
            "players": {},
        }
        campaign = CampaignState.from_dict(data)
        assert campaign.truths == []
        assert campaign.pending_truth_proposals == {}


# ---------------------------------------------------------------------------
# /truths propose
# ---------------------------------------------------------------------------


class TestHandleTruthPropose:
    def test_solo_mode_applies_truth_immediately(self):
        """In solo mode, propose auto-accepts."""
        from soloquest.commands.truths import _handle_truth_propose

        state = _make_state(campaign=None)

        chosen = ChosenTruth(category="Cataclysm", option_summary="The Sun Plague")
        with patch("soloquest.commands.truths._get_truth_choice", return_value=chosen):
            _handle_truth_propose(state, ["Cataclysm"])

        assert len(state.character.truths) == 1
        assert state.character.truths[0].option_summary == "The Sun Plague"

    def test_coop_creates_pending_proposal(self, tmp_path):
        from soloquest.commands.truths import _handle_truth_propose

        campaign = _make_campaign()
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)

        chosen = ChosenTruth(category="Cataclysm", option_summary="The Sun Plague")
        with (
            patch("soloquest.commands.truths._get_truth_choice", return_value=chosen),
            patch("soloquest.state.campaign.save_campaign"),
        ):
            _handle_truth_propose(state, ["Cataclysm"])

        assert "Cataclysm" in state.campaign.pending_truth_proposals
        proposal = state.campaign.pending_truth_proposals["Cataclysm"]
        assert proposal.option_summary == "The Sun Plague"
        assert proposal.proposer == "Kira"

    def test_coop_does_not_apply_truth_to_character(self, tmp_path):
        from soloquest.commands.truths import _handle_truth_propose

        campaign = _make_campaign()
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)

        chosen = ChosenTruth(category="Cataclysm", option_summary="The Sun Plague")
        with (
            patch("soloquest.commands.truths._get_truth_choice", return_value=chosen),
            patch("soloquest.state.campaign.save_campaign"),
        ):
            _handle_truth_propose(state, ["Cataclysm"])

        assert state.character.truths == []

    def test_coop_publishes_propose_truth_event(self, tmp_path):
        from soloquest.commands.truths import _handle_truth_propose

        campaign = _make_campaign()
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)
        mock_sync = MagicMock()
        state.sync = mock_sync

        chosen = ChosenTruth(category="Cataclysm", option_summary="The Sun Plague")
        with (
            patch("soloquest.commands.truths._get_truth_choice", return_value=chosen),
            patch("soloquest.state.campaign.save_campaign"),
        ):
            _handle_truth_propose(state, ["Cataclysm"])

        mock_sync.publish.assert_called_once()
        event = mock_sync.publish.call_args[0][0]
        assert event.type == "propose_truth"
        assert event.data["category"] == "Cataclysm"

    def test_unknown_category_shows_error(self):
        from soloquest.commands.truths import _handle_truth_propose

        state = _make_state()
        with patch("soloquest.commands.truths.display") as mock_display:
            _handle_truth_propose(state, ["NonExistentCategory"])
        mock_display.error.assert_called_once()


# ---------------------------------------------------------------------------
# /truths review
# ---------------------------------------------------------------------------


class TestHandleTruthReview:
    def test_solo_shows_info(self):
        from soloquest.commands.truths import _handle_truth_review

        state = _make_state(campaign=None)
        with patch("soloquest.commands.truths.display") as mock_display:
            _handle_truth_review(state)
        mock_display.info.assert_called_once()

    def test_coop_no_pending_shows_info(self):
        from soloquest.commands.truths import _handle_truth_review

        state = _make_state(campaign=_make_campaign())
        with patch("soloquest.commands.truths.display") as mock_display:
            _handle_truth_review(state)
        mock_display.info.assert_called_once()

    def test_coop_shows_pending_proposals(self):
        from soloquest.commands.truths import _handle_truth_review

        campaign = _make_campaign()
        campaign.pending_truth_proposals["Cataclysm"] = TruthProposal(
            category="Cataclysm",
            option_summary="The Sun Plague",
            proposer="Dax",
            proposed_at="2026-01-01T00:00:00+00:00",
        )
        state = _make_state(campaign=campaign)

        with patch("soloquest.commands.truths.display") as mock_display:
            mock_display.console = MagicMock()
            mock_display.rule = MagicMock()
            _handle_truth_review(state)

        # Rule should be called (indicating content was shown)
        mock_display.rule.assert_called_once()


# ---------------------------------------------------------------------------
# /truths accept
# ---------------------------------------------------------------------------


class TestHandleTruthAccept:
    def test_solo_shows_info(self):
        from soloquest.commands.truths import _handle_truth_accept

        state = _make_state(campaign=None)
        with patch("soloquest.commands.truths.display") as mock_display:
            _handle_truth_accept(state, [])
        mock_display.info.assert_called_once()

    def test_no_pending_shows_info(self):
        from soloquest.commands.truths import _handle_truth_accept

        state = _make_state(campaign=_make_campaign())
        with patch("soloquest.commands.truths.display") as mock_display:
            _handle_truth_accept(state, [])
        mock_display.info.assert_called_once()

    def test_accept_applies_to_character_truths(self, tmp_path):
        from soloquest.commands.truths import _handle_truth_accept

        campaign = _make_campaign()
        campaign.pending_truth_proposals["Cataclysm"] = TruthProposal(
            category="Cataclysm",
            option_summary="The Sun Plague",
            proposer="Dax",
            proposed_at="2026-01-01T00:00:00+00:00",
        )
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)

        with patch("soloquest.state.campaign.save_campaign"):
            _handle_truth_accept(state, ["Cataclysm"])

        assert len(state.character.truths) == 1
        assert state.character.truths[0].option_summary == "The Sun Plague"

    def test_accept_removes_from_pending(self, tmp_path):
        from soloquest.commands.truths import _handle_truth_accept

        campaign = _make_campaign()
        campaign.pending_truth_proposals["Cataclysm"] = TruthProposal(
            category="Cataclysm",
            option_summary="The Sun Plague",
            proposer="Dax",
            proposed_at="2026-01-01T00:00:00+00:00",
        )
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)

        with patch("soloquest.state.campaign.save_campaign"):
            _handle_truth_accept(state, ["Cataclysm"])

        assert "Cataclysm" not in state.campaign.pending_truth_proposals

    def test_accept_adds_to_campaign_truths(self, tmp_path):
        from soloquest.commands.truths import _handle_truth_accept

        campaign = _make_campaign()
        campaign.pending_truth_proposals["Cataclysm"] = TruthProposal(
            category="Cataclysm",
            option_summary="The Sun Plague",
            proposer="Dax",
            proposed_at="2026-01-01T00:00:00+00:00",
        )
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)

        with patch("soloquest.state.campaign.save_campaign"):
            _handle_truth_accept(state, [])

        assert len(state.campaign.truths) == 1
        assert state.campaign.truths[0].option_summary == "The Sun Plague"

    def test_accept_publishes_event(self, tmp_path):
        from soloquest.commands.truths import _handle_truth_accept

        campaign = _make_campaign()
        campaign.pending_truth_proposals["Cataclysm"] = TruthProposal(
            category="Cataclysm",
            option_summary="The Sun Plague",
            proposer="Dax",
            proposed_at="2026-01-01T00:00:00+00:00",
        )
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)
        mock_sync = MagicMock()
        state.sync = mock_sync

        with patch("soloquest.state.campaign.save_campaign"):
            _handle_truth_accept(state, [])

        mock_sync.publish.assert_called_once()
        event = mock_sync.publish.call_args[0][0]
        assert event.type == "accept_truth"
        assert event.data["category"] == "Cataclysm"

    def test_accept_by_category_name(self, tmp_path):
        from soloquest.commands.truths import _handle_truth_accept

        campaign = _make_campaign()
        campaign.pending_truth_proposals["Cataclysm"] = TruthProposal(
            category="Cataclysm",
            option_summary="The Sun Plague",
            proposer="Dax",
            proposed_at="2026-01-01T00:00:00+00:00",
        )
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)

        with patch("soloquest.state.campaign.save_campaign"):
            _handle_truth_accept(state, ["cata"])  # partial match

        assert "Cataclysm" not in state.campaign.pending_truth_proposals
