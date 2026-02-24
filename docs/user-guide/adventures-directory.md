# Adventures Directory Configuration

By default, Starforged CLI stores all your adventure data (saves, sessions, journal) in `~/wyrd-adventures/`. This keeps your game data separate from the CLI tool itself.

## Directory Structure

```
~/wyrd-adventures/
├── saves/      # Character save files (.json)
├── sessions/   # Individual session markdown files
└── journal/    # Cumulative journal markdown files
```

## Why Separate from the CLI?

1. **Second Brain Integration** — Point to your Obsidian/Logseq vault to integrate game sessions with your personal wiki
2. **Version Control** — Track your adventures in git separately from the CLI tool
3. **Portability** — Upgrade the CLI without touching your adventure data
4. **Multiple Campaigns** — Switch between different adventure directories easily

## Configuration

The adventures directory can be configured in two ways (in priority order):

### Option 1: Command-Line Argument (Recommended)

Pass the directory path directly when launching:

```bash
# Use short flag
wyrd -d ~/Documents/ObsidianVault/Starforged

# Or long flag
wyrd --adventures-dir ~/my-campaigns

# Relative paths work too
wyrd -d ./test-campaign
```

**Benefits:**
- ✅ Most explicit and clear
- ✅ Easy to switch between campaigns
- ✅ Works great with shell aliases

### Option 2: Default Location

If no configuration is provided, adventures are stored in:
- `~/wyrd-adventures/`

## Example: Obsidian Integration

```bash
wyrd -d ~/Documents/ObsidianVault/TTRPG/Starforged
```

Your Obsidian vault will now contain:
```
TTRPG/Starforged/
├── saves/
├── sessions/
│   ├── session_001.md
│   └── session_002_first_mission.md
└── journal/
    └── kael_vex_journal.md
```

## Tips

- **Multiple campaigns?** Create shell aliases:
  ```bash
  alias starforged-main='wyrd -d ~/campaigns/starforged-main'
  alias starforged-test='wyrd -d ~/campaigns/test-game'
  ```
- **Use absolute paths** for consistency
- **Backup regularly** if storing in a cloud-synced folder
- **Git-friendly** — Session markdown files are plain text and version-control friendly
- **Share adventures** — Point multiple users to a shared network directory for collaborative worldbuilding

## Future: Config File Support

A future update will add support for `~/.config/wyrd/config.toml`:

```toml
adventures_dir = "~/Documents/ObsidianVault/Starforged"
```
