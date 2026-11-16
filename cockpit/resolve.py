"""Entity resolution: one canonical id per person / vendor, with every spelling kept.

Nothing is merged silently. Every alias row says where it was seen and how sure we are,
so the answer to 'why did you think X was Y' is a query, not a memory.
"""
import json
import re

from .db import ROOT

# Spellings that appear in transcripts/other files and the evidence for each mapping.
PERSON_ALIASES = [
    ("Pria", "VX007", "T1", "H", "Transcript mishearing of Priya; 'holds the routing thing together' fits Staff Engineer"),
    ("the new boy Rahul", "VX018", "T1", "H", "Only recent hire in Engineering (joined 2026-02-03)"),
    ("Kartik", "VX010", "T2", "H", "Spelling of Karthik; planning = FP&A Manager"),
    ("Fatima Shaikh", "VX014", "T2", "H", "Keka spelling is 'Sheikh'"),
    ("Vicky", "VX004", "T2", "L", "Nickname guess for Vikram Menon; could also be someone else. Verify before relying on it"),
    ("Vikram's people", "VX004", "T1", "M", "Engineering reports to Vikram (Manager ID VX004)"),
    ("SM", "VX013", "Resignation letter (Day 2)", "L", "Initials in file name 'Resignation_Letter_SM'; Siddharth Mehta is on notice"),
    ("FS", "VX014", "GL / Payroll 'Entered/Processed By'", "H", "Fatima Sheikh initials"),
    ("KS", "VX010", "Payroll 'Processed By'", "H", "Karthik Subramanian initials; email 01 confirms he ran Feb payroll"),
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


def load_entities(con):
    for r in con.execute("SELECT emp_id, full_name, email FROM person").fetchall():
        first = r["full_name"].split()[0]
        con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (r["full_name"], "person", r["emp_id"], "Employee_Master.xlsx", "H", "canonical"))
        con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (r["email"], "person", r["emp_id"], "Employee_Master.xlsx", "H", "work email"))
        con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (first, "person", r["emp_id"], "derived", "M", "first name; ambiguous if shared"))
    for alias, emp, seen, conf, note in PERSON_ALIASES:
        con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (alias, "person", emp, seen, conf, note))
    for vid, (name, note) in VENDORS.items():
        con.execute("INSERT INTO vendor VALUES(?,?,?)", (vid, name, note))
    for raw, vid in RAW_TO_VENDOR.items():
        con.execute("INSERT INTO alias VALUES(?,?,?,?,?,?)", (raw, "vendor", vid, "GL export", "H", "as written in GL"))
    con.execute("UPDATE gl_entry SET vendor_id = (SELECT resolves_to FROM alias WHERE kind='vendor' AND alias=vendor_raw)")


def load_claims(con):
    for c in json.loads((ROOT / "data" / "curated" / "claims.json").read_text(encoding="utf8")):
        con.execute("INSERT INTO claim VALUES(?,?,?,?,?,?,?,?,?,?)", (
            c["id"], c["doc_id"], c["speaker"], c["topic"], c["as_heard"], c["resolved"],
            c["verdict"], c["evidence"], c["confidence"], int(c.get("disagrees", False))))


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
