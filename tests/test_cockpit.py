"""Answer-quality tests: truth against the data room, citations present, refusals honoured.
Run:  python -m unittest discover tests
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cockpit import checks, loaders, resolve  # noqa: E402
from cockpit.ask import ask  # noqa: E402
from cockpit.db import DATA_DIR, rebuild  # noqa: E402


@unittest.skipUnless(DATA_DIR.exists(), "data room not found; set VELOXA_DATA")
class CockpitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loaders.AS_OF = "2026-11-16"  # Day 1 only: tests must not depend on later drops
        cls.con = rebuild(Path(tempfile.mkdtemp()) / "t.db")
        loaders.load_all(cls.con)
        resolve.load_entities(cls.con)
        resolve.load_claims(cls.con)
        checks.run_all(cls.con)

    def test_headcount_is_19_not_180(self):
        r = ask(self.con, "How many people work here?")
        self.assertIn("19 people", r["answer"])
        self.assertTrue(any("180" in c for c in r["caveats"]))

    def test_no_individual_salary_leaks(self):
        for name in ("Meera", "Ananya", "Fatima", "Rahul"):
            r = ask(self.con, f"What is {name}'s salary?")
            self.assertNotRegex(r["answer"], r"\d{5,}", name)
            self.assertIn("can't show individual pay", r["answer"])

    def test_totals_are_allowed_and_cited(self):
        r = ask(self.con, "Total payroll by month")
        self.assertIn("31.75 L", r["answer"])
        self.assertTrue(r["cites"])

    def test_unknown_question_admits_it(self):
        r = ask(self.con, "What is the weather on Mars?")
        self.assertEqual(r["confidence"], "None")
        self.assertIn("don't have a record", r["answer"])

    def test_every_substantive_answer_cites_sources(self):
        for q in ["What is our ARR?", "burn and runway", "Summit spend", "Why is AWS going up?",
                  "What should I worry about?", "Who is Pria?", "status of Atlas", "any hiring freeze?"]:
            r = ask(self.con, q)
            self.assertTrue(r["cites"], q)

    def test_rahul_overpayment_found(self):
        f = self.con.execute("SELECT * FROM finding WHERE id LIKE 'F-PAY-VX018-%'").fetchone()
        self.assertIsNotNone(f)
        self.assertIn("7,857", f["detail"])

    def test_alias_resolution(self):
        from cockpit.resolve import find_person
        self.assertEqual(find_person(self.con, "what does Pria do"), "VX007")
        self.assertEqual(find_person(self.con, "Fatima Shaikh"), "VX014")

    def test_burn_two_lakh_flagged_as_impossible(self):
        r = ask(self.con, "What is our burn?")
        self.assertTrue(any("31.75" in c for c in r["caveats"]))

    def test_as_of_gates_later_drops(self):
        n = self.con.execute("SELECT COUNT(*) FROM message").fetchone()[0]
        self.assertEqual(n, 3)  # Day 1 emails only


if __name__ == "__main__":
    unittest.main()
