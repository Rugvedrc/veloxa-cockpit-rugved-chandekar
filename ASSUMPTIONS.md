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

**A-27** | 2026-11-18 | Atlas GA is **15 Dec 2026** (was 15 Sep), changed on 2 Sep by "vikram", as Jira's Versions sheet says.
Source: Jira_Export_ATLAS.xlsx Versions R2. Confidence: High that Jira says so; Medium that it is the real plan (Jira may lag). Would change my mind: a newer date from the board or the CEO.

**A-28** | 2026-11-18 | The Jira export, git log and on-call rota are as of the 31 Oct export, though none carries its own date; pace and "needed pace" are measured to 31 Oct.
Source: data_room/README.txt "Exported by IT on 31 Oct 2026"; the last commit is 30 Oct. Confidence: Medium.

**A-29** | 2026-11-18 | Jira assignee initials PN, RV, AD, SK are Priya Nair, Rahul Verma, Arjun Das, Sneha Kulkarni.
Source: Jira's own note that assignees are initials; the VP's 2 Jun plan (Priya core and re-routing, Rahul API, Arjun UI, Sneha hardening) matches the epic owners exactly. Confidence: High.

**A-30** | 2026-11-18 | "Snehal" (rota, incidents, T5) is an **on-call contractor, S. Patil of Patil Infra Services**, and a different person from Sneha Kulkarni.
Source: both names are on the same rota weeks; Keka has no Snehal; invoice PIS-114 bills "On-call SRE support, S. Patil"; PIS-108 starts 18 Aug, the first rota week with Snehal (17 Aug). One inconsistency: email 08 says the contractor starts the week of 24 Aug. Confidence: Medium. Would change my mind: a Keka or vendor record naming the contractor.

**A-31** | 2026-11-18 | `pnair@users.noreply.github.com` is Priya Nair (a second git identity). Merged.
Source: git_log.csv: both addresses commit only to atlas-engine, Nov 2025 to Oct 2026, never within a minute of each other, with the same hours; no other P. Nair exists. Confidence: Medium-high. Would change my mind: evidence that someone else uses that address. Effect if wrong: her share would be 29% of commits, not 40%.

**A-32** | 2026-11-18 | "After hours" means a commit between 22:00 and 06:00 IST; times in the sources are UTC and are converted.
Source: README, git_log, PagerDuty. Confidence: High on the conversion, a convention on the window.

**A-33** | 2026-11-18 | "CRO" means Chief Revenue Officer, and "next month, or the month after" from 18 Nov means December 2026 or January 2027.
Source: T4, T6b. Confidence: Medium. The sources only say "CRO" and give no date.

**A-34** | 2026-11-18 | The August pro-rata on invoice PIS-108 (Rs 60,000 before GST for 14 days) may be high: calendar days give Rs 54,194. The contract basis is unknown.
Source: Invoice_PIS-114.pdf, GL JV-0902. Confidence: Low. A 28-day basis gives exactly Rs 60,000.

**A-35** | 2026-11-18 | Nikhil's "one point eight" cannot be given a unit. It fits no simple reading against Rs 14.27 L in the ledger, so it is reported as unreconciled, not corrected.
Source: T4, GL. Confidence: Low.

**A-36** | 2026-11-18 | The Atlas launch kit is only available as v1 (21 Jul); no later version is assumed to exist.
Source: Atlas_Launch_Kit_v1.pdf. Confidence: Medium.

**A-37** | 2026-11-19 | Priya Nair has resigned (reported 19 Nov by the CEO), but this is **unconfirmed**: Keka and the other HR exports are dated 31 Oct and no letter is in the data room.
Source: T6d. Confidence: High that the CEO said it; unknown that it is final. Would change my mind: a letter, or Keka showing a notice status.

**A-38** | 2026-11-19 | The notice period is unknown. Two readings are shown: "two months" from 19 Nov (last day 19 Jan 2027) and the one precedent in the records, 46 days (last day 4 Jan 2027).
Source: T6d "two months, I think"; Resignation_Letter_SM.pdf (15 Sep to 31 Oct). Confidence: Low. Would change my mind: a contract or an HR note.

**A-39** | 2026-11-19 | "Slag" in T6c is Slack, and "Deepa says it's fine" is ambiguous (messages or attrition).
Source: T1 "slag channel", T1 "Deepa says it's normal". Confidence: Medium. The answer to the request is the same under either reading.

**A-40** | 2026-11-19 | Impact figures use the same windows as the Atlas pace finding: points closed since 1 Jul, commits in the last 90 days (from 2 Aug), all measured to the 31 Oct exports.
Source: own convention, consistent with A-28. Confidence: Medium.

**A-41** | 2026-11-19 | No new GA date can be derived from the records, so none is stated; the estimate belongs to the VP Engineering.
Source: DECISIONS D-26. Confidence: High.

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

**REVISED 2026-11-19 - A-P07 Priya Nair (third time).** Day 4: the CEO reports that Priya resigned. The persona overlay now says Priya has resigned, is worried about the handover of the routing core, has not said why to anyone and has not agreed the notice period. All of that is fiction except the report itself. Her half-day leaves are still not interpreted (A-26), and the Day 3 findings were about work concentration, not intent: I do not claim they predicted this.

**REVISED 2026-11-19 - A-P05 Deepa Joshi.** Day 1 invented that she privately doubts "attrition is normal". T3 and email 11 now show she told the CEO she was worried about one engineer and that engagement had dropped, so the invention is closer to the records. Still fiction beyond them.

**REVISED 2026-11-18 - A-P07 Priya Nair (again).** Day 3 shows her late nights are real (commits between 22:00 and 06:00 IST from June) and that she owns 56% of the Atlas points. The Day 3 persona overlay now says so and keeps the recruiter and physiotherapy inventions, which stay fiction. Her half-day leaves are still not interpreted (A-26): the leave register and the commit hours are separate facts.

**REVISED 2026-11-18 - A-P12 Sneha Kulkarni.** Day 1 said "considering leaving over on-call" was invented. The records now show she was on call every week and handled every SEV1, so on-call fatigue is grounded; "considering leaving" remains invented and is dropped from the overlay.

**REVISED 2026-11-18 - A-P04 Vikram Menon.** The Day 3 overlay has him optimistic in conversation while his own Jira change moved the GA by 13 weeks. That reading is an invention to give him a voice; the records only show the two facts.

**REVISED 2026-11-18 - A-P06 Nikhil Bose.** Day 1 "defensive about numbers" is now grounded in T4 ("finance counts things differently") and in his unreconcilable "one point eight". The CRO worry is invented.

**REVISED 2026-11-18 - A-13 / A-09.** Email 06 was copied to the CEO and the Talent Partner (my Day 2 loader had dropped the Cc header). A-09 "Vicky" stays at Medium; nothing new on it.

*Revisions go here, newest first.*
