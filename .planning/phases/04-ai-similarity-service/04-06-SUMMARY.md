---
phase: 04-ai-similarity-service
plan: 06
status: complete
subsystem: ai-integration
tags: [document-check, loai_tru, push-on-write, seed, DATA-03, SC2, NFR-07, NFR-08, NFR-09, NFR-10, NFR-11, AISV-04, AISV-06]
requires:
  - "04-05: AiClientHttp.check_document(ref_id, text, top_k, nguong_doan, loai_tru), ingest, ai_index purge/backfill CLI, seed-ai.sh import, e2e-ai (K97)"
  - "04-04: NGUONG_DOAN_TRUNG 67.7 / NGUONG_TAI_LIEU 10.4 (Alembic 0010), ket-qua-chi-tiet.json"
  - "04-02: seed-data/manifest.json cap[] A/B + tai-lieu/P01..P25"
  - "03 review fixes: WR-05 stamped run(), WR-06 loai_nguon/nguon_id (0011), WR-07 doan_trung_an"
provides:
  - "document_check.run: real /check-document with nguong_doan + same-topic loai_tru; signal in vi_tri; ingest DOCUMENT after HOAN_TAT"
  - "ai_index.ingest_document + backfill DOCUMENT; TOPIC backfill skips archived topics"
  - "documents.validate_bytes (UploadFile-free validation)"
  - "app.seed_ai_corpus: 25 past-cohort theses with BAO_CAO_CUOI reports, linked to IMPORT archive rows"
  - "deploy/ai-nfr.sh + docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md"
  - "e2e-ai section ai_document (SC2)"
affects: [04-07, 05]
tech-stack:
  added: []
  patterns:
    - "Check first, then index: a document can never match itself; ingest failure is log-only"
    - "Seed tooling writes through services (validate_bytes + documents.store), no new endpoint"
    - "Cleanup loops that call `docker compose exec` redirect stdin from /dev/null"
key-files:
  created:
    - backend/app/seed_ai_corpus.py
    - backend/tests/test_ai_document_flow.py
    - deploy/ai-nfr.sh
    - docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md
  modified:
    - backend/app/services/document_check.py
    - backend/app/services/ai_index.py
    - backend/app/services/documents.py
    - backend/tests/test_outline_flow.py
    - deploy/docker-compose.yml
    - deploy/seed-ai.sh
    - deploy/e2e-ai.sh
    - deploy/e2e-uc2-5.sh
decisions:
  - "loai_tru = ids of every DE_CUONG/BAO_CAO_CUOI tai_lieu_do_an of the same de_tai, including the version under check"
  - "vi_tri = '{Câu a–b} · trùng nguyên văn|trùng ngữ nghĩa' (≤ 50 chars); no suffix when tin_hieu is absent (stub)"
  - "top_k for /check-document is a module constant (5) in document_check — no new setting"
  - "seed_ai_corpus is idempotent by 'IMPORT archive row already linked to a de_tai that has a BAO_CAO_CUOI'; đợt matched by BOTH ten_dot 'Dữ liệu lịch sử {khoa}' and khoa, DA_DONG, nam_hoc/dates derived from the khóa"
  - "AISV-05 left Pending in REQUIREMENTS: passages are shown beside their source, but the highlight marks are plan 04-07"
metrics:
  duration: "~27 min"
  completed: 2026-09-28
estimate:
  tokens: 130000
  tasks: 2
actuals:
  tokens: 26100   # chars/4 over git diff plan_head_before..plan_head_after (includes the concurrent 314248f .planning commit)
  tasks: 2
  commits: 5      # MEASURED rev-list; includes 314248f (concurrent Phase 3 verifier, .planning only) — own commits: 4
plan_head_before: d34478dbb45424411c438ec17d8dd0f676583118
plan_head_after: 1b3d7560840ce9d147e5fdf3a499cf9e3f700cb4
---

# Phase 4 Plan 06: Real document check + DATA-03 corpus + NFR Summary

**Submitting an outline now runs the real bkai check against the 25 seeded past-cohort theses and earlier submissions. The verbatim copy P01-B scores 50.3% against "Phát triển mô hình thống kê điểm số … Metabase (K21)" with 7 verbatim passages beside their source text and no template boilerplate. The unrelated P21-B scores 6.0%, below the 10.4% threshold. On the dev host, submit→HOAN_TAT has a P95 of 3.84 s.**

## Tasks

| # | Task | Commit | Result |
|---|------|--------|--------|
| 1 | RED contract test (+ `_boom(**kw)`) | 7d04c86 | failed on `nguong_doan None != 80.0` |
| 1 | Real-AI document check, ingest after check, seed_ai_corpus, compose mount, seed-ai, e2e ai_document, uc2-5 purge | 6068f65 | 52 backend tests; seed-ai ×2 idempotent; e2e-ai / uc2-5 / uc1 / smoke / check-erd-db green |
| 2 | deploy/ai-nfr.sh + chương 4 page | 8b07866 | every NFR met |
| — | [Rule 1] cleanup loops deleted only the first file | 1b3d756 | 0 leftover files after e2e-ai, uc2-5 and ai-nfr |

## Behaviour as implemented

**`document_check.run(ket_qua_id)`.** The WR-05 stamp and transaction structure is unchanged.

1. The run reads the active `NGUONG_DOAN_TRUNG`, or `None` when the row is missing. It also builds `loai_tru`: every DE_CUONG and BAO_CAO_CUOI id of `doc.de_tai_id`, including the document itself. Then it commits the read transaction.
2. It calls `check_document(doc.id, text, 5, nguong_doan=…, loai_tru=…)`.
3. Each passage stores `vi_tri` with its signal suffix, together with WR-06 `loai_nguon`/`nguon_id`. A real AI item has no `loai`, so it is stored as DOCUMENT.
4. The stamped UPDATE sets `HOAN_TAT` and commits. Only after that does it call `ai_index.ingest_document(doc.id)`, which uses its own session and swallows every error with a warning log.
   - The `LOI` path does not ingest.
   - A stale or replaced run (`rowcount != 1`) does not ingest.
   - A document with missing text does not ingest.

**Test.** `test_ai_document_flow` checks the following:
- **Payload:** `nguong_doan` equals the DB row, and `loai_tru ⊇ {v1, v2}` but excludes the other topic's document.
- **Ingest:** exactly one `ingest(v2, "DOCUMENT", same text)` call, after the check.
- **`vi_tri`:** `"Câu 3–4 · trùng nguyên văn"` and `"Câu 7 · trùng ngữ nghĩa"`.
- **Review item (WR-06 regression):** the `tai_lieu_do_an` id is equal to a `do_an_kho` id. The DOCUMENT passage is labelled `"{topic} (KTEST)"` and the ARCHIVE passage `"Bản ghi kho … (K20)"`.
- **Failures:** if ingest raises, the result is still `HOAN_TAT`. If the check raises, the result is `LOI` and there is no ingest.

## Seed CLI output (`python -m app.seed_ai_corpus --data /seed-data`)

- **First run:** `OK: 25 đồ án nguồn (mới 25, đã có 0)`.
- **Second run:** `mới 0, đã có 25`. The de_tai, dot_do_an, tai_lieu_do_an and linked-kho counts stayed at 25 / 6 / 25 / 25.

| Khóa | Đợt "Dữ liệu lịch sử" id | Pairs (tai_lieu_do_an id) |
|---|---:|---|
| K21 | 66 | P01 #108, P09 #116, P17 #124, P18 #125, P22 #129 |
| K22 | 67 | P02 #109, P07 #114, P14 #121, P16 #123, P25 #132 |
| K18 | 68 | P03 #110, P10 #117, P11 #118, P19 #126, P24 #131 |
| K19 | 69 | P04 #111, P06 #113, P13 #120, P20 #127, P23 #130 |
| K20 | 70 | P05 #112, P08 #115, P12 #119, P15 #122, P21 #128 |

- Backfill printed TOPIC 0, ARCHIVE 300 and DOCUMENT 25, with 0 failures.
- `/health` reports `index_size_tieu_de` 300 and `index_size_tai_lieu` **2208**. That is the same sentence count as the 04-04 calibration corpus.
- seed-ai.sh ends by requiring exactly 25 archive rows that link to a BAO_CAO_CUOI, and an index size above 0.

## SC2 e2e (`deploy/e2e-ai.sh` → `ai_document`)

| Step | Result |
|---|---|
| Bộ môn approves the K97 topics with GV023 as GVHD | DTC225200095's topic (from ai_index) and DTC225200096's new topic both reached DA_PHAN_CONG |
| DTC225200095 submits P01-B.pdf (CHEP_NGUYEN_VAN) | 202 in 0.065 s. **HOAN_TAT within about 1 s: 50.3% ≥ 10.4%.** 7 passages, all verbatim. Top thesis is "Phát triển mô hình thống kê điểm số của người học tại trường THCS Chu Văn An sử dụng Metabase (K21)". Every passage has both the submitted text and the source text. No LỜI CAM ĐOAN, MỤC LỤC, TÀI LIỆU THAM KHẢO or running header appears. |
| GV023 opens the review endpoint and the check detail | Same rate, same top theses, same passages |
| DTC225200096 submits P21-B.pdf (KHONG_LIEN_QUAN) | **6.0% < 10.4%** |
| GV023 asks for changes; the student resubmits P01-B.pdf | HOAN_TAT 50.3%. There is no label for the student's own topic, and the source is still K21 A (loai_tru works) |
| Cleanup | DOCUMENT, TOPIC and ARCHIVE vectors purged. Files and K97 rows deleted. The index is back to 300 / 2208 with 25 files on disk. |

## NFR measurements (dev host: 16 logical CPUs, i5-12500H, 15.3 GiB shared; bkai, TORCH_THREADS 4)

These come from the final run, which is the numbers now on the chương 4 page (08:19Z).

| NFR | Target | Measured | Pass? |
|---|---|---|---|
| NFR-07 | No public route, 401 without key | Host cannot reach :8002. Missing / wrong / correct key gives 401 / 401 / 200. Apache has no route (returns the SPA with 200). The thesis_ai DB user is DENIED on thesis_core. | Pass |
| NFR-08 | Title check P95 ≤ 5 s (20 direct calls, 300 titles) | P50 44 ms, **P95 51 ms**, max 52 ms | Pass |
| NFR-09 | Submit → HOAN_TAT P95 ≤ 30 s (20 B files) | P50 3.28 s, **P95 3.84 s**, max 5.45 s. 20/20 HOAN_TAT, 0 LOI | Pass |
| NFR-10 | Submit response ≤ 2 s | P95 0.071 s, **max 0.072 s** | Pass |
| NFR-11 | 1 encode per ingest | encode_calls 298 → 299 (**+1**) | Pass |
| Memory | ai < 2048 MiB, no OOM | 756 → 764 MiB. **cgroup peak 853 MiB.** OOMKilled false | Pass |

The two earlier runs gave title P95 of 55 and 52 ms and submit→HOAN_TAT P95 of 3.57 and 3.82 s. Per-file timings and rates are in the chương 4 page.

## Reserved accounts for the 04-07 README

- **e2e-ai (K97):** bomon, DTC225200095, DTC225200096 and GV023. GV023 is now used as the GVHD in ai_document.
- **ai-nfr (K96):** bomon, DTC225200095 and GV023.
- Both scripts share DTC225200095 and GV023, so **never run them in parallel**. ai-nfr refuses to start if DTC225200095 already holds an active topic.
- Other scripts: e2e-uc1 uses K99 and e2e-uc2-5 uses K98.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Cleanup loops deleted only the first uploaded file**
- **Found during:** Task 2, in the post-run residue check. `DE_CUONG/` grew from 39 to 79 files after two ai-nfr runs.
- **Issue:** `docker compose exec -T` inside `while read … <<<"$files"` consumed the here-string on stdin, so each cleanup removed only the first file. The same code in e2e-ai and e2e-uc2-5 had been leaking files the same way since Phase 3.
- **Fix:** `</dev/null` on the exec in all three scripts. A one-off comparison of the volume against `tai_lieu_do_an.ten_luu_tru` found **103 unreferenced files** (79 DE_CUONG, 13 BAO_CAO_TIEN_DO, 11 BAO_CAO_CUOI). They were removed, leaving 25, which is exactly the rows. The count stayed at 25 across fresh runs of e2e-ai, e2e-uc2-5 and ai-nfr.
- **Files:** deploy/ai-nfr.sh, deploy/e2e-ai.sh, deploy/e2e-uc2-5.sh. **Commit:** 1b3d756.

**2. [Rule 2 - Correctness] The ai_document e2e checks more than the plan asked**
- The student's own view must carry both `doan_nguon` and `doan_trung` with `doan_trung_an` false, because the source is a published archive thesis under WR-07.
- Boilerplate is checked in the source text as well as the submitted text.
- The GVHD comparison covers passages (`vi_tri`, texts), not only the rate.

**3. [Doc] The chương 4 page carries a `Mã PI` line and a relative link to 03-hieu-chinh-nguong.md**, so `check-docs pi-tags` and `check-docs links` stay green.

### Other

- **Commits on `main`:** per the orchestrator ("sequential on main"). The concurrent read-only Phase 3 verifier committed 314248f (`.planning` only) during this plan. rev-list therefore counts 5 commits, of which 4 are this plan's.
- **TDD:** the RED commit is separate (7d04c86) and GREEN is in the Task 1 feat commit. There is exactly one `def test_` in the new file, as the acceptance check requires.

## Human check (self-performed via headless Chrome/CDP; user confirmation pending)

The scripts are in the scratchpad (`cdp0406.sh`/`.py`, 1440 px). Setup was a temporary K97 cohort, "CDP 04-06 — Hệ thống quản lý câu lạc bộ sinh viên", with GV023 as GVHD.

1. DTC225200095 opened **Đề cương**, set P01-B.pdf on the Dragger's file input and clicked "Nộp phiên bản mới".
2. "Đang kiểm tra" appeared after **0.26 s**. It changed to **"Hoàn tất - 50.3%"** after **3.03 s**, without a reload.
3. "Xem kết quả" opened `/kiem-tra-trung-lap/{id}` (MH-14). The page showed:
   - Tỷ lệ tổng 50.3% and Ngưỡng 10.4%.
   - "Đồ án trùng": "Phát triển mô hình thống kê điểm số … Metabase (K21)".
   - "Đoạn trong tài liệu nộp" next to "Đoạn nguồn (… (K21))", with the tag "Mức trùng: Cao (100%)".
4. GV023 opened **Duyệt đề cương**. The list showed "Hoàn tất - 50.3%", and "Duyệt" opened the review panel with "Kết quả kiểm tra trùng lặp 50.3% … Vượt ngưỡng cảnh báo" and the same top thesis with khóa K21.
5. **Cleanup:** vectors purged, rows and files deleted, 0 K97 cohorts, Chrome profile removed.

**Observation for 04-07, not changed here:** MH-14's per-thesis "Tỷ lệ" is the highest passage score (100%), not the AI's per-source share (`do_an_trung[].ty_le`, 50.3%). This is Phase 3 `detail()` logic, and the AI's per-source share is not stored.

## Known Stubs

None. The `AI_CLIENT=stub` fallback is intentional (D-07). Stub results carry no `tin_hieu`, so `vi_tri` has no suffix there.

## Threat Flags

None beyond the register:
- T-04-23: broad except → LOI kept; ingest isolated after HOAN_TAT; tested.
- T-04-24: `loai_tru` plus check-before-ingest; the resubmission e2e proves it.
- T-04-25: the seed runs only in the api container, reads from a read-only mount, reuses the magic-byte validator and server-generated names, and is idempotent.
- T-04-26: passages are unchanged plain text.
- T-04-27: DOCUMENT purge in e2e-ai, ai-nfr and e2e-uc2-5, plus the file-deletion fix.
- T-04-SC: no new packages.

## Self-Check: PASSED

- FOUND: backend/app/seed_ai_corpus.py, backend/tests/test_ai_document_flow.py, deploy/ai-nfr.sh, docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md
- FOUND commits: 7d04c86, 6068f65, 8b07866, 1b3d756
- Gates on the final tree:
  - backend pytest: 52 passed
  - ai-service pytest: 5 passed
  - `npm run build`: OK
  - smoke-test: passed
  - e2e-uc1, e2e-uc2-5, e2e-ai: green
  - seed-ai.sh ×2: idempotent
  - ai-nfr.sh: all pass
  - check-erd-db: OK, with no schema change (head 0011)
  - check-docs links / pi-tags: OK
- Leftovers:
  - 0 cohorts in K96–K99
  - 25 archive rows linked
  - 300 / 2208 vectors
  - 25 files on the uploads volume
