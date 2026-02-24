"""String resource loader for UI text.

This module provides centralized access to all user-facing strings,
enabling easy editing and future internationalization support.
"""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

_strings_cache: dict[str, Any] | None = None


def _load_strings() -> dict[str, Any]:
    """Load strings from TOML file. Cached after first load."""
    global _strings_cache
    if _strings_cache is not None:
        return _strings_cache

    strings_path = Path(__file__).parent.parent / "data" / "strings.toml"
    with strings_path.open("rb") as f:
        _strings_cache = tomllib.load(f)
    return _strings_cache


def get_string(key: str, **kwargs: Any) -> str:
    """Get a string by dotted key path with optional formatting.

    Args:
        key: Dotted key path (e.g. "oracle.not_found")
        **kwargs: Format variables to substitute

    Returns:
        Formatted string

    Example:
        >>> get_string("oracle.not_found", query="action")
        "Oracle table not found: 'action'"

    Note:
        This function is not cached due to the variable format arguments.
        The underlying string data is cached via _load_strings().
    """
    strings = _load_strings()
    parts = key.split(".")
    value = strings
    for part in parts:
        if not isinstance(value, dict):
            raise KeyError(f"Invalid string key path: {key}")
        value = value[part]

    if not isinstance(value, str):
        raise ValueError(f"String key {key} does not point to a string value")

    return value.format(**kwargs) if kwargs else value


@lru_cache(maxsize=128)
def get_strings_section(section: str) -> dict[str, Any]:
    """Get an entire section of strings.

    Args:
        section: Section name (e.g. "oracle", "character_creation.wizard_steps")

    Returns:
        Dictionary of strings in that section
    """
    strings = _load_strings()
    parts = section.split(".")
    value = strings
    for part in parts:
        if not isinstance(value, dict):
            raise KeyError(f"Invalid section path: {section}")
        value = value[part]

    if not isinstance(value, dict):
        raise ValueError(f"Section {section} is not a dictionary")

    return value
