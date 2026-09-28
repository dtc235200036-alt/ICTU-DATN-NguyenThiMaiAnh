---
phase: 04-ai-similarity-service
fixed_at: 2026-09-28T10:30:00Z
review_path: .planning/phases/04-ai-similarity-service/04-REVIEW.md
iteration: 1
findings_in_scope: 17
fixed: 16
skipped: 1
status: partial
---

# Phase 4: Code Review Fix Report

**Fixed at:** 2026-09-28
**Source review:** .planning/phases/04-ai-similarity-service/04-REVIEW.md
**Iteration:** 1
**Scope:** all 4 Critical + 6 Warning, plus Info where trivial and safe. The same strict `>` in `ScoringPage.tsx:48` was fixed together with CR-01.

**Summary:**
- Findings in scope: 17 (CR-01..04, WR-01..06, IN-01..07)
- Fixed: 16 (IN-04 is partly fixed, see below)
- Skipped: 1 (IN-06)

**Where the work ran.** At the orchestrator's instruction ("work on main, no other agent is running") every edit and commit was made directly on `main` in the main checkout. No worktree was created. All gates ran in that checkout against the rebuilt compose stack `ntma`, so the numbers can be reproduced from this tree.

## Important correction to CR-01 (read first)

The review said P19 (same field, held-out) has 23.96 % total but "0 % per source", and would only be flagged because of the `ty_le_tong` rule. That is only true for the share to the pair's **own** source A. The calibration scored each pair with `do_an_trung[A]`, and A is known only in the labelled dataset. At runtime the Web API cannot know A, so the only rule it can apply is the **highest per-source share**.

Measured on the real stack, P19-B scores **22.81 % against P15-A**, a different healthcare thesis. So P19 is flagged under both the old rule and the new one.

What was done about it:
- CR-01 is implemented as the per-source rule, `max(do_an_trung) >= nguong_ap_dung`. This is the runtime version of the calibrated statistic. It correctly handles the case where matches are spread over many sources: P21 has 6.0 % total but only 1.51 % against any single thesis.
- `calibrate.py evaluate` now scores pairs with that runtime rule and keeps the share to A as a diagnostic column. The thresholds were **not** refit and `--apply` was not used. The re-run's scores are identical to 04-04 for all 25 pairs:
  - tuning split: 17/17;
  - **held-out split: 7/8 = 0.875**, which still passes G3 (≥ 0.85), with P19 as a documented same-domain false positive;
  - G1 and G2 pass;
  - under the runtime statistic, 10.4 still separates the tuning split (largest negative 3.69, smallest positive 20.79).
- The chương 4 page `03-hieu-chinh-nguong.md` was regenerated and no longer claims "P19 not flagged". The deploy README and data dictionary wording were corrected to match.
- The first CR-01 commit message (df366cb) still repeats the review's P19 premise. The follow-up commit 29b8ef7 corrects it.
- No seed pair has total ≥ 10.4 with max share < 10.4, so e2e-ai proves the per-source rule on the real AI a different way. It temporarily sets `NGUONG_TAI_LIEU` to 3.75 %, which sits between P21-B's highest per-source share and its total, then resubmits P21-B: total 6.0 % ≥ threshold, highest share 1.51 % < threshold, result "Dưới ngưỡng cảnh báo". The script trap then restores the thresholds.
- **Decision left to the user:** whether to refit `NGUONG_TAI_LIEU` directly on the runtime statistic (the tuning midpoint would be ≈ 12.2) or accept P19 as a known false positive. Either choice still flags P19.

## Fixed Issues

### CR-01: Document warning used `ty_le_tong`; the calibrated per-source share was discarded

**Files modified:**
- `backend/alembic/versions/0012_ty_le_nguon.py`
- `backend/app/{models/trung_lap.py, schemas/documents.py, services/document_check.py, services/thresholds.py}`
- `backend/tests/test_ai_document_flow.py`
- `frontend/src/features/documents/{api.ts, CheckPanel.tsx, CheckDetailPage.tsx}`, `frontend/src/features/defense/ScoringPage.tsx`
- `deploy/e2e-ai.sh`, `deploy/README.md`
- ERD, class diagram, data dictionary and UI design docs
- `ai-service/calibration/{calibrate.py, ket-qua-chi-tiet.json}`, `docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md`

**Commits:** df366cb, 29b8ef7

**Applied fix:**
- Alembic 0012 adds `ket_qua_kiem_tra_trung_lap.ty_le_nguon_cao_nhat` and `chi_tiet_trung_lap.ty_le_nguon`, which holds the AI's per-source share. Old HOAN_TAT rows are backfilled with the 04-07 character-share estimate.
- The Web API now requests `top_k` 20, so every source that has a passage also has a share.
- `vuot_nguong = ty_le_nguon_cao_nhat >= nguong_ap_dung` is computed on the server and returned in CheckSummary and CheckDetail.
- MH-09, MH-14 and ScoringPage now use `vuot_nguong`, which fixes the strict `>`, and show the per-source share. `ty_le_tong` is display-only.
- MH-14 "Đồ án trùng" now reads the stored AI share.
- The threshold description on the UC0.4 screen was reworded.
- The unit test covers a 42.5 % total spread over two sources (25 / 17.5) against a 30 % threshold, and checks it is **not** flagged.

**Status:** fixed: requires human verification. This changes the decision logic and comes with the correction above.

### CR-02: Global encoder lock and whole-document batches blocked title checks; long reports timed out

**Files modified:**
- `ai-service/app/{embedding.py, pipeline.py, api.py}`, `ai-service/tests/test_document_path.py`, `ai-service/README.md`
- `backend/app/{core/config.py, services/ai_client.py}`
- `deploy/{ai-nfr.sh, e2e-ai.sh, README.md}`

**Commits:** ac1bb26, f9cfb03

**Applied fix:**
- Encoding is split into length-sorted sub-batches of 32 sentences. The model lock is held per sub-batch only.
- The lock is **FIFO**. This was added after ai-nfr caught a title check starving: `threading.Lock` let the document thread re-acquire the lock immediately after releasing it.
- `/check-document` caches its sentence vectors per `ref_id` (at most 20 000 vectors, 15 minutes). The `/ingest DOCUMENT` that follows reuses them, so submit plus index encodes once. e2e-ai asserts `encode_calls` +1.
- The Web API timeout now scales with document length: 24 s + 0.25 s per 1000 characters, capped at 240 s, which is below the 300 s stale expiry.

**Measured** with the 349 594-character text, from inside `ntma-api-1`:

| | /check-document | 5 × /check-title sent during the run |
|---|---|---|
| Before | 29.0 s (2 009 sentences), past the fixed 24 s timeout, so LOI | all ReadTimeout at 4.01 s |
| After | 40.7 s / 42.3 s (2 331 sentences; CR-04 keeps more text), inside the 111 s scaled timeout | 0.09–0.32 s |

The document is slower now only because CR-04 keeps more sentences. The encoding cost is inherent: about 17 ms per sentence, and 8 torch threads were slower on this host.

**Documented:** a report of about 100 pages exceeds the 30 s NFR-09 target, which was measured on short documents. ai-nfr has a new "NFR-09 (dài)" row: 41.7 s inside the 111.5 s timeout, with interleaved title checks at 131–353 ms.

### CR-03: Quadratic chunking on student-controlled text

**Files modified:** `ai-service/app/nlp/chunking.py`, `ai-service/tests/test_document_path.py`

**Commit:** e469312

**Applied fix:**
- Syllables are counted incrementally.
- Every piece has a character cap (MAX_CHARS 2000), and words without spaces are split by characters.
- The abbreviation check slices only the token instead of the whole prefix.

**Regression test:** five adversarial inputs of about 200 KB must each finish in under 2 s. The old code took 51.5 s on one of them.

**Output check:** on all 50 seed files, sentence output is identical to the pre-fix pipeline.

### CR-04: Boilerplate section skipping could hide whole chapters

**Files modified:**
- `ai-service/app/{nlp/boilerplate.py, pipeline.py, schemas.py}`, tests, README
- `backend/alembic/versions/0013_pham_vi_kiem_tra.py`, model, schemas, `document_check.py`, test
- `frontend/src/features/documents/{api.ts, scope.ts, CheckPanel.tsx, CheckDetailPage.tsx}`
- `deploy/{e2e-ai.sh, README.md}`, ERD, class diagram, dictionary, §3.3.5

**Commit:** 128c289

**Applied fix:**
- A section heading only triggers skipping in front matter (before the first MỞ ĐẦU / CHƯƠNG / KẾT LUẬN) or back matter (after the last one).
- One skipped section can remove at most max(40 lines, 15 %). All skipped sections together can remove at most max(80 lines, 40 %).
- An ALL-CAPS line that ends in punctuation is treated as content.
- `/check-document` returns `ty_le_loai_tru`, the percentage of characters removed. This is an additive contract field.
- Alembic 0013 stores `so_doan`, `so_doan_loai_tru` and `ty_le_loai_tru`.
- MH-09 and MH-14 show "Đã so sánh n câu · đã loại m dòng (x % nội dung)".

**Decision:** the warning threshold is **> 50 %**, not the review's 40 %. The short synthetic seed documents legitimately lose up to 45.3 % (P01-B 42.3 %), so 40 % would warn on every demo submission.

**Verification:**
- The reviewer's proof of concept now keeps every chapter sentence.
- A flat document with "Phụ lục" every 30 lines keeps at least 55 %.
- Output on the 50 seed files is byte-identical, so the calibration still holds.

### WR-01: Model not pinned to a revision

**Files modified:** `ai-service/app/{embedding.py, download_model.py}`, `ai-service/alembic/versions/0002_ten_model_revision.py`, README, dictionary

**Commit:** ba45b8b

**Applied fix:**
- `Profile.revision` pins the bake-off commits (bkai `84f9d9ada0d1…`, e5 `d12875059715…`). The value is passed as `revision=` to SentenceTransformer and to download_model.
- `ten_model` is now `repo@sha12`.
- thesis_ai Alembic 0002 relabels the existing rows. The `ai-models` volume holds exactly snapshot 84f9d9ada0d1a3c3…, so no re-encode was needed.

**Verified:** 2508 vectors loaded, `thieu_embedding` 0.

### WR-02: MinHash matrix copied on every check under `index.lock`

**File modified:** `ai-service/app/pipeline.py`

**Commit:** c0a8cd2

**Applied fix:**
- Only the FAISS search and references to the MinHash arrays are taken under the lock. The arrays are always replaced, never mutated in place.
- Jaccard now runs outside the lock over blocks of 32 768 rows, with excluded rows masked. There is no N×128 copy.
- The tie rule is unchanged, and the calibration re-run produced identical scores.

**Not done:** the review's suggested LSH candidate filter. It is not needed at the current corpus size.

### WR-03: The AI DB account had ALL PRIVILEGES from any host, and the runtime process used it for DDL

**Files modified:** `deploy/{mysql/init-thesis-ai.sh, docker-compose.yml, .env.example, e2e-ai.sh, ai-nfr.sh, README.md}`, `ai-service/{docker-entrypoint.sh, alembic/env.py}`, §3.3 connection table

**Commit:** 5e6c0ba

**Applied fix:**
- `'thesis_ai'@'172.28.238.%'` now has SELECT, INSERT, UPDATE and DELETE only.
- A new `'thesis_ai_migrate'@'172.28.238.%'` account has ALL on `thesis_ai.*`.
- The old `'thesis_ai'@'%'` account is dropped.
- A new one-shot `ai-migrate` compose service (same `ntma-ai` image) runs alembic with the DDL account. `ai` starts after it with `AI_MIGRATE_ON_START=0` and uses the DML account.
- The new secret `AI_DB_MIGRATE_PASSWORD` was appended to `deploy/.env` by `init.sh`. Its value was never read into this session.

**Verified:**
- Grants are as intended.
- From the ai container: CREATE, DROP and `thesis_core` access are DENIED, and SELECT works.
- The migrate credentials are not present in the ai container.

### WR-04: Deletes and archiving never reached the AI index

**Files modified:** `backend/app/services/{ai_index.py, archive.py, title_check.py}`, `backend/app/routers/{archive.py, defense.py}`, tests, deploy README

**Commit:** 2d2810a

**Applied fix:**
- `DELETE /api/archive/{id}` schedules removal of the ARCHIVE vector.
- Finalizing a defense indexes the new ARCHIVE record and then removes the topic's TOPIC vector.
- Both are background tasks that only log on failure. Stale comments were updated.

**Tests:** assert the ARCHIVE removal on delete, and the ARCHIVE ingest plus TOPIC removal on finalize.

### WR-05: Extracted text was never checked against the AI limits

**Files modified:** `backend/app/{core/config.py, schemas/documents.py, services/documents.py, services/document_check.py, services/ai_index.py}`, test, `frontend/src/features/{documents/api.ts, documents/CheckPanel.tsx, defense/ScoringPage.tsx, defense/CommitteePage.tsx}`, deploy README

**Commit:** 36b76d9

**Applied fix:**
- New setting `AI_DOCUMENT_MAX_CHARS` = 800 000. This is under the AI limit, and 800 000 characters fits inside the scaled timeout (224 s).
- `run` marks such a check LOI without calling the AI.
- `recheck` returns 409 "Tài liệu quá dài để kiểm tra trùng lặp tự động (n ký tự, tối đa m) — hãy nộp bản đã bỏ phụ lục/mã nguồn dài".
- `DocumentOut.qua_dai_kiem_tra` makes the UI show the reason and hide every "Kiểm tra lại" button.
- Ingest and backfill skip these documents.

**Decision:** the upload itself still succeeds, because UC0.7 E1 says the workflow must never be blocked. The alternative was the review's upload-time 422.

### WR-06: Failed document ingests were silent and never retried

**Files modified:** `backend/alembic/versions/0014_da_index_luc.py`, `models/de_cuong.py`, `services/ai_index.py`, `schemas/dashboard.py`, `services/dashboard.py`, test, `frontend/src/features/dashboard/{api.ts, BmDashboard.tsx}`, ERD, class diagram, dictionary, deploy README

**Commit:** 6149c31

**Applied fix:**
- `tai_lieu_do_an.da_index_luc` is stamped on every successful ingest.
- After each successful ingest, up to 3 pending documents are retried. Pending means a HOAN_TAT check (or no check at all), text within the limit, and `da_index_luc` NULL.
- `backfill --loai DOCUMENT --chua-index` retries only the pending rows and prints the count.
- The Bộ môn dashboard shows "Tài liệu chưa vào chỉ mục AI" when the count is above 0.

**Test:** a document whose ingest failed is healed by the next ingest.

**Final stack:** 0 pending documents.

### IN-01: API key could be echoed in validation errors

**Files modified:** `ai-service/app/core/{config.py, security.py}`, `backend/app/{core/config.py, services/ai_client.py}`

**Commit:** 0953bc6

**Applied fix:** `AI_API_KEY` is now a `SecretStr`, and both Settings classes set `hide_input_in_errors=True`. Verified: the error for a short key no longer contains the key.

### IN-02: Threshold screen could never save when a row was missing

**Files modified:** `backend/app/{schemas/thresholds.py, services/thresholds.py}`, `frontend/src/features/thresholds/{api.ts, ThresholdSettingsPage.tsx}`

**Commit:** e74efdd

**Applied fix:** a missing row is now returned with its calibrated default and `thoi_diem_cap_nhat: null`. The form shows it, and saving inserts it.

### IN-03: Unbounded integer and length inputs

**Files modified:** `ai-service/app/schemas.py`, `ai-service/README.md`, `backend/app/core/config.py`

**Commit:** 3434cc1

**Applied fix:**
- ids, `ref_id` and `loai_tru` items must be ≤ 2⁶³−1.
- TOPIC/ARCHIVE text is limited to 1000 characters.
- `TITLE_CHECK_TOP_K` must be in 1..10.

### IN-04: `/health` ran a full-table count on every call and exposed details without a key

**Files modified:** `ai-service/app/{main.py, api.py}`

**Commit:** e819903

**Applied fix:** `thieu_embedding` is cached for 60 s, and `/reindex` refreshes it immediately.

**Partly fixed:** the detail fields stay unauthenticated on purpose. seed-ai, e2e-ai and ai-nfr read them without the key, and the port is internal-only.

### IN-05: `rebuild` and `count_missing` disagreed about wrong-dimension rows

**File modified:** `ai-service/app/pipeline.py`

**Commit:** 36d5dcd

**Applied fix:** one criterion everywhere: `ten_model` matches and `so_chieu == encoder.dim`. This applies to `count_missing`, `reembed_missing` and the ingest "unchanged" check. `reembed_missing` deletes this model's rows with the wrong dimension before re-inserting.

### IN-07: Runtime user could modify the AI image's code

**Files modified:** `ai-service/Dockerfile`, `deploy/docker-compose.yml`, `deploy/README.md`

**Commit:** 19396d0

**Applied fix:** the source is owned by root, and appuser owns only `.venv` and `/models`. The compose `ai` service now has `read_only: true` and a tmpfs on `/tmp`.

**Verified:** writes under `/app` fail, `/tmp` is writable, and the model and underthesea work.

## Skipped Issues

### IN-06: Verbatim threshold hard-coded in the frontend

**File:** `frontend/src/features/thresholds/ThresholdSettingsPage.tsx:14`

**Reason:** not trivial. Removing the literal needs a new field in the `/api/thresholds` contract backed by the AI `/health` (a synchronous cross-service read on a settings page), or a new backend-owned setting that the Web API then sends to the AI. Both are contract changes and outside "trivial and safe". The value (88.7) is documented as a read-only technical parameter, and the recalibration procedure in the ai-service README lists where to update it.

**Original issue:** `'88.7%'` duplicates `NGUONG_NGUYEN_VAN_MAC_DINH` and will drift silently after a recalibration.

## Verification (final tree, rebuilt stack, main checkout)

| Gate | Result |
|---|---|
| `docker compose up -d --build --wait` | all healthy: ai-db-init and ai-migrate exited 0; ai, api, apache and mysql healthy |
| thesis_core alembic | 0014 (head); thesis_ai 0002 |
| `tools/check-erd-db.py` | OK |
| check-docs class-erd / links / render / pi-tags | OK |
| backend `pytest` | 53 passed |
| ai-service `pytest` | 8 passed (+3: CR-03 timing, CR-04 hiding, CR-02 reuse) |
| `npm run build` | OK |
| `seed-ai.sh` ×3 | idempotent: 300 / 25 / 25, 0 failed, 0 pending documents, index 300 / 2208 |
| `smoke-test.sh` | all passed (run twice) |
| `e2e-uc1.sh` / `e2e-uc2-5.sh` | OK / OK |
| `e2e-ai.sh` | OK (run twice, the second on the final image). Details below. |
| `ai-nfr.sh --report` | all pass (not run in parallel with e2e-ai). Details below. |
| calibration `evaluate` (runtime rule) | G1 / G2 / G3 pass; tuning 17/17, held-out 7/8 (P19 known false positive) |
| Leftovers | 0 K96–K99 cohorts; 25 documents = 25 files; thresholds 67.70 / 10.40 / 67.80 with editor NULL; `ten_model` `…@84f9d9ada0d1`, `thieu_embedding` 0 |

**e2e-ai.sh:**
- Runtime DB user denied on `thesis_core`, CREATE and DROP.
- P01-B at 50.3 % with `vuot_nguong` true, a per-source share equal to MH-14, and scope "61 câu, loại 112 dòng (42.29 %)".
- Submit plus index costs 1 encode.
- P21-B: 6.0 % total / 1.51 % per source, not flagged.
- Per-source rule proof at a temporary 3.75 % threshold passes.
- Resubmission does not match its own topic.

**ai-nfr.sh:**
- NFR-08 P95 52 ms.
- NFR-09 P95 3.02 s, 20/20 HOAN_TAT.
- NFR-10 max 0.058 s.
- Long document: 350 000 chars in 41.7 s, inside a 111.5 s timeout, with interleaved title checks at 131–353 ms.
- NFR-11 +1.
- Memory peak 720 MiB.

**Chương 4 page numbers updated:**
- `docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md` was regenerated by ai-nfr.
- `03-hieu-chinh-nguong.md` was regenerated by calibrate evaluate.

Per instruction, `.planning/config.json` was never staged and no report DOCX or slides were built.

---

_Fixed: 2026-09-28_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
