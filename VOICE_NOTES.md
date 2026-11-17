# Responses to the CEO's voice notes

One section per voice note, committed on the day it is released. Each says what was asked, what I did, and where I pushed back.

---

## T6a (released Tue 17 Nov): "Top three, no typing"

**What you asked**

> "I won't type questions every morning, na. When I open it, it should just tell me what to worry about. Top three."

**Decision: change made, with three conditions.**

**What now happens.** The cockpit opens on **Top 3 to worry about**. Nothing to type. Each of the three shows the main problem, the other problems in the same group, a suggested owner by role, and the records behind it. The questions box is one tab away.

On the 31 Oct data the three are:

1. **Atlas delivery is at risk** (act now). GA slipped from 15 Sep with no new date; the two backend roles meant to help have been on hold since 12 Aug with 8 candidates waiting; Engineering engagement fell from 3.9 to 3.1. Suggested owner: VP Engineering.
2. **Money, books and numbers** (act now). A new joiner was paid for 28 days in February instead of 26 and no correction is visible in the records; AWS cost is up 37% while revenue grew 5%; two similarly named event vendors may be one. Suggested owner: CFO.
3. **People: leavers, hiring and morale** (look soon). The Product Marketing Manager (who built the launch kit) was due to leave on 31 Oct and his backfill was still open with 7 candidates; the board was told hiring is paused but two roles opened after the pause are open; Marketing engagement fell 3.8 to 3.4. Suggested owner: Head of People & Ops.

**Where I did not do exactly what you said**

1. **Three themes, not the three highest-scoring findings.** A flat top three would mix a missed launch with a voucher typo. Findings are grouped into three themes, and the three themes are ranked. Everything else stays under "All findings" so a fourth problem is never hidden.
2. **The ranking rule is on screen.** Ranked by the highest severity in each theme; ties go to what you said worries you most on the kickoff call (engineering speed and Atlas), then to the theme with more findings at "look soon" or above. The severity levels are my judgement, not something in the data, so the screen says so. If you disagree with the order, the rule is one function (`cockpit/worry.py`) and a different order is a small change.
3. **No names as "flight risks".** You did not ask for this, but a "worry" list invites it, so I'm stating it. The Head of People said she is worried about one engineer and chose not to name them. The records support only a team-level signal (Engineering engagement, 4 of 5 people responded). The leave register has patterns for individuals, but a pattern is not evidence of intent, so the cockpit does not turn it into a name. Ask it about a named person's leave and you get the entries, not a guess.

**What I did not build:** survey comments. The Head of People wants you to read them; the survey tool hides them for any team under 6 people and every Veloxa team is under 6, so comments would identify the person who wrote them. That is your decision to make with her, not something the cockpit should engineer around. The cockpit says so when asked.

**How to check it.** `python cockpit.py serve`, open http://127.0.0.1:8765 (it opens on Top 3). Or `python cockpit.py top3`. The date selector shows the same screen as it would have looked on earlier days; on 16 Nov the third item is only the leaver, because the hiring tracker and survey had not been released.

**Evidence in the repo.** `cockpit/worry.py` (ranking), `cockpit/checks.py` (findings and themes), `cockpit/ui.html` (home screen), tests `tests/test_day2.py::test_top_three_*`, decision D-15 and D-16 in DECISIONS.md.

---

## T6b (Wed 18 Nov)
*Not released yet.*

## T6c, T6d (Thu 19 Nov)
*Not released yet.*
