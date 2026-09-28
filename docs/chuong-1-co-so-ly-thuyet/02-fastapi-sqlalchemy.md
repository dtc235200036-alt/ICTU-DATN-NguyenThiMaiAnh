## 1.2. Python, FastAPI, Pydantic, SQLAlchemy 2.0 và Alembic

> **Mã PI:** — — **Yêu cầu:** —

### 1.2.1. Python

Python là ngôn ngữ lập trình thông dịch, đa mục đích, cú pháp gần ngôn ngữ tự nhiên và có hệ sinh thái thư viện lớn cho phát triển web, xử lý dữ liệu và học máy. Việc chọn cùng một ngôn ngữ cho cả Web API và Dịch vụ AI (thay vì hai ngôn ngữ khác nhau cho hai thành phần) giảm chi phí chuyển ngữ cảnh khi phát triển và tận dụng trực tiếp hệ sinh thái xử lý ngôn ngữ tự nhiên/học máy vốn tập trung chủ yếu ở Python (`sentence-transformers`, `underthesea`, `faiss`...).

### 1.2.2. FastAPI

FastAPI là một framework xây dựng API bằng Python, chạy trên chuẩn ASGI (Asynchronous Server Gateway Interface) thay vì WSGI truyền thống, cho phép cả xử lý đồng bộ (`def`) lẫn bất đồng bộ (`async def`) trong cùng một ứng dụng. Ba đặc điểm khiến FastAPI phù hợp để xây dựng cả Web API lẫn Dịch vụ AI của hệ thống:

- **Khai báo kiểu dữ liệu bằng type hint của Python:** tham số route, body request và response đều được khai báo qua kiểu dữ liệu chuẩn Python, FastAPI tự động sinh việc kiểm tra hợp lệ (validation), chuyển đổi kiểu và tài liệu OpenAPI (Swagger UI) từ chính khai báo đó — không cần viết tài liệu API tách rời.
- **Tích hợp sẵn Pydantic:** mọi request/response body được mô tả bằng model Pydantic, giúp lỗi dữ liệu sai định dạng bị chặn ngay ở tầng framework trước khi chạm tới logic nghiệp vụ.
- **Cơ chế Dependency Injection (`Depends`):** cho phép khai báo các bước xử lý dùng chung trước một route (xác thực người dùng, kiểm tra vai trò, mở phiên làm việc CSDL) như các hàm độc lập, tái sử dụng được giữa nhiều route mà không lặp code.

Với các endpoint đồng bộ (`def`, không phải `async def`), FastAPI tự động chạy hàm xử lý trong một thread pool riêng, nhờ đó vẫn phục vụ được nhiều request đồng thời mà mã nghiệp vụ không cần viết theo phong cách `async`/`await` — phù hợp khi phần lớn công việc là gọi cơ sở dữ liệu qua driver đồng bộ.

### 1.2.3. Pydantic

Pydantic là thư viện kiểm tra và chuyển đổi dữ liệu (data validation) dựa trên type hint của Python. Một "model" Pydantic khai báo hình dạng dữ liệu mong đợi (tên trường, kiểu, ràng buộc như độ dài chuỗi, giá trị tối thiểu/tối đa); khi dữ liệu đầu vào không khớp, Pydantic sinh lỗi có cấu trúc chỉ rõ trường nào sai và vì sao, thay vì để lỗi kiểu dữ liệu lan sâu vào logic nghiệp vụ rồi mới thất bại khó hiểu ở đâu đó. Vì FastAPI dùng Pydantic làm nền cho khai báo request/response, các model này còn đóng vai trò tài liệu hợp đồng API (DTO — Data Transfer Object) tách bạch với model cơ sở dữ liệu.

### 1.2.4. SQLAlchemy 2.0

SQLAlchemy là thư viện truy cập cơ sở dữ liệu quan hệ cho Python, cung cấp hai tầng: **Core** (xây dựng câu lệnh SQL bằng API Python, gần với SQL thuần) và **ORM** (Object-Relational Mapping — ánh xạ bảng CSDL thành lớp Python, dòng dữ liệu thành đối tượng). Từ phiên bản 2.0, SQLAlchemy chuẩn hóa phong cách khai báo model bằng type hint (`Mapped[...]`, `mapped_column(...)`), giúp một lớp thực thể vừa là định nghĩa schema, vừa là kiểu dữ liệu mà công cụ kiểm tra kiểu tĩnh (type checker) hiểu được — giảm sai sót khi tên cột hoặc kiểu dữ liệu không khớp giữa code Python và schema thật.

### 1.2.5. Alembic

Alembic là công cụ quản lý **di trú (migration)** schema cơ sở dữ liệu cho SQLAlchemy: mỗi thay đổi cấu trúc CSDL (thêm bảng, thêm cột, đổi kiểu dữ liệu) được ghi thành một "phiên bản" (revision) — một file Python độc lập mô tả bước `upgrade()` và `downgrade()` tương ứng. Nhờ đó, lịch sử tiến hóa của schema được lưu vết đầy đủ, có thể áp dụng tuần tự lên một CSDL trống để tái tạo đúng trạng thái hiện tại, và có thể lùi lại khi cần.

### 1.2.6. Áp dụng trong đồ án

Web API của hệ thống dùng FastAPI (`fastapi>=0.141`) với các route đồng bộ (`def`), phối hợp driver MySQL đồng bộ `pymysql` (`DATABASE_URL=mysql+pymysql://...`) — lựa chọn ưu tiên đơn giản, ít khái niệm mới cần xử lý (so với cặp `async def` + `AsyncSession` + driver bất đồng bộ) phù hợp với ràng buộc thời gian 10 tuần của đồ án, trong khi vẫn giữ đúng khả năng phục vụ nhiều request nhờ cơ chế thread pool nêu trên. Cấu hình ứng dụng dùng `pydantic-settings` (`app/core/config.py`) đọc từ biến môi trường theo nguyên tắc 12-factor (không có giá trị mặc định cho bí mật như `JWT_SECRET`, `DATABASE_URL`), và toàn bộ DTO request/response được khai báo dưới `app/schemas/` (ví dụ `common.py`, `documents.py`, `notifications.py`, `outlines.py`) tách bạch với model CSDL dưới `app/models/` (ví dụ `de_cuong.py`, `thong_bao.py`, `trung_lap.py`).

Tầng dữ liệu dùng SQLAlchemy 2.0 (pin cứng `sqlalchemy==2.0.54`, không nâng lên nhánh 2.1 mới phát hành để tránh rủi ro chưa ổn định trong một đồ án có mốc thời gian cố định) theo phong cách khai báo `Mapped[]`/`mapped_column()`, và Alembic (`alembic>=1.20`, thư mục `backend/alembic/versions/`) lưu lại từng bước tiến hóa schema — ví dụ revision `0006_de_cuong_tai_lieu_thong_bao.py` bổ sung các bảng đề cương, tài liệu đồ án và thông báo. Lịch sử các revision này vừa là cơ chế vận hành (tái tạo CSDL demo từ đầu, đồng bộ schema giữa máy phát triển và server triển khai) vừa là bằng chứng quá trình thiết kế CSDL tiến hóa theo từng giai đoạn thi công, hữu ích khi trình bày ở Chương 3–4.
