# Chạy lại `verify-all.sh --report` ngày 2026-10-21

Kết quả của lần chạy lại toàn bộ kiểm thử tự động sau khi có luồng duyệt đề cương hai cấp
(migration 0016). Thư mục cha giữ nguyên kết quả ngày 2026-10-14 (commit `ed412e1`) để so sánh.

- Mã nguồn: bản `git archive` của commit `aa4b478` (HEAD lúc chạy). Vì bản sao không phải
  kho git nên trường `commit` trong `tong-hop.json` là `?`.
- Môi trường: stack cô lập trên máy phát triển (AMD Ryzen 7 7735HS, 16 luồng, 25,9 GiB RAM,
  Ubuntu 26.04 LTS), project Compose `ntmac4`, cổng HTTP 18080 / HTTPS 18443, MySQL 3307.
  Danh sách SV/GV là bản hư cấu cùng cấu trúc và số lượng (580 SV, 70 GV), sinh bằng
  `../../anh-bao-cao/gen_seed.py`; kho đề tài và 50 tệp tài liệu là dữ liệu tổng hợp trong `seed-data/`.
- Trước khi chạy: `bash deploy/demo-state.sh` (bản sao đã sửa bước kiểm tra trạng thái sau khi GVHD
  duyệt cho đúng luồng hai cấp, xem bên dưới). Máy dùng chung với các việc khác trong lúc đo.
- Lệnh: `bash deploy/verify-all.sh --report`, 430 s, mã thoát 1 (4 bước FAIL).

| Tệp | Nội dung |
|---|---|
| `tong-hop.json` | Kết quả từng bước, số liệu dữ liệu thử nghiệm và NFR-01..19 do `verify-all.sh` sinh |
| `nhat-ky-verify-all.log` | Nhật ký đầy đủ (đường dẫn tạm được thay bằng `<ban-sao>`, `<scratch>`, `$TMP`) |
| `04-hieu-nang-va-bao-mat.md` | Báo cáo `ai-nfr.sh` (NFR-07..11) của lần chạy này |

## Kết quả từng bước

| # | Bước | 14/10 (`ed412e1`) | 21/10 (`aa4b478`) | Ghi chú lần 21/10 |
|---:|---|---|---|---|
| 1 | Tình trạng stack | OK | FAIL | 8/9 kiểm tra OK. Kiểm tra cuối gọi cứng `https://localhost/api/health` (cổng 443), stack cô lập dùng 18443. Gọi lại đúng cổng: `{"status":"ok","db":"ok"}`. Lỗi do môi trường đo |
| 2 | Dữ liệu thử nghiệm | OK | OK | |
| 3 | Smoke test HTTPS | OK (26) | OK (26) | |
| 4 | Pytest Web API | 54 passed | 67 passed | Thêm kiểm thử luồng Bộ môn phê duyệt (`test_outline_bo_mon.py`) |
| 5 | Pytest dịch vụ AI | 8 passed | 8 passed | 173 s do lần đầu `uv sync` cài torch |
| 6 | E2E UC1 | OK (15) | OK (15) | |
| 7 | E2E UC2–UC5 | OK (67) | FAIL | 11 kiểm tra OK rồi dừng: kịch bản còn chờ đề cương `DA_DUYET` ngay sau khi GVHD duyệt, luồng mới cho `GVHD_DA_DUYET`. Kịch bản chưa cập nhật theo luồng hai cấp; các kiểm tra UC3–UC5 phía sau không chạy |
| 8 | E2E dịch vụ AI | OK (31) | OK (31) | |
| 9 | NFR-07..11 dịch vụ AI | OK | OK | Xem `04-hieu-nang-va-bao-mat.md` |
| 10 | NFR hệ thống | OK (14) | OK (14) | |
| 11 | Đối chiếu ERD | OK | FAIL | `erd.puml` trong commit `aa4b478` thiếu `dinh_huong`, `luot_duyet_bo_mon` và 4 cột mới. Chạy lại với `erd.puml` đang được cập nhật cho chương 3 (bản làm việc 21/10): `OK: schema thesis_core khớp erd.puml` |
| 12 | Không còn dữ liệu kiểm thử | OK | OK | |
| 13 | NFR-16 (Chrome headless 1440 px) | OK (25) | FAIL | Lần đầu: máy đo thiếu thư viện `websockets`. Chạy lại có `websockets`: `FAIL 0/25` ở bước đăng nhập — `tools/demo/kich-ban-anh.json` còn tìm nhãn cũ 'Mã SV/GV hoặc email' (nay là 'Tài khoản'). Kịch bản chưa cập nhật |
| 14 | Trạng thái demo không đổi | OK | OK | |

Dòng NFR-16 trong `tong-hop.json` ghi "Đạt 29/29 (đo lúc 2026-10-14…)" vì `verify-all.sh` lấy
lại `anh-chup.json` cũ khi bước đo trực tiếp lỗi — **không phải số đo của lần này**. Số đo thay thế
cho NFR-16 ở lần này: kịch bản `../../anh-bao-cao/kham-pha.json` mở 35 màn hình của ba vai trò ở
1440 px, 35/35 OK, `scrollWidth` lớn nhất 1440 px (`../../anh-bao-cao/kham-pha-kq.json`); kịch bản
chụp ảnh chương 4 (`../../anh-bao-cao/kich-ban-anh-c4.json`) 38/38 bước OK.

Dòng NFR-04 ghi "KHÔNG ĐẠT" chỉ vì bước 7 FAIL (NFR-04 tổng hợp kết quả pytest, smoke, e2e-uc1,
e2e-uc2-5); pytest, smoke và e2e-uc1 đều đạt, mã 403 chéo vai trò đúng.

## Việc cần làm (ngoài phạm vi chương 4)

- Cập nhật `deploy/e2e-uc2-5.sh`, `deploy/demo-state.sh` và `tools/demo/kich-ban-anh.json`
  theo luồng duyệt hai cấp và nhãn đăng nhập mới.
- `verify-all.sh --buoc stack` nên đọc cổng HTTPS từ cấu hình thay vì cố định 443.
- Commit `erd.puml` mới của chương 3.
