"""Tests for shared campaign vows."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from wyrd.models.campaign import CampaignState
from wyrd.models.session import Session
from wyrd.models.vow import Vow, VowRank
from wyrd.sync import LocalAdapter


def _make_state(campaign=None, campaign_dir=None, vows=None):
    from wyrd.loop import GameState

    character = MagicMock()
    character.name = "Kira"

    state = GameState(
        character=character,
        vows=vows or [],
        session=Session(number=1),
        session_count=0,
        dice_mode=MagicMock(),
        dice=MagicMock(),
        moves={},
        oracles={},
        assets={},
        truth_categories={},
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
# Vow model
# ---------------------------------------------------------------------------


class TestVowSharedField:
    def test_shared_defaults_to_false(self):
        vow = Vow(description="Save the colony", rank=VowRank.DANGEROUS)
        assert vow.shared is False

    def test_shared_in_dict_when_true(self):
        vow = Vow(description="Save the colony", rank=VowRank.DANGEROUS, shared=True)
        assert vow.to_dict()["shared"] is True

    def test_shared_omitted_from_dict_when_false(self):
        vow = Vow(description="Save the colony", rank=VowRank.DANGEROUS, shared=False)
        assert "shared" not in vow.to_dict()

    def test_round_trip_preserves_shared_true(self):
        vow = Vow(description="Save the colony", rank=VowRank.DANGEROUS, shared=True)
        restored = Vow.from_dict(vow.to_dict())
        assert restored.shared is True

    def test_round_trip_backward_compat_no_shared_key(self):
        data = {"description": "Old vow", "rank": "dangerous", "ticks": 0, "fulfilled": False}
        vow = Vow.from_dict(data)
        assert vow.shared is False


# ---------------------------------------------------------------------------
# CampaignState shared_vows
# ---------------------------------------------------------------------------


class TestCampaignStateSharedVows:
    def test_shared_vows_defaults_empty(self):
        campaign = _make_campaign()
        assert campaign.shared_vows == []

    def test_shared_vows_serialized_only_when_nonempty(self):
        campaign = _make_campaign()
        d = campaign.to_dict()
        assert "shared_vows" not in d

    def test_shared_vows_serialized_when_present(self):
        campaign = _make_campaign()
        campaign.shared_vows.append(Vow(description="Test", rank=VowRank.DANGEROUS, shared=True))
        d = campaign.to_dict()
        assert "shared_vows" in d
        assert len(d["shared_vows"]) == 1

    def test_shared_vows_round_trip(self):
        campaign = _make_campaign()
        campaign.shared_vows.append(
            Vow(description="Save the colony", rank=VowRank.FORMIDABLE, ticks=8, shared=True)
        )
        restored = CampaignState.from_dict(campaign.to_dict())
        assert len(restored.shared_vows) == 1
        assert restored.shared_vows[0].description == "Save the colony"
        assert restored.shared_vows[0].ticks == 8
        assert restored.shared_vows[0].shared is True

    def test_backward_compat_no_shared_vows_key(self):
        """Campaigns created before shared vows deserialise without error."""
        data = {
            "campaign": {"name": "Test", "slug": "test", "created": "2026-01-01T00:00:00+00:00"},
            "players": {},
        }
        campaign = CampaignState.from_dict(data)
        assert campaign.shared_vows == []


# ---------------------------------------------------------------------------
# handle_vow with --shared flag
# ---------------------------------------------------------------------------


class TestHandleVowShared:
    def test_shared_without_campaign_warns(self):
        from wyrd.commands.vow import handle_vow

        state = _make_state(campaign=None)
        with patch("wyrd.commands.vow.display") as mock_display:
            handle_vow(state, ["dangerous", "save", "the", "colony"], {"shared"})
        mock_display.warn.assert_called_once()
        assert state.vows == []

    def test_shared_adds_to_campaign_shared_vows(self, tmp_path):
        from wyrd.commands.vow import handle_vow

        campaign = _make_campaign()
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)
        # Create necessary subdirectory structure
        (tmp_path / "events").mkdir()

        with patch("wyrd.state.campaign.save_campaign"):
            handle_vow(state, ["dangerous", "save", "colony"], {"shared"})

        assert len(state.campaign.shared_vows) == 1
        vow = state.campaign.shared_vows[0]
        assert vow.description == "save colony"
        assert vow.rank == VowRank.DANGEROUS
        assert vow.shared is True

    def test_shared_does_not_add_to_personal_vows(self, tmp_path):
        from wyrd.commands.vow import handle_vow

        campaign = _make_campaign()
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)

        with patch("wyrd.state.campaign.save_campaign"):
            handle_vow(state, ["dangerous", "save", "colony"], {"shared"})

        assert state.vows == []

    def test_shared_publishes_event(self, tmp_path):
        from wyrd.commands.vow import handle_vow

        campaign = _make_campaign()
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)
        mock_sync = MagicMock()
        state.sync = mock_sync

        with patch("wyrd.state.campaign.save_campaign"):
            handle_vow(state, ["formidable", "find", "the", "relic"], {"shared"})

        mock_sync.publish.assert_called_once()
        event = mock_sync.publish.call_args[0][0]
        assert event.type == "shared_vow_created"
        assert event.data["description"] == "find the relic"
        assert event.data["rank"] == "formidable"

    def test_unshared_vow_works_as_before(self):
        from wyrd.commands.vow import handle_vow

        state = _make_state()
        handle_vow(state, ["dangerous", "save", "colony"], set())
        assert len(state.vows) == 1
        assert state.vows[0].shared is False


# ---------------------------------------------------------------------------
# handle_progress with shared vows
# ---------------------------------------------------------------------------


class TestHandleProgressSharedVows:
    def test_progress_on_shared_vow(self, tmp_path):
        from wyrd.commands.vow import handle_progress

        campaign = _make_campaign()
        vow = Vow(description="Find the relic", rank=VowRank.DANGEROUS, shared=True)
        campaign.shared_vows.append(vow)
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)

        with patch("wyrd.state.campaign.save_campaign") as mock_save:
            handle_progress(state, ["relic"], set())

        assert vow.ticks > 0
        mock_save.assert_called_once()

    def test_progress_on_shared_vow_publishes_event(self, tmp_path):
        from wyrd.commands.vow import handle_progress

        campaign = _make_campaign()
        vow = Vow(description="Find the relic", rank=VowRank.DANGEROUS, shared=True)
        campaign.shared_vows.append(vow)
        state = _make_state(campaign=campaign, campaign_dir=tmp_path)
        mock_sync = MagicMock()
        state.sync = mock_sync

        with patch("wyrd.state.campaign.save_campaign"):
            handle_progress(state, ["relic"], set())

        mock_sync.publish.assert_called_once()
        event = mock_sync.publish.call_args[0][0]
        assert event.type == "shared_vow_progress"

    def test_progress_on_personal_vow_does_not_save_campaign(self):
        from wyrd.commands.vow import handle_progress

        vow = Vow(description="Personal goal", rank=VowRank.DANGEROUS)
        state = _make_state(vows=[vow])

        with patch("wyrd.state.campaign.save_campaign") as mock_save:
            handle_progress(state, ["personal"], set())

        mock_save.assert_not_called()

    def test_shared_vow_shown_in_active_pool(self):
        from wyrd.commands.vow import handle_progress

        campaign = _make_campaign()
        shared_vow = Vow(description="Shared goal", rank=VowRank.DANGEROUS, shared=True)
        campaign.shared_vows.append(shared_vow)
        personal_vow = Vow(description="Personal goal", rank=VowRank.TROUBLESOME)
        state = _make_state(campaign=campaign, vows=[personal_vow])

        # Both vows should be visible; resolve "shared" query matches shared vow
        with patch("wyrd.state.campaign.save_campaign"):
            handle_progress(state, ["shared"], set())

        assert shared_vow.ticks > 0
