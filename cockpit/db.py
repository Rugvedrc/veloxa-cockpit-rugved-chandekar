"""SQLite storage. One file, rebuilt from scratch by `python cockpit.py build`.

Why rebuild-from-source: the exports are the record of truth and new drops arrive
on days 3 and 4. A deterministic rebuild means no hand-edited state to drift.
"""
import os
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "veloxa.db"
DATA_DIR = pathlib.Path(os.environ.get("VELOXA_DATA") or ROOT.parent / "Veloxa_Hackathon_Release_Packs")

SCHEMA = """
CREATE TABLE source (            -- every file we ever loaded
  id INTEGER PRIMARY KEY, name TEXT, relpath TEXT, kind TEXT,
  released_on TEXT,              -- ISO date of the drop (for 'what did we know on date X')
  note TEXT);
CREATE TABLE person (
  emp_id TEXT PRIMARY KEY, full_name TEXT, email TEXT, dept TEXT, title TEXT,
  manager_id TEXT, join_date TEXT, location TEXT, status TEXT, exit_date TEXT, src_ref TEXT);
CREATE TABLE alias (             -- every spelling of a person/vendor we have seen
  alias TEXT, kind TEXT, resolves_to TEXT, seen_in TEXT, confidence TEXT, note TEXT);
CREATE TABLE payroll (           -- SENSITIVE: never exposed per-person by the cockpit
  emp_id TEXT, month TEXT, days_in_month INT, days_payable INT,
  gross INT, deductions INT, net INT, processed_by TEXT, src_ref TEXT);
CREATE TABLE gl_entry (
  id INTEGER PRIMARY KEY, txn_date TEXT, voucher TEXT, vendor_raw TEXT, vendor_id TEXT,
  ref TEXT, cost_centre TEXT, amount INT, narration TEXT, entered_by TEXT, src_ref TEXT);
CREATE TABLE vendor (id TEXT PRIMARY KEY, name TEXT, note TEXT);
CREATE TABLE board_update (
  period TEXT, sent_on TEXT, arr_cr REAL, customers INT, team INT,
  burn_lakh REAL, runway_months INT, narrative TEXT, src_ref TEXT);
CREATE TABLE message (           -- emails
  msg_id TEXT, sender TEXT, recipient TEXT, subject TEXT, sent_at TEXT, body TEXT, src_ref TEXT);
CREATE TABLE document (          -- transcripts, letters, anything free text
  doc_id TEXT PRIMARY KEY, kind TEXT, title TEXT, body TEXT, src_ref TEXT);
CREATE TABLE claim (             -- curated statements from transcripts, with our verdict
  id TEXT PRIMARY KEY, doc_id TEXT, speaker TEXT, topic TEXT, as_heard TEXT,
  resolved TEXT, verdict TEXT, evidence TEXT, confidence TEXT);
CREATE TABLE finding (           -- computed data-quality / business issues
  id TEXT PRIMARY KEY, kind TEXT, severity INT, title TEXT, detail TEXT, evidence TEXT, status TEXT);
"""


def connect(path=None):
    con = sqlite3.connect(path or DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def rebuild(path=None):
    p = pathlib.Path(path or DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()
    con = connect(p)
    con.executescript(SCHEMA)
    return con
