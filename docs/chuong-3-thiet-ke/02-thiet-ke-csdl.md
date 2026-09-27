## 3.2. Thiết kế cơ sở dữ liệu

> **Mã PI:** 2.1 — **Yêu cầu:** DSGN-02

Schema `thesis_core` (Web API) dùng `CHARACTER SET utf8mb4 COLLATE utf8mb4_vietnamese_ci` cho toàn bộ bảng và cột văn bản, đảm bảo lưu trữ, tìm kiếm và sắp xếp đúng tiếng Việt có dấu. Mọi văn bản (tên đề tài, mô tả, họ tên...) được chuẩn hóa Unicode NFC tại mọi biên nhập liệu (API request, import CSV) trước khi ghi vào CSDL, để việc so sánh chuỗi và tra cứu không phụ thuộc vào dạng tổ hợp (NFD) hay dựng sẵn (NFC) của bàn phím nhập.

Schema `thesis_ai` (Dịch vụ AI) là schema riêng, không được mô tả ở đây (xem 03-kien-truc.md, kế hoạch 01-05).

![Hình 3.y – Sơ đồ CSDL (lát cắt UC1.1)](csdl/erd.png)

### Bảng ánh xạ lớp thực thể ↔ bảng CSDL

| Lớp thực thể | Bảng | Ghi chú |
|---|---|---|
| SinhVien | sinh_vien | — |
| GiangVien | giang_vien | — |
| DotDoAn | dot_do_an | — |
| DeTai | de_tai | — |
| KetQuaKiemTraTrungLap | ket_qua_kiem_tra_trung_lap | — |
| ChiTietTrungLap | chi_tiet_trung_lap | — |
