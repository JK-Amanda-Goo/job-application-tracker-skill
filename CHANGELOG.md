# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
