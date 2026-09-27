---
phase: 02-platform-rbac-topic-management
plan: 01
subsystem: auth
tags: [fastapi, sqlalchemy, mysql, alembic, jwt, bcrypt, react, vite, antd, apache, docker-compose, rbac]

requires:
  - phase: 01-survey-design
    provides: "ERD/data dictionary (docs §3.2.3), architecture (§3.3), MH-01 mockup, UC0.1 spec — all implemented verbatim here"
provides:
  - "Docker Compose stack (mysql 8.4 + api + apache) behind Apache HTTPS, project name ntma"
  - "Alembic migration 0001: tai_khoan/sinh_vien/giang_vien, utf8mb4_vietnamese_ci"
  - "FastAPI app skeleton: router auto-discovery, NFC-normalizing schema base, security module (PyJWT + bcrypt)"
  - "POST /api/auth/login, /refresh, /logout, GET /me — full session lifecycle"
  - "get_current_user + require_role(*roles) shared RBAC dependency, PUBLIC_ROUTES allow-list"
  - "Login throttle (5 failures / 15 min -> 429)"
  - "pytest harness against real MySQL thesis_core_test schema"
  - "React SPA: route registry (collectRoutes), MH-01 login screen, /tong-quan landing page, zustand in-memory auth store"
  - "deploy/ helper scripts (init, sql, dom-check, smoke-test, api-login) + tools/check-erd-db.py"
affects: [02-02, 02-03, 02-04, 02-05, 02-06, phase-03, phase-04, phase-05]

actuals:
  tokens: 73013
  tasks: 2
  commits: 2
  plan_head_before: 55bc7de
  plan_head_after: 7d796fea88b757b320e9ba257135c8703e76a0d6

tech-stack:
  added:
    - "backend: fastapi 0.141.1, sqlalchemy 2.0.54, pymysql[rsa] 1.2.3, alembic 1.20.0, pyjwt 2.15.0, bcrypt 5.0.0, pydantic-settings 2.15.0, uvicorn[standard] 0.54.0, faker 40.39 (dep, not yet used), pytest 8.4.2 + httpx 0.28.1 (dev)"
    - "frontend: react/react-dom 18.3.1, vite 7.3.6, typescript 5.9.3, antd 5.29.3, @tanstack/react-query 5.104.0, react-router 7.18.4, axios 1.20.0, zustand 5.0.15"
    - "deploy: mysql:8.4 (server 8.4.11), httpd:2.4 (2.4.68 + OpenSSL 3.5.7), node:20-alpine (build stage), python:3.12-slim + uv 0.11.19 (backend image)"
  patterns:
    - "Router auto-discovery: app/routers/__init__.py discover_routers() walks pkgutil, later routers need no main.py edit"
    - "Model auto-import: app/models/__init__.py walks pkgutil so Alembic env.py sees every model without manual imports"
    - "require_role(*roles) returns a dependency carrying .allowed_roles — test_every_api_route_declares_roles walks route.dependant recursively to enforce 100% RBAC coverage, including future routes"
    - "NFCModel: every request schema inherits NFC-normalization + whitespace strip (except mat_khau* fields, which are NFC-only, never stripped)"
    - "Frontend route registry: features/*/routes.tsx export routes: AppRoute[], collected via import.meta.glob eager"

key-files:
  created:
    - backend/app/core/deps.py
    - backend/app/core/security.py
    - backend/app/core/throttle.py
    - backend/app/core/body_limit.py
    - backend/app/routers/auth.py
    - backend/alembic/versions/0001_tai_khoan_ho_so.py
    - backend/tests/conftest.py
    - backend/tests/test_auth.py
    - deploy/docker-compose.yml
    - deploy/apache/ntma.conf
    - frontend/src/app/registry.ts
    - frontend/src/features/auth/LoginPage.tsx
    - tools/check-erd-db.py
  modified: []

key-decisions:
  - "Apache mod_proxy_http does not enforce LimitRequestBody on proxied content (verified empirically: even a 100-byte limit let a 2000-byte POST to /api/health reach the backend unrejected) — enforced the 26,214,400-byte (25MB) limit at the ASGI layer instead (app/core/body_limit.py), kept LimitRequestBody in ntma.conf as documented intent + protection for the static DocumentRoot path"
  - "curl auto-adds 'Expect: 100-continue' for POST bodies over ~1MB, which Apache's mod_proxy_http mishandles when the backend answers before reading the body (AH01086, 500) — deploy/smoke-test.sh sends '-H \"Expect:\"' on the two body-size checks; not a production concern since browsers do not send this header for typical form/file uploads"
  - "PUBLIC_ROUTES had to include FastAPI's own GET/HEAD /api/docs and /api/openapi.json (discovered by test_every_api_route_declares_roles) — these are auto-generated documentation endpoints with no business data, not a scope violation of AUTH-03"
  - "Dashboard menu label kept as a single shared 'Tổng quan' for all three roles instead of the plan's role-specific BO_MON label 'Tổng quan toàn khoa' — the locked MenuEntry contract ({roles, label, order, to?}) only supports one label per route; per-role label variation deferred to whichever later plan actually renders the sidebar"

patterns-established:
  - "Task type=tracer followed by an in-place expansion task (Task 2) in the same plan; both committed atomically, tracer feedback gate re-ran full <verify> before expanding (auto mode, no checkpoint needed)"

requirements-completed: [DEPL-01, DEPL-02, AUTH-01, AUTH-02, AUTH-03]

coverage:
  - id: D1
    description: "Docker Compose stack (mysql 8.4 + api + apache) behind Apache HTTPS; / serves the React build, /api proxies to FastAPI, http redirects to https, security headers + CSP present"
    requirement: "DEPL-02"
    verification:
      - kind: integration
        ref: "deploy/smoke-test.sh checks a, c, d, e"
        status: pass
    human_judgment: false
  - id: D2
    description: "thesis_core schema created by Alembic revision 0001 with utf8mb4_vietnamese_ci at DB and table level, columns matching docs/chuong-3-thiet-ke/csdl/erd.puml exactly"
    requirement: "DEPL-01"
    verification:
      - kind: integration
        ref: "tools/check-erd-db.py"
        status: pass
      - kind: integration
        ref: "plan 02-01 Task 1 <verify> SQL collation/alembic_version checks"
        status: pass
    human_judgment: false
  - id: D3
    description: "POST /api/auth/login by mã SV/GV or email + password issues a Bearer access JWT; identical 401 for unknown login/wrong password/locked account; 6th failure in 15 min for one (IP, login) returns 429"
    requirement: "AUTH-01"
    verification:
      - kind: integration
        ref: "deploy/smoke-test.sh checks f, g, m"
        status: pass
      - kind: unit
        ref: "backend/tests/test_auth.py::test_login_by_code_and_email_sets_refresh_cookie"
        status: pass
      - kind: unit
        ref: "backend/tests/test_auth.py::test_locked_account_cannot_login_or_refresh"
        status: pass
    human_judgment: false
  - id: D4
    description: "Session persists across reload via httpOnly/Secure/SameSite=Strict refresh cookie scoped to /api/auth; POST /refresh re-mints an access token and refuses locked/missing accounts; POST /logout clears the cookie; GET /me returns the current user"
    requirement: "AUTH-02"
    verification:
      - kind: integration
        ref: "deploy/smoke-test.sh checks i, j, k, l"
        status: pass
      - kind: unit
        ref: "backend/tests/test_auth.py::test_expired_or_refresh_token_rejected_as_bearer"
        status: pass
    human_judgment: false
  - id: D5
    description: "Every /api route except the PUBLIC_ROUTES allow-list carries a require_role dependency (allowed_roles); get_current_user re-reads tai_khoan every request so locking takes effect immediately"
    requirement: "AUTH-03"
    verification:
      - kind: unit
        ref: "backend/tests/test_auth.py::test_every_api_route_declares_roles"
        status: pass
    human_judgment: false
  - id: D6
    description: "MH-01 login screen (Vietnamese labels, hint text, generic error alert) renders correctly through Apache HTTPS and leads to /tong-quan on successful login"
    verification:
      - kind: automated_ui
        ref: "deploy/dom-check.sh /dang-nhap 'Mã SV/GV hoặc email' (headless Chrome DOM check) — pass"
      - kind: manual_procedural
        ref: "headless Chrome screenshot at https://localhost/dang-nhap, self-viewed this session"
        status: pass
    human_judgment: true
    rationale: "Visual/layout fidelity to the MH-01 mockup is a judgment call; self-performed via headless Chrome screenshot (see 'Human-check' section below) but genuine user confirmation is still pending."

duration: 40min
completed: 2026-09-28
status: complete
---

# Phase 2 Plan 1: Tracer + Session/RBAC Foundation Summary

**Docker-composed FastAPI + MySQL + Apache-HTTPS stack with JWT login, httpOnly-cookie session refresh, and a shared `require_role` dependency enforced on every route by a route-coverage test — the vertical slice every later Phase 2 plan builds on.**

## Performance

- **Duration:** ~40 min
- **Completed:** 2026-09-28
- **Tasks:** 2/2 completed
- **Files modified:** 65 (59 in Task 1, 6 new + 2 modified in Task 2)

## Accomplishments

- Stood up the full three-container Docker Compose stack (`mysql:8.4`, FastAPI `api`, Apache `httpd:2.4`) under one compose project (`ntma`), with the `api` container never published to the host — only Apache can reach it.
- Apache serves the Vite-built React SPA statically, proxies `/api/*` to FastAPI, redirects `http://` to `https://`, and carries the security headers (CSP, X-Frame-Options, X-Content-Type-Options) plus SPA fallback (`FallbackResource /index.html`).
- Alembic revision `0001` creates `tai_khoan`, `sinh_vien`, `giang_vien` with `utf8mb4_vietnamese_ci` collation at both database and table level, columns matching `docs/chuong-3-thiet-ke/csdl/erd.puml` exactly (verified by `tools/check-erd-db.py`, which also correctly parses the ERD's multi-line PlantUML note on `de_tai.sinh_vien_id_dang_hoat_dong`).
- End-to-end login proven through actual HTTPS: headless Chrome renders `/dang-nhap` (MH-01 text confirmed), `POST /api/auth/login` for the seeded `bomon` account returns a JWT, and `/tong-quan` renders the authenticated landing page.
- Full session lifecycle: `POST /refresh` (httpOnly/Secure/SameSite=Strict cookie scoped to `/api/auth`), `POST /logout`, `GET /me`, all backed by `get_current_user` re-reading `tai_khoan` on every request (so `bi_khoa` takes effect immediately, no stale-token grace period).
- `require_role(*roles)` + `PUBLIC_ROUTES` allow-list + `test_every_api_route_declares_roles` gives 100% mechanical RBAC coverage — any future route without a role dependency fails the test suite automatically (AUTH-03, Pitfall 9/T-02-06).
- Login throttle: 5 failures per (client IP, login name) in 15 minutes returns 429, verified end-to-end through Apache.
- pytest harness runs against the real `thesis_core_test` MySQL schema (not mocks), with an idempotent Alembic-upgrade fixture and table-truncate-between-tests.

## Task Commits

1. **Task 1 (TRACER): Login end-to-end** — `22bb7ec` (feat)
2. **Task 2: Session and server-side RBAC foundation** — `7d796fe` (feat)

_Tracer feedback gate: full `<verify>` (smoke-test, dom-check, SQL collation/alembic checks, check-erd-db.py) re-ran clean after Task 1 before Task 2 began — auto mode, logged `⚡ Tracer verified end-to-end — expanding`, no checkpoint needed._

## Files Created/Modified

See `key-files` in frontmatter for the most load-bearing ones. Full list: 59 files in Task 1 (monorepo scaffold: `deploy/`, `backend/`, `frontend/`, `tools/check-erd-db.py`) + `backend/app/core/{deps,throttle}.py`, `backend/tests/{conftest,test_auth}.py`, `deploy/{api-login.sh,README.md}` (new) and `backend/app/routers/auth.py`, `deploy/smoke-test.sh` (extended) in Task 2.

## Decisions Made

See `key-decisions` in frontmatter. Summary:
- Body-size limit enforcement moved from Apache (`LimitRequestBody`, which does not apply to proxied `/api/*` traffic — a verified Apache/mod_proxy_http limitation) to a small ASGI middleware in the FastAPI app (`app/core/body_limit.py`), keeping the Apache directive in place as intent/documentation and as real protection for the static DocumentRoot path.
- `deploy/smoke-test.sh`'s two body-size checks send `-H "Expect:"` to avoid a curl-specific `Expect: 100-continue` / Apache-proxy interaction bug (AH01086) unrelated to the actual size-limit behavior being tested.
- `PUBLIC_ROUTES` extended to cover FastAPI's own `/api/docs` and `/api/openapi.json`.
- Dashboard menu kept a single shared label across roles (contract limitation, documented for future correction if a role-specific label is wanted).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Apache mod_proxy_http does not enforce `LimitRequestBody` for proxied requests**
- **Found during:** Task 1, running `deploy/smoke-test.sh` check (h)
- **Issue:** Empirically verified (including with `LimitRequestBody` temporarily set to 100 bytes inside the live container) that Apache never rejects an oversized body on the `/api/*` proxied path — the request always reaches the FastAPI backend regardless of size.
- **Fix:** Added `app/core/body_limit.py` (`MaxBodySizeMiddleware`), registered via `app.add_middleware`, enforcing the same 26,214,400-byte ceiling by inspecting `Content-Length` and returning 413.
- **Files modified:** `backend/app/core/body_limit.py` (new), `backend/app/main.py`
- **Verification:** `deploy/smoke-test.sh` checks (h): 21MB passes, 30MB returns 413.
- **Committed in:** `22bb7ec`

**2. [Rule 1 - Bug] curl's automatic `Expect: 100-continue` breaks Apache↔uvicorn proxying**
- **Found during:** Task 1, same smoke-test check
- **Issue:** For POST bodies above ~1MB, curl sends `Expect: 100-continue` by default; Apache's `mod_proxy_http` does not correctly relay this when the FastAPI backend answers immediately (e.g. 405 for a GET-only route) without reading the body first, producing `AH01086`/500 regardless of the actual body size.
- **Fix:** `deploy/smoke-test.sh`'s size-limit checks explicitly send `-H "Expect:"` to disable this curl behavior; documented as not a production concern since browsers do not send this header for standard uploads.
- **Files modified:** `deploy/smoke-test.sh`
- **Verification:** Same smoke-test checks, now stable.
- **Committed in:** `22bb7ec`

**3. [Rule 2 - Missing critical functionality] `PUBLIC_ROUTES` missing FastAPI's own doc routes**
- **Found during:** Task 2, first run of `test_every_api_route_declares_roles`
- **Issue:** `GET/HEAD /api/docs` and `GET/HEAD /api/openapi.json` (FastAPI auto-generated) had no role dependency and were not in the allow-list, failing the route-coverage test.
- **Fix:** Added the four (method, path) pairs to `PUBLIC_ROUTES` with a comment explaining they carry no business data.
- **Files modified:** `backend/app/core/deps.py`
- **Verification:** `uv run pytest -q tests/test_auth.py` — 4/4 pass.
- **Committed in:** `7d796fe`

---

**Total deviations:** 3 auto-fixed (2× Rule 1 bug fix, 1× Rule 2 missing functionality).
**Impact on plan:** All three were necessary for the plan's own must-haves/acceptance criteria to actually hold true end-to-end; no scope creep beyond what Task 1/2 already specified.

## Issues Encountered

- Initial `docker compose up --build` failed because `frontend/package-lock.json` did not exist yet (needed before the Apache image's build stage can `COPY` it) — ran `npm install` once locally first, which also produced `frontend/dist` and `*.tsbuildinfo` locally; added `*.tsbuildinfo` to `.gitignore` (not anticipated by the plan's `.gitignore` list, harmless generated artifact).
- Everything else matched the plan's `<action>` specification without further issues once the two Apache/mod_proxy quirks above were understood.

## Human-check (self-performed, pending user confirmation)

Per the autonomous-run instruction, self-performed the visual verification a human would normally do:

```
/usr/bin/google-chrome --headless=new --ignore-certificate-errors \
  --window-size=1440,900 --screenshot=<scratchpad>/login-screenshot.png \
  https://localhost/dang-nhap
```

Viewed the resulting PNG: renders exactly per MH-01 — centered white card on `#f5f5f5`, "Hệ thống quản lý đồ án" / "Khoa Công nghệ thông tin", fields "Mã SV/GV hoặc email" / "Mật khẩu" (both marked required), primary "Đăng nhập" button, footnote "Tài khoản do Bộ môn cấp. Liên hệ Bộ môn nếu quên mật khẩu." No visual defects observed. **User confirmation of this visual check is still pending** — flagged here per coverage item D6.

## User Setup Required

None — no external service configuration required. `deploy/init.sh` generates all secrets and the self-signed TLS certificate locally (openssl fallback; `mkcert` not installed on this machine, matching 02-RESEARCH.md's Environment Availability table).

## Next Phase Readiness

Ready for plan 02-02 onward: router auto-discovery, `require_role`, the frontend route registry, `deploy/smoke-test.sh`, and `tools/check-erd-db.py` are all reusable contracts now in place exactly as specified in this plan's `<context>` section. No blockers. The one open item is NFR-03's access/refresh token lifetimes (currently 30m/480m, env-configurable) — flagged in `deploy/README.md` as pending GVHD confirmation, not a blocker for further Phase 2 work.

---
*Phase: 02-platform-rbac-topic-management*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 13 key files confirmed present on disk; both task commits (`22bb7ec`, `7d796fe`) confirmed present in `git log --oneline --all`.
