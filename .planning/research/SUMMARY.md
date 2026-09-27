# Project Research Summary

**Project:** Hệ thống quản lý đồ án sinh viên — Khoa CNTT, ICTU (Thesis/Capstone Management System with AI Similarity Detection)  
**Domain:** Vietnamese university thesis management + local-embedding plagiarism detection  
**Researched:** 2026-09-27  
**Confidence:** MEDIUM-HIGH (core stack patterns = HIGH; Vietnamese NLP specifics = MEDIUM; academic workflow patterns = HIGH)

## Executive Summary

This project builds a bounded thesis-management system for a Vietnamese CS faculty, combining straightforward CRUD workflow (5 use cases: Topic → Outline → Progress → Defense → Archive) with a differentiated AI feature: local, in-faculty document similarity detection (not web-scale Turnitin). The architecture is genuinely SOA—Web API, React SPA, and AI microservice separated by explicit service boundaries—which makes it both a realistic capstone architecture and aligned with grading rubrics emphasizing component isolation.

The **recommended approach** mirrors commercial academic workflow platforms (OpenEduCat, Creatrix Campus) for the core 5 UCs, but invests the AI effort into closed-corpus, Vietnamese-aware embedding-based checking rather than attempting external web indexing. The stack is pragmatic: Python 3.11 FastAPI (specified by user), React 19, MySQL 8.0 with explicit `utf8mb4_vietnamese_ci` collation, and local sentence-transformers models (e.g., bkai-foundation-models/vietnamese-bi-encoder) with FAISS vector indexing. All AI runs on CPU in a separate service, avoiding paid API dependencies.

**Key risks** center on three areas that commonly break academic-NLP projects: (1) Vietnamese text normalization (NFC vs NFD Unicode forms silently breaking embedding comparisons), (2) undetected false positives from shared document templates (nearly every thesis follows the same structure, inflating similarity noise), and (3) response-time blowout when embedding the full 300-topic corpus at comparison time rather than precomputing vectors. Prevention is straightforward if planned early (canonical Unicode form at API boundaries, boilerplate detection before embedding, precomputed vectors in the data model), but late discovery of any of these during T8–T9 (AI and deployment phases) will derail the timeline. The roadmap must front-load architecture decisions and data-model planning (T4) to lock these choices before UC implementation begins.

## Key Findings

### Recommended Stack

**Backend & API:** Python 3.11 + FastAPI 0.141.x with Uvicorn behind Apache. FastAPI is user-mandated; the async-native design and Pydantic v2 validation are well-matched to the 3 components (Web API, AI service, React client) requiring clear API contracts.

**Database:** MySQL 8.0.x with **explicit `CHARACTER SET utf8mb4 COLLATE utf8mb4_vietnamese_ci`** at database/table creation time. The charset choice is non-negotiable for correct Vietnamese diacritic storage and sorting; the legacy `utf8` (3-byte limit) or generic collations silently corrupt or mislabel Vietnamese names. Use SQLAlchemy 2.0.54 ORM (not bleeding-edge 2.1, released 2026-09-24) with Alembic 1.20.0 migrations. For async database access, use `asyncmy` 0.2.x driver (Cython-accelerated). If under timeline pressure and unfamiliar with async, **sync SQLAlchemy + PyMySQL is fully legitimate**—FastAPI threadpools the blocking calls automatically.

**Frontend:** React 19 + Vite 7.3.x (Create React App is dead). Pair with TypeScript 5.x, TanStack Query v5 (server-state), and Ant Design v5/v6 (data-heavy tables/forms). Zustand for lightweight client-state (auth token, role).

**AI/Embeddings Stack:** sentence-transformers 5.6.x + **bkai-foundation-models/vietnamese-bi-encoder** (PhoBERT-v2 backbone, 73.3% Acc@1 on legal-text benchmarks) OR **intfloat/multilingual-e5-base** (simpler fallback). **Critical:** if using bkai encoder, preprocess all text through **underthesea 9.2.x** word segmentation first—PhoBERT was trained on segmented text (`sinh_viên`), and raw text silently degrades embedding quality. FAISS 1.15.x for in-process vector index (exact flat index `IndexFlatIP` is sufficient at <10k vectors). datasketch 1.x for MinHash+LSH near-duplicate detection.

**File Parsing:** python-docx 1.1.x (most mature for paragraph extraction), PyMuPDF 1.24.x+ (fastest PDF extraction, preserves Vietnamese diacritics). Skip pdfminer.six directly.

**See STACK.md** for full rationale, version compatibility, and stack-pattern variants.

### Expected Features

**Must have** (table stakes for thesis-mgmt):
- Topic proposal/registration/approval/assignment with state transitions
- Outline (đề cương) submission (DOCX/PDF), supervisor review/approve/reject-with-comments, revision loop
- Progress tracking with periodic reports + supervisor feedback
- Defense committee formation (assign lecturers) + scheduling + score entry
- Archive: search/browse past theses across cohorts (khóa) with metadata
- RBAC: 3 fixed roles (Student / Lecturer / Admin) with role-specific dashboards
- Similarity check triggered at submission with results (matched items, %, highlighted passage)

**Should have** (competitive differentiation—the AI is here):
- **Semantic topic-title duplicate warning at registration** — catches near-duplicate titles phrased differently
- **Passage-level duplicate detection on outline/report** — compare against faculty archive, report which paragraphs matched, matched source document, aggregate %
- **Local AI with no paid API dependency** — satisfies cost + data-privacy constraint
- **Similarity check integrated into approval workflow** — supervisor sees score before approving

**Defer to v2+** (out of scope):
- Web-scale plagiarism comparison, group topics, real-time chat, mobile app, SSO integration

**Feature dependencies:** RBAC → auth → user/role data; Topic registration → RBAC + (optionally) AI + archive seed; Outline submission → Topic approved + file parsing + (optionally) AI check; Defense → all prior phases.

**See FEATURES.md** for full feature landscape, prioritization matrix, and feature-dependency DAG.

### Architecture Approach

**SOA with three independently-deployed components:** (1) React SPA (static, served by Apache), (2) Web API (FastAPI, uvicorn on localhost:8001), (3) AI Similarity Service (FastAPI, uvicorn on localhost:8002). Both FastAPI services use MySQL with **schema separation** (`thesis_core` owned by Web API, `thesis_ai` owned by AI service)—this enforces the service boundary and keeps the architecture honest (services are decoupled at the data layer, not just HTTP).

**Key architectural patterns:**
- **Sync for title checks** (tiny payload, sub-second): Web API makes a synchronous REST call to AI service `/check-title`, gets back ranked similar titles + scores, returns inline.
- **Async for document checks** (large payload, seconds-long): Web API accepts upload, stores file, creates `SimilarityCheckResult` row with status=PENDING, returns 202 Accepted, then runs expensive comparison in a background task (FastAPI `BackgroundTasks`). Client polls result endpoint until status=DONE.
- **Text extraction in Web API only:** AI service never parses DOCX/PDF; Web API extracts text and sends only plain text to AI service.
- **Vectors stored in AI service's schema, precomputed at ingest time:** Embeddings are computed once (at ingest/seeding) and persisted in `thesis_ai.embeddings`. At AI-service startup, load all vectors into in-memory FAISS `IndexFlatIP`; at comparison time, only embed the new submission (1 model call), then query precomputed index (fast cosine similarity). Avoids "re-embed entire corpus per request" anti-pattern.

**Suggested project structure:** `web-api/`, `ai-service/`, `client/`, `deploy/`, `docs/`.

**Build order by dependency:** (1) Database schema + Web API models, (2) Web API auth + RBAC dependencies, (3) Core UC routers with AI *stubbed*, (4) React client, (5) AI service standalone, (6) Replace stub with real AI client, (7) Apache proxy, (8) Seed data + integration testing, (9) UAT.

**See ARCHITECTURE.md** for component responsibilities, data-flow diagrams, anti-patterns, and integration points.

### Critical Pitfalls

1. **Unicode normalization (NFC vs NFD) silently breaks matching.** Vietnamese text can be encoded two ways; embeddings and SQL queries fail silently on byte-different-but-visually-identical strings. **Prevention:** Apply `unicodedata.normalize("NFC", text)` immediately at every text-ingestion boundary (API input, file extraction, before embedding). Phase: T4 (architecture), enforce in shared text-utility before UC implementation. Verify during T6 with Vietnamese seed data.

2. **Feeding raw (un-segmented) Vietnamese text into PhoBERT-based embedding models.** PhoBERT was trained on word-segmented input (`sinh_viên`); raw text works (no error) but produces degraded similarity scores—invisible quality bug. **Prevention:** Check embedding model card; if segmentation required, run `underthesea` word tokenization consistently before every embed call. Phase: T8, write small calibration test (5-10 known-similar/dissimilar pairs) before wiring up UI.

3. **False positives from shared outline templates, boilerplate, reference lists.** Every đề cương follows the same official template with identical section headers and references. Naive paragraph-embedding comparison flags nearly every pair as high-similarity purely from shared structure. **Prevention:** (a) Strip known boilerplate before comparison, (b) compare at paragraph level, (c) exclude/down-weight reference section. Phase: T5 (extract official template early), T8 (AI design).

4. **DOCX/PDF extraction noise contaminates embeddings.** Naive full-text extraction pulls in repeated headers/footers (every page), page numbers, auto-generated TOC (duplicate all headings), garbled tables. **Prevention:** For DOCX, iterate only `document.paragraphs` (body), explicitly exclude headers/footers. For PDF, use layout-aware extraction (pdfplumber `layout=True`, PyMuPDF `get_text("blocks")`). Build one shared extraction module. Phase: T5/T8.

5. **Similarity threshold picked arbitrarily without calibration.** Without ground truth, developers pick "looks reasonable" cutoffs (e.g., ">80%"). Embedding cosine-similarity for academic Vietnamese text clusters deceptively high (0.5–0.7 common for related-but-different topics). **Prevention:** Use intentionally-seeded duplicate pairs as calibration set: compute scores for known-duplicate and known-non-duplicate pairs, pick threshold(s) that separate with margin. Prefer two-tier output (graduated warning bands). Phase: T8 (AI) + T9 (seed/test).

6. **CPU-only embedding generation blows response-time NFR under full corpus load.** Re-embedding entire corpus (300 topics + 50 documents) per request takes seconds-to-minutes. Problem only appears during integration with full seed data (T9), too late to fix. **Prevention:** Precompute embeddings at ingest/seed time; at comparison time, only embed the new submission (1 model call), then compare against precomputed vectors. Phase: T4 (schema design), T8 (precompute-on-ingest pattern), T9 (verify against NFR).

**See PITFALLS.md** for 12 comprehensive pitfalls including technical debt patterns, security mistakes, UX pitfalls, recovery strategies, and pitfall-to-phase mapping.

## Implications for Roadmap

Based on research and the project's fixed 10-week timeline (T1–T10, where T1–T3 are complete), the following phase structure is recommended.

### Phase 1: Architecture & Data Model (T4)
**Rationale:** Everything downstream depends on correct foundational decisions. Database schema, RBAC patterns, file/embedding storage design must be locked before UC implementation. Early decisions on Unicode normalization and embeddings caching prevent expensive rework in T8–T9.

**Delivers:**
- Database schema (`thesis_core` with explicit `utf8mb4_vietnamese_ci`): Student, Lecturer, Topic, Outline, ProgressReport, Committee, ProjectDocument, SimilarityCheckResult
- AI service schema (`thesis_ai`): embeddings, chunks, index_metadata
- Shared text-ingestion utility (Unicode normalization NFC + input validation)
- Reusable FastAPI dependencies for RBAC (role-based + resource-ownership checks)
- Alembic migration setup
- Sync vs async database pattern decision
- Embedding precomputation placement in schema

**Avoids Pitfalls:** Unicode normalization (#1), embeddings precomputation (#6), RBAC enforcement (#9), MySQL charset (#7)

**Research Flags:** 
- Decide sync vs async early; if unfamiliar with async, validate a sample UC works before full implementation (LOW risk, HIGH impact on code style).
- Confirm exact Vietnamese embedding model before T8 (bkai + underthesea vs multilingual-e5); prepare small calibration set now.

---

### Phase 2: UI Mockups & Data Collection (T5)
**Rationale:** Pairing UI design with real historical data collection ensures feature design is grounded. Early extraction of the official template DOCX enables boilerplate-stripping rules. Seed data design (which duplicate pairs to construct) should happen alongside AI feature design.

**Delivers:**
- Figma mockups for all 5 UC flows (all 3 roles)
- Extraction of official đề cương/báo cáo template DOCX (used for boilerplate detection in T8)
- Sourcing of ~20 real historical đồ án files (test extraction logic, seed realistic pairs, validate embeddings)
- Seed-data design: which topical clusters for 300 đề tài, which duplicate-pair spectrum for 50 documents (exact-copy, paraphrased, same-domain-different-topic, unrelated)

**Avoids Pitfalls:** DOCX/PDF extraction noise (#4), seed-data unrealism (#11)

**Research Flags:**
- Validate that sourced historical documents are representative of actual student writing (if too polished/different, AI calibration will be misleading).

---

### Phase 3: Database Schema & Web API Core (T6)
**Rationale:** Core CRUD infrastructure must be in place before UC implementation. Stand up Apache reverse proxy early (don't defer to T9), enabling integration testing against real deployment environment.

**Delivers:**
- MySQL schema deployed with explicit `utf8mb4_vietnamese_ci` collation (verified with Vietnamese names)
- FastAPI Web API skeleton: routers, models, schemas, dependency injection
- RBAC framework: JWT validation, role claims, `Depends(require_role(...))` dependencies
- Shared text-ingestion utility (Unicode normalization + input validation)
- File storage (server-side UUID-named uploads, outside static web root)
- Apache vhost config with reverse proxy to Web API, HTTPS with self-signed cert
- AI service stub client (httpx-based, returns hardcoded empty results)

**Avoids Pitfalls:** RBAC enforcement (#9), MySQL charset (#7), Apache proxy issues (#10), file upload security (#8)

**Research Flags:**
- **MEDIUM priority:** Test Apache reverse-proxy setup with real uploads and HTTP timeouts early (don't wait until T9).

---

### Phase 4: Core Use-Case Implementation (T7)
**Rationale:** Implement all 5 UCs in rapid succession, reusing RBAC framework. AI calls are stubbed, so UCs are independently testable. "Breadth" phase—all features partially done—before T8 focuses on "depth" of AI quality.

**Delivers (one UC per week, approximately):**
- **UC1 (Topic):** Proposal, registration, approval, supervisor assignment. States and transitions. Verify RBAC.
- **UC2 (Outline):** File upload (type/size validation), text extraction, review/approve/reject-with-comments, revision loop. Verify extraction quality against real DOCX/PDF.
- **UC3 (Progress):** Periodic report submission, GVHD feedback, admin progress dashboard. Verify versioning.
- **UC4 (Defense):** Committee formation, scheduling, score entry, result aggregation. Verify constraints.
- **UC5 (Archive):** Store completed theses, search/filter, read-only per role. Verify RBAC.
- React client for all 5 UCs, wired to real Web API.

**Avoids Pitfalls:** RBAC enforcement (#9—verify every route has `Depends(require_role(...))` and resource-ownership checks), file upload validation (#8), response time (#6—precomputed embeddings structure already in place)

**Testing:** Automated RBAC tests, UC acceptance criteria per role, end-to-end flows.

---

### Phase 5: AI Service Development (T8)
**Rationale:** Build AI service in isolation, tested against small hand-made corpus first. Once working, wire into Web API's UC flows.

**Delivers:**
- AI service FastAPI skeleton: schema, config, dependency injection (API-key auth)
- Embedding model loading (chosen model, verified in T4)
- Chunking/segmentation logic (Vietnamese word segmentation if using bkai)
- FAISS index build/load (in-memory `IndexFlatIP` on startup)
- `/ingest` endpoint (accept `{id, type, text}`, embed, append to index, persist)
- `/check-title` endpoint (sync: return ranked similar titles + scores)
- `/check-document` endpoint (return `{overall_score, matched_documents, matched_spans}`)
- `/reindex` endpoint (bulk ingestion for seed)
- Small hand-made corpus test (10–20 items, known similar/dissimilar pairs) validating embedding quality and threshold calibration
- Integration test: AI service called from Web API, title check returns real results
- Response-time benchmark: verify `/check-document` latency with full 300/50-item corpus meets NFR (target: <5s title, <30s document on CPU)

**Avoids Pitfalls:** Word segmentation (#2), boilerplate false positives (#3), extraction noise (#4), threshold calibration (#5), response-time NFR (#6)

**Research Flags:**
- **HIGH priority:** Model accuracy on actual Vietnamese thesis data. Recommend small labeled validation set (20–30 samples rated as similar/dissimilar by expert) to compare bkai vs multilingual-e5 on actual capstone writing before committing.
- **MEDIUM priority:** Threshold sensitivity analysis. Run calibration data through AI service with different thresholds (0.5–0.8), document which gives best separation.

**Timebox warning:** This phase is where scope creep commonly happens (trying one more model, re-tuning thresholds). Timebox strictly to 1 week. If calibration unsatisfactory by Friday, document limitation in báo cáo and move on to T9. The 5 UCs working end-to-end is higher-priority than AI perfection.

---

### Phase 6: AI Integration & Polish (T8, second half)
**Rationale:** Once AI service working, replace stub client in Web API with real httpx-based one. Add async/background-task wiring for document checks. Verify end-to-end flows.

**Delivers:**
- Web API's AI client (`services/ai_client.py`): real httpx calls (sync for `/check-title`, async BackgroundTasks for `/check-document`)
- Title check flow: synchronous call, response returned inline
- Document check flow: file stored, text extracted, `SimilarityCheckResult` status=PENDING, background task runs, client polls until DONE
- React UI for results: matched items side-by-side, score with calibrated warning level, matched passages highlighted
- Similarity result as advisory (warning shown, not hard block on submission)
- End-to-end test: student registers similar topic, sees warning; student uploads outline, gets result within reasonable time

**Avoids Pitfalls:** False positives from boilerplate (#3), response-time NFR (#6), scope creep (#12)

---

### Phase 7: Deployment, Seed Data, & UAT (T9)
**Rationale:** Final integration with production-like deployment. Seed data (100 SV, 30 GV, 300 topics, 50 documents with planted duplicates) seeded *after* AI service fully functional, so `/ingest` calls exercise real pipeline.

**Delivers:**
- Seed-data generation scripts: populate 100 SV, 30 GV, 300 đề tài (structured around realistic topical clusters), 50 DOCX/PDF documents (deliberately-constructed duplicate pairs: exact-copy, paraphrased, same-domain-different-topic, unrelated)
- `/ingest` call for each seeded item (proves pipeline works end-to-end)
- Apache HTTPS config finalized, reverse proxy tested with real uploads/large requests/slow AI calls
- Full UAT: all 5 UCs tested end-to-end for all 3 roles with seeded data
- Similarity check validation: verify seeded duplicate pairs flagged above threshold, unrelated pairs below, same-template-different-topic suppressed
- Performance measurement: response times for title/document checks, UI loading under full seeded load
- Documentation: system overview, deployment steps, API contract (OpenAPI spec), RBAC/authorization model

**Avoids Pitfalls:** Apache proxy issues (#10), seed-data unrealism (#11)

**Handoff to defense:** System ready for live demo, all 5 UCs work end-to-end, AI checks demonstrate realistic detection, seed data shows believable topical variety, documentation complete.

---

### Phase Ordering Rationale

1. **T4 (Architecture) before T6 (Database) before T7 (UCs):** Foundation must be solid. RBAC framework, text-normalization rules, embeddings-cache schema design all cascade into every UC.

2. **T5 (UI mockups + data collection) in parallel with T4, before T8 (AI):** UI drives API contract; historical data drives template extraction and seed-data design. Both inform what AI service's interfaces need to support.

3. **T7 (UCs implemented with AI stubbed) before T8 (real AI wiring):** Decouples core workflow development from AI service. If UC implementation runs into timeline trouble, AI service development is not blocked.

4. **T8 in two halves: AI service standalone (days 1–3), then integration (days 4–5).** Build AI service in isolation, test against small corpus, prove it works. Then wire into Web API.

5. **T9 (deployment + seed data) last.** Don't try to deploy while building. Apache proxy, seed data scripts, final UAT happen once app is feature-complete.

---

### Research Flags

**Phases needing deeper research during planning:**

- **T8 (AI Service):** Model accuracy on actual Vietnamese thesis data (most critical gap). Stack research recommends bkai + underthesea based on public benchmarks (legal/formal text), but those may not match student theses. Recommend small labeled validation set (20–30 topic/document pairs rated by expert) to compare bkai vs multilingual-e5 on actual capstone writing before committing.

- **T5 (Data Collection):** Realism of sourced historical documents. If the 20 historical files are not representative of actual student writing quality/length/vocabulary, AI calibration (threshold picking) will be misleading. Validate with faculty member or real students that samples are "typical."

**Phases with standard patterns (skip deep research):**

- **T4 (Architecture):** Database schema + API design is well-explored in STACK.md and ARCHITECTURE.md. SOA patterns are established. Implementation planning can proceed directly to coding.

- **T6 (Web API core):** FastAPI + SQLAlchemy + Alembic, React + TanStack Query, Apache `mod_proxy` are well-documented stack. Standard implementation, no deep research needed.

- **T7 (Core UCs):** Thesis-management workflows are standardized across platforms (OpenEduCat, Creatrix, academic papers). 5-UC structure is explicit in FEATURES.md. Implementation proceeds directly from specs to code.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|----------|-------|
| **Stack** | HIGH | Python FastAPI + React + MySQL is user-mandated and well-established. SQLAlchemy 2.0.54, Vite 7.3, FastAPI 0.141 are current, stable, widely-used versions. Charset/collation choice is well-researched (MySQL 8 official docs on Vietnamese collation). |
| **Features** | HIGH | Thesis/FYP management workflows are standardized across commercial systems and academic papers. The 5 UCs and 3-role RBAC are tightly constrained by PROJECT.md and match real-world practice. AI features (semantic topic matching, document duplicate detection) are well-established in Turnitin/Coopy research. |
| **Architecture** | HIGH | SOA with service-per-database, sync-for-fast/async-for-slow, precomputed embeddings + FAISS patterns are standard microservice architecture. Component separation is clearly specified. The pattern of precomputing embeddings and querying FAISS is well-established in plagiarism-detection literature. |
| **Pitfalls** | MEDIUM-HIGH | General software pitfalls (RBAC, file upload, Apache proxy) are HIGH confidence. Vietnamese-specific pitfalls (Unicode, segmentation, collation) are MEDIUM confidence (sourced from model cards, academic papers, community blogs). Academic plagiarism pitfalls (boilerplate, threshold calibration) are MEDIUM-HIGH confidence (peer-reviewed surveys). |

**Overall Confidence:** MEDIUM-HIGH

### Gaps to Address

1. **Exact Vietnamese embedding model accuracy on student thesis corpus.** Research relied on public benchmarks (legal-text retrieval for bkai, general multilingual for e5). Student thesis writing may differ significantly. **Mitigation:** T5 collect real samples; T8 conduct small validation test (20–30 samples) before committing to model.

2. **Boilerplate stripping rules completeness.** Research identifies shared templates cause false positives but is generic. The exact official template structure is known only to faculty. **Mitigation:** T5 extract official template DOCX; T8 implement rules. May require iteration during T9 UAT.

3. **Response-time NFR under full load.** Research recommends precomputation + FAISS, but actual latency depends on hardware and dataset size. **Mitigation:** T4 specify target NFR (e.g., <5s title, <30s document); T8 measure on intended hardware; T9 verify with full seeded load.

4. **Defense committee formation edge cases.** Research suggests simple "assign lecturers, no double-booking," but real workflows may have subtleties (what if two simultaneous sessions need same lecturer?). **Mitigation:** T5 mockups explore with faculty; T7 start simple, document limitations in báo cáo.

---

## Sources

**STACK.md (HIGH confidence):**
- PyPI pages for FastAPI, SQLAlchemy, Alembic, sentence-transformers, FAISS — verified current versions/dependencies
- [bkai-foundation-models/vietnamese-bi-encoder model card](https://huggingface.co/bkai-foundation-models/vietnamese-bi-encoder) — Vietnamese embedding model (MEDIUM: single source, model-author card, 1 public benchmark)
- [underthesea docs](https://pypi.org/project/underthesea/) — Vietnamese word segmentation (MEDIUM: library docs + community benchmark)
- Apache httpd official docs — reverse proxy configuration (HIGH: official)
- PyMuPDF, pdfplumber, python-docx official repos — file parsing (HIGH: official libraries)

**FEATURES.md (HIGH confidence):**
- [OpenEduCat Thesis Management](https://openeducat.org/) — reference system (MEDIUM: vendor marketing, cross-verified)
- [Design of University Graduation Project Management System (ResearchGate)](https://www.researchgate.net/publication/357307141_Design_of_University_Graduation_Project_Management_System_Based_on_Micro_Service_Architecture) — peer-reviewed (HIGH)
- [Coopy — HUST similarity checker](https://soict.hust.edu.vn/coopy.html) — Vietnamese closed-corpus plagiarism detector (HIGH: live system at major Vietnamese university)
- [Turnitin Similarity](https://www.turnitin.com/products/similarity/) — industry standard (HIGH)

**ARCHITECTURE.md (HIGH confidence):**
- SOA patterns, service-per-database, precomputed embeddings — standard microservice architecture (HIGH: established practice)
- [BERT-Enhanced Retrieval Tool for Homework Plagiarism Detection (arXiv 2404.01582)](https://arxiv.org/pdf/2404.01582) — document-level embedding + retrieval (HIGH: peer-reviewed)
- FAISS `IndexFlatIP` for sub-100k vectors — well-established (HIGH: documented)
- [Building Plagiarism Checker Using FAISS (Medium)](https://medium.com/naukri-engineering/building-plagiarism-checker-using-faiss-8c933c8afe1e) — FAISS pattern (MEDIUM: blog post, consistent with literature)

**PITFALLS.md (MEDIUM-HIGH confidence):**
- Unicode normalization (NFC/NFD) — well-researched (MEDIUM-HIGH: Python docs + community reports)
- PhoBERT segmentation — documented in model card + [PhoBERT paper (ACL Anthology)](https://aclanthology.org/2020.findings-emnlp.92.pdf) (HIGH: peer-reviewed)
- Plagiarism-detection false positives — [A Systematic Review of Multilingual Plagiarism Detection (peer-reviewed)](https://thesai.org/Downloads/Volume16No8/Paper_36-A_Systematic_Review_of_Multilingual_Plagiarism_Detection.pdf), [Improving Academic Plagiarism Detection (arXiv)](https://arxiv.org/pdf/1906.11761) (HIGH: peer-reviewed)
- PDF/DOCX extraction — official docs (HIGH)
- MySQL charset/collation — [MySQL 8 Unicode docs](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html), [MySQL WL#3865](https://dev.mysql.com/worklog/task/?id=3865) (HIGH: official)
- RBAC, file upload security, Apache proxy — standard web security (HIGH: extensively documented)

---

*Research synthesis completed: 2026-09-27*  
*Ready for roadmap planning: yes*
