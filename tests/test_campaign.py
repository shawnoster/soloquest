"""Tests for campaign state management — models, state layer, and commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from wyrd.models.campaign import CampaignState, PlayerInfo
from wyrd.state.campaign import (
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
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        campaign, campaign_dir = create_campaign("Iron Veil", "kira")
        assert campaign_dir.exists()
        assert (campaign_dir / "events").is_dir()
        assert (campaign_dir / "players").is_dir()
        assert (campaign_dir / "campaign.toml").exists()

    def test_player_added_to_campaign(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        campaign, _ = create_campaign("Iron Veil", "kira")
        assert "kira" in campaign.players

    def test_duplicate_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        create_campaign("Iron Veil", "kira")
        with pytest.raises(ValueError, match="already exists"):
            create_campaign("Iron Veil", "dax")

    def test_sets_campaign_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        campaign, campaign_dir = create_campaign("Test", "kira")
        assert campaign.campaign_dir == campaign_dir


class TestJoinCampaign:
    def test_adds_new_player(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        _, campaign_dir = create_campaign("Iron Veil", "kira")
        campaign = join_campaign(campaign_dir, "dax")
        assert "dax" in campaign.players

    def test_duplicate_player_is_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        _, campaign_dir = create_campaign("Iron Veil", "kira")
        # Second join for the same player returns the campaign unchanged
        campaign = join_campaign(campaign_dir, "kira")
        assert "kira" in campaign.players


class TestListCampaigns:
    def test_empty_when_no_campaigns_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "nonexistent"
        )
        assert list_campaigns() == []

    def test_returns_slugs(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
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
        from wyrd.loop import GameState

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
        from wyrd.loop import GameState

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
        from wyrd.loop import GameState, _autosave_state

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

        with patch("wyrd.loop.autosave") as mock_save:
            _autosave_state(state)

        mock_save.assert_called_once()
        _, kwargs = mock_save.call_args
        assert kwargs["save_path"] == tmp_path / "players" / "kira.json"

    def test_autosave_no_save_path_in_solo_mode(self):
        """_autosave_state passes save_path=None in solo mode."""
        from wyrd.loop import GameState, _autosave_state

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

        with patch("wyrd.loop.autosave") as mock_save:
            _autosave_state(state)

        mock_save.assert_called_once()
        _, kwargs = mock_save.call_args
        assert kwargs["save_path"] is None


# ---------------------------------------------------------------------------
# /campaign start subcommand
# ---------------------------------------------------------------------------


def _make_state(tmp_path):
    """Build a minimal GameState for testing _handle_start."""
    from wyrd.engine.dice import DiceMode, DigitalDice
    from wyrd.loop import GameState
    from wyrd.models.character import Character

    return GameState(
        character=Character("Wanderer"),
        vows=[],
        session=MagicMock(),
        session_count=0,
        dice_mode=DiceMode.DIGITAL,
        dice=DigitalDice(),
        moves={},
        oracles={},
        assets={},
        truth_categories={},
    )


class TestHandleStart:
    def test_solo_updates_state(self, tmp_path, monkeypatch):
        """Solo path replaces character and saves."""
        from wyrd.commands.campaign import _handle_start_solo
        from wyrd.engine.dice import DiceMode
        from wyrd.models.character import Character
        from wyrd.models.vow import Vow, VowRank

        state = _make_state(tmp_path)

        new_char = Character("Kira")
        new_vows = [Vow(description="Test vow", rank=VowRank.EPIC)]

        with (
            patch(
                "wyrd.commands.campaign.run_new_character_flow",
                return_value=(new_char, new_vows, DiceMode.DIGITAL, []),
            ),
            patch("wyrd.commands.campaign.save_game") as mock_save,
        ):
            _handle_start_solo(state)

        assert state.character is new_char
        assert state.vows is new_vows
        assert state.session_count == 0
        mock_save.assert_called_once()

    def test_solo_cancelled_leaves_state_unchanged(self, tmp_path):
        """Solo path cancelled — state not mutated."""
        from wyrd.commands.campaign import _handle_start_solo

        state = _make_state(tmp_path)
        original_name = state.character.name

        with patch(
            "wyrd.commands.campaign.run_new_character_flow",
            return_value=None,
        ):
            _handle_start_solo(state)

        assert state.character.name == original_name

    def test_create_coop_updates_state(self, tmp_path, monkeypatch):
        """Create co-op path wires campaign into state and saves to players/."""
        from wyrd.commands.campaign import _handle_start_create_coop
        from wyrd.engine.dice import DiceMode
        from wyrd.models.character import Character
        from wyrd.models.vow import Vow, VowRank

        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        state = _make_state(tmp_path)

        new_char = Character("Kira")
        new_vows = [Vow(description="Find the signal", rank=VowRank.EPIC)]

        with (
            patch(
                "wyrd.commands.campaign.run_new_character_flow",
                return_value=(new_char, new_vows, DiceMode.DIGITAL, []),
            ),
            patch("rich.prompt.Prompt.ask", return_value="Iron Veil"),
            patch("wyrd.commands.campaign.save_game") as mock_save,
        ):
            _handle_start_create_coop(state)

        assert state.character is new_char
        assert state.campaign is not None
        assert state.campaign.name == "Iron Veil"
        assert state.campaign_dir is not None
        assert state.sync is not None
        assert state.session_count == 0
        mock_save.assert_called_once()

    def test_join_coop_updates_state(self, tmp_path, monkeypatch):
        """Join co-op path wires campaign into state and saves to players/."""
        from wyrd.commands.campaign import _handle_start_join_coop
        from wyrd.engine.dice import DiceMode
        from wyrd.models.character import Character
        from wyrd.models.vow import Vow, VowRank

        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        # Pre-create a campaign so list_campaigns returns it
        create_campaign("Iron Veil", "existing-player")

        state = _make_state(tmp_path)
        new_char = Character("Dax")
        new_vows = [Vow(description="Seek truth", rank=VowRank.TROUBLESOME)]

        with (
            patch(
                "wyrd.commands.campaign.run_new_character_flow",
                return_value=(new_char, new_vows, DiceMode.DIGITAL, []),
            ),
            patch("rich.prompt.Prompt.ask", return_value="1"),
            patch("wyrd.commands.campaign.save_game") as mock_save,
        ):
            _handle_start_join_coop(state)

        assert state.character is new_char
        assert state.campaign is not None
        assert state.campaign_dir is not None
        assert state.session_count == 0
        mock_save.assert_called_once()

    def test_join_coop_skips_truths(self, tmp_path, monkeypatch):
        """Join co-op calls run_new_character_flow with include_truths=False."""
        from wyrd.commands.campaign import _handle_start_join_coop
        from wyrd.engine.dice import DiceMode
        from wyrd.models.character import Character

        monkeypatch.setattr(
            "wyrd.state.campaign.campaigns_dir", lambda: tmp_path / "campaigns"
        )
        create_campaign("Iron Veil", "existing-player")
        state = _make_state(tmp_path)
        new_char = Character("Dax")

        with (
            patch(
                "wyrd.commands.campaign.run_new_character_flow",
                return_value=(new_char, [], DiceMode.DIGITAL, []),
            ) as mock_flow,
            patch("rich.prompt.Prompt.ask", return_value="1"),
            patch("wyrd.commands.campaign.save_game"),
        ):
            _handle_start_join_coop(state)

        mock_flow.assert_called_once()
        _, kwargs = mock_flow.call_args
        assert kwargs.get("include_truths") is False or mock_flow.call_args[0][2] is False
