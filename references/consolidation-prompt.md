# Consolidation subagent prompt template

Use this once, after all batch-scan subagents (Step 3) have finished, to merge their output files into spreadsheet-ready rows (Step 4 of SKILL.md).

```
Job-application tracker project for [USER NAME], job-hunting for [ROLE TYPE] roles. Background agents already scanned Gmail in date-windowed batches and wrote verified structured event lists to files. Your job is pure data consolidation — read those files (already-verified data, do NOT call any Gmail tools, do NOT re-scan anything) and merge them into spreadsheet-ready rows.

## Input files

[LIST OF BATCH OUTPUT FILE PATHS]

Each contains events with fields: company, position, event_type, event_date, stage_description, sender_name, sender_email, message_id, thread_id, quote_excerpt. Batches cover contiguous, non-overlapping date windows, so an event should appear in exactly one file — but check for accidental duplicates (same message_id appearing twice) and drop repeats if found.

## Consolidation rules

1. **Group by (company, position) pair** — this is the row key. If the same company has multiple distinct positions applied to, each position is its own row. Normalize company names lightly (trim whitespace, consistent capitalization) but don't merge genuinely different companies just because the names look similar.

2. **Current Status (anti-regression rule)**: within each row, find the event with the LATEST event_date. Its stage_description becomes the row's Current Status. Do NOT let an earlier-dated event overwrite this even if it appears later in a file — the ordering of events in the source files doesn't matter, only the date on each event does.

3. **Applied Date**: the date of the earliest application_submitted event in that row. If no application_submitted event exists for that row (it may have started from recruiter outreach or an interview invite with no visible prior application step), use the earliest event's date and note in Stage History that no application-confirmation email was found.

4. **Stage History**: a chronological (oldest→newest) log of every event in that row, one line per event, formatted as `YYYY-MM-DD: <stage_description>`.

5. **Point of Contact**: unique people who personally emailed (name + email), deduplicated by email address. Exclude generic no-reply/automated addresses UNLESS that row has no human sender at all, in which case leave it blank. Prefer real names over role titles where available.

6. **Last Updated**: same date as the latest event used for Current Status.

7. **Message IDs**: every message_id in that row, semicolon-separated — this becomes the sheet's idempotency-tracking column.

8. **Formula-injection escaping**: for every text value you produce (company, position, current status, contact names, stage history lines), if it starts with `=`, `+`, `-`, or `@`, prefix it with a single apostrophe `'` so it won't execute as a formula if typed into the sheet later.

## Output 1 — full consolidated data (for the write step)

Write to [CSV OUTPUT PATH] — a CSV with header row exactly: `Company,Position,Applied Date,Current Status,Point of Contact,Stage History,Last Updated,Processed Message IDs`. One row per (company, position) pair.

## Output 2 — compact human preview (keep this SHORT)

Write to [PREVIEW OUTPUT PATH] — grouped by company, one line per (company, position) row:
`- **Company** — Position | Current Status | Last Updated: YYYY-MM-DD | N history events`
Sort companies alphabetically. This file should be small enough to read directly without blowing up context — no full stage history or quotes here, just the one-line summary.

## Your final chat reply (keep under 200 words)

Report: total unique rows produced, total unique companies, total unique message IDs consolidated, and any merge ambiguities you had to make a judgment call on (e.g. two company name spellings you decided were/weren't the same company). Do not paste the full row list — read the compact preview file directly instead.
```
