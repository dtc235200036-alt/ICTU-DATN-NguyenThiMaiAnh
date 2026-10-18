---
phase: 04-ai-similarity-service
verified: 2026-09-28T10:29:39Z
status: gaps_found
score: 4/5 must-haves verified
covered_files:
  - .planning/phases/04-ai-similarity-service/04-01-PLAN.md
  - .planning/phases/04-ai-similarity-service/04-01-SUMMARY.md
  - .planning/phases/04-ai-similarity-service/04-02-PLAN.md
  - .planning/phases/04-ai-similarity-service/04-02-SUMMARY.md
  - .planning/phases/04-ai-similarity-service/04-03-PLAN.md
  - .planning/phases/04-ai-similarity-service/04-03-SUMMARY.md
  - .planning/phases/04-ai-similarity-service/04-04-PLAN.md
  - .planning/phases/04-ai-similarity-service/04-04-SUMMARY.md
  - .planning/phases/04-ai-similarity-service/04-05-PLAN.md
  - .planning/phases/04-ai-similarity-service/04-05-SUMMARY.md
  - .planning/phases/04-ai-similarity-service/04-06-PLAN.md
  - .planning/phases/04-ai-similarity-service/04-06-SUMMARY.md
  - .planning/phases/04-ai-similarity-service/04-07-PLAN.md
  - .planning/phases/04-ai-similarity-service/04-07-SUMMARY.md
  - ai-service/.dockerignore
  - ai-service/Dockerfile
  - ai-service/README.md
  - ai-service/alembic.ini
  - ai-service/alembic/env.py
  - ai-service/alembic/script.py.mako
  - ai-service/alembic/versions/0001_thesis_ai.py
  - ai-service/alembic/versions/0002_ten_model_revision.py
  - ai-service/app/__init__.py
  - ai-service/app/api.py
  - ai-service/app/core/__init__.py
  - ai-service/app/core/body_limit.py
  - ai-service/app/core/config.py
  - ai-service/app/core/security.py
  - ai-service/app/db.py
  - ai-service/app/download_model.py
  - ai-service/app/embedding.py
  - ai-service/app/index.py
  - ai-service/app/main.py
  - ai-service/app/minhash.py
  - ai-service/app/models.py
  - ai-service/app/nlp/__init__.py
  - ai-service/app/nlp/boilerplate.py
  - ai-service/app/nlp/chunking.py
  - ai-service/app/nlp/normalize.py
  - ai-service/app/nlp/segment.py
  - ai-service/app/pipeline.py
  - ai-service/app/schemas.py
  - ai-service/calibration/__init__.py
  - ai-service/calibration/calibrate.py
  - ai-service/calibration/extract.py
  - ai-service/calibration/ket-qua-chi-tiet.json
  - ai-service/calibration/nguong-de-xuat.json
  - ai-service/docker-entrypoint.sh
  - ai-service/pyproject.toml
  - ai-service/scripts/container_smoke.sh
  - ai-service/scripts/smoke_real_model.py
  - ai-service/tests/conftest.py
  - ai-service/tests/test_document_path.py
  - ai-service/tests/test_schema_erd.py
  - ai-service/tests/test_title_path.py
  - ai-service/uv.lock
  - backend/alembic/versions/0010_nguong_hieu_chinh.py
  - backend/alembic/versions/0012_ty_le_nguon.py
  - backend/alembic/versions/0013_pham_vi_kiem_tra.py
  - backend/alembic/versions/0014_da_index_luc.py
  - backend/app/core/config.py
  - backend/app/models/cau_hinh_nguong.py
  - backend/app/models/de_cuong.py
  - backend/app/models/trung_lap.py
  - backend/app/routers/archive.py
  - backend/app/routers/defense.py
  - backend/app/routers/thresholds.py
  - backend/app/routers/topics.py
  - backend/app/schemas/dashboard.py
  - backend/app/schemas/documents.py
  - backend/app/schemas/thresholds.py
  - backend/app/schemas/topics.py
  - backend/app/seed_ai_corpus.py
  - backend/app/services/ai_client.py
  - backend/app/services/ai_index.py
  - backend/app/services/archive.py
  - backend/app/services/dashboard.py
  - backend/app/services/document_check.py
  - backend/app/services/documents.py
  - backend/app/services/thresholds.py
  - backend/app/services/title_check.py
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/test_ai_client_http.py
  - backend/tests/test_ai_document_flow.py
  - backend/tests/test_archive.py
  - backend/tests/test_defense_flow.py
  - backend/tests/test_outline_flow.py
  - backend/tests/test_thresholds.py
  - backend/uv.lock
  - deploy/.env.example
  - deploy/README.md
  - deploy/ai-nfr.sh
  - deploy/docker-compose.yml
  - deploy/e2e-ai.sh
  - deploy/e2e-uc1.sh
  - deploy/e2e-uc2-5.sh
  - deploy/init.sh
  - deploy/mysql/init-thesis-ai.sh
  - deploy/seed-ai.sh
  - deploy/smoke-test.sh
  - docs/README.md
  - docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md
  - docs/chuong-3-thiet-ke/03-kien-truc-he-thong.md
  - docs/chuong-3-thiet-ke/04-thiet-ke-giao-dien.md
  - docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.png
  - docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.puml
  - docs/chuong-3-thiet-ke/csdl/erd-thesis-ai.svg
  - docs/chuong-3-thiet-ke/csdl/erd.png
  - docs/chuong-3-thiet-ke/csdl/erd.puml
  - docs/chuong-3-thiet-ke/csdl/erd.svg
  - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.png
  - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml
  - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.svg
  - docs/chuong-4-trien-khai/thu-nghiem-ai/01-du-lieu-thu-nghiem.md
  - docs/chuong-4-trien-khai/thu-nghiem-ai/02-so-sanh-mo-hinh-embedding.md
  - docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md
  - docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md
  - docs/chuong-4-trien-khai/thu-nghiem-ai/README.md
  - frontend/src/features/dashboard/BmDashboard.tsx
  - frontend/src/features/dashboard/api.ts
  - frontend/src/features/defense/CommitteePage.tsx
  - frontend/src/features/defense/ScoringPage.tsx
  - frontend/src/features/documents/CheckDetailPage.tsx
  - frontend/src/features/documents/CheckPanel.tsx
  - frontend/src/features/documents/api.ts
  - frontend/src/features/documents/highlight.ts
  - frontend/src/features/documents/scope.ts
  - frontend/src/features/thresholds/ThresholdSettingsPage.tsx
  - frontend/src/features/thresholds/api.ts
  - frontend/src/features/thresholds/routes.tsx
  - frontend/src/features/topics/TitleCheckAlert.tsx
  - frontend/src/features/topics/api.ts
  - seed-data/README.md
  - seed-data/de-tai-kho.csv
  - seed-data/manifest.json
  - seed-data/truy-van-ten-de-tai.csv
  - tools/bakeoff/README.md
  - tools/bakeoff/bakeoff.py
  - tools/bakeoff/cap-mau.jsonl
  - tools/bakeoff/ket-qua-bkai.json
  - tools/bakeoff/ket-qua-e5.json
  - tools/bakeoff/ket-qua.json
  - tools/bakeoff/pyproject.toml
  - tools/bakeoff/uv.lock
  - tools/datagen/README.md
  - tools/datagen/datagen/__init__.py
  - tools/datagen/datagen/__main__.py
  - tools/datagen/datagen/check.py
  - tools/datagen/datagen/documents.py
  - tools/datagen/datagen/render.py
  - tools/datagen/datagen/topics.py
  - tools/datagen/datagen/vocab.py
  - tools/datagen/pyproject.toml
  - tools/datagen/uv.lock
covered_digest: "v2:sha256:c312f8384aa44af9b77e166edbbe751f42c89c954824137058a224a7ff7cd6f9"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "SC3: Trên bộ 50 file thử nghiệm, các cặp chép nguyên văn và diễn đạt lại bị cảnh báo, còn cặp cùng lĩnh vực khác đề tài và cặp không liên quan nằm dưới ngưỡng; bảng kết quả kiểm chứng (điểm từng cặp, model embedding được chọn sau khi so sánh) được lưu để đưa vào báo cáo"
    status: partial
    reason: "Under the runtime rule (max per-source share >= NGUONG_TAI_LIEU 10.4 %), same-field held-out pair P19 IS flagged: P19-B (clinic management, ERP cluster) scores 22.81 % against P15-A (hospital appointment app, a different thesis), from 14 semantic passages and 0 verbatim. The roadmap sentence says same-field pairs must stay below the threshold, so it is not met for 1 of 6 same-field pairs (5/6 below). No document threshold can fix this: P19 at 22.81 % is above the weakest paraphrase pair P09 (13.36 %), so any threshold that keeps P19 below it also stops flagging P09. Everything else in SC3 holds: 7/7 verbatim and 7/7 paraphrase pairs flagged, 5/5 unrelated pairs below the threshold, the per-pair table and the bake-off table are saved, and bkai was chosen by a rule fixed before the run. The 0.875 >= 0.85 held-out gate (G3) was set in plan 04-04. It is not the roadmap contract."
    artifacts:
      - path: "ai-service/calibration/ket-qua-chi-tiet.json"
        issue: "cap P19: bi_canh_bao true, ky_vong false, dat false (ty_le_nguon_cao_nhat 22.81 vs nguong_tai_lieu 10.4)"
      - path: "ai-service/app/pipeline.py"
        issue: "Semantic flag rule (cosine >= 67.7 inside a run of >= MIN_RUN_NGU_NGHIA=2 consecutive same-source sentences) produces 14 same-source semantic runs on same-domain template prose"
      - path: "docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md"
        issue: "Honestly documents P19 as 'Không đạt' / known false positive, so the limitation is recorded as the roadmap Notes require"
    missing:
      - "EITHER accept P19 as a documented limitation via an override (the roadmap Phase 4 Notes allow this: 'Nếu hết T8 mà hiệu chỉnh chưa đạt: ghi nhận giới hạn vào báo cáo và chuyển sang Phase 5'). See the override suggestion in the report body."
      - "OR change the detection method (not the threshold). For example, tune MIN_RUN_NGU_NGHIA or NGUONG_DOAN_TRUNG, or use a same-cluster boilerplate-sentence penalty. Then re-run calibrate tune/evaluate so every same-field pair falls below NGUONG_TAI_LIEU while P09 and the other paraphrase pairs stay flagged. Check that G1, G2 and G3 still pass."
human_verification:
  - test: "Log in as the SV (DTC225200095 or a demo SV) and submit a verbatim-copy file (e.g. seed-data/tai-lieu/P01-B.pdf) as đề cương. Watch the outline page."
    expected: "The panel shows 'Đang kiểm tra' first, then switches to 'Hoàn tất' within a few seconds without a manual reload (3 s polling). It then shows ty_le_tong, the per-source share, and a 'Vượt ngưỡng cảnh báo' tag."
    why_human: "e2e-ai checks the API states (202, then HOAN_TAT after 2 s). It cannot see the live status change or the tag rendering in the browser."
  - test: "Open MH-14 (/kiem-tra-trung-lap/{taiLieuId}) for that check as the SV and as the GVHD."
    expected: "Each duplicate passage sits next to its source passage. Shared 3-word phrases are highlighted with <mark>. The signal label (nguyên văn / ngữ nghĩa) and the 'Đồ án trùng' list with per-source % are shown. No cover page, table of contents or reference list appears as a passage. The scope line 'Đã so sánh n câu · đã loại m dòng (x %)' is shown."
    why_human: "The highlight layout and readability are visual. The API returning the same data to the GVHD is already proven by e2e."
  - test: "As GVHD, open the outline review screen (MH-09, OutlineReviewPage) for the same submission."
    expected: "The CheckPanel shows the same totals, the same top-3 'Đồ án trùng nhiều nhất' and the same over-threshold tag as the SV sees, with a 'Xem chi tiết' link to MH-14."
    why_human: "Visual check of the review screen."
  - test: "As Bộ môn, open 'Ngưỡng trùng lặp' (/cau-hinh-nguong), change 'Ngưỡng tên đề tài' and 'Ngưỡng cảnh báo tài liệu', then confirm the Popconfirm. Run one title check and one document check, then restore the defaults with 'Khôi phục giá trị đề xuất'."
    expected: "The save succeeds and the 'Cập nhật lần cuối … bởi …' line updates. The next checks use the new values (nguong_ap_dung). Values outside 0–100 are rejected with the UC0.4 - E1 message."
    why_human: "The API path is proven by e2e (PUT /api/thresholds, then the next check uses 99.99 and 3.75). The form interaction, validation messages and Popconfirm flow are UI."
  - test: "Decide on SC3/P19 (see gap): accept the same-field false positive as a documented limitation (override), or schedule a detection-method change."
    expected: "A recorded decision (override entry or gap-closure plan). 04-REVIEW-FIX.md explicitly leaves this to the user."
    why_human: "Product/academic judgement: whether one flagged same-field pair out of 6 is acceptable for the defence."
---

# Phase 4: AI Similarity Service Verification Report

**Phase Goal:** SV và GVHD nhận cảnh báo trùng lặp thật (đề tài tương tự kèm tỷ lệ khi đăng ký; đoạn trùng, đồ án trùng và tỷ lệ tương đồng khi nộp đề cương/báo cáo) với ngưỡng đã được kiểm chứng trên bộ dữ liệu có cặp trùng chủ đích
**Verified:** 2026-09-28T10:29:39Z
**Status:** gaps_found. The only gap is SC3 (P19), and it can be accepted with an override. Five human UI and decision checks are also pending.
**Re-verification:** No, this is the first verification.

**Mode note:** ROADMAP marks this phase `mode: mvp`, but the goal is not in "As a …, I want to …, so that …" form. Phases 2 and 3 have the same format and were verified. So this report uses the standard goal-backward method, and the User Flow Coverage table below is organised by the goal's outcome clauses.

## User Flow Coverage

| Step (goal clause) | Expected | Evidence in codebase / live stack | Status |
|---|---|---|---|
| SV registers or proposes a topic | Top similar topics with % | `title_check.kiem_tra_ten` → `AiClientHttp.check_title` → ai `/check-title` (FAISS, bkai). e2e: TV001–TV003 paraphrases return the correct archive thesis as top-1 at 81.92 / 69.83 / 72.89 % in about 0.05 s, and NFC gives the same result as NFD | VERIFIED |
| SV submits đề cương/báo cáo | Async status, then total %, matched theses and duplicate passages | `document_check.run` (BackgroundTasks), then `/check-document`, stored in `ket_qua_kiem_tra_trung_lap` / `chi_tiet_trung_lap`. e2e: P01-B returns 202 in 0.048 s and HOAN_TAT after 2 s: 50.3 %, 7 passages, source "Phát triển mô hình thống kê… (K21)" | VERIFIED (UI visual: human) |
| GVHD sees the same result | Same data on the review screen | `CheckPanel` is mounted in `OutlineReviewPage.tsx:326` and `FinalReportTab.tsx:79`. e2e: "GV023 thấy cùng tỷ lệ, đồ án trùng và đoạn trùng" | VERIFIED (UI visual: human) |
| Thresholds validated on intentional pairs | Verbatim and paraphrase flagged; same-field and unrelated below | calibration: tuning split 17/17, held-out 7/8. **P19 (same field) flagged at 22.81 %** | PARTIAL |

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | SC1: a paraphrased title returns top similar seeded topics with %, within the NFR time; NFD and NFC give the same results | ✓ VERIFIED | e2e-ai run by the verifier: `ai_title`: TV001–TV003 top-1 is the correct archive thesis (81.92 %, 69.83 %, 72.89 %) in 0.045–0.050 s, "NFC=NFD". TV004 (same field) returns no archive hit above the threshold. ai-nfr: NFR-08 P95 56 ms (≤ 5 s). The ai encoder applies `nfc()` and then underthesea `segment()` (`embedding.py:144-148`), and the Web API also calls `nfc()` before the request |
| 2 | SC2: "đang kiểm tra" then "hoàn tất"; total %, matched theses and passages highlighted next to the source; GVHD sees the same; template headings, TOC and references are not counted | ✓ VERIFIED (visual items routed to human) | e2e `ai_document`: 202 in 0.048 s, then HOAN_TAT after 2 s; 50.3 % ≥ 10.4 %; matched thesis label; each passage beside its source; "không đoạn khuôn mẫu"; 61 sentences compared, 112 lines excluded (42.29 %); GVHD sees the same. The frontend polls every 3 s while DANG_KIEM_TRA (`documents/api.ts:86`). `highlightOverlap` marks shared 3-grams in a `<mark>` React text node (`CheckDetailPage.tsx:46-51`). `boilerplate.py` strips MỤC LỤC / TÀI LIỆU THAM KHẢO / LỜI CAM ĐOAN / cover labels and TOC lines. The ablation table is in `03-hieu-chinh-nguong.md` |
| 3 | SC3: verbatim and paraphrase pairs flagged; same-field and unrelated pairs below the threshold; verification table and model choice saved | ✗ FAILED (partial) | `ket-qua-chi-tiet.json`: verbatim 7/7 and paraphrase 7/7 flagged; unrelated 5/5 below (P21 at 1.51 % per source); **same field 5/6 below. P19 is flagged at 22.81 % against P15-A**, from 14 semantic passages and 0 verbatim. Tables are saved: `02-so-sanh-mo-hinh-embedding.md` (bake-off, rule fixed before the run, bkai chosen) and `03-hieu-chinh-nguong.md` (per-pair scores; P19 is marked "Không đạt"). The G3 soft gate (0.875 ≥ 0.85) was set in the plan, not the roadmap. See the Gaps section |
| 4 | SC4: Bộ môn changes the title and content thresholds on the UI, and the next check uses the new values | ✓ VERIFIED (UI interaction routed to human) | e2e `ai_threshold`: PUT /api/thresholds sets NGUONG_TEN_DE_TAI to 99.99; the next check returns nguong 99.99 with no archive hit; restoring gives 81.92 % again. e2e (3b): PUT NGUONG_TAI_LIEU = 3.75, and the next document check stores nguong_ap_dung 3.75. `thresholds.py` has no cache. `title_check._get_threshold` runs per request, and `document_check.create_pending` takes a snapshot at submit. The screen `/cau-hinh-nguong` (BO_MON only) is in the deployed bundle `index-WxVN0tz5.js`. An anonymous GET /api/thresholds returns 401 |
| 5 | SC5: the AI service cannot be reached through Apache and rejects requests without the key; new records are indexed at once and appear in the next check without re-embedding the whole corpus | ✓ VERIFIED | `docker port ntma-ai-1` is empty (ports `{"8002/tcp":null}`, only `expose`). `ntma.conf` has only `ProxyPass /api/`. e2e: host cannot connect to 8002; inside the network, missing key → 401, wrong key → 401, right key → 200 (`hmac.compare_digest` on a router-level dependency); the DB user is DML-only and denied on thesis_core. e2e `ai_index`: a new archive K97 record reaches DA_INDEX with encode_calls 33 → 34 (+1) and the next title check finds it (90.12 %); a new topic is also visible at once (93.51 %). ai-nfr NFR-11: +1 |

**Score:** 4/5 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `ai-service/app/{main,api,pipeline,embedding,index,minhash}.py` | Separate FastAPI service with /ingest /check-title /check-document /reindex /health | ✓ VERIFIED | 636-line pipeline with real FAISS + MinHash. The container `ntma-ai-1` is healthy. /health: model `bkai…@84f9d9ada0d1`, index 300 titles and 2208 sentences, thieu_embedding 0 |
| `ai-service/app/nlp/{normalize,segment,boilerplate,chunking}.py` | NFC, word segmentation, boilerplate stripping, linear-time chunking | ✓ VERIFIED | Covered by ai-service pytest (8 passed), including the CR-03 timing test and the CR-04 chapter-hiding test |
| `backend/app/services/ai_client.py` (`AiClientHttp`) | Real HTTP client replacing the stub | ✓ VERIFIED / WIRED | `get_ai_client` returns the HTTP client when `AI_CLIENT=http`. The live api env has `AI_CLIENT=http` and `AI_SERVICE_URL=http://ai:8002` |
| `backend/app/services/document_check.py` | Async check, per-source decision (`vuot_nguong`), exclusion of same-topic versions, ingest after HOAN_TAT | ✓ VERIFIED | `vuot_nguong = ty_le_nguon_cao_nhat >= nguong_ap_dung` (line 99). `loai_tru` holds same-topic versions. Push-on-write happens after commit |
| `backend/app/services/thresholds.py` + `routers/thresholds.py` | UC0.4 GET/PUT for BO_MON | ✓ VERIFIED | Auto-discovered router, `require_role(BO_MON)`, row lock, editor and timestamp stored |
| `frontend/src/features/thresholds/ThresholdSettingsPage.tsx` | Threshold screen | ✓ VERIFIED | Registered via the `import.meta.glob` route registry, with a menu item for BO_MON. tsc --noEmit is OK |
| `frontend/src/features/documents/{CheckDetailPage,CheckPanel,highlight}.tsx/ts` | MH-14 highlights, MH-09 panel | ✓ VERIFIED | Used on OutlineReviewPage and FinalReportTab. VersionHistory links to MH-14 |
| `deploy/docker-compose.yml` (ai, ai-migrate, ai-db-init) | Internal-only ai service with a read-only filesystem | ✓ VERIFIED | `expose: 8002`, no `ports`, `read_only: true` (inspect: ReadonlyRootfs true), `mem_limit 2g` |
| `deploy/seed-ai.sh`, `e2e-ai.sh`, `ai-nfr.sh` | Seed, e2e and NFR scripts | ✓ VERIFIED | e2e-ai exit 0 and ai-nfr exit 0, both run by the verifier one after the other |
| `seed-data/` | 300 topics (K18–K22), 50 files, manifest with 25 pairs | ✓ VERIFIED | CSV has 300 rows, 60 per cohort. 25 docx + 25 pdf. Manifest: 7 verbatim, 7 paraphrase, 6 same field, 5 unrelated; 17 tuning / 8 held out |
| `docs/chuong-4-trien-khai/thu-nghiem-ai/01..04` | Chương 4 AI pages | ✓ VERIFIED | Data page, bake-off, calibration (per pair, P19 disclosed), NFR/security. No debt markers |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `title_check.kiem_tra_ten` | ai `/check-title` | `get_ai_client(db).check_title(nfc(..), top_k*2, nguong=threshold)` | WIRED | Proven live by e2e ai_title |
| `document_check.run` | ai `/check-document` | `check_document(ref_id, text, top_k, nguong_doan, loai_tru)` | WIRED | Proven live by e2e ai_document |
| `archive.run_ingest` / topic submit / `document_check.run` | ai `/ingest` | `ai_index.*` push-on-write | WIRED | encode_calls +1 per record, +1 for submit plus index (CR-02 vector reuse) |
| `cau_hinh_nguong` | AI requests | read on each request (D-04) | WIRED | e2e threshold round trips |
| Apache | ai service | (must not exist) | ABSENT, as required | Only `/api/` is proxied |
| `ThresholdSettingsPage` | `/api/thresholds` | `useThresholds` / `useSaveThresholds` | WIRED | Bundle contains the route. API returns 401 without a token |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| CheckDetailPage / CheckPanel | `ty_le_tong`, `ty_le_nguon_cao_nhat`, `do_an_trung`, `chi_tiet` | GET /api/documents/{id}/check → DB rows written from the ai `/check-document` response | Yes: P01-B 50.3 %, 7 passages, labelled source | ✓ FLOWING |
| TitleCheckAlert | `matches` | ai FAISS search over 300 seeded titles | Yes: 81.92 % etc. | ✓ FLOWING |
| ThresholdSettingsPage | `gia_tri`, `gia_tri_de_xuat` | `cau_hinh_nguong` rows (67.80 / 10.40 / 67.70) | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| ai-service unit/integration | `uv --directory ai-service run pytest -q` | 8 passed | ✓ PASS |
| backend suite (real MySQL, thesis_core_test) | `uv --directory backend run pytest -q` | 53 passed in 103 s | ✓ PASS |
| Cross-service e2e (SC1, SC2, SC4, SC5, CR-01, CR-02) | `bash deploy/e2e-ai.sh` | exit 0, all OK lines; thresholds restored to 67.80 / 10.40 / 67.70 with editor NULL | ✓ PASS |
| NFR-07..11 (run after e2e, without `--report`, so no doc writes) | `bash deploy/ai-nfr.sh` | NFR-08 P95 56 ms; NFR-09 P95 3.04 s, 20/20; NFR-10 max 0.086 s; long doc 42.0 s inside the 111.5 s timeout, interleaved title checks 123–601 ms; NFR-11 +1; memory peak 669 MiB | ✓ PASS |
| Frontend types | `npx tsc -p tsconfig.app.json --noEmit` | OK | ✓ PASS |
| AI not published | `docker port ntma-ai-1`; `docker inspect` | empty; `{"8002/tcp":null}`, ReadonlyRootfs true | ✓ PASS |
| Working tree after the checks | `git status --short` | only the pre-existing `M .planning/config.json` | ✓ clean |

### Probe Execution

Step 7c: no `scripts/*/tests/probe-*.sh` probes are declared or present. The runnable project checks (e2e-ai, ai-nfr, pytest) were run directly in the table above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| AISV-01 | 04-01, 04-05 | Separate FastAPI AI service, reachable only by the Web API with the internal key; ingest/check-title/check-document | ✓ SATISFIED | SC5 evidence |
| AISV-02 | 04-01 | NFC and word segmentation before embedding; corpus embeddings computed at ingest | ✓ SATISFIED | `Encoder.preprocess`; `rebuild` never encodes; encode_calls +1 per ingest |
| AISV-03 | 04-05 | Semantic title comparison, top-k with %, within NFR | ✓ SATISFIED | SC1 evidence; NFR-08 56 ms |
| AISV-04 | 04-06 | DOCX/PDF extraction, boilerplate removal, duplicate passages | ✓ SATISFIED | e2e ai_document; boilerplate ablation |
| AISV-05 | 04-06, 04-07 | Total %, list of matched theses, each passage highlighted beside its source | ✓ SATISFIED (visual: human) | API evidence plus `highlight.ts` / CheckDetailPage |
| AISV-06 | 04-06 | Async check; UI shows checking / done | ✓ SATISFIED (visual: human) | 202, then HOAN_TAT; 3 s polling |
| AISV-07 | 04-07 | Bộ môn configures the title and content thresholds | ✓ SATISFIED | SC4 evidence |
| DATA-02 | 04-02, 04-05 | 300 topics across cohorts, ingested into AI | ✓ SATISFIED | 300 rows, K18–K22; e2e "300 đề tài kho DA_INDEX"; index_size_tieu_de 300 |
| DATA-03 | 04-02, 04-04 | 50 test files with intentional pair types and a verification table | ✓ SATISFIED | 50 files, 25-pair manifest across 4 types, per-pair table in `03-hieu-chinh-nguong.md`. The table honestly shows P19 as failing, and that outcome is tracked under SC3 |

No orphaned requirements: every Phase 4 ID in REQUIREMENTS.md is claimed by a plan.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| (all phase files) | n/a | TBD / FIXME / XXX | none found | n/a |
| `frontend/src/features/thresholds/ThresholdSettingsPage.tsx` | 14 | Hard-coded `'88.7%'` duplicates the AI's `NGUONG_NGUYEN_VAN_MAC_DINH` (IN-06, skipped in the review fix) | ℹ️ Info | Display text will drift after a recalibration. The README recalibration steps list this spot |
| `backend/app/services/thresholds.py` | DEFINITIONS | Calibrated defaults are duplicated between Alembic 0010 and the service | ℹ️ Info | Documented: update both when recalibrating |
| `ai-service/app/main.py` | /health | Detail fields are unauthenticated (IN-04, partly fixed) | ℹ️ Info | The port is internal-only. Accepted in REVIEW-FIX |
| NFR-09 (long) | n/a | A ~100-page report takes about 42 s, above the 30 s NFR-09 target measured on short documents | ⚠️ Warning | Documented in chương 4 as its own row. It stays inside the scaled timeout and does not block title checks |
| CR-01 decision logic | n/a | REVIEW-FIX marks this "fixed: requires human verification" | ⚠️ Warning | Behaviour is proven by e2e (3b: 6.0 % total but 1.51 % per source gives "Dưới ngưỡng"). Human sign-off on the rule is covered by the SC3 decision item |

### Human Verification Required

1. **Status transition on submit (SV).** Submit P01-B.pdf as đề cương. The panel should go from "Đang kiểm tra" to "Hoàn tất" without a reload and show the total %, the per-source % and the over-threshold tag. *Why human:* this is a live browser rendering; the API states are already proven.
2. **MH-14 highlight layout (SV and GVHD).** Each passage should sit beside its source with `<mark>` highlights, the signal label, the per-source list and the scope line, and no template passages. *Why human:* this is visual.
3. **MH-09 GVHD review panel.** It should show the same totals, top-3 sources, tag and "Xem chi tiết" link. *Why human:* this is visual.
4. **UC0.4 threshold screen.** Edit, confirm, check that the next checks use the new values, confirm the 0–100 validation, then restore the defaults. *Why human:* this is form interaction; the API path is already proven.
5. **SC3/P19 decision.** Accept it as a documented limitation (override below) or plan a detection-method change.

### Gaps Summary

There is one gap, and it has a single root cause. On same-application-domain prose, the semantic passage signal produces runs of 2 or more consecutive sentences that match one other thesis in the same domain. This is enough to push P19-B (clinic management) to 22.81 % against P15-A (hospital appointment app), about twice NGUONG_TAI_LIEU (10.4 %). The threshold cannot fix it, because the weakest paraphrase pair scores 13.36 %. So SC3's sentence "cặp cùng lĩnh vực khác đề tài … nằm dưới ngưỡng" is literally false for 1 of 6 same-field pairs. Everything else about calibration holds: G1 and G2 pass, the tuning split is 17/17, the held-out split is 7/8, and the tables are saved for chương 4.

The rest of the phase goal is achieved and was proven on the live stack by the verifier. Real title warnings, real passage-level document checks visible to SV and GVHD, configurable thresholds, an internal-only keyed AI service and incremental indexing all work.

**This looks intentional.** The roadmap's Phase 4 Notes plan for this case: "Nếu hết T8 mà hiệu chỉnh chưa đạt: ghi nhận giới hạn vào báo cáo và chuyển sang Phase 5". `03-hieu-chinh-nguong.md` already records P19 as a known false positive, and Phase 5 plan 05-06 covers "4.9 hạn chế & hướng phát triển". To accept the deviation, add this to the VERIFICATION.md frontmatter. Status then becomes `human_needed` with the four UI items above:

```yaml
overrides:
  - must_have: "SC3: Trên bộ 50 file thử nghiệm, các cặp chép nguyên văn và diễn đạt lại bị cảnh báo, còn cặp cùng lĩnh vực khác đề tài và cặp không liên quan nằm dưới ngưỡng"
    reason: "P19 (same-field, held-out) is a documented semantic false positive (22.81 % vs P15-A). It cannot be separated by any threshold without losing paraphrase P09. The roadmap Notes allow recording calibration limitations and moving on. Held-out accuracy 7/8 = 0.875 >= 0.85; the limitation is disclosed in chương 4 (03-hieu-chinh-nguong.md) and goes into 4.9."
    accepted_by: "{name}"
    accepted_at: "{ISO timestamp}"
```

---

_Verified: 2026-09-28T10:29:39Z_
_Verifier: Developer (verifier)_
