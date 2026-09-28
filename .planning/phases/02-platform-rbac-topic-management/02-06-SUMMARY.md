---
phase: 02-platform-rbac-topic-management
plan: 06
subsystem: topics
tags: [fastapi, sqlalchemy, mysql, react, antd, tanstack-query, rbac, dashboards]

requires:
  - phase: 02-platform-rbac-topic-management (plan 04)
    provides: "app/services/topics.py (get_topic/_person_refs/_to_out), schemas/topics.py (TopicOut, PersonRef, CohortRef, SavedTitleCheck), models/de_tai.py state constants, models/trung_lap.py"
  - phase: 02-platform-rbac-topic-management (plan 05)
    provides: "list_topics/register_topic/_can_register/_sv_has_active_topic extension points (this plan reuses, does not fork); GET /api/topics filters; frontend useCohorts/useLecturers/TRANG_THAI_DE_TAI"
provides:
  - "GET /api/topic-approvals + POST /{id}/approve|reject (BO_MON-only, router-level require_role) — conditional UPDATEs on trang_thai='CHO_DUYET', never auto-assigns GVHD (UC1.3 E1); services/topic_approval.py approve()/reject() are the hook points Phase 3 (NOTF-01) attaches in-app notifications to"
  - "/api/dashboard/sinh-vien|giang-vien|bo-mon — one endpoint per role, own-scoped aggregates via COUNT (no N+1); schemas/dashboard.py payload shapes are what Phase 3 extends with đề cương/tiến độ/hội đồng/thông báo widgets"
  - "frontend/src/features/topic-approval/{api,TopicApprovalPage,routes}.tsx — MH-07 pending table + Drawer (saved title-check block, GVHD Select, E1 hint) + reject Modal"
  - "frontend/src/features/dashboard/{Sv,Gv,Bm}Dashboard.tsx — MH-02/03/04 Phase-2-only widget subset, DashboardPage.tsx dispatches by role"
  - "deploy/e2e-uc1.sh — full UC1 flow (GV propose, SV self-propose, approve/assign/reject, register, cross-role 403, filtered list) through Apache HTTPS with self-cleanup (reserved accounts GV030/DTC225200099/DTC225200100, cohort khoa K99)"
  - "deploy/smoke-test.sh + deploy/README.md — final cross-role 403 smoke checks and full UC1 browser demo script closing Phase 2"
affects: [phase-03]

actuals:
  tokens: 17900
  tasks: 2
  commits: 3
  plan_head_before: 026c3a8
  plan_head_after: 0a990c4

tech-stack:
  added: []
  patterns:
    - "topic_approval.py's approve()/reject() reuse topics_service.get_topic()/_person_refs() directly (including the underscore-private helper) rather than forking a parallel implementation — the plan's own instruction and the established convention from list_topics/register_topic (plan 02-05)."
    - "approve() reads the topic ONCE to pick which of two conditional UPDATE variants to run (no-SV -> DA_DUYET vs has-SV -> DA_PHAN_CONG+GVHD), but the accept/reject decision itself is still made entirely by each UPDATE's WHERE clause (trang_thai='CHO_DUYET' plus a matching sinh_vien_id) — a concurrent registration or a second Bộ môn's decision between the read and the UPDATE still gets rowcount=0, not a stale write. This is the same non-check-then-act shape as register_topic (02-05)."
    - "list_pending fetches ALL of a page's latest ket_qua_kiem_tra_trung_lap rows in ONE query (ORDER BY de_tai_id, thoi_diem DESC, id DESC, keep first-seen per de_tai_id in Python) rather than per-row queries — same N+1-avoidance shape as _sv_has_active_topic (02-05)."
    - "Dashboard services use only COUNT()/exists() aggregates, never a Python loop over all rows, matching the plan's explicit constraint for /api/dashboard/*."
    - "BmDashboard's default cohort resolution (_default_cohort): newest DANG_MO by id, falling back to newest cohort of any state — mirrors the e2e script's need for a sensible default when no dot_do_an_id query param is given."

key-files:
  created:
    - backend/app/schemas/topic_approval.py
    - backend/app/services/topic_approval.py
    - backend/app/routers/topic_approval.py
    - backend/tests/test_topic_approval_rbac.py
    - backend/app/schemas/dashboard.py
    - backend/app/services/dashboard.py
    - backend/app/routers/dashboard.py
    - backend/app/routers/dashboard.py
    - frontend/src/features/topic-approval/api.ts
    - frontend/src/features/topic-approval/TopicApprovalPage.tsx
    - frontend/src/features/topic-approval/routes.tsx
    - frontend/src/features/dashboard/api.ts
    - frontend/src/features/dashboard/SvDashboard.tsx
    - frontend/src/features/dashboard/GvDashboard.tsx
    - frontend/src/features/dashboard/BmDashboard.tsx
    - deploy/e2e-uc1.sh
  modified:
    - frontend/src/features/dashboard/DashboardPage.tsx
    - deploy/smoke-test.sh
    - deploy/README.md

key-decisions:
  - "PendingTopicItem.giang_vien/sinh_vien/nguoi_de_xuat all reuse topics_service._person_refs(topic) — the same tuple already computed for TopicOut/TopicListItem, so MH-07's row shape and the Drawer's TopicOut share one source of person-mapping logic."
  - "TitleCheckSummary (KHONG_TRUNG/CO_TUONG_TU/CHUA_KIEM_TRA) is a NEW 3-state view model computed in topic_approval.py from the raw ket_qua_kiem_tra_trung_lap.trang_thai (HOAN_TAT/LOI) + chi_tiet presence — kept separate from the raw DB enum because MH-07's Kiểm tra tên column needs a Bộ môn-facing state that TopicOut's SavedTitleCheck does not expose directly."
  - "Drawer's GVHD Select never has a default value even when the proposing GV is the only realistic choice (UC1.3 E1) — approve() rejects with 422 'Vui lòng chọn giảng viên hướng dẫn' whenever giang_vien_id is omitted for a topic that has an SV, so the frontend's disabled-until-chosen button and the backend's required-field validation enforce the same rule twice, independently."
  - "Dashboard meta line/date-format bugs (see Deviations) were found via this plan's own CDP self-check, not the plan's written acceptance criteria — both are cosmetic-but-real MH-07 fidelity issues that a screenshot-based human-check catches and a grep-based acceptance criterion cannot."

patterns-established:
  - "CDP self-check convention (carried from 02-05, reused verbatim): a fresh headless Chrome instance on --remote-debugging-port=9333, page-context `fetch('/api/auth/login', {credentials:'include'})` to set the refresh_token cookie for whichever account is being tested next (each such call OVERWRITES the browser's session — must re-login as the intended actor immediately before any protected navigation), real Input.dispatchMouseEvent clicks (never synthetic .click()) to open antd Select dropdowns, and self-created scratchpad test data cleaned via deploy/sql.sh in the same script that created it."

requirements-completed: [TOPC-03, TOPC-04, AUTH-03, DEPL-02]

coverage:
  - id: D1
    description: "Bộ môn sees every Chờ duyệt topic on MH-07 with Người đề xuất/Lĩnh vực/Ngày đề xuất (DD/MM/YYYY) and a Kiểm tra tên tag (Không trùng/N đề tài tương tự/Chưa kiểm tra); the Drawer shows the saved title-check result plus a GVHD Select that is never pre-filled (UC1.3 E1)"
    requirement: "TOPC-03"
    verification:
      - kind: unit
        ref: "backend/tests/test_topic_approval_rbac.py::test_non_bomon_gets_403_on_every_approval_endpoint — pass (9 parametrized cases; genuine RED confirmed by temporarily removing router-level require_role, 3 GET cases failed 200!=403, then restored to GREEN)"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc1.sh steps (d)-(e)-(h)-(i) through Apache HTTPS — pending list, approve-no-SV -> DA_DUYET, approve-with-SV+GVHD -> DA_PHAN_CONG, reject-with-reason -> TU_CHOI — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP session (scratchpad cdp_check_0206.py): p06-t1-01-list.png (table matches MH-07 columns/tags exactly incl. '1 đề tài tương tự'), p06-t1-03-drawer-has-sv.png / p06-t1-04-gvhd-selected.png (GVHD Select empty-by-default, E1 hint text, primary button disabled until chosen), p06-t1-06-reject-modal.png (Modal matches MH-07 exactly) — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Visual fidelity to MH-07 (table/tag/Drawer/Modal layout, GVHD Select never pre-filled) is a judgment call; self-performed via CDP per the autonomous-run instruction, genuine user confirmation still pending."
  - id: D2
    description: "Approving a GV topic without SV moves it to Đã duyệt; approving a topic with an SV requires the Bộ môn to pick a GVHD manually (never auto-assigned) and moves it to Đã phân công; rejecting requires a non-empty reason, moves it to Từ chối and the proposer sees the reason"
    requirement: "TOPC-03"
    verification:
      - kind: e2e
        ref: "deploy/e2e-uc1.sh — GV topic approved with no SV -> DA_DUYET; same topic later approved WITH SV+giang_vien_id -> DA_PHAN_CONG; SV topic rejected with reason -> TU_CHOI, proposer's GET /api/topics/{id} shows the exact reason string — all pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP: p06-t1-08-sv-sees-reject-reason.png — SV DTC225200004 detail page shows 'Lý do từ chối: Kiểm thử hiển thị P06: đã xem trước bởi tác vụ tự động' — self-viewed"
        status: pass
    human_judgment: false
  - id: D3
    description: "SV and GV tokens (including the proposing GV) get 403 from every /api/topic-approvals endpoint and the topic state is unchanged; approve/reject are conditional UPDATEs so a double click or two admins cannot apply two decisions"
    requirement: "AUTH-03"
    verification:
      - kind: unit
        ref: "test_topic_approval_rbac.py — SV, unrelated GV, and the proposing GV all 403 on GET/approve/reject; topic trang_thai/giang_vien_id/sinh_vien_id/ly_do_tu_choi asserted unchanged after each rejected call"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc1.sh step (g): DTC225200099 approve -> 403; GV030 edit SV's topic -> 403"
        status: pass
    human_judgment: false
  - id: D4
    description: "deploy/e2e-uc1.sh drives the whole UC1 flow through Apache HTTPS with seeded accounts and cleans up its own data"
    requirement: "DEPL-02"
    verification:
      - kind: integration
        ref: "bash deploy/e2e-uc1.sh — all 13 steps print OK end to end; test \"$(bash deploy/sql.sh \"SELECT COUNT(*) FROM dot_do_an WHERE khoa='K99'\")\" = 0 after the script exits — pass, run 3x during this plan without a single failure"
        status: pass
    human_judgment: false
  - id: D5
    description: "Each role's /tong-quan shows its MH-02/03/04 Phase-2 widgets backed by a role-restricted endpoint (SV: Đề tài của tôi; GV: Sinh viên hướng dẫn/Đề tài chờ duyệt/Đề tài hướng dẫn; Bộ môn: Đề tài chờ duyệt/SV chưa có đề tài/Đề tài đã phân công/Đề tài chờ duyệt mới nhất)"
    requirement: "TOPC-04"
    verification:
      - kind: unit
        ref: "backend/tests full suite (37 passed) incl. the generic route-coverage test in test_auth.py, which now also covers /api/dashboard/* — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP: p06-t2-01-sv-dashboard.png, p06-t2-02-gv-dashboard.png, p06-t2-03-bm-dashboard-default.png — each role's widgets show live numbers matching the DB state created earlier in the same session (GV: 0/1 đề tài, 1 chờ duyệt; Bộ môn: 2 chờ duyệt/99 SV chưa có đề tài/100/1 đã phân công, cohort Select defaulted to the newest DANG_MO cohort) — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Visual fidelity to MH-02/03/04 and correctness of live aggregate numbers against a real browser session is a judgment call; self-performed via CDP, genuine user confirmation still pending."
  - id: D6
    description: "bash deploy/smoke-test.sh passes end-to-end through Apache, including cross-role 403 checks on dashboards, accounts, cohorts, approvals and registration"
    requirement: "DEPL-02"
    verification:
      - kind: integration
        ref: "bash deploy/smoke-test.sh — all checks incl. the new (n) dashboard/role-403 block print OK, run 2x during this plan"
        status: pass
    human_judgment: false

duration: ~65min
completed: 2026-09-28
status: complete
---

# Phase 2 Plan 6: Duyệt đề tài (UC1.3, MH-07) + Dashboards (MH-02/03/04) + e2e UC1 Summary

**`/api/topic-approvals` lets the Bộ môn approve (open registration or assign a manually-chosen GVHD), or reject with a mandatory reason, every Chờ duyệt topic via two conditional `UPDATE ... WHERE trang_thai='CHO_DUYET'` statements that make a double decision impossible; role-restricted `/api/dashboard/*` gives each of the three roles its own live MH-02/03/04 widget subset; and `deploy/e2e-uc1.sh` proves the entire UC1 flow — propose, self-propose, approve, register, assign, reject, filter — through Apache HTTPS with fully self-cleaning test data, closing Phase 2.**

## Performance

- **Duration:** ~65 min
- **Started:** 2026-09-28 (STATE.md, end of plan 02-05)
- **Completed:** 2026-09-28
- **Tasks:** 2/2 completed
- **Files modified:** 18 (15 created, 3 modified, across 3 commits)

## Accomplishments

- **Task 1 (UC1.3, TOPC-03, AUTH-03, ROADMAP SC3/SC5):** `topic_approval.py` service reuses `topics_service._person_refs`/`get_topic` rather than forking. `list_pending` fetches the whole page's latest title-check rows in one query (ORDER BY de_tai_id, thoi_diem DESC, id DESC, first-seen-per-topic in Python) and maps each `ket_qua_kiem_tra_trung_lap` row to a new 3-state `TitleCheckSummary` (KHONG_TRUNG/CO_TUONG_TU/CHUA_KIEM_TRA) distinct from the raw HOAN_TAT/LOI DB enum. `approve()` reads the topic once to choose between two conditional `UPDATE`s — `sinh_vien_id IS NULL -> DA_DUYET` (giang_vien_id ignored) or `sinh_vien_id = :seen -> DA_PHAN_CONG + giang_vien_id` (422 if omitted or the GV is unknown/locked) — never auto-assigning a GVHD (UC1.3 E1) even when the proposing GV is the obvious choice. `reject()` is one `UPDATE ... SET trang_thai='TU_CHOI', ly_do_tu_choi=:ly_do WHERE trang_thai='CHO_DUYET'`; the generated `sinh_vien_id_dang_hoat_dong` column then frees the SV automatically. `test_topic_approval_rbac.py` is one test parametrized over 3 callers (SV, unrelated GV, the proposing GV) × 3 endpoints (GET/approve/reject) — genuine RED confirmed by temporarily removing the router-level `require_role`, which flipped the 3 GET cases from 403 to 200, then restored to GREEN. Frontend `TopicApprovalPage.tsx` (MH-07): pending table + Drawer (saved title-check block, GVHD Select with "(người đề xuất)" suffix and the E1 hint, footer button toggling between "Duyệt"/"Duyệt và phân công") + reject Modal, matching the mockup screenshot-for-screenshot. `deploy/e2e-uc1.sh` drives GV propose → SV self-propose → Bộ môn sees both → approve (no SV) → SV registers → second SV 409 → cross-role 403s → Bộ môn assigns GVHD → Bộ môn rejects with reason → proposer sees it → filtered list — all through Apache HTTPS, self-cleaning its own K99 cohort via a `trap`.
- **Task 2 (TOPC-04, D-09, DEPL-02, D-11):** `/api/dashboard/sinh-vien|giang-vien|bo-mon`, one endpoint per role, every query scoped to the caller's own `sinh_vien_id`/`giang_vien_id` (SV/GV) or aggregated with `COUNT()`/`exists()` only (Bộ môn) — no Python loops over all rows. `SvDashboard`/`GvDashboard`/`BmDashboard` render only the Phase-2-backed MH-02/03/04 widgets (đề cương/tiến độ/hội đồng/thông báo widgets deferred to Phase 3, per this plan's own context notes). `smoke-test.sh` gained a cross-role 403 block (dashboards, accounts, cohorts, topic-approvals, registration) and `README.md` gained the full Vietnamese UC1 demo script plus the automated-test section documenting the e2e script's reserved accounts.
- **Both tasks' `<human-check>` items were self-performed** via a CDP-driven headless Chrome session (screenshots in the scratchpad — see Human-check section below), which caught and fixed two real MH-07 fidelity bugs before commit (see Deviations).

## Task Commits

1. **Task 1: Bộ môn approves/assigns/rejects (UC1.3, MH-07) + e2e UC1** — `c20332c` (feat)
2. **Fixup (found during this plan's own human-check): MH-07 date format + duplicate "Đợt" in meta line** — `f2669f6` (fix)
3. **Task 2: role dashboards (MH-02/03/04) + final smoke/README** — `0a990c4` (feat)

_Task 1 is `tdd="true"`; genuine RED was confirmed by temporarily removing the router-level `require_role(VaiTro.BO_MON)` dependency (3 of 9 parametrized cases flipped from 403 to 200) and re-running pytest before restoring and committing GREEN. Task 2 is plain `type="auto"`. The plan carries no checkpoints, so it ran to completion autonomously._

## Files Created/Modified

- `backend/app/schemas/topic_approval.py`, `backend/app/services/topic_approval.py`, `backend/app/routers/topic_approval.py` (new) — Task 1
- `backend/tests/test_topic_approval_rbac.py` (new) — Task 1
- `frontend/src/features/topic-approval/{api.ts,TopicApprovalPage.tsx,routes.tsx}` (new) — Task 1
- `deploy/e2e-uc1.sh` (new) — Task 1
- `backend/app/schemas/dashboard.py`, `backend/app/services/dashboard.py`, `backend/app/routers/dashboard.py` (new) — Task 2
- `frontend/src/features/dashboard/api.ts`, `SvDashboard.tsx`, `GvDashboard.tsx`, `BmDashboard.tsx` (new); `DashboardPage.tsx` (modified) — Task 2
- `deploy/smoke-test.sh`, `deploy/README.md` (modified) — Task 2

## Decisions Made

See `key-decisions` in frontmatter. Summary:
- `PendingTopicItem` reuses `_person_refs()` — same person-mapping logic as `TopicOut`/`TopicListItem`, no duplication.
- `TitleCheckSummary`'s 3 states are a new Bộ môn-facing view model, deliberately separate from the raw `ket_qua_kiem_tra_trung_lap.trang_thai` DB enum.
- GVHD is NEVER pre-selected, enforced independently on both frontend (disabled button) and backend (422 if omitted) — belt-and-suspenders for UC1.3 E1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] MH-07 Drawer "Ngày đề xuất" showed DD/M/YY instead of DD/MM/YYYY**
- **Found during:** this plan's own CDP human-check (screenshot showed "28/9/26")
- **Issue:** `formatNgayDeXuat` used `Intl.DateTimeFormat(..., {dateStyle: 'short'})`, which for `vi-VN` renders a 2-digit year and no leading zero on the month — the plan's action explicitly specifies "DD/MM/YYYY".
- **Fix:** switched to explicit `{day: '2-digit', month: '2-digit', year: 'numeric'}`.
- **Files modified:** `frontend/src/features/topic-approval/TopicApprovalPage.tsx`
- **Commit:** `f2669f6`

**2. [Rule 1 - Bug] Drawer meta line read "Đợt Đợt đồ án tốt nghiệp K22 - HK1 (2026-2027)"**
- **Found during:** same CDP human-check pass (a test cohort literally named "Đợt kiểm thử hiển thị P06" made the duplication visually obvious, but the real seed cohort's name — "Đợt đồ án tốt nghiệp K22 - HK1 (2026-2027)" — has the exact same problem)
- **Issue:** the meta line hardcoded `"Đợt " + detail.dot_do_an.ten_dot`; every real cohort name already starts with the word "Đợt", so the literal prefix always duplicates it. The MH-07 mockup itself shows the short form `"Đợt K22A"` (khoa), not the full `ten_dot`.
- **Fix:** meta line now reads `"Đợt " + detail.dot_do_an.khoa`, matching the mockup exactly.
- **Files modified:** `frontend/src/features/topic-approval/TopicApprovalPage.tsx`
- **Commit:** `f2669f6`

No other deviations — everything else executed exactly as written in the plan.

## Issues Encountered

- The first CDP self-check attempt had every "Xem chi tiết" row-open click silently no-op (the drawer never appeared) because the script clicked the center of the matching `<td>` instead of the "Xem chi tiết" `<button>` inside that row — fixed by adding a `click_row_button(row_text, button_text)` helper that finds the `<tr>` containing the text and clicks the button inside it, not the cell itself. Scratchpad-tooling issue only, not a shipped-code defect.
- Each `fetch('/api/auth/login', {credentials:'include'})` call in the CDP script overwrites the browser's `refresh_token` cookie for whoever is being logged in — the first full run navigated to `/duyet-de-tai` still carrying the last SV's session from data setup and got redirected away, producing "NOT_FOUND" for every subsequent selector. Fixed by re-logging in as `bomon` immediately before that navigation. Also scratchpad-tooling only.
- Demo-data topics/cohorts created during CDP self-verification (cohort khoa K97 + 4 topics + their `ket_qua_kiem_tra_trung_lap`/`chi_tiet_trung_lap` rows) were deleted via `deploy/sql.sh` at the end of the same script, matching the established convention from plans 02-04/02-05; `de_tai` and the K97 cohort confirmed empty again before handoff.

## Human-check (self-performed, pending user confirmation)

Per the autonomous-run instruction, self-performed both tasks' `<human-check>` via a CDP-driven headless Chrome session (`google-chrome --headless=new --remote-debugging-port=9333`), screenshots in the scratchpad:

**Task 1** (`p06-t1-01-list.png` .. `p06-t1-08-sv-sees-reject-reason.png`): as `bomon`, opened "Duyệt & phân công đề tài" — the table showed 4 seeded test topics with the exact MH-07 columns/tags, including a genuine `1 đề tài tương tự` warning tag (the AI stub scored two deliberately near-duplicate titles at 83.33% similarity) alongside `Không trùng` success tags. Opened the similar-title topic's Drawer — saved title-check block rendered as a table of matches, matching MH-07's alert+table pattern exactly. Opened a self-proposed SV topic's Drawer — GVHD Select was empty by default (no pre-selection, per E1), selected a GV, "Duyệt và phân công" enabled and succeeded → toast "Đã duyệt và phân công GVHD", row disappeared from the Chờ duyệt table. Opened a second SV topic, clicked "Từ chối", filled the Modal's required TextArea, "Xác nhận từ chối" succeeded. Logged in as that SV and confirmed her detail page shows exactly "Lý do từ chối: Kiểm thử hiển thị P06: đã xem trước bởi tác vụ tự động".

**Task 2** (`p06-t2-01-sv-dashboard.png` .. `p06-t2-03-bm-dashboard-default.png`): the just-approved SV's `/tong-quan` showed "Đề tài của tôi" with the correct title, GVHD name, and "Đã phân công" tag. The GV whose topic was still pending saw "Sinh viên hướng dẫn 0/1 đề tài", "Đề tài chờ duyệt 1", and a one-row "Đề tài hướng dẫn" table. `bomon`'s "Tổng quan toàn khoa" showed "Đề tài chờ duyệt 2" (red), "SV chưa có đề tài 99/100", "Đề tài đã phân công 1", the cohort Select defaulted to the newest open cohort, and "Đề tài chờ duyệt mới nhất" listed both remaining pending topics with their proposers' names — all numbers matched the DB state created earlier in the same session.

**User confirmation of both checks is still pending** — flagged here per coverage items D1/D5.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Phase 2 is complete: all three roles can log in, be locked/unlocked, open/close a đợt, propose/self-propose/register/approve/assign/reject a topic with server-side RBAC enforced on every route, and see a live role-restricted dashboard — all proven through Apache HTTPS by `smoke-test.sh` + `e2e-uc1.sh` + `check-erd-db.py`. Phase 3 (UC2–UC5: đề cương, tiến độ, bảo vệ, kho đồ án + in-app notifications) should hook `approve()`/`reject()` in `services/topic_approval.py` for NOTF-01, and extend `schemas/dashboard.py`'s payload shapes rather than forking new dashboard endpoints. No blockers.

---
*Phase: 02-platform-rbac-topic-management*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 15 created/referenced key files confirmed present on disk; all 3 task commits (`c20332c`, `f2669f6`, `0a990c4`) confirmed present in `git log --oneline --all`.
