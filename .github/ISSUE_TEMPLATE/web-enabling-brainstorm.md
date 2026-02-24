---
name: 💭 Web-Enabling Brainstorm
about: Track brainstorming and design for cross-device session continuity
title: 'Brainstorm: Web-enabling for desktop/CLI/mobile session continuity'
labels: ['enhancement', 'discussion', 'architecture']
assignees: ''
---

## Problem Statement

Users want to continue their Soloquest sessions seamlessly across different devices and contexts:
- **Desktop CLI** - Full-featured experience for deep play sessions
- **Web browser** - Quick access from any device without installation
- **Mobile** - On-the-go journaling, oracle lookups, character reference

Currently, all session data is stored locally in `~/wyrd-adventures/`, making cross-device continuity impossible without manual file syncing.

## Current Architecture

### Storage Layer
- **Location:** `~/wyrd-adventures/` (configurable via `-d` flag or `SOLOQUEST_ADVENTURES_DIR`)
- **Format:** JSON for character saves, Markdown for journals
- **Structure:**
  ```
  ~/wyrd-adventures/
  ├── saves/          # Character saves (kael.json, maya_okonkwo.json)
  ├── sessions/       # Per-session markdown exports
  └── journal/        # Cumulative character journals
  ```

### Existing Sync Infrastructure (Co-op Play)
The project already has a **hexagonal sync architecture** designed for co-op play ([#79](https://github.com/shawnoster/wyrd/issues/79)):

- **`SyncPort` interface** - Abstract sync protocol
- **`LocalAdapter`** - No-op single-player (zero overhead)
- **`FileLogAdapter`** - JSONL event logs on shared filesystem
- **Event log model** - Append-only immutable events with player attribution

This architecture could potentially be extended with new adapters for cloud sync.

### Data Models
See `wyrd/models/`:
- `Character` - Stats, tracks, assets
- `Session` - Log entries (journal, move results, oracle rolls)
- `Vow` - Progress tracking
- All models have `to_dict()` / `from_dict()` for serialization

## Brainstorming Questions

### 1. Architecture Options

**Option A: Cloud Sync Adapter**
- Extend existing `SyncPort` interface with a new adapter (e.g., `CloudAdapter`)
- Sync JSON saves and markdown exports to cloud storage
- Pros: Leverages existing architecture, clean separation
- Cons: Still requires CLI installation on each device

**Option B: API + Multi-Client**
- Backend API server (FastAPI/Flask) for game state management
- Multiple clients: CLI (current), web app, mobile app
- Pros: True cross-platform, no local storage needed
- Cons: Requires server hosting, major architectural change

**Option C: Hybrid (Local-First with Sync)**
- Keep CLI as primary, add optional cloud sync
- Web/mobile clients as lightweight "views" that poll for updates
- Pros: Preserves local-first philosophy, incremental adoption
- Cons: Complex sync logic, potential conflicts

**Option D: Static Site Generator + Git Sync**
- Export sessions to static site (Hugo/Jekyll)
- Use Git as sync mechanism (GitHub/GitLab)
- Pros: Simple, no server needed, integrates with existing workflows
- Cons: Read-only on web/mobile, requires Git knowledge

### 2. Technical Considerations

**Authentication & Multi-User**
- Single player across devices (sync same character)?
- Multiple players sharing campaigns (co-op)?
- How to handle player identity?

**Conflict Resolution**
- What happens if user edits on two devices simultaneously?
- Last-write-wins? Operational transforms? CRDTs?
- Can we avoid conflicts with event sourcing?

**Offline Support**
- Must CLI work offline (current: yes)?
- Should web/mobile work offline?
- How to sync when back online?

**Data Migration**
- How to migrate existing saves to new system?
- Can users opt-in to sync without breaking existing workflows?
- Backward compatibility with file-based storage?

### 3. User Experience Questions

**Device Priorities**
- Is desktop CLI the primary interface, with web/mobile as secondary?
- Or should all interfaces be equal?
- What features are essential on each platform?

**Session Continuity Scenarios**
1. Start session on desktop, continue on mobile during commute?
2. Quick oracle lookup on phone, resume full session on desktop?
3. Review past sessions on tablet while planning next session?

**Feature Parity**
- Full feature set on all platforms?
- Or minimal read-only access on mobile (character sheet, oracle lookups)?
- What's the minimum viable mobile experience?

### 4. Infrastructure & Hosting

**Self-Hosted vs Managed**
- Should users host their own sync server?
- Or provide a managed service (with privacy concerns)?
- Hybrid approach (default: local, optional: sync)?

**Storage Backend Options**
- Cloud storage (S3, Google Drive, Dropbox)
- Database (PostgreSQL, SQLite + Litestream)
- Git repository (GitHub, GitLab, Gitea)
- Conflict-free replicated data types (CRDTs)

**Costs & Sustainability**
- If managed service, how to cover hosting costs?
- Free tier with limits?
- One-time purchase vs subscription?

### 5. Privacy & Security

**Data Ownership**
- Users own their data (no lock-in)?
- Ability to export/delete all data?
- Local-first by default?

**Encryption**
- End-to-end encryption for cloud sync?
- How to handle encryption keys?
- What about searching/indexing encrypted data?

**Third-Party Dependencies**
- Which cloud services are acceptable?
- Should we support multiple backends (S3, GCS, Azure, etc.)?
- Can users choose their own backend?

## Related Work

### Similar Projects
- **Obsidian Sync** - End-to-end encrypted vault sync across devices
- **Logseq** - Local-first, supports Git sync
- **Standard Notes** - Encrypted note-taking with offline support
- **Joplin** - Note-taking with multiple sync backends (Dropbox, OneDrive, S3)

### Existing Integrations
- Soloquest already supports custom adventures directory for Obsidian/Logseq integration
- Users can manually sync via Dropbox/iCloud/Syncthing

## Success Criteria

What does "success" look like for web-enabling?

1. **Seamless Continuity** - Start session on desktop, continue on mobile without friction
2. **Offline First** - CLI works without internet, syncs when available
3. **Zero Deployment** - No server setup required for basic sync
4. **Privacy Preserved** - Data stays under user control
5. **Backward Compatible** - Existing file-based workflow still works

## Next Steps

This is a brainstorming issue to explore options. Expected outcomes:

1. Gather community feedback on preferred architecture
2. Identify must-have features for each platform
3. Prioritize implementation phases
4. Create follow-up issues for specific components

**Related Issues:**
- [#79](https://github.com/shawnoster/wyrd/issues/79) - Co-op play (shared campaigns)
- Sync infrastructure already exists in `wyrd/sync/`

**Discussion Welcome!**
Please share your thoughts on:
- Which architecture option makes most sense?
- What's your ideal cross-device workflow?
- What features are essential for mobile/web?
- Would you self-host or prefer a managed service?
