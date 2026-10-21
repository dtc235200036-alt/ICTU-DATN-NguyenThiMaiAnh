# Ảnh chụp màn hình chương 4 (dữ liệu hư cấu)

36 ảnh trong `bao-cao/tai_nguyen/chuong_4/c*.png` được chụp ngày 2026-10-21 trên một stack cô lập,
không phải trên máy chủ triển khai và không dùng dữ liệu thật. Ảnh cũ trong `../anh/` (14/10) chứa
họ tên sinh viên thật nên không dùng cho báo cáo.

## Cách dựng stack cô lập

1. `git archive HEAD` (commit `aa4b478`) ra một thư mục riêng (`<ban-sao>`).
2. `python3 gen_seed.py <kho-goc> <ban-sao>/backend/app/seed_data` — sinh `sinh_vien.csv`,
   `giang_vien.csv` hư cấu: giữ thứ tự dòng, lớp, học vị, bộ môn; giữ các mã SV mà script trong
   `deploy/`, `tools/`, `backend/tests`, `frontend/src` tham chiếu; mọi họ tên, email và các mã SV
   còn lại là giá trị hư cấu (hạt giống 20261021). Email GV dạng `gvNNN@ntma-demo.edu.vn`.
3. `source stack-env.sh; bash stack-up.sh` — project Compose `ntmac4`, cổng 18080/18443, MySQL 3307;
   chạy `init.sh`, build image AI, tải mô hình, `docker compose up --wait`, `seed-ai.sh`.
   Lần chạy 21/10 trên máy không có bộ đệm build: mô hình sẵn sàng 333 s, stack lên 424 s,
   nạp kho xong 545 s.
4. Email tài khoản SV do seed sinh từ mã SV được đổi sang tên miền `sv.ntma-demo.edu.vn` bằng SQL
   trên CSDL của bản sao (bảng `tai_khoan`, `sinh_vien`, `giang_vien`).
5. `bash deploy/demo-state.sh` — trạng thái demo (5 SV, 4 GV). Bản sao sửa một chỗ: sau khi GVHD
   duyệt, chờ `GVHD_DA_DUYET` rồi đặt đề cương sang `DA_DUYET` bằng SQL, vì script gốc chưa theo
   luồng hai cấp.
6. `python3 dung-trang-thai-de-cuong.py` — dựng thêm 4 đề cương của luồng hai cấp qua API
   (đúng mẫu tên chờ nộp, sai tên tệp, chờ Bộ môn, đã phê duyệt kèm PDF ký bằng chứng thư thử
   nghiệm `backend/tests/pdf_sign_helper.py`). Mật khẩu đọc từ container, không in ra.

## Chụp

```bash
uv run --no-project --with websockets python3 tools/demo/chay-kich-ban.py \
  kich-ban-anh-c4.json --out-dir <thu-muc-anh> --json anh-c4.json
```

- `kich-ban-anh-c4.json`: 38 bước, khung nhìn 1440×900, qua Apache HTTPS. Kết quả `anh-c4.json`:
  38/38 OK, 145,8 s. Hai ảnh không đưa vào báo cáo: danh sách đề cương của Bộ môn (trùng nội dung
  với ảnh GV) và Tiến độ toàn khoa (cột Đề tài bị ép hẹp, mỗi từ một dòng — lỗi giao diện cần sửa).
- `kham-pha.json`: mở 35 màn hình của ba vai trò ở 1440 px, chỉ đọc. Kết quả `kham-pha-kq.json`:
  35/35 OK, `scrollWidth` lớn nhất 1440 px — dùng làm số đo NFR-16 của lần 21/10.
- Ảnh trang dài được cắt bỏ thanh menu trái 220 px để chữ đủ lớn khi in.

Dừng và xóa stack: `source stack-env.sh; cd $L; docker compose -f deploy/docker-compose.yml down -v`.
