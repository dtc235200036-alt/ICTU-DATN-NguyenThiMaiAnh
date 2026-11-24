### 4.7.5. Đánh giá kiểu PAN trên đồ án thật

> **Mã PI:** 3.4 — **Yêu cầu:** AISV-04, DATA-03

> Mã nguồn: `ai-service/evaluation/` (`tao_bo.py` dựng bộ dữ liệu, `obfuscate.py` các kiểu biến đổi, `pan_eval.py` chạy và chấm, `pan_metrics.py` chỉ số PAN-PC). Số liệu trong trang này chép từ `ket-qua-<nhãn>.json` do `pan_eval.py` ghi, ngày 09/11/2026 (bộ v1 và bộ v2).

#### Mục tiêu

Trang 03 hiệu chỉnh ngưỡng trên 25 cặp tài liệu **tổng hợp**. Trang này đo hệ thống trên **văn bản đồ án thật** theo khung đánh giá của cuộc thi PAN (Potthast và cs. 2010, PAN-PC): chèn các đoạn chép đã biến đổi vào đồ án thật, ghi vị trí ký tự của từng đoạn, rồi đo xem hệ thống phát hiện được bao nhiêu ký tự, theo từng kiểu biến đổi. Mục đích:

- biết hệ thống bắt được kiểu chép nào và bỏ sót kiểu nào, thay vì một con số chung;
- tìm lỗ hổng của thuật toán trên văn bản thật. Lần chạy đầu đo được lỗ hổng của câu ghép: câu ghép từ hai câu nguồn chỉ được khoảng 50 % độ phủ (kiểu `gop_cau`). Hai lỗi đầu vào khác được đo và sửa trên cùng kho đồ án thật: PDF sinh từ LaTeX bị dính âm tiết, và dải chấm mục lục của LaTeX lọt bộ lọc mẫu chung. Cả ba đã sửa ngày 09/11/2026 (`docs/phuong-phap-kiem-tra-dao-van.md`, mục 3.1, 3.3, 3.5);
- chọn ngưỡng cho nhãn đoạn "Trùng sửa nhẹ".

Bộ đánh giá dựng theo gợi ý trong bản đề xuất thuật toán của giảng viên hướng dẫn: chưa có bộ chuẩn công khai cho tiếng Việt nên tự dựng bằng cách chèn đoạn chép vào văn bản sạch, như PAN-PC.

#### Dữ liệu

- **Nguồn:** 106 tệp PDF báo cáo đồ án khóa cũ (K19–K21) trong gói nạp kho lấy từ Drive của Bộ môn. Văn bản được trích bằng đúng hàm trích xuất production (`calibration/extract.py`, bản sao của `backend/app/services/documents.py`). Loại các tệp quá ít nội dung thân bài: bộ v1 còn **105 đồ án** (loại 1 tệp), bộ v2 trích xuất bằng hàm mới còn **104 đồ án** (loại 2 tệp).
- **Chia ngẫu nhiên** (hạt giống 20261109): **75 đồ án (bộ v2: 74) làm kho nguồn**, **30 đồ án làm tài liệu nghi vấn**: 20 bị chèn đạo văn, 10 để nguyên (sạch). Tài liệu nghi vấn không nằm trong kho nguồn.
- **Bảo mật dữ liệu:** đây là văn bản thật của sinh viên. Bộ dữ liệu, văn bản chèn và tệp kết quả chi tiết nằm **ngoài kho git** (`tao_bo.py` từ chối ghi vào trong repo). Trang này chỉ ghi số liệu tổng hợp: không có trích đoạn đồ án, không có tên sinh viên hay giảng viên, không nêu mã hay tên đề tài của từng đồ án.

#### Phương pháp

1. **Chọn đoạn chép.** Đoạn = 3–8 câu thân bài liền nhau, tổng 60–250 âm tiết (trung vị khoảng 114), còn lại sau `strip_boilerplate` và chia câu của production. Chỉ lấy câu văn xuôi tiếng Việt: kết thúc bằng dấu câu, không ký hiệu mã nguồn hay gạch đầu dòng, ít nhất 30 % âm tiết có dấu, không dính tiêu đề hay ô bảng.
2. **Chèn.** Mỗi tài liệu bị chèn nhận **7 đoạn từ 7 nguồn khác nhau, mỗi đoạn một kiểu biến đổi**; kiểu được xáo để vị trí không lộ kiểu. Đoạn được chèn thành một dòng riêng tại ranh giới dòng trong thân bài, rải đều (hai đoạn chèn luôn cách nhau ít nhất một câu của tài liệu nền). Tổng cộng **140 ca**, 20 ca mỗi kiểu. `tao_bo.py` tự kiểm hai chiều: lát cắt theo vị trí ghi trong `nhan.json` đúng văn bản mong đợi ở cả phía nghi vấn lẫn phía nguồn, đoạn chèn còn nguyên sau bộ lọc mẫu chung, và bỏ các đoạn chèn thì trả lại đúng tài liệu nền.
3. **Kiểu biến đổi**, đặt tên theo bảng phân loại ReParaphrased (Zhou và cs. 2024) và kiểu che giấu của PAN:

| Kiểu | Biến đổi (`evaluation/obfuscate.py`) | Tương ứng |
|---|---|---|
| `nguyen_van` | Chép nguyên văn | Verbatim |
| `sua_nhe` | Thay khoảng 15–25 % số cụm có trong từ điển đồng nghĩa (`tu-dong-nghia.tsv`), bỏ 1–3 hư từ ("các", "những", "đã", "sẽ"…), bỏ hoặc đổi 1–2 dấu phẩy, chấm phẩy | Same Polarity Substitution, Functional Word Substitution, Punctuation Changes |
| `dao_cau` | Đảo thứ tự câu (luôn khác thứ tự gốc) | Change of Order |
| `gop_cau` | Gộp từng cặp câu liên tiếp bằng từ nối (", đồng thời", " và", "; ngoài ra,"…) | Coordination Changes |
| `tach_cau` | Tách câu dài hơn 25 âm tiết tại dấu phẩy gần giữa câu (mỗi nửa ≥ 6 âm tiết) | Chiều ngược của Coordination Changes |
| `xao_tron` | Xáo từ trong khoảng 30 % cửa sổ 3–4 từ, rồi xóa khoảng 5 % và chèn khoảng 5 % từ lấy từ chính đoạn | Random obfuscation của PAN-PC |
| `llm` | Một mô hình ngôn ngữ lớn (Claude) đóng vai ChatGPT nhận yêu cầu của sinh viên: "Viết lại đoạn văn sau bằng cách diễn đạt khác, giữ nguyên ý, văn phong đồ án tốt nghiệp"; ràng buộc: giữ dữ kiện, tên riêng, thuật ngữ; đổi từ ngữ và cấu trúc câu; tránh chuỗi từ 8 âm tiết trở lên trùng bản gốc (trừ tên riêng, tên gọi); độ dài trong khoảng ±25 % | Diễn đạt lại bằng mô hình ngôn ngữ lớn |

   Các kiểu trừ `llm` là hàm tất định theo hạt giống; văn bản `llm` lấy từ tệp `dien-dat-lai-llm.jsonl`.
4. **Chạy hệ thống** trong tiến trình như `calibration/calibrate.py`: SQLite `thesis_ai` tạm (migration như MySQL), nạp các nguồn (75 ở bộ v1, 74 ở bộ v2) là DOCUMENT qua `pipeline.ingest_many` (mỗi nguồn một nhóm), rồi mỗi tài liệu nghi vấn qua `score_document` và `flag_chunks` (đúng quy tắc gắn cờ của `check_document`). Mô hình `bkai-foundation-models/vietnamese-bi-encoder@84f9d9ada0d1`; ngưỡng đoạn 67,7 %, ngưỡng nguyên văn 56,0 % (giá trị hiệu chỉnh ở trang 03).
5. **Phát hiện** = chuỗi tối đa các câu liên tiếp gắn cờ cùng một nguồn (không cắt 6 câu như phần hiển thị). Phía nghi vấn: từ đầu câu đầu tới cuối câu cuối; phía nguồn: từ đầu tới cuối các câu nguồn khớp. Mọi câu được định vị chính xác trong văn bản gốc, không câu nào phải dùng cách dò dự phòng: 18.297 câu nghi vấn và 39.369 câu nguồn ở bộ v1; 14.609 và 38.234 ở bộ v2.
6. **Chỉ số** (`evaluation/pan_metrics.py`, theo Potthast và cs. 2010):
   - phát hiện r tính cho ca s khi cùng cặp tài liệu và chồng lấn ở **cả** phía nghi vấn lẫn phía nguồn (như bộ đo tham chiếu của PAN);
   - **recall** vĩ mô = trung bình trên các ca của tỷ lệ ký tự của ca được phát hiện phủ; **precision** vĩ mô = trung bình trên các phát hiện của tỷ lệ ký tự của phát hiện nằm trong một ca; ký tự tính ở cả hai phía;
   - **granularity** = số phát hiện trung bình trên mỗi ca được phát hiện (1 là tốt nhất);
   - **plagdet** = F1 / log₂(1 + granularity);
   - thêm: recall theo kiểu, *tỷ lệ phát hiện* (ca có recall > 0), recall khi chỉ giữ phát hiện do câu gắn cờ nguyên văn hoặc chỉ do câu gắn cờ ngữ nghĩa;
   - **mức tài liệu:** cảnh báo khi tỷ lệ theo nguồn cao nhất ≥ ngưỡng tài liệu hoặc tỷ lệ tổng ≥ ngưỡng tổng, với cặp ngưỡng hiệu chỉnh 10,4 % / 14,8 % và cặp ngưỡng máy chủ 25 % / 25 %.

#### Kết quả bộ v1

Bộ v1 dựng bằng hàm trích xuất PDF **cũ** (chưa dựng lại dấu cách) và chạy với bộ lọc mẫu chung **cũ**. Hai lần chạy: *trước* và *sau* khi tính độ phủ nguyên văn theo từng nguồn (`VanTaySnapshot.match`, `covered_mask`); mọi thứ khác giữ nguyên.

**Chỉ số tổng** (140 ca; 535 phát hiện trước, 536 sau):

| Lần chạy | Precision | Recall | Granularity | Plagdet |
|---|---:|---:|---:|---:|
| Trước | 0,2298 | 0,8503 | 1,0 | 0,3619 |
| Sau | 0,2294 | 0,8544 | 1,0 | 0,3617 |

**Theo kiểu biến đổi** (20 ca mỗi kiểu, lần chạy *sau*; số trong ngoặc là lần chạy *trước* khi khác):

| Kiểu | Recall | Tỷ lệ phát hiện | Recall do tín hiệu nguyên văn | Recall do tín hiệu ngữ nghĩa |
|---|---:|---:|---:|---:|
| `nguyen_van` | 0,950 | 0,95 | 0,950 | 0,000 |
| `sua_nhe` | 1,000 | 1,00 | 0,941 | 0,058 |
| `dao_cau` | 1,000 | 1,00 | 1,000 | 0,000 |
| `gop_cau` | **0,928** (0,895) | 1,00 | **0,928** (0,590) | 0,000 (0,268) |
| `tach_cau` | 0,950 | 0,95 | 0,948 | 0,000 |
| `xao_tron` | 0,590 (0,594) | 0,70 | 0,098 (0,087) | 0,471 (0,482) |
| `llm` | 0,563 | 0,70 | 0,000 | 0,563 |

Nhận xét:

- **Chép nguyên văn, sửa nhẹ, đảo câu, tách câu** được bắt gần đủ, gần như toàn bộ nhờ vân tay. Đảo câu không làm khó hệ thống vì mỗi câu được so riêng.
- **Gộp câu** là lỗ hổng mà bộ đánh giá tìm ra: trước khi sửa, câu ghép "A, đồng thời b" chỉ được khoảng 50 % độ phủ với mỗi câu nguồn, dưới ngưỡng 56 %, nên phần lớn chỉ được bắt nhờ tín hiệu ngữ nghĩa (0,268) hoặc bị bỏ. Sau khi độ phủ lấy hợp các đoạn chung với mọi câu ứng viên của **một** nguồn, phần do tín hiệu nguyên văn tăng từ 0,590 lên 0,928 và recall tăng từ 0,895 lên 0,928. Các mẩu ngắn hơn t = 9 âm tiết của những câu khác nhau vẫn không cộng lại, nên chỉ số của các kiểu khác gần như không đổi.
- **Hai ca "bỏ sót"** của `nguyen_van` và `tach_cau` cùng lấy từ một đồ án nguồn chứa **cùng một đoạn hai lần**. Hệ thống khớp với lần xuất hiện thứ nhất, ca được ghi ở lần thứ hai; cách chấm PAN đòi chồng lấn ở phía nguồn nên không tính. Đây là đặc điểm của dữ liệu, không phải bỏ sót.
- **Viết lại bằng mô hình ngôn ngữ lớn** và **xáo trộn kiểu PAN** là hai kiểu khó: mỗi kiểu 6/20 ca không được phát hiện chút nào. Đoạn `llm` chỉ được bắt bằng tín hiệu ngữ nghĩa (không còn cụm 9 âm tiết chung nào), phù hợp nhận xét của Iqbal và cs. (2025) rằng embedding dùng nguyên rồi so cosine còn yếu với câu diễn đạt lại.

**Độ phủ vân tay trong ca** (×100, lần chạy *sau*). *Câu*: câu nghi vấn nằm trọn trong ca và câu nguồn khớp nhất thuộc đúng nguồn của ca. *Đoạn*: đoạn hiển thị (tối đa 6 câu) có từ nửa số ký tự gắn cờ nguyên văn, cùng nguồn, chồng lên ca; giá trị là `diem_nguyen_van`, đúng đại lượng `check_document` so với ngưỡng nhãn sửa nhẹ.

| Kiểu | Số câu | Câu: p10 / trung vị | Số đoạn | Đoạn: p5 / p10 / trung vị |
|---|---:|---|---:|---|
| `nguyen_van` | 85 | 100 / 100 | 22 | 98,34 / 98,58 / 100 |
| `sua_nhe` | 96 | 64,58 / 94,86 | 26 | 61,92 / 69,89 / 88,10 |
| `dao_cau` | 97 | 100 / 100 | 21 | 99,10 / 99,12 / 100 |
| `gop_cau` | 46 | 94,98 / 98,06 | 20 | 95,37 / 96,01 / 97,40 |
| `tach_cau` | 135 | 100 / 100 | 32 | 88,04 / 96,28 / 100 |
| `xao_tron` | 28 | 26,81 / 44,80 | 2 | 43,38 / 45,07 / 58,61 |
| `llm` | 0 | — | 0 | — |

> **Đã thay ngày 24/11/2026:** nhãn "Trùng sửa nhẹ" không còn dùng `diem_nguyen_van` mà dùng tỷ lệ khớp chữ giữa đoạn và đoạn nguồn (ngưỡng 0,99; `docs/phuong-phap-kiem-tra-dao-van.md` mục 3.7), vì độ phủ vân tay hụt ở mép câu làm đoạn chép y hệt gồm câu ngắn bị gắn nhầm "sửa nhẹ". Hai bảng biên Youden dưới đây giữ lại làm lịch sử.

**Ngưỡng nhãn "Trùng sửa nhẹ"** (bản 09/11, `NGUONG_SUA_NHE` = 96,3). Chọn bằng Youden J như trang 03, dương = đoạn của ca `nguyen_van`, âm = đoạn của ca `sua_nhe`:

| Mức | Ngưỡng | AUC | J | TPR / FPR | Dương nhỏ nhất | Âm lớn nhất | Khoảng chọn |
|---|---:|---:|---:|---|---:|---:|---|
| Câu (không dùng) | 98,9 | 0,804 | 0,588 | 0,953 / 0,365 | 93,75 | 100 | (97,73; 100] |
| **Đoạn (dùng)** | **96,3** | **0,977** | **0,962** | 1,000 / 0,038 | 98,02 | 100 | (94,5; 98,02] |

- Mức câu tách kém vì phần lớn câu trong một đoạn sửa nhẹ vẫn còn nguyên (trung vị 94,86, p90 100). Ở mức đoạn, mọi đoạn chép nguyên văn có điểm ≥ 98,02; các đoạn sửa nhẹ ≤ 94,5 trừ một đoạn đạt 100. Sửa một từ trong câu 30 âm tiết (khoảng 97) vẫn mang nhãn "nguyên văn".
- Một số đoạn `gop_cau` và `tach_cau` (p10 lần lượt 96,01 và 96,28) có điểm dưới 96,3 nên mang nhãn "sửa nhẹ": từ nối và chỗ cắt câu đúng là một thay đổi nhỏ trên chữ.
- Nhãn chỉ để hiển thị: cờ câu và mọi tỷ lệ không đổi. Ngưỡng được chọn trên chính bộ này, chưa có tập giữ riêng để kiểm chứng; bộ v2 cho biên khác (93,7, xem dưới).

**Mức tài liệu** (giống nhau ở hai lần chạy):

| Ngưỡng tài liệu / tổng | Bị chèn, cảnh báo | Bị chèn, bỏ sót | Sạch, cảnh báo nhầm | Sạch, không cảnh báo |
|---|---:|---:|---:|---:|
| 10,4 % / 14,8 % (hiệu chỉnh) | 2 | 18 | 0 | 10 |
| 25 % / 25 % (máy chủ) | 0 | 20 | 0 | 10 |

- 10 tài liệu sạch: tỷ lệ tổng 1,3–7,3 % (trung vị 3,6 %), tỷ lệ với nguồn cao nhất 0,5–1,8 %.
- 20 tài liệu bị chèn: tỷ lệ tổng 3,3–17,1 % (trung vị 6,9 %), tỷ lệ với nguồn cao nhất 0,4–7,4 %. Hai tài liệu bị cảnh báo đều do ngưỡng tổng (15,5 % và 17,1 %).
- Kết quả này **không** có nghĩa là hệ thống bỏ sót 18–20 bài chép: phần chèn chỉ là 7 đoạn trong cả một đồ án (khoảng 5–10 % nội dung), lại chia cho 7 nguồn. Ngưỡng theo tỷ lệ đo **chép bao nhiêu**, không đo **có chép hay không**. Mọi đoạn phát hiện vẫn hiện trong danh sách đoạn trùng để giảng viên xem, kể cả khi tài liệu không vượt ngưỡng.

**Phát hiện không trùng ca nào** (precision thấp). 410 trong 536 phát hiện không chồng lên ca được chèn nào; 9 trong 10 phát hiện dài nhất do tín hiệu ngữ nghĩa. Vì nền là đồ án thật, các phát hiện này gồm:

- nội dung giống nhau thật giữa các đồ án cùng chủ đề;
- đoạn kiến thức giáo khoa chung (định nghĩa, mô tả công nghệ) gần nhau về nghĩa;
- phần mẫu chung lọt bộ lọc cũ (dải chấm mục lục, mảnh bìa), đã sửa trong bộ lọc mới.

Vì vậy precision 0,23 là **cận dưới** của precision thật, và 410 là **cận trên của nhiễu**, không phải số cảnh báo sai đã kiểm chứng.

#### Kết quả bộ v2

Bộ v2 dựng lại từ cùng gói nạp và cùng hạt giống bằng hàm trích xuất PDF **mới** (dựng lại dấu cách), chạy với bộ lọc mẫu chung mới và đủ các sửa đổi ngày 09/11/2026 (độ phủ theo nguồn, chuẩn hóa `ƣ`, nhãn sửa nhẹ). Văn bản trích xuất đổi nên 2 tệp bị loại vì quá ít nội dung thân bài, còn 104 đồ án: 74 nguồn, 30 tài liệu nghi vấn (20 bị chèn, 10 sạch). Các đoạn chèn được **chọn lại** và các đoạn `llm` được **viết lại mới**; vẫn 140 ca, 20 ca mỗi kiểu.

**Chỉ số tổng** (140 ca):

| Bộ | Precision | Recall | Granularity | Plagdet | Phát hiện | Không trùng ca nào |
|---|---:|---:|---:|---:|---:|---:|
| v1 (sau) | 0,2294 | 0,8544 | 1,0 | 0,3617 | 536 | 410 |
| v2 | 0,2912 | 0,8907 | 1,0373 | 0,4275 | 464 | 325 |

**Theo kiểu biến đổi** (20 ca mỗi kiểu; cột cuối là recall của bộ v1, lần chạy *sau*):

| Kiểu | Recall | Tỷ lệ phát hiện | Recall do tín hiệu nguyên văn | Recall do tín hiệu ngữ nghĩa | Recall v1 |
|---|---:|---:|---:|---:|---:|
| `nguyen_van` | 0,982 | 1,00 | 0,982 | 0,000 | 0,950 |
| `sua_nhe` | 0,993 | 1,00 | 0,891 | 0,062 | 1,000 |
| `dao_cau` | 0,995 | 1,00 | 0,995 | 0,000 | 1,000 |
| `gop_cau` | 0,924 | 1,00 | 0,924 | 0,000 | 0,928 |
| `tach_cau` | 0,959 | 1,00 | 0,957 | 0,008 | 0,950 |
| `xao_tron` | 0,589 | 0,80 | 0,129 | 0,456 | 0,590 |
| `llm` | **0,793** | 0,90 | 0,000 | 0,793 | 0,563 |

Nhận xét:

- Mọi ca của năm kiểu dựa vào vân tay đều được phát hiện (134/140 ca, bộ v1 126/140). Hai ca bỏ sót "đoạn lặp hai lần" của bộ v1 không còn vì đoạn đã được chọn lại.
- **Viết lại bằng mô hình ngôn ngữ lớn:** recall 0,793, chỉ 2/20 ca không được phát hiện (bộ v1: 0,563 và 6/20), vẫn hoàn toàn nhờ tín hiệu ngữ nghĩa. **Xáo trộn kiểu PAN** gần như không đổi (0,589, 4/20 ca bỏ sót).
- Granularity 1,037: một số ca được phát hiện thành hai đoạn rời.
- **v1 → v2 không phải so sánh có đối chứng.** Mức tăng gộp cả bản sửa trích xuất, bản sửa bộ lọc mẫu chung và khác biệt giữa hai bộ dữ liệu: đoạn chèn được chọn lại, kho nguồn ít hơn một đồ án, và đoạn `llm` mới bám độ dài bản gốc hơn (0,91–1,08 lần độ dài gốc, bộ v1 1,03–1,23 lần). Bản sửa trích xuất là giải thích hợp lý nhất cho mức tăng của `llm` và tín hiệu ngữ nghĩa, vì âm tiết bị dính ("hệthống") làm hỏng đầu vào của mô hình embedding, nhưng phần đóng góp này chưa được đo tách riêng.

**Độ phủ vân tay trong ca** (×100, cùng định nghĩa như bộ v1):

| Kiểu | Số câu | Câu: p10 / trung vị | Số đoạn | Đoạn: p5 / p10 / trung vị |
|---|---:|---|---:|---|
| `nguyen_van` | 82 | 96,87 / 100 | 22 | 93,94 / 94,55 / 100 |
| `sua_nhe` | 87 | 64,56 / 94,29 | 23 | 76,75 / 77,80 / 86,12 |
| `dao_cau` | 96 | 97,20 / 100 | 25 | 97,08 / 97,71 / 100 |
| `gop_cau` | 49 | 94,18 / 97,18 | 20 | 92,48 / 94,18 / 96,91 |
| `tach_cau` | 123 | 100 / 100 | 32 | 90,02 / 95,60 / 100 |
| `xao_tron` | 40 | 22,36 / 45,26 | 3 | 47,57 / 48,31 / 54,29 |
| `llm` | 3 | 25,86 / 32,73 | 0 | — |

**Kiểm tra lại ngưỡng nhãn "Trùng sửa nhẹ"** (cùng cách chọn như bộ v1, chỉ để kiểm tra; ngưỡng dùng vẫn là 96,3):

| Mức | Biên Youden | AUC | J | TPR / FPR | Dương nhỏ nhất | Âm lớn nhất | Khoảng chọn |
|---|---:|---:|---:|---|---:|---:|---|
| Câu | 96,6 | 0,778 | 0,524 | 0,915 / 0,391 | 90,0 | 100 | [96,43; 96,77] |
| Đoạn | 93,7 | 0,915 | 0,824 | 0,955 / 0,130 | 90,99 | 100 | [93,4; 93,92] |

- Biên mức đoạn trên bộ v2 là 93,7, khác 96,3 của bộ v1: biên giữa hai nhãn **chưa ổn định** giữa hai bộ dữ liệu, với mẫu nhỏ (22 đoạn chép nguyên văn, 23 đoạn sửa nhẹ).
- Ở ngưỡng 96,3, khoảng 10–15 % đoạn chép nguyên văn của bộ v2 hiện nhãn "sửa nhẹ" (p10 94,55), chủ yếu do câu ở mép đoạn chèn bị gộp với chữ của tài liệu nền khi chia câu; khoảng 10 % đoạn sửa nhẹ hiện nhãn "nguyên văn" (p90 97,73).
- Ngày 09/11 giữ 96,3; ngày 24/11 thay bằng tỷ lệ khớp chữ (xem ghi chú ở bảng bộ v1). Trên chính 40 ca này, tỷ lệ khớp chữ tách hoàn toàn: ca chép nguyên văn đều 1,00, ca sửa nhẹ 0,875–0,976.

**Mức tài liệu:**

| Ngưỡng tài liệu / tổng | Bị chèn, cảnh báo | Bị chèn, bỏ sót | Sạch, cảnh báo nhầm | Sạch, không cảnh báo |
|---|---:|---:|---:|---:|
| 10,4 % / 14,8 % (hiệu chỉnh) | 3 | 17 | 0 | 10 |
| 25 % / 25 % (máy chủ) | 1 | 19 | 0 | 10 |

- 10 tài liệu sạch: tỷ lệ tổng 0,03–6,50 % (trung vị 2,41 %; bộ v1 1,3–7,3 %), tỷ lệ với nguồn cao nhất 0,03–1,45 %.
- 19 tài liệu bị chèn: tỷ lệ tổng 3,6–16,75 % (trung vị 7,45 %), tỷ lệ với nguồn cao nhất 0,8–7,4 %. Hai tài liệu bị cảnh báo ở cặp ngưỡng hiệu chỉnh do ngưỡng tổng (15,43 % và 16,75 %).
- **Một tài liệu ngoại lai** có tỷ lệ tổng 51,04 % (26,77 % với một nguồn), bị cảnh báo ở cả hai cặp ngưỡng. Phần lớn tỷ lệ này **không** thuộc đoạn được chèn: đây là một đồ án thật khóa K21 có nhiều đoạn trùng nguyên văn dài (tới khoảng 2.000 ký tự mỗi đoạn) với hai đồ án thật khóa K21 khác trong kho nguồn, cả ba cùng nhóm đề tài. Hệ thống đã làm lộ ra việc dùng lại văn bản thật giữa các đồ án. Đó là khuôn mẫu chung của một nhóm hay sao chép thì cần người xem lại để kết luận; trang này không nêu mã, tên hay đề tài của ba đồ án.

**Phát hiện không trùng ca nào.** 325 trong 464 phát hiện không chồng lên ca được chèn nào. Trong 10 phát hiện dài nhất (khoảng 1.000–2.000 ký tự), 8 do tín hiệu nguyên văn và 2 do tín hiệu ngữ nghĩa (bộ v1: 9/10 do tín hiệu ngữ nghĩa), và 9 thuộc tài liệu ngoại lai trên. Một phần "nhiễu" vì vậy là phát hiện đúng: precision 0,29 vẫn là **cận dưới**, 325 vẫn là **cận trên của nhiễu**.

#### Hạn chế

- **Ca đạo văn là nhân tạo.** Văn bản nền và đoạn nguồn là thật, nhưng việc chèn và biến đổi do chương trình (và một mô hình ngôn ngữ lớn) làm. Sinh viên thật có thể chép theo cách khác, ví dụ chép nhiều đoạn từ một nguồn, hoặc vừa chép vừa sửa nhiều chỗ.
- **Mẫu nhỏ:** 20 ca mỗi kiểu, nên mỗi ca chiếm 0,05 recall của kiểu đó.
- **Từ điển đồng nghĩa tự soạn** cho kiểu `sua_nhe` chỉ có 260 cặp cụm từ, nên mức sửa có thể nhẹ hơn cách sinh viên thật sửa.
- **Precision chưa đo được chính xác** vì không có nhãn cho phần nội dung thật giống nhau giữa các đồ án.
- **Nhãn sửa nhẹ (tỷ lệ khớp chữ, 0,99)** mới kiểm chứng ở mức ca; chưa chạy lại toàn bộ bộ đánh giá với nhãn mới.
- **Hai bộ v1, v2 không so sánh có đối chứng:** khác cả hàm trích xuất, bộ lọc, đoạn chèn và đoạn `llm`, nên chưa tách được đóng góp của từng bản sửa.

#### Chạy lại

Từ thư mục `ai-service/` (cần vài GiB RAM trống cho mô hình; không cần docker hay MySQL). `<goi-nap>` là thư mục gói nạp kho (`manifest.json` và các tệp PDF), `<dir>` là thư mục bộ dữ liệu **ngoài kho git**.

1. Chọn tài liệu nền, nguồn và đoạn; ghi `ke-hoach.json` và `can-llm.jsonl` (đoạn gốc của các ca `llm`):

   ```bash
   cd ai-service
   .venv/bin/python -m evaluation.tao_bo chon --goi <goi-nap> --out <dir>
   # mặc định: --seed 20261109 --so-nghi-van 20 --so-sach 10
   ```

2. Diễn đạt lại bằng mô hình ngôn ngữ lớn (làm tay, ngoài repo): mỗi dòng `{"id", "nguon", "text"}` của `<dir>/can-llm.jsonl` được đưa cho mô hình ngôn ngữ lớn, đóng vai ChatGPT nhận yêu cầu của sinh viên: "Viết lại đoạn văn sau bằng cách diễn đạt khác, giữ nguyên ý, văn phong đồ án tốt nghiệp", kèm ràng buộc giữ dữ kiện, tên riêng, thuật ngữ; đổi từ ngữ và cấu trúc câu; tránh chuỗi từ 8 âm tiết trở lên trùng bản gốc (trừ tên riêng, tên gọi); độ dài trong khoảng ±25 %. Ghi kết quả vào `<dir>/dien-dat-lai-llm.jsonl`, mỗi dòng `{"id": "<id của ca>", "text": "<đoạn đã viết lại>"}`. Bước sau từ chối chạy nếu thiếu ca nào.

3. Áp dụng biến đổi, ghi `nguon/`, `nghi-van/`, `nhan.json` rồi tự kiểm:

   ```bash
   .venv/bin/python -m evaluation.tao_bo tao --out <dir>
   ```

4. Chạy hệ thống và chấm; ghi `ket-qua-<ten>.json` và `ket-qua-<ten>.md`:

   ```bash
   .venv/bin/python -m evaluation.pan_eval --data <dir> --out <dir>/ket-qua --nhan <ten>
   # tùy chọn: --nguong-doan 67.7 --nguong-nguyen-van 56.0 (mặc định lấy từ cấu hình dịch vụ AI)
   ```

   Vector câu được lưu đệm ở `<dir>/cache-vector/<mô hình>/`, nên chạy lại sau khi sửa thuật toán hay đổi ngưỡng không phải mã hóa lại. Tệp kết quả `.json`/`.md` có trích đoạn ngắn của các phát hiện dài nhất để xem tay, nên cũng phải nằm ngoài kho git.

Kiểm thử của bộ đánh giá (profile `fake`, không cần mô hình): `uv run pytest tests/test_pan_metrics.py tests/test_obfuscate.py tests/test_pan_eval_smoke.py`.
