# Changelog

## Unreleased

### Added
- **Configurable Adventures Directory** — All adventure data (saves, sessions, journal) now defaults to `~/starforged-adventures/` instead of the CLI repo directory
- Environment variable `STARFORGED_ADVENTURES_DIR` to customize where adventures are stored
- Adventures directory location displayed on startup
- Documentation: `docs/adventures-directory.md` with configuration guide and Obsidian integration examples

### Changed
- **Breaking**: Adventure files moved from local `saves/`, `sessions/`, `journal/` to `~/starforged-adventures/` by default
- Session export filenames now include optional title slug: `session_001_first_mission.md`
- Journal files follow naming convention: `{character_slug}_journal.md`

### Benefits
- Integrate with personal wikis (Obsidian, Logseq, etc.)
- Version control adventures separately from CLI
- Upgrade CLI without touching adventure data
- Switch between multiple campaign directories

## Previous Releases

See git history for earlier changes.
