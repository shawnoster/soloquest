# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records - documents that capture important architectural decisions made along with their context and consequences.

---

## What are ADRs?

ADRs document significant architectural and design decisions. Each ADR describes:

- **Context** - The forces at play (technical, political, social, project)
- **Decision** - The change being proposed or made
- **Status** - Proposed, Accepted, Deprecated, Superseded
- **Consequences** - The impact of the decision (positive and negative)

---

## ADR Index

| # | Title | Status | Date |
|---|-------|--------|------|
| [001](001-repo-workflow-and-conventions.md) | Repository Workflow and Conventions | Accepted | 2026-02-14 |
| [002](002-ui-panel-guidelines.md) | UI Panel Guidelines | Accepted | 2026-02-17 |

---

## Creating New ADRs

When making significant architectural decisions:

1. Copy the template below
2. Number it sequentially (002, 003, etc.)
3. Fill in all sections
4. Submit in a PR for review
5. Update this index

### ADR Template

```markdown
# ADR-XXX: [Title]

**Status:** Proposed | Accepted | Deprecated | Superseded
**Date:** YYYY-MM-DD

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?
```

---

## References

- [Michael Nygard's ADR article](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub organization](https://adr.github.io/)
