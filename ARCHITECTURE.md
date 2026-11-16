# ARCHITECTURE

Status: Day 1 (Mon 16 Nov 2026). Updated as the design changes; see the change log at the bottom.

## What it is

A local app that answers one CEO question at a time from the Veloxa data room. Every answer carries its sources, a confidence level and caveats, and the system says "I don't have a record" when that is the honest answer.

## Data flow

```
Veloxa_Hackathon_Release_Packs/Day*/   (read only, never copied into the repo)
        |  loaders.py   xlsx / pdf / eml / docx; each file stamped with its release date
        v
SQLite (data/veloxa.db, rebuilt from scratch by `cockpit.py build`)
   source | person | payroll* | gl_entry | board_update | message | document
   alias (every spelling of a person/vendor, with confidence)
   claim (curated transcript statements + our verdict)     <- data/curated/claims.json
   finding (computed issues, each with evidence refs)      <- checks.py
        |
        +--> ask.py      question -> intent handler -> SQL -> {answer, cites, confidence, caveats}
        +--> agents.py   14 people: facts from the DB + invented life from personas.json
        +--> server.py   stdlib HTTP + one HTML page (Ask / Worry / People / Conflicts)
   * payroll is stored but never returned per person
```

## Key design points

| Point | Choice | Why (details in DECISIONS.md) |
|---|---|---|
| Storage | One SQLite file, deleted and rebuilt on every build | Exports are the truth; new drops need no migration; zero setup |
| Provenance | Every row keeps `src_ref` (file!row) | Lets any answer cite the exact record |
| Point-in-time | Each source has `released_on`; `build --as-of DATE` loads only drops released by then | Later material cannot leak into earlier answers |
| Answers | Deterministic SQL handlers, not an LLM | Numbers are query results; unknowns fall through to an honest refusal |
| Conflicts | `alias` and `claim` tables record what was believed and why; nothing is merged silently | Reasoning is queryable and defensible |
| Privacy | Pay never leaves the database per person; agents never receive it | CFO rule in T2 |
| Agents | Persona + facts from DB; LLM only if a key is set | Works offline; grounded either way |

## Module map

| File | Responsibility |
|---|---|
| `cockpit/db.py` | Schema, connection, data-room location (`VELOXA_DATA`) |
| `cockpit/loaders.py` | Parse every export type, release-date gating |
| `cockpit/resolve.py` | Alias tables, claims loader, `find_person` |
| `cockpit/checks.py` | Computed findings behind the "worry" view |
| `cockpit/ask.py` | Intent handlers and fallback search |
| `cockpit/agents.py` | Agent context, LLM call, offline mode, memory |
| `cockpit/server.py`, `ui.html` | Web UI and JSON API on 127.0.0.1 |
| `tests/` | Answer-quality tests, run with one command |

## Not built yet

- Day 2-4 loaders (leave, hiring, pulse, Jira, git, incidents, on-call, PDFs for the resignation letter, invoice and launch kit)
- 25+ question test set (9 exist; at least 5 must test refusals)
- Responses to voice notes T6a-T6d
- Living agents (stretch)

## Change log

- 2026-11-16: initial architecture (Day 1 data only).
