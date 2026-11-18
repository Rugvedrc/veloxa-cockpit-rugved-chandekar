# AI_LOG

Main tasks given to AI, where it was wrong, and what changed. Honest entries only; I own everything here and must be able to explain it without AI.

## 2026-11-16 (Day 1)

**Tasks given to AI (Claude Code):** read the brief and the Day 1 data room; design the SQLite model; write loaders, entity resolution, computed checks, the cockpit answer engine, 14 agent personas, the web UI, tests, and the first drafts of ASSUMPTIONS / TRANSCRIPT_NOTES / DECISIONS.

**Where the AI was wrong, and what was changed**

| # | Mistake | How it was caught | Fix |
|---|---|---|---|
| 1 | Loader regex `[\d.]+` matched the "." in "Rs." and crashed on the board PDFs | First build failed | Regex changed to `\d+(?:\.\d+)?` |
| 2 | Wrote the Google Ads total as "~Rs 5.2 L"; the five invoices sum to Rs 4.24 L | Re-added the GL rows by hand | Corrected in claims.json |
| 3 | Finding text claimed AWS cost was growing "7x faster" than revenue, comparing a 5-month change to a 1-quarter change | Re-read the finding critically | Reworded to state both figures and the unequal periods |
| 4 | Flat-payroll finding mentioned "leave and a resignation" that had not been seen yet | Checked what Day 1 contains | Removed the unsupported claim |
| 5 | Recruiter-fee finding stated the unpaid balance as fact | Narration only says "50% advance" | Made it conditional ("if split 50/50") |
| 6 | Build loaded Day 2-4 files already present in the zip, so Day 1 answers could use unreleased material | Saw 11 emails loaded on a Day 1 build | Added release-date gating (`--as-of`) |
| 7 | Payroll totals listed months alphabetically (Feb, Jan, Mar) | Read the test output | Ordered by insertion row |
| 8 | Offline agent reply pasted raw email text, quoting itself in third person | Ran an interview | Rewrote email facts in first person |
| 9 | First summary to me said the Day 2/4/8 reviews were live sessions; the HR email says there are none | Read the HR email | Plan changed to async deliverables |

| 10 | Defaulted the NVIDIA provider to a Llama model from memory; it had been retired (HTTP 410) | Live test | Listed live models from the API; switched default to a current one |
| 11 | The chosen reasoning model returned empty text (it used all tokens thinking) | Live test | Disabled thinking for that model; empty replies now count as a failure |
| 12 | First live agent replies invented facts ("4 incidents", "on-call since 22 Aug 2025", "few customers live") | Compared replies with the records | Stricter prompt, lower temperature, and a check that retries then discards replies containing numbers not in the agent's records |

| 13 | Setup assumed the data room sits next to my project folder, so a fresh clone would fail | Planning review against HR's "tested from a fresh clone" line | `--data` accepts a folder or the zip; location remembered; clear error listing where it looked |
| 14 | Wrote f-strings that nest the same quote type (works only on Python 3.12+) | Review before submission | Rewrote them; added a tokenizer-based test that fails if the pattern returns; proved the test catches it on a bad sample |
| 15 | Assumed Python 3.10/3.12 were installed because `py -0` listed them; they are not | Tried to run them | Could not test on 3.10; relied on the guard test plus parsing every file with the 3.9 grammar |
| 16 | Keyword fallback answered "Who won the cricket world cup?" with the CEO transcript because it contains the word "world" | New 35-question test set | Require >= 2 whole-word matches in one record |
| 17 | "Why did AWS go up?" got High confidence although the data only shows the trend | Same test set | "Why" questions now say "I can't say why", Low confidence |
| 18 | "Will Priya quit?" was routed to the attrition handler and listed the one departure as if it were an answer | Wrote the refusal tests | Added a prediction handler that declines and states what is on record |
| 19 | Conflicts list included a claim (C03) that actually agrees with the records | Read every answer | Limited the list to real mismatches and mishearings |

## 2026-11-17 (Day 2)

**Tasks given to AI:** read the Day 2 material; write loaders for the tracker, leave register, survey and resignation letter; extend findings, claims and agents; build the top-three screen for voice note T6a; write tests and the first drafts of VOICE_NOTES.md and the Day 2 notes.

| # | Mistake | How it was caught | Fix |
|---|---|---|---|
| 20 | A Day 1 alias row referred to a Day 2 file ("Resignation letter (Day 2)"): a leak I wrote on Day 1 | Reviewing what an alias table should contain before adding Day 2 aliases | Aliases and claims now carry release dates; added a leakage test |
| 21 | Wrote Day 2 facts straight into the persona text, so a Day 1 interview would know them | Re-reading the diff | Day 1 text kept as the base, Day 2 text moved to `_d2` overlays applied only when Day 2 data exists |
| 22 | First idea for ranking themes: sum of severities. It would put "money" first because it has many tiny items | Ran it on the real findings | Rank by maximum severity, tie-break by the CEO's stated main concern |
| 23 | My own Siddharth persona ("accepted a competitor offer") was contradicted by his letter | Reading the letter | Revised, with the original kept in the history (ASSUMPTIONS) |
| 24 | A finding said "nobody was lined up" for the backfill while the tracker shows 7 candidates | Re-reading the finding text | Reworded to "no successor was in place" |
| 25 | The pulse caveat hard-coded "3.9 to 3.1" instead of computing it | Reading the handler | Computed from the rows |
| 26 | Draft of the CEO response said the launch kit was "only handed over on paper" and that payroll was "never corrected": neither is in the records | Checking each sentence against a source | Reworded to what the records say |
| 27 | A live agent (Rohan) invented a reason for the hiring pause ("until Atlas ships") | Live test | Prompt rule not to explain causes unless the records do; guard extended to number words |
| 28 | A test forbade the word "reason" but my own caveat ("I don't infer reasons") contains it; another test mislabelled a principled refusal as "uncertain" | Test failures | Fixed the expectations and added a separate "decline" category |

## 2026-11-18 (Day 3)

**Tasks given to AI:** read all Day 3 material; analyse git, Jira, incidents and the rota; write loaders and findings; reconcile T4 and T5; build dated reporting lines and a reorganisation test for T6b; write tests, VOICE_NOTES and the Day 3 notes.

| # | Mistake | How it was caught | Fix |
|---|---|---|---|
| 29 | My Day 2 loader dropped the Cc header, so the CEO's copy of the 12 Aug hiring pause was invisible | Reading the printed email copy next to the .eml files | Loader keeps Cc; claim C52 revises C28; finding and answers mention it |
| 30 | First draft of the concentration finding said "103 of 588 since", mixing two denominators, and floored percentages (70% showed as 69%) | Re-reading the finding | Fixed the denominators and rounded properly |
| 31 | Two findings hard-coded facts ("none were resolved in October", "hardening is the least finished epic") | Re-reading | Both are computed from the rows |
| 32 | A nested "Snehal (S. Patil)" in parentheses and "owner left" when the data only says he was due to leave | Re-reading | Reworded to what the records say |
| 33 | I defined `run_all` twice in checks.py, so the older list would have won | Noticed the new findings missing in a trial run | Removed the duplicate |
| 34 | The first version of the T5 finding said the VP "contradicted himself". T5 is undated, so I cannot say he spoke after 2 Sep | Re-reading the transcript | Reworded to the size of the gap (a couple of weeks vs 13) and set Medium confidence |
| 35 | "burn" matched "burnout" and the burn-rate answer fired; "burned out" missed the workload handler | Trying questions | Word boundaries and a wider workload pattern |
| 36 | Handlers for launch kit, incidents and Jira answered with unrelated Atlas text before those files were released | Trying the same questions at 17 Nov | Explicit "I don't have X as of this date" answers |
| 37 | The reorganisation test found that someone added to the data was not recognised by name until a rebuild, and that a department called "Revenue" was read as the revenue figure | `tests/test_reorg.py` | Name lookup also reads the people table; the revenue pattern is stricter |
| 38 | A test forbade the word "Jira" in a Day 2 answer that correctly says Jira "isn't loaded yet" | Test failure | Test now checks for the Day 3 facts instead |

**Things I decided myself, not the AI**
- Which source to believe when they conflict: each entry in TRANSCRIPT_NOTES.md was reviewed by me; the AI proposed, I accepted or changed. (To be filled in with my own reasoning where I disagreed.)

**To do:** log every future AI session here, including the wrong answers.
