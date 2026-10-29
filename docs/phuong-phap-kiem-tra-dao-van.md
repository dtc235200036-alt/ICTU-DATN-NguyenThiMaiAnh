# Phương pháp kiểm tra trùng lặp, đạo văn của hệ thống

> Đề tài: Hệ thống quản lý đồ án sinh viên, Khoa CNTT, Trường ĐH CNTT&TT (ICTU), Đại học Thái Nguyên
> Người thực hiện: Nguyễn Thị Mai Anh (DTC235200036)
> Cập nhật: 22/10/2026, theo mã nguồn sau khi chuyển tín hiệu nguyên văn sang vân tay văn bản (commit `4b151e0`).
> Tài liệu liên quan: cơ sở lý thuyết [`chuong-1-co-so-ly-thuyet/07-tim-kiem-vector-va-phat-hien-trung-lap.md`](chuong-1-co-so-ly-thuyet/07-tim-kiem-vector-va-phat-hien-trung-lap.md), khảo sát công cụ [`khao-sat-cong-cu-kiem-tra-trung-lap.md`](khao-sat-cong-cu-kiem-tra-trung-lap.md), số liệu hiệu chỉnh [`chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md`](chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md).

Tài liệu này mô tả hệ thống kiểm tra một đề cương hoặc báo cáo như thế nào, từ lúc nhận file tới lúc hiện "Vượt ngưỡng cảnh báo". Ở mỗi bước có ghi rõ phần nào học từ tài liệu tham khảo [1]–[5], phần nào khác và vì sao. Các số liệu đều lấy từ mã nguồn và lần hiệu chỉnh ngày 21/10/2026.

---

## 1. Tóm tắt

```
 File nộp (DOCX / PDF)          Đồ án kho chỉ có mã nguồn LaTeX
          │                                  │ biên dịch sang PDF (mục 3.2)
          ▼                                  ▼
 [1] Trích xuất văn bản (Web API): DOCX đọc XML, PDF đọc bằng PyMuPDF, chuẩn hóa NFC
          │
          ▼
 [2] Lọc phần mẫu chung: bìa, lời cam đoan, mục lục, tài liệu tham khảo, header/footer...
          │
          ▼
 [3] Chia câu: nối dòng thành một dòng chảy rồi tách câu (6–120 âm tiết)
          │
          ├──────────────────────────────┐
          ▼                              ▼
 [4a] Tín hiệu NGUYÊN VĂN         [4b] Tín hiệu NGỮ NGHĨA
      vân tay winnowing                embedding vietnamese-bi-encoder
      cụm 6 âm tiết, bỏ cụm phổ biến   tìm câu gần nghĩa nhất bằng FAISS
      điểm = độ phủ câu                điểm = cosine
          │                              │
          └──────────────┬───────────────┘
                         ▼
 [5] Gắn cờ từng câu (nguyên văn ≥ 56 % hoặc ngữ nghĩa ≥ 67,7 %), tính tỷ lệ trùng tổng
     và tỷ lệ theo từng đồ án nguồn, ghép câu liền nhau thành đoạn trùng
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

---

## 3. Quy trình chi tiết

### 3.1. Nhận file và trích xuất văn bản

Do Web API thực hiện (`backend/app/services/documents.py`), ngay lúc sinh viên nộp:

- **DOCX:** đọc `word/document.xml` theo luồng (không tải toàn bộ cây XML), lấy chữ của mọi đoạn trong thân văn bản, kể cả ô bảng; tab và ngắt dòng giữ nguyên. Header, footer và chú thích cuối trang không được đọc.
- **PDF:** lấy chữ từng trang bằng PyMuPDF (`page.get_text()`).
- Toàn bộ chuẩn hóa về Unicode NFC, để chữ có dấu gõ kiểu tổ hợp (NFD) và kiểu dựng sẵn so khớp được với nhau.
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
- **dòng bìa:** tên trường, khoa, "Đồ án tốt nghiệp", nhãn "Sinh viên thực hiện", "Giảng viên hướng dẫn", "Thái Nguyên, … năm …";
- **dòng mục lục và tiêu đề:** dòng kết thúc bằng dãy dấu chấm và số trang; "CHƯƠNG …"; tiêu đề đánh số; dòng viết hoa toàn bộ ngắn; chú thích hình và bảng;
- **header, footer của PDF:** dòng ngắn lặp lại từ 3 lần trở lên trong cùng văn bản, số trang.

Để danh sách này không thành chỗ giấu nội dung: tiêu đề mục mẫu chỉ có hiệu lực ở phần đầu hoặc phần cuối tài liệu; mỗi mục bỏ tối đa max(40 dòng, 15 %), tổng cộng tối đa max(80 dòng, 40 %). Kết quả luôn ghi số dòng và tỷ lệ nội dung đã bị loại, và cảnh báo giảng viên khi hơn 50 % nội dung bị loại.

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
3. **Điểm = độ phủ.** Với câu nguồn có chung vân tay, hệ thống tính phần âm tiết của câu nộp nằm trong các đoạn chung liên tiếp dài ít nhất min(9, số âm tiết của câu). Điểm nguyên văn là độ phủ cao nhất với **một** câu của kho.
   - Chép nguyên câu được 100 %. Sửa một từ giữa câu 30 âm tiết vẫn còn khoảng 97 % (MinHash trước đây rơi xuống khoảng 74 %). Chép nửa câu được khoảng 50 %.
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
- **Đoạn trùng:** các câu gắn cờ liên tiếp cùng một nguồn được ghép thành đoạn, tối đa 6 câu, kèm vị trí, đoạn nguồn, điểm từng tín hiệu và nhãn "Trùng nguyên văn" hoặc "Trùng ngữ nghĩa" theo tín hiệu chiếm phần lớn ký tự.

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

---

## 5. Những điểm khác tài liệu tham khảo và lý do

| Vấn đề             | Sorokina [1] / HyPlag [4]                                                      | Hệ thống                                                    | Lý do                                                             |
| --------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------- | ------------------------------------------------------------------ |
| Đơn vị cụm        | 7 từ tiếng Anh [1]; 3 từ để lọc ứng viên, 12 từ để so chi tiết [4] | 6 âm tiết, đoạn bảo đảm 9 âm tiết                    | Âm tiết tiếng Việt ngắn hơn từ tiếng Anh; k chọn theo AUC |
| Điểm của một câu | Có hoặc không trùng; đếm số câu trùng                                 | Độ phủ 0–100 %                                            | Bắt cả chép nửa câu và chép rồi sửa vài từ              |
| Cụm phổ biến       | Bỏ cả câu chứa cụm phổ biến                                             | Chỉ bỏ cụm phổ biến                                      | Không để cụm khuôn che câu chép                             |
| "Khác tác giả"     | Tách tên tác giả từ metadata, xử lý chuyển tự tên                    | Nhóm = đề tài (`de_tai_id`)                             | Mỗi đồ án có một đề tài rõ ràng trong CSDL              |
| Diễn đạt lại      | Không xử lý [1]; có hướng xử lý bằng công thức, trích dẫn [4]     | Embedding câu tiếng Việt                                   | Diễn đạt lại là dạng phổ biến ở bài sinh viên           |
| Đơn vị kết luận  | Cặp tài liệu                                                                | Từng câu, gộp thành tỷ lệ theo nguồn và tỷ lệ tổng | Giảng viên cần thấy đúng đoạn nào trùng                  |

---

## 6. Giới hạn và hướng phát triển

- **Công thức, hình ảnh, trích dẫn chưa được phân tích.** [3][4] cho thấy các đặc trưng này bắt được chép ý và chép đã che giấu; [5] cho thấy cả các phương pháp tốt nhất vẫn bỏ sót phần lớn chép công thức. Đồ án CNTT ít công thức nên ưu tiên trước là **so ảnh** (sơ đồ, hình chụp màn hình) và **so danh mục tài liệu tham khảo**.
- **Đoạn có trích dẫn nguồn vẫn bị tính trùng.** Chưa có nhãn "trích dẫn có ghi nguồn" như bộ lọc của Turnitin.
- **Đầu vào:** chưa có OCR cho PDF ảnh quét; LaTeX chưa được biên dịch tự động (22 đồ án kho đang chờ quy trình ở mục 3.2).
- **Dữ liệu hiệu chỉnh là tổng hợp.** Bộ dữ liệu không có câu chép rồi sửa nhẹ, nên k = 6 có thể hơi dài với văn bản thật: sửa một từ gần đầu hoặc cuối câu làm mất tới 8 âm tiết khỏi độ phủ. Ngưỡng tổng mới được kiểm tra trên bài ghép dựng thêm.
- **Chép rồi biến đổi mạnh** (dịch, viết lại bằng mô hình ngôn ngữ lớn) có thể lọt cả hai tín hiệu; [5] cũng nêu nguy cơ này.

---

## Tài liệu tham khảo

[1] D. Sorokina, J. Gehrke, S. Warner, P. Ginsparg, "Plagiarism Detection in arXiv," in *Proc. 6th IEEE International Conference on Data Mining (ICDM'06)*, 2006, pp. 1070–1075, doi:10.1109/ICDM.2006.126.

[2] S. Schleimer, D. S. Wilkerson, A. Aiken, "Winnowing: Local Algorithms for Document Fingerprinting," in *Proc. ACM SIGMOD*, 2003, pp. 76–85, doi:10.1145/872757.872770.

[3] N. Meuschke, M. Schubotz, F. Hamborg, T. Skopal, B. Gipp, "Analyzing Mathematical Content to Detect Academic Plagiarism," in *Proc. ACM CIKM*, 2017, doi:10.1145/3132847.3133144.

[4] N. Meuschke, V. Stange, M. Schubotz, B. Gipp, "HyPlag: A Hybrid Approach to Academic Plagiarism Detection," in *Proc. ACM SIGIR*, 2018, doi:10.1145/3209978.3210177.

[5] A. Satpute et al., "Taxonomy of Mathematical Plagiarism," arXiv:2401.16969, 2024.
