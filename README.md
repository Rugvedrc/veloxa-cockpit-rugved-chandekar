# Veloxa CXO Cockpit

Ask one question about Veloxa and get a short answer that cites the records behind it, states a confidence level, and says so when the sources disagree or the data is silent. It also has a ranked "what should I worry about" view, an "as of date" selector (what did we know on date X), and 14 colleagues you can interview.

Veloxa is a synthetic company created for the Hiyaku Systems hackathon; all data is fictional.

## Setup (one command)

Requires Python 3.9 or newer. The data room is **not** in this repo (it is confidential), so point the command at the zip you were sent, or at the unzipped folder:

```
python bootstrap.py --data path/to/Veloxa_Hackathon_Release_Packs.zip
```

On macOS/Linux use `python3`. It creates `.venv`, installs two dependencies (`openpyxl`, `pypdf`), builds the databases, and runs the automated test set. If the zip sits next to this folder, in `~/Downloads`, or in `~/Desktop`, `--data` can be omitted. The location is remembered in `data/.datapath` (git-ignored).

## Run

```
.venv\Scripts\python cockpit.py serve          # Windows; macOS/Linux: .venv/bin/python
```

then open http://127.0.0.1:8765 . Tabs: **Ask**, **What should I worry about**, **People** (interview any of the 14), **Conflicts in the sources**. The "What we knew as of" selector re-answers everything using only material released by that date.

Command line:

```
python cockpit.py ask "how many people work here?"
python cockpit.py ask "what is our ARR?" --as-of 2026-11-15     # before any release -> nothing known
python cockpit.py worry
python cockpit.py interview VX007 "what keeps you up at night?"
python cockpit.py build [--data PATH] [--as-of DATE]            # rebuild databases
```

## Tests

```
python cockpit.py test            # same as: python -m unittest discover tests
```

`tests/questions.json` holds 35 question/answer checks (answers with sources, "sources disagree", refusals to give individual pay, "I don't know", point-in-time). `tests/test_cockpit.py` checks the data model, findings, release-date gating and the agents; `tests/test_compat.py` guards Python 3.9 compatibility. Tests never call an LLM.

## Agents and AI

Agent interviews work offline from grounded facts. For full persona mode add `NVIDIA_API_KEY` (or `GROQ_API_KEY` / `ANTHROPIC_API_KEY`) to a git-ignored `.env` in the repo root or its parent folder, or set it as an environment variable. Only those three names are read from `.env`. The agent's facts (never pay) are then sent to that provider; remove the key to stay local. Never commit a key. Change the model with `VELOXA_NVIDIA_MODEL` / `VELOXA_GROQ_MODEL`. If a model answers with a number that is not in the agent's records, the reply is retried once and then replaced by the offline answer.

The cockpit itself does not use an LLM: answers are assembled from SQL so every number traces to a row (see DECISIONS D-03).

## Layout

| Path | What |
|---|---|
| `bootstrap.py` | One-command setup |
| `cockpit.py` | Command line |
| `cockpit/db.py` | Schema, data-room discovery (folder or zip) |
| `cockpit/build.py` | One database per release date; `answer()` entry point |
| `cockpit/loaders.py` | Reads xlsx, pdf, eml, docx into SQLite, stamped with release day |
| `cockpit/resolve.py` | Aliases for people and vendors; curated transcript claims |
| `cockpit/checks.py` | Computed findings behind the worry view |
| `cockpit/ask.py` | Answer engine: question -> SQL -> answer, sources, confidence, caveats |
| `cockpit/agents.py` | The 14 agents |
| `cockpit/server.py`, `ui.html` | Web UI and JSON API (127.0.0.1 only) |
| `data/curated/` | Hand-written inputs: transcript claims, invented personas |
| `ARCHITECTURE.md`, `ASSUMPTIONS.md`, `TRANSCRIPT_NOTES.md`, `DECISIONS.md`, `AI_LOG.md` | The reasoning log |

## Privacy

Individual salaries are stored (payroll register) but no answer or agent exposes them; the cockpit gives totals only, and no agent receives pay data. See DECISIONS D-05.

## Status

Day 1 data (Mon 16 Nov) is loaded, reconciled and analysed. Later drops are added day by day; until a day's data is modelled, later "as of" dates are answered from the latest modelled snapshot and say so.
