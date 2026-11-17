"""SQLite storage and data-room discovery.

One database file per release date, rebuilt from the exports (see build.py). Why rebuild from
source: the exports are the record of truth and new drops arrive on days 2-4, so a
deterministic rebuild means there is no hand-edited state to drift.

The data room is confidential and is NOT part of this repo. It is found at run time (see
find_data_room) as either the unzipped folder or the original .zip.
"""
import os
import pathlib
import sqlite3
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"          # where a .zip is unpacked (git-ignored)
PACK = "Veloxa_Hackathon_Release_Packs"

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
  resolved TEXT, verdict TEXT, evidence TEXT, confidence TEXT,
  disagrees INT,                 -- 1 = what was said contradicts the records
  released_on TEXT,              -- the drop whose material this verdict rests on (point-in-time)
  revises TEXT);                 -- id of an earlier claim this one corrects or extends
CREATE TABLE finding (           -- computed data-quality / business issues
  id TEXT PRIMARY KEY, kind TEXT, severity INT, title TEXT, detail TEXT, evidence TEXT, status TEXT,
  theme TEXT);                   -- delivery | money | people: groups findings for the top-three view
CREATE TABLE requisition (       -- Keka Hire tracker
  req_id TEXT PRIMARY KEY, role TEXT, team TEXT, hiring_manager TEXT, opened TEXT, status TEXT,
  status_date TEXT, in_pipeline INT, notes TEXT, src_ref TEXT);
CREATE TABLE leave (             -- People & Ops leave register (names as initials in the source)
  emp_id TEXT, employee_raw TEXT, leave_type TEXT, from_date TEXT, to_date TEXT, days REAL,
  approved_by TEXT, approver_id TEXT, src_ref TEXT);
CREATE TABLE pulse (             -- Culture Amp pulse, team level only (comments hidden if team < 6)
  quarter TEXT, quarter_end TEXT, team TEXT, team_size INT, responses INT, engagement REAL,
  comments TEXT, src_ref TEXT);
CREATE TABLE resignation (
  emp_id TEXT, letter_date TEXT, last_day TEXT, addressed_to TEXT, stated_reason TEXT, src_ref TEXT);
"""

_override = None
_resolved = None


def _pack_root(p):
    """The folder that directly contains the Day* folders, given a folder at or above it."""
    if any(p.glob("Day*")):
        return p
    for sub in sorted(p.iterdir()) if p.is_dir() else []:
        if sub.is_dir() and any(sub.glob("Day*")):
            return sub
    return None


def _extract(zip_path):
    """Unpack the release zip into data/raw once. Refuses entries that would escape the folder."""
    target = RAW_DIR / zip_path.stem
    root = _pack_root(target) if target.exists() else None
    if root:
        return root
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if not (target / name).resolve().is_relative_to(target.resolve()):
                raise ValueError(f"unsafe path in zip: {name}")
        z.extractall(target)
    return _pack_root(target)


def find_data_room(explicit=None):
    """Locate the data room. Order: explicit path, VELOXA_DATA, then the usual places.
    Accepts the unzipped folder (or a folder containing it) or the .zip itself."""
    tried = []
    saved = ROOT / "data" / ".datapath"  # written after the first successful setup (git-ignored)
    cands = [explicit, os.environ.get("VELOXA_DATA"), saved.read_text().strip() if saved.exists() else None]
    for base in (ROOT, ROOT.parent, pathlib.Path.home() / "Downloads", pathlib.Path.home() / "Desktop"):
        cands += [base / PACK, base / (PACK + ".zip")]
    for c in cands:
        if not c:
            continue
        p = pathlib.Path(c).expanduser()
        tried.append(str(p))
        if p.is_file() and p.suffix.lower() == ".zip":
            root = _extract(p)
        elif p.is_dir():
            root = _pack_root(p)
        else:
            continue
        if root:
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_text(str(root))
            return root
    raise FileNotFoundError(
        "Veloxa data room not found. Give its folder or .zip, e.g.\n"
        "    python bootstrap.py --data path/to/Veloxa_Hackathon_Release_Packs.zip\n"
        "(or set VELOXA_DATA). Looked in:\n  " + "\n  ".join(tried))


def set_data_dir(path):
    global _override, _resolved
    _override, _resolved = path, None


def data_dir():
    global _resolved
    if _resolved is None:
        _resolved = find_data_room(_override)
    return _resolved


def connect(path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def rebuild(path):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()
    con = connect(p)
    con.executescript(SCHEMA)
    return con
