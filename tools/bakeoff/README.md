# tools/bakeoff — So sánh mô hình embedding (D-01)

Công cụ một lần của Phase 4 để **chọn mô hình embedding** cho dịch vụ AI kiểm tra trùng lặp, dựa trên bằng chứng đo được trên chính máy phát triển:

| Profile | Mô hình | Tiền xử lý |
|---------|---------|------------|
| `bkai` | `bkai-foundation-models/vietnamese-bi-encoder` (PhoBERT-base-v2, ≈515 MiB) | chuẩn hóa NFC → tách từ `underthesea.word_tokenize(text, format="text")`, không tiền tố |
| `e5` | `intfloat/multilingual-e5-base` (XLM-R base, ≈1,06 GiB) | chuẩn hóa NFC → thêm `"query: "` ở **cả hai phía** (so khớp đối xứng), không tách từ |

Hai profile giống hệt `app/embedding.py` của plan 04-01. Encode bằng sentence-transformers, `normalize_embeddings=True` (cosine = tích vô hướng), CPU, `torch.set_num_threads(4)`, batch 32.

## Chạy lại

```bash
cd tools/bakeoff
uv sync --frozen                                  # torch lấy từ index CPU (+cpu), không kéo CUDA
uv run python bakeoff.py --validate-pairs         # kiểm tra cap-mau.jsonl
uv run python bakeoff.py --profile bkai           # → ket-qua-bkai.json
uv run python bakeoff.py --profile e5             # → ket-qua-e5.json (chạy SAU khi tiến trình bkai đã thoát)
uv run python bakeoff.py --decide                 # → ket-qua.json (áp dụng quy tắc chọn bên dưới)
# hoặc: uv run python bakeoff.py --all            # tiến trình cha không nạp mô hình, gọi từng profile bằng subprocess, lần lượt
```

Ràng buộc bộ nhớ (máy dùng chung 16 GB, từng bị OOM): mỗi tiến trình chỉ nạp **một** mô hình; trước khi nạp, harness chờ đến khi `MemAvailable ≥ 3 GiB` (tối đa 20 phút) rồi mới tiếp tục.

## Tệp

- `cap-mau.jsonl` — 80 cặp có nhãn, **tự soạn, tổng hợp** (không chép văn bản thật của sinh viên). Mỗi dòng: `{id, kieu, nhom, nhan, a, b}`.
  - `kieu`: `TIEU_DE` (30 cặp tên đề tài), `CAU` (30 cặp câu), `DOAN` (20 cặp đoạn 3–4 câu).
  - `nhom`: `DIEN_DAT_LAI` (cùng nội dung, diễn đạt lại — `nhan = 1`), `CUNG_LINH_VUC` (cùng lĩnh vực, dùng chung từ vựng chuyên ngành nhưng khác nội dung — `nhan = 0`, ca khó quyết định mô hình), `KHONG_LIEN_QUAN` (`nhan = 0`).
  - Phân bố: TIEU_DE 12/12/6, CAU 12/12/6, DOAN 8/8/4. Lĩnh vực: web, di động, AI/ML, IoT, dữ liệu, an toàn thông tin, ERP, học tập số.
- `bakeoff.py` — harness (`--validate-pairs`, `--profile`, `--all`, `--decide`).
- `ket-qua-bkai.json`, `ket-qua-e5.json` — kết quả thô mỗi profile: `theo_kieu[kieu]` = `{auc, auc_kho, tb_duong, tb_am, gap, margin, acc, nguong_acc, nguong_youden, tb_theo_nhom}`, `chi_phi` = `{load_s, title_ms, encode_300_s, peak_rss_mb}`, danh sách cosine từng cặp (`cap`), phiên bản gói (`phien_ban`), số CPU, và `loi` (khác `null` nếu mô hình không nạp được).
- `ket-qua.json` — quyết định đã chốt `{chon, ten_model, phan_doan, tien_to, ly_do, quy_tac, so_sanh, chi_phi, ngay}`; plan 04-04 và 04-05 đọc tệp này.

Định nghĩa chỉ số (theo từng `kieu`): `auc` = ROC AUC (dương = diễn đạt lại, âm = cùng lĩnh vực + không liên quan); `auc_kho` = AUC chỉ trên diễn đạt lại vs cùng lĩnh vực; `gap` = TB cosine dương − TB cosine âm; `margin` = min dương − max âm (> 0 nghĩa là tách được hoàn toàn); `acc` = độ chính xác tốt nhất trên mọi ngưỡng. Chi phí: `load_s` = thời gian import + nạp mô hình (từ cache); `title_ms` = trung vị 20 lần encode một tên đề tài (gồm tiền xử lý); `encode_300_s` = một lần encode 300 câu khác nhau (gồm tiền xử lý); `peak_rss_mb` = RSS đỉnh của tiến trình (`resource.getrusage`).

## Quy tắc chọn (đăng ký trước khi chạy)

Chọn **e5** chỉ khi e5 nạp được **và** AUC của e5 vượt bkai **≥ 0,05 trên CẢ tập CAU và tập DOAN**, **và** e5 encode 300 câu **≤ 20 s**, **và** RSS đỉnh của e5 **≤ 2,5 GiB (2560 MB)**. Nếu bkai không nạp được hoặc trượt cổng 20 s trong khi e5 qua cả hai cổng (độ trễ, bộ nhớ) → chọn e5. Nếu cả hai trượt cổng độ trễ → chọn bkai và ghi rõ rủi ro (phương án dự phòng là backend ONNX, 04-RESEARCH Pattern 2). Mọi trường hợp còn lại → chọn **bkai** (nhỏ hơn, 515 MiB — ưu tiên vì máy dùng chung bộ nhớ).

## Lưu ý

Tập cặp nhỏ và tổng hợp nên kết quả chỉ mang tính **định hướng**, không có ý nghĩa thống kê chặt chẽ; số đo chi phí lấy trên máy phát triển dùng chung (tải nền thay đổi). Bằng chứng cuối cùng về ngưỡng và chất lượng là đánh giá trên tập giữ lại (held-out) 50 tài liệu của plan 04-04.
