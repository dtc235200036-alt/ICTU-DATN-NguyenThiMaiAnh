---
phase: 04-ai-similarity-service
reviewed: 2026-09-28T00:00:00Z
depth: standard
files_reviewed: 47
files_reviewed_list:
  - ai-service/app/api.py
  - ai-service/app/main.py
  - ai-service/app/core/body_limit.py
  - ai-service/app/core/config.py
  - ai-service/app/core/security.py
  - ai-service/app/db.py
  - ai-service/app/download_model.py
  - ai-service/app/embedding.py
  - ai-service/app/index.py
  - ai-service/app/minhash.py
  - ai-service/app/models.py
  - ai-service/app/pipeline.py
  - ai-service/app/schemas.py
  - ai-service/app/nlp/boilerplate.py
  - ai-service/app/nlp/chunking.py
  - ai-service/app/nlp/normalize.py
  - ai-service/app/nlp/segment.py
  - ai-service/alembic/env.py
  - ai-service/alembic/versions/0001_thesis_ai.py
  - ai-service/calibration/calibrate.py
  - ai-service/Dockerfile
  - ai-service/.dockerignore
  - ai-service/docker-entrypoint.sh
  - backend/app/core/config.py
  - backend/app/services/ai_client.py
  - backend/app/services/ai_index.py
  - backend/app/services/archive.py
  - backend/app/services/document_check.py
  - backend/app/services/documents.py
  - backend/app/services/thresholds.py
  - backend/app/services/title_check.py
  - backend/app/routers/thresholds.py
  - backend/app/schemas/thresholds.py
  - backend/app/models/cau_hinh_nguong.py
  - backend/app/seed_ai_corpus.py
  - backend/alembic/versions/0010_nguong_hieu_chinh.py
  - frontend/src/features/documents/highlight.ts
  - frontend/src/features/documents/CheckDetailPage.tsx
  - frontend/src/features/documents/CheckPanel.tsx
  - frontend/src/features/thresholds/ThresholdSettingsPage.tsx
  - frontend/src/features/thresholds/api.ts
  - frontend/src/features/thresholds/routes.tsx
  - deploy/docker-compose.yml
  - deploy/mysql/init-thesis-ai.sh
  - deploy/seed-ai.sh
  - deploy/e2e-ai.sh
  - deploy/ai-nfr.sh
findings:
  critical: 4
  warning: 6
  info: 7
  total: 17
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-09-28
**Depth:** standard, with targeted runtime measurements against the running `ntma-ai-1` container. Only the read-only `/check-document` and `/check-title` endpoints were called.
**Files Reviewed:** 47
**Status:** issues_found

## Summary

The security basics hold up:
- The X-API-Key check uses `hmac.compare_digest` and the key is never logged.
- `AiClientHttp` logs only the exception class name.
- The AI service has no `ports:` entry and no Apache route.
- `/docs` and `/openapi.json` are turned off outside test.
- The request body limit counts the bytes it actually receives.
- The highlight code renders React text and `<mark>` only. There is no raw HTML anywhere under `frontend/src`, so there is no XSS.
- Both threshold routes require `BO_MON`. The input is limited to 0–100 with 2 decimals, and a DB CHECK backs that up.
- NFC normalization is applied the same way in the AI pipeline, the backend `nfc()` and `highlight.ts`.
- Lock ordering has no inversion, so there is no deadlock: `_WRITE_LOCK` → `encoder._lock` → `index.lock`.

The serious problems are in the behaviour of the core feature and in availability:

1. **Wrong warning rule.** The "Vượt ngưỡng cảnh báo" decision compares a different statistic from the one the threshold was calibrated on. The calibration's own data shows a false positive (P19: 23.96 % total vs a 10.4 % threshold).
2. **One global encoder lock and one batch per document.** Measured: a 349 594-character text took **32.5 s**, which is more than the Web API's 24 s timeout, so the check always ends in LOI. A title check sent during that run **failed with ReadTimeout at 4.01 s**.
3. **Chunking runs in quadratic time on text the student controls.** Measured: 81 KB took 8.25 s, and time grows about 4× each time the input doubles. That is roughly 85 min of CPU per request at the allowed 2 000 000 characters.
4. **Boilerplate stripping can be abused to hide content.** One "Phụ lục" line under each chapter heading removes the whole chapter from the check. Verified: the result was 0 lines kept. The Web API also drops the removed-line count.

## Critical Issues

### CR-01: The document warning compares `ty_le_tong` with a threshold calibrated on the per-source share; the AI's `do_an_trung` is thrown away

**File:** `backend/app/services/document_check.py:188-229`, `frontend/src/features/documents/CheckPanel.tsx:117` (the same pattern is in `frontend/src/features/defense/ScoringPage.tsx:48`)

**Issue:** Plan 04-04 calibrated `NGUONG_TAI_LIEU = 10.4` for the rule **`do_an_trung[A] ≥ nguong_tai_lieu`**:
- `calibrate.py:301, 429` compute and fit on the per-source share.
- 04-04-SUMMARY states "ty_le_tong is display-only".

The production path does something different:
- `document_check.run` stores only `ty_le_tong` and `chi_tiet`. The AI's `do_an_trung` (the calibrated statistic) is never persisted.
- `CheckPanel` then shows "Vượt ngưỡng cảnh báo" when `ty_le_tong > nguong_ap_dung`.

The calibration's own record `ket-qua-chi-tiet.json` → `cap[18]` is P19 (CUNG_LINH_VUC, `ky_vong: false`): `ty_le_tong = 23.96`, `ty_le_nguon = 0.0`. It passes calibration, but in production it would show **"Vượt ngưỡng cảnh báo"** (23.96 > 10.40). Any same-field thesis whose flagged sentences are spread over several sources will get a false warning.

A second problem: the comparison is strict `>`, but the threshold definition says "từ giá trị này trở lên" (`services/thresholds.py:48-49`), i.e. `≥`. The calibration and `title_check` both use `≥`.

**Fix:** Persist the calibrated statistic and use it for the decision.
```python
# document_check.run, before the conditional UPDATE
top_share = max((float(d["ty_le"]) for d in raw.get("do_an_trung", [])), default=0.0)
# store it: new column ket_qua_kiem_tra_trung_lap.ty_le_nguon_cao_nhat DECIMAL(5,2)
#   (Alembic 0011), and/or expose a boolean vuot_nguong = top_share >= nguong_ap_dung
```
```tsx
// CheckPanel.tsx / ScoringPage.tsx
const overThreshold = data.vuot_nguong   // computed server-side with >=
```
If a schema change is not acceptable, recalibrate `NGUONG_TAI_LIEU` against `ty_le_tong` and document that choice. Either way, change the operator to `>=`.

### CR-02: A single global encoder lock and whole-document batches block every other request; real reports time out (measured)

**File:** `ai-service/app/embedding.py:303-321`, `ai-service/app/pipeline.py:128, 342`, `backend/app/core/config.py:37-39`, `backend/app/services/ai_client.py:250`

**Issue:** `Encoder.encode` holds `self._lock` for the whole batch. `score_document` sends every sentence of the document as one batch. `ingest_many` does the same while also holding `_WRITE_LOCK`.

Measured on the running stack, from inside `ntma-api-1`:
- A 349 594-character text (2 226 sentences, about the size of a 100-page report) → `/check-document` took **32.5 s**. The Web API's `AI_DOCUMENT_TIMEOUT_SECONDS` is 24 s, so these checks always end in **LOI**. "Kiểm tra lại" repeats the same timeout every time.
- `/check-title` sent 2 s into that run, with the Web API's own timeout (read 4 s, connect 2 s) → **`ReadTimeout` after 4.01 s**. `kiem_tra_ten` then saves LOI for the topic submission.
- The AI service keeps working after the client gives up (there is no cancellation). Each retry queues another ~30 s of encoding.
- After a successful check, `ingest_document` encodes the **same** sentences again (another ~30 s of lock hold, also under `_WRITE_LOCK`). That blocks title checks again, and with queueing it can exceed the 60 s ingest timeout (see WR-06).

NFR-09 (P95 3.84 s) was measured on seed documents of 9–23 k characters, about ten times smaller than a real báo cáo cuối.

**Fix:** Combine these changes:
- Encode in sub-batches and take the lock per sub-batch, so short requests can interleave:
  ```python
  def encode(self, texts):
      out = []
      for i in range(0, len(texts), 64):
          with self._lock:
              out.append(self._model.encode(prepared[i:i+64], ...))
      self.encode_calls += 1  # keep NFR-11 accounting per logical call
  ```
- Scale the document timeout with size, or make `/check-document` asynchronous (job id + poll). The Web API already polls through `ket_qua` and has a 300 s `DOCUMENT_CHECK_TIMEOUT_SECONDS`.
- Reuse the check's vectors for the following ingest (cache by `ref_id` + text hash), so each document is encoded once.
- Add a regression measurement to `ai-nfr.sh` with a document of about 300 k characters, plus one concurrent title check.

### CR-03: Chunking runs in quadratic time on student-controlled text, enabling a CPU denial of service (measured)

**File:** `ai-service/app/nlp/chunking.py:60-63, 89-102, 105-115`

**Issue:**
- `_pack` recomputes `_n(candidate)` over the whole growing string for every part. When the parts contain no syllables (e.g. `"- , - , - , …"`), the candidate never reaches `MAX_SYLLABLES` and grows without limit.
- `_hard_split` has the same problem with syllable-free "words".
- `_is_abbreviation` copies `stream[:punct_start]` for **every** sentence boundary.

Measured locally:
- `"Hệ thống "*130 + "- , "*n` → 21 KB 0.52 s, 41 KB 2.07 s, **81 KB 8.25 s**. Each doubling of input costs about 4×, which is about **85 min** at the allowed `MAX_TEXT_CHARS = 2_000_000`.
- `"X. "*n` (boundary copying) → 240 KB 0.84 s, also quadratic.

This input is an uploaded DOCX (the backend does not cap extracted text), so **any SINH_VIEN** can pin a threadpool thread at 100 % CPU for more than an hour per upload and per "Kiểm tra lại". The same code runs inside `_WRITE_LOCK` during ingest (`pipeline.py:115`), which would stall every ingest.

**Fix:**
```python
def _pack(parts, sep):
    pieces, cur, cur_n = [], [], 0
    for part in parts:
        n = _n(part)
        if cur and cur_n + n > MAX_SYLLABLES:
            pieces.append(sep.join(cur)); cur, cur_n = [], 0
        cur.append(part); cur_n += n
    if cur: pieces.append(sep.join(cur))
    return pieces
# _hard_split: count syllables incrementally, and also cut on character length (e.g. 2000 chars)
# _is_abbreviation: token = stream[stream.rfind(" ", 0, punct_start) + 1 : punct_start].casefold()
```
Also enforce a hard character cap per sentence and per document in the AI service. Cap `noi_dung_trich_xuat` in the backend at the AI limit (see WR-05).

### CR-04: Boilerplate stripping can be abused to exclude any content from the check (verified)

**File:** `ai-service/app/nlp/boilerplate.py:39-48, 149-157`; `backend/app/services/document_check.py:198-229`

**Issue:** A short line matching `_SECTION_RE` (for example "Phụ lục", "Tài liệu tham khảo", "Lời cảm ơn") switches `in_section = True`. Every following line is then dropped until the next major heading (`CHƯƠNG n`, `MỞ ĐẦU`, `KẾT LUẬN`).

A student can add one "Phụ lục" line right under each `CHƯƠNG` heading, and the whole chapter disappears from the check. Verified: a 7-line document with two chapters of copied prose → `strip_boilerplate(...)` returned `[]` with `removed = 7`. The result is 0 %, shown as "Dưới ngưỡng cảnh báo".

The AI service does return `so_doan` and `so_doan_loai_tru`, but `document_check.run` throws them away, so the GVHD has no sign that 90 %+ of the text was never checked. The ALL-CAPS rule (≤ 20 syllables) and the repeated-line rule (≥ 3 occurrences) are smaller variants of the same bypass.

**Fix:**
- Only honour section-skip headings in front matter (before the first `CHƯƠNG` / `MỞ ĐẦU`) and back matter (after `KẾT LUẬN`). Never honour them between two `CHƯƠNG` headings.
- Cap how much a single skipped section can remove (e.g. ≤ 15 % of the lines) before it stops skipping.
- Persist `so_doan` and `so_doan_loai_tru` in `ket_qua_kiem_tra_trung_lap`, show them on MH-09/MH-14, and flag the result when the removed share is above a limit (e.g. > 40 %).

## Warnings

### WR-01: The embedding model is not pinned to a revision, and `ten_model` does not include one

**File:** `ai-service/app/embedding.py:245-249, 291`, `ai-service/app/download_model.py:85`

**Issue:** `SentenceTransformer("bkai-foundation-models/vietnamese-bi-encoder")` downloads whatever is on `main` at first start (new host, `ai-models` volume removed, `download_model`). Embeddings are keyed only by `ten_model = <repo id>`.

If the upstream repo changes:
- `rebuild` still treats the old stored vectors as compatible, because the name and `so_chieu` match.
- New queries and ingests use the new weights.

Cosine scores between the two vector spaces are meaningless, and the calibrated thresholds (67.8 / 67.7) silently stop applying. Nothing detects this.

**Fix:** Add `revision: str` (commit SHA) to `Profile`, pass `revision=` to `SentenceTransformer`, and set `self.name = f"{model}@{revision[:12]}"`. A model change then shows up as `thieu_embedding > 0`, and `/reindex` repairs it.

### WR-02: The MinHash matrix is copied on every check while holding `index.lock` (memory and lock-hold risk as the corpus grows)

**File:** `ai-service/app/pipeline.py:348-373`, `ai-service/app/minhash.py:33`

**Issue:**
- `part.mh_matrix[allowed]` makes a full copy of the N×128 uint64 matrix on every `/check-document`. At a corpus of a few hundred full reports (~450 k sentences) that is about 460 MB.
- `jaccard_many` then allocates an N×128 boolean temporary for each query sentence.
- All of this happens inside `with index.lock`, which also blocks `check_title`'s `index.search`.

With `mem_limit: 2g` and ~0.8–1 GB already used by the model, a realistic archive growth leads to OOM-kills during checks.

**Fix:** Do not copy the matrix. Compute on `part.mh_matrix`, then mask out excluded rows (`jac[~allowed] = -1`), in row blocks. Better, use `datasketch.MinHashLSH` as a candidate filter. Take a snapshot reference to the arrays under the lock and do the scoring outside it; the arrays are replaced, never mutated in place.

### WR-03: The AI database account has ALL PRIVILEGES from any host, and the runtime process uses it for DDL

**File:** `deploy/mysql/init-thesis-ai.sh:24-26`, `ai-service/docker-entrypoint.sh:9`

**Issue:** `'thesis_ai'@'%'` gets `ALL PRIVILEGES ON thesis_ai.*` (DROP, ALTER, CREATE, TRIGGER, EVENT, LOCK …). The same credentials run `alembic upgrade head` and then serve requests. The AI service processes untrusted document text, so any code-execution bug in that parsing stack gets DDL/DROP on the schema.

**Fix:** Use two accounts:
- `thesis_ai_migrate` with DDL, used only by the entrypoint's `alembic upgrade`.
- `thesis_ai` with `SELECT, INSERT, UPDATE, DELETE ON thesis_ai.*` for runtime.

Also restrict the host to the compose subnet (`'thesis_ai'@'172.28.238.%'`).

### WR-04: Deletes and archiving never reach the AI index; stale and duplicate title entries use up the top-k

**File:** `backend/app/services/archive.py:341-345`, `backend/app/services/title_check.py:121-125`, `ai-service/app/pipeline.py:203-221`

**Issue:**
- `archive.delete` removes the `do_an_kho` row but leaves its ARCHIVE vector. `purge` exists but only e2e cleanup calls it.
- An archived thesis stays indexed as both TOPIC and ARCHIVE.

The AI filters by `nguong` and then cuts to `top_k`. The Web API only over-fetches ×2 (10) and then drops deleted refs and merges TOPIC+ARCHIVE pairs. When there are more than 5 near-duplicate archived or deleted titles, real matches are pushed out of the 10 slots and the user sees fewer than `TITLE_CHECK_TOP_K` results. The comment in `_resolve_match` ("chỉ mục AI chưa có /delete") is out of date: REPLACE-with-empty is the delete.

**Fix:** In `delete_record`, schedule `get_ai_client(db).ingest(kho_id, "ARCHIVE", "")` as a background task. When a thesis is archived (`insert_from_defense`), purge its TOPIC entry, or keep it and raise the over-fetch to cover the duplicates.

### WR-05: Extracted text is never checked against the AI service's limits, so large documents end in permanent LOI with a recheck button that cannot succeed

**File:** `backend/app/services/document_check.py:176-194`, `backend/app/services/documents.py:130-168`, `ai-service/app/schemas.py:9,46`

**Issue:** The Web API accepts DOCX `word/document.xml` up to 15 MB and PDFs up to 20 MB, and stores the whole extracted text. The AI rejects `text` over 2 000 000 characters (422) and bodies over 8 MiB (413). Such a document always ends in LOI, while `CheckPanel` keeps offering "Kiểm tra lại" (`request_recheck` only refuses when there is no text). The later `ingest_document` also fails every time, logged only.

**Fix:** Before calling the AI, reject or truncate at the AI limit. Better, validate at upload with a clear 422 message ("Tài liệu quá dài để kiểm tra trùng lặp"). Hide "Kiểm tra lại" for this failure reason.

### WR-06: Failed document ingests are silent and never retried; later copies go undetected

**File:** `backend/app/services/ai_index.py:69-93`, `backend/app/services/document_check.py:250-254`

**Issue:** `ingest_document` only logs a warning on failure (timeout, AI restart, 413). Unlike `do_an_kho.trang_thai_index`, a DOCUMENT has no "not indexed" state. A document that misses ingest is never in the corpus, so a later verbatim copy of it scores 0 %, and nothing reports it. CR-02's queueing makes the 60 s `AI_INGEST_TIMEOUT_SECONDS` realistic to hit.

**Fix:** Add a `trang_thai_index` (or `da_index_luc`) column to `tai_lieu_do_an`. Set it on a successful ingest. Make `backfill --loai DOCUMENT` or a periodic job retry only the rows that are not indexed. Show the count in the Bộ môn dashboard or the `/health` check.

## Info

### IN-01: The API key is a plain `str`, so a validation error can echo it

**File:** `ai-service/app/core/config.py:20, 34-38`, `backend/app/core/config.py:34, 69-70`
**Issue:** A pydantic `ValidationError` includes `input_value=...`. A mis-configured key (e.g. a real 31-character secret) ends up in the container logs at startup.
**Fix:** Declare `AI_API_KEY: SecretStr` and use `.get_secret_value()` in `security.py` and `ai_client.py`.

### IN-02: The threshold screen can never save when a row is missing; the service's insert path cannot be reached

**File:** `backend/app/services/thresholds.py:83-86, 118-123`, `frontend/src/features/thresholds/ThresholdSettingsPage.tsx:108`
**Issue:** `list_thresholds` skips missing rows, so the form has no field for them. `ThresholdUpdate` requires all three values, so PUT always returns 422. The "Thêm dòng nếu CSDL chưa có" branch is dead code.
**Fix:** For a missing row, return the definition with `gia_tri = gia_tri_de_xuat` (and `thoi_diem_cap_nhat = None`).

### IN-03: Integer and length inputs are not bounded

**File:** `ai-service/app/schemas.py:16,19,45,51`, `ai-service/app/pipeline.py:344-345`, `backend/app/core/config.py:40`, `backend/app/services/title_check.py:124`
**Issue:**
- `id`, `ref_id` and the `loai_tru` items have no upper bound. Values above int64 give an `OverflowError` in `np.fromiter` or the MySQL BIGINT column, which surfaces as a 500.
- A TOPIC/ARCHIVE `text` may be up to 2 000 000 characters, but it becomes one `chunk.noi_dung` TEXT row (64 KB), which also gives a 500.
- `TITLE_CHECK_TOP_K * 2` is not checked against the AI's `le=20`, so setting it to 11 or more makes every title check LOI.
**Fix:** Add `le=2**63-1` (and `le=` limits on the list items), a title `max_length` of about 1000 for TOPIC/ARCHIVE, and a `TITLE_CHECK_TOP_K` validator (1–10).

### IN-04: `/health` is unauthenticated and runs a full-table `NOT IN` count on every call

**File:** `ai-service/app/main.py:62-82`, `ai-service/app/pipeline.py:496-499`
**Issue:** Two healthchecks run every 10–15 s, each running `COUNT(chunk) WHERE id NOT IN (SELECT chunk_id FROM embedding …)`. The response also exposes the model name and corpus sizes to anything on the network, without a key. This is minor because the service is internal.
**Fix:** Cache `thieu_embedding` and refresh it after ingest/reindex, or at most every 60 s. Keep only `status` public, and put the details behind the key.

### IN-05: `rebuild` and `count_missing` count differently, and `/reindex` cannot fix rows with a wrong dimension

**File:** `ai-service/app/pipeline.py:254-256, 275, 496-499, 506-509`
**Issue:** `rebuild` counts rows whose `so_chieu` does not match as missing. `count_missing` and `reembed_missing` treat them as present, so `/health` disagrees with the startup log, and those chunks are never re-embedded or loaded.
**Fix:** Filter on `Embedding.so_chieu == encoder.dim` in both helpers, and delete or replace mismatched rows in `reembed_missing`.

### IN-06: The verbatim threshold is hard-coded in the frontend

**File:** `frontend/src/features/thresholds/ThresholdSettingsPage.tsx:14`
**Issue:** `'88.7%'` is a copy of `NGUONG_NGUYEN_VAN_MAC_DINH`. It will silently drift after a recalibration.
**Fix:** Return it from `/api/thresholds` as a read-only item, or read it from the AI `/health` response.

### IN-07: The application code in the AI image can be modified by the runtime user

**File:** `ai-service/Dockerfile:23-27`, `deploy/docker-compose.yml:112-142`
**Issue:** `COPY --chown=appuser:appuser . .` means an attacker with code execution can rewrite `/app/app/*.py`. The change survives container restarts, because the writable layer is kept until the image is rebuilt.
**Fix:** Copy the source as root:root (the venv can stay owned by appuser). Add `read_only: true` with a `tmpfs: /tmp`, and keep `/models` as the only writable volume.

---

_Reviewed: 2026-09-28_
_Reviewer: Developer (code-reviewer)_
_Depth: standard_
