# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.9.1] - 2026-09-04

### Changed
- The approval preview's status-pill classification no longer buckets a row as `pending` forever just because no explicit rejection ever arrived. A row whose Current Status doesn't read as rejected/active/offer, and whose Last Updated is 30+ days old, now classifies as `closed` instead — a thread gone silent for a month is realistically ghosted, not still live. Scoped entirely to `classify()` in `assets/approval-preview-template.html`; the sheet's actual Current Status cell still always records the literal latest event per Step 4's anti-regression rule — only the preview's own derived bucket changes.

## [0.9.0] - 2026-08-26

### Added
- Headhunter-tracking schema gains a `Current Result` column (`Ongoing` / `Closed` / `No update`) tracking where each introduced opportunity actually stands — cross-referenced against the main tracker tab first, falling back to a direct Gmail search when the company never shows up there. Documents the soft-close pattern some platforms use ("thank you for your interest... we appreciate the time you spent" reads as neutral but is a rejection), the recency-based judgment call between `Ongoing` and `No update` for a thread that's gone quiet, and applying one resolved outcome across every headhunter row referencing the same company.
- Step 6 documents two more browser-automation lessons: the "clicks stop registering" stall traced to host-machine memory pressure from many open tabs/apps (a browser restart alone only helps temporarily if that's still the cause — closing other tabs/apps is the actual fix), and using the `find` tool (natural-language element lookup + ref-based clicking) instead of pixel coordinates when window/toolbar layout keeps shifting between screenshots.

## [0.8.2] - 2026-08-26

### Fixed
- `references/weekly-rerun-checklist.md` was linked from Step 7 and the README but missing from SKILL.md's own "Reference files" list — added.

### Added
- Step 6 now documents two browser-automation gotchas hit repeatedly in production: (1) starting a Tab-separated row entry from a full-column selection (e.g. from clicking a column header) makes Tab move down within that column instead of across it, silently stacking values into one column; (2) if clicks/keystrokes stop registering while screenshots and page-text reads keep working, that's a recurring extension-level stall best fixed by a full browser restart, not more retries.

## [0.8.1] - 2026-08-25

### Fixed
- The headhunter-tracking schema documented in v0.8.0 was wrong: it said to list multiple introduced opportunities semicolon-separated in one cell on a single headhunter row. The actual agreed design (confirmed with the user after she caught the mismatch on a live sheet where one headhunter had introduced 10 companies) is one row per (headhunter, company, position) — a headhunter with 10 opportunities gets 10 rows, each with its own First/Last Contact and Processed Message IDs computed from that specific opportunity's events, not copied from the headhunter's aggregate.

## [0.8.0] - 2026-08-25

### Added
- New optional add-on: headhunter tracking as a second spreadsheet tab, keyed by headhunter rather than (company, position). Documents the third-party-vs-in-house classification rule (domain comparison, with guidance for the domain-matches-a-tracked-company-name edge case), a two-phase gathering approach (a narrow `QUERY`-based warm start from the existing tracker tab, followed by a dedicated date-windowed Gmail scan), the row schema (including a new `Notes` column), and three judgment calls that always need a human decision: suspected spam/bot outreach (keep + flag, don't silently drop), true category exclusions (e.g. an automated in-house "Virtual Recruiter" bot) versus quality exclusions (kept distinct on purpose), and irrelevant-role outreach (still counts as a real contact, include it).

## [0.7.0] - 2026-08-24

### Added
- Nine more keywords to the Step 3 query net: `take-home`, `assessment`, `assignment`, `case study`, `screen`, `screening`, `shortlist`, `move forward`, `advance to`, `next round`.

### Fixed
- `take-home` — a category the skill's own frontmatter and INCLUDE criteria named as in-scope since v0.1.0 — was never actually in the query keyword list, so a take-home email that didn't also say "interview" or "next steps" would never have reached the judgment step at all. Documented in SKILL.md that the INCLUDE criteria and the query keyword list are separate layers that must be updated together whenever a new event category is added, since drift between them is itself a silent-miss source distinct from the "company used unexpected wording" kind.

## [0.6.0] - 2026-08-24

### Added
- `references/weekly-rerun-checklist.md` — a checklist to run through on every regular re-run, encoding real production bugs (Drive-read truncation, sort-order drift, keyword-net gaps) as concrete checks rather than scattered prose warnings. Linked from SKILL.md Step 7 and the README's file list.

## [0.5.0] - 2026-08-24

### Changed
- Expanded the Step 3 keyword net with "talent manager", "talent acquisition", "talent team" after a real missed thread: a company's own outreach + a scheduled call + the user's own follow-up, three real messages, invisible to the net because the wording never matched "recruiter" / "interview" / "offer". Documented that the net is inherently incomplete — a user-reported miss should trigger a direct company-name Gmail search, not just a re-run of the same net.

## [0.4.0] - 2026-08-24

### Changed
- Replaced the openness-tier + interview-depth sort heuristic introduced in 0.2.0 with a simpler two-key date sort: Last Updated descending, then Applied Date descending. Simplified the re-sort technique accordingly — no scratch-column rank computation needed, since both keys are already real columns in the schema.

## [0.3.0] - 2026-08-24

### Changed
- Shortened the default regular re-run lookback from ~2 weeks to ~1 week (Step 2).

### Fixed
- Documented a real correctness bug: Google Drive's `read_file_content` silently truncates large sheets with no error (confirmed truncating a 492-row sheet at ~310 rows). Added guidance in Step 4 to verify every candidate "new" row against the live sheet via the Sheets app's own Find dialog before writing, rather than trusting a single Drive read.

## [0.2.0] - 2026-08-23

### Changed
- Replaced chronological (Applied Date) row ordering with a priority-based sort: openness tier (offer > actively progressing > pending > closed), then interview depth, then Applied Date as a final tiebreaker. Documented an efficient scratch-column re-sort technique for large sheets.

## [0.1.0] - 2026-08-22

### Added
- Initial release: `SKILL.md`, the batch-scan and consolidation subagent prompt templates, an HTML approval-preview template with its CSV-to-JSON build script, README, and MIT license.
