## 4.x.3 Hiệu chỉnh và kiểm chứng ngưỡng cảnh báo trùng lặp

> **Mã PI:** 3.4 — **Yêu cầu:** DATA-03, AISV-03, AISV-04

<!-- Tệp này do `ai-service/calibration/calibrate.py evaluate --report` sinh ra từ `calibration/nguong-de-xuat.json` và `calibration/ket-qua-chi-tiet.json`; không sửa tay. -->

### Mục tiêu

Dịch vụ AI cảnh báo trùng lặp dựa trên bốn ngưỡng: ngưỡng tên đề tài khi sinh viên đăng ký (AISV-03), ngưỡng ngữ nghĩa và ngưỡng nguyên văn ở mức câu, và ngưỡng tài liệu quyết định một bài nộp có bị cảnh báo trùng với một đồ án trong kho hay không (AISV-04). Theo quyết định D-04, giá trị mặc định của các ngưỡng **phải đến từ hiệu chỉnh** chứ không đặt theo cảm tính. Theo D-06, ngưỡng chỉ được khớp trên tập hiệu chỉnh (`HIEU_CHINH`) rồi giữ nguyên để kiểm chứng trên tập giữ lại (`KIEM_CHUNG`). Mục này cung cấp bảng kiểm chứng theo từng cặp tài liệu mà DATA-03 và tiêu chí thành công số 3 của Phase 4 yêu cầu.

### Dữ liệu và mô hình

- Bộ dữ liệu tổng hợp mô tả ở [mục 4.x.1](01-du-lieu-thu-nghiem.md): kho 300 đề tài khóa K18–K22, 25 cặp tài liệu A/B (DOCX/PDF) và 80 truy vấn tên đề tài có nhãn.
- Tập hiệu chỉnh: 17 cặp, 56 truy vấn. Tập kiểm chứng (giữ lại, không dùng để khớp): 8 cặp, 24 truy vấn.
- Mô hình embedding đã chốt ở [mục 4.x.2](02-so-sanh-mo-hinh-embedding.md): `bkai-foundation-models/vietnamese-bi-encoder` (profile `bkai`).
- Văn bản được trích xuất bằng bản sao đúng từng dòng của hàm `extract_text` phía Web API, rồi đi qua đúng pipeline của dịch vụ AI (`ingest` → `score_document` → `check_document`, `check_title`). Kho được dựng trên một cơ sở dữ liệu SQLite tạm theo cùng migration với MySQL. Tài liệu A được nạp vào kho; tài liệu B chỉ được kiểm tra, giống như bài nộp mới được kiểm tra trước khi vào kho.

### Phương pháp

1. **Mức câu.** Mỗi câu của tài liệu B (sau khi lọc phần mẫu chung) có hai điểm: cosine embedding tốt nhất (ngữ nghĩa) và Jaccard MinHash tốt nhất trên k-gram âm tiết (nguyên văn) so với mọi câu trong kho. Nhãn của câu lấy từ nguồn gốc đoạn văn ghi trong manifest: *chép nguyên văn*, *diễn đạt lại* hoặc *tự viết*.
2. **Ngưỡng nguyên văn**: dương = câu chép nguyên văn, âm = mọi câu còn lại (kể cả câu diễn đạt lại, vốn để tín hiệu ngữ nghĩa xử lý). **Ngưỡng đoạn (ngữ nghĩa)**: dương = câu diễn đạt lại, âm = câu tự viết.
3. **Ngưỡng tài liệu**: với hai ngưỡng câu đã cố định, `check_document` cho tỷ lệ ký tự của B bị gán cho đồ án nguồn A (*tỷ lệ theo đồ án nguồn*). Cặp bị cảnh báo khi tỷ lệ này ≥ ngưỡng tài liệu. Dương = cặp chép nguyên văn và diễn đạt lại. *Tỷ lệ tổng* (phần của B khớp với bất kỳ tài liệu nào trong kho) được báo cáo kèm.
4. **Ngưỡng tên đề tài**: điểm cao nhất của `check_title` trên kho 300 đề tài; dương = truy vấn diễn đạt lại một đề tài có trong kho.
5. **Cách chọn ngưỡng**: `sklearn.metrics.roc_curve` và chỉ số **Youden J = TPR − FPR**. Mọi ngưỡng nằm giữa điểm đạt J lớn nhất và điểm liền dưới nó cho cùng một kết quả phân loại trên tập hiệu chỉnh, nên ngưỡng được đặt ở **trung điểm của khoảng đó** (cột *Khoảng chọn*). Khi tín hiệu tách hoàn toàn tập hiệu chỉnh, dùng **trung điểm** giữa điểm âm lớn nhất và điểm dương nhỏ nhất để có biên an toàn. Ngưỡng tính theo %, một chữ số thập phân; gắn cờ khi điểm ≥ ngưỡng. Kích thước shingle MinHash chọn trong {3, 4, 5} theo AUC nguyên văn lớn nhất (hòa → 4).
6. **Luật đoạn cho tín hiệu ngữ nghĩa**: `check_document` chỉ giữ cờ ngữ nghĩa của một câu khi câu đó nằm trong chuỗi ít nhất 2 câu liên tiếp bị gắn cờ cùng một đồ án nguồn; cờ nguyên văn đứng một mình vẫn được giữ. Lý do (quan sát trên tập hiệu chỉnh): câu tự viết theo khuôn câu chung của lĩnh vực thường có cosine cao với *một câu lẻ* của đồ án khác, trong khi phần diễn đạt lại luôn đi thành đoạn liền nhau.

### Ngưỡng đã chốt (khớp trên tập HIEU_CHINH)

| Ngưỡng | Giá trị (%) | Phương pháp | AUC tập hiệu chỉnh | Số mẫu (dương / âm) | Dương nhỏ nhất | Âm lớn nhất | Khoảng chọn | TPR / FPR tại ngưỡng |
|---|---:|---|---:|---|---:|---:|---|---|
| Tên đề tài (`nguong_ten_de_tai`) | 67.8 | Youden J (roc_curve) | 0.9758 | 28 / 28 | 61.62 | 72.33 | (67.50; 68.10] | 0.893 / 0.036 |
| Đoạn — ngữ nghĩa (câu) (`nguong_doan`) | 67.7 | Youden J (roc_curve) | 0.7983 | 222 / 1064 | 55.39 | 96.40 | (67.78; 67.80] | 0.829 / 0.351 |
| Đoạn — nguyên văn (câu) (`nguong_nguyen_van`) | 88.7 | Youden J (roc_curve) | 0.9992 | 183 / 1286 | 100.00 | 100.00 | (77.34; 100.00] | 1.000 / 0.002 |
| Tài liệu (theo đồ án nguồn) (`nguong_tai_lieu`) | 10.4 | Trung điểm (tách hoàn toàn) | 1.0000 | 10 / 7 | 20.79 | 0.00 | (0.00; 20.79] | 1.000 / 0.000 |

Shingle MinHash: **k = 4** (AUC nguyên văn trên tập hiệu chỉnh: k = 3: 0.9992, k = 4: 0.9992, k = 5: 0.9992; 128 hoán vị).
Số câu B của tập hiệu chỉnh theo nhãn: chép nguyên văn 183, diễn đạt lại 222, tự viết 1064, không khớp đoạn nội dung nào 0.

### Kết quả kiểm chứng theo cặp tài liệu (ngưỡng cố định)

Ngưỡng áp dụng: đoạn 67.7 %, nguyên văn 88.7 %, tài liệu 10.4 %. Cột *Đoạn trùng* đếm các đoạn trùng mà `check_document` trả về (nguyên văn / ngữ nghĩa).

#### Tập hiệu chỉnh (HIEU_CHINH) — dùng để khớp ngưỡng

| Mã cặp | Loại | Tập | Định dạng A→B | Tỷ lệ tổng (%) | Tỷ lệ theo đồ án nguồn (%) | A dẫn đầu? | Đoạn trùng (nguyên văn / ngữ nghĩa) | Bị cảnh báo? | Kỳ vọng | Kết quả |
|---|---|---|---|---:|---:|---|---|---|---|---|
| P01 | Chép nguyên văn | HIEU_CHINH | DOCX→PDF | 50.30 | 50.30 | Có | 7 / 0 | Có | Cảnh báo | Đạt |
| P02 | Chép nguyên văn | HIEU_CHINH | PDF→DOCX | 48.04 | 48.04 | Có | 5 / 0 | Có | Cảnh báo | Đạt |
| P04 | Chép nguyên văn | HIEU_CHINH | PDF→DOCX | 49.33 | 44.89 | Có | 4 / 1 | Có | Cảnh báo | Đạt |
| P05 | Chép nguyên văn | HIEU_CHINH | DOCX→PDF | 44.83 | 44.83 | Có | 13 / 0 | Có | Cảnh báo | Đạt |
| P07 | Chép nguyên văn | HIEU_CHINH | DOCX→PDF | 57.76 | 46.07 | Có | 6 / 3 | Có | Cảnh báo | Đạt |
| P08 | Diễn đạt lại | HIEU_CHINH | DOCX→PDF | 21.23 | 21.23 | Có | 0 / 5 | Có | Cảnh báo | Đạt |
| P11 | Diễn đạt lại | HIEU_CHINH | PDF→DOCX | 25.54 | 20.79 | Có | 0 / 6 | Có | Cảnh báo | Đạt |
| P12 | Diễn đạt lại | HIEU_CHINH | DOCX→PDF | 33.16 | 31.54 | Có | 0 / 14 | Có | Cảnh báo | Đạt |
| P13 | Diễn đạt lại | HIEU_CHINH | PDF→DOCX | 30.29 | 30.29 | Có | 0 / 4 | Có | Cảnh báo | Đạt |
| P14 | Diễn đạt lại | HIEU_CHINH | DOCX→PDF | 34.09 | 34.09 | Có | 0 / 18 | Có | Cảnh báo | Đạt |
| P15 | Cùng lĩnh vực | HIEU_CHINH | DOCX→PDF | 4.78 | 0.00 | Không | 0 / 4 | Không | Không cảnh báo | Đạt |
| P16 | Cùng lĩnh vực | HIEU_CHINH | PDF→DOCX | 0.00 | 0.00 | Không | 0 / 0 | Không | Không cảnh báo | Đạt |
| P17 | Cùng lĩnh vực | HIEU_CHINH | DOCX→PDF | 0.00 | 0.00 | Không | 0 / 0 | Không | Không cảnh báo | Đạt |
| P20 | Cùng lĩnh vực | HIEU_CHINH | PDF→DOCX | 0.00 | 0.00 | Không | 0 / 0 | Không | Không cảnh báo | Đạt |
| P23 | Không liên quan | HIEU_CHINH | DOCX→PDF | 0.00 | 0.00 | Không | 0 / 0 | Không | Không cảnh báo | Đạt |
| P24 | Không liên quan | HIEU_CHINH | PDF→DOCX | 3.47 | 0.00 | Không | 0 / 1 | Không | Không cảnh báo | Đạt |
| P25 | Không liên quan | HIEU_CHINH | DOCX→PDF | 1.25 | 0.00 | Không | 0 / 1 | Không | Không cảnh báo | Đạt |

#### Tập kiểm chứng (KIEM_CHUNG) — giữ lại, không dùng để khớp

| Mã cặp | Loại | Tập | Định dạng A→B | Tỷ lệ tổng (%) | Tỷ lệ theo đồ án nguồn (%) | A dẫn đầu? | Đoạn trùng (nguyên văn / ngữ nghĩa) | Bị cảnh báo? | Kỳ vọng | Kết quả |
|---|---|---|---|---:|---:|---|---|---|---|---|
| P03 | Chép nguyên văn | KIEM_CHUNG | DOCX→PDF | 51.03 | 49.32 | Có | 16 / 1 | Có | Cảnh báo | Đạt |
| P06 | Chép nguyên văn | KIEM_CHUNG | PDF→DOCX | 49.74 | 46.93 | Có | 5 / 1 | Có | Cảnh báo | Đạt |
| P09 | Diễn đạt lại | KIEM_CHUNG | PDF→DOCX | 17.38 | 13.36 | Có | 0 / 4 | Có | Cảnh báo | Đạt |
| P10 | Diễn đạt lại | KIEM_CHUNG | DOCX→PDF | 20.88 | 20.88 | Có | 0 / 4 | Có | Cảnh báo | Đạt |
| P18 | Cùng lĩnh vực | KIEM_CHUNG | PDF→DOCX | 2.86 | 0.00 | Không | 0 / 1 | Không | Không cảnh báo | Đạt |
| P19 | Cùng lĩnh vực | KIEM_CHUNG | DOCX→PDF | 23.96 | 0.00 | Không | 0 / 14 | Không | Không cảnh báo | Đạt |
| P21 | Không liên quan | KIEM_CHUNG | DOCX→PDF | 6.00 | 0.00 | Không | 0 / 5 | Không | Không cảnh báo | Đạt |
| P22 | Không liên quan | KIEM_CHUNG | PDF→DOCX | 0.00 | 0.00 | Không | 0 / 0 | Không | Không cảnh báo | Đạt |

#### Độ chính xác theo tập và loại cặp

| Loại cặp | HIEU_CHINH | KIEM_CHUNG |
|---|---|---|
| Chép nguyên văn | 5/5 (1.000) | 2/2 (1.000) |
| Diễn đạt lại | 5/5 (1.000) | 2/2 (1.000) |
| Cùng lĩnh vực | 4/4 (1.000) | 2/2 (1.000) |
| Không liên quan | 3/3 (1.000) | 2/2 (1.000) |
| **Tất cả** | **17/17 (1.000)** | **8/8 (1.000)** |

| Cổng | Điều kiện | Kết quả |
|---|---|---|
| G1 (cứng) | mọi cặp CHEP_NGUYEN_VAN bị cảnh báo (cứng) | Đạt |
| G2 (cứng) | mọi cặp KHONG_LIEN_QUAN có tỷ lệ theo đồ án nguồn và tỷ lệ tổng < ngưỡng tài liệu (cứng) | Đạt |
| G3 (mềm) | độ chính xác cặp trên KIEM_CHUNG ≥ 0.85 (mềm) — thực tế 1.000 | Đạt |

#### Tỷ lệ câu bị gắn cờ theo nhãn (mức câu)

| Nhãn câu | HIEU_CHINH | KIEM_CHUNG |
|---|---|---|
| Chép nguyên văn | 183/183 (1.000) | 110/110 (1.000) |
| Diễn đạt lại | 125/222 (0.563) | 22/55 (0.400) |
| Tự viết (dương tính giả) | 44/1064 (0.041) | 57/616 (0.092) |
| Không khớp đoạn nội dung | — | — |

### Kết quả kiểm tra tên đề tài

Ngưỡng tên đề tài 67.8 %: truy vấn bị cảnh báo khi điểm cao nhất ≥ ngưỡng. *Top-1 đúng đối tượng* = đề tài đứng đầu có cùng đối tượng nghiệp vụ với đề tài gốc (chỉ xét truy vấn diễn đạt lại).

| Chỉ số | HIEU_CHINH | KIEM_CHUNG |
|---|---|---|
| Độ chính xác chung | 52/56 (0.929) | 22/24 (0.917) |
| Diễn đạt lại → cảnh báo | 25/28 (0.893) | 11/12 (0.917) |
| Cùng lĩnh vực → không cảnh báo | 27/28 (0.964) | 11/12 (0.917) |
| Top-1 đúng đối tượng | 26/28 (0.929) | 12/12 (1.000) |

### Ảnh hưởng của bước lọc phần mẫu chung (ablation, AISV-04)

Các cặp cùng lĩnh vực và không liên quan được chấm lại khi **tắt** bước lọc phần mẫu chung (bìa, lời cam đoan, lời cảm ơn, mục lục, tiêu đề mục, tài liệu tham khảo, header/footer). Cột *chỉ tài liệu nộp* tắt lọc ở phía bài nộp, kho giữ nguyên như production. Cột *cả kho* tắt lọc ở cả hai phía, tức là một hệ thống không có bước lọc. Ngưỡng giữ nguyên.

| Mã cặp | Loại | Tập | Dòng bị lọc | Tỷ lệ tổng khi lọc (%) | Không lọc — chỉ tài liệu nộp (%) | Không lọc — cả kho (%) | Tăng thêm (điểm %) | Tỷ lệ theo đồ án nguồn khi không lọc (%) | Bị cảnh báo khi không lọc? |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| P15 | Cùng lĩnh vực | HIEU_CHINH | 121 | 4.78 | 2.83 | 11.86 | +7.08 | 0.00 | Không |
| P16 | Cùng lĩnh vực | HIEU_CHINH | 65 | 0.00 | 0.00 | 21.17 | +21.17 | 0.00 | Không |
| P17 | Cùng lĩnh vực | HIEU_CHINH | 108 | 0.00 | 0.00 | 23.17 | +23.17 | 0.00 | Không |
| P18 | Cùng lĩnh vực | KIEM_CHUNG | 65 | 2.86 | 0.00 | 18.25 | +15.39 | 0.00 | Không |
| P19 | Cùng lĩnh vực | KIEM_CHUNG | 119 | 23.96 | 17.65 | 26.48 | +2.52 | 0.39 | Không |
| P20 | Cùng lĩnh vực | HIEU_CHINH | 64 | 0.00 | 0.00 | 22.51 | +22.51 | 0.00 | Không |
| P21 | Không liên quan | KIEM_CHUNG | 116 | 6.00 | 2.70 | 11.58 | +5.58 | 0.00 | Không |
| P22 | Không liên quan | KIEM_CHUNG | 65 | 0.00 | 0.00 | 22.40 | +22.40 | 0.00 | Không |
| P23 | Không liên quan | HIEU_CHINH | 112 | 0.00 | 0.00 | 21.66 | +21.66 | 0.00 | Không |
| P24 | Không liên quan | HIEU_CHINH | 64 | 3.47 | 0.00 | 20.25 | +16.78 | 0.00 | Không |
| P25 | Không liên quan | HIEU_CHINH | 117 | 1.25 | 1.03 | 9.58 | +8.33 | 0.00 | Không |

Trung bình tỷ lệ tổng tăng thêm khi không lọc: **+15.14 điểm %** (nhỏ nhất +2.52, lớn nhất +23.17). Đây là phần mà mẫu chung sẽ bị tính nhầm là trùng nếu không có bước lọc. Cột *chỉ tài liệu nộp* có thể thấp hơn cả khi lọc: kho đã được lọc nên phần mẫu chung của bài nộp không khớp với gì mà chỉ làm tăng mẫu số, đồng thời có thể cắt ngang chuỗi câu trùng.

### Thời gian xử lý (trong tiến trình, máy phát triển)

Đo trực tiếp các hàm pipeline, không qua HTTP, trên máy phát triển dùng chung (16 CPU logic, 4 luồng torch). Kho gồm 300 tiêu đề và 2208 câu tài liệu. Đây chưa phải số đo NFR-08/NFR-09: plan 04-06 đo trong container, Phase 5 đo trên server.

| Thao tác | Số lần | P50 (ms) | P95 (ms) | Lớn nhất (ms) | Giới hạn NFR (P95) |
|---|---:|---:|---:|---:|---|
| `check_title` (kho 300 đề tài) | 20 | 41.0 | 49.4 | 56.0 | ≤ 5 000 ms (NFR-08) |
| `score_document` + `check_document` (một tệp B) | 20 | 1079.0 | 2982.6 | 3027.1 | ≤ 30 000 ms toàn luồng nộp (NFR-09) |

### Giới hạn

- **Dữ liệu tổng hợp.** Toàn bộ kho và tài liệu do chương trình sinh (mục 4.x.1), không phải đồ án thật của khoa. Cách diễn đạt lại và mẫu câu của bộ sinh có thể dễ hoặc khó hơn văn bản thật; ngưỡng cần được hiệu chỉnh lại khi có kho thật.
- **[ASSUMED] Danh sách mẫu chung.** Bước lọc dùng danh sách mặc định (bìa, lời cam đoan, lời cảm ơn, mục lục, tài liệu tham khảo, phụ lục…) vì mẫu đề cương/báo cáo chính thức của khoa chưa được thu thập. Khi có mẫu chính thức phải cập nhật `app/nlp/boilerplate.py` rồi chạy lại `tune` và `evaluate`.
- **Mẫu nhỏ.** Ngưỡng tài liệu được khớp trên 17 cặp; tập kiểm chứng chỉ có 8 cặp, nên mỗi cặp sai làm độ chính xác giảm 0.125.
- **Độ trễ đo trên máy phát triển**, trong tiến trình và trên máy dùng chung; con số chính thức cho NFR-08/NFR-09 do plan 04-06 (container) và Phase 5 (server) đo.
- **Tỷ lệ tổng khác tỷ lệ theo đồ án nguồn.** Cặp không được kỳ vọng cảnh báo có tỷ lệ tổng cao nhất là P19 (cùng lĩnh vực, KIEM_CHUNG): 23.96 % tổng nhưng chỉ 0.00 % theo đồ án nguồn, vì các đoạn khớp rải rác trên nhiều đồ án khác cùng lĩnh vực. Vì vậy quyết định cảnh báo dựa trên tỷ lệ theo **từng** đồ án (`do_an_trung`) so với ngưỡng tài liệu, còn tỷ lệ tổng chỉ để hiển thị kèm.
- **Mức câu còn yếu với diễn đạt lại.** AUC của tín hiệu ngữ nghĩa ở mức câu trên tập hiệu chỉnh chỉ 0.7983. Với ngưỡng cố định, tỷ lệ câu diễn đạt lại bị gắn cờ là 0.563 (hiệu chỉnh) và 0.400 (kiểm chứng); tỷ lệ câu tự viết bị gắn cờ là 0.041 và 0.092. Phát hiện ở mức tài liệu vẫn đúng vì phần diễn đạt lại dồn thành đoạn liền nhau cùng nguồn, nhưng từng đoạn trùng ngữ nghĩa nên được giảng viên đọc lại trước khi kết luận.
- **Tên đề tài trên tập kiểm chứng:** 2 truy vấn phân loại sai (TV015 cùng lĩnh vực 73.03 %, TV038 diễn đạt lại 66.90 %). Đề tài cùng lĩnh vực có khuôn tên giống nhau nên cảnh báo tên đề tài chỉ là **gợi ý** để giảng viên xem lại, không phải kết luận (khớp với nhận xét ở mục 4.x.2).

### Chạy lại

Từ thư mục `ai-service/` (cần ≥ 3 GiB RAM trống; không cần docker hay MySQL):

```bash
uv run python calibration/calibrate.py tune --data ../seed-data \
  --profile-from ../tools/bakeoff/ket-qua.json --out calibration
uv run python calibration/calibrate.py evaluate --data ../seed-data \
  --profile-from ../tools/bakeoff/ket-qua.json --out calibration \
  --report ../docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md --apply
```

Kết quả chi tiết theo từng cặp, truy vấn và câu nằm trong `ai-service/calibration/ket-qua-chi-tiet.json`; ngưỡng, phương pháp và AUC trong `ai-service/calibration/nguong-de-xuat.json` (plan 04-05 đọc tệp này để đặt giá trị mặc định phía Web API).
