# ARCHITECTURE

Status: Day 1 (Mon 16 Nov 2026) complete. Updated as the design changes; see the change log at the bottom.

## What it is

A local app that answers one CEO question at a time from the Veloxa data room. Every answer carries its sources, a confidence level and caveats, flags when the sources disagree, and says "I don't have anything on that" when that is the honest answer.

## Data flow

```
Veloxa_Hackathon_Release_Packs  (folder or .zip, found at run time, never copied into the repo)
        |  loaders.py   xlsx / pdf / eml / docx; each file stamped with its release date
        v
data/veloxa_<release date>.db   (SQLite, ONE PER RELEASE DATE, built on demand by build.py)
   source | person | payroll* | gl_entry | board_update | message | document
   alias  (every spelling of a person/vendor, with confidence)
   claim  (curated transcript statements, our verdict, and a `disagrees` flag)  <- data/curated/claims.json
   finding (computed issues, each with evidence refs)                           <- checks.py
        |
        +--> build.answer(question, as_of) --> ask.py  question -> intent handler -> SQL
        |        -> {answer, cites, confidence, caveats, disagreement}
        +--> agents.py   14 people: facts from the DB + invented personality + optional LLM
        +--> server.py + ui.html (Ask / Worry / People / Conflicts, "as of" selector)   and cockpit.py (CLI)
   * payroll is stored but never returned per person and never given to an agent
```

## Key design points

| Point | Choice | Why (details in DECISIONS.md) |
|---|---|---|
| Storage | SQLite, deleted and rebuilt from the exports | Exports are the truth; new drops need no migration; zero setup |
| Data room | Located at setup (`--data` folder or zip, remembered afterwards), kept out of git | It is confidential; graders run from a fresh clone |
| Provenance | Every row keeps `src_ref` (file!row) | Any answer can cite the exact record |
| Point in time | One database per release date; `as_of` picks the newest release <= that date, `ANALYSED_THROUGH` caps it at what is modelled | Later material cannot leak into earlier answers |
| Answers | Deterministic SQL handlers, not an LLM | Numbers are query results; unknowns fall through to an honest refusal |
| Conflicts | `claim.disagrees` drives a "sources disagree" banner; `alias` records what was believed | Reasoning is queryable and defensible |
| Fallback search | Needs >= 2 whole-word keyword matches in one record | A lone common word is not evidence |
| Privacy | Pay never leaves the database per person; agents never receive it | CFO rule in T2 |
| Agents | Persona + facts from DB; LLM only if a key exists; replies with numbers not in the records are retried, then dropped | Works offline; stays consistent with the records |

## Module map

| File | Responsibility |
|---|---|
| `bootstrap.py` | Venv, dependencies, build, tests |
| `cockpit/db.py` | Schema, connection, data-room discovery (folder/zip, zip-slip safe) |
| `cockpit/build.py` | Per-date databases, cache invalidation, `answer()`, `table()` |
| `cockpit/loaders.py` | Parse every export type with release-date gating |
| `cockpit/resolve.py` | Alias tables, claims loader, `find_person` |
| `cockpit/checks.py` | Computed findings behind the worry view |
| `cockpit/ask.py` | Intent handlers and fallback search |
| `cockpit/agents.py` | Agent context, LLM providers (NVIDIA, Groq, Anthropic), offline mode, memory |
| `cockpit/server.py`, `ui.html` | Web UI and JSON API on 127.0.0.1 |
| `tests/` | 35-question set, behaviour tests, Python 3.9 compatibility guard |

## Not built yet

- Day 2-4 loaders (leave, hiring, pulse, Jira, git, incidents, on-call, resignation letter, invoice, launch kit, email printouts)
- Responses to voice notes T6a-T6d (T6a due Tue 17 Nov, 11:59 PM IST)
- Agent workload and history from Jira / on-call data (Day 3)
- Living agents (stretch)

## Change log

- 2026-11-16 (early): initial architecture, Day 1 data only.
- 2026-11-16 (final): data room found at run time (folder or zip); one database per release date with runtime "as of"; "sources disagree" signal; 35-question test set; Python 3.9 compatibility guard; stricter fallback search.
