# Adding Systems and Features - Process Guide

Step-by-step processes for extending wyrd with new game systems and features.

---

## Table of Contents

1. [Adding a New Game System](#adding-a-new-game-system)
2. [Adding a New Feature](#adding-a-new-feature)
3. [Adding Cross-System Integration](#adding-cross-system-integration)
4. [Documentation Standards](#documentation-standards)
5. [Testing Requirements](#testing-requirements)

---

## Adding a New Game System

Follow this process when adding support for a new solo RPG system (e.g., Mythic GME, Blades in the Dark, etc.).

### Phase 1: Research & Planning

**1.1 Verify Licensing**
- [ ] Confirm the game is legally available for tool development
- [ ] Check license type (CC, OGL, permission required, etc.)
- [ ] Document attribution requirements
- [ ] Identify any usage restrictions

**1.2 Analyze Core Mechanics**
- [ ] Identify core resolution mechanics (dice, moves, etc.)
- [ ] Map out character/entity structure
- [ ] List all mechanical systems (progress tracks, resources, etc.)
- [ ] Document oracle/random generation systems
- [ ] Note any unique mechanics not in other systems

**1.3 Find or Create Data Sources**
- [ ] Look for existing data projects (like dataforged for Starforged)
- [ ] Evaluate data format and licensing
- [ ] Plan data extraction if creating from scratch
- [ ] Document data attribution

### Phase 2: Documentation

**2.1 Create System Specification**

Create `docs/specifications/systems/[system-name].md`:

```markdown
# [System Name]

**System Type:** [PbtA, OSR, GME, etc.]
**Genre:** [Genre]
**Created by:** [Author]
**License:** [License]

## Overview
Brief description of the game and what makes it unique.

## Core Mechanics
Document the resolution system, dice mechanics, etc.

## Character/Entity Structure
How characters (or equivalent) are represented.

## Data Integration
How game content is sourced and integrated.

## Implemented Features
What's currently working.

## Planned Features
What's coming next.

## Related Documentation
Links to feature specs.
```

**2.2 Update System Index**

Add entry to `docs/specifications/systems/README.md`:
- System name and status
- Link to system spec
- Brief feature list

### Phase 3: Data Layer

**3.1 Create Data Directory**
```bash
mkdir -p wyrd/data/[system-name]
```

**3.2 Add Data Files**

Create TOML files for game content:
- `moves.toml` - Move/action definitions
- `oracles.toml` - Random tables
- `[system].toml` - System-specific content

Follow existing TOML structure from other systems.

**3.3 Vendor External Data (if applicable)**
```bash
mkdir -p wyrd/data/[system-name]/vendor
# Add vendored data with LICENSE.md
```

### Phase 4: Models

**4.1 Create System Models**

Add models in `wyrd/models/`:

```python
# models/[system]_character.py
from dataclasses import dataclass

@dataclass
class [System]Character:
    """Character model for [System]."""
    name: str
    # System-specific fields

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: dict) -> "[System]Character":
        """Deserialize from dictionary."""
        ...
```

**4.2 Extend Base Character (if needed)**

Update `models/character.py` to support system-specific extensions:

```python
# Optional system-specific fields
mythic_chaos_factor: int | None = None
blades_stress: int | None = None
```

### Phase 5: Engine

**5.1 Create Engine Modules**

Add system logic in `wyrd/engine/`:

```bash
mkdir -p wyrd/engine/[system-name]
```

Create core mechanics:
```python
# engine/[system]/resolution.py
def resolve_[mechanic](params) -> Result:
    """Core resolution mechanic."""
    ...

# engine/[system]/oracles.py
def consult_[oracle](table: str) -> str:
    """Oracle table lookup."""
    ...
```

**5.2 Create Data Loaders**

```python
# engine/[system]/loader.py
def load_[system]_data(path: Path) -> [System]Data:
    """Load game data from TOML files."""
    ...
```

### Phase 6: Commands

**6.1 Create Command Handlers**

Add commands in `wyrd/commands/`:

```python
# commands/[system].py
from wyrd.loop import GameState

def handle_[command](state: GameState, args: str) -> None:
    """Handle /[command] for [System]."""
    # 1. Parse arguments
    # 2. Call engine logic
    # 3. Display results
    # 4. Update state
    # 5. Log to session
```

**6.2 Register Commands**

Update `commands/registry.py`:

```python
COMMAND_REGISTRY = {
    # Existing commands...
    "[system-command]": commands.[system].handle_[command],
}
```

**6.3 Add Tab Completion**

Update `commands/completion.py`:

```python
def get_completions(document, complete_event):
    # Add system-specific completions
    if text.startswith("/[command]"):
        return [[system]_completions]
```

### Phase 7: Testing

**7.1 Create Test Suite**

```bash
mkdir -p tests/[system-name]
```

Create comprehensive tests:
- `tests/[system]/test_models.py` - Model serialization
- `tests/[system]/test_engine.py` - Core mechanics
- `tests/[system]/test_commands.py` - Command handlers
- `tests/[system]/test_integration.py` - End-to-end flows

**Target:** 80%+ coverage on new code

**7.2 Add Test Fixtures**

Create test data in `tests/fixtures/[system]/`:
- Sample characters
- Test oracle tables
- Example game states

### Phase 8: Documentation

**8.1 Update User Guides**

- Add section to `docs/user-guide/getting-started.md`
- Create `docs/user-guide/[system]-guide.md` if needed
- Update command reference in main README

**8.2 Update Main README**

- Add system to overview
- Update data attribution
- Add system-specific commands to command table

**8.3 Create CHANGELOG Entry**

Add to `CHANGELOG.md`:
```markdown
## [Unreleased]

### Added
- Support for [System Name] ([#PR])
  - Core mechanics implementation
  - Oracle tables
  - Character management
```

### Phase 9: Release

**9.1 Create Feature Branch**
```bash
git checkout -b feat/[system-name]-support
```

**9.2 Commit with Convention**
```bash
git add .
git commit -m "feat: add [System Name] support

- Implement core resolution mechanics
- Add oracle table system
- Create character model and tracking
- Add comprehensive test coverage

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**9.3 Create Pull Request**

Use template:
```markdown
## Summary
- Add support for [System Name]
- [Brief feature list]

## Implementation
- Data files in `wyrd/data/[system]/`
- Engine logic in `wyrd/engine/[system]/`
- Commands: /[command1], /[command2]
- [X] tests, [Y]% coverage

## Test Plan
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual playtest completed
- [x] Documentation updated

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

---

## Adding a New Feature

Follow this process for adding a feature to an existing system or a shared feature.

### Step 1: Create Feature Specification

**Location:**
- System-specific: `docs/specifications/features/[system]/[feature-name].md`
- Shared: `docs/specifications/features/shared/[feature-name].md`

**Template:**
```markdown
# [Feature Name]

**System:** [System Name or "Shared"]
**Status:** Planning
**Created:** [Date]

## Overview
What problem does this solve?

## Goals
- Goal 1
- Goal 2
- Goal 3

## User Experience

### Commands
- `/[command]` - Description

### Workflow
1. User does X
2. System responds with Y
3. State updates to Z

## Technical Design

### Data Models
```python
@dataclass
class [Model]:
    field: type
```

### Engine Logic
- Function 1: Purpose
- Function 2: Purpose

### UI Components
- Display format
- User prompts
- Output formatting

## Testing Strategy
- Unit tests: [What to test]
- Integration tests: [What to test]
- Manual test cases: [Scenarios]

## Related Documentation
- [System Spec](../../systems/[system].md)
- [Related Feature](./related-feature.md)
```

### Step 2: Update Feature Index

Add to `docs/specifications/features/README.md`:
- Feature name and status
- Link to spec
- Brief description

### Step 3: Implement

Follow the appropriate implementation phases from "Adding a New Game System":
- Data layer (if needed)
- Models (if needed)
- Engine logic
- Commands
- Tests

### Step 4: Document & Release

- Update user guides
- Create PR with feature spec link

---

## Adding Cross-System Integration

For features that span multiple systems (e.g., using Mythic with Ironsworn).

### Step 1: Create Integration Specification

Create `docs/specifications/integration/[topic].md`:

```markdown
# [Integration Topic]

**Systems Involved:** [System A], [System B]
**Status:** Planning

## Use Case
Why would users want this integration?

## Approach
How will the systems work together?

## Technical Design
- System A provides: [What]
- System B provides: [What]
- Integration point: [Where/How]

## User Experience
How does the user activate/use this integration?

## Conflicts & Resolution
What happens when systems conflict?

## Related Documentation
- [System A Spec](../systems/system-a.md)
- [System B Spec](../systems/system-b.md)
```

### Step 2: Update System Specs

Add "Integration Points" section to each affected system spec documenting:
- What the system exposes
- What the system can consume
- Compatibility notes

### Step 3: Implement Integration Layer

Create `wyrd/integration/` module:
```python
# integration/[system-a]_[system-b].py
def integrate_[systems](state: GameState) -> IntegratedState:
    """Combine [System A] and [System B] mechanics."""
    ...
```

---

## Documentation Standards

### File Naming
- Use kebab-case: `choose-your-truths.md`
- Be descriptive: `mythic-fate-chart.md` not `fate.md`
- Group by system in features/

### Markdown Style
- Use ATX headers (`#` not underlines)
- Include YAML-style metadata at top
- Use tables for comparisons
- Use code blocks with language tags
- Link liberally to related docs

### Status Labels
- 💭 **Proposed** - Under consideration
- 📋 **Planned** - Approved, ready to implement
- 🚧 **In Progress** - Active development
- ✅ **Implemented** - Complete and tested
- ⏸️ **Paused** - Temporarily suspended
- ❌ **Cancelled** - Will not be implemented

### Version History
Add to bottom of specs when major changes occur:
```markdown
## Version History

- **v2.0** (2026-02-17) - Restructured for multi-system support
- **v1.0** (2026-02-15) - Initial specification
```

---

## Testing Requirements

### Coverage Targets
- **New Systems:** 80%+ coverage on all new code
- **Features:** 90%+ on core logic, 70%+ on commands
- **Integration:** 70%+ on integration points

### Test Categories

**Unit Tests:**
- Model serialization/deserialization
- Engine mechanics (pure functions)
- Data loading and validation

**Integration Tests:**
- Command workflows
- State management
- Cross-system interactions

**Manual Tests:**
- Playtest scenarios
- Error handling
- Edge cases

### Test File Organization
```
tests/
├── [system]/
│   ├── test_models.py
│   ├── test_engine.py
│   ├── test_commands.py
│   └── test_integration.py
├── fixtures/
│   └── [system]/
│       ├── characters.json
│       └── test_data.toml
└── test_integration_[a]_[b].py
```

---

## Quick Reference Checklist

### New System
- [ ] Research & verify licensing
- [ ] Create system spec in `systems/`
- [ ] Add data files in `wyrd/data/[system]/`
- [ ] Create models in `wyrd/models/`
- [ ] Implement engine in `wyrd/engine/[system]/`
- [ ] Add commands in `wyrd/commands/`
- [ ] Write comprehensive tests (80%+ coverage)
- [ ] Update all documentation
- [ ] Create PR with full description

### New Feature
- [ ] Create feature spec in `features/[system]/`
- [ ] Implement (data, models, engine, commands)
- [ ] Write tests (90%+ on logic, 70%+ on commands)
- [ ] Update user guides
- [ ] Create PR with spec link

### Cross-System Integration
- [ ] Create integration spec in `integration/`
- [ ] Update affected system specs
- [ ] Implement integration layer
- [ ] Test all integration points
- [ ] Document user workflow
- [ ] Create PR with integration guide

---

## Examples

### Example: Adding Mythic GME

1. Create `docs/specifications/systems/mythic-gme.md`
2. Add `wyrd/data/mythic/fate-chart.toml`
3. Create `wyrd/engine/mythic/fate_chart.py`
4. Add `wyrd/commands/mythic.py` with `/fate` command
5. Write `tests/mythic/test_fate_chart.py`
6. Update `docs/user-guide/mythic-guide.md`
7. PR: `feat: add Mythic GME support`

### Example: Adding Asset Abilities (Starforged Feature)

1. Create `docs/specifications/features/starforged/asset-abilities.md`
2. Extend `wyrd/models/asset.py`
3. Update `wyrd/engine/assets.py`
4. Enhance `/asset` command
5. Write `tests/test_asset_abilities.py`
6. Update getting started guide
7. PR: `feat: add interactive asset abilities`

### Example: Mythic + Ironsworn Integration

1. Create `docs/specifications/integration/mythic-ironsworn.md`
2. Add "Integration Points" to both system specs
3. Create `wyrd/integration/mythic_ironsworn.py`
4. Add system selection to `/settings`
5. Write integration tests
6. Update user guides with examples
7. PR: `feat: add Mythic GME + Ironsworn integration`

---

## Getting Help

- **Questions:** Open a GitHub Discussion
- **Proposals:** Create an issue with `enhancement` label
- **Process Improvements:** Submit PR to this document

**Remember:** Documentation first, code second. A well-documented system is easier to implement, test, and maintain.
