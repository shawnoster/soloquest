# Remaining Text Lookup Candidates (Issue #47)

This document identifies areas where hardcoded text in Python source files
should be moved to TOML data files, following the pattern established by:
- PR #76: `character_creation.toml` (character creation oracle tables)
- PR #78: `guide.toml` (guide step prose)

---

## 1. `COMMAND_HELP` in `registry.py` → `commands.toml`

**Location:** `soloquest/commands/registry.py:94-125`

Thirty command descriptions are hardcoded in a Python dict. These are
user-facing strings that describe each command's usage and purpose—exactly
the kind of content that should live outside source code.

**Proposed file:** `soloquest/data/commands.toml`

```toml
[campaign]
help = "/campaign [start|create|join|status|leave] — manage campaigns (/campaign start to begin)"

[move]
help = "/move [name] (alias: /m) — resolve a move (e.g. /move strike)"

# ... one entry per command
```

**Why:** Command descriptions are content, not logic. Moving them enables
non-developer contributions, simplifies testing, and keeps `registry.py`
focused on routing logic rather than display strings.

---

## 2. Oracle display data in `oracle.py` → `oracles.toml`

**Location:** `soloquest/commands/oracle.py:19-86`

Two hardcoded structures drive the `/oracle` list display:

### `_ORACLE_CATEGORIES` (lines 19-76)
Groups oracle table keys into display categories (Core, Characters, NPCs,
Places, Space, Planets, Starships, Factions, Events, Yes/No). This is pure
configuration data determining how the oracle list panel is rendered.

### `_ORACLE_INSPIRATIONS` (lines 78-86)
Seven curated example combos shown at the bottom of `/oracle` with no args.
These are editorial choices about useful prompts, not code.

**Proposed addition to:** `soloquest/data/oracles.toml`

```toml
[display]
# Category groupings for the oracle list panel
[[display.categories]]
name = "Core"
keys = ["action", "theme", "descriptor", "focus"]

[[display.categories]]
name = "Characters"
keys = ["given_name", "family_name", "callsign", "role", "goal", "quirks", "disposition", "backstory_prompts", "identity"]

# ...

[[display.inspirations]]
label = "Start a new session"
command = "/oracle begin_a_session"

[[display.inspirations]]
label = "Quick spark of inspiration"
command = "/oracle action theme"

# ...
```

**Why:** Category groupings and inspiration combos are editorial/UX choices
that may evolve independently of oracle table data. They're structured
configuration that doesn't belong in `oracle.py`.

---

## 3. Game loop flowchart in `guide.py` → `guide.toml`

**Location:** `soloquest/commands/guide.py:63-144` (`_show_game_loop`)

The `/guide` overview (with no args) renders a flowchart entirely from
hardcoded `console.print()` calls. The step detail content is already
in `guide.toml`, but the overview is not.

Hardcoded content includes:
- Step labels and one-line descriptions ("ENVISION the current situation", etc.)
- Command hint examples for each step
- Outcome section (STRONG HIT / WEAK HIT / MISS descriptions and prompts)
- Footer help link suggestions (`/guide envision`, `/guide oracle`, etc.)

**Proposed addition to:** `soloquest/data/guide.toml`

```toml
[overview]
title = "Ironsworn: Starforged Game Loop"

[[overview.steps]]
label = "ENVISION"
description = "the current situation"
detail = "Write what your character is doing"
command_hint = "> Type narrative text (no / prefix)"

[[overview.steps]]
label = "ASK THE ORACLE"
description = "when uncertain"
detail = "Get answers about the situation, location, NPCs"
command_hint = "> /oracle [table] (e.g., /oracle action theme)"

[[overview.steps]]
label = "MAKE A MOVE"
description = "when action triggers it"
detail = "Roll dice to resolve risky actions"
command_hint = "> /move [name] (e.g., /move face danger)"

[[overview.outcomes]]
tier = "strong"
label = "STRONG HIT"
symbol = "[OK OK]"
description = "You succeeded and are in control"
prompt = "What do [bold]you[/bold] do next?"

[[overview.outcomes]]
tier = "weak"
label = "WEAK HIT"
symbol = "[OK NO]"
description = "You succeeded with a lesser result or cost"
prompt = "What [bold]happens[/bold] next?"

[[overview.outcomes]]
tier = "miss"
label = "MISS"
symbol = "[NO NO]"
description = "You failed or face a dramatic turn of events"
prompt = "What [bold]happens[/bold] next?"
```

**Why:** The overview and step detail content are the same kind of material.
Having one in TOML and one hardcoded in Python is inconsistent. Unifying
them in `guide.toml` also makes the display logic in `guide.py` simpler.

---

## 4. Contextual suggestions in `guide.py` → `guide.toml`

**Location:** `soloquest/commands/guide.py:147-189` (`_show_contextual_suggestions`)

State-based suggestion messages are hardcoded in Python:

- No active vows warning + command hint
- Low health warning + command hint
- Low momentum warning
- Low supply warning + command hint
- New session welcome message

**Proposed addition to:** `soloquest/data/guide.toml`

```toml
[suggestions]
no_vows = "You have no active vows"
no_vows_hint = "/vow [rank] [description]"
low_health = "Your health is low"
low_health_hint = "/move heal"
low_health_hint_alt = "/move resupply"
low_momentum = "Your momentum is low"
low_momentum_detail = "Consider making moves to gain momentum"
low_supply = "Your supplies are running low"
low_supply_hint = "/move resupply"
new_session = "New session started!"
new_session_detail = "Begin by describing where you are and what you're doing"
```

**Why:** These strings are configuration/content—thresholds that trigger them
are code, but the messages themselves are not. Separating them supports future
customization and keeps `guide.py` focused on logic.

---

## 5. Completion descriptions in `completion.py` → `commands.toml`

**Location:** `soloquest/commands/completion.py:192-214`

Two inline dicts with hardcoded descriptions power tab-completion hints:

- `_complete_guide_args`: 6 guide subcommand descriptions
- `_complete_truths_args`: 2 truths subcommand descriptions

These are display strings shown in the prompt_toolkit completion dropdown
and should live alongside other command strings.

**Proposed addition to:** `soloquest/data/commands.toml`

```toml
[guide.subcommands]
start = "Enter guided mode (step-by-step wizard)"
stop = "Exit guided mode"
envision = "Learn about envisioning and describing your story"
oracle = "Learn about asking the oracle"
move = "Learn about making moves"
outcome = "Learn about interpreting outcomes"

[truths.subcommands]
start = "Start or restart the Choose Your Truths wizard"
show = "Display your current campaign truths"
```

**Why:** These completion descriptions are the same kind of user-facing text
as `COMMAND_HELP`. Collocating them in `commands.toml` makes it easy to find
and update all command-related strings in one place.

---

## Priority Order

| Priority | Area | File | Target |
|---|---|---|---|
| High | `COMMAND_HELP` dict | `registry.py:94` | new `commands.toml` |
| High | Oracle categories & inspirations | `oracle.py:19` | extend `oracles.toml` |
| Medium | Game loop flowchart overview | `guide.py:63` | extend `guide.toml` |
| Medium | Contextual suggestions | `guide.py:147` | extend `guide.toml` |
| Low | Completion descriptions | `completion.py:192` | new `commands.toml` |

The `commands.toml` work (items 1 and 5) can be done together since they
share the same target file. Similarly, items 3 and 4 both extend `guide.toml`
and fit naturally in a single PR.
