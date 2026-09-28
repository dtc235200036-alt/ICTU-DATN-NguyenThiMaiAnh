# Phase 3: Outline, Progress, Defense & Archive - Research

**Researched:** 2026-09-28
**Domain:** Extending an existing FastAPI (sync SQLAlchemy 2.0 + MySQL 8) / React (Vite + AntD + TanStack Query) monolith-per-service with file upload/extraction, async stub duplicate-check, committee scoring, archive search+import, and in-app notifications.
**Confidence:** HIGH (existing-code patterns, DB/architecture contracts, FastAPI/Starlette internals — all read/grepped this session) / MEDIUM (exact new route paths, exact stub-algorithm shape — Claude's Discretion per CONTEXT.md) / LOW (none — no unverified external claims used)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Carried forward (locked by Phase 2 — do not revisit):** Monorepo layout, FastAPI + SQLAlchemy 2.0 sync + Alembic, React + Vite + TS + Ant Design v5 (React 18.3) + TanStack Query, JWT access + httpOnly refresh cookie with token-version revocation, `require_role` on every route + ownership checks in services, NFC normalization at API boundary, docker compose `ntma` (mysql 8.4 / api / apache), AI client seam `app/services/ai_client.py` (`AiClient` protocol, stub mode), tests few and focused, `tools/check-erd-db.py` must stay green (any additive column is written back into erd.puml, lop-thuc-the.puml and the §3.2.3 data dictionary).

**File uploads (OUTL-01, PROG-01, DEFN-01):**
- **D-01:** Accept only DOCX and PDF for outline / final report (progress report attachment optional, same types). Validate by extension **and** magic bytes (PDF `%PDF`, DOCX = ZIP containing `word/document.xml`); max 20 MB (fits the existing 25 MB body limit).
- **D-02:** Files stored on a docker named volume mounted in `api` (outside Apache DocumentRoot), path `uploads/<loai>/<uuid>.<ext>`; original filename kept only in DB; downloads only via an authorized API endpoint (ownership/role checked), never a static URL. Each resubmission creates a new `tai_lieu_do_an` version row — nothing overwritten.
- **D-03:** Text extraction at upload time (python-docx / PyMuPDF per research STACK.md) stored for later AI use; extraction failure does not block submission (flag it).

**Duplicate-check integration (stub now):**
- **D-04:** Outline and final-report submissions create a `ket_qua_kiem_tra_trung_lap` row in state `DANG_KIEM_TRA` and run the stub check via FastAPI `BackgroundTasks` → `HOAN_TAT` / `LOI`; UI shows the "đang kiểm tra / hoàn tất" panel (polling) on the SV page and on the GVHD review screen (MH-09, MH-14 skeleton). Phase 4 swaps only the client.

**Progress milestones (PROG-01..03):**
- **D-05:** Milestones (`moc_tien_do`) are defined per đợt by Bộ môn (name + due date); SV submits one report per milestone; "trễ mốc" = no report by due date (computed, not stored). Bộ môn dashboard lists all SV × milestones with late flags.

**Defense (DEFN-01..04):**
- **D-06:** Bộ môn creates `hoi_dong` (name, members from GV list, 3–5 members, one chủ tịch), schedules `lich_bao_ve` (date, time, room, SV list); the GVHD of a student may not sit on that student's committee (warn/block). Each member enters one overall score (0–10, one decimal) + comment; final score = arithmetic mean, shown only after Bộ môn "chốt" (finalize). Members see only reports of SV in their own committee.

**Archive (REPO-01..03):**
- **D-07:** Finalized theses auto-insert into `do_an_kho` with metadata (khóa, tên đề tài, SV, GVHD, từ khóa, điểm, file). Search by khóa / từ khóa (LIKE on title + keywords, Vietnamese collation) / GVHD. Bộ môn CRUD + CSV import (columns documented) for past cohorts; every new/updated record calls `ai_client.ingest(...)` (stub records the call).

**Notifications (NOTF-01):**
- **D-08:** `thong_bao` rows created in the same transaction as the triggering state change; header bell with unread count + dropdown list + mark-read; polling every 30 s via TanStack Query (no websockets).

**Scope/priority:**
- **D-09:** Plans split by UC; if time runs short, keep the demo chain outline → defense → archive first, progress and notifications after (roadmap note).

### Claude's Discretion
Exact routes (within §3.3.6 groups), page layout details within mockups MH-08..MH-14, pagination sizes, CSV import format details, which Phase-3 tables to migrate in which plan (names must match ERD).

### Deferred Ideas (OUT OF SCOPE)
- Email notifications, committee schedule conflict warnings, grade export (v2 per REQUIREMENTS).
- Real AI duplicate detection + threshold config UI — Phase 4.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OUTL-01 | SV nộp đề cương DOCX/PDF, mỗi lần nộp tạo phiên bản mới | §File Upload Pattern, §Data Model — `tai_lieu_do_an` versioning, shared `documents` service |
| OUTL-02 | GVHD xem đề cương cùng kết quả kiểm tra trùng lặp trên màn duyệt | §Async Duplicate-Check Flow, MH-09/MH-14 structure |
| OUTL-03 | GVHD duyệt/yêu cầu sửa kèm nhận xét; SV sửa nộp lại tới khi duyệt | §State Machines — `de_cuong` FSM (already documented in `trang-thai-de-cuong.puml`), `luot_duyet_de_cuong` |
| PROG-01 | SV nộp báo cáo tiến độ theo mốc cố định (nội dung + file tùy chọn) | §Progress Model — `bao_cao_tien_do` upsert-not-version pattern |
| PROG-02 | GVHD nhận xét + đánh giá từng báo cáo | §Progress Model, §Notifications |
| PROG-03 | Bộ môn xem dashboard tiến độ toàn khoa, đánh dấu SV trễ mốc | §Progress Model — computed "trễ mốc", reuse `dashboard.py` pattern |
| DEFN-01 | SV nộp báo cáo cuối; kích hoạt kiểm tra trùng lặp | §File Upload Pattern (shared with OUTL-01), §Async Duplicate-Check Flow |
| DEFN-02 | Bộ môn lập hội đồng, xếp lịch, danh sách SV | §Defense/Committee Data Model, GVHD-exclusion check |
| DEFN-03 | GV hội đồng xem báo cáo + kết quả trùng lặp của SV thuộc hội đồng mình, nhập điểm+nhận xét | §Defense/Committee Data Model — ownership-by-committee-membership scoping |
| DEFN-04 | Tính điểm = TB cộng; Bộ môn chốt; SV xem lịch/kết quả | §Defense/Committee Data Model — "chốt" transaction, triggers UC5.2 |
| REPO-01 | Đồ án chốt tự động vào kho với metadata | §Archive Model — auto-insert transaction chained off DEFN-04's chốt |
| REPO-02 | Tìm kiếm/lọc kho theo khóa/từ khóa/GVHD, xem chi tiết | §Archive Model — reuse `.contains(nfc(q), autoescape=True)` pattern already in `topics.py` |
| REPO-03 | Bộ môn CRUD kho + import CSV khóa cũ; mỗi bản ghi mới/sửa gọi `ai_client.ingest` | §Archive Model, §AI Client Seam Extension, §CSV Import Pattern |
| NOTF-01 | Thông báo in-app khi duyệt/từ chối, nhận xét mới, phân hội đồng, có lịch bảo vệ | §Notifications — same-transaction creation pattern, retrofit into existing `topic_approval.py` |
</phase_requirements>

## Summary

Phase 3 is a pure vertical extension of the already-working Phase 2 codebase — no new services, no new deployment components, same sync-SQLAlchemy/FastAPI/MySQL/Apache stack. The main net-new engineering surface is: (1) a **file upload/extraction/download subsystem** that does not exist yet anywhere in the codebase (`python-docx`, `PyMuPDF`, `python-multipart` are **not currently in `backend/pyproject.toml`** — confirmed by inspecting the actual `.venv`, not just training memory); (2) **extending the `AiClient` protocol/stub** in `app/services/ai_client.py`, which today only implements `check_title` — Phase 3 needs `check_document` and `ingest` added to both the `Protocol` and `AiClientStub`, matching the `/check-document` and `/ingest` payload shapes documented in `docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md` §3.3.5, so Phase 4 can swap only the class; (3) **11 new `thesis_core` tables** (`de_cuong`, `tai_lieu_do_an`, `luot_duyet_de_cuong`, `moc_tien_do`, `bao_cao_tien_do`, `hoi_dong`, `thanh_vien_hoi_dong`, `lich_bao_ve`, `diem_bao_ve`, `do_an_kho`, `thong_bao`) plus one **FK backfill** on the already-existing `ket_qua_kiem_tra_trung_lap.tai_lieu_do_an_id` column (currently a bare `BigInteger` with a code comment marking it for this exact phase); and (4) a **notification-emission retrofit** into the existing Phase 2 `topic_approval.py` service, since NOTF-01 explicitly covers topic approve/reject, which currently does not create `thong_bao` rows.

Every established Phase 2 pattern transfers directly: conditional-`UPDATE`-with-`rowcount` for state transitions, `require_role` + service-level ownership predicates, `NFCModel`/`nfc()` at every text ingestion boundary, VARCHAR+CHECK-constraint status columns (not SQLAlchemy native `Enum`, which is reserved for the fixed 3-role `vai_tro`), and "compute before opening the write transaction, persist in the same commit" for anything that must be atomic with a state change (already proven for title-check; reuse verbatim for document-check-row-creation, notification-creation, and the defense "chốt" → archive-insert chain).

**Primary recommendation:** Build one shared `app/services/documents.py` module (validate → save → version → extract-text → schedule background check) reused identically by outline submission, progress-report attachments, and final-report submission — do not fork three separate upload code paths. Extend `ai_client.py`'s `Protocol`/`AiClientStub` with `check_document`/`ingest` before writing any router that calls them. Add a shared `app/services/notifications.py` with one `create()` helper (add-not-commit, same pattern as `title_check.luu_ket_qua`) and call it from every state-changing service in this phase **and** retrofit it into `topic_approval.py`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| File validation (extension/magic-bytes/size) | API / Backend | — | Server-side trust boundary; client-side checks are UX-only, never authoritative (matches existing `MaxBodySizeMiddleware` pattern) |
| File storage (disk, versioned naming) | API / Backend | — | Owns `uploads/` docker volume; AI service/DB never store bytes (§3.2.1, §3.3.8 schema-ownership + Anti-Pattern 2) |
| Text extraction (DOCX/PDF → plain text, NFC) | API / Backend | — | Web API "owns file storage" per `03-kien-truc-he-thong.md` §3.3.2; AI service never touches files (Anti-Pattern 2) |
| Duplicate-check orchestration (stub call, state transition) | API / Backend | — | `ai_client.py` seam is the single AI-calling component (§3.3.2); async via in-process `BackgroundTasks` (§3.3.8) |
| Async job execution | API / Backend | — | FastAPI `BackgroundTasks`, in-process, own `SessionLocal()` per task (see Pitfall below) |
| State machine transitions (đề cương, kiểm tra trùng lặp, hội đồng, chốt) | API / Backend + Database | — | Conditional `UPDATE ... WHERE` pattern already established in `topics.py`; constraints enforced by MySQL UNIQUE/CHECK |
| Committee membership / scoring authorization | API / Backend | — | Row-level ownership: GV sees only SV in own `hoi_dong` (DEFN-03/E1 mandates 403, not UI hiding — Pitfall 9 in PITFALLS.md) |
| Score aggregation ("chốt") | API / Backend + Database | — | `AVG()` computed in the same transaction as the `da_chot` flip, guarded by count-equality check (§3.2.5-d) |
| Archive search (khóa/từ khóa/GVHD) | API / Backend + Database | — | DB already `utf8mb4_vietnamese_ci`; reuse `.contains(nfc(q), autoescape=True)` — no new tooling needed |
| CSV import | API / Backend | — | Python stdlib `csv` module, no new dependency; per-row validation, partial success (UC5.4/E1) |
| Notification creation | API / Backend + Database | — | Same-transaction `db.add()` (no commit) alongside the triggering state change, matching `title_check.luu_ket_qua` |
| Notification delivery (bell, unread count, polling) | Browser / Client | — | TanStack Query `refetchInterval: 30_000`, already the project's only "live update" mechanism (D-08 rejects websockets) |
| Upload/polling UI (Steps/Upload/Descriptions/Tag) | Browser / Client | — | Ant Design v5 components already installed (`antd@^5.29`); no new frontend dependency |
| File download | API / Backend | — | Authorized endpoint returning `starlette.responses.FileResponse`, never a static Apache-served path (D-02, §3.3.3) |

## Standard Stack

### Core (new backend dependencies — none currently in `backend/pyproject.toml`)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `python-docx` | 1.2.0 `[VERIFIED: pip index versions, backend/.venv]` | DOCX text extraction (walk `document.paragraphs`, body-only by default) | Mature, single-purpose; `document.paragraphs` already excludes header/footer sections (accessed separately via `section.header`/`section.footer`) so naive iteration is already boilerplate-safe on that axis (PITFALLS.md #4) |
| `pymupdf` (import name `fitz`) | 1.28.2 `[VERIFIED: pip index versions, backend/.venv]` | PDF text extraction | Fast, correct diacritic extraction for Word-exported PDFs (no OCR needed — only input source is DOCX/PDF export per project constraints) |
| `python-multipart` | 0.0.32 `[VERIFIED: pip index versions, backend/.venv]` | Required by FastAPI/Starlette for any `UploadFile`/form-data route | Not a transitive default in current FastAPI/Starlette — must be an explicit dependency or upload routes 500 at import/request time |

**Installation:**
```bash
cd backend && uv add python-docx pymupdf python-multipart
```

### Supporting (already installed — no action needed)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `antd` | ^5.29.0 `[VERIFIED: frontend/package.json]` | `Upload`, `Steps`, `Descriptions`, `Tag`, `Badge`, `Dropdown` for MH-08/09/11/12/13/14 | All UI primitives this phase needs already ship in the installed AntD version — confirmed no `Upload`/`Steps` usage exists yet in `frontend/src` (Phase 3 is the first consumer) |
| `@tanstack/react-query` | ^5.104.0 `[VERIFIED: frontend/package.json]` | Polling (duplicate-check status, notifications) via `refetchInterval` | Already the project's server-state layer (Phase 2); no new library for "live-ish" updates |
| `axios` | ^1.20.0 `[VERIFIED: frontend/package.json]` | `multipart/form-data` upload via `FormData` + existing `api` client | Reuse `frontend/src/api/client.ts` — its refresh-on-401 interceptor already applies to upload requests unmodified |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `python-docx` paragraph iteration | `docx2python` | Adds structured header/footer/table extraction the phase doesn't need yet (real de-boilerplating is a Phase-4/AI-service concern per `ARCHITECTURE.md` Anti-Pattern 2 — Web API in Phase 3 only needs *a* text blob for the stub, not clean chunking) |
| `pymupdf` | `pdfplumber` | Slower, only worth it for table-layout-aware extraction; not needed for this phase's "extract text, don't block on failure" requirement |
| Stdlib `csv` for import | `pandas` | `pandas` is a heavy dependency for a one-off bulk-insert screen; stdlib `csv.DictReader` is sufficient and keeps `pyproject.toml` lean |

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `python-docx` | PyPI | latest release 2025-06 | unknown (seam has no download-count signal for PyPI) | `github.com/python-openxml/python-docx` | SUS (`unknown-downloads` only) | Approved — well-known maintainer org, matches `STACK.md` recommendation, confirmed present on PyPI via `pip index versions` |
| `pymupdf` | PyPI | latest release 2026-08 | unknown | `github.com/pymupdf/pymupdf` | SUS (`unknown-downloads` only) | Approved — same signal gap, established repo/maintainer, matches `STACK.md` |
| `python-multipart` | PyPI | latest release 2026-06 | unknown | `github.com/Kludex/python-multipart` | SUS (`unknown-downloads` only) | Approved — maintained by a core Starlette/FastAPI contributor (`Kludex`), required transitive dependency of FastAPI's own upload docs |

**Packages removed due to `[SLOP]` verdict:** none.
**Packages flagged as suspicious `[SUS]`:** all three flagged **only** because the legitimacy seam could not fetch a PyPI download-count signal (`unknown-downloads`), not because of any actual red flag (all three have real, long-lived GitHub repos matching well-known maintainers, and are the exact packages already named in this project's own `.planning/research/STACK.md`). Recommend the planner still add one lightweight `checkpoint:human-verify` before the first `uv add` in the plan, per protocol, but this is a low-risk formality — do not spend meaningful plan budget re-verifying beyond that.

## Architecture Patterns

### System Architecture Diagram — Outline submission → async duplicate check → GVHD review

```
SV browser (MH-08)                                                          GVHD browser (MH-09/14)
     │ multipart POST /api/outlines/{de_tai_id}/submit                             │
     ▼                                                                             │
Web API router (outlines.py)                                                       │
     │ 1. require_role(SINH_VIEN) + ownership check (de_tai.sinh_vien_id)          │
     │ 2. documents.validate_file() — ext + magic bytes + size                     │
     ▼                                                                             │
documents.py service                                                               │
     │ 3. save bytes -> uploads/DE_CUONG/<uuid>.<ext> (docker volume)              │
     │ 4. INSERT tai_lieu_do_an (so_phien_ban = max+1)                             │
     │ 5. extract_text() best-effort (python-docx/PyMuPDF, NFC) — never blocks     │
     │ 6. INSERT ket_qua_kiem_tra_trung_lap (trang_thai=DANG_KIEM_TRA)             │
     │ 7. db.commit()  <- all of 3-6 in ONE transaction                           │
     │ 8. response 202 sent to SV browser ────────────────────────────────────────┤ (SV sees "đang kiểm tra")
     ▼ (BackgroundTasks — runs AFTER response is sent, own SessionLocal())         │
run_document_check()                                                              │
     │ 9. ai_client.check_document(ref_id, text) [stub]                           │
     │ 10a. success -> UPDATE ket_qua... SET trang_thai=HOAN_TAT, ty_le_tong=...  │
     │      + INSERT chi_tiet_trung_lap rows; commit                             │
     │ 10b. exception (ANY) -> UPDATE ... SET trang_thai=LOI; commit             │  <- must catch broadly,
     └──────────────────────────────────────────────────────────────────────────►│     Starlette does not
                                                                                   │     catch background-task
GVHD opens MH-09 -> GET /api/outlines/{de_tai_id} -> latest tai_lieu_do_an        │     exceptions (verified)
        + its ket_qua_kiem_tra_trung_lap (poll every N s while DANG_KIEM_TRA) ────┘
```

### Recommended Project Structure (additions to existing `backend/app/`)

```
backend/app/
├── models/
│   ├── de_cuong.py              # DeCuong, TaiLieuDoAn, LuotDuyetDeCuong
│   ├── tien_do.py               # MocTienDo, BaoCaoTienDo
│   ├── bao_ve.py                # HoiDong, ThanhVienHoiDong, LichBaoVe, DiemBaoVe
│   ├── kho.py                   # DoAnKho
│   └── thong_bao.py             # ThongBao
├── services/
│   ├── documents.py             # shared: validate/save/version/extract — used by outline+progress+defense
│   ├── outlines.py               # UC2.1-2.3 state machine + review
│   ├── progress.py               # UC3.1-3.4
│   ├── defense.py                # UC4.1-4.5 (committee, schedule, scoring, chốt)
│   ├── archive.py                # UC5.1-5.4 (search, CRUD, CSV import)
│   ├── notifications.py          # shared create() helper + list/mark-read
│   └── ai_client.py              # EXTEND: add check_document, ingest to Protocol + Stub
├── routers/
│   ├── outlines.py / progress.py / defense.py / archive.py / notifications.py
└── alembic/versions/
    ├── 0006_de_cuong_tai_lieu.py          # de_cuong, tai_lieu_do_an, luot_duyet_de_cuong, FK backfill on ket_qua_kttl
    ├── 0007_tien_do.py                    # moc_tien_do, bao_cao_tien_do
    ├── 0008_bao_ve.py                     # hoi_dong, thanh_vien_hoi_dong, lich_bao_ve, diem_bao_ve
    └── 0009_kho_thong_bao.py              # do_an_kho, thong_bao
```

Frontend mirrors the existing `features/<domain>/{api.ts,routes.tsx,*Page.tsx}` convention (see `features/topics/`, `features/topic-approval/`): add `features/outlines/`, `features/progress/`, `features/defense/`, `features/archive/`, `features/notifications/`.

### Pattern 1: Shared upload/extraction service, not three forks

**What:** One `documents.py` with `validate_file(upload: UploadFile) -> bytes`, `save_version(db, de_tai_id, loai, content, ten_goc, de_cuong_id=None) -> TaiLieuDoAn`, `extract_text(path, dinh_dang) -> str | None`.
**When to use:** Every place this phase accepts a DOCX/PDF: outline submit (OUTL-01), progress-report optional attachment (PROG-01), final-report submit (DEFN-01). Also the basis for archive import file references (REPO-03) if CSV rows include a file per record.
**Example (magic-byte validation, `[ASSUMED]` — standard technique, not tool-verified this session but low-risk/well-established):**
```python
import zipfile, io

PDF_MAGIC = b"%PDF-"

def _is_valid_pdf(content: bytes) -> bool:
    return content.startswith(PDF_MAGIC)

def _is_valid_docx(content: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            return "word/document.xml" in zf.namelist()
    except zipfile.BadZipFile:
        return False
```

### Pattern 2: Extend the AI client seam BEFORE writing routers that call it

**What:** `app/services/ai_client.py` (read in full this session) currently defines only:
```python
class AiClient(Protocol):
    def check_title(self, text: str, top_k: int = 5) -> dict: ...
```
`[VERIFIED: backend/app/services/ai_client.py:19-22]` — there is no `check_document` or `ingest` method on the `Protocol` or on `AiClientStub`. D-04 (document duplicate check) and D-07 (archive ingest) both require these. Phase 3 must add both to the `Protocol` and implement stub versions on `AiClientStub`, matching the §3.3.5 contract shapes documented in `03-kien-truc-he-thong.md`:
- `check_document(ref_id: int, text: str, top_k: int = 5) -> dict` → `{"ty_le_tong": float, "do_an_trung": [...], "chi_tiet": [{"doan_nguon", "doan_trung", "vi_tri", "ty_le"}]}`
- `ingest(ref_id: int, loai: str, text: str) -> dict` → `{"chunk_count": int, "indexed": true}`

**When to use:** Every duplicate-check/archive-insert call site. Never call `httpx`/a real AI service directly from a router — the canonical_refs note in CONTEXT.md is explicit: "Phase 4 replaces stub in `ai_client.py`; keep `check_document`/`ingest` signatures matching §3.3.5" — so the stub's method signatures ARE the interface contract, not an implementation detail.
**Stub algorithm (Claude's Discretion, recommend):** reuse the existing Jaccard-on-NFC-casefolded-tokens approach (`_tokenize`/`_jaccard_percent`, already in `ai_client.py`) against a `document_corpus_provider` that reads other `tai_lieu_do_an` rows' extracted text (same shape as `_corpus_provider_factory` for titles) — keeps the stub deterministic and testable, consistent with the Phase 2 precedent (`AiClientStub` scored deterministic Jaccard similarity — see STATE.md decision log).

### Pattern 3: Same-transaction notification creation, reused via one helper

**What:** `app/services/notifications.py::create(db, tai_khoan_id, loai, noi_dung, lien_ket=None)` — builds a `ThongBao` and `db.add()`s it, **does not call `db.commit()`** (caller commits alongside the state change it announces), exactly mirroring the already-proven pattern in `title_check.luu_ket_qua` (`db.add(ket_qua); db.flush()` — caller commits).
**When to use:** Topic approve/reject (retrofit into existing `topic_approval.py`), outline review (OUTL-03), progress comment (PROG-02), committee assignment + schedule (DEFN-02), defense chốt (DEFN-04).
**Example:**
```python
# app/services/notifications.py
def create(db: Session, tai_khoan_id: int, loai: str, noi_dung: str, lien_ket: str | None = None) -> ThongBao:
    tb = ThongBao(tai_khoan_id=tai_khoan_id, loai=loai, noi_dung=noi_dung,
                   lien_ket=lien_ket, da_doc=False, thoi_diem=datetime.now(timezone.utc).replace(tzinfo=None))
    db.add(tb)
    db.flush()
    return tb

# in outlines_service.review_outline(...), same transaction as the state UPDATE:
notifications.create(db, sv_tai_khoan_id, "DE_CUONG_DUYET", f"Đề cương của bạn đã được duyệt", lien_ket=f"/de-cuong/{de_tai_id}")
db.commit()
```

### Pattern 4: Background task owns its own DB session — never reuse the request's `Depends(get_db)` session

**What goes wrong if skipped:** `app/core/db.py` exposes `SessionLocal` (a `sessionmaker`) and `get_db()` which does `db = SessionLocal(); yield db; finally: db.close()` `[VERIFIED: backend/app/core/db.py:12-20]`. If a router does `bg.add_task(run_document_check, db, ...)` passing the **request-scoped** session, two independent problems compound: (a) per current FastAPI/Starlette docs, yield-dependency cleanup runs *after* background tasks (`[CITED: fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/]`) so the session object is not yet closed when the task starts, but relying on that exact ordering across FastAPI versions is fragile and undocumented as a stability guarantee for this use case; (b) more fundamentally, `starlette.background.BackgroundTask.__call__` (`[VERIFIED: backend/.venv/lib/python3.12/site-packages/starlette/background.py]`) has no exception handling, and none of the four call sites in `starlette/responses.py` that invoke `await self.background()` wrap it in try/except either (`[VERIFIED: backend/.venv/lib/python3.12/site-packages/starlette/responses.py:171-172,263-264,284-285,390-391]`) — an uncaught exception inside the task is logged by the ASGI server and silently swallowed from the application's perspective. If the task shares the request's session and something goes wrong mid-task, the row is left in `DANG_KIEM_TRA` forever, **violating the explicit invariant** in `trang-thai-kiem-tra-trung-lap.puml`: *"một bản ghi không bao giờ ở mãi trạng thái Đang kiểm tra"*.

**How to avoid:** The background function opens its own `db = SessionLocal()`, wraps the entire body in `try/except Exception` (broad, not just `AiServiceError`), and in the `except` branch still transitions the row to `LOI` and commits, then `finally: db.close()`. Do not pass the request's `Session` into `bg.add_task(...)` at all — pass only the `ket_qua_id`/`tai_lieu_do_an_id` (plain ints) and re-fetch inside the task.

```python
def run_document_check(ket_qua_id: int, tai_lieu_do_an_id: int, text: str) -> None:
    db = SessionLocal()
    try:
        raw = get_ai_client(db).check_document(tai_lieu_do_an_id, text)
        # ... update ket_qua row to HOAN_TAT + insert chi_tiet rows ...
        db.commit()
    except Exception:
        db.rollback()
        db.execute(update(KetQuaKiemTraTrungLap).where(KetQuaKiemTraTrungLap.id == ket_qua_id).values(trang_thai=LOI))
        db.commit()
    finally:
        db.close()
```

### Anti-Patterns to Avoid
- **Re-forking upload validation per UC:** three copies of magic-byte checking is exactly how one of them ends up unpatched — one shared `documents.py`.
- **SQLAlchemy native `Enum` for new status columns:** the project's own convention (see migration `0004`) uses `VARCHAR(20/30) + CheckConstraint("col IN (...)")` for every status/type column except `tai_khoan.vai_tro`. Follow this for `de_cuong.trang_thai`, `tai_lieu_do_an.loai`/`dinh_dang`, `hoi_dong`/`lich_bao_ve` fields, `do_an_kho.nguon`/`trang_thai_index`, etc. — do not introduce native MySQL `ENUM` here, it breaks the established `check-erd-db.py`-friendly VARCHAR-typed data-dictionary convention.
- **AI service reading files directly / receiving raw bytes:** never send file bytes to `ai_client.check_document`/`ingest` — only extracted `text` strings, per Anti-Pattern 2 in `ARCHITECTURE.md` and the §3.3.5 contract (`ai_client` methods take `text: str`, never `UploadFile`/`bytes`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vietnamese-diacritic filename in `Content-Disposition` on download | Manual RFC 5987 `filename*=UTF-8''...` header encoding | `starlette.responses.FileResponse(path, filename=ten_goc)` | Starlette already does this correctly: `content_disposition_filename = quote(self.filename); if != self.filename: filename*=utf-8''...; else filename="..."` `[VERIFIED: backend/.venv/lib/python3.12/site-packages/starlette/responses.py:322-328]` — just pass `filename=` and stop |
| CSV import parsing | Hand-rolled line-splitting or a `pandas` dependency | Stdlib `csv.DictReader` | Sufficient for a bulk-insert admin screen; per-row try/except for the partial-success requirement (UC5.4/E1) |
| Vietnamese-aware search/sort | Custom collation logic, custom Vietnamese string normalization for sorting | MySQL `utf8mb4_vietnamese_ci` (already the DB-level default per §3.2.1) + `.contains(nfc(q), autoescape=True)` (already proven in `topics.py:397`) | The collation is already correct at the schema level; only NFC-normalize the query string and let MySQL do the rest |
| Score-average + finalize consistency | Ad hoc "read count, then decide" check-then-act | The existing project convention: guard with a `WHERE` clause on the `UPDATE` itself (`da_chot = FALSE`) plus an application-level `COUNT(diem_bao_ve) == COUNT(thanh_vien_hoi_dong)` check inside the same transaction (already specified in §3.2.5-d) | Matches `register_topic`'s conditional-UPDATE-with-rowcount pattern already proven race-safe in this codebase |
| DOCX/PDF type sniffing | Trusting `UploadFile.content_type` (client-supplied, spoofable) | Magic-byte check on the actually-read bytes (`%PDF-` / zip + `word/document.xml`) | PITFALLS.md #8 — extension/MIME-type alone is a well-documented upload-security hole |

**Key insight:** Every "don't hand-roll" item above is not a new library to add — it's an existing verified capability (Starlette's own `FileResponse`, the DB's own collation, this codebase's own conditional-UPDATE convention) that a rushed implementation would otherwise reinvent worse.

## Runtime State Inventory

Not applicable — Phase 3 is additive-only (new tables, new routes, new frontend features). No rename/refactor/migration-of-meaning is involved. **Nothing found in this category** — verified by reading CONTEXT.md's decision log (all D-01..D-09 describe new capabilities, none describe renaming/moving existing concepts) and by inspecting `git status`/`STATE.md` (Phase 2 just completed, no in-flight renames pending).

## Common Pitfalls

### Pitfall 1: Background task exception silently strands a row in `DANG_KIEM_TRA`
**What goes wrong:** Any unhandled exception inside the `BackgroundTasks`-scheduled document-check function (bad file, AI client throwing something other than `AiServiceError`, a `DetachedInstanceError` from touching an ORM object across sessions) is swallowed by Starlette with no HTTP-visible symptom — the request already got its `202`.
**Why it happens:** `starlette.background.BackgroundTask.__call__` and every `Response` subclass that invokes it have zero exception handling (verified by reading the actual installed source this session).
**How to avoid:** Wrap the ENTIRE background function body in a broad `try/except Exception`, and on any exception, still flip the row to `LOI` in a fresh transaction before re-raising/logging. Never let the `except` branch be `except AiServiceError` only.
**Warning signs:** Rows stuck at `DANG_KIEM_TRA` indefinitely in manual testing; GVHD review screen (MH-09) permanently shows "đang kiểm tra".

### Pitfall 2: Migration ordering — `tai_lieu_do_an` must exist before the `ket_qua_kiem_tra_trung_lap.tai_lieu_do_an_id` FK can be added
**What goes wrong:** `ket_qua_kiem_tra_trung_lap.tai_lieu_do_an_id` already exists as a bare nullable `BigInteger` (no FK) — added deliberately in migration `0004` with the comment "Phase 3 thêm FK khi bảng đó ra đời" `[VERIFIED: backend/alembic/versions/0004_kiem_tra_trung_lap_cau_hinh_nguong.py:26-28]`. A migration that tries to `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY (tai_lieu_do_an_id) REFERENCES tai_lieu_do_an(id)` before the `tai_lieu_do_an` table is created will fail at `alembic upgrade`.
**How to avoid:** Order migrations: `de_cuong` → `tai_lieu_do_an` → `luot_duyet_de_cuong` → **then** `op.create_foreign_key(...)` on `ket_qua_kiem_tra_trung_lap`. Also update the SQLAlchemy model (`app/models/trung_lap.py`) to add `ForeignKey("tai_lieu_do_an.id", name="fk_ket_qua_kttl_tai_lieu_do_an")` on that column once the table exists, or `tools/check-erd-db.py` will still pass (it only diffs columns, not FKs) but the ORM relationship will be missing.

### Pitfall 3: `tai_lieu_do_an` has no column for extracted text in the current ERD — this is a genuine open gap, not an oversight to paper over
**What goes wrong:** D-03 says extraction happens "at upload time... stored for later AI use", but the §3.2.3 data dictionary for `tai_lieu_do_an` (read in full this session) has no text/content column — only metadata (`ten_goc`, `ten_luu_tru`, `kich_thuoc`, `dinh_dang`, `so_phien_ban`, timestamps). A plan that silently invents a column here without updating `erd.puml` + `lop-thuc-the.puml` + the data-dictionary doc will fail `tools/check-erd-db.py` and violate the Phase 2 documentation-sync convention.
**How to avoid:** This is exactly the kind of additive-column change the project already has precedent for (`de_tai.ly_do_tu_choi` and `tai_khoan.phien_ban_token` were both added mid-project and backfilled into the docs). Recommend adding `noi_dung_trich_xuat TEXT NULL` and `trich_xuat_loi BOOLEAN NOT NULL DEFAULT FALSE` to `tai_lieu_do_an` in the Phase-3 migration, and writing both back into `erd.puml`, `lop-thuc-the.puml`, and `02-thiet-ke-csdl.md` §3.2.3 in the same plan — do not skip the doc sync step.
**See also:** Open Questions below — flagging this explicitly rather than silently deciding, since it changes a locked-reference document.

### Pitfall 4: `tu_khoa` (keywords) has no source anywhere in the existing data model
**What goes wrong:** REPO-01/D-07 requires `do_an_kho.tu_khoa` to be populated on auto-insert (triggered by DEFN-04's "chốt"), but nothing in `de_tai`/`de_cuong`/`tai_lieu_do_an` currently captures keywords — `de_tai.linh_vuc` (field/lĩnh vực, a single short string) is the closest existing proxy.
**How to avoid:** Documented as an Open Question below rather than silently deciding a schema addition on the planner's behalf, since it's a genuine information-architecture gap, not just an implementation detail.

### Pitfall 5: Progress reports are upsert-not-version — do not reuse the outline's version-history pattern for `bao_cao_tien_do`
**What goes wrong:** UC3.2/A1 explicitly says re-submission for the same milestone **overwrites** ("không tạo phiên bản như đề cương, vì tiến độ không cần giữ lịch sử soạn thảo"). A plan that reuses the outline's append-new-version pattern for progress reports would violate `UNIQUE(de_tai_id, moc_tien_do_id)` on `bao_cao_tien_do` and misrepresent the UC.
**How to avoid:** `bao_cao_tien_do` write path is read-existing-row → `UPDATE` if present and `nhan_xet IS NULL` (GVHD hasn't commented yet) → else create. Once `nhan_xet IS NOT NULL`, reject further resubmission for that milestone with 409 (inferred from UC3.2/A1's "trước khi Giảng viên hướng dẫn nhận xét" — not stored as a separate lock flag, derived from `nhan_xet IS NOT NULL`, matching the project's "computed, not stored" pattern already used for "trễ mốc").

### Pitfall 6: `LimitRequestBody`/app-level 25 MB cap vs. business-rule 20 MB cap are two different numbers, on purpose
**What goes wrong:** Confusing the existing infrastructure-level ceiling (`MAX_BODY_BYTES = 26214400` / 25 MB, enforced by `MaxBodySizeMiddleware`, matches Apache's `LimitRequestBody`) with this phase's business rule (D-01: 20 MB max for outline/report files) and only enforcing one of them.
**How to avoid:** The 25 MB middleware ceiling stays untouched (infra-level, already correct — 20 MB fits comfortably inside it). Add a **separate**, phase-owned check in `documents.validate_file()` rejecting files over 20 MB with a business-appropriate error message (`413` or `422` — recommend `422` since it's a business validation, not a transport-level limit, distinguishing it from the middleware's `413`).

### Pitfall 7: GVHD-on-own-student's-committee exclusion needs a query, not a UI-only warning
**What goes wrong:** D-06 says "GVHD of a student may not sit on that student's committee (warn/block)" — if only enforced by hiding the GV from a frontend picklist, a Bộ môn using the API directly (or a future admin bulk-tool) can still create the invalid assignment, matching PITFALLS.md #9's exact "frontend-only RBAC" failure mode.
**How to avoid:** Enforce server-side when creating `lich_bao_ve` rows: `de_tai.giang_vien_id` (this student's GVHD) must not be in the set of `thanh_vien_hoi_dong.giang_vien_id` for the target `hoi_dong_id`. Recommend **block** (409) over warn-only, consistent with this project's established preference for hard server-side enforcement (every other cross-cutting rule in Phase 1-2 is enforced, not just warned).

## Code Examples

### Shared download endpoint (ownership-checked, correct Vietnamese filename)
```python
# Source: verified against backend/.venv Starlette source this session
from starlette.responses import FileResponse

@router.get("/documents/{tai_lieu_do_an_id}/download")
def download_document(tai_lieu_do_an_id: int, user: CurrentUser = Depends(require_role(*ANY_ROLE)),
                       db: Session = Depends(get_db)):
    doc = documents_service.get_or_404(db, tai_lieu_do_an_id)
    if not documents_service.can_view(user, doc):   # ownership: SV owns de_tai, GVHD of de_tai, or committee member
        raise HTTPException(403, "Bạn không có quyền tải tài liệu này")
    return FileResponse(doc.storage_path(), filename=doc.ten_goc, media_type=_media_type(doc.dinh_dang))
```

### VARCHAR+CHECK status column, matching existing migration convention
```python
# Source: pattern verified in backend/alembic/versions/0004_kiem_tra_trung_lap_cau_hinh_nguong.py
sa.Column("trang_thai", sa.String(length=20), nullable=False),
sa.CheckConstraint("trang_thai IN ('CHUA_NOP','CHO_DUYET','YEU_CAU_SUA','DA_DUYET')", name="ck_de_cuong_trang_thai"),
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| N/A — greenfield within this codebase | N/A | — | Phase 3 introduces no deprecated-vs-current tension; it is the first upload/notification/committee code in the repo |

**Deprecated/outdated:** None applicable to this phase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | DOCX/PDF magic-byte signatures (`%PDF-`, ZIP containing `word/document.xml`) | Architecture Patterns → Pattern 1 | Low — extremely well-established, universally documented file-format facts, not project-specific |
| A2 | Stub `check_document`/`ingest` should reuse the existing Jaccard-on-NFC-tokens approach from `check_title` | Architecture Patterns → Pattern 2 | Low-Medium — CONTEXT.md leaves exact stub algorithm to Claude's Discretion; a different deterministic stub would work equally for demo purposes, this is a style/consistency recommendation, not a hard requirement |
| A3 | Recommend **block** (409, not just warn) for GVHD-on-own-committee | Common Pitfalls → Pitfall 7 | Low — D-06 literally says "warn/block" (either satisfies the locked decision); block is the stricter, safer choice consistent with project convention |
| A4 | Recommend adding `noi_dung_trich_xuat`/`trich_xuat_loi` columns to `tai_lieu_do_an` | Common Pitfalls → Pitfall 3, Open Questions | Medium — this modifies a locked canonical-ref (ERD data dictionary); if the planner instead chooses to re-extract text on-demand at check time (no persisted column), that is also valid and slightly simpler, just re-extracts on every check-retry |
| A5 | Recommend leaving `do_an_kho.tu_khoa` sourced from `de_tai.linh_vuc` (or left NULL) rather than adding a new keywords field | Common Pitfalls → Pitfall 4, Open Questions | Low-Medium — purely a data-completeness choice, does not block any UC's happy path; Bộ môn can always edit via UC5.3 |

## Open Questions (RESOLVED — 03-01 adds noi_dung_trich_xuat/trich_xuat_loi; 03-05 keeps tu_khoa NULL on auto-insert, Bộ môn edits; routes follow existing naming)

1. **Where does extracted document text live?**
   - What we know: D-03 requires extraction-at-upload-time storage; the current `tai_lieu_do_an` data dictionary (locked canonical ref) has no text column.
   - What's unclear: whether the planner should treat this as an additive-column change (with doc-sync obligations) or instead re-extract from the stored file on every duplicate-check attempt (simpler migration, slightly more CPU per retry — irrelevant at this project's scale).
   - Recommendation: add `noi_dung_trich_xuat TEXT NULL` + `trich_xuat_loi BOOLEAN NOT NULL DEFAULT FALSE` to `tai_lieu_do_an`, sync `erd.puml`/`lop-thuc-the.puml`/§3.2.3 in the same migration's plan (matches existing precedent for additive columns).

2. **Where do archive keywords (`tu_khoa`) come from?**
   - What we know: REPO-01 requires `tu_khoa` metadata on auto-insert; no existing field captures "keywords" distinct from `linh_vuc`.
   - What's unclear: whether to (a) reuse `linh_vuc` as a proxy, (b) leave `tu_khoa` NULL on auto-insert and rely on Bộ môn's UC5.3 edit, or (c) add a new optional field somewhere upstream (e.g., at final-report submission) for SV to supply keywords.
   - Recommendation: (b) for auto-insert simplicity — leave NULL, Bộ môn fills in later via UC5.3 — since neither CONTEXT.md nor the UC specs assign an owner for typing keywords in, and inventing a new required input field on an existing form is a bigger scope change than this research should silently assume.

3. **Exact route paths within each §3.3.6 group**
   - What we know: CONTEXT.md explicitly leaves this to Claude's Discretion; §3.3.6 only names the *groups* (`outlines`, `progress`, `defense`, `archive`, `notifications`).
   - What's unclear: nothing blocking — this is genuinely open by design.
   - Recommendation: follow the existing `topics.py`/`topic_approval.py` naming style (`/api/outlines/{de_tai_id}/submit`, `/api/outlines/{de_tai_id}/review`, `/api/defense/committees`, `/api/defense/committees/{id}/schedule`, `/api/defense/scores/{lich_bao_ve_id}`, `/api/archive`, `/api/archive/import`, `/api/notifications`, `/api/notifications/{id}/read`).

## Security Domain

### Applicable ASVS Categories (Level 1, per `.planning/config.json` `security_asvs_level: 1`)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No (carried from Phase 2, unchanged) | Existing JWT + `require_role` |
| V4 Access Control | Yes | Ownership predicates per resource: SV owns `de_tai`; GVHD assigned to `de_tai`; GV must be a `thanh_vien_hoi_dong` row for the target `hoi_dong_id` to view/score that committee's students (DEFN-03/E1 explicitly mandates a 403, not UI hiding) |
| V5 Input Validation | Yes | Pydantic `NFCModel` schemas (existing base) for all new request bodies; server-side magic-byte + size validation for uploads (not trusting `Content-Type`) |
| V6 Cryptography | No new surface this phase | Unchanged from Phase 2 (bcrypt, JWT) |
| V12 Files and Resources | Yes (new this phase) | Generated UUID filenames (never client-supplied), storage outside Apache `DocumentRoot`, download only via authorized API route, extraction via read-only parsing libraries (no macro execution in `python-docx`/`PyMuPDF`) |
| V11 Business Logic | Yes | State-machine guards enforced server-side via conditional `UPDATE`/count-equality checks, not just UI flow (defense chốt only when fully scored; GVHD-exclusion from own student's committee) |

### Known Threat Patterns for this phase's stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Path traversal via client-supplied filename | Tampering | Server-generates `<uuid>.<ext>` for storage path (D-02); original filename stored in DB only, never used to construct a filesystem path |
| Zip-based DOCX resource exhaustion (nested/oversized ZIP) | Denial of Service | Enforce the 20 MB business cap before parsing; `zipfile`/`python-docx` parse read-only, no macro/external-reference resolution |
| IDOR — SV/GV viewing another SV's report or score by guessing an ID | Broken Access Control (V4) | Service-level ownership checks on every GET (mirrors `topics.py`'s `can_view`/`is_owner` pattern) — never rely on the frontend not rendering a link |
| Committee member viewing/scoring a student outside their `hoi_dong` | Broken Access Control (V4) | Explicit `thanh_vien_hoi_dong` membership check before returning report/score data or accepting a score write (DEFN-03/E1 requires HTTP 403) |
| Unauthorized direct download bypassing role checks (guessed `tai_lieu_do_an_id` in a download URL) | Broken Access Control (V4) | No static file route exists at all (D-02) — the only path to file bytes is the authorized `/documents/{id}/download` endpoint, which re-checks ownership on every call |
| LIKE-wildcard injection in archive search (`%`/`_` in `tu_khoa`/`ten_de_tai` query params) | Injection (V5) | Reuse the already-proven `.contains(nfc(q), autoescape=True)` pattern from `topics.py:397` |
| CSV import with malformed/missing rows silently corrupting the archive | Business Logic (V11) | Per-row try/except, skip+report invalid rows (UC5.4/E1), never a single bulk `INSERT` that either all-succeeds or all-fails opaquely |

## Sources

### Primary (HIGH confidence — read/executed this session)
- `backend/app/services/ai_client.py`, `title_check.py`, `topics.py`, `dashboard.py`, `core/deps.py`, `core/db.py`, `core/config.py`, `core/body_limit.py`, `models/*.py` — full read, this session
- `backend/alembic/versions/0004_*.py`, `0005_*.py` — full read, this session
- `backend/.venv/lib/python3.12/site-packages/starlette/{responses.py,background.py}` — read/grepped this session (verifies FileResponse filename encoding and background-task exception behavior)
- `backend/pyproject.toml`, `backend/.venv/bin/pip index versions <pkg>` — executed this session (confirms `python-docx`/`pymupdf`/`python-multipart` absent from current deps, confirms current PyPI versions)
- `gsd_run query package-legitimacy check --ecosystem pypi python-docx pymupdf python-multipart` — executed this session
- `docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md`, `03-kien-truc-he-thong.md` — full read, this session (§3.2.3 data dictionary, §3.3.5-3.3.8 architecture/API contract)
- `docs/chuong-3-thiet-ke/so-do-lop/trang-thai-de-cuong.puml`, `trang-thai-kiem-tra-trung-lap.puml` — full read, this session
- `docs/chuong-2-khao-sat-phan-tich/07..11-dac-ta-uc*.md` (UC2-UC5, UC0) — full read, this session
- `deploy/docker-compose.yml`, `deploy/apache/ntma.conf`, `deploy/e2e-uc1.sh`, `backend/docker-entrypoint.sh` — full read, this session
- `frontend/src/api/client.ts`, `app/registry.ts`, `layouts/AppLayout.tsx`, `frontend/package.json` — full read, this session
- `.planning/phases/03-outline-progress-defense-archive/03-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/config.json` — full read, this session

### Secondary (MEDIUM confidence — official docs, cross-checked)
- [FastAPI — Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/) — fetched this session, confirms background-tasks-before-yield-cleanup ordering in current FastAPI docs
- `.planning/research/ARCHITECTURE.md`, `PITFALLS.md`, `STACK.md` — prior research-phase output, MEDIUM per that research's own confidence grading; reused directly where still applicable to Phase 3's scope

### Tertiary (LOW confidence)
- None used beyond what's already logged in the Assumptions Log above.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions confirmed via `pip index versions` against the actual project venv, package legitimacy checked via seam
- Architecture: HIGH — every pattern grounded in code already read this session (existing services/routers) plus locked architecture docs (§3.3), not external opinion
- Pitfalls: HIGH for the FastAPI/Starlette background-task behavior (verified against actual installed source + official docs), MEDIUM for domain-specific pitfalls carried from `.planning/research/PITFALLS.md`

**Research date:** 2026-09-28
**Valid until:** 30 days (stable stack, no fast-moving dependencies) — but re-verify `python-docx`/`pymupdf` versions at implementation time since they were not pinned before this research
