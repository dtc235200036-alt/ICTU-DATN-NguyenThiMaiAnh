# Architecture Research

**Domain:** SOA academic thesis-management system (Web API + SPA client + AI similarity-check microservice), MySQL, Apache reverse proxy
**Researched:** 2026-09-27
**Confidence:** HIGH (component boundaries, sync/async pattern, auth propagation, file/storage layout — established SOA + IR practice) / MEDIUM (exact embedding model choice, index technology sizing — depends on final corpus size, verify during Phase AI-service build)

## Standard Architecture

### System Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                          CLIENT (Browser)                              │
│                     React SPA (Vite build, static)                     │
└───────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTPS (443)
┌────────────────────────────────▼───────────────────────────────────────┐
│                  APACHE (reverse proxy, TLS termination)                │
│  /            → static React build (or separate static vhost)          │
│  /api/*       → proxy_pass → Web API (uvicorn, 127.0.0.1:8001)         │
│  (no public route to AI service — internal only)                       │
└───────────────────────────────┬───────────────────────────────────────┘
                                 │ HTTP (internal, JWT in Authorization header)
┌────────────────────────────────▼───────────────────────────────────────┐
│                    WEB API — FastAPI (uvicorn :8001)                   │
│  ┌────────────┐ ┌────────────┐ ┌───────────────┐ ┌──────────────────┐ │
│  │ Auth/Users │ │ Topic/     │ │ Outline/       │ │ Committee/       │ │
│  │ (JWT,roles)│ │ Registration│ │ ProgressReport │ │ Defense/Archive  │ │
│  └────────────┘ └────────────┘ └───────────────┘ └──────────────────┘ │
│  Owns: file storage (upload, extract text), all domain entities,       │
│  orchestrates calls to AI service, stores AI results as domain records │
└───────────┬───────────────────────────────────────────────┬───────────┘
            │ SQL (SQLAlchemy)                               │ REST (internal,
            │                                                │ API-key auth,
┌───────────▼────────────┐                    ┌──────────────▼──────────┐
│   MySQL — schema        │                    │  AI SIMILARITY SERVICE   │
│   `thesis_core`          │                    │  FastAPI (uvicorn :8002) │
│  Student, Lecturer,      │                    │  ┌────────────────────┐ │
│  Topic, Outline,         │                    │  │ Embedding (local    │ │
│  ProgressReport,         │                    │  │ Vietnamese model)   │ │
│  Committee, Project      │                    │  ├────────────────────┤ │
│  Document, SimilarityChe-│                    │  │ Vector index (FAISS │ │
│  ckResult (summary)      │                    │  │ in-memory, rebuilt  │ │
└──────────────────────────┘                    │  │ from its own store) │ │
                                                 │  ├────────────────────┤ │
            ┌────────────────────────────────── │ │ Chunking/segmentation│ │
            │ SQL (SQLAlchemy, separate schema)  │  └────────────────────┘ │
┌───────────▼────────────┐                      └──────────────┬──────────┘
│   MySQL — schema        │                                     │
│   `thesis_ai` (owned by  │◄────────────────────────────────────┘
│   AI service only)       │
│  embeddings, chunks,      │
│  index_metadata          │
└──────────────────────────┘
```

Both schemas can live on the **same MySQL server instance** (one server is enough at this scale — 100 students, 30 lecturers, 300 topics, 50 documents) — the separation that matters for the SOA diagram is *schema/data ownership*, not physical server count. Each service connects only to its own schema; nothing but the AI service ever writes to `thesis_ai`, and nothing but the Web API ever writes to `thesis_core`. This is what makes the UML component diagram legitimately "SOA" rather than "one DB, two processes pretending to be services."

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| React client | UI for 3 roles (Student, Lecturer, Bộ môn/Admin), calls Web API only, never talks to AI service directly | Vite + React Router + a fetch/axios client with JWT attached; built to static assets, served by Apache or a static vhost |
| Web API (FastAPI) | Auth/roles, all 5 core use-case workflows, owns file storage + text extraction, is the *only* caller of the AI service, persists AI results into domain tables | FastAPI + SQLAlchemy + Alembic migrations against `thesis_core`; python-docx/pypdf for text extraction; httpx client to call AI service |
| AI Similarity Service (FastAPI) | Semantic title comparison, document duplicate detection, chunk-level similarity, owns its own embedding/index storage | FastAPI + sentence-transformers (Vietnamese model) + FAISS in-process index; exposes `/check-title`, `/check-document`, `/reindex` |
| MySQL (`thesis_core`) | System of record for all business entities | InnoDB, foreign keys enforced, one schema per service |
| MySQL (`thesis_ai`) | System of record for embeddings/chunks/index bookkeeping, private to AI service | Same server, separate schema; BLOB/JSON columns for vectors |
| File storage | Durable storage for uploaded DOCX/PDF (outlines, reports, archived theses) | Local disk volume mounted only into the Web API container/host path, referenced by path in `ProjectDocument` |
| Apache | TLS termination, reverse proxy to Web API, serves static client build, enforces the "server behind Apache/HTTPS" deployment requirement | `mod_proxy` + `mod_ssl`; AI service has no Apache vhost — it is unreachable from outside the host |

## Recommended Project Structure

```
repo/
├── web-api/                        # FastAPI Web API service
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                   # config, security (JWT), deps
│   │   ├── models/                 # SQLAlchemy entities (Student, Lecturer, Topic, Outline, ProgressReport, Committee, ProjectDocument, SimilarityCheckResult)
│   │   ├── schemas/                 # Pydantic DTOs
│   │   ├── routers/                # topics.py, outlines.py, progress.py, committee.py, archive.py, auth.py
│   │   ├── services/                # business logic, incl. ai_client.py (httpx wrapper calling AI service)
│   │   ├── storage/                 # file save/extract-text helpers
│   │   └── alembic/                 # migrations for thesis_core
│   └── tests/
├── ai-service/                      # FastAPI AI similarity service
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                    # config, API-key auth dependency
│   │   ├── embedding/                # model loading, encode()
│   │   ├── index/                    # FAISS index build/load/incremental-add
│   │   ├── chunking/                 # paragraph/sentence segmentation for VN text
│   │   ├── routers/                  # check_title.py, check_document.py, reindex.py, health.py
│   │   └── db/                       # SQLAlchemy models for thesis_ai (embeddings, chunks)
│   └── tests/
├── client/                          # React SPA
│   ├── src/
│   │   ├── api/                     # generated/typed client for Web API
│   │   ├── features/                # by role/use-case: topics, outlines, progress, committee, archive, auth
│   │   └── components/
│   └── vite.config.ts
├── deploy/
│   ├── apache/                      # vhost configs (client static + /api proxy)
│   ├── docker-compose.yml           # web-api, ai-service, mysql (2 schemas), optional adminer
│   └── seed/                        # seed scripts: 100 SV, 30 GV, 300 topics, 50 docs w/ planted duplicates
└── docs/                            # BRD/PRD/HLD, UML sources
```

### Structure Rationale

- **Two top-level service folders (`web-api/`, `ai-service/`):** mirrors the SOA requirement literally — two independently deployable FastAPI apps, each with its own dependencies, own DB models, own Dockerfile. Makes the "3 separate components" grading criterion trivially visible in the repo layout and in the UML component diagram.
- **`services/ai_client.py` inside web-api:** centralizes every outbound call to the AI service (base URL, API key, timeout, retry) so the Web API's business routers never talk HTTP directly — keeps the service boundary honest and makes it easy to point the diagram's "Web API → AI Service" arrow at one file.
- **`ai-service/app/db/` separate from `web-api/app/models/`:** enforces schema ownership; nothing forces the AI service to reuse Web API's SQLAlchemy Base, which would silently create a shared-database anti-pattern.
- **`storage/` only in web-api:** file bytes live and are parsed in exactly one place; the AI service receives already-extracted text, never file paths, so it needs no filesystem access and no MIME/DOCX/PDF parsing dependency.

## Architectural Patterns

### Pattern 1: Sync call for title check, async job for document check

**What:** Two different AI operations have very different latency profiles. Semantic *title* comparison is one short string against an in-memory index — sub-second. Full *document* duplicate check requires extracting text from a DOCX/PDF (can be dozens of pages), chunking, embedding every chunk, and comparing against the whole corpus — potentially several seconds to tens of seconds.

**When to use:**
- Title check at topic registration → synchronous REST call, Web API awaits the AI response and returns it inline (student sees "similar topic found: X, 87%" immediately in the registration form).
- Outline/report duplicate check at submission → Web API accepts the upload, stores the file, creates a `SimilarityCheckResult` row with `status=PENDING`, returns `202 Accepted` immediately, then processes the check in a background task; client polls (or refetches on a timer) a `GET /outlines/{id}/similarity` endpoint until `status=DONE`.

**Trade-offs:** Sync is simpler but blocks the request thread for as long as the AI service takes — acceptable only because title-check payload is tiny. Async avoids a slow/hanging upload request and models the realistic architecture a rubric expects ("AI checks run as a service call, not inline"), but requires a status field and a client polling/refresh pattern.

**Example:**
```python
# web-api/app/routers/outlines.py
@router.post("/outlines/{outline_id}/submit", status_code=202)
async def submit_outline(outline_id: int, file: UploadFile, bg: BackgroundTasks, db: Session = Depends(get_db)):
    path = save_file(file, kind="outline")
    text = extract_text(path)  # docx/pdf -> plain text, done in Web API
    result = SimilarityCheckResult(outline_id=outline_id, status="PENDING")
    db.add(result); db.commit()
    bg.add_task(run_similarity_check, result.id, text, db)  # fire-and-forget
    return {"similarity_check_id": result.id, "status": "PENDING"}
```

At this project's scale (50 test documents, single-server demo, 10-week solo build), **`fastapi.BackgroundTasks` is sufficient** — no Redis/Celery/RQ needed. Note this explicitly as a scoped decision: the sequence diagram in the HLD can still show "Web API → AI Service (async)" as a service call; `BackgroundTasks` is simply the in-process implementation of that arrow. If the report wants to show scalability awareness, mention Celery+Redis as the swap-in for production load without changing the interface.

### Pattern 2: AI service owns its corpus via push-on-write, not pull-on-demand

**What:** The AI service must compare a new topic/document against the *whole department corpus across cohorts*. Two ways to get that corpus into the AI service: (a) AI service reads directly from `thesis_core` (pull), or (b) Web API pushes new/changed items to the AI service's own store as they are created (push), and the AI service maintains its own index.

**When to use:** Push. Every time the Web API creates or updates a `Topic` (title) or finalizes a `ProjectDocument` (outline/report/archived thesis), it calls the AI service's `/ingest` endpoint with `{id, type, text}`. The AI service embeds it, appends to its FAISS index, and persists the vector + chunk text in `thesis_ai`. For the initial seed load (300 historical topics, 50 documents), a `/reindex` batch endpoint accepts a bulk payload or is fed by a seed script that iterates and calls `/ingest` once per record.

**Trade-offs:** Pull (AI service querying `thesis_core` directly) is tempting because it avoids a "keep two stores in sync" concern, but it violates the service boundary the rubric is explicitly grading (SOA = independent services, each with its own data) and creates a hidden coupling — the AI service now needs Web API's schema knowledge and DB credentials. Push costs a little extra plumbing (one `/ingest` call per write) but keeps services genuinely decoupled, matches the "AI service as independent microservice" story in the architecture diagram, and lets the AI service's index rebuild independently (e.g., after swapping embedding models) via `/reindex` without touching `thesis_core`.

### Pattern 3: Vectors stored in the AI service's own MySQL schema, indexed in memory with FAISS

**What:** MySQL has no native vector-search extension (unlike Postgres+pgvector). Given MySQL is a hard constraint (PI 3.1), store each chunk's embedding as a serialized vector (e.g., `float32` array packed into a `BLOB`/`JSON` column) in `thesis_ai.embeddings`, alongside chunk text and a reference id (`topic_id` or `document_id` + `chunk_index`). At AI-service startup, load all rows into an in-memory FAISS `IndexFlatIP` (cosine via normalized inner product) — trivial at this scale (300 titles + 50 docs × ~dozens of chunks each = low thousands of vectors, index build takes well under a second). On each `/ingest` call, also add the new vector directly to the live in-memory index (`index.add`) so it's searchable immediately, not just after a restart.

**When to use:** Always, for this project's scale. `IndexFlatIP`/`IndexFlatL2` (exact, brute-force) is fast enough for low-thousands of vectors — no need for IVF/HNSW approximate indexes, which would add complexity with zero benefit below ~100k vectors.

**Trade-offs:** In-memory index means a service restart requires reloading from MySQL (a few hundred ms — acceptable); it is not a concern at this scale. If the corpus were to grow to hundreds of thousands of chunks, a persistent index format (`faiss.write_index`/`read_index` to disk, or migrating to a dedicated vector DB like Milvus/Qdrant) would become worth it — explicitly out of scope here.

## Data Flow

### Request Flow — Title semantic check (sync)

```
Student submits topic title
    ↓
React client → POST /api/topics (JWT)
    ↓
Web API: validate role, create draft Topic
    ↓ (sync, internal REST + API key)
Web API → AI Service: POST /check-title {text}
    ↓
AI Service: embed(text) → FAISS search top-k in existing title index
    ↓
AI Service → Web API: [{topic_id, title, score}, ...]
    ↓
Web API: persist SimilarityCheckResult(kind=TITLE, matches=...), attach to Topic
    ↓
Web API → React client: 201 + warnings list (score, matched topic)
```

### Request Flow — Document duplicate check (async)

```
Student uploads outline/report (DOCX/PDF)
    ↓
Web API: store file, extract text, create SimilarityCheckResult(status=PENDING)
    ↓ 202 Accepted → client shows "Đang kiểm tra trùng lặp..."
    ↓ (background task)
Web API → AI Service: POST /check-document {ref_id, text}
    ↓
AI Service: chunk text → embed each chunk → FAISS search per chunk → aggregate
    ↓
AI Service → Web API: {overall_score, matched_document_id, matched_spans:[...]}
    ↓
Web API: update SimilarityCheckResult(status=DONE, ...), also POST /ingest so this
         document is now part of the corpus for future checks
    ↓
Client polls GET /outlines/{id}/similarity → renders duplicate spans + % once DONE
```

### Key Data Flows

1. **Ingestion (write-path):** Every finalized `Topic` title and every accepted `ProjectDocument` (outline, progress report, archived thesis) is pushed once from Web API to AI Service via `/ingest`, keeping the AI corpus current without the AI service ever querying `thesis_core`.
2. **Check (read-path):** Web API is the only client of the AI service's `/check-title` and `/check-document`; results always flow back into a `SimilarityCheckResult` row owned by `thesis_core`, so the rest of the system (committee, archive) only ever reads similarity results from the Web API, never from the AI service directly.
3. **Auth propagation:** Browser ↔ Web API uses a per-user JWT (role embedded as claim: `student`/`lecturer`/`admin`). Web API ↔ AI Service uses a separate, static service-to-service credential (shared secret / API key header) — the end-user JWT is *not* forwarded, because the AI service has no concept of users/roles; it only trusts "requests coming from the Web API." The AI service is not reachable through Apache at all (no public vhost/route), which is itself the strongest access control.

## Scaling Considerations

This system's target load is fixed and small by requirement (100 students, 30 lecturers, 300 topics, 50 test documents; demo-grade, not production). Scaling tables at "0-1k / 1k-100k / 100k+ users" would be misleading busywork here — the honest version:

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Demo/thesis defense (this project — ~130 users, ~350 documents total) | Single MySQL instance, two schemas; FAISS `IndexFlatIP` in-memory; `BackgroundTasks` for async checks; single Apache host. This is the whole plan — no further work needed. |
| If reused as a real departmental tool (thousands of documents/year, multiple cohorts) | Swap `BackgroundTasks` for Celery/RQ + Redis so checks survive process restarts and can run on a separate worker; persist FAISS index to disk or move to IVF/HNSW; consider a dedicated vector DB (Qdrant/Milvus) if per-chunk counts pass ~100k. |
| If opened to the whole university (many departments, high concurrency) | Split AI service horizontally (stateless, index sharded/replicated); move file storage to object storage (S3-compatible) instead of local disk; add a message queue between Web API and AI service instead of direct REST for the async path. |

### Scaling Priorities

1. **First realistic bottleneck (even at this scale):** re-embedding/parsing large PDFs synchronously inside a request — already solved by the async/BackgroundTasks pattern above; do not let this regress by making document checks synchronous "for simplicity" during implementation.
2. **Second, only if reused beyond the thesis:** in-memory FAISS index lost on restart — mitigated by always rebuilding from `thesis_ai` at startup (already the design), and by persisting the index to disk once the ingest volume makes a full rebuild noticeably slow.

## Anti-Patterns

### Anti-Pattern 1: AI service reading/writing `thesis_core` directly

**What people do:** Give the AI service a SQLAlchemy connection straight to the Web API's database "because it's simpler than building an `/ingest` endpoint."
**Why it's wrong:** Destroys the service boundary the rubric is grading (PI 2.2/3.2 explicitly want SOA with independent services). Any schema change in the Web API now silently breaks the AI service. Also makes the architecture diagram dishonest — it would show two boxes but really be one shared-database monolith.
**Do this instead:** AI service only exposes/consumes its own REST API (`/ingest`, `/check-title`, `/check-document`, `/reindex`) and only persists to its own schema (`thesis_ai`).

### Anti-Pattern 2: Doing text extraction (DOCX/PDF parsing) inside the AI service

**What people do:** Send the raw uploaded file to the AI service and have it run `python-docx`/`pypdf` there, since "it needs the text anyway."
**Why it's wrong:** Duplicates file-format parsing logic in two services, forces the AI service to have filesystem/network access to file bytes (bigger payloads over the internal API, or a shared volume that re-couples the services), and mixes format-parsing concerns into a service that should only care about NLP/vectors.
**Do this instead:** Web API extracts plain text once (it already owns file storage) and sends only text over the wire to `/check-document` / `/ingest`. AI service never touches DOCX/PDF files.

### Anti-Pattern 3: Forwarding the end-user's JWT to the AI service

**What people do:** Reuse the same `Authorization: Bearer <user-jwt>` header when calling the AI service, since "it's already there."
**Why it's wrong:** The AI service has no user/role model and no reason to validate end-user tokens; doing so couples its auth logic to the Web API's JWT secret/claims, and if the AI service is ever exposed on a different network boundary, leaked user tokens become a bigger blast radius.
**Do this instead:** Separate, static service-to-service credential (API key/shared secret) for Web API → AI Service calls; keep the AI service off any public route entirely (no Apache vhost for it).

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Vietnamese embedding model (e.g., `sentence-transformers` VN model such as `dangvantuan/vietnamese-embedding` or `VoVanPhuc/sup-SimCSE-VietNamese-phobert-base`) | Loaded in-process inside AI service at startup, no external API call, no per-request cost | Verify actual model choice against a small labeled sample of real topic titles during AI-service build (Phase-specific research flag); local inference keeps the "no paid API" constraint satisfied |
| Apache HTTP Server | Reverse proxy (`mod_proxy`, `mod_ssl`) in front of Web API only | AI service must not get a public vhost; this is both a security boundary and the literal SOA requirement (internal-only service) |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| React client ↔ Web API | HTTPS REST + JWT bearer token | Client never has AI-service credentials or URL |
| Web API ↔ AI Service | Internal HTTP REST (httpx), API-key header, JSON payloads (text only, never files) | Sync for `/check-title`, fire-and-forget background task calling `/check-document` and `/ingest` |
| Web API ↔ `thesis_core` (MySQL) | SQLAlchemy ORM, Alembic migrations | Owns Student, Lecturer, Topic, Outline, ProgressReport, Committee, ProjectDocument, SimilarityCheckResult (summary/result row only) |
| AI Service ↔ `thesis_ai` (MySQL) | SQLAlchemy ORM, separate schema, separate migration set | Owns embeddings, chunks, index_metadata — private tables, never queried by Web API |

## Suggested Build Order (dependency-driven)

1. **MySQL `thesis_core` schema + entity models** (Student, Lecturer, Topic, Outline, ProgressReport, Committee, ProjectDocument, SimilarityCheckResult) — everything else depends on this existing first.
2. **Web API auth + roles (JWT, 3 roles)** — every subsequent UC and the React client need this in place before real integration testing is possible.
3. **Core UC routers in Web API** (topic proposal/registration/approval, outline submission/review, progress reports, committee/defense, archive/search) — build with AI integration *stubbed* (e.g., a fake client returning empty matches) so these UCs are independently testable before the AI service exists.
4. **React client**, wired against the real Web API as soon as each UC's endpoints stabilize (can start from Figma mockups earlier, in parallel with step 3).
5. **AI Similarity Service**, built and tested standalone against a small hand-made corpus first (fast feedback loop), exposing `/ingest`, `/check-title`, `/check-document`, `/reindex`.
6. **Wire Web API → AI Service** for real (replace the stub client from step 3 with the httpx-based one): title check sync path first (simpler), then the async document-check path with `BackgroundTasks` and the polling status endpoint.
7. **Apache reverse proxy + HTTPS**, deployed with both FastAPI processes running (AI service bound to localhost/internal network only).
8. **Seed data + planted-duplicate test corpus** (100 SV, 30 GV, 300 topics, 50 docs with intentional duplicate pairs) — do this after step 6 so seeding also exercises the real `/ingest` path end-to-end, rather than writing a separate one-off seeding mechanism.
9. **End-to-end UAT** across all 5 UCs + both AI checks, then documentation/report/slides.

This order front-loads the two things every other phase depends on (schema, auth) and defers the AI service's *wiring* (step 6) until both sides — Web API UCs and AI service internals — already work independently, which keeps AI-service development from blocking core CRUD work, and vice versa.

## Sources

- [dangvantuan/vietnamese-embedding — Hugging Face](https://huggingface.co/dangvantuan/vietnamese-embedding) — MEDIUM confidence (community model card, verify accuracy claims against project's own title samples before committing)
- [VoVanPhuc/sup-SimCSE-VietNamese-phobert-base — Hugging Face](https://huggingface.co/VoVanPhuc/sup-SimCSE-VietNamese-phobert-base) — MEDIUM confidence
- [keepitreal/vietnamese-sbert — Hugging Face](https://huggingface.co/keepitreal/vietnamese-sbert) — MEDIUM confidence, alternative option
- [Building Plagiarism Checker Using FAISS — Naukri Engineering (Medium)](https://medium.com/naukri-engineering/building-plagiarism-checker-using-faiss-8c933c8afe1e) — general pattern reference for FAISS-backed similarity microservice split, confirms retrieve pattern used above
- [BERT-Enhanced Retrieval Tool for Homework Plagiarism Detection System (arXiv)](https://arxiv.org/pdf/2404.01582) — academic reference for chunk-level embedding + retrieval approach to document duplicate detection
- FAISS (`IndexFlatIP`/`IndexFlatL2`) exact-search sizing guidance — HIGH confidence, well-established (brute-force is standard for sub-100k-vector corpora; this project's corpus is in the low thousands)
- SOA / service-per-database, sync-for-fast/async-for-slow, and internal-API-key vs. end-user-JWT patterns — HIGH confidence, standard microservice architecture practice, not domain-specific to this project

---
*Architecture research for: SOA thesis management system (Web API + client + AI similarity service)*
*Researched: 2026-09-27*
