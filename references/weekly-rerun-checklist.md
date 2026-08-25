# Weekly re-run checklist

Run through this on every regular re-run ("update my job application tracker"), not just the first time you set this skill up. Every item here exists because of a real failure caught in production on a live ~500-row tracker (2026-08-24 session) — skip these and you're re-risking the exact bugs that already happened once, silently.

## Before writing (diff verification)

1. **Lookback window is ~1 week**, not the old ~2-week default (SKILL.md Step 2). If it's noticeably longer or shorter than that without the user asking for a different window, double-check why.
2. **Every row the consolidation pass calls "NEW" gets verified against the LIVE sheet**, not just the Drive `read_file_content` dump — search company + position in the Sheets app's own Find dialog (Cmd/Ctrl+Shift+H, `⌘/Ctrl+Shift+H` opens Find & Replace). Do not skip this because the dump "looked complete": on a 492-row sheet, `read_file_content` silently truncated to ~310 rows with no error, which made 8 already-recorded rows look brand new. If this diff pass isn't at least spot-checking new rows this way, it's not verified.
3. **If the user reports a specific missing thread** ("I had a call with X, why isn't it there"), don't just patch that one row. Search Gmail by company name directly (not by re-running the keyword net) and consider whether the same wording gap plausibly missed other companies too.

## After writing

4. **Row count grew by exactly the number of rows written**, and no scratch/helper column was left behind (a rank column added for sorting, typically the first empty column past `Processed Message IDs`).
5. **Sort order is correct**: scroll the top ~10 rows and confirm Last Updated values are non-increasing. Current rule (as of 2026-08-24): Last Updated descending, then Applied Date descending as tiebreaker — see SKILL.md Step 6. If that's no longer the documented rule when you read this, trust SKILL.md over this checklist and update this file to match.
6. **Anti-regression spot check**: pick one updated row and confirm its Current Status reflects the event with the LATEST date in Stage History, not whichever event happened to be processed last in the pipeline.

## Keyword net regression (periodic, not every run)

7. The keyword net keeps growing as real misses get reported — see SKILL.md Step 3 ("talent manager" was added 2026-08-24 after a real miss on a Synthesia thread whose wording never matched "recruiter"/"interview"/"offer"). It will never be complete. If it's been a while since the user last spot-checked, ask "anything I might have missed?" rather than assuming coverage is solid.

## When this checklist itself might be wrong

This file describes the rules as of 2026-08-24. If SKILL.md's Step 2 lookback, Step 6 sort rule, or Step 3 keyword net disagree with what's written here, SKILL.md is the source of truth — update this checklist to match rather than following it blindly.
