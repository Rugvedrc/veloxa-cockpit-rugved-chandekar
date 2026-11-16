# Veloxa CXO Cockpit

Ask one question about Veloxa, get a short answer with the records behind it. Plus a "what should I worry about" view and 14 colleagues you can interview.

## Setup (one command)

```
python bootstrap.py
```

It creates `.venv`, installs two dependencies (`openpyxl`, `pypdf`), builds the database, and runs the tests.
The data room is expected at `../Veloxa_Hackathon_Release_Packs`; otherwise set `VELOXA_DATA` to that folder.

## Run

```
.venv\Scripts\python cockpit.py serve          # web UI: http://127.0.0.1:8765
.venv\Scripts\python cockpit.py ask "how many people work here?"
.venv\Scripts\python cockpit.py worry
.venv\Scripts\python cockpit.py interview VX007 "what keeps you up at night?"
.venv\Scripts\python cockpit.py build --as-of 2026-11-18   # what did we know on that date
```

Agent interviews run offline from grounded facts by default. Set `ANTHROPIC_API_KEY` for full persona mode (data is then sent to Anthropic's API; unset it to stay local).

## Layout

| Path | What |
|---|---|
| `cockpit/loaders.py` | Reads the exports (xlsx, pdf, eml, docx) into SQLite, stamps each with its release day |
| `cockpit/resolve.py` | Aliases for people and vendors, curated transcript claims |
| `cockpit/checks.py` | Computed findings (payroll proration, lookalike vendors, trends, ...) |
| `cockpit/ask.py` | The answer engine: question -> SQL -> answer + sources + caveats |
| `cockpit/agents.py` | The 14 agents |
| `data/curated/` | Hand-written inputs: transcript claims, invented personas |
| `ASSUMPTIONS.md`, `TRANSCRIPT_NOTES.md`, `DECISIONS.md` | The reasoning log |
| `tests/` | Answer-quality tests (`python -m unittest discover tests`) |

## Privacy

Individual salaries are in the database (payroll register) but no answer or agent exposes them; the cockpit gives totals only. See DECISIONS D-05.
