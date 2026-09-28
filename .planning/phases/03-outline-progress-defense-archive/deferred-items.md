# Phase 3 — Deferred items (out of scope for the plan that found them)

Found during 03-07 (not caused by 03-07's changes; not fixed):

- **Orphan upload files in `ntma_uploads-data`.** 42 files are on the volume (29 in `DE_CUONG`, 7 in `BAO_CAO_CUOI`, 6 in `BAO_CAO_TIEN_DO`), but `tai_lieu_do_an` has 0 rows. None of these files is newer than 2026-09-28 06:45Z, so they come from earlier plans' CDP or e2e runs that failed before their cleanup ran. They are harmless, because files are only served through the authorised API. To remove them, run `find /data/uploads -type f -delete` in `api` while `tai_lieu_do_an` is empty, or reset with `down -v`.
- **Old read notifications on reserved e2e accounts.** Notifications left by earlier aborted runs of plans 03-02 to 03-04 (for example "Hội đồng 3 …" and "GVHD yêu cầu sửa đề cương …") still belong to DTC225200098 and GV026–GV028. The e2e run has marked them read, and they do not affect any assertion.
- **Ruff E741 in `backend/app/services/defense.py`.** The variable named `l` in 5 places predates 03-07.
