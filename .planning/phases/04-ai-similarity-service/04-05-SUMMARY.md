---
phase: 04-ai-similarity-service
plan: 05
status: complete
subsystem: ai-integration
tags: [docker-compose, httpx, alembic, faiss, push-on-write, e2e, AISV-01, AISV-02, AISV-03, DATA-02, D-04, D-05, D-07]
requires:
  - "04-01: ai-service image and HTTP contract (/ingest, /check-title, /check-document, /health with encode_calls)"
  - "04-02: seed-data/de-tai-kho.csv (300), truy-van-ten-de-tai.csv, manifest.json"
  - "04-03: tools/bakeoff/ket-qua.json chon = bkai"
  - "04-04: ai-service/calibration/nguong-de-xuat.json (67.8 / 10.4 / 67.7) and ket-qua-chi-tiet.json"
  - "03-04/03-05: archive.run_ingest, import_csv, POST /api/archive/import, /reindex"
provides:
  - "compose services ai (internal only) + ai-db-init (thesis_ai schema/user); volume ai-models"
  - "AiClientHttp behind get_ai_client (AI_CLIENT=http|stub); AiClient protocol with nguong / nguong_doan / loai_tru"
  - "Title check over TOPIC ∪ ARCHIVE with TitleMatch.nguon DE_TAI|KHO, do_an_kho_id, nullable de_tai_id"
  - "Alembic 0010: calibrated defaults + NGUONG_DOAN_TRUNG (for 04-06/04-07)"
  - "services/ai_index.py: run_ingest_topic, backfill, purge + CLI"
  - "deploy/seed-ai.sh (DATA-02) and deploy/e2e-ai.sh (ai_security, ai_title, ai_index)"
affects: [04-06, 04-07, 05]
tech-stack:
  added: []
  patterns:
    - "httpx moved from dev to runtime (already locked 0.28.1); one httpx.Client per call, connect 2 s + per-method read timeout"
    - "Every AI failure → AiServiceError whose text is endpoint + status/exception class only"
    - "Post-commit push-on-write through BackgroundTasks with only the int id crossing the request boundary"
    - "Test cleanups purge their vectors (REPLACE with empty text) before deleting rows"
key-files:
  created:
    - deploy/mysql/init-thesis-ai.sh
    - deploy/seed-ai.sh
    - deploy/e2e-ai.sh
    - backend/alembic/versions/0010_nguong_hieu_chinh.py
    - backend/app/services/ai_index.py
    - backend/tests/test_ai_client_http.py
  modified:
    - deploy/docker-compose.yml
    - deploy/.env.example
    - deploy/init.sh
    - deploy/e2e-uc1.sh
    - deploy/e2e-uc2-5.sh
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/app/core/config.py
    - backend/app/models/cau_hinh_nguong.py
    - backend/app/services/ai_client.py
    - backend/app/services/title_check.py
    - backend/app/services/archive.py
    - backend/app/schemas/topics.py
    - backend/app/routers/topics.py
    - backend/tests/conftest.py
    - frontend/src/features/topics/api.ts
    - frontend/src/features/topics/TitleCheckAlert.tsx
    - docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md
    - docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml (+ .svg/.png re-rendered)
decisions:
  - "Title-check dedup key = the thesis: an ARCHIVE record linked to a de_tai shares the key (DE_TAI, de_tai_id) with that topic and the higher score wins; an unlinked archive record keys on (KHO, id)"
  - "exclude_id also drops an archive record whose de_tai_id is the excluded topic"
  - "The stub accepts nguong but does not filter by it (Jaccard vs cosine scale); title_check filters for both clients"
  - "check_title asks the AI for TITLE_CHECK_TOP_K × 2 and cuts to TITLE_CHECK_TOP_K after dedup/skip"
  - "Saved title-check detail for KHO matches = '{ten_de_tai} ({khoa})'"
  - "seed-ai.sh runs backfill after the DA_INDEX wait (not before it), so the import's own run_ingest does the first encode and backfill is a no-op/repair"
  - "e2e-ai asserts NFR-11 as encode_calls +1 for a new archive record and +2 for a submitted topic (1 query encode for the saved title check + 1 ingest)"
metrics:
  duration: "~28 min"
  completed: 2026-09-28
estimate:
  tokens: 140000
  tasks: 2
actuals:
  tokens: 19800   # chars/4 over the diff of this plan's commits (svg/png excluded)
  tasks: 2
  commits: 4      # MEASURED rev-list 1ce6cec..HEAD before the docs commit; includes a58c808 (concurrent Phase 3 reviewer, .planning only) — own task commits: 3
plan_head_before: 1ce6cec2028972abf02387266dba40749c0692e7
plan_head_after: 8f894ecacc4152be8d896e3f1d4bde1365b9ea63
---

# Phase 4 Plan 05: Cross-service AI tracer Summary

**A student's paraphrased title is now matched against the 300 seeded archive theses by the real bkai container in about 50–90 ms. The container sits on the internal network behind X-API-Key, uses thresholds taken from calibration, and a new archive record or submitted topic appears in the very next check for exactly one embedding call.**

## Tasks

| # | Task | Commit | Result |
|---|------|--------|--------|
| 1 | TRACER: compose ai + ai-db-init, AiClientHttp, ARCHIVE mapping, Alembic 0010, seed-ai, e2e ai_security + ai_title | 181790c | whole verify chain green |
| 2 | Client contract test | bdd5de6 | 1 test |
| 2 | Push-on-write, ai_index backfill/purge, e2e ai_index, purge in uc1/uc2-5 cleanups | 8f894ec | whole verify chain green, 0 K97/K98/K99 cohorts left |

**Tracer gate:** before any expansion, the Task 1 verify chain was re-run end to end: `up -d --build --wait`, head 0010, pytest 50 passed, frontend build, seed-ai, e2e-ai, e2e-uc1, e2e-uc2-5 and check-erd-db. It passed.

## Compose services as implemented

| Service | Definition |
|---|---|
| `ai-db-init` | `mysql:8.4`. Entrypoint is `bash /init-thesis-ai.sh` (mounted read-only). Environment: MYSQL_ROOT_PASSWORD, AI_DB_PASSWORD, MYSQL_HOST=mysql. Depends on mysql being `service_healthy`, `restart: "no"`, network ntma-internal. It runs `CREATE DATABASE IF NOT EXISTS thesis_ai`, then `CREATE USER IF NOT EXISTS` + `ALTER USER`, then `GRANT ALL ON thesis_ai.*` only. The root password is passed through MYSQL_PWD and the AI password through stdin. |
| `ai` | Build context `../ai-service`. `DATABASE_URL=mysql+pymysql://thesis_ai:…@mysql:3306/thesis_ai?charset=utf8mb4`, `AI_API_KEY=${AI_API_KEY:?}`, `AI_MODEL_PROFILE=${AI_MODEL_PROFILE:-bkai}`, APP_ENV production, HF_HOME /models, `TORCH_THREADS=${AI_TORCH_THREADS:-4}`. Volume `ai-models:/models`. `expose: ["8002"]` with **no `ports:`**. `mem_limit ${AI_MEM_LIMIT:-2g}`. Healthcheck is a python urllib `/health` probe requiring `status == "ok"` (interval 10 s, timeout 5 s, retries 30, start_period 600 s). Depends on mysql `service_healthy` and ai-db-init `service_completed_successfully`. `restart: unless-stopped`. |
| `api` (changes) | Adds `AI_CLIENT=${AI_CLIENT:-http}`, `AI_SERVICE_URL=http://ai:8002` and `AI_API_KEY=${AI_API_KEY:?}`. Depends on ai with **`service_started`**. |
| Apache | Unchanged. It has no route to 8002 or `ai`. |

- **First start** (empty `ai-models` volume, model downloaded from Hugging Face): alembic ran at 06:58:07. "Application startup complete" came at 06:59:16, about **68 s**, of which roughly 60 s was the model download. The first full `up --build --wait` took 127 s.
- **Warm restart:** about 10 s.
- **Memory:** 464 MiB of 2 GiB after startup.
- `deploy/init.sh` now appends any `.env.example` key that is missing from an existing `.env`, generating `__GENERATE__` values. On this host it added AI_CLIENT, AI_API_KEY, AI_DB_PASSWORD, AI_MODEL_PROFILE, AI_MEM_LIMIT and AI_STUB_MODE. A second run changes nothing.

## Calibrated values in Alembic 0010 (data only)

| loai | 0004 value | 0010 value | Source key |
|---|---:|---:|---|
| NGUONG_TEN_DE_TAI | 50.00 | **67.80** | nguong_ten_de_tai |
| NGUONG_TAI_LIEU | 30.00 | **10.40** | nguong_tai_lieu |
| NGUONG_DOAN_TRUNG | (new) | **67.70** | nguong_doan |

- The values are written as literals, with a comment naming `ai-service/calibration/nguong-de-xuat.json` and the date 2026-09-28.
- UPDATEs apply only `WHERE tai_khoan_id IS NULL`. The insert happens only if the row is absent. Downgrade deletes NGUONG_DOAN_TRUNG and restores 50/30 where `tai_khoan_id IS NULL`.
- conftest resets the three rows to the stub scale (50/30/80) after `upgrade head`, and forces `AI_CLIENT=stub`.

## AiClient protocol (backend/app/services/ai_client.py)

```python
check_title(text, top_k=5, nguong=None) -> {"matches": [{"ref_id", "loai", "ty_le"}]}
check_document(ref_id, text, top_k=5, nguong_doan=None, loai_tru=None) -> {"ty_le_tong", "do_an_trung", "chi_tiet", ...}
ingest(ref_id, loai, text) -> {"chunk_count", "indexed"}
AiClientHttp(base_url, api_key, *, title_timeout, document_timeout, ingest_timeout, transport=None)
```

- Timeouts are 4 s for titles, 24 s for documents and 60 s for ingest (connect 2 s).
- `AI_CLIENT=http` requires `AI_SERVICE_URL` and an `AI_API_KEY` of at least 32 characters (Settings model validator).
- `check_document` sends `loai_tru` as a sorted list and leaves out `nguong_nguyen_van`. Plan 04-06 wires `nguong_doan` and `loai_tru` from `document_check`, which currently still calls `check_document(doc.id, text)`.

## ai_index CLI (inside the api container; exit 2 unless AI_CLIENT=http)

```bash
docker compose -f deploy/docker-compose.yml exec -T api python -m app.services.ai_index backfill [--loai TOPIC ARCHIVE]
docker compose -f deploy/docker-compose.yml exec -T api python -m app.services.ai_index purge --loai TOPIC|ARCHIVE|DOCUMENT --ids 1,2,3
```

`backfill` output on this host: TOPIC 0 (there are no non-draft topics in the demo DB), ARCHIVE 300 succeeded / 0 failed (every one a no-op on the AI side). `purge ""` is a no-op.

## e2e-ai.sh

- **Accounts used:** bomon, DTC225200095, DTC225200096. GV023 is reserved but unused. Test cohort is K97. Before use, `grep` showed no other script using any of them.
- **ai_security:**
  - The host cannot connect to 127.0.0.1:8002.
  - Inside the api container: no key gives 401, a wrong key gives 401, the real key gives 200. The key is read inside the container and never printed.
  - ntma.conf has no `8002` or `//ai`.
  - `POST https://localhost/check-title` returns 200 with the SPA HTML, not an AI body.
  - The thesis_ai DB user is denied on `thesis_core.tai_khoan`.
- **ai_title timings** (check-title through Apache, curl time_total):

| Query | Type | Time | Top-1 |
|---|---|---:|---|
| TV001 | paraphrase | 0.072–0.090 s | Kho đồ án, 81.92 % (K21) |
| TV002 | paraphrase | 0.049–0.053 s | Kho đồ án, 69.83 % (K22, same object ERP.nha_thuoc) |
| TV003 | paraphrase | 0.050–0.052 s | Kho đồ án, 72.89 % (K20) |
| TV004 | same field | 0.049–0.052 s | no KHO match above 67.8 |

  NFC and NFD gave identical (nguon, id, ty_le) triples for all four queries.
- **ai_index:**
  - New K97 archive record reached DA_INDEX with encode_calls 9 → 10 (**+1**). A paraphrase then matched it at 90.12 %.
  - DTC225200095's self-proposal went to CHO_DUYET with encode_calls +2 (the saved title check plus the ingest). DTC225200096's paraphrase then matched it as DE_TAI at 93.51 %.
  - Cleanup purges the vectors, then deletes the rows.

## Observed /health after seeding

| When | index_size (tieu_de) | index_size_tai_lieu | encode_calls | thieu_embedding |
|---|---:|---:|---:|---:|
| After the first seed-ai.sh | 300 | 0 | 300 (one per import ingest) | 0 |
| After running e2e-ai, e2e-uc1 and e2e-uc2-5 again with purge | **300** | 0 | 52 (container restarted at the last `up --build`) | 0 |

Test runs now leave the index exactly as they found it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] e2e-uc2-5 left an orphan ARCHIVE vector on every run**
- **Found during:** Task 2 verification (the index grew 303 → 304 after one uc2-5 run).
- **Issue:** the script deletes one imported archive record through `DELETE /api/archive/{id}` (UC5.3). Its row is gone before cleanup, so collecting ids from the DB missed it.
- **Fix:** the script records `DELETED_KHO_IDS` and cleanup merges it into the ARCHIVE purge list. A one-off purge removed the four orphans from runs made before purge existed (ids 343–345 and 348). The index is now back to 300 and stays there across e2e-ai, uc1 and uc2-5.
- **Files:** deploy/e2e-uc2-5.sh. **Commit:** 8f894ec.

**2. [Rule 2 - Correctness] T-04-17 proven in the e2e, not only by the grant text**
- ai_security also runs a query as the thesis_ai DB user from inside the ai container against `thesis_core.tai_khoan`, and requires it to be denied. This covers the plan's fails_when clause "the ai DB user can read thesis_core".

**3. [Doc write-back] NGUONG_DOAN_TRUNG in the design docs**
- Added to `enum LoaiCauHinhNguong` in lop-thuc-the.puml (svg/png re-rendered) and to the `cau_hinh_nguong.loai` row of the data dictionary. The data dictionary now also lists the 0010 defaults.
- There is no schema change. check-erd-db and check-docs (class-erd, render, links) pass.

**4. [TDD note] RED shown by mutation**
- The plan puts `test_ai_client_http.py` in Task 2, but Task 1 (the tracer) already has to ship AiClientHttp and the mapping, so the test passed on first run.
- Mutation evidence instead:
  - Keying dedup per archive id makes the test fail.
  - Putting the key into the error message makes the test fail.
- The single test was committed as `test(04-05)` before the Task 2 feature commit.

### Other

- **Commits on `main`:** per the orchestrator's instruction ("sequential on main"). The GSD protected-branch probe reports main as protected, but the project's established flow commits phase work on main.
- **Concurrent commit:** a58c808 (`docs(03): code review`, `.planning/` only) landed during this plan, so rev-list counts 4 commits while this plan made 3 task commits.

## Human check (self-performed, user confirmation pending)

Headless Chrome via CDP (scratchpad `cdp0405.py`, 1440 px):

1. DTC225200095 logged in and opened `/de-tai/de-xuat`, choosing a temporary cohort "Đợt CDP 04-05 (K97)".
2. They typed TV009 "Phát triển nền tảng số luyện nói tiếng Anh trực tuyến tại trường trung học phổ thông Nguyễn Trãi trên nền tảng NodeJS" and left the field.
3. **In 0.26 s** the warning "Phát hiện 3 đề tài tương tự trong kho" appeared. It had a Nguồn column with 3 "Kho đồ án" tags, each with khóa, GVHD and %:
   - K22 at 90.05 %
   - K21 at 77.5 %
   - K18 at 71.37 %
4. "Vẫn gửi đề xuất" followed by "Gửi đề xuất" went to `/de-tai/97`, showing "Chờ duyệt" and "Ngưỡng áp dụng: 67.8%". The saved rows were suffixed "(K22)" / "(K21)" / "(K18)".
5. **Cleanup:** the TOPIC vector was purged and the topic and cohort were deleted. That leaves 0 K97/K98/K99 cohorts, 0 recent notifications and 300 title vectors. Chrome was stopped and its profile deleted.

## Known Stubs

None. The AI_CLIENT=stub fallback is intentional (D-07).

**Recorded limitation:** deleting an archive record through the product does not remove its vector, because §3.3.5 has no /delete. The title check skips refs whose row is gone, and automated tests purge what they delete. This is a deferred idea for plan 04-07's README.

## Threat Flags

None beyond the register. T-04-15..T-04-22 and T-04-SC are mitigated as planned:
- expose-only port, no Apache route, and 401 on a missing or wrong key, all proven by the e2e;
- key-free error messages, proven by the test;
- a schema-only grant, proven by the e2e;
- `service_started` plus timeouts;
- 0010 limited to `tai_khoan_id IS NULL`;
- purge in cleanups;
- init.sh only appends keys;
- httpx 0.28.1 already locked, with no new package.

## Self-Check: PASSED

- FOUND: deploy/mysql/init-thesis-ai.sh, deploy/seed-ai.sh, deploy/e2e-ai.sh, backend/alembic/versions/0010_nguong_hieu_chinh.py, backend/app/services/ai_index.py, backend/tests/test_ai_client_http.py
- FOUND commits: 181790c, bdd5de6, 8f894ec
- Final runs:
  - backend pytest: 51 passed
  - ai-service pytest: 5 passed
  - smoke-test.sh: all checks passed
  - e2e-uc1, e2e-uc2-5 and e2e-ai: green
  - check-erd-db: OK
  - frontend build: OK
  - `dot_do_an` K97/K98/K99 count: 0
  - alembic head: 0010
