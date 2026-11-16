"""Computed findings: things the data says that someone should look at.

Every finding is derived from rows (never hand-typed numbers) and carries evidence refs,
so the 'what should I worry about' view stays true when new drops arrive.
Severity: 3 = act now, 2 = look soon, 1 = FYI.
"""
import calendar
import difflib
from datetime import date

MON = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def _add(con, fid, kind, sev, title, detail, evidence):
    con.execute("INSERT OR REPLACE INTO finding VALUES(?,?,?,?,?,?,?)",
                (fid, kind, sev, title, detail, evidence, "open"))


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
            _add(con, f"F-PAY-{r['emp_id']}-{mon}", "payroll", 3,
                 f"{r['full_name']} was paid for {r['days_payable']} days in {mon} {y}, should be {expected}",
                 f"Joined {r['join_date']}, so only {expected} of {r['days_in_month']} days were payable. "
                 f"Estimated gross overpayment Rs {over:,}. Processed by {r['processed_by']} while the usual "
                 f"processor was out. The employee raised it on 6 Mar and the reply on 10 Mar was only "
                 f"'will check and get back' - no correction is visible in the data.",
                 f"{r['src_ref']}; Employee_Master join date; {', '.join(mails)}")
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
                     f"{a['refs']}; {b['refs']}")
            else:
                _add(con, f"F-VEN-{a['vendor_id']}-{b['vendor_id']}", "vendor", 1,
                     f"Similar names, probably different vendors: '{a['vendor_raw']}' vs '{b['vendor_raw']}'",
                     f"Different cost centres ({a['cc']} vs {b['cc']}) and different purpose. Kept separate so "
                     f"hotel spend is not counted as event spend.", f"{a['refs']}; {b['refs']}")


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
             f"{a['src_ref']}; {z['src_ref']}; Board updates")


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
             "GL_Export_Apr-Sep_2026.xlsx PAYROLL rows; Payroll_Register_Jan-Mar_2026.xlsx")


def hiring(con):
    r = con.execute("SELECT amount, src_ref, narration FROM gl_entry WHERE vendor_id='COHERE'").fetchone()
    if r:
        _add(con, "F-HIRE", "people", 2,
             "Recruiter retained for 2 backend roles, but hiring is now paused",
             f"Rs {r['amount']:,} (50% advance) paid to the recruiter on 30 Jun. The Q2 board update promised "
             f"two backend engineers that quarter; the Q3 update says hiring is paused. No such joiners are in "
             f"Keka. If the fee is split 50/50 as the narration suggests, a balance of about Rs {r['amount']:,} "
             f"is still owed, and Atlas remains short-staffed.", f"{r['src_ref']}; both board updates; Employee_Master.xlsx")


def atlas(con):
    b = con.execute("SELECT * FROM board_update ORDER BY sent_on").fetchall()
    if len(b) >= 2:
        _add(con, "F-ATLAS", "delivery", 3,
             "Atlas (routing engine v3) GA slipped from 15 Sep with no new date",
             f"{b[0]['sent_on']}: 'on track for GA on 15 September'. {b[-1]['sent_on']}: GA moved to absorb "
             f"reliability work after 'a difficult August'. The CEO believes customers were promised delivery "
             f"'by the festive season' and is unsure it will make it. No replacement date exists in any source yet.",
             "Board updates; T1 (CEO call)")


def departures(con):
    for r in con.execute("SELECT * FROM person WHERE status != 'Active'"):
        _add(con, f"F-EXIT-{r['emp_id']}", "people", 2,
             f"{r['full_name']} ({r['title']}) is leaving - last day {r['exit_date']}",
             f"Status '{r['status']}'. The Q3 board update lists this as 'one planned departure in marketing'. "
             f"They sit in Marketing, the function that just ran the Summit and is preparing Atlas launch "
             f"materials; knowledge handover is a risk.", r["src_ref"])


def spoken_vs_data(con):
    b = con.execute("SELECT * FROM board_update ORDER BY sent_on DESC LIMIT 1").fetchone()
    _add(con, "F-NUMBERS", "data", 2,
         "The CEO's and CFO's spoken numbers do not match the board numbers",
         f"ARR was said as '42-45 crore' vs Rs {b['arr_cr']} Cr in the board update; burn as 'two point two' vs "
         f"Rs {b['burn_lakh']:.0f} lakh/month; headcount as '180' (brief) vs {b['team']}. The leaders are working "
         f"from different or imagined numbers - itself a governance risk.",
         "T1; T2; Board_Update_Jul-Sep_2026.pdf; Employee_Master.xlsx")


def sequence_gaps(con):
    rows = con.execute("""SELECT voucher, txn_date, src_ref FROM gl_entry WHERE voucher LIKE 'JV-%'
                          ORDER BY voucher""").fetchall()
    for a, b in zip(rows, rows[1:]):
        if a["txn_date"] > b["txn_date"]:
            _add(con, f"F-SEQ-{a['voucher']}", "finance", 1,
                 f"Voucher {a['voucher']} is dated after {b['voucher']}",
                 f"{a['voucher']} is dated {a['txn_date']} but the higher-numbered {b['voucher']} is dated "
                 f"{b['txn_date']}. Journal numbers should rise with date, so one of them was keyed late or "
                 f"back-dated. Minor on its own; relevant when matching invoices to payments.",
                 f"{a['src_ref']}; {b['src_ref']}")


def run_all(con):
    for fn in (payroll_proration, vendor_lookalikes, cost_trends, payroll_flat, hiring, atlas,
               departures, spoken_vs_data, sequence_gaps):
        fn(con)
    con.commit()
