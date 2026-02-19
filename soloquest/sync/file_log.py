"""FileLogAdapter — per-player JSONL event log for co-op campaigns.

Each player appends to their own JSONL file. Reading merges all player files
by timestamp. Zero locking needed — each player owns exactly one file.

Directory layout:
    {campaign_dir}/events/{player_id}.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path

from soloquest.sync.models import Event, Proposal, Resolution


class FileLogAdapter:
    """SyncPort adapter backed by per-player JSONL files.

    Appends are lock-free because each player writes only their own file.
    poll() reads all other players' files from the last-seen byte offset,
    merges by timestamp, and deduplicates by event UUID.
    """

    def __init__(self, campaign_dir: Path, player_id: str) -> None:
        self._player_id = player_id
        self._events_dir = campaign_dir / "events"
        self._events_dir.mkdir(parents=True, exist_ok=True)
        self._own_file = self._events_dir / f"{player_id}.jsonl"
        # Map of player_id → byte offset for incremental reads
        self._read_offsets: dict[str, int] = {}
        # Set of already-seen event UUIDs for deduplication
        self._seen_ids: set[str] = set()

    @property
    def player_id(self) -> str:
        return self._player_id

    def publish(self, event: Event) -> None:
        """Append a JSON line to this player's event file."""
        with self._own_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def poll(self) -> list[Event]:
        """Return new events from all other players, merged by timestamp."""
        new_events: list[Event] = []

        for path in self._events_dir.glob("*.jsonl"):
            player = path.stem
            if player == self._player_id:
                continue

            offset = self._read_offsets.get(player, 0)
            events, new_offset = self._read_from(path, offset)
            self._read_offsets[player] = new_offset
            new_events.extend(events)

        # Sort merged events by timestamp, then player for determinism
        new_events.sort(key=lambda e: (e.ts, e.player))

        # Deduplicate by UUID (handles cloud-sync conflict copies)
        result: list[Event] = []
        for event in new_events:
            if event.id not in self._seen_ids:
                self._seen_ids.add(event.id)
                result.append(event)

        return result

    def propose(self, proposal: Proposal) -> Resolution:
        """Publish a proposal event. Returns PENDING (caller polls for response)."""
        event = Event(
            player=self._player_id,
            type=proposal.type,
            data={**proposal.data, "_proposal_id": proposal.id},
            id=proposal.id,
        )
        self.publish(event)
        return Resolution.PENDING

    def resolve(self, proposal_id: str, accepted: bool) -> None:
        """Publish an accept/reject event referencing a proposal."""
        event = Event(
            player=self._player_id,
            type="resolution",
            data={
                "ref": proposal_id,
                "accepted": accepted,
            },
        )
        self.publish(event)

    def _read_from(self, path: Path, offset: int) -> tuple[list[Event], int]:
        """Read new lines from path starting at byte offset.

        Defensively skips malformed lines. Returns (events, new_offset).
        """
        if not path.exists():
            return [], offset

        events: list[Event] = []
        try:
            with path.open("r", encoding="utf-8") as f:
                f.seek(offset)
                for raw_line in f:
                    line = raw_line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        events.append(Event.from_dict(data))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        # Skip malformed lines — cloud sync can corrupt partial writes
                        continue
                new_offset = f.tell()
        except OSError:
            return [], offset

        return events, new_offset
