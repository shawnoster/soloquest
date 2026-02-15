"""Tab completion for slash commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

from soloquest.commands.registry import COMMAND_ALIASES, COMMAND_HELP

if TYPE_CHECKING:
    from soloquest.engine.oracles import OracleTable


class CommandCompleter(Completer):
    """Completer for /commands with support for aliases, oracle tables, and moves."""

    def __init__(
        self,
        oracles: dict[str, OracleTable] | None = None,
        moves: dict | None = None,
    ) -> None:
        # Build list of all commands (full names + aliases)
        self.commands: list[str] = []
        self.command_meta: dict[str, str] = {}
        self.oracles = oracles or {}
        self.moves = moves or {}

        # Add full command names with descriptions
        for cmd, help_text in COMMAND_HELP.items():
            self.commands.append(f"/{cmd}")
            # Extract short description from help text (everything after '—')
            if "—" in help_text:
                self.command_meta[f"/{cmd}"] = help_text.split("—", 1)[1].strip()
            else:
                self.command_meta[f"/{cmd}"] = ""

        # Add aliases with their target command
        for alias, target in COMMAND_ALIASES.items():
            self.commands.append(f"/{alias}")
            self.command_meta[f"/{alias}"] = f"alias for /{target}"

    def get_completions(
        self, document: Document, complete_event: object
    ) -> list[Completion]:
        """Return completions for the current input."""
        text = document.text_before_cursor

        # Only complete if we're typing a command (starts with /)
        if not text.startswith("/"):
            return []

        # Check if we're completing arguments after a command
        if " " in text:
            return self._complete_arguments(text)

        # Complete the command itself
        return self._complete_command(text)

    def _complete_command(self, text: str) -> list[Completion]:
        """Complete slash command names."""
        completions = []
        for cmd in self.commands:
            if cmd.startswith(text.lower()):
                # Calculate how many characters to complete
                # Use text (not word) to include the leading /
                start_position = -len(text)
                completions.append(
                    Completion(
                        text=cmd,
                        start_position=start_position,
                        display_meta=self.command_meta.get(cmd, ""),
                    )
                )
        return completions

    def _complete_arguments(self, text: str) -> list[Completion]:
        """Complete arguments for specific commands."""
        # Parse out the command and current argument
        parts = text.split()
        if not parts:
            return []

        command = parts[0].lower()

        # Get the current partial argument being typed
        current_arg = text.split()[-1] if not text.endswith(" ") else ""

        # Complete oracle tables
        if command in ["/oracle", "/o"]:
            return self._complete_oracle_tables(current_arg)

        # Complete move names
        if command in ["/move", "/m"]:
            return self._complete_moves(current_arg)

        return []

    def _complete_oracle_tables(self, current_arg: str) -> list[Completion]:
        """Complete oracle table names."""
        completions = []
        for key, table in self.oracles.items():
            # Match against both key and name (show all if current_arg is empty)
            if not current_arg or current_arg.lower() in key.lower() or current_arg.lower() in table.name.lower():
                start_position = -len(current_arg) if current_arg else 0
                # Prefer the key for completion, show the full name as meta
                completions.append(
                    Completion(
                        text=key,
                        start_position=start_position,
                        display_meta=table.name,
                    )
                )
        return completions

    def _complete_moves(self, current_arg: str) -> list[Completion]:
        """Complete move names."""
        completions = []
        for key, move_data in self.moves.items():
            move_name = move_data.get("name", "")
            # Match against both key and name (show all if current_arg is empty)
            # Normalize for matching (spaces/underscores/hyphens)
            key_normalized = key.replace("_", " ").replace("-", " ")
            name_normalized = move_name.lower().replace("_", " ").replace("-", " ")
            arg_normalized = current_arg.lower().replace("_", " ").replace("-", " ")

            if not current_arg or arg_normalized in key_normalized or arg_normalized in name_normalized:
                start_position = -len(current_arg) if current_arg else 0
                # Prefer the key for completion, show the full name as meta
                completions.append(
                    Completion(
                        text=key,
                        start_position=start_position,
                        display_meta=move_name,
                    )
                )
        return completions
