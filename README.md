# Job Application Tracker (Claude Code skill)

A semi-automated job-application tracker: on request, it scans your Gmail inbox for job-application activity (confirmations, rejections, interview invites, offers, recruiter outreach), computes what would change in a Google Sheet, shows you a reviewable preview, and only writes to the sheet after you approve. Nothing runs on a schedule — every run is something you ask for.

This isn't a toy version of the idea. It's the result of actually running this workflow end-to-end on a real, active job search (~500 candidate events across 200+ companies over 10 months), hitting the failure modes a naive version runs into at that scale, and fixing them:

- A single big Gmail scan will **hallucinate data** — it can fabricate an entry that never happened, and corrupt message IDs while trying to self-correct mid-stream. The skill scans in small date-windowed batches instead.
- A keyword-based search is **language-biased** — an English-only net will silently miss an entire language's worth of recruiting correspondence, including deep multi-stage interview processes, because neither the subject keywords nor the sender domains match. The skill explicitly asks about correspondence language and adds a supplementary net.
- A text-wall approval preview **doesn't work past a few dozen rows**. The skill builds a searchable, filterable HTML preview instead of dumping rows into chat.
- Google Sheets' main grid is canvas-rendered, so **DOM-based cell clicking doesn't work** for the browser-automation write path. The skill uses the Name Box + keyboard instead.

## What it does

1. **First-time setup** — creates the tracker sheet with sensible columns (Company, Position, Applied Date, Current Status, Point of Contact, Stage History, Last Updated, plus an internal message-ID tracking column).
2. **Scan** — searches Gmail in date-windowed batches (weekly for recent activity, monthly further back), each batch run with an explicit anti-hallucination instruction, delegated to subagents so raw email content doesn't clutter your main conversation.
3. **Consolidate** — merges the batches into one row per (company, position), applying an anti-regression rule (a row's current status only ever moves forward in time, never backward) and deduplicating contacts.
4. **Preview** — builds an HTML approval page: grouped by company, filterable by status, each row expandable to its full history and evidence.
5. **Approve** — you review it and give a batch-level go/no-go. Nothing is written before this.
6. **Write** — applies approved changes to the sheet, sequentially, with a partial-failure policy (stop and report on the first mismatch rather than silently pressing on) so a large write is safe to resume.

## Install

Copy this repo into your skills directory (path depends on your Claude Code setup, commonly `~/.claude/skills/`):

```bash
git clone <this-repo-url> ~/.claude/skills/job-application-tracker
```

Then just ask, in a Claude Code session with Gmail and Google Sheets/Drive access:

> "Help me set up a job application tracker" or "Scan my inbox for job application updates"

## Requirements

- Gmail read access from the session (MCP tool or equivalent).
- Some way to read and write a spreadsheet. A dedicated Sheets-write API is used directly if available; otherwise the skill falls back to browser automation of the Sheets web UI, which needs a connected browser-automation tool.
- Ability to spawn subagents for the batched scan/consolidation steps is strongly recommended — the skill is written assuming this, though the core logic (date-windowing, anti-regression, escaping) applies even done inline.

## What this intentionally doesn't do

- No scheduled/standing automation — always on-demand.
- No row-level selective approval — approval is all-or-nothing per run, by design, to keep the interaction simple.
- Doesn't track your own sent mail as separate events (used only as context).
- No calendar integration.
- Can't catch emails it never found in the first place — the approval gate verifies what was extracted, it can't surface what the scan missed. If you spot a gap, that's a real signal to re-check the scan's coverage (see the language-gap note above), not just fix the one row.

## Files

- `SKILL.md` — the skill itself.
- `references/batch-scan-prompt.md` — the subagent prompt template for the scanning step.
- `references/consolidation-prompt.md` — the subagent prompt template for the consolidation step.
- `references/weekly-rerun-checklist.md` — a checklist to run through on every regular re-run, encoding real bugs this skill already hit in production (Drive-read truncation, sort-order drift, keyword-net gaps) as concrete checks.
- `assets/approval-preview-template.html` — working HTML/CSS/JS scaffold for the approval preview (search, status filters, collapsible groups, light/dark theme).
- `scripts/build_preview.py` — converts a consolidated CSV into the preview HTML.

## Releasing

Every notable change gets a `CHANGELOG.md` entry (Keep a Changelog format), a matching git tag, and a GitHub Release whose notes are that changelog section copy-pasted:

```bash
# 1. Add a new version section to the top of CHANGELOG.md
# 2. git add -A && git commit -m "..."
git tag -a vX.Y.Z -m "vX.Y.Z - <one-line summary>"
git push origin main --tags
gh release create vX.Y.Z --title "vX.Y.Z" --notes "$(cat <<'EOF'
<paste the CHANGELOG.md section for this version>
EOF
)"
```

See `CHANGELOG.md` and the repo's [Releases page](../../releases) for the full history.

## License

MIT — see `LICENSE`.
