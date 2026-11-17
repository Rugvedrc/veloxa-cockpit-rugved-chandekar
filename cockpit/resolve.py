"""Entity resolution: one canonical id per person / vendor, with every spelling kept.

Nothing is merged silently. Every alias row says where it was seen, how sure we are and which
drop it rests on, so the answer to 'why did you think X was Y' is a query, not a memory, and
an alias learned on a later day cannot leak into an earlier day's database.
"""
import json
import re

from . import loaders
from .db import ROOT

D1, D2 = "2026-11-16", "2026-11-17"

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
]

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
    for r in con.execute("SELECT alias, resolves_to, confidence FROM alias WHERE kind='person'"):
        a = r["alias"].lower()
        if "@" in a or len(a) < 3:
            continue
        if re.search(r"\b" + re.escape(a) + r"\b", t):
            if best is None or len(a) > best[0]:
                best = (len(a), r["resolves_to"])
    return best[1] if best else None
