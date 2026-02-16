# Documentation Restructure Plan

**Date:** 2026-02-15
**Goal:** Align soloquest documentation with modern GitHub conventions

---

## Current State Assessment

### Root Directory (11 markdown files - TOO MANY)
```
✅ README.md              # Keep - main entry point
✅ CLAUDE.md              # Keep - AI agent instructions
✅ CHANGELOG.md           # Keep - standard location
⚠️  PROJECT_STATUS.md     # Archive - dated snapshot (2026-02-14)
⚠️  PLAN.md               # Archive - completion plan (should be GitHub issues)
⚠️  PLAYTEST_GUIDE.md     # Move to docs/development/
⚠️  PLAYTEST_RESULTS.md   # Archive - empty template
⚠️  AUTOMATED_TESTING_COMPLETE.md  # Archive - dated summary
⚠️  AUTOMATED_TEST_RESULTS.md      # Archive - dated results
⚠️  MIGRATION_NOTES.md    # Consolidate or move to docs/
⚠️  INSTALL_JUST.md       # Consolidate into README or docs/
```

### docs/ Directory (3 files, 1 subdirectory - GOOD START)
```
docs/
├── starforged-cli-spec.md          # Rename to poc-spec.md, move to specifications/
├── getting-started.md              # Good - move to user-guide/
├── adventures-directory.md         # Good - move to user-guide/
└── adr/
    └── 001-repo-workflow-and-conventions.md  # Good location
```

---

## Proposed New Structure

```
/
├── README.md                       # Main entry point with clear navigation
├── CLAUDE.md                       # Updated with new doc structure
├── CHANGELOG.md                    # Version history (automated)
├── LICENSE                         # Project license
├── CONTRIBUTING.md                 # How to contribute (NEW)
│
├── docs/
│   ├── README.md                   # Documentation hub with navigation (NEW)
│   │
│   ├── user-guide/
│   │   ├── getting-started.md     # MOVE from docs/
│   │   ├── adventures-directory.md # MOVE from docs/
│   │   ├── commands.md            # EXTRACT from README (NEW)
│   │   └── dice-modes.md          # EXTRACT from README (NEW)
│   │
│   ├── development/
│   │   ├── setup.md               # CONSOLIDATE: INSTALL_JUST, MIGRATION_NOTES (NEW)
│   │   ├── testing.md             # MOVE: PLAYTEST_GUIDE (NEW)
│   │   ├── contributing.md        # Symlink to /CONTRIBUTING.md (NEW)
│   │   └── architecture.md        # High-level architecture (NEW)
│   │
│   ├── specifications/
│   │   └── poc-spec.md            # RENAME from starforged-cli-spec.md (MOVE)
│   │
│   ├── adr/
│   │   ├── README.md              # ADR index (NEW)
│   │   └── 001-repo-workflow-and-conventions.md  # KEEP
│   │
│   └── archive/
│       ├── README.md              # Explain what's here (NEW)
│       ├── PROJECT_STATUS_2026-02-14.md    # RENAME and ARCHIVE
│       ├── PLAN_2026-02-14.md              # RENAME and ARCHIVE
│       ├── AUTOMATED_TESTING_COMPLETE.md   # ARCHIVE
│       ├── AUTOMATED_TEST_RESULTS.md       # ARCHIVE
│       └── PLAYTEST_RESULTS.md             # ARCHIVE
│
└── [project files...]
```

---

## What This Achieves

### ✅ Modern GitHub Conventions
- Clean root directory (3-4 key files)
- Organized docs/ with clear categories
- Standard locations (CONTRIBUTING.md, CHANGELOG.md)

### ✅ Clear Navigation for Humans
- docs/README.md as documentation hub
- User docs separate from dev docs
- Easy to find what you need

### ✅ Clear Navigation for AI Agents
- CLAUDE.md points to current specs and plans
- Single source of truth for project state
- Historical snapshots preserved in archive/

### ✅ Better Maintenance
- Dated snapshots archived with dates in filename
- Living docs in proper locations
- No duplicate/overlapping content

---

## Migration Plan

### Phase 1: Create New Structure ✅
- [ ] Create docs/README.md (navigation hub)
- [ ] Create docs/user-guide/ directory
- [ ] Create docs/development/ directory
- [ ] Create docs/specifications/ directory
- [ ] Create docs/archive/ directory with README

### Phase 2: Move User Documentation ✅
- [ ] Move docs/getting-started.md → docs/user-guide/
- [ ] Move docs/adventures-directory.md → docs/user-guide/
- [ ] Extract command reference from README → docs/user-guide/commands.md
- [ ] Extract dice modes from README → docs/user-guide/dice-modes.md

### Phase 3: Move Development Documentation ✅
- [ ] Move PLAYTEST_GUIDE.md → docs/development/testing.md
- [ ] Consolidate INSTALL_JUST + MIGRATION_NOTES → docs/development/setup.md
- [ ] Create docs/development/architecture.md
- [ ] Create docs/development/contributing.md
- [ ] Create root CONTRIBUTING.md (symlink or copy)

### Phase 4: Move Specifications ✅
- [ ] Rename docs/starforged-cli-spec.md → docs/specifications/poc-spec.md

### Phase 5: Archive Old Docs ✅
- [ ] Move PROJECT_STATUS.md → docs/archive/PROJECT_STATUS_2026-02-14.md
- [ ] Move PLAN.md → docs/archive/PLAN_2026-02-14.md
- [ ] Move AUTOMATED_TESTING_COMPLETE.md → docs/archive/
- [ ] Move AUTOMATED_TEST_RESULTS.md → docs/archive/
- [ ] Move PLAYTEST_RESULTS.md → docs/archive/
- [ ] Create docs/archive/README.md explaining contents

### Phase 6: Update Navigation ✅
- [ ] Update README.md with Documentation section
- [ ] Update CLAUDE.md with new doc locations
- [ ] Create docs/README.md as hub
- [ ] Create docs/adr/README.md as ADR index
- [ ] Update all cross-references

### Phase 7: Create Current Project State ✅
- [ ] Create docs/development/project-status.md (living doc)
- [ ] Update with current status (post-1.4.0 release)
- [ ] Point CLAUDE.md to this as source of truth

---

## Implementation Commands

```bash
# Phase 1: Create structure
mkdir -p docs/{user-guide,development,specifications,archive}

# Phase 2: Move user docs
git mv docs/getting-started.md docs/user-guide/
git mv docs/adventures-directory.md docs/user-guide/

# Phase 3: Move dev docs
git mv PLAYTEST_GUIDE.md docs/development/testing.md

# Phase 4: Move specs
git mv docs/starforged-cli-spec.md docs/specifications/poc-spec.md

# Phase 5: Archive old docs
git mv PROJECT_STATUS.md docs/archive/PROJECT_STATUS_2026-02-14.md
git mv PLAN.md docs/archive/PLAN_2026-02-14.md
git mv AUTOMATED_TESTING_COMPLETE.md docs/archive/
git mv AUTOMATED_TEST_RESULTS.md docs/archive/
git mv PLAYTEST_RESULTS.md docs/archive/

# Clean up remaining files
# (INSTALL_JUST.md and MIGRATION_NOTES.md will be consolidated into docs/development/setup.md)
```

---

## New File Templates

### docs/README.md
```markdown
# Soloquest Documentation

## For Users
- [Getting Started](user-guide/getting-started.md) - Complete walkthrough
- [Commands Reference](user-guide/commands.md) - All available commands
- [Adventures Directory](user-guide/adventures-directory.md) - Configuration guide
- [Dice Modes](user-guide/dice-modes.md) - Digital, physical, and mixed modes

## For Developers
- [Setup Guide](development/setup.md) - Development environment setup
- [Contributing](development/contributing.md) - How to contribute
- [Testing](development/testing.md) - Testing strategy and manual testing
- [Architecture](development/architecture.md) - System design overview

## Specifications & Design
- [POC Specification](specifications/poc-spec.md) - Original proof-of-concept spec
- [Architecture Decision Records](adr/) - Design decisions

## Project Info
- [Changelog](../CHANGELOG.md) - Version history
- [License](../LICENSE) - MIT License
```

### docs/development/project-status.md (NEW - Living Doc)
```markdown
# Project Status

**Last Updated:** 2026-02-15
**Current Version:** 1.4.0
**Phase:** Post-POC, Active Development

## Current State

The project is **functionally complete** for its core POC goals:
- ✅ Character creation and management
- ✅ Move resolution (digital/physical/mixed dice)
- ✅ Oracle system with 200+ tables (via dataforged)
- ✅ Vow tracking and progress
- ✅ Session journaling and Markdown export
- ✅ Asset system (90+ assets from dataforged)
- ✅ 160+ tests passing with good coverage

## Recent Work (1.4.0)
- Added justfile for cross-platform development
- Fixed character display and fuzzy matching improvements
- Added cancel/exit capability to interactive prompts

## Active Tasks

See GitHub Issues for current work:
https://github.com/your-org/soloquest/issues

## Next Milestones

See GitHub Projects for roadmap:
https://github.com/your-org/soloquest/projects
```

### CLAUDE.md Update
Add navigation section:
```markdown
## Project Documentation

**Current project state:** See [docs/development/project-status.md](docs/development/project-status.md)
**New feature ideas:** See GitHub Issues with `enhancement` label
**Specifications:** See [docs/specifications/poc-spec.md](docs/specifications/poc-spec.md)
**Architecture decisions:** See [docs/adr/](docs/adr/)
**Historical snapshots:** See [docs/archive/](docs/archive/)
```

---

## Success Criteria

- [ ] Root directory has ≤4 markdown files (README, CLAUDE, CHANGELOG, CONTRIBUTING)
- [ ] All user documentation in docs/user-guide/
- [ ] All dev documentation in docs/development/
- [ ] Specs in docs/specifications/
- [ ] Historical docs archived with dates in filename
- [ ] docs/README.md provides clear navigation
- [ ] CLAUDE.md points to current project state
- [ ] All cross-references updated
- [ ] No broken links

---

## Timeline

**Estimated effort:** 2-3 hours
- Phase 1-5: 1 hour (file moves and renames)
- Phase 6: 1 hour (update navigation and cross-references)
- Phase 7: 30 minutes (create project-status.md)
- Testing: 30 minutes (verify all links work)

---

## Benefits

### For Users
- Clear path to getting started
- Easy to find command reference
- Well-organized user guides

### For Contributors
- Clear contribution guidelines
- Easy to find dev setup instructions
- Testing docs in one place

### For Maintainers
- Single source of truth for project status
- Historical decisions preserved in ADRs
- Clean root directory
- Easy to update living docs

### For AI Agents
- CLAUDE.md points to current state
- No confusion from stale dated snapshots
- Clear structure for finding information
- Historical context preserved in archive/

---

## Questions to Resolve

1. Should INSTALL_JUST.md content go in:
   - [ ] README.md (if simple)
   - [ ] docs/development/setup.md (if detailed)
   - [ ] Both (brief in README, detailed in docs)

2. Should MIGRATION_NOTES.md:
   - [ ] Be consolidated into docs/development/setup.md
   - [ ] Remain as separate docs/development/migration.md
   - [ ] Be archived (if no longer relevant)

3. Should we create GitHub Issues/Projects to replace:
   - [ ] PROJECT_STATUS.md tracking
   - [ ] PLAN.md task lists

4. Should docs/development/project-status.md be:
   - [ ] A living markdown file (easy to edit)
   - [ ] Generated from GitHub API (always current)
   - [ ] Just point to GitHub Projects/Milestones

---

## Next Steps

1. Review this plan with project owner
2. Get approval on structure
3. Execute migration (can be done in single PR)
4. Update all documentation
5. Verify no broken links
6. Close this with commit implementing the restructure
