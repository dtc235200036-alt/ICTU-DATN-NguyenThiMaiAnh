# seed-data/ — Dữ liệu thử nghiệm tổng hợp cho dịch vụ AI (DATA-02, DATA-03)

> **Toàn bộ dữ liệu ở đây là TỔNG HỢP (synthetic).** Tên đề tài, họ tên, mã sinh viên và mọi
> đoạn văn trong tài liệu đều do bộ sinh `tools/datagen` tạo ra từ từ vựng tự soạn — không sao
> chép văn bản của bất kỳ sinh viên/đồ án thật nào (D-06, T-04-08). Cấu trúc tài liệu là
> **khuôn mẫu chung [ASSUMED]** của một đồ án CNTT tiếng Việt, vì mẫu chính thức của Khoa
> (TL-04/TL-05 trong `tai-lieu-goc/mau-chinh-thuc/`) chưa được thu thập — thay khi có mẫu.

## Các tệp

| Tệp | Nội dung | Dùng ở |
|-----|----------|--------|
| `de-tai-kho.csv` | 300 đề tài khóa cũ K18–K22 (60/khóa), 8 cụm chủ đề, đúng định dạng **import CSV kho đồ án** (`khoa,ten_de_tai,ma_so_sinh_vien,ho_ten_sinh_vien,ma_giang_vien,tu_khoa,diem`, UTF-8 có BOM) | Plan 04-05: import qua `POST /api/archive/import` → `/ingest` |
| `truy-van-ten-de-tai.csv` | 80 truy vấn tên đề tài có nhãn: 40 `DIEN_DAT_LAI` (diễn đạt lại một đề tài trong kho — kỳ vọng cảnh báo) + 40 `CUNG_LINH_VUC` (đối tượng dự trữ không có trong kho — kỳ vọng không cảnh báo); cột `tap` = `HIEU_CHINH` / `KIEM_CHUNG` (~30% giữ lại) | Plan 04-04: hiệu chỉnh ngưỡng tên đề tài |
| `manifest.json` | `topics` (stt, khóa, tên, cụm, `ma_doi_tuong` của từng dòng kho) và `cap` (25 cặp tài liệu: loại, tập, kỳ vọng, tệp, đoạn nội dung và nguồn gốc từng đoạn của B) | Plan 04-04 (nhãn), 04-06 (nạp tài liệu) |
| `tai-lieu/P01..P25-{A,B}.{docx,pdf}` | 50 tài liệu (25 cặp A/B); A là một đề tài trong kho, B là bài nộp cần kiểm tra | Plan 04-04, 04-06 |

## Phổ cặp tài liệu (DATA-03)

| Loại | Số cặp | Ý nghĩa | Kỳ vọng |
|------|--------|---------|---------|
| `CHEP_NGUYEN_VAN` | 7 | B chép nguyên văn một đoạn liên tiếp của A (40–60% nội dung B) | Cảnh báo |
| `DIEN_DAT_LAI` | 7 | B diễn đạt lại (đổi mẫu câu, từ đồng nghĩa, đảo thứ tự câu) cùng phần đó | Cảnh báo |
| `CUNG_LINH_VUC` | 6 | B cùng cụm chủ đề nhưng đối tượng khác (đối tượng dự trữ) | Không cảnh báo |
| `KHONG_LIEN_QUAN` | 5 | B thuộc cụm chủ đề khác | Không cảnh báo |

8 cặp (2/loại) thuộc tập `KIEM_CHUNG` — **không bao giờ dùng để hiệu chỉnh ngưỡng**, chỉ để kiểm
chứng cuối. Mỗi loại có cả chiều DOCX→PDF và PDF→DOCX.

## Sinh lại

```bash
uv --directory tools/datagen sync --frozen
uv --directory tools/datagen run python -m datagen all --out ../../seed-data
uv --directory tools/datagen run python -m datagen check --data ../../seed-data
```

Bộ sinh dùng hạt giống cố định `20261116` nên kết quả giống nhau từng byte giữa các lần chạy;
`check` tự sinh lại vào thư mục tạm và so sánh. Không sửa tay các tệp ở đây — sửa từ vựng/mã
trong `tools/datagen` rồi sinh lại.
