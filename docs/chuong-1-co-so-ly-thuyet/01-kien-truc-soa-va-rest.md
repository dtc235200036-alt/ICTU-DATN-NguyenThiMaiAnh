## 1.1. Kiến trúc hướng dịch vụ (SOA), RESTful API, JWT và RBAC

> **Mã PI:** — — **Yêu cầu:** —

### 1.1.1. Kiến trúc hướng dịch vụ (SOA)

Kiến trúc hướng dịch vụ (Service-Oriented Architecture — SOA) là một phong cách kiến trúc phần mềm trong đó hệ thống được chia thành nhiều **dịch vụ (service)** độc lập, mỗi dịch vụ đóng gói một nhóm chức năng nghiệp vụ nhất định, sở hữu dữ liệu của riêng mình và chỉ giao tiếp với các dịch vụ khác thông qua một **giao diện (interface)** đã được công bố rõ ràng — thường là các API dựa trên giao thức mạng chuẩn (HTTP/REST, SOAP...). Ba đặc trưng phân biệt SOA với một ứng dụng đơn khối (monolith) chia thư mục theo module là:

- **Ranh giới triển khai độc lập:** mỗi dịch vụ có thể được xây dựng, kiểm thử, đóng gói và triển khai (deploy) riêng, không nhất thiết cùng một tiến trình hay cùng một lần phát hành.
- **Sở hữu dữ liệu riêng (data ownership):** mỗi dịch vụ có cơ sở dữ liệu hoặc schema riêng; dịch vụ khác không được truy cập trực tiếp vào dữ liệu đó, chỉ có thể lấy được thông qua API do dịch vụ sở hữu cung cấp.
- **Giao tiếp qua hợp đồng (contract) tường minh:** các dịch vụ không gọi hàm nội bộ lẫn nhau mà trao đổi qua một giao diện mạng có định dạng dữ liệu, phương thức và mã lỗi được định nghĩa trước, giúp một dịch vụ có thể thay đổi cách cài đặt bên trong mà không phá vỡ các dịch vụ gọi đến nó, miễn là hợp đồng giao tiếp không đổi.

Việc tách dịch vụ mang lại lợi ích về khả năng mở rộng độc lập (scale riêng từng thành phần theo tải), khả năng thay thế công nghệ bên trong một dịch vụ mà không ảnh hưởng dịch vụ khác, và ranh giới bảo mật rõ ràng (một dịch vụ bị xâm nhập không tự động lộ toàn bộ dữ liệu hệ thống). Đánh đổi của SOA so với một khối đơn là độ phức tạp vận hành cao hơn (nhiều tiến trình, nhiều điểm lỗi mạng có thể xảy ra hơn) và cần cơ chế xử lý khi một dịch vụ tạm thời không phản hồi.

### 1.1.2. RESTful API

REST (Representational State Transfer) là một phong cách kiến trúc cho API dựa trên giao thức HTTP, được Roy Fielding trình bày lần đầu trong luận án tiến sĩ năm 2000. Một API được gọi là RESTful khi tuân theo các ràng buộc chính:

- **Hướng tài nguyên (resource-oriented):** mỗi thực thể nghiệp vụ (đề tài, đề cương, tài khoản...) được biểu diễn như một tài nguyên có định danh (URI) riêng, ví dụ `/api/de-tai/{id}`.
- **Dùng đúng ngữ nghĩa của phương thức HTTP:** `GET` để đọc (không gây tác dụng phụ), `POST` để tạo mới, `PUT`/`PATCH` để cập nhật, `DELETE` để xóa; mã trạng thái HTTP (200, 201, 202, 400, 401, 403, 404...) phản ánh đúng kết quả xử lý.
- **Không trạng thái (stateless):** server không lưu trạng thái phiên làm việc giữa các request; mọi thông tin cần thiết để xử lý một request (bao gồm thông tin xác thực) phải được gửi kèm trong chính request đó — đây là lý do REST API thường dùng token (JWT) thay vì session lưu ở server.
- **Định dạng dữ liệu trao đổi thống nhất:** thường là JSON, có cấu trúc nhất quán cho toàn bộ API.

### 1.1.3. Xác thực bằng JSON Web Token (JWT)

JWT (JSON Web Token, RFC 7519) là một định dạng token nhỏ gọn, tự chứa (self-contained), gồm ba phần phân tách bởi dấu chấm: `header.payload.signature`. Phần `header` khai báo thuật toán ký; phần `payload` chứa các **claim** (khẳng định) — ví dụ định danh người dùng, vai trò, thời điểm phát hành (`iat`), thời điểm hết hạn (`exp`); phần `signature` là chữ ký số (HMAC hoặc bất đối xứng) trên hai phần trước, cho phép server xác minh token chưa bị chỉnh sửa mà không cần tra cứu lại một kho lưu trạng thái phiên. Vì bản thân token đã mang đủ thông tin cần thiết và được ký số, JWT phù hợp tự nhiên với nguyên tắc "không trạng thái" của REST: mỗi request chỉ cần đính kèm token trong header `Authorization: Bearer <token>`, server xác minh chữ ký và đọc claim để biết ai đang gọi và với vai trò gì, không cần một bảng phiên tập trung.

### 1.1.4. Kiểm soát truy cập theo vai trò (RBAC)

RBAC (Role-Based Access Control) là mô hình phân quyền trong đó quyền hạn không được gán trực tiếp cho từng người dùng mà được gán cho **vai trò (role)**; mỗi người dùng được gán một hoặc nhiều vai trò và thừa hưởng toàn bộ quyền của vai trò đó. Mô hình này đơn giản hóa việc quản trị quyền khi số vai trò cố định và ít thay đổi hơn nhiều so với số người dùng — chỉ cần định nghĩa quyền theo vai trò một lần, thêm người dùng mới chỉ là gán vai trò có sẵn. Trong REST API xác thực bằng JWT, cách triển khai phổ biến là nhúng vai trò như một claim trong token; mỗi endpoint tự khai báo vai trò nào được phép gọi, và một lớp kiểm tra trung gian (middleware/dependency) so khớp claim vai trò trong token với danh sách vai trò được phép trước khi cho request đi tiếp vào logic nghiệp vụ.

### 1.1.5. Áp dụng trong đồ án

Hệ thống được chia thành đúng ba thành phần triển khai độc lập theo đúng nghĩa SOA ở trên (không phải một khối chia thư mục): client React (SPA build tĩnh, chỉ gọi Web API), Web API (FastAPI, sở hữu schema `thesis_core` và toàn bộ 5 UC nghiệp vụ chính), và Dịch vụ AI kiểm tra trùng lặp (FastAPI riêng, sở hữu schema `thesis_ai`, không có route công khai qua Apache). Ranh giới sở hữu dữ liệu được giữ nghiêm ngặt: hai schema tách biệt, không khóa ngoại băng qua schema; Dịch vụ AI không bao giờ đọc trực tiếp `thesis_core` mà nhận dữ liệu qua endpoint `/ingest` do Web API chủ động đẩy sang (mẫu "push-on-write"), đúng tinh thần "giao tiếp qua hợp đồng tường minh" của SOA.

API giữa các thành phần là RESTful JSON: Web API công bố các nhóm route theo UC (`topics`, `outlines`, `progress`, `defense`, `archive`...), Dịch vụ AI công bố hợp đồng `/ingest`, `/check-title`, `/check-document`, `/reindex`, `/health`. Xác thực người dùng cuối (Sinh viên/Giảng viên/Bộ môn) dùng JWT do Web API phát hành (`app/core/security.py`): access token và refresh token riêng, claim `sub` (id tài khoản), `vai_tro`, `typ` (loại token), `tv` (`token_version` — tăng lên khi đăng xuất để vô hiệu hóa mọi token cũ ngay cả khi chưa hết hạn) và `exp`. Giao tiếp Web API → Dịch vụ AI **không** dùng lại JWT người dùng mà dùng một khóa API nội bộ tĩnh (header `X-API-Key`) — đúng khuyến nghị không nên chuyển tiếp JWT người dùng sang một dịch vụ không có khái niệm người dùng/vai trò, để giảm bán kính ảnh hưởng nếu khóa nội bộ bị lộ.

RBAC được cài đặt với đúng ba vai trò cố định theo đề cương — `SINH_VIEN`, `GIANG_VIEN`, `BO_MON` (lưu trong cột `vai_tro` kiểu ENUM của bảng `tai_khoan`) — thông qua dependency `require_role(*roles)` của FastAPI (`app/core/deps.py`), kết hợp với `get_current_user` để mỗi route tự khai báo vai trò được phép, ví dụ `Depends(require_role(VaiTro.BO_MON))` cho các endpoint chỉ Bộ môn được gọi (duyệt phân công, cấu hình ngưỡng cảnh báo trùng lặp). Cách tiếp cận RBAC bằng dependency nhỏ, tự viết được chọn thay vì một framework quản lý người dùng đầy đủ (như `fastapi-users`) vì hệ thống chỉ có ba vai trò cố định gắn với một quy trình nghiệp vụ cố định — framework tổng quát sẽ tốn công học/điều chỉnh hơn là lợi ích mang lại ở quy mô đồ án này.
