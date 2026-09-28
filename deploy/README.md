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

`python -m app.seed` (DATA-01) chạy tự động mỗi lần container `api` khởi động
(`SEED_ON_START=true`) và là **idempotent** — chạy lại không tạo trùng, không
đổi dữ liệu tài khoản/đợt đồ án đã tồn tại. Có thể chạy lại thủ công:

```bash
docker compose -f deploy/docker-compose.yml exec -T api python -m app.seed
```

Đăng nhập bằng **mã hoặc email**, cùng một mật khẩu dev-only cho mọi tài khoản:

| Vai trò | Mã đăng nhập | Email | Mật khẩu |
|---|---|---|---|
| Bộ môn | `bomon` | `bomon@ictu.edu.vn` | `SEED_DEFAULT_PASSWORD` (mặc định `DoAn@2026`) |
| Giảng viên | `GV001` .. `GV030` | `gv001@ictu.edu.vn` .. `gv030@ictu.edu.vn` | như trên |
| Sinh viên | `DTC225200001` .. `DTC225200100` | `dtc225200001@ictu.edu.vn` .. `dtc225200100@ictu.edu.vn` | như trên |

**Chỉ dùng cho dev/demo** — đổi `SEED_DEFAULT_PASSWORD` trước khi đưa lên môi
trường thật (Phase 5).

Seed cũng tạo sẵn một đợt đồ án đang mở, **"Đợt đồ án tốt nghiệp K22 - HK1
(2026-2027)"** (khóa K22), dùng ngay cho demo UC1 (đề xuất/đăng ký đề tài) mà
không cần Bộ môn mở đợt thủ công trước.

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

## Kịch bản demo UC1 (thao tác trên trình duyệt)

Mở `https://localhost`, chấp nhận cảnh báo chứng chỉ tự ký, rồi thực hiện tuần
tự (ROADMAP Phase 2, SC1–SC5):

1. **Đăng nhập bằng mã hoặc email:** đăng nhập bằng `bomon` (mã) rồi đăng
   nhập lại bằng `bomon@ictu.edu.vn` (email) — cùng vào được. Tải lại trang
   (F5) — vẫn còn phiên đăng nhập (refresh token cookie).
2. **Khóa/mở tài khoản (Bộ môn):** vào "Quản lý tài khoản" (`/tai-khoan`),
   khóa một tài khoản SV (ví dụ `DTC225200002`), thử đăng nhập bằng tài khoản
   đó ở cửa sổ ẩn danh → bị từ chối; mở khóa lại.
3. **Mở/đóng đợt đồ án (Bộ môn):** vào "Quản lý đợt đồ án", đóng đợt "Đợt đồ
   án tốt nghiệp K22 - HK1 (2026-2027)", xác nhận GV/SV không đề xuất/đăng ký
   được đề tài mới trong đợt đã đóng; mở lại đợt trước khi tiếp tục demo.
4. **GV đề xuất đề tài:** đăng nhập `GV001`, vào "Đề xuất đề tài", nhập một
   tên đề tài gần giống đề tài đã có trong kho — quan sát cảnh báo "N đề tài
   tương tự" trước khi gửi; gửi đề xuất → đề tài ở trạng thái "Chờ duyệt".
5. **SV tự đề xuất và đăng ký:** đăng nhập `DTC225200002`, tự đề xuất một đề
   tài mới; ở một tài khoản SV khác chưa có đề tài, vào "Danh sách đề tài",
   lọc đề tài "Đã duyệt" còn trống do GV đề xuất và bấm "Đăng ký".
6. **Bộ môn duyệt / phân công / từ chối (MH-07):** đăng nhập `bomon`, vào
   "Duyệt & phân công đề tài" (`/duyet-de-tai`); mở đề tài GV đề xuất chưa có
   SV → "Duyệt"; mở đề tài đã có SV đăng ký → chọn Giảng viên hướng dẫn rồi
   "Duyệt và phân công"; mở một đề tài khác → "Từ chối" kèm lý do.
7. **SV xem lý do từ chối:** đăng nhập lại tài khoản SV bị từ chối ở bước 6,
   mở chi tiết đề tài, xác nhận thấy đúng lý do từ chối.
8. **Danh sách lọc theo đợt/trạng thái/GVHD:** ở "Danh sách đề tài" (mọi vai
   trò), lọc theo Đợt đồ án, Trạng thái và Giảng viên hướng dẫn — bảng chỉ
   còn đúng các đề tài khớp bộ lọc.
9. **403 khi gọi sai vai trò:** đăng nhập SV, thử mở trực tiếp URL
   `/tai-khoan` hoặc `/duyet-de-tai` — nhận trang 403 "Bạn không có quyền
   truy cập trang này".
10. **Dashboard theo vai trò:** đăng nhập lần lượt `DTC225200001`, `GV001` và
    `bomon`, mở "Tổng quan" — mỗi vai trò thấy đúng widget của mình (SV: đề
    tài của tôi; GV: sinh viên hướng dẫn + đề tài chờ duyệt + bảng đề tài
    hướng dẫn; Bộ môn: đề tài chờ duyệt + SV chưa có đề tài + đề tài đã phân
    công + danh sách chờ duyệt mới nhất).

## Kiểm thử tự động

```bash
uv --directory backend run pytest -q
bash deploy/smoke-test.sh
bash deploy/e2e-uc1.sh
python3 tools/check-erd-db.py
```

`deploy/e2e-uc1.sh` tự dựng riêng một đợt đồ án khóa **K99** và dùng 3 tài
khoản seed dành riêng cho kịch bản tự động (tách biệt với các tài khoản dùng ở
demo thủ công phía trên): `GV030` (đề xuất đề tài), `DTC225200099` (tự đề
xuất đề tài, sau đó bị từ chối) và `DTC225200100` (đăng ký đề tài GV đã
duyệt). Script tự xóa toàn bộ dữ liệu nó tạo ra (đợt K99 + đề tài + kết quả
kiểm tra trùng lặp) khi kết thúc, kể cả khi có bước thất bại giữa chừng.

Widget đề cương/tiến độ/hội đồng/thông báo trên các dashboard (MH-02/03/04)
sẽ được bổ sung ở Phase 3 khi các UC tương ứng có dữ liệu thật.

## Ghi chú kiến trúc triển khai

- Container `api` không publish cổng ra host — chỉ Apache (`apache` service) mới có thể gọi tới `api:8001` qua mạng nội bộ của compose.
- Dịch vụ AI (Phase 4) sẽ không có route Apache nào trỏ tới — kiến trúc SOA giữ Dịch vụ AI hoàn toàn nội bộ (§3.3.1).
