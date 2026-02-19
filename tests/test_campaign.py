"""Tests for campaign state management — models, state layer, and commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soloquest.models.campaign import CampaignState, PlayerInfo
from soloquest.state.campaign import (
    create_campaign,
    join_campaign,
    list_campaigns,
    load_campaign,
    player_save_path,
    save_campaign,
)

# ---------------------------------------------------------------------------
# PlayerInfo model
# ---------------------------------------------------------------------------


class TestPlayerInfo:
    def test_round_trip(self):
        p = PlayerInfo(joined="2026-02-18T00:00:00+00:00")
        assert PlayerInfo.from_dict(p.to_dict()) == p

    def test_to_dict_keys(self):
        p = PlayerInfo(joined="2026-02-18T00:00:00+00:00")
        assert set(p.to_dict().keys()) == {"joined"}


# ---------------------------------------------------------------------------
# CampaignState model
# ---------------------------------------------------------------------------


class TestCampaignState:
    def test_create_slug_from_name(self):
        c = CampaignState.create("The Iron Veil")
        assert c.slug == "the-iron-veil"

    def test_create_strips_non_alnum(self):
        c = CampaignState.create("Iron & Veil!")
        # Only alnum and hyphens
        for ch in c.slug:
            assert ch.isalnum() or ch == "-"

    def test_create_sets_created_timestamp(self):
        c = CampaignState.create("Test")
        assert c.created  # non-empty ISO string

    def test_round_trip_serialization(self):
        c = CampaignState.create("My Campaign")
        c.players["kira"] = PlayerInfo(joined="2026-02-18T00:00:00+00:00")
        restored = CampaignState.from_dict(c.to_dict())
        assert restored.name == c.name
        assert restored.slug == c.slug
        assert restored.created == c.created
        assert "kira" in restored.players

    def test_campaign_dir_injected(self, tmp_path):
        c = CampaignState.create("Test")
        assert c.campaign_dir is None
        c.set_campaign_dir(tmp_path)
        assert c.campaign_dir == tmp_path


# ---------------------------------------------------------------------------
# State layer — campaign directory management
# ---------------------------------------------------------------------------


class TestCreateCampaign:
    def test_creates_directory_structure(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "soloquest.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        campaign, campaign_dir = create_campaign("Iron Veil", "kira")
        assert campaign_dir.exists()
        assert (campaign_dir / "events").is_dir()
        assert (campaign_dir / "players").is_dir()
        assert (campaign_dir / "campaign.toml").exists()

    def test_player_added_to_campaign(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "soloquest.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        campaign, _ = create_campaign("Iron Veil", "kira")
        assert "kira" in campaign.players

    def test_duplicate_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "soloquest.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        create_campaign("Iron Veil", "kira")
        with pytest.raises(ValueError, match="already exists"):
            create_campaign("Iron Veil", "dax")

    def test_sets_campaign_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "soloquest.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        campaign, campaign_dir = create_campaign("Test", "kira")
        assert campaign.campaign_dir == campaign_dir


class TestJoinCampaign:
    def test_adds_new_player(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "soloquest.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        _, campaign_dir = create_campaign("Iron Veil", "kira")
        campaign = join_campaign(campaign_dir, "dax")
        assert "dax" in campaign.players

    def test_duplicate_player_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "soloquest.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        _, campaign_dir = create_campaign("Iron Veil", "kira")
        with pytest.raises(ValueError, match="already a member"):
            join_campaign(campaign_dir, "kira")


class TestListCampaigns:
    def test_empty_when_no_campaigns_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "soloquest.state.campaign.campaigns_dir", lambda: tmp_path / "nonexistent"
        )
        assert list_campaigns() == []

    def test_returns_slugs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "soloquest.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        create_campaign("Alpha", "kira")
        create_campaign("Beta", "kira")
        slugs = list_campaigns()
        assert "alpha" in slugs
        assert "beta" in slugs


class TestLoadSaveCampaign:
    def test_round_trip(self, tmp_path):
        campaign = CampaignState.create("Test Campaign")
        campaign.players["kira"] = PlayerInfo(joined="2026-02-18T00:00:00+00:00")
        save_campaign(campaign, tmp_path)
        loaded = load_campaign(tmp_path)
        assert loaded.name == campaign.name
        assert "kira" in loaded.players
        assert loaded.campaign_dir == tmp_path


class TestPlayerSavePath:
    def test_returns_json_path(self, tmp_path):
        p = player_save_path(tmp_path, "Kira Thane")
        assert p == tmp_path / "players" / "kira_thane.json"

    def test_lowercases_and_replaces_spaces(self, tmp_path):
        p = player_save_path(tmp_path, "Iron Bear")
        assert p.name == "iron_bear.json"


# ---------------------------------------------------------------------------
# GameState integration
# ---------------------------------------------------------------------------


class TestGameStateCampaignFields:
    def test_campaign_defaults_to_none(self):
        from soloquest.loop import GameState

        state = GameState(
            character=MagicMock(),
            vows=[],
            session=MagicMock(),
            session_count=1,
            dice_mode=MagicMock(),
            dice=MagicMock(),
            moves={},
            oracles={},
            assets={},
            truth_categories={},
        )
        assert state.campaign is None
        assert state.campaign_dir is None

    def test_campaign_can_be_set(self, tmp_path):
        from soloquest.loop import GameState

        campaign = CampaignState.create("Test")
        state = GameState(
            character=MagicMock(),
            vows=[],
            session=MagicMock(),
            session_count=1,
            dice_mode=MagicMock(),
            dice=MagicMock(),
            moves={},
            oracles={},
            assets={},
            truth_categories={},
            campaign=campaign,
            campaign_dir=tmp_path,
        )
        assert state.campaign is campaign
        assert state.campaign_dir == tmp_path


# ---------------------------------------------------------------------------
# Autosave routing
# ---------------------------------------------------------------------------


class TestAutosaveRouting:
    def test_autosave_uses_player_save_path_in_campaign(self, tmp_path):
        """_autosave_state routes to campaign players/ directory."""
        from soloquest.loop import GameState, _autosave_state

        char = MagicMock()
        char.name = "Kira"

        campaign = CampaignState.create("Test")
        state = GameState(
            character=char,
            vows=[],
            session=MagicMock(),
            session_count=1,
            dice_mode=MagicMock(),
            dice=MagicMock(),
            moves={},
            oracles={},
            assets={},
            truth_categories={},
            campaign=campaign,
            campaign_dir=tmp_path,
        )
        (tmp_path / "players").mkdir()

        with patch("soloquest.loop.autosave") as mock_save:
            _autosave_state(state)

        mock_save.assert_called_once()
        _, kwargs = mock_save.call_args
        assert kwargs["save_path"] == tmp_path / "players" / "kira.json"

    def test_autosave_no_save_path_in_solo_mode(self):
        """_autosave_state passes save_path=None in solo mode."""
        from soloquest.loop import GameState, _autosave_state

        state = GameState(
            character=MagicMock(),
            vows=[],
            session=MagicMock(),
            session_count=1,
            dice_mode=MagicMock(),
            dice=MagicMock(),
            moves={},
            oracles={},
            assets={},
            truth_categories={},
        )

        with patch("soloquest.loop.autosave") as mock_save:
            _autosave_state(state)

        mock_save.assert_called_once()
        _, kwargs = mock_save.call_args
        assert kwargs["save_path"] is None
