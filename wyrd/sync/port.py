"""SyncPort — the abstract interface all adapters implement."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from wyrd.sync.models import Event, Proposal, Resolution


@runtime_checkable
class SyncPort(Protocol):
    """Port for broadcasting and receiving campaign events.

    Implementations:
      LocalAdapter  — no-op, single-player (default)
      FileLogAdapter — per-player JSONL files on shared filesystem
    """

    @property
    def player_id(self) -> str:
        """The current player's identifier."""
        ...

    def publish(self, event: Event) -> None:
        """Append an event to this player's log."""
        ...

    def poll(self) -> list[Event]:
        """Return new events from other players since last poll."""
        ...

    def propose(self, proposal: Proposal) -> Resolution:
        """Start a consensus workflow and return the resolution.

        In LocalAdapter this is a synchronous no-op (auto-accepted).
        In FileLogAdapter this writes a proposal event and polls for a response.
        """
        ...

    def resolve(self, proposal_id: str, accepted: bool) -> None:
        """Accept or reject a pending proposal from another player."""
        ...
