# Thử nghiệm dịch vụ AI kiểm tra trùng lặp — mục lục

> **Mã PI:** 3.4, 4.1, 4.2 — **Yêu cầu:** AISV-01..AISV-07, DATA-02, DATA-03, NFR-07..NFR-11

Thư mục này là phần "thử nghiệm và đánh giá" của dịch vụ AI (Phase 4) cho chương 4 báo cáo. Mỗi trang dưới đây do một công cụ trong repo sinh hoặc đo lại, nên chạy lại đúng các lệnh ở mục cuối sẽ cho lại cùng số liệu (trên cùng bộ dữ liệu sinh với hạt giống cố định).

## Các trang

| Trang | Nội dung | PI | Yêu cầu |
|---|---|---|---|
| [01-du-lieu-thu-nghiem.md](01-du-lieu-thu-nghiem.md) | Bộ dữ liệu: kho 300 đề tài khóa K18–K22, 50 tài liệu DOCX/PDF thành 25 cặp với phổ trùng lặp chủ đích (chép nguyên văn, diễn đạt lại, cùng lĩnh vực, không liên quan), tách tập hiệu chỉnh / kiểm chứng | 4.2 | DATA-02, DATA-03 |
| [02-so-sanh-mo-hinh-embedding.md](02-so-sanh-mo-hinh-embedding.md) | So sánh `bkai-foundation-models/vietnamese-bi-encoder` (+ tách từ underthesea) với `intfloat/multilingual-e5-base`: độ tách (AUC, khoảng cách điểm) và độ trễ; lý do chốt bkai | 3.4 | AISV-03, AISV-04 |
| [03-hieu-chinh-nguong.md](03-hieu-chinh-nguong.md) | Hiệu chỉnh ngưỡng tên đề tài, ngưỡng đoạn (ngữ nghĩa), ngưỡng nguyên văn (MinHash) và ngưỡng cảnh báo tài liệu trên tập hiệu chỉnh; kiểm chứng trên tập giữ lại; hạn chế | 3.4 | DATA-03, AISV-03, AISV-04 |
| [04-hieu-nang-va-bao-mat.md](04-hieu-nang-va-bao-mat.md) | Đo trên stack chạy thật: cô lập dịch vụ AI (NFR-07), thời gian kiểm tra tên (NFR-08), nộp → hoàn tất (NFR-09), phản hồi nộp (NFR-10), một lần encode mỗi ingest (NFR-11), bộ nhớ | 3.4, 4.1 | AISV-01, AISV-02, AISV-03, AISV-06 |

Các giá trị hiệu chỉnh ở trang 03 là giá trị **đề xuất** hiện trên màn hình cấu hình ngưỡng của Bộ môn (UC0.4, AISV-07); Bộ môn có thể sửa, lần kiểm tra kế tiếp áp dụng giá trị mới, kết quả cũ giữ ngưỡng lúc kiểm tra.

## Chạy lại theo thứ tự

1. Sinh bộ dữ liệu (không cần docker):

   ```bash
   uv --directory tools/datagen run python -m datagen all --out ../../seed-data
   uv --directory tools/datagen run python -m datagen check --data ../../seed-data
   ```

2. So sánh mô hình (mỗi profile một tiến trình riêng, cần vài GiB RAM trống):

   ```bash
   uv --directory tools/bakeoff run python bakeoff.py --all
   uv --directory tools/bakeoff run python bakeoff.py --decide
   ```

3. Hiệu chỉnh và kiểm chứng ngưỡng (từ `ai-service/`):

   ```bash
   uv --directory ai-service run python calibration/calibrate.py tune --data ../seed-data \
     --profile-from ../tools/bakeoff/ket-qua.json --out calibration
   uv --directory ai-service run python calibration/calibrate.py evaluate --data ../seed-data \
     --profile-from ../tools/bakeoff/ket-qua.json --out calibration \
     --report ../docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md --apply
   ```

4. Nạp kho vào stack đang chạy (idempotent: 300 đề tài kho, 25 đồ án nguồn có báo cáo, backfill chỉ mục):

   ```bash
   bash deploy/seed-ai.sh
   ```

5. Kiểm thử đầu-cuối với dịch vụ AI thật (SC1–SC5: tên diễn đạt lại, bảo mật, ngưỡng do Bộ môn đặt, push-on-write, tài liệu chép nguyên văn):

   ```bash
   bash deploy/e2e-ai.sh
   ```

6. Đo hiệu năng/bảo mật và ghi lại trang 04:

   ```bash
   bash deploy/ai-nfr.sh --report docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md
   ```

`e2e-ai.sh` và `ai-nfr.sh` dùng chung tài khoản `DTC225200095` và `GV023` — **không chạy song song hai script**.
