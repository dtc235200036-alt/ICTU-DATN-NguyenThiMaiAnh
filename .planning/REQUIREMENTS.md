# Requirements: Hệ thống quản lý đồ án sinh viên — Khoa CNTT, ICTU

**Defined:** 2026-09-27
**Core Value:** Quy trình đồ án 5 UC chính chạy trọn vẹn end-to-end trên Web, và khi SV đăng ký đề tài hoặc nộp đề cương/báo cáo, hệ thống cảnh báo trùng lặp kèm đề tài/đồ án trùng, đoạn trùng và tỷ lệ tương đồng.

## v1 Requirements

### Phân tích & thiết kế (tài liệu — CLO 1, 2)

- [x] **ANLS-01**: Có kết quả khảo sát quy trình quản lý đồ án thực tế của Khoa CNTT (đăng ký đề tài, duyệt đề cương, theo dõi tiến độ, nộp báo cáo, bảo vệ) kèm các form mẫu dữ liệu (PI 1.1)
- [x] **ANLS-02**: Có sơ đồ BPMN và mô tả chi tiết cho quy trình nghiệp vụ (PI 1.1)
- [ ] **ANLS-03**: Có bảng yêu cầu chức năng chi tiết (PI 1.2)
- [ ] **ANLS-04**: Có bảng yêu cầu phi chức năng: bảo mật, phân quyền, hiệu năng, thời gian phản hồi của kiểm tra trùng lặp có ngưỡng đo được (PI 1.2)
- [ ] **ANLS-05**: Có sơ đồ UC tổng quát đúng chuẩn với 5 UC chính + đặc tả cho từng UC (PI 1.3)
- [ ] **DSGN-01**: Có sơ đồ lớp thực thể (Sinh viên, Giảng viên, Đề tài, Đề cương, Báo cáo tiến độ, Hội đồng, Tài liệu đồ án, Kết quả kiểm tra trùng lặp, …) (PI 2.1)
- [ ] **DSGN-02**: Có sơ đồ CSDL khớp với sơ đồ lớp thực thể (PI 2.1)
- [ ] **DSGN-03**: Có thiết kế kiến trúc SOA bằng UML (component/deployment) thể hiện Web API, client React và dịch vụ AI tách biệt (PI 2.2)
- [x] **DSGN-04**: Có mockup giao diện (HTML prototype, thay cho Figma — phần mềm tương đương theo PI 2.3) cho các giao diện chính của 3 vai trò (PI 2.3)

### Xác thực & phân quyền

- [x] **AUTH-01**: Người dùng đăng nhập bằng tài khoản (mã SV/GV hoặc email) + mật khẩu, nhận JWT
- [x] **AUTH-02**: Phiên đăng nhập được giữ khi reload trình duyệt; người dùng đăng xuất được từ mọi trang
- [x] **AUTH-03**: Hệ thống có 3 vai trò Sinh viên, Giảng viên, Bộ môn (admin); mỗi API kiểm tra vai trò và quyền sở hữu dữ liệu phía server (không chỉ ẩn nút trên UI)
- [x] **AUTH-04**: Bộ môn quản lý tài khoản SV/GV (tạo, sửa, khóa) và mở/đóng đợt đồ án theo khóa

### Quản lý đề tài (UC1)

- [x] **TOPC-01**: GVHD tạo và giao đề tài (tên, mô tả, lĩnh vực) cho một SV trong lớp hướng dẫn của mình, trong đợt đồ án đang mở — đề tài Đã phân công ngay
- [x] **TOPC-02**: Sinh viên xem đề tài GVHD đã giao cho mình; SV không tự đề xuất hay đăng ký đề tài trên hệ thống (trao đổi trực tiếp với GV ngoài hệ thống)
- [x] **TOPC-03**: Bộ môn phân công GVHD cho từng SV đầu mỗi đợt (mỗi SV đúng một GVHD; gán trên màn hình hoặc import CSV); chỉ GVHD được phân công mới giao đề tài cho SV của mình; mỗi SV chỉ có 1 đề tài đang hoạt động, mỗi đề tài chỉ có 1 SV
- [x] **TOPC-04**: Mọi vai trò xem danh sách đề tài trong phạm vi của mình theo trạng thái (nháp → đã phân công), lọc theo đợt và GV

### Quản lý đề cương (UC2)

- [x] **OUTL-01**: SV đã được duyệt đề tài nộp đề cương dạng DOCX hoặc PDF; mỗi lần nộp lại tạo phiên bản mới
- [x] **OUTL-02**: GVHD xem đề cương cùng kết quả kiểm tra trùng lặp ngay trên màn hình duyệt
- [x] **OUTL-03**: GVHD duyệt hoặc yêu cầu sửa kèm nhận xét; SV sửa và nộp lại đến khi được duyệt

### Quản lý tiến độ (UC3)

- [x] **PROG-01**: SV nộp báo cáo tiến độ theo các mốc cố định của đợt (nội dung + file đính kèm tùy chọn)
- [x] **PROG-02**: GVHD nhận xét và đánh giá từng báo cáo tiến độ
- [x] **PROG-03**: Bộ môn xem dashboard tiến độ tất cả SV, đánh dấu SV trễ mốc

### Quản lý bảo vệ (UC4)

- [x] **DEFN-01**: SV nộp báo cáo cuối (DOCX/PDF); lần nộp này chạy kiểm tra trùng lặp nội dung
- [x] **DEFN-02**: Bộ môn lập hội đồng (chọn các GV làm thành viên), xếp lịch (ngày, giờ, phòng) và danh sách SV bảo vệ
- [x] **DEFN-03**: GV được phân vào hội đồng xem báo cáo của SV thuộc hội đồng mình và nhập điểm + nhận xét
- [x] **DEFN-04**: Hệ thống tính điểm bảo vệ bằng trung bình cộng điểm các thành viên; bộ môn chốt kết quả; SV xem lịch và kết quả của mình

### Kho dữ liệu đồ án (UC5)

- [x] **REPO-01**: Đồ án đã chốt kết quả được đưa vào kho với metadata (khóa, đề tài, SV, GVHD, từ khóa, điểm, file)
- [x] **REPO-02**: Người dùng tìm kiếm/lọc đồ án trong kho theo khóa, từ khóa, GVHD và xem chi tiết
- [x] **REPO-03**: Bộ môn thêm/sửa/xóa bản ghi kho, kể cả import đồ án các khóa cũ; mỗi bản ghi mới được đẩy sang dịch vụ AI để index

### AI kiểm tra trùng lặp

- [x] **AISV-01**: Dịch vụ AI là service FastAPI riêng, chỉ Web API gọi được (API key nội bộ, không public qua Apache), có endpoint ingest/check-title/check-document
- [x] **AISV-02**: Văn bản được chuẩn hóa Unicode NFC và tách từ tiếng Việt trước khi embedding; embedding kho được tính sẵn lúc ingest, không tính lại mỗi request
- [x] **AISV-03**: Khi GVHD tạo/giao đề tài, hệ thống so sánh tên đề tài theo ngữ nghĩa với kho và trả về top các đề tài tương tự kèm tỷ lệ % trong thời gian phản hồi theo NFR
- [x] **AISV-04**: Khi nộp đề cương/báo cáo, hệ thống trích text DOCX/PDF, loại phần mẫu chung (tiêu đề mẫu, mục lục, tài liệu tham khảo) và phát hiện các đoạn trùng với đồ án khác trong kho
- [x] **AISV-05**: Kết quả kiểm tra tài liệu hiển thị tỷ lệ tương đồng tổng, danh sách đồ án trùng, và từng đoạn trùng được highlight cạnh đoạn nguồn
- [x] **AISV-06**: Kiểm tra tài liệu chạy bất đồng bộ; UI hiển thị trạng thái đang kiểm tra / hoàn tất
- [x] **AISV-07**: Bộ môn cấu hình được ngưỡng cảnh báo trùng lặp (tên đề tài và nội dung)

### Thông báo

- [x] **NOTF-01**: Người dùng nhận thông báo in-app khi được phân công GVHD, khi được GVHD giao đề tài, khi đề cương được duyệt hoặc yêu cầu sửa, khi có nhận xét mới và khi được phân vào hội đồng / có lịch bảo vệ

### Triển khai & dữ liệu thử nghiệm (CLO 4)

- [x] **DEPL-01**: CSDL MySQL 8 dùng utf8mb4, quản lý schema bằng migration (PI 3.1)
- [x] **DEPL-02**: Hệ thống chạy trên server sau Apache reverse proxy với HTTPS; client React phục vụ tĩnh, `/api` proxy sang Web API (PI 4.1)
- [x] **DATA-01**: Seed 100 SV và 30 GV (PI 4.2)
- [x] **DATA-02**: Seed 300 đề tài thuộc các khóa, ingest vào dịch vụ AI (PI 4.2)
- [x] **DATA-03**: 50 file đề cương/báo cáo thử nghiệm, có các cặp trùng chủ đích (chép nguyên văn, diễn đạt lại, cùng lĩnh vực khác đề tài, không liên quan) và bảng kết quả kiểm chứng (PI 4.2)

### Quyển báo cáo

- [ ] **RPRT-01**: Quyển báo cáo 4 chương đúng khuôn mẫu trường (Cơ sở lý thuyết; Khảo sát & phân tích; Thiết kế; Triển khai kèm hướng dẫn cài đặt, kết quả thử nghiệm)
- [ ] **RPRT-02**: Slide bảo vệ và kịch bản demo end-to-end

## v2 Requirements

### Mở rộng

- **EXT-01**: Gửi email thông báo
- **EXT-02**: Cảnh báo trùng lịch khi xếp 1 GV vào 2 hội đồng cùng thời điểm
- **EXT-03**: Xuất bảng điểm bảo vệ ra PDF/Excel
- **EXT-04**: Điểm bảo vệ có trọng số GVHD / phản biện / hội đồng

## Out of Scope

| Feature | Reason |
|---------|--------|
| So sánh với Internet / thay thế Turnitin | Đề cương giới hạn phạm vi trong kho đồ án của khoa |
| Role "thành viên hội đồng" riêng | Hội đồng dùng tài khoản GV được phân công |
| Đề tài nhóm (nhiều SV/đề tài) | Không có trong đề cương, tăng phức tạp mô hình dữ liệu |
| Chat real-time SV–GV | Không có PI tương ứng; nhận xét trên bài nộp là đủ |
| Tự động xếp lịch hội đồng bằng thuật toán | Xếp tay đủ cho dữ liệu demo |
| AI gợi ý đề tài / gợi ý GVHD | Chỉ 2 tính năng AI được đề cương yêu cầu |
| App mobile native | Đề cương chỉ yêu cầu ứng dụng Web |
| SSO / tích hợp hệ thống đào tạo của trường | Mục tiêu là demo bảo vệ |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ANLS-01 | Phase 1 | Complete |
| ANLS-02 | Phase 1 | Complete |
| ANLS-03 | Phase 1 | Pending |
| ANLS-04 | Phase 1 | Pending |
| ANLS-05 | Phase 1 | Pending |
| DSGN-01 | Phase 1 | Pending |
| DSGN-02 | Phase 1 | Pending |
| DSGN-03 | Phase 1 | Pending |
| DSGN-04 | Phase 1 | Complete |
| AUTH-01 | Phase 2 | Complete |
| AUTH-02 | Phase 2 | Complete |
| AUTH-03 | Phase 2 | Complete |
| AUTH-04 | Phase 2 | Complete |
| TOPC-01 | Phase 2 | Complete |
| TOPC-02 | Phase 2 | Complete |
| TOPC-03 | Phase 2 | Complete |
| TOPC-04 | Phase 2 | Complete |
| OUTL-01 | Phase 3 | Complete |
| OUTL-02 | Phase 3 | Complete |
| OUTL-03 | Phase 3 | Complete |
| PROG-01 | Phase 3 | Complete |
| PROG-02 | Phase 3 | Complete |
| PROG-03 | Phase 3 | Complete |
| DEFN-01 | Phase 3 | Complete |
| DEFN-02 | Phase 3 | Complete |
| DEFN-03 | Phase 3 | Complete |
| DEFN-04 | Phase 3 | Complete |
| REPO-01 | Phase 3 | Complete |
| REPO-02 | Phase 3 | Complete |
| REPO-03 | Phase 3 | Complete |
| AISV-01 | Phase 4 | Complete |
| AISV-02 | Phase 4 | Complete |
| AISV-03 | Phase 4 | Complete |
| AISV-04 | Phase 4 | Complete |
| AISV-05 | Phase 4 | Complete |
| AISV-06 | Phase 4 | Complete |
| AISV-07 | Phase 4 | Complete |
| NOTF-01 | Phase 3 | Complete |
| DEPL-01 | Phase 2 | Complete |
| DEPL-02 | Phase 2 | Complete |
| DATA-01 | Phase 2 | Complete |
| DATA-02 | Phase 4 | Complete |
| DATA-03 | Phase 4 | Complete |
| RPRT-01 | Phase 5 | Pending |
| RPRT-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 45 total
- Mapped to phases: 45
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-27*
*Last updated: 2026-09-27 after roadmap creation (traceability mapped to 5 phases)*
