## 4.x.2 So sánh và chốt mô hình embedding cho dịch vụ AI

> **Mã PI:** 3.4 — **Yêu cầu:** AISV-03, AISV-04

### Mục đích

Dịch vụ AI kiểm tra trùng lặp so sánh tên đề tài theo ngữ nghĩa khi sinh viên đăng ký (AISV-03) và phát hiện đoạn trùng khi nộp đề cương/báo cáo (AISV-04). Cả hai chức năng đều dựa trên embedding câu và độ tương đồng cosine (§1.6.2, §1.7.3). Theo quyết định D-01 của Phase 4, mô hình embedding **không chọn theo cảm tính** mà qua một vòng so sánh trực tiếp (bake-off) có giới hạn thời gian giữa hai ứng viên đã nêu ở §1.6.3–1.6.4. Quy tắc chọn được **viết ra trước khi chạy**. Mục này ghi lại phương pháp, số liệu đo và quyết định. Kết quả được dùng làm đầu vào cho bước hiệu chỉnh ngưỡng (mục 4.x.3) và triển khai dịch vụ AI.

### Hai mô hình ứng viên

| | `bkai` | `e5` |
|---|---|---|
| Mô hình | `bkai-foundation-models/vietnamese-bi-encoder` | `intfloat/multilingual-e5-base` |
| Mô hình nền | PhoBERT-base-v2 (RoBERTa, tiếng Việt), tinh chỉnh kiểu Sentence-BERT | XLM-RoBERTa base, huấn luyện tương phản đa ngôn ngữ |
| Kích thước trọng số | ≈ 515 MiB | ≈ 1,06 GiB |
| Tiền xử lý | Chuẩn hóa NFC → tách từ bằng `underthesea.word_tokenize(text, format="text")`, không tiền tố | Chuẩn hóa NFC → thêm tiền tố `"query: "` ở **cả hai phía** (so khớp đối xứng), không tách từ |

Cả hai được chạy cục bộ trên CPU bằng sentence-transformers, `normalize_embeddings=True` (cosine = tích vô hướng), batch 32, 4 luồng torch. Hai cấu hình này giống hệt cấu hình mà dịch vụ AI dùng khi chạy thật.

### Tập cặp có nhãn

Kho đồ án thật của khoa chưa được thu thập, vì vậy tập đánh giá được **tự soạn hoàn toàn**. Tập gồm 80 cặp văn bản tiếng Việt, không chép văn bản thật của sinh viên (tệp `tools/bakeoff/cap-mau.jsonl`). Nội dung trải trên các lĩnh vực web, di động, AI/ML, IoT, dữ liệu, an toàn thông tin, ERP và học tập số.

| Loại cặp | Diễn đạt lại (trùng, nhãn 1) | Cùng lĩnh vực, khác nội dung (nhãn 0) | Không liên quan (nhãn 0) | Tổng |
|---|---:|---:|---:|---:|
| Tên đề tài (`TIEU_DE`) | 12 | 12 | 6 | 30 |
| Câu (`CAU`) | 12 | 12 | 6 | 30 |
| Đoạn 3–4 câu (`DOAN`) | 8 | 8 | 4 | 20 |

Cặp "diễn đạt lại" thay đổi đáng kể từ ngữ và thứ tự ý chứ không chỉ thay một từ đồng nghĩa. Cặp "cùng lĩnh vực" cố ý dùng chung từ vựng chuyên ngành, thậm chí chung khuôn câu. Ví dụ: "Xây dựng hệ thống quản lý thư viện trực tuyến cho trường đại học" và "Xây dựng hệ thống quản lý ký túc xá cho trường đại học" là hai đề tài khác nhau. Đây là ca khó, quyết định mô hình nào phù hợp hơn. Có câu vì dịch vụ AI so sánh ở mức câu rồi gom thành đoạn trùng.

### Phương pháp đo

Với mỗi cặp, hệ thống tính cosine giữa hai embedding. Theo từng loại cặp, các chỉ số được tính như sau:

- **AUC** (diện tích dưới đường ROC): xác suất một cặp trùng có cosine cao hơn một cặp không trùng chọn ngẫu nhiên. Giá trị 1 nghĩa là tách biệt hoàn toàn.
- **AUC (chỉ diễn đạt lại vs cùng lĩnh vực)**: AUC chỉ tính trên các ca khó.
- **Gap**: hiệu giữa cosine trung bình của cặp trùng và cặp không trùng.
- **Margin**: hiệu giữa cosine nhỏ nhất của cặp trùng và lớn nhất của cặp không trùng. Margin > 0 nghĩa là có một ngưỡng tách đúng mọi cặp.
- **Độ chính xác tại ngưỡng tốt nhất**: tìm trên mọi ngưỡng cosine.

Chi phí được đo trên máy phát triển, mỗi mô hình trong **một tiến trình riêng**, lần lượt từng mô hình. Máy này dùng chung 16 GB RAM. Các chỉ số chi phí gồm:

- Thời gian nạp mô hình (từ cache, gồm cả import thư viện).
- Trung vị 20 lần encode một tên đề tài, gồm cả tiền xử lý.
- Thời gian một lần encode 300 câu khác nhau.
- RSS đỉnh của tiến trình.

Các bảng dưới đây được sinh tự động bằng lệnh `uv run python bakeoff.py --bang` từ `ket-qua-bkai.json`, `ket-qua-e5.json` và `ket-qua.json`, không gõ tay số liệu.

### Kết quả

| Loại cặp | Chỉ số | bkai | e5 |
|---|---|---:|---:|
| Tên đề tài | AUC | 0.8472 | 0.8750 |
| Tên đề tài | AUC (chỉ diễn đạt lại vs cùng lĩnh vực) | 0.7708 | 0.8125 |
| Tên đề tài | TB cosine cặp trùng | 0.5810 | 0.9214 |
| Tên đề tài | TB cosine cặp không trùng | 0.3403 | 0.8597 |
| Tên đề tài | Gap (TB trùng − TB không trùng) | 0.2407 | 0.0617 |
| Tên đề tài | Margin (min trùng − max không trùng) | -0.3290 | -0.0480 |
| Tên đề tài | Độ chính xác tại ngưỡng tốt nhất | 0.8000 | 0.8667 |
| Tên đề tài | Ngưỡng tốt nhất (cosine) | 0.5713 | 0.9059 |
| Câu | AUC | 1.0000 | 1.0000 |
| Câu | AUC (chỉ diễn đạt lại vs cùng lĩnh vực) | 1.0000 | 1.0000 |
| Câu | TB cosine cặp trùng | 0.6298 | 0.9355 |
| Câu | TB cosine cặp không trùng | 0.1570 | 0.8420 |
| Câu | Gap (TB trùng − TB không trùng) | 0.4728 | 0.0935 |
| Câu | Margin (min trùng − max không trùng) | 0.0209 | 0.0087 |
| Câu | Độ chính xác tại ngưỡng tốt nhất | 1.0000 | 1.0000 |
| Câu | Ngưỡng tốt nhất (cosine) | 0.4414 | 0.9100 |
| Đoạn | AUC | 0.9479 | 1.0000 |
| Đoạn | AUC (chỉ diễn đạt lại vs cùng lĩnh vực) | 0.9219 | 1.0000 |
| Đoạn | TB cosine cặp trùng | 0.6483 | 0.9485 |
| Đoạn | TB cosine cặp không trùng | 0.2879 | 0.8631 |
| Đoạn | Gap (TB trùng − TB không trùng) | 0.3604 | 0.0854 |
| Đoạn | Margin (min trùng − max không trùng) | -0.0727 | 0.0091 |
| Đoạn | Độ chính xác tại ngưỡng tốt nhất | 0.9000 | 1.0000 |
| Đoạn | Ngưỡng tốt nhất (cosine) | 0.5909 | 0.9298 |

| Nhóm cặp (TB cosine) | Loại | bkai | e5 |
|---|---|---:|---:|
| DIEN_DAT_LAI | Tên đề tài | 0.5810 | 0.9214 |
| CUNG_LINH_VUC | Tên đề tài | 0.4369 | 0.8821 |
| KHONG_LIEN_QUAN | Tên đề tài | 0.1471 | 0.8149 |
| DIEN_DAT_LAI | Câu | 0.6298 | 0.9355 |
| CUNG_LINH_VUC | Câu | 0.2246 | 0.8622 |
| KHONG_LIEN_QUAN | Câu | 0.0218 | 0.8017 |
| DIEN_DAT_LAI | Đoạn | 0.6483 | 0.9485 |
| CUNG_LINH_VUC | Đoạn | 0.4066 | 0.8815 |
| KHONG_LIEN_QUAN | Đoạn | 0.0505 | 0.8264 |

| Chi phí trên máy phát triển | bkai | e5 | Cổng |
|---|---:|---:|---|
| Nạp mô hình (s, từ cache) | 8.86 | 10.55 | — |
| Encode 1 tên đề tài (ms, trung vị 20 lần) | 18.2 | 20.9 | — |
| Encode 300 câu (s) | 4.84 | 6.30 | ≤ 20 s |
| RSS đỉnh của tiến trình (MB) | 1047.7 | 1572.9 | ≤ 2560 MB |

Máy đo: 16 CPU logic, torch 2.14.0+cpu (4 luồng), sentence-transformers 6.1.0, transformers 5.17.0, underthesea 9.5.0, Python 3.12.3. Đo ngày 2026-09-28 (bkai) và 2026-09-28 (e5).

Quyết định: **bkai-foundation-models/vietnamese-bi-encoder** (`bkai`), nhánh quy tắc `MAC_DINH_BKAI` — chenh AUC e5 - bkai: CAU +0.0000, DOAN +0.0521 (can >= 0.05 tren CA HAI); e5 KHONG dat nguong tren CAU -> giu mac dinh bkai (nho hon, 515 MiB).

### Quy tắc chọn (đăng ký trước) và quyết định

Quy tắc được viết ra trước khi chạy. Nó ưu tiên mô hình nhỏ hơn vì máy chủ dùng chung bộ nhớ:

> Chọn **e5** chỉ khi e5 nạp được **và** AUC của e5 vượt bkai **≥ 0,05 trên cả tập Câu và tập Đoạn**, đồng thời e5 encode 300 câu **≤ 20 s** và RSS đỉnh **≤ 2,5 GiB (2560 MB)**. Nếu bkai không nạp được hoặc trượt cổng 20 s trong khi e5 qua cả hai cổng → chọn e5. Nếu cả hai trượt cổng độ trễ → chọn bkai và ghi rõ rủi ro (dự phòng: backend ONNX). Mọi trường hợp còn lại → chọn **bkai**.

Cả hai mô hình đều qua cổng độ trễ và cổng bộ nhớ, với khoảng dư lớn. Trên tập Câu, hai mô hình bằng nhau: cả hai đều đạt AUC 1,0, tức chênh lệch 0. Trên tập Đoạn, e5 hơn 0,0521. Điều kiện "vượt ≥ 0,05 trên cả hai tập" **không** thỏa, nên quy tắc rơi vào nhánh mặc định.

**Mô hình được chốt: `bkai-foundation-models/vietnamese-bi-encoder`**, kèm tách từ `underthesea` và không dùng tiền tố. Profile cấu hình của dịch vụ AI là `bkai`. Quyết định ghi tại `tools/bakeoff/ket-qua.json`.

### Nhận xét

- **Độ phân tách:** e5 nhỉnh hơn một chút về AUC ở tên đề tài và đoạn. Tuy nhiên, điểm cosine của e5 dồn vào một dải rất hẹp: cặp không liên quan vẫn đạt khoảng 0,80–0,83, còn cặp trùng khoảng 0,92–0,95. Gap chỉ khoảng 0,06–0,09 và ngưỡng tốt nhất nằm quanh 0,91–0,93.
- **Ý nghĩa với bkai:** bkai trải điểm rộng hơn nhiều, gap 0,24–0,47. Cặp không liên quan có cosine trung bình thấp (0,02–0,15) và ngưỡng tốt nhất quanh 0,44–0,59. Với ngưỡng mà Bộ môn cấu hình được (D-04), dải điểm rộng giúp ngưỡng bớt nhạy với sai số hiệu chỉnh. "Tỷ lệ tương đồng" hiển thị cho người dùng cũng dễ hiểu hơn. Nhận xét này không thuộc quy tắc chọn, chỉ là quan sát bổ sung.
- **Ca khó chung:** cả hai mô hình đều gặp khó với tên đề tài có cùng khuôn "Xây dựng hệ thống quản lý … cho …". Cặp "thư viện" với "ký túc xá" là cặp không trùng có cosine cao nhất ở cả hai mô hình. Ở mức tên đề tài, margin của cả hai đều âm, tức không có ngưỡng nào tách đúng mọi cặp. Vì vậy, cảnh báo trùng tên đề tài nên được trình bày là **gợi ý đề tài tương tự kèm tỷ lệ** để giảng viên xem xét, không phải kết luận tự động.
- **Chi phí:** bkai nhẹ hơn e5 (RSS đỉnh khoảng 1,05 GB so với 1,57 GB) và nhanh hơn (4,84 s so với 6,30 s cho 300 câu). Cả hai đều nằm xa trong giới hạn NFR: kiểm tra tên đề tài ≤ 5 s, kiểm tra tài liệu ≤ 30 s.

### Hạn chế

- Tập đánh giá **nhỏ (80 cặp) và tự soạn**, nên kết quả chỉ mang tính **định hướng**, không có ý nghĩa thống kê chặt chẽ. Chênh lệch AUC vài phần trăm nằm trong mức dao động có thể có khi đổi vài cặp.
- Số đo chi phí lấy trên máy phát triển dùng chung (16 CPU logic, tải nền thay đổi), không phải máy chủ triển khai. Độ trễ thật được đo lại trên container ở bước kiểm thử hiệu năng.
- Bằng chứng cuối cùng về chất lượng phát hiện và ngưỡng mặc định là đánh giá trên tập tài liệu thử nghiệm có phần giữ lại (held-out) không dùng để hiệu chỉnh (mục 4.x.1 và 4.x.3). Nếu kết quả đó cho thấy bkai không đạt, việc đổi mô hình chỉ là thay cấu hình profile và lập chỉ mục lại (`/reindex`).

### Chạy lại

```bash
cd tools/bakeoff
uv sync --frozen
uv run python bakeoff.py --validate-pairs
uv run python bakeoff.py --profile bkai   # tiến trình riêng
uv run python bakeoff.py --profile e5     # tiến trình riêng, sau khi bkai đã thoát
uv run python bakeoff.py --decide
uv run python bakeoff.py --bang           # sinh lại các bảng ở trên
```
