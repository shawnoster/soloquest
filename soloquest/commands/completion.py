"""Tab completion for slash commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

from soloquest.commands.registry import COMMAND_ALIASES, COMMAND_HELP

if TYPE_CHECKING:
    from soloquest.engine.oracles import OracleTable


class CommandCompleter(Completer):
    """Completer for /commands with support for aliases, oracle tables, moves, and assets."""

    def __init__(
        self,
        oracles: dict[str, OracleTable] | None = None,
        moves: dict | None = None,
        assets: dict | None = None,
    ) -> None:
        # Build list of all commands (full names + aliases)
        self.commands: list[str] = []
        self.command_meta: dict[str, str] = {}
        self.oracles = oracles or {}
        self.moves = moves or {}
        self.assets = assets or {}

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

    def get_completions(self, document: Document, complete_event: object) -> list[Completion]:
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
        return sorted(completions, key=lambda c: c.text)

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

        # Complete asset names
        if command == "/asset":
            return self._complete_assets(current_arg)

        # Complete guide steps and commands
        if command == "/guide":
            return self._complete_guide_args(current_arg)

        # Complete truths subcommands
        if command == "/truths":
            return self._complete_truths_args(current_arg)

        return []

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase and replace separators for fuzzy matching."""
        return text.lower().replace("_", " ").replace("-", " ")

    @staticmethod
    def _make_completion(text: str, display_meta: str, current_arg: str) -> Completion:
        """Build a single Completion with correct start position."""
        return Completion(
            text=text,
            start_position=-len(current_arg) if current_arg else 0,
            display_meta=display_meta,
        )

    def _complete_options(self, current_arg: str, options: dict[str, str]) -> list[Completion]:
        """Complete from a fixed dict of {option: description} pairs."""
        completions = [
            self._make_completion(option, description, current_arg)
            for option, description in options.items()
            if not current_arg or current_arg.lower() in option.lower()
        ]
        return sorted(completions, key=lambda c: c.text)

    def _complete_oracle_tables(self, current_arg: str) -> list[Completion]:
        """Complete oracle table names."""
        arg = current_arg.lower()
        completions = [
            self._make_completion(key, table.name, current_arg)
            for key, table in self.oracles.items()
            if not current_arg or arg in key.lower() or arg in table.name.lower()
        ]
        return sorted(completions, key=lambda c: c.text)

    def _complete_moves(self, current_arg: str) -> list[Completion]:
        """Complete move names and category filters."""
        if ":" in current_arg:
            prefix, partial_value = current_arg.split(":", 1)
            if prefix.lower() in ("category", "type", "cat"):
                return self._complete_move_categories(partial_value, prefix)

        arg_norm = self._normalize(current_arg)
        completions = [
            self._make_completion(key, move_data.get("name", ""), current_arg)
            for key, move_data in self.moves.items()
            if not current_arg
            or arg_norm in self._normalize(key)
            or arg_norm in self._normalize(move_data.get("name", ""))
        ]
        return sorted(completions, key=lambda c: c.text)

    def _complete_move_categories(self, partial_value: str, prefix: str) -> list[Completion]:
        """Complete category names for the category: filter syntax."""
        categories = sorted(
            {move_data.get("category", "") for move_data in self.moves.values()} - {""}
        )
        completions = [
            self._make_completion(cat, f"{prefix}:{cat}", partial_value)
            for cat in categories
            if not partial_value or partial_value.lower() in cat.lower()
        ]
        return sorted(completions, key=lambda c: c.text)

    def _complete_assets(self, current_arg: str) -> list[Completion]:
        """Complete asset names."""
        arg_norm = self._normalize(current_arg)
        completions = [
            self._make_completion(
                key,
                asset.name if hasattr(asset, "name") else key,
                current_arg,
            )
            for key, asset in self.assets.items()
            if not current_arg
            or arg_norm in self._normalize(key)
            or arg_norm in self._normalize(asset.name if hasattr(asset, "name") else key)
        ]
        return sorted(completions, key=lambda c: c.text)

    def _complete_guide_args(self, current_arg: str) -> list[Completion]:
        """Complete guide arguments (commands and steps)."""
        return self._complete_options(
            current_arg,
            {
                "start": "Enter guided mode (step-by-step wizard)",
                "stop": "Exit guided mode",
                "envision": "Learn about envisioning and describing your story",
                "oracle": "Learn about asking the oracle",
                "move": "Learn about making moves",
                "outcome": "Learn about interpreting outcomes",
            },
        )

    def _complete_truths_args(self, current_arg: str) -> list[Completion]:
        """Complete truths subcommands."""
        return self._complete_options(
            current_arg,
            {
                "start": "Start or restart the Choose Your Truths wizard",
                "show": "Display your current campaign truths",
            },
        )
