## 4.x.3 Hiệu chỉnh và kiểm chứng ngưỡng cảnh báo trùng lặp

> **Mã PI:** 3.4 — **Yêu cầu:** DATA-03, AISV-03, AISV-04

<!-- Tệp này do `ai-service/calibration/calibrate.py evaluate --report` sinh ra từ `calibration/nguong-de-xuat.json` và `calibration/ket-qua-chi-tiet.json`; không sửa tay. -->

### Mục tiêu

Dịch vụ AI cảnh báo trùng lặp dựa trên năm ngưỡng: ngưỡng tên đề tài khi sinh viên đăng ký (AISV-03), ngưỡng ngữ nghĩa và ngưỡng nguyên văn ở mức câu, ngưỡng tài liệu quyết định một bài nộp có bị cảnh báo trùng với một đồ án trong kho hay không, và ngưỡng tổng bắt bài ghép từ nhiều đồ án (AISV-04). Theo quyết định D-04, giá trị mặc định của các ngưỡng **phải đến từ hiệu chỉnh** chứ không đặt theo cảm tính. Theo D-06, ngưỡng chỉ được khớp trên tập hiệu chỉnh (`HIEU_CHINH`) rồi giữ nguyên để kiểm chứng trên tập giữ lại (`KIEM_CHUNG`). Mục này cung cấp bảng kiểm chứng theo từng cặp tài liệu mà DATA-03 và tiêu chí thành công số 3 của Phase 4 yêu cầu.

### Dữ liệu và mô hình

- Bộ dữ liệu tổng hợp mô tả ở [mục 4.x.1](01-du-lieu-thu-nghiem.md): kho 300 đề tài khóa K18–K22, 25 cặp tài liệu A/B (DOCX/PDF) và 80 truy vấn tên đề tài có nhãn.
- Tập hiệu chỉnh: 17 cặp, 56 truy vấn. Tập kiểm chứng (giữ lại, không dùng để khớp): 8 cặp, 24 truy vấn.
- Mô hình embedding đã chốt ở [mục 4.x.2](02-so-sanh-mo-hinh-embedding.md): `bkai-foundation-models/vietnamese-bi-encoder` (profile `bkai`).
- Văn bản được trích xuất bằng bản sao đúng từng dòng của hàm `extract_text` phía Web API, rồi đi qua đúng pipeline của dịch vụ AI (`ingest` → `score_document` → `check_document`, `check_title`). Kho được dựng trên một cơ sở dữ liệu SQLite tạm theo cùng migration với MySQL. Tài liệu A được nạp vào kho; tài liệu B chỉ được kiểm tra, giống như bài nộp mới được kiểm tra trước khi vào kho.

### Phương pháp

1. **Mức câu.** Mỗi câu của tài liệu B (sau khi lọc phần mẫu chung) có hai điểm so với kho: cosine embedding tốt nhất (ngữ nghĩa) và độ phủ vân tay tốt nhất (nguyên văn). Độ phủ = tỷ lệ âm tiết của câu nằm trong các đoạn chung dài ≥ t = w + k − 1 âm tiết với một câu của kho, chỉ tính k-gram không phổ biến (k-gram có ở ≥ L đề tài khác nhau là cụm khuôn mẫu, theo Sorokina và cs. 2006). Câu ứng viên được tra qua chỉ mục vân tay winnowing (Schleimer và cs. 2003), không quét toàn kho. Nhãn của câu lấy từ nguồn gốc đoạn văn ghi trong manifest: *chép nguyên văn*, *diễn đạt lại* hoặc *tự viết*.
2. **Ngưỡng nguyên văn**: dương = câu chép nguyên văn, âm = mọi câu còn lại (kể cả câu diễn đạt lại, vốn để tín hiệu ngữ nghĩa xử lý). **Ngưỡng đoạn (ngữ nghĩa)**: dương = câu diễn đạt lại, âm = câu tự viết.
3. **Ngưỡng tài liệu**: với hai ngưỡng câu đã cố định, `check_document` cho tỷ lệ ký tự của B bị gán cho đồ án nguồn A (*tỷ lệ theo đồ án nguồn*). Cặp bị cảnh báo khi tỷ lệ này ≥ ngưỡng tài liệu. Dương = cặp chép nguyên văn và diễn đạt lại. **Ngưỡng tổng** khớp theo cùng cách trên *tỷ lệ tổng* (phần của B khớp với bất kỳ tài liệu nào trong kho): bài nộp bị cảnh báo khi tỷ lệ theo một đồ án ≥ ngưỡng tài liệu **hoặc** tỷ lệ tổng ≥ ngưỡng tổng, để bài ghép từ nhiều đồ án (mỗi đồ án một ít) không lọt.
4. **Ngưỡng tên đề tài**: điểm cao nhất của `check_title` trên kho 300 đề tài; dương = truy vấn diễn đạt lại một đề tài có trong kho.
5. **Cách chọn ngưỡng**: `sklearn.metrics.roc_curve` và chỉ số **Youden J = TPR − FPR**. Mọi ngưỡng nằm giữa điểm đạt J lớn nhất và điểm liền dưới nó cho cùng một kết quả phân loại trên tập hiệu chỉnh, nên ngưỡng được đặt ở **trung điểm của khoảng đó** (cột *Khoảng chọn*). Khi tín hiệu tách hoàn toàn tập hiệu chỉnh, dùng **trung điểm** giữa điểm âm lớn nhất và điểm dương nhỏ nhất để có biên an toàn. Ngưỡng tính theo %, một chữ số thập phân; gắn cờ khi điểm ≥ ngưỡng. k của vân tay chọn trong {3, 4, 5, 6} theo AUC nguyên văn lớn nhất (hòa → 4); w = 4 và L = 4 giữ cố định.
6. **Luật đoạn cho tín hiệu ngữ nghĩa**: `check_document` chỉ giữ cờ ngữ nghĩa của một câu khi câu đó nằm trong chuỗi ít nhất 2 câu liên tiếp bị gắn cờ cùng một đồ án nguồn; cờ nguyên văn đứng một mình vẫn được giữ. Lý do (quan sát trên tập hiệu chỉnh): câu tự viết theo khuôn câu chung của lĩnh vực thường có cosine cao với *một câu lẻ* của đồ án khác, trong khi phần diễn đạt lại luôn đi thành đoạn liền nhau.

### Ngưỡng đã chốt (khớp trên tập HIEU_CHINH)

| Ngưỡng | Giá trị (%) | Phương pháp | AUC tập hiệu chỉnh | Số mẫu (dương / âm) | Dương nhỏ nhất | Âm lớn nhất | Khoảng chọn | TPR / FPR tại ngưỡng |
|---|---:|---|---:|---|---:|---:|---|---|
| Tên đề tài (`nguong_ten_de_tai`) | 67.8 | Youden J (roc_curve) | 0.9758 | 28 / 28 | 61.62 | 72.33 | (67.50; 68.10] | 0.893 / 0.036 |
| Đoạn — ngữ nghĩa (câu) (`nguong_doan`) | 67.7 | Youden J (roc_curve) | 0.7983 | 222 / 1064 | 55.39 | 96.40 | (67.78; 67.80] | 0.829 / 0.351 |
| Đoạn — nguyên văn (câu) (`nguong_nguyen_van`) | 56.0 | Youden J (roc_curve) | 0.9974 | 183 / 1286 | 42.31 | 81.82 | (55.56; 56.52] | 0.978 / 0.019 |
| Tài liệu (theo đồ án nguồn) (`nguong_tai_lieu`) | 10.4 | Trung điểm (tách hoàn toàn) | 1.0000 | 10 / 7 | 20.79 | 0.00 | (0.00; 20.79] | 1.000 / 0.000 |
| Tài liệu (tổng mọi nguồn) (`nguong_tong_tai_lieu`) | 14.8 | Trung điểm (tách hoàn toàn) | 1.0000 | 10 / 7 | 21.23 | 8.41 | (8.41; 21.23] | 1.000 / 0.000 |

Vân tay: **k = 6** âm tiết (AUC nguyên văn trên tập hiệu chỉnh: k = 3: 0.9859, k = 4: 0.9962, k = 5: 0.9969, k = 6: 0.9974), cửa sổ winnowing w = 4, đoạn chung tối thiểu t = 9 âm tiết, cụm phổ biến khi có ở ≥ 4 đề tài.
Số câu B của tập hiệu chỉnh theo nhãn: chép nguyên văn 183, diễn đạt lại 222, tự viết 1064, không khớp đoạn nội dung nào 0.

### Kết quả kiểm chứng theo cặp tài liệu (ngưỡng cố định)

Ngưỡng áp dụng: đoạn 67.7 %, nguyên văn 56.0 %, tài liệu 10.4 %, tổng 14.8 %. Cột *Đoạn trùng* đếm các đoạn trùng mà `check_document` trả về (nguyên văn / ngữ nghĩa).

> Ghi chú (09/11/2026, thêm tay — lần sinh lại trang bằng `calibrate.py evaluate --report` sẽ xóa dòng này): từ khi có nhãn đoạn "Trùng sửa nhẹ" (`SUA_NHE`, từ 24/11/2026 theo tỷ lệ khớp chữ ≥ 0,99; xem [05-danh-gia-kieu-pan.md](05-danh-gia-kieu-pan.md)), `calibrate.py` đếm vào cột *nguyên văn* mọi đoạn do vân tay, gồm cả đoạn mang nhãn sửa nhẹ. Số liệu trong trang được sinh ngày 21/10/2026, trước khi có nhãn này và trước khi độ phủ nguyên văn tính theo từng nguồn; 25 PDF của bộ dữ liệu cho văn bản giống hệt với hàm trích xuất PDF mới, nên bản sửa trích xuất không làm đổi các ngưỡng; trang này chưa được sinh lại sau bản sửa độ phủ.

*Bị cảnh báo?* dùng **đúng quy tắc triển khai** (sửa lỗi review CR-01): tỷ lệ theo nguồn **cao nhất** (`do_an_trung[0]`, bất kỳ đồ án nào trong kho) ≥ 10.4 % *(nguồn)*, hoặc tỷ lệ tổng ≥ 14.8 % *(tổng)* — Web API không biết đồ án nguồn A của cặp. Cột *theo đồ án nguồn A* là tỷ lệ tới A (thống kê dùng để khớp ngưỡng), chỉ để đối chiếu.

Trên tập hiệu chỉnh, theo thống kê triển khai: âm lớn nhất 8.41 %, dương nhỏ nhất 20.79 % — ngưỡng 10.4 % vẫn nằm trong khoảng tách.

#### Tập hiệu chỉnh (HIEU_CHINH) — dùng để khớp ngưỡng

| Mã cặp | Loại | Tập | Định dạng A→B | Tỷ lệ tổng (%) | Theo nguồn cao nhất (%) | Theo đồ án nguồn A (%) | A dẫn đầu? | Đoạn trùng (nguyên văn / ngữ nghĩa) | Bị cảnh báo? | Kỳ vọng | Kết quả |
|---|---|---|---|---:|---:|---:|---|---|---|---|---|
| P01 | Chép nguyên văn | HIEU_CHINH | DOCX→PDF | 50.30 | 50.30 | 50.30 | Có | 7 / 0 | Có (nguồn) | Cảnh báo | Đạt |
| P02 | Chép nguyên văn | HIEU_CHINH | PDF→DOCX | 50.61 | 48.04 | 48.04 | Có | 7 / 0 | Có (nguồn) | Cảnh báo | Đạt |
| P04 | Chép nguyên văn | HIEU_CHINH | PDF→DOCX | 50.78 | 44.89 | 44.89 | Có | 5 / 1 | Có (nguồn) | Cảnh báo | Đạt |
| P05 | Chép nguyên văn | HIEU_CHINH | DOCX→PDF | 44.83 | 44.83 | 44.83 | Có | 13 / 0 | Có (nguồn) | Cảnh báo | Đạt |
| P07 | Chép nguyên văn | HIEU_CHINH | DOCX→PDF | 57.76 | 46.07 | 46.07 | Có | 6 / 3 | Có (nguồn) | Cảnh báo | Đạt |
| P08 | Diễn đạt lại | HIEU_CHINH | DOCX→PDF | 21.23 | 21.23 | 21.23 | Có | 0 / 5 | Có (nguồn) | Cảnh báo | Đạt |
| P11 | Diễn đạt lại | HIEU_CHINH | PDF→DOCX | 25.54 | 20.79 | 20.79 | Có | 0 / 6 | Có (nguồn) | Cảnh báo | Đạt |
| P12 | Diễn đạt lại | HIEU_CHINH | DOCX→PDF | 33.16 | 31.01 | 31.01 | Có | 2 / 13 | Có (nguồn) | Cảnh báo | Đạt |
| P13 | Diễn đạt lại | HIEU_CHINH | PDF→DOCX | 30.29 | 30.29 | 30.29 | Có | 0 / 4 | Có (nguồn) | Cảnh báo | Đạt |
| P14 | Diễn đạt lại | HIEU_CHINH | DOCX→PDF | 34.09 | 34.09 | 34.09 | Có | 0 / 18 | Có (nguồn) | Cảnh báo | Đạt |
| P15 | Cùng lĩnh vực | HIEU_CHINH | DOCX→PDF | 7.66 | 5.59 | 0.00 | Không | 5 / 4 | Không | Không cảnh báo | Đạt |
| P16 | Cùng lĩnh vực | HIEU_CHINH | PDF→DOCX | 0.00 | 0.00 | 0.00 | Không | 0 / 0 | Không | Không cảnh báo | Đạt |
| P17 | Cùng lĩnh vực | HIEU_CHINH | DOCX→PDF | 8.41 | 8.41 | 0.00 | Không | 3 / 0 | Không | Không cảnh báo | Đạt |
| P20 | Cùng lĩnh vực | HIEU_CHINH | PDF→DOCX | 0.00 | 0.00 | 0.00 | Không | 0 / 0 | Không | Không cảnh báo | Đạt |
| P23 | Không liên quan | HIEU_CHINH | DOCX→PDF | 0.00 | 0.00 | 0.00 | Không | 0 / 0 | Không | Không cảnh báo | Đạt |
| P24 | Không liên quan | HIEU_CHINH | PDF→DOCX | 5.71 | 5.71 | 0.00 | Không | 1 / 1 | Không | Không cảnh báo | Đạt |
| P25 | Không liên quan | HIEU_CHINH | DOCX→PDF | 2.23 | 1.25 | 0.00 | Không | 2 / 1 | Không | Không cảnh báo | Đạt |

#### Tập kiểm chứng (KIEM_CHUNG) — giữ lại, không dùng để khớp

| Mã cặp | Loại | Tập | Định dạng A→B | Tỷ lệ tổng (%) | Theo nguồn cao nhất (%) | Theo đồ án nguồn A (%) | A dẫn đầu? | Đoạn trùng (nguyên văn / ngữ nghĩa) | Bị cảnh báo? | Kỳ vọng | Kết quả |
|---|---|---|---|---:|---:|---:|---|---|---|---|---|
| P03 | Chép nguyên văn | KIEM_CHUNG | DOCX→PDF | 52.54 | 49.32 | 49.32 | Có | 19 / 1 | Có (nguồn) | Cảnh báo | Đạt |
| P06 | Chép nguyên văn | KIEM_CHUNG | PDF→DOCX | 51.07 | 46.93 | 46.93 | Có | 6 / 1 | Có (nguồn) | Cảnh báo | Đạt |
| P09 | Diễn đạt lại | KIEM_CHUNG | PDF→DOCX | 20.94 | 13.36 | 13.36 | Có | 0 / 5 | Có (nguồn) | Cảnh báo | Đạt |
| P10 | Diễn đạt lại | KIEM_CHUNG | DOCX→PDF | 20.88 | 20.88 | 20.88 | Có | 0 / 4 | Có (nguồn) | Cảnh báo | Đạt |
| P18 | Cùng lĩnh vực | KIEM_CHUNG | PDF→DOCX | 4.40 | 2.86 | 1.54 | Không | 1 / 1 | Không | Không cảnh báo | Đạt |
| P19 | Cùng lĩnh vực | KIEM_CHUNG | DOCX→PDF | 23.96 | 22.81 | 0.00 | Không | 0 / 14 | Có (nguồn) | Không cảnh báo | Không đạt |
| P21 | Không liên quan | KIEM_CHUNG | DOCX→PDF | 6.87 | 1.51 | 0.00 | Không | 1 / 5 | Không | Không cảnh báo | Đạt |
| P22 | Không liên quan | KIEM_CHUNG | PDF→DOCX | 2.62 | 2.62 | 0.00 | Không | 1 / 0 | Không | Không cảnh báo | Đạt |

#### Độ chính xác theo tập và loại cặp

| Loại cặp | HIEU_CHINH | KIEM_CHUNG |
|---|---|---|
| Chép nguyên văn | 5/5 (1.000) | 2/2 (1.000) |
| Diễn đạt lại | 5/5 (1.000) | 2/2 (1.000) |
| Cùng lĩnh vực | 4/4 (1.000) | 1/2 (0.500) |
| Không liên quan | 3/3 (1.000) | 2/2 (1.000) |
| **Tất cả** | **17/17 (1.000)** | **7/8 (0.875)** |

| Cổng | Điều kiện | Kết quả |
|---|---|---|
| G1 (cứng) | mọi cặp CHEP_NGUYEN_VAN bị cảnh báo (cứng) | Đạt |
| G2 (cứng) | mọi cặp KHONG_LIEN_QUAN không bị cảnh báo và có tỷ lệ tổng < ngưỡng tài liệu (cứng) | Đạt |
| G3 (mềm) | độ chính xác cặp trên KIEM_CHUNG ≥ 0.85 (mềm) — thực tế 0.875 | Đạt |

#### Tỷ lệ câu bị gắn cờ theo nhãn (mức câu)

| Nhãn câu | HIEU_CHINH | KIEM_CHUNG |
|---|---|---|
| Chép nguyên văn | 183/183 (1.000) | 110/110 (1.000) |
| Diễn đạt lại | 125/222 (0.563) | 22/55 (0.400) |
| Tự viết (dương tính giả) | 60/1064 (0.056) | 66/616 (0.107) |
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

| Mã cặp | Loại | Tập | Dòng bị lọc | Tỷ lệ tổng khi lọc (%) | Không lọc — chỉ tài liệu nộp (%) | Không lọc — cả kho (%) | Tăng thêm (điểm %) | Tỷ lệ theo đồ án nguồn khi không lọc (%) | Bị cảnh báo khi không lọc? | Không lọc cụm phổ biến (%) |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| P15 | Cùng lĩnh vực | HIEU_CHINH | 121 | 7.66 | 5.29 | 11.67 | +4.01 | 0.00 | Không | 22.08 |
| P16 | Cùng lĩnh vực | HIEU_CHINH | 65 | 0.00 | 0.00 | 10.35 | +10.35 | 0.00 | Không | 7.92 |
| P17 | Cùng lĩnh vực | HIEU_CHINH | 108 | 8.41 | 5.46 | 19.62 | +11.21 | 0.00 | Có | 25.66 |
| P18 | Cùng lĩnh vực | KIEM_CHUNG | 65 | 4.40 | 1.08 | 13.00 | +8.60 | 1.08 | Không | 13.66 |
| P19 | Cùng lĩnh vực | KIEM_CHUNG | 119 | 23.96 | 17.65 | 23.93 | -0.03 | 0.00 | Có | 34.97 |
| P20 | Cùng lĩnh vực | HIEU_CHINH | 64 | 0.00 | 0.00 | 11.61 | +11.61 | 0.00 | Không | 7.79 |
| P21 | Không liên quan | KIEM_CHUNG | 116 | 6.87 | 3.43 | 9.13 | +2.26 | 0.00 | Không | 14.61 |
| P22 | Không liên quan | KIEM_CHUNG | 65 | 2.62 | 1.73 | 14.87 | +12.25 | 0.00 | Có | 15.81 |
| P23 | Không liên quan | HIEU_CHINH | 112 | 0.00 | 0.00 | 12.71 | +12.71 | 0.00 | Không | 7.56 |
| P24 | Không liên quan | HIEU_CHINH | 64 | 5.71 | 1.50 | 14.14 | +8.43 | 0.00 | Không | 24.97 |
| P25 | Không liên quan | HIEU_CHINH | 117 | 2.23 | 1.45 | 9.06 | +6.83 | 0.00 | Không | 18.50 |

Trung bình tỷ lệ tổng tăng thêm khi không lọc: **+8.02 điểm %** (nhỏ nhất -0.03, lớn nhất +12.71). Đây là phần mà mẫu chung sẽ bị tính nhầm là trùng nếu không có bước lọc. Cột *chỉ tài liệu nộp* có thể thấp hơn cả khi lọc: kho đã được lọc nên phần mẫu chung của bài nộp không khớp với gì mà chỉ làm tăng mẫu số, đồng thời có thể cắt ngang chuỗi câu trùng. Cột *không lọc cụm phổ biến* giữ bước lọc dòng nhưng đặt L = 0 (mọi k-gram đều là bằng chứng nguyên văn).

### Kịch bản ghép từ nhiều nguồn

Bộ dữ liệu không có bài ghép từ nhiều đồ án, nên mục này dựng thêm một kịch bản (không dùng để khớp ngưỡng): lấy bài B tự viết của 11 cặp âm (cùng lĩnh vực, không liên quan), chèn 4 khối câu chép nguyên văn từ tài liệu A của 4 cặp khác, mỗi khối khoảng 6 % nội dung của bài gốc, rải đều trong bài. Mỗi nguồn vì vậy đứng dưới ngưỡng tài liệu, còn tổng phần chép thì lớn — đúng trường hợp quy tắc chỉ xét một nguồn bỏ sót.

| Bài gốc | Loại | Tập | Câu chèn bị gắn cờ | Phần chèn (%) | Tỷ lệ tổng (%) | Theo nguồn cao nhất (%) | Cảnh báo — chỉ theo nguồn | Cảnh báo — quy tắc hiện tại |
|---|---|---|---|---:|---:|---:|---|---|
| P15 | Cùng lĩnh vực | HIEU_CHINH | 42/42 | 19.91 | 26.53 | 5.34 | Không | Có (tổng) |
| P16 | Cùng lĩnh vực | HIEU_CHINH | 18/18 | 21.74 | 21.74 | 5.94 | Không | Có (tổng) |
| P17 | Cùng lĩnh vực | HIEU_CHINH | 16/16 | 22.22 | 29.72 | 12.07 | Có | Có (nguồn) |
| P18 | Cùng lĩnh vực | KIEM_CHUNG | 19/19 | 21.83 | 25.27 | 5.69 | Không | Có (tổng) |
| P19 | Cùng lĩnh vực | KIEM_CHUNG | 40/40 | 20.13 | 39.26 | 18.22 | Có | Có (nguồn) |
| P20 | Cùng lĩnh vực | HIEU_CHINH | 15/15 | 20.33 | 20.33 | 5.27 | Không | Có (tổng) |
| P21 | Không liên quan | KIEM_CHUNG | 43/43 | 20.21 | 25.69 | 5.93 | Không | Có (tổng) |
| P22 | Không liên quan | KIEM_CHUNG | 15/15 | 22.52 | 24.56 | 6.12 | Không | Có (tổng) |
| P23 | Không liên quan | HIEU_CHINH | 17/17 | 20.55 | 20.55 | 5.70 | Không | Có (tổng) |
| P24 | Không liên quan | HIEU_CHINH | 16/16 | 21.72 | 26.19 | 5.58 | Không | Có (tổng) |
| P25 | Không liên quan | HIEU_CHINH | 43/43 | 20.20 | 21.98 | 5.23 | Không | Có (tổng) |

Cảnh báo theo quy tắc chỉ xét một nguồn: 2/11 bài; theo quy tắc hiện tại (thêm ngưỡng tổng): 11/11 bài.

### Thời gian xử lý (trong tiến trình, máy phát triển)

Đo trực tiếp các hàm pipeline, không qua HTTP, trên máy phát triển dùng chung (16 CPU logic, 4 luồng torch). Kho gồm 300 tiêu đề và 2208 câu tài liệu. Đây chưa phải số đo NFR-08/NFR-09: plan 04-06 đo trong container, Phase 5 đo trên server.

| Thao tác | Số lần | P50 (ms) | P95 (ms) | Lớn nhất (ms) | Giới hạn NFR (P95) |
|---|---:|---:|---:|---:|---|
| `check_title` (kho 300 đề tài) | 20 | 57.9 | 78.7 | 89.8 | ≤ 5 000 ms (NFR-08) |
| `score_document` + `check_document` (một tệp B) | 20 | 1456.9 | 3608.6 | 3621.2 | ≤ 30 000 ms toàn luồng nộp (NFR-09) |

### Giới hạn

- **Dữ liệu tổng hợp.** Toàn bộ kho và tài liệu do chương trình sinh (mục 4.x.1), không phải đồ án thật của khoa. Cách diễn đạt lại và mẫu câu của bộ sinh có thể dễ hoặc khó hơn văn bản thật; ngưỡng cần được hiệu chỉnh lại khi có kho thật.
- **[ASSUMED] Danh sách mẫu chung.** Bước lọc dòng dùng danh sách mặc định (bìa, lời cam đoan, lời cảm ơn, mục lục, tài liệu tham khảo, phụ lục…) vì mẫu đề cương/báo cáo chính thức của khoa chưa được thu thập. Câu khuôn mẫu lọt qua danh sách được bộ lọc cụm phổ biến của vân tay xử lý theo dữ liệu, nhưng bộ lọc này chỉ áp cho tín hiệu nguyên văn; khi có mẫu chính thức vẫn nên cập nhật `app/nlp/boilerplate.py` rồi chạy lại `tune` và `evaluate`.
- **Cụm phổ biến cần kho đủ lớn.** Kho thử nghiệm chỉ có 25 đề tài có tài liệu; với L = 4, một câu khuôn phải xuất hiện ở ≥ 4 đề tài mới bị coi là phổ biến. Kho thật lớn hơn nhiều nên bộ lọc mạnh hơn; L cần được xem lại khi kho lớn lên.
- **Mẫu nhỏ.** Ngưỡng tài liệu được khớp trên 17 cặp; tập kiểm chứng chỉ có 8 cặp, nên mỗi cặp sai làm độ chính xác giảm 0.125.
- **Độ trễ đo trên máy phát triển**, trong tiến trình và trên máy dùng chung; con số chính thức cho NFR-08/NFR-09 do plan 04-06 (container) và Phase 5 (server) đo.
- **Ngưỡng tổng và câu khớp rải rác.** Câu tự viết cùng lĩnh vực có thể khớp rải rác nhiều đồ án: cặp P21 (không liên quan) có 6.87 % tổng nhưng chỉ 1.51 % với đồ án trùng nhiều nhất. Vì vậy ngưỡng tổng (14.8 %) cao hơn ngưỡng theo một đồ án (10.4 %) và được khớp riêng; tập dữ liệu chưa có bài ghép thật từ nhiều nguồn nên ngưỡng tổng mới chỉ được kiểm tra bằng kịch bản dựng thêm ở trên.
- **Cặp cùng lĩnh vực có tỷ lệ tổng cao nhất** là P19 (KIEM_CHUNG): 23.96 % tổng, 22.81 % với một đồ án khác trong kho (tới đồ án nguồn A của cặp: 0.00 %) — bị cảnh báo theo quy tắc triển khai. Phiên bản trước của trang này đánh giá bằng tỷ lệ tới A (chỉ bộ dữ liệu có chủ đích mới biết) nên ghi cặp này là không cảnh báo; đó không phải điều hệ thống chạy thật làm được.
- **Mức câu còn yếu với diễn đạt lại.** AUC của tín hiệu ngữ nghĩa ở mức câu trên tập hiệu chỉnh chỉ 0.7983. Với ngưỡng cố định, tỷ lệ câu diễn đạt lại bị gắn cờ là 0.563 (hiệu chỉnh) và 0.400 (kiểm chứng); tỷ lệ câu tự viết bị gắn cờ là 0.056 và 0.107. Phát hiện ở mức tài liệu vẫn đúng vì phần diễn đạt lại dồn thành đoạn liền nhau cùng nguồn, nhưng từng đoạn trùng ngữ nghĩa nên được giảng viên đọc lại trước khi kết luận.
- **Tên đề tài trên tập kiểm chứng:** 2 truy vấn phân loại sai (TV015 cùng lĩnh vực 73.03 %, TV038 diễn đạt lại 66.90 %). Đề tài cùng lĩnh vực có khuôn tên giống nhau nên cảnh báo tên đề tài chỉ là **gợi ý** để giảng viên xem lại, không phải kết luận (khớp với nhận xét ở mục 4.x.2).
- **Cặp kiểm chứng phân loại sai** (độ chính xác 0.875); ngưỡng **không** được khớp lại trên tập này:
  - P19 (Cùng lĩnh vực, DOCX→PDF): tỷ lệ tổng 23.96 %, theo nguồn cao nhất 22.81 % (tới A 0.00 %) so với ngưỡng 10.4 %, đoạn trùng 0 nguyên văn / 14 ngữ nghĩa, cosine lớn nhất của câu tự viết 95.92 %. Nguyên nhân có thể: câu tự viết cùng lĩnh vực có cosine cao với một đồ án khác cùng chủ đề (mẫu câu chung của lĩnh vực) thành chuỗi ≥ 2 câu liên tiếp, đẩy tỷ lệ theo nguồn cao nhất vượt ngưỡng tài liệu.

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
