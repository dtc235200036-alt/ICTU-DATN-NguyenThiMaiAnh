---
phase: 01-analysis-design
plan: 06
subsystem: docs
tags: [ant-design, mockup, html-css, headless-chrome, ui, DSGN-04]

requires:
  - phase: 01-analysis-design (plan 01-02)
    provides: "tools/render-diagrams.sh + check-docs.py toolchain, antd-admin.css tokens, mh-06.html tracer, docs/README.md mockup conventions, §3.4.1 sider menus per role"
  - phase: 01-analysis-design (plan 01-04)
    provides: "UC2-UC5 and UC0 specs (UC2.1-2.3, UC3.1-3.4, UC4.1-4.5, UC5.1-5.4, UC0.1-0.7), FR-DC/TD/BV/KHO/AI tables"
provides:
  - "13 new static HTML/CSS mockup screens (MH-01..MH-05, MH-07..MH-14) rendered to 1440px PNGs, completing the D-14 14-screen inventory alongside the MH-06 tracer"
  - "antd-admin.css extended with Statistic, Steps, Dropdown, Pagination, filter-bar, login-page-shell, Drawer, Modal, Tabs, Upload.Dragger, Spin, Timeline, circular Progress, dup-passage/dup-thesis-list highlight blocks, Tooltip, member-picker, InputNumber"
  - "mockup-state-panel pattern: a labelled alternative-state illustration placed in document flow AFTER a screen's ant-layout closes, so a second state (Modal/Spin/error) can be shown without stacking two absolutely-positioned overlays or clipping content"
  - "04-thiet-ke-giao-dien.md: full §3.4 with 14 Đã dựng inventory rows and 14 screen subsections (§3.4.3-3.4.16), each naming vai trò/UC/FR and embedding its PNG"
affects: ["01-07", "Phase 2-4 React UI implementation (mockups are the reference)"]

actuals:
  tokens: 39000
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "mockup-state-panel: alternative-state illustrations (Modal, Spin, error Alert) rendered as a normal-flow section AFTER </div> of ant-layout, avoiding two stacked position:absolute overlays and avoiding content clipping under Chrome's viewport-only --screenshot capture"
    - "ant-layout sizes to its own content (sider/main flex height), NOT min-height:100vh -- a screen needing extra height for a tall Drawer/Modal overlay sets an explicit inline min-height on its own .ant-layout instead of relying on the shared stylesheet forcing every screen to fill the full declared viewport"
    - "dup-passage-{high,medium,low}: duplicate-check highlight blocks pair a border-accent color with an explicit text label (not color alone) so similarity level reads for colour-blind users and in print"
    - "ant-tooltip-wrap: a tooltip shown permanently (no hover in a static screenshot) next to the element it explains, e.g. why a disabled button is disabled"

key-files:
  created:
    - docs/chuong-3-thiet-ke/mockup/mh-01.html
    - docs/chuong-3-thiet-ke/mockup/mh-02.html
    - docs/chuong-3-thiet-ke/mockup/mh-03.html
    - docs/chuong-3-thiet-ke/mockup/mh-04.html
    - docs/chuong-3-thiet-ke/mockup/mh-05.html
    - docs/chuong-3-thiet-ke/mockup/mh-07.html
    - docs/chuong-3-thiet-ke/mockup/mh-08.html
    - docs/chuong-3-thiet-ke/mockup/mh-09.html
    - docs/chuong-3-thiet-ke/mockup/mh-10.html
    - docs/chuong-3-thiet-ke/mockup/mh-11.html
    - docs/chuong-3-thiet-ke/mockup/mh-12.html
    - docs/chuong-3-thiet-ke/mockup/mh-13.html
    - docs/chuong-3-thiet-ke/mockup/mh-14.html
  modified:
    - docs/chuong-3-thiet-ke/mockup/antd-admin.css
    - docs/chuong-3-thiet-ke/04-thiet-ke-giao-dien.md

key-decisions:
  - "design-taste-frontend explicitly lists dashboards/admin panels/data tables as Out of Scope (its own §13); per D-12 (Ant Design admin locked) its design-system guidance was overridden again this plan, same as 01-02 -- only its neutral anti-slop principles (no generic placeholder data, no hand-wavy icons, one consistent font/palette) were applied. ui-ux-pro-max's accessibility/UX guidance (contrast, table alternatives, loading/error states, labels above inputs) was applied directly."
  - "Removed `.ant-layout { min-height: 100vh }` from the shared stylesheet: headless Chrome's `--screenshot` flag only captures the declared window-size viewport (not the full scrollable page), so a 100vh-forced layout left no room for a trailing .mockup-state-panel section and also silently clipped Drawer/Modal overlays whose own content was taller than the page's normal-flow content (discovered on MH-07's Drawer, which showed only its header+footer with the middle content invisible until this fix, then confirmed via a full re-render + view of all 14 PNGs). Single-state screens are visually identical since html/body already paint --ant-color-bg-layout underneath."
  - "MH-07's Drawer still needs more height than its own table content provides, so its .ant-layout carries one explicit inline `min-height: 900px` -- a deliberate per-screen escape hatch rather than reintroducing a global 100vh rule that would break the trailing state panels again."
  - "ant-tag and ant-btn both needed `white-space: nowrap` added (two separate fixes, same root cause): Ant Design's real Tag/Button never wrap their label across two lines, but the shared CSS didn't pin that, so narrow table cells (MH-05's 'Đã phân công' Tag, later MH-11's 'Chốt kết quả' Button) wrapped and rendered a broken-looking two-line overlap. Fixed once in antd-admin.css, all affected screens improved after a forced re-render."
  - "MH-05's mockup 'Xem chi tiết đề tài' route for individual topics reuses MH-06's layout in read-only mode rather than adding a 15th screen outside the D-14 inventory (documented in §3.4.7, not built as a separate HTML file)."
  - "MH-09 and MH-08 deliberately reference different students (Trần Thị Mẫu B vs Đinh Văn Sinh Viên) so each screen's illustrated duplicate-check percentage stays internally consistent without needing every mockup to agree on one shared fictional student's exact history."

requirements-completed: [DSGN-04]

coverage:
  - id: D1
    description: "All 14 main screens MH-01..MH-14 exist as static HTML mockups (13 built here + MH-06 from the tracer), each with a fresh 1440px PNG and a Đã dựng inventory row linking both files"
    requirement: "DSGN-04"
    verification:
      - kind: other
        ref: "python3 tools/check-docs.py mockup --all (Task 3 <verify>)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Screens designed after loading ui-ux-pro-max and design-taste-frontend (D-11); shared antd-admin.css Ant Design admin look (D-12), exact 1440px width (D-13), intact Vietnamese diacritics, no scripts/remote resources"
    requirement: "DSGN-04"
    verification:
      - kind: other
        ref: "python3 tools/check-docs.py mockup --all + privacy scan (Task 1-3 <verify>); skill guidance documented in key-decisions and §3.4.1"
        status: pass
    human_judgment: true
    rationale: "Whether the screens genuinely 'look like a real Ant Design admin' and read well as a cross-screen set is a visual/UX judgment; self-performed by the executor (see Human-check section) per explicit autonomous-overnight instruction, but the plan's own <human-check> blocks ask for a human glance before Phase 2-4 treats these as the UI reference."
  - id: D3
    description: "All 3 roles and all 5 UCs covered: dashboards for Sinh viên/Giảng viên/Bộ môn, topic list/approval, outline and final-report submission, outline review with duplicate-result panel, progress report + comments, committee + schedule, scoring, archive search"
    requirement: "DSGN-04"
    verification:
      - kind: other
        ref: "§3.4 sections 3.4.3-3.4.16 each name vai trò/UC/FR (Task 1-3 acceptance_criteria)"
        status: pass
    human_judgment: false
  - id: D4
    description: "MH-14 shows the duplicate-check result Turnitin/Coopy-style: overall ratio, matched-theses list with ratios, highlighted passages next to source passages, and a note excluding template sections"
    requirement: "DSGN-04"
    verification:
      - kind: other
        ref: "grep 'mục lục' in both 04-thiet-ke-giao-dien.md and mh-14.html (Task 2 <verify>); visual check of mh-14.png"
        status: pass
    human_judgment: false
  - id: D5
    description: "Every screen subsection names role/UC/FR IDs, regions/states/interactions, and embeds a fresh PNG against the shared stylesheet"
    requirement: "DSGN-04"
    verification:
      - kind: other
        ref: "python3 tools/check-docs.py render docs/chuong-3-thiet-ke/mockup (Task 1-3 <verify>)"
        status: pass
    human_judgment: false

duration: 95min
completed: 2026-09-28
status: complete
---

# Phase 1 Plan 6: HTML Mockups MH-01..MH-05, MH-07..MH-14 Summary

**All 14 D-14 main screens (MH-01 login through MH-14 duplicate-check detail) now exist as static, no-Figma HTML/CSS Ant Design admin mockups sharing one stylesheet, each rendered to an exact 1440px-wide PNG and documented in chương 3 §3.4 with role/UC/FR references.**

## Performance

- **Duration:** ~95 min
- **Started:** 2026-09-28T00:00:00Z (approx, autonomous overnight run)
- **Completed:** 2026-09-28T01:35:00Z (approx)
- **Tasks:** 3
- **Files modified:** 29 (13 new HTML + 13 new PNG + 3 re-rendered pre-existing PNGs + antd-admin.css + 04-thiet-ke-giao-dien.md, some counted once across tasks)

## Accomplishments

- **Task 1** — MH-01 Đăng nhập (normal + wrong-credentials states), MH-02/03/04 role dashboards (Sinh viên/Giảng viên/Bộ môn, including an opened notification dropdown and the Trễ mốc red-tag progress table), MH-05 Danh sách đề tài (5-filter bar, 5-state topic table, pagination).
- **Task 2** — MH-07 Duyệt đề tài (Drawer with the stored title-check summary + GVHD Select, reject Modal), MH-08 Nộp đề cương/báo cáo cuối (Tabs, Upload.Dragger with the DOCX/PDF/20MB rule, Đang kiểm tra/Hoàn tất version history, GVHD comment Timeline), MH-09 Duyệt đề cương (circular Progress duplicate panel, Đang kiểm tra alternate state), MH-14 Chi tiết kết quả kiểm tra trùng lặp (summary bar, matched-thesis filter list, side-by-side highlighted passages, excluded-template-sections note).
- **Task 3** — MH-10 Báo cáo tiến độ (Timeline + nhận xét form + SV submission Modal), MH-11 Lập hội đồng (member-role picker, disabled Chốt kết quả with a persistent tooltip vs. the enabled/computed-average state), MH-12 Chấm điểm bảo vệ (own-committees-only Select, InputNumber score), MH-13 Kho đồ án (4-filter search, detail state panel, Bộ môn Thêm bản ghi/Import khóa cũ actions); a forced full re-render + view of all 14 PNGs confirmed cross-screen consistency, surfacing and fixing the `ant-btn` text-wrap bug in the process.
- `antd-admin.css` grew from the tracer's ~11 component classes to a full set covering every Ant Design component these 14 screens needed (Statistic, Steps, Dropdown, Pagination, Drawer, Modal, Tabs, Upload.Dragger, Spin, Timeline, circular Progress, Tooltip, InputNumber) plus two reusable non-AntD patterns: `mockup-state-panel` (alternate-state illustrations without stacking overlays) and `dup-passage` (colour-blind-safe duplicate highlight blocks).

## Task Commits

Each task was committed atomically:

1. **Task 1: MH-01 login, MH-02..MH-04 role dashboards, MH-05 topic list** - `d8af646` (feat)
2. **Task 2: MH-07 approve+reject, MH-08 submit, MH-09 review, MH-14 dup-detail** - `e9476a9` (feat)
3. **Task 3: MH-10 progress, MH-11 committee, MH-12 scoring, MH-13 archive; consistency pass** - `2fb9185` (feat)

**Plan metadata:** commit to follow (this SUMMARY + STATE/ROADMAP update)

## Files Created/Modified

- `docs/chuong-3-thiet-ke/mockup/mh-01.html` … `mh-14.html` (13 new files; MH-06 already existed from the tracer) - the 14-screen D-14 mockup set, each with its rendered `.png` sibling
- `docs/chuong-3-thiet-ke/mockup/antd-admin.css` - extended component set (see tech-stack) and two bugfixes (`ant-tag`/`ant-btn` `white-space: nowrap`) and one structural fix (`.ant-layout` no longer forces `min-height: 100vh`)
- `docs/chuong-3-thiet-ke/04-thiet-ke-giao-dien.md` - all 14 inventory rows now `Đã dựng`; §3.4.3-3.4.16 screen subsections; §3.4.1 component table extended

## Decisions Made

See frontmatter `key-decisions`. Highlights: the `min-height: 100vh` removal from `.ant-layout` was the most consequential fix — headless Chrome's `--screenshot` only captures the declared viewport (confirmed by inspecting the actual chrome invocation in `tools/render-diagrams.sh` rather than assuming), so a full-viewport-forced layout both wasted the tall values chosen for MH-04 (large blank areas below short content) and, more seriously, silently clipped Drawer/Modal content on MH-07 whenever the overlay's own content was taller than the underlying table. The fix was verified by cropping and viewing the previously-clipped region before and after.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `ant-tag` text wrapped to two overlapping lines in narrow table cells**
- **Found during:** Task 1, viewing mh-05.png ("Đã phân công" tag rendered with what looked like a strikethrough, actually two overlapping wrapped lines inside the fixed 22px-tall tag)
- **Fix:** Added `white-space: nowrap` to `.ant-tag` in antd-admin.css.
- **Files modified:** docs/chuong-3-thiet-ke/mockup/antd-admin.css
- **Verification:** Force re-rendered all 6 screens built so far, viewed mh-05.png and mh-04.png again, confirmed all tags render on one line.
- **Committed in:** d8af646 (Task 1 commit)

**2. [Rule 1 - Bug] `.ant-layout { min-height: 100vh }` clipped Drawer/Modal overlays and left no room for trailing state panels**
- **Found during:** Task 2, viewing mh-07.png (Drawer showed only header+footer, the alert/table/Select body content was invisible) and mh-08.png (the wrong-file-type error state panel placed after `</div>` of `ant-layout` was entirely missing from the screenshot)
- **Issue:** `min-height: 100vh` forced every `.ant-layout` to fill the exact declared viewport height H; since headless Chrome's `--screenshot` captures only that fixed viewport (not the full scrollable page), this left zero room for (a) any content appended after `ant-layout` closes and (b) a Drawer/Modal overlay whose own natural content was taller than the page's normal-flow content, since the overlay's `position: absolute; inset: 0` anchors to `ant-layout`'s box, not its own content.
- **Fix:** Removed `min-height: 100vh` from `.ant-layout` (sizes to content instead; `html body` already paints the same background color so single-state screens look identical); added one explicit inline `min-height: 900px` on MH-07's own `.ant-layout` since its Drawer content still needs more height than the underlying table provides.
- **Files modified:** docs/chuong-3-thiet-ke/mockup/antd-admin.css, docs/chuong-3-thiet-ke/mockup/mh-07.html
- **Verification:** Force re-rendered all 10 screens built at that point, viewed mh-07.png (full Drawer content + reject-Modal state panel now both visible) and mh-08.png (error state panel now visible) end-to-end; re-checked mh-02/mh-04 (screens with no trailing content) for regressions — visually identical.
- **Committed in:** e9476a9 (Task 2 commit)

**3. [Rule 1 - Bug] `ant-btn` text wrapped inside a narrow table Hành động column**
- **Found during:** Task 3, viewing mh-11.png ("Chốt kết quả" button wrapped to "Chốt" / "kết quả" on two lines)
- **Fix:** Added `white-space: nowrap` to `.ant-btn` in antd-admin.css (same root cause as deviation 1, different component).
- **Files modified:** docs/chuong-3-thiet-ke/mockup/antd-admin.css
- **Verification:** Force re-rendered all 14 screens; only mh-05.png's pixels actually changed (its Đăng ký/Xem buttons), confirming no other screen regressed.
- **Committed in:** 2fb9185 (Task 3 commit)

**4. [Rule 1 - Bug] MH-13's Drawer-open state hid the Bộ môn action buttons entirely**
- **Found during:** Task 3, viewing the first mh-13.png render (Drawer's mask spans the full page width from x=960, covering the "Thêm bản ghi"/"Import khóa cũ" buttons positioned in the content header)
- **Issue:** Showing the detail Drawer as the screen's only/primary state made two required elements (the Bộ môn-only action buttons) simultaneously invisible, when the plan requires both to be documented on this screen.
- **Fix:** Restructured MH-13 to show the closed list view (with both buttons visible) as the primary state, and the Drawer detail as a `.mockup-state-panel` illustration below (a plain card reusing `.ant-drawer-header/-body/-footer` styling without the absolute-positioned mask/backdrop) — the same pattern already used for MH-07/08/09's alternate states.
- **Files modified:** docs/chuong-3-thiet-ke/mockup/mh-13.html
- **Verification:** Re-rendered and viewed mh-13.png twice (once still clipped at H=1000 because the state-panel card's footer buttons fell past the viewport, then again after raising `mockup-size` to 1440x1120) — both the primary list view and the full Drawer detail card now render completely.
- **Committed in:** 2fb9185 (Task 3 commit)

---

**Total deviations:** 4 auto-fixed (all Rule 1 - bugs found while rendering and viewing each screen's own PNG, per the plan's mandated "render then view then fix" loop). **Impact:** All four were necessary for the mockups to render correctly; the min-height fix (deviation 2) was the most consequential since it affected the underlying CSS every one of the 14 screens shares, but was verified not to regress any already-built screen before proceeding.

## Issues Encountered

None beyond the deviations above (all discovered and resolved within the plan's own render-view-fix loop, not blocking or requiring architectural decisions).

## Human-check (self-performed, pending user confirmation)

Per explicit orchestrator instruction (autonomous overnight execution; user asleep), every task's `<human-check>` was self-performed by the executor instead of halting at a checkpoint — all 14 PNGs were viewed directly with the Read tool's image rendering (not inferred from file existence or automated checks alone):

- **Ant Design admin look consistency:** all 14 screens share one dark sider (220px), one header layout (breadcrumb left, avatar+name right), one card/table/form visual language, one Tag colour palette for the 5 topic states (default/processing/warning/error/success), and one page-content padding — confirmed by viewing each PNG in sequence during the Task 3 consistency pass.
- **Role sider menus:** MH-02 uses the exact Sinh viên menu from §3.4.1, MH-03/07/09/10/12/14 use the exact Giảng viên menu, MH-04/07/11/13 use the exact Bộ môn menu — copied verbatim as required, not re-typed with drift.
- **Vietnamese diacritics:** render correctly and legibly across all 14 PNGs (name fields, form labels, Tag text, table headers), including in the smallest text (Tag labels, tooltip, dup-passage labels).
- **MH-04:** shows red "Trễ mốc" tags in the per-milestone progress table as required.
- **MH-09:** shows the duplicate panel with a working "Xem chi tiết" link to MH-14, plus the alternate "Đang kiểm tra, chưa có kết quả" state as a separate panel.
- **MH-14:** shows matched passages highlighted side by side with their source passage, each labelled with an explicit percentage (not colour alone), and the "Đã loại trừ phần mẫu chung" note is present in both the HTML and the §3.4.16 description.
- **MH-08:** shows both the "Đang kiểm tra" (Spin) and "Hoàn tất - N%" states in its version-history table, plus a separate wrong-file-type error state panel.
- **MH-11:** shows the disabled "Chốt kết quả" button with its persistent tooltip on one row and the enabled button with a computed average score (8.3) on another.
- **1440px width:** every PNG measured exactly 1440px wide (enforced automatically by `check-docs.py mockup`, not just visually eyeballed).
- **No content cut off at the bottom:** confirmed for all 14 screens after the `min-height: 100vh` fix and the MH-13/MH-07 height adjustments — the earlier clipped states (documented in Deviations) were caught precisely by this human-check step, not missed.
- **Still recommended:** per the plan's own `<human-check>` rationale ("Ant Design and cross-screen consistency cannot be grepped"), a human (student/GVHD) should still glance through all 14 `mockup/mh-NN.html` files in an actual browser at least once before Phase 2-4 treats them as the authoritative UI reference — this is a genuinely subjective visual judgment that a self-check by the same agent that built the screens cannot fully substitute for, which is exactly why the plan's acceptance criteria still list it as `human_judgment: true` in this SUMMARY's `coverage` block (D2).

## User Setup Required

None - no external service configuration required. The toolchain (`tools/render-diagrams.sh`, `tools/check-docs.py`, Google Chrome) was already proven and cached by plan 01-02; this plan only reused it.

## Next Phase Readiness

- All 14 D-14 screens (DSGN-04, ROADMAP SC5) are built, rendered, and documented — Phase 2-4's React UI implementation now has a complete visual reference for every main screen across all 3 roles and all 5 UCs, including the AI duplicate-check demo screen (MH-14).
- `python3 tools/check-docs.py mockup --all` passes: every inventory row is `Đã dựng` with a working HTML/PNG link, heading, and embedded image.
- `python3 tools/check-docs.py render docs/chuong-3-thiet-ke/mockup` passes: every PNG is fresh against its HTML and the shared stylesheet.
- Plan 01-07 (renumbering captions, confirming assumption markers against real interviews, finishing `check-docs.py all`/`truy-vet --complete`) can now proceed — this was the last content-producing plan blocking those repo-wide checks from passing for the first time.
- No blockers. The `antd-admin.css` component set is now broad enough that Phase 2-4's React/Ant Design implementation can map nearly every CSS class here 1:1 to a real `antd` component.

## Self-Check: PASSED

All 13 new HTML files and their 13 new PNG siblings verified present on disk with `[ -f ]`; all 3 task commit hashes (`d8af646`, `e9476a9`, `2fb9185`) verified present in `git log --oneline --all`; `python3 tools/check-docs.py mockup --all` exits 0 confirming every one of the 14 inventory rows, headings, and image embeds are correctly wired.
