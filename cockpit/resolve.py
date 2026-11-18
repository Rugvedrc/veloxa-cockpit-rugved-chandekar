"""Entity resolution: one canonical id per person / vendor, with every spelling kept.

Nothing is merged silently. Every alias row says where it was seen, how sure we are and which
drop it rests on, so the answer to 'why did you think X was Y' is a query, not a memory, and
an alias learned on a later day cannot leak into an earlier day's database.
"""
import json
import re

from . import loaders
from .db import ROOT

D1, D2, D3 = "2026-11-16", "2026-11-17", "2026-11-18"

# (alias, emp_id, seen in, confidence, evidence, released_on)
PERSON_ALIASES = [
    ("Pria", "VX007", "T1", "H", "Transcript mishearing of Priya; 'holds the routing thing together' fits Staff Engineer", D1),
    ("the new boy Rahul", "VX018", "T1", "H", "Only recent hire in Engineering (joined 2026-02-03)", D1),
    ("Kartik", "VX010", "T2", "H", "Spelling of Karthik; planning = FP&A Manager", D1),
    ("Fatima Shaikh", "VX014", "T2", "H", "Keka spelling is 'Sheikh'", D1),
    ("Vicky", "VX004", "T2", "L", "Nickname guess for Vikram Menon; could also be someone else. Verify before relying on it", D1),
    ("Vikram's people", "VX004", "T1", "M", "Engineering reports to Vikram (Manager ID VX004)", D1),
    ("FS", "VX014", "GL / Payroll 'Entered/Processed By'", "H", "Fatima Sheikh initials", D1),
    ("KS", "VX010", "Payroll 'Processed By'", "H", "Karthik Subramanian initials; email 01 confirms he ran Feb payroll", D1),
    ("SM", "VX013", "Resignation_Letter_SM.pdf", "H", "The letter is signed Siddharth Mehta", D2),
    ("Sid from marketing", "VX013", "T3", "H", "Deepa: 'Sid from marketing has put in his papers'; Siddharth Mehta is the marketing resignation", D2),
    ("Sid", "VX013", "T3", "M", "Short form; only one Siddharth/Sid on staff", D2),
    ("Vicky", "VX004", "T2 + emails 06/07", "M", "Raised from Low: the freeze T2 says to 'check with Vicky' is the pause of REQ-014/015 agreed between Meera and Vikram on 12 Aug", D2),
    ("Ayesha", "VX011", "T4", "H", "Transcription of Aisha Khan: 'Ayesha' runs paid search, which is Aisha's role (Performance Marketing Manager)", D3),
    ("pnair@users.noreply.github.com", "VX007", "git_log.csv", "M",
     "GitHub no-reply address of P. Nair, a second git identity for Priya Nair: both commit only to atlas-engine over the same "
     "dates (Nov 2025 - Oct 2026), never within a minute of each other, with the same hours; no other P. Nair exists", D3),
    ("PN", "VX007", "Jira_Export_ATLAS (assignee initials)", "H", "Initials of Priya Nair; matches the owner of the core-engine epics in Vikram's 2 Jun plan", D3),
    ("RV", "VX018", "Jira_Export_ATLAS (assignee initials)", "H", "Initials of Rahul Verma; owns the API epic as in the 2 Jun plan", D3),
    ("AD", "VX009", "Jira_Export_ATLAS (assignee initials)", "H", "Initials of Arjun Das; owns the planner-UI epic as in the 2 Jun plan", D3),
    ("SK", "VX012", "Jira_Export_ATLAS (assignee initials)", "H", "Initials of Sneha Kulkarni; owns the hardening epic as in the 2 Jun plan", D3),
]

# People paid through a vendor, so absent from Keka. (id, name, vendor, role, evidence, confidence, released_on)
CONTRACTORS = [
    ("X001", "Snehal (S. Patil)", "PATIL", "On-call SRE (contractor, Patil Infra Services)",
     "The on-call rota lists 'Snehal' and 'Sneha' in the same weeks, so they are two people. Keka has no Snehal. Invoice PIS-114 bills "
     "'On-call SRE support, S. Patil'. PIS-108 covers 18-31 Aug, matching the first rota week with Snehal (17 Aug). Email 08 (24 Aug): "
     "'The contractor starts on the rota this week'.", "M", D3),
]
CONTRACTOR_ALIASES = [("Snehal", "X001"), ("S. Patil", "X001")]

# vendor_id -> (canonical name, note). Raw spellings map below.
VENDORS = {
    "AWS": ("Amazon Web Services", "Cloud hosting"),
    "GOOG": ("Google India Pvt Ltd", "Google Ads"),
    "WEWORK": ("WeWork India", "Office rent"),
    "COHERE": ("Cohere Recruiting Partners", "Recruiter; 2 backend roles"),
    "PAYROLL": ("Salaries (payroll)", "Internal posting, not an external vendor"),
    "SAPPHIRE-EVT": ("Sapphire Events Pvt Ltd", "Summit venue/AV. POSSIBLY the same as 'Saphire Event Mgmt' - see findings"),
    "SAPHIRE-MGMT": ("Saphire Event Mgmt", "Summit catering. Kept SEPARATE from Sapphire Events until confirmed"),
    "SAPPHIRE-HOTEL": ("Sapphire Residency Hotel", "Hotel for sales offsite. Different business; name similarity is a coincidence"),
    "PATIL": ("Patil Infra Services", "On-call support contractor (not in Keka)"),
}
RAW_TO_VENDOR = {
    "Amazon Web Services": "AWS", "Google India Pvt Ltd": "GOOG", "WeWork India": "WEWORK",
    "Cohere Recruiting Partners": "COHERE", "Salaries (payroll)": "PAYROLL",
    "Sapphire Events Pvt Ltd": "SAPPHIRE-EVT", "Saphire Event Mgmt": "SAPHIRE-MGMT",
    "Sapphire Residency Hotel": "SAPPHIRE-HOTEL", "Patil Infra Services": "PATIL",
}


def _released(day):
    """True if material from `day` may be known in the database being built."""
    return loaders.AS_OF is None or day <= loaders.AS_OF


def load_entities(con):
    for r in con.execute("SELECT emp_id, full_name, email FROM person").fetchall():
        first = r["full_name"].split()[0]
        con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (r["full_name"], "person", r["emp_id"], "Employee_Master.xlsx", "H", "canonical"))
        con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (r["email"], "person", r["emp_id"], "Employee_Master.xlsx", "H", "work email"))
        con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (first, "person", r["emp_id"], "derived", "M", "first name; ambiguous if shared"))
    for alias, emp, seen, conf, note, day in PERSON_ALIASES:
        if _released(day):
            con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (alias, "person", emp, seen, conf, note))
    for vid, (name, note) in VENDORS.items():
        con.execute("INSERT INTO vendor VALUES(?,?,?)", (vid, name, note))
    for raw, vid in RAW_TO_VENDOR.items():
        con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (raw, "vendor", vid, "GL export", "H", "as written in GL"))
    con.execute("UPDATE gl_entry SET vendor_id = (SELECT resolves_to FROM alias WHERE kind='vendor' AND alias=vendor_raw)")
    for cid, name, vid, role, ev, conf, day in CONTRACTORS:
        if _released(day):
            con.execute("INSERT INTO contractor VALUES(?,?,?,?,?,?)", (cid, name, vid, role, ev, conf))
            for alias, target in CONTRACTOR_ALIASES:
                if target == cid:
                    con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (alias, "contractor", cid, "rota / invoice", conf, ev[:90]))
    con.execute("UPDATE invoice SET vendor_id = (SELECT resolves_to FROM alias WHERE kind='vendor' AND alias=vendor_name)")
    link_records(con)


def _one(con, raw, kinds=("contractor", "person")):
    """The single id a raw name/initials/email resolves to, or None if unknown or ambiguous."""
    if raw is None:
        return None
    for kind in kinds:
        ids = {r[0] for r in con.execute("SELECT resolves_to FROM alias WHERE kind=? AND lower(alias)=lower(?)", (kind, raw))}
        if len(ids) == 1:
            return ids.pop()
    return None


def link_records(con):
    """Point every engineering record at a person. Anything that resolves to more than one person stays NULL."""
    for (em,) in con.execute("SELECT DISTINCT author_email FROM git_commit").fetchall():
        con.execute("UPDATE git_commit SET emp_id=? WHERE author_email=?", (_one(con, em, ("person",)), em))
    for (raw,) in con.execute("SELECT DISTINCT assignee_raw FROM jira_issue").fetchall():
        con.execute("UPDATE jira_issue SET emp_id=? WHERE assignee_raw=?", (_one(con, raw, ("person",)), raw))
    for (raw,) in con.execute("SELECT DISTINCT responder_raw FROM incident").fetchall():
        con.execute("UPDATE incident SET responder_id=? WHERE responder_raw=?", (_one(con, raw), raw))
    for r in con.execute("SELECT rowid, primary_raw, secondary_raw FROM oncall").fetchall():
        con.execute("UPDATE oncall SET primary_id=?, secondary_id=? WHERE rowid=?",
                    (_one(con, r["primary_raw"]), _one(con, r["secondary_raw"]), r["rowid"]))
    for (raw,) in con.execute("SELECT DISTINCT owner_raw FROM launch_kit").fetchall():
        con.execute("UPDATE launch_kit SET owner_id=? WHERE owner_raw=?", (_one(con, raw, ("person",)), raw))


def load_claims(con):
    for c in json.loads((ROOT / "data" / "curated" / "claims.json").read_text(encoding="utf8")):
        day = c.get("released_on", D1)
        if not _released(day):
            continue
        con.execute("INSERT INTO claim VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (
            c["id"], c["doc_id"], c["speaker"], c["topic"], c["as_heard"], c["resolved"],
            c["verdict"], c["evidence"], c["confidence"], int(c.get("disagrees", False)), day, c.get("revises")))


def find_person(con, text):
    """Return emp_id for the best name match in `text`, or None. Longest alias wins."""
    t = text.lower()
    best = None
    # Aliases first, then the people table itself, so someone added or renamed in the data is found without waiting for a rebuild.
    rows = [(r["alias"], r["resolves_to"]) for r in con.execute("SELECT alias, resolves_to FROM alias WHERE kind='person'")]
    for r in con.execute("SELECT emp_id, full_name FROM person"):
        rows.append((r["full_name"], r["emp_id"]))
        rows.append((r["full_name"].split()[0], r["emp_id"]))
    for alias, resolves_to in rows:
        a = alias.lower()
        if "@" in a or len(a) < 3:
            continue
        if re.search(r"\b" + re.escape(a) + r"\b", t):
            if best is None or len(a) > best[0]:
                best = (len(a), resolves_to)
    return best[1] if best else None
