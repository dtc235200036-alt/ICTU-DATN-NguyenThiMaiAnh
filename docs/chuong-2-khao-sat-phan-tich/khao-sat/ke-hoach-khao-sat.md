# Phụ lục A. Kế hoạch khảo sát

> **Mã PI:** 1.1 — **Yêu cầu:** ANLS-01

## A.1. Mục tiêu

Khảo sát nhằm thu thập bằng chứng thực tế cho ANLS-01 (PI 1.1) về quy trình quản lý đồ án/khóa luận tốt nghiệp hiện tại của Khoa Công nghệ thông tin, gồm:

- Quy trình đăng ký đề tài (ai đề xuất, ai duyệt, phân công GVHD);
- Quy trình duyệt đề cương (nội dung kiểm tra, số vòng chỉnh sửa);
- Quy trình theo dõi tiến độ thực hiện;
- Quy trình nộp báo cáo và tổ chức bảo vệ (hội đồng, chấm điểm);
- Các biểu mẫu dữ liệu (giấy/Excel) đang được dùng ở từng bước trên.

Kết quả khảo sát là đầu vào trực tiếp cho sơ đồ BPMN AS-IS (ANLS-02), bảng yêu cầu chức năng/phi chức năng (ANLS-03/04) và một phần cho thiết kế cơ sở dữ liệu (DSGN-01/02).

## A.2. Đối tượng khảo sát

| Mã | Vai trò | Số lượng tối thiểu | Tiêu chí chọn |
|----|---------|---------------------|----------------|
| BM-01 | Đại diện Bộ môn / Văn phòng Khoa | 1 | Người trực tiếp phụ trách quy trình đồ án (tiếp nhận đăng ký, xếp hội đồng, lưu trữ) |
| GV-01 | Giảng viên hướng dẫn | 1 | Đã hướng dẫn ít nhất 1 khóa đồ án gần đây |
| GV-02 | Giảng viên hướng dẫn / thành viên hội đồng | 1 | Đã tham gia hội đồng chấm bảo vệ ít nhất 1 lần |
| SV-01 | Sinh viên đang làm đồ án | 1 | Đang trong quá trình thực hiện đồ án tại thời điểm khảo sát |
| SV-02 | Sinh viên đã bảo vệ khóa trước | 1 | Đã hoàn thành bảo vệ đồ án ở khóa liền trước |
| SV-03 | Sinh viên sắp đăng ký đồ án | 1 | Chuẩn bị bước vào đợt đăng ký đề tài tiếp theo |

Tổng tối thiểu: 1 Bộ môn + 2 Giảng viên + 3 Sinh viên = 6 người.

## A.3. Lịch phỏng vấn

Toàn bộ phỏng vấn thực hiện trong tuần T1 (**28/09/2026 – 04/10/2026**) theo tiến độ đề cương. Sinh viên điền các ô còn trống khi đặt được lịch với từng người.

| Ngày (28/09–04/10) | Giờ | Người được phỏng vấn | Hình thức | Ghi chú |
|----------------------|-----|------------------------|-----------|---------|
| __/09 | __:__ | BM-01 | ☐ Trực tiếp ☐ Trực tuyến | |
| __/09 hoặc __/10 | __:__ | GV-01 | ☐ Trực tiếp ☐ Trực tuyến | |
| __/09 hoặc __/10 | __:__ | GV-02 | ☐ Trực tiếp ☐ Trực tuyến | |
| __/10 | __:__ | SV-01 | ☐ Trực tiếp ☐ Trực tuyến | |
| __/10 | __:__ | SV-02 | ☐ Trực tiếp ☐ Trực tuyến | |
| __/10 | __:__ | SV-03 | ☐ Trực tiếp ☐ Trực tuyến | |

Nếu không sắp xếp đủ 6 buổi trong T1, ưu tiên BM-01 và ít nhất 1 GV, 1 SV trước; các buổi còn lại dời sang đầu T2 và ghi rõ lý do trong biên bản tổng hợp.

## A.4. Phương pháp

- Phỏng vấn bán cấu trúc theo bộ câu hỏi tại **Phụ lục B** (`bo-cau-hoi-phong-van.md`), 20–30 phút mỗi người.
- Kèm phiếu khảo sát ngắn tại **Phụ lục C** (`phieu-khao-sat.md`) để thu thập thêm đánh giá định lượng (mức độ hài lòng, kênh công cụ đang dùng).
- Mỗi buổi phỏng vấn ghi biên bản theo mẫu tại **Phụ lục D** (`mau-bien-ban-phong-van.md`).
- Tài liệu/biểu mẫu nhận được trong buổi phỏng vấn được đăng ký vào sổ tại `tai-lieu-goc/README.md`.

## A.5. Đồng ý và ẩn danh

Trước mỗi buổi phỏng vấn, người phỏng vấn đọc script xin phép ngắn (có thể điều chỉnh cho phù hợp ngữ cảnh):

> "Em là Mai Anh, sinh viên K22A đang làm đồ án tốt nghiệp về hệ thống quản lý đồ án của Khoa. Em xin phép hỏi anh/chị một số câu hỏi về quy trình đồ án hiện tại để phục vụ phân tích cho đồ án của em, khoảng 20–30 phút. Câu trả lời sẽ chỉ được ghi theo mã vai trò (không ghi tên), và em chỉ dùng nội dung này cho mục đích học tập. Anh/chị có đồng ý không ạ?"

Nguyên tắc ẩn danh áp dụng cho mọi biên bản và phiếu khảo sát:

- Chỉ ghi mã vai trò (`BM-01`, `GV-01`, `GV-02`, `SV-01`, `SV-02`, `SV-03`...) — không ghi tên, số điện thoại, email của người được phỏng vấn.
- Không sao chép thông tin cá nhân/hồ sơ sinh viên vào bất kỳ tài liệu nào trong repo.
- Biên bản đã điền lưu tại `tai-lieu-goc/phong-van/BB-<BM|GV|SV>-<NN>.md`.
- Nếu một người được phỏng vấn không đồng ý ghi chép, chỉ ghi tóm tắt định tính bằng lời, không trích dẫn nguyên văn.

## A.6. Ánh xạ kết quả → tài liệu

| Kết quả khảo sát | Tài liệu sử dụng |
|-------------------|-------------------|
| Mô tả quy trình theo lời kể (Q-*-01..09 phần DT/DC/TD/BV/KHO) | `docs/chuong-2-khao-sat-phan-tich/2.1-khao-sat-hien-trang.md` |
| Trình tự các bước, vai trò, quyết định | Sơ đồ BPMN AS-IS (`docs/chuong-2-khao-sat-phan-tich/2.2-bpmn/`) |
| Nhu cầu, kỳ vọng người dùng (Q-*-CHUNG) | Bảng yêu cầu chức năng/phi chức năng (2.3, 2.4) |
| Biểu mẫu giấy/Excel thu được (TL-03, TL-06, TL-07, TL-08) | Thiết kế cơ sở dữ liệu (3.2), các bảng dữ liệu tương ứng |
| Kết quả phiếu khảo sát (Phụ lục C) | Số liệu định lượng minh họa trong 2.1 và phần đánh giá NFR |
