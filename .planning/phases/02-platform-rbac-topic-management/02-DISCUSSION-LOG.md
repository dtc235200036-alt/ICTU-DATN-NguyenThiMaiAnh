# Phase 2: Platform, RBAC & Topic Management - Discussion Log

> **Audit trail only.** Auto mode (--auto): user asleep, recommended defaults selected.

**Date:** 2026-09-28
**Areas:** Repo layout, Database, Auth & session, Frontend, Deployment, Seed data

- [auto] Repo layout → monorepo backend/frontend/ai-service/deploy (recommended)
- [auto] Session storage → httpOnly refresh cookie + in-memory access token (recommended)
- [auto] Concurrency → DB unique constraints + transaction (recommended)
- [auto] Deployment → Docker Compose (mysql, api, apache httpd+mod_ssl self-signed) local-first (recommended)
- [auto] Seed → Faker vi_VN fixed seed, idempotent (recommended)

## Deferred Ideas

Remote server deployment (Phase 5); email notifications (v2).
