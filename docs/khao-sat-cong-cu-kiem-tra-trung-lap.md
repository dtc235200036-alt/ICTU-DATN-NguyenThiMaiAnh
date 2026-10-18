# Khảo sát công cụ và kỹ thuật kiểm tra trùng lặp, đạo văn

> Đề tài: Hệ thống quản lý đồ án sinh viên, Khoa CNTT, Trường ĐH CNTT&TT (ICTU), Đại học Thái Nguyên
> Người thực hiện: Nguyễn Thị Mai Anh (DTC235200036). GVHD: Hà Thị Thanh
> Ngày khảo sát: 14/10/2026. Mức xác minh: mỗi nhận định có trích nguồn [n]. Những chỗ **[CHƯA XÁC MINH]** là thông tin chưa tìm được nguồn gốc hoặc mới chỉ có nguồn thứ cấp.

---

## 1. Mục tiêu

GVHD yêu cầu khảo sát kỹ trước khi xây dựng bộ kiểm tra trùng lặp, gồm ba câu hỏi:

1. Hiện nay người ta dùng **những công cụ nào** để phát hiện trùng lặp/đạo văn?
2. Nếu có dùng AI thì **dùng loại AI nào**, và dùng vào việc gì?
3. Làm sao phát hiện trùng lặp **ở mức ký tự** (ví dụ "20 ký tự liên tiếp giống nhau thì tính là trùng") và **trùng lặp hình ảnh** (ví dụ hai ảnh giống hệt nhau)?

Chính sách ngưỡng do GVHD đưa ra: **tổng tỷ lệ trùng > 20% thì cảnh báo, ≤ 20% thì đạt**. Bộ tiêu chí chính thức của Đại học Thái Nguyên (ĐHTN) GVHD sẽ gửi sau. Báo cáo này **không suy đoán nội dung** của bộ tiêu chí đó. Những điểm còn phụ thuộc vào bộ tiêu chí được gom lại ở mục 7.

---

## 2. Công cụ hiện có trên thị trường

### 2.1. Bảng so sánh

| Công cụ | Phương pháp chính | Báo cáo những gì | Tiếng Việt | Kiểm tra ảnh | Chi phí / giấy phép |
|---|---|---|---|---|---|
| **Turnitin** (Similarity Report, Feedback Studio) | So khớp chuỗi văn bản với kho Internet, kho bài nộp và kho xuất bản (độc quyền). Bộ lọc loại trừ: trích dẫn trong ngoặc kép, danh mục tài liệu tham khảo, khớp nhỏ theo số từ hoặc % (mặc định và tối thiểu là **8 từ**), và "Exclude cited text" ở bản báo cáo mới [1][2]. Có cờ (Flags) cho ký tự bị thay bằng ký tự giống hệt thuộc bảng chữ khác và cho chữ ẩn (chữ trắng trên nền trắng) [3]. | % tương đồng tổng, đoạn trùng được tô màu, danh sách nguồn kèm % từng nguồn | So khớp văn bản được với tiếng Việt: nhiều trường VN dùng chính thức, ví dụ ĐH Ngoại ngữ (ĐHQGHN) [10], UEH [11], ĐH Nông Lâm (ĐHTN) [14] | **Không.** Chỉ quét văn bản, không đọc chữ nằm trong ảnh [4] | Thương mại, trường mua bản quyền |
| **Turnitin AI writing detection** | Mô hình phân loại "văn bản do AI sinh" | % văn bản nghi do AI sinh, tô từng câu | Ngôn ngữ hỗ trợ: tiếng Anh, Tây Ban Nha, Nhật [5]; tiếng Ả Rập (08/2026) [6]; Hà Lan, Đức, Thổ Nhĩ Kỳ (10/2026) [7]. **Không tìm thấy tiếng Việt.** Bài nộp bằng ngôn ngữ không hỗ trợ sẽ không được chấm điểm AI [5]. | — | Đi kèm gói Turnitin |
| **iThenticate** (Turnitin) | Cùng công nghệ với Turnitin, hướng tới nhà xuất bản và tạp chí. Là nền của Crossref Similarity Check [8][9] | Tương tự Turnitin, có loại trừ nội dung [8] | Như Turnitin | Không thấy tài liệu về so ảnh | Thương mại |
| **DoIT** (ĐH Công nghệ, ĐHQGHN) | Hệ thống tiếng Việt, gồm kiểm tra chính tả và phát hiện trùng lặp. Quy trình kiểm tra trùng lặp đã được cấp bằng độc quyền sáng chế (công bố 25/12/2020) [12]. Thuật toán chi tiết **[CHƯA XÁC MINH]**. | Tỷ lệ trùng chung, tỷ lệ trùng với tác phẩm khác, tỷ lệ trùng với công bố của chính tác giả, kết quả trước và sau khi loại nguồn (theo hồ sơ ở thư viện ĐH KHXH&NV TP.HCM) [13] | Có, được thiết kế riêng cho tiếng Việt [12][23] | **[CHƯA XÁC MINH]** | Nguồn thứ cấp nói khoảng 15 cơ sở dùng (có ĐHQGHN), dùng miễn phí khi đăng ký tài khoản **[CHƯA XÁC MINH, nguồn tin tức]**. **Không tìm thấy bằng chứng ĐHTN hay ICTU dùng DoIT.** |
| **Copyleaks** | So khớp văn bản (kể cả văn bản diễn đạt lại, theo tài liệu của hãng) và mô hình phát hiện văn bản AI. Có OCR để quét chữ trong ảnh và tài liệu scan [15] | % trùng, nguồn, % AI | Bộ phát hiện AI hỗ trợ 30 ngôn ngữ, **có tiếng Việt (`vi`)** [16] | Chỉ OCR chữ trong ảnh. Đây không phải so khớp ảnh với ảnh | Thương mại, có API |
| **Ouriginal** (Urkund + PlagScan) | So khớp văn bản | — | — | — | Turnitin mua lại năm 2021 [17]. **Đã ngừng dịch vụ cuối năm 2025** theo thông báo của các trường đang dùng (mỗi trường ghi một mốc ngày khác nhau) [18]. Không nên chọn. |
| **MOSS** (Stanford) | Vân tay k-gram bằng **winnowing** [19][20] | Cặp tệp giống nhau, đoạn khớp | Dành cho **mã nguồn**, không dùng cho văn xuôi | Không | Miễn phí cho mục đích học thuật, chạy dưới dạng dịch vụ |
| **JPlag** | Token hóa mã nguồn rồi chạy **Greedy String Tiling** [21] | Cặp tương đồng, % | Dành cho mã nguồn (có chế độ văn bản) | Không | Mã nguồn mở (GPL-3.0) |
| **copydetect** (Python) | Winnowing, lấy cảm hứng từ MOSS [22] | Báo cáo HTML, đoạn khớp, % | Dành cho mã nguồn | Không | Mã nguồn mở, `pip install copydetect` (0.5.0) |
| **Sherlock** (ĐH Warwick) | So khớp vân tay cho văn bản và mã nguồn | Cặp tương đồng | — | Không | Mã nguồn mở **[CHƯA XÁC MINH phiên bản và trạng thái bảo trì]** |
| Các dịch vụ thương mại VN (kiemtratailieu.vn…) | Không công bố phương pháp | % trùng, nguồn | Có | **[CHƯA XÁC MINH]** | Thương mại. Một số trường có hệ thống riêng, ví dụ ĐH Thủ Dầu Một dùng `trasoat.tdmu.edu.vn` [24] |

### 2.2. Nhận xét

- **Các công cụ phổ biến đều dựa trên so khớp chuỗi văn bản (string matching).** Bước lọc như ngưỡng "≥ 8 từ" hay "đoạn ≥ 100 từ" đều áp lên các đoạn khớp nguyên văn [1][10].
- **Phần "AI" trong các công cụ thương mại** gồm hai việc. (a) Phát hiện diễn đạt lại (paraphrase) bằng mô hình ngôn ngữ, việc mà hệ thống của đề tài đang làm bằng embedding. (b) Phát hiện văn bản do AI sinh. Bộ phát hiện kiểu (b) của Turnitin **chưa hỗ trợ tiếng Việt**. Copyleaks có ghi hỗ trợ tiếng Việt, nhưng không tìm thấy số liệu độ chính xác công bố cho tiếng Việt.
- **Không công cụ phổ biến nào so khớp ảnh với ảnh.** Turnitin không đọc ảnh [4]. Copyleaks chỉ OCR chữ trong ảnh [15]. Kiểm tra ảnh trùng sẽ là **điểm khác biệt** của đề tài, nhưng cũng là phần phải tự xây dựng từ đầu.

---

## 3. Quy định ngưỡng trùng lặp

### 3.1. Cấp Bộ GD&ĐT

- Thông tư 23/2021/TT-BGDĐT (quy chế đào tạo thạc sĩ) yêu cầu luận văn tuân thủ quy định về liêm chính học thuật của cơ sở đào tạo (khoản 2 Điều 8, theo nguồn thứ cấp [25]). **Không tìm thấy điều khoản nào trong các thông tư của Bộ quy định con số % trùng lặp.** Ngưỡng do từng trường tự ban hành. Thông tư 18/2021/TT-BGDĐT (tiến sĩ) cũng vậy: không tìm thấy điều khoản nêu ngưỡng %.
- **[CHƯA XÁC MINH]** Nguồn [25] nhắc tới một thông tư mới năm 2026 về đào tạo sau đại học. Chưa kiểm tra văn bản này có thay thế Thông tư 23/2021 hay không.
- Không tìm thấy văn bản cấp Bộ quy định ngưỡng trùng lặp cho **đồ án hay khóa luận đại học**.

### 3.2. Ví dụ quy định của các trường (để tham khảo, không áp dụng cho ĐHTN)

| Trường | Ngưỡng | Phần loại trừ khi tính % | Nguồn |
|---|---|---|---|
| ĐH Ngoại ngữ, ĐHQGHN (KLTN đại học, ban hành 07/2025) | Vi phạm nếu: (a) sao chép nguyên văn **một đoạn từ 100 từ trở lên** mà không trích dẫn đầy đủ, **hoặc** (b) **từ 25%** văn bản giống nguồn khác. Trừ điểm theo mức: 25–29% trừ 25% điểm; 30–49% trừ 50% điểm; ≥ 50% nhận 0 điểm. Tỷ lệ AI từ 25% trở lên thì GVHD xem xét theo đánh giá chuyên môn. | Chỉ tính phần nội dung chính, **không tính Mục lục, Tóm tắt, Tài liệu tham khảo và trích dẫn đúng quy định** | [10] (bản gốc, dùng Turnitin, có cả chức năng kiểm tra AI) |
| UEH (QĐ 4002/QĐ-ĐHKT, 18/12/2025) | Dấu hiệu vi phạm khi tỷ lệ tương đồng **từ 20%**. Tỷ lệ này "không phải căn cứ duy nhất để kết luận đạo văn". Kết quả của công cụ phát hiện AI cũng không được dùng làm căn cứ duy nhất. | Trích dẫn, danh mục tài liệu tham khảo, phần mô tả phương pháp phổ biến trong chuyên ngành, thuật ngữ, tiêu chuẩn kỹ thuật, văn bản pháp luật, tên riêng | [11] (bản gốc) |
| NEU > 25%; ĐHQGHN > 25% (HD 2383/2017); HCMUE > 20%; UEL, TVU ≥ 30%; HVNH 20–30% | Theo bảng tổng hợp | — | [26] (**nguồn thứ cấp** của một doanh nghiệp, chưa đối chiếu với văn bản gốc) |

Nhìn chung, ngưỡng ở VN thường **từ 20% đến 30%**. Nhiều trường đặt **thêm một tiêu chí độc lập** là đoạn trùng nguyên văn dài (khoảng 100 từ) [10][26]. Các trường **đều loại trừ** tài liệu tham khảo và trích dẫn hợp lệ khi tính % [10][11].

### 3.3. Đại học Thái Nguyên và ICTU

- **Không tìm thấy** văn bản quy định công khai trên mạng của ĐHTN hoặc ICTU về ngưỡng trùng lặp hay phần mềm kiểm tra (đã tìm với các từ khóa: kiểm tra trùng lặp, đạo văn, liêm chính học thuật, Trung tâm Học liệu, ICTU).
- Bằng chứng duy nhất tìm được: Hiệu trưởng **Trường ĐH Nông Lâm (thuộc ĐHTN)** cho biết trường có quy định bắt buộc GVHD và người học dùng phần mềm kiểm tra như **Turnitin** để phát hiện trùng lặp và hỗ trợ nhận diện nội dung có dấu hiệu do AI tạo ra [14]. Đây là **bài báo**, không phải văn bản quy định, và chỉ nói về một trường thành viên.
- Kết luận: **dùng ngưỡng 20% theo chính sách GVHD** và để mọi tham số có thể cấu hình, chờ bộ tiêu chí chính thức của ĐHTN.

---

## 4. Kỹ thuật phát hiện

### 4.1. Trùng lặp ở mức ký tự / chuỗi nguyên văn

**Chuẩn hóa văn bản tiếng Việt trước khi so khớp.** Bước này bắt buộc, vì cùng một chữ có dấu có thể được mã hóa theo nhiều cách khác nhau:

1. Chuẩn hóa Unicode về **NFC** [27]. Văn bản lấy từ PDF hoặc Word có thể ở dạng tổ hợp (NFD), ví dụ "ệ" = e + dấu mũ + dấu nặng. Nếu không chuẩn hóa, hai chuỗi nhìn giống nhau vẫn bị coi là khác.
2. `casefold()` (chữ thường). Gộp mọi khoảng trắng, xuống dòng và tab thành một dấu cách. Bỏ hoặc gộp dấu câu (đổi thành dấu cách) để việc thêm hay bớt dấu phẩy không làm gãy chuỗi khớp.
3. **Giữ nguyên dấu tiếng Việt.** Nếu bỏ dấu, "bàn"/"bán"/"bạn" trùng nhau và sinh khớp giả.
4. Thay các ký tự trông giống nhau (Cyrillic "а" đổi thành Latin "a", ký tự độ rộng 0, NBSP) theo bảng ánh xạ. Turnitin cũng gắn cờ thủ thuật này [3].
5. **Lưu bảng ánh xạ vị trí** từ văn bản đã chuẩn hóa về văn bản gốc, để tô đúng đoạn trùng trên giao diện.

**Các thuật toán:**

| Kỹ thuật | Ý tưởng | Ưu / nhược |
|---|---|---|
| **k-gram ký tự + Rabin–Karp rolling hash** [28] | Băm mọi chuỗi con dài k (ví dụ k = 20) bằng hàm băm cuốn, tính trong O(1) cho mỗi lần dịch. Hai văn bản có chung một mã băm thì có thể có chung một đoạn ≥ k ký tự. | Đơn giản và chính xác. Số mã băm bằng số ký tự, nhưng với khoảng vài trăm tài liệu (vài triệu ký tự) thì vẫn chứa được trong RAM. |
| **Winnowing** (Schleimer, Wilkerson, Aiken 2003, nền của MOSS) [19] | Trong mỗi cửa sổ w mã băm liên tiếp, chỉ giữ mã nhỏ nhất làm "vân tay". **Đảm bảo**: mọi đoạn khớp dài ≥ t = w + k − 1 đều được phát hiện, đoạn ngắn hơn k thì bỏ qua. | Giảm lượng vân tay lưu trữ (mật độ khoảng 2/(w+1)) mà không mất đoạn khớp dài. Đây là lựa chọn chuẩn. |
| **Suffix array / suffix automaton** (LCS) | Dựng mảng hậu tố của chuỗi nối hai văn bản để tìm mọi chuỗi con chung tối đa có độ dài ≥ N. | Chính xác tuyệt đối, cho đoạn khớp tối đa. Phù hợp để **xác minh và mở rộng** một cặp tài liệu đã được lọc trước, ví dụ bằng `pydivsufsort` [29]. Không dùng để quét cả kho. |
| **Greedy String Tiling** (Wise 1993, dùng trong JPlag) [21] | Lặp lại việc phủ "viên gạch" không chồng lấn, ưu tiên đoạn dài nhất trước, với độ dài tối thiểu MML | Chịu được việc đảo thứ tự các đoạn. Độ phức tạp cao hơn, phù hợp so từng cặp. |
| **MinHash/LSH trên k-gram âm tiết** (hệ thống đang dùng) | Ước lượng hệ số Jaccard giữa hai tập k-gram | Tốt để **xếp hạng câu gần giống**, nhưng chỉ cho điểm xấp xỉ theo từng câu. **Không chỉ ra được chính xác đoạn ký tự nào trùng** và không đảm bảo "≥ N ký tự". |

**Cách cài đặt quy tắc "≥ N ký tự liên tiếp trùng" bằng Python (đề xuất):**

1. Chuẩn hóa toàn bộ kho tài liệu, sinh vân tay bằng winnowing với k = N (ví dụ 20) và w nhỏ (ví dụ 4–8). Lưu chỉ mục ngược `hash → [(mã tài liệu, vị trí)]` trong bộ nhớ của AI service. Có thể lưu kèm vào MySQL để không phải tính lại khi khởi động.
2. Với tài liệu cần kiểm tra: sinh vân tay, tra chỉ mục, gom các "hạt giống" khớp theo từng tài liệu nguồn, rồi **mở rộng** sang hai bên bằng cách so trực tiếp từng ký tự (hoặc dùng `difflib.SequenceMatcher` hay suffix array cho cặp đó) để được đoạn khớp tối đa [s, e). Chỉ giữ đoạn có độ dài ≥ N.
3. **Loại trừ trước khi tính**: trích dẫn trong ngoặc kép, danh mục tài liệu tham khảo, phần mẫu chung (bìa, lời cam đoan, mục lục…). Hệ thống đã có `strip_boilerplate` cho việc này. Thêm một bước nữa: **bỏ các k-gram xuất hiện trong quá nhiều tài liệu của kho** (ví dụ > 10% số tài liệu), như cách MOSS bỏ mã khuôn mẫu chung, vì đó là cụm từ chuyên ngành phổ biến chứ không phải sao chép.

```python
import unicodedata, re
_WS = re.compile(r"[\s\W_]+", re.UNICODE)

def normalize(text: str) -> str:
    t = unicodedata.normalize("NFC", text).casefold()
    return _WS.sub(" ", t).strip()          # giữ dấu tiếng Việt

def kgram_hashes(s: str, k: int):           # dùng hash() cho bản thử; bản thật dùng rolling hash 64-bit
    return [(hash(s[i:i+k]), i) for i in range(len(s) - k + 1)]

def winnow(hashes, w: int):
    fp, prev = [], None
    for i in range(len(hashes) - w + 1):
        h, pos = min(hashes[i:i+w], key=lambda x: (x[0], -x[1]))  # lấy phần tử nhỏ nhất, nếu bằng nhau lấy vị trí bên phải
        if (h, pos) != prev:
            fp.append((h, pos)); prev = (h, pos)
    return fp
```

**Tính tỷ lệ % theo độ phủ ký tự (coverage), thay cho tỷ lệ câu bị gắn cờ:**

- `ty_le_tong = |hợp các khoảng ký tự bị khớp| / |tổng ký tự được kiểm tra (sau khi loại trừ)| × 100`. Các khoảng khớp với nhiều nguồn chồng lên nhau chỉ tính **một lần** (gộp khoảng).
- `ty_le_nguon[i]` = độ phủ do riêng nguồn i gây ra, để liệt kê nguồn theo thứ tự giảm dần như Turnitin.
- Báo cáo kèm `ty_le_loai_tru` (phần không được kiểm tra), để người xem không bị đánh lừa bởi một tài liệu "0%" mà thực ra đã bị loại trừ gần hết.

**Lưu ý khi chọn N = 20 ký tự:** 20 ký tự tiếng Việt chỉ khoảng **4–5 âm tiết**, ví dụ "hệ thống quản lý đồ án" dài 22 ký tự. Chuỗi ngắn như vậy rất dễ trùng ngẫu nhiên giữa các đồ án cùng lĩnh vực. Để so sánh: Turnitin mặc định bỏ khớp dưới 8 từ [1], còn ĐH Ngoại ngữ dùng mức đoạn 100 từ cho tiêu chí nguyên văn [10]. Đề xuất: **N là tham số cấu hình**, mặc định hiệu chỉnh trên tập seed (dự kiến khoảng 40–60 ký tự, tương đương 8–12 âm tiết, **[CẦN HIỆU CHỈNH]**), kết hợp với danh sách cụm từ phổ biến bị bỏ qua. Nếu GVHD giữ mức 20 ký tự thì danh sách cụm từ phổ biến là bắt buộc.

### 4.2. Trùng lặp hình ảnh

**Trích xuất ảnh:**

- **DOCX** là một tệp zip. Ảnh nằm trong `word/media/*` (png, jpeg, emf, wmf…). Đọc bằng `zipfile`, hoặc qua `document.part.related_parts` của python-docx (1.2.0). Lưu ý: Pillow trên Linux **không đọc được EMF/WMF**. Có thể bỏ qua kèm ghi chú, hoặc chuyển đổi bằng LibreOffice hay ImageMagick nếu cần.
- **PDF**: PyMuPDF (1.28.x) dùng `page.get_images(full=True)` rồi `doc.extract_image(xref)` để lấy ảnh nhúng nguyên gốc [30]. Hình vẽ vector (sơ đồ vẽ trực tiếp trong Word hoặc PDF) **không phải là ảnh**, nên cách này không bắt được. Nếu cần, có thể render vùng đó thành ảnh (`page.get_pixmap(clip=...)`), nhưng việc này phức tạp và nên để sau.
- Bỏ ảnh quá nhỏ (ví dụ < 64×64 px, thường là icon hoặc logo) và **logo trường/khoa xuất hiện trong mọi đồ án**. Cách lọc: ảnh có mã băm xuất hiện trong > X% số tài liệu của kho thì coi là ảnh mẫu.

**Các kỹ thuật so ảnh:**

| Kỹ thuật | Phát hiện được | Bị qua mặt bởi | Công cụ |
|---|---|---|---|
| **SHA-256 trên byte ảnh** | Ảnh **giống hệt từng byte** | Chỉ cần lưu lại hoặc nén lại là băm khác | `hashlib` |
| **Perceptual hash** (aHash / dHash / pHash 64 bit) [31][32] | Ảnh giống nhau sau khi **đổi kích thước, nén lại JPEG, chỉnh sáng nhẹ, đổi định dạng** | **Cắt xén** mạnh, xoay, lật, ghép ảnh, chèn chữ lên ảnh | `imagehash` 4.3.2 + Pillow 12.x [31] |
| **Embedding CLIP** (cosine) [33] | Ảnh gần giống về **nội dung**, chịu được cắt xén, xoay nhẹ, chụp lại màn hình | Sinh khớp giả giữa các ảnh khác nhau nhưng cùng loại (ví dụ hai sơ đồ use-case khác nhau) | `open-clip-torch` 3.3.0. Mô hình ViT-B/32 chạy được trên CPU nhưng chậm hơn và tốn thêm khoảng 600 MB RAM |

**Ngưỡng khoảng cách Hamming (pHash 64 bit):** khoảng cách 0 nghĩa là gần như chắc chắn trùng, ≤ 5–10 thường được coi là "giống nhau" [32]. **Đây là kinh nghiệm thực hành, không phải chuẩn [CẦN HIỆU CHỈNH]** trên tập ảnh seed: đưa vào các biến thể như đổi cỡ, nén JPEG ở chất lượng 70, chụp màn hình, cắt 10% để đo tỷ lệ phát hiện và khớp giả. Ảnh chụp màn hình giao diện hay sơ đồ UML có nhiều vùng trắng, nên các mã hash dễ gần nhau hơn ảnh chụp thật. Nên kết hợp hai hàm băm (pHash và dHash cùng phải nhỏ hơn ngưỡng) để giảm khớp giả.

**Chịu được cắt xén (tùy chọn):** băm thêm các ô con của ảnh (ví dụ lưới 2×2 hoặc 3×3) hoặc dùng `imagehash.crop_resistant_hash`. Tính năng này **nên làm sau**, nếu còn thời gian.

**Báo cáo ảnh:** "Ảnh k trong tài liệu ↔ ảnh j của đồ án X (trang/thứ tự), khoảng cách Hamming d, loại: giống hệt / gần giống", kèm ảnh thu nhỏ của hai bên. **Nên tách tỷ lệ ảnh trùng (số ảnh trùng / tổng số ảnh) khỏi tỷ lệ văn bản**, vì không có quy chuẩn nào gộp chung hai loại này (xem mục 7).

### 4.3. Trùng lặp ngữ nghĩa (diễn đạt lại)

- Sinh viên thường đổi từ, đảo câu hay viết lại câu, nên so khớp chuỗi nguyên văn bỏ sót. Embedding câu (bi-encoder) đưa câu về vector rồi so bằng cosine. Hệ thống đã làm việc này với `bkai-foundation-models/vietnamese-bi-encoder` [34] kèm bước tách từ `underthesea`, và chỉ mục FAISS chính xác.
- Hạn chế: điểm cosine cao **không chứng minh** được việc sao chép. Hai câu tự viết về cùng một khái niệm vẫn có thể gần nhau. Vì vậy hệ thống đang yêu cầu cờ ngữ nghĩa phải nằm trong chuỗi ≥ 2 câu liên tiếp cùng nguồn. Nên giữ cách làm này và báo cáo **tách riêng** "trùng nguyên văn" với "nghi diễn đạt lại", để GVHD tự đánh giá.

### 4.4. Phát hiện văn bản do AI sinh

- **Turnitin AI** chỉ hỗ trợ một số ngôn ngữ, **không có tiếng Việt** [5][6][7]. Turnitin tự công bố tỷ lệ dương tính giả cấp tài liệu < 1% với tài liệu có > 20% văn bản AI, nhưng thừa nhận dương tính giả vẫn xảy ra và giáo viên phải tự phán đoán [35]. Các mức < 20% bị gắn dấu sao vì kém tin cậy [5].
- **Copyleaks** ghi có hỗ trợ tiếng Việt [16], nhưng không tìm thấy đánh giá độc lập cho tiếng Việt.
- **Thiên lệch:** Liang và cộng sự (Patterns, 2023) đo 7 bộ phát hiện trên bài luận TOEFL của người không phải bản ngữ tiếng Anh. Kết quả: tỷ lệ dương tính giả trung bình **61,3%**, và chỉ cần prompt đơn giản là qua mặt được các bộ phát hiện [36]. Rủi ro này càng lớn với tiếng Việt, ngôn ngữ ít dữ liệu huấn luyện.
- Quy định của các trường cũng thận trọng: UEH **không dùng kết quả của công cụ phát hiện AI làm căn cứ duy nhất** [11]; ĐH Ngoại ngữ khi tỷ lệ AI ≥ 25% thì giao GVHD đánh giá chuyên môn [10].
- **Kết luận cho đề tài:** **không tự xây bộ phát hiện văn bản AI.** Không có dữ liệu gán nhãn tiếng Việt, kết quả không đáng tin cậy, và có rủi ro kết tội oan. Chỉ nên nêu trong báo cáo đồ án là "hướng phát triển" hoặc "tích hợp công cụ bên ngoài nếu Khoa có bản quyền".

---

## 5. Hiện trạng hệ thống và khoảng trống

Mô tả dựa trên mã nguồn `ai-service/app/` và `ai-service/README.md` (đọc ngày 14/10/2026):

| Thành phần | Hiện trạng | Tệp |
|---|---|---|
| Trích xuất | Web API trích văn bản từ DOCX (phân tích XML, giống `paragraph.text`) và PDF (`page.get_text()` của PyMuPDF). AI service **chỉ nhận văn bản, không nhận tệp**. **Không trích ảnh.** | `backend/app/services/documents.py`, `ai-service/README.md` |
| Chuẩn hóa | NFC, bỏ NUL, gộp khoảng trắng. Âm tiết `\w+` sau `casefold`. Tách từ `underthesea` cho mô hình bkai. | `app/nlp/normalize.py`, `app/embedding.py` |
| Loại phần mẫu chung | Bìa, lời cam đoan, lời cảm ơn, mục lục, danh mục hình/bảng, tiêu đề, chú thích, tài liệu tham khảo, phụ lục, header/footer lặp lại. Danh sách hiện là **[ASSUMED]**, chờ mẫu chính thức. Có báo `ty_le_loai_tru`. | `app/nlp/boilerplate.py` |
| Đơn vị so khớp | **Câu**: tách tại `. ! ? …`, bỏ câu < 6 âm tiết, cắt câu > 120 âm tiết. | `app/nlp/chunking.py` |
| Tín hiệu ngữ nghĩa | Cosine tốt nhất qua FAISS `IndexFlatIP` (vector chuẩn hóa L2), ngưỡng `nguong_doan` = 67,7%. | `app/index.py`, `app/pipeline.py` |
| Tín hiệu nguyên văn | MinHash (`datasketch`, 128 hoán vị) trên **4-gram âm tiết**, Jaccard tốt nhất **theo từng câu**, ngưỡng `nguong_nguyen_van` = 88,7%. | `app/minhash.py`, `app/pipeline.py` |
| Tỷ lệ tổng | `ty_le_tong` = **tỷ lệ ký tự của các câu bị gắn cờ** trên tổng ký tự câu nội dung. Mỗi câu bị gắn cờ được tính trọn cả câu, kể cả khi chỉ một phần câu trùng. Lưu ý: tỷ lệ này tính theo ký tự của câu, không phải "tỷ lệ đoạn bị gắn cờ" như mô tả ban đầu. | `pipeline.check_document` |
| Quyết định cảnh báo | Web API so **tỷ lệ của nguồn cao nhất** (`ty_le_nguon_cao_nhat`) với `NGUONG_TAI_LIEU` cấu hình được (giá trị hiệu chỉnh đề xuất 10,4%, giá trị dự phòng 30%). **Không so `ty_le_tong` với 20%.** | `backend/app/services/document_check.py` |
| Phạm vi so | Chỉ kho đồ án của Khoa (PI 3.4) | — |

**Khoảng trống so với yêu cầu mới của GVHD:**

1. **Chưa có quy tắc "≥ N ký tự liên tiếp trùng".** MinHash cho điểm Jaccard xấp xỉ theo câu, không định vị được đoạn ký tự trùng và không đảm bảo độ dài tối thiểu.
2. **% chưa tính theo độ phủ ký tự thật.** Một câu dài chỉ trùng một nửa vẫn bị tính cả câu, còn đoạn trùng nằm vắt qua ranh giới hai câu thì có thể bị lọt.
3. **Chưa kiểm tra ảnh** (cả trích xuất lẫn so khớp).
4. **Quy tắc ra quyết định khác chính sách của GVHD.** GVHD dùng tổng % > 20% thì cảnh báo, hệ thống đang dùng % của nguồn cao nhất so với ngưỡng hiệu chỉnh.
5. Chưa loại trừ **trích dẫn trong ngoặc kép** (mới loại danh mục tài liệu tham khảo theo mục).

---

## 6. Đề xuất giải pháp cho đề tài

**Nguyên tắc:** giữ nguyên các phần đang chạy (embedding + FAISS cho diễn đạt lại), **bổ sung** hai mô-đun độc lập, và thống nhất cách tính % theo độ phủ ký tự. Tất cả chạy trên CPU, phù hợp kho khoảng 300 đề tài và vài trăm tài liệu.

### 6.1. Kiến trúc đề xuất

```
DOCX/PDF ──► Web API: trích văn bản + trích ảnh (mới) ──► AI service
                                                            ├─ (1) Nguyên văn: winnowing k = N ký tự, mở rộng đoạn khớp tối đa  [MỚI]
                                                            ├─ (2) Diễn đạt lại: embedding bkai + FAISS (giữ nguyên)
                                                            └─ (3) Ảnh: SHA-256 + pHash/dHash, Hamming ≤ ngưỡng          [MỚI]
Tổng hợp: ty_le_tong = |hợp khoảng ký tự bị gắn cờ bởi (1) ∪ câu bị gắn cờ bởi (2)| / tổng ký tự được kiểm tra
Quyết định: ty_le_tong > 20% → CẢNH BÁO; ≤ 20% → ĐẠT   (ngưỡng cấu hình qua cau_hinh_nguong)
Báo cáo: % tổng; % nguyên văn và % diễn đạt lại; % theo từng nguồn; danh sách đoạn trùng (vị trí, đoạn nguồn, độ dài); ảnh trùng; % bị loại trừ
```

### 6.2. Chi tiết và thư viện

| Hạng mục | Cách làm | Thư viện (phiên bản trên PyPI, 14/10/2026) | Công sức ước lượng |
|---|---|---|---|
| Mô-đun nguyên văn | Chuẩn hóa (mục 4.1), winnowing với k = `MIN_KY_TU_TRUNG` (cấu hình, mặc định chọn sau khi hiệu chỉnh) và w = 4–8. Chỉ mục ngược dựng trong RAM lúc khởi động từ `chunk.noi_dung`, giống cách đang làm với MinHash. Mở rộng đoạn khớp, gộp khoảng. Lọc k-gram phổ biến (xuất hiện trong > 10% số tài liệu). | Thư viện chuẩn Python. `pydivsufsort` 0.0.20 để xác minh từng cặp (tùy chọn). `rapidfuzz` 3.14.x nếu cần so mờ | 3–4 ngày, gồm unit test |
| Độ phủ ký tự | Ánh xạ khoảng ký tự (văn bản chuẩn hóa → văn bản gốc), hợp khoảng của tín hiệu (1) và các câu của tín hiệu (2), tính % tổng, % từng nguồn, % từng tín hiệu | — | 1–2 ngày |
| Loại trừ trích dẫn | Bỏ đoạn trong `"…"`/`“…”` dài hơn một ngưỡng (giống Turnitin), giữ danh mục tài liệu tham khảo đã có | `re` | 0,5 ngày |
| Mô-đun ảnh | Web API trích ảnh (DOCX `word/media`, PDF `extract_image`), bỏ ảnh < 64 px và ảnh mẫu (logo). Lưu SHA-256 + pHash + dHash vào bảng mới trong MySQL. Truy vấn bằng quét tuyến tính khoảng cách Hamming (vài nghìn ảnh thì dưới 1 giây). | `imagehash` 4.3.2, `Pillow` 12.x, `pymupdf` 1.28.x, `python-docx` 1.2.0 | 3–4 ngày (gồm migration và API) |
| CLIP cho ảnh gần giống | **Không làm trong 10 tuần.** Ghi vào "hướng phát triển". | `open-clip-torch` 3.3.0 | (2–3 ngày nếu làm) |
| Giao diện và báo cáo | Thêm cột "loại trùng" (nguyên văn / diễn đạt lại / ảnh), nhãn ĐẠT/CẢNH BÁO theo 20%, xem ảnh thu nhỏ hai bên | React + antd (đang dùng) | 2–3 ngày |
| Hiệu chỉnh và đánh giá | Bổ sung vào `seed-data` các cặp sao chép có chủ đích: chép nguyên văn đoạn dài ngắn khác nhau, ảnh bị đổi cỡ, nén lại, cắt. Đo precision/recall theo N và ngưỡng Hamming. Ghi kết quả vào `calibration/` như với các ngưỡng hiện có. | Script hiện có trong `calibration/` | 2 ngày |
| **Tổng** | | | **khoảng 12–16 ngày công** |

### 6.3. Vì sao chọn tổ hợp này

- **Winnowing** đáp ứng đúng yêu cầu "≥ N ký tự liên tiếp" với **bảo đảm toán học** (không bỏ sót đoạn khớp dài ≥ t) [19], đã được kiểm chứng qua MOSS, cài bằng thư viện chuẩn và chạy nhanh trên CPU. Nó cũng **chỉ ra chính xác đoạn trùng**, điều PI 3.4 yêu cầu.
- **Giữ embedding** để bắt diễn đạt lại, việc mà các công cụ thương mại cũng làm. Đây là phần "AI" của đề tài và đã có số liệu hiệu chỉnh.
- **MinHash** có thể giữ làm bộ lọc sơ bộ hoặc bỏ dần, vì winnowing thay thế nó cho tín hiệu nguyên văn. Đề xuất: giữ đến khi có số liệu so sánh trên seed, sau đó quyết định.
- **pHash + SHA-256** đủ cho yêu cầu "hai ảnh giống nhau" (kể cả khi bị đổi cỡ hoặc nén lại), chạy nhẹ, và là điểm khác biệt mà Turnitin không có [4].
- **Không làm bộ phát hiện văn bản AI**, vì lý do ở mục 4.4.

---

## 7. Câu hỏi cần xác nhận với GVHD (khi có bộ tiêu chí của ĐHTN)

1. **Ngưỡng và cách tính:** 20% áp lên **toàn bộ tài liệu** hay **từng chương**? Có thêm ngưỡng **theo từng nguồn** (ví dụ ≤ 10% từ một nguồn) không? Ngưỡng là "> 20%" hay "≥ 20%"?
2. **Độ dài khớp tối thiểu:** "20 ký tự" là quy định chính thức hay chỉ là ví dụ? Tính theo ký tự, theo âm tiết hay theo từ? Có tính dấu cách và dấu câu không? Có tiêu chí độc lập kiểu "một đoạn nguyên văn ≥ 100 từ là vi phạm" như ĐH Ngoại ngữ [10] không?
3. **Phần được loại trừ:** bìa, lời cam đoan, mục lục, tóm tắt, tài liệu tham khảo, phụ lục, **trích dẫn có ghi nguồn**, mã nguồn, bảng số liệu, thuật ngữ chuyên ngành?
4. **Trùng diễn đạt lại (ngữ nghĩa)** có được cộng vào tổng % không, hay chỉ tính trùng nguyên văn, còn ngữ nghĩa chỉ để tham khảo?
5. **Ảnh trùng:** tính vào tổng % (theo cách nào?) hay báo riêng? Logo hoặc ảnh mẫu bắt buộc có được loại không? Sơ đồ vẽ trực tiếp (vector) có cần kiểm tra không?
6. **Phạm vi so sánh:** chỉ kho đồ án Khoa CNTT (theo PI 3.4), hay cả các khóa trước, đề cương của chính sinh viên đó (tự trùng), Internet?
7. **Tự trùng lặp:** báo cáo của sinh viên trùng với đề cương của chính mình thì có được loại không? Hệ thống hiện đã loại các nguồn trong `exclude_refs`.
8. **Văn bản do AI sinh:** bộ tiêu chí có yêu cầu kiểm tra không? Nếu có, Khoa có bản quyền Turnitin hay công cụ nào khác không?
9. **Hậu quả:** "cảnh báo" chỉ để thông báo cho GVHD, hay chặn sinh viên nộp hoặc bảo vệ?

---

## 8. Tài liệu tham khảo

Ngày truy cập chung cho mọi mục: **14/10/2026**. Những mục ghi "(không truy cập trực tiếp được)" chỉ dựa trên trích đoạn của công cụ tìm kiếm.

1. Louisiana State University at Alexandria – Turnitin similarity scoring: using exclusions and filters. https://helpdesk.lsua.edu/support/solutions/articles/48001269897-turnitin-similarity-scoring-using-exclusions-and-filters (nguồn thứ cấp: ngưỡng 8 từ mặc định, loại trừ trích dẫn và tài liệu tham khảo)
2. Turnitin – Excluding content from the Similarity Report. https://fa-help.turnitin.com/integrity/student/lti/the-similarity-report/excluding-content-from-the-similarity-report.htm
3. Turnitin – Flags (Feedback Studio). https://help.turnitin.com/feedback-studio/flags.htm
4. University of Liverpool – Improving academic integrity using Turnitin (staff guide). https://www.liverpool.ac.uk/media/livacuk/centre-for-innovation-in-education/staff-guides/improving-academic-integrity-using-turnitin/improving-academic-integrity-using-turnitin.pdf
5. Turnitin – AI writing detection capabilities (guide và FAQ). https://guides.turnitin.com/hc/en-us/articles/28477544839821-Turnitin-s-AI-writing-detection-capabilities (không truy cập trực tiếp được, HTTP 403)
6. Turnitin – Turnitin expands AI writing detection to support Arabic language submissions. https://www.turnitin.com.au/press/turnitin-expands-ai-writing-detection-to-support-arabic-language-submissions
7. PR Newswire – Turnitin now offers AI writing detection for Dutch, German and Turkish language submissions. https://www.prnewswire.com/da/pressemeddelelser/turnitin-now-offers-ai-writing-detection-for-dutch-german-and-turkish-language-submissions-302899374.html
8. iThenticate – Excluding content from the Similarity Report. https://fa-help.turnitin.com/ithenticate/user/the-similarity-report/excluding-content-from-the-similarity-report.htm
9. Crossref – Similarity Check. https://www.crossref.org/services/similarity-check/
10. Trường ĐH Ngoại ngữ, ĐHQGHN – Quy định kiểm soát và xử lý đạo văn đối với sinh viên đại học chính quy làm khóa luận tốt nghiệp (QĐ ngày 15/7/2025, Điều 4). https://student.ulis.vnu.edu.vn/files/uploads/2026/09/3559_Quy-dinh-kiem-soat-va-xu-ly-dao-van-doi-voi-sinh-vien-lam-KLTN.pdf
11. Đại học Kinh tế TP.HCM – Quy định về việc kiểm soát, xử lý hành vi đạo văn, sử dụng AI trong các sản phẩm học thuật (QĐ 4002/QĐ-ĐHKT-NCPTGKTC ngày 18/12/2025). https://daotao.ueh.edu.vn/quy-dinh-ve-viec-kiem-soat-xu-ly-hanh-vi-dao-van-su-dung-tri-tue-nhan-tao-ai-trong-cac-san-pham-hoc-thuat-tai-dai-hoc-kinh-te-thanh-pho-ho-chi-minh/
12. Bản tin ĐHQGHN số 321 (2017), tr. 38–41, bài về DoIT. https://tintuc.vnu.edu.vn/upload/2021/09/29262/file/321%20IN-pages-38-41.pdf (không truy cập trực tiếp được do chứng chỉ TLS hết hạn; nội dung theo trích đoạn tìm kiếm)
13. Thư viện ĐH KHXH&NV TP.HCM – Hồ sơ kết quả kiểm tra trùng lặp bằng phần mềm DoIT. https://libmc.hcmussh.edu.vn/handle/123456789/97?mode=full
14. Giáo dục Việt Nam – "AI phát triển, trường đại học có nhiều biện pháp để ngăn ngừa đạo văn trong đào tạo thạc sĩ, tiến sĩ" (phát biểu của Hiệu trưởng Trường ĐH Nông Lâm, ĐHTN). https://giaoduc.net.vn/ai-phat-trien-truong-dai-hoc-co-nhieu-bien-phap-de-ngan-ngua-dao-van-trong-dao-tao-thac-si-tien-si-post259175.gd
15. Copyleaks Docs – OCR Supported Languages. https://docs.copyleaks.com/reference/actions/miscellaneous/ocr-supported-languages
16. Copyleaks Docs – AI Detection Supported Languages. https://docs.copyleaks.com/reference/actions/miscellaneous/ai-detection-supported-languages.md
17. Turnitin – Turnitin announces intent to acquire Ouriginal. https://www.turnitin.ca/press/turnitin-announces-intent-to-acquire-ouriginal
18. Swedish University of Agricultural Sciences (SLU) – Originality (thông báo ngừng Ouriginal). https://internt.slu.se/en/support-services/education/educational-and-digital-support/educational-systems/originality ; xem thêm: https://en.wikipedia.org/wiki/PlagScan
19. Schleimer S., Wilkerson D. S., Aiken A. (2003). Winnowing: Local Algorithms for Document Fingerprinting. SIGMOD 2003. http://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf
20. MOSS – A System for Detecting Software Similarity. https://theory.stanford.edu/~aiken/moss/
21. JPlag (Greedy String Tiling; Wise M. J., 1993, "String similarity via greedy string tiling and running Karp–Rabin matching"). https://github.com/jplag/JPlag
22. copydetect. https://github.com/blingenf/copydetect ; https://pypi.org/project/copydetect/
23. VNU University of Engineering and Technology won the second prize at the Vietnam Talent Award 2017 (DoIT). https://uet.edu.vn/en/?p=8892
24. Trường ĐH Thủ Dầu Một – Quy trình tra soát luận văn, luận án. https://tdmu.edu.vn/hinh/thuvien/taptin/2-7-2025-10-34-00-am10.Quy%20trinh%20Tra%20soat%20LV%20LA.pdf
25. Thư viện Pháp luật – Luận văn thạc sĩ phải đáp ứng các yêu cầu gì (Thông tư 23/2021/TT-BGDĐT). https://thuvienphapluat.vn/phap-luat/luan-van-thac-si-phai-dap-ung-cac-yeu-cau-gi-phap-luat-quy-dinh-tieu-chuan-cua-nguoi-huong-dan-luan-2547.html ; tin liên quan: https://luatvietnam.vn/bai-viet-lien-quan/23-2021-tt-bgddt-208649.html
26. Kiemtratailieu.vn (Công ty CP Metis) – Quy định kiểm tra trùng lặp, đạo văn tại các trường đại học (nguồn thứ cấp). https://kiemtratailieu.vn/blog/tong-hop-quy-dinh-ve-kiem-tra-trung-lap-dao-van/
27. Unicode Standard Annex #15 – Unicode Normalization Forms. https://unicode.org/reports/tr15/
28. Karp R. M., Rabin M. O. (1987). Efficient randomized pattern-matching algorithms. IBM Journal of Research and Development 31(2). https://doi.org/10.1147/rd.312.0249
29. pydivsufsort. https://github.com/louisabraham/pydivsufsort
30. PyMuPDF – Recipes: Images. https://pymupdf.readthedocs.io/en/latest/recipes-images.html
31. ImageHash (Johannes Buchner). https://github.com/JohannesBuchner/imagehash ; https://pypi.org/project/ImageHash/
32. Krawetz N. – "Looks Like It" (aHash/pHash, ngưỡng khoảng cách Hamming). https://www.hackerfactor.com/blog/index.php?/archives/432-Looks-Like-It.html
33. Radford A. et al. (2021). Learning Transferable Visual Models From Natural Language Supervision (CLIP). https://arxiv.org/abs/2103.00020 ; OpenCLIP: https://github.com/mlfoundations/open_clip
34. bkai-foundation-models/vietnamese-bi-encoder – model card. https://huggingface.co/bkai-foundation-models/vietnamese-bi-encoder
35. Turnitin – Understanding false positives within our AI writing detection capabilities. https://www.turnitin.co.uk/blog/understanding-false-positives-within-our-ai-writing-detection-capabilities
36. Liang W., Yuksekgonul M., Mao Y., Wu E., Zou J. (2023). GPT detectors are biased against non-native English writers. Patterns. https://arxiv.org/abs/2304.02819
