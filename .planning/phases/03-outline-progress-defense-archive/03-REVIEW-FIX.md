---
phase: 03-outline-progress-defense-archive
fixed_at: 2026-09-28T08:00:00Z
review_path: .planning/phases/03-outline-progress-defense-archive/03-REVIEW.md
iteration: 1
findings_in_scope: 25
fixed: 24
skipped: 1
status: partial
---

# Phase 3: Code Review Fix Report

**Fixed at:** 2026-09-28
**Source review:** .planning/phases/03-outline-progress-defense-archive/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 25. That is CR-01, WR-01..WR-13 (all fixed), and the 11 Info items, each fixed only if trivial and safe.
- Fixed: 24. Each has its own `fix(03): …` commit on `main`.
- Skipped: 1 (IN-04). It is a refactor, not a trivial fix. See below. Every Critical and Warning finding is fixed.
- **Needs human verification:** WR-02, WR-03, WR-04 and WR-05 change locking and state logic. Each has a reasoned lock order and targeted verification, but no test reproduces real concurrency.

**Where verification ran:** in the **main checkout** on `main`, as instructed ("work on main"). No worktree was used. All numbers below can be reproduced from this tree.

## Policy decisions (autonomous, per the orchestrator's instructions)

| Finding | Decision |
|---|---|
| CR-01 | DOCX limits are now **15 MB** for `word/document.xml` and **25 MB** in total after decompression. `word/document.xml` is parsed as a stream (stdlib `iterparse`, expat). Each element is pruned as soon as it is processed, so no DOM is built. Text is extracted in `read_and_validate`, which runs before any `FOR UPDATE`. `store()` reuses that text. Compose sets `api` `mem_limit: ${API_MEM_LIMIT:-1g}`, and `.env.example` has `API_MEM_LIMIT=1g`. |
| WR-01 | This is the simplest safe way out. Once any score exists, Bộ môn can still **replace members who have not scored** (for example a lecturer who is locked or absent). A member who **has scored cannot be removed**; the API returns 409 and names them. Their score is valid, so they never block finalize. Date, time and room are frozen once any score exists. Existing members, including ones locked after assignment, may stay in the payload. No endpoint deletes scores. It is not needed, because only a member with no score can block finalize, and that member can now be replaced. |
| WR-07 | For **SINH_VIEN**, `doan_trung` is returned only when the source is a **published archive thesis**. That means an `ARCHIVE` ref, or a `DOCUMENT` whose `de_tai` has a `do_an_kho` row: the 04-06 past-cohort seed, or a thesis already finalized. For other sources the student still sees the title, khóa and ratio, but gets `doan_trung = null` and `doan_trung_an = true`, and MH-14 shows a note instead. GV and Bộ môn see every passage, as before. |
| WR-10 | For **SINH_VIEN**, `diem` is null in the archive list and detail **unless the record is the student's own**. GV and Bộ môn see every score. The archive table hides the Điểm column for students. |

## Fixed Issues

### CR-01: DOCX extraction memory DoS inside the topic lock
**Files modified:** `backend/app/services/documents.py`, `deploy/docker-compose.yml`, `deploy/.env.example`
**Commit:** 7310bda
**Applied fix:** `_extract_docx_text` streams the XML and prunes elements as it goes. It maps `w:t`, `w:tab` and `w:br`/`w:cr` the same way python-docx does for paragraph text. It also picks up table paragraphs, which python-docx's `document.paragraphs` skipped. `ValidatedFile` now carries `text`/`text_extracted`. The limits are the ones above, and the api has its own memory limit.
**Checks:**
- A 14 MB `<w:p/>` bomb, 21 KB zipped, peaked at 161 MB RSS for the whole process and was parsed in 2.2 s.
- A 16 MB XML is rejected, returning `None`, which becomes `trich_xuat_loi`.
- The running container reports `HostConfig.Memory = 1073741824`.

### WR-01: committee can become impossible to finalize
**Files modified:** `backend/app/services/defense.py`, `backend/tests/test_defense_flow.py`, `frontend/src/features/defense/CommitteePage.tsx`
**Commit:** 230b7c4
**Applied fix:** Implements the policy above. `_validate_members(keep_ids=…)`. Member and scorer reads now use locks. The test swaps an unscored member C for D after A and B have scored (200). It then checks that removing scorer A gives 409, that changing the room gives 409, that C gets 403 when scoring, and that D's score leads to finalize at 8.5. In the UI, Save stays enabled, and date, time and room are disabled once scores exist.

### WR-02: race between scoring and committee edits; finalize counted non-members
**Files modified:** `backend/app/services/defense.py`
**Commit:** 713da58
**Applied fix:**
- New `_lock_committee_then_schedule` takes a shared lock on `hoi_dong`, then locks `lich_bao_ve`. `score()` and `finalize()` use it, so the lock order is committee then schedule everywhere, and `update_committee` and `add_schedule` only lock the committee.
- `_is_member(lock=True)` reads the latest committed row. Without the lock it would read the REPEATABLE READ snapshot, which is opened by the auth read at the start of the request.
- `finalize` counts only scores joined to current `thanh_vien_hoi_dong` rows, using locking reads.
**Status:** fixed; needs human verification (concurrency logic).

### WR-03: final report resubmitted after scheduling; weak add_schedule checks
**Files modified:** `backend/app/services/defense.py`
**Commit:** 3db3eac
**Applied fix:**
- `add_schedule` locks `de_tai` after the committee.
- It now requires `DA_PHAN_CONG`, a GVHD, `sinh_vien_id`, and an outline in `DA_DUYET`. The outline check has a new 409 message.
- `submit_final_report` reads its "already scheduled" count with a locking read.
**Status:** fixed; needs human verification (locking).

### WR-04: milestone/committee delete races → 500
**Files modified:** `backend/app/services/progress.py`, `backend/app/services/defense.py`
**Commit:** 219e71a
**Applied fix:**
- `submit_report` takes a shared lock on the `moc_tien_do` row.
- `delete_milestone` locks the milestone row, and `delete_committee` locks the committee row, with `FOR UPDATE`. Both count children with locking reads.
- A leftover `IntegrityError` on commit now gives 409.
**Status:** fixed; needs human verification (locking).

### WR-05: stale or duplicate background runs corrupt chi_tiet
**Files modified:** `backend/app/services/document_check.py`
**Commit:** 1fa590d
**Applied fix:**
- `run()` reads `thoi_diem` from the database as its ownership stamp. It only proceeds when the status is `DANG_KIEM_TRA`.
- It commits the read transaction before calling the AI.
- It then deletes and inserts `chi_tiet` and runs `UPDATE … WHERE DANG_KIEM_TRA AND thoi_diem = stamp` in **one short transaction**. If `rowcount != 1`, it rolls everything back. So a record in `LOI` never has details, and two runs never interleave.
- `_mark_loi` is guarded by the stamp too, so a late failure cannot overwrite a recheck.

The stamp is read from the database, not passed from the request, because `thoi_diem` is `DATETIME(0)`. A value passed in with microseconds would never compare equal. The signature `run(ket_qua_id)` is unchanged, so 04-06 can add `nguong_doan`/`loai_tru` and ingest-after-HOAN_TAT on top.

**Checks:** a temporary test, removed afterwards, simulated a recheck during the AI call. The stale run left `DANG_KIEM_TRA` and 0 details. A late failure did not flip the new run to `LOI`. The owning run then reached `HOAN_TAT`. The same test **failed on the pre-fix code** (the stale run wrote `HOAN_TAT`).
**Status:** fixed; needs human verification (state-machine logic).

### WR-06: ref_id read in the wrong namespace
**Files modified:** `backend/alembic/versions/0011_chi_tiet_nguon.py`, `backend/app/models/trung_lap.py`, `backend/app/services/document_check.py`, `docs/chuong-3-thiet-ke/{01-so-do-lop-thuc-the.md,02-thiet-ke-csdl.md,csdl/erd.puml,.svg,.png,so-do-lop/lop-thuc-the.puml,.svg,.png}`
**Commit:** 3ac1397
**Applied fix:**
- Alembic **0011** adds two nullable columns: `chi_tiet_trung_lap.loai_nguon VARCHAR(20)`, with CHECK `TOPIC|ARCHIVE|DOCUMENT`, and `nguon_id BIGINT`, with no FK because the reference is polymorphic.
- `run()` stores the namespace and id for every passage.
- `_label_for(db, loai, ref_id)` resolves `ARCHIVE` through `do_an_kho` and `DOCUMENT` through `tai_lieu_do_an`. An item without `loai` defaults to DOCUMENT, which matches the §3.3.5 `/check-document` contract and the stub.
- `check_document` is still called with a DOCUMENT-namespace `ref_id`.
- ERD, class diagram (`KhongGianNguon` enum) and data dictionary are updated and re-rendered.
- `check-erd-db` and `check-docs class-erd` pass. The live DB head is 0011.

**Compatibility with 04-06:** the archive already ingests only titles, under ARCHIVE (04-05). Document matches are always DOCUMENT (`tai_lieu_do_an.id`), and 04-06 seeds past theses as DOCUMENT. The review's regression test (`tai_lieu_do_an.id == do_an_kho.id`) is left to 04-06, which wires the real document check.

### WR-07: peers' unpublished passages shown to students
**Files modified:** `backend/app/services/document_check.py`, `backend/app/schemas/documents.py`, `backend/app/routers/documents.py`, `backend/tests/test_outline_flow.py`, `frontend/src/features/documents/{api.ts,CheckDetailPage.tsx}`
**Commit:** 71548c8
**Applied fix:** implements the policy above: `detail(db, doc, user)`, `_published_sources`, and a new `CheckSegment.doan_trung_an` field. The test covers three views of the same check:
- the student viewing a match against a peer's outline gets null and the flag;
- the GVHD gets the full text;
- once the peer topic has a `do_an_kho` row, the student sees the text.

### WR-08: CSV import 500s
**Files modified:** `backend/app/services/archive.py`
**Commit:** 450ea0d
**Applied fix:** a `csv.Error` raised while iterating gives 422 "File CSV không hợp lệ gần dòng N: …". An `IntegrityError` or `DataError` on commit rolls back and gives 409. Checked with a cell of 140,000 characters, which now returns 422 where it used to return 500.

### WR-09: editing HE_THONG records overwrote the finalized score and student link
**Files modified:** `backend/app/services/archive.py`, `frontend/src/features/archive/ArchiveFormModal.tsx`
**Commit:** 6168b2e
**Applied fix:** `_apply` skips `diem`, `sinh_vien_id`, `ma_so_sinh_vien` and `ho_ten_sinh_vien` when `nguon == HE_THONG`. The form disables those fields for such records. Verified: a PUT with `diem=1.0` and an empty student ID kept 8.50 and the student link.

### WR-10: every student sees every defense score
**Files modified:** `backend/app/services/archive.py`, `backend/app/routers/archive.py`, `frontend/src/features/archive/ArchivePage.tsx`, `deploy/e2e-uc2-5.sh`
**Commits:** 7892fa3, feb2ed4 (e2e)
**Applied fix:** implements the policy above. In e2e-uc2-5, the owner DTC225200098 now sees 8.5, and another student, DTC225200097, sees the record and its file with `diem = None`. Before this, the script expected 097 to see the score.

### WR-11: registered student not notified when a lecturer-proposed topic is rejected
**Files modified:** `backend/app/services/topic_approval.py`
**Commit:** b4941df
**Applied fix:** the recipient list is the proposer plus the attached student, when the student is not the proposer. One notification goes to each, in the same transaction.

### WR-12: request errors shown as empty states or endless skeletons
**Files modified:** `frontend/src/components/QueryErrorAlert.tsx` (new), `frontend/src/features/{outlines/OutlinePage.tsx,outlines/FinalReportTab.tsx,defense/ScoringPage.tsx,defense/CommitteePage.tsx,dashboard/GvDashboard.tsx,dashboard/BmDashboard.tsx,notifications/NotificationBell.tsx}`
**Commit:** 57d2e84
**Applied fix:** a shared error Alert with a "Thử lại" (refetch) button, shown before any empty or loading branch. ScoringPage keeps 403 mapped to ForbiddenPage and shows this alert for every other error. CommitteePage covers all four of its queries.

### WR-13: failed final-report check could not be re-run from the UI
**Files modified:** `frontend/src/features/documents/RecheckButton.tsx` (new), `frontend/src/features/documents/api.ts`, `frontend/src/features/defense/{CommitteePage.tsx,ScoringPage.tsx}`
**Commit:** 5d9f1af
**Applied fix:**
- A "Kiểm tra lại" button appears next to a `LOI` check in two places: the Bộ môn committee schedule row, and the committee member's scoring panel.
- `useRecheck` now also invalidates the `['defense']` query keys.
- The student's FinalReportTab has no button, because the API only allows GV and Bộ môn to recheck.

### Info items fixed (trivial and safe)
| ID | Commit | Change |
|---|---|---|
| IN-01 | 9a40356 | The recheck route docstring now says committee members may recheck BAO_CAO_CUOI. This is intended, since WR-13 gives the committee a button. |
| IN-02 | 6edad9f | `_safe_basename` shortens the stem and keeps the extension. |
| IN-03 | 761023a | An SV or GV account with no profile now filters on `-1` instead of `IS NULL` (SV/GV dashboards and outline list). |
| IN-05 | 4224e91 | `URL.revokeObjectURL` runs after a 1 s delay. |
| IN-06 | b7318b1 | The upload error title is now "Nộp thất bại", and 413 shows the 20 MB message. |
| IN-07 | b6c7566 | The `HTTPException` import moved to module level. |
| IN-08 | ee585f4 | `remove_schedule` takes an exclusive lock on `hoi_dong`, then on `lich`. |
| IN-09 | c6f6c8a | e2e-uc2-5 cleanup deletes only K98 IMPORT rows with `id > MAX(id)` taken at script start. |
| IN-10 | de62912 | The Bộ môn dashboard returns 404 for an unknown `dot_do_an_id`. |
| IN-11 | e3edfff | Recheck of a `trich_xuat_loi` document returns 409, with a test assertion. The recheck buttons are hidden for these documents, and CheckPanel explains why. |

## Skipped Issues

### IN-04: circular import between `progress` and `dashboard`
**File:** `backend/app/services/progress.py:47`, `backend/app/services/progress.py:303`
**Reason:** skipped as a non-trivial refactor. It means moving `_default_cohort` into a new shared module and updating both importers. Today it works because of import order, and it has no runtime effect. Better done with the next edit to either module.
**Original issue:** `progress` imports `dashboard` (which imports `progress`) only to call the private `_default_cohort`.

## Verification (main checkout, after all fixes)

| Gate | Result |
|---|---|
| `docker compose -f deploy/docker-compose.yml up -d --build --wait` | all healthy; api `mem_limit` 1 GiB; alembic head **0011** |
| backend `uv --directory backend run pytest -q` | **51 passed** (no new test files; assertions added to test_defense_flow and test_outline_flow) |
| ai-service `uv --directory ai-service run pytest -q` | **5 passed** |
| `deploy/smoke-test.sh` | all checks passed |
| `deploy/e2e-uc1.sh` | OK |
| `deploy/e2e-uc2-5.sh` | OK, including the new WR-10 check |
| `deploy/e2e-ai.sh` | OK |
| `npm run build` (frontend) | OK |
| `python3 tools/check-erd-db.py` / `tools/check-docs.py class-erd` | OK / OK |
| Leftovers | 0 K96–K99 cohorts; AI index_size 300 (unchanged) |

## Notes for 04-06

- `document_check.run(ket_qua_id)` keeps its signature. Plan 04-06 plugs in at four points:
  - `nguong_doan` and `loai_tru` go into the `check_document(doc_id, text)` call. That call now sits between the read commit and the write transaction.
  - The `vi_tri` signal suffix is added where `ChiTietTrungLap` is built.
  - `ingest_document` runs after the final `commit()`, only when the stamped UPDATE matched.
  - The `AiServiceError`/`LOI` path stays stamp-guarded.
- A fake `check_document` in tests must accept `**kwargs`. The existing `_boom(self, ref_id, text, top_k=5)` in test_outline_flow will need `**kw` once 04-06 passes keyword arguments.

---

_Fixed: 2026-09-28_
_Fixer: Developer (code-fixer)_
_Iteration: 1_
