# Choose Your Truths Feature - Implementation Plan

**Feature:** Add "Choose Your Truths" guided wizard for campaign setup
**Target Version:** 2.2.0
**Created:** 2026-02-16
**Status:** Planning

---

## Overview

"Choose Your Truths" is a worldbuilding exercise from Ironsworn: Starforged where players establish the fundamental facts about their version of The Forge (the game's setting). This feature will add an interactive wizard that guides players through 14 truth categories, allowing them to define their campaign's setting before beginning play.

### References
- [Iron Vault - Choose Your Truths Guide](https://ironvault.quest/player's-guide/getting-started/03-choose-your-truths.html)
- [Dataforged Repository](https://github.com/rsek/dataforged) - Contains 14 setting truth categories
- Ironsworn: Starforged Rulebook (Getting Started section)

---

## Background

In Starforged, "Choose Your Truths" appears in the "Getting Started" section of the rulebook. It presents 14 fundamental questions about the setting:

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

Each category typically offers 3-4 options ranging from more optimistic to darker interpretations. Players can choose from the options, roll randomly, or write their own custom truth.

---

## Goals

1. **Add campaign setup wizard** - Guide new players through truth selection
2. **Store truths with campaign** - Persist player's chosen truths
3. **Display truths** - Show truths in character sheet and session exports
4. **Integrate with existing flow** - Fit naturally into current character creation

---

## Architecture

### New Files

```
wyrd/
├── models/
│   └── truths.py           # Truth and TruthCategory models
├── engine/
│   └── truths.py           # Truth data loading and logic
├── commands/
│   └── truths.py           # /truths command handler
└── data/
    └── truths.toml         # Custom truths override (optional)

tests/
├── models/
│   └── test_truths.py
├── engine/
│   └── test_truths.py
└── commands/
    └── test_truths.py
```

### Data Model

```python
# wyrd/models/truths.py
from dataclasses import dataclass

@dataclass
class TruthOption:
    """A single option for a truth category."""
    text: str
    description: str  # Longer explanation

@dataclass
class TruthCategory:
    """A truth category with multiple options."""
    name: str
    description: str
    options: list[TruthOption]

@dataclass
class ChosenTruth:
    """A player's chosen truth for their campaign."""
    category: str
    option_text: str
    custom_text: str = ""  # Optional player modifications
```

### Integration Points

1. **Character Model** - Add `truths: list[ChosenTruth]` field
2. **Save/Load** - Serialize truths to character JSON
3. **Character Sheet Display** - Show truths in `/char` command
4. **Session Export** - Include truths in journal markdown header
5. **Registry** - Register `/truths` command

---

## Implementation Tasks

### Task 1: Review truths data from dataforged

**Goal:** Obtain the 14 truth categories and their options.

**Approach:**
- Check if existing `wyrd/data/dataforged/*.json` files contain truths
- If not, download/extract from [dataforged npm package](https://github.com/rsek/dataforged)
- The truths data is in `dist/starforged/dataforged.json`
- May need to add a separate JSON file: `wyrd/data/dataforged/truths.json`

**Deliverable:** Truth data available in `wyrd/data/dataforged/`

---

### Task 2: Create data model for truths

**Goal:** Add Python models for truth data.

**Files:**
- `wyrd/models/truths.py` - TruthOption, TruthCategory, ChosenTruth

**Integration:**
- Update `wyrd/models/character.py`:
  ```python
  @dataclass
  class Character:
      # ... existing fields ...
      truths: list[ChosenTruth] = field(default_factory=list)
  ```

**Deliverable:** Truth models with serialization support

---

### Task 3: Implement truths data loader

**Goal:** Load truth categories from dataforged.

**File:** `wyrd/engine/truths.py`

**Pattern:** Follow existing patterns in `engine/oracles.py` and `engine/moves.py`

**Functions:**
```python
def load_truth_categories() -> dict[str, TruthCategory]:
    """Load all truth categories from dataforged JSON."""

def get_truth_category(name: str) -> TruthCategory | None:
    """Get a specific truth category by name."""
```

**Deliverable:** Truth loading engine with tests

---

### Task 4: Create interactive truths wizard

**Goal:** Implement `/truths` command with interactive flow.

**File:** `wyrd/commands/truths.py`

**Command Variants:**
- `/truths` - Start the wizard (if no truths set) or show current truths
- `/truths start` - (Re)start the truth selection wizard
- `/truths show` - Display current truths
- `/truths edit [category]` - Edit a specific truth

**Wizard Flow:**
```
1. Display welcome message explaining Choose Your Truths
2. For each truth category (14 total):
   a. Show category name and description
   b. Display 3-4 options with descriptions
   c. Prompt: "Choose option [1-4], roll [r], or custom [c]"
   d. Store selection
   e. Show confirmation and continue to next
3. Display summary of all chosen truths
4. Confirm and save to character
5. Log to session journal
```

**UI Pattern:** Similar to `guided_mode.py` - step-by-step wizard with rich display

**Deliverable:** Fully interactive `/truths` command

---

### Task 5: Add truths to session journal

**Goal:** Include truths in exports and displays.

**Changes:**

1. **Character Sheet Display** (`ui/display.py`):
   ```python
   def character_sheet(...):
       # ... existing display ...
       # Add section for truths
       if character.truths:
           console.print("\n[bold]Campaign Truths:[/bold]")
           for truth in character.truths:
               console.print(f"  • {truth.category}: {truth.option_text}")
   ```

2. **Session Export** (`journal/exporter.py`):
   ```markdown
   # Session N - Title
   *Character Name | Date*

   ## Campaign Setting

   [Display truths here]

   ---

   [Rest of journal...]
   ```

3. **Session Log** - Add entry when truths are set:
   ```python
   state.session.add_note("Campaign truths established")
   ```

**Deliverable:** Truths integrated into all relevant displays

---

### Task 6: Write tests for truths feature

**Goal:** Comprehensive test coverage.

**Test Files:**
- `tests/models/test_truths.py` - Model serialization
- `tests/engine/test_truths.py` - Data loading
- `tests/commands/test_truths.py` - Command handling
- `tests/integration/test_truths_flow.py` - End-to-end wizard

**Coverage Target:** 100% for models and engine, >80% for commands

**Deliverable:** All tests passing with good coverage

---

### Task 7: Update documentation

**Goal:** Document the new feature.

**Files to Update:**

1. **docs/user-guide/getting-started.md**
   - Add "Choose Your Truths" section
   - Explain when and why to use it
   - Show example workflow

2. **docs/development/project-status.md**
   - Add to feature list
   - Update version information

3. **CHANGELOG.md**
   - Add entry for version 2.2.0
   - Document new `/truths` command

4. **Help System** (`wyrd/commands/help.py`):
   - Add `/truths` to command list
   - Add detailed help text

5. **README.md** (if needed)
   - Mention truths feature in features list

**Deliverable:** Complete documentation for users and developers

---

## User Experience Flow

### New Character Creation

```
$ wyrd

Welcome to wyrd!

You don't have a character yet. Let's create one!

Name: Kael Morrow
Homeworld: Drift Station Erebus

[Stat assignment...]

[Assets selection...]

Would you like to Choose Your Truths now? [Y/n]: y

╔══════════════════════════════════════════════════════════╗
║         CHOOSE YOUR TRUTHS - Campaign Setup             ║
╚══════════════════════════════════════════════════════════╝

You'll answer 14 questions about your version of The Forge.
These establish the fundamental truths of your setting.

You can choose from options, roll randomly, or write your own.

Press Enter to continue...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Truth 1 of 14: THE CATACLYSM

The Exodus fleet was forced to flee after a cataclysm.
What was the nature of this disaster?

  [1] The sun of our home system went supernova
  [2] Alien invasion destroyed our civilization
  [3] We destroyed ourselves through war
  [4] An ancient curse or cosmic horror awakened

Choose [1-4], roll [r], or custom [c]: 1

You chose: The sun of our home system went supernova

[Continue through all 14 truths...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your Campaign Truths:

• The Cataclysm: The sun of our home system went supernova
• The Exodus: ...
[... all truths displayed ...]

Save these truths? [Y/n]: y

✓ Campaign truths saved!

[Session begins...]
```

### Viewing Truths Later

```
> /truths

╔══════════════════════════════════════════════════════════╗
║              Your Campaign Truths                        ║
╚══════════════════════════════════════════════════════════╝

• The Cataclysm: The sun of our home system went supernova
• The Exodus: We left in desperation, fleeing certain doom
• Communities: Settlements are isolated and mistrustful
...

Commands:
  /truths edit [category] - Modify a truth
  /truths start - Restart truth selection wizard
```

---

## Technical Considerations

### Data Source Priority

Follow the existing pattern from CLAUDE.md:

1. **Custom TOML** (`wyrd/data/truths.toml`) - User overrides
2. **Dataforged JSON** (`wyrd/data/dataforged/truths.json`) - Official data

### Storage Format

Store truths in character save JSON:

```json
{
  "character": {
    "name": "Kael Morrow",
    "truths": [
      {
        "category": "Cataclysm",
        "option_text": "The sun of our home system went supernova",
        "custom_text": ""
      }
    ]
  }
}
```

### Command Registry

Register in `wyrd/commands/registry.py`:

```python
COMMAND_HANDLERS = {
    # ... existing commands ...
    "truths": truths.handle_truths,
}
```

---

## Success Criteria

- [ ] Player can run `/truths start` to begin wizard
- [ ] All 14 truth categories are presented
- [ ] Player can choose option, roll random, or write custom
- [ ] Truths are saved with character data
- [ ] Truths display in `/char` command
- [ ] Truths appear in session export markdown
- [ ] Tests achieve >80% coverage
- [ ] Documentation is complete
- [ ] Feature integrates smoothly with existing flow

---

## Out of Scope (Future Enhancements)

- Oracle integration (asking "oracle" about truth interpretations)
- Truth-based random events or complications
- Truth interconnections (one truth affecting another)
- Multiple truth "profiles" (different campaigns)
- Collaborative truth selection (multiplayer)

---

## Timeline Estimate

- Task 1 (Data): ~30 minutes
- Task 2 (Models): ~30 minutes
- Task 3 (Loader): ~1 hour
- Task 4 (Wizard): ~2-3 hours
- Task 5 (Display): ~1 hour
- Task 6 (Tests): ~2 hours
- Task 7 (Docs): ~1 hour

**Total:** ~8-9 hours of development time

---

## Next Steps

1. Start with Task 1 - obtain truth data from dataforged
2. Create feature branch: `feat/choose-your-truths`
3. Implement tasks sequentially
4. Test thoroughly after each task
5. Create PR when all tasks complete

---

## Notes

- The 14 truths should be presented in a logical order (setting foundation → specific details)
- UI should be consistent with existing `/guide` wizard style
- Consider adding a "quick setup" option that rolls all truths randomly
- Truths should be optional - players can skip if they prefer to improvise
