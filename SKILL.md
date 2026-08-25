---
name: job-application-tracker
description: Builds and runs a semi-automated job-application tracker that scans a user's Gmail inbox for job-application-related emails (application confirmations, rejections, interview invites, take-home assignments, offers, recruiter outreach) and syncs approved changes into a Google Sheet, with a human approval step before anything is written. Use this skill whenever the user wants to track job applications, build or update a job search tracker, sync Gmail to a spreadsheet for job hunting, or asks things like "scan my inbox for job applications," "update my job tracker," "check for new interview emails," "did I hear back from any companies," or "build me a spreadsheet of everywhere I've applied" — even if they don't use the words "tracker" or "automation." Also use it when a tracker already exists and the user wants a routine refresh ("check for updates," "anything new since last week").
---

# Job Application Tracker

A semi-automated, on-demand workflow: scan Gmail for job-application activity, compute what would change in a Google Sheet, show the user a preview, and only write after they approve. Nothing runs on a schedule — every run is triggered by the user asking for it, in-session.

This skill exists because a naive version of this workflow is easy to get badly wrong at real scale: a single big Gmail scan hallucinates data, a keyword search misses non-English correspondence, and a raw text approval preview becomes unreadable past a few dozen rows. The steps below encode the fixes for each of those failure modes, learned from a real run. Don't skip them because they seem like overkill for a small inbox — you don't know the inbox is small until you've scanned it, and the failure modes above degrade silently (they don't error, they just produce wrong data that looks plausible).

## Before the first run: confirm the environment

1. **Gmail read access** — confirm Gmail tools are available (search/read messages). If not connected, walk the user through OAuth.
2. **Sheet write path** — check what's actually available for writing structured data to a spreadsheet in this environment:
   - If a dedicated Sheets-write API/MCP tool exists, use it — it's faster and less fragile than the fallback below. Skip the browser-automation guidance in Step 5 entirely.
   - Otherwise, assume the common case: a Drive-style file API that can *create* a spreadsheet and *read* its content, but cannot update cell content (only metadata like title). In that case, reads go through the read API and **writes go through live browser automation of the Sheets web UI** — see Step 5.
3. **Browser automation access** (only needed if using the fallback write path) — confirm a browser-automation tool is connected before promising the user a write will happen. If it isn't, say so plainly and stop before Step 5 rather than discovering it mid-write.

## Step 1 — First-time setup

If no tracker sheet exists yet, ask the user (don't guess):
- **Column language** — what language should the sheet itself be written in? Default to matching the language the user is chatting in, but confirm since this differs from the language of their source emails.
- **Any columns beyond the default set** (below), or is the default fine?

Create the sheet with one row per (company, position) and at minimum these columns — the last one is implementation-only, not something the user asked for, but essential for not re-processing the same email twice:

`Company | Position | Applied Date | Current Status | Point of Contact | Stage History | Last Updated | Processed Message IDs`

Why (company, position) as the row key: the same company commonly has multiple concurrent applications for different roles — collapsing them into one row loses information.

Confirm the sheet is created **private by default** — recruiter names and emails accumulate in this sheet, which is third-party personal data. Don't share it with anyone as part of this skill; that's the user's call to make explicitly, separately.

## Step 2 — Decide scan scope

Ask the user, don't assume:
- **First run**: what lookback makes sense for how long they've been job-hunting? A common default is several months, but let them pick — and explicitly tell them what window you used once you land on one, so they can flag if it's not enough.
- **Regular re-runs** (tracker already exists): default to a short fixed lookback (commonly ~1 week) rather than tracking "scan since the row's last-updated date" per row — that per-row approach sounds more precise but adds real complexity for a personal on-demand tool. The trade-off: if the user skips more than the lookback window between runs, a slow-moving thread could fall outside it and get missed silently. That's an acceptable trade for this tool's scope — mention it once, don't re-litigate it every run.
- **Correspondence language(s)**: ask what language(s) their job search emails are likely in. This matters more than it sounds like it should — see the language gap note below.

## Step 3 — Scan Gmail in date-window batches (do not skip this)

**Why batching, not one big scan:** a single extraction pass across a large result set (order of 150+ threads) is where things go wrong — not gracefully, but by fabricating a plausible-looking event that never happened, and by corrupting IDs when a long-running pass tries to self-correct mid-stream. Both failures are invisible unless you go check individual entries against the source inbox. Splitting the lookback window into smaller batches (recent weeks split finer since job-search email volume clusters heavily in the last few weeks of an active search, older months in single monthly windows) keeps each individual pass small enough to stay reliable.

For each date window, dispatch a separate subagent (don't do this inline in the main conversation — see "why delegate" below) with a query combining:
- Common ATS/job-platform sender domains (Greenhouse, Lever, Workday, iCIMS, Ashby, SmartRecruiters, Jobvite, Breezy, Taleo, Workable, and any locally-relevant ones for the user's region/language)
- English keyword net: application, interview, position, role, offer, "next steps", recruiter, recruiting, hiring, candidacy, "thank you for applying", "talent manager", "talent acquisition", "talent team"
- **If the user's correspondence includes a non-English language, add a second keyword net in that language, in the same query or a supplementary one, covering the same date window.** This is not an edge case — an English-only net will silently miss an entire language's worth of recruiting correspondence, including deep multi-stage processes (interview rounds, final rounds, rejections), because neither the subject-line keywords nor the sender domains will match. Confirm this doesn't just quietly happen — actually check for it once by running a supplementary sweep for the user's other language(s) across the full lookback window, even after the main batched scan is "done."
- **The keyword net can miss a real, substantive thread even in the user's own language if its wording is generic enough to dodge every literal keyword.** Caught one for real: a company's own "meet a Talent Manager" outreach + scheduled call + the user's own follow-up — three real messages over two weeks, entirely missed by a scan whose net included "recruiter"/"interview"/"offer" but not "talent manager," because the subject and body never used any of those exact words ("Product opportunity," not "role"; "call," not "interview"). This is a fundamentally open-ended problem — you cannot enumerate every phrasing a company might use — so treat the keyword net as a floor, not a ceiling: if the user ever says "I had a call with X, why isn't it in the tracker," that's a signal to search Gmail for that company by name directly (not just re-run the keyword net) and add whatever the net missed, the same way `talent manager` got added here after this exact incident.

See `references/batch-scan-prompt.md` for a full, copy-adaptable subagent prompt including the exact anti-hallucination instruction and inclusion/exclusion criteria for what counts as a real candidate event vs. noise (job-hiring newsletters, digest emails, unrelated calendar invites, etc. — these share keywords with real signal and need judgment, not just pattern matching).

**Anti-hallucination rule (put this in every batch subagent's prompt, verbatim in spirit):** every message ID, thread ID, and date must be copied from an actual tool result received in that same context — never reconstructed from memory, never guessed by analogy to a similar-looking entry seen earlier. If a field isn't clearly stated in the source email, mark it `UNVERIFIED` rather than inventing a plausible value. Accuracy on a smaller batch matters more than completeness.

**Why delegate to subagents instead of scanning inline:** the raw email content for a real scan is large — pulling it all into the primary conversation blows up context with data you don't need again after extraction. Have each batch subagent write its structured output to its own file and report back only a short count summary in chat (total events, total excluded as noise, anything marked UNVERIFIED) — never the full extracted list.

## Step 4 — Consolidate into rows

Once all batches finish, dispatch one more subagent (again, to keep raw batch data out of the main conversation) to read all the batch files and merge them into spreadsheet rows, applying these rules:

- **Group by (company, position).** Normalize obvious name variants (e.g. the same company appearing as "Foo Inc.", "Foo", "Foo, Inc.") but don't merge genuinely different companies just because they're superficially similar.
- **Current Status = the event with the latest date, full stop.** Never let an earlier-dated event overwrite this just because it was processed later in the pipeline — this is the single most important correctness rule in the whole system, because getting it wrong means the sheet actively lies about where things stand.
- **Applied Date** = earliest `application_submitted`-type event for that row; if none exists (the process may have started from a direct recruiter conversation with no separate confirmation email), use the earliest known event's date and note that explicitly in the history.
- **Stage History** = full chronological log, oldest to newest, one line per event.
- **Point of Contact** = real named people who personally emailed (name + email), deduplicated by email address — not generic no-reply/ATS addresses. Leave blank if the row has no human contact at all.
- **Formula-injection escaping**: any text value that starts with `=`, `+`, `-`, or `@` gets a leading apostrophe `'` prefix before it's ever typed into a cell. This isn't optional — a company name or sender name starting with one of those characters will otherwise execute as a spreadsheet formula.
- **Message IDs**: carry every source message ID for that row through into the sheet's tracking column — this is what makes re-scans idempotent.

**On a regular re-run (tracker already has a live sheet), do not trust a single Drive `read_file_content` call of that sheet as "the existing data" — it silently truncates for large sheets with no error.** Hit this for real on a 492-row sheet: the read returned only the first ~310 rows (whichever rows happen to sort first), and a consolidation subagent that diffed new events against that truncated read produced 8 false "new rows" that were actually already sitting past row 310 — an entry that would have written real duplicates into the sheet. The tool gives no signal that it truncated; the row count just quietly comes up short. Before treating any event as genuinely new (or, worse, writing it), verify company+position isn't already in the sheet using the Sheets app's own Find dialog (⌘/Ctrl+Shift+H — searches ALL live rows, not a partial read) rather than trusting matches/misses against a Drive-read dump alone. For a small diff (a couple dozen candidate rows) checking each one this way is cheap; for a large first-time scan this isn't practical per-row, but the same truncation risk still applies to any Drive read of a large sheet, so treat "no match found" from a truncated read as inconclusive, not as proof a row is new.

Have this subagent produce two outputs: the full data (e.g. a CSV matching the sheet's columns exactly) for the eventual write step, and a compact one-line-per-row preview file you can read directly without blowing up your own context.

## Step 5 — Show the user an approval preview *before* writing anything

**Do not write to the sheet without this step**, and don't skip straight to describing the changes in prose once row counts get non-trivial (more than roughly 20-30 rows). At real scale (a genuinely active job search can easily produce several hundred rows across the first big scan), a text wall in chat is unreadable and defeats the entire point of a human approval gate — the user can't meaningfully review what they can't see.

For anything beyond a trivial row count, build an HTML artifact instead:
- Load the artifact-design skill first if this environment has one, and treat this as a utilitarian dashboard, not an editorial page — the job is to let someone scan and verify data, not to impress.
- Group by company (collapsible), with each row showing position + status + last-updated at a glance, expandable to show full stage history, point of contact, and evidence (message count / IDs).
- Add search and status filtering — a reviewer needs to be able to jump straight to "what's currently active" or search a specific company, not scroll linearly through everything.
- Generate the data as JSON from the consolidated CSV via a script (not by hand-copying rows into the page) and splice it into an HTML template — see `assets/approval-preview-template.html` for a working starting point (search/filter/expand/collapse, status-pill classification, light+dark theme tokens) and `scripts/build_preview.py` for the CSV-to-JSON injection pattern. Keep raw data out of your own conversation context by doing this generation via a script/subagent, not by reading the full CSV into context yourself.

Approval in this version of the skill is **batch-level**: the user approves or cancels the whole computed diff, not individual rows. This is a deliberate simplification to keep the interaction tractable, not an oversight — mention it if the user seems to expect row-by-row control, and treat per-row approval as a reasonable future extension rather than something you need to build by default.

**If the user spot-checks and finds an error, take it seriously and re-verify, not just patch the one row.** A single wrong entry the user happens to notice is a sample, not the full defect count — go check whether the same failure mode (a language gap, a missed thread, a bad date) plausibly affected other rows too, the way you'd want a bug report treated in any other system. Fix what you find, regenerate the preview, and republish it before moving on.

## Step 6 — Write approved changes to the sheet

If a dedicated write API is available, use it directly with the escaped, consolidated data — this whole step simplifies enormously and you can skip the rest of this section.

Otherwise, using browser automation against the live Sheets UI:

- **The main grid is canvas-rendered — don't try to click or target individual cells via the DOM.** Navigate using the Name Box (the real `<input>` element for typing a cell address like `A5`) plus keyboard entry.
- **Multi-line cell values** (like a stage-history log) need `Alt+Enter` between lines while editing a cell — plain `Enter` commits the cell and moves the cursor, which will scatter your remaining lines into the wrong cells.
- **Before writing each row**, re-read that row's company/position to confirm it still matches what the diff expected. The diff was computed from a snapshot; the sheet may have shifted since (a manual edit, or an earlier row insertion in this same batch pushing things down). If it doesn't match, skip that row and record it as a failure rather than overwriting the wrong data.
- **Partial-failure policy**: apply rows sequentially; if one fails, stop immediately rather than continuing past it, and report exactly what succeeded vs. what didn't. Write the Processed Message IDs for a row immediately after that row succeeds, not batched at the end — that way a resumed/retried run doesn't reprocess and duplicate anything that already landed.
- Given the number of individual browser actions this implies at real scale, warn the user up front if a write is going to be large, and consider chunking the write into checkpointed batches so a long run is resumable rather than all-or-nothing.

**Row order = most recently touched first, not insertion order.** After writing, the sheet should surface whatever the user just heard about first. Sort key, in order:

1. **Last Updated** (descending) — the date of the row's most recent event, whatever it was (a new application, a rejection, an interview, anything). This is the primary key.
2. **Applied Date** (descending) as the tiebreaker for rows that share the same Last Updated date.

(An earlier version of this skill used an openness-tier + interview-depth heuristic instead — offer > actively progressing > pending > closed, prioritizing open applications over recency. Amanda replaced that with the simpler Last-Updated-first rule on 2026-08-24 because she wants to see what just changed, not a computed priority ranking. If you're adapting this skill for a different user, ask which they'd prefer rather than assuming.)

**Re-sort technique**: don't retype every row to reorder a sheet that already has data. Use the Sheets UI's Data > Sort range (advanced) on the full data range (header row included, "Data has header row" checked), with two sort columns: Last Updated descending, then Applied Date descending. This sorts the whole sheet in one operation using the columns that are already there — no scratch column needed, since both keys are plain date columns already in the schema (the openness-tier heuristic this replaced needed a computed scratch-column rank because "tier" and "depth" weren't real columns; a straightforward two-key date sort doesn't).

## Step 7 — After writing

Tell the user what was actually written vs. what (if anything) was skipped or failed, and remind them a re-scan next time will use the short regular-run lookback rather than rescanning everything.

## Explicit scope boundaries (by design, not gaps)

- No scheduled/standing automation — every run is user-triggered in-session.
- No row-level selective approval in this version — batch-level approve/cancel only.
- The user's own sent mail is used as context (to understand thread state) but never generates its own tracked event.
- No calendar integration.
- A missed email (false negative) can't be caught by the approval gate — the gate only catches wrong extractions of things that *were* found, not things that were never surfaced. Treat this as an accepted limitation of an on-demand, non-exhaustive tool, not something to over-engineer around.

## Reference files

- `references/batch-scan-prompt.md` — full subagent prompt template for Step 3, including inclusion/exclusion criteria for what counts as a real candidate event.
- `references/consolidation-prompt.md` — full subagent prompt template for Step 4.
- `assets/approval-preview-template.html` — working HTML/CSS/JS scaffold for Step 5 (search, filter by status, collapsible company groups, expandable rows, light/dark theme).
- `scripts/build_preview.py` — script that converts a consolidated CSV into the JSON the template above consumes, and splices it in.
