---
phase: 02-platform-rbac-topic-management
fixed_at: 2026-09-28T00:48:58Z
review_path: .planning/phases/02-platform-rbac-topic-management/02-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 2: Code Review Fix Report

**Fixed at:** 2026-09-28
**Source review:** `.planning/phases/02-platform-rbac-topic-management/02-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (fix_scope = critical_warning: CR-01, WR-01..WR-05; IN-01 explicitly excluded)
- Fixed: 6
- Skipped: 0

All fixes were applied on the main working tree (branch `main`), each committed atomically. After all fixes, the full stack was rebuilt and re-verified: `docker compose -f deploy/docker-compose.yml up -d --build --wait`, `uv --directory backend run pytest -q` (38 passed), `bash deploy/smoke-test.sh` (all checks OK), `bash deploy/e2e-uc1.sh` (all checks OK), and `npm --prefix frontend run build` (build succeeded) — all green.

## Fixed Issues

### CR-01: Request body size limit bypassed when Content-Length is absent

**Files modified:** `backend/app/core/body_limit.py`, `backend/tests/test_body_limit.py`
**Commit:** `cd3496e`
**Applied fix:** `MaxBodySizeMiddleware` kept the existing `Content-Length`-based fast-path reject, but now also wraps `receive()` to count bytes actually read from the ASGI stream and rejects with 413 once the real total exceeds `MAX_BODY_BYTES`, regardless of whether `Content-Length` is present, absent, or understated (e.g. chunked transfer encoding). Added one small regression test (`test_chunked_body_without_content_length_still_gets_413`) that drives the middleware directly with a scope carrying no `content-length` header and feeds it >26 MB in streamed chunks, asserting a 413 is sent — this is the specific gap CR-01 identified.

### WR-01: `create_topic`/`update_topic` re-checked cohort "open" state with check-then-act

**Files modified:** `backend/app/services/topics.py`
**Commit:** `550508a`
**Applied fix:** Added `_lock_open_cohort_or_error`, which re-validates the cohort with `SELECT ... FOR UPDATE` immediately before the write (right before `db.add(topic)`/`db.flush()` in `create_topic`, and right before `db.commit()` in `update_topic`), inside the same transaction that commits the topic write. This closes the TOCTOU window between the initial (early-exit) cohort check and the actual write — if a Bộ môn closes the cohort concurrently, one of the two transactions blocks on the row lock until the other commits, so the write either fails with 409 or completes against a cohort that was still genuinely open at write time. Mirrors the atomic-guard pattern already used by `submit_topic`/`register_topic`. Verified against `tests/test_topic_registration.py`, `test_topic_ownership.py`, `test_topic_approval_rbac.py`, `test_cohorts_rbac.py` (all pass) plus the full suite and `deploy/e2e-uc1.sh`.

### WR-02: Missing `cau_hinh_nguong` threshold row caused an unhandled 500

**Files modified:** `backend/app/services/title_check.py`
**Commit:** `e692997`
**Applied fix:** `kiem_tra_ten` now catches `sqlalchemy.exc.NoResultFound` from the threshold lookup and returns `TitleCheckResult(trang_thai=LOI, ...)` — the same non-blocking degraded response already used when the AI client itself errors — instead of letting the exception propagate into an unhandled 500. Added a documented fallback constant (`_FALLBACK_NGUONG_TEN_DE_TAI = 50.00`, matching migration 0004's seed value) used only to populate the stored `nguong_ap_dung` column when this path triggers, never used for actual duplicate-match comparison.

### WR-03: `--forwarded-allow-ips='*'` over-trusted `X-Forwarded-For`

**Files modified:** `deploy/docker-compose.yml`, `backend/docker-entrypoint.sh`
**Commit:** `35140cc`
**Applied fix:** Added a dedicated compose network (`ntma-internal`, fixed `172.28.238.0/24` subnet) with the `apache` service pinned to a static IP (`172.28.238.10`); `api`'s uvicorn now runs with `--forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}"`, and compose passes `FORWARDED_ALLOW_IPS=172.28.238.10` — so only the Apache container's exact address is trusted to set `X-Forwarded-For`/`-Proto`, not any container that can reach `api:8001`. Verified: rebuilt the stack, confirmed `docker inspect` shows apache at `172.28.238.10`, and re-ran `deploy/smoke-test.sh` + `deploy/e2e-uc1.sh` end to end (all pass, including the 21 MB-pass/30 MB-413 body-limit checks and the login-throttle checks that depend on the client IP).

### WR-04: Logged-out refresh/access tokens remained valid until natural expiry

**Files modified:** `backend/alembic/versions/0005_phien_ban_token.py` (new), `backend/app/models/tai_khoan.py`, `backend/app/core/security.py`, `backend/app/core/deps.py`, `backend/app/routers/auth.py`
**Commit:** `0a437ba`
**Applied fix:** Added a minimal `tai_khoan.phien_ban_token` column (migration 0005). Access and refresh tokens now carry a `"tv"` claim set to the account's `phien_ban_token` at issuance; `get_current_user` and `POST /api/auth/refresh` reject any token whose `"tv"` no longer matches the account's current value. `POST /api/auth/logout` now atomically increments `phien_ban_token` for the account identified by the refresh cookie (`UPDATE tai_khoan SET phien_ban_token = phien_ban_token + 1 WHERE id = ...`), before deleting the cookie — this revokes every token issued before that moment, including a copy that may have been exfiltrated before logout, closing the exact gap the finding described (previously the only revocation mechanism was the blunt, manual `bi_khoa` account lock). This is the simple "token version bumped on logout" approach suggested by the review, not a full revocation-denylist table.

Live-verified against the rebuilt stack (not just unit tests, since this is a stateful cross-request flow): logged in, saved the pre-logout refresh cookie, confirmed a refresh with it returned 200, called logout, then replayed the *same pre-logout* cookie against `/api/auth/refresh` again — it now returns 401 (previously it would have continued to succeed until the cookie's 8-hour expiry). Full backend test suite (38 tests), `deploy/smoke-test.sh`, and `deploy/e2e-uc1.sh` all still pass unchanged.

### WR-05: `PUBLIC_ROUTES` in `deps.py` was unused in production code, only consumed by a test

**Files modified:** `backend/app/core/deps.py`, `backend/tests/conftest.py`, `backend/tests/test_auth.py`
**Commit:** `fcd1b3e`
**Applied fix:** Moved the `PUBLIC_ROUTES` set out of `app/core/deps.py` (production module) into `tests/conftest.py`, since its only consumer was `test_every_api_route_declares_roles`. Updated that test's import from `app.core.deps` to `conftest`. This removes the risk of a future contributor assuming the set has a runtime enforcement effect (it never did — every route's actual protection is its own `Depends(require_role(...))`/`Depends(get_current_user)`). Verified `tests/test_auth.py` still passes with the new import path.

## Skipped Issues

None — all 6 in-scope findings (CR-01, WR-01, WR-02, WR-03, WR-04, WR-05) were fixed. IN-01 was out of `fix_scope` (`critical_warning`) and intentionally not touched.

---

_Fixed: 2026-09-28_
_Fixer: Developer (code-fixer)_
_Iteration: 1_
