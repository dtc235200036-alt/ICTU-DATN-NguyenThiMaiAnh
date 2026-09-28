---
phase: 03-outline-progress-defense-archive
plan: 03
subsystem: defense
tags: [fastapi, sqlalchemy, mysql, background-tasks, react, antd, tanstack-query, react-router]

requires:
  - phase: 03-outline-progress-defense-archive (plan 01)
    provides: "app/services/documents.py (read_and_validate/store/remove_file_quietly/can_view/get_viewable_or_error/to_document_out), app/services/document_check.py (create_pending/run/expire_if_stale/summary), app/services/notifications.py (create, same-transaction pattern), models de_cuong.py (DC_DA_DUYET, LOAI_BAO_CAO_CUOI, TaiLieuDoAn, DeCuong), thong_bao.py (HOI_DONG_PHAN_CONG, LICH_BAO_VE constants pre-declared), core/timeutil.py, schemas/common.py (NFCModel/UtcDateTime/Page), schemas/documents.py (DocumentOut/CheckSummary), test fixtures make_assigned_topic/docx_bytes/pdf_bytes/make_account/auth_headers, UPLOAD_DIR temp dir, deploy/e2e-uc2-5.sh skeleton (call/jget/ok/fail, cleanup already scaffolded for hoi_dong/thanh_vien_hoi_dong/lich_bao_ve/diem_bao_ve)"
  - phase: 03-outline-progress-defense-archive (plan 02)
    provides: "frontend/src/features/documents/{api,DocumentUpload,CheckPanel,CheckStatusTag,routes}.tsx (shared upload/check UI), frontend/src/features/outlines/VersionHistory.tsx (docLabel='báo cáo cuối' variant already designed for this plan), frontend/src/features/accounts/api.ts (useLecturers), frontend/src/api/download.ts, frontend/src/utils/format.ts"
provides:
  - "backend/alembic/versions/0007_hoi_dong_bao_ve.py + app/models/bao_ve.py: hoi_dong, thanh_vien_hoi_dong, lich_bao_ve, diem_bao_ve — exact §3.2.3 shape, no ERD write-back needed (columns pre-documented)"
  - "app/services/defense.py: submit_final_report/get_final_report (UC4.1), create_committee/update_committee/delete_committee/list_committees/get_committee/eligible_students/add_schedule/remove_schedule (UC4.2) — GVHD-exclusion enforced in both add_schedule and update_committee, row-locked (with_for_update) and backed by UNIQUE(lich_bao_ve.sinh_vien_id) for the concurrent-scheduling race"
  - "/api/defense/final-reports/{de_tai_id} (POST 202/GET), /api/defense/committees (GET/POST/GET{id}/PUT{id}/DELETE{id}), /api/defense/eligible-students, /api/defense/committees/{id}/schedules (POST), /api/defense/schedules/{id} (DELETE) — every route declares require_role, BO_MON-only except the SV-only submit route and the ANY_ROLE final-report GET"
  - "frontend/src/features/defense/{api,routes,CommitteePage}.tsx: MH-11 'Lập hội đồng và xếp lịch' full screen; frontend/src/features/outlines/FinalReportTab.tsx: MH-08 'Báo cáo cuối' tab"
  - "deploy/e2e-uc2-5.sh uc4_defense: final report + committee/schedule proven through Apache HTTPS, self-cleaning"
affects: [03-04, 03-05, 03-06, 03-07]

actuals:
  tokens: 26274
  tasks: 2
  commits: 2
  plan_head_before: f4f2b8a57e9f6b518dcd740aa4d4caa9795f5714
  plan_head_after: 12ef618cc7afd74a9b9383be1948affa68e9d2ee

tech-stack:
  added: []
  patterns:
    - "GVHD-exclusion (D-06) checked in TWO write paths (add_schedule and update_committee) against the SAME predicate (topic.giang_vien_id is a current member of the committee) — never a UI-only warning; both paths row-lock hoi_dong FOR UPDATE first so a concurrent member-edit and schedule-add can't race past each other"
    - "Committee/schedule response shapes (ScheduleRow's so_da_cham/diem_tam_tinh/gio_du_kien) are computed server-side in get_committee (batch, no N+1: one query for score counts across all lich_bao_ve ids, one query for latest BAO_CAO_CUOI docs across all de_tai ids) and separately in a single-row helper (_build_schedule_row) used only by add_schedule's response — the batch shape is reserved for potentially-many-row listings, the single-row helper for one-row mutation responses"
    - "gio_du_kien (per-student display time) is ALWAYS computed (SLOT_MINUTES=30 × (thu_tu-1) offset from hoi_dong.gio_bao_ve), never stored — matches the plan's ERD decision that only the committee's own date/time/room are persisted columns"
    - "FinalReportTab reuses VersionHistory with docLabel='báo cáo cuối' (already designed in 03-02 to hide the Trạng thái duyệt column and GVHD-comments Timeline) by mapping FinalReportVersion→OutlineVersion shape with luot_duyet: null — no new version-table component built"

key-files:
  created:
    - backend/alembic/versions/0007_hoi_dong_bao_ve.py
    - backend/app/models/bao_ve.py
    - backend/app/schemas/defense.py
    - backend/app/services/defense.py
    - backend/app/routers/defense.py
    - backend/tests/test_defense_flow.py
    - frontend/src/features/defense/api.ts
    - frontend/src/features/defense/routes.tsx
    - frontend/src/features/defense/CommitteePage.tsx
    - frontend/src/features/outlines/FinalReportTab.tsx
  modified:
    - backend/tests/test_outline_flow.py
    - deploy/e2e-uc2-5.sh
    - frontend/src/features/outlines/OutlinePage.tsx

key-decisions:
  - "Check-order in add_schedule follows the plan's listed message order: topic 404 → GVHD-assigned 409 → final-report-submitted 409 → GVHD-exclusion 409 → committee-already-scored 409 → insert (IntegrityError → already-scheduled-elsewhere 409). update_committee checks committee-already-scored FIRST (per plan text), then validates members, then GVHD-exclusion against already-scheduled students, then applies the member diff."
  - "update_committee's schedule-changed re-notification (UC4.2 A1) sends BOTH the added-member HOI_DONG_PHAN_CONG notification AND the schedule-changed LICH_BAO_VE notification to a newly-added member when both conditions are true in the same PUT — the plan doesn't exclude this double-notify case, and it's arguably correct (a new member both joined AND needs the current date/time/room)."
  - "CommitteePage's 'Sinh viên bảo vệ' card and its eligible-student picker only render once a committee has been saved (has a real id) — a brand-new ('moi') committee shows only the info+members form, since add_schedule needs a real hoi_dong_id to POST against."
  - "Rule 1 fix (see Deviations): test_upload_rejected_before_any_version now diffs UPLOAD_DIR against a pre-test snapshot instead of asserting the whole shared session-wide temp dir is empty — this plan's tests legitimately write real files earlier in the same pytest session when run in the file order the plan's own <verify> command specifies (test_defense_flow.py before test_outline_flow.py)."

patterns-established:
  - "Any future UC that needs a 'this account cannot judge/approve their own related student/topic' rule (committee scoring in 03-04, or any later conflict-of-interest check) should follow defense.py's shape: a plain membership/ownership COUNT query inside the write path, under a row lock, never a separate pre-check endpoint."

requirements-completed: [DEFN-01, DEFN-02, NOTF-01]

coverage:
  - id: D1
    description: "Per DEFN-01, D-01/D-02/D-04 and UC4.1: an SV whose outline is Đã duyệt submits the final report (DOCX/PDF, same validation and versioned storage as outlines) on MH-08's 'Báo cáo cuối' tab; each submission answers 202 and triggers the stub duplicate check in the background; resubmission is refused once the SV is scheduled into a committee"
    requirement: "DEFN-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_defense_flow.py::test_final_report_gate — pass (409 before Đã duyệt, 403 for GV/Bộ môn on submit, 202 + HOAN_TAT check for the SV, 403 for another SV on GET, 409 resubmission after scheduled)"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc4_defense — submit → poll HOAN_TAT → GVHD GET 200 → other SV GET 403 → resubmit-after-scheduled 409 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP session (scratchpad cdp_check_0303.py/0303b.py): p0303-01..03 (SV MH-08 Báo cáo cuối tab, upload, Hoàn tất - 0% panel, version history v1-v3), disabled Alert text confirmed via DOM query after being scheduled — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Visual fidelity of MH-08's Báo cáo cuối tab in a real browser is a judgment call; self-performed via CDP per the autonomous-run instruction, genuine user confirmation still pending."
  - id: D2
    description: "Per DEFN-02, D-06 and UC4.2: the Bộ môn creates a hội đồng (tên, ngày, giờ, phòng) with 3–5 distinct unlocked GVs and exactly one Chủ tịch (at most one Thư ký), and schedules students who have submitted a final report; every committee endpoint is BO_MON-only"
    requirement: "DEFN-02"
    verification:
      - kind: unit
        ref: "backend/tests/test_defense_flow.py::test_committee_rules — pass (403 for SV/GV on every committee/schedule route, 422 for 2-member/2-chủ-tịch/repeated-GV payloads, 201 for valid 3-member committees)"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc4_defense — committee A (GV026 CHU_TICH/GV027 THU_KY/GV028 UY_VIEN) 201, eligible-students lists the topic before scheduling — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP: p0303-04..07/p0303-09/10 (MH-11 empty state, Tạo hội đồng, 3-member Form.List filled via real Select showSearch interactions, Lưu hội đồng và lịch → toast + Sinh viên bảo vệ card appears) — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Visual fidelity of MH-11's form/Select interactions in a real browser is a judgment call; self-performed via CDP, genuine user confirmation still pending."
  - id: D3
    description: "Per D-06 (block, research Pitfall 7): the server refuses with 409 to schedule a student into a committee that contains that student's GVHD, and refuses a member change that would seat a scheduled student's GVHD — not a UI-only warning"
    requirement: "DEFN-02"
    verification:
      - kind: unit
        ref: "backend/tests/test_defense_flow.py::test_committee_rules — pass (scheduling into a committee containing the GVHD → 409 + zero lich_bao_ve rows; PUT adding the GVHD to a committee with an already-scheduled student → 409)"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc4_defense — committee B contains GV029 (the topic's GVHD); scheduling into B → 409 (D-06); scheduling into A (no GVHD) → 201 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP: p0303-08 (eligible-student option for the GVHD-conflicting committee is greyed out/disabled with the ' (GVHD là thành viên hội đồng)' suffix, verified programmatically as DISABLED via the option's ant-select-item-option-disabled class) — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Confirming the disabled-option UX (not just the server 409) in a real browser is a judgment call; self-performed via CDP, genuine user confirmation still pending."
  - id: D4
    description: "Per §3.2.5(c): UNIQUE(lich_bao_ve.sinh_vien_id) guarantees one schedule per student even under concurrent scheduling (second → 409); a committee with any score can no longer change members or schedule rows"
    requirement: "DEFN-02"
    verification:
      - kind: unit
        ref: "backend/tests/test_defense_flow.py::test_committee_rules — pass (scheduling the already-scheduled student into a second GVHD-free committee → 409 via IntegrityError→409 mapping)"
        status: pass
      - kind: e2e
        ref: "python3 tools/check-erd-db.py — pass (uq_lich_bao_ve_sinh_vien_id present and matches erd.puml, no drift)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Per D-08 and NOTF-01: members receive HOI_DONG_PHAN_CONG and scheduled students receive LICH_BAO_VE notifications in the same transaction as the committee/schedule write; a date/time/room change re-notifies members and scheduled students (UC4.2 A1)"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_defense_flow.py::test_committee_rules — pass (HOI_DONG_PHAN_CONG for a member after create, LICH_BAO_VE for the SV after schedule)"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc4_defense — GV026 has HOI_DONG_PHAN_CONG, DTC225200098 has LICH_BAO_VE — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP session: after editing committee B's room (P502→P502-Sua) via PUT, GET /api/notifications for the CDP test SV shows BOTH the original 'Bạn đã được xếp lịch bảo vệ: ... phòng P502' and a second 'Lịch bảo vệ thay đổi: ... phòng P502-Sua' row — confirms the UC4.2 A1 re-notify path end-to-end, a scenario not exercised by the unit tests or e2e script (self-viewed via curl against the live API, not a screenshot)"
        status: pass
    human_judgment: true
    rationale: "The re-notify-on-change path was confirmed via a live API call during the CDP session rather than a dedicated automated test; flagging for genuine user confirmation per the autonomous-run instruction."
  - id: D6
    description: "Per D-09: this plan is step 2 of the demo chain (outline → defense → archive); deploy/e2e-uc2-5.sh gains the final-report + committee part of uc4_defense"
    requirement: "DEFN-01"
    verification:
      - kind: integration
        ref: "bash deploy/e2e-uc2-5.sh (uc2_outline + uc4_defense, full run) — pass; test COUNT(hoi_dong WHERE phong LIKE 'E2E-%')=0 after the run — pass (0)"
        status: pass
    human_judgment: false

duration: ~38min
completed: 2026-09-28
status: complete
---

# Phase 3 Plan 3: UC4.1/4.2 Defense — Final Report + Committee/Schedule Summary

**A student with an approved outline submits the final report (checked in the background for duplicates) and the Bộ môn forms 3–5-member defense committees and schedules students — the server (never just the UI) refuses to seat a student's own GVHD on their committee, both at schedule time and at any later member edit.**

## Performance

- **Duration:** ~38 min
- **Started:** 2026-09-28T03:08Z (STATE.md, end of plan 03-02)
- **Completed:** 2026-09-28T03:46Z
- **Tasks:** 2/2 completed
- **Files modified:** 13 (10 created, 3 modified)

## Accomplishments

- **Task 1 (backend, `tdd="true"`):** Alembic 0007 creates `hoi_dong`/`thanh_vien_hoi_dong`/`lich_bao_ve`/`diem_bao_ve` exactly matching §3.2.3/erd.puml (no doc write-back needed — `tools/check-erd-db.py` stays green with zero changes). `app/services/defense.py` implements UC4.1 (`submit_final_report`/`get_final_report`, gated on GVHD-assigned + outline Đã duyệt + not-yet-scheduled, reusing `documents.store`/`document_check.create_pending` exactly like `outlines.submit`) and UC4.2 (`create_committee`/`update_committee`/`delete_committee`/`list_committees`/`get_committee`/`eligible_students`/`add_schedule`/`remove_schedule`). Member validation (`_validate_members`) enforces 3–5 distinct GVs, exactly one Chủ tịch, at most one Thư ký, and GV-exists-and-unlocked (mirroring `topic_approval.approve`'s pattern). The D-06 GVHD-exclusion check runs in both `add_schedule` (against the topic's assigned GVHD) and `update_committee` (against every already-scheduled student's GVHD) under a `with_for_update()` row lock on `hoi_dong`, with `UNIQUE(lich_bao_ve.sinh_vien_id)` as the final defense against a concurrent double-schedule (`IntegrityError` → 409). `/api/defense` declares per-route `require_role` (SV-only submit, ANY_ROLE final-report GET, BO_MON-only for everything else). `backend/tests/test_defense_flow.py` has the plan's 2 focused tests (final-report gate; the full committee-rules matrix including the GVHD-exclusion 409 on both `add_schedule` and `update_committee`). `deploy/e2e-uc2-5.sh` gained `uc4_defense`, run after `uc2_outline`, proving the whole UC4.1/4.2 slice through Apache HTTPS with two committees (one deliberately containing the GVHD to prove the 409, one clean) and self-cleaning via the already-scaffolded `HOI_DONG_IDS` cleanup.
- **Task 2 (frontend):** `frontend/src/features/defense/api.ts` mirrors `schemas/defense.py` 1:1 and provides every hook the plan named (`useFinalReport`/`useSubmitFinalReport`/`useCommittees`/`useCommittee`/`useEligibleStudents`/`useSaveCommittee`/`useDeleteCommittee`/`useAddSchedule`/`useRemoveSchedule`). `FinalReportTab.tsx` is MH-08's "Báo cáo cuối" tab, reusing `DocumentUpload`/`CheckPanel`/`VersionHistory` as-is (no review-loop UI, per `docLabel='báo cáo cuối'`). `CommitteePage.tsx` is the full MH-11 screen: a committee list (`?hoi_dong_id=` / `moi`), an info+members Form (`Form.List` with 3–5 soft-capped rows, `Select showSearch` over `useLecturers`), a Save button that Tooltips-and-disables once any row has a score, a conditional Delete, and a "Sinh viên bảo vệ" table whose "Thêm sinh viên" picker **disables** (not just warns) any eligible student whose GVHD already sits on the committee.
- **Both tasks' `<human-check>` items were self-performed** via a CDP-driven headless Chrome session against fresh throwaway test data (K97 cohort, cleaned up afterward) — see coverage D1-D3/D5 and "Human-check" below. The session incidentally also exercised and confirmed the UC4.2 A1 room-change re-notification path, which neither the unit tests nor the e2e script cover.

## Task Commits

1. **Task 1: UC4.1/4.2 defense backend (final report + committee/schedule, GVHD exclusion)** — `2888ca5` (feat)
2. **Task 2: MH-08 Báo cáo cuối tab + MH-11 committee/schedule screen** — `12ef618` (feat)

## Files Created/Modified

**Created:** `backend/alembic/versions/0007_hoi_dong_bao_ve.py`, `backend/app/models/bao_ve.py`, `backend/app/{schemas,services,routers}/defense.py`, `backend/tests/test_defense_flow.py`, `frontend/src/features/defense/{api,routes,CommitteePage}.tsx`, `frontend/src/features/outlines/FinalReportTab.tsx`.
**Modified:** `backend/tests/test_outline_flow.py` (Rule 1 fix, see Deviations), `deploy/e2e-uc2-5.sh` (`uc4_defense`), `frontend/src/features/outlines/OutlinePage.tsx` (wires the new tab).

## Decisions Made

See `key-decisions` in frontmatter. Summary: check-order in `add_schedule`/`update_committee` follows the plan's listed message order exactly; a newly-added committee member can receive both `HOI_DONG_PHAN_CONG` and `LICH_BAO_VE` in the same PUT when the date/time/room also changed; the "Sinh viên bảo vệ" card only renders for an already-saved committee (needs a real id to POST schedules against).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `test_upload_rejected_before_any_version` scanned the whole shared `UPLOAD_DIR` tree instead of diffing against a pre-test snapshot**
- **Found during:** Task 1, running `pytest tests/test_defense_flow.py tests/test_outline_flow.py tests/test_auth.py` per this plan's own `<verify>` command
- **Issue:** `UPLOAD_DIR` is a single temp directory shared for the whole pytest session (set once in `conftest.py`, never cleaned between tests). The pre-existing test asserted **zero files exist anywhere in that directory** after its own rejected uploads — an assumption that only held when it happened to be the first test in the session to touch `UPLOAD_DIR`. This plan's `test_defense_flow.py` tests (which legitimately write real PDF files) now run *before* it in the file order the plan's `<verify>` command specifies, so the assertion failed on files this plan's own tests wrote — not a bug in this plan's code, but a latent test-isolation bug in a prior plan's test that this plan's test-file ordering exposed.
- **Fix:** Snapshot `UPLOAD_DIR`'s file set before the rejected-upload attempts, and after them assert only the **diff** (files newly created by this test) is empty — not the whole directory tree.
- **Files modified:** `backend/tests/test_outline_flow.py`
- **Verification:** `uv --directory backend run pytest -q tests/test_defense_flow.py tests/test_outline_flow.py tests/test_auth.py` — 10/10 pass (previously 1 failure); full suite `uv --directory backend run pytest -q` — 44/44 pass.
- **Committed in:** `2888ca5` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug, test-isolation). **Impact:** No functional/production-code gap — the fix is scoped entirely to a pre-existing test's isolation assumption, verified regression-free against the exact file-invocation order this plan's own `<verify>` command specifies.

## Issues Encountered

- Initial CDP attempts to drive antd's `Select showSearch` dropdowns failed twice: first because the lecturer option labels (`"{hoc_vi} {ho_ten}"`, e.g. "TS. Vũ Phú Xuân") never contain the `GV0XX` code I was searching for; second because typing into "the last `.ant-select-selection-search-input` in the whole document" as a fallback sometimes hit the wrong row's search box, and reading options from `.ant-select-item-option` globally (not scoped to the currently-visible dropdown panel) risked stale matches. Fixed by resolving each Select's own search input via a `window.__cdpLastSelect` reference set at open-time, and by scoping option lookup to the dropdown panel(s) that are actually visible (`:not(.ant-select-dropdown-hidden)`). Scratchpad-tooling issue only, not a shipped-code defect — confirms nothing about `CommitteePage.tsx` itself, which a real user's mouse/keyboard would drive correctly either way.

## Human-check (self-performed, pending user confirmation)

Per the autonomous-run instruction, self-performed via a CDP-driven headless Chrome session (`google-chrome --headless=new --remote-debugging-port=9351 --remote-allow-origins='*'`, 1280×3200 viewport), screenshots in the scratchpad (not committed to the repo). Fresh throwaway data: cohort K97 (id 28), a self-proposed topic (id 52, SV DTC225200010 / GVHD GV010), outline approved directly via `db` (matching the test convention, no need to replay UC2).

- **p0303-01/02/03:** SV's MH-08 "Báo cáo cuối" tab — empty upload card, submit → toast → version history (v1..v3, the tab was exercised twice across two script runs), `CheckPanel` showing a genuine `Hoàn tất - 0%` (no cross-topic duplicate seeded this time) with the threshold/tag/table all rendering as designed.
- **p0303-04..07:** Bộ môn's MH-11 — empty "Danh sách hội đồng", "Tạo hội đồng", the info form + 3-member `Form.List` filled via real `Select showSearch` typing/clicking (not raw API calls), "Lưu hội đồng và lịch" → toast "Đã tạo hội đồng" → "Sinh viên bảo vệ" card appears with an empty schedule table and a "Xóa hội đồng" button (only shown because it has 0 students).
- **p0303-08:** The "Thêm sinh viên" picker's option for the CDP test topic is **disabled** (verified both visually — greyed text — and programmatically via the option's `ant-select-item-option-disabled` class) when the committee contains that topic's GVHD (GV010) — confirms D-06's UI-side mirror of the server 409.
- **p0303-09..12 (second committee, no GVHD conflict):** created "Hội đồng CDP 03-03 - B", added the test student successfully (`0/3 đã chấm`, `—` Điểm TB, `Hoàn tất - 0%` Kiểm tra trùng lặp, "Gỡ khỏi lịch" action), then edited the room (P502 → P502-Sua) and re-saved — confirmed via `GET /api/notifications` (not a screenshot, a live API call in the same session) that the student now has **both** the original "Bạn đã được xếp lịch bảo vệ: ... phòng P502" notification and a new "Lịch bảo vệ thay đổi: ... phòng P502-Sua" notification, proving the UC4.2 A1 re-notify-on-change path end-to-end — a scenario neither the unit tests nor `deploy/e2e-uc2-5.sh` currently exercise.

All throwaway data (cohort 28, topic 52, both hội đồng, their `tai_lieu_do_an`/`de_cuong`/`ket_qua_kiem_tra_trung_lap`/`thong_bao` rows, and the 3 uploaded PDF files) fully deleted afterward; `uv --directory backend run pytest -q` (44/44) and `bash deploy/e2e-uc2-5.sh` re-run clean post-cleanup, `SELECT COUNT(*) FROM hoi_dong` = 0.

**User confirmation of this check is still pending** — flagged here per coverage items D1, D2, D3, D5.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Phase 3's defense subsystem (UC4.1/4.2, DEFN-01/02, NOTF-01 for this slice) is complete and proven through Apache HTTPS. Entry points the next plans build on:
- **03-04** (defense scoring, DEFN-03/04 — chấm điểm, chốt kết quả) extends `get_committee`'s `ScheduleRow` (already carries `so_da_cham`/`diem_tam_tinh`/`diem_trung_binh`/`da_chot` — the scoring plan only needs to add `diem_bao_ve` writes and the chốt transition), and reuses `_can_view_final_report`'s viewer rule (the comment already flags "plan 03-04 adds committee members" as a viewer).
- **03-05** (archive, REPO-01..03) can key off `lich_bao_ve.da_chot`/`diem_trung_binh` once 03-04 lands.
- **03-07** (e2e/README) can extend `deploy/e2e-uc2-5.sh`'s `uc4_defense` further (scoring assertions) rather than adding a new function.

No blockers. The pending items are genuine user confirmation of the self-performed CDP checks (D1/D2/D3/D5, coverage), not functional gaps.

---
*Phase: 03-outline-progress-defense-archive*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 10 created/referenced key files confirmed present on disk; both task commits (`2888ca5`, `12ef618`) confirmed present in `git log --oneline --all`.
