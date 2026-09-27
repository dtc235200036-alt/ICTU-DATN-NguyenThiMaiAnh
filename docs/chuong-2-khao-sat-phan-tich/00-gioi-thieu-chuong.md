# CHƯƠNG 2. KHẢO SÁT VÀ PHÂN TÍCH HỆ THỐNG

> **Mã PI:** 1.1, 1.2, 1.3 — **Yêu cầu:** ANLS-01, ANLS-02, ANLS-03, ANLS-04, ANLS-05

Chương này trình bày kết quả khảo sát quy trình quản lý đồ án/khóa luận tốt nghiệp hiện tại của Khoa Công nghệ thông tin (Trường ĐH CNTT&TT Thái Nguyên) và phân tích yêu cầu cho hệ thống mới. Nội dung khảo sát dựa trên phỏng vấn thực tế Bộ môn, Giảng viên, Sinh viên kết hợp tài liệu, quy chế thu thập được (D-01, D-02); những điểm chưa xác nhận được bằng biên bản phỏng vấn hoặc tài liệu gốc được nêu công khai tại §2.1.7 "Giới hạn của khảo sát". Từ khảo sát hiện trạng (AS-IS), chương suy ra quy trình nghiệp vụ trên hệ thống (TO-BE), bảng yêu cầu chức năng/phi chức năng chi tiết, và sơ đồ use case cùng đặc tả từng use case — làm cơ sở cho thiết kế ở Chương 3.

Các mục của chương:

- **2.1. Khảo sát hiện trạng** — quy trình thủ công hiện tại, biểu mẫu đang dùng, vấn đề/hạn chế (VD-\*), phát hiện khảo sát (KS-\*) và giới hạn của khảo sát.
- **2.2. Mô hình hóa quy trình nghiệp vụ** — sơ đồ BPMN AS-IS/TO-BE: 1 sơ đồ tổng quan và 5 quy trình con (Đề tài, Đề cương, Tiến độ, Bảo vệ, Kho dữ liệu đồ án).
- **2.3. Yêu cầu chức năng** — bảng yêu cầu chức năng chi tiết theo module (TK, DT, DC, TD, BV, KHO, TB, AI).
- **2.4. Yêu cầu phi chức năng** — bảng yêu cầu phi chức năng với ngưỡng đo được và phương pháp kiểm tra.
- **2.5. Sơ đồ use case tổng quát** — sơ đồ UC0–UC5 và tác nhân.
- **2.6. Đặc tả use case** — đặc tả chi tiết từng UC con của UC1 (Đề tài), UC2 (Đề cương), UC3 (Tiến độ), UC4 (Bảo vệ), UC5 (Kho dữ liệu đồ án) và UC0 (Chức năng chung).
