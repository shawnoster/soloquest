"""Oracle interpretation commands — /interpret and /accept."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape

from wyrd.sync.models import Event
from wyrd.ui import display
from wyrd.ui.theme import COOP_INTERPRET

if TYPE_CHECKING:
    from wyrd.loop import GameState


def handle_interpret(state: GameState, args: list[str], flags: set[str]) -> None:
    """Propose an interpretation of the last oracle roll.

    Usage:
        /interpret [text]   — propose what the oracle means in fiction

    In solo mode, the interpretation is logged immediately as a note.
    In co-op mode, it is also published to the sync layer so partners can see
    and accept it via /accept.
    """
    if not args:
        display.warn("Usage: /interpret [your interpretation]")
        return

    text = " ".join(args)
    player = state.character.name

    # Log interpretation to session immediately (both solo and co-op)
    state.session.add_note(f"[Interpretation] {text}", player=player)
    display.console.print(
        f"  [{COOP_INTERPRET}]└[/{COOP_INTERPRET}]  💬 [dim]interpretation logged:[/dim]  [italic]{escape(text)}[/italic]"
    )

    # In co-op, publish as an interpret event so partners can see it
    if state.campaign is not None:
        event = Event(
            player=player,
            type="interpret",
            data={
                "text": text,
                **({"ref": state.last_oracle_event_id} if state.last_oracle_event_id else {}),
            },
        )
        state.sync.publish(event)


def handle_accept(state: GameState, args: list[str], flags: set[str]) -> None:
    """Accept a pending partner interpretation and log it to the session.

    Usage:
        /accept             — accept the most recent partner interpretation

    In solo mode this is a no-op (all interpretations are auto-accepted).
    In co-op mode, logs the pending interpretation as a note and publishes
    an accept_interpretation event.
    """
    if state.campaign is None:
        display.info("  (Solo mode — interpretations are accepted automatically.)")
        return

    event = state.pending_partner_interpretation
    if event is None:
        display.info("  No pending partner interpretation. Use /sync to check for activity.")
        return

    text = event.data.get("text", "")
    player = state.character.name

    # Log the accepted interpretation to this player's session
    state.session.add_note(f"[Interpretation accepted] {text}", player=player)
    display.success(f"Interpretation accepted: {text}")

    # Publish acceptance event
    state.sync.publish(
        Event(
            player=player,
            type="accept_interpretation",
            data={"ref": event.id, "text": text},
        )
    )

    # Clear the pending interpretation
    state.pending_partner_interpretation = None
