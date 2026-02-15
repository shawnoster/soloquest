"""Command registry — parses and routes /commands."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Commands that don't need argument parsing
BARE_COMMANDS = {"char", "log", "burn", "end", "forsake", "help", "quit", "q"}

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


COMMAND_HELP: dict[str, str] = {
    "move": "/move [name] (alias: /m) — resolve a move (e.g. /move strike)",
    "oracle": "/oracle [table] (alias: /o) — consult an oracle (e.g. /oracle action theme)",
    "vow": "/vow [rank] [text] (alias: /v) — create a vow",
    "progress": "/progress [vow] (alias: /p) — mark progress on a vow",
    "fulfill": "/fulfill [vow] (alias: /f) — attempt to fulfill a vow",
    "char": "/char (alias: /c) — show character sheet",
    "log": "/log — show session log so far",
    "note": "/note [text] — add a scene note",
    "health": "/health +N or -N — adjust health",
    "spirit": "/spirit +N or -N — adjust spirit",
    "supply": "/supply +N or -N — adjust supply",
    "momentum": "/momentum +N or -N — adjust momentum",
    "burn": "/burn — burn momentum to improve last roll",
    "debility": "/debility [name] — toggle a debility (wounded, shaken, unprepared, etc.)",
    "roll": "/roll [dice] — raw dice roll (e.g. /roll d6, /roll 2d10)",
    "forsake": "/forsake — forsake a vow (costs spirit)",
    "settings": "/settings dice [digital|physical|mixed] — change dice mode",
    "end": "/end — end session and export journal",
    "help": "/help (alias: /h) — show help",
    "quit": "/quit — quit without saving",
}
