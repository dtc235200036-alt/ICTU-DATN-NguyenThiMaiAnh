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
| `seed-ai.sh` | Nạp kho cho dịch vụ AI (300 đề tài kho, 25 đồ án nguồn có báo cáo, backfill chỉ mục) — idempotent (xem "Dịch vụ AI kiểm tra trùng lặp") |
| `e2e-ai.sh` / `ai-nfr.sh` | Kịch bản end-to-end dịch vụ AI thật (SC1–SC5) và đo NFR-07..NFR-11 — **không chạy song song** |
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
bash deploy/seed-ai.sh      # một lần sau khi dựng stack (idempotent)
bash deploy/e2e-ai.sh
bash deploy/ai-nfr.sh
uv --directory ai-service run pytest -q
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

## Dịch vụ AI kiểm tra trùng lặp

Phase 4 thêm hai service vào `deploy/docker-compose.yml`:

- **`ai`** — FastAPI của `ai-service/` (một worker uvicorn, chỉ mục FAISS trong bộ nhớ). Chỉ nằm trên mạng nội bộ của compose: **không publish cổng, không có route Apache**; Web API gọi `http://ai:8002` kèm header `X-API-Key`. Giới hạn bộ nhớ `AI_MEM_LIMIT` (mặc định `2g`; đo thực tế đỉnh ≈ 850 MiB). Trọng số mô hình cache trên volume **`ai-models`** (`/models`).
- **`ai-db-init`** — chạy một lần trước `ai`: tạo schema `thesis_ai` và tài khoản MySQL `thesis_ai` chỉ có quyền trên schema đó (không đọc được `thesis_core`).

### Biến môi trường (`deploy/.env`)

| Khóa | Ý nghĩa |
|---|---|
| `AI_API_KEY` | Khóa nội bộ Web API ↔ Dịch vụ AI (sinh ngẫu nhiên bởi `init.sh`) |
| `AI_DB_PASSWORD` | Mật khẩu tài khoản MySQL `thesis_ai` (sinh bởi `init.sh`) |
| `AI_CLIENT` | `http` (mặc định — gọi dịch vụ AI thật) hoặc `stub` — **phương án dự phòng D-07**: Web API quay về bộ giả lập Jaccard của Phase 2/3, không cần container `ai` hoạt động |
| `AI_STUB_MODE` | Chỉ có hiệu lực khi `AI_CLIENT=stub`: `normal` hoặc `loi` (mô phỏng dịch vụ AI không phản hồi, UC0.6/UC0.7 - E2) |
| `AI_MODEL_PROFILE` | Mô hình embedding đã chốt: `bkai` (`bkai-foundation-models/vietnamese-bi-encoder` + tách từ underthesea); `e5` là phương án thay thế |
| `AI_MEM_LIMIT` | Giới hạn bộ nhớ container `ai` (mặc định `2g`) |

`init.sh` sinh các khóa này khi tạo `.env` mới, và **bổ sung các khóa còn thiếu vào một `.env` đã có** (giữ nguyên giá trị cũ) — chạy lại `bash deploy/init.sh` sau khi cập nhật từ Phase 3. Chỉ ghi giá trị trong `deploy/.env` (chmod 600, đã gitignore), không đưa vào tài liệu hay commit.

### Lần khởi động đầu, máy chủ không có Internet

Lần đầu `ai` khởi động sẽ tải trọng số mô hình (~515 MiB) từ Hugging Face vào volume `ai-models`, nên healthcheck có thể mất vài phút. Máy chủ không có Internet: làm nóng volume ở nơi có mạng trước (hoặc sao chép volume sang):

```bash
docker compose -f deploy/docker-compose.yml run --rm ai python -m app.download_model
```

### Nạp dữ liệu và bảo trì chỉ mục

```bash
bash deploy/seed-ai.sh
```

Idempotent — chạy lại không tạo trùng: import 300 đề tài kho khóa K18–K22 (`seed-data/de-tai-kho.csv`) qua đúng API import của Bộ môn, tạo 25 đồ án nguồn khóa cũ có báo cáo cuối (`python -m app.seed_ai_corpus`, dữ liệu DATA-03), rồi backfill chỉ mục; kết thúc khi `/health` có vector.

Bảo trì:

```bash
# Đẩy lại mọi đề tài / bản ghi kho / tài liệu còn thiếu trong chỉ mục (vd. sau khi dịch vụ AI tạm ngừng)
docker compose -f deploy/docker-compose.yml exec -T api python -m app.services.ai_index backfill
# Sau khi đổi AI_MODEL_PROFILE: encode các chunk còn thiếu vector của mô hình mới rồi dựng lại chỉ mục
docker compose -f deploy/docker-compose.yml exec -T api python -c "import os,urllib.request as u; r=u.Request('http://ai:8002/reindex', data=b'{}', headers={'X-API-Key': os.environ['AI_API_KEY'], 'Content-Type': 'application/json'}); print(u.urlopen(r, timeout=1800).read().decode())"
```

Ngưỡng cảnh báo (tên đề tài, cảnh báo tài liệu, đoạn trùng) do Bộ môn sửa ở menu **Ngưỡng trùng lặp** (`/cau-hinh-nguong`, UC0.4); giá trị đề xuất lấy từ hiệu chỉnh (`ai-service/calibration/nguong-de-xuat.json`, trang chương 4 `docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md`). Ngưỡng nguyên văn (MinHash) là tham số kỹ thuật của dịch vụ AI, không sửa trên giao diện.

### Kiểm thử dịch vụ AI

```bash
bash deploy/e2e-ai.sh
bash deploy/ai-nfr.sh --report docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md
```

- `e2e-ai.sh` — bảo mật dịch vụ AI, tên đề tài diễn đạt lại (cả NFC và NFD), Bộ môn đổi ngưỡng thì lần kiểm tra kế tiếp áp dụng (script luôn khôi phục ba ngưỡng gốc kể cả khi lỗi, và báo FAIL nếu đọc lại không khớp), push-on-write, tài liệu chép nguyên văn / không liên quan. Khóa kiểm thử **K97**.
- `ai-nfr.sh` — đo NFR-07..NFR-11 và bộ nhớ; `--report` ghi đè trang số liệu chương 4. Khóa kiểm thử **K96**.

**Tài khoản dành riêng — không dùng cho demo thủ công:** `DTC225200095`, `DTC225200096` (SV), `GV023` (GVHD), cùng `bomon`; khóa **K96** và **K97**. `e2e-ai.sh` và `ai-nfr.sh` **dùng chung `DTC225200095` và `GV023` nên không bao giờ chạy song song** (`ai-nfr.sh` từ chối chạy nếu `DTC225200095` đang giữ một đề tài hoạt động). Hai script tự dọn dữ liệu, file và vector đã tạo; sau khi chạy:

```bash
bash deploy/sql.sh "SELECT COUNT(*) FROM dot_do_an WHERE khoa IN ('K96','K97','K98','K99')"   # 0
```

### Hạn chế đã biết

- **Thời gian kiểm tra tăng theo độ dài tài liệu** (~0,12 s CPU / 1000 ký tự trên máy phát triển: báo cáo ~100 trang ≈ 40 s, vượt mức 30 s của NFR-09 vốn đo trên đề cương/báo cáo ngắn). Web API đặt timeout `/check-document` theo độ dài: `AI_DOCUMENT_TIMEOUT_SECONDS` (24) + `AI_DOCUMENT_TIMEOUT_PER_1K_CHARS` (0,25) × nghìn ký tự, trần `AI_DOCUMENT_TIMEOUT_MAX_SECONDS` (240, dưới `DOCUMENT_CHECK_TIMEOUT_SECONDS` = 300). Kiểm tra tên đề tài không bị chặn trong lúc đó (dịch vụ AI mã hóa theo lô con); `ai-nfr.sh` đo cả hai.

- **Xóa bản ghi kho không xóa vector của nó khỏi chỉ mục AI.** Hợp đồng §3.3.5 không có endpoint xóa (hoãn lại). Bản ghi đã xóa không còn xuất hiện trong kết quả vì Web API bỏ qua mọi `ref_id` không còn tồn tại, nhưng vector vẫn chiếm chỗ trong chỉ mục; gỡ thủ công khi cần: `docker compose -f deploy/docker-compose.yml exec -T api python -m app.services.ai_index purge --loai ARCHIVE --ids <id>`.
- **Danh sách phần mẫu chung là giả định `[ASSUMED]`** (bìa, lời cam đoan, mục lục, danh mục, tài liệu tham khảo, phụ lục…) cho tới khi có mẫu đề cương/báo cáo chính thức của Khoa — khi có mẫu, cập nhật `ai-service/app/nlp/boilerplate.py` rồi chạy lại hiệu chỉnh (`calibration/calibrate.py tune|evaluate`). Để danh sách này không thành chỗ giấu nội dung, tiêu đề mục mẫu chỉ bỏ nguyên mục ở phần đầu/phần cuối tài liệu và có trần độ dài; MH-09/MH-14 luôn ghi số câu đã so sánh, số dòng và % nội dung bị loại, và cảnh báo khi hơn 50 % nội dung bị loại (tài liệu seed tổng hợp ngắn bị loại tới 45 %).
- **Số liệu chất lượng phát hiện đo trên dữ liệu tổng hợp** (`seed-data/`, sinh bằng `tools/datagen`), không phải đồ án thật của sinh viên; cảnh báo tên đề tài và đoạn trùng ngữ nghĩa là **gợi ý** để giảng viên xem lại, không phải kết luận.
- "Vượt ngưỡng cảnh báo" so **tỷ lệ trùng với một đồ án nguồn** (`ty_le_nguon_cao_nhat`, đúng thống kê đã hiệu chỉnh `NGUONG_TAI_LIEU`) với ngưỡng, không so tỷ lệ tổng: một bài cùng lĩnh vực khớp rải rác nhiều đồ án (P19: tổng 23.96 %, theo nguồn 0 %) không bị cảnh báo. Tỷ lệ theo từng đồ án trên MH-14/MH-09 là giá trị dịch vụ AI trả (`do_an_trung`), lưu ở `chi_tiet_trung_lap.ty_le_nguon`.

### Kịch bản demo AI (thao tác trên trình duyệt)

Chuẩn bị: stack đã dựng, `bash deploy/seed-ai.sh` đã chạy. Dùng các tài khoản demo **không** thuộc danh sách dành riêng ở trên (vd. `DTC225200010`, `DTC225200011`, `GV005`); mật khẩu `SEED_DEFAULT_PASSWORD`.

1. **SC1 — tên đề tài diễn đạt lại.** Đăng nhập `DTC225200010` → **Đề xuất / Đăng ký đề tài** → nhập tên "Sử dụng SQL Server để hạch toán thu chi doanh nghiệp cho công ty cổ phần Hoàng Long" rồi rời ô → cảnh báo "Phát hiện … đề tài tương tự trong kho" với đồ án kho "Ứng dụng SQL Server trong quản lý kế toán tại công ty CP Hoàng Long (K21)" kèm tỷ lệ (≈ 82%). Dán cùng tên ở dạng Unicode tổ hợp (NFD, vd. gõ bằng bộ gõ khác) cho cùng kết quả. Một tên cùng lĩnh vực nhưng khác đề tài không bị cảnh báo trùng kho.
2. **SC2 — tài liệu chép nguyên văn.** Để `DTC225200010` có đề tài đã phân công GVHD `GV005` (Bộ môn duyệt đề xuất ở bước 1 hoặc cho SV đăng ký một đề tài GV đã duyệt). Ở **Đề cương**, nộp `seed-data/tai-lieu/P01-B.pdf` → trạng thái "Đang kiểm tra" rồi "Hoàn tất - 50.3%" (không cần tải lại trang). Bấm "Xem kết quả" (MH-14): tỷ lệ tổng 50.3%, ngưỡng 10.4%, đồ án trùng "Phát triển mô hình thống kê điểm số … Metabase (K21)" 50.3%; mỗi đoạn đặt cạnh đoạn nguồn, cụm từ trùng được tô, nhãn "Trùng nguyên văn", ghi chú đã loại trừ phần mẫu chung (FR-AI-02). Đăng nhập `GV005` → **Duyệt đề cương** → "Duyệt": panel MH-09 hiện cùng tỷ lệ, "Vượt ngưỡng cảnh báo" và "Số đoạn trùng: 7 (7 trùng nguyên văn)". Nộp một file diễn đạt lại (vd. `P11-B.docx`) cho một SV khác: các đoạn mang nhãn "Trùng ngữ nghĩa", ít cụm từ được tô hơn.
3. **SC3 — bảng kiểm chứng trên 50 file.** Mở `docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md`: điểm từng cặp của 25 cặp (chép nguyên văn, diễn đạt lại bị cảnh báo; cùng lĩnh vực, không liên quan dưới ngưỡng) trên tập hiệu chỉnh và tập kiểm chứng giữ lại, cùng mô hình đã chốt (`02-so-sanh-mo-hinh-embedding.md`).
4. **SC4 — Bộ môn đổi ngưỡng.** Đăng nhập `bomon` → **Ngưỡng trùng lặp**: ba ngưỡng kèm giải thích, giá trị đề xuất và người cập nhật. Đặt "Ngưỡng tên đề tài" = 99 → "Lưu cấu hình" → xác nhận. `DTC225200011` kiểm tra lại tên ở bước 1 → không còn cảnh báo. Bộ môn bấm "Khôi phục giá trị đề xuất" → lưu → cảnh báo trở lại. Kết quả đã kiểm tra trước đó vẫn hiện ngưỡng lúc kiểm tra.
5. **SC5 — bản ghi mới được index ngay; dịch vụ AI không lộ ra ngoài.** `bomon` → **Kho đồ án** → thêm bản ghi "Xây dựng hệ thống quản lý phòng thí nghiệm hóa học cho trường cao đẳng y tế" (khóa K22) → cột index chuyển "Đã index" sau vài giây. `DTC225200011` kiểm tra tên "Phát triển phần mềm quản lý phòng thí nghiệm hóa học tại trường cao đẳng y tế" → thấy ngay bản ghi vừa thêm (≈ 90%), không phải tính lại embedding toàn kho (e2e-ai kiểm `encode_calls` +1). Xóa bản ghi sau demo (vector còn trong chỉ mục nhưng không xuất hiện trong kết quả — xem Hạn chế). Phần cô lập: chạy `bash deploy/ai-nfr.sh` (hoặc `e2e-ai.sh`) — host không kết nối được cổng 8002, thiếu/sai khóa → 401, Apache không có route tới dịch vụ AI, tài khoản DB `thesis_ai` bị từ chối trên `thesis_core`; kèm số đo thời gian kiểm tra tên (P95 ≈ 0,05 s) và nộp → hoàn tất (P95 ≈ 4 s).

Dọn dữ liệu demo sau khi xong (đề tài/đề cương của tài khoản demo) theo cách thông thường của UC1–UC2; các file đã nộp nằm trong volume `uploads-data`.

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
- Dịch vụ AI (Phase 4) không có route Apache nào trỏ tới và không publish cổng ra host — chỉ container `api` gọi `http://ai:8002` qua mạng nội bộ kèm `X-API-Key` (§3.3.1, NFR-07).
