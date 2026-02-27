# Specifications

Technical specifications and design documents for wyrd.

**📋 [Process Guide](PROCESS.md)** - Step-by-step guide for adding systems and features

---

## Core Documentation

- **[CLI Specification](spec.md)** - Living specification for the entire CLI
- **[Architecture](architecture.md)** - System-agnostic design and integration points

---

## By Category

### Systems

System-level specifications for supported game systems:

- **[Ironsworn: Starforged](systems/ironsworn-starforged.md)** - Sci-fi solo RPG support
- **Mythic GME** _(planned)_ - Universal game master emulator

See [systems/](systems/) for complete system documentation.

### Features

Feature-specific implementation plans organized by system:

**Starforged Features:**
- **[Choose Your Truths](features/starforged/choose-your-truths.md)** - Campaign setup wizard

**Shared Features:**
- Session journaling _(core architecture)_
- Markdown export _(core architecture)_
- Dice modes _(core architecture)_

See [features/](features/) for all feature specifications.

### Integration

Cross-system integration and hybrid session support:

- System selection _(planned)_
- Hybrid sessions _(planned)_
- Plugin architecture _(future)_

See [integration/](integration/) for integration documentation.

---

## How to Use This Documentation

### Adding a New System

1. Create system spec in `systems/[system-name].md`
2. Document core mechanics and data sources
3. Create feature specs in `features/[system-name]/`
4. Update this README to reference the new system

### Adding a New Feature

**System-specific feature:**
1. Create spec in `features/[system-name]/[feature-name].md`
2. Reference parent system spec
3. Document data models, commands, and UI

**Shared feature:**
1. Create spec in `features/shared/[feature-name].md`
2. Document system integration points
3. Show examples from multiple systems

### Planning Cross-System Work

1. Create integration spec in `integration/[topic].md`
2. Reference affected system specs
3. Document compatibility and trade-offs

---

## Documentation Standards

Each specification should include:

- **Overview** - What problem does this solve?
- **Goals** - What are we trying to achieve?
- **Technical Design** - How does it work?
- **Data Models** - What structures are involved?
- **User Experience** - How do users interact with it?
- **Testing** - How do we validate it works?
- **Related Docs** - Links to relevant specs

Use Markdown, keep it concise, and update docs when implementation diverges from the plan.
