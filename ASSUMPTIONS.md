# ASSUMPTIONS

Entries are never deleted. When one is proved wrong it is marked **REVISED** and the correction is added below it.

Format: date | assumption | source line it rests on | confidence | what would change my mind.

## Company facts

**A-01** | 2026-11-16 | Veloxa has **19 people**, not 180.
Source: Employee_Master.xlsx (19 rows: 18 Active, 1 Notice); both board updates say "Team 19"; T1 transcript says "roughly eighteen". The brief says "180-person".
Confidence: High. Would change my mind: a later export listing ~180 staff (e.g. Keka with contractors), or a board update with a different team figure.

**A-02** | 2026-11-16 | ARR is **Rs 6.1 Cr** (Sep 2026) and **Rs 5.8 Cr** (Jun 2026), taken from the board updates.
Source: Board_Update_Apr-Jun_2026.pdf, Board_Update_Jul-Sep_2026.pdf. The CEO's "forty-two crore, maybe forty-five" is treated as a gut figure.
Confidence: Medium (board numbers are self-reported). Would change my mind: billing data or an invoice-level revenue export.

**A-03** | 2026-11-16 | CFO's "forty-eight" ARR at start of year means **Rs 4.8 Cr**.
Source: T2 "ARR at the start of the year was forty-eight"; consistent with 5.8 Cr three months later.
Confidence: Medium. Would change my mind: any source giving the 1 Apr 2026 ARR.

**A-04** | 2026-11-16 | Monthly burn is **Rs 44-46 lakh**; "two point two lakhs" is a mishearing.
Source: board updates (46 L, 44 L); GL PAYROLL rows (Rs 31.75 L/month alone exceeds 2.2 L).
Confidence: High that 2.2 L is wrong; Medium on the exact figure. Would change my mind: a cash-flow statement.

**A-05** | 2026-11-16 | Today's financial year is Apr 2026 - Mar 2027 ("FY27"). The cockpit always prints calendar dates.
Source: T2 note "may have said twenty-seven"; GL data covers Apr-Sep 2026.
Confidence: Medium. Would change my mind: finance documents labelling the year.

**A-06** | 2026-11-16 | Cost-centre codes mean what they look like: ENG-INF infrastructure, ENG-OPS engineering operations, MKT-PS paid search, MKT-EVT marketing events, PPL-HIR hiring, SAL-TRV sales travel, G&A general.
Source: GL_Export column "Cost Centre" plus narrations.
Confidence: Medium. Would change my mind: a chart of accounts.

**A-07** | 2026-11-16 | Money in the exports is in rupees and gross payroll is monthly.
Source: column headers "Amount (Rs.)", "Gross (Rs.)".
Confidence: High.

## Matching people and vendors

**A-08** | 2026-11-16 | "Pria" = Priya Nair (VX007); "the new boy Rahul" = Rahul Verma (VX018); "Kartik" = Karthik Subramanian (VX010); "Fatima Shaikh" = Fatima Sheikh (VX014). Keka spelling wins.
Source: T1, T2 vs Employee_Master. Confidence: High.

**A-09** | 2026-11-16 | "Vicky" (T2 action item) = Vikram Menon.
Source: T2 "Check the freeze decision with Vicky". Confidence: **Low**. Nothing else says Vikram goes by Vicky; it could be a founder/board member. Would change my mind: any email or transcript using "Vicky".

**A-10** | 2026-11-16 | "Sapphire Events Pvt Ltd" and "Saphire Event Mgmt" may be one vendor, but I keep them **separate** in the model and flag them.
Source: GL JV-0846 and JV-0904, same cost centre MKT-EVT, 0.73 name similarity, different invoice-ref formats.
Confidence: Medium. Would change my mind: invoices/PAN. "Sapphire Residency Hotel" is a different business (sales offsite) and is not merged.

**A-11** | 2026-11-16 | Payroll initials: FS = Fatima Sheikh, KS = Karthik Subramanian.
Source: register "Processed By"; email 01 says Karthik ran February payroll. Confidence: High.

**A-12** | 2026-11-16 | Rahul Verma was overpaid **2 days (about Rs 7,857 gross)** in Feb 2026 and it was never corrected.
Source: Payroll register Feb row (28 of 28 days payable) vs join date 2026-02-03 (26 payable days); emails 02, 03 (query raised 6 Mar, answered "will check"). "Never corrected" is inferred from the absence of a later record.
Confidence: High on the overpayment, Low on "never corrected". Would change my mind: Mar-Apr payslips showing a recovery.

**A-13** | 2026-11-16 | The two backend roles from the Q2 board update are **still unfilled**.
Source: GL JV-0688 (recruiter, 2 backend roles), Q3 board "hiring is paused", no later backend joiner in Keka. Rahul joined before the search. Confidence: Medium. Would change my mind: Hiring_Tracker (Day 2).

**A-14** | 2026-11-16 | The GL payroll line is copied forward, not posted from real runs.
Source: identical Rs 31,75,000 for six months, equal to the Mar-2026 register total. Confidence: Low-Medium. Would change my mind: Keka payroll runs for Apr-Sep.

## Design assumptions

**A-15** | 2026-11-16 | The 14 agents are everyone in Engineering (5), Finance (3), People & Ops (3) and Marketing (3). The other 5 (CEO, Sales x2, Support x2) are real in the data but are not agents.
Source: brief says "14 people across engineering, finance, HR and marketing"; the data has exactly 14. Confidence: High.

**A-16** | 2026-11-16 | The CFO's "salaries never visible to Ananya" rule overrides the CEO's "ask me anything" wish.
Source: T2. Confidence: High that it was said; the CEO may disagree, which would be a pushback case.

**A-17** | 2026-11-16 | Files from later days that already exist in the pack folder are treated as **not yet released** until their day arrives (`--as-of`).
Source: brief "released over the first week". Confidence: High. Cost: none; `build --as-of` lets us see any day.

**A-18** | 2026-11-16 | The HR kickoff email (10:00 AM IST Mon 16 Nov) replaces the brief's schedule: no live sessions, five days, daily deadlines, final submission Fri 20 Nov 6:00 PM IST.
Source: HR email, sections 1-3. Confidence: High. Would change my mind: a later correction from HR.

**A-19** | 2026-11-16 | "Treat as released at 10:00 AM" means a drop is knowable from its release day onward, so "what did we know on date X" uses the folder's day, not file timestamps.
Source: HR email section 3 table. Confidence: High.

**A-20** | 2026-11-16 | Veloxa's data has 19 people but the brief says "180-person" and a CEO line says "one-eighty". HR's email now says all Veloxa material is synthetic; I still treat the exports as the truth over the brief text.
Source: Employee_Master.xlsx, board updates. Confidence: High. Would change my mind: a later Employee_Master with ~180 rows.

**A-21** | 2026-11-16 | Answers for "as of" dates after the last modelled drop come from the Day 1 snapshot (flagged in the answer) rather than from partially loaded later files.
Source: own design (DECISIONS D-13). Confidence: High. Revisit when Day 2 is modelled.

**A-22** | 2026-11-17 | Leave-register names ("P. Nair") are matched to Keka by first initial + surname, and approver codes ("VM") by name initials. Ambiguous matches would be dropped, not guessed.
Source: Leave_Register.xlsx. Confidence: High (all 19 rows and all approvers matched uniquely). Would change my mind: a new hire sharing initials.

**A-23** | 2026-11-17 | "Not shown: team smaller than 6" on every pulse row is Culture Amp's privacy rule, so comments are not missing data and must not be reconstructed.
Source: Pulse_Survey.xlsx Comments column; T3. Confidence: High.

**A-24** | 2026-11-17 | The tracker, leave register and survey are as of the 31 Oct export; "open" means open on that date.
Source: file titles ("Exported 31-Oct-2026"). Confidence: High.

**A-25** | 2026-11-17 | Siddharth's stated reason ("clearer launch timelines") is his reason in his own words, not a verified cause; the letter names no new employer.
Source: Resignation_Letter_SM.pdf. Confidence: High that it is what he wrote.

**A-26** | 2026-11-17 | Priya Nair's five September half-days are not interpreted as anything. They are shown as leave entries only.
Source: Leave_Register.xlsx R14-R18. Confidence: n/a (deliberate non-inference, DECISIONS D-16).

## Invented private lives (the data is silent here)

All of these are fiction from data/curated/personas.json. Work facts always come from the data, never from this file. Each should be revised the moment a source contradicts it.

| ID | Person | Invention | Confidence | Would change my mind |
|---|---|---|---|---|
| A-P04 | Vikram Menon | 42, wife Anjali (paediatrician), son Aarav, never took the August holiday | None (fiction) | Any HR/leave record: Leave_Register (Day 2) |
| A-P07 | Priya Nair | From Kochi, runs 10k, single point of failure, has an unanswered recruiter message | None | Resignation/hiring data; she could be happy |
| A-P09 | Arjun Das | 29, Pune, football and streaming, feels remote staff are last to hear | None | Pulse survey |
| A-P12 | Sneha Kulkarni | 27, cat named Nagios, considering leaving over on-call | None | OnCall_Rota, Pulse survey (Day 2-3) |
| A-P18 | Rahul Verma | 25, from Lucknow, sends money home, fears clawback of the overpay | None | His emails or HR notes |
| A-P03 | Meera Iyer | 46, CA, plays carnatic violin | None | Any bio |
| A-P10 | Karthik Subramanian | 29, doing CFA L2 (T2 mentions CFA), suspects he mishandled Feb payroll | CFA is from T2 (Medium); rest None | Payroll follow-up emails |
| A-P14 | Fatima Sheikh | 26, **married Feb 2026** (T2 "out for her wedding"; email 01 "since Fatima is out"), bakes | Wedding: Medium. Rest None | Leave_Register (Day 2) |
| A-P05 | Deepa Joshi | 39, two kids, meditates; privately doubts "attrition is normal" | None | Pulse survey, attrition data |
| A-P15 | Rohan Banerjee | 31, Kolkata, football fan, frustrated by hiring pause | Remote: Medium (Keka). Rest None | Hiring_Tracker |
| A-P17 | Lakshmi Pillai | 24, from Chennai, sketches | None | none |
| A-P06 | Nikhil Bose | 37, partner Tara, restaurants, defensive about numbers | Defensive: T2 hint (Low). Rest None | His call transcript (Day 3) |
| A-P11 | Aisha Khan | 30, two rescue dogs, sourdough | None | none |
| A-P13 | Siddharth Mehta | 28, **has accepted a competitor offer**, starts December | Leaving: High (Keka). Competitor/offer: None | Resignation_Letter_SM (Day 2) |

## Revisions (the entries above are kept as written)

**REVISED 2026-11-17 - A-P13 Siddharth Mehta.** I had invented that he "accepted a competitor offer, starting December". His letter says he is "looking for a role" and names no employer. Now: no offer; a couple of unsigned conversations. Day 1 wording stays in the Day 1 persona; the revised text is the `_d2` overlay.

**REVISED 2026-11-17 - A-P07 Priya Nair.** Day 1: "has an unanswered recruiter message". The leave register then showed five September afternoons off. I gave those an innocent invented reason (her father's physiotherapy, which she does not volunteer) and softened the recruiter line to weekly messages she ignores. Both are fiction; neither is evidence of anything (A-26).

**REVISED 2026-11-17 - A-P14 Fatima Sheikh.** The wedding is now confirmed: 15 days of marriage leave, 9-27 Feb. Confidence raised from Medium to High.

**REVISED 2026-11-17 - A-09 "Vicky" = Vikram Menon.** Raised from Low to Medium: the "freeze" T2 says to check with Vicky is the pause of REQ-014/015 agreed between Meera and Vikram on 12 Aug. Still no source calls him Vicky. Both alias rows are kept.

**REVISED 2026-11-17 - A-13 backend roles unfilled.** Confirmed by Hiring_Tracker (REQ-014/015 on hold since 12 Aug, 8 candidates, final round cancelled 14 Aug) and emails 06/07. High.

**REVISED 2026-11-17 - A-P09 Arjun Das, A-P15 Rohan Banerjee, A-P04 Vikram Menon.** Persona text extended with Day 2 facts (remote request 18 Sep; relocation leave = the move to Pune; eight candidates waiting; "we'll absorb it"). Still fiction where it goes beyond the records.

*Revisions go here, newest first.*
