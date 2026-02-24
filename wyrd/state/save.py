"""JSON persistence for character saves."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

from wyrd.config import config
from wyrd.engine.dice import DiceMode
from wyrd.models.character import Character
from wyrd.models.session import Session
from wyrd.models.vow import Vow


def _saves_dir() -> Path:
    """Get the saves directory path."""
    return config.saves_dir()


def saves_path(character_name: str) -> Path:
    slug = character_name.lower().replace(" ", "_")
    return _saves_dir() / f"{slug}.json"


def save_exists(character_name: str) -> bool:
    return saves_path(character_name).exists()


def list_saves() -> list[str]:
    """Return list of character names with existing saves."""
    saves_directory = _saves_dir()
    if not saves_directory.exists():
        return []
    return [p.stem.replace("_", " ").title() for p in saves_directory.glob("*.json")]


def list_saves_paths(save_dir: Path | None = None) -> list[Path]:
    """Return all .json save files (excludes .bak) sorted by mtime desc."""
    saves_directory = save_dir if save_dir is not None else _saves_dir()
    if not saves_directory.exists():
        return []
    return sorted(saves_directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def load_by_name(
    name: str, save_dir: Path | None = None
) -> tuple[Character, list[Vow], int, DiceMode, Session | None] | None:
    """Case-insensitive character name lookup.

    Returns same tuple as load_game(), or None if not found.
    """
    saves_directory = save_dir if save_dir is not None else _saves_dir()
    if not saves_directory.exists():
        return None

    slug = name.lower().replace(" ", "_")
    path = saves_directory / f"{slug}.json"
    if not path.exists():
        return None

    backup_path = path.with_suffix(".json.bak")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        if backup_path.exists():
            try:
                data = json.loads(backup_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                return None
        else:
            return None

    try:
        character = Character.from_dict(data["character"])
        vows = [Vow.from_dict(v) for v in data.get("vows", [])]
        session_count = data.get("session_count", 0)
        dice_mode = DiceMode(data.get("settings", {}).get("dice_mode", "digital"))
        session = None
        if "session" in data:
            session = Session.from_dict(data["session"])
        return character, vows, session_count, dice_mode, session
    except (KeyError, ValueError):
        return None


def save_game(
    character: Character,
    vows: list[Vow],
    session_count: int,
    dice_mode: DiceMode,
    session: Session | None = None,
    save_path: Path | None = None,
) -> Path:
    if save_path is None:
        _saves_dir().mkdir(parents=True, exist_ok=True)
        path = saves_path(character.name)
    else:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        path = save_path

    # Create backup if save file exists
    if path.exists():
        backup_path = path.with_suffix(".json.bak")
        backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    data = {
        "character": character.to_dict(),
        "vows": [v.to_dict() for v in vows],
        "session_count": session_count,
        "settings": {
            "dice_mode": dice_mode.value,
        },
    }

    # Save the active session if provided
    if session is not None:
        data["session"] = session.to_dict()

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return path


def autosave(
    character: Character,
    vows: list[Vow],
    session_count: int,
    dice_mode: DiceMode,
    session: Session | None = None,
    save_path: Path | None = None,
) -> None:
    """Silent autosave — same as save_game but swallows errors gracefully."""
    with contextlib.suppress(Exception):
        save_game(character, vows, session_count, dice_mode, session, save_path=save_path)


def load_game(
    character_name: str,
) -> tuple[Character, list[Vow], int, DiceMode, Session | None]:
    """Load a save file. Returns (character, vows, session_count, dice_mode, session).

    Raises ValueError if save is corrupted and no backup exists.
    """
    path = saves_path(character_name)
    backup_path = path.with_suffix(".json.bak")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        # Try to recover from backup
        if backup_path.exists():
            try:
                data = json.loads(backup_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, KeyError):
                raise ValueError(f"Save file corrupted and backup also invalid: {e}") from e
        else:
            raise ValueError(f"Save file corrupted: {e}") from e

    character = Character.from_dict(data["character"])
    vows = [Vow.from_dict(v) for v in data.get("vows", [])]
    session_count = data.get("session_count", 0)
    dice_mode = DiceMode(data.get("settings", {}).get("dice_mode", "digital"))

    # Load active session if present
    session = None
    if "session" in data:
        session = Session.from_dict(data["session"])

    return character, vows, session_count, dice_mode, session


def load_most_recent() -> tuple[Character, list[Vow], int, DiceMode, Session | None] | None:
    """Load the most recently modified save, or None if no saves exist.

    Returns None if save is corrupted.
    """
    saves_directory = _saves_dir()
    if not saves_directory.exists():
        return None
    saves = sorted(saves_directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not saves:
        return None

    try:
        data = json.loads(saves[0].read_text(encoding="utf-8"))
        character = Character.from_dict(data["character"])
        vows = [Vow.from_dict(v) for v in data.get("vows", [])]
        session_count = data.get("session_count", 0)
        dice_mode = DiceMode(data.get("settings", {}).get("dice_mode", "digital"))

        # Load active session if present
        session = None
        if "session" in data:
            session = Session.from_dict(data["session"])

        return character, vows, session_count, dice_mode, session
    except (json.JSONDecodeError, KeyError, ValueError):
        # Corrupted save, return None to trigger new character creation
        return None
