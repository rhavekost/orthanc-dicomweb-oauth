# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) documenting significant architectural and technical decisions made during the development of the Orthanc DICOMweb OAuth plugin.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences.

## Format

Each ADR follows this structure:

```markdown
# ADR NNN: Title

**Status:** [Proposed | Accepted | Deprecated | Superseded]
**Date:** YYYY-MM-DD
**Decision Makers:** Who made this decision

## Context
What is the issue we're seeing that is motivating this decision?

## Decision
What is the change we're proposing?

## Rationale
Why did we choose this option over alternatives?

## Alternatives Considered
What other options did we evaluate?

## Consequences
What becomes easier or harder as a result of this change?

## References
Links to relevant documentation, discussions, or resources
```

## Index of ADRs

- [ADR 001: OAuth2 Client Credentials Flow Only](001-client-credentials-flow.md)
- [ADR 002: No Feature Flags](002-no-feature-flags.md)
- [ADR 003: Minimal API Versioning Strategy](003-minimal-api-versioning.md)
- [ADR 004: Threading Over Async/Await](004-threading-over-async.md)

## Creating New ADRs

1. Copy the template above
2. Use next sequential number
3. Use kebab-case for filename: `NNN-short-title.md`
4. Get review from at least one other developer
5. Update this index when accepted
