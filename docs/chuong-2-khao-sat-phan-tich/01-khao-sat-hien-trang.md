# Chương 2. Khảo sát & phân tích

## 2.1. Khảo sát hiện trạng

> **Mã PI:** 1.1 — **Yêu cầu:** ANLS-01

### 2.1.1. Mục tiêu và phương pháp khảo sát

Mục tiêu của khảo sát là thu thập bằng chứng thực tế về quy trình quản lý đồ án/khóa luận tốt nghiệp hiện tại của Khoa Công nghệ thông tin (đăng ký đề tài, duyệt đề cương, theo dõi tiến độ, nộp báo cáo và tổ chức bảo vệ, lưu trữ đồ án), làm cơ sở cho sơ đồ BPMN AS-IS (§2.2), bảng yêu cầu chức năng/phi chức năng (§2.3–2.4) và một phần thiết kế dữ liệu (§3.1–3.2).

Phương pháp khảo sát gồm ba nguồn kết hợp (D-01):

1. **Phỏng vấn bán cấu trúc** từng vai trò (Bộ môn/Văn phòng Khoa, Giảng viên, Sinh viên), 20–30 phút mỗi người, theo bộ câu hỏi tại [Phụ lục B — Bộ câu hỏi phỏng vấn](khao-sat/bo-cau-hoi-phong-van.md).
2. **Phiếu khảo sát định lượng** bổ sung (thang Likert 1–5, câu hỏi chọn kênh/công cụ) tại [Phụ lục C — Phiếu khảo sát](khao-sat/phieu-khao-sat.md).
3. **Thu thập tài liệu gốc** (quy chế, biểu mẫu, mẫu chính thức, đồ án cũ) theo danh mục tại [`tai-lieu-goc/README.md`](../../tai-lieu-goc/README.md).

Kế hoạch chi tiết (lịch phỏng vấn, đối tượng, nguyên tắc ẩn danh) nằm tại [Phụ lục A — Kế hoạch khảo sát](khao-sat/ke-hoach-khao-sat.md). Mỗi buổi phỏng vấn được ghi lại theo mẫu tại [Phụ lục D — Mẫu biên bản phỏng vấn](khao-sat/mau-bien-ban-phong-van.md).

> GIẢ ĐỊNH — chờ xác nhận: tại thời điểm viết mục này (T1, 28/09/2026), **chưa có buổi phỏng vấn nào diễn ra** — lịch phỏng vấn ở Phụ lục A vẫn còn để trống ngày/giờ (D-01, D-02). Toàn bộ nội dung §2.1.3–2.1.6 dưới đây là bản nháp dựa trên suy luận thực tế phổ biến ở các khoa CNTT có quy trình quản lý đồ án tương tự (đăng ký thủ công qua email/Excel, duyệt đề cương bằng giấy/email, chấm điểm bằng phiếu giấy). Mỗi phát hiện được gắn mã Q-ID của câu hỏi phỏng vấn sẽ xác nhận hoặc bác bỏ nó; việc đối chiếu với biên bản thật (`BB-*`) hoặc tài liệu gốc (`TL-*`) và gỡ nhãn thuộc plan 01-07.

### 2.1.2. Đối tượng khảo sát

| Mã | Vai trò | Hình thức | Biên bản | Trạng thái |
|----|---------|-----------|----------|------------|
| BM-01 | Đại diện Bộ môn / Văn phòng Khoa | Trực tiếp hoặc trực tuyến | — | Chưa phỏng vấn |
| GV-01 | Giảng viên hướng dẫn | Trực tiếp hoặc trực tuyến | — | Chưa phỏng vấn |
| GV-02 | Giảng viên hướng dẫn / thành viên hội đồng | Trực tiếp hoặc trực tuyến | — | Chưa phỏng vấn |
| SV-01 | Sinh viên đang làm đồ án | Trực tiếp hoặc trực tuyến | — | Chưa phỏng vấn |
| SV-02 | Sinh viên đã bảo vệ khóa trước | Trực tiếp hoặc trực tuyến | — | Chưa phỏng vấn |
| SV-03 | Sinh viên sắp đăng ký đồ án | Trực tiếp hoặc trực tuyến | — | Chưa phỏng vấn |

Chi tiết tiêu chí chọn và lịch dự kiến xem [Phụ lục A, mục A.2–A.3](khao-sat/ke-hoach-khao-sat.md). Nguyên tắc ẩn danh (chỉ ghi mã vai trò, không ghi tên/số điện thoại/email) áp dụng cho toàn bộ mục này và các biên bản liên quan (Phụ lục A, mục A.5).

### 2.1.3. Hiện trạng quy trình quản lý đồ án

> GIẢ ĐỊNH — chờ xác nhận: mọi mô tả AS-IS dưới đây là bản nháp trước phỏng vấn thật. Cột "Nguồn xác nhận" ghi mã câu hỏi (Q-ID) tại Phụ lục B sẽ được dùng để xác nhận hoặc điều chỉnh phát hiện này.

#### 2.1.3.1. Đăng ký đề tài

Theo suy luận thực tế phổ biến, GV đề xuất đề tài rời rạc qua email/Excel gửi cho Bộ môn; SV đăng ký qua phiếu giấy hoặc một biểu mẫu trực tuyến không liên kết với dữ liệu đề tài đã đề xuất (Google Form độc lập). Bộ môn tổng hợp thủ công vào một bảng Excel dùng chung, họp xét duyệt định kỳ và phân công GVHD dựa trên kinh nghiệm cá nhân, không có công cụ kiểm tra tải giảng viên hay trùng lặp đề tài tự động.

| Mã | Phát hiện | Nguồn xác nhận | Trạng thái |
|----|-----------|------------------|------------|
| KS-DT-01 | GV gửi danh sách đề tài đề xuất cho Bộ môn qua email/Excel, không có kho đề tài tập trung | Q-BM-10, Q-GV-01 | GIẢ ĐỊNH — chờ xác nhận |
| KS-DT-02 | SV đăng ký đề tài qua phiếu giấy hoặc biểu mẫu trực tuyến rời rạc, không đối chiếu tự động với danh sách đề tài đã duyệt | Q-SV-01, Q-BM-02 | GIẢ ĐỊNH — chờ xác nhận |
| KS-DT-03 | Bộ môn tổng hợp và xét duyệt đề tài thủ công trong cuộc họp định kỳ; không có bước kiểm tra trùng tên đề tài tự động | Q-BM-02, Q-BM-12 | GIẢ ĐỊNH — chờ xác nhận |
| KS-DT-04 | Phân công GVHD dựa trên kinh nghiệm cá nhân của Bộ môn, không theo dõi tải giảng viên (số SV/đề tài đang hướng dẫn) một cách hệ thống | Q-BM-03 | GIẢ ĐỊNH — chờ xác nhận |

#### 2.1.3.2. Đề cương

SV nộp file đề cương qua email hoặc Zalo cho GVHD; không có cơ chế quản lý phiên bản tập trung nên khó biết bản nào là bản mới nhất. GVHD đọc, góp ý bằng cách viết tay lên bản in hoặc trả lời email, và quy trình lặp lại cho đến khi đạt. Chưa có bước kiểm tra trùng lặp nội dung đề cương giữa các SV trong khoa — chỉ dựa vào việc GVHD tự đọc và nhớ các đề cương khác đã từng duyệt.

| Mã | Phát hiện | Nguồn xác nhận | Trạng thái |
|----|-----------|------------------|------------|
| KS-DC-01 | SV nộp đề cương qua email/Zalo, không có quản lý phiên bản tập trung | Q-SV-03, Q-GV-05 | GIẢ ĐỊNH — chờ xác nhận |
| KS-DC-02 | GVHD góp ý viết tay hoặc qua email; đề cương thường phải chỉnh sửa nhiều vòng trước khi được duyệt | Q-GV-04, Q-SV-03 | GIẢ ĐỊNH — chờ xác nhận |
| KS-DC-03 | Không có bước kiểm tra trùng lặp nội dung đề cương trong phạm vi khoa, chỉ dựa vào việc GVHD tự đọc thủ công | Q-GV-07, Q-GV-09 | GIẢ ĐỊNH — chờ xác nhận |
| KS-DC-04 | Chưa rõ Bộ môn có xác nhận thêm một bước duyệt đề cương ngoài GVHD hay không | Q-BM-04 | GIẢ ĐỊNH — chờ xác nhận |

#### 2.1.3.3. Theo dõi tiến độ

Không có mốc báo cáo tiến độ chung cho cả đợt đồ án; mỗi GVHD tự quy định tần suất và nội dung báo cáo cho SV của mình. Trao đổi tiến độ diễn ra qua gặp trực tiếp hoặc nhắn tin (Zalo), không lưu vết văn bản tập trung. Bộ môn không có số liệu tổng hợp tiến độ của toàn khóa nên khó phát hiện sớm SV bị trễ hạn.

| Mã | Phát hiện | Nguồn xác nhận | Trạng thái |
|----|-----------|------------------|------------|
| KS-TD-01 | SV báo cáo tiến độ không theo mốc chung của đợt; tần suất và nội dung do từng GVHD tự quy định | Q-GV-06, Q-SV-05 | GIẢ ĐỊNH — chờ xác nhận |
| KS-TD-02 | Trao đổi tiến độ chủ yếu qua gặp trực tiếp/Zalo, không lưu vết văn bản tập trung | Q-BM-05, Q-GV-12 | GIẢ ĐỊNH — chờ xác nhận |
| KS-TD-03 | Bộ môn không có số liệu tổng hợp tiến độ toàn khóa, khó phát hiện sớm SV trễ hạn | Q-BM-05 | GIẢ ĐỊNH — chờ xác nhận |

#### 2.1.3.4. Nộp báo cáo và bảo vệ

SV nộp báo cáo cuối cùng dưới cả bản cứng và bản mềm, định dạng chưa thống nhất. Kiểm tra trùng lặp/đạo văn hiện chỉ áp dụng phần mềm Turnitin theo quy định của trường, không có kiểm tra bổ sung trong phạm vi riêng của khoa. Hội đồng bảo vệ được Khoa ra quyết định thành lập và xếp lịch thủ công, thông báo cho GV/SV qua bảng tin hoặc email. Việc chấm điểm dùng phiếu giấy cho từng thành viên hội đồng, thư ký hội đồng tổng hợp điểm thủ công.

| Mã | Phát hiện | Nguồn xác nhận | Trạng thái |
|----|-----------|------------------|------------|
| KS-BV-01 | SV nộp báo cáo cuối cùng cả bản cứng và bản mềm, định dạng chưa thống nhất | Q-BM-06, Q-SV-06 | GIẢ ĐỊNH — chờ xác nhận |
| KS-BV-02 | Kiểm tra trùng lặp/đạo văn hiện chỉ áp dụng Turnitin theo quy định của trường, chưa có kiểm tra bổ sung trong phạm vi riêng của khoa | Q-BM-06, Q-GV-07 | GIẢ ĐỊNH — chờ xác nhận |
| KS-BV-03 | Hội đồng bảo vệ được thành lập và xếp lịch thủ công; thông báo cho GV/SV qua bảng tin hoặc email | Q-BM-07, Q-SV-07 | GIẢ ĐỊNH — chờ xác nhận |
| KS-BV-04 | Chấm điểm dùng phiếu giấy cho từng thành viên hội đồng; thư ký tổng hợp điểm thủ công, dễ sai sót | Q-BM-08, Q-GV-08 | GIẢ ĐỊNH — chờ xác nhận |

#### 2.1.3.5. Lưu trữ đồ án

Đồ án đã hoàn thành được lưu bản cứng tại văn phòng khoa/thư viện và bản mềm rải rác trên ổ dùng chung, không có cơ chế tìm kiếm theo từ khóa/GVHD/khóa học tập trung. Việc tra cứu đồ án khóa trước (để tham khảo hoặc để Bộ môn đối chiếu tránh trùng đề tài) hoàn toàn thủ công, phụ thuộc trí nhớ hoặc hỏi trực tiếp người quản lý qua các năm.

| Mã | Phát hiện | Nguồn xác nhận | Trạng thái |
|----|-----------|------------------|------------|
| KS-KHO-01 | Đồ án lưu bản cứng tại văn phòng khoa/thư viện, bản mềm rải rác trên ổ dùng chung | Q-BM-09, Q-SV-08 | GIẢ ĐỊNH — chờ xác nhận |
| KS-KHO-02 | Không có cơ chế tìm kiếm theo từ khóa/GVHD/khóa học tập trung; khó tra cứu đề tài cũ để tránh trùng | Q-BM-09, Q-SV-08 | GIẢ ĐỊNH — chờ xác nhận |
| KS-KHO-03 | Dữ liệu các khóa cũ phân tán, phụ thuộc người quản lý qua các năm, không có bàn giao hệ thống hóa | Q-BM-09 | GIẢ ĐỊNH — chờ xác nhận |

### 2.1.4. Các biểu mẫu dữ liệu

Bảy biểu mẫu dưới đây là các biểu mẫu giấy/Excel đang (giả định) được dùng ở từng bước quy trình, hoặc — với MAU-03 — được suy ra trực tiếp từ tài liệu đề cương gốc đã có trong repo. Cột "Thực thể dự kiến" dùng tên lớp PascalCase theo quy ước tại [`docs/README.md` §6](../README.md).

#### MAU-01 – Phiếu đề xuất đề tài

Mục đích: GV (hoặc SV tự đề xuất) khai báo một đề tài mới để Bộ môn xét duyệt. Người điền: Giảng viên hoặc Sinh viên. Thời điểm: đầu đợt đồ án, khi Bộ môn mở đăng ký.

| Trường dữ liệu | Kiểu dữ liệu | Bắt buộc | Ràng buộc / ghi chú | Thực thể dự kiến |
|---|---|---|---|---|
| Vai trò người đề xuất | Enum (Giảng viên/Sinh viên) | Có | Xác định luồng duyệt tiếp theo | DeTai |
| Tên đề tài | Chuỗi | Có | Tối đa ~200 ký tự; là đầu vào kiểm tra trùng ngữ nghĩa (AISV-03) | DeTai |
| Mô tả/tóm tắt đề tài | Văn bản dài | Có | Vài đoạn mô tả mục tiêu, phạm vi | DeTai |
| Lĩnh vực/hướng đề tài | Chuỗi hoặc danh mục | Không | Hỗ trợ lọc, gợi ý sau này | DeTai |
| Số lượng SV nhận | Số nguyên | Có | Mặc định 1 theo ràng buộc 1 SV : 1 đề tài | DeTai |
| Ngày đề xuất | Ngày | Có | Tự sinh khi tạo bản ghi | DeTai |

Nguồn: TL-03 (Phiếu đề xuất/đăng ký đề tài — GIẢ ĐỊNH — chờ xác nhận, chưa thu thập được bản mẫu thật, xem `tai-lieu-goc/README.md`).

#### MAU-02 – Phiếu đăng ký đề tài

Mục đích: SV đăng ký nhận một đề tài đã được duyệt và còn trống. Người điền: Sinh viên. Thời điểm: sau khi danh sách đề tài đã duyệt được công bố.

| Trường dữ liệu | Kiểu dữ liệu | Bắt buộc | Ràng buộc / ghi chú | Thực thể dự kiến |
|---|---|---|---|---|
| Mã số sinh viên | Chuỗi | Có | Khóa tra cứu sinh viên | DeTai |
| Đề tài đăng ký | Tham chiếu DeTai | Có | Chỉ chọn được đề tài trạng thái "Đã duyệt", chưa có SV | DeTai |
| Ngày đăng ký | Ngày | Có | Tự sinh khi tạo bản ghi | DeTai |
| Xác nhận của GVHD (nếu có) | Boolean/ghi chú | Không | Một số trường hợp GVHD xác nhận trước khi Bộ môn duyệt | DeTai |

Nguồn: TL-03 (GIẢ ĐỊNH — chờ xác nhận, xem `tai-lieu-goc/README.md`).

#### MAU-03 – Đề cương đồ án/khóa luận tốt nghiệp

Mục đích: SV trình bày đề tài, mục tiêu, phạm vi và tiến độ dự kiến để GVHD/Bộ môn duyệt trước khi bắt đầu thực hiện. Người điền: Sinh viên (phối hợp cùng GVHD). Thời điểm: sau khi được phân công GVHD, đầu đợt thực hiện đồ án.

Biểu mẫu này **không phải giả định** — cấu trúc 9 mục dưới đây lấy trực tiếp từ tài liệu đề cương gốc đã nộp trong repo (`H01.DTC235200036.NguyenThiMaiAnh.docx`, đọc bằng `pandoc -t plain`), là một thực thể mẫu chính thức của Khoa CNTT:

| Trường dữ liệu | Kiểu dữ liệu | Bắt buộc | Ràng buộc / ghi chú | Thực thể dự kiến |
|---|---|---|---|---|
| Thông tin sinh viên (mục 1) | Nhóm trường (họ tên, MSSV, lớp) | Có | Lấy từ hồ sơ SV đã đăng nhập, không nhập tay | DeCuong |
| Thông tin GVHD (mục 2) | Nhóm trường (họ tên, khoa, bộ môn) | Có | Lấy từ đề tài đã phân công (TB-DT-14) | DeCuong |
| Tên đề tài (mục 3) | Chuỗi | Có | Đồng bộ với DeTai đã đăng ký, không nhập lại | DeCuong |
| Thời gian thực hiện (mục 4) | Khoảng ngày | Có | Theo mốc của đợt đồ án hiện tại | DeCuong |
| Mục tiêu (mục 5) | Danh sách gạch đầu dòng | Có | Nội dung là văn bản chính được kiểm tra trùng lặp (AISV-04) | DeCuong |
| Bảng CLO/mã PI liên quan (mục 6) | Bảng | Có | Đối chiếu tiêu chí chấm; cấu trúc cột theo bảng gốc (Mã CLO, % CLO, Mã PI, % PI) | DeCuong |
| Yêu cầu về sản phẩm — chi tiết theo PI (mục 7b) | Bảng | Có | Mỗi dòng ứng một mã PI, nội dung là văn bản kiểm tra trùng lặp | DeCuong |
| Cấu trúc quyển báo cáo (mục 8) | Danh sách chương | Có | 4 chương cố định theo mẫu trường | DeCuong |
| Tiến độ thực hiện (mục 9) | Bảng (STT, thời gian, công việc, kết quả dự kiến) | Có | 10 tuần theo lịch đợt đồ án | BaoCaoTienDo (liên kết) |

Nguồn: `H01.DTC235200036.NguyenThiMaiAnh.docx`, mục 1–9 (tài liệu gốc, không phải giả định). **Lưu ý bảo mật:** số điện thoại và email cá nhân trong tài liệu gốc (mục 1, 2) không được sao chép vào bất kỳ tài liệu nào của repo — chỉ tham chiếu cấu trúc mục, không trích dẫn giá trị.

#### MAU-04 – Báo cáo tiến độ và nhận xét

Mục đích: SV báo cáo công việc đã thực hiện theo từng mốc; GVHD nhận xét và đánh giá. Người điền: Sinh viên (nội dung), Giảng viên (nhận xét). Thời điểm: theo các mốc tiến độ của đợt.

| Trường dữ liệu | Kiểu dữ liệu | Bắt buộc | Ràng buộc / ghi chú | Thực thể dự kiến |
|---|---|---|---|---|
| Mốc báo cáo | Tham chiếu mốc đợt | Có | Do Bộ môn thiết lập trước (PROG-01) | BaoCaoTienDo |
| Nội dung đã thực hiện | Văn bản dài | Có | Mô tả công việc trong kỳ | BaoCaoTienDo |
| File đính kèm | Tệp (DOCX/PDF) | Không | Tùy chọn, minh chứng công việc | BaoCaoTienDo |
| Nhận xét của GVHD | Văn bản dài | Không | Điền sau khi SV nộp | BaoCaoTienDo |
| Đánh giá | Enum (Đạt/Chưa đạt/Trễ mốc) | Không | GVHD hoặc hệ thống gắn cờ khi quá hạn (PROG-03) | BaoCaoTienDo |

Nguồn: TL-06 (Phiếu nhận xét của GVHD / báo cáo tiến độ — GIẢ ĐỊNH — chờ xác nhận, xem `tai-lieu-goc/README.md`).

#### MAU-05 – Phiếu chấm điểm bảo vệ

Mục đích: từng thành viên hội đồng chấm điểm và nhận xét báo cáo của SV trong buổi bảo vệ. Người điền: Giảng viên (thành viên hội đồng). Thời điểm: trong/ngay sau buổi bảo vệ.

| Trường dữ liệu | Kiểu dữ liệu | Bắt buộc | Ràng buộc / ghi chú | Thực thể dự kiến |
|---|---|---|---|---|
| Mã hội đồng / buổi bảo vệ | Tham chiếu HoiDong | Có | Gắn với lịch đã xếp (DEFN-02) | DiemBaoVe |
| Sinh viên được chấm | Tham chiếu SV | Có | Một phiếu ứng với một SV | DiemBaoVe |
| Giảng viên chấm | Tham chiếu GV (thành viên hội đồng) | Có | Chỉ GV trong hội đồng đó được chấm (DEFN-03) | DiemBaoVe |
| Tiêu chí điểm (nội dung, hình thức, trình bày/trả lời) | Nhóm điểm thành phần | Có | Số tiêu chí cụ thể — GIẢ ĐỊNH — chờ xác nhận (Q-BM-08) | DiemBaoVe |
| Điểm tổng của thành viên | Số thập phân | Có | Trong khoảng 0–10 | DiemBaoVe |
| Nhận xét | Văn bản dài | Không | Ghi chú của GV chấm | DiemBaoVe |

Nguồn: TL-07 (Phiếu chấm điểm bảo vệ — GIẢ ĐỊNH — chờ xác nhận, xem `tai-lieu-goc/README.md`).

#### MAU-06 – Quyết định/biên bản hội đồng và lịch bảo vệ

Mục đích: Bộ môn/Khoa thành lập hội đồng chấm bảo vệ và xếp lịch cho một nhóm SV. Người điền: Bộ môn/Văn phòng Khoa. Thời điểm: trước đợt bảo vệ.

| Trường dữ liệu | Kiểu dữ liệu | Bắt buộc | Ràng buộc / ghi chú | Thực thể dự kiến |
|---|---|---|---|---|
| Mã hội đồng | Chuỗi/tự sinh | Có | Định danh nội bộ | HoiDong |
| Danh sách thành viên hội đồng | Danh sách GV + vai trò (chủ tịch/thư ký/ủy viên) | Có | Chỉ GV mới được chọn làm thành viên (DEFN-02) | HoiDong |
| Danh sách sinh viên bảo vệ | Danh sách tham chiếu SV | Có | Mỗi SV chỉ thuộc một hội đồng cho đợt đó | HoiDong |
| Ngày, giờ, phòng | Ngày giờ + chuỗi | Có | Dùng để thông báo in-app (NOTF-01) | HoiDong |
| Ghi chú | Văn bản | Không | — | HoiDong |

Nguồn: TL-08 (Biên bản hội đồng / quyết định thành lập hội đồng, lịch bảo vệ mẫu — GIẢ ĐỊNH — chờ xác nhận, xem `tai-lieu-goc/README.md`).

#### MAU-07 – Hồ sơ lưu trữ đồ án

Mục đích: ghi nhận một đồ án đã hoàn thành vào kho dữ liệu của khoa để tra cứu về sau. Người điền: Hệ thống tự sinh khi Bộ môn chốt kết quả, hoặc Bộ môn nhập tay khi import đồ án khóa cũ. Thời điểm: sau khi có kết quả bảo vệ cuối cùng, hoặc khi nhập liệu hồi cố.

| Trường dữ liệu | Kiểu dữ liệu | Bắt buộc | Ràng buộc / ghi chú | Thực thể dự kiến |
|---|---|---|---|---|
| Khóa học | Chuỗi/số | Có | Dùng để lọc trong kho (REPO-02) | DoAnKho |
| Tên đề tài | Chuỗi | Có | Đồng bộ từ DeTai | DoAnKho |
| Sinh viên thực hiện | Tham chiếu SV | Có | — | DoAnKho |
| GVHD | Tham chiếu GV | Có | — | DoAnKho |
| Từ khóa | Danh sách chuỗi | Không | Hỗ trợ tìm kiếm (REPO-02) | DoAnKho |
| Điểm bảo vệ | Số thập phân | Không | Đồng bộ từ DiemBaoVe khi có | DoAnKho |
| File đồ án | Tệp (DOCX/PDF) | Có | Đẩy sang dịch vụ AI để index (REPO-01, REPO-03) | DoAnKho |
| Ngày lưu | Ngày | Có | Tự sinh | DoAnKho |

Nguồn: TL-09/TL-10 (Danh sách đề tài các khóa trước / đồ án thật các khóa trước — GIẢ ĐỊNH — chờ xác nhận, xem `tai-lieu-goc/README.md`).

### 2.1.5. Đánh giá hiện trạng

| Mã | Vấn đề | Ảnh hưởng | Hướng giải quyết trong hệ thống |
|----|--------|-----------|-----------------------------------|
| VD-01 | Khó phát hiện đề tài trùng giữa các khóa khi xét duyệt thủ công | Đề tài lặp lại không bị phát hiện, tốn thời gian họp xét duyệt (GIẢ ĐỊNH — chờ xác nhận) | Kiểm tra trùng tên đề tài theo ngữ nghĩa tự động khi đề xuất/đăng ký (AISV-03, TB-DT-02) |
| VD-02 | Khó phát hiện đoạn nội dung chép lại giữa các đề cương/báo cáo trong khoa | Chỉ dựa vào trí nhớ/đọc thủ công của GVHD, dễ bỏ sót (GIẢ ĐỊNH — chờ xác nhận) | Kiểm tra đoạn trùng tự động, hiển thị tỷ lệ tương đồng và đoạn nguồn (AISV-04, AISV-05) |
| VD-03 | Theo dõi tiến độ phân tán theo từng GVHD, không có mốc chung | Bộ môn không có số liệu tổng hợp, khó phát hiện SV trễ hạn sớm (GIẢ ĐỊNH — chờ xác nhận) | Mốc tiến độ chung của đợt và dashboard tổng hợp cho Bộ môn (PROG-01..03) |
| VD-04 | Tổng hợp điểm bảo vệ thủ công từ phiếu giấy của nhiều thành viên hội đồng | Dễ sai sót khi cộng/tính trung bình, mất thời gian thư ký (GIẢ ĐỊNH — chờ xác nhận) | Hệ thống tự tính điểm trung bình cộng các thành viên (DEFN-04) |
| VD-05 | Tra cứu đồ án các khóa cũ khó, dữ liệu phân tán (bản cứng + ổ dùng chung) | Sinh viên/GVHD không tham khảo được đồ án cũ, Bộ môn khó đối chiếu tránh trùng đề tài (GIẢ ĐỊNH — chờ xác nhận) | Kho dữ liệu tìm kiếm/lọc theo khóa, từ khóa, GVHD (REPO-01, REPO-02) |
| VD-06 | Thông báo quyết định duyệt/phân công/lịch bảo vệ chậm trễ qua email hoặc bảng tin | SV/GV có thể bỏ lỡ thông tin quan trọng (GIẢ ĐỊNH — chờ xác nhận) | Thông báo in-app tức thời khi có quyết định (NOTF-01) |
| VD-07 | Trạng thái đề tài/đề cương không minh bạch theo thời gian thực, phải hỏi trực tiếp Bộ môn/GVHD | Sinh viên mất thời gian chờ và hỏi lại nhiều lần (GIẢ ĐỊNH — chờ xác nhận) | Mọi vai trò tự tra cứu trạng thái theo thời gian thực (UC1.4, UC2.4) |

### 2.1.6. Kết quả phiếu khảo sát

Phiếu khảo sát định lượng ([Phụ lục C](khao-sat/phieu-khao-sat.md)) thu thập đánh giá Likert 1–5 và lựa chọn kênh/công cụ theo ba vai trò (Bộ môn, Giảng viên, Sinh viên). Mỗi câu trả lời (một mã phiếu × một mã câu) được nhập thành một dòng long-format vào `tai-lieu-goc/phong-van/ket-qua-phieu-khao-sat.csv`, theo đúng cấu trúc cột (`ma_phieu,vai_tro,ma_cau,tra_loi,ghi_chu`) đã định nghĩa tại [`khao-sat/mau-tong-hop-phieu-khao-sat.csv`](khao-sat/mau-tong-hop-phieu-khao-sat.csv).

Khi có dữ liệu thật, mục này sẽ tổng hợp mỗi câu hỏi (P-BM-*, P-GV-*, P-SV-*) thành: số phiếu trả lời, giá trị trung bình đối với câu Likert, và tỷ lệ lựa chọn đối với câu chọn kênh/công cụ.

> GIẢ ĐỊNH — chờ xác nhận: chưa có phiếu khảo sát nào được thu thập tại thời điểm viết mục này — `ket-qua-phieu-khao-sat.csv` chưa tồn tại. Không có số liệu định lượng nào được suy đoán hoặc bịa ra trong mục này; số liệu thật sẽ được điền vào bản cập nhật ở plan 01-07 sau khi phát phiếu và thu về kết quả.
