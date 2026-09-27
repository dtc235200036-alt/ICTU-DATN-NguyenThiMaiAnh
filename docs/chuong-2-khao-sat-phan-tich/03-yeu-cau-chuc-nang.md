## 2.3. Yêu cầu chức năng

> **Mã PI:** 1.2 — **Yêu cầu:** ANLS-03

Bảng dưới đây liệt kê các yêu cầu chức năng chi tiết, nhóm theo module nghiệp vụ. Mỗi hàng có mã (FR-\<module\>-NN), tên chức năng, mô tả chi tiết, tác nhân thực hiện, UC liên quan và nguồn (yêu cầu v1 tương ứng trong `.planning/REQUIREMENTS.md`). Module DT (Quản lý đề tài) được hoàn thiện trong kế hoạch 01-02; các module còn lại (DC, TD, BV, KHO, TB, AI) do plan 01-04 bổ sung.

### 2.3.2. Quản lý đề tài (DT)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-DT-01 | Đề xuất đề tài | Giảng viên hoặc Sinh viên đề xuất đề tài mới gồm tên, mô tả, lĩnh vực; chỉ thực hiện được khi đợt đồ án đang mở | Giảng viên, Sinh viên | UC1.1 | TOPC-01, TOPC-02 |
| FR-DT-02 | Cảnh báo đề tài tương tự khi đề xuất | Khi đề xuất/đăng ký, hệ thống so sánh tên đề tài theo ngữ nghĩa với kho đề tài đã có, trả về top các đề tài tương tự kèm tỷ lệ % tương đồng; chỉ cảnh báo, không chặn gửi; ngưỡng cảnh báo do Bộ môn cấu hình | Hệ thống (Dịch vụ AI) | UC1.1 | AISV-03, AISV-07 |

*(FR-DT-03..07 được bổ sung ở Task 2 của kế hoạch này.)*
