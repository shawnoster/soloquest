# Getting Started with Starforged CLI

Welcome to the Starforged CLI — a complete solo roleplaying experience for Ironsworn: Starforged. This guide will walk you through everything you need to know to start your first session.

## Table of Contents

1. [Installation](#installation)
2. [Your First Session](#your-first-session)
3. [Core Concepts](#core-concepts)
4. [Command Quick Reference](#command-quick-reference)
5. [Tips for New Players](#tips-for-new-players)

---

## Installation

### Prerequisites

- Python 3.13 or higher
- `uv` package manager (recommended) or `pip`

### Install with uv (recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/solo-cli.git
cd solo-cli

# Install with uv
uv pip install -e .
```

### Install with pip

```bash
pip install -e .
```

### Verify Installation

```bash
wyrd --version
```

You should see output showing the current version. If you see an error, check that Python 3.13+ is installed and in your PATH.

---

## Your First Session

Let's create a character and play through a quick scenario to learn the basics.

### Starting the Game

Launch the CLI:

```bash
wyrd
```

or if you're developing:

```bash
make run
```

### Character Creation

If this is your first time, you'll be prompted to create a character:

```
No saves found.
Create a new character:

Character name: Maya Okonkwo
Homeworld (optional): Akani Station

Distribute 5 points across your stats (Edge, Heart, Iron, Shadow, Wits).
Each stat starts at 1. Maximum per stat: 3.

Edge (agility, combat): 2
Heart (courage, bonds): 3
Iron (strength, endurance): 1
Shadow (stealth, deception): 2
Wits (perception, knowledge): 2

Select dice mode:
1. Digital — computer rolls all dice
2. Physical — you roll real dice and enter results
3. Mixed — action die is yours, challenge dice are digital

Choice [1/2/3]: 1

Character created!
```

**What just happened?**
- You named your character and homeworld
- You distributed 5 stat points (each starts at 1, max 3)
- You chose how dice will be rolled

### The Interface Explained

Once your character is created, you'll see:

```
═══════════════════════════════════════════════════════════════════════════════
Session 1
═══════════════════════════════════════════════════════════════════════════════
  Character: Maya Okonkwo  |  Dice: digital
  Type to journal. /help for commands.

>
```

**Two ways to interact:**
1. **Journal mode** — Type plain text to record your story
2. **Command mode** — Type `/command` to trigger game mechanics

### Your First Journal Entry

Let's start with some narration:

```
> I arrive at the derelict mining station. The airlock seals behind me with a hiss.
```

The CLI just records this as part of your story. No dice, no mechanics — pure narrative.

### Making Your First Move

Now let's trigger a move. You want to explore the station, which could be dangerous. Time for **Face Danger** with Wits:

```
> /move face danger wits
```

**Output:**
```
───────────────────────────────────────────────────────────────────────────────
Move: Face Danger
───────────────────────────────────────────────────────────────────────────────

Face Danger (Wits +2)
  Action: 5 + 2 = 7  vs  Challenge: 3, 8

Result: WEAK HIT
  You succeed, but with a cost or complication.

[Mechanical: Face Danger (wits) → weak hit (7 vs 3, 8)]
```

**What happened?**
- You rolled an action die (5) + your Wits stat (2) = 7
- You rolled two challenge dice: 3 and 8
- You beat one challenge die (3) but not the other (8) = **weak hit**
- A weak hit means success, but with a cost or complication

### Interpreting Results

Starforged doesn't script outcomes — **you interpret what happens** based on the result and your fiction:

**Strong Hit** (beat both challenge dice)
- Full success, you're in control

**Weak Hit** (beat one challenge die)
- Success with a cost, complication, or lesser benefit

**Miss** (beat no challenge dice)
- Failure or new danger emerges

For this weak hit, you might journal:

```
> I navigate the station successfully but spot signs of recent activity. Someone else is here.
```

### Consulting the Oracle

Need inspiration? Ask the oracle for random prompts:

```
> /oracle action
```

**Output:**
```
Action: Clash

[Oracle: action → Clash]
```

The oracle gave you "Clash" — maybe your character hears fighting ahead. Let's combine two oracle prompts:

```
> /oracle descriptor
```

**Output:**
```
Descriptor: Mechanical

[Oracle: descriptor → Mechanical]
```

"Mechanical Clash" — perhaps maintenance robots are battling each other. Use oracle results as creative prompts, not strict instructions.

### Checking Your Character

View your character sheet:

```
> /char
```

**Output:**
```
═══════════════════════════════════════════════════════════════════════════════
Maya Okonkwo
═══════════════════════════════════════════════════════════════════════════════

Stats                          Tracks
  Edge:     2                    Health:     ████████░░  5/5
  Heart:    3                    Spirit:     ████████░░  5/5
  Iron:     1                    Supply:     ██████░░░░  3/5
  Shadow:   2                    Momentum:   ██░░░░░░░░  2 (max 10, reset 2)
  Wits:     2

Vows: none
Debilities: none
```

### Taking Damage

Let's say you get hurt. Adjust your health track:

```
> /health -2
```

**Output:**
```
Health: 5 → 3  (changed by -2)
```

You can also adjust spirit, supply, and momentum:

```
> /momentum +1
> /spirit -1
> /supply +2
```

### Swearing a Vow

Vows are your character's core quests. Let's swear a dangerous vow:

```
> /vow dangerous Rescue the miners trapped in the lower levels
```

**Output:**
```
Vow sworn: Rescue the miners trapped in the lower levels
  Rank: dangerous
  Progress: ▢▢▢▢▢▢▢▢▢▢  0/10 boxes

[Mechanical: Vow sworn (dangerous): Rescue the miners trapped in the lower levels]
```

### Marking Progress

When you overcome a significant obstacle toward your vow, mark progress:

```
> /progress 1
```

**Output:**
```
Select vow to advance:
  1. Rescue the miners trapped in the lower levels [dangerous] ▢▢▢▢▢▢▢▢▢▢

Choice: 1

Rescue the miners trapped in the lower levels [dangerous]
  Progress: ▢▢▢▢▢▢▢▢▢▢ → ████▢▢▢▢▢▢  2/10 boxes

[Mechanical: Progress on vow: Rescue the miners trapped in the lower levels (2 boxes)]
```

**Progress by rank:**
- Troublesome: 3 boxes per mark
- Dangerous: 2 boxes per mark (like our vow)
- Formidable: 1 box per mark
- Extreme: 2 ticks per mark
- Epic: 1 tick per mark

### Fulfilling a Vow

When your progress track is mostly filled (typically 8-10 boxes), you can attempt to fulfill the vow:

```
> /fulfill
```

You'll be prompted to select which vow to fulfill. The CLI rolls your progress score against challenge dice to determine if you succeed.

### Adding Notes

Need to remember something? Add a note:

```
> /note Check security logs for clues about the recent activity
```

Notes are saved with your session export but don't appear in the main journal.

### Rolling Custom Dice

Need to roll dice outside of a move? Use `/roll`:

```
> /roll 1d6
> /roll 2d10
> /roll challenge
```

### Ending Your Session

When you're done playing:

```
> /end
```

**Output:**
```
Session ended.
Entries: 12 journal, 5 mechanical

Export saved to:
  adventures/maya_okonkwo_session_001.md

Game autosaved.
```

Your session is now saved in two places:
1. **Character save** (autosaved throughout) — tracks stats, vows, health, etc.
2. **Session export** (created on /end) — a markdown file with your full story

---

## Core Concepts

### The Journal-Command Hybrid

The CLI operates in two modes simultaneously:

1. **Journal mode** (default)
   - Type plain text to record your narrative
   - No slash prefix needed
   - Example: `I draw my blade and charge`

2. **Command mode** (prefix with `/`)
   - Type `/command` to trigger game mechanics
   - Example: `/move strike iron`
   - Example: `/oracle action`

**When to use each:**
- Use journal mode to narrate what happens
- Use command mode when the rules require a roll or mechanical change

### Moves

Moves are the core mechanic of Ironsworn: Starforged. They trigger when your character takes risky action:

**Common moves:**
- **Face Danger** — overcome an obstacle or resist harm
- **Secure an Advantage** — prepare or improve your position
- **Gather Information** — investigate or research
- **Strike** — attack in combat
- **Compel** — persuade or deceive someone

**How to trigger a move:**
```
/move [move-name] [stat]
```

**Examples:**
```
/move face danger wits
/move strike iron
/move secure edge
/move gather heart
```

The CLI will:
1. Roll action die + your stat
2. Roll two challenge dice
3. Compare results and show outcome (strong hit, weak hit, or miss)
4. Display the move's text to guide your interpretation

### Dice Modes

Choose how dice are rolled when you create your character:

1. **Digital** (default)
   - Computer rolls everything
   - Fastest option
   - Best for pure digital play

2. **Physical**
   - You roll real dice (d6, d10s)
   - Enter results when prompted
   - Tactile experience, digital record-keeping

3. **Mixed**
   - You roll action die (d6)
   - Computer rolls challenge dice (2d10)
   - Good balance of speed and tactile feel

**Changing dice mode:**
```
/settings dice digital
/settings dice physical
/settings dice mixed
```

### Vows and Progress

Vows are your character's sworn quests. They use progress tracks:

**Vow ranks:**
- **Troublesome** — minor task, quick to complete
- **Dangerous** — significant challenge
- **Formidable** — major undertaking
- **Extreme** — epic quest
- **Epic** — legendary endeavor

**Workflow:**
1. Swear a vow: `/vow dangerous Investigate the alien ruins`
2. Mark progress as you overcome obstacles: `/progress 1`
3. When ready, fulfill the vow: `/fulfill`

**Progress rates:**
| Rank         | Marks per progress |
|--------------|--------------------|
| Troublesome  | 3 boxes            |
| Dangerous    | 2 boxes            |
| Formidable   | 1 box              |
| Extreme      | 2 ticks            |
| Epic         | 1 tick             |

### Oracles

Oracles provide random inspiration when you need answers:

**Common oracles:**
```
/oracle action          → Attack, Assist, Clash, Create, ...
/oracle descriptor      → Ancient, Broken, Cold, Mysterious, ...
/oracle location        → Planetside, Orbital, Deep Space, ...
/oracle character-role  → Hunter, Healer, Smuggler, Warrior, ...
```

**Use oracles when:**
- You're not sure what happens next
- You need NPC personality traits
- You want to add surprise to your narrative
- The rules tell you to "Ask the Oracle"

### Tracks

Your character has three condition tracks:

- **Health** (0-5) — physical harm
- **Spirit** (0-5) — mental/emotional harm
- **Supply** (0-5) — equipment and provisions

And one special track:

- **Momentum** (-6 to +10) — your character's current flow state

**Adjusting tracks:**
```
/health -2      # Take 2 harm
/spirit +1      # Recover 1 spirit
/supply -1      # Use up provisions
/momentum +2    # Gain momentum from a move
```

**Burning momentum:**

Momentum can be "burned" to turn a miss into a weak hit or a weak hit into a strong hit:

```
/momentum burn
```

When you burn momentum:
1. Your momentum value replaces your action die result
2. Momentum resets to your reset value (usually 2, or 0 if debilitated)

### Debilities

Debilities are lasting conditions that reduce your momentum:

**Available debilities:**
- Wounded, Shaken, Unprepared, Encumbered (conditions)
- Maimed, Corrupted (permanent/lasting impacts)

**Effects:**
- Each debility reduces momentum max by 1
- Two or more debilities reduce momentum reset to 0

**Toggling debilities:**
```
/debility wounded      # Toggle wounded on/off
/debility              # Show current debilities
```

### Session Export

When you end a session with `/end`, the CLI creates a markdown file in your adventures directory (default: `~/wyrd-adventures/`).

**Export includes:**
- Session number and date
- Character snapshot
- Full journal with mechanical notations
- Vow status

**Configuring adventures directory:**

```bash
# Option 1: Command-line argument (recommended)
wyrd -d ~/Documents/ObsidianVault/Starforged

# Option 2: Environment variable
export SOLOQUEST_ADVENTURES_DIR="$HOME/Documents/ObsidianVault/Starforged"
wyrd
```

See [Adventures Directory Configuration](adventures-directory.md) for more details.

---

## Command Quick Reference

### Campaign Setup
```
/truths                    Choose Your Truths — establish fundamental facts about your campaign setting
/truths start              (Re)start the truths selection wizard
/truths show               Display your current campaign truths
```

**About Choose Your Truths:**
The truths wizard guides you through 14 categories that define the nature of your version of the Forge (the game's setting). For each truth, you can:
- Choose from 3 preset options
- Roll randomly (d100)
- Write your own custom truth
- Skip and decide later

This typically takes 45-60 minutes and is best done at the start of your campaign.

### Character Management
```
/char                      Show character sheet
/health [delta]            Adjust health (e.g., /health -2)
/spirit [delta]            Adjust spirit
/supply [delta]            Adjust supply
/momentum [delta]          Adjust momentum
/momentum burn             Burn momentum (replace action die)
/debility [name]           Toggle debility (wounded, shaken, etc.)
/settings dice [mode]      Change dice mode (digital/physical/mixed)
```

### Moves
```
/move [name] [stat]        Make a move (e.g., /move strike iron)
/move [name] [stat] -m     Manual mode (enter your own dice)
/forsake                   Forsake your current vow (costs spirit)
```

### Vows and Progress
```
/vow [rank] [description]  Swear a new vow (ranks: troublesome, dangerous, formidable, extreme, epic)
/progress [n]              Mark progress on a vow (default: 1)
/fulfill                   Attempt to fulfill a vow
```

### Oracles
```
/oracle [table]            Roll on an oracle table
                          Common tables: action, descriptor, location,
                          character-role, settlement-name, faction-type
```

### Session Management
```
/log -f [flag]            Review journal entries (use flags to filter)
/note [text]              Add a private note (not in main journal)
/roll [dice]              Roll custom dice (1d6, 2d10, challenge)
/end                      End session and export to markdown
/help                     Show command help
/quit or /q               Quit without saving
```

**Log flags:**
- `-j` — journal entries only
- `-m` — mechanical entries only
- `-d` — dice rolls only
- `-v` — vows only

---

## Tips for New Players

### Start Simple

Don't worry about mastering every rule. Focus on:
1. Narrating what happens
2. Making moves when things are risky
3. Interpreting dice results creatively

The rest will come with practice.

### Use the Oracle Liberally

Stuck? Unsure what happens next? Roll on an oracle:

```
/oracle action descriptor
```

Chain oracles together for richer prompts:
- Action + Descriptor = "Defend Ancient"
- Location + Descriptor = "Orbital Broken"

### Trust Your Interpretation

Dice results don't dictate the story — you do. A "miss" could mean:
- Complete failure
- Success with a serious complication
- A reveal that changes everything
- An unexpected danger

The game trusts you to find the most interesting outcome.

### Let Mechanics Inspire Fiction

When you roll a weak hit, use it as a prompt:
- What's the cost?
- What complication arises?
- What hard choice do you face?

Mechanics are there to create interesting story beats, not constrain you.

### Save Early, Save Often

The CLI autosaves after most commands, but you can also manually save by using `/end` and then resuming later.

### Use Physical Dice for Dramatic Moments

Even in digital mode, consider rolling real dice for:
- Fulfilling an epic vow
- A life-or-death move
- Any moment that feels important

You can always enter manual results with the `-m` flag:

```
/move strike iron -m
```

### Read the Starforged Rulebook

This CLI implements the Ironsworn: Starforged rules, but it's not a substitute for reading them. The rulebook explains:
- How to interpret move outcomes
- When to make moves vs. when to just narrate
- How to build engaging adventures

Get the rulebook at: https://www.ironswornrpg.com/product-ironsworn-wyrd

### Journal Richly

Don't just log mechanics — write your story:

**Mechanical logging:**
```
> /move strike iron
> /health -2
```

**Rich journaling:**
```
> The pirate captain swings her plasma blade at my head. I duck and counter with a strike to her midsection.
> /move strike iron
> She parries and cuts deep into my shoulder. Blood spatters across the deck.
> /health -2
```

The export at the end of your session will read like a story, not a combat log.

### Experiment with Command History

The CLI supports command history using arrow keys:
- **Up arrow** — previous command
- **Down arrow** — next command

This makes repeating similar commands faster:
```
> /oracle action
[Up arrow]
> /oracle action    [modify to:]
> /oracle descriptor
```

### Join the Community

Have questions? Want to share your adventures? Join the Ironsworn community:
- Official Discord: https://discord.gg/ironsworn
- Subreddit: /r/Ironsworn
- Official site: https://www.ironswornrpg.com

---

## Next Steps

1. **Run through this guide** with a test character
2. **Read the Starforged rulebook** to understand moves in depth
3. **Play a full session** and export your story
4. **Customize your config** to set your adventures directory

**Ready to begin?**

```bash
wyrd
```

---

*This guide covers the core features of the Starforged CLI. For advanced features like asset management and custom oracle tables, see the main README or check the CLI's /help command.*
