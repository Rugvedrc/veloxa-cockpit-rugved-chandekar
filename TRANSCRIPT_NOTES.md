# TRANSCRIPT_NOTES

Everything that looks misheard, or that contradicts another source. The machine-readable copy lives in `data/curated/claims.json` and appears in the cockpit under "Conflicts in the sources". Keep the two in sync.

> **Owner's review (Rugved Chandekar):** the conclusions below were first drafted with AI help. HR requires the reasoning behind every conflict to be mine. Before submitting, read each row, change anything you disagree with, and record the date you reviewed it here: ____________.

Rule used throughout: **system exports beat transcripts for facts; transcripts beat exports for intent and context.** A speaker is also assumed to be biased towards their own team's story.

## T1 - CEO kickoff call (Ananya R.) - audio quality fair

| # | Heard | Concluded | Evidence | Conf. |
|---|---|---|---|---|
| T1-1 | "roughly eighteen people ('one-eighty, give or take')" | **19 people**. The brief's "180" is also wrong. | Employee_Master (19 rows); both board updates "Team 19" | High |
| T1-2 | ARR "forty-two crore, maybe forty-five now" | Rs 5.8 Cr (Jun) / 6.1 Cr (Sep). CEO's figure matches nothing, and is below the CFO's start-of-year 4.8 Cr. | Board updates; T2 | Medium |
| T1-3 | "Linear, I think, or they moved back to the Jeera board" | **Jira** (project ATLAS). Linear unconfirmed. | README: "Jira (ATLAS)" | High |
| T1-4 | "Git Hub", "Cult Amp", "slag channel", "hub sport export" | GitHub, Culture Amp, Slack, HubSpot | README (Culture Amp); others by sound | High / Medium for HubSpot |
| T1-5 | "Pria basically holds the routing thing together" | **Priya Nair** (VX007, Staff Engineer) | Only Engineering Priya; role fits | High |
| T1-6 | "the new boy Rahul" | **Rahul Verma** (VX018), joined 2026-02-03 | Employee_Master | High |
| T1-7 | Burn "around two point two" (unit missing) | Rs 44-46 lakh/month; 2.2 lakh impossible | GL payroll Rs 31.75 L/month; board 46 L, 44 L | High |
| T1-8 | Routing engine "version three" promised "by the festive season" | Atlas GA was 15 Sep, then moved with no new date | Board Apr-Jun vs Jul-Sep | Medium |
| T1-9 | "attrition feels high but Deepa says it's normal" | Untestable: Keka lists current staff only | Employee_Master | Low |
| T1-10 | Speaker 2: board wants "the number by March" | Unknown which number. Not acted on. | none | Low |
| T1-11 | "Marketing spend is fine" | Unverified, possible CEO optimism. GL shows Summit Rs 10.03 L split over two lookalike vendors | GL JV-0846, JV-0904 | Low |
| T1-12 | Action: "Send the hub sport export (owner Speaker 2)" | Nothing in the data room is a CRM export. Noted as a missing source. | Data room listing | Medium |

## T2 - CFO call (Meera I.) - audio quality poor (speakerphone)

| # | Heard | Concluded | Evidence | Conf. |
|---|---|---|---|---|
| T2-1 | "FY twenty-six (maybe twenty-seven)" | Current year is Apr 2026 - Mar 2027 (FY27). Use calendar dates. | GL Apr-Sep 2026 | Medium |
| T2-2 | ARR at start of year "forty-eight" | Rs 4.8 Cr (crore assumed) | Board growth path 4.8 -> 5.8 -> 6.1 | Medium |
| T2-3 | Burn "two point two lakhs, sometimes two point five" | Same as T1-7. Probably "forty-two / forty-five". | as above | High that it is wrong |
| T2-4 | "Joho books", "Kayka" | Zoho Books, Keka | README | High |
| T2-5 | Books moved Tally -> Zoho "sometime in Jan, or Feb" | **Unresolved.** Zoho GL starts Apr; Jan-Mar payroll is from a separate pre-Keka workbook. No Tally data. | GL and register file notes | Low |
| T2-6 | "Individual salaries must never show up in anything Ananya sees" | Hard design rule (see DECISIONS D-05) | T2 | High |
| T2-7 | "Kartik", "Fatima Shaikh" | Karthik Subramanian, Fatima Sheikh | Employee_Master | High |
| T2-8 | "Fatima out for her wedding, that month was messy" | **February 2026**: Karthik ran payroll (email 01) and Rahul was paid 28/28 days though he joined 3 Feb | 01.eml, register Feb rows | High |
| T2-9 | "the two backend roles" | Cohere Recruiting Partners, 50% advance Rs 1.77 L on 30 Jun. Roles look unfilled; hiring now paused. | GL JV-0688, board updates | Medium |
| T2-10 | "Nikhil's numbers never match mine" | Open. Candidate cause: lookalike vendors Sapphire / Saphire. | GL | Low |
| T2-11 | Action: "Check the freeze decision with Vicky" | "Vicky" unresolved (see A-09) | none | Low |

## Contradictions between written sources

| # | What disagrees | What I did |
|---|---|---|
| S-1 | Brief says 180 people; Keka and board say 19 | Believe the exports. Flag to the CEO in every headcount answer. |
| S-2 | Q2 board "two backend engineers this quarter" vs Q3 "hiring paused" and no joiners | Treated as a slipped commitment; recruiter fee shown as exposure. |
| S-3 | Payroll register Jan-Mar total Rs 30.65 L (Jan), 31.75 L (Feb, Mar) vs GL flat 31.75 L Apr-Sep | Reported both, flagged the flat line as likely copy-forward. |
| S-4 | Rahul's Feb days payable (28) vs join date (26 days employed) | Computed generally in checks.py, so any other proration error would also appear. |
| S-5 | Board says "one planned departure in marketing" vs Keka listing Siddharth Mehta on notice, exit 31 Oct (the export date) | Consistent; treated as the same person. |

## Things that look like mistakes but may not be

- Voucher numbers out of date order (JV-0903 / JV-0904, JV-0918 / JV-0921): flagged FYI only. Could be late entry.
- "Sapphire Residency Hotel" vs the event vendors: looks like a duplicate, is almost certainly a different business. Kept separate.
- Jan payroll has 18 rows, Feb-Mar 19: correct, Rahul joined 3 Feb.
- Employee_Master has no leavers: not an error, Keka exports active records.

## Day 2 additions (released Tue 17 Nov)

### T3 - Head of People call (Deepa J., Ananya R., Rohan) - audio quality good

| # | Heard | Concluded | Evidence | Conf. |
|---|---|---|---|---|
| T3-1 | Attrition "about twelve, which is normal for Bangalore" (percentage, headcount or target unclear) | Untestable. 12 people is impossible; 12% is about 2 a year; the HR export has no leavers. One departure is known. | Employee_Master; resignation letter | Low |
| T3-2 | "twenty-two open roles in April", "we lost six of them in August" (Rohan) | Wrong for this company. The tracker has 6 requisitions in total; 2 went on hold in August. "Twenty-two" may be "two". Tracker wins. | Hiring_Tracker R4-R9 | High |
| T3-3 | Offer acceptance "down to fifty-something" | No offer data exists. Not used. | Hiring_Tracker | Low |
| T3-4 | "Liver", "Kekka", "Cult Amp" | Keka Hire, Keka, Culture Amp | Tracker title row; README | Medium |
| T3-5 | Engineering scores "dipped in the July round" | Confirmed: 3.9 -> 3.1, 4 of 5 responded. Biggest drop of any team. | Pulse_Survey; email 11 | High |
| T3-6 | "Lakshmi as HRBP, she handles exits" | Keka title is HR & Office Executive; the letter went to Siddharth's manager. Informal description; Keka title kept. | Employee_Master R20; letter | Low |
| T3-7 | "Sid from marketing has put in his papers" | Siddharth Mehta, letter 15 Sep, last day 31 Oct | Resignation_Letter_SM | High |
| T3-8 | "one engineer I'm worried about" (not named) | Left unnamed on purpose (DECISIONS D-16) | T3 | n/a |
| T3-9 | Manager training "November-ish" vs Rohan "January" | Unresolved; both reported | none | Low |
| T3-10 | Wants the CEO to "see survey comments directly" | Not possible: comments are hidden for every team (all under 6). Not worked around. | Pulse_Survey Comments column | High |

### T6a - CEO voice note
"When I open it, it should just tell me what to worry about. Top three." Handled as a requirement, not a fact to reconcile; response in VOICE_NOTES.md.

### Revisions to Day 1 rows (the originals above are kept)
- **T2-9 / T2-11 ("the two backend roles", "check the freeze with Vicky").** Now confirmed by the tracker and emails 06 and 07: REQ-014 and REQ-015, on hold since 12 Aug on the CFO's burn decision, VP Engineering replying "We'll absorb it". That is the freeze T2 said to check "with Vicky", so "Vicky" is more likely Vikram Menon (Low -> Medium).
- **T1-9 (attrition).** Still untestable, now with a date: the one known departure resigned on 15 Sep.
- **T2-8 (Fatima's wedding).** Confirmed by the leave register: 15 days of marriage leave, 9-27 Feb, which also explains who ran February payroll.

### New contradictions between written sources
| # | What disagrees | What I did |
|---|---|---|
| S-6 | Q3 board update: "Hiring is paused" vs tracker: only 2 roles on hold, 2 opened since (REQ-016, REQ-017) | Believed the tracker. Reported as a finding. |
| S-7 | Q2 board "two backend engineers this quarter" vs tracker: both opened 18 May and on hold from 12 Aug | Consistent; the plan was frozen, not abandoned. |
| S-8 | Resignation letter date (15 Sep) equals the Atlas GA date in the Q2 board update | Reported as a fact; no causal claim beyond the letter's own stated reason. |

### Things that look like mistakes but may not be
- The leave register uses initials ("P. Nair") and approver codes ("VM"); matched by first initial + surname and by name initials. Unmatched would be reported, not guessed (none were).
- Pulse "Comments: Not shown: team smaller than 6" on every row is a privacy rule, not missing data.
- Priya Nair has five half-day PM leaves in September. Not interpreted (D-16).

*Revisions go here, newest first.*
