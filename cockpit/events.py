"""Things people have SAID happened that no record shows yet (voice note T6d: "Pria resigned this morning").

They are stored apart from the records, labelled 'reported', and shown with who said it. Nothing here edits
Keka's person rows: headcount, status and manager answers stay as the records say until a record changes.
A reported event can still be reasoned about (what would it do to Atlas?) because that reasoning uses only
the records plus the reported fact, and says so.
"""
import calendar
import json
from datetime import date, timedelta

from . import loaders
from .db import ROOT


def load_events(con):
    path = ROOT / "data" / "curated" / "events.json"
    for e in json.loads(path.read_text(encoding="utf8")):
        if loaders.AS_OF is not None and e["released_on"] > loaders.AS_OF:
            continue
        if not con.execute("SELECT 1 FROM person WHERE emp_id=?", (e["emp_id"],)).fetchone():
            continue  # the person is no longer in the data: skip rather than fail
        con.execute("INSERT INTO reported_event VALUES(?,?,?,?,?,?,?,?,?,?)", (
            e["id"], e["emp_id"], e["kind"], e["reported_on"], e["reported_by"], e["status"],
            e.get("notice_text"), e.get("notice_months"), e["source"], e.get("note")))
    con.commit()


def add_months(d, n):
    y, m = divmod(d.month - 1 + n, 12)
    year, month = d.year + y, m + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def reported(con, emp, kind="resignation"):
    return con.execute("SELECT * FROM reported_event WHERE emp_id=? AND kind=? AND status='reported'", (emp, kind)).fetchone()


def notice_readings(con, ev):
    """The possible last days. The notice period is not in any record, so every reading is labelled with its basis."""
    rep = date.fromisoformat(ev["reported_on"])
    out = []
    if ev["notice_months"]:
        out.append((f"the CEO's '{ev['notice_text']}'", add_months(rep, ev["notice_months"])))
    res = con.execute("SELECT letter_date, last_day FROM resignation LIMIT 1").fetchone()
    if res:
        days = (date.fromisoformat(res["last_day"]) - date.fromisoformat(res["letter_date"])).days
        out.append((f"the only precedent in the records ({days} days)", rep + timedelta(days=days)))
    return sorted(out, key=lambda x: x[1])
