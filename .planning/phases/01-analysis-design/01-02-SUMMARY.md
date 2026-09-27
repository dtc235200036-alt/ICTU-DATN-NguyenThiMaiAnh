---
phase: 01-analysis-design
plan: 02
subsystem: docs
tags: [plantuml, drawio, headless-chrome, bpmn, ant-design, mockup, tracer, ANLS-02, ANLS-03, ANLS-05, DSGN-01, DSGN-02, DSGN-04]

requires:
  - phase: 01-analysis-design (plan 01-01)
    provides: "tai-lieu-goc/ collection area and survey kit conventions this plan does not touch"
provides:
  - "Documentation toolchain: tools/render-diagrams.sh (PlantUML + draw.io + headless-Chrome mockup screenshots), tools/check-docs.py (11 subcommands), tools/plantuml.cfg"
  - "UC1.1 traced end-to-end: BPMN TO-BE -> FR-DT-01/02 -> UC1.1 spec -> DeTai/KetQuaKiemTraTrungLap classes -> de_tai/ket_qua_kiem_tra_trung_lap tables -> MH-06 HTML mockup -> docs/truy-vet.md matrix row"
  - "UC1 complete in Chapter 2: AS-IS (3 lanes, assumption-marked) + TO-BE (4 lanes, UC1.1-1.4) BPMN, FR-DT-01..07, UC1.1-1.4 specs, activity diagram"
  - "Shared Ant Design v5 admin stylesheet (antd-admin.css) and MH-06 static HTML mockup + 1440px PNG"
  - "docs/README.md: ID conventions, Mã PI tag, assumption marker, UC spec format, class<->table naming, mockup conventions, render/check commands"
affects: ["01-03", "01-04", "01-05", "01-06", "01-07"]

actuals:
  tokens: 51080
  tasks: 2
  commits: 2

tech-stack:
  added: ["PlantUML 1.2026.8 (smetana layout, no Graphviz)", "draw.io docker exporter rlespinasse/drawio-desktop-headless:v1.72.0", "Google Chrome 149 headless screenshot"]
  patterns: ["step-code BPMN labels (TB-DT-NN / AS-DT-NN)", "Ant Design v5 CSS-variable token sheet shared by all mockup screens", "UC spec table format (Thuộc tính | Nội dung)", "FR -> UC -> BPMN step -> class -> table -> màn hình trace matrix row"]

key-files:
  created:
    - tools/render-diagrams.sh
    - tools/plantuml.cfg
    - tools/check-docs.py
    - docs/README.md
    - docs/truy-vet.md
    - docs/chuong-2-khao-sat-phan-tich/02-quy-trinh-nghiep-vu.md
    - docs/chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md
    - docs/chuong-2-khao-sat-phan-tich/06-dac-ta-uc1-quan-ly-de-tai.md
    - docs/chuong-2-khao-sat-phan-tich/bpmn/01-de-tai.drawio
    - docs/chuong-2-khao-sat-phan-tich/uc/uc1-quan-ly-de-tai.puml
    - docs/chuong-2-khao-sat-phan-tich/uc/act-uc1-de-xuat-dang-ky-de-tai.puml
    - docs/chuong-3-thiet-ke/01-so-do-lop-thuc-the.md
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml
    - docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md
    - docs/chuong-3-thiet-ke/csdl/erd.puml
    - docs/chuong-3-thiet-ke/04-thiet-ke-giao-dien.md
    - docs/chuong-3-thiet-ke/mockup/antd-admin.css
    - docs/chuong-3-thiet-ke/mockup/mh-06.html
  modified: []

key-decisions:
  - "draw.io docker exporter needs --shm-size=1g or the Electron renderer crashes on non-trivial diagrams (silent 'Empty export data' with no size hint in the error) -- discovered via debug XML round-trip export, then confirmed at scale 1 vs scale 2"
  - "draw.io docker page-index is 1-based on v1.72.0 (not 0-based as some docs imply) -- confirmed empirically before writing the export logic"
  - "AS-IS BPMN and step-table rows are explicitly marked 'GIẢ ĐỊNH — chờ xác nhận' per D-01/D-02 (no interviews conducted yet); docs/README.md documents the rule that the marker is only removed once a BB-*/TL-* source is cited (plan 01-07)"
  - "design-taste-frontend skill self-declares out of scope for dashboards/admin panels; per D-12 (Ant Design admin locked), only its neutral anti-slop principles were applied, its design-system guidance was overridden -- documented in docs/chuong-3-thiet-ke/04-thiet-ke-giao-dien.md §3.4.1"
  - "check-docs.py 'all' and 'truy-vet --complete' are intentionally strict (fail today) since most of chapter 2/3 content is built by later plans 01-03..01-07 -- verified this is expected, not a bug, before finishing"

requirements-completed: [ANLS-02, ANLS-03, ANLS-05, DSGN-01, DSGN-02, DSGN-04]

coverage:
  - id: D1
    description: "One-command render of every *.puml (PNG+SVG, smetana fallback), *.drawio page, and mockup/mh-NN.html (headless Chrome at declared width) without Graphviz or Figma"
    requirement: "ANLS-02"
    verification:
      - kind: other
        ref: "bash tools/render-diagrams.sh docs (plan Task 1+2 <verify>)"
        status: pass
    human_judgment: false
  - id: D2
    description: "UC1.1 traceable end-to-end: BPMN -> FR-DT-01/02 -> UC1.1 spec -> DeTai/KetQuaKiemTraTrungLap -> de_tai/ket_qua_kiem_tra_trung_lap -> MH-06 -> truy-vet.md row"
    requirement: "ANLS-05"
    verification:
      - kind: other
        ref: "python3 tools/check-docs.py trace FR-DT-01 FR-DT-02 (plan Task 1+2 <verify>)"
        status: pass
    human_judgment: false
  - id: D3
    description: "BPMN AS-IS (3 lanes) + TO-BE (4 lanes incl. Hệ thống) for Quản lý đề tài, with start/end events"
    requirement: "ANLS-02"
    verification:
      - kind: other
        ref: "python3 tools/check-docs.py bpmn docs/chuong-2-khao-sat-phan-tich/bpmn/01-de-tai.drawio (plan Task 2 <verify>)"
        status: pass
    human_judgment: false
  - id: D4
    description: "UC1.1-UC1.4 fully specified (actors, pre/post-conditions, main/alternate/exception flows) plus an activity diagram covering propose->check->submit->approve/reject->assign"
    requirement: "ANLS-05"
    verification:
      - kind: other
        ref: "grep -cE '^#### UC1\\.[1-4] ' 06-dac-ta-uc1-quan-ly-de-tai.md >= 4; act-uc1-de-xuat-dang-ky-de-tai.png embedded (plan Task 2 <verify>/acceptance_criteria)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Entity classes (DeTai, KetQuaKiemTraTrungLap, ChiTietTrungLap, ...) and matching ERD tables with utf8mb4_vietnamese_ci"
    requirement: "DSGN-01, DSGN-02"
    verification:
      - kind: other
        ref: "python3 tools/check-docs.py class-erd (plan Task 1 <verify>)"
        status: pass
    human_judgment: false
  - id: D6
    description: "MH-06 static HTML/CSS mockup (Ant Design admin look, no Figma) rendered to an exact-1440px PNG, linked and embedded in §3.4"
    requirement: "DSGN-04"
    verification:
      - kind: other
        ref: "PNG width check + grep for antd-admin.css link + no-script/no-remote-resource grep (plan Task 1 <verify>); python3 tools/check-docs.py mockup MH-06 (plan Task 2 <verify>)"
        status: pass
    human_judgment: true
    rationale: "Visual legibility, Vietnamese diacritic rendering, and 'looks like a real Ant Design admin page' were self-performed by the executor (viewed all 3 required PNGs with the Read tool) per explicit orchestrator instruction to not halt for the sleeping user; a human should still glance at mockup/mh-06.png before plan 01-06 copies its conventions to 13 more screens."
  - id: D7
    description: "docs/README.md publishes conventions (IDs, PI tag, assumption marker, caption rule, render/check commands) for plans 01-03..01-07 to follow"
    verification:
      - kind: other
        ref: "grep checks for ID-prefix table, 'Mã PI:', 'GIẢ ĐỊNH', mockup conventions, render/check commands (plan Task 2 acceptance_criteria)"
        status: pass
    human_judgment: false

duration: 32min
completed: 2026-09-28
status: complete
---

# Phase 1 Plan 2: Tracer Toolchain and UC1 (Quản lý đề tài) Summary

**Documentation toolchain (PlantUML + draw.io docker exporter + headless-Chrome mockup screenshots + an 11-subcommand consistency checker) proven end-to-end with the UC1.1 tracer slice, then UC1 completed in Chapter 2 (AS-IS/TO-BE BPMN, FR-DT-01..07, UC1.1-1.4 specs, activity diagram) and the shared documentation conventions published.**

## Performance

- **Duration:** ~32 min
- **Started:** 2026-09-27T18:20:00Z
- **Completed:** 2026-09-27T18:52:04Z
- **Tasks:** 2
- **Files created:** 29 (see key-files; includes rendered PNG/SVG siblings)

## Accomplishments

- `tools/render-diagrams.sh`: one command renders every `.puml` (PlantUML, `-Playout=smetana` fallback since Graphviz `dot` is not installed), every `.drawio` page (draw.io exporter chain: CLI -> docker `rlespinasse/drawio-desktop-headless:v1.72.0` -> AppImage -> manual-export message), and every `mockup/mh-NN.html` (headless Chrome screenshot at the width/height declared in its `mockup-size` meta tag). No jar or AppImage is committed to the repo.
- `tools/check-docs.py`: 11 subcommands (`render`, `links`, `pi-tags`, `privacy`, `class-erd`, `trace`, `req-coverage`, `truy-vet`, `bpmn`, `mockup`, `all`), stdlib-only Python 3, each printing `path:line: message` failures and exiting 1/0/2.
- UC1.1 (Đề xuất đề tài) traced end-to-end: BPMN TO-BE steps TB-DT-01/02/03/04/05/06 -> FR-DT-01/FR-DT-02 -> UC1.1 spec -> `DeTai`/`KetQuaKiemTraTrungLap`/`ChiTietTrungLap` classes -> `de_tai`/`ket_qua_kiem_tra_trung_lap`/`chi_tiet_trung_lap` tables -> MH-06 HTML mockup -> a row in `docs/truy-vet.md`.
- BPMN AS-IS (Sinh viên/Giảng viên/Bộ môn lanes, manual email/Excel/paper process, explicitly marked `GIẢ ĐỊNH — chờ xác nhận`) and an extended TO-BE (adds UC1.2 đăng ký, UC1.3 duyệt+phân công GVHD, UC1.4 xem/lọc, continuing step codes TB-DT-07..18).
- UC1.2, UC1.3, UC1.4 specified in the same table+flow format as UC1.1 in `06-dac-ta-uc1-quan-ly-de-tai.md`; activity diagram `act-uc1-de-xuat-dang-ky-de-tai.puml` with 4 swimlanes (Sinh viên/Giảng viên/Hệ thống/Bộ môn) covering the full propose-to-assign path.
- `docs/chuong-3-thiet-ke/mockup/antd-admin.css` (Ant Design v5 tokens: 11 pinned `--ant-*` custom properties plus derived tokens) and `mockup/mh-06.html` (Sinh viên sider+header, đề xuất form, yellow warning Alert with a 3-row similarity table and Progress bars) rendered to a 1440px-wide PNG.
- `docs/README.md` fixes ID-prefix conventions, the `Mã PI:` tag line, the `GIẢ ĐỊNH — chờ xác nhận` assumption marker rule, the UC spec table format, class↔table naming, the trace-matrix header, caption numbering, pandoc-safe Markdown rules, mockup conventions, privacy rules, and the render/check commands for plans 01-03..01-07 to follow.

## Task Commits

Each task was committed atomically:

1. **Task 1 (TRACER): UC1.1 end-to-end through toolchain, BPMN, FR, UC spec, class, ERD, HTML mockup MH-06 and truy-vet** - `c8f9277` (feat)
2. **Task 2: Complete UC1 in Chapter 2 (AS-IS + full TO-BE, FR-DT, UC1.2-1.4, activity) and publish conventions** - `0f99f2a` (feat)

**Plan metadata:** commit to follow (this SUMMARY + STATE/ROADMAP update)

## Files Created/Modified

- `tools/render-diagrams.sh` - render-everything CLI (`--check`, `--force`, PATH args), 3 renderer types
- `tools/plantuml.cfg` - shared skinparams (Noto Sans, no shadow, dpi 150)
- `tools/check-docs.py` - 11-subcommand consistency checker
- `docs/README.md` - Phase-1 documentation conventions
- `docs/truy-vet.md` - PI/requirement/functional trace matrices
- `docs/chuong-2-khao-sat-phan-tich/02-quy-trinh-nghiep-vu.md` - §2.2, AS-IS + TO-BE BPMN narrative and step tables
- `docs/chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md` - §2.3, FR-DT-01..07
- `docs/chuong-2-khao-sat-phan-tich/06-dac-ta-uc1-quan-ly-de-tai.md` - §2.6.1, UC1.1-1.4 specs
- `docs/chuong-2-khao-sat-phan-tich/bpmn/01-de-tai.drawio` (+ `-as-is.png`, `-to-be.png`) - BPMN source and renders
- `docs/chuong-2-khao-sat-phan-tich/uc/uc1-quan-ly-de-tai.puml` (+ .png/.svg) - UC1 use-case diagram
- `docs/chuong-2-khao-sat-phan-tich/uc/act-uc1-de-xuat-dang-ky-de-tai.puml` (+ .png/.svg) - activity diagram
- `docs/chuong-3-thiet-ke/01-so-do-lop-thuc-the.md`, `so-do-lop/lop-thuc-the.puml` (+ .png/.svg) - §3.1, entity classes
- `docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md`, `csdl/erd.puml` (+ .png/.svg) - §3.2, ERD
- `docs/chuong-3-thiet-ke/04-thiet-ke-giao-dien.md` - §3.4, conventions + 14-row screen inventory + MH-06 section
- `docs/chuong-3-thiet-ke/mockup/antd-admin.css`, `mockup/mh-06.html` (+ `mh-06.png`) - shared stylesheet and MH-06 mockup

## Decisions Made

See frontmatter `key-decisions`. Highlights: the draw.io docker exporter requires `--shm-size=1g` or the Electron renderer silently crashes (`Error: Empty export data`) on anything beyond a single trivial shape — discovered by round-tripping an XML export first, then bisecting `--scale 1` vs `--scale 2` vs `--shm-size`; page-index for `rlespinasse/drawio-desktop-headless:v1.72.0` is 1-based (confirmed empirically with a 2-page test file before writing the export logic, not assumed from docs).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] draw.io docker exporter crashed on real diagrams**
- **Found during:** Task 1, first BPMN render attempt
- **Issue:** `docker run ... rlespinasse/drawio-desktop-headless:v1.72.0 ... --scale 2 ...` produced `Renderer process crashed` / `Error: Empty export data` on the actual BPMN pool+lanes+shapes diagram (the earlier smoke test with one rectangle had worked, masking this).
- **Fix:** Added `--shm-size=1g` to the docker invocation in `tools/render-diagrams.sh`. Verified scale 1 also worked without it, isolating the cause to `/dev/shm` size under Chromium at scale 2, not the XML content.
- **Files modified:** tools/render-diagrams.sh
- **Verification:** Re-rendered the full BPMN file (2 pages) successfully; visually confirmed via the Read tool.
- **Committed in:** c8f9277 (Task 1 commit)

**2. [Rule 1 - Bug] `check-docs.py links` flagged directory links and a literal Markdown-syntax example as broken**
- **Found during:** Task 1 and Task 2 full `<verify>` runs
- **Issue:** (a) `links` only accepted `os.path.isfile`, so a link to a directory (`khao-sat/`) was reported broken; (b) `docs/README.md`'s own explanation of image-embed syntax was rewritten in Task 2 rather than escaped, but the checker also needed a general fix: it scanned inline-backtick code spans as if they were real links.
- **Fix:** `links` now accepts `os.path.isdir` targets too, and skips fenced code blocks (` ``` `) when scanning for link syntax; the one remaining false-positive line (an inline-code example of image syntax) was reworded in prose instead of relying on the checker to special-case inline code spans.
- **Files modified:** tools/check-docs.py, docs/README.md
- **Verification:** `python3 tools/check-docs.py links docs` exits 0.
- **Committed in:** c8f9277 (directory-link fix), 0f99f2a (fence-skip fix + README reword)

---

**Total deviations:** 2 auto-fixed (1 blocking/tooling, 1 bug). **Impact:** Both were necessary for the render/check toolchain to actually work end-to-end on this machine; no scope creep beyond the plan's own toolchain requirements.

## Issues Encountered

None beyond the deviations above.

## Human-check (self-performed, pending user confirmation)

Per explicit orchestrator instruction (autonomous overnight execution; user asleep), the Task 1 tracer `<human-check>` was self-performed by the executor instead of halting at a checkpoint:

- **Checked:** `docs/chuong-2-khao-sat-phan-tich/bpmn/01-de-tai-to-be.png`, `docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.png`, and `docs/chuong-3-thiet-ke/mockup/mh-06.png` (viewed directly with the Read tool's image rendering, not inferred from file existence).
- **Result:** Vietnamese diacritics render correctly in all three PNGs (confirmed via the drawio and PlantUML renders, and the Chrome screenshot). The BPMN TO-BE diagram shows all 4 lanes (Sinh viên, Giảng viên, Bộ môn, Hệ thống) with legible labels, correctly styled start/end events, an exclusive gateway, and a visually distinct service task. MH-06 looks like a genuine Ant Design admin page (dark sider, header with breadcrumb/bell/user, form, yellow warning Alert with a similarity table and Progress-bar percentages) at exactly 1440px width, with nothing clipped at the bottom.
- **Also checked (Task 2, not required by plan but done for quality):** `docs/chuong-2-khao-sat-phan-tich/bpmn/01-de-tai-as-is.png` and `docs/chuong-2-khao-sat-phan-tich/uc/act-uc1-de-xuat-dang-ky-de-tai.png` — both legible, no overlapping shapes, correct lane counts (3 for AS-IS, 4 for the activity diagram).
- **Still recommended:** a human (the student/GVHD) should glance at `mockup/mh-06.html` in an actual browser at least once before plan 01-06 copies these conventions across 13 more screens, since the plan's own `<human-check>` exists precisely because "looks like a real Ant Design admin page" is a subjective/visual judgment call that a self-check by the same agent that built it cannot fully substitute for.

## User Setup Required

None - no external service configuration required. The toolchain (PlantUML jar, draw.io docker image, Chrome) is already cached/installed on this machine; no new user-facing setup is needed for plans 01-03..01-07 to reuse it.

## Next Phase Readiness

- The toolchain (`tools/render-diagrams.sh`, `tools/check-docs.py`) is proven and ready for plans 01-03..01-07 to reuse without re-deriving it.
- `docs/README.md` conventions are published; plans 01-03..01-06 should follow them verbatim (ID prefixes, PI tag line, assumption marker, UC spec format, mockup conventions).
- UC1 (all 4 sub-UCs) is fully specified in Chapter 2; DSGN-01/02 have their first slice (UC1.1's entities/tables); DSGN-04 has its first mockup (MH-06) with the shared stylesheet other screens will reuse.
- `check-docs.py mockup --all` and `check-docs.py truy-vet --complete` currently fail by design (13 screens and several PI rows are not yet built) — this is expected; plan 01-07 is where `--complete`/`all` should first be expected to pass.
- No blockers for 01-03/01-04 (wave 2, depend on wave 1 completing — both 01-01 and 01-02 are now done).

## Self-Check: PASSED

All 17 created files (plus their rendered PNG/SVG siblings, 29 files total across both commits) verified present on disk with `[ -f ]`; both task commit hashes (`c8f9277`, `0f99f2a`) verified present in `git log --oneline --all`.
