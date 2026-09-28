---
phase: 04-ai-similarity-service
plan: 04
subsystem: ai-service-calibration
status: complete
tags: [calibration, youden, roc, minhash, bkai, boilerplate, DATA-03, AISV-03, AISV-04, D-04, D-06]
requires:
  - "04-01: app.pipeline (ingest_many, check_title, score_document, check_document, rebuild), CorpusIndex, alembic 0001"
  - "04-02: seed-data/ (de-tai-kho.csv, truy-van-ten-de-tai.csv, manifest.json, tai-lieu/P01..P25-{A,B})"
  - "04-03: tools/bakeoff/ket-qua.json (chon=bkai)"
provides:
  - "ai-service/calibration/nguong-de-xuat.json — keys read by 04-05: nguong_ten_de_tai (67.8), nguong_tai_lieu (10.4), nguong_doan (67.7); also nguong_nguyen_van (88.7), minhash_shingle (4), profile, phuong_phap, auc, so_mau, tap=HIEU_CHINH, ngay"
  - "ai-service/calibration/ket-qua-chi-tiet.json — gates, cap[25], truy_van[80], ablation[11], latency, cau, title_accuracy"
  - "calibrate.py tune / evaluate [--report] [--apply]"
  - "docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md (DATA-03 verification table)"
  - "AI-service Settings defaults = calibrated values"
affects: [04-05, 04-06, 04-07]
tech-stack:
  added: []
  patterns: ["thresholds fitted on the tuning split only, read-only on held-out", "Youden J with J-plateau midpoint; midpoint rule on perfect separation", "report tables generated from result JSON", "extraction parity copy of Web API extract_text", "semantic flags need >= 2 consecutive same-source sentences"]
key-files:
  created:
    - ai-service/calibration/__init__.py
    - ai-service/calibration/extract.py
    - ai-service/calibration/calibrate.py
    - ai-service/calibration/nguong-de-xuat.json
    - ai-service/calibration/ket-qua-chi-tiet.json
    - docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md
  modified:
    - ai-service/app/nlp/boilerplate.py
    - ai-service/app/pipeline.py
    - ai-service/app/core/config.py
    - ai-service/README.md
decisions:
  - "Calibrated thresholds (HIEU_CHINH, bkai): title 67.8 (Youden), doan 67.7 (Youden), nguyen van 88.7 (Youden plateau midpoint), tai lieu 10.4 (midpoint, perfect separation), MinHash shingle 4 (AUC tie across 3/4/5 -> 4)"
  - "Youden ties: all thresholds in (thr[i+1], thr[i]] give the same tuning classification; take the midpoint of that interval (avoids a 100.0 verbatim threshold that only exact copies pass)"
  - "check_document: a NGU_NGHIA flag survives only inside a run of >= 2 consecutive flagged sentences with the same source (MIN_RUN_NGU_NGHIA=2); NGUYEN_VAN flags always survive"
  - "Pair warning rule = do_an_trung[A] >= nguong_tai_lieu; ty_le_tong is display-only (P19 same-field has 23.96% total but 0% to its source)"
metrics:
  duration: "~50 min"
  completed: 2026-09-28
actuals:
  tokens: 32000   # chars/4 over calibration/*, the chương 4 page and the diffs in boilerplate/pipeline/config/README
  tasks: 2
  commits: 2      # 04-04 commits in a034b0e..108640b (range also holds concurrent 03-05 commits 0974c6e, cdb7f9d)
plan_head_before: a034b0e12cd364728fc3510afd6ed56748a27d67
plan_head_after: 108640b
---

# Phase 4 Plan 04: Threshold calibration over the real pipeline Summary

**Thresholds were fitted on the tuning split only, using the real bkai pipeline over text extracted exactly as the Web API extracts it: title 67.8 %, semantic 67.7 %, verbatim 88.7 %, document 10.4 %, shingle k = 4. With these values locked, all 8 held-out pairs and all 17 tuning pairs are classified correctly, and all three gates pass.**

## Thresholds (nguong-de-xuat.json, tap = HIEU_CHINH)

| Threshold | Value (%) | Method | AUC (tuning) | Positives / negatives |
|---|---:|---|---:|---|
| nguong_ten_de_tai | 67.8 | youden | 0.9758 | 28 / 28 queries |
| nguong_doan (semantic, sentence) | 67.7 | youden | 0.7983 | 222 paraphrased / 1064 self-written sentences |
| nguong_nguyen_van (MinHash, sentence) | 88.7 | youden (plateau midpoint, interval (77.34; 100]) | 0.9992 | 183 / 1286 sentences |
| nguong_tai_lieu (share to source A) | 10.4 | trung_diem (min positive 20.79, max negative 0.00) | 1.0000 | 10 / 7 pairs |
| minhash_shingle | 4 | AUC 0.9992 for k = 3, 4 and 5 (tie, so 4) | — | — |

**Keys plan 04-05's migration reads:** `nguong_ten_de_tai`, `nguong_tai_lieu`, `nguong_doan`. `nguong_nguyen_van` is also available.

## Gates and accuracy (ket-qua-chi-tiet.json)

- **G1 (every verbatim-copy pair flagged): PASS.**
- **G2 (unrelated pairs: share to source and total rate both below 10.4 %): PASS.** The largest value was P21, with a total rate of 6.00 %.
- **G3 (held-out accuracy ≥ 0.85): PASS.** 8/8 = 1.000. Tuning accuracy was 17/17.
- **By type:** 100 % for every type in both splits.

**Held-out pairs (share to source / total rate):**

| Pair | Type | Share to source | Total rate | Flagged? |
|---|---|---:|---:|---|
| P03 | verbatim | 49.32 | 51.03 | yes |
| P06 | verbatim | 46.93 | 49.74 | yes |
| P09 | paraphrased | 13.36 | 17.38 | yes |
| P10 | paraphrased | 20.88 | 20.88 | yes |
| P18 | same field | 0 | 2.86 | no |
| P19 | same field | 0 | 23.96 | no |
| P21 | unrelated | 0 | 6.00 | no |
| P22 | unrelated | 0 | 0 | no |

- **Sentence level (tuning / held-out):**
  - Verbatim sentences flagged: 1.000 / 1.000.
  - Paraphrased sentences flagged: 0.563 / 0.400.
  - Self-written sentences flagged: 0.041 / 0.092.

  The report's Giới hạn section records the weak sentence-level semantic signal.
- **Titles:**
  - Overall accuracy: 52/56 (0.929) tuning, 22/24 (0.917) held-out.
  - Top-1 object correct on paraphrased queries: 26/28 tuning, 12/12 held-out.
  - Misclassified queries:
    - TV015 (same field, KC, 73.03)
    - TV028 (same field, HC, 72.33)
    - TV038 (paraphrased, KC, 66.90)
    - TV051 (paraphrased, HC, 61.62)
    - TV061 (paraphrased, HC, 66.73)
    - TV062 (paraphrased, HC, 65.35)
- **Title queries evaluated correct, for reuse by the 04-05 e2e:**
  - Paraphrased, flagged, and top-1 correct: TV001, TV002, TV003, TV007, TV009, TV010, TV012, TV019, TV020, TV023, TV024, TV025, TV033, TV035, TV036, TV037, TV039, TV040, TV044, TV046, TV047, TV049, TV050, TV055, TV059, TV060, TV063, TV067, TV070, TV071, TV073, TV076, TV077, TV078, TV079.
  - Same field, correctly not flagged: TV004, TV005, TV006, TV008, TV011, TV013, TV014, TV016, TV017, TV021, TV022, TV026, TV027, TV029, TV030, TV031, TV032, TV034, TV041, TV042, TV043, TV045, TV048, TV052, TV053, TV054, TV056, TV057, TV058, TV064, TV065, TV066, TV068, TV069, TV072, TV074, TV075, TV080.
  - 04-05 should prefer, for example, TV001 (flag) and TV004 (no flag).
- **Ablation (AISV-04 / SC2):** turning off boilerplate stripping in both the corpus and the submission adds **+15.14 percentage points** to the total rate on average across the same-field and unrelated pairs (range +2.52 to +23.17). No pair's share to its source crosses the threshold. The report explains why the "submission only" column can come out lower.
- **Latency (in-process, shared dev host, 16 CPU, 4 torch threads; corpus of 300 titles and 2208 sentences):**
  - check_title: P50 41.0 ms, P95 49.4 ms.
  - score_document + check_document for one B file: P50 1079 ms, P95 2983 ms.
  - Plans 04-06 and Phase 5 measure the NFR-08/09 numbers.

## Commits

| Task | Commit | Message |
|---|---|---|
| 1 | edd0225 | feat(04-04): calibration harness over the real pipeline + thresholds fitted on HIEU_CHINH |
| 2 | 108640b | feat(04-04): held-out verification, ablation, latency + calibrated AI-service defaults |

The concurrent 03-05 executor's commits 0974c6e and cdb7f9d are interleaved on main. They do not touch 04-04 files.

## Deviations from Plan

### Mechanical fixes (tuning-split evidence only; KIEM_CHUNG never inspected before thresholds were locked)

**1. [Rule 1 - Bug] Cover lines leaked into the first content sentence** (`app/nlp/boilerplate.py`)
- **Evidence:** a harness diagnostic mapped each B sentence to its manifest paragraph. Every one of the 25 B documents had one sentence that matched no paragraph: "Đề tài: <title> Ngành: Công nghệ thông tin <first sentence>". The "Đề tài:" and "Ngành:" cover labels are not in the stripping list and do not end in punctuation, so they were glued onto the first real sentence.
- **Fix:** strip `Đề tài:` / `Tên đề tài:` lines and up to 2 PDF-wrapped continuation lines (≤ 20 syllables, no final punctuation, not a label). Strip `Ngành:` / `Chuyên ngành:` only when the colon is present.

**2. [Rule 1 - Bug] The repeated-line (header/footer) rule deleted real text** (`app/nlp/boilerplate.py`)
- **Evidence:** P12 (HIEU_CHINH, PDF B) lost the line "Quang." four times. It was a wrapped paragraph tail that repeated ≥ 3 times, so it was removed and sentences like "… bến xe khách Tuyên Sản phẩm …" were fused.
- **Fix:** the repeated-line rule now skips lines that end in sentence punctuation.
- **Result:** after both fixes, sentence labels match the manifest exactly (1680 self-written, 293 verbatim, 277 paraphrased; 0 unmatched). The 04-01 tests pass.

**3. [Rule 1 - Bug, outside files_modified] Isolated semantic matches inflated the total rate of unrelated documents** (`app/pipeline.py::check_document`)
- **Evidence (tuning split):**
  - The sentence-level Youden semantic threshold was 67.7. The self-written negatives' 90th percentile is 80.1, so isolated template-shaped sentences matched a single sentence of some other thesis in the same field.
  - This put the total rate of the tuning unrelated pairs P23/P24/P25 at 32–35 %, well above the fitted document threshold (16.9 at that point), so hard gate G2 would fail on its ty_le_tong clause.
  - Paraphrased copies, by contrast, arrive as consecutive runs from the same source.
- **Fix:**
  - A `NGU_NGHIA` flag is kept only if the sentence belongs to a run of ≥ `MIN_RUN_NGU_NGHIA` = 2 consecutive flagged sentences with the same source ref (any signal). This is the seed-and-extend passage rule; D-03 allows "sentence-window chunks".
  - `NGUYEN_VAN` flags always stand.
  - The value 2 was fixed by design, not tuned. The tuning-split simulation at 67.7 showed that runs of ≥ 2 already separate the classes.
  - Added as a keyword argument with a default, so the API and schema are unchanged. The 04-01 tests still pass, including `nguong_doan=0 → 100 %`.
- **Why this is flagged for the orchestrator:** `app/pipeline.py` is not in the plan's files_modified, and the change refines D-03's per-sentence flag rule. `README.md` documents it.

**4. [Rule 1 - Method] Youden tie-breaking**
- **Issue:** with plain roc_curve thresholds, the verbatim threshold came out at exactly 100.0. Every copied sentence has Jaccard 1.0, so any value in (77.34, 100] gives the same J.
- **Fix:** `fit_threshold` takes the midpoint of the J-optimal interval (thr[i+1], thr[i]] using `drop_intermediate=False`, which gives 88.7. This is the same margin principle as the plan's midpoint rule. The interval is recorded as `khoang_chon` in the JSON and the report.

### Other

- **Ablation columns:** there are two instead of one: submission-only `strip=False` (the plan's literal ablation) and "no stripping anywhere". For the second, the corpus is rebuilt through `ingest_many` with `pipeline.strip_boilerplate` swapped for the duration of that build only.
- **CachingEncoder:** memoizes B-sentence vectors across the shingle sweep and the ablation, which saves re-encoding. It is never used for latency. The corpus is still embedded once; for the shingle sweep, `pipeline.rebuild` rebuilds MinHash only.
- **Ledger `commits`:** measured by 04-04 subject within `a034b0e..108640b`, because the range also contains two 03-05 commits.
- **Tracking files:** STATE.md, ROADMAP.md and REQUIREMENTS.md were not touched, per the orchestrator's instruction.

## Known Stubs

None.

## Threat Flags

None. There is no new network or auth surface. T-04-13 is mitigated: `tune` filters to HIEU_CHINH, and `evaluate` only reads nguong-de-xuat.json. T-04-14 is mitigated: every table in the chương 4 page is generated from the JSON.

## Self-Check: PASSED

- FOUND: ai-service/calibration/{__init__,extract,calibrate}.py, nguong-de-xuat.json, ket-qua-chi-tiet.json, docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md
- FOUND commits: edd0225, 108640b
- Task 1 and Task 2 automated verify chains exit 0. All acceptance greps and JSON checks pass. `check-docs.py pi-tags/privacy/links` passes on the new page. `uv run pytest -q` in ai-service: 5 passed.
