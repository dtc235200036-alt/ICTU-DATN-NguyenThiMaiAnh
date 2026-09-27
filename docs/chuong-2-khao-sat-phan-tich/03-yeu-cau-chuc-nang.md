## 2.3. Yêu cầu chức năng

> **Mã PI:** 1.2 — **Yêu cầu:** ANLS-03

Bảng dưới đây liệt kê các yêu cầu chức năng chi tiết, nhóm theo module nghiệp vụ. Mỗi hàng có mã (FR-\<module\>-NN), tên chức năng, mô tả chi tiết, tác nhân thực hiện, UC liên quan và nguồn (yêu cầu v1 tương ứng trong `.planning/REQUIREMENTS.md`). Module DT (Quản lý đề tài) được hoàn thiện trong kế hoạch 01-02; các module còn lại (DC, TD, BV, KHO, TB, AI) do plan 01-04 bổ sung.

### 2.3.2. Quản lý đề tài (DT)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-DT-01 | Đề xuất đề tài | Giảng viên hoặc Sinh viên đề xuất đề tài mới gồm tên, mô tả, lĩnh vực; chỉ thực hiện được khi đợt đồ án đang mở | Giảng viên, Sinh viên | UC1.1 | TOPC-01, TOPC-02 |
| FR-DT-02 | Cảnh báo đề tài tương tự khi đề xuất | Khi đề xuất/đăng ký, hệ thống so sánh tên đề tài theo ngữ nghĩa với kho đề tài đã có, trả về top các đề tài tương tự kèm tỷ lệ % tương đồng; chỉ cảnh báo, không chặn gửi; ngưỡng cảnh báo do Bộ môn cấu hình | Hệ thống (Dịch vụ AI) | UC1.1 | AISV-03, AISV-07 |
| FR-DT-03 | Đăng ký đề tài GV đã đề xuất và còn trống | Sinh viên chọn một đề tài do Giảng viên đề xuất, đang ở trạng thái đã duyệt/còn trống, để đăng ký | Sinh viên | UC1.2 | TOPC-02 |
| FR-DT-04 | Duyệt hoặc từ chối đề tài kèm lý do | Bộ môn xem đề tài ở trạng thái Chờ duyệt, quyết định duyệt hoặc từ chối; nếu từ chối phải ghi lý do | Bộ môn | UC1.3 | TOPC-03 |
| FR-DT-05 | Phân công GVHD | Khi duyệt một đề tài, Bộ môn phân công Giảng viên hướng dẫn cho đề tài đó | Bộ môn | UC1.3 | TOPC-03 |
| FR-DT-06 | Ràng buộc mỗi SV chỉ một đề tài đang hoạt động và mỗi đề tài chỉ một SV | Hệ thống chặn một Sinh viên có 2 đề tài đang hoạt động và chặn 2 Sinh viên cùng đăng ký một đề tài, kể cả khi hai SV đăng ký cùng lúc (race condition) | Hệ thống | UC1.2 | TOPC-03 |
| FR-DT-07 | Xem danh sách đề tài theo trạng thái, lọc theo đợt và GV | Mọi vai trò xem danh sách đề tài theo trạng thái (Nháp → Chờ duyệt → Đã duyệt/Từ chối → Đã phân công), lọc theo đợt đồ án và theo Giảng viên | Sinh viên, Giảng viên, Bộ môn | UC1.4 | TOPC-04 |
