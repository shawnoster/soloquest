"""Configuration management for SoloQuest CLI."""

from __future__ import annotations

import os
from pathlib import Path

# Configuration directory follows XDG Base Directory spec
CONFIG_DIR = Path.home() / ".config" / "soloquest"
CONFIG_FILE = CONFIG_DIR / "config.toml"

# Global state for CLI-provided adventures directory
_cli_adventures_dir: Path | None = None


def set_adventures_dir(path: Path | str | None) -> None:
    """
    Set the adventures directory from CLI argument.

    Args:
        path: Path to adventures directory, or None to clear
    """
    global _cli_adventures_dir
    _cli_adventures_dir = None if path is None else Path(path).expanduser().resolve()


def get_adventures_dir() -> Path:
    """
    Get the adventures directory path.

    Priority order:
    1. Command-line argument (--adventures-dir)
    2. SOLOQUEST_ADVENTURES_DIR environment variable
    3. Config file setting (future)
    4. Default: ~/soloquest-adventures

    The adventures directory contains:
    - saves/      Character save files
    - sessions/   Individual session markdown
    - journal/    Cumulative journal markdown
    """
    # 1. Check CLI argument
    if _cli_adventures_dir is not None:
        return _cli_adventures_dir

    # 2. Check environment variable
    env_path = os.environ.get("SOLOQUEST_ADVENTURES_DIR")
    if env_path:
        return Path(env_path).expanduser().resolve()

    # 3. Check config file (if we add TOML support later)
    # if CONFIG_FILE.exists():
    #     import tomllib
    #     config = tomllib.loads(CONFIG_FILE.read_text())
    #     if "adventures_dir" in config:
    #         return Path(config["adventures_dir"]).expanduser().resolve()

    # 4. Default to ~/soloquest-adventures
    return Path.home() / "soloquest-adventures"


# Convenience accessors for common paths
def saves_dir() -> Path:
    """Get the saves directory path."""
    return get_adventures_dir() / "saves"


def sessions_dir() -> Path:
    """Get the sessions directory path."""
    return get_adventures_dir() / "sessions"


def journal_dir() -> Path:
    """Get the journal directory path."""
    return get_adventures_dir() / "journal"
