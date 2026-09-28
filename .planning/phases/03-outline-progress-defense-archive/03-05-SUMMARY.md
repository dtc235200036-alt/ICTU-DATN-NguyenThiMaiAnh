---
phase: 03-outline-progress-defense-archive
plan: 05
subsystem: archive
tags: [fastapi, sqlalchemy, mysql, csv, background-tasks, react, antd, tanstack-query]

requires:
  - phase: 03-outline-progress-defense-archive (plan 04)
    provides: "models/kho.py (DoAnKho, HE_THONG/IMPORT/CHUA_INDEX/DA_INDEX), services/archive.py (insert_from_defense, latest_final_report, ingest_payload, run_ingest), e2e globals DO_AN_KHO_ID + $TMP/bao-cao-cuoi.pdf, K98 IMPORT cleanup"
  - phase: 03-outline-progress-defense-archive (plan 01)
    provides: "documents.storage_path/to_document_out, ai_client (INGEST_LOG, AiClientStub.ingest, AiServiceError), downloadFile"
provides:
  - "app/services/archive.py: list_archive, khoa_options, get_detail, file_path_or_404, create, update_record, delete, mark_for_reindex, import_csv -> (ImportResult, new_ids)"
  - "app/schemas/archive.py: ArchiveIn, ArchiveStudent, ArchiveListItem, ArchiveDetail, ImportRowError, ImportResult"
  - "Routes /api/archive: GET '' / '/khoa' / '/{id}' / '/{id}/file' (ANY_ROLE); POST '' (201), PUT '/{id}', DELETE '/{id}' (204), POST '/{id}/reindex' (202), POST '/import' (BO_MON) — every write queues archive.run_ingest after commit"
  - "frontend features/archive: /kho-do-an (MH-13), ArchiveFormModal, ArchiveImportModal, api hooks"
  - "deploy/README.md 'Định dạng CSV import kho đồ án'; e2e uc5_archive"
affects: [03-06, 03-07, 04-04, 04-05]

actuals:
  tokens: 16300
  tasks: 2
  commits: 7
  own_commits: 3
  plan_head_before: a034b0e12cd364728fc3510afd6ed56748a27d67
  plan_head_after: 98c5285ae9bc1d0001dcd4279f7be95a2127a541

tech-stack:
  added: []
  patterns:
    - "CSV import = stdlib csv.DictReader over utf-8-sig text; per-row validation collects ImportRowError(dong = reader.line_num, ly_do); lookups batched (GV by code, SV by code, existing (khoa, ten_de_tai) by khoa) — no N+1; valid rows inserted in one commit"
    - "Archive writes follow the 03-04 post-commit side-effect pattern: service commits, router adds BackgroundTasks(run_ingest, ids)"
    - "Frontend: detail query polls every 3 s only while CHUA_INDEX; mutations invalidate immediately and once more after 2 s so the list catches the background index"

key-files:
  created:
    - backend/app/schemas/archive.py
    - backend/app/routers/archive.py
    - backend/tests/test_archive.py
    - frontend/src/features/archive/api.ts
    - frontend/src/features/archive/routes.tsx
    - frontend/src/features/archive/ArchivePage.tsx
    - frontend/src/features/archive/ArchiveFormModal.tsx
    - frontend/src/features/archive/ArchiveImportModal.tsx
  modified:
    - backend/app/services/archive.py
    - deploy/README.md
    - deploy/e2e-uc2-5.sh

key-decisions:
  - "Search q = NFC(q).strip(), contains(autoescape=True) on ten_de_tai OR tu_khoa, ANDed with khoa/giang_vien_id; collation utf8mb4_vietnamese_ci makes it case-insensitive but accent-sensitive ('THƯ VIỆN' finds 'thư viện', 'thu vien' does not) — measured"
  - "Manual (UC5.3 A1) and imported records get nguon IMPORT, no file; update never changes nguon/de_tai_id and always resets CHUA_INDEX before the background re-ingest"
  - "sinh_vien_id follows ma_so_sinh_vien: linked when the code matches an existing SV (ho_ten filled from it when blank), cleared otherwise"
  - "Schema class named ImportRowError (plan said ImportError) to avoid shadowing the Python builtin"
  - "CSV: if the header line contains ';' and no ',', ';' is used (Excel VN-locale export); fully blank rows are skipped and not counted in tong_dong"

requirements-completed: [REPO-01, REPO-02, REPO-03]

coverage:
  - id: D1
    description: "Per REPO-02, D-07, UC5.1: every role searches by khóa, từ khóa (escaped, NFC) and GVHD with server pagination, opens a record and downloads the archived final report"
    requirement: "REPO-02"
    verification:
      - kind: unit
        ref: "backend/tests/test_archive.py::test_csv_import_partial_success_search_and_reindex — q NFC substring, khoa, giang_vien_id filters, q='%' total 0 — pass"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc5_archive — DTC225200097 ?khoa=K98 sees diem 8.5 + co_file, /file sha256 equals uploaded report; GV025 q='biển số' finds the import — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0305-01/02/03: SV list + keyword search in URL + Drawer + real download (880 B PDF); GV001 deep link with khoa/GVHD/id filters"
        status: pass
    human_judgment: true
    rationale: "Self-performed via headless Chrome per autonomous-run instruction; user confirmation pending."
  - id: D2
    description: "Per REPO-01: records inserted by chốt appear with khóa, đề tài, SV, GVHD, từ khóa, điểm, file"
    requirement: "REPO-01"
    verification:
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh uc5_archive (HE_THONG record listed with 8.5/co_file, keywords edited by Bộ môn)"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0305-02: Drawer shows Sinh viên 'Dương Bảo Thảo (DTC225200098)', K95, GVHD, 8.67, Nguồn 'Hệ thống (chốt bảo vệ)', '⬇ Tải báo cáo cuối (PDF, 880 B)'"
        status: pass
    human_judgment: true
    rationale: "MH-13 Drawer fidelity judged by self-run CDP screenshots; user confirmation pending."
  - id: D3
    description: "Per REPO-03, UC5.3: only Bộ môn creates/edits/deletes/reindexes (SV/GV 403); delete never touches check history (E1)"
    requirement: "REPO-03"
    verification:
      - kind: unit
        ref: "test_archive_writes_are_bomon_only — SV/GV 403 on 5 write paths, 200 on 3 reads, row unchanged — pass"
        status: pass
      - kind: e2e
        ref: "uc5_archive — DTC225200097 POST 403, GV025 import 403, bomon DELETE 204 then GET 404 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP p0305-04..09: add form → Drawer 'Đã index' → Sửa keywords → Đã index → forced CHUA_INDEX shows 'Index lại' → click → Đã index → Popconfirm delete"
        status: pass
    human_judgment: true
    rationale: "Bộ môn UX self-verified via CDP; user confirmation pending."
  - id: D4
    description: "Per REPO-03, D-07, UC5.4: CSV import with partial success, per-line errors, NFC storage"
    requirement: "REPO-03"
    verification:
      - kind: unit
        ref: "test_csv_import_partial_success_search_and_reindex — BOM CSV 5 rows → tong_dong 5, thanh_cong 2, errors lines 4/5/6; NFD title stored NFC; '8,5' → 8.50; GV linked — pass"
        status: pass
      - kind: e2e
        ref: "uc5_archive — 3-row K98 CSV → '3|2|4:Thiếu tên đề tài' — pass"
        status: pass
      - kind: manual_procedural
        ref: "README sample CSV (CRLF + BOM + broken line) via API: {tong_dong 3, thanh_cong 2, loi [4 Thiếu tên đề tài]}; via MH-13 modal p0305-10 'Đã nhập 2/3 dòng' + table Dòng 4"
        status: pass
    human_judgment: true
    rationale: "Real spreadsheet export not available headless; sample built as CSV UTF-8 with BOM + CRLF. User confirmation pending."
  - id: D5
    description: "Per D-07, FR-KHO-05, UC5.2 E1: every created/updated/imported record is ingested after commit; AI failure leaves CHUA_INDEX; Index lại recovers"
    requirement: "REPO-03"
    verification:
      - kind: unit
        ref: "test_csv_import_partial_success_search_and_reindex — INGEST_LOG +2, patched AiServiceError → PUT 200 + CHUA_INDEX, reindex 202 → DA_INDEX — pass"
        status: pass
      - kind: e2e
        ref: "uc5_archive — PUT keywords → polled DA_INDEX — pass"
        status: pass
    human_judgment: false
  - id: D6
    description: "Per D-09: e2e demo chain gains uc5_archive through Apache; K98 rows cleaned"
    requirement: "REPO-02"
    verification:
      - kind: integration
        ref: "docker compose rebuild; bash deploy/e2e-uc2-5.sh (3 runs green); COUNT(do_an_kho WHERE khoa='K98') = 0; dom-check /kho-do-an ends on login form"
        status: pass
    human_judgment: false

duration: ~20min
completed: 2026-09-28
status: complete
---

# Phase 3 Plan 5: UC5.1/5.3/5.4 Kho đồ án (search, maintenance, CSV import) Summary

**Every role now searches the faculty archive by khóa, từ khóa and GVHD on MH-13 and downloads archived final reports. The Bộ môn adds, edits, deletes and re-indexes records, and imports past cohorts from a documented UTF-8 CSV with partial success and per-line errors. Every new or changed record is pushed to the AI seam after commit.**

## Performance

- **Duration:** ~20 min (2026-09-28T04:10Z → ~04:30Z)
- **Tasks:** 2/2
- **Files:** 8 created, 3 modified

## Accomplishments

- **Task 1 (backend, TDD).** RED `0974c6e` failed with 404s on the missing routes. GREEN `cdb7f9d` passed both tests on the first run.
  - `list_archive` ANDs the khóa, GVHD and `q` filters, sorts newest first and counts with the same predicate. It fetches `co_file` for the whole page in one query.
  - `import_csv` checks size, encoding, required headers and the row cap. It validates each row and inserts all valid rows in one transaction.
  - The router adds `run_ingest` after each create, update, import and reindex.
- **Task 2 (frontend, `98c5285`).** MH-13 at `/kho-do-an`:
  - Menu "Kho đồ án" at order 70 for all three roles. Filters (Khóa, Giảng viên hướng dẫn, Từ khóa), page and open record id all live in the URL.
  - Keyword Tags in the table. The Bộ môn also sees the "Chỉ mục AI" column.
  - Drawer "Chi tiết bản ghi kho" with the authorized download.
  - Bộ môn footer: "Xóa" (Popconfirm quoting UC5.3 E1), "Index lại" (only when CHUA_INDEX) and "Sửa".
  - Form modal and the "Import đồ án khóa cũ" modal.

## Final CSV rules (as implemented)

- **Encoding and layout:** UTF-8, with or without a BOM (`utf-8-sig`). The first line is the header. Header names are NFC-normalized, trimmed and matched case-insensitively. Unknown columns are ignored.
  - Comma-separated. If the header has `;` but no `,`, the file is read as `;`-separated.
- **Whole-file 422s:**
  - "File CSV tối đa 2 MB"
  - "File CSV phải mã hóa UTF-8"
  - "File CSV rỗng"
  - "File CSV thiếu cột bắt buộc: …"
  - "File CSV tối đa 2000 dòng dữ liệu"
- **Blank rows** are skipped and not counted.
- **Row reasons** (several are joined with "; "):
  - "Thiếu khóa", "Khóa quá 20 ký tự"
  - "Thiếu tên đề tài", "Tên đề tài quá 255 ký tự"
  - "Mã sinh viên quá 20 ký tự", "Họ tên sinh viên quá 150 ký tự", "Từ khóa quá 255 ký tự"
  - "Điểm không hợp lệ (0–10)" — accepts `8.5` or `8,5`, at most 2 decimals
  - "Không tìm thấy giảng viên mã {ma}"
  - "Trùng bản ghi (khóa, tên đề tài)" — against the archive or an earlier row of the file, compared case-insensitively
- **Line numbers:** `dong` is `csv.DictReader.line_num`, the physical line with the header as 1.
- **Stored rows:** nguồn IMPORT, CHUA_INDEX, then background ingest.

## Archive routes

| Method | Path | Roles | Notes |
|---|---|---|---|
| GET | `/api/archive` | all | `khoa`, `giang_vien_id`, `q`, `page`, `page_size ≤ 100` → `Page[ArchiveListItem]` |
| GET | `/api/archive/khoa` | all | distinct khóa, descending |
| GET | `/api/archive/{id}` | all | `ArchiveDetail` (404 "Không tìm thấy bản ghi kho") |
| GET | `/api/archive/{id}/file` | all | latest BAO_CAO_CUOI of the archived topic (404 "Bản ghi kho không có file báo cáo") |
| POST | `/api/archive` | BO_MON | 201; 409 duplicate khóa + tên; 422 unknown GV; ingest |
| PUT | `/api/archive/{id}` | BO_MON | → CHUA_INDEX + ingest |
| DELETE | `/api/archive/{id}` | BO_MON | 204, row only |
| POST | `/api/archive/{id}/reindex` | BO_MON | 202 + ingest |
| POST | `/api/archive/import` | BO_MON | multipart `file` → `ImportResult` + ingest(new_ids) |

## Contract gap for Phase 4

§3.3.5 has no AI-side delete. `DELETE /api/archive/{id}` removes the row from thesis_core only, so the vector for that `ref_id` stays in the AI index. Phase 4 (04-05 integration) needs a `/delete` (or re-sync) call. UC5.3 E1 still holds by construction: `chi_tiet_trung_lap.doi_tuong_trung` is text with no foreign key to `do_an_kho`.

## Deviations from Plan

None in behaviour. Naming and small additions:

1. **`ImportRowError` instead of `ImportError`**, to avoid shadowing the Python builtin.
2. **Two small helpfulness additions** to the CSV rules: the `;` delimiter fallback and skipping blank rows (Rule 2, input robustness). Both are documented in the README.
3. **Background-index refresh (UX).** The CDP run showed the list still at "Chưa index" right after import, because the index runs in the background after the response. Mutations now invalidate once more after 2 s, and the detail query polls while CHUA_INDEX. This is frontend only and was committed with Task 2.

## MH-13 fidelity gaps

- **Lĩnh vực filter:** not built. It is not in REPO-02/UC5.1 and `do_an_kho` has no such column, as decided at planning.
- **GVHD column:** shows the name without the học vị prefix ("Trần Tấn Minh", not "ThS. …"), because `PersonRef` carries no `hoc_vi`. The GVHD filter Select does include học vị.
- **Sinh viên column:** the table shows the name only; the Drawer shows "Họ tên (mã)" as in the mockup.
- **Extra Drawer field:** "Nguồn" ("Hệ thống (chốt bảo vệ)" / "Import khóa cũ") is not in the mockup.
- **Điểm format:** shown with up to 2 decimals (8.67, 8.5, 7.9).

## Human-check (self-performed, pending user confirmation)

- **Task 1 (API):**
  - I imported the README sample as CSV UTF-8 with BOM and CRLF, plus a broken line `K18,,,,,,`. Result: `{tong_dong 3, thanh_cong 2, loi [{dong 4, Thiếu tên đề tài}]}`.
  - Search results: "thư viện" → 1, "THƯ VIỆN" → 1, "thu vien" → 0 (the collation is accent-sensitive), "học máy" → 1, "%" → 0, "_" → 0.
  - Stored bytes are NFC (checked with HEX). Rows were deleted afterwards.
- **Task 2 (CDP, `scratchpad/cdp0305.py`, 1440×1100):** throwaway K95 cohort (topic 60, committee 20, scores 8.5/8.5/9.0 → archive id 13).
  - p01: DTC225200001 sees the list with no write buttons or Chỉ mục AI column; the keyword search lands in the URL.
  - p02: the SV Drawer; the download really saved `bao-cao-cuoi.pdf` (880 B).
  - p03: GV001 deep link with khoa, GVHD and id.
  - p04–p09: Bộ môn add → "Đã index", edit keywords → "Đã index", forced CHUA_INDEX → "Index lại" → "Đã index", Popconfirm delete.
  - p10/p10b: README CSV import → "Đã nhập 2/3 dòng" + "Dòng 4 · Thiếu tên đề tài", then the list with no "Chưa index" after 3 s.
  - p11: search "thư viện" finds the imported record.
  - Cleanup: 0 K95 cohorts, 0 committees, 0 do_an_kho rows, 0 CDP topics, uploads removed. Chrome stopped.

## Verification

- `docker compose -f deploy/docker-compose.yml up -d --build --wait` (after each task).
- `uv --directory backend run pytest -q`: 47 passed, including the route role-coverage test.
- `bash deploy/e2e-uc2-5.sh`: green 3 times; `do_an_kho` K98 count is 0 afterwards.
- `python3 tools/check-erd-db.py`: OK (no schema change).
- `npm --prefix frontend ci` + `npm run build`: OK.
- `bash deploy/dom-check.sh /kho-do-an 'Mã SV/GV hoặc email'`: OK.
- `dangerouslySetInnerHTML` count: 0.
- All acceptance-criteria greps pass.

## Threat Flags

None beyond the plan's register. T-03-30 (any role downloads the archived final report) is implemented exactly as accepted: only the BAO_CAO_CUOI of a topic that has a `do_an_kho` row.

## Note on `commits`

`git rev-list --count a034b0e..HEAD` = 7 at SUMMARY time. Four of those are concurrent 04-04 and phase-5 commits on main (edd0225, 108640b, b8b1c0a, 13c5c28). This plan's own commits are 0974c6e, cdb7f9d and 98c5285, plus the docs commit.

---
*Phase: 03-outline-progress-defense-archive*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 8 created key files present; commits 0974c6e, cdb7f9d, 98c5285 present in git log.
