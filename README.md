# Ironsworn: Starforged CLI

A solo journaling companion CLI for [Ironsworn: Starforged](https://www.ironswornrpg.com/) by Shawn Tomkin.

Handles move resolution, oracle lookups, character tracking, and session journaling — with export to Markdown.

> **Note:** This is a personal, non-commercial companion tool. Ironsworn: Starforged is created by Shawn Tomkin and released under Creative Commons Attribution 4.0.

---

## Quickstart

```bash
# Install dependencies
uv sync

# Run
uv run soloquest
# or
uv run python -m soloquest.main
```

**New to Starforged CLI?** See the [Getting Started Guide](docs/getting-started.md) for a complete walkthrough.

---

## Example Session

Here's what a typical session looks like:

```
═══════════════════════════════════════════════════════════════════════════════
Session 1
═══════════════════════════════════════════════════════════════════════════════
  Character: Maya Okonkwo  |  Dice: digital
  Type to journal. /help for commands.

> I step through the airlock into the derelict mining station. Emergency lights flicker overhead.

> /move face danger wits

───────────────────────────────────────────────────────────────────────────────
Move: Face Danger
───────────────────────────────────────────────────────────────────────────────

Face Danger (Wits +2)
  Action: 5 + 2 = 7  vs  Challenge: 3, 8

Result: WEAK HIT
  You succeed, but with a cost or complication.

> I navigate safely but spot recent footprints in the dust. Someone else is here.

> /vow dangerous Find whoever is stalking this station

Vow sworn: Find whoever is stalking this station
  Rank: dangerous
  Progress: ▢▢▢▢▢▢▢▢▢▢  0/10 boxes

> /oracle action descriptor

Action: Clash
Descriptor: Mechanical

> I hear the screech of metal on metal echoing through the corridors.

> /end

Session ended.
Entries: 6 journal, 3 mechanical

Export saved to:
  adventures/maya_okonkwo_session_001.md

Game autosaved.
```

---

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

---

## Commands

| Command | Description |
|---|---|
| `/move [name]` | Resolve a move (e.g. `/move strike`) |
| `/oracle [table]` | Consult an oracle (e.g. `/oracle action theme`) |
| `/vow [rank] [text]` | Create a vow |
| `/progress [vow]` | Mark progress on a vow |
| `/fulfill [vow]` | Attempt to fulfill a vow |
| `/char` | Show character sheet |
| `/log` | Show session log |
| `/note [text]` | Add a scene note |
| `/health +N` | Adjust health |
| `/spirit +N` | Adjust spirit |
| `/supply +N` | Adjust supply |
| `/momentum +N` | Adjust momentum |
| `/settings dice [digital/physical/mixed]` | Change dice mode |
| `/end` | End session and export journal |
| `/quit` | Quit without saving |
| `help` | Show all commands |

Anything typed without a `/` prefix is added to your journal.

---

## Dice Modes

- **digital** — CLI rolls all dice automatically
- **physical** — CLI prompts you to enter each die result
- **mixed** — digital by default; add `--manual` to any command to prompt for that roll

## Adventures Directory

By default, all your adventure data is stored in `~/soloquest-adventures/`:
- `saves/` — character save files
- `sessions/` — individual session markdown
- `journal/` — cumulative journal markdown

**Configure your own location** to integrate with Obsidian, Logseq, or any personal wiki:

```bash
export SOLOQUEST_ADVENTURES_DIR="$HOME/Documents/ObsidianVault/Starforged"
```

See [Adventures Directory Configuration](docs/adventures-directory.md) for details.

---

## Project Structure

```
soloquest/
├── main.py          # Entry point
├── loop.py          # REPL game loop
├── commands/        # Command handlers
├── engine/          # Dice, moves, oracles, momentum
├── models/          # Character, Vow, Session
├── journal/         # Markdown exporter
├── data/            # moves.toml, oracles.toml
├── state/           # JSON save/load
└── ui/              # Rich display helpers
```
