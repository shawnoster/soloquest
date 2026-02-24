"""Tests for CLI one-liner mode (Issue #122)."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wyrd.engine.dice import DiceMode
from wyrd.models.character import Character
from wyrd.models.session import Session
from wyrd.models.vow import Vow
from wyrd.state import save as save_module
from wyrd.state.save import list_saves_paths, load_by_name, save_game

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_saves(tmp_path, monkeypatch):
    """Redirect saves to a temp directory."""
    tmp_saves_dir = tmp_path / "saves"
    monkeypatch.setattr(save_module, "_saves_dir", lambda: tmp_saves_dir)
    return tmp_saves_dir


@pytest.fixture
def sample_character():
    return Character("Robin")


@pytest.fixture
def saved_robin(tmp_saves, sample_character):
    """Persist Robin to the tmp saves dir and return the path."""
    save_game(sample_character, [], 1, DiceMode.DIGITAL)
    return tmp_saves / "robin.json"


# ---------------------------------------------------------------------------
# list_saves_paths
# ---------------------------------------------------------------------------


class TestListSavesPaths:
    def test_returns_empty_list_when_no_saves_dir(self, tmp_path):
        missing = tmp_path / "no_such_dir"
        result = list_saves_paths(missing)
        assert result == []

    def test_excludes_bak_files(self, tmp_saves, sample_character):
        save_game(sample_character, [], 1, DiceMode.DIGITAL)
        # Save again to generate .bak
        save_game(sample_character, [], 2, DiceMode.DIGITAL)
        paths = list_saves_paths(tmp_saves)
        assert all(p.suffix == ".json" for p in paths)
        assert not any(".bak" in p.name for p in paths)

    def test_returns_sorted_by_mtime_desc(self, tmp_saves):

        tmp_saves.mkdir(parents=True, exist_ok=True)
        older = tmp_saves / "old.json"
        newer = tmp_saves / "new.json"
        older.write_text("{}", encoding="utf-8")
        time.sleep(0.01)
        newer.write_text("{}", encoding="utf-8")

        paths = list_saves_paths(tmp_saves)
        assert paths[0].name == "new.json"
        assert paths[1].name == "old.json"

    def test_uses_default_saves_dir_when_none(self, tmp_saves):
        """When save_dir=None, falls back to _saves_dir() (monkeypatched)."""
        save_game(Character("Anya"), [], 1, DiceMode.DIGITAL)
        paths = list_saves_paths(None)
        assert len(paths) == 1


# ---------------------------------------------------------------------------
# load_by_name
# ---------------------------------------------------------------------------


class TestLoadByName:
    def test_found_returns_correct_character(self, tmp_saves, saved_robin):
        result = load_by_name("Robin", tmp_saves)
        assert result is not None
        character, vows, session_count, dice_mode, session = result
        assert character.name == "Robin"

    def test_case_insensitive_lookup(self, tmp_saves, saved_robin):
        result = load_by_name("robin", tmp_saves)
        assert result is not None
        assert result[0].name == "Robin"

    def test_not_found_returns_none(self, tmp_saves):
        tmp_saves.mkdir(parents=True, exist_ok=True)
        result = load_by_name("Nonexistent", tmp_saves)
        assert result is None

    def test_no_saves_dir_returns_none(self, tmp_path):
        result = load_by_name("Robin", tmp_path / "missing")
        assert result is None

    def test_corrupted_save_returns_none(self, tmp_saves):
        tmp_saves.mkdir(parents=True, exist_ok=True)
        (tmp_saves / "ghost.json").write_text("{ bad json", encoding="utf-8")
        result = load_by_name("Ghost", tmp_saves)
        assert result is None

    def test_returns_vows_and_session_count(self, tmp_saves, sample_character):
        from wyrd.models.vow import VowRank

        vow = Vow("Find the truth", VowRank.DANGEROUS)
        save_game(sample_character, [vow], 5, DiceMode.DIGITAL)
        result = load_by_name("Robin", tmp_saves)
        assert result is not None
        _, vows, session_count, _, _ = result
        assert session_count == 5
        assert len(vows) == 1


# ---------------------------------------------------------------------------
# run_oneshot
# ---------------------------------------------------------------------------


class TestRunOneshot:
    def _make_state_components(self):
        character = Character("Robin")
        vows: list[Vow] = []
        session_count = 1
        dice_mode = DiceMode.DIGITAL
        session = None
        return character, vows, session_count, dice_mode, session

    def test_run_oneshot_oracle_calls_handle_oracle(self):
        from wyrd.loop import run_oneshot

        character, vows, session_count, dice_mode, session = self._make_state_components()

        with (
            patch("wyrd.loop._build_game_state") as mock_build,
            patch("wyrd.loop._dispatch_command") as mock_dispatch,
            patch("wyrd.loop._autosave_state"),
        ):
            mock_state = MagicMock()
            mock_build.return_value = mock_state

            result = run_oneshot(
                character, vows, session_count, dice_mode, session, "oracle", ["action"], set()
            )

        assert result == 0
        mock_dispatch.assert_called_once_with(mock_state, "oracle", ["action"], set())

    def test_run_oneshot_roll_calls_handle_roll(self):
        from wyrd.loop import run_oneshot

        character, vows, session_count, dice_mode, session = self._make_state_components()

        with (
            patch("wyrd.loop._build_game_state") as mock_build,
            patch("wyrd.loop._dispatch_command") as mock_dispatch,
            patch("wyrd.loop._autosave_state"),
        ):
            mock_state = MagicMock()
            mock_build.return_value = mock_state

            result = run_oneshot(
                character, vows, session_count, dice_mode, session, "roll", ["d100"], set()
            )

        assert result == 0
        mock_dispatch.assert_called_once_with(mock_state, "roll", ["d100"], set())

    def test_run_oneshot_forces_digital_dice(self):
        from wyrd.loop import run_oneshot

        character, vows, session_count, _, session = self._make_state_components()

        with (
            patch("wyrd.loop._build_game_state") as mock_build,
            patch("wyrd.loop._dispatch_command"),
            patch("wyrd.loop._autosave_state"),
        ):
            mock_build.return_value = MagicMock()

            run_oneshot(
                character,
                vows,
                session_count,
                DiceMode.PHYSICAL,
                session,
                "oracle",
                ["action"],
                set(),
            )

        # dice_mode arg to _build_game_state must be DIGITAL regardless
        _, _, _, dice_mode_used, _ = mock_build.call_args[0]
        assert dice_mode_used == DiceMode.DIGITAL

    def test_run_oneshot_autosaves(self):
        from wyrd.loop import run_oneshot

        character, vows, session_count, dice_mode, session = self._make_state_components()

        with (
            patch("wyrd.loop._build_game_state") as mock_build,
            patch("wyrd.loop._dispatch_command"),
            patch("wyrd.loop._autosave_state") as mock_autosave,
        ):
            mock_state = MagicMock()
            mock_build.return_value = mock_state

            run_oneshot(
                character, vows, session_count, dice_mode, session, "oracle", ["action"], set()
            )

        mock_autosave.assert_called_once_with(mock_state)

    def test_run_oneshot_creates_session_when_none(self):
        from wyrd.loop import run_oneshot

        character, vows, session_count, dice_mode, _ = self._make_state_components()

        with (
            patch("wyrd.loop._build_game_state") as mock_build,
            patch("wyrd.loop._dispatch_command"),
            patch("wyrd.loop._autosave_state"),
        ):
            mock_build.return_value = MagicMock()

            run_oneshot(
                character,
                vows,
                session_count,
                dice_mode,
                None,  # session=None
                "roll",
                ["d6"],
                set(),
            )

        # Session passed to _build_game_state should not be None
        _, _, _, _, session_arg = mock_build.call_args[0]
        assert isinstance(session_arg, Session)


# ---------------------------------------------------------------------------
# main() one-liner dispatch integration
# ---------------------------------------------------------------------------


class TestMainOneshotDispatch:
    def _mock_args(self, oneshot, char=None):
        return MagicMock(adventures_dir=None, new=False, oneshot=oneshot, char=char)

    def test_main_calls_run_oneshot_for_oracle(self):
        from wyrd.engine.dice import DiceMode
        from wyrd.main import main
        from wyrd.models.character import Character

        character = Character("Wanderer")

        with (
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.load_most_recent") as mock_load,
            patch("wyrd.main.load_by_name"),
            patch("wyrd.main.list_saves_paths", return_value=[]),
            patch("wyrd.loop.run_oneshot", return_value=0) as mock_oneshot,
        ):
            mock_args.return_value = self._mock_args(["oracle", "action"])
            mock_load.return_value = (character, [], 1, DiceMode.DIGITAL, None)

            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        mock_oneshot.assert_called_once()
        cmd = mock_oneshot.call_args[0][5]
        args = mock_oneshot.call_args[0][6]
        assert cmd == "oracle"
        assert args == ["action"]

    def test_main_parses_flags_from_oneshot_tokens(self):
        from wyrd.engine.dice import DiceMode
        from wyrd.main import main
        from wyrd.models.character import Character

        character = Character("Wanderer")

        with (
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.load_most_recent") as mock_load,
            patch("wyrd.main.load_by_name"),
            patch("wyrd.main.list_saves_paths", return_value=[]),
            patch("wyrd.loop.run_oneshot", return_value=0) as mock_oneshot,
        ):
            mock_args.return_value = self._mock_args(["roll", "d100", "--verbose"])
            mock_load.return_value = (character, [], 1, DiceMode.DIGITAL, None)

            with pytest.raises(SystemExit):
                main()

        flags = mock_oneshot.call_args[0][7]
        assert "verbose" in flags

    def test_main_char_flag_unknown_exits_1(self, tmp_path):
        from wyrd.main import main

        with (
            patch("wyrd.main.parse_args") as mock_args,
            patch("wyrd.main.load_by_name", return_value=None),
            patch("wyrd.main.list_saves_paths", return_value=[]),
            patch("wyrd.main.display"),
            patch("wyrd.config.config") as mock_cfg,
        ):
            mock_cfg.adventures_dir = tmp_path
            mock_cfg.saves_dir.return_value = tmp_path / "saves"
            mock_args.return_value = self._mock_args(["oracle", "action"], char="Unknown")

            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1

    def test_main_char_flag_loads_named_character(self):
        from wyrd.engine.dice import DiceMode
        from wyrd.main import main
        from wyrd.models.character import Character

        robin = Character("Robin")

        with (
            patch("wyrd.main.parse_args") as mock_args,
            patch(
                "wyrd.main.load_by_name", return_value=(robin, [], 2, DiceMode.DIGITAL, None)
            ),
            patch("wyrd.main.load_most_recent") as mock_load_recent,
            patch("wyrd.loop.run_oneshot", return_value=0) as mock_oneshot,
            patch("wyrd.config.config") as mock_cfg,
        ):
            mock_cfg.adventures_dir = Path("/tmp")
            mock_cfg.saves_dir.return_value = Path("/tmp/saves")
            mock_args.return_value = self._mock_args(["oracle", "action"], char="Robin")

            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 0
        mock_load_recent.assert_not_called()
        char_arg = mock_oneshot.call_args[0][0]
        assert char_arg.name == "Robin"
