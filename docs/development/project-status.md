# Project Status

**Last Updated:** 2026-02-26
**Current Version:** 2.35.0
**Phase:** Post-POC, Active Development

---

## Overview

wyrd is a **functionally complete** CLI companion for playing Ironsworn: Starforged solo. The POC is done, and the project is now in active development for enhancements and polish.

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

**2.35.0** (2026-02-26)
- Fix: strip markdown links from oracle result text (#131)

**2.34.0**
- Render description fields as bullet list in character.md (#130)

**2.33.0**
- Renamed project and CLI from `soloquest` to `wyrd` (#129)

**2.32.0**
- Truths markdown format, display spacing, and UX polish

**2.31.0–2.31.1**
- Resumable truths wizard with inline oracle lookups (#127)
- Refactored truths to adventure/campaign level

**2.30.0**
- Auto-fill paths from suggestion and show asset cards (#126)

**2.29.0**
- One-liner CLI mode and oracle direct lookup (#125)

**2.28.0**
- Unified prompt_toolkit session (#123)

**2.26.0**
- Multi-line journal entry with paragraph block detection (#119)

**2.24.0**
- Markdown formatting in journal entries (#117)

**2.23.0**
- External editor integration for journal entries (#116)

**2.22.0**
- Oracle display data moved to `oracles.toml` (#115)

**2.21.0**
- Persistent command history via `FileHistory` (#113)

**2.20.0**
- Ayu Dark semantic color system and GitHub Dark theme (#105)

**2.19.0–2.18.0**
- Co-op truth consensus (`/truths propose/review/accept/counter`) (#94)
- Shared campaign vows (`/vow --shared`) with progress sync (#93)

**2.17.0**
- Oracle interpretation workflow (`/interpret` and `/accept`) (#92)

**2.16.0**
- Co-op partner activity polling and `/sync` command (#91)

**2.15.0**
- Oracle sync publishing and `LogEntry` player attribution (#90)

**2.14.0**
- Sandbox startup mode and `/campaign start` wizard (#89)

**2.13.0**
- `CampaignState` model and `/campaign` command (#88)

**2.12.0**
- `SyncPort` interface, `LocalAdapter`, and `FileLogAdapter` (#87)

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

### Co-op Play ([#79](https://github.com/shawnoster/wyrd/issues/79)) — Complete

Two-player cooperative play implemented using a hexagonal architecture (port/adapter pattern). Single-player remains the default zero-friction experience.

**Architecture:** `SyncPort` interface with adapters:
- `LocalAdapter` — single-player (no-op, zero overhead)
- `FileLogAdapter` — per-player JSONL event logs on shared filesystem

**Sub-issues (all shipped):**

| # | Issue | Status |
|---|-------|--------|
| [#80](https://github.com/shawnoster/wyrd/issues/80) | SyncPort interface + LocalAdapter | ✅ 2.12.0 |
| [#81](https://github.com/shawnoster/wyrd/issues/81) | Event model + per-player JSONL log | ✅ 2.12.0 |
| [#82](https://github.com/shawnoster/wyrd/issues/82) | CampaignState model + `/campaign` commands | ✅ 2.13.0 |
| [#83](https://github.com/shawnoster/wyrd/issues/83) | Player attribution on LogEntry | ✅ 2.15.0 |
| [#84](https://github.com/shawnoster/wyrd/issues/84) | Truth negotiation (propose/accept/counter) | ✅ 2.19.0 |
| [#85](https://github.com/shawnoster/wyrd/issues/85) | Oracle interpretation (`/interpret` + `/accept`) | ✅ 2.17.0 |
| [#86](https://github.com/shawnoster/wyrd/issues/86) | Shared vows with single progress track | ✅ 2.18.0 |

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
- ✅ Co-op play ([#79](https://github.com/shawnoster/wyrd/issues/79) — shipped 2.12.0–2.19.0)
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
- **2026-02-26:** Co-op play fully shipped (v2.12.0–2.19.0); project renamed `wyrd` (v2.33.0)
