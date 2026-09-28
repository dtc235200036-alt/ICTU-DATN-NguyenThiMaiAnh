---
phase: 05-system-verification-defense-package
plan: 04
status: complete
scope_note: "Deployment/verification part only — report prose (4.3, 4.5, 4.8 pages) and tools/bao-cao/sinh-trang-kiem-thu.py deferred by user ('Bộ báo cáo, slide không gen bây giờ')"
subsystem: deployment-verification
tags: [DEPL-02, DATA-01, DATA-02, DATA-03, NFR-01..19, D-01, D-02, D-03, install, verify-all, clean-clone]
requires:
  - "03-07: smoke-test.sh, e2e-uc1.sh, e2e-uc2-5.sh, full Phase 3 product"
  - "04-06/04-07: seed-ai.sh, e2e-ai.sh, ai-nfr.sh, app.download_model, ai-models volume"
provides:
  - "deploy/install.sh — one-command install/upgrade from a clean clone (secrets, certs, model pre-fetch, compose up --wait, migration/AI/DATA-01 checks, seed-ai)"
  - "deploy/verify-all.sh — chained full-system verification (--quick / full / --report) with timings and redaction"
  - "deploy/nfr-he-thong.sh — system NFR checks through Apache HTTPS (NFR-01..05, 08, 12..15, 17..19)"
  - "deploy/ai-nfr.sh --json; report page retitled 4.7.4"
  - "ai service runs with HF_HUB_OFFLINE=1 / TRANSFORMERS_OFFLINE=1 (D-02)"
  - "docs/chuong-4-trien-khai/ket-qua-kiem-thu/{cai-dat-sach.log, tong-hop.json, nhat-ky-verify-all.log} — machine-readable inputs for the deferred 4.3/4.5/4.8 pages"
affects: [05-05, 05-06, 05-07, 05-08]
tech-stack:
  added: []
  patterns:
    - "Install-time model pre-fetch via `compose run --no-deps --entrypoint python -e HF_HUB_OFFLINE=0 ai -m app.download_model`; runtime offline"
    - "Destructive flag gated by --yes or typed XOA, refused without a TTY"
    - "Everything written to disk passes one redaction filter (.env values >= 8 chars, JWT-shaped strings)"
    - "NFR table assembled from direct measurements + the status of the suite that proves each NFR"
key-files:
  created:
    - deploy/install.sh
    - deploy/verify-all.sh
    - deploy/nfr-he-thong.sh
    - docs/chuong-4-trien-khai/ket-qua-kiem-thu/cai-dat-sach.log
    - docs/chuong-4-trien-khai/ket-qua-kiem-thu/tong-hop.json
    - docs/chuong-4-trien-khai/ket-qua-kiem-thu/nhat-ky-verify-all.log
  modified:
    - deploy/docker-compose.yml
    - deploy/ai-nfr.sh
    - deploy/README.md
    - docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md
decisions:
  - "Clean-clone proof ran under COMPOSE_PROJECT_NAME=ntma-sach (fresh volumes incl. ai-models, so the model download was real) after stopping the working-copy stack; the working-copy volumes were KEPT (compose down without -v) and install.sh re-run — no reseed needed, data identical"
  - "--random-seed-password replaces an empty/absent/dev-default SEED_DEFAULT_PASSWORD only while no mysql-data volume exists (seed is idempotent and never rewrites existing hashes, so a later change would desync api-login.sh)"
  - "Redaction keeps non-secret .env values readable as <KEY> (e.g. <SERVER_NAME>) and secrets as ***"
  - "NFR-05 is additionally measured over HTTPS (Bộ môn lock/unlock of reserved DTC225200094); NFR-04 adds an HTTPS 403 probe on top of the suites"
  - "Reserved for nfr-he-thong.sh: DTC225200094 + khóa K95 (K95 unused but cleaned/leftover-checked)"
metrics:
  duration: "~35 min"
  completed: 2026-09-28
estimate:
  tokens: 150000
actuals:
  tokens: 53500
  tasks: 3
  commits: 4
commits: 4
plan_head_before: 3c4b61cbd2644b1ca3065304661e208235610054
plan_head_after: a3a98dd10cf06737668dbbe10c729fc21944335b
---

# Phase 5 Plan 04: One-command install + full-system verification Summary

`bash deploy/install.sh` stands the seeded, AI-indexed HTTPS system up from a fresh `git clone` in 216 s (model pre-fetched at install time, runtime offline), and `bash deploy/verify-all.sh --report` proves all 12 suites/steps and NFR-01..NFR-19 (all Đạt except NFR-16 "Chưa đo" for 05-05) in 259 s, writing redacted machine-readable results to `docs/chuong-4-trien-khai/ket-qua-kiem-thu/`.

## Scope executed (user instruction)

Executed: Task 1 fully, Task 2 minus the report renderer, Task 3 only the `deploy/README.md` part.

**Deferred by user ("Bộ báo cáo, slide không gen bây giờ") — NOT created:**
- `tools/bao-cao/sinh-trang-kiem-thu.py` and `docs/chuong-4-trien-khai/08-kiem-thu-va-do-kiem-nfr.md` (4.8). `verify-all.sh --report` therefore writes `tong-hop.json` + `nhat-ky-verify-all.log` + the AI page only; the renderer hook (`sinh-trang-kiem-thu`) is not in verify-all yet — add it when the report is generated.
- `docs/chuong-4-trien-khai/03-huong-dan-cai-dat.md` (4.3) and `05-du-lieu-thu-nghiem.md` (4.5). The install procedure lives in `deploy/README.md` ("Cài đặt nhanh (một lệnh)"); all numbers those pages need are in `cai-dat-sach.log` and `tong-hop.json` (`du_lieu`).
- Consequently the plan's Task 2 checks on the 08 page and Task 3's build-report/kiem-tra-bao-cao checks were not run.

## Clean-clone install (Task 1, D-01/D-02)

Commit `5b4d46b`, 2026-09-28T10:43:58Z, 16 CPU (i5-12500H), 15.3 GiB RAM, Ubuntu 24.04, Docker 29.1.3, Compose 2.40.3. Working-copy stack stopped first (same subnet/ports); clone ran as project `ntma-sach` with brand-new volumes.

| Bước | Giây |
|---|---:|
| 0 Kiểm tra điều kiện | 1 |
| 1 deploy/.env + chứng chỉ | 0 |
| 2 Build image AI + tải trước mô hình (download 66 s, 518 MiB) | 69 |
| 3 compose up -d --build --wait | 78 |
| 4 Migration (0014) + ai /health | 0 |
| 5 DATA-01 (100 SV / 30 GV / 1 Bộ môn) | 0 |
| 6 seed-ai.sh (300 imported + indexed, 25 source theses, backfill) | 68 |
| **Tổng** | **216** |

`verify-all --quick` in the clone: 3/3 OK. Image builds used the host's Docker build cache (noted in the log header). Clone containers, volumes (`ntma-sach_*`), images (`ntma-sach-api/apache`) and the clone directory were removed. Working copy re-installed (57 s; idempotent: import "mới 0, đã có 300", seed_ai_corpus "mới 0, đã có 25", counts unchanged).

Model cache in the final compose: named volume `ai-models` mounted at `/models` (`HF_HOME`), filled by install step 2 through `docker compose run --rm --no-deps -T -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 --entrypoint python ai -m app.download_model`; the `ai` service runs with `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, verified inside the running container and by a successful restart offline.

## Full verification (Task 2, D-03) — `verify-all.sh --report`, 259 s

| # | Bước | KQ | Giây | Tóm tắt |
|---|---|---|---:|---|
| 1 | stack | OK | 0.3 | mysql/api/ai healthy, apache running, ai-db-init/ai-migrate exit 0, ai offline + no host port |
| 2 | du-lieu | OK | 0.6 | DATA-01/02/03 |
| 3 | smoke | OK | 3.7 | 24 checks |
| 4 | pytest-backend | OK | 103.5 | 53 passed |
| 5 | pytest-ai | OK | 2.7 | 8 passed |
| 6 | e2e-uc1 | OK | 4.0 | 14 checks |
| 7 | e2e-uc2-5 | OK | 15.5 | 67 checks |
| 8 | e2e-ai | OK | 26.0 | 30 checks |
| 9 | ai-nfr (--json --report) | OK | 92.9 | NFR-07..11 |
| 10 | nfr-he-thong | OK | 8.6 | 14 NFR checks |
| 11 | erd-db | OK | 0.1 | |
| 12 | con-sot | OK | 0.4 | no K95–K99 cohort/archive rows, no locked account |

NFR table (tong-hop.json):

| NFR | Kết quả | Đạt? |
|---|---|---|
| NFR-01 | HTTP 301 → https | Đạt |
| NFR-02 | 131 accounts all `$2b$12$`, seed password 0× in api/apache logs | Đạt |
| NFR-03 | JWT_SECRET 64 chars from env; expired token (app helper, exp in past) → 401, valid → 200, none → 401 | Đạt |
| NFR-04 | suites OK + HTTPS SV→Bộ môn routes 403/403/403 | Đạt |
| NFR-05 | pytest OK + HTTPS lock → login 401, old token 401, unlock → login 200 | Đạt |
| NFR-06 | pytest (magic bytes, body limit) + smoke (30 MB → 413) | Đạt |
| NFR-07 | host cannot reach 8002; 401/401/200; no Apache route; thesis_ai DB user DENIED; e2e-ai OK | Đạt |
| NFR-08 | direct P95 0.053 s; through Apache HTTPS P95 0.057 s (20 calls, 300-title corpus) | Đạt |
| NFR-09 | P95 3.02 s, 20/20 Hoàn tất, 0 lỗi | Đạt |
| NFR-10 | max 0.059 s | Đạt |
| NFR-11 | +1 encode | Đạt |
| NFR-12 | archive search P95 0.018 s; topic list P95 0.014 s | Đạt |
| NFR-13 | 65 text columns / 24 tables in thesis_core + thesis_ai all utf8mb4_vietnamese_ci; alembic heads 0014 / 0002 | Đạt |
| NFR-14 | NFC = NFD (identical nguon/id/ty_le, 81.92 %) | Đạt |
| NFR-15 | ProxyTimeout 120 s, SPA + /assets from Apache, /api via proxy | Đạt |
| NFR-16 | — | Chưa đo (05-05) |
| NFR-17 | 100 SV, 30 GV | Đạt |
| NFR-18 | 300 topics / 5 khóa, 300 DA_INDEX, 300 title vectors, 0 missing | Đạt |
| NFR-19 | 50 files (25 DOCX/25 PDF), 25 pairs, 4 kinds (7/7/6/5), verification table P01–P25 | Đạt |

AI memory peak 776 MiB (cap 2048), not OOM-killed. `du_lieu`: 100/30/1, kho 300 (60 per K18–K22), 300 DA_INDEX, index 300 titles / 2208 document sentences, 50 files, 25 pairs (HIEU_CHINH 17 / KIEM_CHUNG 8), 25 source theses with final report.

Reserved accounts/cohort for nfr-he-thong.sh: **DTC225200094** (+ bomon), khóa **K95** (both were free; recorded in deploy/README.md).

## Verification run

- Task 1 `<automated>`: verify-all --quick OK, `printenv HF_HUB_OFFLINE` = 1, log header has `commit`, second install.sh + quick OK. All 4 acceptance criteria pass (including `--fresh </dev/null` refusing and deleting nothing, ai has no ports, 0 .env values in the log).
- Task 2 `<automated>` (minus the deferred 08 page): tong-hop.json has no failed step, NFR-01..19 present, none False, NFR-08/09/12 True; K95–K99 leftover count 0. Acceptance: grep checks pass; secret/JWT scan of tong-hop.json + nhat-ky-verify-all.log clean. (The regenerated AI page contains the pre-existing literal `https://localhost/check-title` which equals the non-secret SERVER_NAME value; that page is not in the plan's scan list.)
- Task 3 README acceptance (`Cài đặt nhanh`, `verify-all.sh`, `Kịch bản demo UC1` kept) passes.
- `python3 tools/check-docs.py all` — only the known PI 1.1 failure.
- Final state: stack `ntma` up and healthy (mysql/api/ai healthy, apache running), fully seeded; `verify-all --quick` OK.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] README offline model command started uvicorn instead of downloading**
- **Found during:** Task 1 (compose offline flag)
- **Issue:** `docker compose run --rm ai python -m app.download_model` passes the command as args to `docker-entrypoint.sh`, which ignores them and serves; with `HF_HUB_OFFLINE=1` it could not download either.
- **Fix:** README now documents `--no-deps -T -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 --entrypoint python ai -m app.download_model` (same command install.sh uses).
- **Files modified:** deploy/README.md — **Commit:** a3a98dd

**2. [Rule 2 - Missing functionality] `--random-seed-password` semantics**
- The plan's "only if empty or absent" never fires on a fresh install (.env.example ships the dev default), and changing it after seeding silently desyncs api-login.sh from stored hashes. Implemented: replace empty/absent/dev-default only while no `<project>_mysql-data` volume exists, warn otherwise. Commit 5b4d46b.

**3. Plan-adjustment (non-destructive clean-clone proof)**
- Instead of `down -v` on the working copy, the clone ran under a distinct project name (`ntma-sach`) with fresh volumes, and the working copy was only stopped (`down` without `-v`), then re-installed. Same proof (real model download, fresh DB/seed), no demo data loss.

No product bugs were found; no thresholds were changed.

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: test-token-minting | deploy/nfr-he-thong.sh | Mints an expired and a valid access token for the reserved SV inside the api container with the app's own helper (needs docker access to the host = already root-equivalent); tokens stay in shell variables, are unset after use and never written to disk (verify-all redacts JWTs anyway). |

## Self-Check: PASSED

- FOUND: deploy/install.sh, deploy/verify-all.sh, deploy/nfr-he-thong.sh, docs/chuong-4-trien-khai/ket-qua-kiem-thu/{cai-dat-sach.log,tong-hop.json,nhat-ky-verify-all.log}
- FOUND commits: 5b4d46b, b8245ed, ba6ff05, a3a98dd
