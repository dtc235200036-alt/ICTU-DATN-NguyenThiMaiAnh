## 1.4. React, TypeScript, Vite, Ant Design và TanStack Query

> **Mã PI:** — — **Yêu cầu:** —

### 1.4.1. React

React là thư viện JavaScript xây dựng giao diện người dùng theo mô hình **hướng component**: giao diện được chia thành các thành phần (component) độc lập, mỗi component nhận dữ liệu đầu vào (`props`) và tự quản lý trạng thái nội bộ (`state`), tự render lại khi dữ liệu thay đổi. React dùng cơ chế **Virtual DOM** — một cây đối tượng JavaScript đại diện cho giao diện — để tính toán phần khác biệt tối thiểu cần cập nhật trên DOM thật mỗi khi state thay đổi, thay vì vẽ lại toàn bộ trang. Từ phiên bản 16.8, React bổ sung **Hooks** (`useState`, `useEffect`, `useContext`...), cho phép component dạng hàm (function component) quản lý trạng thái và vòng đời mà trước đó chỉ component dạng lớp (class component) làm được — đây là phong cách viết React hiện tại.

### 1.4.2. TypeScript

TypeScript là một superset của JavaScript bổ sung hệ thống kiểu tĩnh (static typing): kiểu dữ liệu của biến, tham số hàm, giá trị trả về được khai báo (hoặc suy luận) và kiểm tra ngay lúc biên dịch, trước khi mã chạy. Lợi ích chính trong một dự án có nhiều thành phần giao tiếp qua API là bắt được lỗi sai kiểu dữ liệu (ví dụ đọc nhầm tên trường, truyền sai kiểu số/chuỗi) ngay khi viết code thay vì chỉ phát hiện khi chạy thử, đặc biệt hữu ích khi kiểu dữ liệu phía client cần khớp chính xác với schema Pydantic phía Web API.

### 1.4.3. Vite

Vite là công cụ dựng dự án và build (bundler) cho ứng dụng JavaScript/TypeScript hiện đại, dùng ES Modules (ESM) gốc của trình duyệt trong lúc phát triển thay vì đóng gói toàn bộ mã trước khi phục vụ, nhờ đó máy chủ phát triển khởi động gần như tức thời và cập nhật giao diện khi sửa code (Hot Module Replacement) rất nhanh dù dự án lớn. Khi build cho production, Vite dùng Rollup để đóng gói và tối ưu (rút gọn code, chia nhỏ theo route) thành các file tĩnh HTML/CSS/JS có thể phục vụ trực tiếp từ một web server tĩnh.

### 1.4.4. Ant Design

Ant Design (`antd`) là bộ thư viện component giao diện cho React theo ngôn ngữ thiết kế (design language) hướng ứng dụng doanh nghiệp/quản trị nội bộ: cung cấp sẵn các component phức tạp thường gặp ở màn hình quản trị dữ liệu — bảng có sắp xếp/lọc/phân trang (`Table`), biểu mẫu có kiểm tra hợp lệ tích hợp (`Form`), hộp thoại, thông báo, điều hướng menu theo vai trò — với hành vi và giao diện nhất quán sẵn có, giảm đáng kể công sức tự xây dựng và tự thiết kế những thành phần này từ đầu.

### 1.4.5. TanStack Query

TanStack Query (trước đây gọi là React Query) là thư viện quản lý **server state** — tức phần dữ liệu có nguồn gốc từ server (kết quả gọi API) — tách bạch khỏi state thuần túy trên client (ví dụ trạng thái mở/đóng một hộp thoại). Thư viện tự động lo việc cache kết quả gọi API, tự làm mới dữ liệu (refetch) khi cần, gộp các yêu cầu tải trùng lặp thành một, quản lý trạng thái đang tải/lỗi, và tự động vô hiệu hóa (invalidate) cache liên quan sau một thao tác ghi (mutation) — thay cho cách viết tay `useEffect` kết hợp `fetch` vốn dễ dẫn tới lỗi trùng lặp gọi API, không đồng bộ dữ liệu giữa các màn hình, hoặc quên xử lý trạng thái lỗi.

### 1.4.6. Áp dụng trong đồ án

Client Web của hệ thống là một SPA (Single-Page Application) xây dựng bằng React 18 + TypeScript, dựng bằng Vite (`frontend/`), build ra thư mục tĩnh được Apache phục vụ trực tiếp từ `DocumentRoot` (không proxy qua uvicorn) — đúng khuyến nghị chỉ những gì thực sự cần xử lý động (`/api/*`) mới đi qua Web API. Giao diện dùng Ant Design (`antd` 5.x) cho toàn bộ màn hình quản trị dữ liệu của ba vai trò (Sinh viên, Giảng viên, Bộ môn) — bảng danh sách đề tài/đề cương có lọc/phân trang, biểu mẫu nộp đề cương/báo cáo, lịch hội đồng bảo vệ — lựa chọn phù hợp cho khối lượng màn hình CRUD lớn cần hoàn thành trong 10 tuần. Trạng thái dữ liệu từ Web API (danh sách đề tài, kết quả kiểm tra trùng lặp, thông báo...) được quản lý bằng TanStack Query, gọi qua `axios` (chọn thay vì `fetch` thuần nhờ interceptor gắn tự động JWT bearer token vào mọi request và xử lý tập trung khi gặp lỗi `401`); phần state thuần client (token hiện tại, thông tin phiên đăng nhập) dùng Zustand — thư viện quản lý state nhẹ, tránh trùng lặp với state đã do TanStack Query quản lý. Điều hướng giữa các cây route theo vai trò dùng React Router.

Trước khi có bản React thật, các màn hình chính được dựng trước dưới dạng **prototype HTML/CSS tĩnh** (`docs/chuong-3-thiet-ke/mockup/mh-NN.html`), dùng đúng tên class CSS theo quy ước component Ant Design (`ant-btn`, `ant-table`, `ant-alert`...) và chung một stylesheet `antd-admin.css` — cách làm này thay thế công cụ thiết kế Figma (không có license/tài khoản phù hợp trong phạm vi đồ án) nhưng vẫn đảm bảo mục tiêu của một bản mockup: cho thấy đúng bố cục, luồng thao tác và tên thành phần giao diện, đồng thời map 1:1 sang component React thật ở giai đoạn thi công nhờ tên class trùng khớp.
