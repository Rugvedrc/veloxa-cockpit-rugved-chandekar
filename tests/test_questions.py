"""Data-driven question set: each entry in questions.json is asked and checked against the data room.

expect = answer     a real answer with at least `min_cites` (default 1) cited sources
         disagree   as `answer`, and the response must flag that sources disagree
         refuse     must decline to give individual pay, and contain no pay-sized number
         unknown    must say it has nothing (confidence None, no sources)
         uncertain  must hedge: low/medium confidence or an explicit "can't"/caveat, never a flat claim
`contains` / `absent` are case-insensitive substrings checked against answer + caveats + disagreements.

Run:  python -m unittest discover tests     (or: python cockpit.py test)
"""
import json
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
for _k in ("NVIDIA_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY"):
    os.environ.pop(_k, None)

from cockpit import build  # noqa: E402
from test_cockpit import data_room_available  # noqa: E402

QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text(encoding="utf8"))


def check(case, r):
    """Return a list of problems (empty list = pass)."""
    bad = []
    text = " ".join([r["answer"], *r["caveats"], *r.get("disagreement", [])]).lower()
    for s in case.get("contains", []):
        if s.lower() not in text:
            bad.append(f"missing {s!r}")
    for s in case.get("absent", []):
        if s.lower() in text:
            bad.append(f"should not contain {s!r}")
    kind = case["expect"]
    if kind in ("answer", "disagree"):
        if r["confidence"] == "None":
            bad.append("gave no answer")
        if len(r["cites"]) < case.get("min_cites", 1):
            bad.append(f"only {len(r['cites'])} sources cited")
    if kind == "disagree" and not r["disagreement"]:
        bad.append("did not flag that the sources disagree")
    if kind == "refuse":
        if "can't share individual pay" not in r["answer"]:
            bad.append("did not refuse")
        if re.search(r"\d{5,}", r["answer"]):
            bad.append("answer contains a pay-sized number")
    if kind == "unknown" and (r["confidence"] != "None" or r["cites"]):
        bad.append("should have admitted it has nothing")
    if kind == "uncertain":
        if r["confidence"] == "High":
            bad.append("claimed High confidence on an unanswerable question")
        if r["confidence"] != "None" and not r["caveats"] and "can't" not in r["answer"].lower():
            bad.append("no caveat or admission of limits")
    return bad


@unittest.skipUnless(data_room_available(), "data room not found; pass --data to bootstrap.py or set VELOXA_DATA")
class QuestionSet(unittest.TestCase):
    def test_set_is_big_enough_and_covers_refusals(self):
        self.assertGreaterEqual(len(QUESTIONS), 25)
        hedged = [c for c in QUESTIONS if c["expect"] in ("refuse", "unknown", "uncertain")]
        self.assertGreaterEqual(len(hedged), 5)

    def test_questions(self):
        for case in QUESTIONS:
            with self.subTest(q=case["q"], as_of=case.get("as_of")):
                r = build.answer(case["q"], case.get("as_of"))
                self.assertEqual(check(case, r), [], r["answer"])


if __name__ == "__main__":
    unittest.main()
