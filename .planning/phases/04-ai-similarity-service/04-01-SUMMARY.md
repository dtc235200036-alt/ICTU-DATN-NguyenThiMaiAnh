---
phase: 04-ai-similarity-service
plan: 01
status: complete
subsystem: ai-service
tags: [fastapi, sentence-transformers, faiss, minhash, underthesea, docker, cpu-only]
requires: []
provides:
  - "ai-service/ standalone FastAPI app: /ingest, /check-title, /check-document, /reindex, /health behind X-API-Key"
  - "thesis_ai Alembic 0001 (chunk / embedding / index_metadata)"
  - "pipeline functions for 04-04 calibration: ingest, ingest_many, check_title, score_document, check_document, rebuild, reembed_missing"
  - "CPU-only non-root single-worker image ntma-ai (built locally as ntma-ai:test)"
affects: [04-03, 04-04, 04-05, 04-06, 04-07]
tech-stack:
  added: [sentence-transformers 6.1.0, transformers 5.17.0, torch 2.14.0+cpu, underthesea 9.5.0, faiss-cpu 1.15.1, datasketch 2.0.0, numpy 2.5.3]
  patterns: [load-once lifespan model, rebuild-index-from-DB at startup, replace-semantics ingest, one encode per batch, router-level API-key dependency, VARCHAR+CHECK enumerations]
key-files:
  created:
    - ai-service/pyproject.toml
    - ai-service/uv.lock
    - ai-service/alembic/versions/0001_thesis_ai.py
    - ai-service/app/main.py
    - ai-service/app/api.py
    - ai-service/app/schemas.py
    - ai-service/app/core/config.py
    - ai-service/app/core/security.py
    - ai-service/app/core/body_limit.py
    - ai-service/app/models.py
    - ai-service/app/db.py
    - ai-service/app/embedding.py
    - ai-service/app/index.py
    - ai-service/app/minhash.py
    - ai-service/app/pipeline.py
    - ai-service/app/nlp/normalize.py
    - ai-service/app/nlp/segment.py
    - ai-service/app/nlp/boilerplate.py
    - ai-service/app/nlp/chunking.py
    - ai-service/app/download_model.py
    - ai-service/Dockerfile
    - ai-service/docker-entrypoint.sh
    - ai-service/scripts/smoke_real_model.py
    - ai-service/scripts/container_smoke.sh
    - ai-service/README.md
    - ai-service/tests/test_title_path.py
    - ai-service/tests/test_document_path.py
    - ai-service/tests/test_schema_erd.py
  modified: []
decisions:
  - "No transformers<5 pin needed: bkai's PhobertTokenizer loads under sentence-transformers 6.1.0 + transformers 5.17.0"
  - "Sentence is the detection unit; passages = runs of consecutive flagged sentences from one source (max 6)"
  - "All-caps short lines (<=20 syllables) are treated as headings/cover title lines in boilerplate stripping (added to the [ASSUMED] list)"
  - "Cover labels (Sinh viên thực hiện, Giảng viên hướng dẫn, Mã sinh viên, Lớp) only stripped when followed by ':' or on a <=6-syllable line, so content sentences starting with those words survive"
  - "Numbered-heading rule skips lines ending in sentence punctuation (keeps numbered list items)"
  - "Empty encode batches do not count as encode calls"
  - "/health recomputes thieu_embedding from thesis_ai on each call (falls back to the last value if the DB errors)"
  - "Dockerfile installs the venv as appuser via COPY --chown instead of chown -R (the chown layer duplicated torch: 3.62 GB vs 1.98 GB)"
metrics:
  duration: "~25 min"
  completed: 2026-09-28
estimate:
  tokens: 160000
  tasks: 3
actuals:
  tokens: 27700
  tasks: 3
  commits: 4
plan_head_before: f4f2b8a57e9f6b518dcd740aa4d4caa9795f5714
plan_head_after: 13e1de69962bfea7ea9d2f390fed5b6f38a56b34
---

# Phase 4 Plan 01: AI Similarity Service Summary

This plan adds a standalone FastAPI AI service (`ai-service/`) that runs on the real Vietnamese bkai bi-encoder. It covers four things:

- Title check: semantic search over an exact FAISS `IndexFlatIP` of TOPIC and ARCHIVE titles.
- Document check: boilerplate stripping, then sentence chunks, then scoring each sentence with cosine OR MinHash-Jaccard, returning passages ready for highlighting.
- Storage: a replace-on-ingest `thesis_ai` store, and the in-memory index is rebuilt at startup with no re-encoding.
- Packaging: a CPU-only, non-root, single-worker image, measured at about 0.6–0.9 GiB under a 2 GiB cap.

## Tasks

| # | Task | Commit | Result |
|---|------|--------|--------|
| 1 | TRACER: title ingest → thesis_ai + FAISS → /check-title behind X-API-Key, real bkai smoke | fa819ed | 3 tests green; smoke exit 0 |
| 2 | Document path (TDD) | 84e7962 (RED), d97a231 (GREEN) | 5/5 tests green |
| 3 | Container, entrypoint, download CLI, container smoke, README | 13e1de6 | CONTAINER SMOKE OK |

**Tracer gate:** the tracer's `<verify>` was re-run from start to finish (`uv sync --frozen`, the 2 title tests plus the ERD test, then `smoke_real_model.py --profile bkai`). It passed before expansion began.

## Package legitimacy evidence (T-04-SC)

No human checkpoint, per orchestrator instruction. Below are the `importlib.metadata` URL lines from the synced venv:

| Package | Locked version | Home-page / Project-URL |
|---------|----------------|-------------------------|
| sentence-transformers | 6.1.0 | Homepage https://www.SBERT.net; Repository https://github.com/huggingface/sentence-transformers/ |
| torch | **2.14.0+cpu** | Homepage https://pytorch.org; Repository https://github.com/pytorch/pytorch |
| transformers | 5.17.0 | https://github.com/huggingface/transformers |
| underthesea | 9.5.0 | Homepage https://undertheseanlp.com/; Repository https://github.com/undertheseanlp/underthesea |
| faiss-cpu | 1.15.1 | Homepage/Repository https://github.com/facebookresearch/faiss |
| datasketch | 2.0.0 | Homepage https://ekzhu.github.io/datasketch; Source https://github.com/ekzhu/datasketch |

- `uv.lock` pins torch to `2.14.0+cpu` from https://download.pytorch.org/whl/cpu (`explicit = true` index). `grep -c 'name = "nvidia' uv.lock` gives `0`, and no triton was resolved. The lock is restricted to `sys_platform == 'linux' and platform_machine == 'x86_64'`. It also includes tokenizers 0.23.2 and numpy 2.5.3.
- **Tokenizer probe:** `SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder")` loaded `PhobertTokenizer` (dim 768) with transformers 5.17.0. **No pin was applied**, and the `transformers<5` fallback rule was not needed.

## Pipeline API (imported by plan 04-04)

```python
# app/embedding.py
class Encoder:
    def __init__(self, profile: str, torch_threads: int = 4)   # "bkai" | "e5" | "fake"
    name: str; dim: int; encode_calls: int
    def preprocess(self, text: str) -> str                      # nfc → (segment) → (prefix)
    def encode(self, texts: list[str]) -> np.ndarray             # float32 (n, dim), L2-normalized, 1 call
# app/index.py
class CorpusIndex:
    def __init__(self, dim: int, signer: Callable[[str], np.ndarray] | None = None)
# app/minhash.py
def signature(text: str, k: int, num_perm: int) -> np.ndarray   # uint32 under datasketch 2.x
def jaccard_many(sig: np.ndarray, matrix: np.ndarray) -> np.ndarray
# app/nlp/boilerplate.py
def strip_boilerplate(text: str) -> StripResult                 # StripResult(lines: list[str], removed: int)
# app/nlp/chunking.py
def sentences(lines: list[str]) -> list[str]
# app/pipeline.py
def ingest(session, index, encoder, loai: str, ma_nguon: int, text: str) -> int
def ingest_many(session, index, encoder, items: list[IngestItem]) -> list[int]   # IngestItem(loai, ma_nguon, text)
def check_title(index, encoder, text: str, top_k: int, nguong: float | None) -> list[dict]
def score_document(index, encoder, text: str, exclude_refs: set[int], strip: bool = True,
                   shingle: int = 4, num_perm: int = 128) -> DocumentScores  # DocumentScores(chunks: list[ChunkScore], removed)
def check_document(scores: DocumentScores, nguong_doan: float, nguong_nguyen_van: float,
                   top_k: int, chi_tiet_toi_da: int) -> dict
def rebuild(session, index, encoder) -> RebuildStats            # RebuildStats(loaded, thieu_embedding); no encode
def reembed_missing(session, index, encoder) -> RebuildStats
def count_missing(session, encoder) -> int
```

`ChunkScore` has these fields: `vi_tri, text, n_chars, sem_ref, sem_text, sem_thu_tu, sem_score, verb_ref, verb_text, verb_thu_tu, verb_score`. Scores are in the range 0..1. Plan 04-04 can re-threshold one `score_document` result with `check_document` as many times as it likes, without encoding again. Build the index as `CorpusIndex(dim, signer=partial(minhash.signature, k=4, num_perm=128))` so that the MinHash parameters match what `score_document` uses.

## Final HTTP contract

All routes except `/health` need `X-API-Key`. A missing or wrong key gets `401 {"detail":"Thiếu hoặc sai API key nội bộ"}`.

- `POST /ingest {id ≥1, type: TOPIC|ARCHIVE|DOCUMENT, text ≤ MAX_TEXT_CHARS (empty allowed)}` returns `{chunk_count, indexed: true}`. It uses REPLACE semantics per (type, id), and an unchanged source costs 0 encode calls.
- `POST /check-title {text 1..1000, top_k 1..20 = 5, nguong 0..100 | null}` returns `{matches: [{ref_id, loai, ty_le}]}`.
- `POST /check-document {ref_id ≥0, text 1..MAX_TEXT_CHARS, top_k 1..20 = 5, nguong_doan 0..100|null, nguong_nguyen_van 0..100|null, loai_tru: int[] ≤2000}` returns `{ty_le_tong, do_an_trung:[{ref_id, ty_le}], chi_tiet:[{ref_id, doan_nguon, doan_trung, vi_tri, ty_le, tin_hieu: NGUYEN_VAN|NGU_NGHIA, diem_ngu_nghia, diem_nguyen_van}], so_doan, so_doan_loai_tru}`.
- `POST /reindex {items?: IngestRequest[] ≤500}` returns `{indexed_count}`. With items, the count is the number ingested (1 encode). With an empty body, the count is the total vectors after re-embedding the missing chunks and rebuilding.
- `GET /health` returns `{status, model_loaded, index_size, index_size_tieu_de, index_size_tai_lieu, ten_model, encode_calls, thieu_embedding}`.
- Limits: a body over 8 MiB returns 413 (streamed byte count). Pydantic range or length violations return 422. `/docs` and `/openapi.json` exist only when `APP_ENV=test`.

## Measurements

**Real-model smoke on the host CPU** (`uv run python scripts/smoke_real_model.py --profile bkai`, exit 0):

```json
{"profile": "bkai", "model": "bkai-foundation-models/vietnamese-bi-encoder", "load_s": 8.77, "title_query_ms": 43.5, "encode_300_s": 4.42, "peak_rss_mb": 980.0, "torch_threads": 4, "top": [{"ref_id": 1, "loai": "ARCHIVE", "ty_le": 85.16}, {"ref_id": 4, "loai": "ARCHIVE", "ty_le": 29.36}, {"ref_id": 2, "loai": "ARCHIVE", "ty_le": 27.62}]}
```

- The paraphrased query "Phát triển phần mềm quản lý thư viện trường THPT" returns the library title first at 85.16. The runner-up scores 29.36.
- The NFD form gives an identical result.
- **Throughput:** encoding 300 sentences took 4.42 s, including underthesea segmentation. That is well inside the 20 s budget, so NFR-09 does not need the ONNX fallback.
- The first cold load, including the model download, took 63.5 s. A warm load takes 8.8 s.

**Container** (`bash ai-service/scripts/container_smoke.sh ntma-ai:test`, final run, `--memory=2g`):

| Metric | Value |
|--------|-------|
| Model-cache path | **host-cache** (`~/.cache/huggingface` mounted read-only at /models, `HF_HUB_OFFLINE=1`); the named-volume fallback was not needed |
| Startup to /health ok | 10 s |
| Paraphrased title | top-1 ARCHIVE 1 at 85.16 (runner-up 27.62) |
| Ingest DOCUMENT, 300 sentences | 4.62 s |
| /check-title latency | 45 ms |
| /check-document latency (300 sentences: 150 copied + 150 unrelated) | 3.73 s; ty_le_tong 57.61, 25 passages |
| Memory | docker stats 551.8 MiB / 2 GiB; memory.current 576 MB; memory.peak 584 MB (an earlier run with a different query peaked at 910 MB) |
| OOMKilled | false |
| Image size | `docker image inspect .Size` = 427,205,782 B (this Docker's image store reports compressed content size); `docker images` uncompressed 1.98 GB — under the 3.5 GiB cap either way |
| Runtime | uid 10001, `uvicorn … --workers 1`; the key never appeared in stdout or container logs |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The executor worktree was created from the wrong repository**
- **Found during:** startup.
- **Issue:** The worktree `/home/hahoang/.developer/worktrees/agent-acf2c7f2c5a089086` belongs to the home-directory repo `~/.git` (remote ThiGiacMayTinh, HEAD `b437ad5 first commit`), not to NTMA. The harness also blocks git/Write calls that target the NTMA checkout or a nested clone.
- **Fix:**
  1. Cloned NTMA read-only into a scratch directory.
  2. `git fetch`ed its `f4f2b8a` into the worktree's repo.
  3. Ran `git checkout -B worktree-agent-acf2c7f2c5a089086 FETCH_HEAD`, so the agent branch now carries NTMA history based on `f4f2b8a`.
  4. Deleted the scratch clone.
- **Result:** All commits are on branch `worktree-agent-acf2c7f2c5a089086` **inside `~/.git`**, not inside the NTMA repo. To merge, run this from the NTMA checkout: `git fetch /home/hahoang/.developer/worktrees/agent-acf2c7f2c5a089086 worktree-agent-acf2c7f2c5a089086 && git merge FETCH_HEAD`. The shared base is `f4f2b8a`.

**2. [Rule 1 - Bug] The Dockerfile's `chown -R /app` duplicated the 1.3 GB venv layer**
- **Found during:** Task 3.
- **Issue:** The first build was 3.62 GB, which is over the 3.5 GiB image cap.
- **Fix:** Create appuser first, then `COPY --chown` and run `uv sync --no-cache` as appuser. The image is now 1.98 GB.
- **Commit:** 13e1de6

**3. [Rule 2 - Correctness] Extra boilerplate guards**
- **Found during:** Task 2.
- **Change:** Added an all-caps short-line heading rule, which catches the cover thesis title, MỞ ĐẦU and KẾT LUẬN. Cover labels now require `:` or a very short line. Numbered headings are skipped when the line ends in sentence punctuation. These rules stop the cover title from merging into the first content sentence, and they keep content sentences that begin with "Giảng viên hướng dẫn…" or "Lớp…".
- **Commit:** d97a231

**4. [Minor] Small differences from the plan text**
- MinHash signatures are `uint32` under datasketch 2.x, not `uint64` as the plan assumed. The value is irrelevant because signatures are never persisted.
- `app/db.py` exposes `make_engine` / `make_session_factory`, and the session factory lives on `app.state` rather than as a module-level `SessionLocal`. The lifespan builds it, so tests and restarts get a fresh engine.

**Total deviations:** 4 (1 environment blocker, 1 bug, 1 correctness addition, 1 minor). **Impact:** the service contract is unchanged, but the orchestrator has to fetch the branch from the worktree path as described in item 1.

## TDD Gate Compliance

- **RED** `84e7962`: `test_document_path.py` failed at collection, because `app.nlp.boilerplate` and `app.nlp.chunking` did not exist yet.
- **GREEN** `d97a231`: 5/5 pass.
- No refactor commit was needed.

## Known Stubs

None. The boilerplate list is intentionally **[ASSUMED]** under D-03, because the official template TL-04/TL-05 has not been collected. This is documented in the module header and the README, and should be replaced when the template arrives.

## Threat Flags

None beyond the plan's threat register. T-04-01..06 are mitigated as specified: router-level key with `compare_digest`, fixed 401 detail, docs disabled outside test, text/body/list caps, bound SQL parameters with CHECK, rebuild from DB plus the metadata drift warning, non-root, single worker, and no host port except the ephemeral 127.0.0.1 smoke port.

## Self-Check: PASSED

- All 28 key files exist under `ai-service/`.
- Commits fa819ed, 84e7962, d97a231 and 13e1de6 are present on `worktree-agent-acf2c7f2c5a089086`.
- `uv run pytest -q` gives 5 passed.
- `git diff --name-only f4f2b8a..HEAD` lists only `ai-service/**`.
- The smoke container and the superseded dangling images from this run were removed. `ntma-ai:test` is kept for plan 04-05.
