---
phase: 03-outline-progress-defense-archive
plan: 07
subsystem: notifications-dashboards
status: complete
tags: [fastapi, sqlalchemy, mysql, react, antd, tanstack-query, notifications, dashboard]

requires:
  - phase: 03-outline-progress-defense-archive (plans 01-06)
    provides: "ThongBao + notifications.create, outlines/defense/progress/archive services, progress.compute_cohort_progress, defense.my_defense, document_check.summary, e2e-uc2-5.sh sections"
  - phase: 02-platform-rbac-topic-management
    provides: "topic_approval.approve/reject (conditional UPDATE), dashboard endpoints per role, AppLayout header, smoke-test.sh, e2e-uc1.sh"
provides:
  - "GET /api/notifications/unread-count, POST /api/notifications/{id}/read, POST /api/notifications/read-all (owner rows only)"
  - "topic_approval.approve/reject emit DE_TAI_DUYET / DE_TAI_PHAN_CONG / DE_TAI_TU_CHOI in the same commit as the state change"
  - "NotificationBell in the AppLayout header (30 s polling, dropdown, mark read, mark all read)"
  - "Phase-3 widgets on /api/dashboard/{sinh-vien,giang-vien,bo-mon} and MH-02/03/04 screens"
  - "progress.row_out (shared SV×milestone row serializer)"
  - "Final smoke-test.sh (Phase-3 cross-role 403), e2e-uc2-5.sh uc0_notifications + uc0_dashboards, README demo UC2–UC5"
affects: [04, 05]

estimate:
  tokens: 110000
actuals:
  tokens: 21600
  tasks: 2
  commits: 3
  plan_head_before: 3f18f6439084ec144cc520186cc2477ad511ce2a
  plan_head_after: 1e6caad071b48bd841cec9448642ef397c79481d

tech-stack:
  added: []
  patterns:
    - "Notification + state change in one commit: first the conditional UPDATE, then on rowcount 0 → rollback, re-read and return 404/409 without creating anything, otherwise notifications.create(...) followed by the single commit"
    - "Owner-scoped mark-read: UPDATE … WHERE id AND tai_khoan_id = me. The MySQL dialect's CLIENT_FOUND_ROWS makes rowcount count matched rows, so rowcount 0 → 404 without revealing whether the id exists"
    - "Client follows server-generated links only when they are single-leading-slash app paths (isAppPath rejects '//' and '/\\')"
    - "Module imports (not from-imports) between services/dashboard.py and services/progress.py break their import cycle"

key-files:
  created:
    - backend/tests/test_notifications.py
    - frontend/src/features/notifications/api.ts
    - frontend/src/features/notifications/NotificationBell.tsx
    - .planning/phases/03-outline-progress-defense-archive/deferred-items.md
  modified:
    - backend/app/services/notifications.py
    - backend/app/schemas/notifications.py
    - backend/app/routers/notifications.py
    - backend/app/services/topic_approval.py
    - backend/app/schemas/dashboard.py
    - backend/app/services/dashboard.py
    - backend/app/services/progress.py
    - frontend/src/layouts/AppLayout.tsx
    - frontend/src/features/dashboard/api.ts
    - frontend/src/features/dashboard/SvDashboard.tsx
    - frontend/src/features/dashboard/GvDashboard.tsx
    - frontend/src/features/dashboard/BmDashboard.tsx
    - deploy/e2e-uc1.sh
    - deploy/e2e-uc2-5.sh
    - deploy/smoke-test.sh
    - deploy/README.md

key-decisions:
  - "A refused topic decision (409/404) rolls back before any notification is created. The accept/refuse decision still comes only from the UPDATE's WHERE clause; the extra db.get in reject only reads the proposer's name and the topic title."
  - "Reject notifies the proposer: the SV when loai_nguoi_de_xuat is SINH_VIEN, otherwise the GV. Approve without an SV notifies the proposing GV (DE_TAI_DUYET). Approve with an SV notifies both the SV and the assigned GVHD (DE_TAI_PHAN_CONG)."
  - "POST /read for someone else's id and for an id that does not exist both return 404 'Không tìm thấy thông báo'. Re-reading one's own already-read row returns 204."
  - "The bell polls only /unread-count every 30 s (refetchIntervalInBackground false). The list of 10 notifications loads only while the dropdown is open."
  - "GV 'Việc cần xử lý': outline reviews, then progress comments, then scoring, capped at 10 in total, one query per type. CHAM_DIEM lists every not-chốt schedule row in the caller's committees that the caller has not scored, including future dates (the ghi_chu shows the committee date)."
  - "The Bộ môn dashboard's upcoming committees are global (hoi_dong has no đợt): a count plus the first 5 with ngay_bao_ve ≥ today_vn(). SV trễ mốc and the 5-row excerpt use the selected đợt through compute_cohort_progress."
  - "SV dashboard 'moc_tiep_theo' is the first milestone still CHUA_DEN_HAN. When every milestone is submitted or overdue it is null and the line is hidden."

requirements-completed: [NOTF-01, PROG-03, DEFN-04, OUTL-02]

coverage:
  - id: D1
    description: "Per NOTF-01/D-08: topic approve/assign/reject create notifications for the SV, the assigned GVHD or the proposer in the same transaction; a refused (409) decision creates none"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_notifications.py::test_notifications_are_private_and_follow_state_changes — SV + GV DE_TAI_PHAN_CONG after 200; second approve 409 with the total count unchanged; GV-proposed approve → DE_TAI_DUYET; reject → DE_TAI_TU_CHOI containing the reason; reject of an approved topic 409 creates nothing — pass"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc0_notifications — DTC225200098 has exactly one DE_TAI_PHAN_CONG linking /de-tai/{id} — pass"
        status: pass
    human_judgment: false
  - id: D2
    description: "Per D-08/T-03-37: users list, count and mark only their own notifications; a foreign id gives 404 and changes nothing"
    requirement: "NOTF-01"
    verification:
      - kind: unit
        ref: "test_notifications — B's list empty, B POST A's id/read 404 and A's row stays unread; A unread-count equals A's rows; /read 204 → count −1; /read-all 204 → 0; SV rows untouched by GV read-all — pass"
        status: pass
      - kind: e2e
        ref: "uc0_notifications — DTC225200097 → 404 on DTC225200098's id with the count unchanged; read-all 204 → 0 — pass"
        status: pass
    human_judgment: false
  - id: D3
    description: "Per D-08/UC0.5: header bell with the unread badge polled every 30 s, dropdown in the MH-02 style, click → mark read + navigate, 'Đánh dấu tất cả đã đọc' clears it"
    requirement: "NOTF-01"
    verification:
      - kind: manual_procedural
        ref: "CDP p0307-01..06: after bomon approved via the API, the badge appeared without reload after 26.3 s (SV) and 29.3 s (GV029); the dropdown showed 'Thông báo (1 chưa đọc)' with a blue dot and bold unread item; clicking it went to /de-tai/83 and the badge went 1 → 0; mark-all → 0"
        status: pass
    human_judgment: true
    rationale: "Self-performed with headless Chrome per the autonomous-run instruction; user confirmation pending."
  - id: D4
    description: "Per OUTL-02/PROG-03/DEFN-04 (MH-02/03/04): SV, GV and Bộ môn dashboards show outline, progress and defense widgets, each endpoint restricted to its own role"
    requirement: "PROG-03"
    verification:
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc0_dashboards — SV098 de_cuong DA_DUYET, 2 milestones, chu_tich set, diem 8.5; GV029 new counters present; bomon K98 sv_tre_moc|tong|so_moc = 1|1|2; SV → bo-mon 403 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0307-07..12 (see Human-check below)"
        status: pass
    human_judgment: true
    rationale: "Mockup fidelity self-judged from screenshots; user confirmation pending."
  - id: D5
    description: "Per D-09: phase gate — pytest, smoke (cross-role 403 on every Phase-3 route group), e2e-uc1, e2e-uc2-5, ERD/class checks, dom-check, no K98/K99 cohorts left; README demo UC2–UC5"
    requirement: "NOTF-01"
    verification:
      - kind: e2e
        ref: "Gate run 2026-09-28: 50 passed; SMOKE TEST pass; e2e UC1 OK; e2e UC2-5 OK; check-erd-db OK; check-docs class-erd OK; dom-check /tong-quan OK; COUNT(K98,K99)=0"
        status: pass
    human_judgment: false

duration: 26min
completed: 2026-09-28
---

# Phase 3 Plan 07: In-app Notifications + Phase-3 Dashboards Summary

**The header bell now shows a live unread count. It polls every 30 s, and the dropdown marks notifications read, navigates to their links, and has a "mark all read" action. Phase 2's topic approve/assign/reject now notify the SV, the GVHD or the proposer in the same commit, and a refused decision notifies no one. The SV, GV and Bộ môn dashboards now summarise outline, progress and defense (MH-02/03/04). The phase closes with a green gate through Apache and a README demo for UC2–UC5.**

## Performance

- **Duration:** about 26 minutes (2026-09-28 06:21Z–06:47Z)
- **Tasks:** 2 of 2
- **Files:** 4 created (including deferred-items.md), 16 modified

## Notification event matrix (all of Phase 3)

| Event | Recipient | loai | lien_ket |
|---|---|---|---|
| Bộ môn approves a GV topic with no SV (UC1.3) | proposing GV | DE_TAI_DUYET | /de-tai/{id} |
| Bộ môn approves and assigns a topic that has an SV (UC1.3) | SV and assigned GVHD | DE_TAI_PHAN_CONG | /de-tai/{id} |
| Bộ môn rejects a topic (UC1.3 A1) | proposer (SV if SV-proposed, else GV) | DE_TAI_TU_CHOI | /de-tai/{id} |
| SV submits an outline version (UC2.1) | GVHD | DE_CUONG_MOI | /duyet-de-cuong?de_tai_id={id} |
| GVHD approves an outline (UC2.2) | SV | DE_CUONG_DUYET | /de-cuong |
| GVHD requests changes (UC2.2) | SV | DE_CUONG_YEU_CAU_SUA | /de-cuong |
| GVHD comments on a progress report (UC3.3) | SV | TIEN_DO_NHAN_XET | /tien-do |
| Committee created, or a member added (UC4.2) | new members | HOI_DONG_PHAN_CONG | /cham-diem |
| Committee date/time/room changed (UC4.2) | members | LICH_BAO_VE | /cham-diem |
| Committee date/time/room changed (UC4.2) | scheduled SVs | LICH_BAO_VE | /bao-ve |
| SV scheduled (UC4.2) | SV | LICH_BAO_VE | /bao-ve |
| SV removed from a schedule (UC4.2) | SV | LICH_BAO_VE | /bao-ve |
| Bộ môn finalises (chốt) a result (UC4.4) | SV | KET_QUA_BAO_VE | /bao-ve |

## Dashboard payload additions

- **`SvDashboardOut`** adds:
  - `de_cuong` {trang_thai, phien_ban, thoi_diem_nop, kiem_tra: CheckSummary} | null. It is null until the topic reaches DA_PHAN_CONG, and has trang_thai CHUA_NOP when no row exists yet.
  - `tien_do` [{ten_moc, han_nop, trang_thai}]
  - `moc_tiep_theo` {ten_moc, han_nop, con_ngay} | null
  - `bao_ve` {ten_hoi_dong, phong, ngay_bao_ve, gio_du_kien, chu_tich, diem_trung_binh (only after chốt)} | null
- **`GvDashboardOut`** adds:
  - `so_de_cuong_cho_duyet`, `so_bao_cao_cho_nhan_xet`, `so_hoi_dong_tham_gia`
  - `viec_can_xu_ly` [{loai: DUYET_DE_CUONG|NHAN_XET_TIEN_DO|CHAM_DIEM, sinh_vien, ten_de_tai, ghi_chu, lien_ket}] (≤ 10)
- **`BmDashboardOut`** adds:
  - `sv_tre_moc`
  - `tien_do_trich` {moc: MilestoneOut[], items: ProgressRowOut[] (≤ 5), tong} | null
  - `moc_tien_do` MilestoneOut[]
  - `so_hoi_dong_sap_toi`
  - `hoi_dong_sap_toi` [{id, ten_hoi_dong, ngay_bao_ve, gio_bao_ve, phong, so_sinh_vien}] (≤ 5)
- **Frontend:**
  - SV: Row/Col cards "Đề tài của tôi", "Thông báo (n chưa đọc)", "Đề cương", "Tiến độ" (antd Steps + "Mốc tiếp theo: … - còn n ngày"), "Lịch và kết quả bảo vệ".
  - GV: 5 Statistic cards plus the "Việc cần xử lý" table, whose buttons are Duyệt / Xem / Chấm điểm.
  - Bộ môn: "SV trễ mốc" (red when > 0, links to /tien-do-toan-khoa?dot_do_an_id=…&chi_tre_moc=1) and "Hội đồng sắp tới" (links to /hoi-dong), "Tiến độ Sinh viên (trích n/tong)" with "Xem tất cả", and "Mốc tiến độ của đợt" with "Thiết lập mốc".

## Task Commits

1. **Task 1 RED:** `3c7afb0` test(03-07): RED — topic decision notifications + notification privacy/read API
2. **Task 1 GREEN:** `2e26186` feat(03-07): notification read API, topic-decision notifications and header bell
3. **Task 2:** `1e6caad` feat(03-07): MH-02/03/04 Phase-3 dashboard widgets, final smoke checks and UC2–UC5 demo script

## TDD Gate Compliance

- **RED** (`3c7afb0`): the test failed at the first notification assertion, because no notification row existed after the approve returned 200.
- **GREEN** (`2e26186`): 14 passed in test_notifications + test_topic_approval_rbac + test_auth.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The test read stale data under REPEATABLE READ**
- **Found during:** Task 1 GREEN.
- **Issue:** The test session's snapshot was taken at `db.refresh(topic)`, so `expire_all()` still showed 0 notifications that the API had already committed.
- **Fix:** The test helper calls `db.rollback()` before re-reading. No app change.
- **Files:** backend/tests/test_notifications.py
- **Commit:** 2e26186

**2. [Rule 2 - Missing cleanup] e2e-uc1.sh left notifications behind**
- **Found during:** Task 1 verify.
- **Issue:** Now that approvals notify, each run of e2e-uc1.sh left DE_TAI_* rows for GV030, DTC225200099 and DTC225200100.
- **Fix:** The cleanup trap deletes those accounts' notifications created since the script started, using the same pattern as e2e-uc2-5.
- **Files:** deploy/e2e-uc1.sh (not listed in files_modified)
- **Commit:** 2e26186

**3. [Rule 3 - Blocking] Circular import between dashboard.py and progress.py**
- **Found during:** Task 2.
- **Issue:** `progress.py` already did `from app.services.dashboard import _default_cohort`, so importing progress from dashboard crashed the api at startup.
- **Fix:** Both modules now use module imports (`progress.compute_cohort_progress`, `dashboard_service._default_cohort`).
- **Files:** backend/app/services/progress.py, backend/app/services/dashboard.py
- **Commit:** 1e6caad

**4. [Refactor, not in files_modified] progress.row_out**
- The SV×milestone row serializer was extracted from `progress.dashboard` so that `/tien-do-toan-khoa` and the Bộ môn dashboard share it. There is no behaviour change; e2e uc3_progress is still green.
- **Commit:** 1e6caad

### Additive fields beyond the plan text

- `BmDashboardOut.so_hoi_dong_sap_toi`: the Statistic needs the full count, while the list is capped at 5.
- `SvOutlineOut` is also returned with trang_thai CHUA_NOP (no versions) once the topic is assigned but no outline has been submitted.

## Human-check (self-performed, pending user confirmation)

- **Script:** `scratchpad/cdp0307.py`, headless Chrome at 1440 px.
- **Throwaway data:**
  - Cohort: K94 "Đợt CDP 03-07".
  - Students: DTC225200098 (GVHD GV029) and DTC225200097 (GVHD GV025), both with approved outlines and final reports, and DTC225200096 (GVHD GV029) with an outline waiting for review.
  - Milestones: Mốc 1 = yesterday, Mốc 2 = +7 d (SV098 submitted, not yet reviewed), Mốc cuối = +14 d.
  - Committees: "Hội đồng CDP 3" today (GV026 as CT, GV027, GV028; SV098) and "Hội đồng CDP 4" in 3 days (GV029 as CT; SV097).
- **Task 1, bell:**
  - Neither user had a badge before the approval.
  - After bomon's approve, the badge appeared without a reload after 26.3 s for the SV and 29.3 s for GV029, which is within the 30 s poll.
  - SV dropdown: "Thông báo (1 chưa đọc)" plus "Đánh dấu tất cả đã đọc". The unread item is bold, has a blue dot and a relative time ("1 phút trước"). Older read items are shown normally.
  - GV dropdown: "Bạn được phân công hướng dẫn Dương Bảo Thảo — đề tài '…'".
  - Clicking the item went to `/de-tai/83` and the badge went 1 → 0. Mark-all left 0.
  - Screenshots p0307-01..06.
- **Task 2, dashboards:**
  - SV before chốt: "Phiên bản mới nhất: v1 · nộp 28/09/2026", "Đã duyệt", "Tỷ lệ trùng lặp gần nhất 0%" (stub). Steps: Mốc 1 Trễ mốc (red ✕), Mốc 2 Đúng hạn (✓), Mốc cuối "Hạn 12/10/2026". Also "Mốc tiếp theo: Mốc cuối - còn 14 ngày", "Hội đồng CDP 3 · Phòng 302", "28/09/2026 · 08:00", "Chủ tịch: TS. …" and "Chưa có kết quả".
  - SV after scoring (8.0/8.5/9.0) and chốt: "Điểm bảo vệ 8.50", and the "Kết quả bảo vệ … 8.50" notification is at the top.
  - GV029: cards Đề cương chờ duyệt 1, Báo cáo tiến độ chờ nhận xét 1, Hội đồng tham gia 1. "Việc cần xử lý" has 3 rows: Duyệt đề cương "Kiểm tra trùng lặp: Hoàn tất (100%)" (stub), Nhận xét tiến độ "Mốc 2 - nộp 28/09/2026", and Chấm điểm bảo vệ "Hội đồng CDP 4 - 01/10/2026". The "Chấm điểm" button goes to `/cham-diem?hoi_dong_id=38&lich_id=22`.
  - Bộ môn: defaults to the newest open đợt (K94). SV trễ mốc 3 (red), Hội đồng sắp tới 2, "Tiến độ Sinh viên (trích 3/3)" with milestone columns and colored tags, and "Mốc tiến độ của đợt" with 3 rows and "Thiết lập mốc". Clicking "SV trễ mốc" goes to `/tien-do-toan-khoa?dot_do_an_id=51&chi_tre_moc=1`.
  - Screenshots p0307-07..12, in the scratchpad and not committed.
- **Cleanup:** 0 K94 cohorts, 0 CDP topics, 0 CDP committees, 0 notifications since the start. No new upload files remained, and Chrome was stopped.
- **Fidelity gaps to confirm:**
  - The GV dashboard has 5 Statistic cards (two from Phase 2 plus three new), so they wrap onto two rows at 1440 px. MH-03 shows 4 on one row.
  - The SV "Thông báo" card lists the 3 newest notifications, read or unread. The mockup only shows this list inside the bell dropdown.
  - MH-02's second line per notification ("· ThS. …" or "· Hội đồng 3 - Phòng 302") is not shown: the notification row has no sender or context field, so only the relative time is displayed.

### Phase 3 UAT items to persist

1. The bell badge appears within 30 s without reload for every NOTF-01 event. The dropdown style matches MH-02, and click navigation and mark-all work.
2. Full README "Kịch bản demo UC2–UC5" walkthrough, covering ROADMAP Phase 3 SC1–SC5, with regular demo accounts (not the e2e reserved ones).
3. The MH-02/03/04 dashboards compared with the mockups using live data (see the fidelity gaps above).
4. Carried from plans 03-01..03-06: MH-08/09/14 outline loop, MH-10 progress, MH-11/12 committees and scoring, and MH-13 archive screens. These were self-checked with CDP and are pending user confirmation.

## Verification (gate run, 2026-09-28)

- `docker compose -f deploy/docker-compose.yml up -d --build --wait`: healthy.
- `uv --directory backend run pytest -q`: **50 passed**. This includes test_notifications and the route role-coverage test for the 3 new notification routes.
- `npm --prefix frontend ci` + `npm run build` (tsc -b + vite): OK.
- `bash deploy/smoke-test.sh`: all passed, with 4 new OK groups (SV 403 ×6, GV 403 ×3, bomon 403 ×2, notifications/unread-count/archive 200 ×3 roles).
- `bash deploy/e2e-uc1.sh`: OK. `bash deploy/e2e-uc2-5.sh`: OK, including uc0_notifications and uc0_dashboards.
- `python3 tools/check-erd-db.py` OK and `python3 tools/check-docs.py class-erd` OK. No schema change in this plan.
- `bash deploy/dom-check.sh /tong-quan 'Mã SV/GV hoặc email'`: OK. `COUNT(dot_do_an WHERE khoa IN ('K98','K99'))` = 0.
- `grep -rn dangerouslySetInnerHTML frontend/src | wc -l` = 0. Every acceptance-criteria grep passes, and `grep -c 'def test_' test_notifications.py` = 1.

## Known Stubs

None added. The duplicate-check and archive-index stub (`ai_client.py`) is still pending Phase 4, as the README states. Dashboard percentages such as 0% or 100% come from that stub.

## Threat Flags

None beyond the plan's register:
- **T-03-37:** owner-filtered UPDATE with 404, tested plus e2e.
- **T-03-38:** `isAppPath` guard.
- **T-03-39:** a single commit and rollback on refusal, tested.
- **T-03-40:** each dashboard route keeps one role, SV/GV queries are filtered by own id, the score is shown only after chốt, and smoke + e2e cover the 403s.
- **T-03-41:** polling hits only the COUNT endpoint and pauses in hidden tabs.
- **T-03-42:** e2e and CDP cleanups are scoped to their own đợt, captured committee ids, and notifications since the start.
- **T-03-SC:** no new packages.

## Issues Encountered

- The first CDP run waited for "Mốc tiếp theo" while every milestone was already submitted or overdue, so the line was correctly hidden. A third milestone (+14 d) was added to the throwaway data, and the cleanup of the failed run was complete.
- Pre-existing problems were logged to `deferred-items.md`: orphan upload files from earlier aborted runs, old read notifications on reserved e2e accounts, and ruff E741 in defense.py.

---
*Phase: 03-outline-progress-defense-archive*
*Completed: 2026-09-28*

## Self-Check: PASSED

All created key files present; commits 3c7afb0, 2e26186, 1e6caad present in git log.
