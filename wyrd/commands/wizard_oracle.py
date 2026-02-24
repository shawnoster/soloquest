"""In-wizard oracle lookup helpers.

Provides three oracle access mechanisms during wizard prompts:
  - Approach 1: '?action theme' prefix on any wizard text input
  - Approach 5: '/oracle action theme' or '/o ...' prefix on any wizard text input
  - Approach 2: Alt+O keybinding (any PromptSession-based wizard prompt)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings

if TYPE_CHECKING:
    from wyrd.engine.oracles import OracleTable
    from wyrd.loop import GameState


def check_oracle_prefix(raw_input: str, state: GameState | None) -> str | None:
    """Intercept oracle query prefixes from wizard prompt input.

    If raw_input starts with '?', '/oracle ', or '/o ', runs the oracle query
    and returns None (signaling the caller to re-prompt the same question).

    If raw_input is exactly '?', '/oracle', or '/o' with no table specified,
    shows a usage hint and returns None.

    If state is None, shows a warning and returns None for oracle prefixes.

    Returns:
        None — oracle ran (or hint shown); caller should re-prompt.
        str  — original raw_input, unchanged; caller should proceed normally.
    """
    from wyrd.ui import display

    stripped = raw_input.strip()
    lower = stripped.lower()

    is_question = lower.startswith("?")
    is_oracle_cmd = lower.startswith("/oracle ") or lower.startswith("/o ")
    is_bare_oracle = lower in ("?", "/oracle", "/o")

    if not (is_question or is_oracle_cmd or is_bare_oracle):
        return raw_input  # not an oracle query — pass through unchanged

    if is_bare_oracle:
        display.info("Usage: ?action theme  or  /oracle action theme")
        return None

    if state is None:
        display.warn("Oracle lookup is not available here (no game state).")
        return None

    if is_question:
        args_str = stripped[1:].strip()
    else:
        _, _, args_str = stripped.partition(" ")
        args_str = args_str.strip()

    if not args_str:
        display.info("Usage: ?action theme  or  /oracle action theme")
        return None

    _run_inline_oracle(state, args_str.split())
    return None


def _run_inline_oracle(state: GameState, args: list[str]) -> None:
    """Execute an oracle lookup using the full handle_oracle pipeline."""
    from wyrd.commands.oracle import handle_oracle

    handle_oracle(state, args, flags=set())


class _OracleOnlyCompleter(Completer):
    """Tab-completion for oracle table names (used by the Alt+O sub-prompt)."""

    def __init__(self, oracles: dict[str, OracleTable]) -> None:
        self.oracles = oracles

    def get_completions(self, document, complete_event):  # type: ignore[override]
        current = document.text_before_cursor
        arg = current.lower()
        for key, table in sorted(self.oracles.items()):
            if not current or arg in key.lower() or arg in table.name.lower():
                yield Completion(
                    text=key,
                    start_position=-len(current) if current else 0,
                    display_meta=table.name,
                )


def make_oracle_key_bindings(
    state: GameState | None,
    oracles: dict[str, OracleTable] | None = None,
) -> KeyBindings:
    """Build KeyBindings with an Alt+O handler for wizard PromptSessions.

    When Alt+O is pressed mid-prompt:
      - run_in_terminal opens a sub-prompt 'Oracle: ' without disturbing the buffer
      - Tab-completion works on oracle table names
      - The oracle result is displayed; focus returns to the original prompt
      - The current buffer content is preserved
    """
    kb = KeyBindings()
    _oracles: dict[str, OracleTable] = oracles or {}  # type: ignore[assignment]

    @kb.add("escape", "o")  # prompt_toolkit encodes Alt+O as Escape followed by 'o'
    def _handle_alt_o(event) -> None:  # type: ignore[no-untyped-def]
        from prompt_toolkit.shortcuts import run_in_terminal

        def _run() -> None:
            from prompt_toolkit import PromptSession as _PS

            sub_session = _PS(
                completer=_OracleOnlyCompleter(_oracles),
                complete_while_typing=False,
            )
            try:
                raw = sub_session.prompt("Oracle: ").strip()
            except (KeyboardInterrupt, EOFError):
                return
            if not raw:
                return
            if state is not None:
                _run_inline_oracle(state, raw.split())
            else:
                from wyrd.ui import display

                display.warn("Oracle lookup is not available here (no game state).")

        run_in_terminal(_run)

    return kb
