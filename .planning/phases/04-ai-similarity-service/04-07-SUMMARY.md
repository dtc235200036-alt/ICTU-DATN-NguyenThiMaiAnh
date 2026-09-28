---
phase: 04-ai-similarity-service
plan: 07
status: complete
subsystem: ai-integration
tags: [UC0.4, thresholds, MH-14, MH-09, highlight, docs-write-back, phase-gate, AISV-05, AISV-07, SC4]
requires:
  - "04-06: document_check with nguong_doan/loai_tru, vi_tri signal suffix, e2e-ai ai_document, ai-nfr.sh"
  - "04-05: cau_hinh_nguong rows NGUONG_TEN_DE_TAI/NGUONG_TAI_LIEU/NGUONG_DOAN_TRUNG (Alembic 0010), e2e-ai ai_title"
  - "03-02: documents feature (CheckPanel, CheckDetailPage, CheckSegment types)"
provides:
  - "GET/PUT /api/thresholds (BO_MON) + ThresholdSettingsPage at /cau-hinh-nguong (menu 'Ngưỡng trùng lặp', order 80)"
  - "frontend/src/features/documents/highlight.ts: highlightOverlap + parseViTri"
  - "MH-14 passage cards with <mark> highlights and signal tags; MH-09 passage count"
  - "detail(): per-thesis rate = share of ty_le_tong (no schema change)"
  - "e2e-ai ai_threshold (SC4) with self-restoring trap; smoke threshold RBAC checks"
  - "Chương 3 write-back, chương 4 AI index page, deploy/README AI section + demo script"
affects: [05]
tech-stack:
  added: []
  patterns:
    - "Policy values read per request, never cached — the next check applies an edit, past results keep their snapshot"
    - "Test/e2e edits to shared policy rows restore value AND editor/time, then re-read"
    - "Text highlighting as a pure segmenter returning {text, match}; the component renders React text + <mark> only"
key-files:
  created:
    - backend/app/services/thresholds.py
    - backend/app/schemas/thresholds.py
    - backend/app/routers/thresholds.py
    - backend/tests/test_thresholds.py
    - frontend/src/features/thresholds/api.ts
    - frontend/src/features/thresholds/routes.tsx
    - frontend/src/features/thresholds/ThresholdSettingsPage.tsx
    - frontend/src/features/documents/highlight.ts
    - docs/chuong-4-trien-khai/thu-nghiem-ai/README.md
  modified:
    - backend/app/services/document_check.py
    - frontend/src/features/documents/CheckDetailPage.tsx
    - frontend/src/features/documents/CheckPanel.tsx
    - deploy/e2e-ai.sh
    - deploy/smoke-test.sh
    - deploy/README.md
    - docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.puml (+ .png/.svg re-rendered)
    - docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md
    - docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md
    - docs/README.md
decisions:
  - "PUT /api/thresholds takes all three values at once; 0–100 and at most 2 decimals, both refused with a 'UC0.4 - E1' message (422)"
  - "nguoi_cap_nhat = SV/GV ho_ten, else the account email (same rule as deps.get_current_user); the Bộ môn account has no profile, so it shows bomon@ictu.edu.vn"
  - "The MinHash verbatim threshold (88.7) is shown read-only in the screen's info Alert; it is not editable"
  - "The highlight unit is a run of 3 consecutive words (Unicode \\p{L}\\p{N}, NFC + lowercase) present in the same order on the other side; separators between two marked words are marked too"
  - "MH-14/MH-09 per-thesis rate = ty_le_tong × (characters of that thesis's stored doan_nguon) / (characters of all stored passages). The AI assigns each flagged sentence to one source, so this reproduces its per-source share without a new column. Fallback: max passage score when ty_le_tong or the passage text is missing"
  - "e2e-ai ai_threshold restores the rows with PUT and then SQL (tai_khoan_id, thoi_diem_cap_nhat), so a test run never becomes the 'last editor', and Alembic 0010's tai_khoan_id IS NULL rule still holds"
metrics:
  duration: "~26 min"
  completed: 2026-09-28
estimate:
  tokens: 120000
  tasks: 3
actuals:
  tokens: 16600   # chars/4 over git diff plan_head_before..plan_head_after, png/svg excluded
  tasks: 3
  commits: 4      # MEASURED: git rev-list --count 3b4581d..7f0a2a1 (1 RED test + 3 feat)
plan_head_before: 3b4581d9d848646eaf3f013ea6269619c664e936
plan_head_after: 7f0a2a123e3493e9271c022d1a4da14f0fb3c19c
---

# Phase 4 Plan 07: Threshold screen, MH-14 highlights, docs write-back, phase gate Summary

**The Bộ môn now sets the title, document-warning and passage thresholds on a UC0.4 screen, and the very next check uses them. On the real AI, a title threshold of 99.99 hides the 81.92% archive match and restoring 67.8 brings it back, while past results keep their snapshot. MH-14 shows each duplicated passage beside its source, with shared 3-word runs marked and a "Trùng nguyên văn" or "Trùng ngữ nghĩa" tag. The per-thesis rate is now the thesis's share of the overall rate: 20.8% + 4.7% = 25.54% for P11-B, where it used to be the max passage score. Chương 3 and the deploy README describe the AI service as built. The full phase gate is green on one rebuilt stack.**

## Tasks

| # | Task | Commit | Result |
|---|------|--------|--------|
| 1 | RED: test_thresholds | 0ff5322 | Failed on 404 (route missing) |
| 1 | /api/thresholds, UC0.4 screen, e2e ai_threshold, smoke | d5bd49c | 53 backend tests; e2e-ai and smoke green; dom-check OK |
| 2 | highlight.ts, MH-14 passage cards, MH-09 count, per-thesis share | 6d12814 | Build OK; 0 raw-HTML uses; e2e-ai share assertions green |
| 3 | Chương 3 write-back, chương 4 index, deploy README, gate | 7f0a2a1 | Every gate below green |

## Threshold API and screen (AISV-07, D-04, SC4)

- **`GET /api/thresholds`:** BO_MON only. Returns `[ThresholdOut]` ordered NGUONG_TEN_DE_TAI, NGUONG_TAI_LIEU, NGUONG_DOAN_TRUNG. Each item has `{loai, nhan, mo_ta, gia_tri, gia_tri_de_xuat (67.8 / 10.4 / 67.7), thoi_diem_cap_nhat (UTC ISO), nguoi_cap_nhat}`.
- **`PUT /api/thresholds`:** BO_MON only. Body is `{NGUONG_TEN_DE_TAI, NGUONG_TAI_LIEU, NGUONG_DOAN_TRUNG}`.
  - Validation is 0–100 with at most 2 decimals. A bad value gets 422 with "Ngưỡng phải nằm trong khoảng 0–100% (UC0.4 - E1)"; the DB CHECK is the second guard.
  - One commit writes the values, `tai_khoan_id` and `thoi_diem_cap_nhat`. It inserts NGUONG_DOAN_TRUNG if the row is missing and takes the rows `FOR UPDATE`.
  - Returns the fresh list.
- **Frontend:** route `/cau-hinh-nguong` (BO_MON), breadcrumb Cấu hình › Ngưỡng cảnh báo trùng lặp, menu "Ngưỡng trùng lặp" (order 80).
  - Three InputNumber fields (0–100, step 0.5, precision 2, %). Each shows its explanation, "Giá trị đề xuất sau hiệu chỉnh: x%" and either "Cập nhật lần cuối: … bởi …" or the calibrated-default line.
  - An info Alert says changes apply to the next checks only and that the MinHash threshold (88.7%) is a technical parameter.
  - "Khôi phục giá trị đề xuất" only fills the form. "Lưu cấu hình" asks for confirmation through a Popconfirm.
  - A 403 on load shows ForbiddenPage.
- **test_thresholds** (1 test) covers:
  - SV/GV get 403 on GET and PUT.
  - 120 and -1 get 422 and nothing changes.
  - A valid PUT records the editor and time.
  - The earlier outline check keeps 30.0 while the next submission snapshots 42.25.
  - check-title reports `nguong` 95.5 with no match, then 50 with the match back.
  - The rows (values, editor, time) are restored in `finally`.
- **e2e-ai `ai_threshold`** (real AI, TV001 paraphrase):
  - At 99.99: `nguong` 99.99 and 0 KHO matches.
  - Restoring 67.8: the KHO match returns at 81.92%.
  - The trap restores the value, editor and time, re-reads them, and FAILs on a mismatch. It runs on every exit.
  - After the gate, the rows read 67.70 / 10.40 / 67.80 with tai_khoan_id NULL.
- **smoke-test:** DTC225200001 and GV001 get 403 on GET and PUT; bomon GET returns 200.

## Highlighting (AISV-05, D-03, T-04-31)

- **`highlightOverlap(text, other, n = 3)`:**
  - Tokenises into word and non-word runs with `/[\p{L}\p{N}]+|[^\p{L}\p{N}]+/gu` and compares words after NFC + lowercase.
  - Marks every word of `text` that sits inside a 3-word run also found consecutively in `other`, and marks the separators between two marked words.
  - Merges neighbouring segments with the same flag. Empty or no-match input gives one unmarked segment.
- **`parseViTri`:** splits the vi_tri text on the last " · " suffix.
- **MH-14:** one card per passage. The header holds "Câu a–b", the Mức trùng tag and the signal tag (red "Trùng nguyên văn" or orange "Trùng ngữ nghĩa"). Both columns render through `highlightOverlap` as React `<span>`/`<mark>` nodes, with the mark background from antd `colorWarningBgHover`.
  - When the check is HOAN_TAT, the FR-AI-02 note is shown, plus one line explaining the marks.
  - The WR-07 hidden-source note is kept.
  - `dangerouslySetInnerHTML` is used 0 times in `frontend/src`.
- **MH-09:** shows "Số đoạn trùng: n" and, when there are any verbatim passages, "(m trùng nguyên văn)".
- **Readability (from the browser check):**
  - Verbatim passages are almost entirely marked (P01-B: 14 marks, 7474 characters).
  - Paraphrased passages show short marks on shared domain phrases or names, such as "chuyên đề ôn tập", "giáo viên chủ nhiệm" and "nghề Tuyên Quang" (P11-B: 62 marks, 1505 characters across 6 passages). They stay readable, and the tag says why the passage was flagged.
  - No issue needed a fix.

## Per-thesis rate on MH-14/MH-09 (04-06 follow-up)

Fixed without a schema change. `_per_source_share()` in `document_check.detail()` spreads `ty_le_tong` over sources in proportion to the characters of each source's stored `doan_nguon`. This is exact up to join spaces, because the AI assigns each flagged sentence to a single source.

| Submission | Before | After |
|---|---|---|
| P01-B | 100% (max passage score) | 50.3% (= ty_le_tong, one source) |
| P11-B | 86.18% / … | 20.8% + 4.7% = 25.5%, against AI ty_le_nguon 20.79 |

It falls back to the old max-passage value when `ty_le_tong` or the passage text is missing. It deviates slightly only when the AI truncates at more than 50 passages (`CHI_TIET_TOI_DA`); the README documents this. e2e-ai now asserts that the top share is at most `ty_le_tong` and that the shares sum to `ty_le_tong` within ±0.5.

## Documentation changed

- **`erd-thesis-ai.puml`**, re-rendered to png and svg:
  - `loai_nguon VARCHAR(20)` with a note: CHECK TOPIC/ARCHIVE/DOCUMENT, VARCHAR + CHECK convention.
  - Note on the `ma_nguon` namespaces per type.
  - `noi_dung` described as a sentence-level chunk.
  - INDEX(loai_nguon, ma_nguon).
  - ai-service `test_schema_erd` is still green.
- **02-thiet-ke-csdl.md:**
  - §3.2.3 `cau_hinh_nguong.loai`: the meaning of each of the three rows, "bổ sung khi thi công Phase 4, D-04", and that UC0.4 is read per request.
  - §3.2.6 table rows: ARCHIVE, sentence chunks, `bam_noi_dung`, model name, /reindex.
  - §3.2.6 new list: three id namespaces, replace semantics of /ingest, rebuild at startup.
- **03-kien-truc-he-thong.md:**
  - §3.3.5 rows: ARCHIVE and replace, `nguong`/`loai`, `nguong_doan`/`nguong_nguyen_van`/`loai_tru`, `tin_hieu`/`diem_*`/`so_doan`/`so_doan_loai_tru`, and the /health fields.
  - §3.3.5 paragraph: "điều chỉnh khi thi công Phase 4 (bổ sung, không phá hợp đồng)".
  - §3.3.8 new rows: per-request thresholds (D-04), and the single-worker in-memory index.
- **`docs/chuong-4-trien-khai/thu-nghiem-ai/README.md`** (new): an index of the 4 pages with PI and requirement IDs, and the reproduction commands in order (datagen, bakeoff `--all`/`--decide`, calibrate tune/evaluate, seed-ai, e2e-ai, ai-nfr `--report`). It carries a Mã PI line.
- **docs/README.md:** the directory map now lists `chuong-4-trien-khai/thu-nghiem-ai/`.
- **deploy/README.md**, section "Dịch vụ AI kiểm tra trùng lặp":
  - The ai and ai-db-init services and the env keys, including the AI_CLIENT=stub fallback and AI_STUB_MODE.
  - `init.sh` appends missing keys to an existing .env.
  - `app.download_model` pre-warm, and seed-ai.
  - Backfill and the /reindex command.
  - e2e-ai and ai-nfr. **They share DTC225200095/GV023 and must never run in parallel.**
  - Reserved accounts and khóa K96/K97.
  - Known limitations:
    - Deleting an archive record keeps its vectors. They are hidden from results, and a manual `ai_index purge` command is given.
    - The boilerplate list is [ASSUMED].
    - The detection numbers come from synthetic data.
    - The per-thesis share approximation.
  - "Kịch bản demo AI" SC1–SC5, using non-reserved demo accounts.
  - The scripts table, test list and architecture note are updated.

## Phase gate (one rebuilt stack, 2026-09-28 08:45–08:52Z)

| Gate | Result |
|---|---|
| `docker compose … up -d --build --wait` | all healthy |
| `npm ci` / `npm run build` | OK / OK |
| backend `pytest -q` | **53 passed** |
| ai-service `pytest -q` | **5 passed** |
| `seed-ai.sh` | idempotent. Backfill DOCUMENT 25/0 failures; 25 source theses; index 300 / 2208 |
| `smoke-test.sh` | all passed, including the new /api/thresholds checks |
| `e2e-uc1.sh` / `e2e-uc2-5.sh` | OK / OK |
| `e2e-ai.sh` | OK: security, TV001–TV004, ai_threshold (99.99 hides the match; 67.8 brings back 81.92%; rows restored), ai_index, and ai_document (P01-B 50.3% with 7 verbatim passages, share 50.3%; P21-B 6.0%) |
| `ai-nfr.sh` | NFR-07 pass. NFR-08 P95 34 ms. NFR-09 P95 3.58 s (20/20, 0 LOI). NFR-10 max 0.076 s. NFR-11 +1. Memory peak 747 MiB, not OOM-killed |
| `check-erd-db.py`, `check-docs class-erd`, `check-docs render docs/chuong-3-thiet-ke` | OK (also links, pi-tags and privacy OK) |
| dom-check `/cau-hinh-nguong`, `/kiem-tra-trung-lap/1` | both end on the login form |
| Leftovers | 0 K96–K99 cohorts; 25 files = 25 rows; index 300 / 2208; thresholds 67.70/10.40/67.80 with editor NULL |

**Traceability.**

| Requirement | Evidence |
|---|---|
| AISV-01 | e2e ai_security, NFR-07 |
| AISV-02 | NFC=NFD in e2e ai_title, NFR-11 |
| AISV-03 | ai_title, NFR-08 |
| AISV-04 | ai_document boilerplate check |
| AISV-05 | MH-14 highlights, ai_document passages, browser check |
| AISV-06 | NFR-09/10, UI states from 04-06 |
| AISV-07 | test_thresholds, ai_threshold, smoke |
| DATA-02 | seed-ai: 300 records |
| DATA-03 | seed-ai: 25 sources, plus the chương 4 page 03 table |

## Human checks (self-performed via headless Chrome/CDP at 1440 px; user confirmation pending)

The scripts are `scratchpad/cdp0407.sh` and `cdp0407.py`.

1. **UC0.4 (bomon):**
   - The page lists the 3 thresholds with their explanations, the recommended values 67.8 / 10.4 / 67.7, the read-only MinHash note, and the menu "Ngưỡng trùng lặp".
   - Setting the title threshold to 99, clicking "Lưu cấu hình" and confirming showed "Đã lưu cấu hình ngưỡng" after 0.26 s. The page then showed "Cập nhật lần cuối … bởi bomon@…".
2. **MH-06 (DTC225200095):** the TV001 paraphrase gave **no warning** at 99. Bomon then clicked "Khôi phục giá trị đề xuất" (the form went back to 67.80) and saved. The same title then showed **"Phát hiện 1 đề tài tương tự trong kho"**. The threshold rows were restored exactly afterwards.
3. **MH-14 for the P01-B (CHEP) submission:**
   - 7 cards, each tagged "Trùng nguyên văn", with long marked runs on both sides.
   - The first card is "Câu 1–6 · Mức trùng: Cao (100%)".
   - The FR-AI-02 note is present.
   - The per-thesis rate is 50.3%.
4. **MH-14 for P11-B (DIEN_DAT_LAI), as DTC225200096:**
   - 6 cards tagged "Trùng ngữ nghĩa" with sparse marks.
   - The sources are K18 at 20.8% and K19 at 4.7%, against a total of 25.5%.
5. **MH-09 (GV023, Duyệt đề cương):** "Ngưỡng áp dụng … 10.4% · Vượt ngưỡng cảnh báo" and "Số đoạn trùng: 6".
6. **Cleanup:** vectors purged, rows and files deleted, 0 K97 cohorts, Chrome profile removed.

**Phase 4 UAT items to keep:**
- The two plan human-checks: the UC0.4 settings effect across two roles, and MH-14/MH-09 highlight readability.
- The final UAT: follow deploy/README "Kịch bản demo AI" SC1–SC5 end to end in a browser.
- Earlier Phase 4 items stay open (04-06 submit→MH-14 flow).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] MH-14/MH-09 per-thesis rate was the max passage score** (the orchestrator asked for this, following up a 04-06 observation)
- **Found during:** Task 2
- **Issue:** `detail()` grouped rows by label and took the maximum `ty_le`, so P01-B showed "100%" for a thesis that makes up 50.3% of the document.
- **Fix:** `_per_source_share()`, which is the share of `ty_le_tong` by stored passage characters, with no schema change. e2e-ai asserts that the top share is at most the total and that the shares sum to the total.
- **Files modified:** backend/app/services/document_check.py, deploy/e2e-ai.sh
- **Commit:** 6d12814

**2. [Rule 2 - Correctness] e2e-ai restores editor and time as well as the values**
- **Found during:** Task 1
- **Issue:** a plain PUT-back would leave `tai_khoan_id` set to bomon on every run. That makes the script the "last editor" and disables Alembic 0010's `tai_khoan_id IS NULL` recalibration path.
- **Fix:** the script PUTs the values back, runs an SQL restore of `tai_khoan_id`/`thoi_diem_cap_nhat` from a snapshot, and then compares the whole snapshot. test_thresholds restores the same way. The restore loop's `docker compose exec` reads stdin from `/dev/null`, following the 04-06 lesson.
- **Commit:** d5bd49c

**3. [Test adjustment]** The RED test expected the editor name "Bộ môn CNPM", but `make_account` gives BO_MON no profile. The shown name follows deps.get_current_user (the email), and the test was adjusted in the GREEN commit before any implementation assertion depended on it.

### Other

- `test_thresholds.py` has exactly one `def test_`, as the acceptance check requires. The TDD RED commit (0ff5322) is separate from GREEN (d5bd49c).
- The plan's `files_modified` did not list `backend/app/services/document_check.py`. It changed for deviation 1.
- `python3 tools/check-docs.py all` fails only on `docs/truy-vet.md` PI 1.1, "Chờ dữ liệu khảo sát thật". This is a Phase 1 real-survey item that predates this plan, is out of scope and is not part of the gate. Every sub-check in the gate is green.
- The report DOCX and slides were not built, as the user deferred them.

## Known Stubs

None. The `AI_CLIENT=stub` fallback is intentional (D-07) and documented in the README.

## Threat Flags

None beyond the register:
- T-04-29: `require_role(BO_MON)` on both routes, covered by pytest, smoke and the route role-coverage test.
- T-04-30: Pydantic 0–100 with 2 decimals, the DB CHECK, and the editor and time recorded.
- T-04-31: pure segments rendered as React text and `<mark>`; raw-HTML count 0.
- T-04-32: the finally block and trap restore and re-read the rows.
- T-04-33: the README names env keys only.
- T-04-SC: no new packages; `npm ci` on the existing lock.

## Self-Check: PASSED

- FOUND: backend/app/{services,schemas,routers}/thresholds.py, backend/tests/test_thresholds.py, frontend/src/features/thresholds/{api.ts,routes.tsx,ThresholdSettingsPage.tsx}, frontend/src/features/documents/highlight.ts, docs/chuong-4-trien-khai/thu-nghiem-ai/README.md
- FOUND commits: 0ff5322, d5bd49c, 6d12814, 7f0a2a1
- The acceptance greps for Tasks 1–3 all pass. There is exactly one `def test_` in test_thresholds.py.
