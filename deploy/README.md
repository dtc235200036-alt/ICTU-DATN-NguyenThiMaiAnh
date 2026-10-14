# Triển khai NTMA (Hệ thống quản lý đồ án — Khoa CNTT)

## Cài đặt nhanh (một lệnh)

Trên một máy Linux có Docker Engine + Compose v2, `openssl`, `curl`, `python3`
(>= 10 GB trống, cổng 80/443 rảnh, Internet chỉ cần trong lúc cài):

```bash
git clone <repo> ntma && cd ntma
bash deploy/install.sh            # cài mới hoặc nâng cấp — chạy lại an toàn, không xóa dữ liệu
bash deploy/verify-all.sh --quick # kiểm tra nhanh (~10 s)
```

Mở `https://localhost` (hoặc `https://<SERVER_NAME>`). `install.sh` thực hiện
và đo thời gian từng bước: (0) kiểm tra điều kiện; (1) `init.sh` — sinh
`deploy/.env` (bí mật ngẫu nhiên, chmod 600) và chứng chỉ TLS tự ký; (2) build
image AI và **tải trước mô hình** vào volume `ai-models` (D-02 — lúc chạy service
`ai` đặt `HF_HUB_OFFLINE=1`); (3) `docker compose up -d --build --wait`; (4) kiểm
tra `alembic_version` = revision mới nhất và `/health` của dịch vụ AI; (5) kiểm
tra 580 SV / 70 GV / Bộ môn (DATA-01); (6) `seed-ai.sh` — 300 đề tài kho qua
đường import thật + 25 đồ án nguồn có báo cáo (DATA-02, DATA-03); (7) tóm tắt
địa chỉ, tài khoản, nguồn mật khẩu.

| Tùy chọn `install.sh` | Ý nghĩa |
|---|---|
| `--fresh` | Cài lại sạch: `docker compose down -v` (**xóa CSDL, file đã nộp, cache mô hình**) trước khi cài. Cần thêm `--yes` hoặc gõ `XOA` để xác nhận; không có TTY mà thiếu `--yes` thì từ chối và không xóa gì |
| `--yes` | Xác nhận `--fresh` không cần hỏi |
| `--server-name TEN` | Ghi `SERVER_NAME` vào `deploy/.env` và sinh lại chứng chỉ tự ký cho tên/IP đó. Chứng chỉ do CA cấp (đặt tay vào `deploy/certs/server.crt` + `server.key`) không bao giờ bị ghi đè |
| `--random-seed-password` | Sinh `SEED_DEFAULT_PASSWORD` ngẫu nhiên vào `deploy/.env` (khi còn trống hoặc là mật khẩu dev mặc định và CSDL chưa có tài khoản — dùng cùng `--fresh --yes` nếu đã cài). Bắt buộc cho máy chủ thật; `install.sh` cảnh báo khi `SERVER_NAME` khác `localhost` mà vẫn dùng mật khẩu dev |
| `--skip-seed-ai` | Bỏ qua bước 6 |

Máy chủ thật (trường/lab): `bash deploy/install.sh --server-name <tên-miền-hoặc-IP> --random-seed-password`,
thay chứng chỉ tự ký bằng chứng chỉ CA ở `deploy/certs/server.crt` / `server.key`
rồi `docker compose -f deploy/docker-compose.yml restart apache`, tường lửa chỉ mở 80/443,
giữ `deploy/.env` ở chế độ 600.

### Kiểm chứng toàn hệ thống — `verify-all.sh`

```bash
bash deploy/verify-all.sh --quick    # stack + dữ liệu + smoke-test
bash deploy/verify-all.sh            # đầy đủ (~5 phút trên máy demo: 259 s)
bash deploy/verify-all.sh --report   # đầy đủ + ghi kết quả cho chương 4
```

- `--quick`: tình trạng stack (mysql/api/ai healthy, apache chạy, `ai-db-init`/`ai-migrate` exit 0, `ai` có `HF_HUB_OFFLINE=1` và không publish cổng), số liệu DATA-01/02/03 (580 SV, 70 GV, 300 đề tài kho K18–K22 đều `DA_INDEX`, `/health` ≥ 300 vector tiêu đề, 50 tệp, 25 đồ án nguồn có báo cáo), `smoke-test.sh`.
- Đầy đủ: thêm `uv --directory backend run pytest -q`, `uv --directory ai-service run pytest -q`, `e2e-uc1.sh`, `e2e-uc2-5.sh`, `e2e-ai.sh`, `ai-nfr.sh --json`, `nfr-he-thong.sh --json`, `tools/check-erd-db.py`, kiểm tra không còn dữ liệu kiểm thử (đợt/bản ghi kho K95–K99, tài khoản bị khóa) và bước **nfr-16**: chạy `tools/demo/kich-ban-anh.json --chi-doc` (23 màn hình, 3 vai trò) bằng Chrome headless 1440 px qua HTTPS — FAIL nếu có lỗi JS/console, HTTP ≥ 400 ngoài dự kiến hoặc tràn ngang (bỏ qua, dùng `anh-chup.json` đã commit, khi chưa có trạng thái demo).
- Mọi chế độ (05-05): ghi chữ ký hàng của tài khoản demo (`demo-state.sh --dem`: số hàng + md5 cột trạng thái/điểm) **trước** các bộ kiểm thử và so lại ở bước cuối **"trạng thái demo"** — lệch là FAIL (các bộ tự động không được đụng trạng thái demo).
- `--report`: ghi `docs/chuong-4-trien-khai/ket-qua-kiem-thu/tong-hop.json` (commit, máy, từng bước + trạng thái + giây, số test pytest, `du_lieu`, bảng NFR-01…NFR-19 với `dat` true/false/null) và `nhat-ky-verify-all.log` (nhật ký đầy đủ), đồng thời ghi lại trang `docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md` (`ai-nfr.sh --report`). Mọi thứ ghi ra đều đã che: giá trị `deploy/.env` dài ≥ 8 ký tự thành `***` (khóa bí mật) hoặc `<TEN_KHOA>`, chuỗi dạng JWT thành `***`.
- In bảng các bước (trạng thái + giây) và thoát khác 0 nếu có bước lỗi.

`nfr-he-thong.sh [--json PATH]` đo NFR mức hệ thống qua Apache HTTPS: NFR-01 (301 → https), NFR-02 (bcrypt cost ≥ 12, mật khẩu không có trong log), NFR-03 (token ký bằng helper của app với `exp` quá khứ → 401), NFR-04 (SV gọi route Bộ môn → 403), NFR-05 (Bộ môn khóa → đăng nhập bị từ chối, mở khóa → đăng nhập lại được), NFR-08 qua HTTPS (20 lần kiểm tra tên, P95 ≤ 5 s), NFR-12 (20 lần tra cứu kho + 20 lần danh sách đề tài, P95 ≤ 1 s), NFR-13 (collation `utf8mb4_vietnamese_ci` ở mọi cột/bảng của `thesis_core` và `thesis_ai`, `alembic_version` mới nhất), NFR-14 (NFC = NFD), NFR-15 (ProxyTimeout > 30 s, SPA tĩnh, `/api` qua proxy), NFR-17/18/19 (số liệu seed). NFR-06 do `smoke-test.sh` + pytest chứng minh, NFR-07/09/10/11 do `ai-nfr.sh`, NFR-16 (Chrome 1440 px) do bước `nfr-16` của verify-all (hoặc `ket-qua-kiem-thu/anh-chup.json`).

**Tài khoản dành riêng cho `nfr-he-thong.sh` — không dùng cho demo thủ công:** `DTC235210073` (SV, bị khóa/mở khóa trong lúc chạy) cùng `bomon`; khóa **K95** dành riêng (script không tạo đợt nào, nhưng dọn nếu có). Script luôn mở khóa lại `DTC235210073` và xóa thông báo phát sinh của nó (trap, kể cả khi lỗi). Không chạy song song với các script kiểm thử khác.

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
| Sinh viên | `DTC235200016` .. `DTC235210045` | `dtc225200001@ictu.edu.vn` .. `dtc225200100@ictu.edu.vn` | như trên |

**Chỉ dùng cho dev/demo** — đổi `SEED_DEFAULT_PASSWORD` trước khi đưa lên môi
trường thật (Phase 5).

Seed cũng tạo sẵn một đợt đồ án đang mở, **"Đợt đồ án tốt nghiệp K22 - HK1
(2026-2027)"** (khóa K22), dùng ngay cho demo UC1 (GVHD giao đề tài) mà
không cần Bộ môn mở đợt thủ công trước, kèm **phân công GVHD mặc định** cho đợt
đó (UC0.8, migration 0015): SV thứ *i* → GV thứ ((*i*−1) mod 30)+1, tức
`DTC235200016` → `GV001`, `DTC235200139` → `GV011`, `DTC235200703` → `GV001`, …
Seed không bao giờ đổi phân công đã có; Bộ môn đổi ở "Phân công GVHD"
(`/phan-cong-gvhd`). SV không tự đề xuất hay đăng ký đề tài: SV trao đổi với
GVHD ngoài hệ thống, rồi chỉ GVHD được Bộ môn phân công mới tạo và giao đề tài
cho SV trong lớp hướng dẫn (góp ý GVHD mục 1).

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
| `install.sh` | Cài đặt / nâng cấp toàn bộ bằng một lệnh (xem "Cài đặt nhanh") |
| `verify-all.sh [--quick] [--report]` | Chạy tuần tự mọi bộ kiểm thử + đo NFR, bảng kết quả, ghi `docs/chuong-4-trien-khai/ket-qua-kiem-thu/` |
| `nfr-he-thong.sh [--json PATH]` | Đo NFR mức hệ thống qua Apache HTTPS (NFR-01..05, 08, 12..15, 17..19) |
| `demo-state.sh [--chi-xoa \| --dem]` | Đưa hệ thống về trạng thái demo bảo vệ (xem "Kịch bản demo bảo vệ (Phase 5)") |
| `tools/demo/chay-kich-ban.py <kịch bản.json>` | Chạy kịch bản JSON trên giao diện thật bằng Chrome headless (CDP), chụp ảnh 1440 px, ghi `--json` / `--log` |

## Reset toàn bộ

```bash
docker compose -f deploy/docker-compose.yml down -v
```

Hoặc cài lại sạch trong một lệnh (xóa cả cache mô hình rồi tải lại): `bash deploy/install.sh --fresh --yes`.

Lệnh này xóa cả volume `mysql-data` **và** `uploads-data` (file đề cương/báo cáo đã nộp) — lần khởi động sau sẽ tạo lại schema và seed dữ liệu từ đầu. Muốn giữ file tải lên, sao lưu trước theo mục "File tải lên" bên dưới.

## Kịch bản demo bảo vệ (Phase 5) — trạng thái demo và chạy lại kịch bản

Dùng cho buổi bảo vệ; thay thế các mục "Kịch bản demo UC1", "UC2–UC5" và "Kịch bản demo AI" bên dưới (giữ lại làm hướng dẫn thao tác chi tiết theo từng phase). Bản trình bày cho người đọc (`docs/kich-ban-demo.md`, lời nói theo từng bước) sẽ viết cùng quyển báo cáo; bản máy chạy được là `tools/demo/kich-ban-demo.json` (B01…B18, mốc thời gian dự kiến, tài khoản, tệp, chữ mong đợi, ý cần nói).

**Tài khoản demo dành riêng** (không bộ kiểm thử tự động nào ghi vào; đợt: "Đợt đồ án tốt nghiệp K22 - HK1 (2026-2027)", mật khẩu `SEED_DEFAULT_PASSWORD`):

| Tài khoản | Trạng thái sau `demo-state.sh` | Dùng trong demo |
|---|---|---|
| `DTC235200139` | chưa có đề tài, GVHD `GV011` | `GV011` ở "Sinh viên của tôi" bấm "Giao đề tài" cho 011, nhập tên diễn đạt lại → cảnh báo AI → "Vẫn giao đề tài" → Đã phân công; 011 đăng nhập thấy đề tài được giao, nộp `seed-data/tai-lieu/P03-B.pdf` → Đang kiểm tra → Hoàn tất |
| `DTC235200258` | đề cương v1 = `P02-B.docx` (chép nguyên văn), Hoàn tất 48 %, chờ GV011 duyệt | MH-09 / MH-14 đoạn tô sáng, Yêu cầu sửa |
| `DTC235200325` | đề cương đã duyệt, 2 báo cáo tiến độ (mốc 1 đã nhận xét, mốc 2 chờ) | UC3 |
| `DTC235200340` | báo cáo cuối đã kiểm tra, "Hội đồng demo K22", 2/3 điểm | GV014 chấm, Bộ môn chốt → tự vào kho |
| `DTC235270078` | đủ 3 điểm, đã chốt (8.5), đã trong Kho đồ án | UC4 kết quả, UC5 tra cứu |
| `GV011` / `GV012` / `GV013` / `GV014` | GVHD (Bộ môn phân công) của 011–015 — giao đề tài cho 011–015 / chủ tịch / thư ký / ủy viên hội đồng demo | |

```bash
bash deploy/demo-state.sh             # xóa trạng thái demo cũ + dựng lại (~20 s; xóa ~3 s, dựng ~13 s)
bash deploy/demo-state.sh --chi-xoa   # chỉ xóa (5 SV demo không còn đề tài, vẫn GVHD GV011; hội đồng demo bị xóa)
bash deploy/demo-state.sh --dem       # chỉ đọc: chữ ký hàng demo (verify-all dùng)
```

`demo-state.sh` chỉ chọn hàng của 5 SV demo trong đợt K22 và hội đồng tên "Hội đồng demo K22", gỡ TOPIC/DOCUMENT/ARCHIVE của chúng khỏi chỉ mục AI rồi xóa theo thứ tự khóa ngoại; **dừng, không xóa gì** nếu hội đồng demo có lịch/thành viên ngoài tài khoản demo. Sau bước xóa (kể cả `--chi-xoa`), Bộ môn gán lại cả 5 SV demo cho GVHD `GV011` trong đợt K22 qua `PUT /api/assignments` (seed mặc định là 012→GV012 … 015→GV015) và xóa thông báo phân công phát sinh để trạng thái demo luôn giống nhau; khi dựng lại, đề tài 012–015 do SV gửi rồi **GVHD `GV011` duyệt** (không còn bước Bộ môn duyệt/phân công). Mốc tiến độ của đợt K22 được get-or-create (không bao giờ xóa) và đặt hạn +3/+17/+45 ngày theo ngày chạy (kẹp trong đợt). Tệp nộp lấy từ các cặp đã hiệu chỉnh Đạt, **bỏ qua** cặp CHEP_NGUYEN_VAN/KHONG_LIEN_QUAN đầu tiên vì `e2e-ai.sh` dùng chúng.

Chạy lại kịch bản trên giao diện thật (Chrome headless qua `https://localhost`, 1440×900; cần `/usr/bin/google-chrome` hoặc `CHROME=...` và gói Python `websockets` có sẵn trên máy):

```bash
# Tập dượt tự động B01…B18 (ghi dữ liệu) — thêm một mục vào nhật ký
bash deploy/demo-state.sh && python3 tools/demo/chay-kich-ban.py tools/demo/kich-ban-demo.json \
  --out-dir /tmp/ntma-tap-duot --log docs/chuong-4-trien-khai/ket-qua-kiem-thu/tap-duot-demo.md && bash deploy/demo-state.sh

# Chụp lại 29 ảnh chương 4 (uc0…uc5) + bảng kê anh-chup.json (NFR-16)
bash deploy/demo-state.sh && python3 tools/demo/chay-kich-ban.py tools/demo/kich-ban-anh.json \
  --out-dir docs/chuong-4-trien-khai/anh --json docs/chuong-4-trien-khai/ket-qua-kiem-thu/anh-chup.json && bash deploy/demo-state.sh
```

Một bước FAIL khi hết giờ chờ chữ mong đợi, có exception JS / lỗi console, HTTP ≥ 400 không khai báo trong `cho_phep_http`, hoặc trang tràn ngang; ảnh lúc lỗi ghi ở `/tmp/ntma-loi-<bước>.png`. Mật khẩu đọc từ `NTMA_MAT_KHAU` hoặc `deploy/.env`, không bao giờ in ra; Chrome debug chỉ bind 127.0.0.1 (cổng tạm) và bị tắt + xóa hồ sơ tạm khi xong. **Luôn chạy `bash deploy/demo-state.sh` sau kịch bản** và không chạy song song với `verify-all.sh`.

## Kịch bản demo UC1 (thao tác trên trình duyệt)

> Cho buổi bảo vệ dùng mục "Kịch bản demo bảo vệ (Phase 5)" ở trên; mục này giữ lại làm hướng dẫn thao tác chi tiết.

Mở `https://localhost`, chấp nhận cảnh báo chứng chỉ tự ký, rồi thực hiện tuần
tự (ROADMAP Phase 2, SC1–SC5):

1. **Đăng nhập bằng mã hoặc email:** đăng nhập bằng `bomon` (mã) rồi đăng
   nhập lại bằng `bomon@ictu.edu.vn` (email) — cùng vào được. Tải lại trang
   (F5) — vẫn còn phiên đăng nhập (refresh token cookie).
2. **Khóa/mở tài khoản (Bộ môn):** vào "Quản lý tài khoản" (`/tai-khoan`),
   khóa một tài khoản SV (ví dụ `DTC235200036`), thử đăng nhập bằng tài khoản
   đó ở cửa sổ ẩn danh → bị từ chối; mở khóa lại.
3. **Mở/đóng đợt đồ án (Bộ môn):** vào "Quản lý đợt đồ án", đóng đợt "Đợt đồ
   án tốt nghiệp K22 - HK1 (2026-2027)", xác nhận GVHD không giao được đề
   tài mới trong đợt đã đóng; mở lại đợt trước khi tiếp tục demo.
4. **Bộ môn phân công GVHD (UC0.8, MH-13):** đăng nhập `bomon`, vào "Phân
   công GVHD" (`/phan-cong-gvhd`), chọn đợt K22 — bảng SV kèm GVHD hiện tại
   (seed mặc định), tải từng GV, lọc đã/chưa phân công. Đổi GVHD của
   `DTC235200036` thành `GV001` rồi lưu (có thể import CSV
   `ma_so_sinh_vien,ma_giang_vien`). Lớp của `GV001` lúc này gồm
   `DTC235200016`, `DTC235200036`, `DTC235200703`, … (GV xem ở "Sinh viên của
   tôi", `/sinh-vien-huong-dan`). GV không phải GVHD của SV thì không giao được
   đề tài cho SV đó.
5. **GVHD tạo và giao đề tài (MH-16 → MH-06):** SV trao đổi và thống nhất đề
   tài với GVHD ngoài hệ thống; trên hệ thống chỉ GVHD tạo đề tài. Đăng nhập
   `GV001`, vào "Sinh viên của tôi" → bấm "Giao đề tài" ở dòng một SV chưa có
   đề tài (vd. `DTC235200489`; form mở sẵn đợt + sinh viên, hoặc vào menu
   "Giao đề tài" rồi chọn SV — ô sinh viên bắt buộc). Nhập một tên đề tài gần
   giống đề tài đã có trong kho — quan sát cảnh báo "N đề tài tương tự" rồi
   chọn "Vẫn giao đề tài" → "Giao đề tài cho sinh viên" → "Đã phân công" ngay,
   kèm kết quả kiểm tra tên đã lưu. "Lưu nháp" để soạn trước (SV chưa thấy bản
   nháp), sau đó gửi từ trang chi tiết. Chọn SV lớp khác thì bị từ chối.
6. **SV xem đề tài được giao:** đăng nhập `DTC235200489` — nhận thông báo
   "GVHD … đã giao cho bạn đề tài …", "Tổng quan" hiện đề tài Đã phân công →
   "Xem chi tiết đề tài" (MH-07). Menu SV không có mục đề xuất/đăng ký đề tài;
   mở trực tiếp `/de-tai/de-xuat` nhận trang 403. SV lớp khác (vd.
   `DTC235200988`, GVHD `GV003`) không xem được đề tài đó.
7. **Quyền (RBAC):** SV và Bộ môn gọi `POST /api/topics`, `PUT`/`submit`,
   `POST /api/topics/check-title` → 403; `POST /api/topics/{id}/register` và
   `/api/topic-approvals*` đã gỡ → 404 (không còn màn "Duyệt đề tài"). Sau khi
   SV có đề tài "Đã phân công", Bộ môn không đổi được GVHD của SV đó.
8. **Danh sách lọc theo đợt/trạng thái/GVHD:** ở "Danh sách đề tài" (mọi vai
   trò), lọc theo Đợt đồ án, Trạng thái và Giảng viên hướng dẫn — bảng chỉ
   còn đúng các đề tài khớp bộ lọc.
9. **403 khi gọi sai vai trò:** đăng nhập SV, thử mở trực tiếp URL
   `/tai-khoan`, `/phan-cong-gvhd` hoặc `/de-tai/de-xuat` — nhận trang 403 "Bạn
   không có quyền truy cập trang này".
10. **Dashboard theo vai trò:** đăng nhập lần lượt `DTC235200016`, `GV001` và
    `bomon`, mở "Tổng quan" — mỗi vai trò thấy đúng widget của mình (SV: đề
    tài được giao + GVHD được phân công; GV: sinh viên hướng dẫn + sĩ số lớp +
    "SV chưa được giao đề tài" + việc "Giao đề tài" + bảng đề tài hướng dẫn;
    Bộ môn: SV chưa được giao đề tài + SV chưa có đề tài + SV chưa phân công
    GVHD + đề tài đã phân công + danh sách đề tài giao gần nhất).

## Kịch bản demo UC2–UC5 (thao tác trên trình duyệt)

> Cho buổi bảo vệ dùng mục "Kịch bản demo bảo vệ (Phase 5)" ở trên; mục này giữ lại làm hướng dẫn thao tác chi tiết.

Tiếp nối kịch bản UC1: cần một SV có đề tài **Đã phân công** (ví dụ bước 4–7
ở trên: `bomon` phân công `DTC235200036` cho GVHD `GV001`, `GV001` "Giao đề
tài" cho `DTC235200036`).
Thứ tự theo D-09: đề cương → bảo vệ → lưu kho → tiến độ; chuông thông báo
(góc phải Header) được kiểm tra ở mọi bước. Dùng các tài khoản SV thông thường (vd. `DTC235200159`)
/ `GV0xx` thông thường — **không** dùng các tài khoản dành riêng cho e2e
(xem mục "Kiểm thử tự động").

1. **Thông báo phân công (NOTF-01):** sau khi `bomon` phân công GVHD, SV nhận
   "Giảng viên hướng dẫn của bạn trong '…': …" và GV nhận "Bạn được phân công
   hướng dẫn thêm n sinh viên …"; khi `DTC235200036` gửi đề tài, `GV001` nhận
   "… gửi đề tài '…' chờ bạn duyệt"; ngay sau khi `GV001` duyệt, đăng nhập
   `DTC235200036` — trong tối đa 30 giây chuông hiện số chưa đọc; mở chuông
   thấy "Đề tài '…' đã được GVHD … duyệt"; bấm vào thông báo → mở chi tiết đề
   tài, số trên chuông giảm 1.
2. **SV nộp đề cương (MH-08, OUTL-01):** `DTC235200036` → "Đề cương" → chọn
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
   (GVHD của SV) vào hội đồng rồi "Thêm sinh viên" `DTC235200036` → **bị chặn**
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

Toàn bộ danh sách dưới đây chạy tuần tự bằng một lệnh: `bash deploy/verify-all.sh` (xem "Kiểm chứng toàn hệ thống").

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
mọi nhóm route Phase 3 (outlines, progress, defense, archive), 200 cho
notifications/archive ở cả ba vai trò, và luồng phân công GVHD (0015):
`POST /api/topics` và `/api/topics/check-title` chỉ GV (SV → 403), route đăng ký
và `/api/topic-approvals` đã gỡ (404), `/api/assignments` gán/import/
xem chỉ Bộ môn, `my-students` chỉ GV, `my-advisor` chỉ SV (`DTC235200016` có
GVHD `GV001` theo seed), các trường dashboard mới `sv_chua_phan_cong` /
`so_sinh_vien_lop` / `giang_vien_huong_dan`.

`deploy/e2e-uc1.sh` tự dựng riêng một đợt đồ án khóa **K99** và dùng 5 tài
khoản seed dành riêng cho kịch bản tự động (tách biệt với các tài khoản dùng ở
demo thủ công phía trên): `GV030` (GVHD — kiểm tra tên, tạo và giao đề tài,
lưu nháp rồi gửi), `DTC235210040` và `DTC235210045` (lớp GV030 — nhận đề tài
được giao, chỉ thấy đề tài của mình), `GV024` (GV không phải GVHD) và
`DTC235210023` (lớp GV024 — không xem được đề tài lớp khác, sau đó được chuyển
sang lớp GV030 và nhận đề tài giao). Các bước kiểm: GV giao cho SV chưa được
phân công → 409; Bộ môn gán (`PUT /api/assignments`) + import CSV + danh sách
phân công; GV kiểm tra tên → 200, SV → 403; giao → Đã phân công + thông báo
SV; SV tạo/sửa/gửi và Bộ môn tạo đề tài → 403, route đăng ký/duyệt → 404, GV
không phải GVHD giao → 409, giao thêm cho SV đã có đề tài → 409, thiếu
`sinh_vien_id` → 422; đổi GVHD khi SV đã có đề tài Đã phân công → 409. Script
tự xóa toàn bộ dữ liệu nó tạo ra (đợt K99 + phân công GVHD + đề tài + kết quả
kiểm tra trùng lặp + thông báo phát sinh) khi kết thúc, kể cả khi có bước thất
bại giữa chừng.

`deploy/e2e-uc2-5.sh` chạy chuỗi đề cương → tiến độ → bảo vệ → lưu kho → thông
báo → dashboard qua Apache trên một đợt khóa **K98** riêng. Tài khoản dành
riêng (**không dùng cho demo thủ công**): `GV025` (GV không liên quan),
`GV026`–`GV028` (hội đồng), `GV029` (GVHD), `DTC235210037` (SV khác),
`DTC235210039` (SV chính). Khi kết thúc (kể cả lỗi giữa chừng) script xóa mọi
dữ liệu của đợt K98 (đề tài, đề cương, tài liệu + file vật lý, mốc/báo cáo tiến
độ, lịch/điểm bảo vệ, hội đồng vừa tạo, bản ghi kho) và thông báo của các tài
khoản trên phát sinh từ lúc script bắt đầu. Sau khi chạy không còn đợt K98/K99:

```bash
bash deploy/sql.sh "SELECT COUNT(*) FROM dot_do_an WHERE khoa IN ('K98','K99')"   # 0
```

## Dịch vụ AI kiểm tra trùng lặp

Phase 4 thêm hai service vào `deploy/docker-compose.yml`:

- **`ai`** — FastAPI của `ai-service/` (một worker uvicorn, chỉ mục FAISS trong bộ nhớ). Chỉ nằm trên mạng nội bộ của compose: **không publish cổng, không có route Apache**; Web API gọi `http://ai:8002` kèm header `X-API-Key`. Giới hạn bộ nhớ `AI_MEM_LIMIT` (mặc định `2g`; đo thực tế đỉnh ≈ 850 MiB). Trọng số mô hình cache trên volume **`ai-models`** (`/models`). Hệ thống file gốc chỉ đọc (`read_only`, `/tmp` là tmpfs) và mã nguồn trong image thuộc `root` — tiến trình `appuser` chỉ ghi được `/models` và `/tmp` (IN-07).
- **`ai-db-init`** — chạy một lần trước `ai`: tạo schema `thesis_ai` và hai tài khoản MySQL chỉ có quyền trên schema đó, chỉ kết nối được từ subnet `ntma-internal` (`172.28.238.%`): `thesis_ai` (SELECT/INSERT/UPDATE/DELETE — tiến trình phục vụ request) và `thesis_ai_migrate` (DDL). Không tài khoản nào đọc được `thesis_core` (WR-03).
- **`ai-migrate`** — one-shot, cùng image với `ai`: `alembic upgrade head` của `thesis_ai` bằng tài khoản `thesis_ai_migrate`; `ai` chỉ khởi động sau khi bước này xong và chạy bằng tài khoản `thesis_ai` (không DDL/DROP, `AI_MIGRATE_ON_START=0`).

### Biến môi trường (`deploy/.env`)

| Khóa | Ý nghĩa |
|---|---|
| `AI_API_KEY` | Khóa nội bộ Web API ↔ Dịch vụ AI (sinh ngẫu nhiên bởi `init.sh`) |
| `AI_DB_PASSWORD` | Mật khẩu tài khoản MySQL `thesis_ai` — chỉ DML (sinh bởi `init.sh`) |
| `AI_DB_MIGRATE_PASSWORD` | Mật khẩu tài khoản MySQL `thesis_ai_migrate` — DDL, chỉ `ai-migrate` dùng (sinh bởi `init.sh`; cài đặt cũ: chạy lại `bash deploy/init.sh` để bổ sung) |
| `AI_CLIENT` | `http` (mặc định — gọi dịch vụ AI thật) hoặc `stub` — **phương án dự phòng D-07**: Web API quay về bộ giả lập Jaccard của Phase 2/3, không cần container `ai` hoạt động |
| `AI_STUB_MODE` | Chỉ có hiệu lực khi `AI_CLIENT=stub`: `normal` hoặc `loi` (mô phỏng dịch vụ AI không phản hồi, UC0.6/UC0.7 - E2) |
| `AI_MODEL_PROFILE` | Mô hình embedding đã chốt: `bkai` (`bkai-foundation-models/vietnamese-bi-encoder` + tách từ underthesea); `e5` là phương án thay thế |
| `AI_MEM_LIMIT` | Giới hạn bộ nhớ container `ai` (mặc định `2g`) |

`init.sh` sinh các khóa này khi tạo `.env` mới, và **bổ sung các khóa còn thiếu vào một `.env` đã có** (giữ nguyên giá trị cũ) — chạy lại `bash deploy/init.sh` sau khi cập nhật từ Phase 3. Chỉ ghi giá trị trong `deploy/.env` (chmod 600, đã gitignore), không đưa vào tài liệu hay commit.

### Mô hình AI tải trước lúc cài đặt, máy chủ không có Internet

`bash deploy/install.sh` tải trọng số mô hình (~518 MiB) từ Hugging Face vào volume `ai-models` **lúc cài đặt** (D-02); service `ai` chạy với `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1` nên không bao giờ gọi Hugging Face lúc chạy — demo không phụ thuộc mạng ngoài. Tải lại thủ công (idempotent, vài giây khi đã có):

```bash
docker compose -f deploy/docker-compose.yml run --rm --no-deps -T \
  -e HF_HUB_OFFLINE=0 -e TRANSFORMERS_OFFLINE=0 --entrypoint python ai -m app.download_model
```

Máy chủ không có Internet: chạy lệnh trên ở nơi có mạng rồi sao chép volume `<project>_ai-models` sang (ENTRYPOINT của image là `docker-entrypoint.sh`, nên phải đổi `--entrypoint` như trên — nếu không container sẽ khởi động uvicorn thay vì tải mô hình).

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

**Tài khoản dành riêng — không dùng cho demo thủ công:** `DTC235210032`, `DTC235210074` (SV), `GV023` (GVHD), cùng `bomon`; khóa **K96** và **K97**. Trong mỗi đợt kiểm thử, `bomon` import phân công (`POST /api/assignments/import`) các SV này cho GVHD `GV023`, SV gửi đề tài và **`GV023` duyệt** (luồng 0015). `e2e-ai.sh` và `ai-nfr.sh` **dùng chung `DTC235210032` và `GV023` nên không bao giờ chạy song song** (`ai-nfr.sh` từ chối chạy nếu `DTC235210032` đang giữ một đề tài hoạt động). Hai script tự dọn dữ liệu, file và vector đã tạo; sau khi chạy:

```bash
bash deploy/sql.sh "SELECT COUNT(*) FROM dot_do_an WHERE khoa IN ('K96','K97','K98','K99')"   # 0
```

### Hạn chế đã biết

- **Thời gian kiểm tra tăng theo độ dài tài liệu** (~0,12 s CPU / 1000 ký tự trên máy phát triển: báo cáo ~100 trang ≈ 40 s, vượt mức 30 s của NFR-09 vốn đo trên đề cương/báo cáo ngắn). Web API đặt timeout `/check-document` theo độ dài: `AI_DOCUMENT_TIMEOUT_SECONDS` (24) + `AI_DOCUMENT_TIMEOUT_PER_1K_CHARS` (0,25) × nghìn ký tự, trần `AI_DOCUMENT_TIMEOUT_MAX_SECONDS` (240, dưới `DOCUMENT_CHECK_TIMEOUT_SECONDS` = 300). Kiểm tra tên đề tài không bị chặn trong lúc đó (dịch vụ AI mã hóa theo lô con); `ai-nfr.sh` đo cả hai.
- **Văn bản trích xuất dài hơn `AI_DOCUMENT_MAX_CHARS` (800 000 ký tự ≈ 230 trang) không được gửi sang dịch vụ AI** (WR-05): nộp vẫn thành công (UC0.7 E1), kết quả kiểm tra là "Lỗi" kèm lý do "Tài liệu quá dài để kiểm tra trùng lặp tự động", nút "Kiểm tra lại" bị ẩn (API trả 409 với cùng lý do) — cần nộp bản đã bỏ phụ lục/mã nguồn dài.

- **Đưa tài liệu vào chỉ mục AI chạy nền sau kiểm tra** (WR-06): lần ingest thành công đóng dấu `tai_lieu_do_an.da_index_luc`; tài liệu lỡ ingest (dịch vụ AI tạm ngừng) còn NULL, được thử lại sau mỗi lần ingest thành công kế tiếp (tối đa 3 tài liệu/lần) và hiện ở ô "Tài liệu chưa vào chỉ mục AI" trên dashboard Bộ môn; thử lại ngay: `docker compose -f deploy/docker-compose.yml exec -T api python -m app.services.ai_index backfill --loai DOCUMENT --chua-index`.
- **Gỡ vector khỏi chỉ mục AI chạy nền, lỗi chỉ ghi log** (WR-04): xóa bản ghi kho gỡ vector ARCHIVE của nó, chốt bảo vệ gỡ vector TOPIC của đề tài vừa vào kho (bản ghi ARCHIVE thay thế) — bằng `/ingest` văn bản rỗng. Nếu lần gỡ đó lỗi (dịch vụ AI tạm ngừng), kết quả vẫn đúng vì Web API bỏ qua `ref_id` không còn tồn tại; gỡ thủ công: `docker compose -f deploy/docker-compose.yml exec -T api python -m app.services.ai_index purge --loai ARCHIVE --ids <id>`.
- **Danh sách phần mẫu chung là giả định `[ASSUMED]`** (bìa, lời cam đoan, mục lục, danh mục, tài liệu tham khảo, phụ lục…) cho tới khi có mẫu đề cương/báo cáo chính thức của Khoa — khi có mẫu, cập nhật `ai-service/app/nlp/boilerplate.py` rồi chạy lại hiệu chỉnh (`calibration/calibrate.py tune|evaluate`). Để danh sách này không thành chỗ giấu nội dung, tiêu đề mục mẫu chỉ bỏ nguyên mục ở phần đầu/phần cuối tài liệu và có trần độ dài; MH-09/MH-14 luôn ghi số câu đã so sánh, số dòng và % nội dung bị loại, và cảnh báo khi hơn 50 % nội dung bị loại (tài liệu seed tổng hợp ngắn bị loại tới 45 %).
- **Số liệu chất lượng phát hiện đo trên dữ liệu tổng hợp** (`seed-data/`, sinh bằng `tools/datagen`), không phải đồ án thật của sinh viên; cảnh báo tên đề tài và đoạn trùng ngữ nghĩa là **gợi ý** để giảng viên xem lại, không phải kết luận.
- "Vượt ngưỡng cảnh báo" so **tỷ lệ trùng với một đồ án nguồn cao nhất** (`ty_le_nguon_cao_nhat`) với ngưỡng (≥), không so tỷ lệ tổng: bài khớp rải rác nhiều đồ án (P21: tổng 6.0 %, với đồ án trùng nhiều nhất 1.51 %) được đánh giá theo từng đồ án. `NGUONG_TAI_LIEU` được khớp trên tỷ lệ tới đồ án nguồn A của cặp có chủ đích; trên tập hiệu chỉnh 10.4 % vẫn tách được hai lớp theo thống kê triển khai (âm lớn nhất 3.69 %, dương nhỏ nhất 20.79 %). **Cảnh báo sai đã biết:** P19-B (cùng lĩnh vực, tập kiểm chứng) trùng ngữ nghĩa 22.81 % với P15-A — một đồ án khác cùng chủ đề y tế — nên bị cảnh báo (độ chính xác kiểm chứng 7/8, mục 4.x.3). Tỷ lệ theo từng đồ án trên MH-14/MH-09 là giá trị dịch vụ AI trả (`do_an_trung`), lưu ở `chi_tiet_trung_lap.ty_le_nguon`.

### Kịch bản demo AI (thao tác trên trình duyệt)

> Cho buổi bảo vệ dùng mục "Kịch bản demo bảo vệ (Phase 5)" ở trên; mục này giữ lại làm hướng dẫn thao tác chi tiết.

Chuẩn bị: stack đã dựng, `bash deploy/seed-ai.sh` đã chạy. Dùng các tài khoản **không** thuộc danh sách dành riêng (tự động: SV thứ 93–100 của danh sách (DTC235210023…DTC235210045), GV023–GV030; demo bảo vệ: DTC235200139, DTC235200258, DTC235200325, DTC235200340, DTC235270078, GV011–GV014), vd. `DTC235200159`, `DTC235200379`, `GV010`; mật khẩu `SEED_DEFAULT_PASSWORD`.

1. **SC1 — tên đề tài diễn đạt lại.** Đăng nhập GVHD `GV010` (GVHD của `DTC235200159`) → **Giao đề tài** → chọn SV → nhập tên "Sử dụng SQL Server để hạch toán thu chi doanh nghiệp cho công ty cổ phần Hoàng Long" rồi rời ô → cảnh báo "Phát hiện … đề tài tương tự trong kho" với đồ án kho "Ứng dụng SQL Server trong quản lý kế toán tại công ty CP Hoàng Long (K21)" kèm tỷ lệ (≈ 82%). Dán cùng tên ở dạng Unicode tổ hợp (NFD, vd. gõ bằng bộ gõ khác) cho cùng kết quả. Một tên cùng lĩnh vực nhưng khác đề tài không bị cảnh báo trùng kho.
2. **SC2 — tài liệu chép nguyên văn.** Để `DTC235200159` có đề tài đã phân công với GVHD `GV010` (seed phân công `DTC235200159` → `GV010`; `GV010` giao đề tài cho `DTC235200159` ở bước 1 bằng "Vẫn giao đề tài"). Ở **Đề cương**, nộp `seed-data/tai-lieu/P01-B.pdf` → trạng thái "Đang kiểm tra" rồi "Hoàn tất - 50.3%" (không cần tải lại trang). Bấm "Xem kết quả" (MH-14): tỷ lệ tổng 50.3%, ngưỡng 10.4%, đồ án trùng "Phát triển mô hình thống kê điểm số … Metabase (K21)" 50.3%; mỗi đoạn đặt cạnh đoạn nguồn, cụm từ trùng được tô, nhãn "Trùng nguyên văn", ghi chú đã loại trừ phần mẫu chung (FR-AI-02). Đăng nhập `GV010` → **Duyệt đề cương** → "Duyệt": panel MH-09 hiện cùng tỷ lệ, "Vượt ngưỡng cảnh báo" và "Số đoạn trùng: 7 (7 trùng nguyên văn)". Nộp một file diễn đạt lại (vd. `P11-B.docx`) cho một SV khác: các đoạn mang nhãn "Trùng ngữ nghĩa", ít cụm từ được tô hơn.
3. **SC3 — bảng kiểm chứng trên 50 file.** Mở `docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md`: điểm từng cặp của 25 cặp (chép nguyên văn, diễn đạt lại bị cảnh báo; cùng lĩnh vực, không liên quan dưới ngưỡng) trên tập hiệu chỉnh và tập kiểm chứng giữ lại, cùng mô hình đã chốt (`02-so-sanh-mo-hinh-embedding.md`).
4. **SC4 — Bộ môn đổi ngưỡng.** Đăng nhập `bomon` → **Ngưỡng trùng lặp**: ba ngưỡng kèm giải thích, giá trị đề xuất và người cập nhật. Đặt "Ngưỡng tên đề tài" = 99 → "Lưu cấu hình" → xác nhận. `GV010` kiểm tra lại tên ở bước 1 → không còn cảnh báo. Bộ môn bấm "Khôi phục giá trị đề xuất" → lưu → cảnh báo trở lại. Kết quả đã kiểm tra trước đó vẫn hiện ngưỡng lúc kiểm tra.
5. **SC5 — bản ghi mới được index ngay; dịch vụ AI không lộ ra ngoài.** `bomon` → **Kho đồ án** → thêm bản ghi "Xây dựng hệ thống quản lý phòng thí nghiệm hóa học cho trường cao đẳng y tế" (khóa K22) → cột index chuyển "Đã index" sau vài giây. `DTC235200159` kiểm tra tên "Phát triển phần mềm quản lý phòng thí nghiệm hóa học tại trường cao đẳng y tế" → thấy ngay bản ghi vừa thêm (≈ 90%), không phải tính lại embedding toàn kho (e2e-ai kiểm `encode_calls` +1). Xóa bản ghi sau demo (vector của nó được gỡ khỏi chỉ mục ngay sau khi xóa). Phần cô lập: chạy `bash deploy/ai-nfr.sh` (hoặc `e2e-ai.sh`) — host không kết nối được cổng 8002, thiếu/sai khóa → 401, Apache không có route tới dịch vụ AI, tài khoản DB `thesis_ai` bị từ chối trên `thesis_core`; kèm số đo thời gian kiểm tra tên (P95 ≈ 0,05 s) và nộp → hoàn tất (P95 ≈ 3 s; báo cáo ~350 000 ký tự ≈ 42 s, kiểm tra tên chen giữa vẫn < 0,4 s).

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
