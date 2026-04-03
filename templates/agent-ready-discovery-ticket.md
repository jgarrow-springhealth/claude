---
name: agent-ready-discovery-ticket
description: Template for scoped discovery tickets. Forces a single answerable question, a named output artifact, and a hard time-box — so discovery doesn't become open-ended research.
---

# Agent-Ready Discovery Ticket

> Discovery tickets answer one question and produce one artifact. If you can't name both, split or defer.

---

## The Question _(required)_

A single, answerable question. If it takes more than two sentences, it's probably two tickets.

```
Should we use X or Y for Z? What are the tradeoffs given our constraints?
```

---

## Output Artifact _(required)_

Name the container. It can fan out downstream (a scoping doc that spawns tickets, an epic update that unblocks a team) — but it must be a single named thing. If you can't name it, the ticket isn't ready.

```
ADR in Confluence under <space/page>
Updated epic CFPL-XXXX with scoped sub-tickets
Scoping doc + ticket breakdown in <space/page>
Slack summary in #<channel> + linked doc
```

---

## Time-box _(required)_

A hard limit. Discovery without a time-box is just research.

```
2 hours / 1 day / end of sprint
If the question isn't answerable in this time, surface blockers and stop.
```

---

## Starting Points _(optional)_

Where to begin. Cuts orientation time. Include if the first step isn't obvious.

```
- Prior art: CFPL-XXXX (last time we evaluated this)
- Relevant code: app/services/foo/
- PRD: <Confluence link>
- Ask: @person who owns this area
```

---

## Explicit Out of Scope _(optional)_

Only include if there's a real risk of drift. Skip if the question is already sharp.

```
- Do not evaluate options outside our current infra
- Do not produce implementation code
```
