"""Day 3 material: engineering exports, invoice, launch kit, identity resolution, findings, planned org change.

Where possible the expected numbers are recomputed from the raw files here, not copied from the database,
so a loader bug cannot agree with itself.
"""
import csv
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
for _k in ("NVIDIA_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(_k, None)

import openpyxl  # noqa: E402

from cockpit import agents, build, db, org, worry  # noqa: E402
from test_cockpit import data_room_available  # noqa: E402


def raw(name):
    return next(db.data_dir().glob(f"Day3*/data_room/engineering/{name}"))


@unittest.skipUnless(data_room_available(), "data room not found; pass --data to bootstrap.py or set VELOXA_DATA")
class Day3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        agents._provider = lambda: (None, None)
        cls.con = build.get_con("2026-11-18")

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def one(self, sql, *a):
        return self.con.execute(sql, a).fetchone()[0]

    # ---- loaders, checked against the raw files
    def test_git_row_count_matches_csv(self):
        with open(raw("git_log.csv"), encoding="utf8") as f:
            self.assertEqual(self.one("SELECT COUNT(*) FROM git_commit"), sum(1 for _ in csv.DictReader(f)))

    def test_jira_totals_match_the_workbook(self):
        ws = openpyxl.load_workbook(raw("Jira_Export_ATLAS.xlsx"), data_only=True)["Issues"]
        rows = [r for r in ws.iter_rows(min_row=4, values_only=True) if r[0]]
        self.assertEqual(self.one("SELECT COUNT(*) FROM jira_issue"), len(rows))
        self.assertEqual(self.one("SELECT SUM(points) FROM jira_issue"), sum(r[5] for r in rows))
        self.assertEqual(self.one("SELECT SUM(points) FROM jira_issue WHERE status!='Done'"), sum(r[5] for r in rows if r[6] != "Done"))

    def test_incident_times_are_converted_from_utc_to_ist(self):
        r = self.con.execute("SELECT * FROM incident WHERE id='INC-205'").fetchone()
        self.assertTrue(r["opened_utc"].startswith("2026-08-22T20:41"))
        self.assertTrue(r["opened_ist"].startswith("2026-08-23T02:11"))   # +5:30 crosses midnight
        self.assertAlmostEqual(r["hours"], 5.57, places=1)

    def test_invoice_arithmetic_and_vendor_link(self):
        i = self.con.execute("SELECT * FROM invoice").fetchone()
        self.assertEqual((i["base"], i["tax"], i["total"]), (120000, 21600, 141600))
        self.assertEqual(i["base"] * 118 // 100, i["total"])
        self.assertEqual(i["vendor_id"], "PATIL")

    def test_launch_kit_parsed(self):
        kit = {r["asset"]: r["status"] for r in self.con.execute("SELECT * FROM launch_kit")}
        self.assertEqual(kit["Press note"], "Draft")
        self.assertIn("planned 22 Sep", kit["Launch date"])
        self.assertEqual(self.one("SELECT owner_id FROM launch_kit LIMIT 1"), "VX013")

    def test_email_cc_is_captured_and_the_printout_matches_the_eml_files(self):
        cc = self.one("SELECT cc FROM message WHERE subject LIKE '%Pausing two reqs'")
        self.assertIn("ananya@veloxa.in", cc)
        self.assertIn("rohan@veloxa.in", cc)
        self.assertIn("11 of 11 threads identical", self.one("SELECT note FROM source WHERE name='Email_Printouts.pdf'"))

    # ---- identity resolution
    def test_every_engineering_record_is_linked_to_someone(self):
        for sql in ("SELECT COUNT(*) FROM git_commit WHERE emp_id IS NULL", "SELECT COUNT(*) FROM jira_issue WHERE emp_id IS NULL",
                    "SELECT COUNT(*) FROM incident WHERE responder_id IS NULL", "SELECT COUNT(*) FROM oncall WHERE primary_id IS NULL OR secondary_id IS NULL"):
            self.assertEqual(self.one(sql), 0, sql)

    def test_priyas_two_git_identities_are_one_person(self):
        self.assertEqual(self.one("SELECT COUNT(*) FROM git_commit WHERE emp_id='VX007'"), 588)
        self.assertEqual(self.one("SELECT COUNT(DISTINCT author_email) FROM git_commit WHERE emp_id='VX007'"), 2)
        self.assertEqual(self.one("SELECT COUNT(*) FROM git_commit WHERE author_email='pnair@users.noreply.github.com'"), 163)

    def test_snehal_is_the_contractor_and_sneha_is_the_employee(self):
        self.assertEqual(self.one("SELECT responder_id FROM incident WHERE responder_raw='Snehal' LIMIT 1"), "X001")
        self.assertEqual(self.one("SELECT responder_id FROM incident WHERE responder_raw='Sneha' LIMIT 1"), "VX012")
        self.assertEqual(self.one("SELECT COUNT(*) FROM person WHERE full_name LIKE 'Snehal%'"), 0)
        self.assertEqual(self.one("SELECT COUNT(*) FROM oncall WHERE primary_raw='Sneha' OR secondary_raw='Sneha'"), 17)

    def test_jira_initials_resolve_to_the_plan_owners(self):
        got = {r[0]: r[1] for r in self.con.execute("SELECT DISTINCT assignee_raw, emp_id FROM jira_issue")}
        self.assertEqual(got, {"PN": "VX007", "RV": "VX018", "AD": "VX009", "SK": "VX012"})

    # ---- findings
    def test_atlas_date_slip_found_from_jira(self):
        f = self.con.execute("SELECT * FROM finding WHERE id='F-ATLAS'").fetchone()
        self.assertIn("15 Sep to 15 Dec 2026 (13 weeks)", f["title"])
        self.assertIn("04.eml", f["evidence"])
        self.assertIn("06.eml", f["evidence"])

    def test_remaining_work_finding_numbers(self):
        f = self.con.execute("SELECT * FROM finding WHERE id='F-ATLAS-BURN'").fetchone()
        self.assertIn("115 of 233", f["title"])
        self.assertIn("2026-09-17", f["title"])
        self.assertIn("Jira may simply be stale", f["detail"])  # the honest caveat travels with the claim

    def test_concentration_and_oncall_findings(self):
        k = self.con.execute("SELECT * FROM finding WHERE id='F-KEYPERSON'").fetchone()
        self.assertIn("56%", k["title"])
        self.assertIn("588 of 1,453", k["detail"])
        self.assertIn("Everyone else made 0 after-hours commits", k["detail"])
        o = self.con.execute("SELECT * FROM finding WHERE id='F-ONCALL'").fetchone()
        self.assertIn("all 17 rota weeks (11 as primary)", o["title"])
        self.assertIn("0 of 4 done", o["detail"])

    def test_launch_kit_finding(self):
        f = self.con.execute("SELECT * FROM finding WHERE id='F-LAUNCHKIT'").fetchone()
        self.assertIn("12 weeks", f["detail"])
        self.assertIn("REQ-016", f["detail"])

    def test_invoice_finding_has_both_issues_and_the_correct_tax_note(self):
        f = self.con.execute("SELECT * FROM finding WHERE id='F-INVOICE'").fetchone()
        self.assertIn("not in the ledger", f["detail"])
        self.assertIn("IGST at 18% is correct", f["detail"])

    def test_workload_findings_never_speculate_about_intent_or_health(self):
        for fid in ("F-KEYPERSON", "F-ONCALL", "F-JIRA-STALE"):
            text = " ".join(self.con.execute("SELECT title, detail FROM finding WHERE id=?", (fid,)).fetchone()).lower()
            for bad in ("flight risk", "quit", "resign", "will leave", "burn out", "burnout", "exhaust", "unhappy", "stress"):
                self.assertNotIn(bad, text, fid)

    # ---- claims
    def test_claims_conflicts_and_revisions(self):
        c = lambda i: self.con.execute("SELECT * FROM claim WHERE id=?", (i,)).fetchone()
        self.assertEqual((c("C40")["revises"], c("C40")["disagrees"]), ("C13", 1))
        self.assertEqual(c("C45")["revises"], "C28")
        self.assertEqual(c("C52")["revises"], "C28")
        self.assertEqual((c("C30")["revises"], c("C30")["disagrees"]), ("C15", 1))
        self.assertEqual(self.one("SELECT COUNT(*) FROM claim WHERE id IN ('C13','C15','C28')"), 3)  # history kept

    # ---- org: current vs planned
    def test_current_lines_come_from_keka_and_planned_lines_are_separate(self):
        m = org.manager_of(self.con, "VX006")
        self.assertEqual(m["current"]["emp_id"], "VX001")
        self.assertEqual(len(m["planned"]), 1)
        self.assertIsNone(m["planned"][0]["manager_id"])           # nobody named
        self.assertEqual(m["planned"][0]["manager_title"], "CRO")
        self.assertEqual(sorted(r["emp_id"] for r in org.reports_of(self.con, "VX004")), ["VX007", "VX009", "VX012", "VX018"])

    def test_planned_change_is_flagged_as_not_a_fact_in_answers(self):
        r = build.answer("Who does Nikhil report to?", "2026-11-18")
        self.assertIn("Ananya Rao", r["answer"])
        self.assertIn("not yet in Keka", r["answer"])
        self.assertTrue(any("never as fact" in c for c in r["caveats"]))

    # ---- top three on Day 3
    def test_top_three_on_day3(self):
        t = worry.top_three(self.con)
        self.assertEqual(t["themes"][0]["theme"], "delivery")
        self.assertIn("15 Dec", t["themes"][0]["headline"])
        self.assertEqual(len(t["themes"]), 3)
        blob = str(t).lower()
        for bad in ("flight risk", "quit", "resign ", "half-day", "burn out", "burnout"):
            self.assertNotIn(bad, blob)

    # ---- point in time
    def test_day2_database_knows_nothing_of_day3(self):
        d2 = build.get_con("2026-11-17")
        try:
            for t in ("git_commit", "incident", "oncall", "jira_issue", "invoice", "launch_kit", "contractor"):
                self.assertEqual(d2.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0], 0, t)
            self.assertEqual(d2.execute("SELECT COUNT(*) FROM claim WHERE released_on > '2026-11-17'").fetchone()[0], 0)
            self.assertEqual(d2.execute("SELECT COUNT(*) FROM alias WHERE alias IN ('Ayesha','PN','Snehal')").fetchone()[0], 0)
            self.assertEqual(d2.execute("SELECT COUNT(*) FROM finding WHERE id IN ('F-KEYPERSON','F-ONCALL','F-ATLAS-BURN','F-LAUNCHKIT')").fetchone()[0], 0)
            self.assertNotIn("15 Dec", d2.execute("SELECT title FROM finding WHERE id='F-ATLAS'").fetchone()[0])
            self.assertNotIn("jira", agents.persona(d2, "VX007")["worries"].lower())
        finally:
            d2.close()

    # ---- agents
    def test_agents_know_their_own_engineering_work_only(self):
        mine = " ".join(t for t, _ in agents.grounded_facts(self.con, "VX012"))
        self.assertIn("4 tickets, 18 story points, 0 done", mine)
        self.assertIn("17 of 17 weeks", mine)
        other = " ".join(t for t, _ in agents.grounded_facts(self.con, "VX014"))  # Fatima, Finance
        self.assertNotIn("Jira", other.replace("Jira has", ""))

    def test_no_agent_prompt_contains_pay_after_day3(self):
        gross = {str(r[0]) for r in self.con.execute("SELECT DISTINCT gross FROM payroll")}
        for emp in agents.PERSONAS:
            prompt = agents.system_prompt(self.con, emp)
            for g in gross:
                self.assertNotIn(g, prompt, emp)


if __name__ == "__main__":
    unittest.main()
