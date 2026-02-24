"""Markdown serialization for campaign truths.

Truths are stored in a human-readable ``truths.md`` file in the adventure
directory.  Users can edit this file directly; the CLI reads it on load
and honours any changes.

Format example::

    # Campaign Truths — Kira

    ## The Cataclysm — Promises of a new age

    The galaxy is scarred by the Sundering...

    ### Quest Starter

    There are those who believe...

    - **Subchoice:** The cities of bone
    - **Note:** This sets the tone for Kira's origin.

    ---

    ## Exodus — The people didn't flee — they were driven out.

    **Custom**

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
        summary = truth.custom_text or truth.option_summary
        lines.append(f"## {truth.category} — {summary}")
        lines.append("")

        if truth.custom_text:
            lines.append("**Custom**")
        else:
            if truth.option_text:
                lines.append(truth.option_text)
            if truth.quest_starter:
                lines.append("")
                lines.append("### Quest Starter")
                lines.append("")
                lines.append(truth.quest_starter)

        # Subchoice (optional inline bullet)
        if truth.subchoice:
            lines.append("")
            lines.append(f"- **Subchoice:** {truth.subchoice}")

        # Notes section (always included so users know where to add entries)
        lines.append("")
        lines.append("### Notes")
        lines.append("")
        for note_line in (ln.strip() for ln in truth.note.split("\n") if ln.strip()):
            lines.append(f"- {note_line}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ── Deserialise ──────────────────────────────────────────────────────────────


def truths_from_markdown(text: str) -> list[ChosenTruth] | None:
    """Parse a markdown truths file and return a list of :class:`ChosenTruth`.

    Supports both the current format (summary embedded in H2, detail as the
    first paragraph) and the legacy format (``**Choice:**`` / ``### Detail``).

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
        h2_line = lines[0][3:].strip()  # strip "## "

        # New format: "Category — Summary text"
        if " \u2014 " in h2_line:
            category, h2_summary = h2_line.split(" \u2014 ", 1)
            category = category.strip()
            h2_summary = h2_summary.strip()
        else:
            category = h2_line.strip()
            h2_summary = ""

        if not category:
            continue

        fields: dict[str, str] = {}
        if h2_summary:
            fields["option_summary"] = h2_summary

        is_custom = False
        current_heading: str | None = None
        heading_body: list[str] = []
        pre_detail: list[str] = []  # lines before first subheading/bullet/tag
        left_pre_detail = False  # True once structural elements are seen
        note_lines_collected: list[str] = []

        for line in lines[1:]:
            stripped = line.strip()

            # ### Subheading
            if stripped.startswith("### "):
                if heading_body:
                    field = _HEADING_TAGS.get(current_heading or "")
                    if field:
                        fields[field] = " ".join(heading_body)
                    heading_body.clear()
                if not left_pre_detail and pre_detail and "option_text" not in fields:
                    fields["option_text"] = " ".join(pre_detail)
                left_pre_detail = True
                current_heading = stripped[4:].strip()
                continue

            # Bullet: - **Tag:** value
            m = _BULLET_PATTERN.match(stripped)
            if m:
                if heading_body:
                    field = _HEADING_TAGS.get(current_heading or "")
                    if field:
                        fields[field] = " ".join(heading_body)
                    heading_body.clear()
                if not left_pre_detail and pre_detail and "option_text" not in fields:
                    fields["option_text"] = " ".join(pre_detail)
                left_pre_detail = True
                current_heading = None
                tag, value = m.group(1), m.group(2).strip()
                if tag in _INLINE_TAGS:
                    fields[_INLINE_TAGS[tag]] = value
                continue

            # Plain bullet under ### Notes (new format)
            if stripped.startswith("- ") and current_heading == "Notes":
                note_text = stripped[2:].strip()
                if note_text:
                    note_lines_collected.append(note_text)
                continue

            # **Custom** standalone flag (new format)
            if stripped == "**Custom**":
                if not left_pre_detail and pre_detail and "option_text" not in fields:
                    fields["option_text"] = " ".join(pre_detail)
                left_pre_detail = True
                is_custom = True
                continue

            # Plain: **Tag:** value (legacy Choice / Custom)
            m = _TAG_PATTERN.match(stripped)
            if m:
                if heading_body:
                    field = _HEADING_TAGS.get(current_heading or "")
                    if field:
                        fields[field] = " ".join(heading_body)
                    heading_body.clear()
                if not left_pre_detail and pre_detail and "option_text" not in fields:
                    fields["option_text"] = " ".join(pre_detail)
                left_pre_detail = True
                current_heading = None
                tag, value = m.group(1), m.group(2).strip()
                if tag == "Custom":
                    is_custom = True
                    fields["custom_text"] = value
                    if not fields.get("option_summary"):
                        fields["option_summary"] = value
                elif tag in _INLINE_TAGS:
                    fields[_INLINE_TAGS[tag]] = value
                continue

            # Hard separator
            if stripped == "---":
                if heading_body:
                    field = _HEADING_TAGS.get(current_heading or "")
                    if field:
                        fields[field] = " ".join(heading_body)
                    heading_body.clear()
                if not left_pre_detail and pre_detail and "option_text" not in fields:
                    fields["option_text"] = " ".join(pre_detail)
                left_pre_detail = True
                current_heading = None
                continue

            # Blank line — skip
            if not stripped:
                continue

            # Body text
            if current_heading:
                if current_heading == "Notes":
                    note_lines_collected.append(stripped)
                else:
                    heading_body.append(stripped)
            elif not left_pre_detail:
                pre_detail.append(stripped)

        # Final flush
        if heading_body:
            field = _HEADING_TAGS.get(current_heading or "")
            if field:
                fields[field] = " ".join(heading_body)
        if not left_pre_detail and pre_detail and "option_text" not in fields:
            fields["option_text"] = " ".join(pre_detail)
        if note_lines_collected:
            fields["note"] = "\n".join(note_lines_collected)

        if not fields:
            continue

        custom_text = fields.get("custom_text", "")
        if is_custom and not custom_text:
            custom_text = fields.get("option_summary", "")
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
