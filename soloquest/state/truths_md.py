"""Markdown serialization for campaign truths.

Truths are stored in a human-readable ``<character>.truths.md`` file
alongside the JSON save.  Users can edit this file directly; the CLI
reads it on load and honours any changes.

Format example::

    # Campaign Truths — Kira

    ## The Cataclysm

    **Choice:** Promises of a new age

    ### Detail

    The galaxy is scarred by the Sundering...

    ### Quest Starter

    There are those who believe...

    - **Subchoice:** The cities of bone
    - **Note:** This sets the tone for Kira's origin.

    ---

    ## Exodus

    **Custom:** The people didn't flee — they were driven out.

    - **Note:**

    ---
"""

from __future__ import annotations

import re
from pathlib import Path

from soloquest.models.truths import ChosenTruth

# ── Field tags ──────────────────────────────────────────────────────────────
# Inline fields (plain **Tag:** value or bullet - **Tag:** value)
_INLINE_TAGS = {
    "Choice": "option_summary",
    "Custom": "custom_text",
    "Subchoice": "subchoice",
    "Note": "note",
}

# Subheading tags (### Heading followed by a paragraph)
_HEADING_TAGS = {
    "Detail": "option_text",
    "Quest Starter": "quest_starter",
}

# Matches:  **Tag:** value   (plain)
_TAG_PATTERN = re.compile(r"^\*\*([^*:]+):\*\*\s*(.*)")
# Matches:  - **Tag:** value  (bullet)
_BULLET_PATTERN = re.compile(r"^-\s+\*\*([^*:]+):\*\*\s*(.*)")


# ── Path helper ──────────────────────────────────────────────────────────────


def truths_md_path(save_path: Path) -> Path:
    """Return the ``.truths.md`` path that sits beside *save_path*.

    Example: ``saves/kira.json`` → ``saves/kira.truths.md``
    """
    return save_path.parent / (save_path.stem + ".truths.md")


# ── Serialise ────────────────────────────────────────────────────────────────


def truths_to_markdown(truths: list[ChosenTruth], character_name: str = "") -> str:
    """Render *truths* as a human-readable / machine-parseable Markdown string."""
    header = f"# Campaign Truths — {character_name}" if character_name else "# Campaign Truths"
    lines: list[str] = [header, ""]

    for truth in truths:
        lines.append(f"## {truth.category}")
        lines.append("")

        if truth.custom_text:
            lines.append(f"**Custom:** {truth.custom_text}")
        else:
            lines.append(f"**Choice:** {truth.option_summary}")
            if truth.option_text:
                lines.append("")
                lines.append("### Detail")
                lines.append("")
                lines.append(truth.option_text)
            if truth.quest_starter:
                lines.append("")
                lines.append("### Quest Starter")
                lines.append("")
                lines.append(truth.quest_starter)

        # Bullet list for short inline fields
        lines.append("")
        if truth.subchoice:
            lines.append(f"- **Subchoice:** {truth.subchoice}")
        # Note is always included (even blank) so users know where to add one
        lines.append(f"- **Note:** {truth.note}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ── Deserialise ──────────────────────────────────────────────────────────────


def truths_from_markdown(text: str) -> list[ChosenTruth] | None:
    """Parse a markdown truths file and return a list of :class:`ChosenTruth`.

    Returns ``None`` on a parse error so callers can fall back gracefully.
    """
    truths: list[ChosenTruth] = []

    # Split into `## Category` sections
    sections = re.split(r"\n(?=## )", text)

    for section in sections:
        section = section.strip()
        if not section.startswith("## "):
            continue

        lines = section.splitlines()
        category = lines[0][3:].strip()
        if not category:
            continue

        fields: dict[str, str] = {}
        current_heading: str | None = None
        body_lines: list[str] = []

        def _flush() -> None:
            if current_heading and body_lines:
                field = _HEADING_TAGS.get(current_heading)
                if field:
                    fields[field] = " ".join(body_lines)
            body_lines.clear()

        for line in lines[1:]:
            stripped = line.strip()

            # ### Subheading → start collecting paragraph body
            if stripped.startswith("### "):
                _flush()
                current_heading = stripped[4:].strip()
                continue

            # Bullet: - **Tag:** value
            m = _BULLET_PATTERN.match(stripped)
            if m:
                _flush()
                current_heading = None
                tag, value = m.group(1), m.group(2).strip()
                if tag in _INLINE_TAGS:
                    fields[_INLINE_TAGS[tag]] = value
                continue

            # Plain: **Tag:** value  (Choice / Custom)
            m = _TAG_PATTERN.match(stripped)
            if m:
                _flush()
                current_heading = None
                tag, value = m.group(1), m.group(2).strip()
                if tag in _INLINE_TAGS:
                    fields[_INLINE_TAGS[tag]] = value
                continue

            # Hard separator — flush and end the section
            if stripped == "---":
                _flush()
                current_heading = None
                continue

            # Blank line — skip (don't reset heading; body may follow)
            if not stripped:
                continue

            # Body text for current ### subheading
            if current_heading:
                body_lines.append(stripped)

        _flush()

        if not fields:
            continue

        custom_text = fields.get("custom_text", "")
        option_summary = fields.get("option_summary", custom_text)

        if not option_summary and not custom_text:
            continue

        truths.append(
            ChosenTruth(
                category=category,
                option_summary=option_summary or custom_text,
                option_text=fields.get("option_text", ""),
                custom_text=custom_text,
                quest_starter=fields.get("quest_starter", ""),
                subchoice=fields.get("subchoice", ""),
                note=fields.get("note", ""),
            )
        )

    return truths if truths else None


# ── Convenience I/O ──────────────────────────────────────────────────────────


def write_truths_md(truths: list[ChosenTruth], save_path: Path, character_name: str = "") -> None:
    """Write (or overwrite) the companion ``.truths.md`` for *save_path*."""
    md_path = truths_md_path(save_path)
    md_path.write_text(truths_to_markdown(truths, character_name), encoding="utf-8")


def read_truths_md(save_path: Path) -> list[ChosenTruth] | None:
    """Load truths from the companion ``.truths.md`` if it exists.

    Returns ``None`` when the file is absent or cannot be parsed.
    """
    md_path = truths_md_path(save_path)
    if not md_path.exists():
        return None
    try:
        return truths_from_markdown(md_path.read_text(encoding="utf-8"))
    except Exception:
        return None


# ── Adventure / campaign-level truths (canonical store) ──────────────────────


def adventure_truths_path(adventures_dir: Path) -> Path:
    """Return the campaign-level ``truths.md`` at the root of the adventure directory."""
    return adventures_dir / "truths.md"


def read_adventure_truths(adventures_dir: Path) -> list[ChosenTruth] | None:
    """Load truths from ``{adventures_dir}/truths.md``.

    Returns ``None`` when the file is absent or cannot be parsed.
    """
    path = adventure_truths_path(adventures_dir)
    if not path.exists():
        return None
    try:
        return truths_from_markdown(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_adventure_truths(
    truths: list[ChosenTruth], adventures_dir: Path, character_name: str = ""
) -> None:
    """Write (or overwrite) ``{adventures_dir}/truths.md``."""
    path = adventure_truths_path(adventures_dir)
    path.write_text(truths_to_markdown(truths, character_name), encoding="utf-8")
