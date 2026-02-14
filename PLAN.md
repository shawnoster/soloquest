# Starforged CLI — Completion Plan

**Goal:** Take the POC from "functionally complete" to "ready for real gameplay"

---

## Phase 10: Validation & Polish (Current)

### 10.1 Manual Testing ⏳
**Goal:** Verify the complete gameplay loop works smoothly

**Tasks:**
- [ ] Create a new character from scratch
  - Test stat assignment validation
  - Test asset selection
  - Test background vow creation
  - Test dice mode selection
- [ ] Play through 2-3 complete scenes:
  - Mix of journal entries and commands
  - Test `/move` with different stats
  - Test `/oracle` for narrative prompts
  - Test track adjustments (health, spirit, supply, momentum)
  - Test vow progress and fulfillment
  - Test momentum burn on a miss
- [ ] Test session end:
  - Export session to Markdown
  - Verify readability of exported journal
  - Verify character state saves correctly
- [ ] Resume saved session:
  - Load character
  - Continue from previous session
  - Verify session number increments
  - Verify vows persist
- [ ] Test all dice modes:
  - Digital (auto-roll)
  - Physical (manual input)
  - Mixed (with --manual and --auto flags)
- [ ] Test error paths:
  - Invalid move name
  - Invalid oracle table
  - Invalid vow name (progress/fulfill)
  - Out-of-range track adjustments
  - Quit with unsaved entries (Ctrl+C)
  - Quit command with confirmation

**Success Criteria:**
- Complete a full session start-to-end without errors
- Exported Markdown is readable and well-formatted
- All commands work as documented
- Error messages are helpful and don't crash

---

### 10.2 Documentation 📝
**Goal:** Make it easy for new users to get started

**Tasks:**
- [ ] Add example session walkthrough to README
  - Show actual CLI output
  - Demonstrate journal + commands
  - Show exported Markdown
- [ ] Add "Quick Start" section to README
  - First time setup
  - Character creation
  - Basic commands
- [ ] Add troubleshooting section
  - Common issues
  - How to report bugs
- [ ] Add gameplay tips
  - When to use which moves
  - Oracle combinations
  - Momentum management

**Success Criteria:**
- A new user can start playing without reading the spec
- README answers the most common questions

---

### 10.3 Edge Case Hardening 🛡️
**Goal:** Graceful failure for unexpected inputs

**Tasks:**
- [ ] Test invalid move names:
  - Typos
  - Partial matches
  - Ambiguous matches
- [ ] Test invalid oracle names:
  - Typos
  - Unknown tables
- [ ] Test invalid vow operations:
  - Progress on non-existent vow
  - Fulfill non-existent vow
  - Forsake with 0 spirit
- [ ] Test track edge cases:
  - Adjust health/spirit/supply below 0
  - Adjust momentum above max
  - Burn momentum with negative momentum
  - Debilities with already-maxed debilities
- [ ] Test save/load edge cases:
  - Corrupted JSON
  - Missing files
  - Empty saves directory
- [ ] Test input validation:
  - Special characters in character names
  - Very long journal entries
  - Empty commands
  - Commands with only flags

**Success Criteria:**
- No crashes or stack traces for any user input
- Error messages guide users to correct usage
- Invalid state is prevented or caught early

---

### 10.4 UI/UX Improvements ✨
**Goal:** Make the experience feel polished

**Tasks:**
- [ ] Command aliases:
  - `/m` → `/move`
  - `/o` → `/oracle`
  - `/v` → `/vow`
  - `/p` → `/progress`
  - `/f` → `/fulfill`
  - `/c` → `/char`
- [ ] Move outcome formatting:
  - Better visual separation of outcome tiers
  - Highlight strong hits vs misses
  - Show move text in panels
- [ ] Progress bar visualization:
  - Show vow progress tracks as visual bars (■■■■□□□□□□)
  - Color-code by rank
- [ ] Session resume context:
  - Show last 3-5 journal entries on resume
  - Show active vows on start
- [ ] Momentum burn prompt:
  - Only offer if it would actually improve outcome
  - Show before/after outcome clearly
- [ ] Character sheet improvements:
  - Add debilities display
  - Show filled/empty dots for tracks (●●●○○)
  - Color-code low health/spirit warnings

**Success Criteria:**
- CLI feels responsive and intuitive
- Important information is highlighted
- Visual feedback matches the narrative tone

---

## Phase 11: Expansion (Optional — Beyond POC)

### 11.1 Asset System
- [ ] Asset definitions in TOML
- [ ] Asset ability tracking
- [ ] Asset upgrade system
- [ ] `/asset` command

### 11.2 Connection Tracker
- [ ] NPC model with relationship progress tracks
- [ ] `/connection` command
- [ ] Connection-specific moves (Make a Connection, Compel, etc.)

### 11.3 Sector Map
- [ ] Location tracking
- [ ] Travel system
- [ ] Sector generation

### 11.4 Campaign Threats
- [ ] Threat progress clocks
- [ ] `/threat` command

### 11.5 Export Enhancements
- [ ] HTML export with CSS styling
- [ ] PDF export via weasyprint or similar
- [ ] JSON export for external tools

### 11.6 Oracle Expansion
- [ ] Full oracle tables from rulebook
- [ ] Custom user-defined oracles
- [ ] Oracle categories and grouping
- [ ] Combined oracle rolls (e.g., `/oracle settlement` → name + trouble + population)

---

## Success Metrics

### POC Complete (Phase 10)
- [ ] 100% of core commands tested manually
- [ ] 0 crashes during normal gameplay
- [ ] README has example session
- [ ] New user can complete a session in <15 minutes

### Production Ready (Phase 11+)
- [ ] Test coverage >50% overall
- [ ] All moves from rulebook implemented
- [ ] Full oracle tables
- [ ] Asset system functional
- [ ] User documentation site

---

## Timeline Estimate

| Phase | Effort | Description |
|-------|--------|-------------|
| 10.1 Manual Testing | 2-3 hours | Play through multiple sessions |
| 10.2 Documentation | 1-2 hours | README example, quick start |
| 10.3 Edge Cases | 2-3 hours | Test and fix error paths |
| 10.4 UI/UX | 3-4 hours | Aliases, formatting, visualization |
| **Phase 10 Total** | **8-12 hours** | POC validation complete |
| Phase 11 (optional) | 20-40 hours | Full expansion features |

---

## Current Focus

**Immediate next steps:**
1. ✅ Status assessment (done)
2. ✅ Plan creation (done)
3. 🎯 Run manual playthrough (next)
4. 🎯 Document findings
5. 🎯 Fix any issues discovered
6. 🎯 Update README with example

**Then:**
- Edge case testing
- UI polish
- Final validation

---

## Notes

- The core engine is solid (100% test coverage)
- The REPL loop works (prompt_toolkit integration successful)
- Data-driven design makes adding moves/oracles easy
- Export format is clean and readable
- Architecture supports future expansion

**Main risk:** UX feel. Need real gameplay testing to validate:
- Journal + command flow feels natural
- Exported sessions are genuinely readable
- Dice modes work without friction

**Mitigation:** Do manual testing early, iterate on UX based on findings.
