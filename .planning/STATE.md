---
gsd_state_version: "1.0"
current_phase: 3
current_phase_name: Outline, Progress, Defense & Archive
status: verifying
stopped_at: Completed 05-04-PLAN.md (deploy/verification part; report prose deferred by user)
last_updated: "2026-09-28T10:58:46.721Z"
last_activity: 2026-09-28
last_activity_desc: Phase 4 plan 04-07 complete (UC0.4 threshold screen + /api/thresholds with SC4 e2e, MH-14 highlights + signal tags, per-thesis share fix, chương 3 write-back, deploy README AI section; full phase gate green) — Phase 4 ready for verification
state_head: a3a98dd10cf06737668dbbe10c729fc21944335b
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 35
  completed_plans: 27
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-27)

**Core value:** Quy trình đồ án 5 UC chạy trọn end-to-end trên Web, và khi SV đăng ký đề tài hoặc nộp đề cương/báo cáo, hệ thống cảnh báo trùng lặp kèm đề tài/đồ án trùng, đoạn trùng và tỷ lệ tương đồng.
**Current focus:** Phase 3 — Outline, Progress, Defense & Archive

## Current Position

Phase: 3 (Outline, Progress, Defense & Archive) — EXECUTING
Plan: 7 of 7
Status: Phase complete — ready for verification
Last activity: 2026-09-28 — Plan 03-07 complete (bell + dashboards + smoke/e2e/README; Phase 3 gate green)

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
| Phase 03 P01 | 42min | 2 tasks | 39 files |
| Phase 03 P02 | 55min | 2 tasks | 14 files |
| Phase 03 P03 | 38min | 2 tasks | 13 files |
| Phase 03 P04 | 22min | 2 tasks | 17 files |
| Phase 03 P05 | 20min | 2 tasks | 11 files |
| Phase 03 P06 | 16min | 2 tasks | 21 files |
| Phase 03 P07 | 26min | 2 tasks | 20 files |
| Phase 04 P05 | 28min | 2 tasks | 25 files |
| Phase 04 P06 | 27 min | 2 tasks | 12 files |
| Phase 04 P07 | 26min | 3 tasks | 21 files |
| Phase 05 P04 | 35min | 3 tasks | 10 files |

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
- [Phase 03]: documents.py is the ONE shared upload/extraction service (validate→store→extract_text) for outline/progress/defense — never forked per UC
- [Phase 03]: document_check.run() (BackgroundTasks) always opens its own SessionLocal and wraps the whole body in a broad except → LOI, never leaving a row stuck DANG_KIEM_TRA
- [Phase 03]: outlines.review() implements both DA_DUYET and YEU_CAU_SUA branches together (Task 1) since they share one conditional-UPDATE/notification shape — avoided a throwaway Task-1-only placeholder
- [Phase 03]: AiClientStub.check_document scores at paragraph granularity (>=8 tokens/line, NFC) and excludes the query document's own de_tai_id from the corpus, not just its own row id
- [Phase 03]: documents/api.ts is the single source of DocumentOut/CheckSummary/CheckMatch/CheckSegment/CheckDetail; outlines/api.ts re-exports them
- [Phase 03]: CheckPanel's canRecheck is caller-supplied (not role-derived internally); OutlineReviewPage passes true since the route is GV/Bo mon-only and the server re-checks ownership
- [Phase 03]: AppLayout breadcrumb lookup switched to react-router matchPath (was exact pathname equality, silently broke every :param route's breadcrumb)
- [Phase 03]: [Phase 03]: GVHD-exclusion (D-06) checked in add_schedule AND update_committee, both under a hoi_dong row lock + UNIQUE(lich_bao_ve.sinh_vien_id) as final defense — never a UI-only warning
- [Phase 03]: [Phase 03]: gio_du_kien (per-student defense slot time) is always computed server-side (SLOT_MINUTES=30 offset from hoi_dong.gio_bao_ve by thu_tu), never stored
- [Phase 03]: [Phase 03]: FinalReportTab reuses VersionHistory with docLabel='báo cáo cuối' (no review-loop UI) instead of a new version-table component
- [Phase 03]: 03-04: finalize mean = Decimal sum/n quantize(0.01, ROUND_HALF_UP) under lich_bao_ve FOR UPDATE; conditional UPDATE WHERE da_chot = FALSE; archive row + KET_QUA_BAO_VE in the same transaction
- [Phase 03]: 03-04: AI ingest of a finalized thesis runs post-commit in BackgroundTasks (archive.run_ingest, own SessionLocal); payload DOCUMENT with latest BAO_CAO_CUOI text else TOPIC ten_de_tai+tu_khoa; failure leaves CHUA_INDEX
- [Phase 03]: 03-04: committee members get read access to BAO_CAO_CUOI only (documents.is_committee_member_for_topic), never outline/progress docs
- [Phase 03]: 03-04: do_an_kho gains additive ma_so_sinh_vien/ho_ten_sinh_vien snapshot columns (written back to ERD/class diagram/§3.2.3)
- [Phase 03]: 03-05: Archive search q=NFC contains(autoescape) on title OR keywords; utf8mb4_vietnamese_ci is case-insensitive but accent-sensitive ('thu vien' does not find 'thư viện')
- [Phase 03]: 03-05: Manual/imported archive records are nguon IMPORT without file; any update resets CHUA_INDEX and re-ingests in background
- [Phase 03]: 03-05: CSV import partial success — per-row errors with physical line number, valid rows in one transaction; ';' fallback + blank rows skipped
- [Phase 03]: 03-05: DELETE /api/archive removes the thesis_core row only — AI-side delete is a Phase 4 contract gap (§3.3.5 has no /delete)
- [Phase 03]: 03-06: D-05 late status computed on read by trang_thai_moc (VN date); SV trễ mốc = any NOP_TRE/TRE_MOC
- [Phase 03]: 03-06: final report (UC4.1) not gated on milestone completion — lateness tracked by UC3.4 only
- [Phase 03]: 03-06: bao_cao_tien_do.tai_lieu_do_an_id additive column; resubmit without file keeps previous attachment, new file = new BAO_CAO_TIEN_DO version
- [Phase 03]: 03-07: refused topic decisions roll back before any notification; approve/reject notify SV+GVHD / proposing GV / proposer in the same commit
- [Phase 03]: 03-07: bell polls only /notifications/unread-count every 30 s (paused in hidden tabs); list loads when the dropdown opens; client navigates only to single-slash app paths
- [Phase 03]: 03-07: dashboard<->progress use module imports to avoid an import cycle; progress.row_out shared by /tien-do-toan-khoa and the Bộ môn dashboard
- [Phase 4]: 04-05: title-check dedup keys on the thesis — an ARCHIVE record linked to a de_tai shares the TOPIC key and the higher score wins
- [Phase 4]: 04-05: Alembic 0010 writes calibrated defaults 67.80/10.40 + NGUONG_DOAN_TRUNG 67.70 only where tai_khoan_id IS NULL; tests pin stub-scale 50/30/80
- [Phase 4]: 04-05: api depends on ai with service_started only; AiClientHttp maps every failure to AiServiceError (endpoint + status only)
- [Phase 4]: 04-05: e2e cleanups purge TOPIC/ARCHIVE vectors (ai_index purge) before deleting rows so runs leave the AI index unchanged
- [Phase 04]: 04-06: document check sends NGUONG_DOAN_TRUNG + loai_tru (all same-topic DE_CUONG/BAO_CAO_CUOI versions); signal suffix in vi_tri; ingest DOCUMENT only after the stamped HOAN_TAT commit
- [Phase 04]: 04-06: app.seed_ai_corpus seeds 25 past-cohort theses (closed 'Dữ liệu lịch sử {khóa}' đợt, BAO_CAO_CUOI via documents.store) linked to IMPORT archive rows; idempotent
- [Phase 04]: 04-06: e2e-ai (K97) and ai-nfr (K96) share DTC225200095 + GV023 — never run in parallel
- [Phase 04]: 04-07: /api/thresholds is BO_MON-only; PUT takes all three rows (0-100, <=2 decimals, UC0.4 - E1); values read per request, never cached
- [Phase 04]: 04-07: MH-14/MH-09 per-thesis rate = share of ty_le_tong by stored passage characters (no schema change); fallback max passage score
- [Phase 04]: 04-07: highlightOverlap marks 3-word runs (NFC+lowercase) rendered as React text + mark elements; signal tag parsed from the vi_tri suffix
- [Phase 04]: 04-07: e2e/test threshold edits restore value AND editor/time so Alembic 0010 tai_khoan_id IS NULL semantics survive test runs
- [Phase 05]: 05-04: clean-clone install proven under a separate compose project (ntma-sach) with fresh volumes; working-copy volumes kept; ai runs HF_HUB_OFFLINE=1 after install-time model pre-fetch
- [Phase 05]: 05-04: report pages 4.3/4.5/4.8 and sinh-trang-kiem-thu.py deferred by user; inputs kept in docs/chuong-4-trien-khai/ket-qua-kiem-thu/ (tong-hop.json, cai-dat-sach.log)

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

Last session: 2026-09-28T10:58:46.665Z
Stopped at: Completed 05-04-PLAN.md (deploy/verification part; report prose deferred by user)
Resume file: None
