# wyrd Architecture

**Version:** 2.0
**Language:** Python 3.13
**Target:** Multi-system solo journaling companion CLI

---

## Overview

wyrd is a terminal-based companion for playing solo RPGs. The CLI handles the mechanical layer — move resolution, oracle lookups, dice rolling, character tracking — while keeping the journaling experience as the primary surface. Every session produces a Markdown artifact the player can keep.

### Core Design Principles

1. **Journal-first interface** - The hybrid journal/command loop feels natural to use
2. **Flexible dice modes** - Physical and digital dice modes work without friction
3. **Readable export** - Session export produces genuinely readable journals
4. **System-agnostic core** - Architecture supports multiple game systems

---

## Architecture Overview

```
wyrd/
├── main.py               # Entry point, session bootstrap
├── loop.py               # Main REPL loop
├── commands/             # Command handlers (UI layer)
│   ├── registry.py       # Command routing
│   ├── move.py           # /move resolution
│   ├── oracle.py         # /oracle lookups
│   ├── vow.py            # /vow, /progress (Ironsworn-specific)
│   ├── character.py      # /char, stat/track adjustments
│   ├── session.py        # /log, /end, /note
│   ├── truths.py         # /truths (Starforged-specific)
│   └── guide.py          # /guide (gameplay tutorials)
├── engine/               # Game mechanics (business logic)
│   ├── dice.py           # Dice provider abstraction (digital/physical/mixed)
│   ├── moves.py          # Move definitions and resolution logic
│   ├── oracles.py        # Oracle table data and lookup
│   ├── truths.py         # Truth category loader
│   └── assets.py         # Asset card system
├── models/               # Data models
│   ├── character.py      # Character dataclass
│   ├── vow.py            # Vow dataclass (Ironsworn-specific)
│   ├── session.py        # Session log dataclass
│   └── truths.py         # Truth models (Starforged-specific)
├── journal/              # Export system
│   └── exporter.py       # Markdown export
├── data/                 # Game content (system-specific)
│   ├── moves.toml        # Move definitions
│   ├── oracles.toml      # Oracle tables
│   ├── truths.toml       # Truth categories
│   └── dataforged/       # Vendored dataforged content
├── state/                # Persistence
│   └── save.py           # JSON save/load
└── ui/                   # Display formatting
    └── display.py        # Rich-based rendering helpers
```

### Layer Separation

- **Commands/** - UI layer, handles user input and formatting
- **Engine/** - Business logic, system-specific mechanics
- **Models/** - Data structures, serialization
- **Journal/** - Export and formatting
- **State/** - Persistence layer

---

## Key Dependencies

- **rich** — Terminal rendering (panels, tables, progress bars)
- **prompt_toolkit** — Multi-line input, history, autocomplete
- **tomllib** (stdlib 3.11+) — Data file parsing
- **dataforged** — Ironsworn: Starforged game content

**No TUI framework; no curses; no textual** - Pure REPL with rich formatting.

---

## Core Features (System-Agnostic)

### Session Management

Every session:
- Loads character state
- Maintains in-memory journal log
- Exports to Markdown on `/end`
- Auto-saves character state

### Journaling Interface

- **Default mode:** Any text without `/` prefix is journaled
- **Commands:** Lines starting with `/` trigger mechanics
- **Multi-line support:** Natural prose entry
- **Timestamps:** Automatic session metadata

### Dice System

Three modes, all support both digital and physical dice:

| Mode | Behavior |
|------|----------|
| `digital` | CLI rolls all dice automatically |
| `physical` | CLI prompts for every die value |
| `mixed` | Digital by default; `--manual` flag on commands triggers physical prompt |

The dice abstraction layer supports:
- d6 (action dice)
- d10 (challenge dice)
- d100 (oracle tables)
- System-specific dice (future: Mythic d10 tables, etc.)

### Character Tracking

System-agnostic character model includes:
- **Name and metadata** (system-dependent fields)
- **Stats** (flexible key-value pairs)
- **Tracks** (health, resources, momentum, etc.)
- **Assets/abilities** (system-specific)

### Markdown Export

Every session exports to:
- **Session file** - `sessions/session_NN_[slug].md`
- **Cumulative journal** - `journal/[character]_journal.md`

Export format interleaves:
- Narrative journal entries (prose)
- Mechanical outcomes (moves, oracles)
- Metadata (timestamps, character state changes)

---

## System Integration Points

To add a new game system (e.g., Mythic GME):

### 1. Data Files

Add system-specific data in `wyrd/data/[system]/`:
```
data/
├── ironsworn/
│   ├── moves.toml
│   ├── oracles.toml
│   └── assets.toml
└── mythic/
    ├── fate-chart.toml
    ├── meaning-tables.toml
    └── chaos-factor.toml
```

### 2. Engine Modules

Create system-specific engines in `wyrd/engine/[system]/`:
```python
# engine/mythic/fate_chart.py
def resolve_fate_question(chaos_factor: int, odds: str) -> str:
    """Resolve a yes/no question using Mythic's Fate Chart."""
    ...
```

### 3. Command Handlers

Add system-specific commands in `wyrd/commands/`:
```python
# commands/mythic.py
def handle_fate_question(state: GameState, args: str) -> None:
    """Handle /fate command for Mythic GME."""
    ...
```

### 4. Models

Extend character model for system-specific needs:
```python
# models/character.py
class Character:
    # Core fields (all systems)
    name: str

    # System-specific (optional)
    chaos_factor: int | None = None  # Mythic
    vows: list[Vow] | None = None    # Ironsworn
```

---

## Future Considerations

### Multi-System Sessions

Future versions may support:
- Running multiple systems in one session
- Using Mythic GME for oracle questions in Ironsworn
- System selection at session start
- Hybrid mechanical systems

### Plugin Architecture

Potential plugin system for community-contributed systems:
```
~/.wyrd/plugins/
└── blades-in-the-dark/
    ├── manifest.toml
    ├── moves.toml
    └── clocks.py
```

---

## Related Documentation

- **[Systems](systems/)** - System-specific specifications
- **[Features](features/)** - Feature implementation plans
- **[Integration](integration/)** - Cross-system integration approaches
