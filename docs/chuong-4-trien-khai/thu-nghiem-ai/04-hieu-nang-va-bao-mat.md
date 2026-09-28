## 4.x.4 Hiệu năng và bảo mật của dịch vụ kiểm tra trùng lặp

> **Mã PI:** 3.4, 4.1 — **Yêu cầu:** AISV-01, AISV-02, AISV-03, AISV-06 (NFR-07..NFR-11)

> Số liệu trong trang này do `bash deploy/ai-nfr.sh --report docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md` đo và ghi tự động ngày 2026-09-28 — không sửa tay.

### Mục tiêu

Kiểm chứng các yêu cầu phi chức năng NFR-07..NFR-11 (mục 2.4, `docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md`) của dịch vụ AI trên stack triển khai thật (Apache → Web API → dịch vụ AI, MySQL), với kho dữ liệu thử nghiệm đã seed đủ (DATA-02, DATA-03).

### Môi trường đo

| Thành phần | Giá trị |
|---|---|
| Máy | Máy phát triển dùng chung (không phải server triển khai) — 16 CPU logic (12th Gen Intel(R) Core(TM) i5-12500H), RAM 15.3 GiB, chạy đồng thời các ứng dụng khác |
| Dịch vụ AI | Container `ai` (CPU, `TORCH_THREADS=4`, trần bộ nhớ 2048 MiB), hồ sơ mô hình `bkai` — `bkai-foundation-models/vietnamese-bi-encoder@84f9d9ada0d1` |
| Kho đã index | 300 tiêu đề (300 đề tài kho K18–K22) · 2208 câu tài liệu (25 đồ án nguồn có báo cáo cuối) |
| Đường đi của request | NFR-08: gọi thẳng dịch vụ AI trong mạng nội bộ (không tính độ trễ mạng client, đúng phương pháp của NFR-08); NFR-09/10: qua Apache HTTPS → Web API → BackgroundTasks → dịch vụ AI |

### Kết quả

| NFR | Chỉ tiêu | Cách đo | Kết quả đo | Đạt? |
|---|---|---|---|---|
| NFR-07 | Dịch vụ AI không có đường public; thiếu khóa -> 401 | Host gọi 127.0.0.1:8002; trong mạng nội bộ gọi /check-title thiếu / sai / đúng X-API-Key; tìm route trong ntma.conf và POST https://localhost/check-title; tài khoản DB thesis_ai đọc thesis_core và CREATE TABLE trên thesis_ai | Host không kết nối được; mã 401 401 200; không có route (Apache trả 200 là trang SPA); thesis_core: DENIED | Đạt |
| NFR-08 | P95 kiểm tra tên đề tài ≤ 5 s | 20 lời gọi trực tiếp POST /check-title (trong container api, kèm khóa), kho 300 tiêu đề | P50 47 ms, **P95 52 ms**, max 61 ms | Đạt |
| NFR-09 | P95 nộp -> Hoàn tất ≤ 30 s | Nộp lần lượt 20 file B khác nhau qua Apache, thăm dò GET /api/documents/{id}/check mỗi 0,25 s | P50 1.41 s, **P95 3.02 s**, max 3.03 s; 20/20 HOAN_TAT, 0 LOI | Đạt |
| NFR-10 | API nộp trả phản hồi ≤ 2 s | Thời gian phản hồi 202 của POST /api/outlines/{id}/submit (cùng 20 lần nộp) | P95 0.051 s, **max 0.058 s** | Đạt |
| NFR-09 (dài) | Báo cáo ~100 trang hoàn tất trong timeout của Web API; kiểm tra tên chen giữa không bị chặn (< 4 s) | POST /check-document 350000 ký tự qua AiClientHttp (timeout theo độ dài 111.5 s); 5 lần /check-title (timeout 4 s) gửi trong lúc đó | 2333 câu, **41.71 s**; kiểm tra tên chen giữa: 131 ms, 353 ms, 239 ms, 183 ms, 297 ms | Đạt |
| NFR-11 | Ingest 1 bản ghi = 1 lần encode | encode_calls (/health) trước và sau khi Bộ môn thêm 1 bản ghi kho (chờ DA_INDEX) | 61 -> 62 (**+1**) | Đạt |
| Bộ nhớ | Container ai < 2048 MiB, không OOM | docker stats trước/sau vòng NFR-09; đỉnh cgroup memory.peak; State.OOMKilled | 640.8MiB -> 705.3MiB; **đỉnh 720 MiB**; OOMKilled=false | Đạt |

### Chi tiết NFR-09 / NFR-10 theo từng file

Mỗi file là một phiên bản đề cương mới của cùng một đề tài (GVHD yêu cầu sửa giữa hai lần nộp); các phiên bản trước của đề tài nằm trong danh sách loại trừ nên không bao giờ khớp với nhau. Tỷ lệ là tỷ lệ tương đồng tổng hợp do dịch vụ AI trả về (so với 25 đồ án nguồn và các tài liệu đã nộp trước đó).

| # | File | Phản hồi nộp (s) | Nộp → Hoàn tất (s) | Trạng thái | Tỷ lệ (%) | Số đoạn trùng |
|---:|---|---:|---:|---|---:|---:|
| 1 | P01-B.pdf | 0.042 | 1.42 | HOAN_TAT | 50.3 | 7 |
| 2 | P02-B.docx | 0.032 | 1.12 | HOAN_TAT | 48.04 | 5 |
| 3 | P03-B.pdf | 0.040 | 3.02 | HOAN_TAT | 51.03 | 17 |
| 4 | P04-B.docx | 0.031 | 0.85 | HOAN_TAT | 49.33 | 5 |
| 5 | P05-B.pdf | 0.038 | 3.03 | HOAN_TAT | 44.83 | 13 |
| 6 | P06-B.docx | 0.038 | 1.41 | HOAN_TAT | 49.74 | 6 |
| 7 | P07-B.pdf | 0.058 | 1.44 | HOAN_TAT | 57.76 | 9 |
| 8 | P08-B.pdf | 0.037 | 1.13 | HOAN_TAT | 21.23 | 5 |
| 9 | P09-B.docx | 0.038 | 1.13 | HOAN_TAT | 17.38 | 4 |
| 10 | P10-B.pdf | 0.039 | 1.13 | HOAN_TAT | 20.88 | 4 |
| 11 | P11-B.docx | 0.046 | 1.43 | HOAN_TAT | 25.54 | 6 |
| 12 | P12-B.pdf | 0.051 | 2.76 | HOAN_TAT | 33.16 | 14 |
| 13 | P13-B.docx | 0.033 | 1.39 | HOAN_TAT | 30.29 | 4 |
| 14 | P14-B.pdf | 0.047 | 3.02 | HOAN_TAT | 34.09 | 18 |
| 15 | P15-B.pdf | 0.045 | 2.75 | HOAN_TAT | 4.78 | 4 |
| 16 | P16-B.docx | 0.039 | 1.12 | HOAN_TAT | 0.0 | 0 |
| 17 | P17-B.pdf | 0.048 | 1.41 | HOAN_TAT | 0.0 | 0 |
| 18 | P18-B.docx | 0.042 | 1.13 | HOAN_TAT | 2.86 | 1 |
| 19 | P19-B.pdf | 0.043 | 2.75 | HOAN_TAT | 23.96 | 14 |
| 20 | P20-B.docx | 0.035 | 1.14 | HOAN_TAT | 0.0 | 0 |

Thời gian NFR-08 từng lời gọi (ms): 45, 51, 48, 45, 48, 44, 44, 50, 50, 43, 52, 46, 45, 61, 47, 44, 45, 44, 49, 50.

### Nhận xét

- Kiểm tra tài liệu chạy nền: API nộp trả 202 ngay sau khi lưu file và trích xuất văn bản, nên thời gian phản hồi (NFR-10) không phụ thuộc thời gian suy luận của mô hình.
- Thời gian nộp → Hoàn tất gồm độ phân giải thăm dò 0,25 s; phần lớn còn lại là thời gian mã hóa các câu của tài liệu nộp trên CPU (tài liệu dài — báo cáo cuối — tốn nhiều hơn đề cương).
- Tài liệu dài (CR-02): thời gian mã hóa tăng tuyến tính theo số câu (~0,1 s CPU / 1000 ký tự), nên báo cáo ~100 trang vượt chỉ tiêu 30 s của đề cương/báo cáo thông thường; Web API vì vậy đặt timeout `/check-document` theo độ dài (`AI_DOCUMENT_TIMEOUT_SECONDS` + `AI_DOCUMENT_TIMEOUT_PER_1K_CHARS` × nghìn ký tự, trần `AI_DOCUMENT_TIMEOUT_MAX_SECONDS`). Dịch vụ AI mã hóa theo lô con 32 câu và chỉ giữ khóa mô hình trong từng lô con, nên kiểm tra tên gửi giữa chừng chỉ chờ tối đa một lô con; ingest ngay sau kiểm tra dùng lại vector đã mã hóa (không mã hóa lần hai).
- Embedding của kho được tính một lần lúc ingest và giữ trong chỉ mục FAISS trong bộ nhớ; thêm một bản ghi chỉ mã hóa đúng bản ghi đó (NFR-11).
- Chất lượng phát hiện (tỷ lệ cảnh báo đúng/sai trên các cặp có chủ đích) được trình bày ở mục 4.x.3 — [03-hieu-chinh-nguong.md](03-hieu-chinh-nguong.md).

### Chạy lại

```bash
bash deploy/seed-ai.sh          # nếu kho chưa seed
bash deploy/ai-nfr.sh --report docs/chuong-4-trien-khai/thu-nghiem-ai/04-hieu-nang-va-bao-mat.md
```

Phase 5 chạy lại đúng lệnh này trên server triển khai (Apache + HTTPS) và thay các số liệu ở trên bằng số đo trên server.
