"""Command registry — parses and routes /commands."""

from __future__ import annotations

import shlex
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_commands() -> dict:
    with open(_DATA_DIR / "commands.toml", "rb") as f:
        return tomllib.load(f)


_COMMANDS = _load_commands()

# Commands that don't need argument parsing
BARE_COMMANDS = {
    "char",
    "log",
    "end",
    "newsession",
    "forsake",
    "help",
    "quit",
    "q",
    "exit",
    "guide",
    "next",
    "truths",
    "campaign",
}

# Command aliases — short forms for common commands
COMMAND_ALIASES = {
    "m": "move",
    "o": "oracle",
    "c": "char",
    "v": "vow",
    "p": "progress",
    "f": "fulfill",
    "h": "help",
}


@dataclass
class ParsedCommand:
    name: str
    args: list[str]
    flags: set[str]  # --manual, --auto, etc.
    raw: str


def parse_command(line: str) -> ParsedCommand | None:
    """Parse a /command line. Returns None if not a command."""
    line = line.strip()
    if not line.startswith("/"):
        return None

    # Strip leading slash
    parts = line[1:]
    try:
        tokens = shlex.split(parts)
    except ValueError:
        tokens = parts.split()

    if not tokens:
        return None

    name = tokens[0].lower()
    # Resolve aliases
    name = COMMAND_ALIASES.get(name, name)
    flags: set[str] = set()
    args: list[str] = []

    for token in tokens[1:]:
        if token.startswith("--"):
            flags.add(token[2:].lower())
        else:
            args.append(token)

    return ParsedCommand(name=name, args=args, flags=flags, raw=line)


def fuzzy_match_command(name: str, known: list[str]) -> str | None:
    """Find the best matching command name, or None."""
    name = name.lower()
    # Exact match first
    if name in known:
        return name
    # Prefix match
    matches = [k for k in known if k.startswith(name)]
    if len(matches) == 1:
        return matches[0]
    return None


COMMAND_HELP: dict[str, str] = _COMMANDS["help"]
GUIDE_SUBCOMMANDS: dict[str, str] = _COMMANDS["guide"]["subcommands"]
TRUTHS_SUBCOMMANDS: dict[str, str] = _COMMANDS["truths"]["subcommands"]
