# Integration Specifications

Documentation for cross-system integration and hybrid session support.

---

## Overview

As Soloquest grows to support multiple game systems, we need clear patterns for:
- Switching between systems mid-session
- Running multiple systems simultaneously
- Sharing data between systems
- Managing system-specific vs. shared state

---

## Planned Integration Topics

### System Selection

**Status:** 💭 Proposed

How users choose which game system(s) to use:
- System picker at startup
- Default system preference
- Mid-session system switching
- Multi-system sessions

### Hybrid Sessions

**Status:** 💭 Proposed

Using multiple systems together:
- **Example:** Ironsworn for moves + Mythic for oracles
- **Example:** Mythic for scene framing + Starforged for resolution
- Conflict resolution when systems overlap
- Journal export with multi-system content

### State Management

**Status:** 💭 Proposed

Managing character and session state across systems:
- System-agnostic base character model
- System-specific extensions
- Save file format for multi-system characters
- Migration between game systems

### Data Sharing

**Status:** 💭 Proposed

Sharing content between systems:
- Universal oracle tables
- Cross-system asset libraries
- Portable character archetypes
- System translation guides

---

## Integration Principles

When designing cross-system features:

1. **System Independence** - Each system should work standalone
2. **Optional Integration** - Cross-system features are opt-in
3. **Clear Boundaries** - System-specific mechanics stay isolated
4. **User Choice** - Users control which systems are active
5. **Graceful Degradation** - Missing systems don't break core functionality

---

## Examples from Other Tools

### Iron Vault (Obsidian Plugin)

- System switching via frontmatter
- Move mechanics are Ironsworn-specific
- Oracle tables are system-agnostic
- Journal structure supports any system

### Mythic GME + Solo RPGs

- Mythic runs alongside any system
- Fate Chart for yes/no questions
- Random Events interrupt any scene
- Meaning Tables generate universal prompts

---

## Future Considerations

### Plugin Architecture

Community-contributed systems via plugins:
```
~/.wyrd/plugins/
├── blades-in-the-dark/
│   ├── manifest.toml
│   ├── moves.toml
│   └── clocks.py
└── apocalypse-world/
    ├── manifest.toml
    └── moves.toml
```

### API for System Developers

Expose stable API for system integration:
- Register moves
- Register oracles
- Extend character model
- Add commands
- Export format hooks

---

## Related Documentation

- **[Architecture](../architecture.md)** - System-agnostic design
- **[Systems](../systems/)** - Individual system specifications
- **[Features](../features/)** - Feature implementation plans
