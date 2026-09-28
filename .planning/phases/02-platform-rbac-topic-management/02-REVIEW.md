---
phase: 02-platform-rbac-topic-management
reviewed: 2026-09-28T00:00:00Z
depth: standard
files_reviewed: 107
files_reviewed_list:
  - backend/.dockerignore
  - backend/.python-version
  - backend/Dockerfile
  - backend/alembic.ini
  - backend/alembic/versions/0001_tai_khoan_ho_so.py
  - backend/alembic/versions/0002_dot_do_an.py
  - backend/alembic/versions/0003_de_tai.py
  - backend/alembic/versions/0004_kiem_tra_trung_lap_cau_hinh_nguong.py
  - backend/app/__init__.py
  - backend/app/core/__init__.py
  - backend/app/core/body_limit.py
  - backend/app/core/config.py
  - backend/app/core/db.py
  - backend/app/core/deps.py
  - backend/app/core/roles.py
  - backend/app/core/security.py
  - backend/app/core/throttle.py
  - backend/app/main.py
  - backend/app/models/__init__.py
  - backend/app/models/base.py
  - backend/app/models/cau_hinh_nguong.py
  - backend/app/models/de_tai.py
  - backend/app/models/dot_do_an.py
  - backend/app/models/tai_khoan.py
  - backend/app/models/trung_lap.py
  - backend/app/routers/__init__.py
  - backend/app/routers/accounts.py
  - backend/app/routers/auth.py
  - backend/app/routers/cohorts.py
  - backend/app/routers/dashboard.py
  - backend/app/routers/health.py
  - backend/app/routers/lecturers.py
  - backend/app/routers/topic_approval.py
  - backend/app/routers/topics.py
  - backend/app/schemas/__init__.py
  - backend/app/schemas/accounts.py
  - backend/app/schemas/auth.py
  - backend/app/schemas/cohorts.py
  - backend/app/schemas/common.py
  - backend/app/schemas/dashboard.py
  - backend/app/schemas/topic_approval.py
  - backend/app/schemas/topics.py
  - backend/app/seed.py
  - backend/app/services/__init__.py
  - backend/app/services/accounts.py
  - backend/app/services/ai_client.py
  - backend/app/services/dashboard.py
  - backend/app/services/title_check.py
  - backend/app/services/topic_approval.py
  - backend/app/services/topics.py
  - backend/docker-entrypoint.sh
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/test_accounts_rbac.py
  - backend/tests/test_auth.py
  - backend/tests/test_cohorts_rbac.py
  - backend/tests/test_topic_approval_rbac.py
  - backend/tests/test_topic_ownership.py
  - backend/tests/test_topic_registration.py
  - deploy/.env.example
  - deploy/README.md
  - deploy/apache/Dockerfile
  - deploy/apache/ntma.conf
  - deploy/api-login.sh
  - deploy/certs/gen-cert.sh
  - deploy/docker-compose.yml
  - deploy/dom-check.sh
  - deploy/e2e-uc1.sh
  - deploy/init.sh
  - deploy/mysql/initdb/01-test-db.sh
  - deploy/smoke-test.sh
  - deploy/sql.sh
  - frontend/src/App.tsx
  - frontend/src/api/client.ts
  - frontend/src/app/registry.ts
  - frontend/src/features/accounts/AccountsPage.tsx
  - frontend/src/features/accounts/api.ts
  - frontend/src/features/accounts/routes.tsx
  - frontend/src/features/auth/AuthBootstrap.tsx
  - frontend/src/features/auth/ForbiddenPage.tsx
  - frontend/src/features/auth/LoginPage.tsx
  - frontend/src/features/auth/RequireAuth.tsx
  - frontend/src/features/auth/routes.tsx
  - frontend/src/features/cohorts/CohortsPage.tsx
  - frontend/src/features/cohorts/api.ts
  - frontend/src/features/cohorts/routes.tsx
  - frontend/src/features/dashboard/BmDashboard.tsx
  - frontend/src/features/dashboard/DashboardPage.tsx
  - frontend/src/features/dashboard/GvDashboard.tsx
  - frontend/src/features/dashboard/SvDashboard.tsx
  - frontend/src/features/dashboard/api.ts
  - frontend/src/features/dashboard/routes.tsx
  - frontend/src/features/topic-approval/TopicApprovalPage.tsx
  - frontend/src/features/topic-approval/api.ts
  - frontend/src/features/topic-approval/routes.tsx
  - frontend/src/features/topics/TitleCheckAlert.tsx
  - frontend/src/features/topics/TopicDetailPage.tsx
  - frontend/src/features/topics/TopicFormPage.tsx
  - frontend/src/features/topics/TopicListPage.tsx
  - frontend/src/features/topics/api.ts
  - frontend/src/features/topics/constants.ts
  - frontend/src/features/topics/routes.tsx
  - frontend/src/layouts/AppLayout.tsx
  - frontend/src/main.tsx
  - frontend/src/stores/auth.ts
  - frontend/vite.config.ts
  - tools/check-erd-db.py
findings:
  critical: 1
  warning: 5
  info: 1
  total: 7
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-09-28
**Depth:** standard
**Files Reviewed:** 107
**Status:** issues_found

## Summary

Reviewed the full Phase 2 slice (monorepo scaffold, MySQL schema/migrations, FastAPI JWT+RBAC backend, React/Ant Design client, AI-stub title check) with priority on auth/JWT/cookie handling, RBAC/IDOR, SQL safety, upload limits, secrets, and the concurrency/state-machine correctness of topic registration and approval.

Overall the implementation is careful and defensive: `register_topic`/`submit_topic`/`topic_approval.approve`/`reject` all use single conditional `UPDATE` statements (not check-then-act) to close the well-known TOCTOU race windows, backed by a real DB-level unique constraint (`uk_de_tai_sv_hoat_dong` on the generated column `sinh_vien_id_dang_hoat_dong`) so the "1 active topic per student" and "1 student per topic" invariants hold even under true concurrency — confirmed by the two `test_topic_registration.py` race tests. RBAC is enforced server-side on every route (verified by the dedicated `test_every_api_route_declares_roles` test), ownership/scope checks in `topics.py`/`dashboard.py` are consistently narrowed before any other filter is applied, `LIKE`/`%`/`_` wildcard injection in search filters is escaped (`autoescape=True`), passwords are bcrypt-hashed directly (no passlib), and login uses a constant-time-ish dummy-hash comparison plus IP+username throttling.

That said, several issues remain, the most serious being that the application's own documented last line of defense against oversized request bodies can be bypassed outright, plus a handful of concurrency/robustness/config gaps below.

## Critical Issues

### CR-01: Request body size limit is bypassed when `Content-Length` is absent (chunked transfer encoding)

**File:** `backend/app/core/body_limit.py:29-41`
**Issue:** `MaxBodySizeMiddleware` is explicitly documented (lines 1-11) as the *real* enforcement point for the 26 MB request-body ceiling (D-12/NFR-06), because "Apache mod_proxy_http không tự thực thi `LimitRequestBody` cho nội dung được proxy tới backend". The middleware's check is:
```python
headers = dict(scope.get("headers") or [])
content_length = headers.get(b"content-length")
if content_length is not None:
    ...
    if too_large:
        return 413
await self.app(scope, receive, send)
```
If the request has no `Content-Length` header at all — which is the normal case for HTTP/1.1 `Transfer-Encoding: chunked` requests, or any client that simply omits it — `content_length` is `None`, the size check is skipped entirely, and the body is passed straight through to the app with **no limit**. Since this middleware is stated to be the sole real enforcement layer (Apache's `LimitRequestBody` in `ntma.conf` only protects the static `DocumentRoot`, not the proxied `/api` path), an attacker (or even a naive HTTP client library that streams a body) can send an arbitrarily large request body to any endpoint and it will be fully buffered/read by the ASGI app, risking memory/resource exhaustion (DoS) and defeating the documented NFR-06 threshold.
**Fix:** Do not rely on the `Content-Length` header alone. Either reject requests to non-trivial endpoints that use `Transfer-Encoding: chunked` without a body cap, or enforce the limit by counting bytes as they are actually read from `receive()` and aborting once `max_bytes` is exceeded, e.g.:
```python
async def __call__(self, scope, receive, send):
    if scope["type"] != "http":
        return await self.app(scope, receive, send)

    total = 0

    async def limited_receive():
        nonlocal total
        message = await receive()
        if message["type"] == "http.request":
            total += len(message.get("body", b""))
            if total > self.max_bytes:
                raise HTTPException(status_code=413)  # or send 413 directly and close
        return message

    await self.app(scope, limited_receive, send)
```
This closes the gap regardless of whether `Content-Length` is present.

## Warnings

### WR-01: `create_topic` / `update_topic` re-check cohort "open" state with check-then-act instead of an atomic guard

**File:** `backend/app/services/topics.py:203-260` (`create_topic`, `update_topic`), contrast with `submit_topic` (`:263-298`) and `register_topic` (`:392-433`)
**Issue:** `submit_topic` and `register_topic` correctly avoid TOCTOU races by embedding the "cohort must still be open" condition directly inside the single conditional `UPDATE ... WHERE ...` statement (comment at `:273-274` explicitly calls this out as intentional). `create_topic` and `update_topic`, however, call `_get_open_cohort_or_error(db, ...)` as a plain `SELECT` *before* a separate `INSERT`/`UPDATE`, with no re-validation at write time. Between that read and the final `db.commit()` — a window that can be multi-second when `payload.gui=True` triggers the (documented as potentially slow, Phase-4) AI title-check call at `:217` — a Bộ môn can close the cohort (`POST /api/cohorts/{id}/close`) and the new/edited topic will still be written with `trang_thai` `NHAP`/`CHO_DUYET` against what is now a closed cohort, violating the "đợt đã đóng chặn đề xuất mới" invariant that `submit_topic`/`register_topic` are careful to uphold atomically.
**Fix:** Fold the open-cohort check into the write itself (e.g. re-`SELECT ... FOR UPDATE` the cohort row inside the same transaction right before `db.add(topic)`/`db.flush()`, or add a `WHERE dot_do_an_id IN (SELECT id FROM dot_do_an WHERE trang_thai = 'DANG_MO')`-style guard analogous to `submit_topic`), and treat "0 rows affected / cohort now closed" as a 409 the same way the other two functions do.

### WR-02: Missing `cau_hinh_nguong` threshold row causes an unhandled 500 instead of graceful degradation

**File:** `backend/app/services/title_check.py:37-41` (`_get_threshold`)
**Issue:** `kiem_tra_ten` (used by `POST /topics/check-title`, `create_topic`, and `submit_topic`) calls `_get_threshold(db)` which does `.scalar_one()` on the `cau_hinh_nguong` row for `NGUONG_TEN_DE_TAI`. If that row is ever missing (deleted via direct DB access, a future migration mishap, or a fresh DB where migration 0004's seed insert was skipped/rolled back), `scalar_one()` raises `sqlalchemy.exc.NoResultFound`, which is not caught anywhere in this call path and will surface as an unhandled 500 to the user. This is inconsistent with the UC0.6/E2 design intent explicitly stated one function up ("không bao giờ chặn gửi đề xuất... khi AiClient lỗi trả về trang_thai LOI") — an AI-service outage is handled gracefully, but a missing threshold config is not, even though both are "duplicate-check infra unavailable" cases from the user's perspective.
**Fix:** Wrap the threshold lookup (or use `scalar_one_or_none()` with a documented fallback default, e.g. the same value as the migration's seed row) and treat a missing config the same way as `AiServiceError` — return `trang_thai=LOI` rather than raising.

### WR-03: `uvicorn --forwarded-allow-ips='*'` over-trusts `X-Forwarded-For`, weakening IP-keyed login throttling

**File:** `backend/docker-entrypoint.sh:10-15`, used by `backend/app/core/throttle.py` (`LoginThrottle`) via `_client_ip` in `backend/app/routers/auth.py:29-30`
**Issue:** The login brute-force throttle keys on `(request.client.host, dang_nhap.casefold())`. With `--proxy-headers --forwarded-allow-ips='*'`, uvicorn will trust an `X-Forwarded-For` header from *any* peer that can open a TCP connection to it, not just the Apache reverse proxy. The `api` service is not published to the host (`expose: "8001"` only in `docker-compose.yml`), so this is only reachable from other containers on the same compose network today — but any other container later added to that network (or a compromise of any existing one) can connect to `api:8001` directly and set an arbitrary `X-Forwarded-For` value, completely spoofing the IP half of the throttle key and evading the 5-failures/15-minute lockout for credential stuffing.
**Fix:** Restrict `--forwarded-allow-ips` to the Apache container's address (e.g. the compose service DNS name resolved at startup, or a fixed internal IP/CIDR for the `ntma` network) instead of `'*'`.

### WR-04: Logged-out / stale refresh tokens remain valid until natural expiry (no server-side revocation)

**File:** `backend/app/routers/auth.py:159-163` (`logout`), `backend/app/core/security.py:57-65` (`create_refresh_token`)
**Issue:** `POST /api/auth/logout` only deletes the httpOnly cookie client-side (`_delete_refresh_cookie`); the refresh JWT itself is stateless and carries no `jti`/session id that could be checked against a revocation store. If a refresh token cookie is exfiltrated (misconfigured proxy, browser/device compromise, log leakage, etc.) before logout, it remains fully valid for the rest of its `REFRESH_TOKEN_EXPIRE_MINUTES` window (default 480 minutes / 8 hours) even after the legitimate user logs out — the only mitigation available is Bộ môn locking the *entire account* (`bi_khoa`), which is a blunt, manual, administrator-driven instrument, not a per-session revocation.
**Fix:** Out of scope to fully solve in Phase 2, but worth tracking: add a minimal server-side revocation check (e.g. a `session_version`/`token_epoch` column on `tai_khoan` bumped on logout/password change and embedded as a claim, checked in `decode_token`/`refresh`), or persist a denylist of revoked `jti`s with TTL = remaining token lifetime.

### WR-05: `PUBLIC_ROUTES` in `deps.py` is unused in production code — its only consumer is a test

**File:** `backend/app/core/deps.py:20-29`, consumed only by `backend/tests/test_auth.py:113,131`
**Issue:** `PUBLIC_ROUTES` reads as if it were an allow-list actively enforced somewhere (e.g. a middleware gate), but no such enforcement exists — every route's actual protection comes from its own `Depends(require_role(...))`/`Depends(get_current_user)`. `PUBLIC_ROUTES` is in fact only referenced by `test_every_api_route_declares_roles`, which uses it purely to *skip* the small set of intentionally-public endpoints while asserting every other route declares role-based auth. This is a legitimate and valuable test, but keeping the set in the production `app/core/deps.py` module (rather than colocating it with the test, or clearly marking it test-support-only) invites a future contributor to assume it does something at runtime and rely on it incorrectly.
**Fix:** Either move `PUBLIC_ROUTES` into `tests/` (e.g. `tests/conftest.py`) since it is test-only fixture data, or add an explicit module docstring note that it is consumed only by the route-audit test and has no runtime effect.

## Info

### IN-01: Login throttle key is `(client_ip, username)`, not IP-only or global — easily distributed across usernames or source IPs

**File:** `backend/app/core/throttle.py:9-22`
**Issue:** Not a bug relative to the stated design (the docstring is explicit about the tradeoff), but worth flagging as a known limitation: because the throttle key includes the *specific* login identifier, an attacker performing a distributed credential-stuffing attack (many usernames from the same IP, or the same username from many source IPs/proxies) is not slowed down by this control — each `(ip, username)` pair gets its own independent 5-attempt budget. Combined with WR-03 above (spoofable IP), this narrows the effective protection further.
**Fix:** No code change required for Phase 2 scope; consider adding a secondary IP-only (or global) rate limit in a later phase if brute-force protection needs to be strengthened beyond the current per-pair budget.

---

_Reviewed: 2026-09-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
