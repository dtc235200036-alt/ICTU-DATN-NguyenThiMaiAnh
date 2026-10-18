---
phase: 01-analysis-design
plan: 01
subsystem: docs
tags: [khao-sat, phong-van, phieu-khao-sat, tai-lieu-goc, pandoc, ANLS-01]

requires: []
provides:
  - "Interview question sets (Phụ lục B) for Bộ môn/Giảng viên/Sinh viên, tagged by quy trình (DT/DC/TD/BV/KHO/CHUNG) and downstream artifact"
  - "Interview minutes template (Phụ lục D) keyed by the same question IDs, with save-path and privacy instructions"
  - "Survey plan (Phụ lục A) scheduling 6 interview slots inside T1 (28/09-04/10/2026), consent script, results→document mapping"
  - "Questionnaires (Phụ lục C) with 24 items across 3 roles, and a long-format tally CSV header"
  - "4 printable DOCX copies of Phụ lục A/B/C/D under ban-in/"
  - "tai-lieu-goc/ source-document collection area: 12-row checklist (TL-01..TL-12), manifest table, naming convention, privacy rules, and a do-an-cu/ folder git-ignored by default"
affects: ["01-02", "01-03", "01-07"]

actuals:
  tokens: 7438
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns: ["Question/questionnaire/checklist IDs (Q-*-NN, P-*-NN, TL-NN) cross-referenced across appendix files", "pandoc .md -> .docx export for printable copies", "folder-local .gitignore for third-party personal data (do-an-cu/)"]

key-files:
  created:
    - docs/chuong-2-khao-sat-phan-tich/khao-sat/ke-hoach-khao-sat.md
    - docs/chuong-2-khao-sat-phan-tich/khao-sat/bo-cau-hoi-phong-van.md
    - docs/chuong-2-khao-sat-phan-tich/khao-sat/phieu-khao-sat.md
    - docs/chuong-2-khao-sat-phan-tich/khao-sat/mau-bien-ban-phong-van.md
    - docs/chuong-2-khao-sat-phan-tich/khao-sat/mau-tong-hop-phieu-khao-sat.csv
    - docs/chuong-2-khao-sat-phan-tich/khao-sat/ban-in/ke-hoach-khao-sat.docx
    - docs/chuong-2-khao-sat-phan-tich/khao-sat/ban-in/bo-cau-hoi-phong-van.docx
    - docs/chuong-2-khao-sat-phan-tich/khao-sat/ban-in/phieu-khao-sat.docx
    - docs/chuong-2-khao-sat-phan-tich/khao-sat/ban-in/mau-bien-ban-phong-van.docx
    - tai-lieu-goc/README.md
    - tai-lieu-goc/quy-che/.gitkeep
    - tai-lieu-goc/bieu-mau/.gitkeep
    - tai-lieu-goc/mau-chinh-thuc/.gitkeep
    - tai-lieu-goc/phong-van/.gitkeep
    - tai-lieu-goc/do-an-cu/.gitignore
  modified: []

key-decisions:
  - "Wrote 40 interview questions total (13 BM + 14 GV + 13 SV), above the ≥36 floor, to give natural per-role coverage without padding any single role artificially"
  - "Reused the CHUNG process code for cross-cutting questions (permission to receive blank forms, tools/channels, pain points) rather than inventing a 7th code"
  - "Minutes template groups all three roles' answer tables in one file with an explicit 'delete the other two roles' instruction, instead of shipping 3 separate minutes files — keeps Phụ lục D a single cross-reference point"

requirements-completed: []

coverage:
  - id: D1
    description: "Interview question sets per role (Phụ lục B) tagged with quy trình and downstream artifact, ≥12 rows per role"
    requirement: "ANLS-01"
    verification:
      - kind: other
        ref: "grep -cE counts for Q-BM/Q-GV/Q-SV rows + PI-tag + no-phone-number checks (plan Task 1 <verify>)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Interview minutes template (Phụ lục D) keyed by the same question IDs, with save-path and privacy instructions"
    requirement: "ANLS-01"
    verification:
      - kind: other
        ref: "grep for 'Mã biên bản', 'Tài liệu nhận được', tai-lieu-goc/phong-van/BB- and ≥36 question-ID rows (plan Task 1 <verify>)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Survey plan (Phụ lục A) with 6 interviewee slots scheduled inside T1, consent/anonymisation section, results-to-document mapping"
    requirement: "ANLS-01"
    verification:
      - kind: other
        ref: "grep for role codes + '28/09' date anchor (plan Task 2 <verify>)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Questionnaires (Phụ lục C) with ≥8 items per role (24 total) and a long-format tally CSV header"
    requirement: "ANLS-01"
    verification:
      - kind: other
        ref: "grep -cE P-BM/P-GV/P-SV row count + CSV header exact-match (plan Task 2 <verify>)"
        status: pass
    human_judgment: false
  - id: D5
    description: "4 printable DOCX copies of Phụ lục A/B/C/D exported via pandoc"
    requirement: "ANLS-01"
    verification:
      - kind: other
        ref: "unzip -l ... | grep word/document.xml on all 4 files (plan Task 2 <verify>)"
        status: pass
    human_judgment: false
  - id: D6
    description: "tai-lieu-goc/ collection area: 12-row checklist (TL-01..TL-12), manifest table, naming rules, privacy rules, do-an-cu/ git-ignored by default"
    requirement: "ANLS-01"
    verification:
      - kind: other
        ref: "test -f on .gitkeep files, grep -cE TL-NN row count, git check-ignore on probe .pdf/.docx (plan Task 3 <verify>)"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-28
status: complete
---

# Phase 1 Plan 1: Survey Kit and Source-Document Collection Checklist Summary

**Full interview/questionnaire kit (Phụ lục A–D, 40 interview questions + 24 questionnaire items across 3 roles, printable as DOCX via pandoc) plus a `tai-lieu-goc/` collection area with a 12-row document checklist, manifest, and a git-ignored-by-default folder for third-party past-thesis binaries.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-09-28
- **Tasks:** 3
- **Files created:** 15

## Accomplishments

- Interview question sets for Bộ môn, Giảng viên, Sinh viên (40 questions total, ≥12 per role), each tagged with a quy trình code (DT/DC/TD/BV/KHO/CHUNG) and the downstream Chapter-2/3 artifact it feeds
- Interview minutes template (Phụ lục D) cross-referenced to the same question IDs, with explicit save-path (`tai-lieu-goc/phong-van/BB-<BM|GV|SV>-<NN>.md`) and role-code-only privacy instructions
- Survey plan (Phụ lục A) scheduling 6 interviewee slots (BM-01, GV-01/02, SV-01/02/03) inside T1 (28/09–04/10/2026), with a verbal consent script and a results→document mapping table
- Questionnaires (Phụ lục C, 24 items) mixing Likert/choice/open questions per role, plus a long-format tally CSV header (`mau-tong-hop-phieu-khao-sat.csv`)
- 4 printable DOCX copies of Phụ lục A/B/C/D exported via pandoc into `ban-in/`
- `tai-lieu-goc/` source-document collection area: README checklist (TL-01..TL-12) naming every document to request, who to ask, target folder, and downstream consumer (e.g. TL-04/TL-05 → `mau-chinh-thuc/` → Phase 4 AISV-04); empty manifest table with a SHA-256 command; `do-an-cu/.gitignore` keeping past-thesis PDF/DOCX/DOC/ZIP out of git by default while manifest rows stay committed

## Task Commits

Each task was committed atomically:

1. **Task 1: Interview question sets per role + minutes template (Phụ lục B, D)** - `bff21e2` (feat)
2. **Task 2: Survey plan, questionnaires, tally CSV and printable DOCX (Phụ lục A, C)** - `3737d8f` (feat)
3. **Task 3: Source-document collection area and checklist (tai-lieu-goc/)** - `28f5e17` (feat)

**Plan metadata:** commit to follow (this SUMMARY + STATE/ROADMAP update)

## Files Created/Modified

- `docs/chuong-2-khao-sat-phan-tich/khao-sat/bo-cau-hoi-phong-van.md` - Phụ lục B, 40 interview questions
- `docs/chuong-2-khao-sat-phan-tich/khao-sat/mau-bien-ban-phong-van.md` - Phụ lục D, minutes template
- `docs/chuong-2-khao-sat-phan-tich/khao-sat/ke-hoach-khao-sat.md` - Phụ lục A, survey plan
- `docs/chuong-2-khao-sat-phan-tich/khao-sat/phieu-khao-sat.md` - Phụ lục C, 24 questionnaire items
- `docs/chuong-2-khao-sat-phan-tich/khao-sat/mau-tong-hop-phieu-khao-sat.csv` - tally CSV header
- `docs/chuong-2-khao-sat-phan-tich/khao-sat/ban-in/*.docx` - 4 printable copies (pandoc export)
- `tai-lieu-goc/README.md` - collection checklist, naming rules, manifest, privacy rules
- `tai-lieu-goc/{quy-che,bieu-mau,mau-chinh-thuc,phong-van}/.gitkeep` - per-class folders
- `tai-lieu-goc/do-an-cu/.gitignore` - keeps past-thesis binaries out of git by default

## Decisions Made

- 40 total interview questions (13 BM + 14 GV + 13 SV) — above the ≥36 floor, sized naturally per role rather than padded
- CHUNG process code reused for cross-cutting questions (blank-form permission, tools/channels, pain points) instead of adding a 7th code
- Single minutes-template file groups all 3 roles' answer tables with a "delete the other two" instruction, keeping Phụ lục D one cross-reference point instead of 3 near-duplicate files

## Deviations from Plan

None - plan executed exactly as written. All three tasks' automated `<verify>` commands and `<acceptance_criteria>` were run and passed on the first attempt (see verification log below); no auto-fixes were needed.

## Issues Encountered

- Two files outside this plan's scope were already modified in the working tree before this executor started (`.planning/config.json` — orchestrator-owned runtime flag, and `.planning/phases/01-analysis-design/01-CONTEXT.md` — a D-11 mockup-approach revision from user-directed prior work). Neither was touched, staged, or committed by this plan; both remain uncommitted in the working tree for the orchestrator/next session to handle.

## Verification Log

- Task 1 `<verify>`: BM=13, GV=14, SV=13 rows (all ≥12); PI tag present; minutes save-path present; minutes question-ID rows=40 (≥36) — **PASS**
- Task 1 `<acceptance_criteria>`: Q-GV-10/11 contain "thời gian" waiting-time questions; no phone-number regex match — **PASS**
- Task 2 `<verify>`: CSV header exact match; P-count=24 (≥24); '28/09' present in plan; all 4 DOCX contain `word/document.xml` — **PASS**
- Task 3 `<verify>`: all 4 `.gitkeep` present; TL rows=12 (≥12); `git check-ignore` confirms PDF and DOCX probes in `do-an-cu/` are ignored; 'mau-chinh-thuc' and 'SHA-256' mentioned — **PASS**
- Plan-level `<verification>`: phone-number regex across all kit files + `tai-lieu-goc/README.md` — clean; `git status --porcelain` scoped to plan directories — only the committed files, no stray changes — **PASS**

## User Setup Required

None - no external service configuration required. This plan produces templates only; the student (not Developer) conducts the real interviews and requests the real documents in T1, per D-01/D-02.

## Next Phase Readiness

- The survey kit (Phụ lục A–D) is ready to print and use for real interviews starting T1 (28/09–04/10/2026)
- `tai-lieu-goc/` is ready to receive real documents from Bộ môn/Giảng viên; plan 01-07 will update the checklist statuses once files arrive
- No blockers for 01-02/01-03 (which also declare ANLS-01) — they proceed independently; ANLS-01 will only be marked Complete in REQUIREMENTS.md once all declaring plans (01-01, 01-02, 01-03, 01-07) have a SUMMARY

## Self-Check: PASSED

All 15 created files verified present on disk; all 3 task commit hashes (`bff21e2`, `3737d8f`, `28f5e17`) verified present in git log.

---
*Phase: 01-analysis-design*
*Completed: 2026-09-28*
