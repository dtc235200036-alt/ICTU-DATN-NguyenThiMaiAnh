## 3.4. Thiết kế giao diện

> **Mã PI:** 2.3 — **Yêu cầu:** DSGN-04

Các mockup của đồ án là **prototype HTML/CSS tĩnh**, lưu trong `mockup/` (mở trực tiếp `mockup/mh-NN.html` bằng bất kỳ trình duyệt nào); mỗi ảnh PNG đi kèm được chụp ở độ rộng 1440px bằng headless Chrome (`tools/render-diagrams.sh`). Đây là phần thay thế Figma theo quyết định D-11 (sửa 28/09/2026), và là "phần mềm thiết kế tương đương" của tiêu chí PI 2.3. Toàn bộ màn hình được thiết kế sau khi nạp hai skill UI/UX đã cài trong môi trường làm việc: `ui-ux-pro-max` và `design-taste-frontend` (xem ghi chú áp dụng/loại trừ bên dưới).

### 3.4.1. Quy ước giao diện và thành phần

Phong cách chốt theo D-12: **Ant Design admin** — sider tối bên trái, header có breadcrumb, bảng (table) và biểu mẫu (form) là hai loại nội dung chính. Theo D-13, thiết kế **chỉ cho desktop, khung cố định 1440px**; không có phiên bản responsive/mobile.

**Ghi chú áp dụng skill:** `ui-ux-pro-max` cung cấp hướng dẫn chung cho dashboard/form/table (nhãn gắn với input, phản hồi trạng thái submit, xử lý bảng dài) — được áp dụng trực tiếp. `design-taste-frontend` tự khai là **không dành cho dashboard/admin panel** (mục "Out of Scope" của skill khuyến nghị dùng Fluent/Carbon/Atlassian/Polaris cho các giao diện dạng này); vì D-12 đã chốt cứng Ant Design cho toàn bộ Phase 2–4, hướng dẫn về hệ thống thiết kế của skill này bị **override theo D-12** — chỉ áp dụng các nguyên tắc anti-slop trung lập của nó (không icon vẽ tay tùy tiện, không dữ liệu giả kiểu "Jane Doe", nhất quán một họ font/một palette).

| Lớp CSS | Thành phần Ant Design | Dùng ở màn hình |
|---|---|---|
| `ant-layout`, `ant-layout-sider`, `ant-layout-main` | Layout, Sider | Tất cả |
| `ant-layout-header`, `ant-breadcrumb`, `ant-badge`, `ant-header-user` | Layout.Header, Breadcrumb, Badge, Avatar | Tất cả |
| `ant-menu`, `ant-menu-item`, `ant-menu-item-selected` | Menu | Tất cả |
| `ant-card`, `ant-card-title` | Card | Tất cả |
| `ant-form-item`, `ant-input`, `ant-select-selector`, `ant-input-textarea` | Form, Input, Select, Input.TextArea | MH-06, MH-08, MH-09... |
| `ant-btn`, `ant-btn-primary`, `ant-btn-default`, `ant-btn-danger` | Button | Tất cả |
| `ant-tag`, `ant-tag-processing`, `ant-tag-warning`, `ant-tag-success`, `ant-tag-error` | Tag | MH-05, MH-06, MH-07... |
| `ant-alert`, `ant-alert-warning`, `ant-alert-error`, `ant-alert-info` | Alert | MH-06, MH-09, MH-14 |
| `ant-table` | Table | MH-05, MH-06, MH-09, MH-13... |
| `ant-progress` | Progress | MH-06, MH-09, MH-14 |

**Sider menu theo vai trò** (chốt tại đây, kế hoạch 01-06 sao chép nguyên văn):

- **Sinh viên:** Tổng quan · Đề tài của tôi · Đề xuất / Đăng ký đề tài · Đề cương · Báo cáo tiến độ · Bảo vệ · Kho đồ án
- **Giảng viên:** Tổng quan · Đề tài hướng dẫn · Đề xuất đề tài · Duyệt đề cương · Nhận xét tiến độ · Hội đồng bảo vệ · Kho đồ án
- **Bộ môn:** Tổng quan toàn khoa · Quản lý đợt đồ án · Duyệt & phân công đề tài · Duyệt đề cương · Tiến độ toàn khoa · Hội đồng & lịch bảo vệ · Kho đồ án · Cấu hình ngưỡng trùng lặp

### 3.4.2. Danh mục màn hình

| Mã MH | Tên màn hình | Vai trò | UC | Tệp nguồn | Ảnh | Trạng thái |
|---|---|---|---|---|---|---|
| MH-01 | Đăng nhập | Cả 3 vai trò | — | — | — | Chưa dựng |
| MH-02 | Dashboard Sinh viên | Sinh viên | — | — | — | Chưa dựng |
| MH-03 | Dashboard Giảng viên | Giảng viên | — | — | — | Chưa dựng |
| MH-04 | Dashboard Bộ môn (kèm tiến độ toàn khoa) | Bộ môn | — | — | — | Chưa dựng |
| MH-05 | Danh sách đề tài (lọc trạng thái/đợt/GV) | Cả 3 vai trò | UC1.4 | — | — | Chưa dựng |
| MH-06 | Đề xuất / đăng ký đề tài có cảnh báo trùng tên | Giảng viên, Sinh viên | UC1.1, UC0.6 | [mh-06.html](mockup/mh-06.html) | [mh-06.png](mockup/mh-06.png) | Đã dựng |
| MH-07 | Duyệt đề tài và phân công GVHD | Bộ môn | UC1.3 | — | — | Chưa dựng |
| MH-08 | Nộp đề cương (phiên bản, trạng thái kiểm tra) | Sinh viên | UC2 | — | — | Chưa dựng |
| MH-09 | Duyệt đề cương có panel kết quả trùng lặp | Giảng viên | UC2 | — | — | Chưa dựng |
| MH-10 | Báo cáo tiến độ và nhận xét | Sinh viên, Giảng viên | UC3 | — | — | Chưa dựng |
| MH-11 | Lập hội đồng và xếp lịch | Bộ môn | UC4 | — | — | Chưa dựng |
| MH-12 | Chấm điểm bảo vệ | Giảng viên | UC4 | — | — | Chưa dựng |
| MH-13 | Kho đồ án (tìm kiếm, lọc) | Cả 3 vai trò | UC5 | — | — | Chưa dựng |
| MH-14 | Chi tiết kết quả kiểm tra trùng lặp | Giảng viên, Bộ môn | UC0.6 | — | — | Chưa dựng |

### 3.4.8. MH-06 – Đề xuất đề tài

**Vai trò:** Giảng viên, Sinh viên · **UC:** UC1.1, UC0.6 · **FR:** FR-DT-01, FR-DT-02

**Mục đích:** Cho phép người dùng nhập một đề xuất đề tài mới và thấy ngay cảnh báo nếu có đề tài tương tự trong kho, trước khi quyết định sửa tên hay vẫn gửi.

**Vùng (regions):**
- Sider trái: menu điều hướng theo vai trò (mục "Đề xuất / Đăng ký đề tài" đang chọn)
- Header: breadcrumb "Quản lý đề tài / Đề xuất đề tài", chuông thông báo có badge số chưa đọc, tên người dùng
- Nội dung chính: form một cột trong `ant-card` gồm Đợt đồ án, Tên đề tài, cảnh báo trùng lặp (nếu có), Lĩnh vực, Mô tả, và hai nút hành động cuối form

**Trạng thái (states):**
- Chưa nhập đủ trường bắt buộc: nút "Gửi đề xuất" vẫn hiển thị nhưng submit sẽ báo lỗi validate tại từng trường (không hiển thị ở bản tĩnh này)
- Không phát hiện trùng lặp: khối `ant-alert-warning` không xuất hiện, form chỉ còn 4 trường
- Phát hiện trùng lặp (trạng thái được minh họa trong ảnh dưới): hiển thị `ant-alert-warning` với bảng tối đa N đề tài tương tự kèm `ant-progress` tỷ lệ %, và hai nút "Sửa tên đề tài" / "Vẫn gửi đề xuất"

**Tương tác (interactions):**
- "Sửa tên đề tài" đưa focus lại về ô Tên đề tài để người dùng chỉnh sửa (luồng thay thế A1, UC1.1)
- "Vẫn gửi đề xuất" đóng cảnh báo và tiếp tục điền các trường còn lại (luồng thay thế A2, UC1.1)
- "Gửi đề xuất" tạo đề tài trạng thái "Chờ duyệt" (bước TB-DT-06)

![Hình 3.x – MH-06 · Đề xuất đề tài](mockup/mh-06.png)
