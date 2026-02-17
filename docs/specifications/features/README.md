# Feature Specifications

Detailed implementation plans for individual features, organized by game system.

---

## Starforged Features

Features specific to Ironsworn: Starforged:

- **[Choose Your Truths](starforged/choose-your-truths.md)** - Campaign setup wizard with 14 truth categories

### Planned
- Asset ability tracking - Interactive asset abilities
- Sector mapping - Star map generation and location tracking
- Connection system - NPC relationships and bonds

---

## Shared Features

Features that work across multiple game systems:

### Implemented
- **Session Journaling** - Core REPL loop (see [architecture.md](../architecture.md))
- **Markdown Export** - Session and cumulative journal export
- **Dice Modes** - Digital, physical, and mixed dice rolling
- **Guided Mode** - Interactive gameplay tutorials

### Planned
- **Plugin System** - Load community-contributed game systems
- **Theme Customization** - Terminal color schemes and formatting
- **Cloud Sync** - Optional session backup to cloud storage

---

## Mythic Features (Planned)

Features specific to Mythic GME:

- **Fate Chart** - Yes/no question resolution
- **Chaos Factor** - Dynamic difficulty scaling
- **Random Events** - Scene interruptions and complications
- **Meaning Tables** - Action/Description oracle pairs
- **Thread Tracking** - Story thread management

---

## Feature Document Template

Each feature spec should include:

```markdown
# [Feature Name]

**System:** [System Name or "Shared"]
**Status:** [Planning | In Progress | Implemented]
**Created:** [Date]

## Overview
What problem does this solve?

## Goals
- Goal 1
- Goal 2

## Technical Design
How does it work?

## Data Models
What structures are involved?

## Commands
What commands does the user invoke?

## User Experience
How do users interact with it?

## Testing
How do we validate it works?

## Related Documentation
- Link to system spec
- Link to architecture doc
```

---

## Feature Status Key

- ✅ **Implemented** - Feature is complete and tested
- 🚧 **In Progress** - Feature is being actively developed
- 📋 **Planned** - Feature is designed and ready to implement
- 💭 **Proposed** - Feature is under consideration
- ⏸️ **Paused** - Feature development temporarily suspended
- ❌ **Cancelled** - Feature will not be implemented
