"""Export session logs to markdown journal files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from soloquest.models.character import Character
    from soloquest.models.session import Session

from soloquest.config import journal_dir, sessions_dir
from soloquest.models.session import EntryKind


def _sessions_dir() -> Path:
    """Get the sessions directory path."""
    return sessions_dir()


def _journal_dir() -> Path:
    """Get the journal directory path."""
    return journal_dir()


def _character_slug(character_name: str) -> str:
    """Convert character name to filesystem-safe slug."""
    return character_name.lower().replace(" ", "_")


def _format_entry(entry) -> str:
    """Format a single log entry for markdown export."""
    # Format timestamp
    time_str = entry.timestamp.strftime("%H:%M")

    # Format based on entry kind
    if entry.kind == EntryKind.JOURNAL:
        return f"\n{entry.text}\n"
    elif entry.kind == EntryKind.MOVE:
        return f"\n**{time_str}** — {entry.text}\n"
    elif entry.kind == EntryKind.ORACLE:
        return f"\n**{time_str}** — *Oracle:* {entry.text}\n"
    elif entry.kind == EntryKind.NOTE:
        return f"\n> **Note:** {entry.text}\n"
    elif entry.kind == EntryKind.MECHANICAL:
        return f"\n*{entry.text}*\n"
    else:
        return f"\n{entry.text}\n"


def export_session(session: Session, character: Character) -> Path:
    """
    Export a single session to its own markdown file.

    Creates: {adventures_dir}/sessions/session_{number:03d}_{title_slug}.md

    Returns the path to the created file.
    """
    sessions_directory = _sessions_dir()
    sessions_directory.mkdir(parents=True, exist_ok=True)

    # Create filename: session_001_title.md or session_001.md
    title_slug = session.title.lower().replace(" ", "_") if session.title else ""
    if title_slug:
        filename = f"session_{session.number:03d}_{title_slug}.md"
    else:
        filename = f"session_{session.number:03d}.md"
    path = sessions_directory / filename

    # Build markdown content with YAML frontmatter
    lines = []

    # YAML frontmatter
    title = session.title or f"Session {session.number}"
    lines.append("---\n")
    lines.append(f"session: {session.number}\n")
    lines.append(f"character: {character.name}\n")
    lines.append(f"date: {session.started_at.strftime('%Y-%m-%d')}\n")
    if session.title:
        lines.append(f"title: {session.title}\n")
    lines.append("---\n\n")
    lines.append(f"# {title}\n")

    # Entries
    for entry in session.entries:
        lines.append(_format_entry(entry))

    # Footer with session stats
    moves_count = sum(1 for e in session.entries if e.kind == EntryKind.MOVE)
    oracles_count = sum(1 for e in session.entries if e.kind == EntryKind.ORACLE)
    journal_count = sum(1 for e in session.entries if e.kind == EntryKind.JOURNAL)

    lines.append("\n---\n")
    lines.append(f"\n*Session {session.number} — {moves_count} moves, {oracles_count} oracles, {journal_count} journal entries*\n")

    content = "".join(lines)
    path.write_text(content, encoding="utf-8")

    return path


def append_to_journal(session: Session, character: Character) -> Path:
    """
    Append a session to the character's full journal file.

    Creates/updates: {adventures_dir}/journal/{character_slug}_journal.md

    Returns the path to the journal file.
    """
    journal_directory = _journal_dir()
    journal_directory.mkdir(parents=True, exist_ok=True)

    slug = _character_slug(character.name)
    path = journal_directory / f"{slug}_journal.md"

    # Build session content
    lines = []

    # Session header
    title = session.title or f"Session {session.number}"
    lines.append(f"\n## {title}\n")
    lines.append(f"*{session.started_at.strftime('%Y-%m-%d')}*\n")

    # Entries
    for entry in session.entries:
        lines.append(_format_entry(entry))

    lines.append("\n---\n")

    content = "".join(lines)

    # If journal doesn't exist, create with header
    if not path.exists():
        header = f"# {character.name} — Journal\n\n"
        if character.homeworld:
            header += f"- **Homeworld:** {character.homeworld}\n\n"
        header += "---\n"
        path.write_text(header + content, encoding="utf-8")
    else:
        # Append to existing journal
        existing = path.read_text(encoding="utf-8")
        path.write_text(existing + content, encoding="utf-8")

    return path
