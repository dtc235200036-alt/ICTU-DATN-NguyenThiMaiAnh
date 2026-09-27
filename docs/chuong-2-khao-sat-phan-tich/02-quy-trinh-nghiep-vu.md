# Chương 2. Khảo sát & phân tích

## 2.2. Mô hình hóa quy trình nghiệp vụ

> **Mã PI:** 1.1 — **Yêu cầu:** ANLS-02

Mỗi quy trình nghiệp vụ của hệ thống được mô hình hóa dưới dạng hai sơ đồ BPMN: **AS-IS** (quy trình thủ công hiện tại, làm cơ sở khảo sát) và **TO-BE** (quy trình vận hành trên hệ thống, có bước kiểm tra trùng lặp bằng AI). Cả hai đều dùng chung 3 làn (swimlane) **Sinh viên / Giảng viên / Bộ môn**; riêng TO-BE có thêm làn **Hệ thống** thể hiện các bước tự động (Web API và Dịch vụ AI). Theo D-03, bộ sơ đồ gồm 1 sơ đồ tổng quan và 5 quy trình con, khớp 5 UC chính: Quản lý đề tài, Quản lý đề cương, Theo dõi tiến độ, Nộp báo cáo và bảo vệ, Quản lý kho dữ liệu đồ án.

### 2.2.1. Quy trình tổng quan

> GIẢ ĐỊNH — chờ xác nhận: chưa có phỏng vấn thật tại thời điểm viết (D-01, D-02). Phần AS-IS dưới đây là bản nháp; sẽ được đối chiếu sau khi có biên bản phỏng vấn (plan 01-07).

Sơ đồ tổng quan (`bpmn/00-tong-quan.drawio`) thể hiện toàn bộ chuỗi quy trình đồ án dưới dạng các sub-process đã thu gọn (collapsed), mỗi sub-process được mô tả chi tiết ở một sơ đồ riêng (§2.2.2–§2.2.6).

#### Quy trình AS-IS

![Hình 2.a – Quy trình tổng quan (AS-IS) — GIẢ ĐỊNH — chờ xác nhận](bpmn/00-tong-quan-as-is.png)

| Mã bước | Lane | Công việc | Dữ liệu / biểu mẫu | Ghi chú |
|---------|------|-----------|---------------------|---------|
| AS-TQ-01 | Bộ môn | Bộ môn mở đợt đồ án tốt nghiệp | Thông báo mở đợt | GIẢ ĐỊNH — chờ xác nhận |
| AS-TQ-02 | Giảng viên | Quản lý đề tài (xem `bpmn/01-de-tai.drawio`) | — | GIẢ ĐỊNH — chờ xác nhận; chi tiết ở §2.2.2 |
| AS-TQ-03 | Sinh viên | Quản lý đề cương (xem `bpmn/02-de-cuong.drawio`) | — | GIẢ ĐỊNH — chờ xác nhận; chi tiết ở §2.2.3 |
| AS-TQ-04 | Giảng viên | Theo dõi tiến độ (xem `bpmn/03-tien-do.drawio`) | — | GIẢ ĐỊNH — chờ xác nhận; chi tiết ở §2.2.4 |
| AS-TQ-05 | Sinh viên | Nộp báo cáo và bảo vệ (xem `bpmn/04-bao-ve.drawio`) | — | GIẢ ĐỊNH — chờ xác nhận; chi tiết ở §2.2.5 |
| AS-TQ-06 | Bộ môn | Lưu kho đồ án (xem `bpmn/05-kho-do-an.drawio`) | — | GIẢ ĐỊNH — chờ xác nhận; chi tiết ở §2.2.6 |

**Điểm cải tiến của TO-BE so với AS-IS:**

- Toàn bộ chuỗi 5 quy trình con chạy trên một hệ thống thống nhất thay vì rời rạc qua email/Excel/giấy ở từng bước.
- Hai điểm tích hợp AI xuyên suốt (kiểm tra trùng lặp và thông báo in-app) được thể hiện tường minh trong làn Hệ thống, thay vì ẩn trong quy trình thủ công của từng bước.

#### Quy trình TO-BE

![Hình 2.b – Quy trình tổng quan (TO-BE)](bpmn/00-tong-quan-to-be.png)

| Mã bước | Lane | Công việc | Dữ liệu / biểu mẫu | Ghi chú |
|---------|------|-----------|---------------------|---------|
| TB-TQ-01 | Bộ môn | Bộ môn mở đợt đồ án tốt nghiệp | Thông báo mở đợt | — |
| TB-TQ-02 | Giảng viên | Quản lý đề tài (xem `bpmn/01-de-tai.drawio`) | — | Chi tiết ở §2.2.2 |
| TB-TQ-03 | Sinh viên | Quản lý đề cương (xem `bpmn/02-de-cuong.drawio`) | — | Chi tiết ở §2.2.3 |
| TB-TQ-04 | Giảng viên | Theo dõi tiến độ (xem `bpmn/03-tien-do.drawio`) | — | Chi tiết ở §2.2.4 |
| TB-TQ-05 | Sinh viên | Nộp báo cáo và bảo vệ (xem `bpmn/04-bao-ve.drawio`) | — | Chi tiết ở §2.2.5 |
| TB-TQ-06 | Bộ môn | Lưu kho đồ án (xem `bpmn/05-kho-do-an.drawio`) | — | Chi tiết ở §2.2.6 |
| TB-TQ-07 | Hệ thống | Kiểm tra trùng lặp (dịch vụ AI) — được gọi từ Quản lý đề tài, Quản lý đề cương và Nộp báo cáo/bảo vệ | Tên đề tài hoặc nội dung tài liệu | AISV-01..07 |
| TB-TQ-08 | Hệ thống | Thông báo in-app — được gọi từ Quản lý đề tài, Quản lý đề cương, Theo dõi tiến độ và Nộp báo cáo/bảo vệ | Sự kiện duyệt/từ chối/nhận xét/lịch bảo vệ | NOTF-01 |

### 2.2.2. Quy trình quản lý đề tài

> GIẢ ĐỊNH — chờ xác nhận: chưa có phỏng vấn thật tại thời điểm viết (D-01, D-02). Phần AS-IS dưới đây là bản nháp dựa trên suy luận thực tế phổ biến ở các khoa CNTT có quy trình tương tự; sẽ được đối chiếu và cập nhật (hoặc gỡ bỏ nhãn giả định) sau khi có biên bản phỏng vấn Bộ môn/GV/SV (plan 01-07).

#### Quy trình AS-IS

![Hình 2.w – Quy trình quản lý đề tài (AS-IS) — GIẢ ĐỊNH — chờ xác nhận](bpmn/01-de-tai-as-is.png)

| Mã bước | Lane | Công việc | Dữ liệu / biểu mẫu | Ghi chú |
|---------|------|-----------|---------------------|---------|
| AS-DT-01 | Giảng viên | GV gửi danh sách đề tài đề xuất cho Bộ môn qua email/Excel | File Excel/email tự do | GIẢ ĐỊNH — chờ xác nhận |
| AS-DT-02 | Sinh viên | SV đăng ký đề tài qua phiếu giấy hoặc biểu mẫu trực tuyến rời rạc | Phiếu đăng ký giấy hoặc Google Form | GIẢ ĐỊNH — chờ xác nhận |
| AS-DT-03 | Bộ môn | Bộ môn tổng hợp danh sách đề tài và đăng ký thủ công vào Excel | Bảng tổng hợp Excel | GIẢ ĐỊNH — chờ xác nhận |
| AS-DT-04 | Bộ môn | Bộ môn họp xét duyệt đề tài | Biên bản họp | GIẢ ĐỊNH — chờ xác nhận |
| AS-DT-05 | Bộ môn | Bộ môn phân công GVHD thủ công | Bảng phân công | GIẢ ĐỊNH — chờ xác nhận; không kiểm tra tải GV tự động |
| AS-DT-06 | Bộ môn | Bộ môn công bố danh sách đề tài đã duyệt qua email/bảng tin | Thông báo email/bảng tin khoa | GIẢ ĐỊNH — chờ xác nhận; không có thông báo tức thời |

**Điểm cải tiến của TO-BE so với AS-IS:**

- Kiểm tra trùng tên đề tài tự động bằng AI ngay khi đề xuất, thay vì Bộ môn tự phát hiện trùng lặp thủ công khi họp xét duyệt (hoặc không phát hiện được).
- Chặn tự động một SV đăng ký nhiều đề tài hoặc hai SV cùng đăng ký một đề tài, kể cả khi đăng ký cùng lúc (FR-DT-06, Task 2), thay vì đối chiếu thủ công trên Excel.
- Trạng thái đề tài minh bạch theo thời gian thực (Nháp → Chờ duyệt → Đã duyệt/Từ chối → Đã phân công), mọi vai trò tự tra cứu được (UC1.4) thay vì chờ email công bố.
- Thông báo in-app tức thời cho SV và GV khi có quyết định duyệt/từ chối/phân công, thay vì chờ email hoặc bảng tin.

#### Quy trình TO-BE

![Hình 2.x – Quy trình quản lý đề tài (TO-BE)](bpmn/01-de-tai-to-be.png)

| Mã bước | Lane | Công việc | Dữ liệu / biểu mẫu | Ghi chú |
|---------|------|-----------|---------------------|---------|
| TB-DT-01a | Giảng viên | GV nhập đề xuất đề tài (tên, mô tả, lĩnh vực) | Biểu mẫu đề xuất đề tài (điện tử) | Chỉ thực hiện được khi đợt đồ án đang mở |
| TB-DT-01b | Sinh viên | SV tự đề xuất đề tài (tên, mô tả, lĩnh vực) | Biểu mẫu đề xuất đề tài (điện tử) | Chỉ thực hiện được khi đợt đồ án đang mở |
| TB-DT-02 | Hệ thống | Kiểm tra trùng lặp tên đề tài theo ngữ nghĩa (gọi Dịch vụ AI) | Tên đề tài vừa nhập, kho đề tài đã có | So sánh ngữ nghĩa, không phải so khớp chuỗi ký tự |
| TB-DT-03 | Hệ thống | Gateway: có đề tài tương tự vượt ngưỡng cấu hình? | Ngưỡng do Bộ môn cấu hình (FR-DT-02) | Ngưỡng đặt trong yêu cầu phi chức năng (ANLS-04) |
| TB-DT-04 | Hệ thống | Hiển thị danh sách đề tài tương tự kèm tỷ lệ % | Top N đề tài tương tự | Chỉ cảnh báo, không chặn gửi |
| TB-DT-05 | Giảng viên | Người đề xuất sửa tên đề tài hoặc vẫn gửi | — | Quyết định thuộc về người đề xuất |
| TB-DT-06 | Hệ thống | Chuyển trạng thái đề tài sang "Chờ duyệt" | Bản ghi đề tài | Kết thúc UC1.1 |
| TB-DT-07 | Sinh viên | SV chọn đăng ký một đề tài do GV đề xuất và còn trống | Danh sách đề tài trạng thái "Đã duyệt", chưa có SV | UC1.2 |
| TB-DT-08 | Hệ thống | Kiểm tra SV chưa có đề tài đang hoạt động và đề tài chưa có SV khác đăng ký | Ràng buộc 1 SV – 1 đề tài (FR-DT-06) | Phải xử lý đúng khi 2 SV đăng ký cùng lúc |
| TB-DT-09 | Hệ thống | Gateway: đăng ký có hợp lệ? | — | — |
| TB-DT-10 | Hệ thống | Ghi nhận đăng ký, chuyển đề tài sang "Chờ duyệt" | Bản ghi đề tài | Nhánh hợp lệ của UC1.2 |
| TB-DT-11 | Hệ thống | Từ chối đăng ký, thông báo lý do | Thông báo in-app | Nhánh không hợp lệ của UC1.2 |
| TB-DT-12 | Bộ môn | Bộ môn xem đề tài ở trạng thái "Chờ duyệt" | Danh sách đề tài chờ duyệt | UC1.3 |
| TB-DT-13 | Bộ môn | Gateway: Bộ môn có duyệt đề tài? | — | — |
| TB-DT-14 | Bộ môn | Phân công GVHD | Danh sách GV khả dụng | Nhánh duyệt của UC1.3 |
| TB-DT-15 | Hệ thống | Chuyển trạng thái "Đã phân công", gửi thông báo in-app cho SV và GV | Thông báo in-app (NOTF-01) | Kết thúc UC1.3 nhánh duyệt |
| TB-DT-16 | Bộ môn | Từ chối kèm lý do | Ghi chú lý do từ chối | Nhánh từ chối của UC1.3 |
| TB-DT-17 | Hệ thống | Chuyển trạng thái "Từ chối", gửi thông báo in-app cho SV và GV | Thông báo in-app (NOTF-01) | Kết thúc UC1.3 nhánh từ chối |
| TB-DT-18 | Hệ thống | SV/GV/Bộ môn xem và lọc danh sách đề tài theo trạng thái, đợt, GV | Bộ lọc danh sách đề tài | UC1.4, dùng chung cho cả 3 vai trò |

### 2.2.3. Quy trình quản lý đề cương

> GIẢ ĐỊNH — chờ xác nhận: chưa có phỏng vấn thật tại thời điểm viết (D-01, D-02). Phần AS-IS dưới đây là bản nháp dựa trên suy luận thực tế phổ biến; sẽ được đối chiếu và cập nhật sau khi có biên bản phỏng vấn Bộ môn/GV/SV (plan 01-07).

#### Quy trình AS-IS

![Hình 2.c – Quy trình quản lý đề cương (AS-IS) — GIẢ ĐỊNH — chờ xác nhận](bpmn/02-de-cuong-as-is.png)

| Mã bước | Lane | Công việc | Dữ liệu / biểu mẫu | Ghi chú |
|---------|------|-----------|---------------------|---------|
| AS-DC-01 | Sinh viên | SV gửi file đề cương qua email/Zalo cho GVHD | File DOCX/PDF tự do (MAU-03) | GIẢ ĐỊNH — chờ xác nhận |
| AS-DC-02 | Giảng viên | GVHD đọc và góp ý thủ công (viết tay/email) | Bản in có bút phê hoặc email góp ý | GIẢ ĐỊNH — chờ xác nhận |
| AS-DC-03 | Sinh viên | SV chỉnh sửa và gửi lại (lặp cho đến khi đạt) | File DOCX/PDF chỉnh sửa | GIẢ ĐỊNH — chờ xác nhận; không quản lý phiên bản tập trung |
| AS-DC-04 | Giảng viên | GVHD xác nhận đạt, thông báo miệng/email cho SV | — | GIẢ ĐỊNH — chờ xác nhận; không có bước kiểm tra trùng lặp |

**Điểm cải tiến của TO-BE so với AS-IS:**

- Kiểm tra trùng lặp nội dung đề cương tự động trong phạm vi khoa (AISV-04), thay vì chỉ dựa vào trí nhớ/đọc thủ công của GVHD.
- Quản lý phiên bản tập trung mỗi lần SV nộp lại (OUTL-01), thay vì gửi file rời rạc qua email/Zalo không lưu vết.
- GVHD xem kết quả kiểm tra trùng lặp ngay trên màn hình duyệt (OUTL-02), thay vì chỉ đọc nội dung đơn thuần.
- Trạng thái đề cương minh bạch theo thời gian thực (Đang kiểm tra → Hoàn tất → Đã duyệt/Yêu cầu sửa), Bộ môn tự tra cứu được, thay vì chờ thông báo miệng/email.

#### Quy trình TO-BE

![Hình 2.d – Quy trình quản lý đề cương (TO-BE)](bpmn/02-de-cuong-to-be.png)

| Mã bước | Lane | Công việc | Dữ liệu / biểu mẫu | Ghi chú |
|---------|------|-----------|---------------------|---------|
| TB-DC-01 | Sinh viên | SV nộp đề cương (DOCX/PDF) | MAU-03, mỗi lần nộp tạo phiên bản mới | OUTL-01 |
| TB-DC-02 | Hệ thống | Kiểm tra định dạng/dung lượng, lưu phiên bản mới | File đề cương | Pitfall 8: kiểm tra magic bytes, không chỉ đuôi file |
| TB-DC-03 | Hệ thống | Gửi kiểm tra trùng lặp tài liệu (bất đồng bộ) — trạng thái "Đang kiểm tra" | Nội dung đề cương đã trích xuất | AISV-04, AISV-06; loại bỏ phần mẫu chung trước khi so sánh (Pitfall 3) |
| TB-DC-04 | Hệ thống | Nhận kết quả, cập nhật trạng thái "Hoàn tất" | Tỷ lệ tương đồng, đoạn trùng, đồ án trùng | AISV-05 |
| TB-DC-05 | Giảng viên | GVHD xem đề cương cùng kết quả kiểm tra trùng lặp | Panel kết quả trùng lặp | OUTL-02 |
| TB-DC-06 | Giảng viên | Gateway: Duyệt hay yêu cầu sửa? | Nhận xét kèm theo | OUTL-03 |
| TB-DC-07 | Giảng viên | GVHD ghi nhận xét yêu cầu sửa | Nhận xét | Nhánh yêu cầu sửa |
| TB-DC-08 | Sinh viên | SV sửa và nộp lại | File đề cương chỉnh sửa | Lặp lại từ TB-DC-02 đến khi được duyệt (OUTL-03) |
| TB-DC-09 | Hệ thống | Chuyển trạng thái "Đã duyệt", gửi thông báo in-app | Thông báo in-app (NOTF-01) | Nhánh duyệt, kết thúc |
| TB-DC-10 | Bộ môn | Xem/lọc danh sách đề cương theo trạng thái | Bộ lọc danh sách đề cương | Chức năng dùng chung, tương tự UC1.4 |

### 2.2.4. Quy trình theo dõi tiến độ

> GIẢ ĐỊNH — chờ xác nhận: chưa có phỏng vấn thật tại thời điểm viết (D-01, D-02). Phần AS-IS dưới đây là bản nháp; sẽ được đối chiếu sau khi có biên bản phỏng vấn (plan 01-07).

#### Quy trình AS-IS

![Hình 2.e – Quy trình theo dõi tiến độ (AS-IS) — GIẢ ĐỊNH — chờ xác nhận](bpmn/03-tien-do-as-is.png)

| Mã bước | Lane | Công việc | Dữ liệu / biểu mẫu | Ghi chú |
|---------|------|-----------|---------------------|---------|
| AS-TD-01 | Sinh viên | SV báo cáo tiến độ không định kỳ, gặp trực tiếp/nhắn tin | Không có biểu mẫu cố định | GIẢ ĐỊNH — chờ xác nhận |
| AS-TD-02 | Giảng viên | GVHD nhận xét trực tiếp, không lưu vết văn bản | — | GIẢ ĐỊNH — chờ xác nhận; Bộ môn không có số liệu tổng hợp (xem §2.1.3.3) |

**Điểm cải tiến của TO-BE so với AS-IS:**

- Mốc tiến độ chung cho cả đợt do Bộ môn thiết lập (PROG-01), thay vì mỗi GVHD tự quy định tần suất riêng.
- Báo cáo tiến độ có nội dung và (tùy chọn) file đính kèm được lưu tập trung, thay vì trao đổi miệng/nhắn tin không lưu vết.
- Hệ thống tự động đánh dấu SV trễ mốc bằng timer khi quá hạn (PROG-03), thay vì Bộ môn phải tự phát hiện.
- Bộ môn có dashboard tổng hợp tiến độ toàn khóa theo thời gian thực, thay vì không có số liệu tổng hợp.

#### Quy trình TO-BE

![Hình 2.f – Quy trình theo dõi tiến độ (TO-BE)](bpmn/03-tien-do-to-be.png)

| Mã bước | Lane | Công việc | Dữ liệu / biểu mẫu | Ghi chú |
|---------|------|-----------|---------------------|---------|
| TB-TD-01 | Bộ môn | Bộ môn thiết lập các mốc tiến độ của đợt | Danh sách mốc (ngày, mô tả) | PROG-01 |
| TB-TD-02 | Sinh viên | SV nộp báo cáo tiến độ theo mốc (nội dung + file tùy chọn) | MAU-04 | PROG-01 |
| TB-TD-03 | Giảng viên | GVHD nhận xét và đánh giá báo cáo | MAU-04 (phần nhận xét) | PROG-02 |
| TB-TD-05 | Hệ thống | Timer "Quá hạn mốc" kích hoạt khi SV chưa nộp đúng hạn; hệ thống đánh dấu SV trễ mốc | Trạng thái báo cáo tiến độ | PROG-03 |
| TB-TD-06 | Bộ môn | Bộ môn theo dõi dashboard tiến độ toàn khóa | Tổng hợp trạng thái tất cả SV | PROG-03 |
