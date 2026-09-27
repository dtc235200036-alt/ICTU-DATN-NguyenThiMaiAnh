# Phụ lục C. Phiếu khảo sát

> **Mã PI:** 1.1 — **Yêu cầu:** ANLS-01

## Hướng dẫn

Phiếu khảo sát bổ sung cho phỏng vấn (Phụ lục B), thu thập nhanh đánh giá định lượng (thang Likert 1–5: 1 = Rất không đồng ý … 5 = Rất đồng ý), lựa chọn kênh/công cụ đang dùng, và một câu hỏi mở mỗi vai trò. Có thể phát bản in hoặc nhập lại vào Google Forms; kết quả được tổng hợp theo định dạng CSV mô tả ở cuối phụ lục này.

## C.1. Bộ môn / Văn phòng Khoa

| Mã | Nội dung | Kiểu trả lời |
|----|----------|--------------|
| P-BM-01 | Việc tra cứu đề tài/đồ án các khóa trước hiện nay dễ dàng | Likert 1–5 |
| P-BM-02 | Quy trình duyệt đề cương hiện tại rõ ràng, không gây nhầm lẫn | Likert 1–5 |
| P-BM-03 | Việc theo dõi tiến độ sinh viên hiện nay tốn nhiều thời gian thao tác thủ công | Likert 1–5 |
| P-BM-04 | Việc tổng hợp điểm bảo vệ hiện nay dễ xảy ra sai sót | Likert 1–5 |
| P-BM-05 | Kênh trao đổi/quản lý đang dùng nhiều nhất hiện nay | Chọn 1: Email / Zalo / Giấy / Google Drive / Khác |
| P-BM-06 | Công việc nào Bộ môn cho là cần số hóa/ưu tiên nhất | Chọn 1: Đăng ký đề tài / Duyệt đề cương / Theo dõi tiến độ / Xếp hội đồng / Lưu trữ đồ án |
| P-BM-07 | Mức độ hữu ích nếu hệ thống tự cảnh báo trùng lặp tên đề tài và nội dung đề cương/báo cáo | Likert 1–5 |
| P-BM-08 | Ý kiến/đề xuất khác | Mở |

## C.2. Giảng viên

| Mã | Nội dung | Kiểu trả lời |
|----|----------|--------------|
| P-GV-01 | Việc duyệt đề cương/báo cáo bằng giấy hoặc email hiện nay mất nhiều thời gian | Likert 1–5 |
| P-GV-02 | Khó phát hiện đoạn nội dung trùng lặp nếu chỉ đọc thủ công | Likert 1–5 |
| P-GV-03 | Việc trao đổi phản hồi với sinh viên hướng dẫn hiện nay thuận tiện | Likert 1–5 |
| P-GV-04 | Kênh trao đổi đang dùng nhiều nhất với sinh viên | Chọn 1: Email / Zalo / Giấy / Google Drive / Khác |
| P-GV-05 | Định dạng phiếu chấm hội đồng hiện tại rõ ràng, dễ điền | Likert 1–5 |
| P-GV-06 | Mức độ hữu ích nếu hệ thống hiển thị tỷ lệ tương đồng kèm đoạn trùng cụ thể và nguồn trùng | Likert 1–5 |
| P-GV-07 | Thiết bị thường dùng khi làm việc với hệ thống quản lý học tập | Chọn nhiều: Máy tính để bàn / Laptop / Điện thoại |
| P-GV-08 | Ý kiến/đề xuất khác | Mở |

## C.3. Sinh viên

| Mã | Nội dung | Kiểu trả lời |
|----|----------|--------------|
| P-SV-01 | Việc tìm hiểu và đăng ký đề tài hiện nay dễ dàng | Likert 1–5 |
| P-SV-02 | Việc nhận phản hồi đề cương từ GVHD hiện nay nhanh chóng | Likert 1–5 |
| P-SV-03 | Việc tra cứu đồ án các khóa trước hiện nay thuận tiện | Likert 1–5 |
| P-SV-04 | Kênh trao đổi đang dùng nhiều nhất với GVHD | Chọn 1: Email / Zalo / Giấy / Google Drive / Khác |
| P-SV-05 | Muốn xem trước kết quả kiểm tra trùng lặp trước khi nộp chính thức | Chọn 1: Có / Không / Chưa rõ |
| P-SV-06 | Thiết bị thường dùng khi làm việc với hệ thống quản lý học tập | Chọn nhiều: Máy tính để bàn / Laptop / Điện thoại |
| P-SV-07 | Mức độ mong muốn có hệ thống trực tuyến thay thế quy trình giấy/email hiện tại | Likert 1–5 |
| P-SV-08 | Ý kiến/đề xuất khác | Mở |

## Tổng hợp kết quả

Mỗi câu trả lời (một mã phiếu × một mã câu) là một dòng trong bảng tổng hợp dạng long-format tại `mau-tong-hop-phieu-khao-sat.csv`, cột: `ma_phieu,vai_tro,ma_cau,tra_loi,ghi_chu`.
