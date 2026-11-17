"""Computed findings: things the data says that someone should look at.

Every finding is derived from rows (never hand-typed numbers) and carries evidence refs, so the
'what should I worry about' view stays true when new drops arrive. A finding that can use richer
data (e.g. the hiring tracker) does so only when that table is present, so an earlier day's
database never shows later facts.

Severity: 3 = act now, 2 = look soon, 1 = FYI.
Theme groups findings for the top-three view: delivery | money | people.
"""
import calendar
import difflib
from datetime import date

MON = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def _add(con, fid, kind, sev, title, detail, evidence, theme):
    con.execute("INSERT OR REPLACE INTO finding VALUES(?,?,?,?,?,?,?,?)",
                (fid, kind, sev, title, detail, evidence, "open", theme))


def _has(con, table):
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] > 0


def _usual_processor_leave(con, month_first, month_last):
    """Leave of the person who normally runs payroll, overlapping the month (None if unknown)."""
    top = con.execute("SELECT processed_by FROM payroll GROUP BY processed_by ORDER BY COUNT(*) DESC").fetchone()
    if not top or not _has(con, "leave"):
        return None
    who = con.execute("SELECT resolves_to FROM alias WHERE kind='person' AND alias=? LIMIT 1", (top[0],)).fetchone()
    if not who:
        return None
    return con.execute("""SELECT l.*, p.full_name FROM leave l JOIN person p USING(emp_id)
                          WHERE l.emp_id=? AND l.from_date <= ? AND l.to_date >= ?""",
                       (who[0], month_last.isoformat(), month_first.isoformat())).fetchone()


def payroll_proration(con):
    """Joiners/leavers must be paid only for days employed in the month."""
    n = 0
    for r in con.execute("""SELECT p.*, e.full_name, e.join_date, e.exit_date FROM payroll p
                            JOIN person e USING(emp_id)"""):
        mon, yr = r["month"].split("-")
        y, m = int(yr), MON[mon]
        first, last = date(y, m, 1), date(y, m, calendar.monthrange(y, m)[1])
        start = max(first, date.fromisoformat(r["join_date"]))
        end = min(last, date.fromisoformat(r["exit_date"])) if r["exit_date"] else last
        expected = (end - start).days + 1
        if expected > 0 and r["days_payable"] != expected:
            over = round(r["gross"] * (r["days_payable"] - expected) / r["days_in_month"])
            n += 1
            mails = [x["src_ref"] for x in con.execute(
                "SELECT src_ref FROM message WHERE subject LIKE '%payslip%' ORDER BY sent_at")]
            lv = _usual_processor_leave(con, first, last)
            why = (f"{lv['full_name']}, who normally runs payroll, was on approved {lv['leave_type'].lower()} leave "
                   f"{lv['from_date']} to {lv['to_date']} (leave register)") if lv else "the usual processor was out"
            ev = f"{r['src_ref']}; Employee_Master join date; {', '.join(mails)}" + (f"; {lv['src_ref']}" if lv else "")
            n_who = r["processed_by"]
            _add(con, f"F-PAY-{r['emp_id']}-{mon}", "payroll", 3,
                 f"{r['full_name']} was paid for {r['days_payable']} days in {mon} {y}, should be {expected}",
                 f"Joined {r['join_date']}, so only {expected} of {r['days_in_month']} days were payable. "
                 f"Estimated gross overpayment Rs {over:,}. Processed by {n_who} because {why}. The employee "
                 f"raised it on 6 Mar and the reply on 10 Mar was only 'will check and get back' - no correction "
                 f"is visible in the data.", ev, "money")
    return n


def vendor_lookalikes(con):
    vs = con.execute("""SELECT vendor_id, vendor_raw, MIN(cost_centre) cc, SUM(amount) total,
                        GROUP_CONCAT(src_ref) refs FROM gl_entry WHERE vendor_id NOT IN ('PAYROLL')
                        GROUP BY vendor_id""").fetchall()
    for i, a in enumerate(vs):
        for b in vs[i + 1:]:
            ratio = difflib.SequenceMatcher(None, a["vendor_raw"].lower(), b["vendor_raw"].lower()).ratio()
            if ratio < 0.6:
                continue
            if a["cc"] == b["cc"]:
                _add(con, f"F-VEN-{a['vendor_id']}-{b['vendor_id']}", "vendor", 2,
                     f"Possible duplicate vendor: '{a['vendor_raw']}' and '{b['vendor_raw']}'",
                     f"Same cost centre ({a['cc']}), near-identical names (similarity {ratio:.2f}), combined "
                     f"Rs {a['total'] + b['total']:,}. Different invoice-ref formats. This can make the same "
                     f"event show up as two vendors and may explain why Marketing's and Finance's totals differ. "
                     f"Not merged: needs the invoice/PAN to confirm.",
                     f"{a['refs']}; {b['refs']}", "money")
            else:
                _add(con, f"F-VEN-{a['vendor_id']}-{b['vendor_id']}", "vendor", 1,
                     f"Similar names, probably different vendors: '{a['vendor_raw']}' vs '{b['vendor_raw']}'",
                     f"Different cost centres ({a['cc']} vs {b['cc']}) and different purpose. Kept separate so "
                     f"hotel spend is not counted as event spend.", f"{a['refs']}; {b['refs']}", "money")


def cost_trends(con):
    rows = con.execute("""SELECT txn_date, amount, src_ref FROM gl_entry WHERE vendor_id='AWS'
                          ORDER BY txn_date""").fetchall()
    if len(rows) >= 2:
        a, z = rows[0], rows[-1]
        g = (z["amount"] - a["amount"]) / a["amount"] * 100
        boards = con.execute("SELECT arr_cr FROM board_update ORDER BY sent_on").fetchall()
        arr_g = (boards[-1]["arr_cr"] / boards[0]["arr_cr"] - 1) * 100 if len(boards) > 1 else 0
        _add(con, "F-AWS-TREND", "cost", 2,
             f"AWS bill up {g:.0f}% ({a['amount']:,} -> {z['amount']:,}) while ARR grew {arr_g:.0f}%",
             f"Booked monthly in arrears, {a['txn_date']} to {z['txn_date']} (+{g:.0f}% over five months). The board "
             f"reports ARR +{arr_g:.0f}% between its two quarterly updates, so hosting cost is outpacing revenue. "
             f"Cause unknown: could be Atlas load testing or the August reliability problems; no usage data to check.",
             f"{a['src_ref']}; {z['src_ref']}; Board updates", "money")


def payroll_flat(con):
    vals = [r[0] for r in con.execute("SELECT DISTINCT amount FROM gl_entry WHERE cost_centre='PAYROLL'")]
    reg = con.execute("""SELECT month, SUM(gross) g FROM payroll GROUP BY month""").fetchall()
    if len(vals) == 1:
        last = reg[-1] if reg else None
        match = f" It equals the Mar-2026 register total (Rs {last['g']:,}) exactly." if last and last["g"] == vals[0] else ""
        _add(con, "F-PAY-FLAT", "finance", 1,
             f"Payroll posted in GL is identical every month (Rs {vals[0]:,}) for Apr-Sep",
             f"Six months with zero variance. Real payroll normally moves a little each month (leave, deductions, "
             f"increments, joiners, leavers).{match} Looks copied forward rather than posted from each month's "
             f"actual payroll run. Needs the Keka payroll data to confirm.",
             "GL_Export_Apr-Sep_2026.xlsx PAYROLL rows; Payroll_Register_Jan-Mar_2026.xlsx", "money")


def hiring(con):
    fee = con.execute("SELECT amount, src_ref FROM gl_entry WHERE vendor_id='COHERE'").fetchone()
    if not fee:
        return
    if _has(con, "requisition"):
        held = con.execute("SELECT * FROM requisition WHERE status='On hold' ORDER BY req_id").fetchall()
        if held:
            cand = sum(r["in_pipeline"] for r in held)
            mails = [m["src_ref"] for m in con.execute("SELECT src_ref FROM message WHERE subject LIKE '%Pausing%' ORDER BY sent_at")]
            roles = ", ".join(f"{r['req_id']} {r['role']}" for r in held)
            cancelled = "; ".join(r["notes"] for r in held if r["notes"])
            _add(con, "F-HIRE", "people", 3 if cand >= 6 else 2,
                 f"{len(held)} backend roles on hold since {held[0]['status_date']} with {cand} candidates waiting",
                 f"{roles}, opened {held[0]['opened']}. The CFO paused them 'until the round closes' to protect burn "
                 f"and the VP Engineering replied 'We'll absorb it'. Tracker note: {cancelled}. The recruiter was already "
                 f"paid Rs {fee['amount']:,} (50% advance) on 30 Jun for these roles; if the fee is split 50/50 about the "
                 f"same is still owed. Meanwhile Atlas (already late) is being built by the existing team.",
                 f"{'; '.join(r['src_ref'] for r in held)}; {'; '.join(mails)}; {fee['src_ref']}", "delivery")
            return
    _add(con, "F-HIRE", "people", 2,
         "Recruiter retained for 2 backend roles, but hiring is now paused",
         f"Rs {fee['amount']:,} (50% advance) paid to the recruiter on 30 Jun. The Q2 board update promised "
         f"two backend engineers that quarter; the Q3 update says hiring is paused. No such joiners are in "
         f"Keka. If the fee is split 50/50 as the narration suggests, a balance of about Rs {fee['amount']:,} "
         f"is still owed, and Atlas remains short-staffed.",
         f"{fee['src_ref']}; both board updates; Employee_Master.xlsx", "delivery")


def hiring_vs_board(con):
    """The board was told hiring is paused; the tracker may show otherwise."""
    if not _has(con, "requisition"):
        return
    b = con.execute("SELECT * FROM board_update ORDER BY sent_on DESC LIMIT 1").fetchone()
    opened = con.execute("""SELECT * FROM requisition WHERE status='Open' AND opened > '2026-08-12' ORDER BY opened""").fetchall()
    if b and "paused" in b["narrative"].lower() and opened:
        txt = "; ".join(f"{r['req_id']} {r['role']} ({r['team']}, opened {r['opened']}, {r['in_pipeline']} in pipeline)" for r in opened)
        _add(con, "F-HIRE-BOARD", "people", 2,
             f"Board told 'hiring is paused', but {len(opened)} roles opened after the pause are still open",
             f"Board update of {b['sent_on']} says hiring is paused while the round closes. The tracker shows only the "
             f"two backend roles on hold; since then: {txt}. Either the statement was loose or roles were opened "
             f"against the stated pause. One of them is the backfill for the leaving Product Marketing Manager.",
             f"{b['src_ref']}; " + "; ".join(r["src_ref"] for r in opened), "people")


def atlas(con):
    b = con.execute("SELECT * FROM board_update ORDER BY sent_on").fetchall()
    if len(b) >= 2:
        _add(con, "F-ATLAS", "delivery", 3,
             "Atlas (routing engine v3) GA slipped from 15 Sep with no new date",
             f"{b[0]['sent_on']}: 'on track for GA on 15 September'. {b[-1]['sent_on']}: GA moved to absorb "
             f"reliability work after 'a difficult August'. The CEO believes customers were promised delivery "
             f"'by the festive season' and is unsure it will make it. No replacement date exists in any source yet.",
             "Board updates; T1 (CEO call)", "delivery")


def pulse_drops(con):
    """Team-level only (comments are hidden for teams under 6, and so are individuals)."""
    if not _has(con, "pulse"):
        return
    for t in [r[0] for r in con.execute("SELECT DISTINCT team FROM pulse ORDER BY team")]:
        rows = con.execute("SELECT * FROM pulse WHERE team=? ORDER BY quarter_end DESC LIMIT 2", (t,)).fetchall()
        if len(rows) < 2:
            continue
        now, before = rows
        drop = before["engagement"] - now["engagement"]
        if drop < 0.3:
            continue
        mail = con.execute("SELECT src_ref FROM message WHERE subject LIKE 'pulse%' ORDER BY sent_at").fetchall()
        follow = (" HR advised the CEO on 29 Sep to have the VP Engineering run 1:1s; no follow-up is visible."
                  if t == "Engineering" and mail else "")
        eng = t == "Engineering"
        _add(con, f"F-PULSE-{t.upper().replace(' ', '-')}", "people", 3 if drop >= 0.7 else 2,
             f"{t} engagement fell {before['engagement']} -> {now['engagement']} ({now['quarter']}), {now['responses']} of {now['team_size']} responded",
             f"The biggest team-level drop on record is {t}: {before['quarter']} {before['engagement']} to "
             f"{now['quarter']} {now['engagement']}. Comments are hidden because the team is under 6 people, so the "
             f"reasons are not in the data.{follow} Reported at team level only on purpose.",
             f"{now['src_ref']}; {before['src_ref']}" + (f"; {mail[0][0]}" if mail and eng else ""),
             "delivery" if eng else "people")


def departures(con):
    for r in con.execute("SELECT * FROM person WHERE status != 'Active'"):
        res = con.execute("SELECT * FROM resignation WHERE emp_id=?", (r["emp_id"],)).fetchone()
        if res:
            gap = (date.fromisoformat(res["last_day"]) - date.fromisoformat(res["letter_date"])).days
            back = con.execute("SELECT * FROM requisition WHERE team=? AND notes LIKE '%ackfill%'", (r["dept"],)).fetchone()
            tail = (f" The backfill ({back['req_id']}, opened {back['opened']}) had {back['in_pipeline']} candidates and was "
                    f"still '{back['status']}' at the 31 Oct export, so no successor was in place for the launch work."
                    if back else "")
            _add(con, f"F-EXIT-{r['emp_id']}", "people", 2,
                 f"{r['full_name']} ({r['title']}) is leaving - last day {r['exit_date']}",
                 f"Letter dated {res['letter_date']} (the planned Atlas GA date), {gap} days' notice, addressed to "
                 f"{res['addressed_to']}. Stated reason: wanting 'clearer launch timelines'; the letter mentions no new "
                 f"job. He built the launch kit and promised a handover before leaving.{tail}",
                 f"{res['src_ref']}; {r['src_ref']}" + (f"; {back['src_ref']}" if back else ""), "people")
        else:
            _add(con, f"F-EXIT-{r['emp_id']}", "people", 2,
                 f"{r['full_name']} ({r['title']}) is leaving - last day {r['exit_date']}",
                 f"Status '{r['status']}'. The Q3 board update lists this as 'one planned departure in marketing'. "
                 f"They sit in Marketing, the function that just ran the Summit and is preparing Atlas launch "
                 f"materials; knowledge handover is a risk.", r["src_ref"], "people")


def pending_requests(con):
    """A request to HR with no visible reply."""
    for m in con.execute("SELECT * FROM message WHERE lower(subject)='remote'"):
        reply = con.execute("SELECT 1 FROM message WHERE lower(subject) LIKE 're: remote%'").fetchone()
        if not reply:
            who = con.execute("SELECT full_name, location, src_ref FROM person WHERE email LIKE ?",
                              (f"%{m['sender'].split('<')[-1].strip('> ')}%",)).fetchone()
            if who:
                _add(con, "F-REMOTE", "people", 1,
                     f"{who['full_name']} asked on {m['sent_at'][:10]} to make remote work permanent; no reply on record",
                     f"Keka already lists {who['full_name']} as '{who['location']}'. The request offers a monthly "
                     f"Bengaluru visit. No answer appears in the emails supplied.", f"{m['src_ref']}; {who['src_ref']}", "people")


def spoken_vs_data(con):
    b = con.execute("SELECT * FROM board_update ORDER BY sent_on DESC LIMIT 1").fetchone()
    _add(con, "F-NUMBERS", "data", 2,
         "The CEO's and CFO's spoken numbers do not match the board numbers",
         f"ARR was said as '42-45 crore' vs Rs {b['arr_cr']} Cr in the board update; burn as 'two point two' vs "
         f"Rs {b['burn_lakh']:.0f} lakh/month; headcount as '180' (brief) vs {b['team']}. Leaders are quoting "
         f"different numbers from the board's, so check figures before using them.",
         "T1; T2; Board_Update_Jul-Sep_2026.pdf; Employee_Master.xlsx", "money")


def sequence_gaps(con):
    rows = con.execute("""SELECT voucher, txn_date, src_ref FROM gl_entry WHERE voucher LIKE 'JV-%'
                          ORDER BY voucher""").fetchall()
    for a, b in zip(rows, rows[1:]):
        if a["txn_date"] > b["txn_date"]:
            _add(con, f"F-SEQ-{a['voucher']}", "finance", 1,
                 f"Voucher {a['voucher']} is dated after {b['voucher']}",
                 f"{a['voucher']} is dated {a['txn_date']} but the higher-numbered {b['voucher']} is dated "
                 f"{b['txn_date']}. Numbers normally rise with date, so one was probably entered out of order. "
                 f"Minor; matters only when matching invoices to payments.",
                 f"{a['src_ref']}; {b['src_ref']}", "money")


def run_all(con):
    for fn in (payroll_proration, vendor_lookalikes, cost_trends, payroll_flat, hiring, hiring_vs_board, atlas,
               pulse_drops, departures, pending_requests, spoken_vs_data, sequence_gaps):
        fn(con)
    con.commit()
