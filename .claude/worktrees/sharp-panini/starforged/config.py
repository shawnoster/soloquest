"""Configuration management for Starforged CLI."""

from __future__ import annotations

import os
from pathlib import Path

# Configuration directory follows XDG Base Directory spec
CONFIG_DIR = Path.home() / ".config" / "starforged"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def get_adventures_dir() -> Path:
    """
    Get the adventures directory path.

    Priority order:
    1. STARFORGED_ADVENTURES_DIR environment variable
    2. Config file setting
    3. Default: ~/starforged-adventures

    The adventures directory contains:
    - saves/      Character save files
    - sessions/   Individual session markdown
    - journal/    Cumulative journal markdown
    """
    # 1. Check environment variable
    env_path = os.environ.get("STARFORGED_ADVENTURES_DIR")
    if env_path:
        return Path(env_path).expanduser().resolve()

    # 2. Check config file (if we add TOML support later)
    # if CONFIG_FILE.exists():
    #     import tomllib
    #     config = tomllib.loads(CONFIG_FILE.read_text())
    #     if "adventures_dir" in config:
    #         return Path(config["adventures_dir"]).expanduser().resolve()

    # 3. Default to ~/starforged-adventures
    return Path.home() / "starforged-adventures"


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
