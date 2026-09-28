# Phase 3: Outline, Progress, Defense & Archive - Context

**Gathered:** 2026-09-28 (auto mode — user asleep; recommended defaults selected, review later)
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the working Phase 2 system (same backend/frontend/deploy stack) with UC2 Đề cương, UC3 Tiến độ, UC4 Bảo vệ, UC5 Kho đồ án and in-app notifications (UC0.5). Requirements: OUTL-01..03, PROG-01..03, DEFN-01..04, REPO-01..03, NOTF-01. AI checks stay on the **stub** (document check + archive ingest calls go through the AI client seam); the real AI service is Phase 4. Threshold UI (AISV-07) and real duplicate highlighting are Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Carried forward (locked by Phase 2 — do not revisit)
- Monorepo layout, FastAPI + SQLAlchemy 2.0 sync + Alembic, React + Vite + TS + Ant Design v5 (React 18.3) + TanStack Query, JWT access + httpOnly refresh cookie with token-version revocation, `require_role` on every route + ownership checks in services, NFC normalization at API boundary, docker compose `ntma` (mysql 8.4 / api / apache), AI client seam `app/services/ai_client.py` (`AiClient` protocol, stub mode), tests few and focused, `tools/check-erd-db.py` must stay green (any additive column is written back into erd.puml, lop-thuc-the.puml and the §3.2.3 data dictionary).

### File uploads (OUTL-01, PROG-01, DEFN-01)
- **D-01:** Accept only DOCX and PDF for outline / final report (progress report attachment optional, same types). Validate by extension **and** magic bytes (PDF `%PDF`, DOCX = ZIP containing `word/document.xml`); max 20 MB (fits the existing 25 MB body limit). [auto] Q: "Upload validation?" → Selected: "extension + magic bytes + size" (recommended)
- **D-02:** Files stored on a docker named volume mounted in `api` (outside Apache DocumentRoot), path `uploads/<loai>/<uuid>.<ext>`; original filename kept only in DB; downloads only via an authorized API endpoint (ownership/role checked), never a static URL. Each resubmission creates a new `tai_lieu_do_an` version row — nothing overwritten.
- **D-03:** Text extraction at upload time (python-docx / PyMuPDF per research STACK.md) stored for later AI use; extraction failure does not block submission (flag it).

### Duplicate-check integration (stub now)
- **D-04:** Outline and final-report submissions create a `ket_qua_kiem_tra_trung_lap` row in state `DANG_KIEM_TRA` and run the stub check via FastAPI `BackgroundTasks` → `HOAN_TAT` / `LOI`; UI shows the "đang kiểm tra / hoàn tất" panel (polling) on the SV page and on the GVHD review screen (MH-09, MH-14 skeleton). Phase 4 swaps only the client. [auto] → "BackgroundTasks + polling" (recommended, matches architecture §3.3.7)

### Progress milestones (PROG-01..03)
- **D-05:** Milestones (`moc_tien_do`) are defined per đợt by Bộ môn (name + due date); SV submits one report per milestone; "trễ mốc" = no report by due date (computed, not stored). Bộ môn dashboard lists all SV × milestones with late flags. [auto] → "Bộ môn defines milestones per đợt" (recommended)

### Defense (DEFN-01..04)
- **D-06:** Bộ môn creates `hoi_dong` (name, members from GV list, 3–5 members, one chủ tịch), schedules `lich_bao_ve` (date, time, room, SV list); the GVHD of a student may not sit on that student's committee (warn/block). Each member enters one overall score (0–10, one decimal) + comment; final score = arithmetic mean, shown only after Bộ môn "chốt" (finalize). Members see only reports of SV in their own committee.

### Archive (REPO-01..03)
- **D-07:** Finalized theses auto-insert into `do_an_kho` with metadata (khóa, tên đề tài, SV, GVHD, từ khóa, điểm, file). Search by khóa / từ khóa (LIKE on title + keywords, Vietnamese collation) / GVHD. Bộ môn CRUD + CSV import (columns documented) for past cohorts; every new/updated record calls `ai_client.ingest(...)` (stub records the call).

### Notifications (NOTF-01)
- **D-08:** `thong_bao` rows created in the same transaction as the triggering state change; header bell with unread count + dropdown list + mark-read; polling every 30 s via TanStack Query (no websockets). [auto] → "polling" (recommended — Apache/uvicorn simplicity)

### Scope/priority
- **D-09:** Plans split by UC; if time runs short, keep the demo chain outline → defense → archive first, progress and notifications after (roadmap note).

### Claude's Discretion
- Exact routes (within §3.3.6 groups), page layout details within mockups MH-08..MH-14, pagination sizes, CSV import format details, which Phase-3 tables to migrate in which plan (names must match ERD).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md` + `csdl/erd.puml` — tables `de_cuong`, `tai_lieu_do_an`, `luot_duyet_de_cuong`, `moc_tien_do`, `bao_cao_tien_do`, `hoi_dong`, `thanh_vien_hoi_dong`, `lich_bao_ve`, `diem_bao_ve`, `do_an_kho`, `thong_bao`, `ket_qua_kiem_tra_trung_lap`, `chi_tiet_trung_lap`
- `docs/chuong-3-thiet-ke/01-so-do-lop-thuc-the.md` + `so-do-lop/trang-thai-de-cuong.puml`, `trang-thai-kiem-tra-trung-lap.puml`
- `docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md` §3.3.5–3.3.7 (AI contract, route groups, async document-check sequence)
- `docs/chuong-3-thiet-ke/04-thiet-ke-giao-dien.md` + `mockup/mh-08..mh-14.html` (+ mh-02..04 dashboards)
- `docs/chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md` (FR-DC/TD/BV/KHO/TB), `04-yeu-cau-phi-chuc-nang.md`, UC specs `07`–`11`
- `.planning/phases/02-platform-rbac-topic-management/02-0*-SUMMARY.md` (patterns: services/routers/schemas split, deploy scripts, CDP self-check, e2e script style), `02-REVIEW-FIX.md`
- `.planning/research/PITFALLS.md` (upload security, extraction noise), `.planning/research/STACK.md`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/core/deps.py` (`require_role`, current user), `app/core/body_limit.py`, `app/services/ai_client.py` (stub seam), `app/services/title_check.py` (persisted check pattern), `app/services/topics.py` (conditional-UPDATE state transitions, ownership helpers), `app/routers/dashboard.py`
- Frontend: `api/client.ts` (refresh-on-401, `getErrorMessage`), `AppLayout` + `collectRoutes()` role menus, `features/topics/*` page patterns, `ForbiddenPage`
- Deploy: `deploy/smoke-test.sh`, `deploy/e2e-uc1.sh`, `deploy/README.md`, `tools/check-erd-db.py`

### Established Patterns
- State transitions via single conditional UPDATE; RBAC route coverage test; Alembic numbered migrations (next = 0006).

### Integration Points
- Topic in state `DA_PHAN_CONG` (assigned GVHD) is the entry point for UC2.
- Phase 4 replaces stub in `ai_client.py`; keep `check_document`/`ingest` signatures matching §3.3.5.

</code_context>

<specifics>
## Specific Ideas

- Add `deploy/e2e-uc2-5.sh` in the same style as `e2e-uc1.sh` proving outline → progress → defense → archive end-to-end through Apache.

</specifics>

<deferred>
## Deferred Ideas

- Email notifications, committee schedule conflict warnings, grade export (v2 per REQUIREMENTS).
- Real AI duplicate detection + threshold config UI — Phase 4.

</deferred>

---

*Phase: 03-outline-progress-defense-archive*
*Context gathered: 2026-09-28 (auto)*
