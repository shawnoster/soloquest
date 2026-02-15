"""Tab completion for slash commands."""

from __future__ import annotations

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

from soloquest.commands.registry import COMMAND_ALIASES, COMMAND_HELP


class CommandCompleter(Completer):
    """Completer for /commands with support for aliases."""

    def __init__(self) -> None:
        # Build list of all commands (full names + aliases)
        self.commands: list[str] = []
        self.command_meta: dict[str, str] = {}

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
        word = document.get_word_before_cursor()

        # Only complete if we're typing a command (starts with /)
        if not text.startswith("/"):
            return []

        # If we have spaces, only complete the first word (the command itself)
        if " " in text.strip():
            return []

        # Find matching commands
        completions = []
        for cmd in self.commands:
            if cmd.startswith(text.lower()):
                # Calculate how many characters to complete
                start_position = -len(word) if word else 0
                completions.append(
                    Completion(
                        text=cmd,
                        start_position=start_position,
                        display_meta=self.command_meta.get(cmd, ""),
                    )
                )

        return completions
