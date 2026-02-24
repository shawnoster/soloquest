"""LocalAdapter — no-op SyncPort for single-player mode.

All methods are zero-overhead. Proposals auto-accept. Poll returns nothing.
Single-player code never touches the event log.
"""

from __future__ import annotations

from wyrd.sync.models import Event, Proposal, Resolution


class LocalAdapter:
    """No-op sync adapter for single-player mode.

    Satisfies the SyncPort protocol without any file I/O or network access.
    """

    def __init__(self, player_id: str) -> None:
        self._player_id = player_id

    @property
    def player_id(self) -> str:
        return self._player_id

    def publish(self, event: Event) -> None:
        """No-op — single-player has no one to broadcast to."""

    def poll(self) -> list[Event]:
        """No-op — single-player has no partners to receive from."""
        return []

    def propose(self, proposal: Proposal) -> Resolution:
        """Auto-accept — single-player needs no consensus."""
        return Resolution.ACCEPTED

    def resolve(self, proposal_id: str, accepted: bool) -> None:
        """No-op — single-player has no pending proposals."""
