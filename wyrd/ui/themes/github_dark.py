"""GitHub Dark palette — semantic color constants for wyrd.

Source: OpenCode github theme (sst/opencode).
GitHub Dark reference palette:
  blue    #58a6ff  — links, primary
  green   #3fb950  — success, added
  red     #f85149  — error, removed
  orange  #d29922  — warning
  purple  #bc8cff  — functions, secondary
  pink    #ff7b72  — keywords
  yellow  #e3b341  — emphasis
  cyan    #39c5cf  — accent
  fg      #c9d1d9  — editor foreground
  fgMuted #8b949e  — muted text
  border  #30363d  — borders

See docs/adr/003-color-system-and-theming.md for the full semantic color spec.
All constants are raw hex strings or Rich style strings usable directly in
Rich markup: f"[{CONSTANT}]text[/{CONSTANT}]".
"""

from __future__ import annotations

# ── Palette — GitHub Dark ──────────────────────────────────────────────────────

# Outcomes
OUTCOME_STRONG = "bold #3fb950"  # green — strong hit
OUTCOME_WEAK = "bold #e3b341"  # yellow — weak hit
OUTCOME_MISS = "bold #f85149"  # red — miss
OUTCOME_MATCH = "bold #58a6ff"  # blue — match (doubles)

# Oracle
ORACLE_GUTTER = "#39c5cf"  # cyan — connector/gutter └
ORACLE_RESULT = "bold #58a6ff"  # blue — result text

# Narrative
NARRATIVE_NOTE = "#e3b341"  # yellow — scene notes / 📌
NARRATIVE_JOURNAL = "#c9d1d9"  # GitHub editor foreground — journal text

# Mechanics
MECHANIC_GUTTER = "#d29922"  # orange — move connector └
MECHANIC_STAT = "#58a6ff"  # blue — stat labels
MECHANIC_TRACK_HIGH = "#3fb950"  # green — track high
MECHANIC_TRACK_MID = "#e3b341"  # yellow — track mid
MECHANIC_TRACK_LOW = "#f85149"  # red — track low

# Feedback
FEEDBACK_ERROR = "#f85149"  # red
FEEDBACK_WARN = "#d29922"  # orange
FEEDBACK_SUCCESS = "#3fb950"  # green
FEEDBACK_INFO = "#8b949e"  # muted gray

# Structure
BORDER_ACTION = "#39c5cf"  # cyan — move panels
BORDER_ORACLE = "#39c5cf"  # cyan — oracle panels
BORDER_ASSET = "#bc8cff"  # purple — asset panels
BORDER_REFERENCE = "#39c5cf"  # cyan — reference / wizard panels
STRUCTURE_RULE = "#30363d"  # border gray — rule lines / dividers

# Co-op / Social
COOP_INTERPRET = "#bc8cff"  # purple — interpretation proposals
COOP_TRUTH = "#e3b341"  # yellow — truth proposals
COOP_VOW = "#3fb950"  # green — shared vows
COOP_PLAYER = "#8b949e"  # muted — partner player header

# Vow ranks
RANK_TROUBLESOME = "#3fb950"  # green — low stakes
RANK_DANGEROUS = "#e3b341"  # yellow — moderate
RANK_FORMIDABLE = "#d29922"  # orange — serious
RANK_EXTREME = "#f85149"  # red — very hard
RANK_EPIC = "#ff7b72"  # pink — harsh/epic

# Inline command hints / cross-references
HINT_COMMAND = "#39c5cf"  # cyan — /command references
