# ADR-002: UI Panel Guidelines

- **Status:** Accepted
- **Date:** 2026-02-17

## Context

The CLI uses Rich `Panel` (bordered box) for some output and plain text for others. Without explicit rules, new features make ad-hoc choices — leading to visual inconsistency where some game feedback is boxed and some isn't, without a clear reason.

## Decision

### The core distinction

**Panels are for game results. Plain text is for everything else.**

A *game result* is a discrete, self-contained response to a player action: a move outcome after rolling dice, an oracle reveal, an asset card. These feel like the game "speaking back" to the player and deserve visual weight and a title.

Everything else — errors, prompts, instructions, status, lists — is UI scaffolding that supports the interaction. It should be lightweight so it doesn't compete with the results.

### Use a Panel when

- The output is the **result of a completed game action** (dice rolled, oracle consulted, asset looked up)
- The content has a **clear, natural title** (move name, oracle table name, asset name)
- The content is **multi-line and self-contained** — the player may want to re-read it
- The output marks a **narrative beat** that should stand out in the scroll-back

Examples: move result, oracle result, asset detail, narrative move description.

### Do not use a Panel when

- The output is **feedback or error handling**: errors (`✗`), warnings (`⚠`), success confirmations (`✓`), info hints
- The output is **interactive scaffolding**: stat prompts, vow selection lists, "which stat?" choices
- The output is **incremental status**: mechanical updates (`↳`), autosave indicator
- The output is **a list or browse view**: category listings, move tables, oracle table indexes
- The output is **a persistent summary**: the character sheet uses horizontal Rules (`───`) instead of a Panel because it's a reference view, not a single action result

### Border color conventions

Border color communicates the *type* of result at a glance:

| Color | Meaning | Used for |
|---|---|---|
| `blue` | Action resolution | Move results (dice rolls) |
| `bright_cyan` | Fate / information | Oracle results |
| `bright_magenta` | Character content | Asset details |
| `cyan` | Reference / narrative | Narrative moves, wizard steps, intro text |

New features should follow these existing color assignments. Introduce a new color only if the content genuinely doesn't fit any existing category.

### In-text cross-references use `[cyan]`

Dataforged game text contains cross-references to other moves — e.g., `[Pay the Price](Starforged/Moves/...)` in asset abilities and narrative move descriptions. These are rendered as `[cyan]Move Name[/cyan]` — not as terminal hyperlinks.

**Rationale:**

- `cyan` is the established reference color, so colored move names signal "this is a game term you can look up"
- Terminal hyperlinks (from `rich.markdown.Markdown`) would link to internal dataforged paths, not real URLs — misleading and non-functional
- Consistent across all game text contexts (asset panels use `bright_magenta` borders, move panels use `cyan` or `blue`, but cross-references are always `cyan` regardless of context)

The shared utility `display.render_game_text(text)` handles this conversion along with `**bold**` and bullet list normalization. All game text from dataforged should pass through this function before being placed in a panel.

### The character sheet exception

`/character` is a special case: it's a full-screen reference view, not the result of a single action. It uses `Rule` separators to organize sections without boxing everything. This keeps it scannable and avoids the visual noise of nested panels.

### Navigation menus use hand-drawn ASCII boxes

The startup menu (choose action, load character) is a third category: neither a game result nor plain flowing text. It uses a hand-drawn ASCII box:

```
+-- Choose an action ----------------------------+
|                                                |
|  [r] Resume session (continue)                 |
|  [n] New character                             |
+------------------------------------------------+
```

This is intentional and distinct from Rich `Panel`:

- ASCII `+` corners (`+`, `|`, `-`) are visually lighter — appropriate for navigation scaffolding that appears before the game starts
- Rich `Panel` rounded corners (`╭╮╰╯`) are visually heavier — reserved for in-game results
- The contrast makes it immediately clear whether the player is in the game or in a setup/navigation context

Do not use Rich `Panel` for startup menus or character selection screens.

### Wizard step content uses Panels; wizard prompts do not

Multi-step wizards (e.g., `/guide envision`, `/truths`) contain two kinds of output:

- **Instructional content** (rules explanation, option descriptions): use `Panel` with `border_style="cyan"` — this is reference material the player may re-read
- **Prompts and choices** (the actual "what do you choose?" questions): plain text — this is scaffolding

## Consequences

- Developers have a clear rule: *if you're showing the result of a game action, use a Panel; otherwise, don't*.
- The scroll-back log is easier to read because results visually stand out from surrounding UI text.
- New commands should route display through `display.py` functions where possible, rather than calling `Panel` directly from command handlers.
- The visual hierarchy is: ASCII boxes (navigation) → plain text (scaffolding) → Rich Panel (game results). Each layer is visually heavier than the last.
