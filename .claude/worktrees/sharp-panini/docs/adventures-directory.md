# Adventures Directory Configuration

By default, Starforged CLI stores all your adventure data (saves, sessions, journal) in `~/starforged-adventures/`. This keeps your game data separate from the CLI tool itself.

## Directory Structure

```
~/starforged-adventures/
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

### Option 1: Environment Variable (Recommended)

Set `STARFORGED_ADVENTURES_DIR` to any directory:

```bash
# In your ~/.bashrc or ~/.zshrc
export STARFORGED_ADVENTURES_DIR="$HOME/Documents/ObsidianVault/Starforged"

# Or run one-time
STARFORGED_ADVENTURES_DIR="$HOME/my-campaigns" starforged
```

### Option 2: Default Location

If no configuration is provided, adventures are stored in:
- `~/starforged-adventures/`

## Example: Obsidian Integration

```bash
# Point to your Obsidian vault
export STARFORGED_ADVENTURES_DIR="$HOME/Documents/ObsidianVault/TTRPG/Starforged"

# Run the CLI - sessions will appear in your vault automatically
starforged
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

- **Use absolute paths** in `STARFORGED_ADVENTURES_DIR`
- **Backup regularly** if storing in a cloud-synced folder
- **Git-friendly** — Session markdown files are plain text and version-control friendly
- **Share adventures** — Point multiple users to a shared network directory for collaborative worldbuilding

## Future: Config File Support

A future update will add support for `~/.config/starforged/config.toml`:

```toml
adventures_dir = "~/Documents/ObsidianVault/Starforged"
```
