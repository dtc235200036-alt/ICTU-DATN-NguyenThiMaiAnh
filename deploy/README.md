# Triển khai NTMA (Hệ thống quản lý đồ án — Khoa CNTT)

## Yêu cầu

- Docker + Docker Compose v2
- `openssl` (dùng để sinh chứng chỉ TLS tự ký — `mkcert` sẽ được ưu tiên nếu có trên PATH)
- Node.js 20 và `uv` (Python) — chỉ cần cho phát triển và chạy test trên máy host, không cần để chạy stack qua Docker

## Chạy lần đầu

```bash
bash deploy/init.sh
docker compose -f deploy/docker-compose.yml up -d --build --wait
```

Mở `https://localhost` và chấp nhận cảnh báo chứng chỉ tự ký của trình duyệt (chỉ xảy ra một lần cho mỗi trình duyệt).

## Tài khoản demo

Tài khoản Bộ môn được seed tự động khi container `api` khởi động lần đầu (idempotent):

- Mã đăng nhập: `bomon`
- Email: `bomon@ictu.edu.vn`
- Mật khẩu: giá trị biến môi trường `SEED_DEFAULT_PASSWORD` (mặc định `DoAn@2026` — **chỉ dùng cho dev/demo**, đổi giá trị này trước khi đưa lên môi trường thật).

## Thời hạn token (chờ xác nhận GVHD — xem ghi chú NFR-03)

- `ACCESS_TOKEN_EXPIRE_MINUTES` (mặc định 30 phút)
- `REFRESH_TOKEN_EXPIRE_MINUTES` (mặc định 480 phút — độ dài phiên làm việc)

Hai giá trị này đọc từ `deploy/.env` (sinh bởi `deploy/init.sh`), có thể chỉnh trực tiếp trong file đó trước khi `docker compose up`.

## Chạy test

```bash
docker compose -f deploy/docker-compose.yml up -d --wait mysql
uv --directory backend run pytest -q
```

Test pytest chạy trực tiếp trên máy host, kết nối tới MySQL của compose qua cổng host (`MYSQL_HOST_PORT`, mặc định 3307), dùng schema `thesis_core_test` riêng.

## Script hỗ trợ (`deploy/`)

| Script | Mục đích |
|---|---|
| `sql.sh "<SQL>"` | Chạy một câu SQL trong container `mysql` (`DB=thesis_core_test bash deploy/sql.sh "..."` để đổi schema) |
| `api-login.sh <dang_nhap>` | In ra access_token cho một tài khoản, dùng mật khẩu seed mặc định |
| `dom-check.sh <path> <text>` | Kiểm tra DOM đã render (headless Chrome) qua HTTPS chứa một chuỗi mong đợi |
| `smoke-test.sh` | Bộ kiểm tra qua Apache HTTPS (redirect, health, SPA fallback, header bảo mật, đăng nhập, giới hạn kích thước request, phiên/refresh/logout, throttle đăng nhập) |
| `tools/check-erd-db.py` | Đối chiếu tên cột giữa `docs/chuong-3-thiet-ke/csdl/erd.puml` và schema `thesis_core` thật |

## Reset toàn bộ

```bash
docker compose -f deploy/docker-compose.yml down -v
```

Lệnh này xóa cả volume `mysql-data` — lần khởi động sau sẽ tạo lại schema và seed dữ liệu từ đầu.

## Ghi chú kiến trúc triển khai

- Container `api` không publish cổng ra host — chỉ Apache (`apache` service) mới có thể gọi tới `api:8001` qua mạng nội bộ của compose.
- Dịch vụ AI (Phase 4) sẽ không có route Apache nào trỏ tới — kiến trúc SOA giữ Dịch vụ AI hoàn toàn nội bộ (§3.3.1).
