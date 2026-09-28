# Phase 4: AI Similarity Service - Research

**Researched:** 2026-09-28
**Domain:** Local Vietnamese-language semantic + lexical duplicate-detection microservice (FastAPI + sentence-transformers + FAISS + datasketch), swapped in behind an existing stub seam
**Confidence:** MEDIUM-HIGH for package versions/sizes/wheel availability (live-verified this session against PyPI/HF/pytorch.org); MEDIUM for Vietnamese-embedding model choice and CPU latency (no reproducible benchmark on this exact hardware — D-01 bake-off is the actual verification step); LOW→confirmed-as-gap for "official template exists" (it does not, see Environment Availability)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Carried forward (locked):**
- Architecture §3.3: AI service = own FastAPI process, bound to 127.0.0.1:8002 / internal compose network only, **no Apache route**, `X-API-Key` internal key, own MySQL schema `thesis_ai` (tables per `docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.puml`), API contract §3.3.5 (`/ingest`, `/check-title`, `/check-document`, `/reindex`, `/health`), receives text only (never files). Web API keeps BackgroundTasks + polling for document checks (Phase 3). NFR: title check ≤5 s, document check ≤30 s P95 on seeded corpus.
- Stack per research STACK.md: sentence-transformers, FAISS (`faiss-cpu`, IndexFlatIP), underthesea word segmentation, datasketch MinHash for verbatim copy, NFC normalization everywhere.

**D-01 (model selection):** Open the phase with a timeboxed bake-off: `bkai-foundation-models/vietnamese-bi-encoder` (+ underthesea segmentation) vs `intfloat/multilingual-e5-base` (no segmentation) on a small labeled set of known similar/different Vietnamese thesis-title and paragraph pairs; pick by separation (AUC / gap between duplicate and non-duplicate scores) and latency; record the table for the report.

**D-02 (runtime):** Run on **CPU** inside the container (target server unknown); model weights cached in a docker volume, loaded once at startup; embeddings precomputed at ingest, never recomputed per request.

**D-03 (detection method):** Title check = cosine similarity (embedding) top-k with % score. Document check = chunk into paragraph/sentence-window chunks after stripping boilerplate (template headings, mục lục, tài liệu tham khảo, lời cam đoan/cảm ơn — patterns from the official template when available, otherwise a documented default list), then flag a chunk if embedding cosine ≥ content threshold **or** MinHash Jaccard ≥ verbatim threshold; report overall % = share of matched chunks (by characters), matched theses list, per-passage pairs with source text for highlighting.

**D-04 (thresholds):** Thresholds live in `cau_hinh_nguong` (already exists, Web API side); Bộ môn edits title/content thresholds on a new settings screen; Web API passes the active threshold to the AI service per request (AI service stays stateless about policy). Defaults come from calibration.

**D-05 (topic corpus):** 300 archive topics across several cohorts (khóa K18–K22) generated with realistic Vietnamese IT thesis titles in topic clusters (web, mobile, AI/ML, IoT, data, security, ERP…), inserted via the existing archive import path so they flow through `/ingest`.

**D-06 (test document corpus):** 50 DOCX/PDF test documents generated programmatically (python-docx + a PDF export) using the official template structure when available, with an explicit pair spectrum: exact copy, paraphrased, same field/different topic, unrelated; ~30% of pairs held out as a validation set not used for threshold tuning. A manifest (pair id, type, expected flag) + a results table (scores, flagged?, pass/fail) are saved under `docs/` for chương 4. No real student text is copied verbatim (privacy/copyright).

**D-07 (deployment):** Add `ai` service to `deploy/docker-compose.yml` on the internal network only; Web API gets `AI_SERVICE_URL`, `AI_API_KEY` env; `AI_STUB_MODE` kept as a fallback switch.

### Claude's Discretion

Chunk size/overlap, top-k, exact boilerplate patterns, MinHash parameters, bake-off set size (small, timeboxed), UI details for MH-14 highlights and the threshold screen within Ant Design.

### Deferred Ideas (OUT OF SCOPE)

- Delete-from-index endpoint for removed archive records (not in §3.3.5 contract) — note as limitation unless trivial.
- GPU inference, web-scale plagiarism search — out of scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AISV-01 | AI service is a standalone FastAPI service, only Web API can call it (internal API key, no public route via Apache), has ingest/check-title/check-document endpoints | §3.3.1–3.3.5 already locked in `docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md`; deployment pattern verified against existing `deploy/docker-compose.yml` (see Architecture Patterns, Environment Availability) |
| AISV-02 | Text is Unicode-NFC normalized and Vietnamese word-segmented before embedding; corpus embeddings precomputed at ingest, never recomputed per request | Standard Stack (underthesea), Common Pitfalls #1/#2/#6, Code Examples |
| AISV-03 | Semantic title comparison returns top-k similar topics with % within NFR response time | Standard Stack (sentence-transformers + FAISS IndexFlatIP), Common Pitfalls #6/#Latency, Validation section omitted per config (see note) |
| AISV-04 | Document check extracts already-provided text, strips shared boilerplate (headings, mục lục, tài liệu tham khảo), and detects duplicated passages against other theses | Common Pitfalls #3/#4 (boilerplate + extraction-noise, **verified against actual in-repo extraction code**), Architecture Patterns (chunking + dual-signal detection) |
| AISV-05 | Document check result shows total similarity %, list of duplicate theses, and each duplicated passage highlighted next to its source | Existing `CheckDetail`/`CheckSegment` schema contract (verified in-repo), MH-14 mockup (verified), Architecture Patterns |
| AISV-06 | Document check runs asynchronously; UI shows checking/complete status | Already implemented in Phase 3 (`document_check.py` BackgroundTasks pattern) — Phase 4 only swaps the AI client call inside `run()`, no new async plumbing needed |
| AISV-07 | Bộ môn can configure title/content duplicate-warning thresholds | `cau_hinh_nguong` table already exists (verified in-repo); Phase 4 adds the settings screen + calibration-derived defaults |
| DATA-02 | Seed 300 topics across cohorts, ingested into the AI service | D-05, Common Pitfalls #Seed-realism, Environment Availability (no real topic corpus collected — must be synthetic) |
| DATA-03 | 50 test DOCX/PDF files with intentional duplicate pairs across 4 types + verification table | D-06, Standard Stack (python-docx + reportlab, **no LibreOffice needed** — see Architecture Patterns), Common Pitfalls #Seed-realism, Environment Availability |
</phase_requirements>

## Summary

This phase builds a second FastAPI process (`ai-service/`) that owns Vietnamese semantic + lexical duplicate detection, replacing the Jaccard-over-syllables `AiClientStub` already wired into `backend/app/services/ai_client.py`. The contract, schema (`thesis_ai`), and deployment boundary (internal-only, no Apache route, `X-API-Key`) are already locked in `docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md` §3.3 — this phase does not need to invent architecture, only implement it. All core package choices (`sentence-transformers`, `faiss-cpu`, `underthesea`, `datasketch`, `python-docx`, `pymupdf`) were re-verified live this session against PyPI/Hugging Face/pytorch.org and are current, Python-3.12-compatible, and installable with `manylinux` wheels — no compile-from-source risk on the existing `python:3.12-slim` Docker base the backend already uses.

The single largest risk this research surfaces is **not** model accuracy — it's environment: (1) `torch`'s default PyPI package pulls a full CUDA toolkit (confirmed via live PyPI metadata) and must be installed from the CPU-only index or the Docker image balloons by several GB; (2) the **official thesis template and old-thesis corpus that the phase's own bake-off (D-01) and boilerplate list (D-03) depend on have not been collected** — `tai-lieu-goc/mau-chinh-thuc/` and `tai-lieu-goc/do-an-cu/` are both empty (only `.gitkeep`/`.gitignore`) — so both the bake-off pairs and the boilerplate-stripping pattern list must be authored synthetically by the plan, not sourced from real documents; (3) the existing PDF text extraction (`backend/app/services/documents.py:110-111`, already shipped, out of this phase's scope to change) uses PyMuPDF's naive `page.get_text()` — **confirmed** to NOT strip repeated headers/footers/page numbers the way the DOCX path's `document.paragraphs` iteration structurally does — so the AI service's boilerplate-stripping stage must defensively deduplicate repeated lines across chunks, not just match known template phrases; (4) CPU embedding throughput for a ~100-chunk document is a real risk against the 30 s NFR and should be measured on the actual host within the first implementation task, not assumed.

**Primary recommendation:** Build `ai-service/` as its own `uv`-managed FastAPI project mirroring `backend/`'s existing Dockerfile pattern (python:3.12-slim, uv sync --frozen), install torch from the CPU-only wheel index explicitly, load the sentence-transformers model once at process startup, rebuild the FAISS `IndexFlatIP` from `thesis_ai.embedding` rows at startup (never persisted to disk separately), and treat D-01's bake-off pairs and D-06's 50 test documents as 100% synthetic authored content (python-docx + reportlab, no LibreOffice dependency needed) since no real corpus exists to draw from.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| DOCX/PDF text extraction | API / Backend (Web API) | — | Already implemented in Phase 3 (`app/services/documents.py`); AI service never receives files, only extracted text (§3.3.5) — out of this phase's scope to change |
| Unicode NFC normalization + Vietnamese word segmentation | API / Backend (AI service) | — | §3.3.2: "Chuẩn hóa NFC & tách từ" is an explicit AI-service sub-component; must also be applied identically to titles arriving via `/check-title` from the Web API (which does its own NFC at the form boundary, per NFR-14) |
| Boilerplate stripping + chunking | API / Backend (AI service) | — | §3.3.2: "Lọc phần mẫu chung & chia đoạn" is an explicit AI-service sub-component — the Web API forwards raw extracted text unfiltered |
| Embedding generation + FAISS index | API / Backend (AI service) | — | §3.3.2/§3.3.8: embedding model + in-memory FAISS index live entirely inside the AI service process; never exposed to Web API or client |
| Duplicate-result persistence (`ket_qua_kiem_tra_trung_lap`, `chi_tiet_trung_lap`) | API / Backend (Web API) | — | Owned by `thesis_core` schema, already modeled (`app/models/trung_lap.py`) — AI service returns transient JSON only, does not persist business-facing results |
| Threshold configuration (`cau_hinh_nguong`) | API / Backend (Web API) | — | Web API owns policy; AI service is stateless about thresholds, only told the active value per §3.3.8 |
| Async job orchestration (BackgroundTasks, polling) | API / Backend (Web API) | — | Already built in Phase 3 (`document_check.py`) — Phase 4 only replaces the `get_ai_client(db).check_document(...)` call target |
| Duplicate-passage highlighting UI (MH-14) | Browser / Client | — | Pure rendering of `CheckDetail.chi_tiet` already returned by the existing schema; no new client-server contract needed |
| Threshold settings screen | Browser / Client | API / Backend | New Ant Design form calling a new/extended Web API endpoint over `cau_hinh_nguong` |

## Standard Stack

### Core (AI service — new `ai-service/` project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Runtime | Matches `backend/pyproject.toml` (`>=3.12,<3.13`) and `backend/Dockerfile` (`python:3.12-slim`) [VERIFIED: backend/pyproject.toml:5, backend/Dockerfile:2]. All packages below confirmed to ship `cp312` (or `cp310-abi3`, forward-compatible) manylinux wheels — no compiler toolchain needed in the image. |
| FastAPI | ≥0.141 | AI-service HTTP framework | Same version already pinned in `backend/pyproject.toml:7` — keep both services on the same FastAPI line to avoid two sets of quirks to debug. |
| Uvicorn | `uvicorn[standard]` ≥0.54 | ASGI server | Matches `backend/pyproject.toml:8`. |
| `sentence-transformers` | 6.1.0 (released 2026-09-18) | Load & run the embedding model locally | [VERIFIED: `pip index versions sentence-transformers` this session — registry, MEDIUM confidence tier per source-hierarchy]. Requires `transformers<6.0,>=5.0`, `torch>=2.2`, Python `>=3.10` [VERIFIED: PyPI JSON `requires_dist`/`requires_python` for this exact version]. |
| `torch` (CPU wheel) | 2.14.0+cpu | Embedding model backend, CPU-only per D-02 | **Do not `pip install torch` plain** — the default PyPI `torch` package's `requires_dist` lists `cuda-toolkit`, `nvidia-cudnn-cu13`, `nvidia-nccl-cu13`, `triton` etc. as platform-conditional deps on Linux [VERIFIED: PyPI JSON `requires_dist` for `torch==2.14.0`, read this session — these are declared dependencies, not inferred]. Install instead via `pip install torch --index-url https://download.pytorch.org/whl/cpu`; the `cp312-cp312-manylinux_2_28_x86_64` CPU wheel for 2.14.0 is confirmed present and is **196,253,793 bytes (≈187 MiB)** [VERIFIED: `curl -sI` HTTP HEAD against `download.pytorch.org`, this session — no CUDA payload]. |
| `bkai-foundation-models/vietnamese-bi-encoder` | current (PhoBERT-base-v2 backbone) | **Primary candidate**, D-01 bake-off | Confirmed the model card states raw input **must already be word-segmented** and explicitly recommends `underthesea` (`pyvi`/`RDRSegment` as alternatives) [CITED: huggingface.co/bkai-foundation-models/vietnamese-bi-encoder, MEDIUM]. Weight file `model.safetensors` is **540,015,464 bytes (≈515 MiB)** [VERIFIED: HTTP HEAD via HF resolve redirect, this session]. |
| `intfloat/multilingual-e5-base` | current | **Alternative candidate**, D-01 bake-off | Requires `"query: "` prefix on every input for symmetric/semantic-similarity use (title/paragraph comparison is symmetric, so use `"query: "` on both sides, not `"passage: "`) [CITED: huggingface.co/intfloat/multilingual-e5-base model card, MEDIUM]. Weight file is **1,112,201,288 bytes (≈1.06 GiB)** — roughly **2.1× larger** than the bkai model [VERIFIED: HTTP HEAD, this session]. No segmentation step needed, simpler pipeline, but larger download/RAM footprint. |
| `faiss-cpu` | 1.15.1 (released 2026-09-16) | In-process exact vector index (`IndexFlatIP`) | [VERIFIED: `pip index versions faiss-cpu` this session]. **Important packaging change to plan around:** starting at this version faiss-cpu ships a single `cp310-abi3` stable-ABI wheel for Linux/macOS (`manylinux_2_27_x86_64.manylinux_2_28_x86_64`), not a per-minor-version `cp312` wheel — **empirically confirmed** this session: `pip download --no-deps --only-binary=:all: faiss-cpu==1.15.1` on this Python 3.12.3 host resolved to `faiss_cpu-1.15.1-cp310-abi3-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` (18.8 MB), no source build triggered [VERIFIED: `pip download` executed this session, real positive result — pip's own resolver, not an assumption]. |
| `underthesea` | 9.5.0 (released 2026-05-17) | Vietnamese word segmentation for the bkai model | [VERIFIED: `pip index versions underthesea` this session]. Base install does **not** pull `torch`/`transformers` — those are gated behind the `deep`/`voice` extras in `requires_dist` [VERIFIED: PyPI JSON `requires_dist`, this session] — so the word-segmentation step itself adds no extra CUDA/torch weight beyond what `sentence-transformers` already needs. Its native extension `underthesea_core` 3.3.2 ships a real `cp312-manylinux2014_x86_64` wheel [VERIFIED: PyPI JSON file listing, this session] — no Rust toolchain needed in the Docker image. |
| `datasketch` | 2.0.0 (released 2026-07-05) | MinHash for verbatim/near-verbatim shingle matching | [VERIFIED: `pip index versions datasketch` this session]. **Breaking change from the version STACK.md assumed ("1.x"):** 2.0.0 changed the *default* MinHash permutation scheme to `"affine32"`, which "fixes a similarity over-estimation bias on large sets, halves sketch memory, and speeds up updates ~4x"; hash values differ from 1.x — only matters if sketches are ever persisted and reloaded across a version bump, not a concern for this phase's greenfield build [VERIFIED: GitHub Releases API, `ekzhu/datasketch` v2.0.0 release notes, this session — official repo]. Default `num_perm=128` [CITED: ekzhu.com/datasketch/minhash.html official docs, MEDIUM]. |
| `python-docx` | ≥1.2 (already in `backend/pyproject.toml:16`) | DOCX text extraction (Web API, already shipped) **and** DOCX generation (DATA-03 test corpus) | Same library already used and already vetted; no new dependency for the extraction side. |
| `pymupdf` | ≥1.28 (already in `backend/pyproject.toml:17`) | PDF text extraction (Web API, already shipped) | Already in use — see Common Pitfalls for a confirmed gap in how it's currently called. |
| `reportlab` | 5.0.1 | Generate the PDF half of the DATA-03 synthetic test corpus **directly from the same paragraph list used for DOCX**, no DOCX→PDF conversion | [VERIFIED: PyPI JSON, this session]. `requires_python: >=3.9,<4` — Python-3.12-compatible. See Architecture Patterns for why this avoids LibreOffice entirely. |
| `scikit-learn` | current (already a transitive dep of `sentence-transformers` per its `requires_dist`) | ROC-based threshold calibration (`roc_curve`, or manual Youden's J) | Pulled in anyway by `sentence-transformers`'s own `requires_dist` — no extra install needed to get `sklearn.metrics.roc_curve`. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `httpx` | 1.x (already in `backend` dev deps) | Web API → AI service HTTP client | Add as a runtime dep (not just dev) to `backend/pyproject.toml` for the new `AiClientHttp` implementation. |
| `pydantic-settings` | 2.x | AI-service config (model name, API key, DB URL) | Mirror `backend/app/core/config.py` pattern exactly (same `Settings` + `get_settings()` shape) for consistency across the two services. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `bkai-foundation-models/vietnamese-bi-encoder` (+ underthesea) | `intfloat/multilingual-e5-base` | ~2.1× larger weight download (1.06 GiB vs 515 MiB, both verified this session), but no segmentation pipeline and no PhoBERT-specific tokenizer quirks. D-01's bake-off is the actual decision mechanism — this table exists so the planner knows the concrete size/complexity tradeoff going in. |
| Converting the 50 test DOCX files to PDF via LibreOffice headless | Generating DOCX (python-docx) and PDF (reportlab) **independently** from the same in-memory paragraph list | LibreOffice is confirmed present on this dev host (`which soffice` succeeds) [VERIFIED: `which soffice` this session] but is a large, stateful dependency to add to a Docker image purely for synthetic test-data generation that has full content control anyway. Generating both formats from one shared paragraph list (a) removes the LibreOffice dependency from any image entirely, (b) guarantees byte-identical paragraph text between the DOCX and PDF version of the same synthetic document (removing a confound when comparing extraction quality — Pitfall 4), and (c) is a one-off `scripts/` tool, not part of the AI service or Web API runtime. Keep LibreOffice as a documented fallback only if a script needs to convert a *real* captured document later (not needed given D-06's "no real text copied" rule). |
| FAISS `IndexFlatIP` (already locked) | Plain NumPy dot-product matrix | Already covered in `research/STACK.md`; reconfirmed still valid — corpus stays in the low thousands of vectors (300 topics + 50×~100 chunks ≈ 5,300 vectors), well under where FAISS's exactness/setup cost stops paying for itself vs raw NumPy. No change from prior research. |

## Package Legitimacy Audit

> Required whenever this phase installs external packages. Ran `gsd-tools query package-legitimacy check --ecosystem pypi` this session.

| Package | Registry | Age (evidence) | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| sentence-transformers | PyPI | 90+ releases, 0.1.0→6.1.0 [VERIFIED: `pip index versions`] | unknown (seam data source unavailable) | github.com/UKPLab/sentence-transformers | SUS (`too-new`, `unknown-downloads`) | Approved — heuristic false positive, see note |
| torch | PyPI | dozens of releases, 2.2.0→2.14.0 [VERIFIED] | unknown | pytorch.org / github.com/pytorch/pytorch | SUS (`too-new`, `unknown-downloads`) | Approved — heuristic false positive, see note |
| underthesea | PyPI | 90+ releases, 1.0.0→9.5.0 [VERIFIED] | unknown | undertheseanlp.com | SUS (`unknown-downloads`) | Approved |
| faiss-cpu | PyPI | 8+ releases, 1.8.0→1.15.1 [VERIFIED], maintained by Meta | unknown | github.com/facebookresearch/faiss | SUS (`too-new`, `unknown-downloads`) | Approved — heuristic false positive, see note |
| datasketch | PyPI | 40+ releases, 0.1.1→2.0.0 [VERIFIED], changelog cross-checked on GitHub | unknown | github.com/ekzhu/datasketch | SUS (`unknown-downloads`) | Approved |
| python-docx | PyPI | already installed in `backend/pyproject.toml`, pre-vetted Phase 2/3 | unknown | github.com/python-openxml/python-docx | SUS (`unknown-downloads`) | Approved (already in production use) |
| pymupdf | PyPI | already installed in `backend/pyproject.toml`, pre-vetted Phase 2/3 | unknown | github.com/pymupdf/pymupdf | SUS (`unknown-downloads`) | Approved (already in production use) |
| reportlab | PyPI | reportlab.com, industry-standard PDF toolkit for 20+ years | unknown | reportlab.com | SUS (`unknown-downloads`) | Approved — heuristic false positive, see note |
| scikit-learn | PyPI | transitive dep of sentence-transformers already | unknown | (no repo URL in PyPI metadata) | SUS (`too-new`, `unknown-downloads`, `no-repository`) | Approved — foundational scientific-Python package, already an indirect dependency regardless |
| fastapi, uvicorn | PyPI | already installed in `backend/pyproject.toml`, pre-vetted Phase 2 | unknown | github.com/fastapi/fastapi, github.com/Kludex/uvicorn | SUS | Approved (already in production use) |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** all of the above, but **all for the identical reason** — the seam's download-count data source (`weeklyDownloads: null` for every single package checked, including `numpy`) was unreachable in this session's environment, and its `too-new` signal keys off the **latest** release date rather than the package's first-ever release, which misfires on every actively-maintained project. Independent verification this session (PyPI version-history length, official repo ownership, and — for `datasketch` — reading the actual GitHub Releases changelog) found no genuine legitimacy concern for any package above. **Recommendation to planner:** add **one** combined `checkpoint:human-verify` task before the first `ai-service/pyproject.toml` install (verify the lockfile resolves against the real registry), rather than one checkpoint per package — per-package gating here would be pure friction given the uniform, explained false-positive cause.

## Architecture Patterns

### System Architecture Diagram

```
                                   ┌─────────────────────────────────────────┐
                                   │           Web API (FastAPI)              │
 Browser (React) ── /api/* ──────▶│  routers: topics, outlines, documents    │
                                   │       │                    │            │
                                   │       ▼                    ▼            │
                                   │  title_check.py    document_check.py    │
                                   │  (sync, UC0.6)      (BackgroundTasks,    │
                                   │       │              UC0.7, §3.3.7)      │
                                   │       └─────────┬──────────┘            │
                                   │                 ▼                       │
                                   │         get_ai_client(db)                │
                                   │      AiClientHttp (NEW, Phase 4)         │
                                   │   httpx + X-API-Key, AI_SERVICE_URL      │
                                   └────────────────┬──────────────────────────┘
                                                     │ HTTP, internal network only
                                                     ▼
                        ┌───────────────────────────────────────────────────┐
                        │        AI Service (FastAPI, 127.0.0.1:8002)         │
                        │                                                    │
                        │  POST /ingest ──▶ NFC normalize ──▶ segment ──▶     │
                        │                   strip boilerplate + chunk ──▶    │
                        │                   embed (batch) ──▶ write          │
                        │                   thesis_ai.chunk + .embedding      │
                        │                                                    │
                        │  POST /check-title ──▶ NFC+segment query ──▶       │
                        │                embed query (1 call) ──▶            │
                        │                FAISS IndexFlatIP.search (in-mem) ──▶│
                        │                top-k cosine % ──▶ response         │
                        │                                                    │
                        │  POST /check-document ──▶ NFC+segment+strip+chunk ─▶│
                        │                embed all chunks (1 batched call) ──▶│
                        │                per-chunk: FAISS cosine OR           │
                        │                          MinHash Jaccard ≥ nguong ──▶│
                        │                aggregate ty_le_tong + chi_tiet ──▶  │
                        │                response (still synchronous HTTP     │
                        │                call FROM Web API's BackgroundTask,  │
                        │                the async-to-the-USER behavior is    │
                        │                entirely a Web API concern)          │
                        │                                                    │
                        │  GET /health ──▶ {status, model_loaded, index_size} │
                        │  POST /reindex ──▶ rebuild FAISS from thesis_ai      │
                        │                                                    │
                        │  at process startup: load model once,               │
                        │  SELECT chunk JOIN embedding, build FAISS index      │
                        │  from thesis_ai — never persisted to a FAISS file   │
                        └──────────────────────┬─────────────────────────────┘
                                                ▼
                                     MySQL schema `thesis_ai`
                                (chunk, embedding, index_metadata)
```

Note the async/sync boundary is **already fully implemented in Phase 3** and does not change: the Web API's `document_check.run()` (`app/services/document_check.py`) already opens its own `SessionLocal`, calls `get_ai_client(db).check_document(...)`, and writes `HOAN_TAT`/`LOI` — Phase 4's job is purely to make that one call hit a real HTTP endpoint instead of the in-process stub, and to make `/check-document` itself synchronous-but-fast-enough-for-a-background-task (the 30 s NFR budget lives entirely inside the AI service's own request/response cycle, not in a second layer of async).

### Recommended Project Structure

```
ai-service/
├── pyproject.toml          # own uv-managed project, python ">=3.12,<3.13"
├── uv.lock
├── Dockerfile               # mirrors backend/Dockerfile pattern (uv sync --frozen)
├── app/
│   ├── main.py               # FastAPI app, lifespan loads model + builds FAISS index once
│   ├── core/
│   │   ├── config.py         # Settings: MODEL_NAME, API_KEY, DATABASE_URL, MODEL_CACHE_DIR
│   │   └── security.py       # X-API-Key dependency, 401 on missing/wrong key (NFR-07)
│   ├── models/                # SQLAlchemy models for thesis_ai (chunk, embedding, index_metadata)
│   ├── nlp/
│   │   ├── normalize.py       # NFC normalization (shared logic, mirrors AISV-02)
│   │   ├── segment.py         # underthesea word_tokenize wrapper (only if bake-off picks bkai)
│   │   ├── boilerplate.py     # heading-pattern + repeated-line stripping (D-03, Pitfall 3/4)
│   │   └── chunking.py        # paragraph/sentence-window chunker
│   ├── embedding/
│   │   ├── model.py           # sentence-transformers load-once wrapper, batched .encode()
│   │   └── index.py           # FAISS IndexFlatIP build/search/rebuild
│   ├── minhash.py              # datasketch MinHash + Jaccard for verbatim signal
│   └── routers/
│       ├── ingest.py
│       ├── check_title.py
│       ├── check_document.py
│       ├── reindex.py
│       └── health.py
└── tests/
    └── fixtures/               # tiny synthetic corpus for standalone unit tests (per specifics: testable before compose wiring)
```

### Pattern 1: Load-once model, precompute-at-ingest, compare-only-the-new-item

**What:** Model is loaded exactly once in FastAPI's `lifespan` startup hook; `/ingest` embeds only the newly-ingested chunk(s) and appends to the in-memory FAISS index; `/check-title` and `/check-document` embed only the incoming query text and search against the already-built index.
**When to use:** Always — this is the only pattern that satisfies NFR-08/NFR-09/NFR-11 given CPU-only inference (Common Pitfall #6 in `research/PITFALLS.md`, reconfirmed applicable here).
**Example:**
```python
# app/main.py — sketch, illustrates the load-once + rebuild-index-at-startup shape
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import faiss

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = SentenceTransformer(settings.MODEL_NAME, cache_folder=settings.MODEL_CACHE_DIR)
    app.state.index, app.state.chunk_ids = build_index_from_db()  # SELECT chunk JOIN embedding
    yield

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: Batched encode for /ingest and /check-document, single encode for /check-title

**What:** `model.encode(list_of_chunks, batch_size=32)` in one call for a multi-chunk document; a single `model.encode([query_text])` for a title check.
**When to use:** Every ingest of a multi-paragraph document, and every `/check-document` call (all chunks of the submitted document encoded together, then compared against the precomputed corpus index).
**Why it matters:** confirmed via web search this session — a single-core sentence-BERT-class model runs roughly "2 sentences per second" un-batched [CITED: nehaytamore.medium.com benchmark writeup, LOW-MEDIUM — blog-sourced, not reproduced on this hardware]; batching plus this host's 16 cores materially changes that number, but the *only* way to validate the 30 s NFR-09 budget for a ~100-chunk document is to measure it directly on the actual host early in implementation — do not assume either the optimistic or pessimistic number holds.
**Fallback if CPU latency threatens the NFR:** `sentence-transformers` officially supports an `onnx` backend via `backend="onnx"` (or `optimum-onnx[onnxruntime]` extra) claiming "up to 2-3x" CPU speedup for short-text workloads [CITED: sbert.net/docs/sentence_transformer/usage/efficiency.html, official docs, HIGH-MEDIUM]. Keep this as a documented escape hatch, not a default — added complexity should only be paid if the plain-torch measurement actually fails the NFR.

### Pattern 3: Boilerplate stripping must handle repeated-line detection generically, not just phrase-matching

**What:** Because the official template (TL-04/TL-05) was never collected (see Environment Availability), and because the *existing, already-shipped* PDF extraction path is naive (`page.get_text()`, confirmed below), the boilerplate stripper cannot rely solely on matching a fixed phrase list against known template headings. It must **also** detect "any line/short-paragraph that repeats near-identically across ≥N chunks of the same document" and drop those before chunking/embedding — this catches repeated headers/footers/page numbers regardless of whether a real template was ever supplied.
**Verified basis:** `backend/app/services/documents.py:96-120` (`extract_text`) — DOCX path (line 107-108): `document = Document(BytesIO(content)); text = "\n".join(p.text for p in document.paragraphs)` — `python-docx`'s `.paragraphs` iterates body paragraphs only, structurally excluding `section.header`/`section.footer` content, so DOCX extraction is already immune to header/footer leakage. PDF path (line 110-111): `with fitz.open(...) as pdf: text = "\n".join(page.get_text() for page in pdf)` — this is PyMuPDF's plain per-page text-stream extraction, **not** the layout-aware `get_text("blocks")` mode `research/PITFALLS.md` Pitfall 4 recommends, and a Word-exported PDF embeds its header/footer text directly into every page's content stream (there is no separate header/footer object for a PDF the way DOCX has). This is out-of-phase-scope to change (owned by Phase 3 code, already shipped), so the AI service's boilerplate stage is the only remaining place this can be fixed. [VERIFIED: `backend/app/services/documents.py:96-120`, read this session; quoted verbatim above]

### Anti-Patterns to Avoid

- **Assuming `pip install torch` is small:** it is not — it declares CUDA-toolkit and NVIDIA library dependencies on Linux by default (verified via live PyPI metadata this session). Always use the `--index-url https://download.pytorch.org/whl/cpu` index for this project.
- **Building a fixed boilerplate phrase list from the official template and stopping there:** the template does not exist yet in this repo; ship a documented generic default list (common Vietnamese thesis section headings: "MỤC LỤC", "TÀI LIỆU THAM KHẢO", "LỜI CAM ĐOAN", "LỜI CẢM ƠN", "DANH MỤC HÌNH ẢNH", "DANH MỤC BẢNG BIỂU", etc.) **plus** the generic repeated-line detector from Pattern 3 above — do not treat the phrase list alone as sufficient.
- **Persisting the FAISS index to a file and loading it on startup instead of rebuilding from `thesis_ai`:** `index_metadata` exists specifically to detect index/DB drift after a restart (per `02-thiet-ke-csdl.md` §3.2.6) — the locked pattern is rebuild-from-DB, not load-from-disk.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cosine similarity search over a few thousand vectors | Custom brute-force loop in Python | `faiss.IndexFlatIP` on L2-normalized vectors (already locked) | FAISS handles normalization-invariant search correctly and is the expected vocabulary for the report; confirmed installable with a stable-ABI wheel, no build cost. |
| Near-duplicate/verbatim-copy detection | Custom n-gram overlap scoring | `datasketch.MinHash` + Jaccard (already locked) | Handles shingle hashing and similarity estimation with well-understood statistical guarantees; default `num_perm=128` is appropriate at this corpus scale — no tuning needed. |
| ROC/threshold selection | Hand-rolled "try a few numbers and eyeball it" | `sklearn.metrics.roc_curve` (already a transitive dependency via `sentence-transformers`) + Youden's J statistic, **or**, given the small calibration-set size (≤35 pairs after the 30% holdout), a simpler "midpoint between max non-duplicate score and min duplicate score" — pick whichever the actual calibration-set size supports without over-fitting noise | A handful of manually-eyeballed data points is exactly Pitfall 5 from `research/PITFALLS.md` ("threshold picked arbitrarily") — use a documented, reproducible statistical method even if the dataset is small, and document which method was used and why in the calibration table for chương 4. |
| PDF/DOCX generation for the 50-file synthetic test corpus | A DOCX→PDF conversion pipeline | Generate both formats independently from one shared Python paragraph list (`python-docx` + `reportlab`) | Removes the LibreOffice dependency entirely and guarantees the two formats contain identical text, which is what DATA-03's manifest/results table needs to be meaningful. |

**Key insight:** every "don't hand-roll" item above is already a locked stack choice (STACK.md/CONTEXT.md) — this phase's real hand-rolling risk is in the *glue* (boilerplate stripping, chunking, threshold selection method), which has no off-the-shelf library and must be built carefully per Common Pitfalls below.

## Common Pitfalls

> `research/PITFALLS.md` already covers this domain in depth (12 pitfalls, cross-referenced by phase). The items below are **new findings from this session's verification pass**, not a repeat of that document — read PITFALLS.md pitfalls #1–#6, #11, #12 alongside these.

### Pitfall A: `torch`'s default PyPI package silently pulls CUDA dependencies on Linux

**What goes wrong:** A plain `pip install torch` (or an unqualified `torch>=2.2` in `pyproject.toml` without an explicit CPU index) resolves platform-conditional dependencies including `cuda-toolkit[cublas,cudart,...]==13.0.3`, `nvidia-cudnn-cu13`, `nvidia-nccl-cu13`, `nvidia-nvshmem-cu13`, and `triton` on Linux — multiple gigabytes, and none of it usable inside a container with no GPU.
**Why it happens:** `torch`'s own `requires_dist` metadata declares these as platform-conditional (`platform_system == "Linux"`) dependencies of the *default* package — there is no separate `torch-cpu` package name; the CPU-only build is a different **index**, not a different **package name**.
**How to avoid:** In `ai-service/pyproject.toml`, configure `[tool.uv.sources]` (or an equivalent index pin) so `torch` resolves against `https://download.pytorch.org/whl/cpu` specifically; verify the resulting lockfile references a `+cpu` wheel tag, not a bare `torch-2.14.0-cp312-...manylinux...whl`.
**Warning signs:** Docker build unexpectedly downloads 2+ GB during the `torch` install step; `docker image ls` shows the ai-service image several GB larger than expected.
**Verified:** [VERIFIED: `torch==2.14.0` PyPI JSON `requires_dist`, this session — direct registry read, not inferred]

### Pitfall B: The official template and old-thesis corpus this phase's own design assumes do not exist yet

**What goes wrong:** D-01's bake-off says to use "a small labeled set of known similar/different Vietnamese thesis-title and paragraph pairs," D-03's boilerplate list says "patterns from the official template when available," and D-06 references "the official template structure when available." All three assume `tai-lieu-goc/mau-chinh-thuc/` (TL-04/TL-05) and `tai-lieu-goc/do-an-cu/` (TL-09/TL-10) contain real material. **They do not** — both directories contain only `.gitkeep`/`.gitignore`, and `tai-lieu-goc/README.md`'s manifest table shows every row's status as `Chưa có` (not yet received).
**Why it happens:** Phase 1's data-collection task (T5, "thu thập kho") depends on interviews/requests to Bộ môn/GVHD that have not concluded by the time Phase 4 planning starts (see `.planning/STATE.md` blocker: "Cần file mẫu đề cương/báo cáo chính thức + ~20 đồ án thật... — Phase 1 → 4").
**How to avoid:** Plan Phase 4 assuming the "otherwise a documented default list" fallback from D-03 is the **actual** path, not a contingency: author a generic Vietnamese-thesis boilerplate heading list from general knowledge of the academic template genre (mục lục, danh mục hình/bảng, lời cam đoan, lời cảm ơn, tài liệu tham khảo, kết luận) and clearly mark it `[ASSUMED]`-derived in the plan/report; author the D-01 bake-off pairs and the D-06 test corpus entirely synthetically (which D-06 already requires anyway — "No real student text is copied verbatim"). Add a follow-up task/checkpoint: if the template does arrive mid-phase (via the still-open Phase 1 collection effort), swap the boilerplate list and re-run calibration — do not block the phase waiting for it.
**Verified:** [VERIFIED: `ls`/`find` on `tai-lieu-goc/mau-chinh-thuc/` and `tai-lieu-goc/do-an-cu/`, this session — both empty except `.gitkeep`/`.gitignore`; `tai-lieu-goc/README.md` manifest table read, all rows `Chưa có`]

### Pitfall C: The existing PDF extraction path is naive and will leak repeated headers/footers into embeddings — cannot be fixed in this phase's scope, must be defended against downstream

See Pattern 3 above (Architecture Patterns) for the full verified code citation. The load-bearing consequence for planning: **do not** write the AI-service boilerplate stripper as "phrase-match against a known template list" alone; it must include a generic "drop lines that repeat near-identically across many chunks of the same source document" pass, because the upstream extraction (already shipped, Phase 3, out of scope to touch) does not structurally separate PDF headers/footers from body text the way it does for DOCX.

### Pitfall D: CPU embedding latency for a ~100-chunk document is an unverified assumption, not a measured number

**What goes wrong:** The NFR-09 target (≤30 s P95 for a full document check) and this phase's whole async-background pattern are built around an *assumed* CPU throughput. The only concrete public data point found this session — "2 sentences per second on a single CPU core" for a Sentence-BERT-class model — is blog-sourced (LOW-MEDIUM confidence) and not reproduced on this project's actual host or actual model (`bkai-foundation-models/vietnamese-bi-encoder` specifically). Naively, 100 chunks at 2/sec/core un-batched would be 50 s — already over budget — while batching + this host's 16 cores could bring that well under budget, or batching gains could be smaller than hoped for longer academic-paragraph-length chunks (which are longer than typical benchmark sentences, and attention cost grows with sequence length).
**How to avoid:** Make "measure batched CPU encode time for a 100-chunk synthetic document on the target Docker container" one of the **first** implementation tasks (not an afterthought at the T9 verification phase this NFR is nominally tied to) — if it's already too slow, the ONNX backend fallback (Pattern 2 above) or a smaller default chunk count is cheaper to apply early than late.
**Verified:** [CITED: nehaytamore.medium.com benchmark, LOW-MEDIUM — not independently reproduced this session, explicitly flagged as an open question below, not presented as settled]

## Code Examples

### Extending `Settings` for the AI-service HTTP client (Web API side)

```python
# backend/app/core/config.py — additions needed in Phase 4 (mirrors existing style at lines 27-29)
AI_SERVICE_URL: str | None = None   # e.g. "http://ai:8002" per D-07 compose service name
AI_API_KEY: str | None = None       # sent as X-API-Key header; never logged
# AI_CLIENT gains a new valid value "http" alongside the existing "stub" (config.py:28 comment
# already anticipates this: "Phase 4 thêm nhánh AI_CLIENT='http' ở đây.")
```

### `get_ai_client` branch to add (Web API side)

```python
# backend/app/services/ai_client.py — get_ai_client(), currently only returns AiClientStub
# (see file body: "Phase 2/3 chỉ hỗ trợ 'stub'; Phase 4 thêm nhánh AI_CLIENT='http' ở đây.")
def get_ai_client(db: Session) -> AiClient:
    settings = get_settings()
    if settings.AI_CLIENT == "http":
        return AiClientHttp(settings.AI_SERVICE_URL, settings.AI_API_KEY)
    return AiClientStub(...)  # existing stub path, unchanged, kept as fallback per D-07
```

### Vietnamese word segmentation before embedding (if D-01 selects the bkai model)

```python
# app/nlp/segment.py — Source: bkai-foundation-models/vietnamese-bi-encoder model card (CITED)
from underthesea import word_tokenize

def segment(text: str) -> str:
    return word_tokenize(text, format="text")  # joins syllables with "_", e.g. "sinh_viên"
```

### E5 prefix convention (if D-01 selects multilingual-e5-base instead)

```python
# Source: intfloat/multilingual-e5-base model card (CITED) — symmetric task (semantic
# similarity between two titles/paragraphs) uses "query: " on BOTH sides, not "query:"/"passage:"
def embed_symmetric(model, text: str):
    return model.encode(f"query: {text}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `research/STACK.md` recommended `datasketch` "1.x" | `datasketch` 2.0.0 (current) defaults to the `affine32` MinHash permutation scheme instead of the legacy scheme | 2026-07-05 (v2.0.0 release) | No functional impact for a greenfield Phase 4 build (nothing persisted yet to be incompatible with) — only matters if a future phase ever persists MinHash sketches across a `datasketch` major-version bump; note it in the plan so nobody is confused by hash values differing from any older reference material. [VERIFIED: GitHub Releases API, `ekzhu/datasketch`, this session] |
| `faiss-cpu` used to ship per-Python-minor-version wheels (`cp310`, `cp311`, `cp312`, distinct binaries) | `faiss-cpu` ≥1.15.x ships a single `cp310-abi3` stable-ABI wheel covering Python 3.10+ on Linux/macOS | Confirmed at 1.15.0/1.15.1 (checked both) | No action needed — `pip`/`uv` resolve it correctly automatically (empirically confirmed this session) — but if the plan or a future debugging session greps for a `cp312` filename specifically and finds none, that is expected, not a missing-wheel bug. [VERIFIED: PyPI file listing + live `pip download` resolution test, this session] |
| Naive `page.get_text()` PDF extraction (already shipped, Phase 3) | Layout-aware `get_text("blocks")` extraction (recommended in `research/PITFALLS.md` Pitfall 4, never actually adopted) | N/A — the naive path is what's in production today | Out of scope to change in Phase 4; the boilerplate-stripping stage in the AI service must compensate instead (see Pitfall C above). |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A generic (non-template-derived) Vietnamese thesis boilerplate heading list will adequately approximate the real official template well enough for calibration to transfer once the real template arrives | Common Pitfalls (B), Architecture Patterns (Anti-Patterns) | If the real template's structure differs meaningfully (e.g., different section ordering, additional mandatory boilerplate paragraphs), false positives could persist even after this phase's calibration — mitigated by re-running calibration when/if the template is collected, already noted as a follow-up |
| A2 | Batched CPU encoding of ~100 chunks will fit the 30 s NFR-09 budget on the eventual target hardware | Common Pitfalls (D), Architecture Patterns (Pattern 2) | If it doesn't, the async/BackgroundTasks pattern (already built, Phase 3) absorbs some of the impact since it's not blocking the submit response (NFR-10), but the "Hoàn tất" status could take much longer than 30 s, degrading UX and failing the explicit NFR check at Phase 5 — mitigated by measuring early (recommended as a first task) and the documented ONNX-backend fallback |
| A3 | D-01's bake-off model choice (bkai vs e5-base) generalizes from a small synthetic pair set to the full 300-topic + 50-document corpus | Standard Stack (model rows) | A model that looks good on a handful of hand-authored pairs could behave differently at corpus scale (more topically-adjacent-but-distinct titles to discriminate against) — mitigated by D-06's held-out validation split, which is designed exactly for this |
| A4 | The 128-default `num_perm` and a k≈5-8 word shingle size (already Claude's-discretion per CONTEXT.md) will separate the seeded exact-copy/paraphrase pairs from same-field/unrelated pairs without further tuning | Standard Stack (datasketch row), Don't Hand-Roll | Low risk given corpus scale (thousands of vectors, not millions) — MinHash accuracy at `num_perm=128` is a well-documented default; if separation is poor, the fix is a shingle-size adjustment, not a library change |

**If this table is empty:** N/A — see rows above; everything else in this document is either `[VERIFIED]` this session or `[CITED]` from an official/model-card source.

## Open Questions

1. **Will the D-01 bake-off actually have enough labeled pairs to make a statistically meaningful AUC comparison?**
   - What we know: D-01 calls for "a small labeled set" and the bake-off set size is explicitly Claude's discretion; no real corpus exists to draw pairs from (Pitfall B).
   - What's unclear: How many synthetic pairs is "enough" to trust a model-selection decision that will govern the rest of the phase.
   - Recommendation: Treat the bake-off as directional, not statistically rigorous — pick the model with the clearer separation AND acceptable latency, document the small-sample caveat explicitly in the chương 4 report, and rely on D-06's larger 50-document/held-out-validation set as the real calibration evidence.

2. **What is the actual batched CPU embedding throughput for the chosen model, on the actual deployment container, for a 100-chunk document?**
   - What we know: One blog-sourced single-core data point (2 sentences/sec), 16 cores available on this dev host, official ONNX-backend fallback exists if needed.
   - What's unclear: Real throughput for this specific PhoBERT-base-v2-sized model, batched, on whatever CPU the actual target server has (still unknown per D-02's own note).
   - Recommendation: Measure directly as an early implementation task (see Common Pitfalls D), not deferred to Phase 5 verification.

3. **Where exactly should `AiClientHttp` live and what should its retry/timeout behavior be when the AI service is slow or down?**
   - What we know: `AiClientError`-equivalent already exists as `AiServiceError` in the current stub (`ai_client.py:26-28`) and is documented as "never block business logic" — the Web API's title-check and document-check flows already have `alt` branches for AI-service failure in the sequence diagrams (§3.3.7).
   - What's unclear: Concrete `httpx` timeout values appropriate for a ≤5 s / ≤30 s NFR budget (the HTTP client's own timeout must be comfortably inside those numbers, not equal to them, to leave room for the Web API's own overhead).
   - Recommendation: Set `httpx` timeouts at roughly 80% of the relevant NFR (e.g., ~4 s for title check, ~24 s for document check) so the Web API can raise `AiServiceError` and fail gracefully before the NFR clock itself expires.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker / docker compose | AI service deployment (D-07) | ✓ (existing `ntma` stack running) | — | — |
| Python 3.12 (matching existing backend) | AI-service runtime | ✓ (host has 3.12.3; Docker base already `python:3.12-slim`) | 3.12.3 (host) / 3.12-slim (image) | — |
| `uv` package manager pattern | AI-service Dockerfile, mirrors `backend/Dockerfile` | ✓ (existing Dockerfile pins `uv:0.11.19`; latest upstream is `0.12.19`, released 3 days before this research) | 0.11.19 (pinned in-repo) | Keep the same pin as `backend/Dockerfile` for consistency; bumping both together is a separate, low-risk decision, not required for this phase |
| Network access to PyPI / Hugging Face at build/first-run time | Installing packages + downloading the embedding model into the cache volume | ✓ (verified live this session — PyPI JSON API, HF resolve redirects, pytorch.org CPU wheel index all reachable) | — | If the actual deploy server has no outbound internet, the model weights (515 MiB–1.06 GiB) and CPU torch wheel (~187 MiB) must be pre-downloaded and baked into the image or volume ahead of time — flag this explicitly to the user since D-02 notes the target server is unknown |
| Official thesis template (TL-04/TL-05) | D-03 boilerplate list, D-06 test-corpus structure | ✗ — confirmed empty (`tai-lieu-goc/mau-chinh-thuc/` contains only `.gitkeep`) | — | Documented generic default boilerplate list (see Common Pitfalls B) — no blocking fallback needed, D-03 already anticipates this |
| Old real theses (TL-09/TL-10) | D-01 bake-off pairs | ✗ — confirmed empty (`tai-lieu-goc/do-an-cu/` contains only `.gitignore`) | — | Fully synthetic bake-off + test corpus (already required anyway by D-06's privacy rule) |
| RAM headroom on this dev host | Loading the embedding model (~515 MiB–1.06 GiB weights) + torch runtime (~200-400 MiB overhead) alongside the already-running `ntma` stack | ⚠ — host has 15 GiB total; **only 837 MiB immediately free**, though 7.7 GiB is reclaimable buff/cache (≈7.5 GiB "available"); the existing `ntma` containers currently use only ~700 MiB combined, but this is a **shared dev machine** also running several unrelated projects (`ttv-mongo`, `chathrms-*`, `tcengine-postgres` — confirmed via `docker ps`/`docker stats` this session) that this user's own prior notes record has hit OOM before on this exact 16 GiB machine | 15 GiB total / 7.5 GiB available at measurement time | Budget the AI-service container conservatively (e.g., a documented ~2 GiB working-set target) and prefer the smaller bkai model (515 MiB) over e5-base (1.06 GiB) unless the bake-off strongly favors e5-base, purely to reduce shared-host memory pressure risk — this is a real, previously-experienced failure mode on this machine, not a hypothetical |
| LibreOffice (`soffice`) | Not required if reportlab approach is adopted (recommended) | ✓ present on this dev host regardless (`which soffice` succeeds) | — | N/A — documented only as evidence the fallback path is available if ever needed later |

**Missing dependencies with no fallback:** none — every gap above has a documented, already-anticipated fallback (synthetic data, generic boilerplate list, conservative model choice).

**Missing dependencies with fallback:** official template, old-thesis corpus (both use the synthetic/generic fallback already baked into D-03/D-06); potential offline-deploy-server internet access (fallback: pre-bake weights into the image/volume).

## Security Domain

> `security_enforcement` is enabled (ASVS Level 1, `security_block_on: high`) per `.planning/config.json`.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No (service-to-service only, no end-user auth in the AI service) | N/A — user JWT terminates at the Web API per §3.3.4/§3.3.8, already locked |
| V3 Session Management | No | N/A |
| V4 Access Control | Yes | Static internal `X-API-Key` header, checked on every non-`/health` endpoint (already specified §3.3.5: "Mọi endpoint (trừ `/health`) yêu cầu header `X-API-Key` hợp lệ; thiếu hoặc sai trả về 401"); enforce via a FastAPI dependency applied uniformly (same pattern as the Web API's `require_role`, per `research/PITFALLS.md` Pitfall 9's lesson — one shared dependency, not per-route ad hoc checks) |
| V5 Input Validation | Yes | Pydantic request models on every AI-service endpoint (`{id, type, text}` for `/ingest`, etc. per §3.3.5); reject oversized text payloads defensively even though the AI service never receives raw files (a very large `text` field could still be a resource-exhaustion vector for CPU embedding) |
| V6 Cryptography | No new surface | The internal API key is a shared secret compared via constant-time comparison (`hmac.compare_digest`), not stored hashed (it's a service credential, not a user password) — never hand-roll the comparison as `==` |
| V10 SSRF / internal network boundary | Yes | Already locked: AI service binds `127.0.0.1:8002` only, no Apache `ProxyPass` route (NFR-07) — verify this explicitly during implementation with the same test NFR-07 already specifies: call the AI service directly (bypassing Apache) without the API key and confirm `401`; confirm Apache's config has no route to port 8002 |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Missing/forged `X-API-Key` reaching a business-logic endpoint | Spoofing | Uniform FastAPI dependency checked before any handler body runs, constant-time comparison, applied via `app.include_router(..., dependencies=[Depends(require_api_key)])` rather than per-route |
| Oversized or pathological `text` payload sent to `/check-document` causing CPU/RAM exhaustion (a "few-KB text that decompresses to a huge token count" is not a real DOCX-zip-bomb vector here since the AI service never receives files — but an extremely long string is still a resource-consumption vector) | Denial of Service | Reject request bodies with a text length ceiling well above any realistic thesis chunk but well below a memory-exhaustion threshold (e.g., a few MB of text) at the Pydantic model level (`max_length`) |
| AI-service internal API key leaking into logs or error responses | Information Disclosure | Never log the `X-API-Key` header value; ensure FastAPI's default exception handlers don't echo request headers in `debug`/`docs` responses |
| A future contributor adding an Apache `ProxyPass` for the AI service "just to test something" and forgetting to remove it | Elevation of Privilege (bypasses the entire internal-only boundary) | Keep NFR-07's verification step (grep Apache config for any route to port 8002) as a standing pre-deploy check, not a one-time check at initial build |

## Sources

### Primary (HIGH confidence — read/executed directly this session)
- `pip index versions <pkg>` — live PyPI registry queries for sentence-transformers, faiss-cpu, underthesea, datasketch, torch, reportlab, fpdf2
- PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`) — `requires_dist`/`requires_python` for sentence-transformers, underthesea, faiss-cpu, torch, datasketch, underthesea_core, reportlab
- `https://download.pytorch.org/whl/cpu/torch/` index listing + `curl -sI` HEAD requests — CPU wheel existence and exact byte sizes for torch 2.9.1+cpu and 2.14.0+cpu, cp312, manylinux_2_28_x86_64
- `https://huggingface.co/api/models/<model>` + resolve-redirect `curl -sIL` — file listings and exact `model.safetensors` byte sizes for `bkai-foundation-models/vietnamese-bi-encoder` and `intfloat/multilingual-e5-base`
- `https://api.github.com/repos/ekzhu/datasketch/releases` — official GitHub Releases API, v2.0.0 changelog (affine32 scheme change)
- `pip download --no-deps --only-binary=:all: faiss-cpu==1.15.1` — empirical resolution test on this Python 3.12.3 host, confirmed `cp310-abi3` manylinux wheel resolves correctly
- `backend/app/services/documents.py:96-120`, `backend/app/services/document_check.py`, `backend/app/services/ai_client.py`, `backend/app/models/trung_lap.py`, `backend/app/models/cau_hinh_nguong.py`, `backend/app/models/de_cuong.py`, `backend/app/core/config.py`, `backend/pyproject.toml`, `backend/Dockerfile`, `deploy/docker-compose.yml` — all read directly this session
- `docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md`, `docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.puml`, `docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md` (§3.2.3/§3.2.6), `docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md`, `docs/chuong-3-thiet-ke/mockup/mh-14.html` — all read directly this session
- `tai-lieu-goc/README.md`, `find tai-lieu-goc/mau-chinh-thuc tai-lieu-goc/do-an-cu` — confirmed empty collection directories this session
- `docker ps` / `docker stats --no-stream`, `free -h`, `df -h`, `nproc` — live host resource snapshot this session

### Secondary (MEDIUM confidence)
- huggingface.co/bkai-foundation-models/vietnamese-bi-encoder model card (via WebSearch) — segmentation requirement, benchmark claim
- huggingface.co/intfloat/multilingual-e5-base model card (via WebSearch) — prefix convention
- ekzhu.com/datasketch/minhash.html official docs (via WebFetch) — default `num_perm=128`, Jaccard estimation mechanism
- sbert.net/docs/sentence_transformer/usage/efficiency.html official docs (via WebSearch) — ONNX backend CPU speedup claim

### Tertiary (LOW confidence — flagged for validation, not treated as settled)
- nehaytamore.medium.com CPU throughput benchmark ("2 sentences/sec single core") — single blog source, not reproduced on this hardware/model; see Open Question 2

### Carried forward from prior phase research (already MEDIUM/LOW per their own confidence tags, not re-verified beyond what's noted above)
- `.planning/research/STACK.md`, `.planning/research/PITFALLS.md` — full domain research from Phase 1; this document supplements rather than repeats them

## Metadata

**Confidence breakdown:**
- Package versions/wheel availability/sizes: HIGH — live-verified against PyPI/HF/pytorch.org this session, several with empirical `pip download` resolution tests
- Vietnamese embedding model choice (bkai vs e5-base): MEDIUM — model cards read, but the actual decision is explicitly deferred to D-01's own bake-off, which this research does not (and should not) preempt
- CPU latency for full-document checks: LOW→flagged — no reproducible benchmark on this exact model/hardware; documented as Open Question 2 and Assumption A2, not asserted as fact
- Environment/data-collection gaps (missing template/corpus): HIGH — directly verified via filesystem inspection this session
- Security domain: MEDIUM — ASVS category mapping is standard reasoning applied to an already-locked architecture, not independently re-verified against the ASVS document text itself

**Research date:** 2026-09-28
**Valid until:** ~14 days for the package-version rows (fast-moving PyPI ecosystem, several packages released within days of this research); ~30 days for the architectural/schema findings (locked in `docs/`, stable); re-verify immediately if the official template or old-thesis corpus arrives (Pitfall B), as that changes the D-03/D-06 fallback assumptions this document relies on
