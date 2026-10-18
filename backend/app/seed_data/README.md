# seed_data

`app/seed.py` đọc hai file CSV trong thư mục này khi khởi động (`SEED_ON_START=true`).
Đây là danh sách SV/GV thật nên **không được commit** (đã có trong `.gitignore`); hãy tự đặt file vào đây trước khi chạy.

- `sinh_vien.csv` — cột: `ma_so_sinh_vien,ho_ten,lop`
- `giang_vien.csv` — cột: `ma_giang_vien,ho_ten,hoc_vi,email,bo_mon`

Mã hóa UTF-8. Các script trong `deploy/` và `tools/demo/` đăng nhập bằng một số mã SV cụ thể, nên danh sách cần chứa các mã đó.
