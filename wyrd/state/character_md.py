"""Markdown serialization for character narrative fields.

``character.md`` is the canonical source for descriptive / narrative fields:
homeworld, pronouns, callsign, look, act, wear, backstory, gear.

Mechanical fields (stats, tracks, debilities, assets) remain canonical in the
JSON save; the Assets section in ``character.md`` is included for human
readability and light editing only — asset abilities and track values written
here are honoured on load.

Format example::

    # Character Sheet — Kira Vex

    **Homeworld:** Drift Station Theta
    **Pronouns:** she/her
    **Callsign:** The Reaper

    ## Description

    - Wear: Worn leather duster over a scavenged tech vest.
    - Look: Scarred face, cybernetic left eye, short-cropped silver hair.
    - Act: Moves cautiously, always scanning for exits.

    ### Backstory

    She was a shipbreaker on Drift Station Theta before the Sundering took
    everything.  Lost her crew to the Andurath Void.  Now she hunts answers,
    one contract at a time.

    ### Gear

    - Battered plasma cutter
    - Emergency medkit
    - Navigation module (cracked screen)

    ## Assets

    ### Starship

    **Name:** The Iron Wake
    Abilities: [x] [ ] [ ]

    ---

    ### Glowcat

    **Companion Name:** Sparks
    **Health:** 3
    Abilities: [x] [x] [ ]

    ---
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from wyrd.models.asset import CharacterAsset
from wyrd.models.character import Character

# ── Regex helpers ─────────────────────────────────────────────────────────────

# Matches:  **Tag:** value   (with or without trailing content)
_TAG_PATTERN = re.compile(r"^\*\*([^*:]+):\*\*\s*(.*)")

# Matches:  Abilities: [x] [ ] [x]
_ABILITIES_LINE = re.compile(r"^Abilities:\s*((?:\[[x ]\]\s*)+)", re.IGNORECASE)
_ABILITY_CELL = re.compile(r"\[([x ])\]", re.IGNORECASE)

# Matches:  - [x] ability text  or  - [ ]
_ABILITY_BULLET = re.compile(r"^-\s+\[([x ])\]\s*(.*)", re.IGNORECASE)


# ── Key derivation (mirrors wyrd/engine/assets.py) ────────────────────────────


def _name_to_key(name: str) -> str:
    """Derive asset key from display name using the same normalisation as the engine."""
    return name.lower().replace(" ", "_").replace("-", "_")


# ── Path helper ───────────────────────────────────────────────────────────────


def character_md_path(save_path: Path) -> Path:
    """Return the ``.character.md`` path that sits beside *save_path*.

    Example: ``saves/kira_vex.json`` → ``saves/kira_vex.character.md``
    """
    return save_path.parent / (save_path.stem + ".character.md")


# ── Narrative data container ──────────────────────────────────────────────────


@dataclass
class CharacterNarrative:
    """Narrative fields parsed from ``character.md``.

    Only fields explicitly present in the file carry values; empty strings /
    empty lists signal "not set" so callers can merge selectively.
    """

    homeworld: str = ""
    pronouns: str = ""
    callsign: str = ""
    look: str = ""
    act: str = ""
    wear: str = ""
    backstory: str = ""
    gear: list[str] = field(default_factory=list)

    def apply_to(self, character: Character) -> None:
        """Override *character* narrative fields with values present here."""
        if self.homeworld:
            character.homeworld = self.homeworld
        if self.pronouns:
            character.pronouns = self.pronouns
        if self.callsign:
            character.callsign = self.callsign
        if self.look:
            character.look = self.look
        if self.act:
            character.act = self.act
        if self.wear:
            character.wear = self.wear
        if self.backstory:
            character.backstory = self.backstory
        if self.gear:
            character.gear = list(self.gear)


# ── Serialise ─────────────────────────────────────────────────────────────────


def _abilities_line(unlocked: list[bool]) -> str:
    cells = " ".join("[x]" if u else "[ ]" for u in unlocked)
    return f"Abilities: {cells}"


def character_to_markdown(
    character: Character,
    asset_registry: dict | None = None,
) -> str:
    """Render *character* as a human-readable / machine-parseable Markdown string.

    *asset_registry* (``dict[key, Asset]``) is optional; when provided it is
    used to resolve display names for assets.
    """
    lines: list[str] = [f"# Character Sheet — {character.name}", ""]

    # ── Identity fields ───────────────────────────────────────────────────────
    for tag, value in [
        ("Homeworld", character.homeworld),
        ("Pronouns", character.pronouns),
        ("Callsign", character.callsign),
    ]:
        if value:
            lines.append(f"**{tag}:** {value}")
    lines.append("")

    # ── Description section ───────────────────────────────────────────────────
    lines.append("## Description")
    lines.append("")

    for label, prose in [
        ("Wear", character.wear),
        ("Look", character.look),
        ("Act", character.act),
    ]:
        lines.append(f"- {label}: {prose}" if prose else f"- {label}:")

    lines.append("")

    lines.append("### Backstory")
    lines.append("")
    lines.append(character.backstory if character.backstory else "")
    lines.append("")

    lines.append("### Gear")
    lines.append("")
    for item in character.gear:
        lines.append(f"- {item}")
    lines.append("")

    # ── Assets section ────────────────────────────────────────────────────────
    if character.assets:
        lines.append("## Assets")
        lines.append("")

        for char_asset in character.assets:
            # Resolve display name from registry, fall back to key → title case
            if asset_registry and char_asset.asset_key in asset_registry:
                display_name = asset_registry[char_asset.asset_key].name
            else:
                display_name = char_asset.asset_key.replace("_", " ").title()

            lines.append(f"### {display_name}")
            lines.append("")

            # Input values (string fields, e.g. companion name)
            for input_name, input_val in char_asset.input_values.items():
                lines.append(f"**{input_name}:** {input_val}")

            # Track values (integer meters, e.g. health)
            for track_name, track_val in char_asset.track_values.items():
                lines.append(f"**{track_name.title()}:** {track_val}")

            # Ability checkboxes — with text if registry available
            asset_def = asset_registry.get(char_asset.asset_key) if asset_registry else None
            if char_asset.abilities_unlocked:
                for i, unlocked in enumerate(char_asset.abilities_unlocked):
                    mark = "x" if unlocked else " "
                    if asset_def and i < len(asset_def.abilities):
                        text = asset_def.abilities[i].text.replace("\n", " ").strip()
                        lines.append(f"- [{mark}] {text}")
                    else:
                        lines.append(f"- [{mark}]")

            # Conditions
            if char_asset.conditions:
                lines.append(f"**Conditions:** {', '.join(sorted(char_asset.conditions))}")

            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


# ── Deserialise ───────────────────────────────────────────────────────────────


def _parse_abilities(line: str) -> list[bool] | None:
    """Return ability list from an ``Abilities: [x] [ ] …`` line, or None."""
    m = _ABILITIES_LINE.match(line.strip())
    if not m:
        return None
    return [cell.group(1).lower() == "x" for cell in _ABILITY_CELL.finditer(m.group(1))]


def _collect_prose(body_lines: list[str]) -> str:
    """Join body lines into a prose string, preserving internal paragraph breaks."""
    # Strip leading / trailing blank lines, keep internal structure
    stripped = "\n".join(body_lines).strip()
    # Collapse runs of 3+ blank lines down to a single blank line
    return re.sub(r"\n{3,}", "\n\n", stripped)


_DESC_BULLET = re.compile(r"^-\s+(Wear|Look|Act):\s*(.*)", re.IGNORECASE)


def _parse_description(lines: list[str], narrative: CharacterNarrative) -> None:
    """Populate *narrative* from the body lines of a ``## Description`` section.

    Supports both the current bullet format (``- Wear: …``) and the legacy
    ``### heading`` sub-section format for backward compatibility.
    """
    current_heading: str | None = None
    body_lines: list[str] = []

    def flush() -> None:
        if current_heading is None:
            return
        if current_heading == "Gear":
            narrative.gear = [
                ln.strip()[2:].strip() for ln in body_lines if ln.strip().startswith("- ")
            ]
        else:
            prose = _collect_prose(body_lines)
            if current_heading == "Look":
                narrative.look = prose
            elif current_heading == "Act":
                narrative.act = prose
            elif current_heading == "Wear":
                narrative.wear = prose
            elif current_heading == "Backstory":
                narrative.backstory = prose

    for line in lines:
        # New bullet format: - Wear: value
        m = _DESC_BULLET.match(line.strip())
        if m:
            label, value = m.group(1).title(), m.group(2).strip()
            if label == "Look":
                narrative.look = value
            elif label == "Act":
                narrative.act = value
            elif label == "Wear":
                narrative.wear = value
            continue

        # Legacy sub-section format: ### Heading
        if line.startswith("### "):
            flush()
            current_heading = line[4:].strip()
            body_lines = []
        else:
            body_lines.append(line)

    flush()


def _parse_assets(lines: list[str]) -> list[CharacterAsset]:
    """Parse the body lines of a ``## Assets`` section into CharacterAsset list."""
    asset_blocks: list[tuple[str, list[str]]] = []
    current_name = ""
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("### "):
            if current_name:
                asset_blocks.append((current_name, current_lines))
            current_name = line[4:].strip()
            current_lines = []
        elif current_name:
            current_lines.append(line)

    if current_name:
        asset_blocks.append((current_name, current_lines))

    assets: list[CharacterAsset] = []
    for asset_name, asset_lines in asset_blocks:
        key = _name_to_key(asset_name)
        abilities_unlocked: list[bool] = []
        input_values: dict[str, str] = {}
        track_values: dict[str, int] = {}
        conditions: set[str] = set()

        for line in asset_lines:
            stripped = line.strip()

            # - [x] ability text  (new format)
            m = _ABILITY_BULLET.match(stripped)
            if m:
                abilities_unlocked.append(m.group(1).lower() == "x")
                continue

            # Abilities: [x] [ ] [ ]  (legacy format)
            parsed = _parse_abilities(stripped)
            if parsed is not None:
                abilities_unlocked = parsed
                continue

            # **Tag:** value
            m = _TAG_PATTERN.match(stripped)
            if m:
                tag, value = m.group(1).strip(), m.group(2).strip()
                if tag == "Conditions":
                    conditions = {c.strip().lower() for c in value.split(",") if c.strip()}
                else:
                    # Integer value → track, string value → input
                    try:
                        track_values[tag.lower()] = int(value)
                    except ValueError:
                        input_values[tag] = value
                continue

        assets.append(
            CharacterAsset(
                asset_key=key,
                abilities_unlocked=abilities_unlocked,
                track_values=track_values,
                input_values=input_values,
                conditions=conditions,
            )
        )

    return assets


def character_from_markdown(
    text: str,
) -> tuple[CharacterNarrative, list[CharacterAsset]] | None:
    """Parse a ``character.md`` file.

    Returns ``(narrative, assets)`` on success, or ``None`` on a parse error.
    The character name in the H1 header is intentionally ignored — the JSON save
    is canonical for name.
    """
    narrative = CharacterNarrative()
    assets: list[CharacterAsset] = []

    lines = text.splitlines()
    if not lines:
        return None

    # ── Identity fields (before first ## section) ─────────────────────────────
    for line in lines:
        if line.startswith("## "):
            break
        m = _TAG_PATTERN.match(line.strip())
        if m:
            tag, value = m.group(1).strip(), m.group(2).strip()
            if tag == "Homeworld":
                narrative.homeworld = value
            elif tag == "Pronouns":
                narrative.pronouns = value
            elif tag == "Callsign":
                narrative.callsign = value

    # ── Split into ## sections ────────────────────────────────────────────────
    sections: list[tuple[str, list[str]]] = []
    current_name = ""
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_name:
                sections.append((current_name, current_lines))
            current_name = line[3:].strip()
            current_lines = []
        elif current_name:
            current_lines.append(line)

    if current_name:
        sections.append((current_name, current_lines))

    for section_name, section_lines in sections:
        if section_name == "Description":
            _parse_description(section_lines, narrative)
        elif section_name == "Assets":
            assets = _parse_assets(section_lines)

    return narrative, assets


# ── Convenience I/O ───────────────────────────────────────────────────────────


def write_character_md(
    character: Character,
    save_path: Path,
    asset_registry: dict | None = None,
) -> None:
    """Write (or overwrite) the companion ``.character.md`` for *save_path*."""
    md_path = character_md_path(save_path)
    md_path.write_text(character_to_markdown(character, asset_registry), encoding="utf-8")


def read_character_md(
    save_path: Path,
) -> tuple[CharacterNarrative, list[CharacterAsset]] | None:
    """Load narrative fields from the companion ``.character.md`` if it exists.

    Returns ``None`` when the file is absent or cannot be parsed.
    """
    md_path = character_md_path(save_path)
    if not md_path.exists():
        return None
    try:
        return character_from_markdown(md_path.read_text(encoding="utf-8"))
    except Exception:
        return None
