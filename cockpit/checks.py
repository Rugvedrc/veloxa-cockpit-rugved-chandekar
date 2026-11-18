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
from datetime import date, timedelta

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
            pm = con.execute("SELECT src_ref, cc FROM message WHERE subject LIKE '%Pausing%' ORDER BY sent_at").fetchall()
            mails = [m["src_ref"] for m in pm]
            roles = ", ".join(f"{r['req_id']} {r['role']}" for r in held)
            cancelled = "; ".join(r["notes"] for r in held if r["notes"])
            cc = next((m["cc"] for m in pm if m["cc"]), None)
            copied = f" The CEO and the Talent Partner were copied on the pause." if cc and "ananya" in cc.lower() else ""
            _add(con, "F-HIRE", "people", 3 if cand >= 6 else 2,
                 f"{len(held)} backend roles on hold since {held[0]['status_date']} with {cand} candidates waiting",
                 f"{roles}, opened {held[0]['opened']}. The CFO paused them 'until the round closes' to protect burn "
                 f"and the VP Engineering replied 'We'll absorb it'.{copied} Tracker note: {cancelled}. The recruiter was already "
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


EXPORT_DATE = date(2026, 10, 31)  # data_room/README.txt: "Exported by IT on 31 Oct 2026"


def _ver(con):
    return con.execute("SELECT * FROM jira_version ORDER BY last_changed DESC LIMIT 1").fetchone()


def atlas(con):
    b = con.execute("SELECT * FROM board_update ORDER BY sent_on").fetchall()
    if len(b) < 2:
        return
    v = _ver(con)
    if not v:  # Day 1-2: only the board and the CEO's call
        _add(con, "F-ATLAS", "delivery", 3,
             "Atlas (routing engine v3) GA slipped from 15 Sep with no new date",
             f"{b[0]['sent_on']}: 'on track for GA on 15 September'. {b[-1]['sent_on']}: GA moved to absorb "
             f"reliability work after 'a difficult August'. The CEO believes customers were promised delivery "
             f"'by the festive season' and is unsure it will make it. No replacement date exists in any source yet.",
             "Board updates; T1 (CEO call)", "delivery")
        return
    new, old = date.fromisoformat(v["release_date"]), date.fromisoformat(v["original_release_date"])
    weeks = (new - old).days // 7
    plan = con.execute("SELECT src_ref FROM message WHERE subject='Atlas plan'").fetchone()
    pause = con.execute("SELECT src_ref, cc FROM message WHERE subject LIKE '%Pausing two reqs' ORDER BY sent_at LIMIT 1").fetchone()
    dep = (" Vikram's 2 Jun plan to the CEO made the date conditional on 'the two backend hires land by July'; those roles opened on "
           "18 May and were paused on 12 Aug with the CEO copied." if plan and pause else "")
    ev = [v["src_ref"], b[0]["src_ref"], b[-1]["src_ref"], "T1"] + ([plan["src_ref"], pause["src_ref"]] if plan and pause else [])
    _add(con, "F-ATLAS", "delivery", 3,
         f"Atlas GA slipped from {old.strftime('%d %b')} to {new.strftime('%d %b %Y')} ({weeks} weeks)",
         f"Jira's release date for Atlas GA was changed on {v['last_changed']} by '{v['changed_by']}' from {v['original_release_date']} to "
         f"{v['release_date']}. The board saw 'on track' on {b[0]['sent_on']} and 'moved GA' on {b[-1]['sent_on']} without a new date. "
         f"The CEO believes customers were promised delivery 'by the festive season'; mid-December is after any reading of that.{dep}",
         "; ".join(ev), "delivery")


def jira_stats(con):
    """Totals, pace and the pace needed to reach the Jira GA date. None if Jira is not loaded (yet)."""
    v = _ver(con)
    issues = con.execute("SELECT * FROM jira_issue").fetchall()
    if not v or not issues:
        return None
    done = [i for i in issues if i["status"] == "Done"]
    open_ = [i for i in issues if i["status"] != "Done"]
    rem = sum(i["points"] for i in open_)
    ga = date.fromisoformat(v["release_date"])
    win = date(2026, 7, 1)
    pace = sum(i["points"] for i in done if i["resolved"] >= win.isoformat()) / ((EXPORT_DATE - win).days / 7)
    return {"v": v, "issues": issues, "done": done, "open": open_, "tot": sum(i["points"] for i in issues), "rem": rem,
            "done_pts": sum(i["points"] for i in done), "last": max(i["resolved"] for i in done), "ga": ga, "pace": pace,
            "need": rem / max((ga - EXPORT_DATE).days / 7, 0.1), "weeks_at_pace": rem / pace if pace else None}


def atlas_burn(con):
    """Is the remaining Jira work plausible by the GA date at the pace actually achieved?"""
    s = jira_stats(con)
    if not s:
        return
    v, issues, done, open_, tot, rem, last, ga, pace, need = (s[k] for k in ("v", "issues", "done", "open", "tot", "rem", "last", "ga", "pace", "need"))
    day_after = (date.fromisoformat(last) + timedelta(days=1)).isoformat()
    gitn = con.execute("SELECT COUNT(*) FROM git_commit WHERE committed_ist >= ?", (f"{day_after}T00:00:00",)).fetchone()[0]
    after_last = sum(1 for i in done if i["resolved"] > last)
    oct_done = sum(1 for i in done if i["resolved"] >= "2026-10-01")
    # the epic with the smallest share of its points done
    shares = []
    for e in con.execute("SELECT * FROM jira_epic"):
        pts = [(i["points"], i["status"] == "Done") for i in issues if i["epic_key"] == e["key"]]
        if pts:
            shares.append((sum(p for p, d in pts if d) / sum(p for p, _ in pts), e["key"], e["name"]))
    least = min(shares) if shares else None
    _add(con, "F-ATLAS-BURN", "delivery", 3,
         f"{rem} of {tot} Atlas story points are still open and nothing has been resolved since {last}",
         f"{len(open_)} of {len(issues)} tickets are open ({sum(1 for i in open_ if i['status'] == 'In Progress')} in progress). Finishing "
         f"{rem} points by {ga.isoformat()} needs about {need:.0f} points a week; the pace since 1 Jul was about {pace:.1f} a week "
         f"and {'none were' if oct_done == 0 else str(oct_done) + ' were'} resolved in October. At the July-October pace the remaining work "
         f"would take roughly {rem / pace:.0f} weeks. Caveat: {gitn} commits landed after {last} but commit messages carry no ticket key, "
         f"so work and tickets cannot be matched; Jira may simply be stale."
         + (f" Least finished epic: {least[2]} ({least[1]}), {least[0] * 100:.0f}% of its points done." if least else ""),
         f"{issues[0]['src_ref'].rsplit('!R', 1)[0]}; {v['src_ref']}; git_log.csv", "delivery")
    if gitn > 50 and after_last == 0:
        octc = con.execute("SELECT COUNT(*) FROM git_commit WHERE committed_ist >= '2026-10-01'").fetchone()[0]
        _add(con, "F-JIRA-STALE", "delivery", 2,
             f"Jira and git disagree: {gitn} commits since the last ticket was closed ({last})",
             f"Code kept moving ({octc} commits in October) while no ticket was resolved. Either tickets are not being closed or the "
             f"work is not being tracked, so neither source alone says how close Atlas is.",
             f"{issues[0]['src_ref'].rsplit('!R', 1)[0]}; git_log.csv", "delivery")


def key_person(con):
    """Concentration of Atlas work. About how work is spread, not about anyone's intentions."""
    issues = con.execute("SELECT * FROM jira_issue WHERE emp_id IS NOT NULL").fetchall()
    commits = con.execute("SELECT * FROM git_commit WHERE emp_id IS NOT NULL").fetchall()
    if not issues or not commits:
        return
    pts, open_pts = {}, {}
    for i in issues:
        pts[i["emp_id"]] = pts.get(i["emp_id"], 0) + i["points"]
        if i["status"] != "Done":
            open_pts[i["emp_id"]] = open_pts.get(i["emp_id"], 0) + i["points"]
    top = max(pts, key=pts.get)
    share = pts[top] / sum(pts.values())
    if share < 0.4:
        return
    p = con.execute("SELECT full_name, title FROM person WHERE emp_id=?", (top,)).fetchone()
    mine = [c for c in commits if c["emp_id"] == top]
    eng = [c for c in commits if c["repo"] == "atlas-engine"]
    ids = sorted({c["author_email"] for c in mine})
    late = lambda c: int(c["committed_ist"][11:13]) >= 22 or int(c["committed_ist"][11:13]) < 6
    mine_late = [c for c in mine if late(c)]
    others_late = sum(1 for c in commits if c["emp_id"] != top and late(c))
    first_late = min((c["committed_ist"][:7] for c in mine_late), default=None)
    since = [c for c in mine if c["committed_ist"] >= "2026-07-01"]
    wk = sum(1 for c in since if date.fromisoformat(c["committed_ist"][:10]).weekday() >= 5)
    after_first = [c for c in mine if first_late and c["committed_ist"][:7] >= first_late]
    mail = con.execute("SELECT src_ref, sent_at FROM message WHERE subject LIKE 'time this week%'").fetchone()
    tail = f" Her 1 Sep email asking to talk about 'Atlas ownership' was sent at {mail['sent_at'][11:16]}." if mail else ""
    pct = lambda a, b: f"{a * 100 / b:.0f}%"
    _add(con, "F-KEYPERSON", "people", 3,
         f"Atlas depends on one engineer: {p['full_name']} owns {share * 100:.0f}% of its story points",
         f"{p['full_name']} ({p['title']}) owns {pts[top]} of {sum(pts.values())} Atlas points and {open_pts.get(top, 0)} of the "
         f"{sum(open_pts.values())} still open, and made {len(mine)} of {len(commits):,} commits ({pct(len(mine), len(commits))}; "
         f"{pct(sum(1 for c in mine if c['repo'] == 'atlas-engine'), len(eng))} of atlas-engine), counting her {len(ids)} git identities as one. "
         f"After-hours commits (22:00-06:00 IST) appear only for her: none before {first_late or 'n/a'}, then {len(mine_late)} of "
         f"her {len(after_first)} commits from then on; {pct(wk, len(since)) if since else 'n/a'} of her commits since July are on "
         f"weekends. Everyone else made {others_late} after-hours commits.{tail} "
         f"This is about how the work is spread, not about anyone's plans.",
         "Jira_Export_ATLAS.xlsx!Issues; git_log.csv" + (f"; {mail['src_ref']}" if mail else ""), "people")


def git_identities(con):
    rows = con.execute("""SELECT emp_id, COUNT(DISTINCT author_email) n, GROUP_CONCAT(DISTINCT author_email) emails, COUNT(*) c
                          FROM git_commit WHERE emp_id IS NOT NULL GROUP BY emp_id HAVING n > 1""").fetchall()
    for r in rows:
        p = con.execute("SELECT full_name FROM person WHERE emp_id=?", (r["emp_id"],)).fetchone()
        per = con.execute("SELECT author_email, COUNT(*) c FROM git_commit WHERE emp_id=? GROUP BY author_email", (r["emp_id"],)).fetchall()
        _add(con, f"F-GITID-{r['emp_id']}", "data", 1,
             f"{p['full_name']} commits under {r['n']} identities; counted as one person",
             "Counted separately they would be " + " and ".join(f"{x['c']}" for x in per) + f" commits ({r['c']} together), and the second "
             "address would look like another engineer. Merged on evidence: a no-reply form of the same name, the same repo and dates, "
             "the same hours, no overlap within a minute. Medium-high confidence (ASSUMPTIONS A-31).", "git_log.csv", "delivery")


def oncall_load(con):
    weeks = con.execute("SELECT * FROM oncall").fetchall()
    inc = con.execute("SELECT * FROM incident").fetchall()
    if not weeks:
        return
    count = {}
    for w in weeks:
        for k in {w["primary_id"], w["secondary_id"]} - {None}:
            count[k] = count.get(k, 0) + 1
    emp = {k: v for k, v in count.items() if con.execute("SELECT 1 FROM person WHERE emp_id=?", (k,)).fetchone()}
    if not emp:
        return
    top = max(emp, key=emp.get)
    if emp[top] < 0.9 * len(weeks):
        return
    p = con.execute("SELECT full_name, title FROM person WHERE emp_id=?", (top,)).fetchone()
    prim = sum(1 for w in weeks if w["primary_id"] == top)
    mine = [i for i in inc if i["responder_id"] == top]
    sev1 = [i for i in mine if i["severity"] == "SEV1"]
    night = lambda i: int(i["opened_ist"][11:13]) >= 22 or int(i["opened_ist"][11:13]) < 6
    hard = con.execute("SELECT COUNT(*) n, SUM(status='Done') d FROM jira_issue WHERE epic_key='ATLAS-5' AND emp_id=?", (top,)).fetchone()
    contractor = con.execute("SELECT c.name, i.base, i.tax FROM contractor c LEFT JOIN invoice i ON i.vendor_id=c.vendor_id LIMIT 1").fetchone()
    ctext = (f" A contractor, {contractor['name']}, joined the rota in mid-August"
             + (f" at Rs {contractor['base']:,} a month plus GST" if contractor["base"] else "") + "; the two backend roles that would have added capacity stayed frozen.") if contractor else ""
    _add(con, "F-ONCALL", "people", 2,
         f"{p['full_name']} was on call in all {len(weeks)} rota weeks ({prim} as primary) and handled every SEV1",
         f"{p['full_name']} ({p['title']}) handled {len(sev1)} SEV1s ({sum(i['hours'] for i in sev1):.1f} hours of incident time, "
         f"{sum(1 for i in sev1 if night(i))} starting at night IST) and {len(mine)} of {len(inc)} incidents overall. Her own Atlas hardening tickets: "
         f"{hard['d'] or 0} of {hard['n']} done. On 24 Aug she wrote that she was pausing the Atlas perf tickets to stabilise routing-api.{ctext}",
         "OnCall_Rota.xlsx; Incidents_Aug-Oct_2026.xlsx; 08.eml; Jira_Export_ATLAS.xlsx!Issues", "people")


def launch_kit(con):
    rows = con.execute("SELECT * FROM launch_kit").fetchall()
    v = _ver(con)
    if not rows:
        return
    asset = {r["asset"]: r["status"] for r in rows}
    owner = con.execute("SELECT * FROM person WHERE emp_id=?", (rows[0]["owner_id"],)).fetchone()
    back = con.execute("SELECT * FROM requisition WHERE notes LIKE '%ackfill%'").fetchone()
    planned = None
    for r in rows:
        if r["asset"] == "Launch date":
            import re
            m = re.search(r"planned (\d{1,2}) (\w{3})", r["status"])
            if m:
                planned = date(int(r["dated"][:4]), {mm: i for i, mm in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}[m.group(2)], int(m.group(1)))
    gap = f" Jira now has GA on {v['release_date']}, {(date.fromisoformat(v['release_date']) - planned).days // 7} weeks after that." if v and planned else ""
    left = (f" Its owner, {owner['full_name']}, was due to leave on {owner['exit_date']} (status: {owner['status'].lower()})"
            + (f"; the backfill {back['req_id']} was still '{back['status']}'." if back else ".")) if owner and owner["exit_date"] else ""
    pend = [a for a, s in asset.items() if s.lower().startswith("draft")]
    _add(con, "F-LAUNCHKIT", "delivery", 2,
         "The Atlas launch kit is stale: only v1 exists, the press note is a draft and its launch date predates the slip",
         f"Kit {rows[0]['version']} is dated {rows[0]['dated']}. Deck, website page (unpublished) and the 3-email sequence are 'Ready'; "
         f"{', '.join(pend) or 'nothing'} is still draft; the launch date was 'planned {planned.strftime('%d %b') if planned else '?'}'.{gap}{left} "
         f"Marketing's account ('ready since July, just waiting on engineering') is true of the assets, not of the plan.",
         f"{rows[0]['src_ref']}; 05.eml" + (f"; {v['src_ref']}" if v else "") + (f"; {back['src_ref']}" if back else ""), "delivery")


def contractor_invoice(con):
    inv = con.execute("SELECT * FROM invoice").fetchone()
    if not inv:
        return
    gl = con.execute("SELECT * FROM gl_entry WHERE vendor_id=? ORDER BY txn_date", (inv["vendor_id"],)).fetchall()
    last_gl = max((g["txn_date"] for g in con.execute("SELECT txn_date FROM gl_entry")), default=None)
    pro = [g for g in gl if "18-31 Aug" in (g["narration"] or "")]
    parts = []
    if inv["invoice_date"] > (last_gl or ""):
        parts.append(f"{inv['invoice_no']} (dated {inv['invoice_date']}, Rs {inv['total']:,} incl. IGST) is for September but is not in the "
                     f"ledger export, which ends {last_gl}; unless it was accrued, September engineering-ops cost is understated by that amount.")
    if pro:
        booked = pro[0]["amount"]
        base = round(booked / 1.18)
        fair = round(inv["base"] * 14 / 31)
        parts.append(f"{pro[0]['ref']} for 14 days (18-31 Aug) was booked at Rs {booked:,}, i.e. Rs {base:,} before 18% GST. Pro-rating the "
                     f"Rs {inv['base']:,} retainer by calendar days gives Rs {fair:,}; Rs {base:,} equals exactly half a month, so a 28-day basis was "
                     f"used. Up to Rs {round((base - fair) * 1.18):,} more than a calendar-day basis, if that is the contract basis (unknown).")
    parts.append("IGST at 18% is correct: the supplier's GSTIN state code is 27 (Maharashtra) and the place of supply is Karnataka, an inter-state sale.")
    _add(con, "F-INVOICE", "finance", 1, "Contractor invoices: September is not in the ledger, and the August pro-rata may be high",
         " ".join(parts), f"{inv['src_ref']}; " + "; ".join(g["src_ref"] for g in gl), "money")


def reorg_pending(con):
    for r in con.execute("""SELECT l.*, p.full_name, p.title, m.full_name mgr FROM reporting_line l JOIN person p USING(emp_id)
                            LEFT JOIN person m ON m.emp_id = (SELECT manager_id FROM reporting_line c WHERE c.emp_id=l.emp_id AND c.status='current')
                            WHERE l.status='planned'"""):
        has_role = con.execute("SELECT COUNT(*) FROM person WHERE title LIKE '%' || ? || '%' OR title LIKE '%Chief Revenue%'",
                               (r["manager_title"] or "~",)).fetchone()[0]
        req = con.execute("SELECT COUNT(*) FROM requisition WHERE role LIKE '%' || ? || '%' OR role LIKE '%Chief Revenue%'",
                          (r["manager_title"] or "~",)).fetchone()[0]
        _add(con, f"F-ORG-{r['emp_id']}", "people", 1,
             f"{r['full_name']}'s team is due to report to a {r['manager_title']} who does not exist in the records yet",
             f"{r['note']} Today Keka shows {r['full_name']} ({r['title']}) reporting to {r['mgr'] or 'no one'}. "
             f"{'No such role is on the payroll' if not has_role else 'A matching role exists'}; "
             f"{'no matching requisition is in the hiring tracker' if not req else 'a matching requisition exists'}. "
             f"Treated as a planned change, not a fact.", r["source"], "people")


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
            draft = con.execute("SELECT asset FROM launch_kit WHERE owner_id=? AND lower(status) LIKE 'draft%'", (r["emp_id"],)).fetchall()
            kit = f" The kit he owns still has a draft ({', '.join(d['asset'] for d in draft)})." if draft else ""
            _add(con, f"F-EXIT-{r['emp_id']}", "people", 2,
                 f"{r['full_name']} ({r['title']}) is leaving - last day {r['exit_date']}",
                 f"Letter dated {res['letter_date']} (the planned Atlas GA date), {gap} days' notice, addressed to "
                 f"{res['addressed_to']}. Stated reason: wanting 'clearer launch timelines'; the letter mentions no new "
                 f"job. He built the launch kit and promised a handover before leaving.{kit}{tail}",
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
    mk = con.execute("SELECT 1 FROM claim WHERE id='C30'").fetchone()
    extra = (" Marketing's total of 'one point eight' (unit not stated) does not fit the ledger's Rs 14.27 lakh for marketing "
             "under any simple reading.") if mk else ""
    _add(con, "F-NUMBERS", "data", 2,
         "The CEO's and CFO's spoken numbers do not match the board numbers" if not mk else
         "Leaders' spoken numbers (ARR, burn, headcount, marketing spend) do not match the records",
         f"ARR was said as '42-45 crore' vs Rs {b['arr_cr']} Cr in the board update; burn as 'two point two' vs "
         f"Rs {b['burn_lakh']:.0f} lakh/month; headcount as '180' (brief) vs {b['team']}.{extra} Leaders are quoting "
         f"different numbers from the records, so check figures before using them.",
         "T1; T2; Board_Update_Jul-Sep_2026.pdf; Employee_Master.xlsx" + ("; T4; GL_Export_Apr-Sep_2026.xlsx" if mk else ""), "money")


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
    for fn in (payroll_proration, vendor_lookalikes, cost_trends, payroll_flat, hiring, hiring_vs_board, atlas, atlas_burn,
               key_person, git_identities, oncall_load, launch_kit, contractor_invoice, pulse_drops, departures,
               pending_requests, reorg_pending, spoken_vs_data, sequence_gaps):
        fn(con)
    con.commit()
