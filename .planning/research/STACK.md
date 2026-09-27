# Stack Research

**Domain:** University thesis/graduation-project management system (Vietnamese academic workflow) + local AI similarity/plagiarism-detection microservice
**Researched:** 2026-09-27
**Confidence:** MEDIUM (core web/backend versions cross-verified against PyPI/official release pages = MEDIUM tier; Vietnamese NLP/embedding ecosystem claims rest on HF model cards, benchmark blog posts and community comparisons = LOW-MEDIUM, flagged per-row below)

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11 | Runtime for both Web API and AI service | Sweet spot: supported by FastAPI, SQLAlchemy 2.x, sentence-transformers 5.x, and `underthesea` (needs ≥3.10). 3.12/3.13 are fine too, but 3.11 has the widest wheel/driver compatibility for older student-lab Linux boxes. |
| FastAPI | 0.141.x (latest stable, released 2026-07-29) | Web API + AI service framework | User-mandated. Async-native, Pydantic v2 built in, auto OpenAPI docs — the OpenAPI spec doubles as your PI 2.2 API documentation artifact for free. |
| Pydantic | v2 (bundled with FastAPI 0.141) | Request/response validation, DTOs | Ships with FastAPI; do not manually pin v1 — v1 is EOL and several FastAPI 0.14x features assume v2. |
| Uvicorn | latest (`uvicorn[standard]`) | ASGI server behind Apache | Standard pairing with FastAPI; `[standard]` extra pulls in `uvloop`/`httptools` for real performance, and `--proxy-headers` flag is what makes it trust Apache's `X-Forwarded-*` headers. |
| SQLAlchemy | 2.0.54 (stable 2.0 line) | ORM / Core for MySQL | **Do NOT jump to 2.1** (released 2026-09-24, days before this research) — too new, driver/Alembic ecosystem hasn't caught up, and a 10-week solo thesis project should not absorb bleeding-edge breakage risk. 2.0's typed ORM (`Mapped[]`, `mapped_column`) is what all current tutorials and Alembic examples target. |
| Alembic | 1.20.0 | DB schema migrations | Alembic 1.20 dropped support for SQLAlchemy <2.0, confirming 2.0.x is the intended pairing. Migrations give you a clean, gradable history of schema evolution across the 10-week timeline — useful evidence for the "Thiết kế CSDL" chapter. |
| MySQL | 8.0.x (LTS) | Mandatory relational store (PI 3.1) | User/PI-mandated. 8.0 (not 5.7) for `utf8mb4` defaults (critical for Vietnamese text — see Pitfalls note below), window functions (useful for tiến độ/leaderboard-style queries), and CTEs. |
| MySQL driver (async) | `asyncmy` 0.2.x | SQLAlchemy async engine ↔ MySQL | Newer, Cython-accelerated, and has correct `caching_sha2_password` (MySQL 8's default auth plugin) support. `aiomysql` (PyMySQL-based) is the older/more battle-tested option but is slower and has lagged on MySQL 8 auth compatibility. Pick asyncmy for a fresh MySQL 8 project. |
| MySQL driver (sync, if you skip async) | `PyMySQL` 1.1.x | Sync engine fallback | If the team is not comfortable with `async def` + `AsyncSession` dependency wiring under time pressure, sync SQLAlchemy + PyMySQL is a fully legitimate, simpler alternative — see "Stack Patterns by Variant" below for the tradeoff. |

### AI Service — NLP / Embedding / Similarity Stack

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `sentence-transformers` | 5.6.x | Load & run embedding models locally | The standard local-inference wrapper around HF transformer models; no paid API calls, runs on CPU (fine at this scale — few hundred docs). |
| `bkai-foundation-models/vietnamese-bi-encoder` | current (HF model, RoBERTa/PhoBERT-base-v2 backbone) | **Primary** Vietnamese sentence/paragraph embedding model | Purpose-built for Vietnamese; on the public Legal Text Retrieval (Zalo 2021) benchmark it beats vietnamese-sbert (Acc@1 73.3%, MRR@10 80.7%). Same domain shape as academic/legal-style Vietnamese prose your đề cương/báo cáo text will have. **Confidence: MEDIUM** (HF model card + one public benchmark, not independently reproduced by this research). |
| `underthesea` | 9.2.x (Python ≥3.10 required) | Vietnamese word segmentation, required pre-processing step for the model above | The bkai encoder's PhoBERT-v2 backbone was pretrained on **word-segmented** text (e.g. `vui_tính`) — you must run a segmenter before encoding or the model silently degrades. Benchmarked at ~80% segmentation accuracy vs `pyvi`'s ~58%; at only a few hundred documents, underthesea's extra CPU cost is irrelevant, so take the accuracy. **Confidence: MEDIUM** (community benchmark blog, not a peer-reviewed source, but consistent with underthesea being the most actively maintained toolkit in 2026). |
| `intfloat/multilingual-e5-base` | current (HF model) | **Fallback / simpler alternative** embedding model | Works directly on raw (non-segmented) Vietnamese text — no segmentation pipeline needed. Slightly weaker on Vietnamese-specific benchmarks than a fine-tuned Vietnamese model, but a legitimate one-less-moving-part option if the underthesea+PhoBERT segmentation pipeline becomes a schedule risk. Requires `"query: "` / `"passage: "` prefixing per the E5 convention — do not skip this, it measurably affects similarity scores. |
| `faiss-cpu` | 1.15.x | In-process vector similarity index inside the AI service | At this scale (≈300 topics + a few hundred docs → low thousands of paragraph vectors) an **exact flat index** (`IndexFlatIP` on L2-normalized vectors = cosine similarity) is both simplest and fastest — no need for IVF/HNSW approximate indexing. FAISS is a library, not a server: build the index in memory at AI-service startup from vectors persisted in MySQL, no extra deployed component. |
| `datasketch` | 1.x | MinHash + LSH for shingle-based near-duplicate detection | Standard, well-maintained Python implementation of MinHash/LSH — pairs with embedding similarity to catch literal copy-paste that paraphrase-tolerant embeddings can miss (see technique below). |
| `python-docx` | 1.1.x | DOCX paragraph text extraction | Simplest, most mature library for "walk paragraphs in order" — matches exactly what paragraph-level duplicate detection needs. Do not reach for `docx2python`'s nested structured output (headers/footers/images/comments) unless you actually need that metadata; it adds parsing complexity you won't use. |
| `PyMuPDF` (`pymupdf`/`fitz`) | 1.24.x+ | PDF text extraction | Fastest of the mainstream Python PDF libraries and extracts embedded-font Vietnamese diacritics correctly **as long as the source PDF has a valid ToUnicode map** — true for essentially all PDFs exported from Word (which is your only input format per PI constraints; no scanned/OCR PDFs expected). `pdfplumber` is the fallback if you ever need precise table/layout-aware extraction; avoid raw `pdfminer.six` (both PyMuPDF and pdfplumber already wrap/outperform it). |

### Authentication / RBAC

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `PyJWT` | 2.13.x | JWT issue/verify | FastAPI's own docs migrated from `python-jose` to `PyJWT` — python-jose is effectively abandoned (last meaningful release ~3 years old) with unpatched advisories. PyJWT is actively maintained (CVE-2026-48526 fixed in 2.13.0) and ~25% faster at verify. **Do not use python-jose for a new project in 2026.** |
| `bcrypt` (direct) | 4.x | Password hashing | `passlib` — long the go-to "batteries included" wrapper — is unmaintained (no meaningful release since 2020) and has known friction with `bcrypt` ≥4.0/Python 3.12+. Call the `bcrypt` package directly (`bcrypt.hashpw`/`checkpw`) instead of wrapping it in passlib. If you want an actively maintained passlib-style wrapper with Argon2id support, `pwdlib` is the emerging 2026 replacement — reasonable alternative, not required at this scale. |
| Custom RBAC via FastAPI `Depends` | — | 3-role authorization (Sinh viên / Giảng viên / Bộ môn-Khoa) | With exactly 3 fixed roles and workflow-specific rules (e.g. "only the assigned GVHD can duyệt this đề cương"), a full user-management framework is the wrong shape. Encode `role` (and where needed `assigned_gvhd_id`) as JWT claims, then write small `Depends(require_role("bo_mon"))` / row-level ownership check dependencies. This is less code than integrating `fastapi-users` and gives full control over the approval-workflow edge cases PI 3.3 requires. |

### React Client

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| React | 19.3 | UI library | User-mandated; current stable. |
| Vite | 7.3.x | Build tool / dev server | Standard 2026 React tooling (Create React App is dead). `npm create vite@latest -- --template react-ts`. Requires Node.js ≥20.19/22.12 — check the dev/deploy machine's Node version. |
| TypeScript | 5.x | Type safety across API contract | Strongly recommended even for a thesis: mirroring FastAPI/Pydantic schemas as TS types catches integration bugs between the 3 SOA components before runtime, which matters when you (solo) are building both ends. |
| TanStack Query (React Query) | v5 | Server-state data fetching/caching | The 2026 standard for "talk to a REST API" in React — handles caching, refetch, loading/error states, and mutation-invalidation patterns out of the box. Avoid hand-rolled `useEffect` + `fetch` data fetching; it's what most React anti-pattern guides call out first. |
| Axios | 1.x | HTTP client under TanStack Query | Pick over raw `fetch` for its interceptor API — needed to attach the JWT bearer token to every request and to centrally handle 401 (refresh/redirect to login), which you'll want across 3 roles' worth of screens. |
| React Router | v7 | Client-side routing | Standard, works cleanly with a Vite SPA; simpler mental model than TanStack Router for a CRUD-heavy app with 3 role-scoped route trees. |
| Ant Design (`antd`) | v5/v6 | UI component kit | **Best fit for this specific app.** You need data-heavy CRUD screens fast: đề tài listing/approval tables with filters, đề cương review forms, hội đồng scheduling grids, tiến độ tracking. Ant Design ships a fully-featured `Table` (sorting/filtering/pagination) and `Form` out of the box, is the most common choice for Vietnamese enterprise/academic internal tools, and minimizes custom styling work under a 10-week solo timeline. `shadcn/ui` (copy-in Radix+Tailwind components) gives more visual control but requires assembling data-table/form behavior yourself — better for a product with unique branding, worse for time-to-demo. MUI is a reasonable second choice if the Material look is preferred. |
| Zustand | 4.x/5.x | Lightweight client state (auth token, current user) | Simpler than Redux for the small amount of genuinely global client state this app needs (auth session, maybe a "current role view"). Server state stays in TanStack Query, not Zustand — don't duplicate it. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `python-multipart` | current | FastAPI file upload parsing | Required by FastAPI for any `UploadFile` (đề cương/báo cáo submission) endpoint — install explicitly, it's not a transitive default anymore in recent FastAPI. |
| `pydantic-settings` | 2.x | Env-based config (DB URL, JWT secret, AI-service base URL) | Standard FastAPI 2026 pattern for 12-factor config across the 2 services (Web API, AI service) and 3 environments (dev/demo/prod-like). |
| `httpx` | 1.x | Server-to-server calls, Web API → AI service | Async-capable HTTP client for the Web API to call the internal AI service's `/similarity` endpoints; same library FastAPI's own `TestClient` is built on, so test code and production code share idioms. |
| `python-jose` | — | **Avoid** | See "What NOT to Use". |

## Installation

```bash
# Web API service
pip install "fastapi[standard]" "sqlalchemy[asyncio]==2.0.*" alembic asyncmy \
  pyjwt bcrypt python-multipart pydantic-settings httpx

# AI similarity service (separate FastAPI app/venv per SOA split)
pip install "fastapi[standard]" sentence-transformers underthesea faiss-cpu \
  datasketch python-docx pymupdf

# React client
npm create vite@latest client -- --template react-ts
cd client
npm install antd @tanstack/react-query axios react-router zustand
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not (as primary) |
|----------|-------------|-------------|------------------------|
| MySQL async driver | asyncmy | aiomysql | Older PyMySQL-based codepath, slower, historically behind on MySQL 8 `caching_sha2_password` auth — fine if you already have aiomysql-based code, not the best fresh-start pick. |
| Auth/RBAC | Custom `Depends`-based RBAC | `fastapi-users` / `fastapi-rbac` | Full user-management frameworks assume flexible/growing role and identity models (social login, email verification flows, multi-tenant). This project has exactly 3 fixed roles baked into a fixed academic workflow — the framework's abstractions cost more to learn/fight than they save. |
| Vietnamese embedding | `bkai-foundation-models/vietnamese-bi-encoder` + `underthesea` segmentation | `intfloat/multilingual-e5-base` | Simpler pipeline (no segmentation step, no PhoBERT-specific tokenization quirks), but measurably weaker on Vietnamese-specific retrieval benchmarks than a purpose-tuned model. Use e5 if segmentation pipeline risk outweighs the accuracy loss. |
| Vietnamese embedding | (above) | `dangvantuan/vietnamese-embedding` (SimCSE/PhoBERT) | Another credible Vietnamese-tuned option surfaced in research; less benchmark evidence available than bkai's during this research pass — worth a quick side-by-side test on your seed corpus (PI 4.2's deliberately-duplicated docs) before committing. |
| Word segmentation | `underthesea` | `pyvi` | ~2x faster but only ~58% segmentation accuracy vs underthesea's ~80% in the one public benchmark found; at a few-hundred-document scale, speed is not the constraint — accuracy is, since it directly affects duplicate-detection quality. |
| Vector search | FAISS (`faiss-cpu`, flat index) | Plain NumPy/scikit-learn cosine similarity matrix | At <10k paragraph vectors, a brute-force NumPy matrix multiply is also fast enough (sub-second) and removes a dependency. Legitimate simplification if you want one fewer library; FAISS is recommended mainly because "vector index" is the expected/standard vocabulary for an AI-similarity feature in a defense committee's eyes, and it costs nothing extra to set up at this scale. |
| Vector search | FAISS (in-process) | Qdrant (dedicated vector DB server) | Qdrant's value is a persistent server with rich payload filtering for larger/growing/multi-tenant corpora. Running an extra Docker service behind Apache adds deployment surface for a fixed ~300-topic, demo-scope project with no such requirement — not worth it here. Reconsider only if the "kho dữ liệu" is expected to keep growing across many future khóa and outlive this thesis's demo scope. |
| Vector search | FAISS / NumPy | MySQL-native vector functions | MySQL 8.0 (mainline, non-HeatWave) has no native vector similarity type/index — don't try to force cosine similarity into SQL; keep embeddings and search in the Python AI service, persist raw vectors in MySQL only for durability across restarts. |
| PDF extraction | PyMuPDF | pdfplumber | Slower (wraps pdfminer.six), but stronger for layout/table-aware extraction if a later requirement needs to preserve tabular structure inside báo cáo files. Use as a secondary tool, not primary. |
| Password hashing | `bcrypt` (direct) | `pwdlib` | `pwdlib` is a legitimate, actively-maintained passlib successor with Argon2id support — reasonable to pick instead of raw bcrypt if you want a slightly nicer API; both are fine, avoid only `passlib` itself. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `python-jose` | Effectively abandoned (last meaningful release ~3 years ago); FastAPI's own docs have moved off it; unpatched security advisories accumulate over time. | `PyJWT` |
| `passlib` | Unmaintained since ~2020; breaks with newer `bcrypt` releases and newer Python versions. | `bcrypt` directly, or `pwdlib` |
| SQLAlchemy 2.1.x | Released days before this research (2026-09-24); still stabilizing, driver/tooling ecosystem (Alembic, asyncmy) hasn't fully caught up yet. Unnecessary risk for a fixed-deadline solo project. | SQLAlchemy 2.0.54 (stable 2.0 line) |
| Create React App | Long dead/unmaintained; no longer the React team's recommended starting point. | Vite |
| MySQL 5.7 | Ships `latin1`-era defaults and lacks window functions/CTEs used in modern query patterns; also nearing/past EOL support windows. | MySQL 8.0.x, with the schema explicitly set to `utf8mb4`/`utf8mb4_unicode_ci` (or `0900_ai_ci`) — non-negotiable for correct Vietnamese diacritic storage/collation. |
| Raw `pdfminer.six` as your primary PDF tool | Lower-level, slower than tools built on top of it. | PyMuPDF (primary) or pdfplumber (secondary) |
| Approximate FAISS indexes (IVF/HNSW/PQ) | Unnecessary complexity/tuning (nlist, nprobe, quantization) for a corpus of a few thousand vectors; approximate search exists to trade accuracy for speed at million-vector scale, which this project will never reach. | `IndexFlatIP` (exact, cosine via L2-normalized vectors) |
| Running Qdrant/pgvector purely to "have a vector DB" | Extra deployed service behind Apache/HTTPS for no functional gain at this scale; adds ops surface a solo 10-week thesis doesn't need. | In-process FAISS inside the AI service, vectors persisted as BLOB/JSON in MySQL for durability |
| Feeding raw (non-segmented) Vietnamese text directly into the bkai PhoBERT-based encoder | Its backbone was pretrained on word-segmented text (`vui_tính`-style tokens); skipping segmentation silently degrades embedding quality without raising an error. | Run `underthesea.word_tokenize(text, format="text")` before encoding — or switch to `multilingual-e5-base`, which does not require segmentation. |

## Stack Patterns by Variant

**If the team is confident with async Python (async/await, `AsyncSession` dependency wiring):**
- Use FastAPI async endpoints + SQLAlchemy `AsyncEngine`/`AsyncSession` + `asyncmy`.
- Because it's the 2026-standard pattern, scales cleanly, and matches nearly all current tutorials/Stack Overflow answers you'll be debugging against.

**If the timeline is tight and the team wants to minimize new concepts to learn (recommended default for a solo 10-week thesis):**
- Use FastAPI with plain **sync** endpoints (`def`, not `async def`) + SQLAlchemy sync `Engine`/`Session` + `PyMySQL`.
- Because FastAPI automatically runs sync path operations in a threadpool, so you get correct concurrency behavior without touching `async`/`await` anywhere in your CRUD code — fewer footguns, faster to build and debug for someone learning FastAPI for the first time.
- **Important corollary:** the AI service does CPU-bound local model inference (embedding + similarity), which is *never* naturally async. Whether the AI service's endpoints are declared `async def` or `def`, make sure model inference calls are either (a) plain sync `def` endpoints (FastAPI threadpools them automatically), or (b) explicitly wrapped in `await asyncio.to_thread(...)` if you insist on `async def`. Do not call `model.encode(...)` directly inside an `async def` endpoint without offloading — it will block the entire event loop for every concurrent request.

**If Apache is only reverse-proxying REST (no live/streaming features):**
- Use `mod_proxy` + `mod_proxy_http` only (`ProxyPass`/`ProxyPassReverse` to `http://127.0.0.1:<port>/`), skip `mod_proxy_wstunnel`.
- Because this project's UC set (đăng ký, duyệt, nộp, chấm) is plain request/response — no chat/notifications-over-websocket requirement was stated. Since Apache httpd ≥2.4.47, `mod_proxy_http` alone can even upgrade WebSocket connections if a future requirement adds them, so you're not locking yourself out by starting simple.
- Serve the React production build (`vite build` output) as **static files directly from Apache's DocumentRoot** — do not proxy static assets through uvicorn. Only `/api/*` (Web API) needs a `ProxyPass`. The AI service should **not** get a public Apache proxy path at all — it's called server-to-server from the Web API over localhost/internal network only, keeping the SOA boundary and the attack surface both correct (matches PI 2.2/4.1: the client only ever talks to the Web API).

**Paragraph-level duplicate detection — recommended combined technique:**
- Chunk each DOCX/PDF into paragraphs at structural boundaries during extraction (python-docx paragraph objects; PyMuPDF block/line breaks for PDF).
- Run **two independent similarity signals** per paragraph pair and flag on either crossing threshold:
  1. **Semantic:** word-segment (underthesea) → embed (bkai vietnamese-bi-encoder) → cosine similarity via FAISS `IndexFlatIP`. Catches paraphrased/reworded copying.
  2. **Lexical:** k-word shingles (k≈5–8) on the segmented tokens → MinHash signatures (`datasketch`) → Jaccard estimate. Catches verbatim/near-verbatim copy-paste that a paraphrase-tolerant embedding model can under-flag or over-generalize.
- Report both scores (and which one triggered) in the UI so a GVHD can see *why* something was flagged — matters for PI 3.4's "chỉ rõ đoạn trùng ... tỷ lệ tương đồng" requirement and for defensibility in front of the hội đồng.
- Aggregate to a document-level "tỷ lệ tương đồng" as the fraction of paragraphs flagged, plus the list of top-matching source documents.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|------------------|-------|
| SQLAlchemy 2.0.54 | Alembic 1.20.0 | Alembic 1.20 requires SQLAlchemy ≥2.0.0; confirmed pairing. |
| SQLAlchemy 2.0.x async engine | asyncmy 0.2.x | Use `mysql+asyncmy://` dialect URL; do not mix with `pymysql` sync URL in the same engine. |
| FastAPI 0.141.x | Pydantic v2, Starlette (bundled) | Do not manually install/pin Pydantic v1 alongside it. |
| Vite 7.3.x | Node.js ≥20.19 or ≥22.12 | Verify the dev machine's Node version before scaffolding — older Node (18.x) will fail to run Vite 7. |
| `bkai-foundation-models/vietnamese-bi-encoder` | `sentence-transformers` ≥2.x, `underthesea` (any recent version with `word_tokenize`) | Segmentation must happen **before** the text reaches `SentenceTransformer.encode()`. |
| `underthesea` | Python ≥3.10 | Confirmed floor from PyPI/docs; fine under the recommended Python 3.11. |
| `faiss-cpu` | Any Python 3.9–3.12 wheel | No GPU/CUDA setup needed or wanted here — this is a CPU-only, small-corpus deployment. |

## Sources

- [FastAPI PyPI](https://pypi.org/project/fastapi/) — current version (websearch, MEDIUM/verified)
- [SQLAlchemy download page](https://www.sqlalchemy.org/download.html) and [2.1.0b2 release post](https://www.sqlalchemy.org/blog/2026/04/16/sqlalchemy-2.1.0b2-released/) — version timeline (websearch, MEDIUM/verified)
- [Alembic changelog](https://alembic.sqlalchemy.org/en/latest/changelog.html) — 1.20.0, SQLAlchemy ≥2.0 requirement (websearch, MEDIUM/verified)
- [SQLAlchemy asyncmy discussion #6893](https://github.com/sqlalchemy/sqlalchemy/discussions/6893), [aiomysql PyPI](https://pypi.org/project/aiomysql/) — driver comparison (websearch, MEDIUM)
- [FastAPI discussion #11345 — python-jose abandonment](https://github.com/fastapi/fastapi/discussions/11345), [PyJWT best practices 2026](https://johal.in/jwt-secure-tokens-pyjwt-best-practices-for-api-auth-2026/) — auth library recommendation (websearch, MEDIUM)
- [FastAPI discussion #11773 — passlib unmaintained](https://github.com/fastapi/fastapi/discussions/11773) — password hashing recommendation (websearch, MEDIUM)
- [Vite releases](https://vite.dev/releases), [React v19 blog](https://react.dev/blog/2024/12/05/react-19) — frontend versions (websearch, MEDIUM/verified)
- [shadcn/ui vs MUI vs Ant Design (2026)](https://adminlte.io/blog/shadcn-ui-vs-mui-vs-ant-design/), [Ant Design vs MUI vs Shadcn](https://www.index.dev/skill-vs-skill/shadcn-ui-vs-material-ui-vs-ant-design) — UI kit comparison (websearch, LOW-MEDIUM, blog-sourced)
- [bkai-foundation-models/vietnamese-bi-encoder model card](https://huggingface.co/bkai-foundation-models/vietnamese-bi-encoder) and [segmentation commit](https://huggingface.co/bkai-foundation-models/vietnamese-bi-encoder/commit/c1d85a224485625115c419475af96fa7460f07f0) — model architecture, benchmark, segmentation requirement (websearch, MEDIUM — primary source is the model author's own card)
- [intfloat/multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base), [Multilingual E5 technical report](https://arxiv.org/pdf/2402.05672) — alternative embedding model (websearch, MEDIUM)
- [Underthesea vs Pyvi vs VnCoreNLP benchmark](https://huybik.github.io/Word-Tokenizer-Benchmark/) — segmentation speed/accuracy comparison (websearch, LOW — single community benchmark, not independently reproduced)
- [underthesea PyPI](https://pypi.org/project/underthesea/) — version/requirements (websearch, MEDIUM)
- [FAISS vs Qdrant vs pgvector, DEV Community](https://dev.to/pranjulrathour/faiss-vs-qdrant-vs-pgvector-choosing-a-vector-store-for-a-student-or-startup-rag-project-kj2) — vector store choice at small scale (websearch, LOW-MEDIUM, blog-sourced)
- [Shingling for Similarity and Plagiarism Detection](https://dzone.com/articles/shingling-for-similarity-and-plagiarism-detection), [MinHash/LSH plagiarism detection, Medium](https://medium.com/@salma_s/plagiarism-and-near-duplicate-detection-using-shingling-minhashing-and-locality-sensitive-hashing-9c7fb76f2608) — shingling+MinHash technique (websearch, LOW-MEDIUM, blog-sourced but consistent with well-established IR literature)
- [Apache mod_proxy docs](https://httpd.apache.org/docs/current/mod/mod_proxy.html), [mod_proxy_wstunnel docs](https://httpd.apache.org/docs/current/mod/mod_proxy_wstunnel.html) — reverse proxy config (websearch, MEDIUM — official Apache docs)
- [PyMuPDF GitHub](https://github.com/pymupdf/pymupdf), [Nutrient PDF library comparison 2026](https://www.nutrient.io/blog/best-python-pdf-libraries/) — PDF extraction tool choice (websearch, LOW-MEDIUM)
- [docx2python PyPI](https://pypi.org/project/docx2python/) — DOCX extraction alternative (websearch, LOW-MEDIUM)
- [sentence-transformers PyPI](https://pypi.org/project/sentence-transformers/) — current version (websearch, MEDIUM)

---
*Stack research for: University thesis/graduation-project management system + Vietnamese AI similarity-detection service*
*Researched: 2026-09-27*
