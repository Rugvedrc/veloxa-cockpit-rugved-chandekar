"""Load every export we have into the model. Idempotent; re-run after each data drop.

Files are found by name anywhere under DATA_DIR/Day*/ so later drops need no code
change for files we already understand.
"""
import email
import email.policy
import email.utils
import re
import zipfile
from datetime import datetime, timezone, timedelta

import openpyxl
from pypdf import PdfReader

from . import db

IST = timezone(timedelta(hours=5, minutes=30))
DAY_DATES = {"Day1": "2026-11-16", "Day2": "2026-11-17", "Day3": "2026-11-18", "Day4": "2026-11-19"}
MONTHS = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


AS_OF = None  # ISO date; only drops released on/before it are loaded ('what did we know on date X')


def files(pattern):
    out = []
    root = db.data_dir()
    for p in sorted(root.glob(f"Day*/{pattern}")):
        day = DAY_DATES.get(p.relative_to(root).parts[0][:4])
        if AS_OF is None or (day and day <= AS_OF):
            out.append(p)
    return out


def add_source(con, path, kind, note=""):
    day = next((DAY_DATES[p[:4]] for p in path.parts if p[:4] in DAY_DATES), None)
    con.execute("INSERT INTO source(name,relpath,kind,released_on,note) VALUES(?,?,?,?,?)",
                (path.name, str(path.relative_to(db.data_dir())), kind, day, note))


def _rows(path, header_row=3):
    """Yield (excel_row_number, dict) for an export whose header sits on `header_row`."""
    ws = openpyxl.load_workbook(path, data_only=True).active
    rows = ws.iter_rows(min_row=header_row, values_only=True)
    header = [str(h).strip() for h in next(rows)]
    for i, r in enumerate(rows, start=header_row + 1):
        if any(c is not None for c in r):
            yield i, dict(zip(header, r))


def load_employees(con):
    for p in files("data_room/hr/Employee_Master.xlsx"):
        add_source(con, p, "hr", "Keka export; contractors are NOT in it")
        for i, r in _rows(p):
            con.execute("INSERT OR REPLACE INTO person VALUES(?,?,?,?,?,?,?,?,?,?,?)", (
                r["Emp ID"], r["Full Name"], r["Work Email"], r["Department"], r["Title"],
                r["Manager ID"], r["Join Date"], r["Location"], r["Status"], r["Exit Date"],
                f"{p.name}!R{i}"))


def load_payroll(con):
    for p in files("data_room/finance/Payroll_Register_*.xlsx"):
        add_source(con, p, "finance", "pre-Keka payroll workbook; SENSITIVE")
        for i, r in _rows(p):
            con.execute("INSERT INTO payroll VALUES(?,?,?,?,?,?,?,?,?)", (
                r["Emp ID"], r["Month"], r["Days in Month"], r["Days Payable"], r["Gross (Rs.)"],
                r["Deductions (Rs.)"], r["Net (Rs.)"], r["Processed By"], f"{p.name}!R{i}"))


def load_gl(con):
    for p in files("data_room/finance/GL_Export_*.xlsx"):
        add_source(con, p, "finance", "Zoho Books GL, selected cost centres only")
        for i, r in _rows(p):
            con.execute("""INSERT INTO gl_entry(txn_date,voucher,vendor_raw,ref,cost_centre,amount,
                           narration,entered_by,src_ref) VALUES(?,?,?,?,?,?,?,?,?)""", (
                r["Txn Date"], r["Voucher"], r["Vendor / Payee"], r["Ref"], r["Cost Centre"],
                r["Amount (Rs.)"], r["Narration"], r["Entered By"], f"{p.name}!R{i}"))


def _pdf_text(path):
    return "\n".join(pg.extract_text() or "" for pg in PdfReader(path).pages)


def load_board(con):
    for p in files("data_room/documents/Board_Update_*.pdf"):
        add_source(con, p, "document")
        t = _pdf_text(p)
        period = re.search(r"Period:\s*([A-Za-z]+ to [A-Za-z]+ \d{4})", t).group(1)
        d, mon, y = re.search(r"Sent (\d+) ([A-Za-z]{3}) (\d{4})", t).groups()
        lines = [l.strip() for l in t.splitlines()]

        def after(label):
            return lines[lines.index(label) + 1]

        num = lambda s: float(re.search(r"\d+(?:\.\d+)?", s).group())
        narrative = re.sub(r"\s+", " ", t.split("Runway", 1)[1].split("\n", 2)[2])
        con.execute("INSERT INTO board_update VALUES(?,?,?,?,?,?,?,?,?)", (
            period, f"{y}-{MONTHS[mon]:02d}-{int(d):02d}", num(after("ARR (recurring)")),
            int(num(after("Customers"))), int(num(after("Team"))), num(after("Monthly burn")),
            int(num(after("Runway"))), narrative.strip(), p.name))
        con.execute("INSERT OR REPLACE INTO document VALUES(?,?,?,?,?)",
                    (p.stem, "board_update", p.stem.replace("_", " "), t, p.name))


def load_emails(con):
    seen = set()
    for p in files("data_room/email/*.eml"):
        m = email.message_from_bytes(p.read_bytes(), policy=email.policy.default)
        mid = m["Message-ID"]
        if mid in seen:
            continue
        seen.add(mid)
        add_source(con, p, "email")
        sent = email.utils.parsedate_to_datetime(m["Date"]).astimezone(IST).isoformat()
        body = m.get_body(("plain",)).get_content().strip()
        con.execute("INSERT INTO message VALUES(?,?,?,?,?,?,?,?)",
                    (mid, m["From"], m["To"], m["Subject"], sent, body, p.name, m["Cc"]))


def _docx_text(path):
    x = zipfile.ZipFile(path).read("word/document.xml").decode("utf8")
    x = re.sub(r"</w:p>", "\n", x)
    x = re.sub(r"<[^>]+>", "", x)
    for a, b in (("&apos;", "'"), ("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&")):
        x = x.replace(a, b)
    return x


def load_transcripts(con):
    for p in files("transcripts/*.docx"):
        add_source(con, p, "transcript", "machine-generated; may be misheard")
        body = _docx_text(p)
        con.execute("INSERT OR REPLACE INTO document VALUES(?,?,?,?,?)",
                    (p.stem.split("_")[0], "transcript", body.strip().splitlines()[0], body, p.name))


def _people_lookup(con):
    """('A', 'das') -> emp_id for 'A. Das'-style names; 'VM' -> emp_id for approver initials.
    Entries that would be ambiguous are dropped rather than guessed."""
    by_name, by_init = {}, {}
    for r in con.execute("SELECT emp_id, full_name FROM person"):
        first, *_, last = r["full_name"].split()
        for table, key in ((by_name, (first[0].upper(), last.lower())), (by_init, first[0].upper() + last[0].upper())):
            table[key] = None if key in table else r["emp_id"]
    return by_name, by_init


def load_requisitions(con):
    for p in files("data_room/hr/Hiring_Tracker.xlsx"):
        add_source(con, p, "hr", "Keka Hire export")
        for i, r in _rows(p):
            con.execute("INSERT INTO requisition VALUES(?,?,?,?,?,?,?,?,?,?)", (
                r["Req ID"], r["Role"], r["Team"], r["Hiring Manager"], r["Opened"], r["Status"],
                r["Status Date"], r["In pipeline"], r["Notes"], f"{p.name}!R{i}"))


def load_leave(con):
    by_name, by_init = _people_lookup(con)
    for p in files("data_room/hr/Leave_Register.xlsx"):
        add_source(con, p, "hr", "Google Sheet kept by People & Ops; names are initials")
        for i, r in _rows(p):
            first, last = r["Employee"].split(". ", 1)
            con.execute("INSERT INTO leave VALUES(?,?,?,?,?,?,?,?,?)", (
                by_name.get((first.upper(), last.lower())), r["Employee"], r["Leave Type"], r["From"],
                r["To"], r["Days"], r["Approved By"], by_init.get(r["Approved By"]), f"{p.name}!R{i}"))


def load_pulse(con):
    for p in files("data_room/hr/Pulse_Survey.xlsx"):
        add_source(con, p, "hr", "Culture Amp; team level; comments hidden for teams under 6")
        for i, r in _rows(p):
            q = r["Quarter"]  # e.g. 'Jul-Sep 2026' -> quarter end 2026-09
            end = f"{q[-4:]}-{MONTHS[q[4:7]]:02d}"
            con.execute("INSERT INTO pulse VALUES(?,?,?,?,?,?,?,?)", (
                q, end, r["Team"], r["Team size"], r["Responses"], r["Engagement (1-5)"], r["Comments"],
                f"{p.name}!R{i}"))


def load_letters(con):
    for p in files("data_room/documents/Resignation_Letter_*.pdf"):
        add_source(con, p, "document")
        t = _pdf_text(p)
        lines = [l.strip() for l in t.splitlines() if l.strip()]
        name = lines[0]
        row = con.execute("SELECT emp_id FROM person WHERE full_name=?", (name,)).fetchone()
        letter = datetime.strptime(re.search(r"\d{1,2} [A-Za-z]+ \d{4}", t).group(), "%d %B %Y").date()
        last = datetime.strptime(re.search(r"last working day will be (\d{1,2} [A-Za-z]+ \d{4})", t).group(1), "%d %B %Y").date()
        to = re.search(r"^To (.+)$", t, re.M).group(1).strip()
        why = re.search(r"([^.]*looking for[^.]*\.)", re.sub(r"\s+", " ", t))
        con.execute("INSERT INTO resignation VALUES(?,?,?,?,?,?)", (
            row["emp_id"] if row else None, letter.isoformat(), last.isoformat(), to,
            why.group(1).strip() if why else None, p.name))
        con.execute("INSERT OR REPLACE INTO document VALUES(?,?,?,?,?)",
                    (p.stem, "letter", p.stem.replace("_", " "), t, p.name))


def _utc(s):
    """'2026-08-04T05:12:00Z' -> aware UTC datetime."""
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def load_git(con):
    import csv
    for p in files("data_room/engineering/git_log.csv"):
        add_source(con, p, "engineering", "git history; committed_at is UTC in the source")
        with open(p, encoding="utf8", newline="") as fh:
            for i, r in enumerate(csv.DictReader(fh), start=2):
                t = datetime.fromisoformat(r["committed_at"])
                con.execute("INSERT INTO git_commit VALUES(?,?,?,?,?,?,?,?,?)", (
                    r["sha"], r["author_email"].strip().lower(), None, t.astimezone(timezone.utc).isoformat(),
                    t.astimezone(IST).isoformat(), r["repo"], r["message"], int(r["files_changed"]), f"{p.name}!R{i}"))


def load_incidents(con):
    for p in files("data_room/engineering/Incidents_*.xlsx"):
        add_source(con, p, "engineering", "PagerDuty export; times are UTC in the source")
        for i, r in _rows(p):
            o, c = _utc(r["Opened"]), _utc(r["Resolved"])
            con.execute("INSERT INTO incident VALUES(?,?,?,?,?,?,?,?,?,?,?)", (
                r["ID"], r["Severity"], o.isoformat(), c.isoformat(), o.astimezone(IST).isoformat(),
                c.astimezone(IST).isoformat(), round((c - o).total_seconds() / 3600, 2), r["Service"],
                r["Responder"], None, f"{p.name}!R{i}"))


def load_oncall(con):
    for p in files("data_room/engineering/OnCall_Rota.xlsx"):
        add_source(con, p, "engineering", "team wiki table copied into a sheet")
        for i, r in _rows(p):
            con.execute("INSERT INTO oncall VALUES(?,?,?,?,?,?)",
                        (r["Week of"], r["Primary"], r["Secondary"], None, None, f"{p.name}!R{i}"))


def load_jira(con):
    for p in files("data_room/engineering/Jira_Export_*.xlsx"):
        add_source(con, p, "engineering", "Jira export, project ATLAS; assignee shown as initials")
        wb = openpyxl.load_workbook(p, data_only=True)
        for i, r in _sheet_rows(wb["Issues"], 3):
            con.execute("INSERT INTO jira_issue VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (
                r["Key"], r["Type"], r["Summary"], r["Epic Link"], r["Assignee"], None, r["Story Points"],
                r["Status"], r["Created"], r["Resolved"] or None, r["Fix Version"], f"{p.name}!Issues!R{i}"))
        for i, r in _sheet_rows(wb["Epics"], 1):
            con.execute("INSERT INTO jira_epic VALUES(?,?,?)", (r["Key"], r["Epic Name"], f"{p.name}!Epics!R{i}"))
        for i, r in _sheet_rows(wb["Versions"], 1):
            con.execute("INSERT INTO jira_version VALUES(?,?,?,?,?,?)", (
                r["Version"], r["Release Date"], r["Original Release Date"], r["Last Changed"], r["Changed By"],
                f"{p.name}!Versions!R{i}"))


def _sheet_rows(ws, header_row):
    rows = ws.iter_rows(min_row=header_row, values_only=True)
    header = [str(h).strip() for h in next(rows)]
    for i, r in enumerate(rows, start=header_row + 1):
        if any(c is not None for c in r):
            yield i, dict(zip(header, r))


def _inr(s):
    """'1,41,600' -> 141600 (Indian digit grouping)."""
    return int(s.replace(",", ""))


def load_invoices(con):
    for p in files("data_room/documents/Invoice_*.pdf"):
        add_source(con, p, "document")
        t = _pdf_text(p)
        flat = re.sub(r"\s+", " ", t)
        no = re.search(r"Invoice No\. (\S+)", flat).group(1)
        d, m, y = re.search(r"Date (\d{2})/(\d{2})/(\d{4})", flat).groups()
        vendor = t.strip().splitlines()[0].title()
        desc = re.search(r"Amount \(Rs\.\) (.+?) (?:[\d,]+) IGST", flat).group(1)
        base = _inr(re.search(re.escape(desc) + r" ([\d,]+)", flat).group(1))
        tax = _inr(re.search(r"IGST @ \d+% ([\d,]+)", flat).group(1))
        total = _inr(re.search(r"Total ([\d,]+)", flat).group(1))
        note = re.search(r"(Previous invoice .+)$", flat)
        con.execute("INSERT INTO invoice VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (
            no, vendor, None, re.search(r"GSTIN (\w+)", flat).group(1), f"{y}-{m}-{d}",
            re.search(r"Place of Supply (.+?) Description", flat).group(1), desc, base, tax, total,
            note.group(1) if note else None, p.name))
        con.execute("INSERT OR REPLACE INTO document VALUES(?,?,?,?,?)", (p.stem, "invoice", p.stem.replace("_", " "), t, p.name))


def load_launch_kit(con):
    for p in files("data_room/documents/Atlas_Launch_Kit_*.pdf"):
        add_source(con, p, "document")
        t = _pdf_text(p)
        lines = [l.strip() for l in t.splitlines() if l.strip()]
        version = re.search(r"launch kit, (v\d+)", lines[0], re.I).group(1)
        owner, dated = re.search(r"Owner: (\w+)\. (\d+ \w+ \d{4})", lines[1]).groups()
        dated = datetime.strptime(dated, "%d %b %Y").date().isoformat()
        body = lines[lines.index("Status") + 1:]
        for asset, status in zip(body[0::2], body[1::2]):
            con.execute("INSERT INTO launch_kit VALUES(?,?,?,?,?,?,?)", (version, owner, None, dated, asset, status, p.name))
        con.execute("INSERT OR REPLACE INTO document VALUES(?,?,?,?,?)", (p.stem, "launch_kit", p.stem.replace("_", " "), t, p.name))


def load_email_printout(con):
    """The printable copy of the emails must agree with the .eml files; record whether it does."""
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    for p in files("data_room/email/Email_Printouts.pdf"):
        t = _pdf_text(p)
        blocks = re.split(r"\n(?=\d\d\. )", t)[1:]
        have = {(norm(r["subject"]), norm(r["body"])) for r in con.execute("SELECT subject, body FROM message")}
        same = diff = 0
        for b in blocks:
            subject = norm(b.splitlines()[0][4:])
            body = norm(re.sub(r"^.*?\nDate:[^\n]*\n", "", b, count=1, flags=re.S))
            if (subject, body) in have:
                same += 1
            else:
                diff += 1
        add_source(con, p, "email", f"printable copy: {same} of {same + diff} threads identical to the .eml files, {diff} differences")
        con.execute("INSERT OR REPLACE INTO document VALUES(?,?,?,?,?)", (p.stem, "printout", "Email printouts", t, p.name))


def load_all(con):
    for fn in (load_employees, load_payroll, load_gl, load_board, load_emails, load_transcripts,
               load_requisitions, load_leave, load_pulse, load_letters,
               load_git, load_incidents, load_oncall, load_jira, load_invoices, load_launch_kit, load_email_printout):
        fn(con)
    con.commit()
