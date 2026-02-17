# Project Status

**Last Updated:** 2026-02-15
**Current Version:** 1.4.0
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

**1.4.0** (2026-02-15)
- Added justfile for cross-platform development
- Fixed character display and fuzzy matching improvements
- Added cancel/exit capability to all interactive prompts

**1.3.0**
- Enhanced interactive prompt handling

**1.2.0**
- Character and asset display improvements

See [CHANGELOG.md](../../CHANGELOG.md) for complete history.

---

## Test Coverage

**160+ tests passing** with good coverage:

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
| Overall | ~27% | Expected due to interactive UI code |

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
soloquest/
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

### Current Focus

Check [GitHub Issues](https://github.com/yourusername/soloquest/issues) for active work.

### Roadmap

See [GitHub Projects](https://github.com/yourusername/soloquest/projects) for planned features.

### Open Questions

- Asset ability tracking (in progress)
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
- ❌ Co-op/guided mode
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

- **Bug reports:** [GitHub Issues](https://github.com/yourusername/soloquest/issues)
- **Feature requests:** [GitHub Discussions](https://github.com/yourusername/soloquest/discussions)
- **General questions:** [Ironsworn Discord](https://discord.gg/ironsworn)

---

## Historical Context

For historical project snapshots, see [docs/archive/](../archive/).

Key historical milestones:
- **2026-02-14:** POC completion (9 phases complete)
- **2026-02-14:** Comprehensive automated testing added
- **2026-02-15:** Documentation restructure and GitHub conventions alignment
