---
phase: 03-outline-progress-defense-archive
verified: 2026-09-28T12:00:00Z
status: human_needed
score: 5/5 must-haves verified
covered_files: [".planning/phases/03-outline-progress-defense-archive/03-01-PLAN.md", ".planning/phases/03-outline-progress-defense-archive/03-01-SUMMARY.md", ".planning/phases/03-outline-progress-defense-archive/03-02-PLAN.md", ".planning/phases/03-outline-progress-defense-archive/03-02-SUMMARY.md", ".planning/phases/03-outline-progress-defense-archive/03-03-PLAN.md", ".planning/phases/03-outline-progress-defense-archive/03-03-SUMMARY.md", ".planning/phases/03-outline-progress-defense-archive/03-04-PLAN.md", ".planning/phases/03-outline-progress-defense-archive/03-04-SUMMARY.md", ".planning/phases/03-outline-progress-defense-archive/03-05-PLAN.md", ".planning/phases/03-outline-progress-defense-archive/03-05-SUMMARY.md", ".planning/phases/03-outline-progress-defense-archive/03-06-PLAN.md", ".planning/phases/03-outline-progress-defense-archive/03-06-SUMMARY.md", ".planning/phases/03-outline-progress-defense-archive/03-07-PLAN.md", ".planning/phases/03-outline-progress-defense-archive/03-07-SUMMARY.md", "backend/Dockerfile", "backend/alembic/versions/0006_de_cuong_tai_lieu_thong_bao.py", "backend/alembic/versions/0007_hoi_dong_bao_ve.py", "backend/alembic/versions/0008_do_an_kho.py", "backend/alembic/versions/0009_tien_do.py", "backend/alembic/versions/0011_chi_tiet_nguon.py", "backend/app/core/config.py", "backend/app/core/timeutil.py", "backend/app/models/bao_ve.py", "backend/app/models/de_cuong.py", "backend/app/models/kho.py", "backend/app/models/thong_bao.py", "backend/app/models/tien_do.py", "backend/app/models/trung_lap.py", "backend/app/routers/archive.py", "backend/app/routers/defense.py", "backend/app/routers/documents.py", "backend/app/routers/notifications.py", "backend/app/routers/outlines.py", "backend/app/routers/progress.py", "backend/app/schemas/archive.py", "backend/app/schemas/common.py", "backend/app/schemas/dashboard.py", "backend/app/schemas/defense.py", "backend/app/schemas/documents.py", "backend/app/schemas/notifications.py", "backend/app/schemas/outlines.py", "backend/app/schemas/progress.py", "backend/app/services/archive.py", "backend/app/services/dashboard.py", "backend/app/services/defense.py", "backend/app/services/documents.py", "backend/app/services/notifications.py", "backend/app/services/outlines.py", "backend/app/services/progress.py", "backend/app/services/topic_approval.py", "backend/pyproject.toml", "backend/tests/conftest.py", "backend/tests/test_archive.py", "backend/tests/test_defense_flow.py", "backend/tests/test_notifications.py", "backend/tests/test_outline_flow.py", "backend/tests/test_progress_flow.py", "deploy/.env.example", "deploy/README.md", "deploy/docker-compose.yml", "deploy/e2e-uc1.sh", "deploy/e2e-uc2-5.sh", "deploy/smoke-test.sh", "frontend/src/api/download.ts", "frontend/src/components/QueryErrorAlert.tsx", "frontend/src/features/archive/ArchiveFormModal.tsx", "frontend/src/features/archive/ArchiveImportModal.tsx", "frontend/src/features/archive/ArchivePage.tsx", "frontend/src/features/archive/api.ts", "frontend/src/features/archive/routes.tsx", "frontend/src/features/dashboard/BmDashboard.tsx", "frontend/src/features/dashboard/GvDashboard.tsx", "frontend/src/features/dashboard/SvDashboard.tsx", "frontend/src/features/dashboard/api.ts", "frontend/src/features/defense/CommitteePage.tsx", "frontend/src/features/defense/MyDefensePage.tsx", "frontend/src/features/defense/ScoringPage.tsx", "frontend/src/features/defense/api.ts", "frontend/src/features/defense/routes.tsx", "frontend/src/features/documents/CheckDetailPage.tsx", "frontend/src/features/documents/CheckPanel.tsx", "frontend/src/features/documents/CheckStatusTag.tsx", "frontend/src/features/documents/DocumentUpload.tsx", "frontend/src/features/documents/RecheckButton.tsx", "frontend/src/features/documents/api.ts", "frontend/src/features/documents/routes.tsx", "frontend/src/features/notifications/NotificationBell.tsx", "frontend/src/features/notifications/api.ts", "frontend/src/features/outlines/FinalReportTab.tsx", "frontend/src/features/outlines/OutlinePage.tsx", "frontend/src/features/outlines/OutlineReviewPage.tsx", "frontend/src/features/outlines/VersionHistory.tsx", "frontend/src/features/outlines/api.ts", "frontend/src/features/outlines/routes.tsx", "frontend/src/features/progress/MilestoneList.tsx", "frontend/src/features/progress/ProgressOverviewPage.tsx", "frontend/src/features/progress/ProgressPage.tsx", "frontend/src/features/progress/ProgressReviewPage.tsx", "frontend/src/features/progress/api.ts", "frontend/src/features/progress/constants.ts", "frontend/src/features/progress/routes.tsx", "frontend/src/layouts/AppLayout.tsx", "frontend/src/utils/format.ts"]
covered_digest: "v2:sha256:272c65595778e5a0318f3b345db4eaed536dcd27106ccd0af3299d8ef4a6ef59"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Walk README 'Kịch bản demo UC2–UC5' in a real browser as SV / GVHD / GV hội đồng / Bộ môn: MH-08 nộp đề cương + lịch sử phiên bản, MH-09 duyệt với khung kiểm tra trùng lặp (polling), MH-14 chi tiết kết quả, MH-10 tiến độ, MH-11 hội đồng & lịch, MH-12 chấm điểm, MH-13 kho, dashboards MH-02/03/04"
    expected: "Each screen renders the data the API returns (verified by e2e), states update without reload (check 'Đang kiểm tra' → 'Hoàn tất'), role menus show only the role's screens, Vietnamese text renders correctly"
    why_human: "Visual fidelity and UX; the executor's CDP runs were self-performed and are marked 'user confirmation pending' in 03-01..03-07 SUMMARY"
  - test: "Notification bell: as Bộ môn approve/reject a topic and have GVHD request outline changes; watch the bell as SV and GVHD in two browsers for up to 30 s; open an item; click 'Đánh dấu tất cả đã đọc'"
    expected: "Unread badge increments within one 30 s poll, the dropdown lists the new item with its link, mark-read and read-all zero the badge"
    why_human: "Real-time polling behaviour in a browser; the API side is verified by e2e + test_notifications, the UI timing is not"
  - test: "Concurrency review of WR-02..WR-05 locking (score vs committee edit, final-report resubmit vs add_schedule, milestone/committee delete vs child insert, stale background check runs)"
    expected: "Lock order committee → schedule is consistent; no deadlock or 500 under concurrent requests; finalize counts only current members' scores"
    why_human: "03-REVIEW-FIX.md flags these as 'needs human verification' — no test reproduces real concurrency; only sequential paths are exercised"
---

# Phase 3: Outline, Progress, Defense & Archive — Verification Report

**Phase Goal:** Sau khi đề tài được phân công, SV, GVHD và Bộ môn đi trọn quy trình đề cương → tiến độ → bảo vệ → lưu kho trên Web, có thông báo in-app ở mỗi bước chuyển trạng thái
**Verified:** 2026-09-28
**Status:** human_needed
**Re-verification:** No — initial verification
**Mode:** mvp (see note on goal format below)

## MVP-mode note

ROADMAP marks this phase `Mode: mvp`, but the goal is not in user-story form ("As a …, I want to …, so that …"). Strictly, MVP-mode verification should stop and ask for `/gsd mvp-phase 3` to rewrite the goal. The orchestrator asked for this verification explicitly, so it went ahead. The goal's outcome clause ("đi trọn quy trình … có thông báo in-app ở mỗi bước") was used as the success condition, with the User Flow Coverage table below. Advisory only; it does not block.

## User Flow Coverage

Evidence is from the verifier's own run of `deploy/e2e-uc2-5.sh`: 67 OK lines, exit 0, through Apache HTTPS against the running `ntma` stack. The script cleaned up after itself; afterwards the DB held 0 K98 đợt, 0 test topics and 0 K98 kho rows.

| # | Step | Expected | Evidence | Status |
|---|------|----------|----------|--------|
| 1 | SV with assigned topic submits outline DOCX | 202, version 1, check reaches HOAN_TAT | "nộp đề cương v1 -> 202", "Kiểm tra trùng lặp tài liệu v1 hoàn tất" | ✓ |
| 2 | GVHD opens review, sees extracted text + check panel, requests changes | YEU_CAU_SUA + SV notification | "GV029 thấy tóm tắt … + kiểm tra Hoàn tất", "yêu cầu sửa … -> Yêu cầu sửa", "có thông báo Yêu cầu sửa" | ✓ |
| 3 | SV resubmits PDF (v2), GVHD approves | DA_DUYET + notification | "nộp đề cương v2 (PDF) -> 202", "duyệt đề cương v2 -> Đã duyệt", "thông báo Đề cương được duyệt" | ✓ |
| 4 | Bộ môn sets milestones; SV reports; GVHD reviews; dashboard flags late SV | TRE_MOC flag on Bộ môn dashboard | "Mốc 1 Trễ mốc, Mốc 2 Đúng hạn có tệp", "GV029 nhận xét Mốc 2: Đạt", "Bộ môn thấy … Trễ mốc" | ✓ |
| 5 | SV submits final report (check runs); Bộ môn creates committee + schedule | GVHD-on-committee blocked; SV/members notified | "báo cáo cuối -> 202 … HOAN_TAT", "hội đồng B (chứa GVHD) bị từ chối 409", "HOI_DONG_PHAN_CONG", "LICH_BAO_VE" | ✓ |
| 6 | Members score; outsider blocked; Bộ môn finalizes | mean 8.0/8.5/9.0 = 8.5; finalize blocked at 2/3 | "GV025 … 403", "chốt khi mới 2/3 … 409", "chốt kết quả -> 200, điểm TB 8.5, lưu kho" | ✓ |
| 7 | SV sees schedule + result | score 8.5 + KET_QUA_BAO_VE notification | "DTC225200098 thấy điểm 8.5 + thông báo KET_QUA_BAO_VE" | ✓ |
| 8 | Thesis appears in archive; search/filter/detail/download; Bộ môn CRUD + CSV import + reindex | HE_THONG record DA_INDEX; import partial success; 403 for non-Bộ môn | "nguồn HE_THONG, đã index (DA_INDEX)", "import CSV 3 dòng -> 2 thành công", "GV025 tìm 'biển số'", "xóa … -> 204 … 404" | ✓ |
| 9 | Notifications: unread count, list, mark read, privacy | 6 unread incl. DE_TAI_PHAN_CONG; cross-user mark → 404; read-all → 0 | e2e lines under NOTF-01 | ✓ |

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SV nộp đề cương DOCX/PDF (sai định dạng / quá dung lượng bị từ chối), nộp lại tạo phiên bản mới; GVHD thấy đề cương + khung kiểm tra trùng lặp, duyệt/yêu cầu sửa kèm nhận xét, vòng lặp đến khi duyệt | ✓ VERIFIED | `documents.read_and_validate` checks extension + magic bytes (`%PDF-`, ZIP with `word/document.xml`) and 20 MB `MAX_UPLOAD_BYTES`. `store()` sets `so_phien_ban = max+1` and never overwrites. `outlines.submit/_review_da_duyet/_review_yeu_cau_sua` use a conditional-UPDATE FSM (CHUA_NOP/YEU_CAU_SUA → CHO_DUYET → DA_DUYET or YEU_CAU_SUA; a comment is required for YEU_CAU_SUA). `OutlineReviewPage` renders `CheckPanel`. Tests `test_upload_rejected_before_any_version` (covers .txt, bad ZIP, GIF-as-PDF, PDF-as-DOCX, 20 MB+1) and `test_outline_state_machine_one_way` pass. The e2e run covers v1 DOCX → yêu cầu sửa → v2 PDF → duyệt. |
| 2 | SV nộp báo cáo tiến độ theo mốc (nội dung + file tùy chọn); GVHD nhận xét/đánh giá; Bộ môn dashboard toàn khoa đánh dấu SV trễ mốc | ✓ VERIFIED | `/api/progress/*` routes: milestones CRUD (BO_MON), `reports/{moc_id}` (SV), `reports/{id}/review` (GV, GVHD-only; others get 403), `dashboard` (BO_MON). `ProgressOverviewPage` shows red TRE_MOC tags, the `so_sv_tre_moc` statistic and a `chi_tre_moc` filter. `test_milestones_and_late_flags` and `test_report_resubmit_and_review_scope` pass. e2e steps under Evidence 4. |
| 3 | SV nộp báo cáo cuối (kích hoạt kiểm tra); Bộ môn lập hội đồng, xếp lịch; GV chỉ thấy SV hội đồng mình, nhập điểm + nhận xét; điểm = TB cộng; Bộ môn chốt; SV xem lịch + kết quả | ✓ VERIFIED | Routes `defense.py`: final-reports (SV), committees/schedules (BO_MON), `my-committees`/`score` (GV), `finalize` (BO_MON), `me` (SV). Committee rule blocks GVHD (409). Non-member gets 403 on the schedule and on the download. Finalize requires all members to have scored; mean 8.0/8.5/9.0 → 8.5. `MyDefensePage` shows room, date, time and `diem_trung_binh`. Three tests in `test_defense_flow.py` pass. e2e steps 5–7. |
| 4 | Đồ án đã chốt tự vào kho đủ metadata; tìm/lọc theo khóa, từ khóa, GVHD + chi tiết; Bộ môn thêm/sửa/xóa + import khóa cũ; mỗi bản ghi mới gọi index sang AI client | ✓ VERIFIED | Finalize inserts `do_an_kho` (nguon=HE_THONG) and ingests. The e2e run saw id 359 reach DA_INDEX. Router `archive.py` schedules `run_ingest` as a BackgroundTask on create, update, import (new ids) and reindex. `ArchivePage` has khóa, GVHD and keyword (`q`) filters, plus `ArchiveFormModal` and `ArchiveImportModal` for BO_MON. `test_archive_writes_are_bomon_only` and `test_csv_import_partial_success_search_and_reindex` pass. |
| 5 | Thông báo in-app (số chưa đọc + danh sách) khi đề tài/đề cương duyệt/từ chối, nhận xét mới, phân vào hội đồng / có lịch bảo vệ | ✓ VERIFIED | Notification types DE_TAI_DUYET/PHAN_CONG/TU_CHOI, DE_CUONG_DUYET/YEU_CAU_SUA/MOI, TIEN_DO_NHAN_XET, HOI_DONG_PHAN_CONG, LICH_BAO_VE, KET_QUA_BAO_VE. Each is created in the same transaction as its state change; for example, `topic_approval.reject` creates DE_TAI_TU_CHOI before `commit`. The `/api/notifications` list, unread-count, read and read-all routes are private to the caller (cross-user read returns 404). `NotificationBell` (Badge + Popover, `refetchInterval: 30_000`) is mounted in `AppLayout`. `test_notifications_are_private_and_follow_state_changes` passes. |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/{outlines,documents,progress,defense,archive,notifications,dashboard}.py` | UC2–UC5 + NOTF logic | ✓ VERIFIED | 114–1244 lines each. Substantive and exercised by e2e. |
| `backend/app/routers/{outlines,documents,progress,defense,archive,notifications}.py` | REST API with `require_role` | ✓ VERIFIED | Auto-registered via `discover_routers()`. Every route declares `require_role`. |
| Alembic 0006–0009 (+0011) | Phase 3 tables | ✓ VERIFIED | `tools/check-erd-db.py`: "OK: schema thesis_core khớp erd.puml". |
| Frontend `features/{outlines,documents,progress,defense,archive,notifications,dashboard}` | MH-02..04, MH-08..14, bell | ✓ VERIFIED | Routes are role-scoped. `tsc -b --noEmit` exits 0. The deployed Apache bundle `index-B2rRhPy6.js` contains the Phase 3 strings. |
| `deploy/e2e-uc2-5.sh` | End-to-end proof through Apache | ✓ VERIFIED | 785 lines. Exit 0 with 67 OK assertions, and the trap cleanup worked. |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| Outline/final-report submit | `document_check.run` | BackgroundTasks → `ket_qua_kiem_tra_trung_lap` DANG_KIEM_TRA→HOAN_TAT | WIRED (e2e HOAN_TAT ×3) |
| `OutlineReviewPage` / `FinalReportTab` | check API | `CheckPanel` + 3 s `refetchInterval` while DANG_KIEM_TRA | WIRED |
| `defense.finalize` | `do_an_kho` + AI ingest | insert HE_THONG row → ingest | WIRED (e2e DA_INDEX) |
| Archive create/update/import/reindex | `ai_client.ingest` | `background_tasks.add_task(archive.run_ingest, ids)` | WIRED |
| State changes | `thong_bao` | `notifications.create` in the same txn | WIRED |
| `AppLayout` | `NotificationBell` | unread-count polling every 30 s | WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| Bộ môn progress dashboard | late flags | computed from `moc_tien_do` × `bao_cao_tien_do` (not stored) | yes (e2e 1\|1\|2) | ✓ FLOWING |
| MyDefensePage | schedule + mean score | `/api/defense/me` → `lich_bao_ve`/`diem_bao_ve` | yes (8.5) | ✓ FLOWING |
| ArchivePage | list | `/api/archive` MySQL query with khoa/q/giang_vien_id | yes | ✓ FLOWING |
| NotificationBell | unread count/list | `/api/notifications/unread-count` | yes (6 → 0) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend suite, one full run | `uv --directory backend run pytest -q` | 51 passed in 82.7 s | ✓ PASS |
| End-to-end UC2–UC5 through Apache HTTPS | `bash deploy/e2e-uc2-5.sh` | exit 0, 67 OK, cleanup confirmed | ✓ PASS |
| ERD ↔ DB | `python tools/check-erd-db.py` | OK | ✓ PASS |
| Frontend typecheck | `npx tsc -b --noEmit` | exit 0 | ✓ PASS |

### Probe Execution

No probes declared (no `scripts/*/tests/probe-*.sh`). Skipped.

### Requirements Coverage

| Requirement | Plan | Status | Evidence |
|-------------|------|--------|----------|
| OUTL-01 | 03-01/02 | ✓ SATISFIED | SC1: validation + versioning |
| OUTL-02 | 03-01/02 | ✓ SATISFIED | Review screen shows extracted text + CheckPanel |
| OUTL-03 | 03-01/02 | ✓ SATISFIED | Revision loop exercised by e2e |
| PROG-01 | 03-06 | ✓ SATISFIED | Report per milestone, optional file |
| PROG-02 | 03-06 | ✓ SATISFIED | GVHD review with Đạt rating; non-GVHD gets 403 |
| PROG-03 | 03-06 | ✓ SATISFIED | Bộ môn dashboard with late flags |
| DEFN-01 | 03-03 | ✓ SATISFIED | Final-report submit triggers the check |
| DEFN-02 | 03-03 | ✓ SATISFIED | Committee + schedule; GVHD blocked |
| DEFN-03 | 03-04 | ✓ SATISFIED | Committee-scoped view/score |
| DEFN-04 | 03-04 | ✓ SATISFIED | Mean, finalize, SV result |
| REPO-01 | 03-04/05 | ✓ SATISFIED | Auto-archive with metadata |
| REPO-02 | 03-05 | ✓ SATISFIED | Search/filter/detail/download |
| REPO-03 | 03-05 | ✓ SATISFIED | CRUD + CSV import + ingest |
| NOTF-01 | 03-07 (+all) | ✓ SATISFIED | Bell + all trigger types |

No orphaned requirements. All 14 IDs mapped to Phase 3 are claimed and satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (92 Phase 3 files scanned) | — | TBD/FIXME/XXX | none found | — |
| `frontend/src/features/*` | various | `placeholder=` | ℹ️ Info | Ant Design input hints, not stubs |
| `backend/app/services/defense.py` | 5 sites | Ruff E741 (`l` variable) | ℹ️ Info | Style only (deferred-items.md) |
| `ntma_uploads-data` volume | — | orphan files from earlier aborted runs | ℹ️ Info | Served only via the authorised API (deferred-items.md) |
| `03-REVIEW-FIX.md` | IN-04 | circular import progress↔dashboard skipped | ℹ️ Info | Refactor only; works at runtime |

### Notes on scope and concurrency

- The running stack now uses `AI_CLIENT=http` (Phase 4, 04-05). `AiClientStub` is still in `ai_client.py`, and pytest forces `AI_CLIENT=stub`. SC1/SC3's "stub data" therefore holds in tests, and the e2e run checks the same seam against the real service. This is not a gap.
- `backend/app/services/document_check.py` has an uncommitted in-flight diff from plan 04-06. It was ignored and is excluded from `covered_files` along with `ai_client.py`, because both files are now owned by Phase 4.

### Human Verification Required

#### 1. Full visual walk-through of UC2–UC5 screens
**Test:** Follow the README "Kịch bản demo UC2–UC5" in a real browser for each role (MH-02..04, MH-08..14).
**Expected:** Screens render the API data. The check panel moves from "Đang kiểm tra" to "Hoàn tất" without a reload. Role menus are correct. Vietnamese text renders correctly.
**Why human:** Visual/UX fidelity. The executor's CDP checks were self-performed and are pending user confirmation.

#### 2. Notification bell in real time
**Test:** Trigger topic approve/reject and an outline change request; watch the bell as SV and GVHD in two browsers; mark one item read, then use read-all.
**Expected:** The badge updates within 30 s, the list links to the right screen, and the count drops to 0.
**Why human:** Browser polling timing.

#### 3. Concurrency locking (WR-02..WR-05)
**Test:** Review or stress the concurrent paths: scoring vs committee edit, final-report resubmit vs scheduling, deletes vs child inserts, stale check runs.
**Expected:** No deadlock or 500. Finalize counts only current members.
**Why human:** 03-REVIEW-FIX marks these "needs human verification"; no test reproduces real concurrency.

### Gaps Summary

No gaps. All 5 roadmap success criteria and all 14 requirements are backed by code that exists, is wired, and was exercised in this verification by 51 passing pytest tests and a clean end-to-end run through Apache HTTPS. The status is `human_needed` only because visual/UX confirmation and the concurrency-locking review cannot be proven programmatically.

---

_Verified: 2026-09-28_
_Verifier: Developer (verifier)_
