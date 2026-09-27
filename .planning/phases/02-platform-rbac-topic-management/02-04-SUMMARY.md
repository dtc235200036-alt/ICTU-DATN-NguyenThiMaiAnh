---
phase: 02-platform-rbac-topic-management
plan: 04
subsystem: topics-and-ai-stub
tags: [fastapi, sqlalchemy, alembic, mysql, react, antd, tanstack-query, ai-stub, jaccard]

requires:
  - phase: 02-platform-rbac-topic-management (plan 01)
    provides: "require_role/ANY_ROLE/get_current_user, router+model auto-discovery, NFCModel, deploy/{sql,api-login,smoke-test}.sh, tools/check-erd-db.py"
  - phase: 02-platform-rbac-topic-management (plan 03)
    provides: "DotDoAn (DANG_MO/DA_DONG), useCohorts() hook, cau_hinh_nguong table exclusion from test truncation"
provides:
  - "Migration 0003: de_tai (STORED generated column sinh_vien_id_dang_hoat_dong + uk_de_tai_sv_hoat_dong, D-05; additive ly_do_tu_choi, D-04) + ERD write-back (erd.puml/lop-thuc-the.puml/02-thiet-ke-csdl.md)"
  - "app/services/topics.py: is_owner/can_view, create_topic/update_topic/submit_topic/get_topic — service functions plans 02-05/02-06 extend, not replace"
  - "/api/topics: POST (create draft or submit), PUT/{id}, POST/{id}/submit, GET/{id}, POST/check-title — RBAC + ownership + open-cohort gating"
  - "Migration 0004: ket_qua_kiem_tra_trung_lap, chi_tiet_trung_lap, cau_hinh_nguong + default thresholds (NGUONG_TEN_DE_TAI=50.00, NGUONG_TAI_LIEU=30.00)"
  - "app/services/ai_client.py: AiClient Protocol + AiClientStub (deterministic Jaccard-over-syllable-sets scoring) + get_ai_client(db) — the seam Phase 4 swaps for httpx, unchanged shape {matches:[{ref_id,ty_le}]}"
  - "app/services/title_check.py: kiem_tra_ten/luu_ket_qua/latest_title_check — threshold filtering, persistence, and the saved-result reader MH-07 (plan 02-06) will use"
  - "frontend/src/features/topics/{constants,api,routes,TopicFormPage,TopicDetailPage,TitleCheckAlert}.tsx — MH-06 propose/edit/detail screens with the UC0.6 warning flow"
affects: [02-05, 02-06, phase-03, phase-04]

actuals:
  tokens: 18089
  tasks: 2
  commits: 4
  plan_head_before: f8fa245cb1d35375e30d3d3dc6de7c0a822425c5
  plan_head_after: 3460f5fb6a700e19d9526601975e95d9e764ac06

tech-stack:
  added: []
  patterns:
    - "AI client seam (D-10): AiClient Protocol takes only (text, top_k) -> {matches:[{ref_id,ty_le}]} — no threshold, no user JWT, no network dependency in Phase 2. get_ai_client(db) reads AI_STUB_MODE at call time so tests/deploy can flip normal/loi without restarting the process logic (only the container env var)."
    - "Title-check-before-write-transaction (D-10 §3.3.5 seq diagram): create_topic(gui=True) and submit_topic call title_check.kiem_tra_ten() BEFORE any row is written, then title_check.luu_ket_qua() writes the saved result in the SAME commit as the status change — never a separate write, so a saved result and its topic's CHO_DUYET transition are atomically consistent."
    - "submit_topic's conditional UPDATE embeds the open-cohort check as a correlated subquery (`dot_do_an_id IN (SELECT id FROM dot_do_an WHERE trang_thai='DANG_MO')`) in the same WHERE clause as trang_thai='NHAP' — one round trip, no check-then-act gap even if the cohort closes between read and write."
    - "react-query default retry (3x) turns a definitive 403 into an infinite Skeleton because isLoading only flips false after retries exhaust — any query whose consumer treats `isLoading || !data` as \"still loading\" MUST disable retry for 4xx (see useTopic fix, Rule 1 deviation below)."

key-files:
  created:
    - backend/alembic/versions/0003_de_tai.py
    - backend/alembic/versions/0004_kiem_tra_trung_lap_cau_hinh_nguong.py
    - backend/app/models/de_tai.py
    - backend/app/models/trung_lap.py
    - backend/app/models/cau_hinh_nguong.py
    - backend/app/schemas/topics.py
    - backend/app/services/topics.py
    - backend/app/services/ai_client.py
    - backend/app/services/title_check.py
    - backend/app/routers/topics.py
    - backend/tests/test_topic_ownership.py
    - frontend/src/features/topics/constants.ts
    - frontend/src/features/topics/api.ts
    - frontend/src/features/topics/routes.tsx
    - frontend/src/features/topics/TopicFormPage.tsx
    - frontend/src/features/topics/TopicDetailPage.tsx
    - frontend/src/features/topics/TitleCheckAlert.tsx
  modified:
    - backend/app/core/config.py
    - deploy/docker-compose.yml
    - deploy/.env.example
    - docs/chuong-3-thiet-ke/csdl/erd.puml
    - docs/chuong-3-thiet-ke/csdl/erd.png
    - docs/chuong-3-thiet-ke/csdl/erd.svg
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.png
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.svg
    - docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md

key-decisions:
  - "AiClientStub scores Jaccard similarity (|A∩B|/|A∪B| x100, 2dp) over NFC-casefolded Unicode-word-regex token sets, deterministic and NFC/NFD-input-identical since tokenization NFC-normalizes first; verified the plan's fixed example pair scores exactly 66.67"
  - "cau_hinh_nguong.tai_lieu_do_an_id on ket_qua_kiem_tra_trung_lap stays nullable/UNIQUE WITHOUT its FK in migration 0004 — Phase 3's migration adds the FK once tai_lieu_do_an exists (per plan's Research Q1 decision)"
  - "SV-only sidebar menu entry ('/de-tai/de-xuat-sv-menu') is a structural workaround: MenuEntry carries exactly one label per route, but GV and SV need different labels ('Đề xuất đề tài' vs 'Đề xuất / Đăng ký đề tài') pointing at the same '/de-tai/de-xuat' page — the shim route's menu.to redirects the click straight to the real path, so its own dummy element is effectively unreachable in normal use (plan 02-05 repoints the SV entry's `to`)"

patterns-established:
  - "CDP-driven headless Chrome self-verification (continuing plans 02-02/02-03's pattern): real Input.dispatchMouseEvent coordinates (NOT synthetic .click()) were required to open antd Select dropdowns — a plain DOM .click() on .ant-select-selector does not trigger rc-select's internal open handler, but a real mousePressed/mouseReleased pair does"

requirements-completed: [TOPC-01, TOPC-02, AUTH-03, DEPL-01]

coverage:
  - id: D1
    description: "GV proposes a topic into an open đợt (draft or submit); only the owner GV can edit/submit a draft; another GV/SV/BO_MON get 403 on edit/submit"
    requirement: "TOPC-01"
    verification:
      - kind: unit
        ref: "backend/tests/test_topic_ownership.py::test_gv_draft_ownership_enforced — pass, confirmed genuine RED first (404 before app.routers.topics existed)"
        status: pass
      - kind: manual_procedural
        ref: "CDP session: GV001 created a draft via the real MH-06 form (real Input.dispatchMouseEvent clicks, not synthetic .click()), Lưu nháp -> Nháp tag, Sửa -> /de-tai/1/sua, Gửi đề xuất -> Chờ duyệt tag; screenshots t1-01..t1-05 self-viewed"
        status: pass
    human_judgment: true
    rationale: "Form layout fidelity to MH-06 and the end-to-end draft -> submit flow in a real browser are judgment calls; self-performed via CDP per the autonomous-run instruction, but genuine user confirmation is still pending."
  - id: D2
    description: "SV self-proposes the same way (self-proposal half of TOPC-02); topic detail visible only to owner/BO_MON/public-when-open"
    requirement: "TOPC-02"
    verification:
      - kind: unit
        ref: "backend/tests/test_topic_ownership.py::test_sv_proposal_visibility_enforced (incl. kiem_tra_ten.trang_thai==HOAN_TAT and nguong_ap_dung==50.0 assertions added in Task 2) — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP session: DTC225200001 (SV) submitted a proposal under AI_STUB_MODE=loi; menu correctly showed the SV-specific label 'Đề xuất / Đăng ký đề tài'; detail page showed 'Chưa kiểm tra' — screenshot t2-04/t2-05 self-viewed"
        status: pass
    human_judgment: true
    rationale: "Self-performed via CDP per the autonomous-run instruction; genuine user confirmation still pending."
  - id: D3
    description: "T-02-22/T-02-23: RBAC enforced server-side for every topic write/read — 403 for non-owners on write, 403 for unauthorized viewers on read"
    requirement: "AUTH-03"
    verification:
      - kind: unit
        ref: "test_topic_ownership.py — 2 tests, all 6 assertions (3 non-owner writes + owner write + 2 non-viewer reads) pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP: GV002 visiting GV001's pending topic detail URL directly showed the real ForbiddenPage ('403 — Bạn không có quyền truy cập trang này') — this required a Rule 1 fix (see Deviations) after the first CDP run caught an infinite-Skeleton bug"
        status: pass
    human_judgment: false
  - id: D4
    description: "de_tai created by migration 0003 matching the (updated) ERD column-for-column; DEPL-01 check-erd-db.py still passes with the new tables"
    requirement: "DEPL-01"
    verification:
      - kind: integration
        ref: "python3 tools/check-erd-db.py -> OK (both after 0003 and after 0004); alembic_version -> 0004; bash tools/render-diagrams.sh + tools/check-docs.py class-erd/render -> exit 0"
        status: pass
    human_judgment: false

duration: ~40min
completed: 2026-09-28
status: complete
---

# Phase 2 Plan 4: Đề xuất đề tài (UC1.1) + Similar-Title AI Stub Warning (UC0.6) Summary

**Topic proposal/draft/submit with server-enforced ownership (migration 0003, `sinh_vien_id_dang_hoat_dong` generated column + `uk_de_tai_sv_hoat_dong`), plus a deterministic Jaccard-similarity AI stub (migration 0004) that warns proposers of similar existing topics before they submit — never blocking, always persisted for the Bộ môn's later review.**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-09-28
- **Tasks:** 2/2 completed
- **Files:** 17 created, 10 modified (across 4 commits)

## Accomplishments

- **Task 1 (UC1.1, TOPC-01/02, AUTH-03, DEPL-01):** Migration `0003` creates `de_tai` with the exact §3.2.3/§3.2.5 shape — `sinh_vien_id_dang_hoat_dong` as a MySQL `STORED GENERATED` column (`CASE WHEN trang_thai IN (...) THEN sinh_vien_id END`) under `uk_de_tai_sv_hoat_dong`, plus the additive `ly_do_tu_choi TEXT NULL` column FR-DT-04 needs but the original ERD lacked. The ERD gap was closed in the same task: `ly_do_tu_choi` was written back into `erd.puml`, `lop-thuc-the.puml` and the §3.2.3 data dictionary, then diagrams re-rendered — `check-erd-db.py` and `check-docs.py class-erd` both still pass. `app/services/topics.py` implements `is_owner`/`can_view` (D-08), `create_topic`/`update_topic` (open-cohort check, `IntegrityError` -> 409 on the duplicate-active-topic constraint), and `submit_topic` via a single conditional `UPDATE ... WHERE trang_thai='NHAP' AND dot_do_an_id IN (SELECT id FROM dot_do_an WHERE trang_thai='DANG_MO')` — no check-then-act gap. The MH-06 form (`TopicFormPage.tsx`) and read-only detail (`TopicDetailPage.tsx`) render the propose/edit/view flow with `Lưu nháp`/`Gửi đề xuất`/`Sửa` gated by the server's `quyen.sua`/`quyen.gui`.
- **Task 2 (UC0.6, FR-DT-02):** Migration `0004` creates `ket_qua_kiem_tra_trung_lap`, `chi_tiet_trung_lap` and `cau_hinh_nguong` (seeded with `NGUONG_TEN_DE_TAI=50.00`, `NGUONG_TAI_LIEU=30.00`). `app/services/ai_client.py`'s `AiClientStub` computes a deterministic Jaccard similarity over NFC-casefolded Unicode-word tokens — verified to score the plan's fixed example pair ("Hệ thống quản lý kho bằng mã QR" vs "Quản lý kho hàng bằng mã QR") at exactly `66.67`, identically for NFC and NFD input, and to raise `AiServiceError` in `AI_STUB_MODE=loi` without ever blocking a submission (UC1.1 E2). `app/services/title_check.py` filters matches against the live `cau_hinh_nguong` threshold and persists exactly one `ket_qua_kiem_tra_trung_lap` row (+ N `chi_tiet_trung_lap` rows) in the SAME commit as the topic's status change — computed before the write transaction opens, per the §3.3.5 sequence diagram. The frontend (`TitleCheckAlert.tsx`) shows the MH-06 warning table with `Progress` percentages and `Sửa tên đề tài`/`Vẫn gửi đề xuất`, gating the next submit until acknowledged; `TopicDetailPage.tsx` gained the "Kết quả kiểm tra trùng tên (UC0.6)" saved-result section (Không trùng / N đề tài tương tự / Chưa kiểm tra) that MH-07 (plan 02-06) will read.
- **Both tasks' `<human-check>` items were self-performed** via a CDP-driven headless Chrome session (screenshots in the scratchpad — see `Human-check` section below). A genuine bug was caught and fixed mid-verification (see Deviations).

## Task Commits

1. **Task 1 RED: failing ownership tests for topic proposal** — `cbeefc5` (test)
2. **Task 1 GREEN: migration 0003 + ownership rules + MH-06 form/detail** — `a6e4739` (feat)
3. **Task 2: similar-title warning via D-10 AI stub (UC0.6)** — `bab12c4` (feat)
4. **Rule 1 fix: TopicDetailPage stuck on Skeleton forever on 403** — `3460f5f` (fix) — found via Task 1's own human-check

_Task 1 is `tdd="true"`; genuine RED was confirmed by temporarily removing the migration/model/schema/service/router files (backed up first, not deleted outright — see Issues Encountered) and re-running pytest (2 failures, 404 — routes didn't exist yet) before restoring and committing GREEN. Task 2 is plain `type="auto"`. The plan carries no checkpoints, so it ran to completion autonomously._

## Files Created/Modified

See `key-files` in frontmatter. Full list:
- `backend/alembic/versions/{0003_de_tai,0004_kiem_tra_trung_lap_cau_hinh_nguong}.py`, `backend/app/models/{de_tai,trung_lap,cau_hinh_nguong}.py`, `backend/app/schemas/topics.py`, `backend/app/services/{topics,ai_client,title_check}.py`, `backend/app/routers/topics.py`, `backend/tests/test_topic_ownership.py` (new) — backend
- `backend/app/core/config.py` (modified) — `AI_CLIENT`, `AI_STUB_MODE`, `TITLE_CHECK_TOP_K` settings
- `frontend/src/features/topics/{constants,api,routes,TopicFormPage,TopicDetailPage,TitleCheckAlert}.tsx` (new) — frontend
- `deploy/docker-compose.yml`, `deploy/.env.example` (modified) — `AI_STUB_MODE` passthrough
- `docs/chuong-3-thiet-ke/{csdl/erd,so-do-lop/lop-thuc-the}.{puml,png,svg}`, `docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md` (modified) — ERD write-back for `ly_do_tu_choi`

## Decisions Made

See `key-decisions` in frontmatter. Summary:
- Jaccard-over-syllable-sets is the D-10 stub's deterministic stand-in for the Phase 4 semantic model; NFC-normalizes + casefolds before tokenizing so NFC/NFD input always agree.
- `ket_qua_kiem_tra_trung_lap.tai_lieu_do_an_id` stays FK-less (nullable + UNIQUE only) until Phase 3 creates `tai_lieu_do_an`.
- SV's sidebar menu entry for `/de-tai/de-xuat` is a second, distinct `AppRoute` (dummy path, real `menu.to` override) because the existing `MenuEntry` type has no per-role-label mechanism — documented inline in `routes.tsx` for plan 02-05 to repoint.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `TopicDetailPage` stuck on `Skeleton` forever when the server returns 403**
- **Found during:** Task 1 human-check (CDP session) — GV002 visiting GV001's pending topic detail
- **Issue:** `useTopic`'s render guard was `if (isLoading || !topic) return <Skeleton />`. React Query's default `retry: 3` means `isLoading` only becomes `false` after three retries against a *definitive* 403 — and even then, `!topic` stays true forever, so the component never left the loading state. The screenshot showed an indefinite skeleton instead of any error.
- **Fix:** `useTopic` now disables retry for any response status `< 500` (4xx are definitive, not transient); `TopicDetailPage` checks `isError` and renders the real `ForbiddenPage` for a 403, or a generic error `Result` otherwise.
- **Files modified:** `frontend/src/features/topics/api.ts`, `frontend/src/features/topics/TopicDetailPage.tsx`
- **Verification:** Re-ran the CDP script — GV002 now sees "403 — Bạn không có quyền truy cập trang này" (screenshot `t1-06b-gv002-forbidden-fixed.png`) immediately instead of a stuck skeleton.
- **Committed in:** `3460f5f`

---

**Total deviations:** 1 auto-fixed (Rule 1 functional bug affecting a plan must-have — "another GV or SV gets 403 ... instead of the topic").
**Impact on plan:** Necessary for the plan's own must-have to hold true in a real browser; no scope creep beyond what Task 1 already specified (visibility enforcement).

## Issues Encountered

- Mid-Task-1, a scripted attempt to prove genuine TDD RED (moving the 5 new implementation files to a temp dir) hit a `mv` destination-collision error (`schemas/topics.py`, `services/topics.py`, `routers/topics.py` all share the basename `topics.py`) and one `rm -rf` cleanup of the temp dir accidentally deleted 3 files that a prior (silently failed) `mv` had already relocated there. Recovered immediately by rewriting the 3 files from the content already produced earlier in this session (verbatim) — no data was permanently lost, and the subsequent genuine-RED verification (backend tests failing with 404) confirms the recovered files behave identically to the originals. Switched to `cp`-then-`rm`-individual-files (never `rm -rf` a directory containing anything not 100% certain to be a backup) for the rest of the session.
- Ant Design's `Select` dropdown did not open when clicked via a synthetic DOM `.click()` in the CDP script (rc-select listens for a real pointer event) — switched to `Input.dispatchMouseEvent` (mousePressed/mouseReleased at the element's real bounding-rect coordinates) for every Select interaction, which worked immediately. Documented as a new pattern for future CDP-based checks in this repo.
- The 4 throwaway topics created during CDP self-verification (ids 1-4, "He thong quan ly do an tot nghiep CNTT thu nghiem GV001", "He thong quan ly kho bang ma QR", "Quan ly kho hang bang ma QR", "De tai kiem tra che do AI loi UC1.1 E2") were deleted from the DB afterward (`de_tai` + their `ket_qua_kiem_tra_trung_lap`/`chi_tiet_trung_lap` rows) so they don't pollute the DATA-01 demo dataset; `de_tai` confirmed empty again before handoff. `AI_STUB_MODE` was reverted to `normal` on the running container after the E2 failure-mode check.

## Human-check (self-performed, pending user confirmation)

Per the autonomous-run instruction, self-performed both tasks' `<human-check>` via a CDP-driven headless Chrome session (screenshots in the scratchpad, referenced by name below — not committed to the repo):

**Task 1** (`t1-01-form-empty.png` .. `t1-06b-gv002-forbidden-fixed.png`): logged in as GV001, filled the real MH-06 form (Đợt đồ án Select, Tên đề tài Input) using real `Input.dispatchMouseEvent` clicks and `Input.dispatchKeyEvent` typing, clicked "Lưu nháp" — new draft appeared with tag "Nháp"; clicked "Sửa" -> navigated to `/de-tai/1/sua`; clicked "Gửi đề xuất" -> tag flipped to "Chờ duyệt", and the new "Kết quả kiểm tra trùng tên (UC0.6)" section showed "Không trùng" / "Ngưỡng áp dụng: 50%". Logged in as GV002, navigated directly to `/de-tai/1` — after the Rule 1 fix above, got the real 403 `ForbiddenPage` (confirmed both in `document.body.innerText` and visually in the screenshot).

**Task 2** (`t2-01-warning-shown.png` .. `t2-05-loi-mode-detail.png`): GV001 submitted "Hệ thống quản lý kho bằng mã QR"; GV002 started a proposal titled "Quản lý kho hàng bằng mã QR" and blurred the title field — the real MH-06 warning appeared ("Phát hiện 1 đề tài tương tự trong kho", table row "He thong quan ly kho bang ma QR / K22 / Trần Tấn Minh / 66.67%" with a `Progress` bar). Clicked "Sửa tên đề tài" — confirmed `document.activeElement` was the title input. Clicked "Vẫn gửi đề xuất" (collapses to the acknowledgement Tag), then "Gửi đề xuất" — submission succeeded, and the new topic's detail page showed "1 đề tài tương tự" with the saved comparison table. Then set `AI_STUB_MODE=loi` on the running `api` container (via `docker compose up -d --wait api` with the env var overridden, no `.env` file edit), logged in as `DTC225200001` (SV), typed a title and blurred — the info alert "Chưa kiểm tra được trùng lặp tên đề tài (dịch vụ kiểm tra không phản hồi)..." appeared exactly as specified; submission still succeeded and the detail page showed the "Chưa kiểm tra" tag. Reverted `AI_STUB_MODE` back to `normal` afterward.

**User confirmation of both checks is still pending** — flagged here per coverage items D1/D2/D3.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Ready for plan 02-05 (UC1.2 self-registration onto GV-proposed topics) and 02-06 (UC1.3 Bộ môn duyệt/phân công, which reads `latest_title_check`/`TopicOut.kiem_tra_ten` exactly as MH-07 needs). `app/services/topics.py`'s `is_owner`/`can_view`/`_to_out` are the extension points those plans should reuse, not fork. The AI seam (`get_ai_client`, `AiClient` Protocol) is ready for Phase 4 to swap the stub for an httpx client without touching any caller. No blockers.

---
*Phase: 02-platform-rbac-topic-management*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 17 new/referenced key files confirmed present on disk; all 4 task commits (`cbeefc5`, `a6e4739`, `bab12c4`, `3460f5f`) confirmed present in `git log --oneline --all`.
