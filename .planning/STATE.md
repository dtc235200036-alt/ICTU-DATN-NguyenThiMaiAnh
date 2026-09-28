---
gsd_state_version: "1.0"
current_phase: 3
current_phase_name: Outline, Progress, Defense & Archive
status: executing
stopped_at: Phase 3 context gathered (auto); Phase 2 awaiting UAT; Phase 1 paused at 01-07 human checkpoint
last_updated: "2026-09-28T01:50:42.254Z"
last_activity: 2026-09-28
last_activity_desc: Phase 3 execution started
state_head: b7bfbd1b638401f2c8da6d88833a69203c90a40a
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 20
  completed_plans: 12
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-27)

**Core value:** Quy trình đồ án 5 UC chạy trọn end-to-end trên Web, và khi SV đăng ký đề tài hoặc nộp đề cương/báo cáo, hệ thống cảnh báo trùng lặp kèm đề tài/đồ án trùng, đoạn trùng và tỷ lệ tương đồng.
**Current focus:** Phase 3 — Outline, Progress, Defense & Archive

## Current Position

Phase: 3 (Outline, Progress, Defense & Archive) — EXECUTING
Plan: 1 of 7
Status: Executing Phase 3
Last activity: 2026-09-28 — Phase 3 execution started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 12min | 3 tasks | 15 files |
| Phase 01 P02 | 32min | 2 tasks | 29 files |
| Phase 01 P03 | 25min | 3 tasks | 17 files |
| Phase 01 P04 | 14min | 3 tasks | 34 files |
| Phase 01 P05 | 36min | 3 tasks | 35 files |
| Phase 01 P06 | 95min | 3 tasks | 29 files |
| Phase 02 P01 | 40min | 2 tasks | 65 files |
| Phase 02 P02 | 50min | 2 tasks | 17 files |
| Phase 02 P03 | 45min | 2 tasks | 11 files |
| Phase 02 P04 | 40min | 2 tasks | 27 files |
| Phase 02 P05 | 30min | 2 tasks | 9 files |
| Phase 02 P06 | 65min | 2 tasks | 18 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 5 phase (coarse), vertical slices; tên phase bằng tiếng Anh để slug thư mục sạch, goal/criteria bằng tiếng Việt
- [Roadmap]: Apache HTTPS (DEPL-02) + seed 100 SV/30 GV (DATA-01) dựng ngay ở Phase 2, không đợi T9
- [Roadmap]: AI client là stub ở Phase 2–3; Phase 4 thay stub bằng dịch vụ AI thật
- [Roadmap]: Seed 300 đề tài + 50 file (DATA-02/03) làm cùng Phase 4 để làm corpus và tập hiệu chỉnh ngưỡng
- [Phase 01]: 40 câu hỏi phỏng vấn (13 BM/14 GV/13 SV), mã CHUNG dùng lại cho câu hỏi chung; 1 file mẫu biên bản gộp 3 vai trò thay vì 3 file riêng
- [Phase 01]: draw.io docker exporter needs --shm-size=1g or Electron renderer crashes on non-trivial diagrams (1-based page-index confirmed empirically)
- [Phase 01]: AS-IS BPMN and step rows marked GIẢ ĐỊNH — chờ xác nhận (D-01/D-02: no interviews yet); removed only when a BB-*/TL-* source is cited (plan 01-07)
- [Phase 01]: design-taste-frontend skill is out-of-scope for dashboards; D-12 (Ant Design admin) overrides its design-system guidance, only neutral anti-slop principles applied
- [Phase 01]: Overview BPMN (00-tong-quan) đặt 2 service task Hệ thống dùng chung (Kiểm tra trùng lặp, Thông báo in-app) fan-in từ Đề tài/Đề cương/Tiến độ/Bảo vệ thay vì lặp lại ở từng sơ đồ con
- [Phase 01]: MAU-03 (Đề cương) suy ra trực tiếp từ đề cương gốc thật (H01.DTC235200036...docx, mục 1-9), không gắn nhãn giả định; 6 biểu mẫu MAU còn lại cite TL-ID và gắn nhãn chờ xác nhận
- [Phase 01]: [Phase 01]: FR module TK (tai khoan/phan quyen) added; docs/README.md convention table updated to match
- [Phase 01]: [Phase 01]: Fixed stale 05-so-do-uc-tong-quat.md references (docs/README.md, docs/truy-vet.md) to the real 05-so-do-use-case.md filename
- [Phase 01]: DeTai state machine uses two entry paths into DA_PHAN_CONG (GV-proposed via DA_DUYET+SV registration vs SV-proposed direct) reconciled from locked UC1.2/UC1.3 wording
- [Phase 01]: 1 SV : 1 active topic enforced via MySQL generated column + UNIQUE index (NULL-permissive); 1 topic : 1 SV under concurrent registration via conditional UPDATE ... WHERE sinh_vien_id IS NULL
- [Phase 01]: PlantUML enum blocks must be connected via a dependency line to their owning class - disconnected enum nodes crash the Smetana layout engine used when Graphviz dot is absent
- [Phase 01]: design-taste-frontend lists dashboards/data tables as Out of Scope; D-12 (Ant Design admin) overrides its design-system guidance again in 01-06, only neutral anti-slop principles applied
- [Phase 01]: Removed .ant-layout min-height:100vh from antd-admin.css: headless Chrome --screenshot only captures the declared viewport, so it was clipping Drawer/Modal overlays and trailing state-panel sections; screens now size to content
- [Phase 01]: mockup-state-panel pattern: alternate-state illustrations (Modal/Spin/error) placed in normal document flow after ant-layout closes, avoiding stacked overlays
- [Phase 02]: Apache mod_proxy_http does not enforce LimitRequestBody for proxied /api/* traffic — enforced the 25MB body limit at the ASGI layer instead (app/core/body_limit.py)
- [Phase 02]: PUBLIC_ROUTES extended to include FastAPI's own /api/docs and /api/openapi.json so the route-coverage test passes without weakening AUTH-03
- [Phase 02]: Task 2 followed real RED->GREEN TDD cycle (test commit then feat commit) honoring task-level tdd="true" even though the plan frontmatter is type: execute
- [Phase 02]: Account service 404s (not 403) when the target is BO_MON, uniformly making BO_MON accounts uncreatable/unalterable via /api/accounts without a special-cased error path
- [Phase 02]: [Phase 02]: dot_do_an router uses per-route require_role (GET any-role, writes BO_MON-only) instead of a shared router-level dependency, since accounts.py's uniform-role pattern doesn't fit mixed-permission routes
- [Phase 02]: [Phase 02]: Faker(vi_VN) names built from last/middle/first-name provider calls composed in Vietnamese order, never .name()/address-style providers (Pitfall 5 — English token leak)
- [Phase 02]: [Phase 02]: getErrorMessage() fixed to parse FastAPI/Pydantic's list-shaped 422 detail — app-wide fix, not cohort-specific, found via this plan's own human-check
- [Phase 02]: [Phase 02]: AiClientStub scores deterministic Jaccard similarity over NFC-casefolded syllable sets (D-10 stub, verified 66.67% on the plan's fixed example pair) — Phase 4 swaps for a real semantic model behind the same {matches:[{ref_id,ty_le}]} seam
- [Phase 02]: [Phase 02]: Title-check computed before the write transaction, persisted in the SAME commit as the topic status change (create_topic gui=True / submit_topic) — never a separate write, keeping the saved result and CHO_DUYET transition atomically consistent
- [Phase 02]: [Phase 02]: react-query default retry(3) turns a definitive 403 into an infinite Skeleton for any consumer treating isLoading||!data as still-loading — useTopic now skips retry on 4xx; found via this plan's own human-check
- [Phase 02]: [Phase 02] TopicListParams stays a plain dataclass (not Pydantic) — FastAPI Query() already validates/coerces trang_thai/pham_vi/sap_xep enums before the router builds it
- [Phase 02]: [Phase 02] register_topic's rowcount=0 re-read only picks the user-facing error message — the accept/reject decision was already made atomically by the conditional UPDATE's WHERE clause, never a check-then-act gap
- [Phase 02]: [Phase 02]: topic_approval.py reuses topics_service._person_refs/get_topic directly rather than forking a parallel implementation
- [Phase 02]: [Phase 02]: GVHD never pre-selected even for the sole proposing GV (UC1.3 E1) — enforced independently on frontend (disabled button) and backend (422 if omitted)
- [Phase 02]: [Phase 02]: dashboard services use only COUNT()/exists() aggregates per role, never a Python loop over all rows

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1]: Khảo sát thực tế (ANLS-01) cần phỏng vấn bộ môn/GV/SV — lên lịch ngay T1
- [Phase 1 → 4]: Cần file mẫu đề cương/báo cáo chính thức + ~20 đồ án thật để lọc phần mẫu chung và hiệu chỉnh AI
- [Phase 4]: Độ chính xác model embedding tiếng Việt trên văn bản đồ án chưa kiểm chứng (bkai vs multilingual-e5) — so sánh đầu phase, có timebox
- [Timeline]: Hạn cứng 07/12/2026, không có tuần đệm
- [Research]: research/SUMMARY.md giả định T1–T3 đã xong; thực tế tiến độ bắt đầu 28/09/2026 — roadmap coi như chưa có gì hoàn thành

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-09-28T01:01:46.179Z
Stopped at: Phase 3 context gathered (auto); Phase 2 awaiting UAT; Phase 1 paused at 01-07 human checkpoint
Resume file: .planning/phases/03-outline-progress-defense-archive/03-CONTEXT.md
