---
phase: 01-analysis-design
plan: 03
subsystem: docs
tags: [bpmn, drawio, survey, khao-sat, bpmn-overview, de-cuong, tien-do, bao-ve, kho-do-an, ANLS-01, ANLS-02]

requires:
  - phase: 01-analysis-design (plan 01-02)
    provides: "tools/render-diagrams.sh, tools/check-docs.py, docs/README.md conventions, bpmn/01-de-tai.drawio style reference (UC1 tracer)"
provides:
  - "01-khao-sat-hien-trang.md: §2.1 Khảo sát hiện trạng draft (mục tiêu/phương pháp, đối tượng khảo sát, 18 phát hiện AS-IS KS-* cho 5 quy trình, 7 biểu mẫu MAU-01..07, 7 vấn đề VD-*, kết quả phiếu khảo sát)"
  - "Full 6-diagram BPMN set (1 tổng quan + 5 quy trình con), each AS-IS+TO-BE, 12 PNGs rendered"
  - "02-quy-trinh-nghiep-vu.md extended with §2.2.1 (tổng quan), §2.2.3 (đề cương), §2.2.4 (tiến độ), §2.2.5 (bảo vệ), §2.2.6 (kho)"
affects: ["01-04", "01-05", "01-06", "01-07"]

actuals:
  tokens: 29261
  tasks: 3
  commits: 3
  plan_head_before: a0036c3698b8fde213175db93ef9ba06d7fdbea5
  plan_head_after: 9a58ae67561a2ce6611204786b4f36fe0906332d

tech-stack:
  added: []
  patterns: ["dashed tan/yellow boxes (fillColor=#fff2cc;strokeColor=#d6b656;dashed=1) to visually mark collapsed sub-process references on the overview BPMN, distinct from regular tasks (blue) and service tasks (green)", "exitX/exitY/entryX/entryY constraints on fan-in edges into a shared service-task box to avoid overlapping edge labels", "timer/boundary-style event (outline=timer) for missed-milestone detection on the Tiến độ TO-BE diagram", "text-only annotation vertex (style=text;) for a lane with no activity in AS-IS diagrams, to keep the lane visibly present without inventing a task"]

key-files:
  created:
    - docs/chuong-2-khao-sat-phan-tich/01-khao-sat-hien-trang.md
    - docs/chuong-2-khao-sat-phan-tich/bpmn/00-tong-quan.drawio
    - docs/chuong-2-khao-sat-phan-tich/bpmn/02-de-cuong.drawio
    - docs/chuong-2-khao-sat-phan-tich/bpmn/03-tien-do.drawio
    - docs/chuong-2-khao-sat-phan-tich/bpmn/04-bao-ve.drawio
    - docs/chuong-2-khao-sat-phan-tich/bpmn/05-kho-do-an.drawio
  modified:
    - docs/chuong-2-khao-sat-phan-tich/02-quy-trinh-nghiep-vu.md

key-decisions:
  - "Overview BPMN (00-tong-quan) đặt 2 service task Hệ thống dùng chung (Kiểm tra trùng lặp, Thông báo in-app) fan-in từ Đề tài/Đề cương/Tiến độ/Bảo vệ thay vì lặp lại ở từng sơ đồ con — cho thấy 2 điểm tích hợp AI/thông báo xuyên suốt chỉ ở một chỗ"
  - "MAU-03 (Đề cương) suy ra trực tiếp từ đề cương gốc thật (H01.DTC235200036...docx, mục 1-9), không gắn nhãn giả định; 6 biểu mẫu MAU còn lại cite TL-ID và gắn nhãn chờ xác nhận"
  - "Fan-in edges vào 2 service task Hệ thống dùng exitX/exitY/entryX/entryY khác nhau cho mỗi cạnh để tránh nhãn cạnh chồng lên nhau khi nhiều luồng hội tụ vào cùng một điểm — phát hiện và tự sửa khi tự xem lại PNG overview lần đầu"

requirements-completed: [ANLS-01, ANLS-02]

coverage:
  - id: D1
    description: "§2.1 Khảo sát hiện trạng draft: mục tiêu/phương pháp, đối tượng khảo sát (6 mã vai trò), 18 phát hiện KS-* (≥3/quy trình) đều gắn nhãn GIẢ ĐỊNH — chờ xác nhận và cite Q-ID, 7 biểu mẫu MAU-01..07 với bảng trường dữ liệu, 7 vấn đề VD-*, §2.1.6 không bịa số liệu"
    requirement: "ANLS-01"
    verification:
      - kind: other
        ref: "Task 1 <verify>: grep counts (MAU>=7, KS>=15, VD>=6, marker>=15) all higher than threshold; check-docs.py privacy/links exit 0 (plan Task 1 <verify>)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Bộ 6 sơ đồ BPMN (1 tổng quan + 5 quy trình con: Đề tài[01-02], Đề cương, Tiến độ, Bảo vệ, Kho), mỗi sơ đồ AS-IS (3 lane, gắn nhãn giả định) + TO-BE (4 lane thêm Hệ thống), start/end event đúng chuẩn"
    requirement: "ANLS-02"
    verification:
      - kind: other
        ref: "python3 tools/check-docs.py bpmn (toàn bộ 6 file, bao gồm 01-de-tai.drawio không bị sửa) exit 0; ls đếm 6 .drawio + 12 PNG (plan Task 3 <verify>)"
        status: pass
    human_judgment: false
  - id: D3
    description: "02-quy-trinh-nghiep-vu.md có đủ §2.2.1..§2.2.6, mỗi mục có bảng bước AS-IS + TO-BE với mã bước AS-*/TB-* và cột Ghi chú gắn nhãn giả định trên nhánh AS-IS; §2.2.2 (UC1, do 01-02 tạo) không bị sửa"
    requirement: "ANLS-02"
    verification:
      - kind: other
        ref: "grep -qE cho từng heading §2.2.1/2.2.3/2.2.4/2.2.5/2.2.6; git diff-tree xác nhận bpmn/01-de-tai.drawio không nằm trong 2 commit Task 2/3 (plan Task 2+3 <verify>)"
        status: pass
    human_judgment: false
  - id: D4
    description: "12 PNG BPMN (6 diagram × AS-IS/TO-BE) rõ nét, lane đúng thứ tự Sinh viên/Giảng viên/Bộ môn (+Hệ thống ở TO-BE), dấu tiếng Việt còn nguyên"
    verification: []
    human_judgment: true
    rationale: "Legibility, layout collision, and Vietnamese diacritic rendering are visual judgment calls the plan's own <human-check> assigns to a human; self-performed here per explicit orchestrator instruction (user asleep) by viewing all 12 PNGs with the Read tool, including one round of self-fix (edge-label overlap on the overview diagram) — still recommended a human glance before plan 01-07 finalizes captions."

duration: 25min
completed: 2026-09-28
status: complete
---

# Phase 1 Plan 3: Khảo sát hiện trạng + BPMN Overview/Đề cương/Tiến độ/Bảo vệ/Kho Summary

**Draft survey chapter (§2.1, 18 marked AS-IS findings + 7 data forms) and the full 6-diagram BPMN set (1 overview + 5 sub-processes, each AS-IS/TO-BE, 12 PNGs) completing §2.2 with step tables for every process.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-09-27T19:14:07Z (session start; first commit 2026-09-28T02:00:36+07)
- **Completed:** 2026-09-28T02:13:52+07:00 (last content commit)
- **Tasks:** 3
- **Files modified:** 17 (1 modified, 16 created: 1 khảo sát doc + 5 .drawio + 10 PNG + 1 modified process doc counted once)

## Accomplishments

- `01-khao-sat-hien-trang.md`: §2.1.1 mục tiêu/phương pháp (3 nguồn: phỏng vấn, phiếu khảo sát, thu thập tài liệu — D-01), §2.1.2 đối tượng khảo sát (BM-01, GV-01/02, SV-01/02/03, tất cả "Chưa phỏng vấn"), §2.1.3 hiện trạng 5 quy trình với 18 phát hiện `KS-*` (mỗi phát hiện cite Q-ID và gắn nhãn `GIẢ ĐỊNH — chờ xác nhận`), §2.1.4 7 biểu mẫu `MAU-01..07` với bảng trường dữ liệu (`Thực thể dự kiến` dùng tên lớp PascalCase), §2.1.5 7 vấn đề `VD-*` làm động lực TO-BE, §2.1.6 giải thích cách tổng hợp phiếu khảo sát mà không bịa số liệu.
- `bpmn/00-tong-quan.drawio`: sơ đồ tổng quan 1 pool, chuỗi 6 sub-process (Mở đợt → Đề tài → Đề cương → Tiến độ → Bảo vệ → Kho) dạng box viền đứt màu vàng để phân biệt "tham chiếu sang sơ đồ khác"; TO-BE thêm lane Hệ thống với 2 service task dùng chung (Kiểm tra trùng lặp, Thông báo in-app), mỗi cạnh fan-in dùng exit/entry point riêng để nhãn không chồng nhau.
- `bpmn/02-de-cuong.drawio`: AS-IS (gửi email/Zalo, góp ý thủ công, không kiểm tra trùng lặp) vs TO-BE (nộp DOCX/PDF → kiểm tra định dạng → kiểm tra trùng lặp bất đồng bộ với 2 trạng thái Đang kiểm tra/Hoàn tất → GVHD xem kết quả → gateway Duyệt/Yêu cầu sửa với loop về SV → thông báo in-app; thêm nhánh Bộ môn xem/lọc danh sách).
- `bpmn/03-tien-do.drawio`: AS-IS (không mốc chung, không lưu vết) vs TO-BE (Bộ môn thiết lập mốc → SV nộp theo mốc → GVHD nhận xét; nhánh timer "Quá hạn mốc" → Hệ thống đánh dấu trễ mốc → dashboard Bộ môn).
- `bpmn/04-bao-ve.drawio`: AS-IS (nộp giấy+mềm, quyết định hội đồng giấy, phiếu chấm giấy, thư ký tổng hợp thủ công) vs TO-BE (nộp cuối → kiểm tra trùng lặp bất đồng bộ → Bộ môn lập hội đồng → thông báo → GV chấm+nhận xét → tính trung bình cộng → Bộ môn chốt kết quả → SV xem lịch/kết quả → kích hoạt tạo bản ghi kho).
- `bpmn/05-kho-do-an.drawio`: AS-IS (bản cứng thư viện + ổ dùng chung, tra cứu thủ công) vs TO-BE 3 luồng độc lập trên cùng trang: (a) tự động tạo bản ghi + đẩy AI index khi chốt kết quả bảo vệ, (b) Bộ môn thêm/sửa/xóa/import khóa cũ → index, (c) SV/GV/Bộ môn tìm kiếm/lọc theo khóa/từ khóa/GVHD → xem chi tiết.
- `02-quy-trinh-nghiep-vu.md`: thêm §2.2.1 (tổng quan, trước §2.2.2), §2.2.3–§2.2.6 (đề cương, tiến độ, bảo vệ, kho — sau §2.2.2), mỗi mục có bảng bước AS-IS + TO-BE (mã `AS-*`/`TB-*`) và bullet "Điểm cải tiến của TO-BE so với AS-IS"; §2.2.2 (UC1, do plan 01-02 tạo) và `bpmn/01-de-tai.drawio` không bị sửa (xác nhận bằng `git diff-tree --name-only`).

## Task Commits

Each task was committed atomically:

1. **Task 1: Draft §2.1 Khảo sát hiện trạng with AS-IS findings and data forms MAU-01..MAU-07** - `c3d49fd` (docs)
2. **Task 2: BPMN overview, Đề cương and Tiến độ processes (AS-IS + TO-BE) with step tables** - `09d678b` (feat)
3. **Task 3: BPMN Nộp báo cáo & bảo vệ and Kho đồ án (AS-IS + TO-BE); full BPMN set check** - `9a58ae6` (feat)

**Plan metadata:** commit to follow (this SUMMARY + STATE/ROADMAP update)

## Files Created/Modified

- `docs/chuong-2-khao-sat-phan-tich/01-khao-sat-hien-trang.md` - §2.1 draft (khảo sát, biểu mẫu)
- `docs/chuong-2-khao-sat-phan-tich/bpmn/00-tong-quan.drawio` (+ `-as-is.png`, `-to-be.png`) - sơ đồ tổng quan
- `docs/chuong-2-khao-sat-phan-tich/bpmn/02-de-cuong.drawio` (+ 2 PNG) - quy trình đề cương
- `docs/chuong-2-khao-sat-phan-tich/bpmn/03-tien-do.drawio` (+ 2 PNG) - quy trình tiến độ
- `docs/chuong-2-khao-sat-phan-tich/bpmn/04-bao-ve.drawio` (+ 2 PNG) - quy trình bảo vệ
- `docs/chuong-2-khao-sat-phan-tich/bpmn/05-kho-do-an.drawio` (+ 2 PNG) - quy trình kho đồ án
- `docs/chuong-2-khao-sat-phan-tich/02-quy-trinh-nghiep-vu.md` - thêm §2.2.1, §2.2.3–§2.2.6

## Decisions Made

See frontmatter `key-decisions`. Highlights: the overview diagram deliberately centralizes the two cross-cutting AI/notification service tasks in one Hệ thống lane rather than duplicating them per sub-process; MAU-03 is the only data form not marked as assumption because it is derived from the real outline document already in the repo; fan-in edge routing on the overview diagram needed explicit exit/entry constraints to avoid overlapping labels, discovered by viewing the first render.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Overlapping edge labels on the overview TO-BE BPMN diagram**
- **Found during:** Task 2, self-performed visual check of `00-tong-quan-to-be.png` after first render
- **Issue:** Four fan-in edges into each of the two shared Hệ thống service tasks (Kiểm tra trùng lặp, Thông báo in-app) routed through nearly identical vertical paths, causing their "gọi"/"thông báo" midpoint labels to stack on top of each other — illegible at report resolution.
- **Fix:** Added distinct `exitX/exitY/entryX/entryY` constraints (and small geometry offsets) per edge so each fan-in line enters the target box at a different x-fraction, spreading the labels apart.
- **Files modified:** `docs/chuong-2-khao-sat-phan-tich/bpmn/00-tong-quan.drawio`
- **Verification:** Re-rendered and re-viewed the PNG; all 8 labels ("gọi" ×3, "thông báo" ×4, main chain unlabeled) are now legible with no overlap; `check-docs.py bpmn` still exits 0.
- **Committed in:** `09d678b` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug/legibility). **Impact:** Necessary for the diagram to be readable in the final report; no scope creep beyond the plan's own diagram requirement.

## Issues Encountered

None beyond the deviation above.

## Human-check (self-performed, pending user confirmation)

Per explicit orchestrator instruction (autonomous overnight execution; user asleep), Task 3's `<human-check>` (open the 12 PNGs, confirm shared visual style, correct lanes, legible labels, intact Vietnamese diacritics) was self-performed instead of halting at a checkpoint:

- **Checked:** all 12 PNGs across the 6 diagrams (`00-tong-quan`, `02-de-cuong`, `03-tien-do`, `04-bao-ve`, `05-kho-do-an` × AS-IS/TO-BE), viewed directly with the Read tool's image rendering.
- **Result:** All six diagrams share the same visual style established by `01-de-tai.drawio` in plan 01-02 (rounded blue task boxes, green service tasks, gateway diamonds, BPMN start/end circles); lanes read Sinh viên / Giảng viên / Bộ môn on AS-IS and add Hệ thống on TO-BE, in that order; Vietnamese diacritics render correctly everywhere (checked in labels like "chưa đạt", "quá hạn", "trùng lặp", "chốt kết quả"); labels are legible at report size after the overview-diagram fix documented above. Minor: a few text labels sit close to their connector lines (e.g. "Chưa đạt" gateway label in `02-de-cuong-as-is.png`, small circular start-event labels in `05-kho-do-an-to-be.png`) but remain readable — acceptable for a draft chapter, not blocking.
- **Still recommended:** a human (the student/GVHD) should glance at the 12 PNGs at least once before plan 01-07 finalizes figure numbering and before the chapter is exported to `.docx`, since "looks legible in a report" is ultimately the reader's call.

## User Setup Required

None — no external service configuration required. The toolchain from plan 01-02 (`tools/render-diagrams.sh`, `tools/check-docs.py`, draw.io docker exporter, PlantUML jar) was reused without modification.

## Next Phase Readiness

- Chapter 2's process narrative (§2.1, §2.2) is now complete for all 5 processes plus the overview — plan 01-04 (parallel wave 2) can proceed independently on §2.3–2.6 (yêu cầu chức năng/phi chức năng, UC tổng quát, đặc tả UC2–UC5) without waiting on this plan, per the plan's own scope boundary (it never touched 01-04's files).
- Every AS-IS finding and step still carries `GIẢ ĐỊNH — chờ xác nhận` and cites a Q-ID — plan 01-07 (reconciliation with real interview minutes) has a complete, well-labeled surface to work against; no invented "confirmed" facts exist anywhere in this plan's output.
- `docs/truy-vet.md` was not touched by this plan (out of scope — no new FR/UC rows introduced); plan 01-04/01-07 will extend it as functional requirements and UC specs for the other 4 processes are written.
- No blockers for 01-04; 01-05 (kiến trúc/CSDL) and 01-06 (mockup) can reference the TO-BE step tables (`TB-DC-*`, `TB-TD-*`, `TB-BV-*`, `TB-KHO-*`) written here when designing screens/entities for those processes.

## Self-Check: PASSED

All 17 files (1 khảo sát doc, 5 `.drawio` sources, 10 PNGs, 1 modified `02-quy-trinh-nghiep-vu.md`) verified present on disk with `[ -f ]`/`ls`; all 3 task commit hashes (`c3d49fd`, `09d678b`, `9a58ae6`) verified present in `git log --oneline --all`; `git diff-tree --name-only` on both feat commits confirmed `bpmn/01-de-tai.drawio` was never touched.
