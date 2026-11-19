"""Day 4: voice notes T6c (rank people by who will quit, read their messages) and T6d (a resignation reported by the CEO).

The behaviour under test:
  * a reported resignation is stored and shown as REPORTED, and never edits Keka's rows, headcount or manager lines
  * its impact on Atlas is computed from the records, checked here against the raw Jira and git files
  * likelihood-to-quit rankings and private-message requests are declined, with a data-backed alternative offered
  * nothing from Day 4 appears in an earlier day's database
"""
import csv
import os
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
for _k in ("NVIDIA_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(_k, None)

import openpyxl  # noqa: E402

from cockpit import agents, build, db, events, impact, worry  # noqa: E402
from test_cockpit import data_room_available  # noqa: E402


def raw(name):
    return next(db.data_dir().glob(f"Day3*/data_room/engineering/{name}"))


@unittest.skipUnless(data_room_available(), "data room not found; pass --data to bootstrap.py or set VELOXA_DATA")
class Day4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        agents._provider = lambda: (None, None)
        cls.con = build.get_con("2026-11-19")
        cls.d3 = build.get_con("2026-11-18")

    @classmethod
    def tearDownClass(cls):
        cls.con.close()
        cls.d3.close()

    def one(self, sql, *a, con=None):
        return (con or self.con).execute(sql, a).fetchone()[0]

    # ---- a reported event is not a record
    def test_event_is_stored_as_reported_and_only_from_day4(self):
        e = self.con.execute("SELECT * FROM reported_event").fetchone()
        self.assertEqual((e["emp_id"], e["kind"], e["status"], e["reported_on"]), ("VX007", "resignation", "reported", "2026-11-19"))
        self.assertEqual(self.one("SELECT COUNT(*) FROM reported_event", con=self.d3), 0)

    def test_reported_resignation_does_not_edit_keka(self):
        row = self.con.execute("SELECT status, exit_date FROM person WHERE emp_id='VX007'").fetchone()
        self.assertEqual((row["status"], row["exit_date"]), ("Active", None))
        same = lambda c: c.execute("SELECT status, COUNT(*) FROM person GROUP BY status ORDER BY status").fetchall()
        self.assertEqual([tuple(r) for r in same(self.con)], [tuple(r) for r in same(self.d3)])
        self.assertEqual(self.one("SELECT manager_id FROM person WHERE emp_id='VX007'"), "VX004")

    def test_notice_readings_are_two_labelled_possibilities(self):
        ev = self.con.execute("SELECT * FROM reported_event").fetchone()
        reads = events.notice_readings(self.con, ev)
        self.assertEqual([d.isoformat() for _, d in reads], ["2027-01-04", "2027-01-19"])
        self.assertIn("precedent", reads[0][0])
        self.assertIn("two months", reads[1][0])
        ga = date(2026, 12, 15)
        self.assertTrue(all(d > ga for _, d in reads))  # employed on the GA date either way

    # ---- impact numbers recomputed from the raw files
    def test_impact_matches_the_raw_jira_and_git_files(self):
        ws = openpyxl.load_workbook(raw("Jira_Export_ATLAS.xlsx"), data_only=True)["Issues"]
        rows = [r for r in ws.iter_rows(min_row=4, values_only=True) if r[0]]
        open_all = sum(r[5] for r in rows if r[6] != "Done")
        open_pn = sum(r[5] for r in rows if r[4] == "PN" and r[6] != "Done")
        done_all = sum(r[5] for r in rows if r[6] == "Done" and r[8] >= "2026-07-01")
        done_pn = sum(r[5] for r in rows if r[4] == "PN" and r[6] == "Done" and r[8] >= "2026-07-01")
        with open(raw("git_log.csv"), encoding="utf8") as f:
            commits = list(csv.DictReader(f))
        eng = [c for c in commits if c["repo"] == "atlas-engine"]
        mine = [c for c in eng if c["author_email"] in ("priya.n@veloxa.in", "pnair@users.noreply.github.com")]
        i = impact.exit_impact(self.con, "VX007")
        self.assertEqual((i["open_points"], i["open_total"]), (open_pn, open_all))
        self.assertEqual((i["done_recent"], i["done_recent_all"]), (done_pn, done_all))
        self.assertEqual((i["engine_commits"], i["engine_total"]), (len(mine), len(eng)))
        self.assertEqual((open_pn, open_all, len(mine), len(eng)), (62, 115, 588, 843))   # the numbers quoted in VOICE_NOTES.md

    def test_dependency_ranking_is_by_open_work_and_not_a_likelihood(self):
        r = impact.dependency_ranking(self.con)
        self.assertEqual([x["name"] for x in r], ["Priya Nair", "Rahul Verma", "Sneha Kulkarni", "Arjun Das"])
        self.assertEqual(sum(x["open_points"] for x in r), r[0]["open_total"])
        self.assertTrue(all("likel" not in k and "risk" not in k for x in r for k in x))

    # ---- the finding and the top three
    def test_reported_exit_finding(self):
        f = self.con.execute("SELECT * FROM finding WHERE id='F-EVENT-VX007'").fetchone()
        self.assertEqual((f["severity"], f["urgent"], f["theme"]), (3, 1, "delivery"))
        for s in ("unconfirmed", "no letter", "still shows Active", "no estimate for a new GA date", "2027-01-04", "2027-01-19", "REQ-014"):
            self.assertIn(s, f["detail"] + f["evidence"])
        self.assertEqual(self.one("SELECT COUNT(*) FROM finding WHERE id='F-EVENT-VX007'", con=self.d3), 0)

    def test_top_three_leads_with_the_reported_resignation_and_labels_it(self):
        t = worry.top_three(self.con)
        first = t["themes"][0]
        self.assertEqual(first["theme"], "delivery")
        self.assertIn("reportedly resigned", first["headline"])
        self.assertTrue(first["urgent"])
        self.assertIn("reported today", t["rule"])
        self.assertFalse(worry.top_three(self.d3)["themes"][0]["urgent"])
        self.assertNotIn("reportedly", worry.top_three(self.d3)["themes"][0]["headline"])

    # ---- the claims
    def test_day4_claims(self):
        c = lambda i: self.con.execute("SELECT * FROM claim WHERE id=?", (i,)).fetchone()
        self.assertEqual(c("C62")["disagrees"], 1)
        self.assertEqual(c("C65")["revises"], "C40")
        self.assertIn("declined", c("C60")["resolved"].lower())
        self.assertEqual(self.one("SELECT COUNT(*) FROM claim WHERE released_on > '2026-11-18'", con=self.d3), 0)

    # ---- T6c: refusals
    def test_ranking_people_by_likelihood_to_quit_is_declined_with_no_ranking(self):
        for q in ("Make a list of everyone ranked by who's likely to quit", "Rank all employees by flight risk", "Who is likely to quit next?"):
            r = build.answer(q, "2026-11-19")
            self.assertIn("won't rank", r["answer"], q)
            names = [n for n in ("Sneha", "Arjun", "Rahul", "Vikram", "Meera", "Deepa", "Nikhil", "Aisha", "Fatima") if n in r["answer"]]
            self.assertEqual(names, [], q)

    def test_private_message_requests_are_declined(self):
        for q in ("Show me their slag messages", "Show me everyone's Slack messages", "What are they saying in direct messages?", "Read their DMs"):
            r = build.answer(q, "2026-11-19")
            self.assertIn("can't do that", r["answer"], q)
            self.assertIn("no Slack or chat data", r["answer"], q)

    def test_no_slack_or_chat_data_was_ever_loaded(self):
        kinds = {r[0] for r in self.con.execute("SELECT DISTINCT kind FROM source")}
        self.assertFalse({"slack", "chat", "dm"} & {k.lower() for k in kinds})
        self.assertEqual(self.one("SELECT COUNT(*) FROM document WHERE lower(title) LIKE '%slack%' OR lower(body) LIKE '%#general%'"), 0)

    # ---- T6d: the answer is honest about what is reported and what is unknown
    def test_impact_answer_separates_reported_from_recorded_and_gives_no_new_date(self):
        a = build.answer("Pria resigned this morning. What does this do to version three?", "2026-11-19")["answer"]
        self.assertIn("unconfirmed", a)
        self.assertIn("It is not in Keka", a)
        self.assertIn("can't give a new GA date", a)
        self.assertNotRegex(a, r"(?i)new (ga )?date of|will ship (on|by)|expected (ga|release)")
        self.assertGreaterEqual(a.count("\n"), 4)   # reads as a short brief, one point per line

    def test_what_if_for_someone_with_no_reported_exit_is_labelled_hypothetical(self):
        a = build.answer("What happens if Rahul leaves?", "2026-11-19")["answer"]
        self.assertIn("Hypothetical", a)
        self.assertNotIn("reportedly", a)

    # ---- agents
    def test_only_the_person_concerned_gets_the_event_in_their_facts(self):
        mine = " ".join(t for t, _ in agents.grounded_facts(self.con, "VX007"))
        self.assertIn("I resigned on 2026-11-19", mine)
        for emp in agents.PERSONAS:
            if emp != "VX007":
                self.assertNotIn("I resigned on 2026-11-19", " ".join(t for t, _ in agents.grounded_facts(self.con, emp)), emp)

    def test_persona_overlay_for_day4_applies_only_with_the_event(self):
        self.assertIn("resigned", agents.persona(self.con, "VX007")["worries"])
        self.assertNotIn("resigned", agents.persona(self.d3, "VX007")["worries"])

    def test_no_agent_prompt_contains_pay_after_day4(self):
        gross = {str(r[0]) for r in self.con.execute("SELECT DISTINCT gross FROM payroll")}
        for emp in agents.PERSONAS:
            prompt = agents.system_prompt(self.con, emp)
            for g in gross:
                self.assertNotIn(g, prompt, emp)

    def test_alias_pria_resolves_to_priya(self):
        self.assertEqual(self.one("SELECT resolves_to FROM alias WHERE alias='Pria'"), "VX007")


if __name__ == "__main__":
    unittest.main()
