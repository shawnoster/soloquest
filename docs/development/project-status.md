# Project Status

**Last Updated:** 2026-02-18
**Current Version:** 2.11.3
**Phase:** Post-POC, Active Development

---

## Overview

Soloquest is a **functionally complete** CLI companion for playing Ironsworn: Starforged solo. The POC is done, and the project is now in active development for enhancements and polish.

---

## Current State

### ✅ Core Features Complete

- **Character Management** - Create, save, load characters with stats and tracks
- **Move Resolution** - Full move system with digital/physical/mixed dice modes
- **Oracle System** - 200+ oracle tables via dataforged integration
- **Vow Tracking** - Create, progress, fulfill, and forsake vows
- **Asset System** - 90+ assets from dataforged
- **Choose Your Truths** - Interactive campaign setup wizard with 14 truth categories
- **Session Journaling** - Hybrid journal/command interface
- **Markdown Export** - Beautiful session and cumulative journal exports
- **Adventures Directory** - Configurable data storage for Obsidian/Logseq integration

### Recent Releases

**2.11.3** (2026-02-18)
- Moved guide prose to TOML data file
- Applied ruff formatting, added AGENTS.md
- Moved character creation tables to TOML data file

See [CHANGELOG.md](../../CHANGELOG.md) for complete history.

---

## Test Coverage

**597 tests passing** with good coverage:

| Module | Coverage | Notes |
|--------|----------|-------|
| `engine/moves.py` | 100% | Move resolution, momentum burn |
| `engine/oracles.py` | 100% | Oracle table loading and lookups |
| `models/character.py` | 100% | Character model and tracks |
| `models/vow.py` | 100% | Vow progress and fulfillment |
| `models/session.py` | 100% | Session logging |
| `engine/dice.py` | 83% | Dice modes |
| `state/save.py` | 67% | Save/load (partial) |
| `commands/*` | Variable | Interactive, tested via integration |
| Overall | ~67% | Expected due to interactive UI code |

---

## Technology Stack

- **Language:** Python 3.13+
- **Package Manager:** uv
- **Build System:** hatchling
- **CLI Framework:** prompt_toolkit
- **UI Library:** rich
- **Testing:** pytest, pytest-cov
- **Linting/Formatting:** ruff
- **Task Runner:** just (with Makefile fallback)
- **CI/CD:** GitHub Actions with semantic-release

---

## Architecture

The project follows a clean separation of concerns:

```
wyrd/
├── commands/    # Command handlers (UI layer)
├── engine/      # Game mechanics (business logic)
├── models/      # Data models
├── state/       # Persistence
├── journal/     # Export system
├── ui/          # Display formatting
└── data/        # Game content (dataforged)
```

See [ADR-001](../adr/001-repo-workflow-and-conventions.md) for architectural decisions.

---

## Active Development

### Current Focus: Co-op Play ([#79](https://github.com/shawnoster/wyrd/issues/79))

Designing two-player cooperative play using a hexagonal architecture (port/adapter pattern) so the sync mechanism is swappable without touching game logic. Single-player remains the default zero-friction experience.

**Architecture:** `SyncPort` interface with adapters:
- `LocalAdapter` — single-player (no-op, zero overhead)
- `FileLogAdapter` — per-player JSONL event logs on shared filesystem

**Key features:**
- Shared campaign directory with per-player character saves
- Append-only event log (narrative + mechanical actions)
- Consensus protocol for truths and oracle interpretations
- Shared vows with single progress track

**Sub-issues (in dependency order):**

| # | Issue | Status |
|---|-------|--------|
| [#80](https://github.com/shawnoster/wyrd/issues/80) | SyncPort interface + LocalAdapter | Planned |
| [#81](https://github.com/shawnoster/wyrd/issues/81) | Event model + per-player JSONL log | Planned |
| [#82](https://github.com/shawnoster/wyrd/issues/82) | CampaignState model + `/campaign` commands | Planned |
| [#83](https://github.com/shawnoster/wyrd/issues/83) | Player attribution on LogEntry | Planned |
| [#84](https://github.com/shawnoster/wyrd/issues/84) | Truth negotiation (propose/accept/counter) | Planned |
| [#85](https://github.com/shawnoster/wyrd/issues/85) | Oracle interpretation (`/interpret` + `/accept`) | Planned |
| [#86](https://github.com/shawnoster/wyrd/issues/86) | Shared vows with single progress track | Planned |

### Other Open Questions

- Connection/relationship system
- Sector/location tracking
- Custom oracle tables
- Export formats (HTML, PDF)

---

## Known Limitations

These are **intentionally out of scope** for the current phase:

- ❌ Full sector/star map generation
- ❌ NPC relationship web
- ❌ Campaign threat tracking
- 🔄 Co-op play (in design — [#79](https://github.com/shawnoster/wyrd/issues/79))
- ❌ Web or GUI frontend
- ❌ Audio/sound hooks

These may be added in future versions based on user demand.

---

## Contributing

The project welcomes contributions! See:

- **[Contributing Guide](../../CONTRIBUTING.md)** - How to contribute
- **[Setup Guide](setup.md)** - Development environment setup
- **[Testing Guide](testing.md)** - Manual testing procedures

---

## Questions or Feedback?

- **Bug reports:** [GitHub Issues](https://github.com/shawnoster/wyrd/issues)
- **Feature requests:** [GitHub Issues](https://github.com/shawnoster/wyrd/issues)
- **General questions:** [Ironsworn Discord](https://discord.gg/ironsworn)

---

## Historical Context

For historical project snapshots, see [docs/archive/](../archive/).

Key historical milestones:
- **2026-02-14:** POC completion (9 phases complete)
- **2026-02-14:** Comprehensive automated testing added
- **2026-02-15:** Documentation restructure and GitHub conventions alignment
- **2026-02-18:** Co-op play design complete (hexagonal architecture, event log)
