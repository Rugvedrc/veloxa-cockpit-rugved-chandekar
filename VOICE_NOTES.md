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

### Update, Wed 18 Nov: what the top three looks like with the engineering data

The screen recomputes from the records, so with Day 3 the order changed:

1. **Atlas delivery is at risk** (act now). Jira has the GA date moved from 15 Sep to **15 Dec** (13 weeks), changed on 2 Sep; 115 of 233 story points are still open and nothing has been resolved since 17 Sep. Suggested owner: VP Engineering.
2. **People** (act now). **One engineer owns 56% of the Atlas work**, and the on-call engineer was on the rota in all 17 weeks and handled every SEV1. Suggested owner: Head of People & Ops.
3. **Money, books and numbers** (act now). The February overpayment, AWS cost growth, the possibly duplicated event vendor, and spoken numbers that do not match the records.

This top three now names one engineer. That is deliberate and consistent with what I said above: it states **where the work sits** (a documented fact you also said on the first call, "Pria basically holds the routing thing together"), not what anyone intends. The cockpit still never names a flight risk, and the findings are tested for words like "quit", "resign" and "burn out".

---

## T6b (released Wed 18 Nov): "Marketing reports to the new CRO; don't let it break"

**What you asked**

> "So, marketing will report to the new CRO from next month. Or the month after, still finalising. Make sure the thing doesn't break when we move people around."

**Decision: change made, with limits.**

**What now happens.** Reporting lines are data with dates, not a fixed tree. Two kinds are kept apart:
- **Current**, from Keka. Today Nikhil Bose reports to you.
- **Planned**, from what has been said. Marketing is to report to the CRO in December 2026 or January 2027. It carries its source, its date window, and the fact that **no one is named**.

Ask "Who does Nikhil report to?" and the answer gives both, with the planned line labelled "not yet in Keka". Ask "Who will marketing report to?" and it says what is known and what is not.

**How I checked that it does not break.** `tests/test_reorg.py` takes a copy of the data and reorganises it the way the real company is about to: a CRO is hired, Marketing moves under them, Sales is renamed Revenue and moves too, a marketer changes team and manager, an engineer leaves, and the CFO's seat is vacated. Then it runs every test question, recomputes every finding, rebuilds the top three, and runs all 14 agents. Nothing raises, and the answers follow the moves ("Who reports to Zoya?", "Who is on the Revenue team?"). It found two real problems that I fixed: a newly added person was not recognised by name, and a department called "Revenue" was being read as the revenue figure.

**Where I did not do exactly what you asked**

1. **I did not apply the move early.** "Next month, or the month after, still finalising" is not a date. Until it is in Keka, the cockpit shows Nikhil reporting to you and shows the CRO line as planned. Treating a plan as a fact is how a dashboard starts to lie.
2. **I did not guess who the CRO is.** There is no CRO in Keka and no CRO requisition in the hiring tracker. The cockpit says so. If you give me a name and a start date, it is one line in `data/curated/org_changes.json`.
3. **I did not write an agent for the CRO.** The 14 agents are the 14 people who exist. When the CRO joins, they need a persona from someone who knows them; I will not invent one for a person who does not exist yet.
4. **"Doesn't break" is proven for the logic, not for the data.** If Keka is slow to update, the cockpit will be slow to update too. The planned line is the bridge, and it is labelled as one.

**How to check it.** `python cockpit.py ask "Who will marketing report to?"` and `python -m unittest tests.test_reorg -v`. The date selector shows that on 17 Nov there was no planned change on record.

**Evidence in the repo.** `cockpit/org.py`, `data/curated/org_changes.json`, `tests/test_reorg.py`, decisions D-19 to D-23 in DECISIONS.md.

## T6c, T6d (Thu 19 Nov)
*Not released yet.*
