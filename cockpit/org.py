"""Reporting lines, with dates, so the cockpit keeps working when people move (voice note T6b).

Two kinds of line, never mixed up:
  current  built from Keka's Manager ID. This is what is true now.
  planned  from data/curated/org_changes.json: things the CEO or others have said will happen
           ('marketing will report to the new CRO'). They carry a date window and a source, may name no
           manager yet, and are never shown as fact.

Nothing here (or in the handlers that use it) hard-codes a person, a title or a department: every
lookup is by id or by a title found in the data, and a missing manager, a vacated title or a
brand-new department simply produces a shorter answer, not an error.
"""
import json

from . import loaders
from .db import ROOT


def load_org(con):
    for p in con.execute("SELECT emp_id, manager_id, join_date FROM person WHERE manager_id IS NOT NULL").fetchall():
        mgr = con.execute("SELECT title FROM person WHERE emp_id=?", (p["manager_id"],)).fetchone()
        con.execute("INSERT INTO reporting_line VALUES(?,?,?,?,?,?,?,?)",
                    (p["emp_id"], p["manager_id"], mgr["title"] if mgr else None, p["join_date"], None, "current",
                     "Employee_Master.xlsx", None))
    path = ROOT / "data" / "curated" / "org_changes.json"
    for c in json.loads(path.read_text(encoding="utf8")):
        if loaders.AS_OF is not None and c["released_on"] > loaders.AS_OF:
            continue
        subject = con.execute("SELECT emp_id FROM person WHERE title=? AND status='Active' LIMIT 1", (c["subject_title"],)).fetchone()
        if not subject:  # the role is vacant or renamed: skip rather than guess
            continue
        mgr = None
        if c.get("new_manager_name"):
            row = con.execute("SELECT emp_id FROM person WHERE full_name=?", (c["new_manager_name"],)).fetchone()
            mgr = row["emp_id"] if row else None
        con.execute("INSERT INTO reporting_line VALUES(?,?,?,?,?,?,?,?)",
                    (subject["emp_id"], mgr, c["new_manager_title"], c["earliest"], c["latest"], "planned", c["source"], c["note"]))
    con.commit()


def manager_of(con, emp):
    """{'current': person row or None, 'planned': [reporting_line rows with the manager's name if known]}"""
    cur = con.execute("""SELECT p.* FROM reporting_line r JOIN person p ON p.emp_id=r.manager_id
                         WHERE r.emp_id=? AND r.status='current' ORDER BY r.from_date DESC LIMIT 1""", (emp,)).fetchone()
    planned = [dict(r) for r in con.execute("SELECT * FROM reporting_line WHERE emp_id=? AND status='planned' ORDER BY from_date", (emp,))]
    return {"current": cur, "planned": planned}


def reports_of(con, emp):
    """People currently reporting to `emp` (by line, so a planned move changes nothing until it is real)."""
    return con.execute("""SELECT p.* FROM reporting_line r JOIN person p ON p.emp_id=r.emp_id
                          WHERE r.manager_id=? AND r.status='current' AND p.status != 'Exited' ORDER BY p.full_name""", (emp,)).fetchall()


def planned_text(line):
    who = line["manager_title"] or "a new manager"
    when = f"{line['from_date'][:7]}" + (f" or {line['to_date'][:7]}" if line["to_date"] and line["to_date"][:7] != line["from_date"][:7] else "")
    return f"to report to the {who}, expected {when}; no one is named yet" if line["manager_id"] is None \
        else f"to report to {who}, expected {when}"
