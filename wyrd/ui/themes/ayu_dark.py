"""Ayu Dark palette — semantic color constants for wyrd.

See docs/adr/003-color-system-and-theming.md for the full semantic color spec.
All constants are raw hex strings or Rich style strings usable directly in
Rich markup: f"[{CONSTANT}]text[/{CONSTANT}]".
"""

from __future__ import annotations

# ── Palette — Ayu Dark ────────────────────────────────────────────────────────

# Outcomes
OUTCOME_STRONG = "bold #aad94c"
OUTCOME_WEAK = "bold #e6b450"
OUTCOME_MISS = "bold #d95757"
OUTCOME_MATCH = "bold #59c2ff"

# Oracle
ORACLE_GUTTER = "#39bae6"
ORACLE_RESULT = "bold #59c2ff"

# Narrative
NARRATIVE_NOTE = "#e6c08a"
NARRATIVE_JOURNAL = "#bfbdb6"  # Ayu Editor Foreground — journal text

# Mechanics
MECHANIC_GUTTER = "#ffb454"
MECHANIC_STAT = "#73b8ff"
MECHANIC_TRACK_HIGH = "#aad94c"
MECHANIC_TRACK_MID = "#e6b450"
MECHANIC_TRACK_LOW = "#d95757"

# Feedback
FEEDBACK_ERROR = "#d95757"
FEEDBACK_WARN = "#ff8f40"
FEEDBACK_SUCCESS = "#aad94c"
FEEDBACK_INFO = "#5a6378"

# Structure
BORDER_ACTION = "#39bae6"
BORDER_ORACLE = "#39bae6"
BORDER_ASSET = "#d2a6ff"
BORDER_REFERENCE = "#39bae6"
STRUCTURE_RULE = "#5a6378"

# Co-op / Social
COOP_INTERPRET = "#d2a6ff"
COOP_TRUTH = "#e6b450"
COOP_VOW = "#aad94c"
COOP_PLAYER = "#5a6673"

# Vow ranks
RANK_TROUBLESOME = "#aad94c"
RANK_DANGEROUS = "#e6b450"
RANK_FORMIDABLE = "#ff8f40"
RANK_EXTREME = "#d95757"
RANK_EPIC = "#f07178"

# Inline command hints / cross-references
HINT_COMMAND = "#39bae6"  # same as ORACLE_GUTTER — cyan for /command references
