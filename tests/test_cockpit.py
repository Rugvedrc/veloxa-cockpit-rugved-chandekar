"""Behaviour tests for the data model, findings, point-in-time gating and the agents.
The question/answer set lives in questions.json (see test_questions.py).
Run everything:  python -m unittest discover tests     (or: python cockpit.py test)
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

for _k in ("NVIDIA_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY"):  # tests never call an LLM
    os.environ.pop(_k, None)

from cockpit import agents, build, db  # noqa: E402
from cockpit.ask import ask  # noqa: E402
from cockpit.resolve import find_person  # noqa: E402


def data_room_available():
    try:
        db.data_dir()
        return True
    except FileNotFoundError:
        return False


@unittest.skipUnless(data_room_available(), "data room not found; pass --data to bootstrap.py or set VELOXA_DATA")
class CockpitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        agents._provider = lambda: (None, None)  # force offline mode even if a key appears later
        cls.con = build.get_con("2026-11-16")

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    # --- model and findings
    def test_headcount_is_19_not_180(self):
        r = ask(self.con, "How many people work here?")
        self.assertIn("19 people", r["answer"])
        self.assertTrue(any("180" in c for c in r["caveats"]))

    def test_rahul_overpayment_found_with_amount(self):
        f = self.con.execute("SELECT * FROM finding WHERE id LIKE 'F-PAY-VX018-%'").fetchone()
        self.assertIsNotNone(f)
        self.assertIn("7,857", f["detail"])

    def test_payroll_total_matches_register_sum(self):
        mar = self.con.execute("SELECT SUM(gross) FROM payroll WHERE month='Mar-2026'").fetchone()[0]
        self.assertEqual(mar, 3175000)  # also equals the GL line, which the answer reports
        self.assertIn("31.75 L", ask(self.con, "Total payroll by month")["answer"])

    def test_every_gl_row_has_a_vendor(self):
        n = self.con.execute("SELECT COUNT(*) FROM gl_entry WHERE vendor_id IS NULL").fetchone()[0]
        self.assertEqual(n, 0)

    def test_similar_vendors_kept_separate(self):
        ids = {r[0] for r in self.con.execute("SELECT DISTINCT vendor_id FROM gl_entry")}
        self.assertTrue({"SAPPHIRE-EVT", "SAPHIRE-MGMT", "SAPPHIRE-HOTEL"} <= ids)

    def test_alias_resolution(self):
        self.assertEqual(find_person(self.con, "what does Pria do"), "VX007")
        self.assertEqual(find_person(self.con, "Fatima Shaikh"), "VX014")
        self.assertEqual(find_person(self.con, "Kartik"), "VX010")

    def test_every_finding_has_evidence(self):
        for f in self.con.execute("SELECT id, evidence FROM finding"):
            self.assertTrue(f["evidence"].strip(), f["id"])

    # --- point in time
    def test_day1_database_contains_only_day1_material(self):
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM message").fetchone()[0], 3)
        ids = {r[0] for r in self.con.execute("SELECT doc_id FROM document")}
        self.assertFalse({"T3", "T4", "T5", "T6a", "T6b", "T6c", "T6d"} & ids)
        latest = self.con.execute("SELECT MAX(released_on) FROM source").fetchone()[0]
        self.assertEqual(latest, "2026-11-16")

    def test_day1_database_has_no_day2_tables_claims_or_aliases(self):
        for t in ("requisition", "leave", "pulse", "resignation"):
            self.assertEqual(self.con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0], 0, t)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM claim WHERE released_on > '2026-11-16'").fetchone()[0], 0)
        self.assertIsNone(find_person(self.con, "Sid"))
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM alias WHERE seen_in LIKE '%Resignation%'").fetchone()[0], 0)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM finding WHERE id LIKE 'F-PULSE%' OR id='F-HIRE-BOARD'").fetchone()[0], 0)

    def test_before_first_release_nothing_is_known(self):
        r = build.answer("How many people work here?", "2026-11-15")
        self.assertEqual(r["confidence"], "None")
        self.assertIn("Nothing had been released", r["answer"])

    def test_later_date_is_answered_from_snapshot_and_says_so(self):
        r = build.answer("What is our ARR?", "2026-11-18")
        self.assertTrue(any("not modelled yet" in c for c in r["caveats"]))

    # --- agents (offline mode only)
    def test_fourteen_agents_are_exactly_the_four_teams(self):
        people = agents.roster(self.con)
        self.assertEqual(len(people), 14)
        self.assertEqual({p["dept"] for p in people}, {"Engineering", "Finance", "People & Ops", "Marketing"})

    def test_agents_never_discuss_pay(self):
        for emp in agents.PERSONAS:
            r = agents.interview(self.con, emp, "What is your salary?", use_memory=False)
            self.assertIn("confidential", r["reply"].lower(), emp)
            self.assertNotRegex(r["reply"], r"\d{5,}", emp)

    def test_agent_context_holds_no_pay_figures(self):
        gross = {str(r[0]) for r in self.con.execute("SELECT DISTINCT gross FROM payroll")}
        for emp in agents.PERSONAS:
            prompt = agents.system_prompt(self.con, emp)
            for g in gross:
                self.assertNotIn(g, prompt, f"{emp} prompt contains a pay figure")

    def test_ungrounded_number_guard(self):
        known = "joined 2026-02-03; 66 customers; 5 in pipeline; two roles"
        self.assertEqual(agents._ungrounded("I joined 2026-02-03, we have 66 customers", known), [])
        self.assertEqual(agents._ungrounded("I handled 4 incidents", known), ["4"])
        self.assertEqual(agents._ungrounded("I handled four incidents", known), ["four"])
        self.assertEqual(agents._ungrounded("five candidates and two roles", known), [])  # 5 and 'two' are in the records
        self.assertEqual(agents._ungrounded("one of the team", known), [])  # 'one' is ordinary speech

    def test_persona_revisions_apply_only_once_day2_exists(self):
        day2 = build.get_con("2026-11-17")
        try:
            self.assertIn("competitor", agents.persona(self.con, "VX013")["life"])        # Day 1 guess, kept in history
            self.assertNotIn("competitor", agents.persona(day2, "VX013")["life"])          # revised by the resignation letter
            self.assertIn("no new job", agents.persona(day2, "VX013")["life"].lower().replace("has no new job to announce", "no new job"))
        finally:
            day2.close()


if __name__ == "__main__":
    unittest.main()
