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

**Things I decided myself, not the AI**
- Which source to believe when they conflict: each entry in TRANSCRIPT_NOTES.md was reviewed by me; the AI proposed, I accepted or changed. (To be filled in with my own reasoning where I disagreed.)

**To do:** log every future AI session here, including the wrong answers.
