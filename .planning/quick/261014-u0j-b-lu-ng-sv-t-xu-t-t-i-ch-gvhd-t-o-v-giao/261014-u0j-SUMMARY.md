---
phase: quick-261014-u0j
plan: 01
subsystem: topics (UC1), dashboards, deploy scripts, chương 2-3 docs
tags: [gvhd-feedback, topic-assign, rbac, fastapi, react, docs]
requires: [UC0.8 phan_cong_huong_dan]
provides:
  - "GVHD-only topic creation/assignment (POST/PUT/submit/check-title) with sinh_vien_id required"
  - "SV proposal, SV registration and GVHD approval removed (404)"
  - "Chương 2-3 documents, diagrams, mockups and traceability for the GV-assign flow"
affects: [backend/app/routers/topics.py, backend/app/services/topics.py, frontend/src/features/topics, deploy/*.sh, docs/chuong-2-khao-sat-phan-tich, docs/chuong-3-thiet-ke]
tech-stack:
  added: []
  patterns: [require_role(GIANG_VIEN) on write routes, is_advisor_of before every write, IntegrityError -> 409 for 1 SV : 1 active topic]
key-files:
  created:
    - backend/tests/test_topic_assign.py
    - docs/chuong-2-khao-sat-phan-tich/uc/act-uc1-tao-giao-de-tai.puml
  modified:
    - backend/app/routers/topics.py
    - backend/app/services/topics.py
    - backend/app/services/assignments.py
    - backend/app/services/dashboard.py
    - frontend/src/features/topics/TopicFormPage.tsx
    - deploy/e2e-uc1.sh
    - tools/demo/kich-ban-anh.json
  deleted:
    - backend/app/routers/topic_approval.py
    - backend/app/services/topic_approval.py
    - backend/app/schemas/topic_approval.py
    - frontend/src/features/topic-approval/
decisions:
  - "D-03: no Alembic migration; legacy enum values CHO_DUYET/DA_DUYET/TU_CHOI, ly_do_tu_choi, loai_nguoi_de_xuat and thong_bao type strings kept in the DB, code no longer produces them"
  - "SV dashboard fallback query excludes NHAP so a GV draft is never shown to the SV"
  - "UC1 reduced to UC1.1 Tao va giao de tai + UC1.2 Xem va loc; FR-DT-01..11 keep IDs; MH-07 repurposed as Chi tiet de tai duoc giao"
metrics:
  tasks: 3
  completed: 2026-10-14
status: complete
actuals:
  tokens: 300000
  tasks: 3
  commits: 3
plan_head_before: 792074482cf38a5c92d4b0ea47cd97b2c2b7a31e
plan_head_after: 1b34f0b4921ab54f4a9170589e1dfd764d2cd148
---

# Phase quick-261014-u0j Plan 01: GVHD tạo và giao đề tài Summary

Student topic proposal, registration and GVHD approval are removed; only the GVHD assigned by Bộ môn creates a topic and assigns it straight to a student in their advisee class (Đã phân công immediately, UC0.6 title check saved, student notified), verified by pytest 54/54 and a full `verify-all.sh --report` at 14/14 OK.

## What was built

**Task 1 (commit b0c9aa4) — backend + API-level scripts.**
- `POST/PUT /api/topics`, `/submit`, `/check-title` are `require_role(GIANG_VIEN)` (SV and Bộ môn get 403). `sinh_vien_id` is required (422 if missing). Create/update/submit always call `_require_my_student` (409 "không thuộc lớp hướng dẫn"); sending is Đã phân công and creates one `DE_TAI_PHAN_CONG` notification (lien_ket `/de-tai/{id}`) in the same commit. Submit of a draft that lost its SV returns 409 with a "chọn sinh viên" message.
- Deleted the registration handler/service and the whole `topic_approval` router/service/schema (route now 404). SV scope in `can_view` and `_scope_predicate` is limited to the SV's own non-draft topics; `QuyenOut.dang_ky` and `TopicListItem.co_the_dang_ky` removed.
- `assignments.reassign` no longer moves CHO_DUYET topics or blocks removal on "chờ duyệt"; it still blocks change/removal for Đã phân công and detaches the old GV's drafts.
- Dashboards: GV `so_sinh_vien_chua_giao_de_tai` + one aggregated `GIAO_DE_TAI` task (first); Bộ môn `sv_chua_giao_de_tai` + `de_tai_moi_giao` (5 latest Đã phân công).
- Tests: new `test_topic_assign.py` (RED first, 5 failed against old code; covers 403/404 RBAC, 409/422, concurrent create -> exactly one 201 + one 409, draft hidden from SV then submit, detached draft), rewrote ownership/notifications/assignments tests, deleted registration and approval-RBAC tests.
- Scripts: `e2e-uc1.sh` fully rewritten (steps a-k), `e2e-uc2-5.sh`, `e2e-ai.sh`, `ai-nfr.sh`, `demo-state.sh` (GV011 `giao_de_tai` for 012-015, 011 left unassigned), `smoke-test.sh`, `nfr-he-thong.sh` (check-title as GV001, NFR-12 status array), `verify-all.sh` (NFR-04 evidence text).

**Task 2 (commit ed412e1) — frontend, demo, screenshots.**
- Deleted `features/topic-approval`; GV-only "Giao đề tài" route/menu; `TopicFormPage` GV-only with required student select; "Vẫn giao đề tài"; list without register/"Người đề xuất"; `TopicDetailPage` = MH-07; dashboards (GV card + task label "Giao", BM card + "Đề tài giao gần nhất", SV empty state text); `MyStudentsPage` no approve button.
- `kich-ban-anh.json` (29 steps, 4 ghi_du_lieu) and `kich-ban-demo.json` (B01-B18) rewritten; 29 PNGs regenerated and exactly equal the 29 step ids (3 old PNGs removed), `anh-chup.json`, `tap-duot-demo.md` regenerated, deploy README rewritten.

**Task 3 (commit 1b34f0b) — documents + final verification.**
- Chương 2: UC1 spec (UC1.1/UC1.2, BR-DT-01..05), FR-DT-01..11 rewritten (IDs kept), 02 process (TB-DT-00a..00c, TB-DT-01..12), 05, 11 (UC0.6/UC0.8/notification wording), 01 survey notes.
- Chương 3: class/state docs, DB design (legacy enum/column documented as "giá trị/cột cũ ... không còn phát sinh"), architecture API table and `seq-check-title`, interface inventory + MH-02..07/16 sections, truy-vet, docs/README, REQUIREMENTS.md, PROJECT.md (Key Decisions row added).
- Diagrams re-rendered: `bpmn/01-de-tai` (TO-BE page regenerated, AS-IS wording aligned) and `bpmn/00-tong-quan`; `uc/uc1-quan-ly-de-tai`, `uc/uc-tong-quat`, `uc/uc0-chuc-nang-chung`, `uc/act-uc1-tao-giao-de-tai` (renamed from `act-uc1-de-xuat-dang-ky-de-tai`); `so-do-lop/trang-thai-de-tai`, `trang-thai-de-cuong`; `kien-truc/seq-check-title`; mockups mh-02, 03, 04, 05, 06, 07, 16.
- `python3 tools/check-docs.py all` prints only the pre-existing PI 1.1 line; `tools/check-erd-db.py` OK.

## verify-all --report result (full, 336 s, exit 0): 14/14 OK

| # | Step | Result |
|---|------|--------|
| 1 | Stack health | OK |
| 2 | Test data DATA-01/02/03 | OK |
| 3 | Smoke test (HTTPS) | OK |
| 4 | Pytest backend | OK |
| 5 | Pytest ai-service | OK |
| 6 | E2E UC1 | OK |
| 7 | E2E UC2-UC5 | OK |
| 8 | E2E AI | OK |
| 9 | NFR-07..11 AI | OK |
| 10 | NFR system over HTTPS | OK |
| 11 | ERD vs schema | OK |
| 12 | No leftover test data | OK |
| 13 | NFR-16 (25/25 screens at 1440 px) | OK |
| 14 | Demo state unchanged | OK |

Evidence files regenerated and committed: `tong-hop.json`, `nhat-ky-verify-all.log`, `thu-nghiem-ai/04-hieu-nang-va-bao-mat.md`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `test_thresholds.py` called check-title as an SV**
- **Found during:** Task 1 full pytest run
- **Issue:** check-title is now GV-only, so the existing threshold test got 403
- **Fix:** use the GV account (`gv_a`) for the three check-title calls
- **Files modified:** backend/tests/test_thresholds.py
- **Commit:** b0c9aa4

**2. [Rule 2 - Missing critical] SV dashboard could show a GV draft**
- **Found during:** Task 1 dashboard rewrite
- **Issue:** the fallback "latest topic by sinh_vien_id" query could return an NHAP draft the SV must not see (D-05)
- **Fix:** exclude `NHAP` in that query
- **Files modified:** backend/app/services/dashboard.py
- **Commit:** b0c9aa4

**3. [Rule 1 - Bug] e2e-ai SV lookup returned empty**
- **Found during:** Task 1 e2e-ai run (`page_size=50` over 580 SVs missed the two accounts)
- **Fix:** look each SV up with `q=<MSSV>`
- **Files modified:** deploy/e2e-ai.sh
- **Commit:** b0c9aa4

**4. [Rule 1 - Bug] GV dashboard task row rendered "— - —"**
- **Found during:** Task 2 screenshot review (aggregated GIAO_DE_TAI task has no SV/topic)
- **Fix:** render "Lớp hướng dẫn" when both are null
- **Files modified:** frontend/src/features/dashboard/GvDashboard.tsx
- **Commit:** ed412e1

## Decisions / notes for the orchestrator

- **No migration added** (D-03): enum values CHO_DUYET/DA_DUYET/TU_CHOI, columns `ly_do_tu_choi` and `loai_nguoi_de_xuat`, and `thong_bao` type strings stay in the DB; `models/de_tai.py`, `models/thong_bao.py` and Alembic untouched.
- **`CONVENTIONS.md` not edited** (it mirrors PROJECT.md and is regenerated by GSD tooling): its Core Value still says "khi sinh viên đăng ký đề tài hoặc nộp đề cương/báo cáo". `.planning/PROJECT.md` and `.planning/REQUIREMENTS.md` were updated and committed with Task 3 (they are listed in the plan's files_modified); STATE.md/ROADMAP.md/PLAN.md/SUMMARY.md left for the orchestrator.
- The ai image was never rebuilt; only `api` and `apache` were rebuilt. Demo state was rebuilt (`demo-state.sh`) and verified pristine by verify-all step 14.
- `tap-duot-demo.md` keeps older rehearsal runs in its history section; only the newest run reflects the new flow.
- Untracked `docs/khao-sat-cong-cu-kiem-tra-trung-lap.md` (other task) was not staged or committed.

## Known Stubs

None.

## Threat Flags

None (no new endpoints; two routes removed, four write routes tightened to GV-only per T-u0j-01..05).

## Self-Check: PASSED

- Commits b0c9aa4, ed412e1, 1b34f0b exist on branch phan-cong-gvhd (3 commits since plan_head_before).
- Deleted modules gone; `backend/tests/test_topic_assign.py`, `docs/chuong-2-khao-sat-phan-tich/uc/act-uc1-tao-giao-de-tai.png`, 29 step PNGs present.
- pytest 54 passed; verify-all --report 14/14 OK.
