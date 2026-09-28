---
phase: 03-outline-progress-defense-archive
plan: 04
subsystem: defense
tags: [fastapi, sqlalchemy, mysql, alembic, background-tasks, react, antd, tanstack-query]

requires:
  - phase: 03-outline-progress-defense-archive (plan 03)
    provides: "models bao_ve.py (HoiDong/ThanhVienHoiDong/LichBaoVe/DiemBaoVe), services/defense.py (get_committee, _build_schedule_row, _latest_final_report_or_none, _compute_slot_time), routers/defense.py, e2e uc4_defense (committee A GV026/027/028 dated today), frontend features/defense (api.ts, CommitteePage)"
  - phase: 03-outline-progress-defense-archive (plan 01)
    provides: "documents.can_view/get_viewable_or_error, document_check.summary/expire_if_stale, notifications.create, ai_client (get_ai_client, AiClientStub.ingest, INGEST_LOG), core/db SessionLocal, core/timeutil today_vn"
provides:
  - "Alembic 0008 do_an_kho (+ ma_so_sinh_vien/ho_ten_sinh_vien snapshot, uq_do_an_kho_de_tai_id, ck nguon/trang_thai_index/diem, ix khoa/giang_vien_id)"
  - "app/models/kho.py: DoAnKho + HE_THONG/IMPORT/CHUA_INDEX/DA_INDEX"
  - "app/services/archive.py: insert_from_defense(db, lich) -> DoAnKho (add+flush, no commit); latest_final_report(db, de_tai_id); ingest_payload(db, kho) -> (loai, text); run_ingest(do_an_kho_ids: list[int]) -> None (own SessionLocal, per-id try/except)"
  - "app/services/defense.py: my_committees, get_schedule_for_scoring, score, finalize -> (FinalizeOut, do_an_kho_id), my_defense"
  - "app/services/documents.py: is_committee_member_for_topic(db, giang_vien_id, de_tai_id); can_view grants BAO_CAO_CUOI to committee members"
  - "Routes GET /api/defense/my-committees (GV), GET /api/defense/schedules/{id} (GV, BO_MON), PUT /api/defense/schedules/{id}/score (GV), POST /api/defense/schedules/{id}/finalize (BO_MON, BackgroundTasks run_ingest), GET /api/defense/me (SV)"
  - "frontend: ScoringPage (/cham-diem, MH-12), MyDefensePage (/bao-ve, UC4.5/MH-02 card), CommitteePage 'Chốt kết quả' (MH-11)"
  - "deploy/e2e-uc2-5.sh uc4_defense part 2; globals LICH_BAO_VE_ID and DO_AN_KHO_ID for plan 03-05's uc5_archive"
affects: [03-05, 03-06, 03-07, 04-04, 04-05]

actuals:
  tokens: 15500
  tasks: 2
  commits: 3
  plan_head_before: 3b48205d48f02eceb82ec196e9213fa4afd7dba6
  plan_head_after: cc4daa5c8cc3832ba060ef143f3fdebb3950bfc8

tech-stack:
  added: []
  patterns:
    - "Score/finalize serialise on a SELECT … FOR UPDATE of the lich_bao_ve row; finalize flips da_chot with a conditional UPDATE WHERE da_chot = FALSE and inserts the archive row + notification in the same transaction; the AI ingest runs after commit in BackgroundTasks with its own SessionLocal"
    - "Committee-scoped document access is a single helper (documents.is_committee_member_for_topic) reused by documents.can_view (BAO_CAO_CUOI only) and defense._can_view_final_report"

key-files:
  created:
    - backend/alembic/versions/0008_do_an_kho.py
    - backend/app/models/kho.py
    - backend/app/services/archive.py
    - frontend/src/features/defense/ScoringPage.tsx
    - frontend/src/features/defense/MyDefensePage.tsx
  modified:
    - backend/app/services/defense.py
    - backend/app/services/documents.py
    - backend/app/schemas/defense.py
    - backend/app/routers/defense.py
    - backend/tests/test_defense_flow.py
    - deploy/e2e-uc2-5.sh
    - docs/chuong-3-thiet-ke/csdl/erd.puml (+png/svg)
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml (+png/svg)
    - docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md
    - frontend/src/features/defense/api.ts
    - frontend/src/features/defense/routes.tsx
    - frontend/src/features/defense/CommitteePage.tsx

key-decisions:
  - "Mean rounding: Decimal sum / n, quantize(0.01, ROUND_HALF_UP) — measured 8.0/8.5/9.0 → 8.50 (unit test, e2e and CDP run)"
  - "Ingest payload: ref_id = do_an_kho.id; DOCUMENT with the latest BAO_CAO_CUOI's noi_dung_trich_xuat when that version extracted cleanly, else TOPIC with 'ten_de_tai\\ntu_khoa'"
  - "insert_from_defense writes trang_thai_index CHUA_INDEX; only run_ingest's success path flips it to DA_INDEX (failure leaves/resets CHUA_INDEX, logged, next id continues)"
  - "Bộ môn may open GET /schedules/{id} (read-only): co_the_cham false with ly_do 'Chỉ thành viên hội đồng được chấm điểm'; PUT score is GIANG_VIEN-only"
  - "Committee members get read access only to the final report (BAO_CAO_CUOI), never to the outline or progress documents of that topic"

patterns-established:
  - "Background post-commit side effects (AI ingest) follow document_check.run: own SessionLocal, broad per-item except, terminal state always written"

requirements-completed: [DEFN-03, DEFN-04, REPO-01, NOTF-01]

coverage:
  - id: D1
    description: "Per DEFN-03, D-06 and UC4.3 E1: a GV sees and scores only students scheduled in a committee they belong to; any other GV gets 403 on schedule detail, score write and final-report download/check"
    requirement: "DEFN-03"
    verification:
      - kind: unit
        ref: "backend/tests/test_defense_flow.py::test_scoring_is_committee_scoped_and_finalize_is_one_way — pass (GV D 403 on the 4 paths, member C 200 download, SV/BO_MON 403 on PUT score)"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc4_defense — GV025 403 on schedule + download, GV026 my-committees + download 200 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0304-02/03: GV025 /cham-diem shows 'Bạn chưa được phân vào hội đồng nào', deep link with lich_id shows the same empty state — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Self-performed via headless Chrome per autonomous-run instruction; user confirmation pending."
  - id: D2
    description: "Per D-06: one score 0–10, max one decimal + nhận xét; refused before the defense date and after chốt; members see only their own score, SV sees no score before chốt"
    requirement: "DEFN-03"
    verification:
      - kind: unit
        ref: "test_scoring_is_committee_scoped_and_finalize_is_one_way — 10.5/8.25 → 422; tomorrow committee → 409; re-score after chốt → 409; /me ket_qua null before chốt"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0304-04/05/09 (MH-12 list, scoring panel with download + check summary + 'Đã lưu điểm', form disabled with 'Kết quả đã chốt' after finalize)"
        status: pass
    human_judgment: true
    rationale: "MH-12 visual fidelity judged by self-run CDP screenshots; user confirmation pending."
  - id: D3
    description: "Per DEFN-04 and §3.2.5(d): chốt only when score count equals member count, mean rounded to 2 decimals, conditional UPDATE, later chốt/score → 409"
    requirement: "DEFN-04"
    verification:
      - kind: unit
        ref: "test_scoring_is_committee_scoped_and_finalize_is_one_way — 409 '2/3' then 200 with 8.50, second finalize 409"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh — finalize 409 '(2/3)', then 200 diem_trung_binh 8.5, GV026 re-score 409 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0304-06/07/08: MH-11 '2/3 đã chấm' + 'Chờ tất cả thành viên chấm' → Popconfirm 'Chốt kết quả bảo vệ?' → 'Đã chốt', Điểm TB 8.50"
        status: pass
    human_judgment: true
    rationale: "MH-11 chốt interaction self-verified via CDP; user confirmation pending."
  - id: D4
    description: "Per REPO-01, D-07 and UC5.2: chốt inserts one do_an_kho row (HE_THONG, khóa, tên, SV id+mã+họ tên, GVHD, điểm, tu_khoa NULL) and a background job ingests it → DA_INDEX"
    requirement: "REPO-01"
    verification:
      - kind: unit
        ref: "test_scoring_is_committee_scoped_and_finalize_is_one_way — exactly one row with all fields, DA_INDEX, INGEST_LOG +1 with that id"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh — deploy/sql.sh shows HE_THONG|DA_INDEX for DO_AN_KHO_ID; K98 rows cleaned (COUNT = 0)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Per DEFN-04, UC4.5, NOTF-01: SV sees schedule and, only after chốt, the score; KET_QUA_BAO_VE notification in the chốt transaction"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "test_scoring_is_committee_scoped_and_finalize_is_one_way — KET_QUA_BAO_VE present, /me 8.5 after chốt"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh — DTC225200098 /me 8.5 + KET_QUA_BAO_VE — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0304-01/10: 'Lịch và kết quả bảo vệ' with Chủ tịch/Thư ký/Ủy viên lines and 'Chưa có kết quả', then Statistic 'Điểm bảo vệ' 8.50"
        status: pass
    human_judgment: true
    rationale: "MH-02 card fidelity self-verified; user confirmation pending."
  - id: D6
    description: "Per D-09: e2e proves outline → defense → archive through Apache"
    requirement: "DEFN-04"
    verification:
      - kind: integration
        ref: "bash deploy/e2e-uc2-5.sh after docker compose rebuild — pass; dom-check /cham-diem and /bao-ve end on the login form — pass"
        status: pass
    human_judgment: false

duration: ~22min
completed: 2026-09-28
status: complete
---

# Phase 3 Plan 4: UC4.3–4.5 + UC5.2 Scoring, Finalize, Auto-archive Summary

**Committee members now score only their own students (0–10, one decimal), the Bộ môn finalizes the ROUND_HALF_UP mean under a row lock, and the same transaction archives the thesis into `do_an_kho` and notifies the student. The AI index push then runs in the background. The demo chain outline → defense → archive runs end to end through Apache.**

## Performance

- **Duration:** ~22 min (2026-09-28T03:47Z → 04:09Z)
- **Tasks:** 2/2
- **Files:** 5 created, 12 modified (plus 4 re-rendered diagram images)

## Accomplishments

- **Task 1 (backend, TDD):** RED test first (`090be7d`, failed on the missing `app.models.kho`), then GREEN (`c9ae8ba`).
  - Alembic 0008 creates `do_an_kho` exactly as specified. The two snapshot columns were written back into `erd.puml`, `lop-thuc-the.puml` and §3.2.3, which also now lists `CHUA_INDEX`/`DA_INDEX`. Both diagrams were re-rendered. `check-erd-db.py` and `check-docs.py class-erd/render` pass.
  - Scoring runs under `FOR UPDATE`. The error order is 403 (not a member) → 409 (already chốt) → 409 (before the defense date), then an upsert of the caller's own score.
  - `finalize` checks that the score count equals the member count, computes the Decimal mean with ROUND_HALF_UP, and flips `da_chot` with a conditional UPDATE. In the same transaction it calls `archive.insert_from_defense`, creates the `KET_QUA_BAO_VE` notification and commits. The router then queues `archive.run_ingest`.
  - `documents.can_view` now lets committee members read `BAO_CAO_CUOI` files only.
- **Task 2 (frontend, `cc4daa5`):**
  - **MH-12** `/cham-diem`: my committees, the students table with "Điểm của tôi" / "Chưa chấm", and a scoring panel with the download button, check summary sentence, "Xem chi tiết", InputNumber (precision 1), Nhận xét and "Lưu điểm". The form is disabled with an info Alert explaining why when scoring is not allowed.
  - **MH-11:** the action column shows "Chốt kết quả" (Popconfirm with the mean and a warning) only when every member has scored. Otherwise it shows "Chờ tất cả thành viên chấm", and "Đã chốt" after finalizing.
  - **UC4.5** `/bao-ve`: committee · room, date · time, the Chủ tịch/Thư ký/Ủy viên lines, and "Chưa có kết quả" until finalized, then a Statistic with the score.

## Contracts for plan 03-05

- `archive.insert_from_defense(db, lich) -> DoAnKho` does add + flush and never commits.
- `archive.ingest_payload(db, kho) -> (loai, text)`: returns `("DOCUMENT", <latest BAO_CAO_CUOI noi_dung_trich_xuat>)` when that version extracted cleanly, otherwise `("TOPIC", "ten_de_tai\ntu_khoa")`. `ref_id` is `do_an_kho.id`.
- `archive.run_ingest(do_an_kho_ids: list[int]) -> None` can be reused for re-index and import. On failure it leaves `CHUA_INDEX`.
- e2e: `uc4_defense` sets the globals `LICH_BAO_VE_ID` and `DO_AN_KHO_ID`, which `uc5_archive` can use. The existing cleanup already deletes `do_an_kho` rows for the K98 đợt and K98 IMPORT rows.
- Measured mean rounding: 8.0 / 8.5 / 9.0 → `8.50` (ROUND_HALF_UP on Decimal, not float).

## Deviations from Plan

None in production scope. One test-only adjustment while going GREEN: the test's own `db` session had started a REPEATABLE READ snapshot, so it could not see the archive row written by the request and the background task. The fix calls `db.rollback()` before re-reading (instead of `expire_all()`). It lives inside the new test and was committed with Task 1.

## MH-11 / MH-12 fidelity gaps

- In MH-12 the "Chấm điểm" card also shows a short subtitle (mã SV · hội đồng · date/time · room) and the topic name. This context is not in the mockup.
- In MH-11, while no scores exist, the "Hành động" column shows both "Gỡ khỏi lịch" and "Chờ tất cả thành viên chấm". This keeps the 03-03 remove action.
- The success toast after chốt reads "Đã chốt kết quả — điểm 8.50; đồ án đã vào kho". No mockup text exists for it.
- In MH-12, when the check result is not yet `HOAN_TAT`, a CheckStatusTag is shown instead of the percentage sentence.

## Human-check (self-performed, pending user confirmation)

This was run through a CDP-driven headless Chrome session (`scratchpad/cdp0304.py`, 1440×1100) on throwaway cohort K95 (đợt 32, topic 56, "Hội đồng 3", room 302, dated today). The accounts were the e2e ones (GV025–029, DTC225200098), used while the e2e was not running. Screenshots p0304-01..10 are in the scratchpad and were not committed:

1. The student before chốt sees the schedule, members and "Chưa có kết quả".
2. GV025 sees "Bạn chưa được phân vào hội đồng nào", including via a deep link with `lich_id`.
3. GV026 sees MH-12, downloads (the button shows "PDF, 880 B"), reads "Tỷ lệ tổng 0% - dưới ngưỡng 30% của Bộ môn.", and saves 8.0 with a nhận xét ("Đã lưu điểm").
4. GV027 saves 8.5.
5. The Bộ môn sees "2/3 đã chấm" and "Chờ tất cả thành viên chấm".
6. GV028 saves 9.0.
7. The Bộ môn sees "3/3 đã chấm", opens the Popconfirm (buttons Hủy/Đồng ý), confirms, and sees the toast, the "Đã chốt" tag and 8.50.
8. GV026 reloads and sees the form disabled with "Kết quả đã chốt".
9. The student sees "Điểm bảo vệ 8.50".

The archive row was `HE_THONG|DA_INDEX|8.50|K95|DTC225200098`. The data was fully cleaned afterwards: 0 K95 đợt, 0 hội đồng, 0 do_an_kho, and uploaded files removed. Task 1's API-level human check (messages 403 UC4.3 E1 / 409 "(2/3)") is covered by the unit test and the e2e output line "Chưa đủ thành viên hội đồng chấm điểm (2/3)".

## Issues Encountered

- The first CDP runs failed for scratchpad-tooling reasons, not app defects:
  - The login redirect lands on "/", so the script now navigates explicitly after logging in.
  - The antd Popconfirm confirm button is labelled "Đồng ý", not "OK".
  - The script was not idempotent across reruns, so the throwaway scores were reset via SQL.

## Verification

- `docker compose … up -d --build --wait`: alembic head 0008.
- Full `pytest` (45 passed).
- `check-erd-db.py`, `check-docs.py class-erd`, `check-docs.py render docs/chuong-3-thiet-ke`.
- `bash deploy/e2e-uc2-5.sh` (run 3 times, all green); K98 `do_an_kho` count is 0 afterwards.
- `npm ci` + `npm run build`.
- `dom-check.sh /cham-diem` and `/bao-ve`.
- No `dangerouslySetInnerHTML`.

---
*Phase: 03-outline-progress-defense-archive*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 5 created key files present; commits 090be7d, c9ae8ba, cc4daa5 present in git log.
