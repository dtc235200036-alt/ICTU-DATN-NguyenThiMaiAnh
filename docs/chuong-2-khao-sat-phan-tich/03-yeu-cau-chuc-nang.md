## 2.3. Yêu cầu chức năng

> **Mã PI:** 1.2 — **Yêu cầu:** ANLS-03

Bảng dưới đây liệt kê các yêu cầu chức năng chi tiết, nhóm theo module nghiệp vụ. Mỗi hàng có mã (FR-\<module\>-NN), tên chức năng, mô tả chi tiết, tác nhân thực hiện, UC liên quan và nguồn (yêu cầu v1 tương ứng trong `.planning/REQUIREMENTS.md`). Module DT (Quản lý đề tài) được hoàn thiện trong kế hoạch 01-02 và được điều chỉnh theo nghiệp vụ phân công GVHD đầu đợt (Bộ môn phân lớp hướng dẫn, GVHD duyệt đề tài — bổ sung FR-DT-08..FR-DT-11, đổi tác nhân FR-DT-04 và nội dung FR-DT-05); module TK (Tài khoản và phân quyền) và các module còn lại (DC, TD, BV, KHO, TB, AI) do plan 01-04 bổ sung.

### 2.3.1. Tài khoản và phân quyền (TK)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-TK-01 | Đăng nhập | Người dùng đăng nhập bằng mã SV/GV hoặc email + mật khẩu; hệ thống trả về JWT nếu xác thực đúng | Sinh viên, Giảng viên, Bộ môn | UC0.1 | AUTH-01 |
| FR-TK-02 | Giữ phiên và đăng xuất | Phiên đăng nhập được giữ khi tải lại trình duyệt (JWT lưu phía client); người dùng đăng xuất được từ mọi trang | Sinh viên, Giảng viên, Bộ môn | UC0.1 | AUTH-02 |
| FR-TK-03 | Phân quyền theo 3 vai trò | Hệ thống có 3 vai trò Sinh viên, Giảng viên, Bộ môn; mỗi API kiểm tra vai trò và quyền sở hữu dữ liệu phía server, không chỉ ẩn nút trên giao diện | Hệ thống | UC0.1 | AUTH-03 |
| FR-TK-04 | Quản lý tài khoản SV/GV | Bộ môn tạo, sửa, khóa tài khoản Sinh viên và Giảng viên | Bộ môn | UC0.2 | AUTH-04 |
| FR-TK-05 | Quản lý đợt đồ án | Bộ môn mở hoặc đóng đợt đồ án theo khóa; các thao tác đề xuất/đăng ký đề tài chỉ thực hiện được khi đợt đang mở | Bộ môn | UC0.3 | AUTH-04 |

### 2.3.2. Quản lý đề tài (DT)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-DT-01 | Đề xuất đề tài | Giảng viên hoặc Sinh viên đề xuất đề tài mới gồm tên, mô tả, lĩnh vực; chỉ gửi được khi đợt đồ án đang mở (lưu nháp thì luôn được). Sinh viên chỉ gửi được đề xuất trong đợt mà mình đã được Bộ môn phân công GVHD (FR-DT-05), nếu chưa có hệ thống báo "Bạn chưa được Bộ môn phân công giảng viên hướng dẫn trong đợt này"; đề tài SV gửi được gắn ngay với GVHD đó, chuyển "Chờ duyệt" và GVHD nhận thông báo | Giảng viên, Sinh viên | UC1.1 | TOPC-01, TOPC-02 |
| FR-DT-02 | Cảnh báo đề tài tương tự khi đề xuất | Khi đề xuất/đăng ký, hệ thống so sánh tên đề tài theo ngữ nghĩa với kho đề tài đã có, trả về top các đề tài tương tự kèm tỷ lệ % tương đồng; chỉ cảnh báo, không chặn gửi; ngưỡng cảnh báo do Bộ môn cấu hình | Hệ thống (Dịch vụ AI) | UC1.1 | AISV-03, AISV-07 |
| FR-DT-03 | Đăng ký đề tài GVHD mở cho lớp | Sinh viên chọn một đề tài ở trạng thái "Mở cho lớp đăng ký" do chính GVHD của mình mở trong đợt đó để đăng ký; đăng ký thành công thì đề tài chuyển "Đã phân công" ngay (không qua bước duyệt) và GVHD nhận thông báo | Sinh viên | UC1.2 | TOPC-02 |
| FR-DT-04 | Duyệt hoặc từ chối đề tài kèm lý do | GVHD của sinh viên xem đề tài "Chờ duyệt" do sinh viên trong lớp hướng dẫn của mình đề xuất, quyết định duyệt (chuyển "Đã phân công") hoặc từ chối (chuyển "Từ chối", bắt buộc ghi lý do; SV được đề xuất lại, vẫn gửi tới GVHD đó). Bộ môn, Sinh viên và Giảng viên khác không có quyền duyệt (server trả 403) | Giảng viên (GVHD) | UC1.3 | TOPC-03 |
| FR-DT-05 | Phân công GVHD | Đầu mỗi đợt đồ án, Bộ môn phân công mỗi Sinh viên cho đúng một Giảng viên hướng dẫn (lớp hướng dẫn của GV) — gán từng dòng hoặc gán hàng loạt cho các SV đã chọn; màn hình có thống kê tổng SV / đã phân công / chưa phân công, số SV mỗi GV đang hướng dẫn, lọc theo từ khóa, GVHD và tình trạng phân công. SV và GV nhận thông báo khi phân công thay đổi | Bộ môn | UC0.8 | TOPC-03 |
| FR-DT-06 | Ràng buộc mỗi SV chỉ một đề tài đang hoạt động và mỗi đề tài chỉ một SV | Hệ thống chặn một Sinh viên có 2 đề tài đang hoạt động và chặn 2 Sinh viên cùng đăng ký một đề tài, kể cả khi hai SV đăng ký cùng lúc (race condition) — chỉ một đăng ký thắng | Hệ thống | UC1.2 | TOPC-03 |
| FR-DT-07 | Xem danh sách đề tài theo trạng thái, lọc theo đợt và GV | Mọi vai trò xem danh sách đề tài theo trạng thái (Nháp → Chờ duyệt → Mở cho lớp đăng ký/Từ chối → Đã phân công), lọc theo đợt đồ án và theo Giảng viên; phạm vi hiển thị theo vai trò: GV chỉ thấy đề tài mình hướng dẫn/đề xuất (không thấy bản nháp của SV), SV thấy đề tài của mình và đề tài do GVHD của mình mở cho lớp, Bộ môn thấy toàn bộ (chỉ xem) | Sinh viên, Giảng viên, Bộ môn | UC1.4 | TOPC-04 |
| FR-DT-08 | Import phân công GVHD từ CSV | Bộ môn import phân công hàng loạt từ tệp CSV mỗi dòng `ma_so_sinh_vien,ma_giang_vien`; các dòng hợp lệ được lưu, các dòng lỗi (không tìm thấy mã SV/GV, vi phạm ràng buộc FR-DT-09) được báo lại kèm số dòng và lý do | Bộ môn | UC0.8 | TOPC-03 |
| FR-DT-09 | Ràng buộc đổi/gỡ GVHD | Hệ thống chặn đổi hoặc gỡ GVHD của một SV khi SV đã có đề tài "Đã phân công" trong đợt (đề cương, tiến độ, bảo vệ đều gắn với GVHD đó); chặn gỡ GVHD khi SV đang có đề tài "Chờ duyệt"; khi đổi GVHD, đề tài "Chờ duyệt" của SV chuyển sang GVHD mới duyệt | Hệ thống | UC0.8 | TOPC-03 |
| FR-DT-10 | GV giao đề tài hoặc mở cho lớp đăng ký | Khi tạo đề tài, Giảng viên chọn một SV trong lớp hướng dẫn của mình ở đợt đó — gửi đi thì đề tài chuyển "Đã phân công" ngay và SV nhận thông báo (GV giao đề tài); hoặc để trống — gửi đi thì đề tài chuyển "Mở cho lớp đăng ký", chỉ SV trong lớp của GV ở đợt đó nhìn thấy và đăng ký được | Giảng viên | UC1.1 | TOPC-01 |
| FR-DT-11 | Xem lớp hướng dẫn | Giảng viên xem danh sách SV Bộ môn đã phân công cho mình theo từng đợt đang mở, kèm đề tài hiện tại của từng SV, và đi thẳng tới thao tác "Duyệt đề tài" hoặc "Giao đề tài"; Sinh viên xem GVHD của mình trên trang tổng quan | Giảng viên, Sinh viên | UC0.8 | TOPC-03 |

### 2.3.3. Quản lý đề cương (DC)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-DC-01 | Nộp đề cương | Sinh viên đã được duyệt đề tài nộp đề cương dạng DOCX hoặc PDF; mỗi lần nộp lại tạo một phiên bản mới, giữ nguyên các phiên bản trước | Sinh viên | UC2.1 | OUTL-01 |
| FR-DC-02 | Kiểm tra định dạng và dung lượng file nộp | Hệ thống từ chối file sai định dạng (không phải DOCX/PDF) hoặc vượt quá dung lượng tối đa trước khi lưu phiên bản | Hệ thống | UC2.1 | OUTL-01 |
| FR-DC-03 | Xem đề cương kèm kết quả kiểm tra trùng lặp | Giảng viên hướng dẫn xem nội dung đề cương cùng kết quả kiểm tra trùng lặp (UC0.7) ngay trên màn hình duyệt | Giảng viên | UC2.2 | OUTL-02 |
| FR-DC-04 | Duyệt hoặc yêu cầu sửa đề cương | Giảng viên hướng dẫn duyệt hoặc yêu cầu sửa kèm nhận xét; Sinh viên sửa và nộp lại, lặp lại đến khi được duyệt | Giảng viên, Sinh viên | UC2.2 | OUTL-03 |
| FR-DC-05 | Xem lịch sử phiên bản và nhận xét | Sinh viên và Giảng viên xem lại toàn bộ các phiên bản đề cương đã nộp cùng nhận xét của từng lần duyệt | Sinh viên, Giảng viên | UC2.3 | OUTL-01, OUTL-03 |

### 2.3.4. Quản lý tiến độ (TD)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-TD-01 | Thiết lập mốc tiến độ | Bộ môn thiết lập các mốc tiến độ cố định áp dụng cho toàn bộ đợt đồ án (ví dụ: mốc 1, mốc 2, mốc cuối) | Bộ môn | UC3.1 | PROG-01 |
| FR-TD-02 | Nộp báo cáo tiến độ | Sinh viên nộp báo cáo tiến độ theo từng mốc, gồm nội dung mô tả và file đính kèm tùy chọn | Sinh viên | UC3.2 | PROG-01 |
| FR-TD-03 | Nhận xét và đánh giá báo cáo tiến độ | Giảng viên hướng dẫn nhận xét và đánh giá từng báo cáo tiến độ Sinh viên đã nộp | Giảng viên | UC3.3 | PROG-02 |
| FR-TD-04 | Theo dõi tiến độ toàn khoa | Bộ môn xem dashboard tiến độ của tất cả Sinh viên, hệ thống tự động đánh dấu Sinh viên trễ mốc (không nộp báo cáo trước hạn) | Bộ môn | UC3.4 | PROG-03 |

### 2.3.5. Quản lý bảo vệ (BV)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-BV-01 | Nộp báo cáo cuối | Sinh viên nộp báo cáo cuối dạng DOCX/PDF; lần nộp này kích hoạt kiểm tra trùng lặp nội dung (UC0.7) | Sinh viên | UC4.1 | DEFN-01 |
| FR-BV-02 | Lập hội đồng bảo vệ | Bộ môn chọn các Giảng viên làm thành viên hội đồng cho một đợt bảo vệ | Bộ môn | UC4.2 | DEFN-02 |
| FR-BV-03 | Xếp lịch bảo vệ | Bộ môn xếp ngày, giờ, phòng và danh sách Sinh viên bảo vệ theo từng hội đồng | Bộ môn | UC4.2 | DEFN-02 |
| FR-BV-04 | Chấm điểm và nhận xét | Giảng viên được phân vào hội đồng chỉ xem báo cáo của Sinh viên thuộc hội đồng mình và nhập điểm kèm nhận xét | Giảng viên | UC4.3 | DEFN-03 |
| FR-BV-05 | Tính điểm trung bình cộng | Hệ thống tính điểm bảo vệ của mỗi Sinh viên bằng trung bình cộng điểm của các thành viên hội đồng đã chấm | Hệ thống | UC4.4 | DEFN-04 |
| FR-BV-06 | Chốt kết quả bảo vệ | Bộ môn chốt kết quả bảo vệ sau khi mọi thành viên hội đồng đã chấm điểm | Bộ môn | UC4.4 | DEFN-04 |
| FR-BV-07 | Xem lịch và kết quả bảo vệ | Sinh viên xem lịch bảo vệ (ngày, giờ, phòng, hội đồng) và kết quả bảo vệ của chính mình | Sinh viên | UC4.5 | DEFN-04 |

### 2.3.6. Quản lý kho dữ liệu đồ án (KHO)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-KHO-01 | Tự động lưu đồ án vào kho | Khi Bộ môn chốt kết quả bảo vệ, hệ thống tự động tạo bản ghi kho với metadata: khóa, đề tài, Sinh viên, GVHD, từ khóa, điểm, file báo cáo | Hệ thống | UC5.2 | REPO-01 |
| FR-KHO-02 | Tìm kiếm và xem chi tiết đồ án trong kho | Mọi vai trò tìm kiếm/lọc đồ án trong kho theo khóa, từ khóa, Giảng viên hướng dẫn và xem chi tiết một bản ghi | Sinh viên, Giảng viên, Bộ môn | UC5.1 | REPO-02 |
| FR-KHO-03 | Quản lý bản ghi kho | Bộ môn thêm, sửa, xóa bản ghi kho dữ liệu đồ án | Bộ môn | UC5.3 | REPO-03 |
| FR-KHO-04 | Import đồ án khóa cũ | Bộ môn import hàng loạt đồ án của các khóa trước vào kho | Bộ môn | UC5.4 | REPO-03 |
| FR-KHO-05 | Đẩy bản ghi kho sang dịch vụ AI để index | Mỗi bản ghi kho mới (tự động hoặc import) đều được đẩy sang dịch vụ AI để tính embedding và đưa vào chỉ mục so sánh trùng lặp | Hệ thống | UC5.2, UC5.4 | REPO-03 |

### 2.3.7. Thông báo (TB)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-TB-01 | Thông báo in-app | Người dùng nhận thông báo in-app (số lượng chưa đọc + danh sách, đánh dấu đã đọc) khi được Bộ môn phân công/đổi GVHD, khi có đề tài chờ GVHD duyệt, khi được GV giao đề tài hoặc có SV đăng ký đề tài của GV, khi đề tài/đề cương được duyệt hoặc từ chối, khi có nhận xét mới, khi được phân vào hội đồng hoặc có lịch bảo vệ | Sinh viên, Giảng viên, Bộ môn | UC0.5 | NOTF-01 |

### 2.3.8. Kiểm tra trùng lặp bằng AI (AI)

| Mã | Tên chức năng | Mô tả chi tiết | Tác nhân | UC | Nguồn |
|----|---------------|-----------------|----------|----|-------|
| FR-AI-01 | Kiểm tra trùng tên đề tài | Khi đề xuất/đăng ký đề tài, so sánh ngữ nghĩa tên đề tài với kho đề tài đã có, trả về top các đề tài tương tự kèm tỷ lệ % tương đồng | Hệ thống (Dịch vụ AI) | UC0.6 | AISV-03 |
| FR-AI-02 | Trích xuất và lọc văn bản trước khi so sánh | Khi nộp đề cương/báo cáo, trích text từ DOCX/PDF, loại bỏ phần mẫu chung (tiêu đề mẫu, mục lục, tài liệu tham khảo), sau đó phát hiện các đoạn trùng với đồ án khác trong kho | Hệ thống (Dịch vụ AI) | UC0.7 | AISV-04 |
| FR-AI-03 | Hiển thị kết quả kiểm tra tài liệu | Kết quả kiểm tra tài liệu hiển thị tỷ lệ tương đồng tổng, danh sách đồ án trùng, và từng đoạn trùng được highlight cạnh đoạn nguồn | Hệ thống | UC0.7 | AISV-05 |
| FR-AI-04 | Kiểm tra bất đồng bộ | Kiểm tra tài liệu chạy bất đồng bộ (không chặn thao tác nộp); giao diện hiển thị trạng thái Đang kiểm tra / Hoàn tất | Hệ thống | UC0.7 | AISV-06 |
| FR-AI-05 | Cấu hình ngưỡng cảnh báo trùng lặp | Bộ môn cấu hình được ngưỡng cảnh báo trùng lặp cho tên đề tài và cho nội dung; lần kiểm tra sau khi lưu cấu hình mới sẽ áp dụng ngưỡng mới | Bộ môn | UC0.4 | AISV-07 |
