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
| `smoke-test.sh` | Bộ kiểm tra qua Apache HTTPS (redirect, health, SPA fallback, header bảo mật, đăng nhập, giới hạn kích thước request, phiên/refresh/logout, throttle đăng nhập, 403 chéo vai trò trên route Phase 2–3) |
| `e2e-uc1.sh` / `e2e-uc2-5.sh` | Kịch bản end-to-end UC1 và UC2–UC5 qua Apache (xem "Kiểm thử tự động") |
| `tools/check-erd-db.py` | Đối chiếu tên cột giữa `docs/chuong-3-thiet-ke/csdl/erd.puml` và schema `thesis_core` thật |

## Reset toàn bộ

```bash
docker compose -f deploy/docker-compose.yml down -v
```

Lệnh này xóa cả volume `mysql-data` **và** `uploads-data` (file đề cương/báo cáo đã nộp) — lần khởi động sau sẽ tạo lại schema và seed dữ liệu từ đầu. Muốn giữ file tải lên, sao lưu trước theo mục "File tải lên" bên dưới.

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

## Kịch bản demo UC2–UC5 (thao tác trên trình duyệt)

Tiếp nối kịch bản UC1: cần một SV có đề tài **Đã phân công** (ví dụ bước 5–6
ở trên: `DTC225200002` tự đề xuất, `bomon` "Duyệt và phân công" cho `GV001`).
Thứ tự theo D-09: đề cương → bảo vệ → lưu kho → tiến độ; chuông thông báo
(góc phải Header) được kiểm tra ở mọi bước. Dùng các tài khoản `DTC2252000xx`
/ `GV0xx` thông thường — **không** dùng các tài khoản dành riêng cho e2e
(xem mục "Kiểm thử tự động").

1. **Thông báo phân công (NOTF-01):** ngay sau khi `bomon` duyệt và phân công,
   đăng nhập `DTC225200002` và (cửa sổ ẩn danh) `GV001` — trong tối đa 30 giây
   chuông hiện số chưa đọc; mở chuông thấy "Đề tài '…' đã được duyệt — GVHD: …"
   (SV) và "Bạn được phân công hướng dẫn …" (GV); bấm vào thông báo → mở chi
   tiết đề tài, số trên chuông giảm 1.
2. **SV nộp đề cương (MH-08, OUTL-01):** `DTC225200002` → "Đề cương" → chọn
   file DOCX/PDF (≤ 20 MB) → "Nộp phiên bản mới". Panel kiểm tra trùng lặp chuyển
   "Đang kiểm tra" → "Hoàn tất"; bấm "Xem chi tiết" mở MH-14
   (`/kiem-tra-trung-lap/…`). GVHD nhận thông báo "đề cương mới".
3. **GVHD yêu cầu sửa (MH-09, OUTL-02):** `GV001` → "Duyệt đề cương" → mở đề
   cương → nhập nhận xét → "Yêu cầu sửa". SV nhận thông báo; trang Đề cương của
   SV hiện "Yêu cầu sửa" kèm nhận xét.
4. **SV nộp lại → GVHD duyệt:** SV nộp phiên bản 2 (lịch sử giữ cả v1, v2);
   GVHD "Duyệt" → SV nhận thông báo "đề cương đã được duyệt". Dashboard SV
   ("Tổng quan") hiện "Phiên bản mới nhất: v2 · nộp …", tag "Đã duyệt" và
   "Tỷ lệ trùng lặp gần nhất".
5. **SV nộp báo cáo cuối (UC4.1):** "Đề cương" → tab "Báo cáo cuối" → nộp
   PDF/DOCX → "Nộp báo cáo cuối" (chỉ mở khi đề cương đã duyệt).
6. **Bộ môn lập hội đồng và xếp lịch (MH-11, DEFN-01):** `bomon` → "Hội đồng &
   lịch bảo vệ" → "Tạo hội đồng": 3–5 GV (đúng một Chủ tịch), **ngày bảo vệ =
   hôm nay** (chỉ chấm được từ ngày bảo vệ), giờ, phòng. Thử thêm `GV001`
   (GVHD của SV) vào hội đồng rồi "Thêm sinh viên" `DTC225200002` → **bị chặn**
   (GVHD không ngồi hội đồng của SV mình); bỏ `GV001` khỏi hội đồng rồi thêm
   lại → thành công. Thành viên nhận "phân vào hội đồng", SV nhận "lịch bảo vệ".
7. **GV chấm điểm (MH-12, DEFN-02):** lần lượt từng thành viên → "Hội đồng bảo
   vệ" → chọn SV → xem báo cáo cuối + kết quả kiểm tra → nhập điểm (0–10) và
   nhận xét. Dashboard GV hiện dòng "Chấm điểm bảo vệ" trong "Việc cần xử lý"
   cho tới khi chấm xong.
8. **Bộ môn chốt → đồ án vào kho (DEFN-03, REPO-01):** `bomon` mở hội đồng →
   "Chốt kết quả" (cần đủ điểm mọi thành viên) → điểm trung bình hiện cho SV ở
   "Bảo vệ" và thẻ "Lịch và kết quả bảo vệ" trên dashboard; bản ghi mới xuất
   hiện trong "Kho đồ án" (nguồn "Hệ thống", "Đã index").
9. **Tra cứu kho và import CSV (MH-13, REPO-02/03):** mọi vai trò → "Kho đồ án"
   lọc theo khóa / từ khóa / GVHD, mở chi tiết, tải báo cáo. `bomon` → "Import
   khóa cũ" với file mẫu ở mục "Định dạng CSV import kho đồ án" → "Đã nhập 2/3
   dòng" kèm lỗi theo dòng.
10. **Tiến độ (MH-10, MH-04, PROG-01..03):** `bomon` → "Tiến độ toàn khoa" →
    "Thiết lập mốc": Mốc 1 hạn **hôm qua**, Mốc 2 hạn tuần sau. SV → "Báo cáo
    tiến độ" nộp Mốc 2 (kèm file tùy chọn); `GV001` → "Nhận xét tiến độ" nhận
    xét + đánh giá → SV nhận thông báo. Quay lại `bomon`: SV bị gắn "Trễ mốc"
    (Mốc 1 chưa nộp), thẻ "SV trễ mốc" trên dashboard > 0 và dẫn tới bộ lọc
    "Chỉ SV trễ mốc".
11. **Dashboard từng vai trò (MH-02/03/04):** "Tổng quan" của SV (thông báo, đề
    cương, tiến độ, lịch/kết quả bảo vệ), GV (Đề cương chờ duyệt, Báo cáo tiến
    độ chờ nhận xét, Hội đồng tham gia, Việc cần xử lý) và Bộ môn (SV trễ mốc,
    Hội đồng sắp tới, "Tiến độ Sinh viên (trích 5/…)", "Mốc tiến độ của đợt").
    "Đánh dấu tất cả đã đọc" trên chuông đưa số chưa đọc về 0.

Các bước trên phủ ROADMAP Phase 3 SC1–SC5. **Lưu ý:** kiểm tra trùng lặp tài
liệu và index kho hiện vẫn chạy trên **stub** (`ai_client.py`) — tỷ lệ và đoạn
trùng là giả lập cho tới Phase 4 (dịch vụ AI thật).

## Kiểm thử tự động

```bash
uv --directory backend run pytest -q
bash deploy/smoke-test.sh
bash deploy/e2e-uc1.sh
bash deploy/e2e-uc2-5.sh
python3 tools/check-erd-db.py
```

Test Phase 3 (pytest): `backend/tests/test_outline_flow.py`,
`test_defense_flow.py`, `test_archive.py`, `test_progress_flow.py`,
`test_notifications.py`. `smoke-test.sh` kiểm tra thêm 403 chéo vai trò trên
mọi nhóm route Phase 3 (outlines, progress, defense, archive) và 200 cho
notifications/archive ở cả ba vai trò.

`deploy/e2e-uc1.sh` tự dựng riêng một đợt đồ án khóa **K99** và dùng 3 tài
khoản seed dành riêng cho kịch bản tự động (tách biệt với các tài khoản dùng ở
demo thủ công phía trên): `GV030` (đề xuất đề tài), `DTC225200099` (tự đề
xuất đề tài, sau đó bị từ chối) và `DTC225200100` (đăng ký đề tài GV đã
duyệt). Script tự xóa toàn bộ dữ liệu nó tạo ra (đợt K99 + đề tài + kết quả
kiểm tra trùng lặp + thông báo phát sinh) khi kết thúc, kể cả khi có bước thất
bại giữa chừng.

`deploy/e2e-uc2-5.sh` chạy chuỗi đề cương → tiến độ → bảo vệ → lưu kho → thông
báo → dashboard qua Apache trên một đợt khóa **K98** riêng. Tài khoản dành
riêng (**không dùng cho demo thủ công**): `GV025` (GV không liên quan),
`GV026`–`GV028` (hội đồng), `GV029` (GVHD), `DTC225200097` (SV khác),
`DTC225200098` (SV chính). Khi kết thúc (kể cả lỗi giữa chừng) script xóa mọi
dữ liệu của đợt K98 (đề tài, đề cương, tài liệu + file vật lý, mốc/báo cáo tiến
độ, lịch/điểm bảo vệ, hội đồng vừa tạo, bản ghi kho) và thông báo của các tài
khoản trên phát sinh từ lúc script bắt đầu. Sau khi chạy không còn đợt K98/K99:

```bash
bash deploy/sql.sh "SELECT COUNT(*) FROM dot_do_an WHERE khoa IN ('K98','K99')"   # 0
```

## File tải lên

Đề cương, báo cáo tiến độ, báo cáo cuối và file kho lưu trong named volume
`ntma_uploads-data`, mount tại `/data/uploads` trong container `api` (đường dẫn
`uploads/<loai>/<uuid>.<ext>`, tên gốc chỉ nằm trong CSDL). Apache **không bao
giờ** phục vụ thư mục này — file chỉ tải được qua API có kiểm tra quyền
(`/api/documents/{id}/download`, `/api/archive/{id}/file`).

Sao lưu / khôi phục (chạy ở thư mục gốc repo):

```bash
docker run --rm -v ntma_uploads-data:/data -v "$PWD":/backup alpine tar czf /backup/uploads-backup.tgz -C /data .
docker run --rm -v ntma_uploads-data:/data -v "$PWD":/backup alpine tar xzf /backup/uploads-backup.tgz -C /data
```

## Định dạng CSV import kho đồ án

Bộ môn nhập đồ án các khóa cũ vào kho (UC5.4, D-07) từ màn hình "Kho đồ án" →
"Import khóa cũ" hoặc `POST /api/archive/import` (multipart, trường `file`).

| Cột | Bắt buộc | Giới hạn | Ghi chú |
|---|---|---|---|
| `khoa` | có | ≤ 20 ký tự | Ví dụ `K19` |
| `ten_de_tai` | có | ≤ 255 ký tự | |
| `ma_so_sinh_vien` | không | ≤ 20 ký tự | Nếu trùng mã một SV đã có tài khoản, bản ghi được liên kết với SV đó (và tự điền họ tên khi để trống) |
| `ho_ten_sinh_vien` | không | ≤ 150 ký tự | |
| `ma_giang_vien` | không | mã GV đã có | Mã không tồn tại → dòng bị từ chối |
| `tu_khoa` | không | ≤ 255 ký tự | Nhiều từ khóa phân tách bằng dấu phẩy, đặt trong ngoặc kép |
| `diem` | không | 0–10, tối đa 2 chữ số thập phân | Chấp nhận `8.5` hoặc `8,5` |

Quy tắc:

- Mã hóa **UTF-8** (có hoặc không có BOM — "CSV UTF-8" của Excel/LibreOffice đều được); dòng đầu là tiêu đề cột; phân tách bằng dấu phẩy (nếu dòng tiêu đề chỉ có dấu chấm phẩy thì hệ thống tự dùng `;`). Cột không có trong bảng trên bị bỏ qua; dòng trống hoàn toàn bị bỏ qua.
- Tối đa **2 MB** và **2000 dòng dữ liệu** mỗi file; vượt giới hạn, sai mã hóa hoặc thiếu cột bắt buộc → cả file bị từ chối (422).
- Dòng trùng (`khoa`, `ten_de_tai`) với một bản ghi đã có trong kho hoặc với một dòng phía trên trong cùng file bị từ chối ("Trùng bản ghi (khóa, tên đề tài)").
- **Import thành công một phần** (UC5.4 E1): các dòng hợp lệ được lưu (nguồn "Import khóa cũ", văn bản chuẩn hóa NFC), các dòng lỗi bị bỏ qua và liệt kê kèm **số dòng** (dòng tiêu đề = 1) và lý do: "Thiếu khóa", "Thiếu tên đề tài", "Khóa quá 20 ký tự", "Điểm không hợp lệ (0–10)", "Không tìm thấy giảng viên mã …", "Trùng bản ghi (khóa, tên đề tài)".
- Mỗi bản ghi mới được đẩy sang Dịch vụ AI để index chạy nền ("Đã index"); lỗi AI để lại "Chưa index", Bộ môn bấm "Index lại" trong chi tiết bản ghi.
- Bản ghi import chỉ có metadata, chưa kèm file báo cáo (file các khóa cũ được nạp cùng bộ dữ liệu Phase 4, DATA-03).

File mẫu (3 dòng):

```csv
khoa,ten_de_tai,ma_so_sinh_vien,ho_ten_sinh_vien,ma_giang_vien,tu_khoa,diem
K19,Xây dựng hệ thống quản lý thư viện số,DTC195200011,Trần Văn Bình,GV001,"thư viện, quản lý",8.5
K18,Ứng dụng học máy dự đoán kết quả học tập,,Lê Thị Hoa,,"học máy, dự đoán","7,75"
```

Để thử báo lỗi theo dòng, thêm một dòng thiếu tên đề tài, ví dụ `K18,,,,,,` —
kết quả sẽ là "Đã nhập 2/3 dòng" kèm "Dòng 4: Thiếu tên đề tài".

## Ghi chú kiến trúc triển khai

- Container `api` không publish cổng ra host — chỉ Apache (`apache` service) mới có thể gọi tới `api:8001` qua mạng nội bộ của compose.
- Dịch vụ AI (Phase 4) sẽ không có route Apache nào trỏ tới — kiến trúc SOA giữ Dịch vụ AI hoàn toàn nội bộ (§3.3.1).
