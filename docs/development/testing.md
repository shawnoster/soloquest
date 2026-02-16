# Manual Playtest Guide

**Goal:** Test the complete gameplay loop and identify any issues or UX friction.

---

## Setup

```bash
cd /e/solo-cli
uv run starforged
# or
uv run python -m starforged.main
```

---

## Test 1: Character Creation

### Steps:
1. Run the CLI (should see splash screen)
2. Choose to create a new character (type `n`)
3. Enter character details:
   - **Name:** "Kael Vex" (or your choice)
   - **Homeworld:** "Drift Station Erebus"
4. Assign stats (distribute: 3, 2, 2, 1, 1):
   - Edge: 2
   - Heart: 1
   - Iron: 3
   - Shadow: 2
   - Wits: 3
5. Choose 3 assets:
   - "starship"
   - "ace"
   - "gearhead"
6. Enter background vow (Epic):
   - "Discover what destroyed the Andurath colony"
7. Choose dice mode: 1 (Digital)

### Expected Result:
- Character created successfully
- Session starts with character info displayed
- Prompt ready for input

### Checklist:
- [ ] Stat validation works (rejects invalid values)
- [ ] All prompts clear and understandable
- [ ] No crashes or errors
- [ ] Character name displays correctly

---

## Test 2: Journal Entry + Basic Commands

### Scene Setup:
You're investigating an abandoned settlement on a barren moon.

### Steps:

1. **Write journal entry:**
```
The airlock hisses open. Dust swirls in the thin atmosphere. The settlement ahead looks abandoned, but I spot faint light in one of the structures.
```

2. **View character sheet:**
```
/char
```

3. **Check help:**
```
/help
```

4. **Check available moves:**
```
/help moves
```

### Checklist:
- [ ] Journal entry accepted (no `/` prefix)
- [ ] `/char` displays all stats correctly
- [ ] Background vow appears in character sheet
- [ ] Help text is clear and complete
- [ ] Move categories display correctly

---

## Test 3: Move Resolution (Digital Dice)

### Scenario:
You need to search the settlement for clues.

### Steps:

1. **Gather Information (Wits move):**
```
/move gather information
```
   - When prompted for stat: choose `wits` (or enter `5` if numbered)
   - When prompted for adds: enter `0`
   - Observe the roll result

2. **Check session log:**
```
/log
```

3. **Try a combat move - Strike:**
```
/move strike
```
   - Choose stat: `iron`
   - Adds: `1`
   - Observe outcome

4. **Adjust momentum manually:**
```
/momentum +2
```

5. **Check log again:**
```
/log --compact
```

### Checklist:
- [ ] Move lookup works (fuzzy matching)
- [ ] Stat selection clear
- [ ] Dice roll displays clearly
- [ ] Outcome tier visible (Strong Hit/Weak Hit/Miss)
- [ ] Outcome text displays
- [ ] Match detection works (if challenge dice match)
- [ ] Log shows all entries
- [ ] `--compact` flag hides mechanical entries
- [ ] Momentum adjusts correctly

---

## Test 4: Oracle Lookups

### Scenario:
You need narrative prompts.

### Steps:

1. **Consult Action/Theme:**
```
/oracle action theme
```

2. **Single oracle:**
```
/oracle descriptor
```

3. **Check available oracles:**
```
/help oracles
```

4. **Try another oracle:**
```
/oracle npc role
```

5. **Write journal entry incorporating oracle results:**
```
[Write something based on the oracle results you got]
```

### Checklist:
- [ ] Multiple oracles work (action + theme together)
- [ ] Single oracles work
- [ ] Results display clearly
- [ ] All oracle tables listed in help
- [ ] Oracle results logged to session

---

## Test 5: Track Management

### Scenario:
Combat consequences and recovery.

### Steps:

1. **Take damage:**
```
/health -2
```

2. **Lose spirit:**
```
/spirit -1
```

3. **Use supplies:**
```
/supply -1
```

4. **Check character:**
```
/char
```

5. **Try to heal:**
```
/move heal
```
   - Choose stat: `wits`
   - Observe outcome
   - If success, restore health manually:
```
/health +2
```

6. **Test track bounds (should clamp):**
```
/health +10
```
   - Should cap at 5

7. **Test momentum bounds:**
```
/momentum +20
```
   - Should cap at 10

### Checklist:
- [ ] Tracks adjust correctly
- [ ] Negative adjustments work
- [ ] Positive adjustments work
- [ ] Values clamp at min/max (0-5 for health/spirit/supply, -6 to +10 for momentum)
- [ ] Character sheet updates correctly

---

## Test 6: Vow Management

### Scenario:
Swear a new vow and make progress.

### Steps:

1. **Create a dangerous vow:**
```
/vow dangerous Find the source of the signal
```

2. **Check character (should show both vows):**
```
/char
```

3. **Make progress on the vow:**
```
/progress signal
```
   - Should fuzzy match "Find the source of the signal"
   - Dangerous rank = 8 ticks per mark

4. **Mark progress again:**
```
/progress signal
```

5. **Check vow status:**
```
/char
```

6. **Try to fulfill (will probably fail with low progress):**
```
/fulfill signal
```
   - Observe progress roll (no action die)
   - If miss/weak hit, vow stays active

### Checklist:
- [ ] Vow creation works
- [ ] Rank parsing works (dangerous, formidable, extreme, epic, troublesome)
- [ ] Fuzzy matching finds vows by partial name
- [ ] Progress marks correctly (8 ticks for dangerous)
- [ ] Progress score calculated correctly (ticks / 4)
- [ ] Fulfill triggers progress roll
- [ ] Failed fulfill doesn't complete vow

---

## Test 7: Momentum Burn

### Scenario:
Test momentum burn on a miss.

### Steps:

1. **Ensure you have momentum >= 5:**
```
/momentum +6
```

2. **Face Danger (likely to miss with low stats):**
```
/move face danger
```
   - Choose your lowest stat (probably heart: 1)
   - Adds: 0
   - If you get a miss, you should be offered momentum burn
   - Accept the burn (if offered)

3. **Verify momentum reset:**
```
/char
```
   - Momentum should be at reset value (2 by default)

### Checklist:
- [ ] Momentum burn offered only when beneficial
- [ ] Burn upgrades outcome correctly
- [ ] Momentum resets to reset value
- [ ] Before/after outcome clearly shown

---

## Test 8: Debilities

### Scenario:
Test the debility system.

### Steps:

1. **Toggle wounded debility:**
```
/debility wounded
```

2. **Check character:**
```
/char
```
   - Momentum max should be 9 (reduced by 1)

3. **Toggle shaken:**
```
/debility shaken
```
   - Momentum max should be 8
   - Momentum reset should be 1

4. **Check momentum bounds:**
```
/momentum +10
```
   - Should cap at current max (8)

5. **Toggle off wounded:**
```
/debility wounded
```
   - Momentum max should increase to 9

### Checklist:
- [ ] Debilities toggle on/off
- [ ] Momentum max decreases correctly
- [ ] Momentum reset decreases correctly
- [ ] Character sheet shows debilities
- [ ] Momentum respects new caps

---

## Test 9: Forsake a Vow

### Scenario:
Abandon a vow.

### Steps:

1. **Check current spirit:**
```
/char
```

2. **Forsake your dangerous vow:**
```
/forsake
```
   - Should prompt for vow selection
   - Select the "Find the source of the signal" vow
   - Confirm

3. **Verify spirit cost:**
```
/char
```
   - Spirit should be reduced by rank cost (Dangerous = 2)

### Checklist:
- [ ] Forsake prompts for vow selection
- [ ] Confirmation required
- [ ] Spirit cost applied correctly
- [ ] Vow removed from active vows
- [ ] Spirit clamps at 0 if cost > current spirit

---

## Test 10: Raw Dice Rolls

### Steps:

1. **Roll various dice:**
```
/roll d6
/roll 2d10
/roll d100
```

2. **Check that results display:**
   - Should show individual die values
   - Should show total

### Checklist:
- [ ] d6 rolls correctly
- [ ] 2d10 rolls correctly
- [ ] d100 rolls correctly
- [ ] Results are in valid ranges

---

## Test 11: Session Notes

### Steps:

1. **Add a note:**
```
/note Mysterious signal coming from the northern facility
```

2. **Add another:**
```
/note NPC: Dr. Yuki Tanaka - settlement medic, seems nervous
```

3. **Check log:**
```
/log
```

### Checklist:
- [ ] Notes added successfully
- [ ] Notes appear in session log
- [ ] Notes formatted distinctly from journal entries

---

## Test 12: Session End & Export

### Steps:

1. **End the session:**
```
/end
```

2. **When prompted, give it a title:**
   - "Abandoned Settlement Investigation"

3. **Observe the summary:**
   - Moves rolled count
   - Oracles consulted count
   - Journal entries count
   - Active vows
   - Momentum status

4. **Check exported files:**

```bash
# In a separate terminal or after exiting:
ls -la sessions/
ls -la journal/
ls -la saves/

# Read the session export:
cat sessions/session_01_abandoned_settlement_investigation.md

# Read the journal:
cat journal/kael_vex_journal.md

# Check the save file:
cat saves/kael_vex.json
```

### Checklist:
- [ ] Session title accepted
- [ ] Summary stats correct
- [ ] Three files created (session, journal, save)
- [ ] Markdown is readable and well-formatted
- [ ] Journal entries appear in narrative order
- [ ] Move results clearly marked
- [ ] Oracle results italicized
- [ ] Mechanical notes quoted
- [ ] JSON save is valid and complete
- [ ] Session number increments

---

## Test 13: Resume Session

### Steps:

1. **Run the CLI again:**
```bash
uv run starforged
```

2. **Choose to resume:**
   - Press Enter or type `r`

3. **Verify:**
   - Character loaded correctly
   - Session number is 2
   - Vows persist
   - Stats/tracks correct

4. **Add a journal entry:**
```
Session 2: Returning to investigate the northern facility.
```

5. **Check log:**
```
/log
```
   - Should only show Session 2 entries

6. **End session:**
```
/end
```

7. **Check journal file again:**
```bash
cat journal/kael_vex_journal.md
```
   - Should now have both sessions

### Checklist:
- [ ] Resume loads character correctly
- [ ] Session number increments
- [ ] Previous vows persist
- [ ] Character state correct
- [ ] New session appends to journal

---

## Test 14: Physical Dice Mode

### Steps:

1. **Change dice mode:**
```
/settings dice physical
```

2. **Make a move:**
```
/move face danger
```
   - Choose stat
   - Enter adds
   - CLI should prompt: "Roll your action die (d6):"
   - Enter a value (e.g., `4`)
   - CLI should prompt: "Roll challenge dice (2d10):"
   - Enter two values (e.g., `7 3`)
   - Observe outcome

3. **Test oracle in physical mode:**
```
/oracle action
```
   - Should prompt: "Roll d100:"
   - Enter a value (e.g., `42`)
   - Observe result

### Checklist:
- [ ] Dice mode changes
- [ ] Physical prompts appear
- [ ] Input validation works (1-6 for d6, 1-10 for d10, 1-100 for d100)
- [ ] Invalid input re-prompts gracefully
- [ ] Outcomes resolve correctly with manual input

---

## Test 15: Mixed Dice Mode

### Steps:

1. **Change to mixed mode:**
```
/settings dice mixed
```

2. **Make a move (should auto-roll):**
```
/move strike
```

3. **Make a move with manual flag:**
```
/move strike --manual
```
   - Should prompt for dice input

4. **Make a move with auto flag (should force digital even in mixed):**
```
/move strike --auto
```

### Checklist:
- [ ] Mixed mode defaults to digital
- [ ] `--manual` flag forces physical input
- [ ] `--auto` flag forces digital roll
- [ ] Flags work correctly

---

## Test 16: Edge Cases

### Error Handling Tests:

1. **Invalid move name:**
```
/move asdfasdf
```
   - Should show error with helpful message

2. **Ambiguous move:**
```
/move s
```
   - Might match multiple moves (strike, secure, etc.)
   - Should list options

3. **Invalid vow:**
```
/progress nonexistent
```
   - Should error gracefully

4. **Invalid oracle:**
```
/oracle fake_table
```
   - Should error with available options

5. **Invalid track adjustment:**
```
/health +999
```
   - Should clamp to max (5)

6. **Invalid command:**
```
/fakecommand
```
   - Should suggest similar commands or show help

7. **Quit with unsaved entries:**
   - Write a journal entry
   - Type `/quit`
   - Should warn about unsaved entries
   - Confirm or cancel

8. **Ctrl+C with unsaved entries:**
   - Write journal entry
   - Press Ctrl+C
   - Should warn about unsaved entries

### Checklist:
- [ ] No crashes for invalid input
- [ ] Error messages are helpful
- [ ] Fuzzy matching suggests alternatives
- [ ] Unsaved entry warnings work
- [ ] Quit confirmation works

---

## Final Report Template

After completing all tests, fill out:

### What Worked Well:
- [List features that worked smoothly]

### Issues Found:
- [List bugs, errors, or unexpected behavior]

### UX Friction:
- [List anything that felt awkward or confusing]

### Suggestions:
- [List ideas for improvements]

### Test Results:
- [ ] Character creation: PASS / FAIL
- [ ] Journal entry: PASS / FAIL
- [ ] Move resolution: PASS / FAIL
- [ ] Oracle lookups: PASS / FAIL
- [ ] Track management: PASS / FAIL
- [ ] Vow management: PASS / FAIL
- [ ] Momentum burn: PASS / FAIL
- [ ] Debilities: PASS / FAIL
- [ ] Session export: PASS / FAIL
- [ ] Resume session: PASS / FAIL
- [ ] Dice modes: PASS / FAIL
- [ ] Error handling: PASS / FAIL

### Markdown Quality:
- [ ] Readable and well-formatted
- [ ] Narrative flows naturally
- [ ] Mechanical results clearly marked
- [ ] Would genuinely use this as a journal

---

## Next Steps After Playtest

1. Document all findings in `PLAYTEST_RESULTS.md`
2. Fix critical bugs
3. Address UX friction
4. Update README with example session
5. Iterate on UI/formatting based on feedback
