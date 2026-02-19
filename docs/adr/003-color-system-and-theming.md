# ADR-003: Color System and Theming

- **Status:** Accepted
- **Date:** 2026-02-19

## Context

ADR-002 established when to use Panels vs plain text and what border colors mean. It documents
colors by location ("oracle borders are `bright_cyan`") but not by *semantic role*. This means:

- The same color is hardcoded in a dozen places with no shared name
- Changing the theme requires touching every call site
- It's unclear whether two uses of "yellow" mean the same thing or are coincidental

To support theming — starting with **Ayu Dark** — we need a semantic color system: named
roles grouped by their meaning in the game, each mapped to a specific palette value.

## Decision

### Principle: semantic roles, not color names at call sites

No call site in `display.py` should reference a raw color name like `"yellow"` or `"bright_cyan"`.
Every color is accessed through a named constant that encodes its meaning. Swapping themes means
changing one block of constant definitions, not hunting through markup strings.

---

### Semantic color groups

Colors are organized into eight groups. Each group covers one domain of the UI.

#### Group 1 — Outcomes (dice roll results)

The result of rolling against challenge dice. Colors must be immediately distinguishable.

| Role | Constant | Ayu Dark | Notes |
|------|----------|----------|-------|
| Strong hit | `OUTCOME_STRONG` | `#aad94c` | Ayu String — bright green |
| Weak hit | `OUTCOME_WEAK` | `#e6b450` | Ayu Accent — warm amber |
| Miss | `OUTCOME_MISS` | `#d95757` | Ayu Error — muted red |
| Match (doubles) | `OUTCOME_MATCH` | `#59c2ff` | Ayu Entity — bright blue |

#### Group 2 — Oracle / Fate

Output from oracle tables; the voice of randomness in the game.

| Role | Constant | Ayu Dark | Notes |
|------|----------|----------|-------|
| Connector/gutter `└` | `ORACLE_GUTTER` | `#39bae6` | Ayu Tag — medium cyan |
| Result text | `ORACLE_RESULT` | `#59c2ff` | Ayu Entity — bright blue |
| Roll number (dim) | `ORACLE_ROLL` | `#5a6673` | Ayu Comment — muted |

#### Group 3 — Narrative

Player-written text and notes. Should feel like ink on paper, not UI chrome.

| Role | Constant | Ayu Dark | Notes |
|------|----------|----------|-------|
| Journal text | `NARRATIVE_JOURNAL` | `#bfbdb6` | Ayu Editor Foreground |
| Scene note | `NARRATIVE_NOTE` | `#e6c08a` | Ayu Special — warm parchment |
| Muted / dim prose | `NARRATIVE_MUTED` | `#5a6673` | Ayu Comment |

#### Group 4 — Mechanics

Moves, stat labels, and track bars.

| Role | Constant | Ayu Dark | Notes |
|------|----------|----------|-------|
| Move connector/gutter `└` | `MECHANIC_GUTTER` | `#ffb454` | Ayu Function — warm orange |
| Stat label | `MECHANIC_STAT` | `#73b8ff` | Ayu VCS Modified — soft blue |
| Track high | `MECHANIC_TRACK_HIGH` | `#aad94c` | Ayu String — green |
| Track mid | `MECHANIC_TRACK_MID` | `#e6b450` | Ayu Accent — amber |
| Track low | `MECHANIC_TRACK_LOW` | `#d95757` | Ayu Error — red |

#### Group 5 — Feedback (UI messages)

Non-game system messages: errors, warnings, confirmations.

| Role | Constant | Ayu Dark | Notes |
|------|----------|----------|-------|
| Error `✗` | `FEEDBACK_ERROR` | `#d95757` | Ayu Error |
| Warning `⚠` | `FEEDBACK_WARN` | `#ff8f40` | Ayu Keyword — orange |
| Success `✓` | `FEEDBACK_SUCCESS` | `#aad94c` | Ayu VCS Added — green |
| Info (hint text) | `FEEDBACK_INFO` | `#5a6378` | Ayu UI Foreground |

#### Group 6 — Structure (borders, rules, dividers)

Panel borders and rule lines. Colors reflect ADR-002's semantic border assignments.

| Role | Constant | Ayu Dark | Notes |
|------|----------|----------|-------|
| Action border (move panels) | `BORDER_ACTION` | `#39bae6` | Ayu Tag |
| Oracle border | `BORDER_ORACLE` | `#39bae6` | Ayu Tag |
| Asset border | `BORDER_ASSET` | `#d2a6ff` | Ayu Constant — lavender |
| Reference border (wizard) | `BORDER_REFERENCE` | `#39bae6` | Ayu Tag |
| Rule / divider | `STRUCTURE_RULE` | `#5a6378` | Ayu UI Foreground |

#### Group 7 — Co-op / Social

Partner activity, interpretations, shared vows, and truth proposals.

| Role | Constant | Ayu Dark | Notes |
|------|----------|----------|-------|
| Interpretation proposal | `COOP_INTERPRET` | `#d2a6ff` | Ayu Constant — lavender |
| Truth proposal / accept | `COOP_TRUTH` | `#e6b450` | Ayu Accent — amber |
| Shared vow | `COOP_VOW` | `#aad94c` | Ayu VCS Added — green |
| Partner player header | `COOP_PLAYER` | `#5a6673` | Ayu Comment |

#### Group 8 — Vow ranks

Progress track rank labels. Escalating heat from safe to epic.

| Role | Constant | Ayu Dark | Notes |
|------|----------|----------|-------|
| Troublesome | `RANK_TROUBLESOME` | `#aad94c` | green — low stakes |
| Dangerous | `RANK_DANGEROUS` | `#e6b450` | amber — moderate |
| Formidable | `RANK_FORMIDABLE` | `#ff8f40` | orange — serious |
| Extreme | `RANK_EXTREME` | `#d95757` | red — very hard |
| Epic | `RANK_EPIC` | `#f07178` | Ayu Markup — harsh pink |

---

### Ayu Dark reference palette

The full Ayu Dark source values for reference. Only the colors used above need to be defined
as constants; the rest are documented here for completeness when adapting a new variant.

| Name | Hex | Used for |
|------|-----|----------|
| `syntax.tag` | `#39bae6` | gutters, borders |
| `syntax.function` | `#ffb454` | move gutter |
| `syntax.entity` | `#59c2ff` | oracle result, outcome match |
| `syntax.string` | `#aad94c` | strong hit, success, track high, vow green |
| `syntax.keyword` | `#ff8f40` | feedback warn, rank formidable |
| `syntax.special` | `#e6c08a` | narrative note |
| `syntax.comment` | `#5a6673` | muted text |
| `syntax.constant` | `#d2a6ff` | asset border, co-op interpret |
| `syntax.operator` | `#f29668` | (reserved) |
| `syntax.markup` | `#f07178` | rank epic |
| `editor.foreground` | `#bfbdb6` | journal text |
| `ui.foreground` | `#5a6378` | info, rule lines |
| `ui.accent` | `#e6b450` | weak hit, warn, amber roles |
| `ui.error` | `#d95757` | miss, error, track low |
| `ui.added` | `#aad94c` | (shared with string) |

---

### Implementation

Color constants live in `soloquest/ui/display.py` in the `# ── Palette ──` section.
Each constant is a Rich markup color string — either a named color or a hex literal:

```python
# ── Palette — Ayu Dark ────────────────────────────────────────────────────────
# Outcomes
OUTCOME_STRONG  = "bold #aad94c"
OUTCOME_WEAK    = "bold #e6b450"
OUTCOME_MISS    = "bold #d95757"
OUTCOME_MATCH   = "bold #59c2ff"

# Oracle
ORACLE_GUTTER   = "#39bae6"
ORACLE_RESULT   = "bold #59c2ff"
ORACLE_ROLL     = "dim"

# ... etc.
```

To support a new theme (e.g., Ayu Light, Catppuccin, Nord), create a theme module that exports
the same constant names with different values, and make `display.py` import from that module.
The theme can be selected via `--theme` flag or a config setting.

---

### Rules for adding new colors

1. **Does an existing role cover the meaning?** Use it, even if the hex isn't perfect.
2. **Is this a new semantic domain?** Define a new group before adding a new constant.
3. **Never hardcode a hex or color name at the call site.** Always use a named constant.
4. **Bold is a weight modifier, not a color.** `"bold #aad94c"` is fine; the semantic role is `#aad94c`.

## Consequences

- One place to swap a full theme: the palette block in `display.py`.
- New features get color guidance without needing to read all of `display.py`.
- `display.py` call sites become self-documenting — `OUTCOME_STRONG` is clearer than `"bold green"`.
- Future: a `--theme` flag or config key can select Light/Mirage variants of Ayu or other palettes entirely.
