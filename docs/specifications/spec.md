# Soloquest — CLI Specification

**Version:** 2.0
**Language:** Python 3.13
**Target:** Multi-system solo journaling companion CLI

---

## 1. Overview

Soloquest is a terminal-based companion for playing solo RPGs. The CLI handles the mechanical layer — move resolution, oracle lookups, dice rolling, character tracking — while keeping the journaling experience as the primary surface. Every session produces a Markdown artifact the player can keep.

### Design Philosophy

1. **Journal-first interface** — The hybrid journal/command loop feels natural to use
2. **Flexible dice modes** — Physical and digital dice modes work without friction
3. **Readable export** — Session export produces genuinely readable journals
4. **System-agnostic core** — Architecture supports multiple game systems

### Supported Systems

- **Ironsworn: Starforged** ✅ Complete — See [systems/ironsworn-starforged.md](systems/ironsworn-starforged.md)
- **Mythic GME** 🔮 Planned — Universal game master emulator

### Related Documentation

This is the **living specification** for the entire CLI. For detailed information:

- **[Architecture](architecture.md)** — System-agnostic design and integration points
- **[Systems](systems/)** — Game system specifications
- **[Features](features/)** — Feature implementation plans
- **[Process Guide](PROCESS.md)** — How to add new systems and features

---

## 2. Architecture Overview

> **Detailed architecture documentation:** See [architecture.md](architecture.md)

```
soloquest/
├── main.py               # Entry point, session bootstrap
├── loop.py               # Main REPL loop
├── commands/             # Command handlers (UI layer)
│   ├── registry.py       # Command routing
│   ├── move.py           # /move resolution
│   ├── oracle.py         # /oracle lookups
│   ├── vow.py            # /vow, /progress (Ironsworn)
│   ├── truths.py         # /truths (Starforged)
│   ├── guide.py          # /guide (gameplay tutorials)
│   ├── character.py      # /char, stat/track adjustments
│   └── session.py        # /log, /end, /note
├── engine/               # Game mechanics (business logic)
│   ├── dice.py           # Dice provider abstraction
│   ├── moves.py          # Move resolution logic
│   ├── oracles.py        # Oracle table lookups
│   ├── truths.py         # Truth category loader
│   └── assets.py         # Asset system
├── models/               # Data models
│   ├── character.py      # Character dataclass
│   ├── vow.py            # Vow dataclass (Ironsworn)
│   ├── session.py        # Session log dataclass
│   └── truths.py         # Truth models (Starforged)
├── journal/              # Export system
│   └── exporter.py       # Markdown export
├── data/                 # Game content (system-specific)
│   ├── moves.toml        # Move definitions
│   ├── oracles.toml      # Oracle tables
│   ├── truths.toml       # Truth categories
│   └── dataforged/       # Vendored Starforged content
├── state/                # Persistence
│   └── save.py           # JSON save/load
└── ui/                   # Display formatting
    └── display.py        # Rich-based rendering
```

**Key dependencies:**
- `rich` — Terminal rendering (panels, tables, progress bars)
- `prompt_toolkit` — Multi-line input, history, autocomplete
- `tomllib` (stdlib 3.11+) — Data file parsing
- `dataforged` — Ironsworn: Starforged game content
- No TUI framework; no curses; no textual — Pure REPL with rich formatting

---

## 3. Use Cases

---

### UC-01: Start or Resume a Session

**Actor:** Player  
**Trigger:** Runs `python main.py`

**Main Flow:**
1. CLI displays splash screen with character name if a save exists
2. Player chooses: resume last session, load a different character, or create new character
3. If resuming: session log loads, last few journal entries display as context
4. Main journal loop begins

**Alternate Flow — New Character:**
1. Player is prompted for name, homeworld, background vow
2. Player assigns stats (Edge, Heart, Iron, Shadow, Wits) via simple prompts — total points enforced
3. Player selects 3 starting assets from a short list
4. Character saved, session 1 begins

**Exit Criteria:** Player is in the main loop with character context loaded.

---

### UC-02: Journal Entry (Default Mode)

**Actor:** Player  
**Trigger:** Player types narrative prose at the prompt

**Main Flow:**
1. Player types freely — no command prefix
2. Text is appended to the in-memory session log with a timestamp
3. Prompt returns, player continues writing

**Notes:**
- Any line not starting with `/` is treated as journal text
- Multi-line entries supported: player ends with a blank line or `.` on its own line
- Journal entries render in a muted style to distinguish from mechanical output

---

### UC-03: Make a Move (Digital Dice)

**Actor:** Player  
**Trigger:** `/move [name]` — e.g. `/move strike`

**Main Flow:**
1. CLI fuzzy-matches the move name against the move registry
2. Displays move description and available stats
3. Player selects stat (numbered menu or types stat name)
4. Player enters any adds (default 0)
5. CLI rolls action die (d6) and two challenge dice (2d10) internally
6. Computes action score: `die + stat + adds`
7. Compares against challenge dice, determines outcome tier:
   - **Strong Hit:** action score beats both challenge dice
   - **Weak Hit:** action score beats one challenge die
   - **Miss:** action score beats neither
   - **Match:** challenge dice are equal (any outcome)
8. Displays result panel with all values visible
9. Shows outcome text from move definition
10. If momentum burn would improve result, offers the option
11. Result appended to session log

**Exit Criteria:** Move result displayed and logged; player continues journaling.

---

### UC-04: Make a Move (Physical Dice)

**Actor:** Player  
**Trigger:** `/move [name]` with dice mode set to `physical` or `mixed`

**Main Flow:**
1–4. Same as UC-03 (move lookup, stat selection, adds)
5. CLI prompts: `Roll your action die (d6): >`
6. Player enters result (validated 1–6, re-prompts on invalid)
7. CLI prompts: `Roll challenge dice (2d10): >`
8. Player enters two values space-separated (e.g. `4 7`) (validated 1–10 each)
9. Outcome resolution proceeds identically to UC-03 from step 6

**Alternate Flow — Mixed Mode Per-Roll Override:**
- Player appends `--manual` to any move command to force physical prompt regardless of mode setting
- Player appends `--auto` to force digital roll regardless of mode setting

**Edge Cases:**
- Out-of-range input: gentle re-prompt with range reminder, no stack trace
- Momentum burn path: if player has enough momentum to improve outcome, the burn prompt appears before the manual roll prompt since no additional dice are needed

---

### UC-05: Consult an Oracle (Digital)

**Actor:** Player  
**Trigger:** `/oracle [table name]` — e.g. `/oracle action theme` or `/oracle planet class`

**Main Flow:**
1. CLI matches table name against oracle registry (supports partial/fuzzy match)
2. If multiple tables named: rolls all of them in sequence (common pattern: action + theme together)
3. Rolls d100 internally for each table
4. Displays result panel with table name, roll value, and result
5. Result appended to session log

**Supported Oracle Tables (POC subset):**
- Action / Theme (the core creative pair)
- Planet Class / Descriptor / Atmosphere
- Settlement Name / Trouble / Population
- NPC Role / Disposition / Name (spacer)
- Derelict Type / Zone
- Combat Event / Threat
- Feature / Detail (generic)

---

### UC-06: Consult an Oracle (Physical Dice)

**Actor:** Player  
**Trigger:** `/oracle [table]` with dice mode `physical`

**Main Flow:**
1. CLI matches table name
2. Prompts: `Roll d100 (or two d10s as percentile): >`
3. Player enters 1–100; CLI looks up the result
4. Displays result panel; appended to log

**Note:** Two d10s read as percentile (e.g. rolling 3 and 7 = 37). A result of `00` or `100` both map to 100.

---

### UC-07: Manage Vows

**Actor:** Player  
**Trigger:** `/vow [rank] [description]` or `/progress [partial vow name]`

**Create Vow Flow:**
1. Player runs `/vow formidable find the survivors of the Andurath`
2. Vow created with rank (Troublesome/Dangerous/Formidable/Extreme/Epic) and a progress track starting at 0
3. Vow displayed and saved to character

**Mark Progress Flow:**
1. Player runs `/progress andurath` (fuzzy match on vow name)
2. CLI shows current progress track, adds ticks per rank:
   - Troublesome: 3 boxes / Dangerous: 2 / Formidable: 1 / Extreme: 2 ticks / Epic: 1 tick
3. Progress track re-displayed with filled boxes

**Fulfill a Vow:**
1. `/fulfill andurath` — triggers a progress roll (no dice, just progress score vs 2d10)
2. Physical or digital mode applies to the 2d10 challenge roll

---

### UC-08: Adjust Character Tracks

**Actor:** Player  
**Trigger:** Direct track adjustment commands

**Supported commands:**
```
/health +1        # or -1, +2, etc.
/spirit -1
/supply +1
/momentum +2
/burn             # burn momentum for current roll outcome
```

**Flow:**
1. CLI validates new value is within track bounds (0–5 for health/spirit/supply, -6 to +10 for momentum)
2. Displays updated track inline
3. Change appended to session log as a mechanical note

---

### UC-09: View Character Sheet

**Actor:** Player  
**Trigger:** `/char`

**Display:**
- Name, background, homeworld
- All five stats
- Momentum track with current/max and reset value
- Health, Spirit, Supply tracks as filled/empty dots
- Active vows with progress tracks
- Assets (name only in POC)

---

### UC-10: End Session and Export

**Actor:** Player  
**Trigger:** `/end`

**Main Flow:**
1. CLI prompts for an optional session title
2. Displays session summary: moves made, oracles consulted, vow progress
3. Writes two files:
   - `sessions/session_NN_[slug].md` — this session only
   - `journal/[character_name]_journal.md` — full cumulative journal (appended)
4. Saves character state to `saves/[character_name].json`
5. Displays closing message with session number and file paths

**Markdown Export Format:**
```markdown
# Session 12 — Drift Station Erebus
*[Character Name] | [Date]*

---

I push through the airlock into recycled air that smells of rust...

---
**STRIKE** | Iron 3 + d6(5) + 1 = 9 vs [4, 7] → **Strong Hit**
+1 momentum (now 6)

---

The security officer doesn't reach for his weapon...
```

---

### UC-11: Configure Dice Mode

**Actor:** Player  
**Trigger:** Settings menu at session start, or `/settings dice [digital|physical|mixed]` in-session

**Options:**

| Mode | Behavior |
|------|----------|
| `digital` | CLI rolls all dice silently |
| `physical` | CLI prompts for every die value |
| `mixed` | Digital by default; `--manual` flag on any command triggers physical prompt |

Persisted per-character in the save file.

---

### UC-12: Get Help

**Actor:** Player  
**Trigger:** `help`, `help moves`, `help oracles`, `/move ?`

**Flow:**
1. `help` alone — lists all commands with one-line descriptions
2. `help moves` — lists all available moves grouped by category
3. `help oracles` — lists all available oracle tables
4. `/move ?` — shows full move text for that move without triggering it

---

## 4. Moves Included (POC Subset)

**Adventure Moves:** Face Danger, Secure an Advantage, Gather Information, Heal, Resupply, Make Camp, Undertake an Expedition, Finish an Expedition

**Connection Moves:** Make a Connection, Compel, Test Your Relationship

**Combat Moves:** Enter the Fray, Strike, Clash, Take Decisive Action, Face Defeat, Battle

**Fate Moves:** Pay the Price, Ask the Oracle

**Vow Moves:** Swear an Iron Vow, Reach a Milestone, Forsake Your Vow, Fulfill Your Vow

---

## 5. Data Format (TOML)

### moves.toml (excerpt)
```toml
[strike]
name = "Strike"
category = "combat"
description = "When you attack in close quarters..."
stat_options = ["iron", "edge"]
strong_hit = "Inflict +1 harm. You may also choose one..."
weak_hit = "Inflict your harm."
miss = "Pay the Price."
momentum_on_strong = 1

[face_danger]
name = "Face Danger"
category = "adventure"
description = "When you attempt something risky..."
stat_options = ["edge", "heart", "iron", "shadow", "wits"]
strong_hit = "You are successful. Take +1 momentum."
weak_hit = "You succeed but at a cost. Choose one..."
miss = "Pay the Price."
```

### oracles.toml (excerpt)
```toml
[action]
name = "Action"
die = "d100"
results = [
  [1, 1, "Advance"],
  [2, 2, "Attack"],
  # ...
  [100, 100, "Withdraw"]
]

[planet_class]
name = "Planet Class"
die = "d100"
results = [
  [1, 15, "Desert World"],
  [16, 30, "Furnace World"],
  # ...
]
```

---

## 6. State / Save Format (JSON)

```json
{
  "character": {
    "name": "Kael Morrow",
    "homeworld": "Drift Station Erebus",
    "stats": { "edge": 2, "heart": 1, "iron": 3, "shadow": 2, "wits": 3 },
    "health": 4, "spirit": 3, "supply": 2,
    "momentum": 5, "momentum_max": 10, "momentum_reset": 2,
    "assets": ["command_ship", "ace", "empath"]
  },
  "vows": [
    {
      "description": "Find the survivors of the Andurath",
      "rank": "formidable",
      "progress": 4,
      "fulfilled": false
    }
  ],
  "settings": {
    "dice_mode": "digital"
  },
  "session_count": 12
}
```

---

## 7. Implemented Features

### Core Mechanics (Starforged)
- ✅ Move resolution (all 56 moves)
- ✅ Oracle lookups (200+ tables)
- ✅ Character creation and management
- ✅ Vow tracking and progress
- ✅ Asset library (90+ cards)
- ✅ Choose Your Truths wizard
- ✅ Momentum burn mechanic

### Session Management
- ✅ REPL-based journaling
- ✅ Markdown export (session + cumulative)
- ✅ Save/load character state
- ✅ Persistent sessions (survive Ctrl-C)

### Quality of Life
- ✅ Guided mode (gameplay tutorial)
- ✅ Tab completion
- ✅ Fuzzy command matching
- ✅ Digital/physical/mixed dice modes
- ✅ Adventures directory configuration

---

## 8. Planned Features

### Starforged Enhancements
- 📋 Interactive asset abilities
- 📋 Asset health/integrity tracking
- 💭 Sector/star map generation
- 💭 NPC relationship tracking
- 💭 Connection system integration

### New Systems
- 📋 **Mythic GME** - Fate Chart, Chaos Factor, Random Events
- 💭 **Other systems** - Based on user demand

### Infrastructure
- 💭 Plugin architecture for community systems
- 💭 Theme customization
- 💭 Cloud sync (optional)

**Legend:**
- ✅ Implemented
- 📋 Planned (designed, ready to implement)
- 💭 Proposed (under consideration)

See [features/](features/) for detailed feature specifications.

---

## 9. Living Document

This specification evolves as Soloquest grows:

- **Use cases** remain stable — they define core workflows
- **Architecture** grows as new systems are added
- **Features** link to detailed specs in [features/](features/)
- **Systems** documented in [systems/](systems/)

When adding significant new functionality:
1. Create a feature spec in [features/](features/)
2. Link to it from this document
3. Update use cases if workflows change
4. Update architecture overview if structure changes

**Version History:**
- **v2.0** (2026-02-17) - Restructured for multi-system support, renamed from POC spec
- **v1.0** (2026-02-14) - Original proof-of-concept specification
