"""Tests for command history persistence."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from prompt_toolkit.history import FileHistory


class TestFileHistory:
    def test_history_file_created_in_adventures_dir(self, tmp_path):
        """FileHistory creates .soloquest_history in adventures directory."""
        from soloquest.config import config
        from soloquest.engine.dice import DiceMode
        from soloquest.loop import run_session
        from soloquest.models.character import Character

        # Set up temporary config directory
        config.set_adventures_dir(tmp_path)

        character = Character(name="Test")
        vows = []
        session_count = 0
        dice_mode = DiceMode.DIGITAL

        # Mock the PromptSession to avoid actually prompting
        with (
            patch("soloquest.loop.PromptSession") as mock_prompt,
            patch("soloquest.loop.display"),
        ):
            # Mock prompt to immediately quit
            mock_session = MagicMock()
            mock_session.prompt.side_effect = EOFError
            mock_prompt.return_value = mock_session

            # Run session (will quit immediately due to EOFError)
            run_session(character, vows, session_count, dice_mode)

            # Verify FileHistory was created with correct path
            mock_prompt.assert_called_once()
            call_kwargs = mock_prompt.call_args[1]
            assert "history" in call_kwargs
            history = call_kwargs["history"]
            assert isinstance(history, FileHistory)

            # Verify the history file path is correct
            expected_path = tmp_path / ".soloquest_history"
            assert history.filename == str(expected_path)

    def test_history_persists_across_sessions(self, tmp_path):
        """Commands are persisted and available in next session."""
        from soloquest.config import config
        from soloquest.engine.dice import DiceMode
        from soloquest.loop import run_session
        from soloquest.models.character import Character

        # Set up temporary config directory
        config.set_adventures_dir(tmp_path)
        history_file = tmp_path / ".soloquest_history"

        character = Character(name="Test")
        vows = []
        session_count = 0
        dice_mode = DiceMode.DIGITAL

        # First session: verify FileHistory is created
        with (
            patch("soloquest.loop.PromptSession") as mock_prompt,
            patch("soloquest.loop.display"),
        ):
            mock_session = MagicMock()
            mock_session.prompt.side_effect = EOFError
            mock_prompt.return_value = mock_session

            run_session(character, vows, session_count, dice_mode)

            # Get the history object from first session
            call_kwargs = mock_prompt.call_args[1]
            history1 = call_kwargs["history"]
            assert isinstance(history1, FileHistory)
            assert history1.filename == str(history_file)

        # Second session: verify FileHistory points to same file
        with (
            patch("soloquest.loop.PromptSession") as mock_prompt2,
            patch("soloquest.loop.display"),
        ):
            mock_session2 = MagicMock()
            mock_session2.prompt.side_effect = EOFError
            mock_prompt2.return_value = mock_session2

            run_session(character, vows, session_count, dice_mode)

            # Verify FileHistory was initialized with the same file
            call_kwargs2 = mock_prompt2.call_args[1]
            history2 = call_kwargs2["history"]
            assert isinstance(history2, FileHistory)
            assert history2.filename == str(history_file)
            # Both sessions use the same history file
            assert history1.filename == history2.filename

    def test_adventures_dir_created_if_missing(self, tmp_path):
        """Adventures directory is created if it doesn't exist."""
        from soloquest.config import config
        from soloquest.engine.dice import DiceMode
        from soloquest.loop import run_session
        from soloquest.models.character import Character

        # Use a non-existent subdirectory
        non_existent = tmp_path / "new_adventures"
        config.set_adventures_dir(non_existent)

        character = Character(name="Test")
        vows = []
        session_count = 0
        dice_mode = DiceMode.DIGITAL

        with (
            patch("soloquest.loop.PromptSession") as mock_prompt,
            patch("soloquest.loop.display"),
        ):
            mock_session = MagicMock()
            mock_session.prompt.side_effect = EOFError
            mock_prompt.return_value = mock_session

            run_session(character, vows, session_count, dice_mode)

            # Verify directory was created
            assert non_existent.exists()
            assert non_existent.is_dir()

            # Verify history file can be created in this directory
            history_file = non_existent / ".soloquest_history"
            assert history_file.parent.exists()
