---
phase: 03-outline-progress-defense-archive
plan: 06
subsystem: progress
status: complete
tags: [fastapi, sqlalchemy, mysql, alembic, react, antd, tanstack-query]

requires:
  - phase: 03-outline-progress-defense-archive (plan 01)
    provides: "documents.read_and_validate/store/remove_file_quietly/to_document_out/can_view, notifications.create, DeCuong/DC_DA_DUYET/LOAI_BAO_CAO_TIEN_DO, TIEN_DO_NHAN_XET, timeutil (now_utc/today_vn/to_vn_date), make_assigned_topic/pdf_bytes/docx_bytes fixtures, e2e-uc2-5.sh helpers + cleanup of bao_cao_tien_do/moc_tien_do"
  - phase: 02-platform-rbac-topic-management
    provides: "require_role/ANY_ROLE, dashboard._default_cohort, CohortRef/PersonRef, useCohorts, route registry"
provides:
  - "Alembic 0009: moc_tien_do, bao_cao_tien_do (+ tai_lieu_do_an_id attachment column, written back to ERD/class diagram/§3.2.3)"
  - "app/services/progress.py: trang_thai_moc (the single D-05 rule), milestone CRUD, submit_report (upsert), review_report, list_students, topic_progress, compute_cohort_progress, dashboard"
  - "/api/progress: GET/POST /milestones, PUT/DELETE /milestones/{id}, GET /me, POST /reports/{moc_id}, GET /students, GET /topics/{de_tai_id}, POST /reports/{bao_cao_id}/review, GET /dashboard"
  - "frontend features/progress: /tien-do (SV), /nhan-xet-tien-do (GV), /tien-do-toan-khoa (Bộ môn), shared MilestoneList"
  - "e2e uc3_progress between uc2_outline and uc4_defense"
affects: [03-07]

actuals:
  tokens: 23400
  tasks: 2
  commits: 3
  plan_head_before: 995970f270e0ba0315b1b21403328f41fd16d7ca
  plan_head_after: 1d96bae6a41b1f11b518e59b548d2c6264debed1

tech-stack:
  added: []
  patterns:
    - "Late status is computed on read by one function (trang_thai_moc) from han_nop, the report's VN date and today_vn(); nothing about lateness is stored"
    - "Progress rows are built with two queries per list (all milestones of the involved đợt + all reports of the involved topics), so there is no N+1 for the GV list or the faculty dashboard"
    - "Submit locks the SV's topic row, then the existing report row FOR UPDATE; review locks the report row, so a resubmit and a review cannot interleave"

key-files:
  created:
    - backend/alembic/versions/0009_tien_do.py
    - backend/app/models/tien_do.py
    - backend/app/schemas/progress.py
    - backend/app/services/progress.py
    - backend/app/routers/progress.py
    - backend/tests/test_progress_flow.py
    - frontend/src/features/progress/api.ts
    - frontend/src/features/progress/routes.tsx
    - frontend/src/features/progress/constants.ts
    - frontend/src/features/progress/MilestoneList.tsx
    - frontend/src/features/progress/ProgressPage.tsx
    - frontend/src/features/progress/ProgressReviewPage.tsx
    - frontend/src/features/progress/ProgressOverviewPage.tsx
  modified:
    - deploy/e2e-uc2-5.sh
    - docs/chuong-3-thiet-ke/csdl/erd.puml
    - docs/chuong-3-thiet-ke/csdl/erd.png
    - docs/chuong-3-thiet-ke/csdl/erd.svg
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.png
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.svg
    - docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md

key-decisions:
  - "D-05 rule as implemented: a report counts as on time (DUNG_HAN) if its submission date in Vietnam time is on or before han_nop, or the milestone has no han_nop; otherwise it is NOP_TRE. With no report, the milestone is CHUA_DEN_HAN while today (VN) is on or before han_nop, or there is no han_nop; otherwise it is TRE_MOC. An SV is flagged trễ mốc if any milestone is NOP_TRE or TRE_MOC."
  - "The final report (UC4.1) is NOT gated on milestone completion. Lateness is tracked by UC3.4 only."
  - "Resubmitting without a new file keeps the previous attachment. A new file always creates a new BAO_CAO_TIEN_DO version, and older files are never deleted (D-02)."
  - "A GVHD may edit a comment later. Each edit notifies the SV again."
  - "When the đợt is closed (DA_DONG), creating, editing and deleting milestones all return 409. SV submissions are not blocked by the đợt state."
  - "UC3.3 E1 ('Chưa nộp' on a missing report) is covered by the computed Trễ mốc tag. No row is written for a missing report."
  - "Added fields beyond the plan: MilestoneOut.so_bao_cao (shown in the delete warning), MilestoneStatus.so_ngay_tre (for 'Nộp trễ n ngày…'), TopicProgressOut.co_the_nhan_xet, and giang_vien on dashboard rows."

requirements-completed: [PROG-01, PROG-02, PROG-03, NOTF-01]

coverage:
  - id: D1
    description: "Per D-05/UC3.1: Bộ môn defines ordered milestones per đợt; a han_nop outside the đợt → 422, a closed đợt → 409, and deleting a milestone that has reports → 409"
    requirement: "PROG-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_progress_flow.py::test_milestones_and_late_flags — 422 (2025-12-31 < 2026-01-01), SV/GV 403, order M1..M4, DELETE M3 409 / M4 204 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0306-02/03/04/15/16: modal, out-of-range message, milestone table, delete Popconfirm warning, then 409 toast 'Mốc đã có báo cáo — hãy sửa hạn nộp thay vì xóa (UC3.1 - A1)'"
        status: pass
    human_judgment: true
    rationale: "Self-performed via headless Chrome per the autonomous-run instruction; user confirmation pending."
  - id: D2
    description: "Per PROG-01/UC3.2: an SV with an approved outline submits one report per milestone with an optional DOCX/PDF (new tai_lieu_do_an version); a resubmission before the comment overwrites the row, and after the comment it is refused with 409"
    requirement: "PROG-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_progress_flow.py::test_report_resubmit_and_review_scope — outline CHO_DUYET 409; same id + new noi_dung; 1 row; versions [1,2] with v1 file on disk; 409 after review — pass"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc3_progress — PDF submit 200, Mốc 2 DUNG_HAN with the file, resubmit after review 409 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0306-05a/05/06/07: default selects the first unsubmitted milestone, the file is chosen via the Dragger, then 'Mốc 2 · nộp 28/09/2026' shows 'Tệp đính kèm: cdp0306-moc2.pdf'"
        status: pass
    human_judgment: true
    rationale: "MH-10 SV-side fidelity self-judged from CDP screenshots; user confirmation pending."
  - id: D3
    description: "Per PROG-02/NOTF-01/UC3.3: only the topic's GVHD comments and grades (Đạt / Cần cải thiện / Chưa đạt); the SV gets TIEN_DO_NHAN_XET in the same transaction; another SV cannot read the topic's progress"
    requirement: "PROG-02"
    verification:
      - kind: unit
        ref: "test_report_resubmit_and_review_scope — other SV 403 on /topics/{id}, unrelated GV 403 on review, GVHD 200 + TIEN_DO_NHAN_XET — pass"
        status: pass
      - kind: e2e
        ref: "uc3_progress — GV029 sees so_cho_nhan_xet 1 + tre_moc, GV025 review 403, GV029 DAT 200, SV notification present — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0306-08..12: GV list with badges and a Trễ mốc tag, the 'Nhận xét cho Mốc 2' form with Radio Đánh giá, the overdue unsubmitted milestone shows only its tag, the SV sees the comment with the 'Cần cải thiện' tag; notification text 'GVHD đã nhận xét báo cáo Mốc 2: Cần cải thiện'"
        status: pass
    human_judgment: true
    rationale: "MH-10 GV-side fidelity self-judged; user confirmation pending."
  - id: D4
    description: "Per PROG-03/UC3.4: Bộ môn sees every assigned SV × milestone with computed statuses, the SV trễ mốc count, and a late-only filter; only BO_MON can read it"
    requirement: "PROG-03"
    verification:
      - kind: unit
        ref: "test_milestones_and_late_flags — M1 TRE_MOC, M2 NOP_TRE, M3 DUNG_HAN (+ attachment), M4 CHUA_DEN_HAN; so_sv_tre_moc 1; chi_tre_moc keeps the row — pass"
        status: pass
      - kind: e2e
        ref: "uc3_progress — dashboard chi_tre_moc=true shows the SV tre_moc True, so_sv_tre_moc 1; DTC225200097 403 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0306-13/14: matrix with SV097 (Đúng hạn / Chưa đến hạn) and SV098 (Trễ mốc / Đúng hạn); ticking 'Chỉ SV trễ mốc' leaves only SV098; URL ?dot_do_an_id=43&chi_tre_moc=1"
        status: pass
    human_judgment: true
    rationale: "MH-04 matrix fidelity self-judged; user confirmation pending."
  - id: D5
    description: "Per D-09: e2e gains uc3_progress, run between uc2_outline and uc4_defense, and it cleans up after itself"
    requirement: "PROG-01"
    verification:
      - kind: e2e
        ref: "bash deploy/e2e-uc2-5.sh green 3 times (before and after the frontend rebuild); COUNT(moc_tien_do WHERE ten_moc LIKE '%(E2E)') = 0"
        status: pass
    human_judgment: false

duration: 16min
completed: 2026-09-28
---

# Phase 3 Plan 06: UC3 Progress Tracking Summary

**The Bộ môn now sets milestones for each đợt. Students submit one report per milestone, optionally with a DOCX/PDF that is stored as a new document version. The GVHD comments on and grades each report, and the SV gets a notification. The Bộ môn sees a faculty-wide SV × milestone matrix. Its Đúng hạn / Nộp trễ / Trễ mốc / Chưa đến hạn statuses are computed from dates at read time, and the matrix can be filtered to late students only.**

## Performance

- **Duration:** about 16 minutes (2026-09-28 06:03Z–06:20Z)
- **Tasks:** 2 of 2
- **Files:** 13 created, 8 modified

## Accomplishments

- **Migration 0009** adds `moc_tien_do` and `bao_cao_tien_do`, with the ERD names, the unique constraint `uq_bao_cao_tien_do_de_tai_moc` and the check constraint `ck_bao_cao_tien_do_danh_gia`.
- **Additive column** `bao_cao_tien_do.tai_lieu_do_an_id` is written back to three places:
  - `erd.puml`: new column plus the relation `|o--o|` "tệp đính kèm tùy chọn (PROG-01)".
  - `lop-thuc-the.puml`: a `BaoCaoTienDo "0..1" -- "0..1" TaiLieuDoAn : "đính kèm"` association.
  - §3.2.3: the new column row, and the danh_gia description now lists DAT / CAN_CAI_THIEN / CHUA_DAT.
  - Both diagrams were re-rendered. `check-erd-db.py`, `check-docs class-erd` and `check-docs render` are green.
- **Progress service and routes.** Every route declares `require_role`, and the route role-coverage test passes. The SV attachment goes through the shared `documents.read_and_validate` + `documents.store` path, and file writes are compensated on failure.
- **Three screens:**
  - `/tien-do` (SV, MH-10)
  - `/nhan-xet-tien-do` (GVHD, MH-10)
  - `/tien-do-toan-khoa` (Bộ môn, MH-04 progress card + "Mốc tiến độ của đợt" + "Thiết lập mốc")
  - Menus are at order 50 for all three roles.

## `compute_cohort_progress` contract (for plan 03-07)

```python
compute_cohort_progress(db, dot_do_an_id) -> tuple[list[MocTienDo], list[ProgressRow]]

@dataclass ProgressCell: moc: MocTienDo; trang_thai: str; so_ngay_tre: int | None; bao_cao: BaoCaoTienDo | None
@dataclass ProgressRow:  de_tai: DeTai (sinh_vien + giang_vien selectin-loaded); cells: list[ProgressCell]; tre_moc: bool (property)
```

- Rows are the đợt's `DA_PHAN_CONG` topics, ordered by SV code.
- Milestones are ordered by `thu_tu`.
- Everything is built with 3 queries: milestones, topics, reports.
- For a dashboard count, use `sum(r.tre_moc for r in rows)`.

## Task Commits

1. **Task 1 RED:** `9356e3c` test(03-06): RED — progress milestones/late flags + resubmit/review scope
2. **Task 1 GREEN:** `69a525a` feat(03-06): progress milestones, per-milestone reports, GVHD review and computed late flags
3. **Task 2:** `1d96bae` feat(03-06): MH-10 progress report/review screens and MH-04 Tiến độ toàn khoa

## Decisions Made

See `key-decisions` in the frontmatter. The most important:

- The D-05 rule lives in one function and uses Vietnam dates.
- The final report is not gated on milestones.
- Resubmitting without a file keeps the old attachment.
- A closed đợt freezes milestone changes, but SV submissions are still accepted.

## Deviations from Plan

None in behaviour. The small additive response fields are listed in the key-decisions (`so_bao_cao`, `so_ngay_tre`, `co_the_nhan_xet`, dashboard `giang_vien`). They exist so the screens can show the MH-10 "Nộp trễ n ngày…" line and the delete warning without computing dates on the client.

## MH-10 / MH-04 fidelity gaps

- **MH-04 "Tiến độ toàn khoa"** is its own page. The progress card, the milestone card and the "SV trễ mốc" statistic are there. The other overview cards on MH-04 (Đề tài chờ duyệt, SV chưa có đề tài, Hội đồng sắp tới) belong to the Bộ môn dashboard, which is plan 03-07.
- **MH-10 in the mockup** puts the GV comment panel and the SV submit form on one screen. Here they are two role-specific pages (`/nhan-xet-tien-do`, `/tien-do`). The texts match the mockup.
- **Extra UI not in the mockup:**
  - A "Mốc" Select in the SV form, which lists only milestones not yet commented.
  - A resubmission warning ("nộp lại sẽ ghi đè nội dung").
  - The SV card also shows the GVHD's comment with a danh_gia tag.
- **File name shown twice.** The chosen file appears both in antd's upload list and in the "Đã chọn: …" line. This is the same as the existing `DocumentUpload`.
- **No notification bell yet.** The SV notification was verified through `/api/notifications`. The header bell is plan 03-07.

## Human-check (self-performed, pending user confirmation)

- **Task 1 (API, real clock):** the e2e through Apache on 2026-09-28 created a milestone due 2026-09-27 and one due 2026-10-05.
  - Result: Mốc 1 `TRE_MOC`, Mốc 2 `DUNG_HAN` with the file, and the SV flagged `tre_moc`.
  - Error messages are in Vietnamese ("Hạn nộp nằm ngoài thời gian đợt đồ án (UC3.1 - E1)", "GVHD đã nhận xét báo cáo mốc này — không thể nộp lại").
- **Task 2 (CDP):** script `scratchpad/cdp0306.py`, headless Chrome at 1440 px.
  - **Throwaway data:** K95 cohort "Đợt CDP 03-06" (đợt 43). DTC225200098 and DTC225200097 proposed topics that were assigned to GV029, with outlines set to DA_DUYET via SQL. SV097's Mốc 1 report was inserted 2 days back so it counts as on time.
  - **Screenshots:** p0306-01..16 are in the scratchpad and were not committed.
  - **Flow covered:**
    - Bộ môn modal: the out-of-range date is refused, then Mốc 1 and Mốc 2 are created.
    - SV submits Mốc 2 with a PDF.
    - GV029 grades it "Cần cải thiện", and the unsubmitted overdue milestone shows only its tag.
    - SV sees the comment; the notification exists.
    - Bộ môn: the matrix, the late-only filter, and the delete attempt that returns 409.
  - **Cleanup:** 0 K95 cohorts, 0 milestones, 0 CDP topics, uploads removed, notifications since the start deleted. Chrome stopped.

## Issues Encountered

- **First CDP run failed in the scratchpad tooling, not the app.**
  - Cause 1: `deploy/sql.sh` connects with a latin1 client charset, so selecting milestones by the Vietnamese name found nothing.
  - Cause 2: the cleanup missed the title-check `ket_qua_kiem_tra_trung_lap` rows.
  - Fix: the script now selects by `thu_tu`, inserts Vietnamese text as a hex literal, and deletes the check rows. The leftover đợt 41 was cleaned by hand.
- **SV page default milestone.** The SV page selects the first unsubmitted milestone (Mốc 1) by default, so the script clicks Mốc 2 explicitly. This is intended behaviour.

## Verification

- `docker compose -f deploy/docker-compose.yml up -d --build --wait` after each task; alembic head is 0009.
- `uv --directory backend run pytest -q`: 49 passed, including the 2 new tests and the route role-coverage test.
- `python3 tools/check-erd-db.py`, `check-docs.py class-erd`, and `check-docs.py render docs/chuong-3-thiet-ke`: OK.
- `bash deploy/e2e-uc2-5.sh`: green 3 times. The E2E milestone count afterwards is 0.
- `npm --prefix frontend ci` + `npm run build`: OK.
- `bash deploy/dom-check.sh /tien-do-toan-khoa 'Mã SV/GV hoặc email'`: OK.
- `dangerouslySetInnerHTML` count: 0. All acceptance-criteria greps pass.

## Threat Flags

None beyond the plan's register:
- **T-03-32:** the topic viewer rule is tested. Attachments are served only via `/api/documents/{id}/download` → `can_view`.
- **T-03-33:** there is a 403 test for each role boundary.
- **T-03-34 / T-03-36:** covered by the row locks, the 409 after a comment, the milestone-to-đợt check (404), and the UNIQUE constraint.
- **T-03-35:** the attachment uses the same validator as outlines.
- **No new packages.**

## Next Phase Readiness

Plan 03-07 can reuse `compute_cohort_progress` for the dashboards' "SV trễ mốc" counts and add the header notification bell. `TIEN_DO_NHAN_XET` rows already exist with `lien_ket "/tien-do"`.

---
*Phase: 03-outline-progress-defense-archive*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 13 created key files present; commits 9356e3c, 69a525a, 1d96bae present in git log.
