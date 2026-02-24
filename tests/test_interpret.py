"""Tests for /interpret and /accept commands."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from wyrd.models.campaign import CampaignState
from wyrd.models.session import EntryKind, Session
from wyrd.sync import LocalAdapter
from wyrd.sync.models import Event


def _make_state(campaign=None, last_oracle_event_id=None):
    from wyrd.loop import GameState

    character = MagicMock()
    character.name = "Kira"

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
        truth_categories={},
        sync=LocalAdapter("Kira"),
        campaign=campaign,
        last_oracle_event_id=last_oracle_event_id,
    )
    return state


# ---------------------------------------------------------------------------
# handle_interpret
# ---------------------------------------------------------------------------


class TestHandleInterpret:
    def test_no_args_warns(self):
        from wyrd.commands.interpret import handle_interpret

        state = _make_state()
        with patch("wyrd.commands.interpret.display") as mock_display:
            handle_interpret(state, [], set())
        mock_display.warn.assert_called_once()

    def test_logs_note_to_session(self):
        from wyrd.commands.interpret import handle_interpret

        state = _make_state()
        handle_interpret(state, ["the", "blacksmith", "arms", "rebels"], set())
        entries = state.session.entries
        assert len(entries) == 1
        assert entries[0].kind == EntryKind.NOTE
        assert "the blacksmith arms rebels" in entries[0].text
        assert "[Interpretation]" in entries[0].text

    def test_note_has_player_attribution(self):
        from wyrd.commands.interpret import handle_interpret

        state = _make_state()
        handle_interpret(state, ["arm", "rebels"], set())
        assert state.session.entries[0].player == "Kira"

    def test_solo_does_not_publish_event(self):
        from wyrd.commands.interpret import handle_interpret

        state = _make_state(campaign=None)
        mock_sync = MagicMock()
        state.sync = mock_sync
        handle_interpret(state, ["something"], set())
        mock_sync.publish.assert_not_called()

    def test_coop_publishes_interpret_event(self):
        from wyrd.commands.interpret import handle_interpret

        campaign = MagicMock(spec=CampaignState)
        state = _make_state(campaign=campaign)
        mock_sync = MagicMock()
        state.sync = mock_sync
        handle_interpret(state, ["something"], set())
        mock_sync.publish.assert_called_once()
        event = mock_sync.publish.call_args[0][0]
        assert event.type == "interpret"
        assert event.data["text"] == "something"

    def test_coop_includes_oracle_ref_when_available(self):
        from wyrd.commands.interpret import handle_interpret

        campaign = MagicMock(spec=CampaignState)
        state = _make_state(campaign=campaign, last_oracle_event_id="oracle-uuid-123")
        mock_sync = MagicMock()
        state.sync = mock_sync
        handle_interpret(state, ["my", "read"], set())
        event = mock_sync.publish.call_args[0][0]
        assert event.data["ref"] == "oracle-uuid-123"

    def test_coop_no_ref_when_no_oracle_yet(self):
        from wyrd.commands.interpret import handle_interpret

        campaign = MagicMock(spec=CampaignState)
        state = _make_state(campaign=campaign, last_oracle_event_id=None)
        mock_sync = MagicMock()
        state.sync = mock_sync
        handle_interpret(state, ["something"], set())
        event = mock_sync.publish.call_args[0][0]
        assert "ref" not in event.data


# ---------------------------------------------------------------------------
# handle_accept
# ---------------------------------------------------------------------------


class TestHandleAccept:
    def test_solo_mode_shows_info(self):
        from wyrd.commands.interpret import handle_accept

        state = _make_state(campaign=None)
        with patch("wyrd.commands.interpret.display") as mock_display:
            handle_accept(state, [], set())
        mock_display.info.assert_called_once()

    def test_no_pending_interpretation_shows_info(self):
        from wyrd.commands.interpret import handle_accept

        campaign = MagicMock(spec=CampaignState)
        state = _make_state(campaign=campaign)
        state.pending_partner_interpretation = None
        with patch("wyrd.commands.interpret.display") as mock_display:
            handle_accept(state, [], set())
        mock_display.info.assert_called_once()

    def test_accept_logs_note_to_session(self):
        from wyrd.commands.interpret import handle_accept

        campaign = MagicMock(spec=CampaignState)
        state = _make_state(campaign=campaign)
        partner_event = Event(
            player="Dax",
            type="interpret",
            data={"text": "the blacksmith arms rebels"},
        )
        state.pending_partner_interpretation = partner_event
        handle_accept(state, [], set())
        entries = state.session.entries
        assert len(entries) == 1
        assert entries[0].kind == EntryKind.NOTE
        assert "the blacksmith arms rebels" in entries[0].text

    def test_accept_publishes_acceptance_event(self):
        from wyrd.commands.interpret import handle_accept

        campaign = MagicMock(spec=CampaignState)
        state = _make_state(campaign=campaign)
        mock_sync = MagicMock()
        state.sync = mock_sync
        partner_event = Event(
            player="Dax",
            type="interpret",
            data={"text": "rebels"},
        )
        state.pending_partner_interpretation = partner_event
        handle_accept(state, [], set())
        mock_sync.publish.assert_called_once()
        published = mock_sync.publish.call_args[0][0]
        assert published.type == "accept_interpretation"
        assert published.data["ref"] == partner_event.id

    def test_accept_clears_pending_interpretation(self):
        from wyrd.commands.interpret import handle_accept

        campaign = MagicMock(spec=CampaignState)
        state = _make_state(campaign=campaign)
        state.pending_partner_interpretation = Event(
            player="Dax", type="interpret", data={"text": "x"}
        )
        handle_accept(state, [], set())
        assert state.pending_partner_interpretation is None

    def test_accept_logs_with_player_attribution(self):
        from wyrd.commands.interpret import handle_accept

        campaign = MagicMock(spec=CampaignState)
        state = _make_state(campaign=campaign)
        state.pending_partner_interpretation = Event(
            player="Dax", type="interpret", data={"text": "something"}
        )
        handle_accept(state, [], set())
        assert state.session.entries[0].player == "Kira"
