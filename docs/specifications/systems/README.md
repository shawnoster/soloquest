# Game Systems

System-level specifications for each supported solo RPG system.

---

## Supported Systems

### Ironsworn: Starforged

**Status:** ✅ Active
**Genre:** Sci-fi space opera
**Created by:** Shawn Tomkin

See [ironsworn-starforged.md](ironsworn-starforged.md) for complete specification.

**Core Features:**
- Move-based resolution (PbtA-style)
- Oracle tables for narrative generation
- Vow tracking and progress mechanics
- Character stats and momentum
- Asset system (paths, companions, modules)
- Choose Your Truths campaign setup

---

## Planned Systems

### Mythic GME

**Status:** 🔮 Planned
**Genre:** System-agnostic game master emulator
**Created by:** Tana Pigeon

**Planned Features:**
- Fate Chart (yes/no questions)
- Chaos Factor tracking
- Random event tables
- Meaning tables (Action/Description)
- NPC tracking
- Thread and scene management

**Integration:** Could run alongside Ironsworn or independently

---

## System Comparison

| Feature | Starforged | Mythic GME |
|---------|-----------|------------|
| Move Resolution | ✅ PbtA-style | ❌ N/A (GM emulator) |
| Oracle Tables | ✅ 200+ tables | ✅ Meaning tables |
| Character Stats | ✅ 5 stats | ❌ System-agnostic |
| Progress Tracking | ✅ Vows | ✅ Threads |
| Journaling | ✅ Native | ✅ Scene-based |
| Dice | d6 + 2d10 | d100 + d10 |

---

## Adding a New System

To add a new game system to Soloquest:

1. **Research** - Study the game's mechanics and licensing
2. **System Spec** - Create `[system-name].md` in this directory
3. **Data Files** - Add game content to `wyrd/data/[system]/`
4. **Engine** - Implement mechanics in `wyrd/engine/[system]/`
5. **Commands** - Add system-specific commands
6. **Tests** - Write comprehensive test coverage
7. **Documentation** - Update user guides and this README

See [architecture.md](../architecture.md) for integration points.
