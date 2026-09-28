---
phase: 05-system-verification-defense-package
plan: 05
status: complete
scope_note: "Product/verification part only. Report prose and slide material deferred by user ('Bộ báo cáo, slide không gen bây giờ'): docs/chuong-4-trien-khai/06-huong-dan-su-dung-va-ket-qua.md (4.6), 08-kiem-thu-va-do-kiem-nfr.md (4.8) and docs/kich-ban-demo.md were NOT created"
subsystem: demo-verification
tags: [D-04, D-08, NFR-16, RPRT-01, RPRT-02, CDP, demo-state, screenshots, rehearsal]
requires:
  - "05-04: deploy/verify-all.sh, tong-hop.json, install.sh, seeded + AI-indexed stack"
  - "Phases 2-4: full product (UC0-UC5, AI title/document checks)"
provides:
  - "deploy/demo-state.sh — scoped reset + API build-up of the defense demo state (default / --chi-xoa / --dem)"
  - "tools/demo/cdp.py — dependency-free headless Chrome CDP driver (host websockets)"
  - "tools/demo/chay-kich-ban.py — JSON scenario runner (--json manifest, --log Markdown, --chi-doc)"
  - "tools/demo/kich-ban-anh.json — 27 screenshot steps uc0..uc5 (MH-01..MH-14, 3 roles)"
  - "tools/demo/kich-ban-demo.json — machine twin of the defense demo, B01..B16 with timeline, accounts, files, expected texts, talking points"
  - "docs/chuong-4-trien-khai/anh/*.png (27, 1440x900) + ket-qua-kiem-thu/anh-chup.json manifest"
  - "docs/chuong-4-trien-khai/ket-qua-kiem-thu/tap-duot-demo.md — raw rehearsal log (16/16 OK, 71.6 s)"
  - "verify-all: 'trạng thái demo' before/after check (all modes) + live NFR-16 step (full mode); tong-hop.json NFR-16 Đạt"
affects: [05-06, 05-07, 05-08]
tech-stack:
  added: []
  patterns:
    - "Browser automation without Playwright: Chrome --remote-debugging-port=0 on 127.0.0.1, DevToolsActivePort, host websockets, focus emulation, vi-VN via LANGUAGE/LANG env"
    - "Scenario JSON = single source for screenshots, rehearsal and NFR-16; steps that write data flagged ghi_du_lieu and skipped by --chi-doc"
    - "Demo rows fingerprinted (count + md5 of status/score columns) by demo-state.sh --dem; verify-all compares before/after"
key-files:
  created:
    - deploy/demo-state.sh
    - tools/demo/cdp.py
    - tools/demo/chay-kich-ban.py
    - tools/demo/kich-ban-anh.json
    - tools/demo/kich-ban-demo.json
    - docs/chuong-4-trien-khai/anh/ (27 PNG)
    - docs/chuong-4-trien-khai/ket-qua-kiem-thu/anh-chup.json
    - docs/chuong-4-trien-khai/ket-qua-kiem-thu/tap-duot-demo.md
  modified:
    - deploy/verify-all.sh
    - deploy/README.md
    - docs/chuong-4-trien-khai/ket-qua-kiem-thu/tong-hop.json
    - docs/chuong-4-trien-khai/ket-qua-kiem-thu/nhat-ky-verify-all.log
    - frontend/index.html
    - frontend/src/features/outlines/OutlineReviewPage.tsx
decisions:
  - "Demo accounts kept as planned (DTC225200011-015, GV011-GV014, bomon, K22 đợt): none is used by an automated script; the old manual AI demo in deploy/README.md was switched from DTC225200011 to DTC225200010"
  - "Demo files deliberately skip the first passing CHEP_NGUYEN_VAN (P01) and KHONG_LIEN_QUAN (P21) pairs: e2e-ai.sh submits exactly those and asserts the archive source is top-1; a demo copy of the same B file in the DOCUMENT index would break it. Chosen: 012 outline P02-B (48.04 %), 011 live upload P03-B (49.3 %), 013 P22-B, 014/015 outlines P16-B/P17-B, finals P23-B/P24-B"
  - "Milestones of the K22 đợt are get-or-create by name and re-dated each run to today +3/+17/+45 days (clamped to the đợt end) so the demo reads 'Đúng hạn / Chưa đến hạn' on any demo day"
  - "NFR-16 is measured live inside verify-all (read-only subset, 23 screens) when the demo state exists, else taken from the committed anh-chup.json"
  - "verify-all --report regenerated tong-hop.json/nhat-ky; the machine-generated AI page thu-nghiem-ai/04-hieu-nang-va-bao-mat.md was reverted (it would now say 304 titles because the demo topics are indexed) — 05-08's final --report run regenerates it"
metrics:
  duration: "~62 min"
  completed: 2026-09-28
estimate:
  tokens: 170000
actuals:
  tokens: 31000
  tasks: 3
  commits: 8
commits: 8
plan_head_before: 2f6da8f034df5b3c18cc4868b9219c8aad18af85
plan_head_after: 65aca9eacf82b5aaedab65435b960b64aa6a7300
---

# Phase 5 Plan 05: Demo state, CDP screenshot driver, NFR-16 and first automated rehearsal Summary

`bash deploy/demo-state.sh` rebuilds the rehearsed defense state in ~19 s. The screenshot run uses a committed headless-Chrome CDP driver and a JSON scenario to capture 27 real 1440×900 screens across 5 UCs and 3 roles. The automated twin of the defense demo (B01–B16) ran 16/16 without errors in 71.6 s. `verify-all --report` now passes all 14 steps with NFR-01…NFR-19 all Đạt, and confirms the demo rows stay unchanged.

## Scope executed (user instruction)

Built: `deploy/demo-state.sh`, `tools/demo/{cdp.py, chay-kich-ban.py, kich-ban-anh.json, kich-ban-demo.json}`, the screenshots + `anh-chup.json`, NFR-16 and the demo-intact check in `verify-all.sh`/`tong-hop.json`, the raw rehearsal log `tap-duot-demo.md`, and the "Kịch bản demo bảo vệ (Phase 5)" section in `deploy/README.md`.

**Deferred by user ("Bộ báo cáo, slide không gen bây giờ"). These were NOT created:**
- `docs/chuong-4-trien-khai/06-huong-dan-su-dung-va-ket-qua.md` (4.6 user guide + functional results). Inputs are ready: 27 PNGs, `anh-chup.json` (id → mô tả, vai trò, MH, màn hình mong đợi, kết quả), and per-suite status in `tong-hop.json`.
- `docs/chuong-4-trien-khai/08-kiem-thu-va-do-kiem-nfr.md` (4.8, incl. NFR-16). The numbers are in `tong-hop.json` (`nfr[15]`). `tools/bao-cao/sinh-trang-kiem-thu.py` is still not written (deferred since 05-04).
- `docs/kich-ban-demo.md` (the presenter's prose script). `tools/demo/kich-ban-demo.json` already carries every field it needs (timeline, accounts, files, exact title, expected screens, talking points `y_can_noi`, requirement ids). The fallback plan still has to be written into the prose.
- As a result, these Task 2/3 checks were not run: `check-docs links/pi-tags` on the 06 page, `build-report.sh`/`kiem-tra-bao-cao.py`, and the `kich-ban-demo.md` id/privacy check.

## Demo state (`deploy/demo-state.sh`)

| Account | State after the script |
|---|---|
| DTC225200011 | no topic. Live demo: paraphrased title → AI warning 81.92 % (archive "Ứng dụng SQL Server trong quản lý kế toán tại công ty CP Hoàng Long", K21) → submit → approve + GV011 → upload P03-B.pdf → Hoàn tất 49.3 % |
| DTC225200012 | topic assigned to GV011. Outline v1 = P02-B.docx, Hoàn tất 48.04 %, vượt ngưỡng, source "Ứng dụng PyTorch trong giải đáp thắc mắc tuyển sinh … An Khang (K22)". Awaiting GV011 |
| DTC225200013 | outline approved (P22-B). Progress: mốc 1 commented (Đạt), mốc 2 awaiting |
| DTC225200014 | final report P23-B checked. "Hội đồng demo K22" (today 08:30, C2-301). Scored by GV012 8.0 and GV013 8.5; GV014 still to score |
| DTC225200015 | 3/3 scores, finalized (TB 8.5), in the archive (HE_THONG, DA_INDEX) |
| GV011 / GV012 / GV013 / GV014 | GVHD / chủ tịch / thư ký / ủy viên |

- **Durations:** reset only ~2–3 s; full run ~18–20 s (build-up 12–13 s, including 6 real AI document checks).
- **Idempotent:** run 3× in a row, with the same state and counts each time.
- **Safety:** selection is scoped to the 5 SV ids in the K22 đợt plus the committee named "Hội đồng demo K22". The script aborts before deleting anything if that committee holds a foreign schedule or member, or if an archive row points elsewhere. It purges TOPIC/DOCUMENT/ARCHIVE from the AI index and removes the upload files. The upload file count matched the `tai_lieu_do_an` rows afterwards (31/31).
- **`--dem`:** a read-only row fingerprint. The change-detection test is below.

## Screenshots (`kich-ban-anh.json` → `docs/chuong-4-trien-khai/anh/`, all 1440×900, scrollWidth ≤ 1440, 0 errors)

| File | UC / role / MH |
|---|---|
| uc0-dang-nhap | UC0 guest, MH-01 (401 of /auth/refresh allowed) |
| uc0-tong-quan-sinh-vien | UC0 SV 013, MH-02 |
| uc0-thong-bao | UC0 SV 013, bell popover (NOTF-01) |
| uc0-trang-403 | UC0 SV 013 on /tai-khoan → 403 |
| uc0-tong-quan-giang-vien | UC0 GV011, MH-03 |
| uc0-tong-quan-bo-mon | UC0 Bộ môn, MH-04 |
| uc0-quan-ly-tai-khoan / uc0-dot-do-an / uc0-cau-hinh-nguong | UC0 Bộ môn (UC0.2 / UC0.3 / UC0.4, view only) |
| uc1-sv-canh-bao-trung-ten | UC1 SV 011, MH-06 AI warning 81.92 % |
| uc1-sv-gui-de-xuat | UC1 SV 011, topic Chờ duyệt with saved check (writes) |
| uc1-danh-sach-de-tai | UC1 Bộ môn, MH-05 filtered by đợt K22 |
| uc1-duyet-phan-cong | UC1 Bộ môn, MH-07 drawer, GV011 selected (writes: needs 011's topic) |
| uc2-sv-nop-de-cuong | UC2 SV 012, MH-08 Hoàn tất 48 % |
| uc2-gv-duyet-de-cuong | UC2 GV011, MH-09 panel |
| uc2-chi-tiet-trung-lap | UC2 GV011, MH-14 highlighted passages beside source |
| uc3-sv-bao-cao-tien-do / uc3-gv-nhan-xet-tien-do / uc3-bo-mon-theo-doi-tien-do | UC3 SV 013 / GV011 / Bộ môn (MH-10) |
| uc4-hoi-dong-lich | UC4 Bộ môn, MH-11 |
| uc4-sv-bao-cao-cuoi | UC4 SV 014, final report tab |
| uc4-gv-cham-diem | UC4 GV014, MH-12 (writes: saves score) |
| uc4-bo-mon-chot-diem | UC4 Bộ môn, "Chốt kết quả bảo vệ?" confirm (not confirmed) |
| uc4-sv-ket-qua-bao-ve | UC4 SV 015, result 8.50 |
| uc5-kho-tim-kiem | UC5 SV 012, MH-13 K22 + "tiêm chủng" |
| uc5-kho-chi-tiet / uc5-kho-import | UC5 Bộ môn, record drawer / CSV import modal |

I reviewed every PNG in contact sheets and several at full size. The Vietnamese text renders correctly, the right data shows for each role, and there are no spinners or error states.

## Automated rehearsal (`kich-ban-demo.json`, logged in `tap-duot-demo.md`)

16/16 OK, 71.6 s machine time. The planned narrated timeline is 00:00–13:45, about 14:30 in total.

| Step | Time (s) | Step | Time (s) |
|---|---:|---|---:|
| B01 Bộ môn overview | 4.4 | B09 SV 013 progress | 4.2 |
| B02 SV 011 AI title warning 81.92 % | 5.0 | B10 GV011 comments mốc 2 | 4.9 |
| B03 submit anyway | 2.5 | B11 GV014 scores 014 | 4.9 |
| B04 approve + assign GV011 | 5.7 | B12 Bộ môn finalizes 014 (8.33) → archive | 5.2 |
| B05 upload P03-B → Hoàn tất 49.3 %, detail | 9.2 | B13 archive search "câu lạc bộ" + import modal | 4.6 |
| B06 GV011 MH-09 on 012 | 4.5 | B14 thresholds (view) | 2.1 |
| B07 MH-14 highlighted passages | 2.2 | B15 403 + http→https | 4.9 |
| B08 request revision | 2.8 | B16 wrap-up overview | 4.3 |

The demo state was restored afterwards. **Pending human item:** the student still has to rehearse on the real system and time it (ROADMAP SC4). This is not a blocker.

## Verification run

- **Task 1 tracer `<automated>`:** OK. Two screens at (1440, 900), no Chrome left. All acceptance greps pass, and no password or JWT appears in any output.
- **Task 2:** `demo-state.sh` ×2 → scenario (27/27) → `demo-state.sh`. The manifest check passed: 27 ids, uc0..uc5, none bad, 27 PNGs.
  - `grep 'Hội đồng demo K22' / '--chi-xoa' deploy/demo-state.sh` and `grep 'trạng thái demo' deploy/verify-all.sh` both pass.
  - Demo-intact detection: after one real API change (GV011 reviewing 013's pending report), `--buoc trang-thai-demo` FAILed on `bao_cao_tien_do` and `thong_bao`. The state was restored afterwards.
  - The deferred-page checks (06/08, build-report) were not run.
- **Task 3:** the rehearsal command passed (16/16) and the log contains "Lần chạy". There are 16 ids (within 12–16). `grep kich-ban-demo.md deploy/README.md` passes. The md-based checks were deferred.
- **`bash deploy/verify-all.sh --report`:** 14/14 OK in 344 s. This includes e2e-ai with the demo documents in the index, a live nfr-16 run (23 screens, max 1440 px), and an unchanged demo state. NFR-01..NFR-19 are all Đạt.
- **`python3 tools/check-docs.py all`:** clean (apart from the known PI 1.1 item).
- **Final `bash deploy/verify-all.sh --quick`:** 4/4 OK. The stack is up and healthy, seeded, and in demo state (4 demo topics, 1 committee, 015 archived). No debug Chrome is running.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Body 8 px margin → white frame + horizontal overflow when antd opens a Modal/Drawer (NFR-16)**
- **Found during:** Task 2 (archive drawer measured scrollWidth 1448 at 1440 px).
- **Fix:** `html, body { margin: 0 }` in `frontend/index.html`, then rebuilt the apache image. **Commit:** 9f81829 (`fix(05-05)`).

**2. [Rule 1 - Bug] MH-09 card title truncated to "Duyệt ..."**
- The long topic name in `Card extra` hid the student's name. The topic now appears as a line inside the card (`OutlineReviewPage.tsx`). **Commit:** 9f81829.

**3. [Rule 1 - Bug] Demo data would break e2e-ai**
- The plan said to pick demo files "exactly like e2e-ai.sh" (the first passing pairs). Those same B files then sit in the DOCUMENT index, so e2e-ai's top-source check would fail. The demo uses the next passing pairs instead. `verify-all` full run confirmed e2e-ai stays green.

**4. [Rule 1 - Bug] `curl -F "noi_dung=…;…"` cut the progress text at ';'**
- Switched to `--form-string` in `demo-state.sh`.

**5. [Rule 3 - Blocking] Headless Chrome specifics**
- `onBlur` never fired (the title check never ran) → added `Emulation.setFocusEmulationEnabled`.
- A cancelled request blocked "network idle" → the driver now ignores requests pending > 8 s and clears on navigate.
- `<input type=date|time>` rendered in en-US → Chrome is started with `LANGUAGE/LANG=vi_VN`.
- The row locator picked the whole Card → it now uses the innermost row.
- Heading text shadowed buttons → clickable matches are preferred.

**6. [Rule 3] Concurrent `fix(deploy)` commits (ed9105e, 62acd2d, 742635c, not mine) made the deploy scripts honour HTTPS_PORT/HTTP_PORT**
- Aligned `demo-state.sh` and `chay-kich-ban.py` to `https://localhost:${HTTPS_PORT:-443}`.
- B15 now uses a `mo_http` action on `${HTTP_PORT:-80}`. **Commit:** 65aca9e.
- These 3 foreign commits are inside the measured `commits: 8`. 5 of the 8 are 05-05's own.

**7. Plan adjustments (non-destructive)**
- The screenshot set has 27 steps (the plan asked for ≥ 22). It adds `uc1-sv-gui-de-xuat` and `uc4-sv-ket-qua-bao-ve`.
- Accounts, cohorts and thresholds have no MH number in §3.4.2 (recorded as "—").
- NFR-16 is measured live inside verify-all rather than by the deferred renderer.

**Observed, not changed (seed artifact, not a product bug):** GV011's "Nhận xét tiến độ" list and dashboard count include a historical K18 source-thesis topic that has no student, shown as "—". It comes from `seed_ai_corpus` (topics with DA_PHAN_CONG and no SV in closed đợt), so GV011 shows "5/5 đề tài".

## Known Stubs

None in code. The deferred report and prose files are listed under "Scope executed".

## Threat Flags

None beyond the plan's threat model. T-05-17: 127.0.0.1 with an ephemeral port, the profile is removed, and verify checks that no Chrome remains. T-05-18: the password comes from env/.env and is never printed. T-05-19: scoped selection with abort. T-05-20: demo fingerprint before and after verify-all.

## Self-Check: PASSED

- FOUND: deploy/demo-state.sh, tools/demo/{cdp.py,chay-kich-ban.py,kich-ban-anh.json,kich-ban-demo.json}, 27 PNGs, anh-chup.json, tap-duot-demo.md
- FOUND commits: 36c165a, 9f81829, 23c4145, e57ea99, 65aca9e
