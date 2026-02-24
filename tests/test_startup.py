"""Tests for startup logic — sandbox mode and auto-resume."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestSandboxStartup:
    def test_sandbox_creates_wanderer_character(self):
        """No saves → sandbox creates Character('Wanderer')."""
        from wyrd.main import main

        with (
            patch("wyrd.main.list_saves", return_value=[]),
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.display"),
            patch("wyrd.loop.run_session") as mock_run,
        ):
            mock_args.return_value = MagicMock(
                new=False, adventures_dir=None, oneshot=[], char=None
            )
            main()

        mock_run.assert_called_once()
        character = mock_run.call_args[0][0]
        assert character.name == "Wanderer"

    def test_sandbox_does_not_call_new_character_flow(self):
        """No saves → sandbox does NOT call run_new_character_flow."""
        from wyrd.main import main

        with (
            patch("wyrd.main.list_saves", return_value=[]),
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.display"),
            patch("wyrd.loop.run_session"),
            patch("wyrd.commands.new_character.run_new_character_flow") as mock_flow,
        ):
            mock_args.return_value = MagicMock(
                new=False, adventures_dir=None, oneshot=[], char=None
            )
            main()

        mock_flow.assert_not_called()

    def test_new_flag_triggers_sandbox(self):
        """--new flag → sandbox mode even when saves exist."""
        from wyrd.main import main

        with (
            patch("wyrd.main.list_saves", return_value=["Kira"]),
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.display"),
            patch("wyrd.loop.run_session") as mock_run,
        ):
            mock_args.return_value = MagicMock(new=True, adventures_dir=None, oneshot=[], char=None)
            main()

        character = mock_run.call_args[0][0]
        assert character.name == "Wanderer"

    def test_sandbox_passes_empty_vows(self):
        """Sandbox mode starts with empty vows list."""
        from wyrd.main import main

        with (
            patch("wyrd.main.list_saves", return_value=[]),
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.display"),
            patch("wyrd.loop.run_session") as mock_run,
        ):
            mock_args.return_value = MagicMock(
                new=False, adventures_dir=None, oneshot=[], char=None
            )
            main()

        vows = mock_run.call_args[0][1]
        assert vows == []


class TestAutoResumeStartup:
    def test_auto_resume_loads_most_recent(self):
        """With saves → auto-resumes most recent (unchanged UX)."""
        from wyrd.engine.dice import DiceMode
        from wyrd.main import main
        from wyrd.models.character import Character

        saved_character = Character("Kira")

        with (
            patch("wyrd.main.list_saves", return_value=["Kira"]),
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.load_most_recent") as mock_load,
            patch("wyrd.main.display"),
            patch("wyrd.loop.run_session") as mock_run,
        ):
            mock_args.return_value = MagicMock(
                new=False, adventures_dir=None, oneshot=[], char=None
            )
            mock_load.return_value = (saved_character, [], 3, DiceMode.DIGITAL, None)
            main()

        character = mock_run.call_args[0][0]
        assert character.name == "Kira"

    def test_auto_resume_not_called_when_new_flag(self):
        """--new flag → load_most_recent is NOT called."""
        from wyrd.main import main

        with (
            patch("wyrd.main.list_saves", return_value=["Kira"]),
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.load_most_recent") as mock_load,
            patch("wyrd.main.display"),
            patch("wyrd.loop.run_session"),
        ):
            mock_args.return_value = MagicMock(new=True, adventures_dir=None, oneshot=[], char=None)
            main()

        mock_load.assert_not_called()

    def test_corrupted_save_returns_early(self):
        """Corrupted save → error message, run_session not called."""
        from wyrd.main import main

        with (
            patch("wyrd.main.list_saves", return_value=["Kira"]),
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.load_most_recent", return_value=None),
            patch("wyrd.main.display") as mock_display,
            patch("wyrd.loop.run_session") as mock_run,
        ):
            mock_args.return_value = MagicMock(
                new=False, adventures_dir=None, oneshot=[], char=None
            )
            main()

        mock_run.assert_not_called()
        mock_display.error.assert_called_once()
