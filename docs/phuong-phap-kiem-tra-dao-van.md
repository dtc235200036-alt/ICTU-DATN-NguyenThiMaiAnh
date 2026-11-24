# Phương pháp kiểm tra trùng lặp, đạo văn của hệ thống

> Đề tài: Hệ thống quản lý đồ án sinh viên, Khoa CNTT, Trường ĐH CNTT&TT (ICTU), Đại học Thái Nguyên
> Người thực hiện: Nguyễn Thị Mai Anh (DTC235200036)
> Cập nhật: 09/11/2026, theo mã nguồn sau đợt sửa bộ kiểm tra trùng lặp: độ phủ nguyên văn theo từng nguồn, nhãn "Trùng sửa nhẹ", sửa trích xuất PDF, lọc mẫu chung, đánh giá kiểu PAN; 23/11/2026 thêm kiểm tra một tệp tải lên, mục 3.10 (lần trước: 22/10/2026, commit `4b151e0`, chuyển tín hiệu nguyên văn sang vân tay văn bản).
> Tài liệu liên quan: cơ sở lý thuyết [`chuong-1-co-so-ly-thuyet/07-tim-kiem-vector-va-phat-hien-trung-lap.md`](chuong-1-co-so-ly-thuyet/07-tim-kiem-vector-va-phat-hien-trung-lap.md), khảo sát công cụ [`khao-sat-cong-cu-kiem-tra-trung-lap.md`](khao-sat-cong-cu-kiem-tra-trung-lap.md), số liệu hiệu chỉnh [`chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md`](chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md), đánh giá kiểu PAN [`chuong-4-trien-khai/thu-nghiem-ai/05-danh-gia-kieu-pan.md`](chuong-4-trien-khai/thu-nghiem-ai/05-danh-gia-kieu-pan.md).

Tài liệu này mô tả hệ thống kiểm tra một đề cương hoặc báo cáo như thế nào, từ lúc nhận file tới lúc hiện "Vượt ngưỡng cảnh báo". Ở mỗi bước có ghi rõ phần nào học từ tài liệu tham khảo [1]–[8], phần nào khác và vì sao. Các số liệu lấy từ mã nguồn, lần hiệu chỉnh ngày 21/10/2026 và lần đánh giá kiểu PAN ngày 09/11/2026 (mục 4.1).

---

## 1. Tóm tắt

```
 File nộp (DOCX / PDF)          Đồ án kho chỉ có mã nguồn LaTeX
          │                                  │ biên dịch sang PDF (mục 3.2)
          ▼                                  ▼
 [1] Trích xuất văn bản (Web API): DOCX đọc XML, PDF đọc bằng PyMuPDF (dựng lại dấu cách
     từ vị trí chữ), chuẩn hóa NFC
          │
          ▼
 [2] Lọc phần mẫu chung: bìa, lời cam đoan, mục lục (cả dải chấm LaTeX), tài liệu tham khảo,
     header/footer...
          │
          ▼
 [3] Chia câu: nối dòng thành một dòng chảy rồi tách câu (6–120 âm tiết)
          │
          ├──────────────────────────────┐
          ▼                              ▼
 [4a] Tín hiệu NGUYÊN VĂN         [4b] Tín hiệu NGỮ NGHĨA
      vân tay winnowing                embedding vietnamese-bi-encoder
      cụm 6 âm tiết, bỏ cụm phổ biến   tìm câu gần nghĩa nhất bằng FAISS
      điểm = độ phủ câu, gộp theo      điểm = cosine
      từng đồ án nguồn
          │                              │
          └──────────────┬───────────────┘
                         ▼
 [5] Gắn cờ từng câu (nguyên văn ≥ 56 % hoặc ngữ nghĩa ≥ 67,7 %), tính tỷ lệ trùng tổng
     và tỷ lệ theo từng đồ án nguồn, ghép câu liền nhau thành đoạn trùng có nhãn
     "trùng nguyên văn" / "trùng sửa nhẹ" / "trùng ngữ nghĩa"
                         │
                         ▼
 [6] Cảnh báo (Web API): một đồ án ≥ NGUONG_TAI_LIEU  HOẶC  tổng mọi nguồn ≥ NGUONG_TONG_TAI_LIEU
     (hiệu chỉnh: 10,4 % / 14,8 %; máy chủ đang dùng 25 % / 25 %, mục 3.8)
                         │
                         ▼
 [7] Giảng viên xem từng đoạn trùng đặt cạnh đoạn nguồn và tự kết luận
```

Hệ thống đi theo mô hình nhiều tầng mà Meuschke và cộng sự mô tả [3][4]. Tầng đầu tìm ứng viên nhanh bằng vân tay và chỉ mục vector, tầng sau so chi tiết từng câu, tầng cuối là người xem. Hệ thống chỉ **gợi ý** đoạn đáng ngờ; kết luận có đạo văn hay không vẫn do giảng viên đưa ra.

---

## 2. Các tài liệu tham khảo và điều hệ thống học được

| #   | Tài liệu                                                                                                     | Nội dung chính                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Hệ thống áp dụng                                                                                                                                                                                  |
| --- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [1] | Sorokina, Gehrke, Warner, Ginsparg (2006). *Plagiarism Detection in arXiv*, ICDM                             | Quét toàn bộ arXiv: 287.857 bài, 3.023 bài không dùng được vì lỗi chuyển đổi, còn 284.834 bài; chạy 20 giờ trên một CPU. Bài gửi dạng TeX (95,2 %) được **biên dịch sang PDF rồi mới trích văn bản**, vì đọc thẳng mã nguồn TeX cần cả một hệ TeX để thay macro. Đơn vị so là câu. Dùng winnowing theo từ (k = 7 từ, t = 12, w = 6). Bỏ các cụm 7 từ xuất hiện ở từ 4 bài khác tác giả trở lên (L-common, L = 4). Tách danh mục tài liệu tham khảo. Cố ý bỏ công thức vì công thức trùng chưa chắc là chép.                                                                      | Chuyển LaTeX sang PDF trước khi xử lý (mục 3.2); câu là đơn vị so; vân tay winnowing; lọc cụm phổ biến với L = 4; bỏ tài liệu tham khảo; không coi công thức là bằng chứng |
| [2] | Schleimer, Wilkerson, Aiken (2003). *Winnowing: Local Algorithms for Document Fingerprinting*, SIGMOD        | Chỉ giữ giá trị băm nhỏ nhất trong mỗi cửa sổ w k-gram. Bảo đảm: hai văn bản chung một đoạn dài ít nhất t = w + k − 1 thì chung ít nhất một vân tay. Đoạn ngắn hơn k là "nhiễu" và không bao giờ được xét.                                                                                                                                                                                                                                                                                                                                                                                                                           | Công thức t = w + k − 1 để chọn tham số (k = 6, w = 4 nên t = 9 âm tiết); tra vân tay bằng chỉ mục thay vì so vét cạn                                                                |
| [3] | Meuschke và cs. (2017). *Analyzing Mathematical Content to Detect Academic Plagiarism*, CIKM                | Hệ thống so văn bản tìm tốt bản chép gần nguyên văn nhưng bỏ sót diễn đạt lại, dịch và chép ý. Công thức toán là đặc trưng độc lập với chữ: so tần suất định danh (identifier) xếp được nguồn đúng lên đầu cho 8/10 ca thật, MRR 0,86, trên 105.120 bài arXiv (NTCIR-11). Quy trình chuẩn gồm lọc ứng viên, so chi tiết, hậu xử lý và người xem.                                                                                                                                                                                                                                                             | Mô hình nhiều tầng; thêm tín hiệu ngữ nghĩa để bắt diễn đạt lại. **Chưa** phân tích công thức (mục 6)                                                                     |
| [4] | Meuschke, Stange, Schubotz, Gipp (2018). *HyPlag: A Hybrid Approach to Academic Plagiarism Detection*, SIGIR | Kết hợp bốn loại đặc trưng: chữ, trích dẫn, công thức, hình ảnh. Phần chữ lọc ứng viên bằng vân tay từ 3 từ (Sherlock), so chi tiết bằng khớp chuỗi từ 12 từ giống nhau trở lên. Giao diện đặt văn bản nộp cạnh văn bản nguồn để người xem đối chiếu.                                                                                                                                                                                                                                                                                                                                                                       | Kết hợp hai tín hiệu (nguyên văn + ngữ nghĩa); màn chi tiết đặt đoạn nộp cạnh đoạn nguồn và tô cụm trùng. **Chưa** dùng trích dẫn và hình ảnh (mục 6)            |
| [5] | Satpute và cs. (2024). *Taxonomy of Mathematical Plagiarism*, arXiv:2401.16969                              | Gán nhãn 122 cặp tài liệu nghi chép trong zbMATH Open và xếp cách biến đổi nội dung toán vào 7 loại (diễn đạt lại, thêm/bớt, thay thế, chuyển công thức thành lời và ngược lại, đổi cách trình bày, biến đổi công thức, giữ cấu trúc lập luận nhưng đổi nghĩa). Họ dùng MathPix để chuyển PDF sang LaTeX nhằm lấy công thức. Các phương pháp tốt nhất hiện có chỉ đạt PlagDet 0,06 (phát hiện đạo văn) và 0,16 (so nội dung toán), tức là bỏ sót phần lớn các ca. Bài cũng lưu ý mô hình ngôn ngữ lớn làm việc đạo văn dễ hơn vì sinh ra nội dung không ghi nguồn. | Lý do ghi rõ giới hạn: hệ thống bắt tốt chép nguyên văn và diễn đạt lại mức câu, chưa bắt được chép ý, chép công thức hay chép rồi biến đổi mạnh                    |
| [6] | Zhou, Qiu, Liang, Acuna (2024). *Paraphrase Identification with Deep Learning: A Review of Datasets and Methods*, arXiv:2212.06933v3 | Tổng quan các phương pháp nhận diện diễn đạt lại, từ cách truyền thống tới học sâu. Đề xuất bảng phân loại **ReParaphrased** gồm 24 kiểu diễn đạt lại (mở rộng Extended Paraphrase Typology), ví dụ thay từ đồng nghĩa, thay hư từ, đổi dấu câu, đổi trật tự, nối câu bằng liên từ, chép nguyên văn. Chỉ ra một số kiểu xuất hiện quá ít trong các bộ dữ liệu phổ biến (kể cả dữ liệu huấn luyện mô hình ngôn ngữ lớn), làm giảm khả năng phát hiện đạo văn; công cụ sinh văn bản như ChatGPT, Claude làm việc chép bằng diễn đạt lại dễ hơn. | Dùng bảng phân loại để chọn và gọi tên các kiểu biến đổi trong bộ đánh giá kiểu PAN (mục 4.1); thêm kiểu "viết lại bằng mô hình ngôn ngữ lớn" |
| [7] | Iqbal, Sharjeel, Shafi, Mehmood, Raza (2025). *Urdu Sentential Paraphrased Plagiarism Detection Using Large Language Models*, ACM TALLIP 24(9) | Phát hiện câu diễn đạt lại cho tiếng Urdu, một ngôn ngữ ít tài nguyên. Nhận xét: các nghiên cứu tiếng Urdu trước đó dùng nguyên embedding huấn luyện sẵn rồi so cosine thì không cải thiện đáng kể. Bài sửa kiến trúc D-TRaPPD, dùng embedding của mô hình ngôn ngữ lớn làm đặc trưng và **huấn luyện có giám sát** bộ phân loại trên các kho cặp câu gán nhãn tay (2.684–4.900 cặp), đạt F1 92,09 % / 96,70 % / 98,23 % trên ba kho. | Giải thích vì sao tín hiệu ngữ nghĩa của hệ thống (embedding dùng nguyên, so cosine) còn yếu ở mức câu. **Chưa** huấn luyện có giám sát: cần cặp câu tiếng Việt có nhãn và GPU (mục 7) |
| [8] | Potthast, Stein, Barrón-Cedeño, Rosso (2010). *An Evaluation Framework for Plagiarism Detection*, COLING | Khung đánh giá của cuộc thi PAN: chèn đoạn đạo văn đã che giấu (nhân tạo hoặc do người viết) vào văn bản sạch, ghi vị trí ký tự của từng ca; đo precision, recall vĩ mô theo ký tự, granularity (số phát hiện trên mỗi ca) và điểm tổng hợp plagdet. Kiểu che giấu "random obfuscation" xáo, xóa, chèn từ ngẫu nhiên. | Bộ đánh giá kiểu PAN trên đồ án thật (mục 4.1): cùng cách dựng dữ liệu, cùng bốn chỉ số, cùng kiểu xáo trộn ngẫu nhiên |

---

## 3. Quy trình chi tiết

### 3.1. Nhận file và trích xuất văn bản

Do Web API thực hiện (`backend/app/services/documents.py`), ngay lúc sinh viên nộp:

- **DOCX:** đọc `word/document.xml` theo luồng (không tải toàn bộ cây XML), lấy chữ của mọi đoạn trong thân văn bản, kể cả ô bảng; tab và ngắt dòng giữ nguyên. Header, footer và chú thích cuối trang không được đọc.
- **PDF:** lấy chữ từng trang bằng PyMuPDF, nhưng **dựng lại dấu cách** từ vị trí từng ký tự (`_pdf_page_text`, đọc `page.get_text("rawdict")` theo đúng thứ tự khối, dòng như `page.get_text()`).
  - **Lỗi đã sửa:** PyMuPDF 1.28.2 (MuPDF) không bao giờ chèn dấu cách sau các chữ thuộc khối Unicode U+1E00–U+1EFF (ệ, ử, ế…). PDF sinh từ LaTeX (và một số bản xuất từ Word) không có ký tự dấu cách thật; khoảng trống giữa hai từ chỉ là vị trí đặt chữ. Kết quả là âm tiết bị dính: "hệthống", "sửdụng".
  - **Cách sửa:** trên mỗi dòng, chèn một dấu cách khi khoảng hở ngang giữa ký tự mới và mép phải xa nhất đã gặp lớn hơn 0,10 × cỡ chữ, và không bên nào đã là khoảng trắng. So với mép phải xa nhất (không chỉ ký tự liền trước) để dấu thanh vẽ rời hay glyph chồng nhau không sinh dấu cách. Các hệ số 0,08 / 0,10 / 0,12 cho cùng kết quả trên 104 PDF thật, nên lấy giá trị giữa.
  - **Hiệu quả trên 104 PDF đồ án thật của kho:** số lần xuất hiện của 6 cụm từ thông dụng ở dạng có dấu cách / dạng dính liền đổi từ 28.889 / 39.663 thành 68.552 / 0. Công cụ `pdftotext` cho 68.647 / 0, tức là bản trích mới gần như khớp.
  - **Vì sao quan trọng:** chữ dính làm sai âm tiết, nên vân tay của bài PDF không khớp với cùng nội dung nộp bằng DOCX, và embedding PhoBERT của câu dính chữ cũng kém đi.
  - **Chi phí:** trích xuất chậm hơn khoảng 3,4 lần (trung vị 0,35 giây, lớn nhất 0,74 giây mỗi tệp trên 104 PDF trên).
  - 25 PDF của bộ dữ liệu hiệu chỉnh (`seed-data`) cho văn bản giống hệt trước, nên các ngưỡng đã hiệu chỉnh không đổi. Bản sao hàm trích xuất trong `ai-service/calibration/extract.py` được sửa cùng lúc.
  - Văn bản PDF đã lưu trên máy chủ trước bản sửa vẫn dính chữ: cần trích xuất lại và nạp lại chỉ mục (quy trình ở `deploy/README.md`, mục "Trích xuất lại PDF sau bản sửa dấu cách").
- Toàn bộ chuẩn hóa về Unicode NFC, để chữ có dấu gõ kiểu tổ hợp (NFD) và kiểu dựng sẵn so khớp được với nhau. Dịch vụ AI chuẩn hóa thêm một bước (`ai-service/app/nlp/normalize.py`): chữ `ƣ`/`Ƣ` (U+01A3/U+01A2, không có trong tiếng Việt) mà font TCVN3 trong PDF cũ dùng thay cho `ư`/`Ư` được đổi về `ư`/`Ư`.
- Trích xuất là "tốt nhất có thể": lỗi hoặc không có chữ (ví dụ PDF chỉ gồm ảnh quét) thì việc nộp vẫn thành công nhưng tài liệu bị đánh dấu lỗi trích xuất và không kiểm tra trùng lặp. Hệ thống **chưa có OCR**.
- Văn bản dài hơn 800.000 ký tự (khoảng 230 trang) không được gửi sang dịch vụ AI; kết quả báo "Tài liệu quá dài để kiểm tra trùng lặp tự động".

Sorokina và cộng sự cũng gom mọi định dạng về một đường xử lý duy nhất: đưa hết về PDF rồi dùng một bộ chuyển PDF sang văn bản [1]. Hệ thống làm tương tự ở mức văn bản: DOCX và PDF có hai bộ đọc khác nhau, nhưng từ bước 3.3 trở đi chúng đi chung một đường.

### 3.2. Đầu vào LaTeX: biên dịch sang PDF rồi mới xử lý

**Vì sao không đọc thẳng mã nguồn `.tex`.** Theo kinh nghiệm của arXiv [1], lấy chữ từ PDF thực tế hơn đọc mã nguồn TeX, vì văn bản thật chỉ xuất hiện sau khi TeX thay hết macro. Với đồ án LaTeX của sinh viên, đọc thẳng `.tex` còn gặp thêm các vấn đề sau:

- chữ bị chia ra nhiều tệp (`\input`, `\include`), lẫn với lệnh định dạng, chú thích `%` và đoạn bị tắt bằng `\iffalse`;
- tên mục, tài liệu tham khảo (`.bib`), nhãn hình và bảng chỉ thành chữ sau khi biên dịch;
- văn bản chép từ một đồ án DOCX sẽ trông khác hẳn khi nằm trong mã LaTeX, nên vân tay khó khớp.

Biên dịch ra PDF cho đúng văn bản người đọc nhìn thấy. Sau đó tài liệu đi qua **cùng** đường xử lý với mọi PDF khác (mục 3.1, 3.3–3.6), nên vân tay của nó so được với đồ án nộp bằng DOCX hay PDF.

**Phạm vi.** Sinh viên nộp đề cương và báo cáo bằng DOCX hoặc PDF; người viết bằng LaTeX nộp file PDF đã biên dịch. Bước này vì thế chỉ cần khi **nạp kho đồ án cũ**. Hiện còn 22 trong 128 đồ án thật đã thu thập chưa nạp được vì chỉ có mã nguồn LaTeX.

**Quy trình đề xuất (chưa thực hiện):**

1. Xác định tệp chính của mỗi đồ án: tệp có `\documentclass` và `\begin{document}`.
2. Biên dịch trong môi trường cô lập, vì mã LaTeX có thể chạy lệnh hệ thống hoặc đọc tệp ngoài thư mục:
   - container tạm, không có mạng (`--network none`), có giới hạn thời gian;
   - tắt shell escape (`-no-shell-escape`), chỉ cho đọc và ghi trong thư mục đồ án (`openin_any=p`, `openout_any=p`);
   - `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`; nếu đồ án dùng `fontspec` thì chạy `latexmk -pdfxe`.
3. Kiểm tra PDF thu được:
   - trích thử văn bản và xem dấu tiếng Việt có đúng không. Font mã hóa T5 (gói `vntex`) đôi khi cho chữ trích ra sai dấu; khi đó biên dịch lại với XeLaTeX hoặc LuaLaTeX, hoặc bật ánh xạ ToUnicode (gói `cmap`, `\pdfgentounicode=1`);
   - số trang khớp với bản in hoặc bản PDF lưu ở khoa (nếu có).
4. Nạp PDF vào kho theo đúng đường đã dùng cho 106 đồ án hiện có: trích xuất bằng PyMuPDF, rồi đưa vào chỉ mục AI kèm nhóm là đề tài.
5. Nếu không biên dịch được (thiếu lớp tài liệu, font hoặc hình), có thể dùng phương án dự phòng: chuyển LaTeX sang văn bản thuần (ví dụ `pandoc -f latex -t plain`). Chất lượng thấp hơn vì macro tự định nghĩa không được thay, nên cần ghi chú nguồn này để biết vì sao vân tay có thể kém.

Công thức toán sau khi trích từ PDF thành các mảnh ký hiệu rời. Hệ thống không xử lý công thức riêng (mục 6); câu nào chỉ còn dưới 6 âm tiết sẽ bị bỏ ở bước chia câu.

### 3.3. Lọc phần mẫu chung

Dịch vụ AI bỏ những phần mọi đồ án đều có trước khi chia câu (`ai-service/app/nlp/boilerplate.py`). Nếu không bỏ, hai đồ án không liên quan cũng trùng nhau ở bìa và lời cam đoan:

- **bỏ nguyên mục:** lời cam đoan, lời cảm ơn, mục lục, các danh mục (hình, bảng, từ viết tắt, ký hiệu), tài liệu tham khảo, phụ lục, nhận xét của giảng viên;
- **dòng bìa:** tên trường, khoa, "Đồ án tốt nghiệp", tiêu ngữ "Độc lập - Tự do - Hạnh phúc", nhãn "Sinh viên thực hiện", "Giảng viên hướng dẫn" (cả biến thể "Giáo viên hướng dẫn"), "Thái Nguyên, … năm …". Ở phần đầu tài liệu (trước tiêu đề lớn đầu tiên), nhãn đứng riêng một dòng ("Giảng viên hướng dẫn:") kéo theo **dòng giá trị ngay sau** (tên GVHD, tên sinh viên, lớp). Trang phụ bìa lặp bìa đúng 2 lần nên quy tắc dòng lặp không bắt được, mà tên GVHD thì trùng giữa các đồ án cùng GVHD;
- **dòng mục lục và tiêu đề:** dòng kết thúc bằng dãy dấu chấm và số trang; dòng kết thúc bằng **dải chấm cách** ". . . ." mà PDF sinh từ LaTeX tạo ra (có hoặc không kèm số trang, vì số trang hay rơi xuống dòng sau), kể cả dòng chỉ có dải chấm; "CHƯƠNG …"; tiêu đề đánh số; dòng viết hoa toàn bộ ngắn; chú thích hình và bảng;
- **header, footer của PDF:** dòng ngắn lặp lại từ 3 lần trở lên trong cùng văn bản, số trang.

Để danh sách này không thành chỗ giấu nội dung: tiêu đề mục mẫu chỉ có hiệu lực ở phần đầu hoặc phần cuối tài liệu; mỗi mục bỏ tối đa max(40 dòng, 15 %), tổng cộng tối đa max(80 dòng, 40 %). Phần tên đề tài sau nhãn "Đề tài:" bị PDF bẻ sang dòng sau vẫn được bỏ, nhưng không bao giờ nuốt một tiêu đề lớn hay tiêu đề mục (nếu nuốt, mục mẫu đang mở sẽ lan vào thân bài). Mỗi nhãn bìa chỉ kéo theo một dòng giá trị. Kết quả luôn ghi số dòng và tỷ lệ nội dung đã bị loại, và cảnh báo giảng viên khi hơn 50 % nội dung bị loại.

**Đợt sửa ngày 09/11/2026** (đo trên đồ án thật): trên các đồ án thật, số câu được giữ lại mà còn chứa dải chấm mục lục giảm từ 7.176 xuống 0, số mảnh bìa còn sót giảm từ 106 xuống 7. Biểu thức nhận dạng dải chấm cũ có thời gian chạy bậc hai theo độ dài dòng (một dòng 20.000 dấu chấm mất khoảng 9 giây) và đã được viết lại để chạy tuyến tính. Đổi lại, phần nội dung báo cho GVHD là "không được kiểm tra" (`ty_le_loai_tru`) tăng trung bình khoảng 7 điểm phần trăm, phần lớn chính là các dải chấm.

So với [1]: Sorokina chỉ tách danh mục tài liệu tham khảo bằng cách tìm dòng "References" hoặc "Bibliography" cuối cùng, làm được với khoảng 75 % số bài. Đồ án tiếng Việt có khuôn mẫu khoa rõ hơn nên hệ thống lọc được nhiều loại phần mẫu hơn. Danh sách hiện là **giả định**, cần cập nhật khi có mẫu chính thức của Khoa.

### 3.4. Chia câu

`ai-service/app/nlp/chunking.py`:

- Mọi dòng còn lại được nối thành **một dòng chảy** rồi mới tách câu. PDF bẻ dòng giữa câu, DOCX mỗi đoạn một dòng; nối lại thì cùng một nội dung cho cùng các câu bất kể định dạng.
  - Sorokina gặp đúng vấn đề này: họ coi "xuống dòng + chữ hoa" là hết câu, nên khi PDF bẻ dòng ngay trước một tên riêng thì câu bị cắt đôi ở chỗ khác nhau giữa hai file và trượt khớp [1].
- Ranh giới câu: dấu `.`, `!`, `?`, `…` theo sau là khoảng trắng và chữ hoa, chữ số hoặc dấu mở ngoặc. Bỏ qua viết tắt thường gặp (TS., ThS., PGS., GS., TP., NXB., …).
- Mỗi câu dài 6–120 âm tiết và tối đa 2.000 ký tự. Câu quá dài được cắt ở dấu `;`, rồi dấu `,`, rồi theo từ. Câu dưới 6 âm tiết bị bỏ: quá ngắn để làm bằng chứng.
- Các câu không chồng lấn nhau, nên tỷ lệ tính theo ký tự là chính xác.

### 3.5. Tín hiệu nguyên văn: vân tay văn bản (winnowing)

`ai-service/app/fingerprint.py`, `ai-service/app/index.py`:

1. **Cụm âm tiết.** Mỗi câu được casefold, tách thành âm tiết (token chữ và số), rồi tạo các cụm k = 6 âm tiết liên tiếp. Mỗi cụm băm thành số 64 bit (blake2b cho từng âm tiết, sau đó băm đa thức cho cả cụm). Sorokina cũng dùng băm 64 bit kiểu Rabin cho cụm từ và thấy đủ để không đụng độ [1].
2. **Winnowing.** Trong mỗi cửa sổ w = 4 cụm liên tiếp, chỉ giữ giá trị băm nhỏ nhất. Kho chỉ lưu các vân tay này trong một **chỉ mục ngược** (vân tay → các câu chứa nó). Theo [2], hai câu chung một đoạn dài ít nhất t = w + k − 1 = 9 âm tiết thì luôn chung ít nhất một vân tay. Vì vậy chỉ cần tra bảng, không phải so với từng câu của kho.
   - Như Sorokina [1], cửa sổ không vượt qua ranh giới câu.
3. **Điểm = độ phủ theo từng nguồn.** Với mỗi câu nộp, hệ thống lấy tối đa 20 câu kho chung nhiều vân tay nhất (bỏ cụm phổ biến) và gom chúng theo **đồ án nguồn** (`VanTaySnapshot.match` trong `index.py`). Với từng câu ứng viên, hệ thống đánh dấu các âm tiết của câu nộp nằm trong đoạn chung liên tiếp dài ít nhất t = min(9, số âm tiết của câu) với **riêng câu đó** (`covered_mask` trong `fingerprint.py`). Độ phủ của một nguồn là tỷ lệ âm tiết thuộc **hợp** các mặt nạ đó trên mọi câu ứng viên của nguồn. Điểm nguyên văn của câu là độ phủ của nguồn cao nhất; câu nguồn hiển thị là câu ứng viên có độ phủ riêng cao nhất của nguồn đó.
   - Chép nguyên câu được 100 %. Sửa một từ giữa câu 30 âm tiết vẫn còn khoảng 97 % (MinHash trước đây rơi xuống khoảng 74 %). Chép nửa câu được khoảng 50 %.
   - **Ghép hai câu của cùng một nguồn thành một câu** ("A, đồng thời b") được khoảng 100 %. Trước ngày 09/11/2026, độ phủ chỉ tính với **một** câu của kho, nên câu ghép chỉ được khoảng 50 % với mỗi câu nguồn, dưới ngưỡng 56 %: đây là lỗ hổng đo được bằng kiểu biến đổi `gop_cau` của bộ đánh giá kiểu PAN (mục 4.1).
   - Các mẩu ngắn hơn t chung với **những câu khác nhau** không cộng lại thành một đoạn, kể cả khi đứng liền nhau trong câu nộp: mỗi đoạn chung vẫn phải dài từ t âm tiết với một câu nguồn duy nhất. Hợp chỉ lấy giữa các câu của cùng một nguồn, không lấy giữa nhiều nguồn.
   - Câu bị gắn cờ nguyên văn khi độ phủ từ **56 %** trở lên.
   - Khác [1]: Sorokina đếm số câu trùng và cần từ m = 4 câu; hệ thống chấm điểm từng câu, rồi tính tỷ lệ theo ký tự ở bước 3.7.
4. **Cụm phổ biến (L-common, L = 4).** Cụm 6 âm tiết có trong từ 4 **đề tài** khác nhau trở lên được coi là câu khuôn (ví dụ "trong chương này em trình bày tổng quan về …") và không tính là bằng chứng.
   - Đếm theo đề tài, không theo tài liệu: nhiều phiên bản đề cương của cùng một đề tài chỉ tính một lần. Đây là cách hiểu cho đồ án sinh viên của "các bài không chung tác giả" trong [1].
   - Nhóm của chính đề tài đang được kiểm tra không được đếm.
   - Khác [1]: Sorokina bỏ **cả câu** chứa cụm phổ biến; hệ thống chỉ bỏ **cụm** đó, phần còn lại của câu vẫn được so. Như vậy người chép không thể "giấu" một câu chép chỉ bằng cách chèn vào một cụm khuôn mẫu.
   - Sorokina chọn L = 4 vì khi gồm cả cụm có trong 4 bài, kết quả bắt đầu chứa các cặp chỉ trùng nhau ở đoạn khuôn mẫu như lời cảm ơn tài trợ. Cụm phổ biến nhất của họ có mặt trong 12.966 bài [1].
5. **Tham số.** k = 6 âm tiết được chọn trong các giá trị 3–6 theo AUC trên tập hiệu chỉnh: 0,9859 / 0,9962 / 0,9969 / 0,9974. Sorokina dùng k = 7 **từ** tiếng Anh [1]. Một âm tiết tiếng Việt ngắn hơn một từ tiếng Anh, nên t = 9 âm tiết (khoảng nửa câu ngắn) là mức "đoạn đủ dài để không phải trùng ngẫu nhiên".

### 3.6. Tín hiệu ngữ nghĩa: embedding câu

`ai-service/app/embedding.py`, `ai-service/app/index.py`, `ai-service/app/pipeline.py`:

- Câu được tách từ bằng underthesea (ví dụ `cơ_sở dữ_liệu`), rồi mã hóa bằng `bkai-foundation-models/vietnamese-bi-encoder` (PhoBERT) thành vector đã chuẩn hóa.
- FAISS `IndexFlatIP` tìm **chính xác** câu gần nghĩa nhất trong kho (cosine), bỏ qua nguồn bị loại trừ.
- Câu bị gắn cờ ngữ nghĩa khi cosine từ **67,7 %** trở lên. Cờ ngữ nghĩa chỉ được giữ khi câu nằm trong chuỗi **ít nhất 2 câu liên tiếp** trùng cùng một nguồn. Một câu đơn lẻ "gần nghĩa" thường chỉ là cùng lĩnh vực.
- Khi một câu có cả hai tín hiệu, tín hiệu nguyên văn được ưu tiên vì là bằng chứng mạnh hơn.

Đây là phần [3][4] chỉ ra còn thiếu ở các hệ thống so chuỗi: bắt câu diễn đạt lại. Mô hình được chọn theo một quy tắc viết ra trước khi đo (xem [`chuong-4-trien-khai/thu-nghiem-ai/02-so-sanh-mo-hinh-embedding.md`](chuong-4-trien-khai/thu-nghiem-ai/02-so-sanh-mo-hinh-embedding.md)).

### 3.7. Tổng hợp kết quả

- **Tỷ lệ trùng tổng:** số ký tự của các câu bị gắn cờ chia cho số ký tự đã so sánh.
- **Tỷ lệ theo từng đồ án nguồn:** chỉ đếm câu gắn cờ của nguồn đó. Danh sách nguồn xếp giảm dần.
- **Đoạn trùng:** các câu gắn cờ liên tiếp cùng một nguồn được ghép thành đoạn, tối đa 6 câu, kèm vị trí, đoạn nguồn, điểm từng tín hiệu và một trong ba nhãn (`tin_hieu`, `ai-service/app/pipeline.py`):
  - ít hơn nửa số ký tự của đoạn bị gắn cờ nguyên văn → **"Trùng ngữ nghĩa"** (`NGU_NGHIA`);
  - từ nửa số ký tự trở lên bị gắn cờ nguyên văn: so trực tiếp chữ của đoạn với đoạn nguồn. **Tỷ lệ khớp chữ** (`_ty_le_khop_chu`) là số âm tiết của đoạn nằm trong các khối trùng liên tục với nguồn, chia cho độ dài lớn hơn giữa đoạn và phần nguồn được căn khớp (nên cả thay từ lẫn bỏ từ đều làm giảm tỷ lệ). Tỷ lệ **< 0,99** (`NGUONG_SUA_NHE`) → **"Trùng sửa nhẹ"** (`SUA_NHE`); ngược lại → **"Trùng nguyên văn"** (`NGUYEN_VAN`).
  - Nhãn chỉ để hiển thị: cờ của từng câu, tỷ lệ tổng và tỷ lệ theo nguồn không đổi. Web API ghi nhãn vào `vi_tri` ("Câu a–b · trùng sửa nhẹ"), giao diện hiện thẻ màu riêng và đếm riêng số đoạn sửa nhẹ. Kết quả lưu trước khi có nhãn này vẫn hiện đúng hai nhãn cũ.
  - **Chọn 0,99 (24/11/2026):** bản chép y hệt cho đúng 1. Trên bộ đánh giá kiểu PAN v2 (mục 4.1), tính trên đoạn chèn và đoạn nguồn của từng ca: 20/20 ca chép nguyên văn đạt 1,00, 20/20 ca sửa nhẹ nằm trong 0,875–0,976. 400 đoạn sửa nhẹ mô phỏng (`evaluation/obfuscate.sua_nhe`) trên dữ liệu mẫu có trung vị 0,958, lớn nhất 0,99. Thay một từ trong câu khoảng 30 âm tiết cho khoảng 0,97, tức "sửa nhẹ". Bản 09/11 dùng `diem_nguyen_van` < 96,3 (Youden J trên bộ v1), nhưng kiểm thử đầu-cuối ngày 24/11 cho thấy độ phủ vân tay hụt tới w − 1 = 3 âm tiết ở mỗi mép câu, nên đoạn chép y hệt gồm các câu ngắn chỉ đạt 72–96 và bị gắn nhầm "sửa nhẹ". Độ phủ phụ thuộc độ dài câu nên không dùng làm thước đo mức sửa; nó vẫn là tín hiệu gắn cờ (3.5).

### 3.8. Quyết định cảnh báo

Do Web API thực hiện (`backend/app/services/document_check.py`). Tài liệu bị đánh dấu **Vượt ngưỡng cảnh báo** khi:

- tỷ lệ trùng với **một** đồ án nguồn cao nhất ≥ `NGUONG_TAI_LIEU` (lý do `MOT_NGUON`): chép phần lớn từ một đồ án; **hoặc**
- tỷ lệ trùng tổng mọi nguồn ≥ `NGUONG_TONG_TAI_LIEU` (lý do `TONG_NGUON`): bài ghép từ nhiều đồ án, mỗi đồ án một ít.

Hiệu chỉnh đề xuất **10,4 %** và **14,8 %** (mục 4); đây cũng là giá trị mặc định khi cài mới. Ngưỡng tổng được đặt cao hơn vì câu tự viết cùng lĩnh vực có thể khớp rải rác với nhiều đồ án. Trên kịch bản ghép 4 nguồn, mỗi nguồn khoảng 6 %, quy tắc chỉ xét một đồ án chỉ cảnh báo được 2/11 bài; thêm ngưỡng tổng thì cảnh báo được cả 11/11.

**Giá trị đang áp dụng trên máy chủ:** từ 29/10/2026, Bộ môn đặt cả hai ngưỡng là **25 %** (màn hình cấu hình ngưỡng, UC0.4). Mỗi câu bị gắn cờ chỉ thuộc một đồ án nguồn, nên tỷ lệ theo một đồ án không bao giờ vượt tỷ lệ tổng; với hai ngưỡng bằng nhau, quy tắc thực chất là **tổng trùng ≥ 25 % thì cảnh báo**. Ngưỡng này cao hơn giá trị hiệu chỉnh nên hệ thống cảnh báo ít hơn. Tính lại trên số liệu ở `03-hieu-chinh-nguong.md` với quy tắc tổng ≥ 25 %:

- mọi cặp chép nguyên văn (tỷ lệ tổng ≥ 44 %) vẫn bị cảnh báo;
- tập hiệu chỉnh đúng 16/17 cặp: bỏ sót P08 (diễn đạt lại, tổng 21,23 %);
- tập kiểm chứng đúng 6/8 cặp: bỏ sót P09 và P10 (diễn đạt lại, tổng khoảng 20,9 %); ngược lại, ca P19 (cùng lĩnh vực, tổng 23,96 %) không còn bị cảnh báo nhầm;
- kịch bản ghép 4 nguồn (phần chèn khoảng 20–22 %) cảnh báo 6/11 bài, thay vì 11/11.

Mỗi kết quả kiểm tra lưu lại ngưỡng lúc kiểm tra, nên kết quả cũ không đổi.

Các quy tắc đi kèm:

- **Không tự khớp với mình:** các phiên bản trước của cùng đề tài luôn bị loại trừ (`loai_tru`).
- **Kiểm tra trước, đưa vào kho sau:** tài liệu chỉ được đưa vào chỉ mục sau khi kiểm tra xong, để các lần nộp sau của sinh viên khác so được với nó.
- **Ngưỡng chụp tại thời điểm kiểm tra:** Bộ môn đổi ngưỡng thì chỉ áp dụng cho lần kiểm tra sau; kết quả cũ giữ ngưỡng lúc kiểm tra.
- **Người kết luận:** màn chi tiết đặt từng đoạn nộp cạnh đoạn nguồn và tô cụm trùng, giống cách HyPlag hỗ trợ người xem [4]. Giảng viên là người quyết định.

### 3.9. Kiểm tra tên đề tài

Khi giảng viên tạo hoặc giao đề tài, tên đề tài được mã hóa bằng cùng mô hình embedding và so với tên các đề tài hiện hành và đồ án trong kho. Kết quả có độ tương đồng từ **67,8 %** trở lên được liệt kê để cảnh báo trùng đề tài.

### 3.10. Kiểm tra đạo văn một tệp tải lên (thêm 23/11/2026)

Theo yêu cầu của giảng viên hướng dẫn, phương pháp ở mục 3.1–3.8 được mở thành một chức năng độc lập: giảng viên hoặc Bộ môn tải một tệp PDF/DOCX bất kỳ lên màn hình "Kiểm tra đạo văn" (`/kiem-tra-dao-van`, `backend/app/routers/upload_checks.py`) để so với kho đồ án và các tài liệu đã nộp trong hệ thống. Sinh viên không dùng được chức năng này.

- **Cùng một đường xử lý:** tệp được kiểm tra định dạng và trích xuất như khi nộp (mục 3.1), rồi chạy cùng `document_check.run` với văn bản nằm trong bộ nhớ. Kết quả dùng cùng ngưỡng, cùng nhãn và cùng màn chi tiết với tài liệu đã nộp. Tệp không có chữ (PDF ảnh quét) hoặc dài hơn `AI_DOCUMENT_MAX_CHARS` bị từ chối ngay (422).
- **`ref_id` 0, không loại trừ:** tệp không phải một nguồn trong kho nên Web API gửi `ref_id` 0 và không có `loai_tru`. Hệ quả: nếu tệp chính là một tài liệu đã nộp, kết quả trùng gần 100 % với tài liệu đó.
- **Không lưu, không đưa vào chỉ mục:** tệp không được ghi ra đĩa và không được gửi sang `/ingest`, nên không làm thay đổi kết quả kiểm tra bài của sinh viên sau này. Chỉ kết quả (tỷ lệ, đoạn trùng, tên tệp) được lưu vào `ket_qua_kiem_tra_trung_lap` / `chi_tiet_trung_lap`, gắn với người tải lên qua cột `tai_khoan_id` (Alembic 0020).
- **Chỉ người tải lên xem được:** người khác mở kết quả nhận 404.
- **Giới hạn tải:** mỗi người tối đa 2 lần kiểm tra đang chạy; lần thứ ba nhận 429, để một người không làm dịch vụ AI quá tải (kiểm tra một đồ án dài có thể mất vài phút).

---

## 4. Hiệu chỉnh và kết quả

Chi tiết ở [`chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md`](chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md). Tóm tắt:

| Mục                             | Kết quả                                                                                                                                                           |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dữ liệu                        | 25 cặp tài liệu tổng hợp (chép nguyên văn, diễn đạt lại, cùng lĩnh vực, không liên quan), chia tập hiệu chỉnh và tập kiểm chứng giữ riêng |
| Ngưỡng nguyên văn            | 56,0 % (Youden J; TPR 0,978, FPR 0,019)                                                                                                                             |
| Ngưỡng tổng                   | 14,8 % (trung điểm giữa âm lớn nhất 8,41 % và dương nhỏ nhất 21,23 %); máy chủ đang dùng 25 % (mục 3.8)                                                 |
| Độ chính xác mức tài liệu | Tập hiệu chỉnh 17/17, tập kiểm chứng 7/8. Ca sai là một bài cùng lĩnh vực trùng ngữ nghĩa nhiều với một đồ án cùng chủ đề                  |
| Bài ghép nhiều nguồn         | Cả 284 câu chèn đều bị gắn cờ; 11/11 bài bị cảnh báo                                                                                                    |
| Tốc độ so nguyên văn        | Kho 150.000 câu, báo cáo 1.500 câu: 0,09 giây (MinHash quét toàn kho: 34,5 giây)                                                                            |

Giống Sorokina [1], các tham số được chọn bằng thực nghiệm trên một tập nhỏ có nhãn. Tập này là dữ liệu tổng hợp, nên cần hiệu chỉnh lại khi có đồ án thật được gán nhãn.

### 4.1. Đánh giá kiểu PAN trên đồ án thật

Chi tiết, bảng đầy đủ và lệnh chạy lại ở [`chuong-4-trien-khai/thu-nghiem-ai/05-danh-gia-kieu-pan.md`](chuong-4-trien-khai/thu-nghiem-ai/05-danh-gia-kieu-pan.md); mã ở `ai-service/evaluation/`.

**Cách dựng.** Theo khung PAN-PC [8]: lấy văn bản thật, chèn đoạn chép đã biến đổi vào, ghi vị trí ký tự của từng ca rồi đo phát hiện của hệ thống theo ký tự.

- **Dữ liệu:** đồ án thật khóa K19–K21 lấy từ Drive của Bộ môn (106 tệp PDF). Bộ v1 dùng 105 đồ án (loại 1 tệp quá ít nội dung thân bài); bộ v2, trích xuất bằng hàm mới, dùng 104 đồ án (loại 2 tệp). Bộ dữ liệu nằm ngoài kho git vì là văn bản thật của sinh viên; tài liệu này chỉ ghi số liệu tổng hợp.
- **Chia:** 75 đồ án (bộ v2: 74) làm kho nguồn; 30 đồ án làm tài liệu nghi vấn, trong đó 20 bị chèn đạo văn và 10 để sạch.
- **Ca đạo văn:** mỗi tài liệu bị chèn nhận 7 đoạn (3–8 câu thân bài liền nhau, 60–250 âm tiết) lấy từ 7 nguồn khác nhau, mỗi đoạn một kiểu biến đổi, chèn rải đều trong thân bài. Tổng cộng 140 ca, 20 ca mỗi kiểu.
- **Kiểu biến đổi**, đặt tên theo bảng phân loại ReParaphrased [6] và PAN [8]:

| Kiểu | Biến đổi | Tương ứng |
|---|---|---|
| `nguyen_van` | Chép nguyên văn | Verbatim [6] |
| `sua_nhe` | Thay khoảng 15–25 % cụm có trong từ điển đồng nghĩa, bỏ vài hư từ, bỏ hoặc đổi một hai dấu phẩy, chấm phẩy | Same Polarity Substitution, Functional Word Substitution, Punctuation Changes [6] |
| `dao_cau` | Đảo thứ tự các câu | Change of Order [6] |
| `gop_cau` | Gộp từng cặp câu liên tiếp bằng từ nối ("…, đồng thời …") | Coordination Changes [6] |
| `tach_cau` | Tách câu dài hơn 25 âm tiết tại dấu phẩy gần giữa câu | Chiều ngược của Coordination Changes [6] |
| `xao_tron` | Xáo từ trong khoảng 30 % cửa sổ 3–4 từ, xóa khoảng 5 % và chèn khoảng 5 % từ | Random obfuscation của PAN [8] |
| `llm` | Một mô hình ngôn ngữ lớn (Claude) đóng vai ChatGPT nhận yêu cầu của sinh viên: "Viết lại đoạn văn sau bằng cách diễn đạt khác, giữ nguyên ý, văn phong đồ án tốt nghiệp"; ràng buộc: giữ dữ kiện, tên riêng, thuật ngữ; đổi từ ngữ và cấu trúc câu; tránh chuỗi từ 8 âm tiết trở lên trùng bản gốc (trừ tên riêng, tên gọi); độ dài trong khoảng ±25 % | Diễn đạt lại bằng mô hình ngôn ngữ lớn, nguy cơ mà [5][6] nêu |

- **Chỉ số:** precision, recall vĩ mô, granularity và plagdet của PAN-PC [8]; recall theo từng kiểu; cảnh báo mức tài liệu với cặp ngưỡng hiệu chỉnh 10,4 % / 14,8 % và cặp ngưỡng máy chủ 25 % / 25 %. Một phát hiện là chuỗi tối đa các câu liên tiếp gắn cờ cùng một nguồn.

**Kết quả bộ v1** (trích xuất PDF cũ, bộ lọc mẫu chung cũ; mọi câu được định vị chính xác trong văn bản gốc), trước và sau khi tính độ phủ theo từng nguồn (mục 3.5):

| Chỉ số | Trước | Sau |
|---|---:|---:|
| Precision | 0,2298 | 0,2294 |
| Recall | 0,8503 | 0,8544 |
| Granularity | 1,0 | 1,0 |
| Plagdet | 0,3619 | 0,3617 |
| Recall `gop_cau` | 0,895 | 0,928 |
| Phần recall `gop_cau` do tín hiệu nguyên văn | 0,590 | 0,928 |

- Recall theo kiểu (sau): `dao_cau` 1,0; `sua_nhe` 1,0; `nguyen_van` 0,95; `tach_cau` 0,95; `gop_cau` 0,928; `xao_tron` 0,590; `llm` 0,563 (phát hiện được 14/20 ca, tất cả nhờ tín hiệu ngữ nghĩa).
- Hai ca "bỏ sót" của `nguyen_van` và `tach_cau` cùng lấy từ một đồ án nguồn chứa **cùng một đoạn hai lần**. Hệ thống khớp với lần xuất hiện thứ nhất, còn ca được ghi ở lần thứ hai, và cách chấm PAN không tính phát hiện đó. Đây là đặc điểm của dữ liệu, không phải bỏ sót.
- **Mức tài liệu:** 10 tài liệu sạch có tỷ lệ tổng 1,3–7,3 % (không đổi sau sửa); 20 tài liệu bị chèn có 3,3–17,1 %. Với 10,4 % / 14,8 %: 2/20 tài liệu bị chèn bị cảnh báo, 0/10 tài liệu sạch bị cảnh báo nhầm. Với 25 % / 25 %: 0/20. Phần chèn chỉ là 7 đoạn trong cả một đồ án (khoảng 5–10 % nội dung), nên ngưỡng theo tỷ lệ đo **chép bao nhiêu**, không đo **có chép hay không**; danh sách đoạn trùng vẫn hiện mọi phát hiện để giảng viên xem.
- **Precision thấp (0,23)** vì nền là đồ án thật: 410 phát hiện không trùng ca nào được chèn. Chúng gồm nội dung thật sự giống nhau giữa các đồ án cùng chủ đề, các đoạn kiến thức giáo khoa chung gần nhau về nghĩa, và phần mẫu chung lọt bộ lọc (đã sửa ở mục 3.3). Con số này là **cận trên của nhiễu**, không phải số cảnh báo sai đã kiểm chứng.

**Kết quả bộ v2** (cùng tệp PDF, cùng hạt giống; trích xuất PDF mới, bộ lọc mẫu chung mới, đủ các sửa đổi ngày 09/11/2026; 104 đồ án: 74 nguồn, 20 bị chèn, 10 sạch; đoạn chèn chọn lại, đoạn `llm` viết lại mới; vẫn 140 ca):

| Chỉ số | Bộ v1 (sau) | Bộ v2 |
|---|---:|---:|
| Precision | 0,2294 | 0,2912 |
| Recall | 0,8544 | 0,8907 |
| Granularity | 1,0 | 1,037 |
| Plagdet | 0,3617 | 0,4275 |
| Phát hiện / không trùng ca nào | 536 / 410 | 464 / 325 |
| Ca phát hiện được | 126/140 | 134/140 |

- Recall theo kiểu (v2): `dao_cau` 0,995; `sua_nhe` 0,993; `nguyen_van` 0,982; `tach_cau` 0,959; `gop_cau` 0,924; `llm` **0,793** (18/20 ca, tất cả nhờ tín hiệu ngữ nghĩa); `xao_tron` 0,589 (16/20 ca).
- **Không phải so sánh có đối chứng.** Ngoài bản sửa trích xuất và bộ lọc mẫu chung, đoạn chèn đã được chọn lại, kho nguồn ít hơn một đồ án, và đoạn `llm` mới bám độ dài bản gốc hơn (0,91–1,08 lần, so với 1,03–1,23 lần ở v1). Bản sửa trích xuất là giải thích hợp lý nhất cho mức tăng của `llm` và tín hiệu ngữ nghĩa (âm tiết bị dính làm hỏng đầu vào của mô hình embedding), nhưng chưa được đo tách riêng.
- **Mức tài liệu:** 10 tài liệu sạch có tỷ lệ tổng 0,03–6,50 %, tỷ lệ với nguồn cao nhất ≤ 1,45 %, không bị cảnh báo nhầm ở cả hai cặp ngưỡng. 19 tài liệu bị chèn có 3,6–16,75 %. Với 10,4 % / 14,8 %: 3/20 bị cảnh báo (hai do ngưỡng tổng, 15,43 % và 16,75 %, cộng tài liệu ngoại lai dưới đây); với 25 % / 25 %: 1/20, chỉ tài liệu ngoại lai.
- **Một tài liệu ngoại lai** có tỷ lệ tổng 51,04 % (26,77 % với một nguồn), phần lớn không thuộc đoạn được chèn: đó là một đồ án thật khóa K21 có nhiều đoạn trùng nguyên văn dài (tới khoảng 2.000 ký tự mỗi đoạn) với hai đồ án thật khóa K21 khác trong kho, cả ba cùng nhóm đề tài. Hệ thống đã làm lộ ra việc dùng lại văn bản thật giữa các đồ án; đó là khuôn mẫu chung của nhóm hay sao chép thì cần người xem lại.
- **Nhiễu:** 325 phát hiện không trùng ca nào; trong 10 phát hiện dài nhất, 8 là trùng nguyên văn và 9 thuộc tài liệu ngoại lai. Một phần "nhiễu" vì vậy là phát hiện đúng, nên precision 0,29 vẫn là **cận dưới**.
- **Biên nhãn sửa nhẹ trên v2:** Youden mức đoạn cho 93,7 (AUC 0,915, J 0,824; 22 đoạn nguyên văn, 23 đoạn sửa nhẹ), khác 96,3 của v1. Đoạn nguyên văn: p5 93,94, p10 94,55, trung vị 100; đoạn sửa nhẹ: p10 77,8, trung vị 86,12, p90 97,73. Ở 96,3, khoảng 10–15 % đoạn chép nguyên văn hiện nhãn "sửa nhẹ" (chủ yếu do câu ở mép đoạn bị gộp với chữ của tài liệu nền khi chia câu) và khoảng 10 % đoạn sửa nhẹ hiện nhãn "nguyên văn". Phân tích này dựa trên `diem_nguyen_van`; từ 24/11/2026 nhãn dùng tỷ lệ khớp chữ, tách hoàn toàn hai kiểu ở mức ca (3.7).

---

## 5. Những điểm khác tài liệu tham khảo và lý do

| Vấn đề             | Sorokina [1] / HyPlag [4]                                                      | Hệ thống                                                    | Lý do                                                             |
| --------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------- | ------------------------------------------------------------------ |
| Đơn vị cụm        | 7 từ tiếng Anh [1]; 3 từ để lọc ứng viên, 12 từ để so chi tiết [4] | 6 âm tiết, đoạn bảo đảm 9 âm tiết                    | Âm tiết tiếng Việt ngắn hơn từ tiếng Anh; k chọn theo AUC |
| Điểm của một câu | Có hoặc không trùng; đếm số câu trùng                                 | Độ phủ 0–100 %                                            | Bắt cả chép nửa câu và chép rồi sửa vài từ              |
| Độ phủ tính với | Một câu nguồn [1] | Hợp các đoạn chung ≥ 9 âm tiết với các câu của **một** đồ án nguồn | Câu nộp ghép từ hai câu của cùng nguồn vẫn được khoảng 100 %, không còn rơi xuống khoảng 50 % |
| Cụm phổ biến       | Bỏ cả câu chứa cụm phổ biến                                             | Chỉ bỏ cụm phổ biến                                      | Không để cụm khuôn che câu chép                             |
| "Khác tác giả"     | Tách tên tác giả từ metadata, xử lý chuyển tự tên                    | Nhóm = đề tài (`de_tai_id`)                             | Mỗi đồ án có một đề tài rõ ràng trong CSDL              |
| Diễn đạt lại      | Không xử lý [1]; có hướng xử lý bằng công thức, trích dẫn [4]     | Embedding câu tiếng Việt                                   | Diễn đạt lại là dạng phổ biến ở bài sinh viên           |
| Đơn vị kết luận  | Cặp tài liệu                                                                | Từng câu, gộp thành tỷ lệ theo nguồn và tỷ lệ tổng | Giảng viên cần thấy đúng đoạn nào trùng                  |

---

## 6. Giới hạn và hướng phát triển

- **Công thức, hình ảnh, trích dẫn chưa được phân tích.** [3][4] cho thấy các đặc trưng này bắt được chép ý và chép đã che giấu; [5] cho thấy cả các phương pháp tốt nhất vẫn bỏ sót phần lớn chép công thức. Đồ án CNTT ít công thức nên ưu tiên trước là **so ảnh** (sơ đồ, hình chụp màn hình) và **so danh mục tài liệu tham khảo**.
- **Đoạn có trích dẫn nguồn vẫn bị tính trùng.** Chưa có nhãn "trích dẫn có ghi nguồn" như bộ lọc của Turnitin.
- **Đầu vào:** chưa có OCR cho PDF ảnh quét; LaTeX chưa được biên dịch tự động (22 đồ án kho đang chờ quy trình ở mục 3.2).
- **Dữ liệu hiệu chỉnh là tổng hợp.** Các ngưỡng vẫn khớp trên bộ dữ liệu tổng hợp. Bộ đánh giá kiểu PAN (mục 4.1) đã thử trên văn bản đồ án thật, kể cả ca chép rồi sửa nhẹ mà bộ tổng hợp không có: cả 20 ca sửa nhẹ đều được phát hiện, phần lớn nhờ tín hiệu nguyên văn (recall 0,94), nên k = 6 không làm mất ca sửa nhẹ ở mức đoạn, dù sửa một từ gần đầu hoặc cuối câu vẫn làm mất tới 8 âm tiết khỏi độ phủ của câu đó. Ngưỡng tổng mới được kiểm tra trên bài ghép dựng thêm; trên đồ án thật, 7 đoạn chép trong cả một đồ án chưa đủ để vượt ngưỡng (mục 4.1).
- **Chép rồi biến đổi mạnh** (dịch, viết lại bằng mô hình ngôn ngữ lớn, xáo trộn từ) có thể lọt cả hai tín hiệu; [5][6] cũng nêu nguy cơ này. Bộ đánh giá kiểu PAN đo được: đoạn do mô hình ngôn ngữ lớn viết lại có recall 0,563 (6/20 ca không được phát hiện) ở bộ v1 và 0,793 (2/20) ở bộ v2, chỉ nhờ tín hiệu ngữ nghĩa; đoạn xáo trộn kiểu PAN có recall khoảng 0,59 ở cả hai bộ (4–6/20 ca bỏ sót). Hai bộ không phải so sánh có đối chứng (mục 4.1). Embedding được dùng nguyên, chưa huấn luyện thêm cho bài toán này; [7] cho thấy huấn luyện có giám sát trên cặp câu gán nhãn cải thiện rõ ở một ngôn ngữ ít tài nguyên (mục 7).
- **Ngưỡng nhãn "Trùng sửa nhẹ" (tỷ lệ khớp chữ 0,99)** mới kiểm chứng ở mức ca trên 40 ca của bộ v2 và trên dữ liệu mô phỏng; chưa chạy lại toàn bộ bộ đánh giá với nhãn mới (đoạn hiển thị có thể lệch biên ca một câu).

---

## 7. Đối chiếu với thuật toán đề xuất của giảng viên hướng dẫn

Bản đề xuất (*Thuật toán đề xuất.docx*) mô tả một pipeline lai hai giai đoạn theo khung PAN: tìm nguồn ứng viên (source retrieval) rồi căn chỉnh chi tiết (text alignment), kết hợp vân tay và embedding. Danh mục nguồn trong bản đề xuất tự ghi là chưa được tra lại, nên mục này chỉ dùng bản đề xuất làm **danh sách yêu cầu**; mọi trích dẫn ở đây là tài liệu đã kiểm tra [1]–[8].

| Bước trong đề xuất | Hệ thống | Trạng thái | Lý do |
|---|---|---|---|
| **GĐ 0.** PDF → văn bản, giữ ánh xạ (trang, offset) để tô sáng | PyMuPDF, dựng lại dấu cách (3.1). Vị trí ghi theo số thứ tự câu ("Câu a–b"); màn chi tiết tô cụm trùng ngay trên câu | Đã làm, thay đổi | Tô trên câu đủ cho người xem; ánh xạ trang chỉ cần khi xuất báo cáo PDF (đang hoãn) |
| OCR trang quét (Tesseract, VietOCR) | PDF chỉ có ảnh bị đánh dấu lỗi trích xuất, việc nộp vẫn thành công | **Hoãn** | Bài nộp là DOCX hoặc PDF xuất từ phần mềm soạn thảo; OCR thêm một mô hình lớn, và lỗi nhận dạng làm sai vân tay |
| Làm sạch: header/footer lặp, nối dòng bị ngắt, NFC, chữ thường | Dòng lặp ≥ 3 lần, dòng chảy câu, NFC kèm `ƣ` → `ư`, casefold (3.1, 3.3, 3.4) | Đã làm | |
| Loại mục tài liệu tham khảo | Bỏ nguyên mục, kèm các mục mẫu khác (3.3) | Đã làm | |
| Loại đoạn trích dẫn trong ngoặc kép | Chưa có | **Hoãn** | Ngoặc kép trong đồ án dùng cả cho tên riêng, thuật ngữ; bỏ hết thì thành chỗ giấu nội dung (cùng lý do giới hạn mục mẫu ở 3.3). Cần quy tắc "có ghi nguồn" đi kèm |
| Tách câu, tách từ; n-gram theo **từ** | Tách câu (3.4); tách từ underthesea chỉ cho embedding; vân tay dùng k-gram **âm tiết** | Thay đổi | k-gram âm tiết không phụ thuộc lỗi của bộ tách từ; k = 6 âm tiết chọn theo AUC (0,9974) và cụm khuôn mẫu đã có bộ lọc cụm phổ biến |
| **GĐ 1.** k-gram, băm cuốn chiếu, winnowing, chỉ mục ngược hash → (tài liệu, vị trí) | Băm từng âm tiết rồi băm đa thức cho cụm, winnowing w = 4, chỉ mục ngược vân tay → câu (3.5) | Đã làm | Câu là đơn vị so và hiển thị nên chỉ mục lưu theo câu |
| Embedding câu hoặc cửa sổ 3 câu, bằng bge-m3 hoặc SBERT tiếng Việt (PhoBERT) | Embedding từng câu bằng `vietnamese-bi-encoder` (PhoBERT); cửa sổ 3 câu thay bằng luật "chuỗi ≥ 2 câu cùng nguồn" (3.6) | Đã làm; **bge-m3 hoãn** | bge-m3 chưa qua vòng so sánh mô hình; mô hình lớn hơn nhiều trong khi container AI có trần 2 GiB, và đổi mô hình phải hiệu chỉnh lại mọi ngưỡng |
| Chỉ mục vector FAISS HNSW hoặc IVF-PQ | FAISS `IndexFlatIP`, tìm chính xác | **Hoãn** (HNSW) | Kho của Khoa chỉ vài chục nghìn câu, tìm chính xác đủ nhanh (kiểm tra đề cương P95 khoảng 3 giây); chỉ mục xấp xỉ thêm sai số và tham số phải chỉnh |
| Bỏ vân tay có ở hơn x % tài liệu (bìa, lời cam đoan) | Bỏ cụm có ở ≥ 4 đề tài (L-common, 3.5), cộng bộ lọc mẫu chung theo quy tắc (3.3) | Đã làm | Theo [1]; đếm theo đề tài để nhiều phiên bản của một đề tài chỉ tính một lần |
| **GĐ 2a.** Tìm nguồn ứng viên theo độ chứa C(Q, D) mức tài liệu, giữ top-N | Tìm ứng viên **theo từng câu** (tối đa 20 câu kho chung nhiều vân tay nhất), gom theo nguồn để tính độ phủ (3.5) | Thay đổi | Bài ghép từ nhiều nguồn, mỗi nguồn một ít, có độ chứa thấp với từng nguồn nên dễ rơi khỏi top-N; tra bảng theo câu đã đủ nhanh (1.500 câu trên kho 150.000 câu: 0,09 giây) |
| Song song lấy top-k láng giềng vector cho từng đoạn | FAISS tìm câu gần nghĩa nhất cho từng câu | Đã làm | |
| **GĐ 2b.** Hạt giống (vân tay khớp, cặp câu cosine ≥ τ), gộp hạt giống thành đoạn (seed-extension, Smith–Waterman) | Hạt giống ở mức câu (cờ nguyên văn hoặc ngữ nghĩa); câu gắn cờ liên tiếp cùng nguồn gộp thành đoạn (3.7) | Thay đổi | Chuỗi câu liên tiếp cùng nguồn đã là đoạn; đoạn bị đảo câu vẫn được phát hiện đủ (recall `dao_cau` 1,0 ở bộ v1, 0,995 ở bộ v2, mục 4.1) nên chưa cần căn chỉnh cục bộ |
| Xác minh: độ dài ≥ L_min, độ tương đồng ≥ θ | Đoạn chung ≥ t = 9 âm tiết, độ phủ ≥ 56 %, cosine ≥ 67,7 % kèm luật chuỗi | Đã làm | |
| Gán nhãn nguyên văn / sửa nhẹ / paraphrase | Ba nhãn `NGUYEN_VAN` / `SUA_NHE` / `NGU_NGHIA` (3.7) | Đã làm (09/11/2026) | |
| **GĐ 2c.** Loại trích dẫn hợp lệ | Chưa có | **Hoãn** | Như dòng "ngoặc kép" ở trên |
| Loại tự đạo (cùng tác giả, cùng tài liệu) | Loại trừ các phiên bản trước của cùng đề tài (3.8) | Đã làm | |
| Hợp nhất vùng chồng lấn | Mỗi câu gắn cờ thuộc đúng một nguồn, các câu không chồng lấn | Đã làm | Tỷ lệ không bao giờ cộng trùng |
| **GĐ 3.** Tỷ lệ tổng theo token (hợp các vùng), tỷ lệ theo từng nguồn | Theo ký tự của câu bị gắn cờ; tỷ lệ theo từng nguồn (3.7) | Đã làm, đơn vị ký tự | Câu bị gắn cờ được tính trọn câu |
| Kết luận ba mức (< 10 % thấp, 10–25 % cần rà soát, > 25 % cao) | Một mức "Vượt ngưỡng cảnh báo" với hai ngưỡng (một nguồn, tổng), giảng viên kết luận (3.8) | **Hoãn** | Bản đề xuất cũng ghi các mức phải hiệu chỉnh trên dữ liệu có nhãn của trường, mà dữ liệu đó chưa có. Mục 4.1 cho thấy tỷ lệ đo lượng chép, không đo có chép hay không, nên chia mức theo tỷ lệ dễ làm bài chép ít bị xếp "thấp" |
| Đầu ra JSON và báo cáo PDF tô sáng | JSON lưu ở Web API; màn chi tiết đặt đoạn nộp cạnh đoạn nguồn, tô cụm trùng | **Hoãn** (xuất PDF) | Màn hình đã đủ để giảng viên đối chiếu; báo cáo PDF cần ánh xạ trang và một bộ dựng PDF |
| Winnowing O(n), thời gian truy vấn không tăng tuyến tính theo kho | Tra bảng vân tay, không quét toàn kho (3.5) | Đã làm | |
| Đánh giá bằng precision, recall, granularity, plagdet trên bộ tự dựng (chép, thay từ, đảo câu, viết lại bằng LLM) | Bộ đánh giá kiểu PAN trên đồ án thật (105 ở bộ v1, 104 ở bộ v2), 7 kiểu biến đổi (4.1) | Đã làm | |
| (Ngoài đề xuất) Huấn luyện có giám sát bộ phân loại diễn đạt lại như [7] | Embedding dùng nguyên, so cosine | **Hoãn** | Cần vài nghìn cặp câu tiếng Việt gán nhãn (các kho tiếng Urdu trong [7] có 2.684–4.900 cặp) và GPU để huấn luyện; máy chủ của Khoa chạy mô hình trên CPU |

---

## Tài liệu tham khảo

[1] D. Sorokina, J. Gehrke, S. Warner, P. Ginsparg, "Plagiarism Detection in arXiv," in *Proc. 6th IEEE International Conference on Data Mining (ICDM'06)*, 2006, pp. 1070–1075, doi:10.1109/ICDM.2006.126.

[2] S. Schleimer, D. S. Wilkerson, A. Aiken, "Winnowing: Local Algorithms for Document Fingerprinting," in *Proc. ACM SIGMOD*, 2003, pp. 76–85, doi:10.1145/872757.872770.

[3] N. Meuschke, M. Schubotz, F. Hamborg, T. Skopal, B. Gipp, "Analyzing Mathematical Content to Detect Academic Plagiarism," in *Proc. ACM CIKM*, 2017, doi:10.1145/3132847.3133144.

[4] N. Meuschke, V. Stange, M. Schubotz, B. Gipp, "HyPlag: A Hybrid Approach to Academic Plagiarism Detection," in *Proc. ACM SIGIR*, 2018, doi:10.1145/3209978.3210177.

[5] A. Satpute et al., "Taxonomy of Mathematical Plagiarism," arXiv:2401.16969, 2024.

[6] C. Zhou, C. Qiu, L. Liang, D. E. Acuna, "Paraphrase Identification with Deep Learning: A Review of Datasets and Methods," arXiv:2212.06933v3, 2024.

[7] H. R. Iqbal, M. Sharjeel, J. Shafi, U. Mehmood, A. A. Raza, "Urdu Sentential Paraphrased Plagiarism Detection Using Large Language Models," *ACM Transactions on Asian and Low-Resource Language Information Processing*, vol. 24, no. 9, Article 96, Sep. 2025, doi:10.1145/3748320.

[8] M. Potthast, B. Stein, A. Barrón-Cedeño, P. Rosso, "An Evaluation Framework for Plagiarism Detection," in *Coling 2010: Posters*, Beijing, China, 2010, pp. 997–1005. https://aclanthology.org/C10-2115/
