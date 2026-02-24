# Web-Enabling Brainstorming Issue

This document contains the content for a GitHub issue to track brainstorming about web-enabling Soloquest for cross-device session continuity.

## How to Create the Issue

**Option 1: Use the Issue Template**
1. Go to https://github.com/shawnoster/wyrd/issues/new/choose
2. Select "💭 Web-Enabling Brainstorm" template
3. Review and adjust the pre-filled content
4. Click "Submit new issue"

**Option 2: Create Manually**
1. Go to https://github.com/shawnoster/wyrd/issues/new
2. Copy the content from `.github/ISSUE_TEMPLATE/web-enabling-brainstorm.md`
3. Paste into the issue description
4. Set title: `Brainstorm: Web-enabling for desktop/CLI/mobile session continuity`
5. Add labels: `enhancement`, `discussion`, `architecture`
6. Click "Submit new issue"

## Issue Summary

The issue covers:

### Problem
Users want to continue sessions across desktop CLI, web browser, and mobile devices. Current local-only storage (`~/wyrd-adventures/`) prevents this.

### Current State
- **Storage:** JSON saves + Markdown journals in local directory
- **Existing Sync Infrastructure:** Hexagonal architecture with `SyncPort` interface already designed for co-op play ([#79](https://github.com/shawnoster/wyrd/issues/79))
- **Models:** All models have `to_dict()`/`from_dict()` for serialization

### Architecture Options Explored

1. **Cloud Sync Adapter** - Extend existing `SyncPort` with cloud storage
2. **API + Multi-Client** - Backend server with CLI/web/mobile clients
3. **Hybrid Local-First** - CLI primary with optional sync
4. **Git Sync** - Use Git as sync mechanism with static site

### Key Questions

- **Authentication:** Single player across devices or multi-user?
- **Conflict Resolution:** How to handle simultaneous edits?
- **Offline Support:** Must CLI/web/mobile work offline?
- **Privacy:** Data ownership, encryption, third-party services?
- **Infrastructure:** Self-hosted vs managed service?
- **UX:** Feature parity across platforms or tiered access?

### Success Criteria

1. Seamless continuity across devices
2. Offline-first operation
3. Zero deployment for basic sync
4. Privacy preserved (user data control)
5. Backward compatible with existing workflows

### Related Work

Similar to Obsidian Sync, Logseq, Standard Notes, Joplin - all local-first with optional sync.

## Why This Issue Matters

Cross-device continuity is a common user request and would significantly improve the user experience. The project already has:
- Clean architecture with `SyncPort` abstraction
- Serializable data models
- Co-op play infrastructure that could be extended

This brainstorming issue will help gather community input before committing to a specific technical approach.

## Next Steps After Issue Creation

1. Share in Ironsworn Discord and relevant communities
2. Gather feedback on architecture preferences
3. Identify must-have features per platform
4. Prioritize implementation phases
5. Create follow-up implementation issues

---

**Note:** This document was created because the automation cannot directly create GitHub issues. The issue template has been added to `.github/ISSUE_TEMPLATE/` for easy reuse.
