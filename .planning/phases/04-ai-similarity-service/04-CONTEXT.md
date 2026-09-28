# Phase 4: AI Similarity Service - Context

**Gathered:** 2026-09-28 (auto mode — recommended defaults selected; user asked to speed up with parallel agents)
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the separate AI duplicate-check service (`ai-service/`, FastAPI) and swap it in for the stub behind the existing `backend/app/services/ai_client.py` seam; seed the 300-topic corpus and the 50-document calibration set with intentional duplicate pairs; calibrate thresholds; add the Bộ môn threshold-config UI; show real passage-level highlights on MH-14 / GVHD review screens. Requirements: AISV-01..07, DATA-02, DATA-03.

</domain>

<decisions>
## Implementation Decisions

### Carried forward (locked)
- Architecture §3.3: AI service = own FastAPI process, bound to 127.0.0.1:8002 / internal compose network only, **no Apache route**, `X-API-Key` internal key, own MySQL schema `thesis_ai` (tables per `docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.puml`), API contract §3.3.5 (`/ingest`, `/check-title`, `/check-document`, `/reindex`, `/health`), receives text only (never files). Web API keeps BackgroundTasks + polling for document checks (Phase 3). NFR: title check ≤5 s, document check ≤30 s P95 on seeded corpus.
- Stack per research STACK.md: sentence-transformers, FAISS (`faiss-cpu`, IndexFlatIP), underthesea word segmentation, datasketch MinHash for verbatim copy, NFC normalization everywhere.

### Model selection
- **D-01:** Open the phase with a timeboxed bake-off: `bkai-foundation-models/vietnamese-bi-encoder` (+ underthesea segmentation) vs `intfloat/multilingual-e5-base` (no segmentation) on a small labeled set of known similar/different Vietnamese thesis-title and paragraph pairs; pick by separation (AUC / gap between duplicate and non-duplicate scores) and latency; record the table for the report. [auto] → "bake-off then lock" (recommended per roadmap note)
- **D-02:** Run on **CPU** inside the container (the dev laptop has a 4 GB RTX 3050, but the target server is unknown); model weights cached in a docker volume, loaded once at startup; embeddings precomputed at ingest, never recomputed per request.

### Detection method
- **D-03:** Title check = cosine similarity (embedding) top-k with % score. Document check = chunk into paragraph/sentence-window chunks after stripping boilerplate (template headings, mục lục, tài liệu tham khảo, lời cam đoan/cảm ơn — patterns from the official template when available, otherwise a documented default list), then flag a chunk if embedding cosine ≥ content threshold **or** MinHash Jaccard ≥ verbatim threshold; report overall % = share of matched chunks (by characters), matched theses list, per-passage pairs with source text for highlighting.
- **D-04:** Thresholds live in `cau_hinh_nguong` (already exists, Web API side); Bộ môn edits title/content thresholds on a new settings screen; Web API passes the active threshold to the AI service per request (AI service stays stateless about policy). Defaults come from calibration.

### Data (DATA-02, DATA-03)
- **D-05:** 300 archive topics across several cohorts (khóa K18–K22) generated with realistic Vietnamese IT thesis titles in topic clusters (web, mobile, AI/ML, IoT, data, security, ERP…), inserted via the existing archive import path so they flow through `/ingest`.
- **D-06:** 50 DOCX/PDF test documents generated programmatically (python-docx + a PDF export) using the official template structure when available, with an explicit pair spectrum: exact copy, paraphrased, same field/different topic, unrelated; ~30% of pairs held out as a validation set not used for threshold tuning. A manifest (pair id, type, expected flag) + a results table (scores, flagged?, pass/fail) are saved under `docs/` for chương 4. No real student text is copied verbatim (privacy/copyright).

### Deployment
- **D-07:** Add `ai` service to `deploy/docker-compose.yml` on the internal network only; Web API gets `AI_SERVICE_URL`, `AI_API_KEY` env; `AI_STUB_MODE` kept as a fallback switch.

### Claude's Discretion
- Chunk size/overlap, top-k, exact boilerplate patterns, MinHash parameters, bake-off set size (small, timeboxed), UI details for MH-14 highlights and the threshold screen within Ant Design.

</decisions>

<canonical_refs>
## Canonical References

- `docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md` §3.3.1–3.3.8 (contract, sequences)
- `docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.puml`, `02-thiet-ke-csdl.md` (thesis_ai tables, cau_hinh_nguong, ket_qua_kiem_tra_trung_lap, chi_tiet_trung_lap)
- `docs/chuong-3-thiet-ke/mockup/mh-14.html` (duplicate detail), `mh-09.html` (GVHD review panel)
- `docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md` (NFR-07..NFR-10 thresholds)
- `.planning/research/STACK.md`, `PITFALLS.md` (NFC, segmentation, boilerplate false positives, CPU latency, calibration), `ARCHITECTURE.md`
- `backend/app/services/ai_client.py` (seam to replace), Phase 3 SUMMARYs once available
- `tai-lieu-goc/mau-chinh-thuc/` (official template, if the student has supplied it)

</canonical_refs>

<code_context>
## Existing Code Insights

- Web API seam `ai_client.py` (`check_title`, and after Phase 3 `check_document`, `ingest`), `title_check.py` persistence, BackgroundTasks document-check runner (Phase 3), archive CSV import (Phase 3) = ingest path for DATA-02.
- Compose stack `ntma` (mysql/api/apache); tests pytest against real MySQL; e2e scripts in `deploy/`.

</code_context>

<specifics>
## Specific Ideas

- `ai-service/` can be developed and unit-tested standalone (own pyproject via uv, own tests with a tiny fixture corpus) before wiring into compose.
- Save the bake-off and calibration tables as Markdown under `docs/chuong-4-trien-khai/` for the report.

</specifics>

<deferred>
## Deferred Ideas

- Delete-from-index endpoint for removed archive records (not in §3.3.5 contract) — note as limitation unless trivial.
- GPU inference, web-scale plagiarism search — out of scope.

</deferred>

---

*Phase: 04-ai-similarity-service*
*Context gathered: 2026-09-28 (auto)*
