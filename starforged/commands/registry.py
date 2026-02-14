"""Command registry — parses and routes /commands."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Commands that don't need argument parsing
BARE_COMMANDS = {"char", "log", "burn", "end", "help", "quit", "q"}


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
    "move": "/move [name] — resolve a move (e.g. /move strike)",
    "oracle": "/oracle [table] — consult an oracle (e.g. /oracle action theme)",
    "roll": "/roll [dice] — raw roll (e.g. /roll 2d10)",
    "vow": "/vow [rank] [text] — create a vow",
    "progress": "/progress [vow] — mark progress on a vow",
    "fulfill": "/fulfill [vow] — attempt to fulfill a vow",
    "char": "/char — show character sheet",
    "log": "/log — show session log so far",
    "note": "/note [text] — add a scene note",
    "health": "/health +N or -N — adjust health",
    "spirit": "/spirit +N or -N — adjust spirit",
    "supply": "/supply +N or -N — adjust supply",
    "momentum": "/momentum +N or -N — adjust momentum",
    "burn": "/burn — burn momentum to improve last roll",
    "debility": "/debility [name] — toggle a debility (wounded, shaken, unprepared, etc.)",
    "settings": "/settings dice [digital|physical|mixed] — change dice mode",
    "end": "/end — end session and export journal",
    "help": "help or help [topic] — show help",
    "quit": "/quit — quit without saving",
}
