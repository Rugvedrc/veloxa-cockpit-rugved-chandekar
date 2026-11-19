"""Voice note T6b: "Make sure the thing doesn't break when we move people around."

A copy of the Day 3 database is reorganised in ways the real data does not (yet) show: a CRO is hired,
marketing moves under them, a person changes department and manager, someone leaves, a department is
renamed, an executive's seat is vacated. Then everything the cockpit does is run against it: every test
question, the findings, the top three, every handler and every agent. Nothing may raise, and the answers
that depend on the moved lines must change with them.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
for _k in ("NVIDIA_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(_k, None)

from cockpit import agents, ask as askmod, build, checks, db, worry  # noqa: E402
from test_cockpit import data_room_available  # noqa: E402

LATEST = "2026-11-19"  # the newest modelled day
QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text(encoding="utf8"))
EXTRA = ["Who reports to Zoya?", "Who does Nikhil report to?", "Who is on the Revenue team?", "Who is Aisha?", "Who is Rahul?",
         "Who is Meera?", "Who will marketing report to?", "Is anyone overloaded?", "What should I worry about?", "How many people work here?",
         "Who is leaving the company?", "How many leave days did Fatima take?", "Is hiring paused?", "Who is the CRO?"]


def reorganise(con):
    con.execute("INSERT INTO person VALUES('VX020','Zoya Kapoor','zoya@veloxa.in','Revenue','CRO','VX001','2026-12-01','Bengaluru','Active',NULL,'test!R99')")
    con.execute("INSERT INTO reporting_line VALUES('VX020','VX001','CEO','2026-12-01',NULL,'current','test',NULL)")
    # marketing's head now reports to the CRO; the planned line becomes real, so remove it
    con.execute("UPDATE person SET manager_id='VX020' WHERE emp_id='VX006'")
    con.execute("DELETE FROM reporting_line WHERE emp_id='VX006'")
    con.execute("INSERT INTO reporting_line VALUES('VX006','VX020','CRO','2026-12-01',NULL,'current','test',NULL)")
    # Sales is renamed Revenue and reports to the CRO; a marketer moves to Revenue under Manoj
    con.execute("UPDATE person SET dept='Revenue' WHERE dept='Sales'")
    con.execute("UPDATE person SET manager_id='VX020' WHERE emp_id='VX002'")
    con.execute("UPDATE reporting_line SET manager_id='VX020' WHERE emp_id='VX002'")
    con.execute("UPDATE person SET dept='Revenue', manager_id='VX002' WHERE emp_id='VX011'")
    con.execute("UPDATE reporting_line SET manager_id='VX002' WHERE emp_id='VX011'")
    # an engineer leaves and the CFO's seat is vacated
    con.execute("UPDATE person SET status='Exited', exit_date='2026-11-30' WHERE emp_id='VX018'")
    con.execute("UPDATE person SET status='Exited', exit_date='2026-11-30' WHERE emp_id='VX003'")
    con.commit()


@unittest.skipUnless(data_room_available(), "data room not found; pass --data to bootstrap.py or set VELOXA_DATA")
class Reorg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        agents._provider = lambda: (None, None)
        build.get_con(LATEST).close()
        cls.tmp = tempfile.mkdtemp()
        cls.path = Path(cls.tmp) / "reorg.db"
        shutil.copy(build.db_path(LATEST), cls.path)
        cls.con = db.connect(cls.path)
        reorganise(cls.con)

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_every_question_still_answers_without_error(self):
        for case in QUESTIONS:
            with self.subTest(q=case["q"]):
                r = askmod.ask(self.con, case["q"])
                self.assertIsInstance(r["answer"], str)
                self.assertTrue(r["answer"])
                self.assertIn("confidence", r)

    def test_extra_questions_about_the_moved_people_do_not_error(self):
        for q in EXTRA:
            with self.subTest(q=q):
                self.assertTrue(askmod.ask(self.con, q)["answer"])

    def test_findings_can_be_recomputed_on_the_reorganised_data(self):
        self.con.execute("DELETE FROM finding")
        checks.run_all(self.con)
        self.assertGreater(self.con.execute("SELECT COUNT(*) FROM finding").fetchone()[0], 10)

    def test_top_three_survives_a_vacated_executive_seat(self):
        t = worry.top_three(self.con)
        self.assertEqual(len(t["themes"]), 3)
        money = next(x for x in t["themes"] if x["theme"] == "money")
        self.assertIsNone(money["suggested_owner"])  # the CFO seat is empty: no owner is suggested, no crash

    def test_answers_follow_the_moves(self):
        a = lambda q: askmod.ask(self.con, q)["answer"]
        self.assertIn("Zoya Kapoor", a("Who does Nikhil report to?"))
        self.assertNotIn("not yet in Keka", a("Who does Nikhil report to?"))      # the move is now real
        self.assertIn("Nikhil Bose", a("Who reports to Zoya?"))
        self.assertIn("Manoj Kumar", a("Who is on the Revenue team?"))             # a department the code has never heard of
        self.assertIn("Aisha Khan", a("Who is on the Revenue team?"))              # moved in from Marketing
        self.assertNotIn("Aisha Khan", a("Who is on the marketing team?"))
        self.assertIn("Exited", a("Who is Rahul?"))
        self.assertIn("Manoj Kumar", a("Who does Aisha report to?"))

    def test_no_planned_line_means_no_planned_claim(self):
        r = askmod.ask(self.con, "Who will marketing report to?")
        self.assertNotIn("planned (not yet in Keka)", r["answer"].lower())

    def test_all_fourteen_agents_still_build_a_prompt_and_answer(self):
        for emp in agents.PERSONAS:
            with self.subTest(emp=emp):
                self.assertTrue(agents.system_prompt(self.con, emp))
                self.assertTrue(agents.interview(self.con, emp, "Who do you report to?", use_memory=False)["reply"])

    def test_the_agent_whose_manager_changed_sees_the_new_one(self):
        facts = " ".join(t for t, _ in agents.grounded_facts(self.con, "VX006"))
        self.assertIn("reports to Zoya Kapoor", facts)

    def test_a_reported_resignation_becomes_a_record_when_keka_catches_up(self):
        """T6d lifecycle: reported -> Keka shows it. The answers must switch from 'reportedly' to 'Keka shows'."""
        tmp = Path(self.tmp) / "lifecycle.db"
        shutil.copy(build.db_path(LATEST), tmp)
        con = db.connect(tmp)
        try:
            before = askmod.ask(con, "What does Priya's resignation do to Atlas?")["answer"]
            self.assertIn("reportedly resigned", before)
            con.execute("UPDATE person SET status='Notice period', exit_date='2027-01-19' WHERE emp_id='VX007'")
            con.execute("UPDATE reported_event SET status='confirmed'")
            after = askmod.ask(con, "What does Priya's resignation do to Atlas?")["answer"]
            self.assertIn("Keka shows Priya Nair as 'notice period', last day 2027-01-19", after)
            self.assertNotIn("reportedly", after)
            con.execute("DELETE FROM finding")
            checks.run_all(con)
            ids = {r[0] for r in con.execute("SELECT id FROM finding")}
            self.assertNotIn("F-EVENT-VX007", ids)     # no longer 'reported'
            self.assertIn("F-EXIT-VX007", ids)         # it is now an ordinary departure
            text = con.execute("SELECT detail FROM finding WHERE id='F-EXIT-VX007'").fetchone()[0]
            self.assertNotIn("Marketing", text)        # no leftover text written for someone else
            self.assertIn("Engineering loses a Staff Engineer", text)
            self.assertIn("Priya Nair", askmod.ask(con, "Who is leaving the company?")["answer"])
        finally:
            con.close()

    def test_a_manager_who_left_does_not_break_the_org_view(self):
        self.con.execute("UPDATE person SET status='Exited', exit_date='2026-11-30' WHERE emp_id='VX004'")
        self.assertTrue(askmod.ask(self.con, "Who does Priya report to?")["answer"])
        self.assertTrue(askmod.ask(self.con, "Who reports to Vikram?")["answer"])


if __name__ == "__main__":
    unittest.main()
