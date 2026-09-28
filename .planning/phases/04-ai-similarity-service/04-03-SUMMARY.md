---
phase: 04-ai-similarity-service
plan: 03
subsystem: ai-model-selection
status: complete
tags: [bake-off, embedding, bkai, multilingual-e5, underthesea, sentence-transformers, D-01]
requires: []
provides:
  - "tools/bakeoff/ket-qua.json — locked model: chon=bkai, ten_model=bkai-foundation-models/vietnamese-bi-encoder, phan_doan=true, tien_to=''"
  - "tools/bakeoff/cap-mau.jsonl — 80 authored labeled Vietnamese pairs (TIEU_DE/CAU/DOAN)"
  - "docs/chuong-4-trien-khai/thu-nghiem-ai/02-so-sanh-mo-hinh-embedding.md — chương 4 comparison + decision"
affects: [04-01, 04-04, 04-05]
tech-stack:
  added: [sentence-transformers 6.1.0, torch 2.14.0+cpu, transformers 5.17.0, underthesea 9.5.0, scikit-learn 1.9.1, numpy 2.5.3]
  patterns: ["one model per subprocess, parent never loads a model", "MemAvailable >= 3 GiB gate before model load", "pre-registered decision rule applied by code (--decide)", "report tables generated from result JSON (--bang)"]
key-files:
  created:
    - tools/bakeoff/pyproject.toml
    - tools/bakeoff/uv.lock
    - tools/bakeoff/README.md
    - tools/bakeoff/cap-mau.jsonl
    - tools/bakeoff/bakeoff.py
    - tools/bakeoff/ket-qua-bkai.json
    - tools/bakeoff/ket-qua-e5.json
    - tools/bakeoff/ket-qua.json
    - docs/chuong-4-trien-khai/thu-nghiem-ai/02-so-sanh-mo-hinh-embedding.md
  modified: []
decisions:
  - "D-01 locked: embedding model = bkai-foundation-models/vietnamese-bi-encoder (profile bkai: NFC + underthesea word_tokenize(format='text'), no prefix) — rule branch MAC_DINH_BKAI: e5 AUC delta CAU +0.0000, DOAN +0.0521, not >= 0.05 on BOTH"
  - "No tokenizer pin needed: transformers 5.17.0 (via sentence-transformers 6.1.0) loads bkai's slow PhobertTokenizer"
metrics:
  duration: "~40 min"
  completed: 2026-09-28
actuals:
  tokens: 34650   # chars/4 over all changed files (authored ~17400 + uv.lock/raw result JSON ~17250)
  tasks: 2
  commits: 2
plan_head_before: f4f2b8a57e9f6b518dcd740aa4d4caa9795f5714
plan_head_after: 5b200dd24e71d6cf4723495ab29c4f5149c793be
---

# Phase 4 Plan 03: Embedding model bake-off (D-01) Summary

**bkai-foundation-models/vietnamese-bi-encoder is locked as the embedding model. A pre-registered rule applied by `bakeoff.py --decide` chose it: e5 beat bkai by only +0.0521 AUC on paragraphs and +0.0000 on sentences, and the rule required +0.05 on both. Both models passed the latency and memory gates by a wide margin.**

## What was built

- `tools/bakeoff/` is a uv project, CPU-only. torch resolves as `2.14.0+cpu` from `https://download.pytorch.org/whl/cpu` through an explicit `pytorch-cpu` index. The lock has 0 `nvidia`/`triton` entries.
- `cap-mau.jsonl` holds 80 authored synthetic pairs across 8 fields:
  - TIEU_DE: 12 paraphrased, 12 same-field, 6 unrelated
  - CAU: 12 / 12 / 6
  - DOAN: 8 / 8 / 4 (paragraphs of 3–4 sentences)

  All text is NFC. Same-field negatives deliberately reuse the paraphrase anchor and the domain template.
- `bakeoff.py` subcommands:
  - `--validate-pairs`: checks counts, unique ids, NFC and label/group consistency.
  - `--profile bkai|e5`: runs one model in the current process. It waits for MemAvailable ≥ 3 GiB, uses torch threads 4 and batch 32, and makes one encode call per kind. It records AUC, AUC restricted to paraphrased vs same-field pairs, mean positive/negative, gap, margin, best-threshold accuracy and the Youden threshold. Cost: load time, median of 20 single-title encodes, one encode of 300 distinct sentences, peak RSS from getrusage. It also saves the per-pair cosines, versions and CPU count, and writes `loi` with exit 0 if the model fails to load.
  - `--all`: runs the profiles one after another via subprocess.
  - `--decide`: applies the pre-registered rule.
  - `--bang`: prints the chương 4 tables straight from the JSON.

## Results (from ket-qua-bkai.json / ket-qua-e5.json, cached-weight runs)

| Kind | Metric | bkai | e5 |
|---|---|---:|---:|
| TIEU_DE | AUC | 0.8472 | 0.8750 |
| TIEU_DE | gap | 0.2407 | 0.0617 |
| TIEU_DE | margin | -0.3290 | -0.0480 |
| TIEU_DE | best acc | 0.8000 | 0.8667 |
| CAU | AUC | 1.0000 | 1.0000 |
| CAU | gap | 0.4728 | 0.0935 |
| CAU | margin | 0.0209 | 0.0087 |
| CAU | best acc | 1.0000 | 1.0000 |
| DOAN | AUC | 0.9479 | 1.0000 |
| DOAN | gap | 0.3604 | 0.0854 |
| DOAN | margin | -0.0727 | 0.0091 |
| DOAN | best acc | 0.9000 | 1.0000 |

| Cost (16 logical CPUs, 4 torch threads) | bkai | e5 | Gate |
|---|---:|---:|---|
| load_s (from cache) | 8.86 | 10.55 | — |
| title_ms (median of 20) | 18.2 | 20.9 | — |
| encode_300_s | 4.84 | 6.30 | ≤ 20 s |
| peak_rss_mb | 1047.7 | 1572.9 | ≤ 2560 MB |

Observations:
- e5's cosines are compressed: unrelated pairs score 0.80–0.83 and duplicates 0.92–0.95. bkai spreads from 0.02 to 0.65, so its thresholds are less fragile.
- Both models find template-shaped titles hard. The pair "Xây dựng hệ thống quản lý thư viện … cho trường đại học" vs "… ký túc xá …" (T13) is the highest-scoring negative for both. Title margins are negative for both models, so title warnings should be shown as suggestions, not verdicts. This is a hint for the 04-04 calibration.
- A later reproducibility rerun of e5 gave the same metrics and decision. Timings drifted on the shared host (encode_300_s 7.08 s).

## Decision

- **Rule, pre-registered and coded in `apply_rule`:** choose e5 only if it beats bkai by at least 0.05 AUC on BOTH CAU and DOAN, with encode_300_s ≤ 20 and peak RSS ≤ 2560 MB. Choose e5 if bkai fails to load or fails the 20 s gate while e5 passes both gates. If both fail latency, choose bkai and record the ONNX risk. Otherwise choose bkai.
- **Branch that fired:** `MAC_DINH_BKAI`. The AUC delta was CAU +0.0000 and DOAN +0.0521, so e5 missed the threshold on CAU. All seven branches were sanity-checked with synthetic inputs (scratch, not committed).
- **Profile string plans 04-04 and 04-05 must use:** `AI_MODEL_PROFILE=bkai`. Model `bkai-foundation-models/vietnamese-bi-encoder`, input = NFC then `underthesea.word_tokenize(text, format="text")`, no prefix, `normalize_embeddings=True`.

## Package legitimacy / resolved versions (T-04-SC)

Research audit verdict was Approved; there is no human checkpoint, per the orchestrator. `importlib.metadata` URLs from the synced venv:

| Package | Version | Home-page / Project-URL |
|---|---|---|
| sentence-transformers | 6.1.0 | https://www.SBERT.net; https://github.com/huggingface/sentence-transformers/ |
| torch | 2.14.0+cpu | https://pytorch.org; https://github.com/pytorch/pytorch |
| transformers | 5.17.0 | https://github.com/huggingface/transformers |
| tokenizers | 0.23.2 | https://github.com/huggingface/tokenizers |
| underthesea | 9.5.0 | https://undertheseanlp.com/; https://github.com/undertheseanlp/underthesea |
| underthesea-core | 3.3.2 | https://github.com/undertheseanlp/underthesea/tree/main/extensions/underthesea_core |
| scikit-learn | 1.9.1 | https://scikit-learn.org; https://github.com/scikit-learn/scikit-learn |
| numpy | 2.5.3 | https://numpy.org; https://github.com/numpy/numpy |

- **Tokenizer probe:** `AutoTokenizer.from_pretrained('bkai-foundation-models/vietnamese-bi-encoder')` returned `PhobertTokenizer` and tokenized segmented text correctly under transformers 5.17.0, so no `transformers<5` pin was applied.
- **Model repositories (T-04-11):** only the two named repos were loaded, with no `trust_remote_code`. The HF cache snapshots contain `model.safetensors` only (no `.bin`). bkai is at revision `84f9d9ada0d1a3c37557398b9ae9fcedcdf40be0` and e5 at `d128750597153bb5987e10b1c3493a34e5a4502a`.

## Commits

| Task | Commit | Message |
|---|---|---|
| 1 | 9051315 | feat(04-03): labeled Vietnamese pair set + bake-off harness, bkai measured |
| 2 | 5b200dd | feat(04-03): lock embedding model by pre-registered rule — bkai chosen |

## Deviations from Plan

### Environment / process

**1. [Rule 3 - Blocking] Harness worktree was created from the wrong repository**
- **Found during:** startup.
- **Issue:** The assigned worktree `/home/hahoang/.claude/worktrees/agent-abc453ab65dfbb081` is a worktree of the home-directory repo (`~/.git`, commit b437ad5 "first commit"), not of NTMA. The isolation hooks refused `git -C` on the NTMA repo, Write-tool writes into a nested git root, and heredoc writes.
- **Fix:** Cloned NTMA read-only into `<worktree>/ntma` and created branch `worktree-agent-04-03` from f4f2b8a (identical to NTMA main HEAD at start). Files were authored with the Write tool in a staging mirror at the worktree root (`<worktree>/tools/bakeoff`, `<worktree>/docs/...`), where uv and the models ran. They were then copied with plain `cp` into the clone and committed there. The shared NTMA checkout was never written to. Nothing was committed to the home repo.
- **Integration:** the orchestrator must fetch branch `worktree-agent-04-03` from `/home/hahoang/.claude/worktrees/agent-abc453ab65dfbb081/ntma`.

**2. [Rule 1 - Measurement] Load time re-measured from warm cache**
- **Issue:** The first run of each model included the Hugging Face download: bkai load_s 9.85 s, e5 load_s 86.72 s.
- **Fix:** Each profile was rerun once, sequentially, after the download. The committed JSON holds the cached-weight runs (bkai 8.86 s, e5 10.55 s). Metrics were identical across runs.

**3. [Rule 2 - Evidence integrity] Added `--bang` table renderer and `auc_kho` metric**
- `--bang` enforces the plan's "numbers copied from the JSON files, never typed by hand". The doc tables were checked to be a verbatim substring of `--bang` output.
- `auc_kho` (paraphrased vs same-field only) isolates the hard case the plan says decides the model. It is informational and not used by the rule.

**4. Plan verify re-runs `--profile e5`**
- Running that verify in the clone would overwrite the committed e5 JSON with fresh, drifting timings, putting the doc out of sync. So the full Task 2 verify chain (`--profile e5 && --decide && checks`) was run in the staging copy; it passed with the same decision.
- In the clone I ran: `uv sync --frozen`, `--validate-pairs`, both JSON checks, the doc grep, all acceptance greps, and `check-docs.py pi-tags/privacy/links` on `docs/chuong-4-trien-khai`. All exited 0.

## Known Stubs

None.

## Threat Flags

None. The only new surface is local model download from the two named HF repos, which is already in the plan's threat model.

## Self-Check: PASSED

All 10 files are present in the clone. Commits 9051315 and 5b200dd are present on `worktree-agent-04-03`. The plan commits contain no deletions, and `git diff --name-only f4f2b8a HEAD` lists only `tools/bakeoff/**` and the chương 4 page.
