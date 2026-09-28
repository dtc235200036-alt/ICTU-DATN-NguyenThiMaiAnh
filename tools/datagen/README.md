# tools/datagen — bộ sinh dữ liệu thử nghiệm tổng hợp (DATA-02, DATA-03)

Công cụ một lần (không chạy trong Docker, không đụng CSDL) sinh toàn bộ `seed-data/`:
kho 300 đề tài, 80 truy vấn tên đề tài có nhãn, 50 tài liệu DOCX/PDF có phổ cặp trùng
chủ đích và `manifest.json`. Mọi văn bản là tự soạn (D-06).

## Cấu trúc

```
tools/datagen/
├── pyproject.toml / uv.lock     python-docx, reportlab, pymupdf (chỉ để kiểm tra round-trip)
└── datagen/
    ├── __main__.py   CLI + hạt giống SEED = 20261116
    ├── vocab.py      từ vựng tự soạn: cụm, đối tượng, đơn vị, đồng nghĩa, tên người;
    │                 hồ sơ đối tượng, mẫu câu (kèm câu "anh em" diễn đạt lại), dữ kiện công nghệ,
    │                 khuôn mẫu chung [ASSUMED] của đồ án
    ├── topics.py     kho 300 đề tài + 80 truy vấn (DATA-02)
    ├── documents.py  25 cặp tài liệu + nguồn gốc từng đoạn (DATA-03)
    ├── render.py     xuất DOCX (python-docx) và PDF (reportlab + DejaVuSans) từ CÙNG danh sách khối
    └── check.py      kiểm tra quy tắc import, round-trip trích xuất, thống kê trùng lặp, tính tất định
```

## CLI

```bash
cd tools/datagen
uv sync --frozen
uv run python -m datagen topics    --out ../../seed-data   # CSV kho + truy vấn + manifest.topics
uv run python -m datagen documents --out ../../seed-data   # 50 tệp + manifest.cap
uv run python -m datagen all       --out ../../seed-data
uv run python -m datagen check     --data ../../seed-data [--only topics|documents]
```

`check` in một dòng `OK: …` cho mỗi kiểm tra đạt, thoát mã khác 0 kèm danh sách vi phạm nếu có.

## Mở rộng từ vựng

- **Đối tượng mới**: thêm vào `CUM[<cụm>]["doi_tuong"]` *trước* 3 đối tượng dự trữ cuối danh sách
  (dự trữ = không bao giờ vào kho). Số đối tượng không dự trữ phải giữ 12/cụm để kho đúng 300 dòng
  (96 đối tượng × 3–4 lần). Nếu muốn đối tượng đó có thể làm tài liệu, thêm hồ sơ vào `HO_SO`.
- **Đơn vị**: thêm cặp (viết tắt, đầy đủ) vào `DON_VI[<nhóm>]`, tên riêng dùng `{tinh|huyen|xa|dn|truong}`.
- **Mẫu câu**: mỗi mẫu là một cặp (câu gốc, câu anh em diễn đạt lại) dùng cùng các ô
  `{dt} {sp} {dv} {tn} {tn2} {cn} {cn2} {dl} {dl2} {cg} {lv} {n1} {pt} {gs} {diem}`; mỗi câu kết thúc
  bằng dấu chấm, không có ". " ở giữa, ≤ 90 âm tiết, và nên có ≥ 2 ô để câu về đối tượng khác nhau
  không trùng nhau (kiểm tra `CUNG_LINH_VUC`/`KHONG_LIEN_QUAN` < 5%).
- **Đồng nghĩa**: chỉ thêm cặp an toàn ngữ pháp vào `DONG_NGHIA` (thay một lượt, theo ranh giới âm tiết).

Sau mọi thay đổi: chạy `all` rồi `check`, và commit lại toàn bộ `seed-data/`.
