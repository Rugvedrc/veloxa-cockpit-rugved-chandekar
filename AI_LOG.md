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

**Things I decided myself, not the AI**
- Which source to believe when they conflict: each entry in TRANSCRIPT_NOTES.md was reviewed by me; the AI proposed, I accepted or changed. (To be filled in with my own reasoning where I disagreed.)

**To do:** log every future AI session here, including the wrong answers.
