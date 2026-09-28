# Nhật ký tập dượt demo tự động

- Kịch bản: `tools/demo/kich-ban-demo.json` (B01…B16, 5 UC × 3 vai trò)
- Lệnh: `bash deploy/demo-state.sh && python3 tools/demo/chay-kich-ban.py tools/demo/kich-ban-demo.json --out-dir /tmp/ntma-tap-duot --log docs/chuong-4-trien-khai/ket-qua-kiem-thu/tap-duot-demo.md && bash deploy/demo-state.sh`
- "Thời gian (s)" là thời gian máy chạy (Chrome headless 1440×900 qua Apache HTTPS, gồm cả đăng nhập khi đổi vai trò), không gồm lời trình bày. Mỗi lần chạy thêm một mục bên dưới (do `chay-kich-ban.py --log` ghi).
- Tập dượt của người trình bày trên hệ thống thật: chưa thực hiện (bước con người).

### Lần chạy 2026-09-28T11:45:34Z — Kịch bản demo bảo vệ — 5 UC × 3 vai trò (bản chạy tự động)

- Kịch bản: `tools/demo/kich-ban-demo.json` · URL: `https://localhost` · khung nhìn 1440x900
- Kết quả: **OK** — 16/16 bước OK, tổng 71.6 s

| Bước | Mô tả | Thời gian (s) | Kết quả |
|---|---|---:|---|
| B01 | Bộ môn mở Tổng quan toàn khoa | 4.4 | OK |
| B02 | SV 011 đề xuất đề tài bằng tên diễn đạt lại một đồ án trong kho | 5.0 | OK |
| B03 | SV 011 chọn Vẫn gửi đề xuất và gửi | 2.5 | OK |
| B04 | Bộ môn duyệt đề tài của 011 và phân công GV011 | 5.7 | OK |
| B05 | SV 011 nộp đề cương P03-B.pdf (chép nguyên văn) — Đang kiểm tra rồi Hoàn tất, mở kết quả | 9.2 | OK |
| B06 | GV011 mở đề cương chờ duyệt của 012 — khung kết quả trùng lặp | 4.5 | OK |
| B07 | GV011 xem chi tiết — đoạn nộp cạnh đoạn nguồn, cụm trùng tô sáng | 2.2 | OK |
| B08 | GV011 yêu cầu 012 sửa đề cương kèm nhận xét | 2.8 | OK |
| B09 | SV 013 xem báo cáo tiến độ theo mốc | 4.2 | OK |
| B10 | GV011 nhận xét báo cáo mốc 2 của 013 | 4.9 | OK |
| B11 | GV014 (ủy viên Hội đồng demo K22) chấm điểm SV 014 | 4.9 | OK |
| B12 | Bộ môn chốt kết quả bảo vệ của 014 — tự lưu kho | 5.2 | OK |
| B13 | Bộ môn tìm đồ án vừa lưu kho theo từ khóa + khóa K22; mở hộp thoại import khóa cũ | 4.6 | OK |
| B14 | Bộ môn xem cấu hình ngưỡng trùng lặp (chỉ xem, không lưu) | 2.1 | OK |
| B15 | Bảo mật: SV 013 mở trang của Bộ môn -> 403; http:// tự chuyển sang https:// | 4.9 | OK |
| B16 | Kết: Bộ môn quay lại Tổng quan — số liệu đã cập nhật sau buổi demo | 4.3 | OK |
