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
   requisition | leave | pulse | resignation                                   (Day 2 HR material)
   git_commit | incident | oncall | jira_issue/epic/version | invoice | launch_kit   (Day 3 engineering; times kept in UTC and IST)
   contractor | reporting_line (current from Keka, planned from curated org_changes.json)   (identity and org, Day 3)
   reported_event (what someone said happened, e.g. a resignation; never edits Keka rows)  <- data/curated/events.json   (Day 4)
   alias  (every spelling of a person/vendor, with confidence and release date)
   claim  (curated transcript statements, our verdict, `disagrees`, `released_on`, `revises`)  <- data/curated/claims.json
   finding (computed issues, each with evidence refs and a theme)               <- checks.py
        |
        +--> worry.top_three()   findings -> themes (delivery | money | people) -> ranked top three   [home screen, T6a]
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
| Agents | Persona + facts from DB; LLM only if a key exists; replies with numbers (digits or words) not in the records are retried, then dropped; Day 2 persona revisions are overlays applied only once Day 2 exists | Works offline; stays consistent with the records and the date |
| Top three | Findings carry a theme; themes ranked by max severity, then the CEO's stated concern, then count; rule shown on screen | Answers T6a without mixing unlike things (DECISIONS D-15) |
| People risk | Team-level only; no named flight risks; survey comments never shown | Small teams are identifiable (DECISIONS D-16) |
| Release dates | Claims, aliases, persona overlays and findings are all date-gated | A Day 1 database holds nothing from Day 2 or 3 (DECISIONS D-17) |
| Identities | Alias table with confidence; ambiguous matches stay empty; two git identities merged on evidence; a contractor kept separate from an employee with a similar name | DECISIONS D-20 |
| Org | Dated reporting lines, current vs planned; no hard-coded names, titles or departments in handlers | A reorganisation test runs everything on a reshuffled copy (D-21, T6b) |
| Disagreement | Jira vs git, VP vs Jira, spoken vs recorded: both sides are shown, not one picked | D-23 |
| Reported vs recorded | A reported event is stored apart, labelled, and flips to "Keka shows" when a record changes (tested) | D-25 |
| People requests | Likelihood-to-quit rankings and private-message reading are declined; a dependency view is offered; no new GA date is ever produced | D-24, D-26, D-27 |

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
| `cockpit/worry.py` | Top-three themes and the ranking rule |
| `cockpit/org.py` | Reporting lines with dates: current vs planned |
| `cockpit/events.py` | Reported events (not records) and notice-period readings |
| `cockpit/impact.py` | Continuity exposure: what the work records say is at stake if a person left; dependency ranking |
| `cockpit/agents.py` | Agent context, LLM providers (NVIDIA, Groq, Anthropic), offline mode, memory |
| `cockpit/server.py`, `ui.html` | Web UI and JSON API on 127.0.0.1 |
| `tests/` | 115-question set, behaviour tests for Days 1-4, the reorganisation and lifecycle test, Python 3.9 compatibility guard |

## Not built yet

- Living agents (stretch): agents that keep producing plausible activity after 31 Oct. Not attempted: invented activity would need to be kept apart from the records so it could never contaminate an answer, and the must-haves came first.
- Agents for people who do not exist yet (the CRO); deliberately not invented

## Change log

- 2026-11-16 (early): initial architecture, Day 1 data only.
- 2026-11-19: Day 4 (voice notes T6c, T6d; no data files). Reported events kept apart from records; impact and dependency views; refusals for likelihood rankings and private messages; "urgent" findings lead their theme; top three labels reported-today items; 115-question set; `ANALYSED_THROUGH` moved to 2026-11-19.
- 2026-11-18: Day 3 data (git, Jira, incidents, on-call rota, launch kit, invoice, email printouts, T4, T5, T6b); Cc header captured; contractor and git-identity resolution; findings for Atlas date and remaining work, concentration, on-call load, launch kit and invoices; dated reporting lines and a reorganisation test (T6b); name lookup reads the people table; 91-question test set; `ANALYSED_THROUGH` moved to 2026-11-18.
- 2026-11-17: Day 2 data (hiring tracker, leave register, pulse survey, resignation letter, 4 emails, T3, T6a); findings get themes; top-three home screen (T6a); claims, aliases and persona text become release-dated; `ANALYSED_THROUGH` moved to 2026-11-17; 54-question test set.
- 2026-11-16 (final): data room found at run time (folder or zip); one database per release date with runtime "as of"; "sources disagree" signal; 35-question test set; Python 3.9 compatibility guard; stricter fallback search.
