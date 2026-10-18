---
phase: 02-platform-rbac-topic-management
verified: 2026-09-28T09:10:00Z
status: human_needed
score: 13/13 must-haves verified
covered_files:
  - .planning/phases/02-platform-rbac-topic-management/02-01-PLAN.md
  - .planning/phases/02-platform-rbac-topic-management/02-01-SUMMARY.md
  - .planning/phases/02-platform-rbac-topic-management/02-02-PLAN.md
  - .planning/phases/02-platform-rbac-topic-management/02-02-SUMMARY.md
  - .planning/phases/02-platform-rbac-topic-management/02-03-PLAN.md
  - .planning/phases/02-platform-rbac-topic-management/02-03-SUMMARY.md
  - .planning/phases/02-platform-rbac-topic-management/02-04-PLAN.md
  - .planning/phases/02-platform-rbac-topic-management/02-04-SUMMARY.md
  - .planning/phases/02-platform-rbac-topic-management/02-05-PLAN.md
  - .planning/phases/02-platform-rbac-topic-management/02-05-SUMMARY.md
  - .planning/phases/02-platform-rbac-topic-management/02-06-PLAN.md
  - .planning/phases/02-platform-rbac-topic-management/02-06-SUMMARY.md
  - .planning/phases/02-platform-rbac-topic-management/02-REVIEW-FIX.md
  - .planning/phases/02-platform-rbac-topic-management/02-REVIEW.md
  - backend/alembic/versions/0005_phien_ban_token.py
  - backend/app/core/body_limit.py
  - backend/app/core/deps.py
  - backend/app/core/security.py
  - backend/app/models/tai_khoan.py
  - backend/app/routers/auth.py
  - backend/app/services/title_check.py
  - backend/app/services/topics.py
  - backend/docker-entrypoint.sh
  - backend/tests/conftest.py
  - backend/tests/test_auth.py
  - backend/tests/test_body_limit.py
  - deploy/docker-compose.yml
  - docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md
  - docs/chuong-3-thiet-ke/csdl/erd.puml
  - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml
covered_digest: "v2:sha256:d0aefad58c0c34ec53abddc0cf30fc7f554f7782dad741fb4b99e7bbcfed5bb8"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 12/13
  gaps_closed:
    - "Per D-04 and DEPL-01 (02-01-PLAN.md): the database default collation and every table collation is utf8mb4_vietnamese_ci, and tai_khoan/sinh_vien/giang_vien carry exactly the §3.2.3 column names (tools/check-erd-db.py passes)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Reload any authenticated page (e.g. /tong-quan) in a real browser and confirm the session survives (AuthBootstrap's POST /api/auth/refresh on mount); click Đăng xuất from several different pages and confirm each returns to /dang-nhap and clears the session (AUTH-02)."
    expected: "Session persists across reload without re-entering credentials; logout works identically from every authenticated page."
    why_human: "Executor self-performed this via a CDP-driven headless Chrome session (screenshots kept only in the scratchpad, not committed) because Playwright/Puppeteer are not installed and the user was asleep during autonomous execution (02-02-SUMMARY.md, 02-03-SUMMARY.md). Automated evidence (smoke-test.sh's refresh/logout/cookie checks, e2e-uc1.sh, and the wiring in AuthBootstrap.tsx/client.ts/AppLayout.tsx) all pass, so this is not blocking, but a real-browser confirmation by the user is still outstanding."
  - test: "Click through MH-02/03/04 dashboards, MH-05 topic list filters, MH-06 propose/edit form and MH-07 approval Drawer as SV, GV and Bộ môn accounts, confirming visual fidelity to the Phase 1 mockups and that antd controls (Select dropdowns, Popconfirm, Modal) behave as expected."
    expected: "Each screen matches its MH-0x mockup; filters, forms and confirmations work as designed for each role."
    why_human: "Same self-performed-CDP situation across plans 02-02..02-06 (see each SUMMARY.md's 'Human-check (self-performed, pending user confirmation)' section) — visual/UX fidelity is inherently a human judgment call. Automated coverage (pytest RBAC/ownership/concurrency tests, smoke-test.sh, e2e-uc1.sh, frontend build) passes, so this does not block the phase, but genuine user confirmation is still pending per the executors' own notes."
---

# Phase 2: Platform, RBAC & Topic Management Verification Report

**Phase Goal:** Hệ thống chạy thật sau Apache HTTPS; SV, GV và Bộ môn đăng nhập và đi trọn UC Quản lý đề tài, với mọi quyền truy cập được kiểm tra phía server
**Verified:** 2026-09-28
**Status:** human_needed
**Re-verification:** Yes — after gap closure (commit 1990663)

## Goal Achievement

### Observable Truths

Mapped to ROADMAP § Phase 2 Success Criteria 1–5, cross-checked against the six PLAN files' `must_haves.truths`. This is a **re-verification** after gap-closure commit `1990663` ("docs(02): write phien_ban_token (WR-04) back into ERD, class diagram and data dictionary"). Truth #3 (previously FAILED) was fully re-checked with fresh evidence; the previously-passing truths were regression-checked (full backend pytest suite + smoke-test.sh re-run live, plus a fresh read of the affected doc/code files).

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **SC1 (partial) — Apache HTTPS + static React + `/api` proxy**: `http://localhost/` 301→HTTPS, React served statically, `/api/*` proxied to FastAPI, security headers present | ✓ VERIFIED | Regression: `bash deploy/smoke-test.sh` re-run live — all 18 checks OK, including "http://localhost/ trả 301", CSP/X-Content-Type-Options headers present. |
| 2 | **SC1 (partial) — MySQL 8 utf8mb4 created entirely via migration** | ✓ VERIFIED | Regression: live docker-compose stack still up (`ntma-mysql-1`/`ntma-api-1`/`ntma-apache-1` healthy); `check-erd-db.py` (below) independently confirms schema/ERD parity, which subsumes this truth. |
| 3 | **SC1 (partial) — ERD/DB parity check (`tools/check-erd-db.py`) now passes — GAP CLOSED** | ✓ VERIFIED | Re-ran live: `python3 tools/check-erd-db.py` → `OK: schema thesis_core khớp erd.puml cho các bảng đã tạo.` (exit 0). Confirmed `docs/chuong-3-thiet-ke/csdl/erd.puml` line 16 now has `phien_ban_token : BIGINT <<NOT NULL>> = 0`; `docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md` §3.2.3 line 34 has the matching data-dictionary row; `docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml` line 96 has `+phienBanToken : Long` in the `TaiKhoan` class (camelCase, per that diagram's own naming convention). Also ran `python3 tools/check-docs.py class-erd` (exit 0) and `python3 tools/check-docs.py render` (exit 0) as instructed — both pass, confirming class/ERD consistency and that rendered `.svg`/`.png` diagrams are current (the commit's diff shows `erd.svg`, `erd.png`, `lop-thuc-the.svg`, `lop-thuc-the.png` were all regenerated). |
| 4 | **SC1 (partial) — Vietnamese collation orders `Đ` correctly** | ✓ VERIFIED | Not re-run live in this pass (unaffected by the gap-closure commit, which only touched docs); relies on prior verification (collation confirmed on every table, DB-driven sort in `topics.py`/account list) plus this pass's regression pytest run passing (accounts/topics tests unaffected). |
| 5 | **SC2 — Any of the 100 SV + 30 GV + Bộ môn logs in with mã/email + mật khẩu, session persists across reload, logout from every page** | ✓ VERIFIED (session/logout mechanics); UI reload/logout **click-through** self-performed, listed under Human Verification | Regression: `bash deploy/smoke-test.sh` re-run live — login OK, wrong-password 401, refresh-cookie flags OK, `/api/auth/refresh` OK, `/api/auth/me` 200/401, logout 204 + cookie cleared + subsequent refresh 401, 6th bad login 429, all unchanged from prior pass. |
| 6 | **SC2 — Bộ môn creates/edits/locks SV & GV accounts; a locked account cannot log in, unlocking restores login** | ✓ VERIFIED | Regression: `uv --directory backend run pytest -q` re-run live → `38 passed`, including `test_accounts_rbac.py::test_bomon_lock_blocks_login_and_unlock_restores_it`. |
| 7 | **SC2 — Bộ môn opens/closes đợt đồ án by khóa** | ✓ VERIFIED | Regression: full pytest suite green (`test_cohorts_rbac.py` included in the 38); smoke-test unaffected. |
| 8 | **SC3 — GV proposes a topic into an open đợt; SV self-proposes or registers a GV-proposed open topic; Bộ môn approves/rejects with reason and assigns GVHD; all roles view a status/đợt/GV-filtered list** | ✓ VERIFIED | Not re-run live in this pass (e2e-uc1.sh is a stateful script that mutates DB data and was not part of the required regression set for this re-verification); unaffected by the doc-only gap-closure commit; supported by the unchanged, still-green pytest suite covering topic ownership/approval/registration paths. |
| 9 | **SC4 — DB blocks 2 active topics for one SV and 2 SV for one topic, even under true concurrency** | ✓ VERIFIED | Regression: `uv --directory backend run pytest -q` re-run live → `38 passed`, including `test_topic_registration.py`'s two Barrier-based concurrency tests. |
| 10 | **SC5 — Direct API calls with a wrong-role token or on data not owned are rejected server-side** | ✓ VERIFIED | Regression: full pytest suite green (RBAC/ownership test files included); smoke-test's 403 checks (`DTC225200001 bị 403 trên accounts/cohorts/topic-approvals`, `GV001 bị 403 trên topic-approvals/register`) re-confirmed live. |
| 11 | **TOPC-04/NFR-12 — topic list answers ≤ 1s P95 over 20 calls through Apache** | ✓ VERIFIED | Not re-measured live in this pass (unaffected by a documentation-only commit); prior independent live measurement (~0.02s/call) stands, and smoke-test's `DTC225200001 xem /api/topics -> 200` re-confirms the endpoint is still healthy. |
| 12 | **Full backend test suite is green and the DB-level constraints/RBAC declarations hold across the whole phase** | ✓ VERIFIED | Re-ran live: `uv --directory backend run pytest -q` → `38 passed, 1 warning in 28.19s` (warning is a pre-existing `httpx`/starlette deprecation notice, not a regression). |
| 13 | **Code-review findings (CR-01, WR-01..WR-05) from 02-REVIEW.md are actually fixed, not just claimed fixed** | ✓ VERIFIED | Unaffected by the gap-closure commit (which only touched docs, not code); prior independent verification of `body_limit.py`, `docker-compose.yml`/`docker-entrypoint.sh`, `tai_khoan.phien_ban_token`+JWT `"tv"` claim, and `PUBLIC_ROUTES` relocation stands; this pass's fresh pytest run (`test_chunked_body_without_content_length_still_gets_413` included in the 38) reconfirms the body-limit fix specifically. |

**Score:** 13/13 truths verified (0 present-but-behavior-unverified)

### Deferred Items

None.

### Advisory (New Scope, Unevidenced)

None — this re-verification round introduced no new-scope findings; the gap-closure commit is strictly additive documentation (3 `.puml`/`.md` line insertions + regenerated `.svg`/`.png` renders) with no code changes.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/chuong-3-thiet-ke/csdl/erd.puml` | Stays in sync with the live schema via `tools/check-erd-db.py` — **previously ✗ STUB (stale)** | ✓ VERIFIED | `phien_ban_token : BIGINT <<NOT NULL>> = 0` now present in the `tai_khoan` entity (line 16); `check-erd-db.py` passes. |
| `docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md` | §3.2.3 data dictionary lists every `tai_khoan` column | ✓ VERIFIED | Row for `phien_ban_token` present (line 34) with type, nullability and description. |
| `docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml` | Class diagram `TaiKhoan` stays consistent with the live schema | ✓ VERIFIED | `+phienBanToken : Long` present in the `TaiKhoan` class (line 96); `tools/check-docs.py class-erd` passes (exit 0). |
| `docs/chuong-3-thiet-ke/csdl/erd.svg` / `erd.png` | Rendered diagrams reflect the current `.puml` source | ✓ VERIFIED | Regenerated in commit 1990663 (binary diff); `tools/check-docs.py render` passes (exit 0), confirming renders are current. |
| `docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.svg` / `.png` | Rendered class diagram reflects current `.puml` source | ✓ VERIFIED | Regenerated in commit 1990663; covered by the same `check-docs.py render` pass above. |

All artifacts from the initial verification pass remain as previously verified (deploy/docker-compose.yml, deploy/apache/ntma.conf, alembic migrations 0001-0005, deps.py, routers, frontend features, backend/tests/*) — regression-checked via the live pytest and smoke-test re-runs above, no changes to those files in the gap-closure commit.

### Key Link Verification

No key links were affected by the gap-closure commit (documentation-only). All previously-verified links (AuthBootstrap→auth.py refresh, client.ts 401-retry interceptor, list_topics role-scoping, register_topic DB constraint, Apache→FastAPI proxy, docker-entrypoint.sh→alembic) stand — regression-confirmed indirectly via the unchanged, still-passing pytest suite and smoke-test.

### Data-Flow Trace (Level 4)

Not affected by this round's change (doc-only). Prior findings (topic list, dashboard widgets, title-check stub, JWT `"tv"` claim) all still ✓ FLOWING per the unchanged code and the fresh pytest/smoke-test regression run.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| ERD/DB parity (the closed gap) | `python3 tools/check-erd-db.py` | `OK: schema thesis_core khớp erd.puml cho các bảng đã tạo.` (exit 0) | ✓ PASS |
| Class/ERD consistency | `python3 tools/check-docs.py class-erd` | exit 0, no failures | ✓ PASS |
| Diagram render freshness | `python3 tools/check-docs.py render` | exit 0, no failures | ✓ PASS |
| Full backend test suite (regression) | `uv --directory backend run pytest -q` | `38 passed, 1 warning in 28.19s` | ✓ PASS |
| Platform smoke test (regression) | `bash deploy/smoke-test.sh` | 18/18 checks "OK", exit 0 | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| `deploy/smoke-test.sh` | `bash deploy/smoke-test.sh` | All 18 checks printed "OK", exited 0 | PASS |

`deploy/e2e-uc1.sh` was not re-run in this pass (it is stateful/mutating and was not required for the targeted gap re-check + regression scope defined for this re-verification); it was independently verified in the prior pass and nothing in the gap-closure commit touches the code paths it exercises.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|-------------|--------------|--------|----------|
| DEPL-01 | 02-01 | MySQL 8 utf8mb4, schema via migration, ERD-verified | ✓ SATISFIED | `alembic current` = 0005 head (unchanged); `check-erd-db.py` now passes — the ERD-doc regression noted in the prior report is fully closed. |
| DEPL-02 | 02-01, 02-06 | Apache reverse proxy + HTTPS, static React, `/api` proxy | ✓ SATISFIED | smoke-test.sh re-run passes through `https://localhost` |
| AUTH-01 | 02-01 | Login by mã/email + mật khẩu, JWT | ✓ SATISFIED | smoke-test login/wrong-password checks re-confirmed |
| AUTH-02 | 02-01, 02-02 | Session persists on reload, logout from any page | ✓ SATISFIED (mechanics); UI click-through self-performed, see Human Verification | refresh/logout cookie mechanics re-confirmed live |
| AUTH-03 | 02-01..02-06 | 3 roles, every API checks role + ownership server-side | ✓ SATISFIED | Full pytest suite (RBAC files) green |
| AUTH-04 | 02-02, 02-03 | Bộ môn manages SV/GV accounts + đợt đồ án | ✓ SATISFIED | `test_accounts_rbac.py`, `test_cohorts_rbac.py` pass in regression run |
| DATA-01 | 02-03 | Seed 100 SV + 30 GV | ✓ SATISFIED | Unaffected by this pass; previously confirmed live (100/30/1) |
| TOPC-01 | 02-04 | GV proposes topic into open đợt | ✓ SATISFIED | Unaffected by doc-only change; pytest topic tests green |
| TOPC-02 | 02-04, 02-05 | SV self-proposes or registers open GV topic | ✓ SATISFIED | Unaffected; pytest topic tests green |
| TOPC-03 | 02-05, 02-06 | Bộ môn approves/rejects + assigns GVHD; 1 SV:1 topic, 1 topic:1 SV | ✓ SATISFIED | Concurrency tests re-confirmed green in regression run |
| TOPC-04 | 02-05, 02-06 | All roles view filtered topic list by state/đợt/GV | ✓ SATISFIED | Unaffected; smoke-test topic-list check re-confirmed |

No orphaned requirements: all 11 IDs mapped to Phase 2 in REQUIREMENTS.md (AUTH-01..04, TOPC-01..04, DEPL-01, DEPL-02, DATA-01) are satisfied. DEPL-01's ERD-parity caveat from the prior report is now fully resolved.

### Anti-Patterns Found

None. The gap-closure commit only added 1 ERD-entity line, 1 data-dictionary row, 1 class-diagram field, and regenerated 4 binary/svg render artifacts — no TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers, no stub patterns, no code changes at all.

### Human Verification Required

Carried forward unchanged from the prior verification pass — neither item is affected by the gap-closure commit, and both remain non-blocking per this task's instructions (self-performed by executors, pending user confirmation):

1. **Session-restore-on-reload and logout-from-every-page (AUTH-02) — real browser confirmation**
   **Test:** Reload an authenticated page (e.g. `/tong-quan`) and confirm the session survives without re-login; click "Đăng xuất" from several different pages.
   **Expected:** Reload keeps the user logged in; logout returns to `/dang-nhap` from any page.
   **Why human:** Self-performed by the executor via CDP-driven headless Chrome (screenshots kept only in the local scratchpad, not committed) because the user was asleep during autonomous execution and Playwright/Puppeteer are not installed. Automated evidence (smoke-test.sh's refresh/logout/cookie assertions, plus code-level wiring in `AuthBootstrap.tsx`/`client.ts`/`AppLayout.tsx`) all passes, so this is not treated as a blocking gap — but genuine user confirmation in a real browser is still outstanding.

2. **Visual/UX fidelity of MH-01..MH-07 screens across all 3 roles**
   **Test:** Click through login, dashboards (MH-02/03/04), topic list (MH-05), propose/edit form (MH-06) and approval Drawer (MH-07) as SV, GV and Bộ môn.
   **Expected:** Each screen matches its Phase-1 mockup; antd controls (Select, Popconfirm, Modal) behave as intended; Vietnamese text/diacritics render and sort correctly.
   **Why human:** Every plan's `<human-check>` items (02-02 through 02-06) were self-performed by the executor via the same CDP technique for the stated reason (autonomous run, no Playwright installed, user asleep) — see each `0X-SUMMARY.md`'s "Human-check (self-performed, pending user confirmation)" section. Automated coverage (unit/integration tests, smoke-test, e2e-uc1, frontend build) passes, so this does not block the phase goal, but is flagged for the user's own confirmation per the task instructions.

### Gaps Summary

**No gaps remain.** The single gap from the prior verification pass — the ERD/DB parity check (`tools/check-erd-db.py`) failing because `tai_khoan.phien_ban_token` (added by migration 0005 during the WR-04 code-review fix) was missing from `docs/chuong-3-thiet-ke/csdl/erd.puml` — is closed by commit `1990663`. Fresh, independently-run evidence for this re-verification pass:

- `python3 tools/check-erd-db.py` → exit 0, `OK: schema thesis_core khớp erd.puml cho các bảng đã tạo.`
- `python3 tools/check-docs.py class-erd` → exit 0
- `python3 tools/check-docs.py render` → exit 0 (confirms the regenerated `.svg`/`.png` diagrams in the commit are current)
- Direct file reads confirm the `phien_ban_token`/`phienBanToken` field is present, consistently named per each artifact's own convention, in all three documentation artifacts (`erd.puml`, `02-thiet-ke-csdl.md` §3.2.3, `lop-thuc-the.puml`).

Regression check of the previously-passing items found **no regressions**: `uv --directory backend run pytest -q` still reports `38 passed`, and `bash deploy/smoke-test.sh` still reports all 18 checks "OK" against the live docker-compose stack.

The two human-verification items (real-browser session/logout confirmation, and visual/UX fidelity of MH-01..MH-07 across all 3 roles) remain outstanding but non-blocking, as they were self-performed by the executors via CDP and are explicitly called out as pending genuine user confirmation — this drives the overall status to `human_needed` rather than `passed`, per the task instructions to keep them non-blocking while still surfacing them.

---

_Verified: 2026-09-28_
_Verifier: Developer (verifier)_
