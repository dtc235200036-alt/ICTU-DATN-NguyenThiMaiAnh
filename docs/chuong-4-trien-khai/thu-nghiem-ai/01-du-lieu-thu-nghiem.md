# Dữ liệu thử nghiệm cho dịch vụ AI kiểm tra trùng lặp

> **Mã PI:** 4.2 — **Yêu cầu:** DATA-02, DATA-03 — **Quyết định:** D-05, D-06
> (số mục chính thức của Chương 4 sẽ được đánh khi ghép quyển; mục này trình bày phần dữ liệu thử nghiệm)

## 4.x.1. Mục đích

Dịch vụ AI chỉ có thể được đánh giá khách quan khi có một bộ dữ liệu mà **đáp án đã biết trước**: đề tài nào
thực chất là đề tài cũ được đặt lại tên, đoạn văn nào được chép nguyên văn hay được viết lại, tài liệu nào chỉ
cùng lĩnh vực mà không hề trùng. Mục này mô tả bộ dữ liệu được xây dựng cho mục đích đó (PI 4.2):

- **DATA-02** — kho 300 đề tài khóa cũ (K18–K22) để nạp vào kho đồ án qua đúng luồng import CSV của hệ thống,
  cùng 80 truy vấn tên đề tài có nhãn dùng để hiệu chỉnh và kiểm chứng ngưỡng cảnh báo trùng tên đề tài.
- **DATA-03** — 50 tài liệu đề cương/báo cáo (DOCX và PDF) tạo thành 25 cặp có mức trùng lặp chủ đích, kèm
  manifest ghi nguồn gốc từng đoạn để đối chiếu kết quả của dịch vụ AI.

**Dữ liệu tổng hợp.** Toàn bộ tên đề tài, họ tên, mã sinh viên và mọi đoạn văn đều được bộ sinh `tools/datagen`
tạo ra từ từ vựng tự soạn; không có câu chữ nào lấy từ đồ án hay báo cáo thật của sinh viên (D-06, bảo vệ quyền
riêng tư và bản quyền). Mã sinh viên dùng khối `DTC{yy}5290nnn` không trùng với tài khoản sinh viên đang có trong
hệ thống, và mã giảng viên chỉ lấy trong GV001–GV022 đã có sẵn.

**Khuôn mẫu [ASSUMED].** Mẫu trình bày chính thức của Khoa (TL-04, TL-05) chưa được thu thập, nên mọi tài liệu
dùng một **khuôn mẫu chung giả định** của đồ án CNTT: trang bìa, lời cam đoan, lời cảm ơn, mục lục có chấm dẫn,
danh mục hình ảnh, các chương Mở đầu – Cơ sở lý thuyết – Phân tích và thiết kế – Cài đặt và thử nghiệm – Kết luận,
tài liệu tham khảo; bản PDF có dòng đầu trang "Đồ án tốt nghiệp - Khoa Công nghệ thông tin" và số trang trên mọi
trang. Phần khuôn mẫu này **giống hệt nhau ở mọi tài liệu** (chỉ thay tên đề tài, tên người, năm) — chính là phần
mà dịch vụ AI phải nhận ra là khuôn mẫu và không tính là trùng lặp. Khi có mẫu chính thức, chỉ cần thay khuôn mẫu
trong `tools/datagen/datagen/vocab.py` và sinh lại.

## 4.x.2. Kho 300 đề tài khóa cũ (DATA-02)

Tệp `seed-data/de-tai-kho.csv` gồm 300 đề tài, mỗi khóa từ K18 đến K22 đúng 60 đề tài, thuộc 8 cụm chủ đề: ứng
dụng web (WEB), ứng dụng di động (MOBILE), trí tuệ nhân tạo/học máy (AI_ML), Internet vạn vật (IOT), khoa học dữ
liệu (DU_LIEU), an toàn thông tin (AN_TOAN), ERP/hệ thống doanh nghiệp (ERP) và học tập số (HOC_TAP). Tệp đúng
định dạng import CSV kho đồ án (UTF-8 có BOM, dòng tiêu đề
`khoa,ten_de_tai,ma_so_sinh_vien,ho_ten_sinh_vien,ma_giang_vien,tu_khoa,diem`), nên được nạp bằng chính chức
năng "Import đồ án khóa cũ" của Bộ môn và đi qua luồng đánh chỉ mục `/ingest` như dữ liệu thật.

Bảng 4.x.1. Phân bố đề tài theo cụm chủ đề và khóa

| Cụm | K18 | K19 | K20 | K21 | K22 | Tổng |
|-----|----:|----:|----:|----:|----:|-----:|
| WEB | 8 | 7 | 8 | 6 | 8 | 37 |
| MOBILE | 7 | 9 | 9 | 7 | 7 | 39 |
| AI_ML | 9 | 5 | 7 | 8 | 9 | 38 |
| IOT | 8 | 9 | 6 | 5 | 9 | 37 |
| DU_LIEU | 5 | 7 | 7 | 9 | 8 | 36 |
| AN_TOAN | 6 | 7 | 6 | 9 | 10 | 38 |
| ERP | 9 | 9 | 8 | 7 | 3 | 36 |
| HOC_TAP | 8 | 7 | 9 | 9 | 6 | 39 |
| **Tổng** | **60** | **60** | **60** | **60** | **60** | **300** |

**Đề tài kinh điển lặp lại qua các khóa.** Giống kho đồ án thật, những bài toán quen thuộc (quản lý thư viện,
đặt lịch khám bệnh, giám sát nhà kính, quản lý kho hàng…) xuất hiện ở nhiều khóa. Mỗi cụm có 15 "đối tượng" nghiệp
vụ; 12 đối tượng đầu của mỗi cụm (96 đối tượng) được dùng trong kho, mỗi đối tượng lặp lại 3 lần (84 đối tượng)
hoặc 4 lần (12 đối tượng), mỗi lần ở một khóa khác với đơn vị ứng dụng, công nghệ và cách diễn đạt khác nhau,
nên 300 tên đề tài đều khác nhau. 3 đối tượng cuối của mỗi cụm (24 đối tượng) là **đối tượng dự trữ**, không bao
giờ xuất hiện trong kho.

**80 truy vấn tên đề tài có nhãn** (`seed-data/truy-van-ten-de-tai.csv`):

- 40 truy vấn `DIEN_DAT_LAI` — một đề tài có trong kho được viết lại (cách gọi đối tượng khác, động từ và sản
  phẩm đồng nghĩa, đơn vị viết tắt ↔ đầy đủ, đổi từ nối); không truy vấn nào trùng nguyên văn tên trong kho.
  Kỳ vọng: **có cảnh báo**, và đề tài gốc (cột `tieu_de_goc`) phải nằm trong danh sách đề tài tương tự.
  Ví dụ: "Sử dụng SQL Server để hạch toán thu chi doanh nghiệp cho công ty cổ phần Hoàng Long" ↔ đề tài gốc
  "Ứng dụng SQL Server trong quản lý kế toán tại công ty CP Hoàng Long".
- 40 truy vấn `CUNG_LINH_VUC` — đề tài cùng cụm chủ đề nhưng về một đối tượng dự trữ (không có trong kho), ví dụ
  "Xây dựng và triển khai giải pháp hỗ trợ phòng chống tấn công từ chối dịch vụ cho công ty cổ phần Thành Công sử
  dụng Suricata". Kỳ vọng: **không cảnh báo** — đây là các mẫu "âm tính khó" vì dùng chung từ vựng lĩnh vực.

Mỗi loại được chia 28 truy vấn `HIEU_CHINH` và 12 truy vấn `KIEM_CHUNG` (30% giữ lại).

## 4.x.3. Bộ 50 tài liệu với phổ trùng lặp chủ đích (DATA-03)

Thư mục `seed-data/tai-lieu/` chứa 25 cặp tài liệu `P01..P25-{A,B}`. Tài liệu **A** luôn là một đề tài trong kho
300 (tên đề tài, khóa, giảng viên hướng dẫn và sinh viên lấy từ đúng dòng kho đó); tài liệu **B** đóng vai trò bài
nộp cần kiểm tra. Có 8 cặp độ dài báo cáo cuối kỳ (55–62 đoạn nội dung) và 17 cặp độ dài đề cương (16–22 đoạn).
Mỗi đoạn nội dung gồm 2–5 câu hoàn chỉnh kết thúc bằng dấu chấm, để dịch vụ AI (so khớp ở mức câu) và bảng đối
chiếu dùng chung một đơn vị. Hai định dạng được xuất từ **cùng một danh sách đoạn** (python-docx cho DOCX,
reportlab với phông DejaVuSans cho PDF), không qua bước chuyển đổi, nên văn bản của một đoạn giống hệt nhau ở cả
hai định dạng.

Bảng 4.x.2. Bốn loại cặp tài liệu

| Loại | Số cặp | Cách tạo tài liệu B | Kỳ vọng |
|------|-------:|---------------------|---------|
| `CHEP_NGUYEN_VAN` | 7 | Đổi tên đề tài (cùng đối tượng, khác động từ/đơn vị); chép **nguyên văn** một dải đoạn liên tiếp của A, chiếm 40–60% nội dung B; phần còn lại tự viết về một đối tượng khác cùng cụm | Cảnh báo |
| `DIEN_DAT_LAI` | 7 | Cùng cách chọn dải đoạn nhưng **viết lại từng câu** (mẫu câu "anh em" với cấu trúc khác, từ đồng nghĩa, đảo thứ tự câu sau câu đầu của đoạn) | Cảnh báo |
| `CUNG_LINH_VUC` | 6 | B viết về một đối tượng dự trữ cùng cụm với A; không chép, không diễn đạt lại đoạn nào | Không cảnh báo |
| `KHONG_LIEN_QUAN` | 5 | B viết về một đối tượng thuộc cụm chủ đề khác | Không cảnh báo |

Mỗi loại có 2 cặp thuộc tập `KIEM_CHUNG` (tổng 8 cặp, 32%); 17 cặp còn lại thuộc tập `HIEU_CHINH`. Định dạng
A/B luân phiên trong từng loại, nên loại nào cũng có cả chiều DOCX→PDF và PDF→DOCX, và mỗi chiều có một cặp
kiểm chứng.

Bảng 4.x.3. Danh sách 25 cặp tài liệu (sinh từ `seed-data/manifest.json`; "Tỷ lệ" = số ký tự của các đoạn chép
hoặc diễn đạt lại từ A / tổng số ký tự nội dung của B)

| Mã cặp | Loại | Tập | Độ dài | Tệp A | Tệp B | Đề tài A (khóa) | Tỷ lệ chép / diễn đạt lại | Kỳ vọng cảnh báo |
|--------|------|-----|--------|-------|-------|-----------------|--------------------------:|------------------|
| P01 | CHEP_NGUYEN_VAN | HIEU_CHINH | DE_CUONG | `P01-A.docx` | `P01-B.pdf` | Phát triển mô hình thống kê điểm số của người học tại trường THCS Chu Văn An sử dụng Metabase (K21) | 50,3% | Có |
| P02 | CHEP_NGUYEN_VAN | HIEU_CHINH | DE_CUONG | `P02-A.pdf` | `P02-B.docx` | Ứng dụng PyTorch trong giải đáp thắc mắc tuyển sinh qua trợ lý ảo tại trung tâm đào tạo ngoại ngữ An Khang (K22) | 48,0% | Có |
| P03 | CHEP_NGUYEN_VAN | KIEM_CHUNG | BAO_CAO | `P03-A.docx` | `P03-B.pdf` | Ứng dụng Swift trong điểm danh sinh viên tại trường cao đẳng nghề Hà Giang (K18) | 49,3% | Có |
| P04 | CHEP_NGUYEN_VAN | HIEU_CHINH | DE_CUONG | `P04-A.pdf` | `P04-B.docx` | Xây dựng và triển khai website tổ chức lớp học qua mạng cho trung tâm giáo dục thường xuyên Đồng Hỷ (K19) | 44,9% | Có |
| P05 | CHEP_NGUYEN_VAN | HIEU_CHINH | BAO_CAO | `P05-A.docx` | `P05-B.pdf` | Phát triển công cụ hỗ trợ phát hiện thư điện tử lừa đảo tại DNTN Thành Công trên nền tảng Wazuh (K20) | 44,8% | Có |
| P06 | CHEP_NGUYEN_VAN | KIEM_CHUNG | DE_CUONG | `P06-A.pdf` | `P06-B.docx` | Nghiên cứu và phát triển hệ thống IoT hỗ trợ quan trắc chất lượng không khí tại ủy ban nhân dân xã Gia Sàng (K19) | 46,9% | Có |
| P07 | CHEP_NGUYEN_VAN | HIEU_CHINH | DE_CUONG | `P07-A.docx` | `P07-B.pdf` | Phát triển hệ thống thông tin tiếp nhận hồ sơ xét tuyển qua mạng tại trung tâm giáo dục thường xuyên Đại Từ (K22) | 46,1% | Có |
| P08 | DIEN_DAT_LAI | HIEU_CHINH | DE_CUONG | `P08-A.docx` | `P08-B.pdf` | Xây dựng và triển khai website chia sẻ bài giảng video tại trường THCS Quang Trung (K20) | 45,1% | Có |
| P09 | DIEN_DAT_LAI | KIEM_CHUNG | DE_CUONG | `P09-A.pdf` | `P09-B.docx` | Thiết kế và xây dựng ứng dụng hỗ trợ quản lý quan hệ khách hàng cho công ty TNHH Trường Thịnh (K21) | 47,7% | Có |
| P10 | DIEN_DAT_LAI | KIEM_CHUNG | DE_CUONG | `P10-A.docx` | `P10-B.pdf` | Thiết kế và xây dựng công cụ hỗ trợ nhận diện phần mềm độc hại cho công ty trách nhiệm hữu hạn Phúc An trên nền tảng Wazuh (K18) | 49,8% | Có |
| P11 | DIEN_DAT_LAI | HIEU_CHINH | DE_CUONG | `P11-A.pdf` | `P11-B.docx` | Nghiên cứu và phát triển hệ thống hỗ trợ ôn tập thi trung học phổ thông tại trường CĐ nghề Tuyên Quang (K18) | 49,7% | Có |
| P12 | DIEN_DAT_LAI | HIEU_CHINH | BAO_CAO | `P12-A.docx` | `P12-B.pdf` | Ứng dụng Node-RED trong hướng dẫn chỗ đỗ xe còn trống cho bến xe liên tỉnh Tuyên Quang (K20) | 42,0% | Có |
| P13 | DIEN_DAT_LAI | HIEU_CHINH | DE_CUONG | `P13-A.pdf` | `P13-B.docx` | Ứng dụng PyTorch trong đọc biển kiểm soát phương tiện cho bãi đỗ xe Thành Công (K19) | 50,0% | Có |
| P14 | DIEN_DAT_LAI | HIEU_CHINH | BAO_CAO | `P14-A.docx` | `P14-B.pdf` | Xây dựng ứng dụng Android hỗ trợ đặt và giao đồ ăn cho cơ sở lưu trú An Khang (K22) | 46,8% | Có |
| P15 | CUNG_LINH_VUC | HIEU_CHINH | BAO_CAO | `P15-A.docx` | `P15-B.pdf` | Xây dựng ứng dụng điện thoại hẹn giờ khám chữa bệnh tại bệnh viện tuyến tỉnh Thái Nguyên (K20) | 0,0% | Không |
| P16 | CUNG_LINH_VUC | HIEU_CHINH | DE_CUONG | `P16-A.pdf` | `P16-B.docx` | Ứng dụng ReactJS trong quản lý thư viện tại trung tâm GDTX Phú Lương (K22) | 0,0% | Không |
| P17 | CUNG_LINH_VUC | HIEU_CHINH | DE_CUONG | `P17-A.docx` | `P17-B.pdf` | Phát triển mô hình học máy chấm công qua khuôn mặt tại trung tâm GDTX Phổ Yên sử dụng YOLOv8 (K21) | 0,0% | Không |
| P18 | CUNG_LINH_VUC | KIEM_CHUNG | DE_CUONG | `P18-A.pdf` | `P18-B.docx` | Ứng dụng Keycloak trong xác thực hai lớp tại doanh nghiệp tư nhân Đại Phát (K21) | 0,0% | Không |
| P19 | CUNG_LINH_VUC | KIEM_CHUNG | BAO_CAO | `P19-A.docx` | `P19-B.pdf` | Nghiên cứu và phát triển phân hệ ERP theo dõi thiết bị và khấu hao tài sản tại sở thông tin và truyền thông tỉnh Lạng Sơn (K18) | 0,0% | Không |
| P20 | CUNG_LINH_VUC | HIEU_CHINH | DE_CUONG | `P20-A.pdf` | `P20-B.docx` | Thiết kế và xây dựng hệ thống báo cáo tích hợp dữ liệu kinh doanh cho chuỗi cửa hàng Nam Việt sử dụng Metabase (K19) | 0,0% | Không |
| P21 | KHONG_LIEN_QUAN | KIEM_CHUNG | BAO_CAO | `P21-A.docx` | `P21-B.pdf` | Thiết kế và cài đặt bộ điều khiển tự động hóa thiết bị gia đình cho cư dân thành phố Bắc Giang trên nền tảng Raspberry Pi (K20) | 0,0% | Không |
| P22 | KHONG_LIEN_QUAN | KIEM_CHUNG | DE_CUONG | `P22-A.pdf` | `P22-B.docx` | Ứng dụng Metabase trong trực quan hóa báo cáo điều hành cho công ty CP Hưng Thịnh (K21) | 0,0% | Không |
| P23 | KHONG_LIEN_QUAN | HIEU_CHINH | DE_CUONG | `P23-A.docx` | `P23-B.pdf` | Xây dựng và triển khai hệ thống thu ngân và lập hóa đơn bán lẻ cho cửa hàng tiện lợi Minh Phát (K19) | 0,0% | Không |
| P24 | KHONG_LIEN_QUAN | HIEU_CHINH | DE_CUONG | `P24-A.pdf` | `P24-B.docx` | Nghiên cứu và phát triển ứng dụng web đặt chỗ lưu trú trực tuyến tại khu du lịch Võ Nhai (K18) | 0,0% | Không |
| P25 | KHONG_LIEN_QUAN | HIEU_CHINH | BAO_CAO | `P25-A.docx` | `P25-B.pdf` | Ứng dụng TensorFlow trong chẩn đoán bệnh cây qua ảnh lá cho vùng trồng chè Gia Sàng (K22) | 0,0% | Không |

**Nguồn gốc từng đoạn.** Trong `manifest.json`, mỗi đoạn nội dung của B mang trường `nguon`: `null` (đoạn tự
viết) hoặc `{"nguon": "A", "chi_so": i, "kieu": "NGUYEN_VAN" | "DIEN_DAT"}` (chép nguyên văn / diễn đạt lại từ
đoạn thứ `i` của A). Nhờ đó, kết quả của dịch vụ AI (câu nào bị đánh dấu, trỏ về đồ án nào) được đối chiếu tự
động với đáp án ở mức câu, không cần chấm tay.

## 4.x.4. Kiểm tra chất lượng bộ dữ liệu

Lệnh `python -m datagen check` tự kiểm tra bộ dữ liệu trước khi dùng; tất cả các kiểm tra sau đều đạt:

- CSV kho qua **mọi quy tắc import** đã tài liệu hóa: UTF-8, đúng dòng tiêu đề, trường bắt buộc, độ dài tối đa,
  dạng NFC, điểm 0–10, mã giảng viên tồn tại, không trùng (khóa, tên đề tài), ≤ 2 MB và ≤ 2000 dòng; không ô
  nào bắt đầu bằng ký tự công thức.
- **Round-trip trích xuất:** dùng đúng logic trích xuất của Web API (python-docx cho DOCX, PyMuPDF
  `page.get_text()` cho PDF, chuẩn hóa NFC; hàm trích xuất PDF mới ngày 09/11/2026, dựng lại dấu cách từ vị trí
  ký tự, cho văn bản giống hệt trên 25 PDF này), mọi đoạn nội dung của cả 50 tệp đều còn nguyên văn; mọi tệp PDF đều
  lặp dòng đầu trang ít nhất 3 lần (tình huống dịch vụ AI phải lọc bỏ).
- **Thống kê trùng lặp** bằng hệ số Jaccard trên tập 4-gram âm tiết ở mức câu:

Bảng 4.x.4. Thống kê trùng lặp theo loại cặp

| Loại | Cặp | Câu của B | Tỷ lệ chép / diễn đạt lại | Chỉ số kiểm tra | Yêu cầu |
|------|----:|----------:|--------------------------:|-----------------|---------|
| CHEP_NGUYEN_VAN | 7 | 628 | 44,8% – 50,3% | 100% câu chép trùng khớp hoàn toàn (Jaccard = 1,0) với câu nguồn | Tỷ lệ 40–60%, câu chép = 1,0 |
| DIEN_DAT_LAI | 7 | 578 | 42,1% – 50,0% | 100% câu diễn đạt lại có Jaccard < 0,5 với câu nguồn | ≥ 70% câu < 0,5 |
| CUNG_LINH_VUC | 6 | 554 | 0% | 0% – 3,3% câu của B có Jaccard ≥ 0,5 với một câu bất kỳ của A | < 5% |
| KHONG_LIEN_QUAN | 5 | 490 | 0% | 0% câu của B có Jaccard ≥ 0,5 với A | < 5% |

Kết quả cho thấy phổ trùng lặp đúng như thiết kế: cặp chép nguyên văn trùng tuyệt đối về mặt từ ngữ; cặp diễn
đạt lại **gần như không còn trùng từ ngữ** (nên chỉ tín hiệu ngữ nghĩa mới phát hiện được, đúng mục đích thử
thách mô hình embedding); còn các cặp cùng lĩnh vực và không liên quan không có câu nào gần trùng đáng kể. Ngoài
ra, chỉ 3,6% câu tự viết của B có Jaccard ≥ 0,5 với câu của *bất kỳ* tài liệu A nào trong bộ — đây là các câu
văn phong chung như "Hệ thống kiểm tra tính hợp lệ của … trước khi lưu", vốn cũng gặp trong đồ án thật.

- **Tính tất định:** bộ sinh dùng hạt giống cố định `20261116`; sinh lại vào thư mục tạm cho kết quả giống từng
  byte (CSV, manifest và cả 50 tệp DOCX/PDF).

## 4.x.5. Nguyên tắc sử dụng tập giữ lại

- Chỉ tập `HIEU_CHINH` (17 cặp tài liệu, 56 truy vấn tên đề tài) được dùng để chọn ngưỡng cảnh báo.
- Tập `KIEM_CHUNG` (8 cặp tài liệu, 24 truy vấn) **không bao giờ** được dùng khi hiệu chỉnh; nó chỉ được chạy một
  lần sau khi ngưỡng đã chốt, và kết quả trên tập này là con số được báo cáo trong bảng kết quả kiểm chứng.

## 4.x.6. Tái tạo bộ dữ liệu

```bash
uv --directory tools/datagen sync --frozen
uv --directory tools/datagen run python -m datagen all --out ../../seed-data
uv --directory tools/datagen run python -m datagen check --data ../../seed-data
```
