# Pitfalls Research

**Domain:** Vietnamese university thesis/capstone management system with local-embedding AI similarity detection (FastAPI + React + MySQL, Apache reverse proxy), solo student, 10-week graduation-defense build
**Researched:** 2026-09-27
**Confidence:** MEDIUM-HIGH (general web/software pitfalls are HIGH confidence, well-documented; Vietnamese-NLP-specific and academic-plagiarism-specific pitfalls are MEDIUM — synthesized from research papers/library docs, not project post-mortems for this exact stack)

## Critical Pitfalls

### Pitfall 1: Comparing text without normalizing Unicode form (NFC vs NFD) silently breaks matching

**What goes wrong:**
Vietnamese text can be encoded as precomposed characters (NFC — "á" as one codepoint) or decomposed (NFD — "a" + combining acute accent, common when text comes from macOS, some DOCX exports, or copy-paste from PDF). Two strings that render identically can be byte-different. If embeddings, exact-string checks, or database `WHERE name = ?` lookups compare raw strings, two visually identical Vietnamese đề tài titles are silently treated as different — duplicate detection misses real duplicates, and MySQL uniqueness/lookup queries fail intermittently depending on upload source (Word vs pasted text vs PDF-extracted text).

**Why it happens:**
Vietnamese has the most combining-diacritic density of any widely-used Latin-script language (up to 2 diacritics per vowel: tone + modifier). Developers who only test with text they typed themselves in one input method never see the NFC/NFD mismatch; it only appears once real DOCX/PDF files from different Word versions or different students' machines are ingested.

**How to avoid:**
Apply `unicodedata.normalize("NFC", text)` immediately at every text ingestion boundary (file upload, form input, embedding-service request) before storing, comparing, or embedding. Pick NFC as the single canonical form project-wide and normalize at the earliest possible point (API boundary), not scattered throughout the codebase.

**Warning signs:**
Duplicate titles that "look the same" in the UI but the system reports 0% similarity; MySQL exact-match queries occasionally returning no rows for text that visibly matches; seed data comparisons behave differently depending on whether titles were typed directly vs copy-pasted from a DOCX.

**Phase to address:**
Architecture/data-model phase (T4) — decide and document the normalization policy; enforce it in the shared text-ingestion utility used by both the Web API and the AI service before UC implementation (T6–T8).

---

### Pitfall 2: Feeding raw (un-segmented) Vietnamese text into a PhoBERT-based embedding model

**What goes wrong:**
PhoBERT and most Vietnamese SBERT models (`vietnamese-sbert`, `vietnamese-embedding`) were pretrained on **word-segmented** input (syllables joined by `_`, e.g. `sinh_viên` not `sinh viên`). Feeding raw un-segmented text still "works" (no error) but produces degraded, sometimes badly miscalibrated similarity scores, because the model never learned to treat un-joined multi-syllable words as single tokens. This is an invisible quality bug — nothing crashes, the demo just quietly gives worse discrimination between similar/dissimilar topics.

**Why it happens:**
The embedding model's inference API accepts any string; there is no built-in validation forcing correct preprocessing. Documentation on model cards mentions segmentation as a preprocessing step but it's easy to skip when prototyping with quick wins ("it already gives some number").

**How to avoid:**
Confirm which embedding model is chosen and check whether it requires pretokenization (models like `dangvantuan/vietnamese-embedding` built on SimCSE/SBERT with PhoBERT backbone typically do; some newer multilingual/document-embedding models handle raw text natively — verify per model card). If segmentation is required, run `underthesea` word segmentation (best benchmarked accuracy among Vietnamese segmenters) as a preprocessing step before both embedding generation and index building, applied consistently at query time and corpus time.

**Warning signs:**
Semantically identical or near-identical đề cương pairs score unexpectedly low similarity; clearly unrelated topics score unexpectedly high; similarity scores cluster tightly (little discrimination) regardless of input.

**Phase to address:**
AI service implementation phase (T8) — write a small calibration test set (5-10 known-similar and known-dissimilar title/paragraph pairs) before wiring up the UI, and verify segmentation is applied identically in the ingestion path and the comparison path.

---

### Pitfall 3: False positives from shared outline templates, boilerplate, and reference lists

**What goes wrong:**
Every đề cương/báo cáo at this khoa follows the same official template (mandatory section headers like "Lý do chọn đề tài", "Mục tiêu nghiên cứu", "Kết luận", university/Đảng-ủy boilerplate on the cover page, thesis-format instructions, common citation entries e.g. textbooks or the same 2-3 referenced ICTU papers). If whole-document or whole-paragraph embeddings are compared without stripping this shared structure, nearly *every* pair of documents will show suspiciously high similarity purely from identical section headers, formatting text, and common references — masking real plagiarism (real duplicates don't stand out from the noise floor) and destroying trust in the tool during the defense demo when a committee member notices two unrelated topics flagged as "85% similar."

**Why it happens:**
Naive "compare whole document" or "compare whole paragraph" approaches don't distinguish structural/template text from actual content. This is the single most-cited failure mode in academic plagiarism-detection research: text overlap ≠ plagiarism, especially for template-heavy institutional documents.

**How to avoid:**
1. Strip known boilerplate before comparison: standard section headings, cover-page/administrative text, table-of-contents, and reference-list entries (detect via heading pattern matching against the official template, or by filtering short lines matching a known boilerplate phrase list built from the official template DOCX).
2. Compare at the paragraph/chunk level (not whole document) so unique substantive chunks can be identified even when surrounded by shared structure — this also enables "which đoạn trùng" reporting required by PI 3.4.
3. Exclude the reference/citation section entirely from similarity scoring (or score it separately with a much higher threshold), since shared citations across theses in the same field are expected and not plagiarism.
4. Weight or filter out chunks below a minimum content length (a lone heading like "1.2 Mục tiêu" should never itself trigger a duplicate flag).

**Warning signs:**
Two topics from entirely unrelated fields (e.g., "website bán hàng" vs "hệ thống IoT") score high similarity; similarity score barely changes between clearly-different vs clearly-duplicate seed pairs; every document in the seed corpus shows non-trivial similarity to every other document.

**Phase to address:**
AI service design (T8), but the boilerplate/template list must be extracted during data collection (T5, "thu thập kho" của đồ án cũ) — collect the official template DOCX early so the stripping rules can be built and tested before the AI phase, not discovered late.

---

### Pitfall 4: DOCX/PDF extraction noise contaminates embeddings (headers, footers, page numbers, TOC, tables)

**What goes wrong:**
Naive full-text extraction (e.g., dumping every paragraph in a `python-docx` document, or every line from `pdfplumber`/PyMuPDF) pulls in running headers/footers (repeated on every page — e.g., "Đồ án tốt nghiệp — Khoa CNTT"), page numbers, watermark/draft text, and auto-generated table-of-contents entries (which duplicate every section heading verbatim). These repeated fragments (a) inflate apparent similarity between unrelated documents (same header on every page = guaranteed "duplicate" line-level match), and (b) for PDFs, table content is frequently extracted as garbled/reordered text if a naive `page.extract_text()` call is used without layout-aware extraction, further corrupting embeddings.

**Why it happens:**
`python-docx` exposes headers/footers via a separate API (`section.header`, `section.footer`) that is easy to forget when just iterating `document.paragraphs`; if headers are stored as content (some conversion tools flatten them into body text) they get swept in unintentionally. For PDF, simple text extraction concatenates content in stream order which does not always match visual reading order, especially with multi-column layouts or embedded tables — pdfplumber/PyMuPDF need explicit table-detection and layout logic, not just `.extract_text()`.

**How to avoid:**
- For DOCX: iterate only `document.paragraphs` (body) and explicitly skip/exclude header/footer sections; strip TOC field-code paragraphs (these are usually a distinguishable style, e.g. "TOC 1"/"TOC 2").
- For PDF: use a layout-aware extraction path (pdfplumber's `extract_text(layout=True)` or PyMuPDF `get_text("blocks")`) and cross-check table regions separately; do not naively concatenate raw text if the source documents contain tables (common in a "Kế hoạch thực hiện" or a comparison table section).
- Deduplicate repeated line-level headers/footers across pages before chunking (any line that repeats identically on >50% of pages is boilerplate, not content).
- Build one shared extraction module used identically for the seed corpus and for newly uploaded files, so scores are consistent.

**Warning signs:**
Every extracted document starts/ends with the same few lines regardless of topic; extracted paragraph counts are much larger than the visible page count would suggest; table cells appear as run-on garbled text; TOC headings appear twice in the extracted content (once from TOC, once from the actual section).

**Phase to address:**
Data collection + AI service phases (T5, T8) — build and unit-test the extraction module against a handful of real historical đồ án files (with headers/footers/tables/TOC) before writing similarity logic on top of it.

---

### Pitfall 5: Similarity threshold picked arbitrarily, with no calibration against labeled data

**What goes wrong:**
Without ground truth, it's tempting to pick a "looks reasonable" cutoff (e.g., ">80% = duplicate warning") based on gut feel. This threshold is almost never correct for the actual embedding model + document type combination, and worse, embedding cosine-similarity distributions for unrelated academic Vietnamese text tend to sit in a deceptively "high-looking" range (0.5–0.7 is common for topically-related-but-different text due to shared domain vocabulary), so an intuitively-chosen threshold like 0.8 may never fire, or a threshold like 0.5 may flag almost everything.

**Why it happens:**
There is no publicly available Vietnamese thesis-plagiarism-threshold benchmark to copy from; every embedding model has a different similarity scale/distribution. Developers under time pressure skip calibration and hardcode a number.

**How to avoid:**
Use the intentionally-seeded duplicate pairs (PI 4.2 requirement — "50 file... có các cặp trùng lặp chủ đích") as the calibration set from the start, not just as a final demo prop: compute similarity scores for all known-duplicate pairs and all known-non-duplicate pairs, and pick threshold(s) that separate the two groups with margin. Prefer a two-tier output (e.g., "cảnh báo cao" / "cảnh báo thấp" bands) over a single binary cutoff — this is both more honest about model uncertainty and better UX (the committee sees graduated confidence, not a brittle single number). Document the calibration method and resulting thresholds in the báo cáo (this is examinable content for CLO/PI, not just an implementation detail).

**Warning signs:**
Threshold was set once during early development and never revisited after real seed data existed; no written record of why the threshold value was chosen; demo relies on cherry-picked pairs rather than the full seeded set to "prove" detection works.

**Phase to address:**
AI phase (T8) and seed/test phase (T9) — calibration must happen with the actual seed corpus, meaning seed data generation and AI threshold tuning are coupled and should not be scheduled as fully sequential/independent tasks.

---

### Pitfall 6: CPU-only embedding generation blows the response-time NFR during live comparison

**What goes wrong:**
Sentence-transformer/PhoBERT-based models on CPU (no GPU, typical for a student's laptop or a modest deployment box) take non-trivial time per call — fine for a single title comparison, but if the "check duplicate" flow is naively implemented as "embed the new submission, then loop over all 300 đề tài / 50 documents re-embedding each comparison target synchronously inside the HTTP request," response time balloons well past a usable NFR (PI 1.2 explicitly calls out response-time as a requirement to be evaluated), and worse, will look bad live in front of the defense committee if the request appears to hang.

**Why it happens:**
It's the simplest thing to implement first ("embed both texts, compute cosine similarity, return"), and it works fine in dev with a handful of test rows — the problem only appears once the seed corpus (300 topics + 50 documents) is loaded and a real request has to compare against the whole existing corpus.

**How to avoid:**
Precompute and persist embeddings for all existing corpus items (topics and document chunks) at ingestion/seed time — never re-embed the existing corpus on every check. At comparison time, only the new submission needs to be embedded (one model call), then compared against the precomputed vectors via fast cosine-similarity (numpy dot product or a lightweight vector index) — this changes the operation from "N embeddings" to "1 embedding + N comparisons," which is orders of magnitude faster. Also batch multi-chunk document embedding (encode all chunks of one document in a single `model.encode(list_of_chunks)` call rather than one-by-one) since sentence-transformers batching gives real throughput gains. Set a realistic response-time NFR (e.g., "<5s for title check, <30s for full document comparison") reflecting CPU inference costs, not a copy-pasted generic NFR.

**Warning signs:**
Demo request takes >10-15 seconds with the full 300-topic/50-document seed corpus loaded; CPU usage spikes to 100% during every duplicate check even for a small title; no caching/precomputed-embeddings table exists in the schema.

**Phase to address:**
Architecture design (T4, plan an embeddings-cache table/column from the start) and AI phase (T8, implement precompute-on-ingest + compare-only-new-item pattern); verify against NFR during T9 testing with full seed data loaded.

---

### Pitfall 7: MySQL charset/collation set to `utf8` (3-byte) or a non-Vietnamese-aware collation, silently corrupting or mis-sorting text

**What goes wrong:**
MySQL's legacy `utf8` charset is actually limited to 3-byte UTF-8 sequences and can silently corrupt certain Unicode characters if they fall outside the BMP (less common for Vietnamese base text, but common if any emoji/rich text sneaks into notes/comments fields); more importantly, choosing `utf8mb4_general_ci` (or leaving the server default) rather than a Vietnamese-aware collation like `utf8mb4_vietnamese_ci` (or `utf8mb4_0900_ai_ci` on MySQL 8) makes name/title sorting and case/accent-insensitive comparisons behave in surprising ways for Vietnamese diacritics (e.g., alphabetical ordering of sinh viên names not matching Vietnamese dictionary order, or ORDER BY producing an order a Vietnamese-speaking committee member immediately notices as "wrong").

**Why it happens:**
Table/column charset frequently defaults to whatever the MySQL server's global default is, not what the developer explicitly set, especially when tables are created ad hoc via an ORM without an explicit charset directive; migrations copy-pasted from tutorials often use `utf8` without the `mb4` suffix out of habit.

**How to avoid:**
Explicitly set `CHARACTER SET utf8mb4 COLLATE utf8mb4_vietnamese_ci` (or `utf8mb4_0900_ai_ci` for MySQL 8.0+ if broader accent-insensitive matching across scripts is preferred) at the database level, and confirm the ORM/migration tool inherits it per-table — don't rely on server defaults. Test with actual Vietnamese names containing the full diacritic range early (T6, when the schema/CSDL is first built), not just at final integration.

**Warning signs:**
Sorting sinh viên/giảng viên lists by name produces an order that doesn't match Vietnamese dictionary order; `LIKE` searches with Vietnamese input behave inconsistently for accented vs unaccented queries; any column shows `?` or mangled bytes for names with rarer diacritic combinations (ơ, ư, ê with tone marks stacked).

**Phase to address:**
Database design phase (T6, PI 3.1) — set charset/collation in the initial schema migration, verified against seed data (T9) containing realistic Vietnamese names.

---

### Pitfall 8: File upload accepted without type/size/content validation, opening security and stability holes

**What goes wrong:**
Accepting DOCX/PDF uploads based only on file extension or client-declared MIME type lets an attacker (or an accidental corrupt file) upload a renamed executable, an oversized file that exhausts disk/memory, or a "zip bomb"-style DOCX (DOCX is itself a ZIP container — a maliciously crafted DOCX with deeply nested/highly-compressed XML can cause `python-docx`/`zipfile` to consume excessive memory when parsed). Combined with no path sanitization on stored filenames, this also opens path-traversal risks (`../../etc/passwd`-style filenames) when writing to the server's upload directory.

**Why it happens:**
Under a tight 10-week solo timeline, upload validation is often deferred as "not core functionality" since the demo only needs to work with well-behaved seed files — but the requirement (PI 3.4 + PI 4.1 phân quyền/bảo mật) explicitly includes this system being demo-security-reviewed.

**How to avoid:**
Validate actual file content (magic bytes / MIME sniffing, not just extension) server-side; enforce a strict file-size limit both at the Apache layer (`LimitRequestBody`) and the FastAPI layer (reject oversized `Content-Length` early, and stream-parse rather than loading fully into memory at both layers); generate a new server-side filename (UUID) rather than trusting the client-provided name for storage; restrict extraction libraries to read-only parsing without following embedded macros/external references (DOCX can embed remote resource references — disable resolving them if the parsing library supports it).

**Warning signs:**
Upload endpoint accepts any file where the filename ends in `.docx`/`.pdf` without checking actual content; uploaded files are stored using the original client filename directly; no explicit max-size check exists in either Apache config or FastAPI route.

**Phase to address:**
UC implementation phase (T7, đề cương/báo cáo submission UC) with the size/type checks specified as explicit acceptance criteria; reinforced at deployment (T9) via Apache-level limits.

---

### Pitfall 9: RBAC enforced only in the frontend, or role checks scattered ad hoc per endpoint

**What goes wrong:**
With three roles (Sinh viên, Giảng viên, Bộ môn/Khoa) and cross-cutting resources (đề tài, đề cương, báo cáo, hội đồng), it's easy to hide UI elements per role in React while leaving the corresponding FastAPI endpoints unprotected or under-protected — meaning a sinh viên account that discovers/guesses another student's đề tài ID could view or even edit records that should be GVHD/Bộ môn-only (IDOR — insecure direct object reference). It's also common to implement role checks as duplicated `if role == "..."` conditionals sprinkled across route handlers, where one omitted check later becomes an exploitable gap and is very hard to audit holistically for a defense committee to trust.

**Why it happens:**
Frontend-first development naturally starts by hiding buttons/menus for the "wrong" role because that's visible progress; backend authorization is comparatively invisible and easy to postpone, especially solo under deadline pressure. Ad hoc per-endpoint checks feel faster than building a shared authorization layer.

**How to avoid:**
Implement a single reusable FastAPI dependency (e.g., `require_role(*roles)` / ownership-check dependency) applied to every protected route from the start, not retrofitted; additionally verify object-level ownership (a Giảng viên can only see/edit đề cương for topics they are assigned GVHD for, not all đề cương in the system) — role alone is not sufficient, resource ownership must also be checked. Write this as an explicit UC acceptance criterion ("SV A cannot view/download SV B's báo cáo") and test it directly (not just via UI walkthrough) before considering UC 3.3 done.

**Warning signs:**
Authorization logic exists only as conditional rendering in React components; no automated test attempts an unauthorized request against a protected endpoint; endpoints return 200 with data for a resource the caller shouldn't be able to see, relying on the frontend to just "not show the link."

**Phase to address:**
UC implementation phase (T7) — build the authorization dependency during the *first* UC (Quản lý đề tài) so every subsequent UC reuses it, rather than reinventing checks per UC.

---

### Pitfall 10: Apache reverse-proxy configuration silently breaks uploads, long AI requests, or HTTPS correctness

**What goes wrong:**
Several independent Apache+FastAPI/uvicorn integration issues commonly surface only at deployment time (T9), too late to fix comfortably before the defense: (a) Apache's default request body size limit (`LimitRequestBody`, default effectively ~1GB but sometimes constrained by distro defaults or `mod_security` if present) or a missing/too-small `ProxyReceiveBufferSize` truncates or rejects large DOCX/PDF uploads; (b) the AI-service similarity check on a full document can take longer than Apache's default `ProxyTimeout`, causing Apache to return a 502/504 to the user mid-computation even though the backend was still working; (c) FastAPI's auto-generated URLs/redirects and Swagger docs break under a subpath proxy (`/api/...`) unless `root_path` (or `X-Forwarded-Prefix` + trusted-proxy config) is explicitly set, causing broken links/redirects that look fine when testing directly against uvicorn but fail through Apache; (d) if any endpoint needs WebSocket/SSE (e.g., live status updates on AI checking progress), Apache requires the `upgrade=websocket` proxy flag and `mod_proxy_wstunnel`, which is easy to forget since REST endpoints work fine without it.

**Why it happens:**
Development happens against `uvicorn` directly (`localhost:8000`) for weeks, and Apache is only introduced at the very end (per the T9 schedule) as a "just add the proxy" step — by which point upload sizes, AI processing time, and any subpath-dependent behavior are already baked in and assumed to work, when they haven't been tested through the actual proxy at all.

**How to avoid:**
Stand up the Apache reverse proxy early (even a bare-bones version, alongside T6 CSDL+API work) and develop/test against it continuously rather than only at T9, so these mismatches surface with time to fix. Explicitly configure: `ProxyTimeout` generous enough for the slowest AI comparison call (measured, not guessed); `LimitRequestBody` sized above the largest allowed upload plus margin; `root_path`/`X-Forwarded-*` handling in FastAPI (`proxy_headers=True` in uvicorn, or an `ASGIMiddleware` for forwarded headers) matched to the actual Apache `ProxyPass` path structure; HTTPS termination at Apache with correct forwarding of `X-Forwarded-Proto` so FastAPI doesn't generate `http://` links behind an HTTPS front door.

**Warning signs:**
"Works when I hit uvicorn directly on port 8000 but breaks through the domain/HTTPS URL"; uploads that work locally fail once proxied; Swagger UI (`/docs`) shows broken "Try it out" requests when accessed through the proxy; long-running AI check requests intermittently return a gateway error under proxy but succeed when timed directly against uvicorn.

**Phase to address:**
Deployment planning should start in T6 (spin up Apache early, even minimally) rather than being deferred entirely to T9 — T9 should be *verification* of a proxy setup that's already been running throughout development, not first-time setup under deadline pressure.

---

### Pitfall 11: Seed data that doesn't actually stress-test the AI feature (duplicate pairs too obvious, or corpus too small/uniform)

**What goes wrong:**
The seed data requirement (100 SV, 30 GV, 300 đề tài, 50 documents with intentional duplicate pairs — PI 4.2) exists specifically to demonstrate and validate the AI similarity feature to the defense committee. If the "duplicate pairs" are generated by trivial exact copy-paste (identical text, maybe with the student's name swapped), they'll trivially match on *any* method, including naive string comparison — proving nothing about the semantic-similarity capability that's the actual selling point (PI 3.4 requires semantic comparison, not exact match). Conversely, if all 300 đề tài titles are near-randomly generated with no realistic topical clustering (multiple students genuinely proposing similar topics across khóa, which is the real-world case this feature targets), the demo won't show believable "near-duplicate but not identical" detection — the single most important scenario to demonstrate live.

**Why it happens:**
Generating "realistic-looking" seed data is often treated as a low-effort filler task scheduled at the very end (T9, alongside deployment) rather than a designed artifact that needs to specifically probe the AI system's behavior at multiple similarity levels (identical, paraphrased/near-duplicate, same-domain-different-topic, unrelated).

**How to avoid:**
Design the 50-document seed set deliberately across a spectrum: a few exact-duplicate pairs (sanity check), several paraphrased/reworded-but-semantically-identical pairs (the real target case — same idea, different wording/structure), several same-domain-different-topic pairs (should NOT trigger high similarity — the false-positive check from Pitfall 3), and several completely unrelated pairs (baseline). Do the same for the 300 đề tài titles — cluster a meaningful subset around a handful of common topic themes (e.g., "website bán hàng", "hệ thống quản lý ...", "chatbot hỗ trợ...") since that's realistically what happens across cohorts, rather than 300 fully distinct one-off titles. Treat seed-data design as a T4/T5 task informed by the AI approach, not a T9 afterthought.

**Warning signs:**
All "duplicate" seed pairs are byte-identical or near-identical text; seed đề tài titles show no natural topical overlap at all; the demo script only ever shows the exact-duplicate case, never the "similar-but-reworded" case that's the actual value proposition.

**Phase to address:**
Data collection phase (T5) for sourcing real historical đồ án text to base realistic pairs on, finalized as part of seed script during T9 — but the *design* of what pairs to construct should be decided alongside the AI feature design in T8, not independently.

---

### Pitfall 12: Scope creep on the AI feature at the expense of the core 5-UC workflow within a fixed 10-week solo timeline

**What goes wrong:**
Semantic similarity/plagiarism detection is the most "interesting" and demo-impressive part of the project, which creates strong temptation to over-invest time tuning embeddings, trying multiple models, building a fancy similarity-visualization UI, etc., at the expense of the core end-to-end workflow (5 UC: đề tài → đề cương → tiến độ → bảo vệ → kho lưu trữ) that is explicitly the primary grading criterion ("Quy trình đồ án 5 UC chính chạy trọn vẹn end-to-end" is stated as Core Value, before the AI feature). Given one student and 10 fixed weeks, any week spent gold-plating AI accuracy is a week not spent making sure all 5 UC function correctly end-to-end for every role.

**Why it happens:**
AI/ML work has an open-ended "just try one more model/threshold/technique" quality that doesn't have a natural stopping point, unlike CRUD UC work which has a clear "done when the acceptance criteria pass" boundary — solo developers under pressure often gravitate to the open-ended, more novel task and let the closed-ended-but-tedious task slip.

**How to avoid:**
Timebox the AI feature explicitly (the schedule already does this — T8 only) and treat "good enough, calibrated against the seed set" as done, rather than iterating indefinitely on model choice. Protect T6-T7 (CSDL+API, 5 UC) as non-negotiable — if T8 AI work threatens to slip earlier, that's the signal to freeze AI scope at whatever quality it has and finish UCs, not the reverse. Explicitly define an AI feature MVP bar upfront (e.g., "detects at least the seeded near-duplicate pairs above threshold, and does not flag the seeded unrelated pairs") so "done" is objective rather than a moving target of perceived accuracy.

**Warning signs:**
More time in the weekly schedule is going into re-running/re-tuning the AI comparison than into UC acceptance testing; any of the 5 UC is still "mostly working" close to T9; the AI feature has had more than one full model swap without a corresponding calibration re-test against the seed set.

**Phase to address:**
Applies across T7 vs T8 boundary — the roadmap should sequence and protect T7 (5 UC) completion before/independent of T8 AI polishing, and treat T8 as strictly timeboxed.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|-----------------|
| Compare whole documents instead of paragraph-level chunks | Simpler to implement, faster to get "a number" | Can't report "đoạn trùng" (which paragraph matched) as required by PI 3.4; false positives from boilerplate dominate | Never for the final demo — acceptable only as a throwaway first spike to sanity-check the embedding model |
| Hardcode a single global similarity threshold with no calibration record | Fast to ship the AI feature | Threshold likely wrong for the real corpus; can't defend the number to the committee | Only during early development before seed data with known-duplicate pairs exists |
| Skip Vietnamese word segmentation preprocessing | One less dependency (`underthesea`), faster setup | Degraded similarity quality that's invisible until compared against a calibrated baseline | Only if the chosen embedding model's card confirms it works on raw (non-segmented) text |
| Store uploaded files with client-provided filenames | Simpler code | Path traversal risk, filename collisions across students, no CDN-safe naming | Never |
| Re-embed the whole corpus on every duplicate check instead of precomputing | Simplest possible implementation | Breaks response-time NFR once corpus reaches seed-data scale (300 topics / 50 docs) | Only for a first proof-of-concept with <10 corpus items |
| Enforce roles only in the React UI | Faster to demo role-based views | Real authorization bypass (IDOR); fails any security review | Never |
| Test only against `uvicorn` directly, add Apache proxy at the very end | Faster local iteration during weeks 6-8 | Upload size/timeout/subpath bugs surface for the first time under deadline pressure at T9 | Only for the first 1-2 weeks of backend work; must switch to proxy-fronted testing well before T9 |

## Integration Gotchas

Common mistakes when connecting to external services/components.

| Integration | Common Mistake | Correct Approach |
|-------------|-----------------|-------------------|
| MySQL | Leaving charset/collation at server default (`utf8`/`utf8mb4_general_ci`) | Explicitly set `utf8mb4` + `utf8mb4_vietnamese_ci` (or `utf8mb4_0900_ai_ci` on MySQL 8) at DB/table creation |
| Vietnamese embedding model | Feeding raw un-segmented text to a PhoBERT-backbone model | Run `underthesea` word segmentation consistently before every embed call, corpus and query side |
| DOCX parsing (`python-docx`) | Iterating only `document.paragraphs`, missing headers/footers stored separately, or accidentally including them | Explicitly exclude header/footer sections; strip TOC-field paragraphs by style name |
| PDF parsing (`pdfplumber`/PyMuPDF) | Naive `extract_text()` on documents containing tables/multi-column layout | Use layout-aware extraction, handle table regions separately, verify against real sample files |
| Apache ↔ FastAPI (subpath proxy) | Not setting `root_path`/`X-Forwarded-Prefix`, breaking docs/redirects under `/api` prefix | Configure `uvicorn --proxy-headers` + matching `ProxyPass`/`ProxyPassReverse`, test through the actual proxy URL, not just `localhost:8000` |
| Apache ↔ long AI requests | Default `ProxyTimeout` too short for full-document similarity checks | Set `ProxyTimeout` based on measured worst-case AI response time + margin |
| File uploads ↔ Apache | Relying on FastAPI's size check alone, ignoring Apache's own `LimitRequestBody` | Set consistent max-size limits at both layers |

## Performance Traps

Patterns that work at small scale but fail as the seed corpus grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|-----------------|
| Re-embedding the entire existing corpus on every new comparison request | Duplicate-check request time grows linearly with corpus size | Precompute + persist embeddings at ingestion time; only embed the new item at request time | Becomes noticeable once corpus > ~50-100 items; will be very visible at the full 300-topic/50-doc seed scale |
| One-by-one `model.encode()` calls per chunk instead of batched encoding | Slow bulk seeding/ingestion of the 50 test documents | Batch chunks into a single `model.encode(list)` call | Any bulk import of more than a handful of documents |
| Synchronous AI comparison blocking the request/response cycle in the Web API | UI appears frozen during document similarity checks; Apache proxy may time out | Consider async processing / background task with a "processing" status polled or pushed to the client for full-document checks | Once document-level (not just title-level) comparison is in scope, given CPU-only inference |
| No index/cache on embeddings storage (e.g., storing vectors as unindexed BLOB/JSON and scanning all rows in Python) | Comparison step slows as corpus grows even after precomputing embeddings | At minimum load all corpus vectors into memory as a numpy matrix once per process (300-500 vectors is trivially small) rather than reloading from DB per comparison | Not a real risk at this project's scale (300-500 vectors) if done as a numpy matrix; would matter far beyond this project's scope |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Trusting file extension/MIME type from the client for uploads | Malicious or corrupt file causes parser crash/resource exhaustion, or disguised executable stored and later served | Server-side content sniffing/validation; parse with exception handling; never execute/serve uploaded files as scripts |
| No path sanitization on stored upload filenames | Path traversal, filename collision overwriting another student's file | Generate server-side UUID filenames; never use raw client filename for storage path |
| RBAC checked only via frontend conditional rendering | IDOR — any authenticated user can access/modify data belonging to another role/user by calling the API directly | Enforce role + resource-ownership checks in a shared FastAPI dependency on every route |
| No rate/size limiting on the AI comparison endpoint | A large or repeated upload can exhaust CPU/memory on the AI service, degrading demo responsiveness for everyone | Apply file size caps and simple per-user request throttling on the AI service |
| Storing DOCX/PDF uploads inside the web-servable static directory | Uploaded (potentially malicious) files become directly downloadable/executable via Apache without going through access control | Store uploads outside the public web root; serve only via an authenticated FastAPI endpoint that streams the file after RBAC check |
| Apache configured with HTTPS but FastAPI unaware of `X-Forwarded-Proto` | Mixed-content warnings, insecure cookie flags, broken redirects appearing "secure" but leaking data over HTTP internally | Configure trusted-proxy headers so FastAPI knows the original scheme was HTTPS and sets `Secure` cookies accordingly |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-------------------|
| Reporting only a bare similarity percentage with no explanation | Giảng viên/Bộ môn don't know whether 62% is alarming or normal, undermining trust in the tool during defense Q&A | Pair the percentage with the matched đoạn/topic side-by-side and a graduated label ("cao / trung bình / thấp") based on the calibrated thresholds from Pitfall 5 |
| Flagging every submission with some non-zero similarity noise | GVHD becomes desensitized to warnings ("cried wolf"), ignoring a real duplicate later | Only surface warnings above the calibrated meaningful threshold; suppress near-zero background noise entirely from the UI |
| No indication of AI processing status on slower full-document checks | User assumes the app is frozen/broken during a multi-second CPU embedding call | Show an explicit "đang kiểm tra trùng lặp..." loading state, ideally polling/async as noted in Performance Traps |
| Blocking topic/đề cương submission entirely on a similarity warning | Prevents legitimate edge cases (student genuinely extending a prior topic with adviser approval) from being submitted at all | Treat AI similarity as an advisory warning shown to Bộ môn/GVHD for judgment, not a hard block on submission |

## "Looks Done But Isn't" Checklist

- [ ] **Duplicate/similarity check:** Often "works" only on the exact-copy seed pair — verify it also correctly flags the paraphrased near-duplicate pairs and does NOT flag same-template-different-topic pairs
- [ ] **File upload:** Often accepts any file extension without content validation — verify with a renamed non-DOCX/PDF file and an oversized file
- [ ] **RBAC:** Often only hides UI elements — verify by calling protected API endpoints directly (e.g., via curl/Postman) as the wrong role/user
- [ ] **Vietnamese text display/search:** Often tested only with the developer's own typed text — verify with real DOCX-sourced Vietnamese text (NFC/NFD mismatch, full diacritic range) and check MySQL sort order
- [ ] **Response-time NFR:** Often measured only against a near-empty dev database — verify with the full seeded corpus (300 topics / 50 documents) loaded
- [ ] **Apache deployment:** Often only tested by loading the homepage — verify file upload, the slowest AI comparison request, and (if used) WebSocket/SSE through the actual proxy URL, not directly against uvicorn
- [ ] **Seed data:** Often generated as a low-effort filler task — verify duplicate pairs actually exercise semantic (not just exact-string) matching, and that title clustering resembles realistic cross-cohort topic overlap

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|----------------|-----------------|
| NFC/NFD mismatch discovered late | LOW | Add a normalization pass in the shared text-ingestion utility and re-run it as a one-time migration over already-stored data |
| Un-segmented text fed to embedding model | MEDIUM | Add segmentation step, then re-generate (batch) embeddings for the existing corpus — feasible given corpus is only ~300-500 items |
| Boilerplate-driven false positives discovered late (e.g., during rehearsal) | MEDIUM | Retrofit a boilerplate-stripping filter using the official template as reference; re-run similarity scoring only (embeddings can be reused if segmentation/normalization already correct) |
| Response-time NFR failing under full seed load | MEDIUM | Add embedding precompute-on-ingest for existing items; this is a targeted fix, not a rearchitecture, if the schema already has a place to store vectors |
| RBAC/IDOR gap found late | HIGH | Requires auditing every route for missing checks — recommend budgeting a dedicated review pass before final demo rather than trusting ad hoc discovery |
| Apache proxy misconfiguration found at deployment (T9) | MEDIUM-HIGH | Costly mainly because of *time* pressure (T9 is close to the defense) rather than technical difficulty — mitigated entirely by not deferring proxy testing to T9 in the first place |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls (phase labels follow the đề cương's T1-T10 schedule referenced in PROJECT.md).

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|----------------|
| NFC/NFD normalization | T4 (kiến trúc/data model) | Unit test: two byte-different-but-visually-identical Vietnamese strings normalize to the same stored value |
| Word segmentation before embedding | T8 (AI service) | Calibration test set of known-similar/dissimilar pairs scores as expected after segmentation is applied |
| Boilerplate/template false positives | T5 (thu thập kho, extract template) → T8 (AI logic) | Seeded same-template-different-topic pairs score below the warning threshold |
| DOCX/PDF extraction noise | T5/T8 (extraction module) | Extracted text for a real historical đồ án file excludes headers/footers/TOC duplication, tables not garbled |
| Threshold calibration | T8 (AI) + T9 (seed/test) | Documented threshold derivation against the full 50-doc seeded set, included in báo cáo |
| CPU embedding latency / response-time NFR | T4 (schema: embeddings cache) + T8 (precompute pattern) | Measured response time against full 300/50-item seed corpus meets the documented NFR |
| MySQL utf8mb4 + Vietnamese collation | T6 (CSDL) | Seed data with full Vietnamese diacritic range sorts/searches correctly |
| File upload validation | T7 (UC nộp đề cương/báo cáo) | Test with oversized file and mismatched-content file, confirm rejection |
| RBAC/IDOR | T7 (first UC, shared auth dependency) | Direct API call test as wrong role/user is denied, not just hidden in UI |
| Apache proxy config (timeout/size/subpath/websocket) | T6 onward (stand up proxy early), verified T9 | Upload, slowest AI request, and any WebSocket/SSE feature all succeed through the actual proxy URL |
| Seed data realism | T5 (design) + T9 (generation) | Seed set includes exact-duplicate, paraphrased-duplicate, same-domain-different-topic, and unrelated pairs — not just exact copies |
| Scope creep (AI vs 5 UC) | T7/T8 boundary (roadmap sequencing) | All 5 UC pass acceptance criteria before AI polishing continues past its timeboxed week |

## Sources

- [dangvantuan/vietnamese-embedding — Hugging Face](https://huggingface.co/dangvantuan/vietnamese-embedding) — MEDIUM confidence (model card, community-maintained)
- [keepitreal/vietnamese-sbert — Hugging Face](https://huggingface.co/keepitreal/vietnamese-sbert) — MEDIUM confidence
- [Vietnamese Sentence Paraphrase Identification Using Sentence-BERT and PhoBERT — Springer](https://link.springer.com/content/pdf/10.1007/978-3-031-15063-0_40.pdf) — MEDIUM-HIGH confidence (peer-reviewed)
- [A Systematic Review of Multilingual Plagiarism Detection](https://thesai.org/Downloads/Volume16No8/Paper_36-A_Systematic_Review_of_Multilingual_Plagiarism_Detection.pdf) — MEDIUM-HIGH confidence (peer-reviewed survey)
- [Improving Academic Plagiarism Detection for STEM Documents by Analyzing Mathematical Content and Citations (arXiv)](https://arxiv.org/pdf/1906.11761) — MEDIUM-HIGH confidence, source for boilerplate/false-positive discussion
- [Testing of Support Tools for Plagiarism Detection (arXiv)](https://arxiv.org/pdf/2002.04279) — MEDIUM confidence
- [Content similarity detection — Wikipedia](https://en.wikipedia.org/wiki/Content_similarity_detection) — MEDIUM confidence, general background
- [pdfplumber (GitHub)](https://github.com/jsvine/pdfplumber) — HIGH confidence (official docs)
- [PyMuPDF text extraction recipes](https://pymupdf.readthedocs.io/en/latest/recipes-text.html) — HIGH confidence (official docs)
- [awsome-vietnamese-nlp (GitHub)](https://github.com/vndee/awsome-vietnamese-nlp) — MEDIUM confidence (community list)
- [PhoBERT: Pre-trained language models for Vietnamese (ACL Anthology)](https://aclanthology.org/2020.findings-emnlp.92.pdf) — HIGH confidence (peer-reviewed, original paper)
- [Is word segmentation necessary for Vietnamese sentiment classification? (arXiv)](https://arxiv.org/pdf/2301.00418) — MEDIUM-HIGH confidence
- [NLP Benchmarking popular Vietnamese tokenizer](https://huybik.github.io/Word-Tokenizer-Benchmark/) — MEDIUM confidence (independent benchmark)
- [Speeding up Inference — Sentence Transformers documentation](https://sbert.net/docs/sentence_transformer/usage/efficiency.html) — HIGH confidence (official docs)
- [mod_proxy — Apache HTTP Server Version 2.4 (official docs)](https://httpd.apache.org/docs/current/mod/mod_proxy.html) — HIGH confidence
- [URL not found when behind Proxy with Apache using subpaths — fastapi/fastapi#3930](https://github.com/fastapi/fastapi/issues/3930) — MEDIUM confidence (community-reported issue)
- [MySQL 8.4 Reference Manual — Unicode Character Sets](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html) — HIGH confidence (official docs)
- [MySQL WL#3865: Vietnamese collation](https://dev.mysql.com/worklog/task/?id=3865) — HIGH confidence (official MySQL worklog)
- [Everything you never wanted to know about MySQL Charsets & Collations — CodeRed](https://www.coderedcorp.com/blog/guide-to-mysql-charsets-collations/) — MEDIUM confidence

---
*Pitfalls research for: Vietnamese university thesis management system with local-embedding AI similarity/duplicate detection*
*Researched: 2026-09-27*
