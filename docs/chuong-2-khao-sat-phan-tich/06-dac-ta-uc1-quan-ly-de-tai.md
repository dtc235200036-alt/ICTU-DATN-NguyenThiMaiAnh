### 2.6.1. Đặc tả UC1 – Quản lý đề tài

> **Mã PI:** 1.3 — **Yêu cầu:** ANLS-05

UC1 – Quản lý đề tài được tách thành 4 UC con để mỗi UC có một luồng nghiệp vụ độc lập, dễ đặc tả và dễ lập trình theo lát cắt: UC1.1 Đề xuất đề tài, UC1.2 Đăng ký đề tài có sẵn, UC1.3 Duyệt đề tài và phân công GVHD, UC1.4 Xem và lọc danh sách đề tài.

![Hình 2.y – Sơ đồ UC1 – Quản lý đề tài](uc/uc1-quan-ly-de-tai.png)

#### UC1.1 – Đề xuất đề tài

| Thuộc tính | Nội dung |
|---|---|
| Mã UC | UC1.1 |
| Tên UC | Đề xuất đề tài |
| Tác nhân | Giảng viên, Sinh viên |
| Mô tả | Giảng viên hoặc Sinh viên nhập một đề tài mới (tên, mô tả, lĩnh vực) vào đợt đồ án đang mở. Hệ thống kiểm tra trùng lặp tên đề tài theo ngữ nghĩa (bao gồm UC0.6) trước khi ghi nhận. |
| Tiền điều kiện | Người dùng đã đăng nhập với vai trò Giảng viên hoặc Sinh viên; có ít nhất một đợt đồ án đang ở trạng thái "đang mở" |
| Hậu điều kiện | Đề tài mới được tạo với trạng thái "Chờ duyệt"; nếu có đề tài tương tự vượt ngưỡng, danh sách tương tự đã được hiển thị cho người đề xuất trước khi gửi |
| Yêu cầu liên quan | FR-DT-01, FR-DT-02 |
| Màn hình | MH-06 |

**Luồng sự kiện chính**

1. Người dùng (GV hoặc SV) chọn "Đề xuất đề tài" trên màn hình MH-06.
2. Người dùng nhập tên đề tài, mô tả, lĩnh vực và chọn đợt đồ án đang mở.
3. Hệ thống gọi UC0.6 (Kiểm tra trùng lặp tên đề tài) để so sánh ngữ nghĩa tên đề tài vừa nhập với kho đề tài đã có.
4. Nếu không có đề tài nào vượt ngưỡng tương đồng: hệ thống chuyển sang bước 6.
5. Nếu có đề tài tương tự vượt ngưỡng: hệ thống hiển thị danh sách tối đa N đề tài tương tự kèm tỷ lệ % tương đồng (MH-06).
6. Hệ thống ghi nhận đề tài mới với trạng thái "Chờ duyệt" và thông báo thành công cho người dùng.

**Luồng thay thế**

- **A1** (rẽ nhánh từ bước 5): Người đề xuất xem danh sách đề tài tương tự, chỉnh sửa lại tên đề tài, hệ thống quay lại bước 3 để kiểm tra lại.
- **A2** (rẽ nhánh từ bước 5): Người đề xuất xác nhận vẫn muốn gửi dù có cảnh báo trùng lặp; hệ thống tiếp tục bước 6 và ghi chú lại rằng đề tài đã được gửi kèm cảnh báo.

**Ngoại lệ**

- **E1**: Đợt đồ án đã đóng tại thời điểm gửi → hệ thống từ chối và thông báo lý do, không tạo đề tài.
- **E2**: Dịch vụ AI (UC0.6) không phản hồi trong thời gian quy định (NFR ANLS-04) → hệ thống vẫn cho phép gửi đề tài, ghi nhận trạng thái kiểm tra là "chưa kiểm tra" để Bộ môn biết khi duyệt (UC1.3, Task 2).

*(UC1.2, UC1.3, UC1.4 được đặc tả ở Task 2 của kế hoạch này.)*
