---
phase: 02-platform-rbac-topic-management
plan: 05
subsystem: topics
tags: [fastapi, sqlalchemy, mysql, react, antd, tanstack-query, concurrency]

requires:
  - phase: 02-platform-rbac-topic-management (plan 04)
    provides: "app/services/topics.py (is_owner/can_view/create_topic/update_topic/submit_topic/get_topic), schemas/topics.py (TopicOut, PersonRef, CohortRef), routers/topics.py, migration 0003 de_tai (sinh_vien_id_dang_hoat_dong generated column + uk_de_tai_sv_hoat_dong), frontend features/topics/{api,routes,constants,TopicDetailPage}.tsx"
  - phase: 02-platform-rbac-topic-management (plan 03)
    provides: "DotDoAn (DANG_MO/DA_DONG), useCohorts() hook"
provides:
  - "GET /api/topics: list_topics(db, user, params) — role-scoped (SV/GV own+open, BO_MON all), filtered by đợt/trạng thái/GVHD/lĩnh vực/từ khóa, server-side paginated"
  - "POST /api/topics/{id}/register: register_topic(db, user, id) — single conditional UPDATE + uk_de_tai_sv_hoat_dong, no check-then-act"
  - "TopicOut.quyen.dang_ky / TopicListItem.co_the_dang_ky — SV-only registrability flag computed once per request via sinh_vien_id_dang_hoat_dong"
  - "frontend/src/features/topics/TopicListPage.tsx (MH-05) — filter bar + table + pagination + Đăng ký action, all state in useSearchParams"
  - "backend/tests/test_topic_registration.py — the two concurrency tests named by ROADMAP SC4"
affects: [02-06, phase-03, phase-04]

actuals:
  tokens: 10200
  tasks: 2
  commits: 2
  plan_head_before: eb080cd884e8b361610e8ea2d42f4eeb3f3f508c
  plan_head_after: d40d83cd9ac02cc2323a1c4fc531f07d1baf52bf

tech-stack:
  added: []
  patterns:
    - "Scope-predicate-first list query (T-02-29): _scope_predicate(user, pham_vi) builds the SV/GV/BO_MON visibility boundary BEFORE any user-supplied filter is ANDed in, so a filter can narrow but never widen what a role is allowed to see — verified by a test that combines an explicit trang_thai+pham_vi=tat_ca filter and still gets 0 rows for another SV's pending topic."
    - "One extra query per request/page, not per row (D-05): _sv_has_active_topic(db, user) reads the sinh_vien_id_dang_hoat_dong generated column ONCE per list_topics/get_topic call and is threaded through _can_register() for every row — avoids N+1 when computing co_the_dang_ky across a page of results."
    - "Registration is a single conditional UPDATE, never read-then-write (§3.2.5-b): register_topic's WHERE clause (sinh_vien_id IS NULL AND trang_thai=DA_DUYET AND loai_nguoi_de_xuat=GIANG_VIEN AND cohort DANG_MO) is the ONLY thing that decides the winner under a concurrent request; a rowcount=0 re-read exists purely to pick the right error message, never to decide the outcome."
    - "_person_refs() extracted as a shared helper between _to_out (TopicOut) and _list_item_out (TopicListItem) — same person-mapping logic, no duplication, both paths rely on the same selectinload/joinedload eager-loading to avoid N+1."

key-files:
  created:
    - frontend/src/features/topics/TopicListPage.tsx
    - backend/tests/test_topic_registration.py
  modified:
    - backend/app/schemas/topics.py
    - backend/app/services/topics.py
    - backend/app/routers/topics.py
    - backend/tests/test_topic_ownership.py
    - frontend/src/features/topics/api.ts
    - frontend/src/features/topics/routes.tsx
    - frontend/src/features/topics/TopicDetailPage.tsx

key-decisions:
  - "TopicListParams as a plain @dataclass (not a Pydantic/NFCModel) in schemas/topics.py — FastAPI's Query() already validates/coerces every field (Literal enums for trang_thai/pham_vi/sap_xep) before the router builds it, so a second validation layer would be redundant; q is NFC-normalized explicitly inside list_topics via nfc(), matching D-06 without a second model."
  - "Registration's rowcount=0 branch re-reads the topic/cohort ONLY to choose the user-facing message (404 missing / 409 cohort closed / 409 already-taken) — the actual accept/reject decision was already made atomically by the UPDATE's WHERE clause, so this is not a check-then-act gap (the re-read cannot flip a request that the UPDATE already rejected)."
  - "MH-05's sidebar menu restructure (SV 'Đề xuất / Đăng ký đề tài' repointed from the propose form directly to the list page) follows plan 02-04's documented shim-route convention exactly: each per-role label needs its own AppRoute object (dummy path + Navigate) because MenuEntry carries one label per route; two new shims added for SV 'Đề tài của tôi' and GV 'Đề tài hướng dẫn', both pointing at '/de-tai?pham_vi=cua_toi'."

patterns-established:
  - "CDP driver bugfix carried forward: the scratchpad's click_selector/click_text helpers had an extra stray '}' in their generated IIFE wrapper (silently swallowed as a JS exception, manifesting as a false 'selector not found' after full retry exhaustion) — fixed for this and future CDP-based self-verification sessions. Also confirmed the app-wide antd ConfigProvider locale is vi_VN, so Popconfirm's default confirm button reads 'Đồng ý' (not 'OK') — relevant for any future CDP script that needs to click it."

requirements-completed: [TOPC-04, TOPC-02, TOPC-03, AUTH-03]

coverage:
  - id: D1
    description: "Every role (SV/GV/BO_MON) lists and filters topics by state/đợt/GVHD/lĩnh vực/keyword within a server-enforced scope that filters can never widen (UC1.4 A1, TOPC-04)"
    requirement: "TOPC-04"
    verification:
      - kind: unit
        ref: "backend/tests/test_topic_ownership.py::test_sv_proposal_visibility_enforced (extended: GET /api/topics scope assertions) — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP session: SV 'Đề tài của tôi'/'Đề xuất / Đăng ký đề tài', GV 'Đề tài hướng dẫn', BO_MON 'Danh sách đề tài' + filters + reload — screenshots t1-01..t1-05 self-viewed"
        status: pass
    human_judgment: true
    rationale: "Visual fidelity to MH-05 and filter/URL-persistence UX in a real browser are judgment calls; self-performed via CDP per the autonomous-run instruction, genuine user confirmation still pending."
  - id: D2
    description: "GET /api/topics answers in <=1s P95 over 20 calls through Apache (NFR-12)"
    requirement: "TOPC-04"
    verification:
      - kind: integration
        ref: "for-loop of 20 curl calls through https://localhost, 19th-fastest sorted -> 0.0196s"
        status: pass
    human_judgment: false
  - id: D3
    description: "SV registers a GV-proposed Đã duyệt topic with no SV, in an open đợt, from MH-05 or the detail page; only SV can (GV/BO_MON get 403); topic moves to Chờ duyệt with that SV attached"
    requirement: "TOPC-02"
    verification:
      - kind: unit
        ref: "backend/tests/test_topic_registration.py — genuine RED confirmed by temporarily removing the /register router endpoint (both new tests failed 404), then restored to GREEN"
        status: pass
      - kind: integration
        ref: "curl through Apache: SV -> 404 on missing topic, GV -> 403 on same call"
        status: pass
      - kind: manual_procedural
        ref: "CDP session: DTC225200002 clicked 'Đăng ký' on MH-05, confirmed the Popconfirm, landed on /de-tai/5 with 'Chờ duyệt' + SV name shown — screenshot t2-02-after-register.png self-viewed"
        status: pass
    human_judgment: true
    rationale: "End-to-end registration UX (Popconfirm copy, success toast, redirect) in a real browser is a judgment call; self-performed via CDP, genuine user confirmation still pending."
  - id: D4
    description: "1 SV:1 active topic and 1 topic:1 SV hold under concurrent registration — the database (row lock + conditional UPDATE + uk_de_tai_sv_hoat_dong), not application code, decides the winner (TOPC-03, D-05, ROADMAP SC4)"
    requirement: "TOPC-03"
    verification:
      - kind: unit
        ref: "test_topic_registration.py::test_register_topic_race_one_winner_per_topic (5 iterations) and ::test_register_topic_race_one_active_topic_per_student (3 iterations) — both stable across 3 repeated full runs, no 1213/1205 deadlocks observed"
        status: pass
    human_judgment: false
  - id: D5
    description: "AUTH-03: role/ownership enforced server-side on the new list and register endpoints — filters cannot leak another user's pending topic; register rejects non-SV callers with 403"
    requirement: "AUTH-03"
    verification:
      - kind: unit
        ref: "test_topic_ownership.py scope assertions + curl 403-for-GV check above"
        status: pass
    human_judgment: false

duration: ~30min
completed: 2026-09-28
status: complete
---

# Phase 2 Plan 5: Danh sách đề tài (UC1.4) + Đăng ký đề tài có sẵn (UC1.2) Summary

**GET /api/topics with a server-side scope predicate built before any filter is applied (so a filter can never widen visibility), and POST /api/topics/{id}/register as a single conditional UPDATE that lets MySQL's row lock — not application code — decide exactly one winner when two students race for the same topic, or one student races for two topics.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-09-27T23:22:40Z (STATE.md, end of plan 02-04)
- **Completed:** 2026-09-28
- **Tasks:** 2/2 completed
- **Files modified:** 9 (2 created, 7 modified, across 2 commits)

## Accomplishments

- **Task 1 (UC1.4, TOPC-04, NFR-12):** `list_topics` builds the role's scope predicate FIRST (`_scope_predicate`) — BO_MON unrestricted; SV/GV see their own topics (any state) always, plus (only when `pham_vi=tat_ca`) the open `DA_DUYET`+no-SV pool — then ANDs `dot_do_an_id`/`trang_thai`/`giang_vien_id`/`linh_vuc`/`q` on top, so filters can narrow but never widen scope (T-02-29). `q` uses `autoescape=True` LIKE (T-02-32/33); `selectinload` on `dot_do_an`/`giang_vien`/`sinh_vien` avoids N+1; `sap_xep=ten` sorts under the DB's `utf8mb4_vietnamese_ci` collation. Extended `test_topic_ownership.py`'s existing SV-proposal test (no new test function, per D-03's "fewer tests" preference) to prove SV B never sees SV A's pending topic — even with an explicit `trang_thai=CHO_DUYET&pham_vi=tat_ca` filter — while BO_MON does. Frontend `TopicListPage.tsx` (MH-05): filter bar (Đợt đồ án/Trạng thái/Giảng viên hướng dẫn/Lĩnh vực/Tìm kiếm) + sortable/paginated table, every filter/page/pham_vi/sap_xep living in `useSearchParams` so menu clicks, reload and back/forward all keep the same view. `routes.tsx` repoints SV's "Đề xuất / Đăng ký đề tài" menu entry to the list page and adds "Đề tài của tôi" (SV)/"Đề tài hướng dẫn" (GV)/"Danh sách đề tài" (BO_MON) entries, following plan 02-04's documented shim-route convention.
- **Task 2 (UC1.2, TOPC-02/03, D-05, ROADMAP SC4, `tdd="true"`):** `register_topic` is ONE conditional `UPDATE de_tai SET sinh_vien_id=:sv, trang_thai='CHO_DUYET' WHERE id=:id AND sinh_vien_id IS NULL AND trang_thai='DA_DUYET' AND loai_nguoi_de_xuat='GIANG_VIEN' AND dot_do_an_id IN (SELECT id FROM dot_do_an WHERE trang_thai='DANG_MO')` — no read before the write. `IntegrityError` on `uk_de_tai_sv_hoat_dong` → 409 A1 ("Bạn đã có một đề tài đang hoạt động…"); `OperationalError` 1213/1205 → 409 retry message; `rowcount=0` triggers a re-read used ONLY to pick the right message (404 missing / 409 cohort closed / 409 E1 "Đề tài vừa được người khác đăng ký hoặc không còn trống") — the accept/reject decision itself was already final at the UPDATE. `TopicOut.quyen.dang_ky`/`TopicListItem.co_the_dang_ky` are computed via one extra `sinh_vien_id_dang_hoat_dong` lookup per request/page (not per row). `test_topic_registration.py`'s genuine RED was confirmed by temporarily removing the `/register` router endpoint (both new tests failed with 404), then restoring to GREEN — 5 iterations of Race A (fresh SV pair per topic) and 3 of Race B (fresh SV per pair of topics), stable across 3 repeated full runs with no deadlocks observed. Frontend: `useRegisterTopic()` + a "Đăng ký" `Popconfirm` button on MH-05 rows and the detail page, gated by `co_the_dang_ky`/`quyen.dang_ky`.
- **Both tasks' `<human-check>` items were self-performed** via a CDP-driven headless Chrome session (screenshots in the scratchpad — see Human-check section below).

## Task Commits

1. **Task 1: MH-05 topic list with server-side role scope** — `5c2e363` (feat)
2. **Task 2: SV registers open GV topic with DB-guaranteed one winner** — `d40d83c` (feat)

_Task 2 is `tdd="true"`; genuine RED was confirmed by temporarily removing the `/register` route (both new tests failed 404) and re-running pytest before restoring and committing GREEN, per its own commit message. Task 1 is plain `type="auto"`. The plan carries no checkpoints, so it ran to completion autonomously._

## Files Created/Modified

- `backend/app/schemas/topics.py` — `TopicListItem`, `TopicListParams` (Task 1); `QuyenOut.dang_ky`, `TopicListItem.co_the_dang_ky` (Task 2)
- `backend/app/services/topics.py` — `list_topics`, `_scope_predicate`, `_list_item_out`, `_person_refs` refactor (Task 1); `register_topic`, `_sv_has_active_topic`, `_can_register` (Task 2)
- `backend/app/routers/topics.py` — `GET /api/topics` (Task 1); `POST /api/topics/{id}/register` (Task 2)
- `backend/tests/test_topic_ownership.py` — extended scope assertions (Task 1)
- `backend/tests/test_topic_registration.py` (new) — the two concurrency tests (Task 2)
- `frontend/src/features/topics/TopicListPage.tsx` (new) — MH-05 (Task 1); Đăng ký action added (Task 2)
- `frontend/src/features/topics/routes.tsx` — menu restructure (Task 1)
- `frontend/src/features/topics/api.ts` — `TopicListItem`/`useTopics` (Task 1); `useRegisterTopic`, `quyen.dang_ky`/`co_the_dang_ky` types (Task 2)
- `frontend/src/features/topics/TopicDetailPage.tsx` — Đăng ký button (Task 2)

## Decisions Made

See `key-decisions` in frontmatter. Summary:
- `TopicListParams` stays a plain dataclass — FastAPI `Query()` already validates/coerces it, a second Pydantic layer would be redundant.
- The rowcount=0 re-read in `register_topic` only picks the error message; the UPDATE's WHERE clause already made the real decision atomically.
- New MH-05 sidebar entries follow the exact shim-route convention plan 02-04 documented for exactly this situation.

## Deviations from Plan

None — plan executed exactly as written. (The CDP driver script bugfix below was a self-verification tooling issue in the scratchpad, not a deviation in the shipped code.)

## Issues Encountered

- The scratchpad's ad-hoc CDP driver (`cdp.py`, written fresh this session) had a stray extra `}` in the generated JS for `click_selector`/`click_text`, which silently threw a JS syntax error inside `Runtime.evaluate` and was swallowed by the retry loop as a plain "selector not found" — cost some debugging time before being traced to the JS string construction. Fixed in the scratchpad tooling (not part of the shipped repo).
- The app's antd `ConfigProvider` locale is `vi_VN`, so `Popconfirm`'s default confirm button reads "Đồng ý" rather than "OK" — the first registration CDP attempt clicked the wrong button (re-opened the row's own "Đăng ký" button) until the script targeted `.ant-popconfirm-buttons` specifically.
- Demo-data topics created during CDP self-verification (ids 5 and 6, plus their `ket_qua_kiem_tra_trung_lap`/`chi_tiet_trung_lap` rows) were deleted afterward so they don't pollute the DATA-01 demo dataset; `de_tai` confirmed empty again before handoff, matching plan 02-04's established cleanup convention.

## Human-check (self-performed, pending user confirmation)

Per the autonomous-run instruction, self-performed both tasks' `<human-check>` via a CDP-driven headless Chrome session:

**Task 1** (`t1-01-sv-cua-toi.png` .. `t1-05-bomon-reload.png`): DTC225200001 clicked "Đề tài của tôi" (→ `/de-tai?pham_vi=cua_toi`, showed only her own topic) then "Đề xuất / Đăng ký đề tài" (→ `/de-tai`, full "Danh sách đề tài" with the MH-05 filter bar and columns); reload kept the same URL/filters. GV001 clicked "Đề tài hướng dẫn" (→ `/de-tai?pham_vi=cua_toi`). `bomon` opened "Danh sách đề tài", confirmed the Đợt đồ án dropdown listed the real seeded cohort, and reload preserved the view. Screenshot `t1-04-bomon-list.png` shows the table matching MH-05 columns/tags exactly (Tên đề tài, Lĩnh vực, Người đề xuất, GVHD, Sinh viên, Trạng thái, Hành động).

**Task 2** (`t2-01-list-with-dangky.png` .. `t2-03-second-sv-detail.png`): DTC225200002 (fresh SV, no active topic) saw the "Đăng ký" button on the open GV-proposed topic in MH-05, clicked it, confirmed the Popconfirm ("Đăng ký đề tài này?" / "Sau khi đăng ký, đề tài chuyển sang Chờ duyệt để Bộ môn xác nhận và phân công GVHD."), got the success toast "Đăng ký thành công — đề tài đang chờ Bộ môn duyệt", and landed on the detail page showing "Chờ duyệt" with her name under Sinh viên (`t2-02-after-register.png`). DTC225200003 then navigated directly to the same topic's detail URL and got a 403 `ForbiddenPage` (the topic left the public/open visibility rule the instant it was no longer `DA_DUYET`+no-SV) — confirmed no stale "Đăng ký" button is reachable by a second student.

**User confirmation of both checks is still pending** — flagged here per coverage items D1/D3.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Ready for plan 02-06 (UC1.3 Bộ môn duyệt/từ chối + phân công GVHD, which will read the same `DeTai`/`_to_out` extension points and presumably add the missing "approve"/"assign" transitions this plan's human-check had to simulate via `deploy/sql.sh`). `list_topics`/`register_topic`/`_can_register`/`_sv_has_active_topic` are the extension points 02-06 should reuse, not fork. No blockers.

---
*Phase: 02-platform-rbac-topic-management*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 2 new/referenced key files confirmed present on disk; both task commits (`5c2e363`, `d40d83c`) confirmed present in `git log --oneline --all`.
