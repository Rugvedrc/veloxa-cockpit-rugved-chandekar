"""Day 2 material: loaders, findings, the top-three screen (voice note T6a) and revision of Day 1 claims."""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
for _k in ("NVIDIA_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(_k, None)

from cockpit import agents, build, worry  # noqa: E402
from test_cockpit import data_room_available  # noqa: E402


@unittest.skipUnless(data_room_available(), "data room not found; pass --data to bootstrap.py or set VELOXA_DATA")
class Day2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = build.get_con("2026-11-17")

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    # --- loaders
    def test_row_counts(self):
        n = lambda t: self.con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        self.assertEqual((n("requisition"), n("leave"), n("pulse"), n("resignation")), (6, 19, 24, 1))

    def test_every_leave_row_and_approver_is_matched_to_a_person(self):
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM leave WHERE emp_id IS NULL OR approver_id IS NULL").fetchone()[0], 0)
        f = self.con.execute("SELECT p.full_name FROM leave l JOIN person p USING(emp_id) WHERE employee_raw='F. Sheikh'").fetchone()
        self.assertEqual(f[0], "Fatima Sheikh")

    def test_resignation_letter_parsed(self):
        r = self.con.execute("SELECT * FROM resignation").fetchone()
        self.assertEqual((r["emp_id"], r["letter_date"], r["last_day"]), ("VX013", "2026-09-15", "2026-10-31"))
        self.assertIn("clearer launch timelines", r["stated_reason"])

    def test_leave_totals_are_arithmetically_consistent(self):
        self.assertEqual(self.con.execute("SELECT SUM(days) FROM leave").fetchone()[0], 55.5)

    # --- findings
    def test_engineering_pulse_drop_found_at_team_level(self):
        f = self.con.execute("SELECT * FROM finding WHERE id='F-PULSE-ENGINEERING'").fetchone()
        self.assertEqual(f["severity"], 3)
        self.assertIn("3.9 -> 3.1", f["title"])
        self.assertIn("under 6", f["detail"])

    def test_hiring_finding_uses_tracker(self):
        f = self.con.execute("SELECT * FROM finding WHERE id='F-HIRE'").fetchone()
        self.assertIn("8 candidates", f["title"])
        self.assertIn("We'll absorb it", f["detail"])

    def test_board_pause_contradiction_found(self):
        f = self.con.execute("SELECT * FROM finding WHERE id='F-HIRE-BOARD'").fetchone()
        self.assertIn("REQ-016", f["detail"])
        self.assertIn("REQ-017", f["detail"])

    def test_payroll_finding_now_cites_marriage_leave(self):
        f = self.con.execute("SELECT * FROM finding WHERE id LIKE 'F-PAY-VX018%'").fetchone()
        self.assertIn("marriage leave", f["detail"])
        self.assertIn("Leave_Register", f["evidence"])

    def test_no_finding_names_an_individual_as_a_flight_risk(self):
        for f in self.con.execute("SELECT title, detail FROM finding"):
            text = (f["title"] + " " + f["detail"]).lower()
            for bad in ("flight risk", "priya", "p. nair", "half-day", "half day"):
                self.assertNotIn(bad, text)

    # --- claims
    def test_day2_claims_present_and_revise_day1(self):
        c28 = self.con.execute("SELECT * FROM claim WHERE id='C28'").fetchone()
        self.assertEqual((c28["revises"], c28["released_on"]), ("C12", "2026-11-17"))
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM claim WHERE id='C12'").fetchone()[0], 1)  # history kept
        self.assertEqual(self.con.execute("SELECT disagrees FROM claim WHERE id='C18'").fetchone()[0], 1)

    def test_vicky_alias_confidence_raised_but_history_kept(self):
        rows = self.con.execute("SELECT confidence FROM alias WHERE alias='Vicky' ORDER BY rowid").fetchall()
        self.assertEqual([r[0] for r in rows], ["L", "M"])

    # --- top three (voice note T6a)
    def test_top_three_shape_and_order(self):
        t = worry.top_three(self.con)
        self.assertEqual(len(t["themes"]), 3)
        self.assertEqual([x["rank"] for x in t["themes"]], [1, 2, 3])
        sev = [x["severity"] for x in t["themes"]]
        self.assertEqual(sev, sorted(sev, reverse=True))
        self.assertEqual(t["themes"][0]["theme"], "delivery")          # tie on severity -> the CEO's stated concern
        self.assertTrue(all(x["evidence"] for x in t["themes"]))
        self.assertIn("judgement", t["rule"])

    def test_top_three_names_no_individual_risk_and_is_json_serialisable(self):
        blob = json.dumps(worry.top_three(self.con)).lower()
        for bad in ("flight risk", "priya", "half-day"):
            self.assertNotIn(bad, blob)

    def test_top_three_is_stable(self):
        self.assertEqual(worry.top_three(self.con), worry.top_three(self.con))

    # --- agents with Day 2 facts
    def test_agent_facts_include_own_leave_and_not_others(self):
        agents._provider = lambda: (None, None)
        facts = " ".join(t for t, _ in agents.grounded_facts(self.con, "VX014"))
        self.assertIn("Marriage 2026-02-09 to 2026-02-27", facts)
        self.assertNotIn("Personal (half day", facts)  # that is another person's leave

    def test_resigning_agent_knows_the_letter(self):
        facts = " ".join(t for t, _ in agents.grounded_facts(self.con, "VX013"))
        self.assertIn("I resigned by letter dated 2026-09-15", facts)

    def test_agent_prompts_still_hold_no_pay_figures(self):
        gross = {str(r[0]) for r in self.con.execute("SELECT DISTINCT gross FROM payroll")}
        for emp in agents.PERSONAS:
            p = agents.system_prompt(self.con, emp)
            for g in gross:
                self.assertNotIn(g, p, emp)


if __name__ == "__main__":
    unittest.main()
