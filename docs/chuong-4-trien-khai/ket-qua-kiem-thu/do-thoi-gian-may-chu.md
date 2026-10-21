# Đo thời gian phản hồi trên máy chủ triển khai (chỉ đọc)

- Thời điểm: 2026-10-21. Phiên bản mã nguồn trên máy chủ: commit `aa4b478`.
- Máy chủ: máy ảo Ubuntu 22.04.5 LTS, 6 vCPU Intel Xeon Platinum 8272CL 2,60 GHz, RAM 16 GB,
  Docker 29.6.1, Docker Compose 5.3.1. Máy chủ dùng chung với các dự án khác, nên Apache của
  NTMA nghe cổng 8088 (HTTP) và 8443 (HTTPS) thay cho 80/443.
- Cách đo: từ chính máy chủ, gọi qua Apache HTTPS (`https://localhost:8443`), đo `time_total`
  của curl. Chỉ dùng các lời gọi không ghi dữ liệu: `POST /api/topics/check-title` (kiểm tra tức
  thời, không lưu kết quả), `GET /api/archive?q=...`, `GET /api/topics`, `GET /api/health`.
  Kho trên máy chủ lúc đo: 306 vector tiêu đề, 2 591 vector câu tài liệu, 0 bản ghi thiếu embedding.
- Mỗi phép đo 20 lần. Với 20 mẫu, P95 theo hạng gần nhất là giá trị thứ 19, nên giá trị lớn nhất
  bên dưới là chặn trên của P95.

| Phép đo | Vai trò | Số lần | Mã HTTP | P50 (s) | Lớn nhất (s) | Chỉ tiêu (P95) | Đạt? |
|---|---|---:|---|---:|---:|---|---|
| Kiểm tra trùng tên đề tài (20 truy vấn đầu của `seed-data/truy-van-ten-de-tai.csv`) | GV | 20 | 20 × 200 | 0.136 | 2.025 | ≤ 5 s (NFR-08) | Đạt |
| Tra cứu kho theo từ khóa | Bộ môn | 20 | 20 × 200 | 0.029 | 0.034 | ≤ 1 s (NFR-12) | Đạt |
| Danh sách đề tài | Bộ môn | 20 | 20 × 200 | 0.034 | 0.266 | ≤ 1 s (NFR-12) | Đạt |
| `GET /api/health` | — | 1 | 200 | 0.011 | 0.011 | — | — |

Bộ nhớ container lúc đo (`docker stats`): api 409 MiB / trần 1 GiB, ai 525 MiB / trần 2 GiB,
mysql 531 MiB, apache 28 MiB.

Lần đo này chỉ ghi P50 và giá trị lớn nhất, không ghi thời gian của từng lời gọi.

Các phép đo có ghi dữ liệu (NFR-09/NFR-10: nộp 20 tệp; NFR-05: khóa/mở khóa tài khoản) không chạy
trên máy chủ vì kho trên máy chủ đang được nạp dữ liệu đồ án thật; các số liệu đó lấy từ stack
cục bộ (`tong-hop.json`, `../thu-nghiem-ai/04-hieu-nang-va-bao-mat.md`).
