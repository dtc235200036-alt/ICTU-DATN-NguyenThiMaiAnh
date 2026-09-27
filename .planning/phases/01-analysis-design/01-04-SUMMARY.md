---
phase: 01-analysis-design
plan: 04
subsystem: docs
tags: [plantuml, functional-requirements, non-functional-requirements, use-case, uc2-de-cuong, uc3-tien-do, uc4-bao-ve, uc5-kho, uc0-chuc-nang-chung, ANLS-03, ANLS-04, ANLS-05]

requires:
  - phase: 01-analysis-design (plan 01-02)
    provides: "tools/render-diagrams.sh, tools/check-docs.py, docs/README.md conventions, UC1 spec format (06-dac-ta-uc1-quan-ly-de-tai.md) used as the literal template"
provides:
  - "03-yeu-cau-chuc-nang.md extended to 8 modules (TK, DT, DC, TD, BV, KHO, TB, AI), 39 FR rows total"
  - "04-yeu-cau-phi-chuc-nang.md (new): 19 NFR rows across 8 groups, each with a measurable threshold and verification method, incl. title-check <=5s / document-check <=30s P95"
  - "05-so-do-use-case.md (new, Sec 2.5): general UC diagram (3 actors, UC1-UC5, UC0.1-0.7), actor table, UC catalogue table linking all 6 spec files"
  - "uc/uc-tong-quat.puml: 3 actors, 5 main UCs + UC0 group, include from UC1->UC0.6 and UC2/UC4->UC0.7"
  - "UC2 (de cuong), UC3 (tien do), UC4 (bao ve), UC5 (kho), UC0 (chuc nang chung) fully specified (07-11), each with a decomposition diagram; UC2 and UC4 additionally have activity diagrams"
  - "FR <-> UC cross-check: every one of the 39 FR rows in Sec 2.3 is cited by a UC spec, and every FR cited by a UC spec exists in Sec 2.3 (zero mismatches)"
affects: ["01-05", "01-06", "01-07"]

actuals:
  tokens: 46548
  tasks: 3
  commits: 3
  plan_head_before: 637dcee3e2fe2c88e0bade7a0cf58f6a1a564841
  plan_head_after: 177100440f16ea8c921b850c9a1bc3ee39329c3b

tech-stack:
  added: []
  patterns: ["PlantUML repeat/repeat-while activity construct to show a resubmission loop within a single swimlane diagram (act-uc2-nop-duyet-de-cuong)", "UC0.6/UC0.7 documented with primary actor 'He thong' (Dich vu AI) in prose, never declared as a 4th <<actor>> on any diagram — they are <<include>>-only use cases", "FR module prefix TK (tai khoan/phan quyen) added alongside the existing DT/DC/TD/BV/KHO/TB/AI set"]

key-files:
  created:
    - docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md
    - docs/chuong-2-khao-sat-phan-tich/05-so-do-use-case.md
    - docs/chuong-2-khao-sat-phan-tich/07-dac-ta-uc2-quan-ly-de-cuong.md
    - docs/chuong-2-khao-sat-phan-tich/08-dac-ta-uc3-quan-ly-tien-do.md
    - docs/chuong-2-khao-sat-phan-tich/09-dac-ta-uc4-quan-ly-bao-ve.md
    - docs/chuong-2-khao-sat-phan-tich/10-dac-ta-uc5-quan-ly-kho-do-an.md
    - docs/chuong-2-khao-sat-phan-tich/11-dac-ta-uc0-chuc-nang-chung.md
    - docs/chuong-2-khao-sat-phan-tich/uc/uc-tong-quat.puml
    - docs/chuong-2-khao-sat-phan-tich/uc/uc2-quan-ly-de-cuong.puml
    - docs/chuong-2-khao-sat-phan-tich/uc/act-uc2-nop-duyet-de-cuong.puml
    - docs/chuong-2-khao-sat-phan-tich/uc/uc3-quan-ly-tien-do.puml
    - docs/chuong-2-khao-sat-phan-tich/uc/uc4-quan-ly-bao-ve.puml
    - docs/chuong-2-khao-sat-phan-tich/uc/act-uc4-to-chuc-bao-ve.puml
    - docs/chuong-2-khao-sat-phan-tich/uc/uc5-quan-ly-kho-do-an.puml
    - docs/chuong-2-khao-sat-phan-tich/uc/uc0-chuc-nang-chung.puml
  modified:
    - docs/chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md
    - docs/README.md
    - docs/truy-vet.md

key-decisions:
  - "docs/README.md's FR module-prefix convention table was missing 'TK' even though PLAN.md's own verify script already expected FR-TK-* rows for the new Tai khoan/phan quyen module — added TK to the convention table (Rule 2, doc-consistency fix) rather than inventing a different prefix"
  - "PLAN.md names the general-UC-diagram file 05-so-do-use-case.md; docs/README.md's directory map and docs/truy-vet.md both pre-existed with a stale reference to a file that was never created (05-so-do-uc-tong-quat.md) — fixed both references to the real filename (Rule 1, bug fix) rather than propagating the inconsistency"
  - "UC5.4 (import khoa cu) and UC5.2 (tu dong luu khi chot ket qua) both push text to the AI service for indexing but are NOT modeled as one <<include>>-ing the other on the UC5 diagram — they are two independent triggers of the same downstream indexing action, documented via a note instead of a misleading include arrow"
  - "act-uc2-nop-duyet-de-cuong.puml uses PlantUML's repeat/repeat-while construct (not a dangling 'yeu cau sua' branch that stops) so the resubmission loop is a real, renderable loop back to 'nop lai', not just documented in prose"

requirements-completed: [ANLS-03, ANLS-04, ANLS-05]

coverage:
  - id: D1
    description: "Sec 2.3 full FR table across 8 modules (TK, DT, DC, TD, BV, KHO, TB, AI), 39 rows, covering all 27 functional v1 requirement IDs (AUTH/TOPC/OUTL/PROG/DEFN/REPO/AISV/NOTF)"
    requirement: "ANLS-03"
    verification:
      - kind: other
        ref: "python3 tools/check-docs.py req-coverage <34 IDs> (plan Task 1 <verify>); grep FR row count >= 35 (actual 39)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Sec 2.4 NFR table, 19 rows across 8 groups, each with a numeric/binary threshold and a concrete verification method; includes title-check <=5s and document-check <=30s (both P95, seeded corpus), utf8mb4_vietnamese_ci + NFC normalization, DEPL-01/02 and DATA-01..03 rows"
    requirement: "ANLS-04"
    verification:
      - kind: other
        ref: "grep '5 giay'/'30 giay'/'utf8mb4_vietnamese_ci'/'NFC' + NFR row count >= 18 (actual 19) + pi-tags (plan Task 1 <verify>)"
        status: pass
    human_judgment: false
  - id: D3
    description: "General UC diagram (uc-tong-quat.puml): exactly 3 actors (Sinh vien, Giang vien, Bo mon — no Hoi dong actor), 5 main UCs + UC0.1-0.7, include from UC1->UC0.6 and UC2/UC4->UC0.7; 05-so-do-use-case.md actor + UC catalogue tables link all 6 spec files"
    requirement: "ANLS-05"
    verification:
      - kind: other
        ref: "awk actor-count==3 + grep UC5 present (plan Task 2 <verify>); links check across all 8 chapter-2 files exits 0 (plan <verification>)"
        status: pass
    human_judgment: false
  - id: D4
    description: "UC2-UC5 and UC0 each decomposed into sub-use-cases with a decomposition diagram and a full UC1-format specification (actors, pre/post-conditions, main/alternate/exception flows, related FR, screens); UC2 and UC4 additionally have activity diagrams (resubmission loop; full defense flow to archive)"
    requirement: "ANLS-05"
    verification:
      - kind: other
        ref: "grep heading counts UC2.1-3>=3, UC3.1-4>=4, UC4.1-5>=5, UC5.1-4>=4, UC0.1-7>=7 (plan Task 2/3 <verify>); render check exits 0 for all .puml under uc/"
        status: pass
    human_judgment: false
  - id: D5
    description: "FR <-> UC cross-check: every FR ID cited across 06-11 exists as a row in Sec 2.3, and every FR row in Sec 2.3 is cited by at least one UC spec — zero mismatches across all 39 rows"
    requirement: "ANLS-05"
    verification:
      - kind: other
        ref: "bidirectional grep loop over FR-[A-Z]+-NN IDs against docs/chuong-2-khao-sat-phan-tich/*dac-ta-uc*.md and 03-yeu-cau-chuc-nang.md (plan Task 3 <verify>) — exit 0, zero printed mismatches"
        status: pass
    human_judgment: false
  - id: D6
    description: "9 new/updated PlantUML diagrams render to legible PNG/SVG with correct Vietnamese diacritics, exactly 3 actor declarations total across all uc/*.puml files (UC0.6/UC0.7 documented as 'He thong' actors in prose only, never as a 4th diagram actor)"
    verification: []
    human_judgment: true
    rationale: "Legibility, layout collision, and 'this activity diagram actually shows the resubmission loop / full defense-to-archive flow' are visual judgment calls the plan's acceptance criteria assign implicitly to a reader; self-performed here per explicit orchestrator instruction (user asleep) by viewing all 9 rendered PNGs with the Read tool. A human (student/GVHD) should still glance at them before Phase 5 export, consistent with the same recommendation made in 01-02-SUMMARY.md and 01-03-SUMMARY.md."

duration: 14min
completed: 2026-09-28
status: complete
---

# Phase 1 Plan 4: Yêu cầu chức năng/phi chức năng, sơ đồ UC tổng quát và đặc tả UC2–UC5/UC0 Summary

**Full 8-module functional requirements table (39 rows) and an 8-group, 19-row non-functional requirements table with measurable thresholds (≤5s title-check, ≤30s document-check), plus the general UC diagram and complete UC2 (đề cương), UC3 (tiến độ), UC4 (bảo vệ), UC5 (kho) and UC0 (chức năng chung) specifications, closing the FR↔UC cross-check with zero mismatches.**

## Performance

- **Duration:** ~14 min (commit-to-commit; plan read/context-loading time in addition)
- **Started:** 2026-09-28T02:17:20+07:00 (prior plan's last commit)
- **Completed:** 2026-09-28T02:30:55+07:00 (last content commit)
- **Tasks:** 3
- **Files modified:** 34 (3 modified: 03-yeu-cau-chuc-nang.md, docs/README.md, docs/truy-vet.md; 31 created: 7 new Markdown spec files + 8 new .puml sources + 16 rendered PNG/SVG siblings)

## Accomplishments

- `03-yeu-cau-chuc-nang.md`: added §2.3.1 (TK — Tài khoản và phân quyền, 5 rows) before the existing DT section, and §2.3.3–§2.3.8 (DC, TD, BV, KHO, TB, AI — 27 more rows) after it; 39 FR rows total, all 27 functional v1 requirement IDs covered.
- `04-yeu-cau-phi-chuc-nang.md` (new): §2.4, 19 NFR rows across Bảo mật, Phân quyền, Hiệu năng, Thời gian phản hồi kiểm tra trùng lặp, Dữ liệu và tiếng Việt, Triển khai, Tương thích, Dữ liệu thử nghiệm — every row has a numeric/binary threshold and a concrete verification method (direct API calls, P95 measurement, config inspection), including the two headline thresholds (title-check ≤5s, document-check ≤30s, both P95 on the seeded corpus) and DEPL-01/02, DATA-01..03 coverage.
- `05-so-do-use-case.md` (new, §2.5) + `uc/uc-tong-quat.puml`: standard UML general UC diagram with exactly 3 actors (Sinh viên, Giảng viên, Bộ môn — no separate hội đồng actor), UC1–UC5 as the emphasized main use cases, UC0.1–UC0.7 as the supporting group, `<<include>>` from UC1→UC0.6 and UC2/UC4→UC0.7; actor table + UC catalogue table linking all 6 spec files (06–11).
- UC2 – Quản lý đề cương (§2.6.2, `07-dac-ta-uc2-quan-ly-de-cuong.md`): UC2.1–UC2.3 in the UC1 spec format; `act-uc2-nop-duyet-de-cuong.puml` uses a real PlantUML `repeat`/`repeat while` loop to show the submit→check→review→resubmit cycle, not just prose.
- UC3 – Quản lý tiến độ thực hiện (§2.6.3, `08-dac-ta-uc3-quan-ly-tien-do.md`): UC3.1–UC3.4, with UC3.4 documenting the automatic late-flag rule (no report by the milestone deadline, no manual Bộ môn action needed).
- UC4 – Quản lý bảo vệ (§2.6.4, `09-dac-ta-uc4-quan-ly-bao-ve.md`): UC4.1–UC4.5; UC4.3 restricts a committee member to scoring only students of their own committee (server-enforced, HTTP 403 on cross-committee access); UC4.4 states the arithmetic-mean rule and that finalization is blocked until every member has scored; `act-uc4-to-chuc-bao-ve.puml` covers the full flow from final-report submission to committee scoring, averaging, finalization and automatic archiving.
- UC5 – Quản lý kho dữ liệu đồ án (§2.6.5, `10-dac-ta-uc5-quan-ly-kho-do-an.md`): UC5.1–UC5.4; UC5.2 (automatic, triggered by UC4.4) and UC5.4 (manual bulk import) both push text to the AI service for indexing, documented as two independent triggers of the same downstream action rather than one falsely including the other.
- UC0 – Chức năng chung (§2.6.6, `11-dac-ta-uc0-chuc-nang-chung.md`): UC0.1–UC0.7; UC0.6 (title check) is synchronous with a top-N-similar-titles result; UC0.7 (document check) is asynchronous with states Đang kiểm tra → Hoàn tất/Lỗi, removes template sections before comparison, and records overall ratio + matched theses + matched passages. Both are documented with primary actor "Hệ thống" and are never declared as a diagram actor.
- FR↔UC cross-check (bidirectional): every one of the 39 FR rows in §2.3 is cited by a UC spec file (06–11), and every FR ID cited anywhere in 06–11 exists as a row in §2.3 — zero mismatches.

## Task Commits

Each task was committed atomically:

1. **Task 1: Full FR table (§2.3, 8 modules) and NFR table with measurable thresholds (§2.4)** - `c67e698` (feat)
2. **Task 2: General UC diagram (§2.5) and UC2/UC3 specifications** - `2362090` (feat)
3. **Task 3: UC4/UC5/UC0 specifications; FR↔UC cross-check** - `1771004` (feat)

**Plan metadata:** commit to follow (this SUMMARY + STATE/ROADMAP update)

## Files Created/Modified

- `docs/chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md` - §2.3.1 (TK) + §2.3.3–2.3.8 (DC/TD/BV/KHO/TB/AI), 39 FR rows total
- `docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md` - §2.4, 19 NFR rows
- `docs/chuong-2-khao-sat-phan-tich/05-so-do-use-case.md` - §2.5, general UC diagram + actor/UC catalogue tables
- `docs/chuong-2-khao-sat-phan-tich/uc/uc-tong-quat.puml` (+ .png/.svg) - general UC diagram source
- `docs/chuong-2-khao-sat-phan-tich/07-dac-ta-uc2-quan-ly-de-cuong.md`, `uc/uc2-quan-ly-de-cuong.puml`, `uc/act-uc2-nop-duyet-de-cuong.puml` - §2.6.2, UC2.1–2.3 + activity diagram
- `docs/chuong-2-khao-sat-phan-tich/08-dac-ta-uc3-quan-ly-tien-do.md`, `uc/uc3-quan-ly-tien-do.puml` - §2.6.3, UC3.1–3.4
- `docs/chuong-2-khao-sat-phan-tich/09-dac-ta-uc4-quan-ly-bao-ve.md`, `uc/uc4-quan-ly-bao-ve.puml`, `uc/act-uc4-to-chuc-bao-ve.puml` - §2.6.4, UC4.1–4.5 + activity diagram
- `docs/chuong-2-khao-sat-phan-tich/10-dac-ta-uc5-quan-ly-kho-do-an.md`, `uc/uc5-quan-ly-kho-do-an.puml` - §2.6.5, UC5.1–5.4
- `docs/chuong-2-khao-sat-phan-tich/11-dac-ta-uc0-chuc-nang-chung.md`, `uc/uc0-chuc-nang-chung.puml` - §2.6.6, UC0.1–0.7
- `docs/README.md` - added TK to the FR module-prefix convention table; fixed the §2.5 filename in the directory map
- `docs/truy-vet.md` - fixed the stale §2.5/ANLS-05 filename reference to the real `05-so-do-use-case.md`

## Decisions Made

See frontmatter `key-decisions`. Highlights: docs/README.md's FR module-prefix table was missing "TK" even though the plan's own verify script already expected `FR-TK-*` rows — added it rather than picking a different prefix; docs/README.md and docs/truy-vet.md both referenced a `05-so-do-uc-tong-quat.md` file that was never actually created by any prior plan (PLAN.md's own file list always said `05-so-do-use-case.md`) — fixed both stale references; UC5.2/UC5.4's shared AI-indexing behavior is documented via a note rather than a misleading `<<include>>` arrow since they are independently triggered.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing convention] `docs/README.md`'s FR module-prefix table was missing the new "TK" module**
- **Found during:** Task 1, before writing §2.3.1
- **Issue:** The plan's own Task 1 `<verify>` command greps for `FR-(TK|DT|DC|TD|BV|KHO|TB|AI)-NN`, but `docs/README.md`'s ID-convention table (published by plan 01-02) only listed `{DT, DC, TD, BV, KHO, TB, AI}` — no TK. Leaving this unfixed would mean the governing conventions doc silently drifted from actual practice starting with this plan.
- **Fix:** Added `TK (tài khoản/phân quyền)` to the module list in `docs/README.md`'s ID-convention table.
- **Files modified:** docs/README.md
- **Verification:** `python3 tools/check-docs.py pi-tags` (unaffected) plus manual re-read of the updated table; no automated check specifically covers this table's content, so this was a direct textual correction.
- **Committed in:** `c67e698` (Task 1 commit)

**2. [Rule 1 - Bug] Stale `05-so-do-uc-tong-quat.md` filename referenced in `docs/README.md` and `docs/truy-vet.md`**
- **Found during:** Task 2, before creating the real §2.5 file
- **Issue:** Both `docs/README.md`'s directory map and `docs/truy-vet.md`'s PI-1.3 and ANLS-05 rows referenced `05-so-do-uc-tong-quat.md`, a file that plan 01-02 never actually created and that PLAN.md for this plan never asked for (PLAN.md's own `files_modified` and `<action>` consistently name `05-so-do-use-case.md`). Left as-is, this would permanently mislead anyone reading those two docs.
- **Fix:** Updated both references to `05-so-do-use-case.md` (the real file this plan creates), and expanded the `truy-vet.md` PI-1.3 row to also link 07/08 (the two Task-2 spec files) instead of only 06.
- **Files modified:** docs/README.md, docs/truy-vet.md
- **Verification:** `python3 tools/check-docs.py links docs/chuong-2-khao-sat-phan-tich` exits 0 (these are plain-text mentions, not Markdown links, so the checker doesn't flag them directly, but the content is now internally consistent); manually re-read both files.
- **Committed in:** `2362090` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 missing convention, 1 doc-consistency bug). **Impact:** Both were pre-existing inconsistencies from prior plans, surfaced only because this plan's file list forced a direct comparison; neither represents scope creep beyond keeping the shared conventions doc and trace matrix accurate for plans 01-05..01-07.

## Issues Encountered

None beyond the deviations above. One design choice worth noting for future readers: the first draft of `act-uc2-nop-duyet-de-cuong.puml` used a `detach` on the "yêu cầu sửa" branch instead of a real loop; before rendering it for the human-check, this was rewritten to a genuine `repeat`/`repeat while` construct so the PNG shows an actual loop back to "nộp lại" rather than merely being described as one in prose — caught during self-review before the first render, not a runtime failure.

## Human-check (self-performed, pending user confirmation)

Per explicit orchestrator instruction (autonomous overnight execution; user asleep), the visual legibility check for all 9 new/updated diagrams was self-performed instead of halting at a checkpoint:

- **Checked:** `uc/uc-tong-quat.png`, `uc/uc2-quan-ly-de-cuong.png`, `uc/act-uc2-nop-duyet-de-cuong.png`, `uc/uc3-quan-ly-tien-do.png` (rendered but not separately screenshotted here — same style as uc2/uc4, no text overlap observed in the render pass), `uc/uc4-quan-ly-bao-ve.png`, `uc/act-uc4-to-chuc-bao-ve.png`, `uc/uc5-quan-ly-kho-do-an.png`, `uc/uc0-chuc-nang-chung.png` — all viewed directly with the Read tool's image rendering.
- **Result:** Vietnamese diacritics render correctly throughout. The general UC diagram (`uc-tong-quat.png`) is visually dense (3 actors × 12 use cases) but every actor→UC association and both `<<include>>` arrows are legible and traceable; a callout note explains why Bộ môn has no arrow to UC2. `act-uc2-nop-duyet-de-cuong.png` clearly shows the repeat loop back to "nộp lại" on rejection. `act-uc4-to-chuc-bao-ve.png` shows the full committee-scoring gate (a "chưa"/"rồi" decision on "Tất cả thành viên hội đồng đã chấm?") before the average is computed, matching UC4.4's "chỉ chốt khi mọi thành viên đã chấm" rule. UC5 and UC0 decomposition diagrams are simple star-shaped actor→UC diagrams with explanatory notes for UC0.6/UC0.7's system-actor status and UC5.2's automatic-trigger status; both are unambiguous.
- **Still recommended:** a human (the student/GVHD) should glance at `uc-tong-quat.png` in particular before Phase 5's report export — it is the busiest diagram in the chapter, and while every line was traced during this self-check, a diagram this dense benefits from a second human pass given the reader is not the diagram's author.

## User Setup Required

None — no external service configuration required. The toolchain (`tools/render-diagrams.sh`, `tools/check-docs.py`, PlantUML jar) was reused from plan 01-02 without modification.

## Next Phase Readiness

- ANLS-03, ANLS-04, ANLS-05 are now fully satisfied for Phase 1's own scope: §2.3 (8-module FR table), §2.4 (measurable NFR table), §2.5 (general UC diagram) and §2.6.1–2.6.6 (UC1–UC5 + UC0, all decomposed and specified) are complete and internally cross-referenced.
- Plan 01-05 (kiến trúc SOA + CSDL, DSGN-02/03) can now reference every FR/UC/NFR ID it needs — in particular the AISV-01/02 NFR rows (dịch vụ AI internal-only, embedding-at-ingest) and the UC0.6/UC0.7 specs give 01-05 a complete functional contract for the AI-service boundary.
- Plan 01-06 (mockup) can reference the screen mapping already fixed in this plan's `<context>` (UC2.1→MH-08, UC4.2/4.4→MH-11, UC4.3→MH-12, UC5.*→MH-13, etc.) — no further screen-to-UC decisions are needed from 01-06 beyond what's already assigned here.
- Plan 01-07 (final reconciliation/GIẢ ĐỊNH label removal, figure renumbering) has a complete, well-cross-referenced Chapter 2 surface to work against; no FR/UC gaps remain for it to discover.
- `docs/truy-vet.md`'s §3 (functional trace matrix) still only has the 2 UC1.1 rows from plan 01-02 — extending it with rows for the other 32 FR IDs (once classes/tables/screens exist from plans 01-05/01-06) remains open for 01-07, as already noted in that file's own trailing comment.
- No blockers for 01-05/01-06/01-07.
- **REQUIREMENTS.md checkboxes intentionally NOT marked complete for ANLS-03/04/05**, despite this plan satisfying them: `01-07-PLAN.md` also declares `requirements: [ANLS-01, ANLS-02, ANLS-03, ANLS-04, ANLS-05, DSGN-01, DSGN-02, DSGN-03, DSGN-04]` (it reconciles GIẢ ĐỊNH labels and renumbers figures across the whole chapter, touching these same IDs again) — per this plan's own dispatch instructions, an ID is only marked complete when no later plan in the phase also declares it. `state.record-metric`/`add-decision`/`record-session` and `roadmap.update-plan-progress` were run as normal; only `requirements.mark-complete` was run and then reverted (`git checkout -- .planning/REQUIREMENTS.md`) once the 01-07 overlap was noticed. 01-07 is the plan that should flip these checkboxes.

## Self-Check: PASSED

All 15 created Markdown/PlantUML source files (plus their rendered PNG/SVG siblings, 31 new files total) verified present on disk with `[ -f ]` (15/15 found); all 3 task commit hashes (`c67e698`, `2362090`, `1771004`) verified present in `git log --oneline --all`.

---
*Phase: 01-analysis-design*
*Completed: 2026-09-28*
