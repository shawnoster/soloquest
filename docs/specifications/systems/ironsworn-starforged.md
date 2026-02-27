# Ironsworn: Starforged System

**System Type:** Powered by the Apocalypse (PbtA) variant
**Genre:** Sci-fi space opera
**Created by:** Shawn Tomkin
**License:** Creative Commons Attribution 4.0

---

## Overview

Ironsworn: Starforged is a standalone tabletop RPG about spacefarers in a dangerous frontier. Players take on the role of adventurers exploring the Forge, a vast expanse of space settled by humans who fled a dying Earth.

wyrd provides mechanical support for Starforged's core systems:
- Move-based resolution
- Oracle-driven narrative generation
- Character progression and assets
- Vow tracking and progress mechanics
- Campaign setup (Choose Your Truths)

---

## Core Mechanics

### Move Resolution

Starforged uses a **move system** where players trigger moves by fictional positioning. Each move follows the pattern:

1. Player describes action
2. Choose relevant stat (Edge, Heart, Iron, Shadow, Wits)
3. Roll action die (d6) + stat + any adds
4. Compare against two challenge dice (d10, d10)

**Outcomes:**
- **Strong Hit** - Action score beats both challenge dice
- **Weak Hit** - Action score beats one challenge die
- **Miss** - Action score beats neither challenge die
- **Match** - Challenge dice are equal (opportunity or complication)

### Stats

Five core stats rated 1-3:
- **Edge** - Speed, agility, ranged combat
- **Heart** - Courage, empathy, sociability
- **Iron** - Physical strength, close combat, endurance
- **Shadow** - Stealth, deception, trickery
- **Wits** - Expertise, observation, technical skill

### Tracks

- **Health (0-5)** - Physical condition
- **Spirit (0-5)** - Mental/emotional state
- **Supply (0-5)** - Provisions and resources
- **Momentum (-6 to +10)** - Narrative advantage, can be burned to improve rolls

### Vows

Central to Starforged's narrative structure:
- Players swear **iron vows** (quests)
- Ranked by difficulty: Troublesome, Dangerous, Formidable, Extreme, Epic
- Progress tracked in 10-box tracks
- Fulfilled via progress move (comparing progress score vs challenge dice)

### Assets

90+ asset cards representing:
- **Paths** - Character backgrounds and approaches
- **Companions** - NPCs who travel with you
- **Modules** - Ship upgrades and capabilities
- **Vehicles** - Additional transport

Each asset has 3 abilities; some have health/integrity tracks.

### Oracles

200+ tables for generating:
- Story prompts (Action/Theme)
- Locations (planets, settlements, derelicts)
- NPCs (names, roles, dispositions)
- Events and complications
- Descriptive details

---

## Campaign Setup

### Choose Your Truths

Before play begins, Starforged offers 14 fundamental worldbuilding questions:

1. **Cataclysm** - What destroyed the precursor civilization?
2. **Exodus** - Why did humanity leave Earth?
3. **Communities** - How are settlements organized?
4. **Iron** - What does swearing an iron vow mean?
5. **Laws** - What governance exists?
6. **Religion** - What do people believe?
7. **Magic** - Does anything supernatural exist?
8. **Communication** - How do people communicate across space?
9. **Medicine** - What's the state of healthcare?
10. **Artificial Intelligence** - Do AIs exist?
11. **War** - Is there conflict?
12. **Lifeforms** - What alien life exists?
13. **Precursors** - What remains of ancient civilizations?
14. **Horrors** - What terrifying things lurk in space?

Each category offers 3-4 preset options or the ability to write custom truths. Players can choose, roll randomly, or customize freely.

**Implementation:** See [features/starforged/choose-your-truths.md](../features/starforged/choose-your-truths.md)

---

## Data Integration

### Dataforged

wyrd uses the [dataforged](https://github.com/rsek/dataforged) package for comprehensive Starforged content:
- All 56 moves with full text
- 200+ oracle tables with roll ranges
- 90 asset cards with abilities
- Truth categories with subchoices
- Quest starters and campaign seeds

**License:** CC BY 4.0 / CC BY-NC 4.0 / MIT
**Maintainer:** rsek
**Content:** © Shawn Tomkin

### Custom Data

wyrd can override dataforged entries via TOML files in `wyrd/data/`:
- `moves.toml` - Custom or house-ruled moves
- `oracles.toml` - Additional oracle tables
- `truths.toml` - Custom truth categories

Custom data takes priority over dataforged, allowing house rules and homebrew content.

---

## Implemented Features

### Core Mechanics
- ✅ Move resolution (all 56 moves)
- ✅ Oracle lookups (200+ tables)
- ✅ Character creation and management
- ✅ Stat and track adjustments
- ✅ Momentum burn mechanic

### Vows & Progress
- ✅ Swear iron vows
- ✅ Mark progress
- ✅ Fulfill vows (progress roll)
- ✅ Forsake vows

### Assets
- ✅ Asset library (90+ cards)
- ✅ Asset display
- ⚠️ Asset abilities (partial - not fully interactive)
- ⚠️ Asset health/integrity tracking (planned)

### Campaign Setup
- ✅ Choose Your Truths wizard
- ✅ Quest starters
- ✅ Truth storage and display

### Session Management
- ✅ Session journaling
- ✅ Markdown export
- ✅ Cumulative journal
- ✅ Save/load character state

### Quality of Life
- ✅ Guided mode (gameplay tutorial)
- ✅ Tab completion
- ✅ Fuzzy command matching
- ✅ Digital/physical/mixed dice modes

---

## Planned Features

### Assets
- Interactive asset abilities
- Asset health/integrity tracking
- Asset upgrade tracking

### Exploration
- Sector/star map generation
- Location tracking
- Discovery logging

### NPCs & Connections
- NPC relationship tracking
- Connection moves integration
- Bond progress tracking

### Advanced Features
- Campaign clock tracking
- Threat tracking
- Legacy tracks (campaign-level progression)

---

## Related Documentation

- **[Choose Your Truths Feature](../features/starforged/choose-your-truths.md)** - Campaign setup wizard
- **[Architecture](../architecture.md)** - System-agnostic design
- **[CLI Specification](../spec.md)** - Complete CLI specification
