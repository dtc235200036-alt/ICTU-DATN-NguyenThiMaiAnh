# Phase 5: System Verification & Defense Package - Context

**Gathered:** 2026-09-28 (auto mode — user asleep; recommended defaults selected, review later)
**Status:** Ready for planning

<domain>
## Phase Boundary

Bring the finished system (Phases 2–4) up as one demo-ready deployment with the full seed data, measure the NFRs on it, write chương 4 (Triển khai) and assemble the 4-chapter report (DOCX) plus defense slides and an end-to-end demo script, rehearsed once. Requirements: RPRT-01, RPRT-02 (and final evidence for DEPL-02, DATA-01..03, NFR-07..11). No new product features.

</domain>

<decisions>
## Implementation Decisions

### Carried forward (locked)
- Docker Compose project `ntma` (mysql 8.4 / api / apache httpd with TLS / ai internal-only) is the deployment unit; Apache HTTPS reverse proxy, no Apache route to the AI service; seed = 100 SV, 30 GV, 1 Bộ môn (DATA-01), 300 archive topics via the real archive import (DATA-02), 50 test files (DATA-03) from `seed-data/`.
- Docs are Markdown under `docs/` (chương-1 … chương-4), exported with pandoc to DOCX (Phase 1 D-08); diagrams PlantUML/draw.io already rendered; `tools/check-docs.py` must stay green; every deliverable traceable to PI 1.1–4.2 via `docs/truy-vet.md`.

### Deployment target
- **D-01:** The "server" for the thesis is a clean Linux host running the compose stack. Default: the dev host itself, brought up **from a clean clone** with a single documented procedure (`deploy/install.sh` or equivalent: generate secrets/.env, certs, `docker compose up -d --build --wait`, migrations, seed, AI backfill). Moving to a real school/lab server is the same procedure — documented as the "Hướng dẫn cài đặt" in chương 4. If the user later supplies a real server (e.g. box 10.22.7.144), rerun the procedure there; not a blocker. [auto] → "clean-clone reproducible install on the demo host" (recommended)
- **D-02:** Offline-safe AI model: the install procedure pre-fetches the bkai model into the cache volume (or bakes it) so the demo does not depend on Hugging Face availability.

### Verification & measurement
- **D-03:** One scripted full-system check (`deploy/verify-all.sh` or reuse of smoke/e2e-uc1/e2e-uc2-5/e2e-ai/ai-nfr scripts chained) run against the seeded deployment; results (pass/fail + timings) saved to `docs/chuong-4-trien-khai/` for the report. NFR measurements (title check ≤5 s, document check ≤30 s P95, others NFR-07..11) measured on the full corpus via the real HTTPS path.
- **D-04:** A browser walkthrough of the 5 UCs × 3 roles via headless Chrome (CDP) producing screenshots at 1440px for chương 4 "Kết quả thử nghiệm" and slides. User confirmation of the rehearsal is a human step (recorded as pending, not blocking the autonomous run).

### Report (RPRT-01)
- **D-05:** Chương 4 "Triển khai": môi trường & công nghệ, cấu trúc mã nguồn, hướng dẫn cài đặt (from D-01), dữ liệu thử nghiệm, kết quả chức năng (screenshots per UC), kết quả AI (bake-off, calibration, held-out table — already under `docs/chuong-4-trien-khai/thu-nghiem-ai/`), đo NFR, bảo mật/phân quyền, hạn chế & hướng phát triển. Plus Mở đầu, Kết luận, Tài liệu tham khảo, Phụ lục.
- **D-06:** Build pipeline `tools/build-report.sh`: pandoc concatenation in chapter order → `bao-cao/bao-cao-do-an.docx` using a `reference.docx`. The official school template is not yet supplied (`tai-lieu-goc/mau-chinh-thuc/` empty) → create a reasonable `reference.docx` (Times New Roman 13, 1.5 line spacing, A4 margins per common Vietnamese thesis rules, heading numbering) marked as ASSUMED; swap in the official template when supplied. Front matter (bìa, lời cam đoan, lời cảm ơn, mục lục, danh mục hình/bảng) generated or templated.

### Slides & demo (RPRT-02)
- **D-07:** Defense slides (~15–20 slides): bối cảnh & mục tiêu, khảo sát/BPMN, UC, kiến trúc SOA, CSDL, AI method + bake-off + calibration results, demo flow, kết quả NFR, kết luận. Produced as a file the user can present/edit (PPTX via python-pptx or pandoc, or the account's Slides artifact type — Developer's Discretion; must be exportable to PPTX/PDF).
- **D-08:** Demo script `docs/kich-ban-demo.md`: step-by-step with accounts, data, expected screens, timing (~10–15 min), including the duplicate-title warning and a seeded duplicate document showing highlighted passages; plus a reset script to restore the demo state.

### Developer's Discretion
- Exact script names, report front-matter mechanics, slide tooling, screenshot set, chapter-4 section ordering within the school's 4-chapter structure.

</decisions>

<canonical_refs>
## Canonical References

- `H01.DTC235200036.NguyenThiMaiAnh.docx` §8 (report structure), §6/§7b (CLO/PI criteria)
- `.planning/REQUIREMENTS.md` (RPRT-01/02), `.planning/ROADMAP.md` Phase 5 success criteria
- `docs/README.md`, `docs/truy-vet.md`, `docs/chuong-1-*`, `chuong-2-*`, `chuong-3-*`, `docs/chuong-4-trien-khai/thu-nghiem-ai/*`
- `deploy/` (docker-compose.yml, README.md, smoke-test.sh, e2e-*.sh, init.sh), `ai-service/README.md`
- Phase 2–4 SUMMARY / VERIFICATION files
- `docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md` (NFR targets)

</canonical_refs>

<code_context>
## Existing Code Insights

- Deploy scripts and e2e scripts exist per phase; Phase 4 adds `e2e-ai.sh` and `ai-nfr.sh`.
- `tools/check-docs.py`, `tools/render-diagrams.sh`, `tools/check-erd-db.py` exist.
- headless Chrome CDP driver used for self-checks in Phases 2–3.

</code_context>

<specifics>
## Specific Ideas

- Keep build artifacts (DOCX, PPTX, screenshots) reproducible from the repo via scripts.
- Phase 1 human items (interview minutes, official templates) may still be missing — report must clearly mark ASSUMED survey content rather than invent interview results.

</specifics>

<deferred>
## Deferred Ideas

- Deployment to a real remote school server (only if user provides one).
- Final formatting to the official template once supplied.

</deferred>

---

*Phase: 05-system-verification-defense-package*
*Context gathered: 2026-09-28 (auto)*
