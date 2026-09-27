---
phase: 02-platform-rbac-topic-management
plan: 03
subsystem: cohorts-and-seed
tags: [fastapi, sqlalchemy, alembic, mysql, react, antd, tanstack-query, faker, rbac]

requires:
  - phase: 02-platform-rbac-topic-management (plan 01)
    provides: "require_role/ANY_ROLE/get_current_user, router+model auto-discovery, NFCModel, hash_password, deploy/{sql,api-login,smoke-test}.sh, tools/check-erd-db.py"
  - phase: 02-platform-rbac-topic-management (plan 02)
    provides: "AppLayout/RequireAuth/AuthBootstrap shell, frontend route registry conventions, getErrorMessage/api client"
provides:
  - "Migration 0002 + app/models/dot_do_an.py (DotDoAn, DANG_MO/DA_DONG) — dot_do_an table exactly per erd.puml, CHECK constraint + index on trang_thai"
  - "/api/cohorts: GET for any authenticated role; POST/PUT/{id}/open/{id}/close require_role(BO_MON); 404 on unknown id; open/close idempotent"
  - "frontend/src/features/cohorts/{api.ts,CohortsPage.tsx,routes.tsx} — useCohorts/useCreateCohort/useUpdateCohort/useSetCohortState hooks (exported for plans 02-04/02-05) + Quản lý đợt đồ án screen at /dot-do-an (BO_MON menu order 20)"
  - "backend/tests/test_cohorts_rbac.py — 403 coverage (2 roles x 4 write endpoints) + any-role GET coverage"
  - "app/seed.py: idempotent DATA-01 population — 100 SV (DTC225200001..100), 30 GV (GV001..030), 1 Bộ môn, one open đợt đồ án; Faker(vi_VN) fixed-seed name generation"
  - "deploy/README.md: Tài khoản demo table (all 3 roles, shared dev password, re-run command, open-cohort note)"
  - "fix: frontend getErrorMessage() now surfaces FastAPI/Pydantic 422 validator messages (was silently falling back to a generic error for any non-string `detail`, e.g. model_validator ValueError — affects every schema in the app, not just cohorts)"
affects: [02-04, 02-05, 02-06, phase-03, phase-04]

actuals:
  tokens: 8158
  tasks: 2
  commits: 4
  plan_head_before: b280987
  plan_head_after: ab75585

tech-stack:
  added: []
  patterns:
    - "Router with mixed role requirements per route (unlike accounts.py's uniform BO_MON-only router-level dependency): cohorts.py declares require_role(*ANY_ROLE) on GET and require_role(VaiTro.BO_MON) individually on POST/PUT/open/close, since one router-level dependency can't express both permission levels"
    - "Faker(vi_VN) name generation built from individual last_name()/middle_name()/first_name_{male,female}() provider calls composed in Vietnamese Họ+đệm+Tên order, never .name() (mixes Western order + occasional Ông/Bà prefix) or any address-style provider (leaks the English token 'John' per 02-RESEARCH.md Pitfall 5) — asserted >=2 words and no ASCII leak token per generated name"
    - "Seed idempotency keyed by natural business key (ma_dang_nhap for accounts, ten_dot for the cohort) checked before any Faker call — on rerun, no Faker calls happen at all for already-seeded rows, so existing profile names/emails are never touched, only genuinely-missing rows are created"
    - "One hash_password() call per seed run, reused for every newly-created account in that run (bcrypt cost 12 on ~130 accounts individually would cost ~30s; existing accounts keep their existing hash across reruns)"

key-files:
  created:
    - backend/alembic/versions/0002_dot_do_an.py
    - backend/app/models/dot_do_an.py
    - backend/app/schemas/cohorts.py
    - backend/app/routers/cohorts.py
    - backend/tests/test_cohorts_rbac.py
    - frontend/src/features/cohorts/api.ts
    - frontend/src/features/cohorts/CohortsPage.tsx
    - frontend/src/features/cohorts/routes.tsx
  modified:
    - backend/app/seed.py
    - deploy/README.md
    - frontend/src/api/client.ts

key-decisions:
  - "Migration 0002's revision-id variables (revision/down_revision/branch_labels/depends_on) were written WITHOUT the typing.Union type hints that 0001 uses, to satisfy the plan's own literal acceptance-criteria grep (`down_revision = \"0001\"`) — Alembic reads these as plain module globals regardless of type hints, so this is a zero-functional-cost stylistic deviation from 0001, not a behavior change"
  - "A code comment in app/seed.py explaining why Faker's address-style provider is avoided was reworded to not contain the literal substring 'address(' after tripping the plan's own `grep -c 'address(' backend/app/seed.py` acceptance gate — same class of grep-vs-comment false positive as plan 02-02's localStorage/sessionStorage incident, fixed the same way (reword, no functional change)"
  - "getErrorMessage() in frontend/src/api/client.ts fixed to handle FastAPI/Pydantic's list-of-{type,loc,msg} 422 detail shape (previously only handled a plain string detail from HTTPException) — found via this plan's own human-check requirement that the end-before-start date validator surface its Vietnamese message in the UI; classified as Rule 1 (bug fix), scope is app-wide (every schema's validator errors), not cohort-specific"

patterns-established:
  - "CDP-driven headless Chrome self-verification (continuing the pattern from plan 02-02): raw Python + websockets against Chrome DevTools Protocol, used to prove both this plan's <human-check> items end-to-end (create/close/reopen a cohort through the real Modal/Popconfirm, and search the seeded SV list by Vietnamese surname) since Playwright/Puppeteer remain uninstalled on this machine"

requirements-completed: [AUTH-04, AUTH-03, DATA-01, DEPL-01]

coverage:
  - id: D1
    description: "Bộ môn opens a đợt đồ án for a khóa (created DANG_MO), edits it, closes it (DA_DONG) and reopens it from Quản lý đợt đồ án; every authenticated role can list cohorts"
    requirement: "AUTH-04"
    verification:
      - kind: integration
        ref: "Task 1 <automated> verify: alembic head 0002, check-erd-db.py OK, GET /api/cohorts 200 for bomon through Apache — pass"
      - kind: manual_procedural
        ref: "CDP session: created 'Đợt thử nghiệm K23' through the real Modal, cycle Đang mở -> Đã đóng -> Đang mở via Popconfirm on the real Table row; screenshots cohort3-after-create.png/cohort4-after-close.png/cohort5-after-reopen.png self-viewed"
        status: pass
    human_judgment: true
    rationale: "Form UX, date display (DD/MM/YYYY), and Popconfirm wording fidelity are judgment calls; self-performed via CDP per the autonomous-run instruction, but genuine user confirmation is still pending."
  - id: D2
    description: "SV and GV tokens get 403 from the server on POST/PUT/open/close of /api/cohorts, and the cohort row is unchanged"
    requirement: "AUTH-03"
    verification:
      - kind: unit
        ref: "backend/tests/test_cohorts_rbac.py::test_non_bomon_gets_403_on_every_cohort_write (2 roles x 4 endpoints = 8 cases) — pass, confirmed genuine RED first (ModuleNotFoundError before app.models.dot_do_an existed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "table dot_do_an is created only by Alembic revision 0002 with exactly the §3.2.3 columns and utf8mb4_vietnamese_ci; tools/check-erd-db.py still passes"
    requirement: "DEPL-01"
    verification:
      - kind: integration
        ref: "python3 tools/check-erd-db.py -> OK; bash deploy/sql.sh \"SELECT version_num FROM alembic_version\" -> 0002 — pass"
        status: pass
    human_judgment: false
  - id: D4
    description: "python -m app.seed is idempotent and leaves exactly 100 SV, 30 GV, 1 Bộ môn and at least one open cohort, Vietnamese Faker names NFC + bcrypt cost 12; every seeded account logs in with mã or email and the documented dev password; Vietnamese collation verified on the live schema"
    requirement: "DATA-01"
    verification:
      - kind: integration
        ref: "Ran seed 2x explicitly (both printed 0 new) + once more via container restart (SEED_ON_START) — SV=100, GV=30, BO_MON=1, open cohorts=1, non-bcrypt-$2b$12$ hashes=0, total tai_khoan=131 (stable across all 3 runs)"
        status: pass
      - kind: integration
        ref: "bash deploy/api-login.sh DTC225200001 and gv030@ictu.edu.vn both succeed through Apache HTTPS; STRCMP('Đặng','Dương' COLLATE utf8mb4_vietnamese_ci)=1 (Đ after D) on live schema"
        status: pass
      - kind: integration
        ref: "docker exec python check: 130 profile names all unicodedata.is_normalized('NFC'), >=2 words, no 'John' substring — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP session as bomon: Sinh viên tab lists 100 rows with correct diacritics, sorted alphabetically; searched 'Nguyễn' -> 10 matching rows, all real Vietnamese given-name combinations; Giảng viên tab shows 30 GV rows; logged in as DTC225200001 via fetch, GET /auth/refresh confirms vai_tro=SINH_VIEN; screenshots seed1-sv-list.png/seed2b-search-retry.png/seed3-gv-list.png self-viewed"
        status: pass
    human_judgment: true
    rationale: "Vietnamese diacritic rendering/collation-ordering fidelity in the real UI is a judgment call; self-performed via CDP per the autonomous-run instruction, but genuine user confirmation is still pending."

duration: ~45min
completed: 2026-09-28
status: complete
---

# Phase 2 Plan 3: Đợt đồ án (UC0.3) + DATA-01 Seed Population Summary

**Migration 0002 + role-gated `/api/cohorts` API + Quản lý đợt đồ án screen (Bộ môn opens/closes đợt theo khóa, RBAC-enforced server-side), plus an idempotent Faker(vi_VN)-driven seed of 100 SV / 30 GV / 1 Bộ môn / 1 open cohort with documented demo credentials.**

## Performance

- **Duration:** ~45 min
- **Completed:** 2026-09-28
- **Tasks:** 2/2 completed
- **Files:** 8 created, 3 modified (across 4 commits)

## Accomplishments

- **Task 1 (UC0.3, AUTH-04/AUTH-03/DEPL-01):** Migration `0002` creates `dot_do_an` with exactly the §3.2.3 columns (`id`, `ten_dot`, `khoa`, `nam_hoc`, `ngay_bat_dau`, `ngay_ket_thuc`, `trang_thai`), a `ck_dot_do_an_trang_thai` CHECK constraint, an index on `trang_thai`, and `utf8mb4_vietnamese_ci` — `tools/check-erd-db.py` confirms an exact column-name match against `erd.puml`. `app/models/dot_do_an.py` mirrors it with `DANG_MO`/`DA_DONG` constants. `/api/cohorts` lets any authenticated role `GET` (list, optional `trang_thai`/`khoa` filters, newest-first) while `POST`/`PUT`/`{id}/open`/`{id}/close` each independently declare `require_role(VaiTro.BO_MON)` (a router-level dependency wasn't possible here since GET needs a different role set than the writes, unlike `accounts.py`). Unknown ids 404 with a Vietnamese message; open/close are idempotent. `CohortCreate`/`CohortUpdate` validate `khoa` (`^K\d{2}$`), `nam_hoc` (`^\d{4}-\d{4}$`), and reject an end date before the start date via a `model_validator`. The frontend `Quản lý đợt đồ án` screen (`/dot-do-an`, BO_MON-only, menu order 20) renders the full UC0.3 flow: Table with Đang mở/Đã đóng tags and DD/MM/YYYY dates, create/edit Modal, and a Popconfirm on close that warns closing blocks new topic proposals/registrations.
- **Task 2 (DATA-01):** `app/seed.py` was rewritten to add the full demo population on top of the existing Bộ môn bootstrap: `GV001`..`GV030` and `DTC225200001`..`DTC225200100`, each with a Faker(`vi_VN`)-generated Vietnamese name built from individual `last_name()`/`middle_name()`/`first_name_{male,female}()` provider calls (never `.name()` or any address-style provider — see Pitfall 5 in `02-RESEARCH.md`), NFC-normalized and asserted to have ≥2 words and no ASCII leak token. A single `hash_password(SEED_DEFAULT_PASSWORD)` call is reused for every newly-created account per run. One open cohort ("Đợt đồ án tốt nghiệp K22 - HK1 (2026-2027)", khóa K22) is created if missing, never touched if it already exists. `deploy/README.md` gained a `Tài khoản demo` table covering all three roles, the shared dev password, the manual re-run command, and a Phase-5 password-change warning.
- **Both tasks' `<human-check>` items were self-performed** via a CDP-driven headless Chrome session (screenshots in the scratchpad — see `Human-check` section below), proving: creating "Đợt thử nghiệm K23" through the real Modal → close → reopen cycle with correct Popconfirm/date-display behavior; and the Sinh viên/Giảng viên account lists with correct diacritics and a working "Nguyễn" surname search (10 matching rows) plus a real SV login.

## Task Commits

1. **Task 1 RED: failing RBAC tests for /api/cohorts** — `d679825` (test)
2. **Task 1 GREEN: migration 0002 + /api/cohorts + Quản lý đợt đồ án screen** — `34e0ea3` (feat)
3. **Rule 1 fix: getErrorMessage() 422 validation messages** — `f75f3b3` (fix) — found via Task 1's own human-check
4. **Task 2: DATA-01 seed population + README** — `ab75585` (feat)

_Task 1 is `tdd="true"`; a genuine RED state was confirmed by temporarily removing the migration/model/schema/router files and re-running pytest (collection failed with `ModuleNotFoundError: app.models.dot_do_an`) before restoring them and committing GREEN. Task 2 is plain `type="auto"`. The plan carries no checkpoints, so it ran to completion autonomously._

## Files Created/Modified

See `key-files` in frontmatter. Full list:
- `backend/alembic/versions/0002_dot_do_an.py`, `backend/app/models/dot_do_an.py`, `backend/app/schemas/cohorts.py`, `backend/app/routers/cohorts.py`, `backend/tests/test_cohorts_rbac.py` (new) — Task 1 backend
- `frontend/src/features/cohorts/{api.ts,CohortsPage.tsx,routes.tsx}` (new) — Task 1 frontend
- `frontend/src/api/client.ts` (modified) — Rule 1 fix
- `backend/app/seed.py`, `deploy/README.md` (modified) — Task 2

## Decisions Made

See `key-decisions` in frontmatter. Summary:
- Dropped `typing.Union` type hints on migration 0002's revision-id variables to satisfy the plan's own literal grep acceptance criterion — purely cosmetic, Alembic doesn't care about type hints on these globals.
- Reworded a code comment in `seed.py` that literally contained the substring `address(` (explaining why Faker's address-style provider is avoided), which tripped the plan's own `grep -c 'address(' backend/app/seed.py` gate — same class of issue as plan 02-02's `localStorage`/`sessionStorage` comment incident.
- Fixed `getErrorMessage()` to parse FastAPI/Pydantic's list-shaped 422 `detail` — an app-wide bug (not cohort-specific) that would have silently swallowed every Pydantic validator's Vietnamese error message across the whole app; found because this plan's own human-check required the date-order validator's message to actually render.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `getErrorMessage()` didn't handle FastAPI/Pydantic's list-shaped 422 `detail`**
- **Found during:** Task 1 human-check (CDP session), submitting an end-date-before-start-date cohort
- **Issue:** `model_validator`-raised `ValueError`s produce `detail: [{type, loc, msg, ...}]`, not a plain string; `getErrorMessage()` only handled `typeof detail === 'string'` and silently fell back to the generic "Đã xảy ra lỗi..." message, hiding the Vietnamese validation message the plan's must-haves require to be visible.
- **Fix:** `getErrorMessage()` now detects the Pydantic error-list shape, extracts each `msg`, strips the `"Value error, "` prefix Pydantic v2 adds for custom validator messages, and joins them.
- **Files modified:** `frontend/src/api/client.ts`
- **Verification:** Re-ran the CDP script — `HAS_VN_DATE_ERROR_MESSAGE: True`, screenshot `cohort2-bad-date-error.png` shows the toast "Ngày kết thúc phải sau ngày bắt đầu".
- **Committed in:** `f75f3b3`

**2. [Rule 1 - Bug] Plan's own acceptance-criteria grep conflicted with the established typed-migration style**
- **Found during:** Task 1, running the plan's `<acceptance_criteria>` checks after committing
- **Issue:** `grep -q 'down_revision = "0001"'` requires an untyped assignment, but migration 0001 (and my first draft of 0002, matching its style) uses `down_revision: Union[str, None] = "0001"` — the type-annotated substring never matches the untyped grep pattern regardless of quoting.
- **Fix:** Removed the `Union` type hints from 0002's four revision-id variables (functionally identical to Alembic, which only reads them as plain module globals).
- **Files modified:** `backend/alembic/versions/0002_dot_do_an.py`
- **Verification:** `grep -q 'down_revision = "0001"' backend/alembic/versions/0002_dot_do_an.py` exits 0; full pytest suite + `check-erd-db.py` still pass after the change.
- **Committed in:** `34e0ea3`

**3. [Rule 1 - Bug] Comment text in `seed.py` tripped the plan's own `address(` grep gate**
- **Found during:** Task 2, running the plan's `<acceptance_criteria>` checks
- **Issue:** A docstring comment explaining why Faker's address-style provider is avoided literally contained `.address()`, which `grep -c 'address(' backend/app/seed.py` (correctly, per its literal spec) counted as 1, not 0 — same class of comment-vs-code false positive as plan 02-02's `localStorage`/`sessionStorage` incident.
- **Fix:** Reworded the comment to describe the provider without using the literal method-call substring.
- **Files modified:** `backend/app/seed.py`
- **Verification:** `grep -c 'address(' backend/app/seed.py` → `0`.
- **Committed in:** `ab75585` (folded into Task 2's commit, written before first commit of the file)

---

**Total deviations:** 3 auto-fixed (1× Rule 1 functional bug affecting a plan must-have, 2× Rule 1 grep-gate-vs-style/comment false positives, zero functional cost).
**Impact on plan:** All three were necessary for the plan's own must-haves/acceptance criteria to hold true end-to-end; no scope creep beyond what Task 1/2 already specified.

## Issues Encountered

- First CDP script attempt for the cohort close/reopen Popconfirm accidentally clicked the wrong button in a search-input helper (see below) — resolved by using a more direct placeholder-based selector and a real `Enter` keydown event instead of guessing at the antd `Input.Search` button DOM structure.
- The two throwaway "Đợt thử nghiệm K23" cohorts created during Task 1's CDP verification were deleted from the DB afterward (`DELETE FROM dot_do_an WHERE id IN (1,2)`) so they don't pollute the DATA-01 demo dataset — confirmed `dot_do_an` was empty again before Task 2's seed ran.
- `deploy/init.sh`/Docker Compose stack (`ntma-{mysql,api,apache}-1`) was already running from the previous session (02-02); rebuilt (`--build --wait`) at each code change point (Task 1 migration, `client.ts` fix, `seed.py` fix) rather than a single rebuild at the end, so every automated/manual check ran against the actual code being verified.

## Human-check (self-performed, pending user confirmation)

Per the autonomous-run instruction, self-performed both tasks' `<human-check>` via a CDP-driven headless Chrome session (screenshots in the scratchpad, referenced by name below — not committed to the repo):

**Task 1** (`cohort2-bad-date-error.png`, `cohort3-after-create.png`, `cohort4-after-close.png`, `cohort5-after-reopen.png`): logged in as `bomon`, opened `/dot-do-an`, clicked the real "Mở đợt mới" button, filled the real antd Modal Form (native-value-setter + `input`/`change` event dispatch) with an intentionally-invalid end-date-before-start-date — got the Vietnamese toast "Ngày kết thúc phải sau ngày bắt đầu" (after the `getErrorMessage` fix above). Fixed the end date and resubmitted — the new row appeared with dates displayed as `28/09/2026`/`30/06/2027` (DD/MM/YYYY) and a blue "Đang mở" tag. Clicked "Đóng đợt" on the real Table row, confirmed the real Popconfirm — tag flipped to "Đã đóng". Clicked "Mở lại", confirmed — tag flipped back to "Đang mở".
- Throwaway rows deleted from the DB afterward (see Issues Encountered).

**Task 2** (`seed1-sv-list.png`, `seed2b-search-retry.png`, `seed3-gv-list.png`): as `bomon`, opened `/tai-khoan`, the Sinh viên tab listed the seeded 100 rows with correct Vietnamese diacritics; typed "Nguyễn" into the real `Input.Search` and pressed Enter — 10 matching rows, all plausible Vietnamese given-name combinations (Nguyễn Đức Phúc, Nguyễn Hữu Anh, Nguyễn Mai Bảo Linh, etc.), alphabetically ordered by the part after "Nguyễn". Giảng viên tab listed the 30 seeded GV rows. Logged out `bomon`, logged in as `DTC225200001` via a direct `fetch` to `/api/auth/login`, then confirmed `GET`-equivalent `/api/auth/refresh` returned `vai_tro: "SINH_VIEN"`.

**User confirmation of both checks is still pending** — flagged here per coverage items D1 and D4.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Ready for plans 02-04/02-05 (topic proposal/registration, UC1): `useCohorts()` is exported from `frontend/src/features/cohorts/api.ts` exactly as their filter/form screens need, and `DotDoAn.trang_thai == DANG_MO` is the check those plans must apply before allowing a topic proposal/registration (per this plan's router docstring). The open demo cohort "Đợt đồ án tốt nghiệp K22 - HK1 (2026-2027)" (khóa K22) is live and ready for UC1 demos with the 100 SV / 30 GV seeded population. No blockers.

---
*Phase: 02-platform-rbac-topic-management*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 8 new key files confirmed present on disk; all 4 task commits (`d679825`, `34e0ea3`, `f75f3b3`, `ab75585`) confirmed present in `git log --oneline --all`.
