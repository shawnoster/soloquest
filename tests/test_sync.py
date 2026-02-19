"""Tests for the sync package — SyncPort, LocalAdapter, FileLogAdapter."""

from __future__ import annotations

import json
from datetime import UTC

from soloquest.sync import Event, FileLogAdapter, LocalAdapter, Proposal, Resolution, SyncPort

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestEvent:
    def test_has_auto_id(self):
        e = Event(player="kira", type="journal")
        assert e.id

    def test_two_events_have_different_ids(self):
        e1 = Event(player="kira", type="journal")
        e2 = Event(player="kira", type="journal")
        assert e1.id != e2.id

    def test_round_trip_serialization(self):
        original = Event(player="kira", type="oracle_roll", data={"roll": 42})
        restored = Event.from_dict(original.to_dict())
        assert restored.id == original.id
        assert restored.player == original.player
        assert restored.type == original.type
        assert restored.data == original.data
        assert restored.ts == original.ts

    def test_to_dict_keys(self):
        e = Event(player="kira", type="journal", data={"text": "hello"})
        d = e.to_dict()
        assert set(d.keys()) == {"id", "player", "type", "ts", "data"}


class TestResolution:
    def test_values(self):
        assert Resolution.ACCEPTED.value == "accepted"
        assert Resolution.REJECTED.value == "rejected"
        assert Resolution.PENDING.value == "pending"


# ---------------------------------------------------------------------------
# LocalAdapter — #80
# ---------------------------------------------------------------------------


class TestLocalAdapter:
    def test_implements_sync_port_protocol(self):
        adapter = LocalAdapter("kira")
        assert isinstance(adapter, SyncPort)

    def test_player_id(self):
        adapter = LocalAdapter("kira")
        assert adapter.player_id == "kira"

    def test_publish_is_noop(self):
        adapter = LocalAdapter("kira")
        # Should not raise and should not write any files
        adapter.publish(Event(player="kira", type="journal", data={"text": "hi"}))

    def test_poll_returns_empty_list(self):
        adapter = LocalAdapter("kira")
        assert adapter.poll() == []

    def test_propose_returns_accepted(self):
        adapter = LocalAdapter("kira")
        proposal = Proposal(player="kira", type="propose_truth", data={"category": "Cataclysm"})
        result = adapter.propose(proposal)
        assert result == Resolution.ACCEPTED

    def test_resolve_is_noop(self):
        adapter = LocalAdapter("kira")
        # Should not raise
        adapter.resolve("some-uuid", accepted=True)
        adapter.resolve("some-uuid", accepted=False)

    def test_multiple_polls_always_empty(self):
        adapter = LocalAdapter("kira")
        for _ in range(5):
            assert adapter.poll() == []


# ---------------------------------------------------------------------------
# FileLogAdapter — #81
# ---------------------------------------------------------------------------


class TestFileLogAdapterPublish:
    def test_creates_player_file(self, tmp_path):
        adapter = FileLogAdapter(tmp_path, "kira")
        adapter.publish(Event(player="kira", type="journal", data={"text": "hello"}))
        assert (tmp_path / "events" / "kira.jsonl").exists()

    def test_appends_json_lines(self, tmp_path):
        adapter = FileLogAdapter(tmp_path, "kira")
        adapter.publish(Event(player="kira", type="journal", data={"text": "first"}))
        adapter.publish(Event(player="kira", type="journal", data={"text": "second"}))
        lines = (tmp_path / "events" / "kira.jsonl").read_text().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["data"]["text"] == "first"
        assert json.loads(lines[1])["data"]["text"] == "second"

    def test_each_line_is_valid_json(self, tmp_path):
        adapter = FileLogAdapter(tmp_path, "kira")
        for i in range(5):
            adapter.publish(Event(player="kira", type="journal", data={"n": i}))
        lines = (tmp_path / "events" / "kira.jsonl").read_text().splitlines()
        for line in lines:
            obj = json.loads(line)
            assert "id" in obj and "player" in obj


class TestFileLogAdapterPoll:
    def test_poll_returns_empty_when_no_other_players(self, tmp_path):
        adapter = FileLogAdapter(tmp_path, "kira")
        assert adapter.poll() == []

    def test_poll_reads_other_player_events(self, tmp_path):
        kira = FileLogAdapter(tmp_path, "kira")
        dax = FileLogAdapter(tmp_path, "dax")

        dax.publish(Event(player="dax", type="journal", data={"text": "dax here"}))

        events = kira.poll()
        assert len(events) == 1
        assert events[0].player == "dax"
        assert events[0].data["text"] == "dax here"

    def test_poll_is_incremental(self, tmp_path):
        kira = FileLogAdapter(tmp_path, "kira")
        dax = FileLogAdapter(tmp_path, "dax")

        dax.publish(Event(player="dax", type="journal", data={"n": 1}))
        first_poll = kira.poll()
        assert len(first_poll) == 1

        dax.publish(Event(player="dax", type="journal", data={"n": 2}))
        second_poll = kira.poll()
        assert len(second_poll) == 1
        assert second_poll[0].data["n"] == 2

    def test_poll_does_not_return_own_events(self, tmp_path):
        kira = FileLogAdapter(tmp_path, "kira")
        kira.publish(Event(player="kira", type="journal"))
        assert kira.poll() == []

    def test_poll_deduplicates_by_uuid(self, tmp_path):
        kira = FileLogAdapter(tmp_path, "kira")
        dax_file = tmp_path / "events" / "dax.jsonl"
        dax_file.parent.mkdir(parents=True, exist_ok=True)

        event = Event(player="dax", type="journal", data={"text": "once"})
        line = json.dumps(event.to_dict()) + "\n"
        # Write same event twice (simulating cloud-sync conflict copy)
        dax_file.write_text(line + line)

        events = kira.poll()
        assert len(events) == 1

    def test_poll_skips_malformed_lines(self, tmp_path):
        kira = FileLogAdapter(tmp_path, "kira")
        dax_file = tmp_path / "events" / "dax.jsonl"
        dax_file.parent.mkdir(parents=True, exist_ok=True)

        good_event = Event(player="dax", type="journal", data={"text": "good"})
        dax_file.write_text(
            "not valid json\n" + json.dumps(good_event.to_dict()) + "\n" + "{broken\n"
        )

        events = kira.poll()
        assert len(events) == 1
        assert events[0].data["text"] == "good"

    def test_poll_merges_multiple_players_by_timestamp(self, tmp_path):
        from datetime import datetime, timedelta

        kira = FileLogAdapter(tmp_path, "kira")

        # Write dax and rex events with known timestamps
        base = datetime(2026, 2, 18, 12, 0, 0, tzinfo=UTC)
        dax_event = Event(
            player="dax", type="journal", data={"n": 2}, ts=base + timedelta(seconds=2)
        )
        rex_event = Event(
            player="rex", type="journal", data={"n": 1}, ts=base + timedelta(seconds=1)
        )

        for name, event in [("dax", dax_event), ("rex", rex_event)]:
            f = tmp_path / "events" / f"{name}.jsonl"
            f.write_text(json.dumps(event.to_dict()) + "\n")

        events = kira.poll()
        assert len(events) == 2
        assert events[0].data["n"] == 1  # rex (earlier)
        assert events[1].data["n"] == 2  # dax (later)


class TestFileLogAdapterPropose:
    def test_propose_writes_event_and_returns_pending(self, tmp_path):
        kira = FileLogAdapter(tmp_path, "kira")
        proposal = Proposal(player="kira", type="propose_truth", data={"category": "Cataclysm"})
        result = kira.propose(proposal)
        assert result == Resolution.PENDING
        lines = (tmp_path / "events" / "kira.jsonl").read_text().splitlines()
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["type"] == "propose_truth"
        assert obj["data"]["_proposal_id"] == proposal.id

    def test_resolve_writes_resolution_event(self, tmp_path):
        kira = FileLogAdapter(tmp_path, "kira")
        kira.resolve("some-proposal-id", accepted=True)
        lines = (tmp_path / "events" / "kira.jsonl").read_text().splitlines()
        assert len(lines) == 1
        obj = json.loads(lines[0])
        assert obj["type"] == "resolution"
        assert obj["data"]["ref"] == "some-proposal-id"
        assert obj["data"]["accepted"] is True


# ---------------------------------------------------------------------------
# GameState integration — sync field defaults to LocalAdapter
# ---------------------------------------------------------------------------


class TestGameStateSyncField:
    def test_game_state_has_sync_field(self):
        """GameState.sync defaults to LocalAdapter without any extra args."""
        from unittest.mock import MagicMock

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
        assert isinstance(state.sync, LocalAdapter)

    def test_game_state_accepts_custom_sync(self, tmp_path):
        from unittest.mock import MagicMock

        from soloquest.loop import GameState

        adapter = FileLogAdapter(tmp_path, "kira")
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
            sync=adapter,
        )
        assert state.sync is adapter
        assert isinstance(state.sync, SyncPort)
