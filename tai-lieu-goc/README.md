# Tài liệu gốc thu thập (khảo sát)

> **Mã PI:** 1.1 — **Yêu cầu:** ANLS-01

Thư mục này lưu các tài liệu gốc (quy chế, biểu mẫu, mẫu chính thức, đồ án các khóa trước, biên bản phỏng vấn) thu thập được từ Bộ môn / Giảng viên / Sinh viên trong quá trình khảo sát (D-02). Đây là kho tài liệu nguồn — không phải một chương của quyển báo cáo, nên nằm ngoài `docs/` (D-09).

## 1. Danh mục cần thu thập

Trạng thái khởi tạo là `Chưa có` cho toàn bộ danh mục; plan 01-07 cập nhật trạng thái sau khi sinh viên nộp file thật.

| Mã | Tài liệu | Xin từ | Định dạng | Thư mục | Dùng cho | Trạng thái |
|----|----------|--------|-----------|---------|----------|------------|
| TL-01 | Quy chế/quy định đồ án, khóa luận tốt nghiệp của Trường/Khoa | Bộ môn / Văn phòng Khoa | PDF/DOCX | `quy-che/` | Cơ sở cho A.5, ANLS-04 (yêu cầu bảo mật/quy trình) | Chưa có |
| TL-02 | Quy định kiểm tra trùng lặp/Turnitin và ngưỡng hiện hành | Bộ môn / Văn phòng Khoa | PDF/DOCX | `quy-che/` | Feeds Yêu cầu phi chức năng (NFR ngưỡng trùng lặp) và AISV-07 | Chưa có |
| TL-03 | Phiếu đề xuất/đăng ký đề tài | Bộ môn / Giảng viên | PDF/DOCX/ảnh | `bieu-mau/` | Feeds bảng biểu mẫu dữ liệu (2.1) và thiết kế CSDL đề tài (DSGN-01/02) | Chưa có |
| TL-04 | Mẫu đề cương chính thức | Bộ môn / Giảng viên | DOCX | `mau-chinh-thuc/` | Phase 4 — bộ lọc phần mẫu chung (AISV-04) | Chưa có |
| TL-05 | Mẫu quyển báo cáo đồ án chính thức | Bộ môn / Văn phòng Khoa | DOCX | `mau-chinh-thuc/` | Phase 4 (AISV-04) và Phase 5 — pandoc reference-doc (D-08) | Chưa có |
| TL-06 | Phiếu nhận xét của GVHD / báo cáo tiến độ | Giảng viên | PDF/DOCX/ảnh | `bieu-mau/` | Feeds biểu mẫu dữ liệu tiến độ (2.1), thiết kế CSDL báo cáo tiến độ | Chưa có |
| TL-07 | Phiếu chấm điểm bảo vệ | Bộ môn / Giảng viên | PDF/DOCX/ảnh | `bieu-mau/` | DEFN-03/04 (trường điểm, trọng số, tổng hợp) | Chưa có |
| TL-08 | Biên bản hội đồng / quyết định thành lập hội đồng, lịch bảo vệ mẫu | Bộ môn | PDF/DOCX/ảnh | `bieu-mau/` | Feeds thiết kế CSDL hội đồng (DEFN-02) | Chưa có |
| TL-09 | Danh sách đề tài các khóa trước | Bộ môn | Excel/PDF | `bieu-mau/` | Phase 4 — seed realism, DATA-02 (300 đề tài thực tế) | Chưa có |
| TL-10 | ~20 đồ án thật các khóa trước (DOCX/PDF) | Bộ môn / Kho lưu trữ Khoa | DOCX/PDF | `do-an-cu/` | Phase 4 — so sánh model embedding và hiệu chỉnh ngưỡng trùng lặp | Chưa có |
| TL-11 | Mẫu nhận xét/phản biện | Giảng viên | PDF/DOCX/ảnh | `bieu-mau/` | Feeds biểu mẫu dữ liệu chấm điểm/phản biện | Chưa có |
| TL-12 | Biên bản phỏng vấn đã điền (BB-xx) | Sinh viên (tự tạo qua Phụ lục D) | Markdown | `phong-van/` | Nguồn khảo sát chính cho 2.1 Khảo sát hiện trạng, BPMN AS-IS | Chưa có |

## 2. Quy ước đặt tên

- Tài liệu thu thập: `TL-NN-<khoa-hoac-mo-ta-khong-dau>.<ext>` — ví dụ: `TL-10-k20-quan-ly-thu-vien.pdf`, `TL-04-mau-de-cuong-2026.docx`.
- Biên bản phỏng vấn đã điền: `BB-<BM|GV|SV>-<NN>.md` — ví dụ: `BB-GV-01.md`, lưu tại `phong-van/`.

## 3. Sổ đăng ký tệp (manifest)

Mỗi khi nhận một tài liệu, thêm một dòng vào bảng dưới đây — kể cả khi file nhị phân không được commit (do `.gitignore` trong `do-an-cu/`), dòng manifest vẫn commit để truy vết đã thu thập gì, từ ai, khi nào.

| Mã TL | Tệp | Thư mục | Nguồn (vai trò) | Ngày nhận | SHA-256 (12 ký tự đầu) | Ghi chú |
|-------|-----|---------|-------------------|-----------|-------------------------|---------|
| | | | | | | |

Lệnh tính băm (chạy trong thư mục chứa file, rồi copy 12 ký tự đầu vào cột SHA-256):

```bash
sha256sum <file> | cut -c1-12
```

## 4. Quy tắc bảo mật

- Không ghi tên, số điện thoại hay email của người được phỏng vấn vào bất kỳ tài liệu nào trong repo — chỉ dùng mã vai trò (`BM-01`, `GV-01`, `SV-01`...).
- Đồ án các khóa trước (`do-an-cu/`) mặc định được git-ignore vì chứa dữ liệu cá nhân của bên thứ ba (tên/mã SV khác, nội dung có bản quyền); chỉ dòng manifest (tên file, khóa, SHA-256) được commit. Muốn commit các file này, xác nhận repo không có remote công khai rồi xóa `do-an-cu/.gitignore`.
- Quy chế, biểu mẫu trống và mẫu chính thức của Trường/Khoa (TL-01, TL-02, TL-03, TL-04, TL-05, TL-06, TL-07, TL-08, TL-09, TL-11) không chứa dữ liệu cá nhân của người thứ ba nên được phép commit bình thường.
- Không commit bất kỳ hồ sơ/kết quả học tập cá nhân nào của sinh viên thực hiện đồ án này hoặc của người khác.
