---
phase: 03-outline-progress-defense-archive
plan: 02
subsystem: ui
tags: [react, antd, tanstack-query, react-router, axios, fastapi]

requires:
  - phase: 03-outline-progress-defense-archive (plan 01)
    provides: "GET /api/outlines (list/detail), POST /api/outlines/{id}/submit|review, GET/POST /api/documents/{id}/check|download|recheck, thin MH-08/MH-09 tracer screens, OutlineDetail/OutlineListItem/CheckDetail schemas, deploy/e2e-uc2-5.sh"
provides:
  - "frontend/src/api/download.ts: downloadFile(path, fallbackName) — authorized blob download (D-02), parses Content-Disposition (RFC 5987 filename*=utf-8''… or plain filename=), surfaces a Blob error body's JSON `detail` as a DownloadError — the ONE download path every future plan (progress attachments, final report, archive) reuses"
  - "frontend/src/features/documents/{api,DocumentUpload,CheckStatusTag,CheckPanel,CheckDetailPage,routes}.tsx: shared document/duplicate-check UI surface — DocumentOut/CheckSummary/CheckMatch/CheckSegment/CheckDetail types now live in ONE place; useDocumentCheck (3s poll while DANG_KIEM_TRA, no retry on 4xx) and useRecheck; DocumentUpload (drag-drop + client pre-check + server-422 Alert); CheckStatusTag; CheckPanel (MH-09 panel: percentage, threshold comparison, top-3 matches table, Xem chi tiết); CheckDetailPage (MH-14 full skeleton: summary bar, source filter, side-by-side passages with Mức trùng Cao/Trung bình/Thấp tags) at /kiem-tra-trung-lap/:taiLieuId for all three roles"
  - "frontend/src/features/outlines/{OutlinePage,VersionHistory,OutlineReviewPage}.tsx: full MH-08 (Tabs on `?tab=`, upload, Lịch sử phiên bản table, Nhận xét của GVHD timeline) and full MH-09 (list with URL-kept Trạng thái filter, version Select with \"(mới nhất)\", tóm tắt trích xuất, Yêu cầu sửa/Duyệt đề cương form, live CheckPanel) — Bộ môn reuses the same OutlineReviewPage read-only"
  - "frontend/src/utils/format.ts: formatPercent, formatRelative added"
  - "frontend/src/layouts/AppLayout.tsx: breadcrumb route matching fixed to use react-router's matchPath instead of exact pathname equality — every parameterized route (:id, :taiLieuId) now shows its breadcrumb"
affects: [03-03, 03-04, 03-05, 03-06]

actuals:
  tokens: 15900
  tasks: 2
  commits: 2
  plan_head_before: 80e1ca8c2a4cbf04e325f8af3ec59dcc0c39a697
  plan_head_after: 5dcef8ea901f67bfc91b7d7fb993f289d257146e

tech-stack:
  added: []
  patterns:
    - "Shared documents feature (frontend/src/features/documents/) holds every duplicate-check UI primitive (types, hooks, DocumentUpload, CheckStatusTag, CheckPanel, CheckDetailPage) — outlines/progress/final-report/scoring all import from here instead of forking parallel implementations"
    - "MH-14 (CheckDetailPage) is a role-agnostic route with no menu entry, reached only via CheckPanel's \"Xem chi tiết\" or a version-history \"Xem kết quả\" link — documents.get_viewable_or_error is the only access gate"
    - "DocumentUpload owns file selection + server-error display (422 → titled Alert); the page supplies onSubmit (the actual mutateAsync + success toast), keeping the upload widget reusable across outline/progress/final-report without duplicating error-parsing logic"
    - "VersionHistory's docLabel prop ('đề cương' | 'báo cáo cuối') toggles the Trạng thái duyệt column and Nhận xét của GVHD timeline — plan 03-04 reuses the same component for the no-review-loop báo cáo cuối tab by passing docLabel='báo cáo cuối'"

key-files:
  created:
    - frontend/src/api/download.ts
    - frontend/src/features/documents/api.ts
    - frontend/src/features/documents/DocumentUpload.tsx
    - frontend/src/features/documents/CheckStatusTag.tsx
    - frontend/src/features/documents/CheckPanel.tsx
    - frontend/src/features/documents/CheckDetailPage.tsx
    - frontend/src/features/documents/routes.tsx
    - frontend/src/features/outlines/VersionHistory.tsx
  modified:
    - frontend/src/features/outlines/api.ts
    - frontend/src/features/outlines/OutlinePage.tsx
    - frontend/src/features/outlines/OutlineReviewPage.tsx
    - frontend/src/features/outlines/routes.tsx
    - frontend/src/utils/format.ts
    - frontend/src/layouts/AppLayout.tsx

key-decisions:
  - "documents/api.ts is now the single source of DocumentOut/CheckSummary/CheckMatch/CheckSegment/CheckDetail; outlines/api.ts imports and re-exports them so no existing import path broke"
  - "CheckPanel's canRecheck is a caller-supplied boolean (not role-derived internally) — OutlineReviewPage passes true unconditionally since the route itself is GV/Bộ môn-only and the server independently re-checks ownership on POST /recheck"
  - "OutlineReviewPage keeps trang_thai filter in the URL (?trang_thai=) but the selected-version and nhận xét form state stay local — only the two pieces of state a bookmarked/shared link should reproduce (which list filter, which outline) live in the URL"

patterns-established:
  - "Every future document-check UI (progress, final report, defense scoring) renders through documents/CheckPanel.tsx and documents/CheckDetailPage.tsx — never a per-screen reimplementation of the percentage/threshold/match-table layout"
  - "AppLayout's route→breadcrumb lookup MUST use matchPath, not pathname equality, now that the app has parameterized routes without a matching literal fallback — future dynamic routes get correct breadcrumbs for free"

requirements-completed: [OUTL-01, OUTL-02, OUTL-03]

coverage:
  - id: D1
    description: "SV's Đề cương tab matches MH-08 — drag-and-drop upload with NFR-06 hint, 422 error Alert titled 'Nộp thất bại: sai định dạng file', Lịch sử phiên bản table (Phiên bản/Ngày nộp/Trạng thái duyệt/Kết quả kiểm tra/Tải file/Xem kết quả), Nhận xét của GVHD timeline showing both Yêu cầu sửa and Đã duyệt entries with nhận xét text"
    requirement: "OUTL-01"
    verification:
      - kind: automated_ui
        ref: "deploy/dom-check.sh /kiem-tra-trung-lap/1 'Mã SV/GV hoặc email' — pass (unauthenticated deep link ends on login form)"
        status: pass
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh — full revision loop (v1 DOCX → Yêu cầu sửa → v2 PDF → Duyệt), 422 renamed-ZIP rejection, cross-role 403s, sha256 download byte-identity — pass, rerun clean after CDP session + AppLayout fix"
        status: pass
      - kind: manual_procedural
        ref: "CDP session (scratchpad cdp_check_0302.py/0302c.py): p0302-01 (empty state) .. p0302-04 (Hoàn tất - 50% against a genuine cross-topic duplicate), p0302-11b (Nhận xét của GVHD timeline, both entries) — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Visual fidelity to MH-08 in a real browser is a judgment call; self-performed via CDP per the autonomous-run instruction, genuine user confirmation still pending."
  - id: D2
    description: "GVHD's Duyệt đề cương screen matches MH-09 — list with Trạng thái filter (URL-kept), version Select with '(mới nhất)', download link with format+size, tóm tắt trích xuất or D-03 warning, live CheckPanel (percentage, threshold Tag, top matches, Xem chi tiết) that never blocks approval while DANG_KIEM_TRA, Yêu cầu sửa (nhận xét required) / Duyệt đề cương (Popconfirm) only on the latest pending version"
    requirement: "OUTL-02"
    verification:
      - kind: e2e
        ref: "deploy/e2e-uc2-5.sh — pass (see D1)"
        status: pass
      - kind: manual_procedural
        ref: "CDP session: p0302-07/08 (review detail + Yêu cầu sửa, first full run — screenshots later overwritten by a broken retry, but DB state (luot_duyet_de_cuong rows for both YEU_CAU_SUA and DA_DUYET) proves the flow executed), p0302-11/11b (Đã duyệt state with 50% tỷ lệ tổng, Vượt ngưỡng cảnh báo tag, Đồ án trùng nhiều nhất table with correct Khóa column parsed from the '(K96)' label suffix) — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Visual fidelity to MH-09 and the review interaction in a real browser is a judgment call; self-performed via CDP, genuine user confirmation still pending."
  - id: D3
    description: "MH-14 (/kiem-tra-trung-lap/:taiLieuId) shows the full check result — summary bar (Tỷ lệ tổng/Ngưỡng áp dụng/Trạng thái/Thời điểm/Loại tài liệu), source filter list, side-by-side Đoạn trong tài liệu nộp / Đoạn nguồn with Mức trùng Cao/Trung bình/Thấp tags — reachable by all three roles subject to documents.get_viewable_or_error, with a correct breadcrumb"
    requirement: "OUTL-02"
    verification:
      - kind: automated_ui
        ref: "grep -q 'Mức trùng' CheckDetailPage.tsx && grep -q \"'/kiem-tra-trung-lap/:taiLieuId'\" documents/routes.tsx — pass; deploy/dom-check.sh /kiem-tra-trung-lap/1 — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP: p0302-05 (initial) / p0302-05b (after the AppLayout matchPath fix) — genuine 100% Mức trùng: Cao segments against the real Topic-A duplicate, source filter list with (K96) Khóa, breadcrumb 'Kiểm tra trùng lặp / Chi tiết kết quả kiểm tra trùng lặp' rendering correctly — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Visual fidelity to MH-14 in a real browser is a judgment call; self-performed via CDP, genuine user confirmation still pending."
  - id: D4
    description: "Bộ môn reuses OutlineReviewPage read-only — sees 'Đề cương toàn khoa' (all outlines, default Tất cả filter) with a Xem-only action column and no Yêu cầu sửa/Duyệt đề cương buttons on the detail screen"
    requirement: "OUTL-03"
    verification:
      - kind: unit
        ref: "backend/tests/test_outline_flow.py::test_outline_access_is_scoped (03-01, unchanged) — Bộ môn 200 view/download + 403 review — pass"
        status: pass
      - kind: manual_procedural
        ref: "CDP: p0302-12-bomon-list.png (Đề cương toàn khoa, both test topics listed, Hành động column shows only 'Xem') / p0302-13-bomon-readonly-detail.png (no action form) — self-viewed"
        status: pass
    human_judgment: true
    rationale: "Visual confirmation that no action buttons render for Bộ môn is a judgment call best done in a real browser; self-performed via CDP, genuine user confirmation still pending."

duration: ~55min
completed: 2026-09-28
status: complete
---

# Phase 3 Plan 2: MH-08/MH-09/MH-14 Full Fidelity + Shared Document UI Summary

**Shared `features/documents/*` (authorized download, upload widget, check-status tag, duplicate-check panel, MH-14 detail page) power the full MH-08 SV screen and MH-09 GVHD/Bộ môn review screen, replacing 03-01's thin tracer with production-quality UI — no backend change.**

## Performance

- **Duration:** ~55 min
- **Tasks:** 2/2 completed
- **Files modified:** 14 (8 created, 6 modified)

## Accomplishments

- **Task 1 — shared document UI + MH-08:** `frontend/src/api/download.ts` is the one authorized blob-download path (D-02) — reads the Content-Disposition header Starlette actually emits (`filename*=utf-8''…` when non-ASCII, plain `filename="…"` otherwise, confirmed against the installed Starlette 1.2.1 `FileResponse` source), and surfaces a Blob error body's JSON `detail` as a `DownloadError`. `frontend/src/features/documents/` centralizes every duplicate-check UI primitive: the `DocumentOut`/`CheckSummary`/`CheckMatch`/`CheckSegment`/`CheckDetail` types (now declared once, re-exported from `outlines/api.ts`), `useDocumentCheck`/`useRecheck` hooks, `DocumentUpload` (drag-drop, client-side extension/size pre-check as UX only, server-422 Alert titled exactly "Nộp thất bại: sai định dạng file" per MH-08), `CheckStatusTag`, `CheckPanel` (MH-09's percentage/threshold/top-matches panel, reused as-is by MH-09), and `CheckDetailPage` (MH-14's full skeleton: summary bar, clickable source-filter list, side-by-side "Đoạn trong tài liệu nộp"/"Đoạn nguồn" cards with Cao/Trung bình/Thấp `Mức trùng` tags) at `/kiem-tra-trung-lap/:taiLieuId` for all three roles. `OutlinePage.tsx` now renders the full MH-08 Đề cương tab (Tabs keyed on `?tab=`, upload card with a disabled-reason Alert per state, `VersionHistory` table + GVHD-comments Timeline).
- **Task 2 — MH-09 full fidelity, Bộ môn read-only:** `OutlineReviewPage.tsx` gained the full MH-09 layout — a list Card with a Trạng thái Select kept in the URL (`?trang_thai=`, default Chờ duyệt for GV / Tất cả for Bộ môn) and a review Card with a phiên bản Select ("v{n} - nộp {date} (mới nhất)"), download link with format+size, tóm tắt trích xuất (or the D-03 extraction-failure warning), an Alert for an already-reviewed version, and the Yêu cầu sửa/Duyệt đề cương form gated on `quyen.duyet` + newest-version-selected. The right-hand `CheckPanel` never disables approval while `DANG_KIEM_TRA` (UC2.2 E1). Bộ môn hits the identical route/component — `quyen.duyet` is server-computed `false` for BO_MON so the form never renders (T-03-13: UI hides for UX, the API independently refuses `BO_MON` review). `routes.tsx` now serves `/duyet-de-cuong` to both `GIANG_VIEN` and `BO_MON` under one `MenuEntry` (same label/order for both, so no shim route was needed, unlike `/de-tai`).
- **Both tasks' `<human-check>` items were self-performed** via a CDP-driven headless Chrome session against genuinely generated cross-topic duplicate data (two real test topics sharing two DOCX paragraphs, producing an authentic 50% `tỷ_le_tong` / 100% per-segment `Mức trùng: Cao` match) — see coverage D1-D4 and "Human-check" below.

## Task Commits

1. **Task 1: shared document UI + MH-08 full fidelity** — `0e794b0` (feat)
2. **Task 2: MH-09 full fidelity, Bộ môn read-only** — `5dcef8e` (feat)

## Files Created/Modified

**Created:** `frontend/src/api/download.ts`; `frontend/src/features/documents/{api,DocumentUpload,CheckStatusTag,CheckPanel,CheckDetailPage,routes}.tsx`; `frontend/src/features/outlines/VersionHistory.tsx`.
**Modified:** `frontend/src/features/outlines/{api,OutlinePage,OutlineReviewPage,routes}.tsx`; `frontend/src/utils/format.ts` (added `formatPercent`/`formatRelative`); `frontend/src/layouts/AppLayout.tsx` (breadcrumb route-matching fix, see Deviations).

## Decisions Made

See `key-decisions` in frontmatter. Summary: document/check types now live in exactly one file (`features/documents/api.ts`); `CheckPanel`'s `canRecheck` is caller-supplied rather than re-deriving role logic; only the outline-review page's list filter and selected outline live in the URL, not the transient review-form state.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `AppLayout.tsx`'s breadcrumb lookup never matched any parameterized route**
- **Found during:** Task 1's human-check (MH-14 screenshot showed no breadcrumb at all)
- **Issue:** `matchedRoute = routes.find((route) => route.path === location.pathname)` compares the route's raw pattern string (e.g. `/kiem-tra-trung-lap/:taiLieuId`) against the browser's actual pathname (e.g. `/kiem-tra-trung-lap/1`) with strict equality — this can never match for ANY route with a `:param` segment. The bug pre-dates this plan (it already silently broke `/de-tai/:id` and `/de-tai/:id/sua` breadcrumbs since Phase 2), but this plan's new `/kiem-tra-trung-lap/:taiLieuId` route made it visible and the plan explicitly requires this route's breadcrumb.
- **Fix:** Switched to react-router's `matchPath({ path: route.path, end: true }, location.pathname)`, which is pattern-aware and behaves identically to strict equality for literal (non-parameterized) paths — verified no regression on static routes via `dom-check.sh` and a fresh CDP pass.
- **Files modified:** `frontend/src/layouts/AppLayout.tsx`
- **Verification:** CDP screenshot `p0302-05b-sv-mh14-breadcrumb-fixed.png` shows "Kiểm tra trùng lặp / Chi tiết kết quả kiểm tra trùng lặp"; `deploy/dom-check.sh` re-run clean for `/kiem-tra-trung-lap/1`, `/duyet-de-cuong`, `/de-tai/1`.
- **Committed in:** `0e794b0` (Task 1 commit)

**2. [Rule 1 - Bug] `VersionHistory`'s GVHD-comment line produced a stray double dash for an approval with no nhận xét**
- **Found during:** Task 2's human-check (CDP screenshot of the "Đã duyệt" timeline entry)
- **Issue:** The line always rendered `{nhan_xet || '—'} — {giang_vien.ho_ten}`, so an approval without a nhận xét (nhận xét is optional for `DA_DUYET`, only mandatory for `YEU_CAU_SUA`) showed "— — Mai Đức Tùng" instead of just the reviewer's name.
- **Fix:** Render `nhận_xét — tên` only when nhận xét is present, otherwise just the reviewer's name.
- **Files modified:** `frontend/src/features/outlines/VersionHistory.tsx`
- **Verification:** CDP screenshot `p0302-11b-gv-nhan-xet-fixed.png` shows a clean "Mai Đức Tùng" line for the no-comment approval entry.
- **Committed in:** `0e794b0` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs). **Impact:** Both fixes are small, targeted, and verified regression-free against every existing route/screen; no scope creep — both were directly required for this plan's own MH-14/MH-08 fidelity requirements.

## Issues Encountered

- The first CDP human-check run (`cdp_check_0302.py`) executed the ENTIRE review lifecycle correctly (v1 submit → Yêu cầu sửa → v2 resubmit → Duyệt đề cương) in one pass, but a follow-up script meant only to re-screenshot the MH-14 breadcrumb after the `AppLayout` fix instead tried to redo steps that no longer applied (the outline was already `DA_DUYET`), overwriting several intermediate screenshots (list/review-detail/Yêu cầu sửa states) with less useful "already done" states. The final DB state (`luot_duyet_de_cuong` rows for both `YEU_CAU_SUA` and `DA_DUYET`) and the surviving `p0302-11-gv-after-approve.png` screenshot still prove the full flow executed and rendered correctly; a fresh Bộ môn read-only screenshot and a "no stray dash" GV screenshot were captured afterward to close the gap. Scratchpad-tooling sequencing issue only, not a shipped-code defect.

## Human-check (self-performed, pending user confirmation)

Per the autonomous-run instruction, self-performed both tasks' `<human-check>` via a CDP-driven headless Chrome session (`google-chrome --headless=new --remote-debugging-port=9345 --remote-allow-origins='*'`), screenshots in the scratchpad (not committed to the repo):

Set up two genuine test topics under a throwaway cohort (K96): Topic A (DTC225200001/GV002, outline approved) sharing two DOCX paragraphs with Topic B (DTC225200098/GV029, the main demo topic) so the duplicate-check panel and MH-14 detail show REAL non-zero matches, not fixture zeros.

- **p0302-01/02:** SV's empty Đề cương tab, then a `.zip` renamed `.docx` rejected with the exact MH-08 error copy ("Nộp thất bại: sai định dạng file" + the NFR-06 explanation).
- **p0302-03/04:** Valid DOCX submit → toast → `Chờ duyệt` + `Đang kiểm tra` → reload shows `Hoàn tất - 50%` (genuine cross-topic match), Lịch sử phiên bản table and pending Nhận xét-của-GVHD entry render correctly.
- **p0302-05/05b:** MH-14 detail — summary bar, source-filter list (with `(K96)` Khóa parsed correctly), side-by-side passages, `Mức trùng: Cao (100%)` tags; `05b` (after the `AppLayout` fix) shows the breadcrumb rendering.
- **GV029 full review lifecycle** (executed successfully, confirmed via DB state and `p0302-11-gv-after-approve.png`): list filtered to Chờ duyệt → review detail with `Tóm tắt nội dung đã trích xuất`, `CheckPanel` showing `50% · Vượt ngưỡng cảnh báo` and the top-match table → `Yêu cầu sửa` with a nhận xét → SV resubmits v2 → GV `Duyệt đề cương` (Popconfirm) → final screen shows both timeline entries (`Yêu cầu sửa` then `Đã duyệt`), version history with both `v1`/`v2` rows, correct `Tải file`/`Xem kết quả` actions.
- **p0302-11b:** re-confirmed the no-nhận-xét approval line renders cleanly after the fix.
- **p0302-12/13:** Bộ môn's "Đề cương toàn khoa" list (both test topics, `Xem`-only action column) and the read-only detail screen (no Yêu cầu sửa/Duyệt đề cương buttons).

Test data (cohort id 24, topics 47/48, their `tai_lieu_do_an`/`ket_qua_kiem_tra_trung_lap`/`luot_duyet_de_cuong`/`thong_bao` rows, and the 3 uploaded files) fully deleted afterward; `deploy/e2e-uc2-5.sh` and `deploy/dom-check.sh` re-run clean post-cleanup.

**User confirmation of this check is still pending** — flagged here per coverage items D1-D4.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

Phase 3's outline UI (UC2, OUTL-01..03) is now full-fidelity and production-quality. `features/documents/*` is the shared foundation the remaining Phase 3 plans build on:
- **03-03** (progress reports, PROG-01..03) reuses `DocumentUpload`/`CheckPanel`/`CheckDetailPage` as-is for the (optional) progress-report attachment and its duplicate check, and `VersionHistory` with `docLabel='báo cáo tiến độ'` if it ever needs a version table (though `bao_cao_tien_do` is upsert-not-version per 03-RESEARCH.md Pitfall 5).
- **03-04** (defense, final report) reuses `DocumentUpload`/`CheckPanel`/`CheckDetailPage`/`VersionHistory` (with `docLabel='báo cáo cuối'`, hiding the Trạng thái duyệt column and GVHD-comments timeline since there's no revision loop) for the "Báo cáo cuối" tab this plan reserved on `OutlinePage`'s `Tabs items` array.
- **03-05/03-06** reuse `downloadFile`/`CheckPanel`/`CheckDetailPage` for archive attachments and committee scoring screens.

No blockers. The one pending item is genuine user confirmation of the four self-performed CDP checks (D1-D4, coverage), not a functional gap.

---
*Phase: 03-outline-progress-defense-archive*
*Completed: 2026-09-28*

## Self-Check: PASSED

All 14 created/modified key files confirmed present on disk; both task commits (`0e794b0`, `5dcef8e`) confirmed present in `git log --oneline --all`.
