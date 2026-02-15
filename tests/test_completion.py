"""Tests for command tab completion."""

from __future__ import annotations

from prompt_toolkit.document import Document

from soloquest.commands.completion import CommandCompleter


class TestCommandCompleter:
    def test_completes_move_command(self):
        completer = CommandCompleter()
        doc = Document("/mov", cursor_position=4)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) == 1
        assert completions[0].text == "/move"

    def test_completes_alias(self):
        completer = CommandCompleter()
        doc = Document("/m", cursor_position=2)
        completions = list(completer.get_completions(doc, None))

        # Should match /m (alias for move) and /move and /momentum
        assert len(completions) == 3
        commands = {c.text for c in completions}
        assert "/m" in commands
        assert "/move" in commands
        assert "/momentum" in commands

    def test_shows_meta_for_commands(self):
        completer = CommandCompleter()
        doc = Document("/help", cursor_position=5)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) == 1
        assert completions[0].text == "/help"
        # display_meta is a FormattedText, check if it contains the string
        assert "show help" in str(completions[0].display_meta)

    def test_shows_alias_meta(self):
        completer = CommandCompleter()
        doc = Document("/h", cursor_position=2)
        completions = list(completer.get_completions(doc, None))

        # Find /h completion
        h_completion = [c for c in completions if c.text == "/h"][0]
        # display_meta is a FormattedText, check if it contains the string
        assert "alias for /help" in str(h_completion.display_meta)

    def test_no_completions_without_slash(self):
        completer = CommandCompleter()
        doc = Document("move", cursor_position=4)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) == 0

    def test_no_completions_after_space(self):
        completer = CommandCompleter()
        doc = Document("/move face", cursor_position=10)
        completions = list(completer.get_completions(doc, None))

        # Don't complete arguments, only the command itself
        assert len(completions) == 0

    def test_completes_all_commands_with_slash_only(self):
        completer = CommandCompleter()
        doc = Document("/", cursor_position=1)
        completions = list(completer.get_completions(doc, None))

        # Should get all commands + aliases
        assert len(completions) > 15  # At least 15 commands available

    def test_case_insensitive_completion(self):
        completer = CommandCompleter()
        doc = Document("/MOV", cursor_position=4)
        completions = list(completer.get_completions(doc, None))

        assert len(completions) == 1
        assert completions[0].text == "/move"
