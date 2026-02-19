"""Tests for co-op partner activity polling and display."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rich.console import Console

from soloquest.models.campaign import CampaignState
from soloquest.models.session import Session
from soloquest.sync import LocalAdapter
from soloquest.sync.models import Event

# ---------------------------------------------------------------------------
# display.partner_activity
# ---------------------------------------------------------------------------


def _capture(events: list[Event]) -> str:
    """Render partner_activity to a string for assertions."""
    from soloquest.ui import display

    console = Console(record=True, highlight=False)
    original = display.console
    display.console = console
    try:
        display.partner_activity(events)
    finally:
        display.console = original
    return console.export_text()


class TestPartnerActivityDisplay:
    def test_empty_events_produces_no_output(self):
        output = _capture([])
        assert output == ""

    def test_oracle_roll_shown(self):
        event = Event(
            player="dax",
            type="oracle_roll",
            data={"tables": ["action"], "rolls": [42], "results": ["Bolster"]},
        )
        output = _capture([event])
        assert "dax" in output
        assert "ACTION" in output
        assert "42" in output
        assert "Bolster" in output

    def test_oracle_roll_multi_table(self):
        event = Event(
            player="dax",
            type="oracle_roll",
            data={
                "tables": ["action", "theme"],
                "rolls": [42, 87],
                "results": ["Bolster", "Weapon"],
            },
        )
        output = _capture([event])
        assert "ACTION" in output
        assert "THEME" in output
        assert "Bolster" in output
        assert "Weapon" in output

    def test_oracle_roll_with_note(self):
        event = Event(
            player="dax",
            type="oracle_roll",
            data={
                "tables": ["action"],
                "rolls": [10],
                "results": ["Seek"],
                "note": "why did she lie?",
            },
        )
        output = _capture([event])
        assert "why did she lie?" in output

    def test_unknown_event_type_shows_fallback(self):
        event = Event(player="dax", type="future_type", data={"key": "val"})
        output = _capture([event])
        assert "future_type" in output

    def test_player_header_shown(self):
        event = Event(
            player="kira", type="oracle_roll", data={"tables": [], "rolls": [], "results": []}
        )
        output = _capture([event])
        assert "kira" in output

    def test_same_player_only_one_header(self):
        events = [
            Event(
                player="dax",
                type="oracle_roll",
                data={"tables": ["action"], "rolls": [1], "results": ["A"]},
            ),
            Event(
                player="dax",
                type="oracle_roll",
                data={"tables": ["theme"], "rolls": [2], "results": ["B"]},
            ),
        ]
        output = _capture(events)
        # "dax" appears once as header
        assert output.count("dax") == 1

    def test_different_players_get_separate_headers(self):
        events = [
            Event(
                player="dax",
                type="oracle_roll",
                data={"tables": ["action"], "rolls": [1], "results": ["A"]},
            ),
            Event(
                player="kira",
                type="oracle_roll",
                data={"tables": ["theme"], "rolls": [2], "results": ["B"]},
            ),
        ]
        output = _capture(events)
        assert "dax" in output
        assert "kira" in output


# ---------------------------------------------------------------------------
# _poll_and_display in loop.py
# ---------------------------------------------------------------------------


def _make_game_state(campaign=None):
    from soloquest.loop import GameState

    state = GameState(
        character=MagicMock(),
        vows=[],
        session=Session(number=1),
        session_count=0,
        dice_mode=MagicMock(),
        dice=MagicMock(),
        moves={},
        oracles={},
        assets={},
        truth_categories={},
        sync=LocalAdapter("test"),
        campaign=campaign,
    )
    return state


class TestPollAndDisplay:
    def test_solo_mode_no_campaign_skips_poll(self):
        """In solo mode _poll_and_display is a no-op (campaign=None, not explicit)."""
        from soloquest.loop import _poll_and_display

        state = _make_game_state(campaign=None)
        mock_sync = MagicMock()
        state.sync = mock_sync

        _poll_and_display(state, explicit=False)

        mock_sync.poll.assert_not_called()

    def test_explicit_sync_polls_even_without_campaign(self):
        """Explicit /sync command should poll even in solo mode."""
        from soloquest.loop import _poll_and_display

        state = _make_game_state(campaign=None)
        mock_sync = MagicMock()
        mock_sync.poll.return_value = []
        state.sync = mock_sync

        with patch("soloquest.loop.display") as mock_display:
            _poll_and_display(state, explicit=True)

        mock_sync.poll.assert_called_once()
        mock_display.info.assert_called_once()

    def test_coop_mode_polls_after_command(self):
        """In co-op mode poll is called automatically."""
        from soloquest.loop import _poll_and_display

        campaign = MagicMock(spec=CampaignState)
        state = _make_game_state(campaign=campaign)
        mock_sync = MagicMock()
        mock_sync.poll.return_value = []
        state.sync = mock_sync

        _poll_and_display(state, explicit=False)

        mock_sync.poll.assert_called_once()

    def test_displays_events_when_poll_returns_some(self):
        """When poll returns events, partner_activity is called."""
        from soloquest.loop import _poll_and_display

        campaign = MagicMock(spec=CampaignState)
        state = _make_game_state(campaign=campaign)
        events = [
            Event(player="dax", type="oracle_roll", data={"tables": [], "rolls": [], "results": []})
        ]
        mock_sync = MagicMock()
        mock_sync.poll.return_value = events
        state.sync = mock_sync

        with patch("soloquest.loop.display") as mock_display:
            _poll_and_display(state, explicit=False)

        mock_display.partner_activity.assert_called_once_with(events)

    def test_no_message_when_no_events_in_auto_mode(self):
        """Auto poll with no events shows nothing."""
        from soloquest.loop import _poll_and_display

        campaign = MagicMock(spec=CampaignState)
        state = _make_game_state(campaign=campaign)
        mock_sync = MagicMock()
        mock_sync.poll.return_value = []
        state.sync = mock_sync

        with patch("soloquest.loop.display") as mock_display:
            _poll_and_display(state, explicit=False)

        mock_display.partner_activity.assert_not_called()
        mock_display.info.assert_not_called()

    def test_explicit_no_events_shows_info_message(self):
        """Explicit /sync with no events shows 'no activity' message."""
        from soloquest.loop import _poll_and_display

        state = _make_game_state(campaign=None)
        mock_sync = MagicMock()
        mock_sync.poll.return_value = []
        state.sync = mock_sync

        with patch("soloquest.loop.display") as mock_display:
            _poll_and_display(state, explicit=True)

        mock_display.info.assert_called_once()
