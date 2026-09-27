---
phase: 01-analysis-design
plan: 05
subsystem: database
tags: [plantuml, mysql, uml-class-diagram, erd, soa, fastapi, sequence-diagram]

# Dependency graph
requires:
  - phase: 01-analysis-design (plan 01-02, tracer)
    provides: 6 tracer classes/tables (SinhVien/GiangVien/DotDoAn/DeTai/KetQuaKiemTraTrungLap/ChiTietTrungLap) and docs/README.md conventions
  - phase: 01-analysis-design (plan 01-03, 01-04)
    provides: full FR table (§2.3), NFR table (§2.4), UC specs (UC0/UC1/UC4), ARCHITECTURE.md research
provides:
  - Full entity class diagram (19 classes, 13 enums) covering every FR and MAU field
  - 3 state machines (DeTai, DeCuong, KetQuaKiemTraTrungLap)
  - thesis_core ERD (19 tables, 1:1 with classes) and thesis_ai ERD (chunk/embedding/index_metadata)
  - Data dictionary, class<->table mapping, integrity/concurrency rules (§3.2.5)
  - SOA architecture: component + deployment diagrams, sync/async D-07 sequence diagrams, AI service API contract
affects: [01-06 (mockups, reads class model for screen data), 01-07 (final assembly, numbering, GIẢ ĐỊNH label removal), Phase 2 (Alembic migration generated from erd.puml)]

# Actuals (#2632)
actuals:
  tokens: 19937
  tasks: 3
  commits: 5
  plan_head_before: f789ba6a637ec6f9becbda28b69233c9f007931d
  plan_head_after: 79df62bdcc99e174e5ad3e0f6bd88bdaf29b9787

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PlantUML class diagrams must connect every enum via a `..>` dependency line to its owning class — leaving enums as disconnected 1-node components crashes the Smetana layout engine (used when Graphviz `dot` is absent) with a nondeterministic ArrayIndexOutOfBoundsException"
    - "Avoid literal Unicode comparison operators (≤/≥) inside PlantUML alt/loop condition headers — falls back to a missing-glyph box in that font path even when the same glyph renders fine as body text; use ASCII (<=/>=) instead"
    - "MySQL generated column + UNIQUE index (NULL-permissive) for 'at most one active X per Y' constraints; conditional UPDATE ... WHERE col IS NULL checked by affected-row count for 'first writer wins' race conditions"

key-files:
  created:
    - docs/chuong-3-thiet-ke/so-do-lop/trang-thai-de-tai.puml
    - docs/chuong-3-thiet-ke/so-do-lop/trang-thai-de-cuong.puml
    - docs/chuong-3-thiet-ke/so-do-lop/trang-thai-kiem-tra-trung-lap.puml
    - docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.puml
    - docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md
    - docs/chuong-3-thiet-ke/kien-truc/component.puml
    - docs/chuong-3-thiet-ke/kien-truc/deployment.puml
    - docs/chuong-3-thiet-ke/kien-truc/seq-check-title.puml
    - docs/chuong-3-thiet-ke/kien-truc/seq-check-document.puml
  modified:
    - docs/chuong-3-thiet-ke/01-so-do-lop-thuc-the.md
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml
    - docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md
    - docs/chuong-3-thiet-ke/csdl/erd.puml
    - docs/README.md
    - docs/truy-vet.md

key-decisions:
  - "DeTai state machine: two entry paths into DA_PHAN_CONG — GV-proposed topics go CHO_DUYET -> DA_DUYET (còn trống) -> SV registers (back to CHO_DUYET) -> DA_PHAN_CONG; SV-proposed (or SV-attached) topics go CHO_DUYET -> DA_PHAN_CONG directly. Reconciled from UC1.2/UC1.3 spec wording already locked in 01-04."
  - "1 SV : 1 active topic enforced via a MySQL generated column (de_tai.sinh_vien_id_dang_hoat_dong) + UNIQUE index, not an application-only check — NULLs (inactive states) don't collide."
  - "1 topic : 1 SV under concurrent registration enforced via conditional UPDATE ... WHERE sinh_vien_id IS NULL + affected-row check (documented in §3.2.5), not check-then-act."
  - "ket_qua_kiem_tra_trung_lap.tai_lieu_do_an_id is UNIQUE — one check result per document version, so a late AI response for an older version can never overwrite a newer version's result (two independent rows, not an update-in-place)."
  - "19 classes map 1:1 to 19 thesis_core tables — no bảng liên kết/kỹ thuật exception needed (ThanhVienHoiDong and DiemBaoVe are modeled as first-class classes, not hidden join tables)."

patterns-established:
  - "Pattern: any future PlantUML class diagram with enum blocks in this repo must add a dependency line per enum (see lop-thuc-the.puml bottom section) to avoid the Smetana render crash."

requirements-completed: [DSGN-01, DSGN-02, DSGN-03]

coverage:
  - id: D1
    description: "Full entity class diagram (19 classes: TaiKhoan, SinhVien, GiangVien, DotDoAn, MocTienDo, DeTai, DeCuong, TaiLieuDoAn, LuotDuyetDeCuong, BaoCaoTienDo, HoiDong, ThanhVienHoiDong, LichBaoVe, DiemBaoVe, DoAnKho, KetQuaKiemTraTrungLap, ChiTietTrungLap, ThongBao, CauHinhNguong) with 3 state machines"
    requirement: "DSGN-01"
    verification:
      - kind: automated_ui
        ref: "bash tools/render-diagrams.sh docs/chuong-3-thiet-ke/so-do-lop && python3 tools/check-docs.py render docs/chuong-3-thiet-ke/so-do-lop"
        status: pass
      - kind: other
        ref: "python3 tools/check-docs.py pi-tags + links docs/chuong-3-thiet-ke/01-so-do-lop-thuc-the.md"
        status: pass
    human_judgment: false
  - id: D2
    description: "thesis_core ERD (19 tables matching classes 1:1) + thesis_ai ERD (chunk/embedding/index_metadata) + data dictionary + integrity/concurrency rules"
    requirement: "DSGN-02"
    verification:
      - kind: other
        ref: "python3 tools/check-docs.py class-erd"
        status: pass
      - kind: other
        ref: "python3 tools/check-docs.py trace FR-DT-01 FR-DT-02"
        status: pass
      - kind: automated_ui
        ref: "bash tools/render-diagrams.sh docs/chuong-3-thiet-ke/csdl"
        status: pass
    human_judgment: false
  - id: D3
    description: "SOA architecture: component + deployment diagrams (3 separate components, AI service unreachable via Apache), sync title-check + async document-check D-07 sequences, AI service API contract"
    requirement: "DSGN-03"
    verification:
      - kind: other
        ref: "grep checks for /check-title, /check-document, 202, LOI, 127.0.0.1:8002, /ingest, X-API-Key across kien-truc/*.puml and 03-kien-truc-he-thong.md"
        status: pass
      - kind: other
        ref: "python3 tools/check-docs.py privacy docs/chuong-3-thiet-ke/"
        status: pass
      - kind: manual_procedural
        ref: "docs/chuong-3-thiet-ke/kien-truc/component.png, deployment.png (viewed via Read tool)"
        status: pass
    human_judgment: true
    rationale: "Plan's own <human-check> block requires a human to visually confirm no line connects Apache/browser to the AI service — self-performed here per sequential_execution autonomous-run instructions (user asleep); flagged below for user confirmation on next review."

duration: 36min
completed: 2026-09-27
status: complete
---

# Phase 1 Plan 5: Full Entity Class Diagram, thesis_core/thesis_ai ERDs, SOA Architecture Summary

**Full 19-class/19-table domain model with 3 state machines, thesis_core ⟷ thesis_ai ERDs verified entity-by-entity (`class-erd` passes), and SOA architecture (component/deployment/sync+async D-07 sequences) locking the AI service as internal-only.**

## Performance

- **Duration:** 36 min
- **Started:** 2026-09-27T19:20:00Z
- **Completed:** 2026-09-27T19:56:00Z
- **Tasks:** 3
- **Files modified:** 35 (docs only; 2 additional consistency-fix files in a 4th deviation commit)

## Accomplishments
- Extended the tracer's 6-class/6-table slice to the full 19-class entity model (13 enums) and 19-table `thesis_core` ERD, kept in exact 1:1 correspondence (`class-erd` check passes with zero "bảng liên kết" exceptions needed)
- Modeled 3 state machines (Đề tài, Đề cương, Kết quả kiểm tra trùng lặp) reconciled against the already-locked UC1.2/UC1.3/UC2.2/UC0.7 specs from plan 01-04, including the two-path GV-proposed vs SV-proposed đề tài approval flow
- Designed the AI service's independent `thesis_ai` schema (chunk/embedding/index_metadata) with zero foreign keys into `thesis_core`, and wrote the concurrency/integrity rules that make "1 SV : 1 active topic" and "1 topic : 1 SV under concurrent registration" real database guarantees, not just application checks
- Produced the full SOA architecture: component diagram (3 separately deployable components, AI service reachable only from the Web API's AI client), deployment diagram (AI service bound to 127.0.0.1:8002, no Apache route), and both D-07 sequence diagrams (sync title-check, async document-check with 202/polling/LOI/version-overwrite-safety)

## Task Commits

Each task was committed atomically:

1. **Task 1: Full entity class diagram and state machines (§3.1)** - `b109b47` (feat)
2. **Task 2: thesis_core and thesis_ai ERDs, data dictionary, mapping and integrity rules (§3.2)** - `bb2aa50` (feat)
3. **Task 3: SOA architecture — component, deployment, D-07 sequence diagrams and AI service contract (§3.3)** - `c58c4c0` (feat)

**Deviation fix:** `79df62b` (docs — stale filename reference cleanup, see below)

**Plan metadata:** (this commit, follows SUMMARY)

## Files Created/Modified
- `docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml` - 19-class entity model + 13 enums + enum dependency lines (render-crash fix)
- `docs/chuong-3-thiet-ke/so-do-lop/trang-thai-de-tai.puml` - Đề tài state machine (NHAP→CHO_DUYET→DA_DUYET/TU_CHOI→DA_PHAN_CONG)
- `docs/chuong-3-thiet-ke/so-do-lop/trang-thai-de-cuong.puml` - Đề cương state machine (submit/review/revise loop)
- `docs/chuong-3-thiet-ke/so-do-lop/trang-thai-kiem-tra-trung-lap.puml` - Duplicate-check result state machine (never stuck in DANG_KIEM_TRA)
- `docs/chuong-3-thiet-ke/01-so-do-lop-thuc-the.md` - §3.1 full class table (FR citations) + 3 transition tables
- `docs/chuong-3-thiet-ke/csdl/erd.puml` - 19-table thesis_core ERD with generated-column uniqueness rule
- `docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.puml` - thesis_ai ERD (chunk/embedding/index_metadata)
- `docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md` - §3.2 full data dictionary (19 tables), mapping table, integrity/concurrency rules
- `docs/chuong-3-thiet-ke/kien-truc/component.puml` - 3-component SOA diagram with 5 AI service provided interfaces
- `docs/chuong-3-thiet-ke/kien-truc/deployment.puml` - single-host deployment, AI service bound to 127.0.0.1:8002
- `docs/chuong-3-thiet-ke/kien-truc/seq-check-title.puml` - synchronous title-check sequence (UC0.6)
- `docs/chuong-3-thiet-ke/kien-truc/seq-check-document.puml` - asynchronous document-check sequence (UC0.7)
- `docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md` - §3.3 full architecture writeup (§3.3.1–3.3.8)
- `docs/README.md`, `docs/truy-vet.md` - stale `03-kien-truc.md` filename references corrected to `03-kien-truc-he-thong.md`

## Decisions Made
- Reconciled the Đề tài state machine's "Đã duyệt" (còn trống) intermediate state against the existing UC1.2/UC1.3 spec text (already locked by plan 01-04) rather than inventing a new flow — see `key-decisions` in frontmatter.
- Chose a MySQL generated column + UNIQUE index for the "1 SV : 1 active topic" rule (NULLs excluded from uniqueness) instead of an application-only check, per the plan's explicit recommendation.
- Modeled `ThanhVienHoiDong` and `DiemBaoVe` as first-class classes (not hidden join tables) so all 19 classes map 1:1 to all 19 tables with no "bảng liên kết" exceptions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] PlantUML Smetana layout engine crash on the class diagram**
- **Found during:** Task 1, first render attempt
- **Issue:** `bash tools/render-diagrams.sh docs/chuong-3-thiet-ke/so-do-lop` failed with `java.lang.ArrayIndexOutOfBoundsException: Index 15 out of bounds for length 12` inside PlantUML's Smetana layout engine (used because Graphviz `dot` is not installed on this machine and no passwordless sudo is available to install it). Bisection confirmed: the crash is caused by the 13 `enum` blocks being fully disconnected (0-degree) nodes alongside the one large connected component of 19 classes — reproduced 13/13 times with enums present, 0/13 without.
- **Fix:** Added a `..>` dependency line from one representative class to each enum (13 lines total), making every enum part of the single connected component. No content/semantics change — purely a rendering fix.
- **Files modified:** docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml
- **Verification:** Rendered successfully on the very next attempt and on 3 subsequent forced re-renders; PNG visually inspected (all 19 classes + 13 enums legible, no missing edges).
- **Committed in:** b109b47 (Task 1 commit)

**2. [Rule 1 - Bug] Missing-glyph box for "≤" in sequence diagram alt/loop headers**
- **Found during:** Task 3, after rendering seq-check-title.puml / seq-check-document.puml
- **Issue:** The literal "≤" character (used in "≤ 5s"/"≤ 30s"/"≤ 20MB" condition labels) rendered as a visible missing-glyph box specifically in `alt`/`loop` header text, even though the same glyph would render fine as ordinary body text elsewhere.
- **Fix:** Replaced "≤ Ns" with ASCII "<= N giây"/"<= 20MB" in the three affected labels.
- **Files modified:** docs/chuong-3-thiet-ke/kien-truc/seq-check-title.puml, docs/chuong-3-thiet-ke/kien-truc/seq-check-document.puml
- **Verification:** Re-rendered and visually re-inspected — all text legible, no glyph boxes.
- **Committed in:** c58c4c0 (Task 3 commit)

**3. [Rule 1 - Bug] Stale `03-kien-truc.md` filename references**
- **Found during:** Task 3, while writing 03-kien-truc-he-thong.md
- **Issue:** `docs/README.md`'s directory map and `docs/truy-vet.md`'s DSGN-03 traceability row still named a pre-01-05 placeholder filename (`03-kien-truc.md`), which 01-05-PLAN.md and 01-07-PLAN.md both consistently supersede with `03-kien-truc-he-thong.md`. Left uncorrected, both would be dangling/misleading references once this plan's file existed under the real name.
- **Fix:** Updated both one-line references to the real filename.
- **Files modified:** docs/README.md, docs/truy-vet.md
- **Verification:** `grep -rn "03-kien-truc\.md"` across docs/ now returns nothing.
- **Committed in:** 79df62b (separate small deviation commit, after Task 3)

---

**Total deviations:** 3 auto-fixed (2 render bugs, 1 stale reference)
**Impact on plan:** All three fixes were necessary for the deliverables to actually render/navigate correctly; none changed the domain model, schema, or architecture content specified by the plan. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required

None - no external service configuration required.

## Human-check (self-performed, pending user confirmation)

Per this run's `<sequential_execution>` instructions (autonomous overnight run, user asleep), the plan's `<human-check>` block for Task 3 was self-performed rather than paused on:

- **Test:** Opened `docs/chuong-3-thiet-ke/kien-truc/component.png` and `deployment.png` (via the Read tool, i.e. actually viewed the rendered images, not just confirmed file existence).
- **Observed:** Three separate components clearly visible (Client React; Web API package with 8 internal modules + AI client; Dịch vụ AI package with 4 internal modules behind 5 lollipop interfaces). Apache has exactly two outgoing edges: to the client build (implied) and to the Web API's "Xác thực & phân quyền" module labeled `/api/*`. No edge connects Apache or Client directly to the Dịch vụ AI package — the only edges into it are dashed lines from the Web API's "AI client" module to the 5 provided interfaces. Web API's business modules connect only to `MySQL thesis_core`; the AI service's `Mô hình embedding`/`Chỉ mục vector` modules connect only to `MySQL thesis_ai`. The deployment diagram shows the AI service uvicorn process bound to `127.0.0.1:8002` with an explicit note that Apache has no `ProxyPass` to that port.
- **Conclusion:** Matches the plan's expected outcome exactly.
- **Flag for user:** Please re-open both PNGs on your own next session and confirm this reading — this check was self-performed by the executing agent, not by you.

## Next Phase Readiness
- Plan 01-06 (mockups) can proceed independently — it only touches `04-thiet-ke-giao-dien.md` and `mockup/`, disjoint from this plan's files.
- Plan 01-07 (final assembly) has everything it needs from this plan: figure numbering placeholders (`Hình 3.x`), the `03-kien-truc-he-thong.md` filename now consistently referenced everywhere, and a fully populated §3.1/§3.2/§3.3.
- Phase 2's Alembic migration can be generated directly from `docs/chuong-3-thiet-ke/csdl/erd.puml` — all 19 tables, types, and the generated-column uniqueness rule are specified.
- No blockers.

---
*Phase: 01-analysis-design*
*Completed: 2026-09-27*

## Self-Check: PASSED

All 16 files listed in Files Created/Modified (plus the SUMMARY itself) confirmed present on disk; all 4 commit hashes (b109b47, bb2aa50, c58c4c0, 79df62b) confirmed present in `git log --oneline --all`.
