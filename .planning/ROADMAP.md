# Roadmap: Hệ thống quản lý đồ án sinh viên — Khoa CNTT, ICTU

## Overview

Lộ trình 10 tuần (28/09/2026 → 07/12/2026) gồm 5 phase. Đầu tiên là hồ sơ phân tích & thiết kế (CLO 1–2). Tiếp theo là lát cắt chạy thật đầu tiên: đăng nhập 3 vai trò, phân quyền phía server và UC Quản lý đề tài, dựng sẵn sau Apache HTTPS. Phase 3 hoàn tất 4 UC còn lại (đề cương, tiến độ, bảo vệ, kho) với lời gọi AI qua stub. Phase 4 thay stub bằng dịch vụ AI kiểm tra trùng lặp thật, được hiệu chỉnh trên dữ liệu có cặp trùng chủ đích. Cuối cùng là kiểm thử toàn hệ thống trên server cùng quyển báo cáo và slide bảo vệ. Mỗi phase ghi cửa sổ tuần theo đề cương (T1–T10) để báo cáo tiến độ với GVHD; phase code có thể bắt đầu sớm hơn cửa sổ nếu phase trước xong sớm.

## Đối chiếu tiến độ đề cương

| Tuần | Nội dung theo đề cương | Phase |
|------|------------------------|-------|
| T1 (28/09–04/10) | Khảo sát, BPMN | Phase 1 |
| T2–T3 (05/10–18/10) | Yêu cầu, UC | Phase 1 |
| T4 (19/10–25/10) | Dữ liệu & kiến trúc | Phase 1 |
| T5 (26/10–01/11) | Mockup + thu thập kho | Phase 1 |
| T6 (02/11–08/11) | CSDL + API | Phase 2 (kèm Apache HTTPS + UC1) |
| T7 (09/11–15/11) | 5 UC | Phase 2 (UC1) + Phase 3 (UC2–UC5) |
| T8 (16/11–22/11) | AI | Phase 4 (kèm seed 300 đề tài + 50 file) |
| T9 (23/11–29/11) | Triển khai, seed, kiểm thử | Phase 5 (Apache đã dựng ở Phase 2, seed đã làm ở Phase 2 và 4) |
| T10 (30/11–07/12) | Báo cáo + slide | Phase 5 |

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Analysis & Design** - Phân tích & thiết kế: khảo sát, BPMN, yêu cầu, UC, sơ đồ lớp/CSDL, kiến trúc SOA, mockup giao diện HTML (T1–T5)
- [ ] **Phase 2: Platform, RBAC & Topic Management** - Lát cắt chạy thật đầu tiên sau Apache HTTPS: đăng nhập 3 vai trò, phân quyền phía server, UC1 Quản lý đề tài (T6)
- [ ] **Phase 3: Outline, Progress, Defense & Archive** - UC2–UC5 (đề cương, tiến độ, bảo vệ, kho đồ án) + thông báo in-app, lời gọi AI qua stub (T7)
- [ ] **Phase 4: AI Similarity Service** - Dịch vụ AI riêng thay stub: cảnh báo trùng tên đề tài + đoạn trùng đề cương/báo cáo, hiệu chỉnh trên 300 đề tài và 50 file có cặp trùng chủ đích (T8)
- [ ] **Phase 5: System Verification & Defense Package** - Demo end-to-end trên server với toàn bộ dữ liệu, đo NFR, quyển báo cáo 4 chương + slide (T9–T10)

## Phase Details

### Phase 1: Analysis & Design

**Goal**: Bộ hồ sơ phân tích & thiết kế (CLO 1–2) hoàn chỉnh và truy vết được về PI 1.1–2.3, đủ để thi công mà không phải đoán quy trình, schema, kiến trúc hay giao diện
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Target window**: T1–T5 (28/09–01/11/2026): T1 khảo sát/BPMN · T2–T3 yêu cầu/UC · T4 dữ liệu & kiến trúc · T5 mockup + thu thập kho
**Requirements**: ANLS-01, ANLS-02, ANLS-03, ANLS-04, ANLS-05, DSGN-01, DSGN-02, DSGN-03, DSGN-04
**Success Criteria** (what must be TRUE):
  1. GVHD đọc được kết quả khảo sát quy trình thực tế của Khoa CNTT (đăng ký đề tài → duyệt đề cương → tiến độ → nộp báo cáo → bảo vệ) kèm form mẫu dữ liệu và sơ đồ BPMN có mô tả chi tiết từng bước; file mẫu đề cương/báo cáo chính thức của trường và một số đồ án các khóa trước đã được thu thập vào repo
  2. Bảng yêu cầu chức năng chi tiết và bảng yêu cầu phi chức năng tồn tại, trong đó bảo mật, phân quyền, hiệu năng và thời gian phản hồi kiểm tra trùng lặp đều có ngưỡng đo được (đề xuất: ≤ 5 s cho tên đề tài, ≤ 30 s cho tài liệu)
  3. Sơ đồ UC tổng quát đúng chuẩn UML có 3 tác nhân (SV, GV, Bộ môn) và 5 UC chính, mỗi UC có bản đặc tả (tác nhân, tiền/hậu điều kiện, luồng chính, luồng thay thế/ngoại lệ)
  4. Sơ đồ lớp thực thể và sơ đồ CSDL khớp nhau từng thực thể (kể cả Kết quả kiểm tra trùng lặp), và sơ đồ UML component/deployment thể hiện Web API, client React, dịch vụ AI là 3 thành phần tách biệt sau Apache
  5. Mockup giao diện (HTML prototype) cho các màn hình chính của cả 3 vai trò, bao phủ 5 UC và màn hình kết quả kiểm tra trùng lặp

**Plans**: 6/7 plans executed
Plans:
**Wave 1**
- [x] 01-01-PLAN.md — Bộ công cụ khảo sát (Phụ lục A–D, bản in DOCX) + khu thu thập tài liệu gốc `tai-lieu-goc/` (wave 1)
- [x] 01-02-PLAN.md — TRACER: toolchain (PlantUML/draw.io/headless Chrome/checker) + UC1.1 xuyên suốt BPMN → FR → UC → lớp → bảng → mockup HTML MH-06 → truy vết; hoàn thiện UC1 chương 2 + quy ước (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-03-PLAN.md — Khảo sát hiện trạng (bản nháp, 7 biểu mẫu) + BPMN tổng quan và 4 quy trình còn lại, AS-IS/TO-BE (wave 2)
- [x] 01-04-PLAN.md — Bảng yêu cầu chức năng/phi chức năng + sơ đồ UC tổng quát + đặc tả UC2–UC5, UC0 (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 01-05-PLAN.md — Sơ đồ lớp + máy trạng thái, CSDL thesis_core/thesis_ai, kiến trúc SOA + sequence AI (wave 3)
- [x] 01-06-PLAN.md — 13 màn mockup HTML/CSS còn lại (tổng 14, dùng skill ui-ux-pro-max + design-taste-frontend) + ảnh PNG chụp bằng headless Chrome (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*
- [ ] 01-07-PLAN.md — Truy vết hoàn chỉnh + lắp chương; checkpoint dữ liệu khảo sát thật; đối chiếu dữ liệu thật (cập nhật mockup nếu biểu mẫu thật đổi trường) (wave 4, có checkpoint)

**UI hint**: yes
**Notes**:
- Khảo sát thực tế (ANLS-01) phụ thuộc người thật (bộ môn, GV, SV): lên lịch phỏng vấn ngay T1.
- File mẫu chính thức thu thập ở đây là đầu vào cho luật lọc phần mẫu chung (AISV-04) ở Phase 4; ~20 đồ án thật dùng để so sánh model embedding và hiệu chỉnh ngưỡng.
- Chốt ngay ở T4 để tránh sửa lại về sau: MySQL `utf8mb4_vietnamese_ci`, chuẩn hóa Unicode NFC tại mọi biên nhập liệu, embedding tính sẵn và lưu trong schema riêng của dịch vụ AI.

### Phase 2: Platform, RBAC & Topic Management

**Goal**: Hệ thống chạy thật sau Apache HTTPS; SV, GV và Bộ môn đăng nhập và đi trọn UC Quản lý đề tài, với mọi quyền truy cập được kiểm tra phía server
**Mode:** mvp
**Depends on**: Phase 1 (cần DSGN-01..03: sơ đồ lớp, CSDL, kiến trúc)
**Target window**: T6 (02/11–08/11/2026): CSDL + API. Dựng khung + Apache có thể bắt đầu từ T4–T5 khi DSGN-01..03 đã có bản nháp
**Requirements**: DEPL-01, DEPL-02, AUTH-01, AUTH-02, AUTH-03, AUTH-04, DATA-01, TOPC-01, TOPC-02, TOPC-03, TOPC-04
**Success Criteria** (what must be TRUE):
  1. Người dùng mở hệ thống qua HTTPS trên Apache: client React được phục vụ tĩnh, `/api` được proxy sang Web API; CSDL MySQL 8 (utf8mb4) được tạo hoàn toàn bằng migration, và tên tiếng Việt có dấu hiển thị, tìm kiếm, sắp xếp đúng
  2. Bất kỳ tài khoản nào trong 100 SV + 30 GV đã seed và tài khoản Bộ môn đều đăng nhập được bằng mã hoặc email + mật khẩu, reload trình duyệt vẫn giữ phiên, đăng xuất được từ mọi trang; Bộ môn tạo/sửa/khóa tài khoản SV/GV (tài khoản bị khóa không đăng nhập được) và mở/đóng đợt đồ án theo khóa
  3. GV đề xuất đề tài vào đợt đang mở; SV tự đề xuất hoặc đăng ký một đề tài GV còn trống; Bộ môn duyệt/từ chối kèm lý do và phân công GVHD; mọi vai trò xem danh sách đề tài theo trạng thái (nháp → chờ duyệt → đã duyệt/từ chối → đã phân công) và lọc theo đợt, GV
  4. Hệ thống chặn một SV có 2 đề tài đang hoạt động và chặn 2 SV cùng một đề tài, kể cả khi 2 SV đăng ký cùng lúc
  5. Gọi API trực tiếp (bỏ qua UI) bằng token sai vai trò hoặc để truy cập dữ liệu không thuộc quyền sở hữu đều bị từ chối, ví dụ SV không duyệt được đề tài, GV không sửa được đề tài của GV khác

**Plans**: 6/6 plans executed (tuần tự — dùng chung một stack Docker Compose và schema MySQL test)
Plans:
**Wave 1**
- [x] 02-01-PLAN.md — TRACER: docker compose (MySQL 8.4 + FastAPI + Apache HTTPS) → React MH-01 → /api/auth/login (Alembic 0001); refresh/logout/me, require_role trên mọi route, throttle, pytest trên MySQL thật

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-02-PLAN.md — Khung ứng dụng (giữ phiên khi reload, đăng xuất mọi trang, menu theo vai trò, 403) + Bộ môn quản lý tài khoản SV/GV (khóa/mở khóa) + tra cứu GV

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 02-03-PLAN.md — Bộ môn mở/đóng đợt đồ án (Alembic 0002) + seed 100 SV / 30 GV / Bộ môn / đợt đang mở

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 02-04-PLAN.md — Đề xuất đề tài GV/SV (MH-06, Alembic 0003, cột bổ sung ly_do_tu_choi ghi ngược vào ERD) + cảnh báo trùng tên qua AI stub (Alembic 0004, ngưỡng, lưu kết quả)

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 02-05-PLAN.md — Danh sách/lọc đề tài theo vai trò (MH-05) + SV đăng ký đề tài có sẵn với test đồng thời (1 SV:1 đề tài, 1 đề tài:1 SV)

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 02-06-PLAN.md — Bộ môn duyệt/phân công GVHD/từ chối (MH-07) + dashboard 3 vai trò (MH-02/03/04) + e2e UC1 và smoke qua Apache

**UI hint**: yes
**Notes**:
- Lời gọi kiểm tra trùng tên đề tài đi qua AI client stub (trả kết quả giả lập) cho đến Phase 4.
- Seed 100 SV + 30 GV (PI 4.2) đặt ở đây thay vì T9 để kiểm thử phân quyền và các UC sau với người dùng thực tế.
- DEPL-02 dựng Apache ngay trong lát cắt đầu tiên (không đợi T9) để phát hiện sớm lỗi proxy, upload và timeout.

### Phase 3: Outline, Progress, Defense & Archive

**Goal**: Sau khi đề tài được phân công, SV, GVHD và Bộ môn đi trọn quy trình đề cương → tiến độ → bảo vệ → lưu kho trên Web, có thông báo in-app ở mỗi bước chuyển trạng thái
**Mode:** mvp
**Depends on**: Phase 2
**Target window**: T7 (09/11–15/11/2026): 5 UC (UC1 đã xong ở Phase 2)
**Requirements**: OUTL-01, OUTL-02, OUTL-03, PROG-01, PROG-02, PROG-03, DEFN-01, DEFN-02, DEFN-03, DEFN-04, REPO-01, REPO-02, REPO-03, NOTF-01
**Success Criteria** (what must be TRUE):
  1. SV đã được duyệt đề tài nộp đề cương DOCX/PDF (file sai định dạng hoặc quá dung lượng bị từ chối), mỗi lần nộp lại tạo phiên bản mới; GVHD mở màn hình duyệt thấy đề cương cùng khung kết quả kiểm tra trùng lặp (dữ liệu stub), duyệt hoặc yêu cầu sửa kèm nhận xét, và vòng sửa → nộp lại lặp đến khi được duyệt
  2. SV nộp báo cáo tiến độ theo các mốc cố định của đợt (nội dung + file tùy chọn); GVHD nhận xét và đánh giá từng báo cáo; Bộ môn xem dashboard tiến độ của toàn bộ SV, SV trễ mốc được đánh dấu rõ
  3. SV nộp báo cáo cuối (lần nộp kích hoạt kiểm tra trùng lặp qua stub); Bộ môn lập hội đồng từ các GV, xếp ngày/giờ/phòng và danh sách SV; GV trong hội đồng chỉ thấy báo cáo của SV thuộc hội đồng mình và nhập điểm + nhận xét; hệ thống tính điểm bằng trung bình cộng, Bộ môn chốt, SV xem được lịch và kết quả của mình
  4. Đồ án đã chốt kết quả tự xuất hiện trong kho với đủ metadata; người dùng tìm/lọc kho theo khóa, từ khóa, GVHD và xem chi tiết; Bộ môn thêm/sửa/xóa và import bản ghi các khóa cũ, mỗi bản ghi mới phát sinh lời gọi index sang AI client
  5. Người dùng thấy thông báo in-app (số chưa đọc + danh sách) khi đề tài/đề cương được duyệt hoặc từ chối, khi có nhận xét mới, và khi được phân vào hội đồng hoặc có lịch bảo vệ

**Plans**: 2/7 plans executed (tuần tự — dùng chung một stack Docker Compose và schema MySQL test; thứ tự theo D-09: đề cương → bảo vệ → kho, rồi tiến độ và thông báo)
Plans:
**Wave 1**
- [x] 03-01-PLAN.md — TRACER: SV nộp đề cương → lưu (volume riêng) + trích xuất → kiểm tra stub nền DANG_KIEM_TRA→HOAN_TAT → GVHD duyệt → thông báo (Alembic 0006, cột bổ sung noi_dung_trich_xuat/trich_xuat_loi ghi ngược ERD); vòng yêu cầu sửa, tải file, kiểm tra lại, 4 test; deploy/e2e-uc2-5.sh

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-02-PLAN.md — Màn MH-08 (nộp + lịch sử phiên bản + nhận xét), MH-09 (duyệt với khung kiểm tra trùng lặp polling), MH-14 (chi tiết kết quả); tải file có xác thực

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 03-03-PLAN.md — SV nộp báo cáo cuối (kiểm tra trùng lặp nền) + Bộ môn lập hội đồng, xếp lịch, chặn GVHD ngồi hội đồng SV mình (Alembic 0007, MH-11)

**Wave 4** *(blocked on Wave 3 completion)*
- [ ] 03-04-PLAN.md — GV hội đồng chấm điểm (403 ngoài hội đồng), Bộ môn chốt TB cộng → tự lưu kho + ingest AI stub, SV xem lịch/kết quả (Alembic 0008, MH-12)

**Wave 5** *(blocked on Wave 4 completion)*
- [ ] 03-05-PLAN.md — Kho đồ án: tìm/lọc theo khóa, từ khóa, GVHD, xem chi tiết + tải báo cáo; Bộ môn thêm/sửa/xóa, index lại, import CSV khóa cũ (MH-13)

**Wave 6** *(blocked on Wave 5 completion)*
- [ ] 03-06-PLAN.md — Tiến độ: Bộ môn thiết lập mốc, SV nộp báo cáo theo mốc (file tùy chọn), GVHD nhận xét/đánh giá, dashboard tiến độ toàn khoa đánh dấu SV trễ mốc (Alembic 0009, MH-10)

**Wave 7** *(blocked on Wave 6 completion)*
- [ ] 03-07-PLAN.md — Chuông thông báo (số chưa đọc, danh sách, đánh dấu đã đọc, polling 30 s) + thông báo duyệt/từ chối đề tài; widget Phase 3 trên dashboard MH-02/03/04; smoke + e2e + README demo UC2–UC5

**UI hint**: yes
**Notes**:
- AI client vẫn là stub; khung kết quả kiểm tra và trạng thái "đang kiểm tra / hoàn tất" được dựng sẵn để Phase 4 chỉ cần thay stub.
- Phase lớn nhất (14 yêu cầu): chia plan theo UC. Nếu trễ, giữ chuỗi đề cương → bảo vệ → kho chạy trước vì đó là đường demo chính.

### Phase 4: AI Similarity Service

**Goal**: SV và GVHD nhận cảnh báo trùng lặp thật (đề tài tương tự kèm tỷ lệ khi đăng ký; đoạn trùng, đồ án trùng và tỷ lệ tương đồng khi nộp đề cương/báo cáo) với ngưỡng đã được kiểm chứng trên bộ dữ liệu có cặp trùng chủ đích
**Mode:** mvp
**Depends on**: Phase 3
**Target window**: T8 (16/11–22/11/2026): AI. Seed 300 đề tài + 50 file (PI 4.2) làm cùng phase này để làm corpus và tập hiệu chỉnh ngưỡng
**Requirements**: AISV-01, AISV-02, AISV-03, AISV-04, AISV-05, AISV-06, AISV-07, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. Khi SV đăng ký/đề xuất một đề tài có tên diễn đạt khác nhưng cùng nghĩa với một đề tài trong kho 300 đề tài đã seed, SV thấy top đề tài tương tự kèm tỷ lệ % trong ngưỡng thời gian NFR; cùng một tên nhập ở dạng Unicode tổ hợp (NFD) hay dựng sẵn (NFC) đều cho cùng kết quả
  2. Khi SV nộp đề cương/báo cáo, UI hiện trạng thái "đang kiểm tra" rồi "hoàn tất"; kết quả gồm tỷ lệ tương đồng tổng, danh sách đồ án trùng và từng đoạn trùng được highlight cạnh đoạn nguồn, và GVHD thấy cùng kết quả ngay trên màn hình duyệt; tiêu đề mẫu, mục lục và tài liệu tham khảo không bị tính là trùng
  3. Trên bộ 50 file thử nghiệm, các cặp chép nguyên văn và diễn đạt lại bị cảnh báo, còn cặp cùng lĩnh vực khác đề tài và cặp không liên quan nằm dưới ngưỡng; bảng kết quả kiểm chứng (điểm từng cặp, model embedding được chọn sau khi so sánh) được lưu để đưa vào báo cáo
  4. Bộ môn đổi ngưỡng cảnh báo cho tên đề tài và cho nội dung trên UI, và lần kiểm tra kế tiếp áp dụng ngưỡng mới
  5. Dịch vụ AI không truy cập được từ bên ngoài qua Apache và từ chối request thiếu API key nội bộ; bản ghi kho mới thêm được index ngay và xuất hiện trong lần kiểm tra kế tiếp mà không phải tính lại embedding toàn kho

**Plans**: TBD
**UI hint**: yes
**Notes**:
- Mở đầu phase bằng so sánh model embedding (bkai vietnamese-bi-encoder + tách từ underthesea so với multilingual-e5) trên tập nhỏ các cặp đã biết giống/khác; timebox và chốt model trước khi nối UI.
- Thiết kế phổ cặp trùng của 50 file (chép nguyên văn / diễn đạt lại / cùng lĩnh vực khác đề tài / không liên quan) và các cụm chủ đề của 300 đề tài cùng lúc với thiết kế AI; tách riêng một phần cặp làm tập kiểm chứng để bảng kết quả không chỉ phản ánh dữ liệu đã dùng để chỉnh ngưỡng.
- Phù hợp chạy `/gsd-ai-integration-phase` trước khi plan.
- Nếu hết T8 mà hiệu chỉnh chưa đạt: ghi nhận giới hạn vào báo cáo và chuyển sang Phase 5, vì 5 UC chạy end-to-end quan trọng hơn độ hoàn hảo của AI.

### Phase 5: System Verification & Defense Package

**Goal**: Hệ thống hoàn chỉnh chạy trên server với đầy đủ dữ liệu thử nghiệm, kịch bản demo chạy trơn tru, quyển báo cáo và slide sẵn sàng nộp và bảo vệ trước 07/12/2026
**Mode:** mvp
**Depends on**: Phase 4
**Target window**: T9–T10 (23/11–07/12/2026): T9 triển khai/seed/kiểm thử · T10 báo cáo + slide
**Requirements**: RPRT-01, RPRT-02
**Success Criteria** (what must be TRUE):
  1. Trên server sau Apache HTTPS có đủ dữ liệu seed (100 SV, 30 GV, 300 đề tài, 50 file), một lượt demo đi trọn 5 UC cho cả 3 vai trò, từ đăng ký đề tài có cảnh báo trùng đến chốt điểm và tra cứu kho, không phát sinh lỗi
  2. Thời gian phản hồi kiểm tra trùng tên đề tài và kiểm tra tài liệu, đo trên server với toàn bộ kho, đạt ngưỡng NFR đã chốt ở ANLS-04; số liệu đo nằm trong chương Triển khai
  3. Quyển báo cáo 4 chương đúng khuôn mẫu trường (Cơ sở lý thuyết; Khảo sát & phân tích; Thiết kế; Triển khai kèm hướng dẫn cài đặt và kết quả thử nghiệm), mỗi deliverable truy vết được về mã PI 1.1–4.2
  4. Slide bảo vệ và kịch bản demo end-to-end hoàn chỉnh, đã được chạy tập lại ít nhất một lần trên hệ thống thật theo đúng kịch bản

**Plans**: TBD
**Notes**:
- Chương 2–3 lấy trực tiếp từ hồ sơ Phase 1; chương 1 (Cơ sở lý thuyết) nên viết dần từ T4 để giảm tải T10.
- Hạn 07/12/2026 là thứ Hai ngay sau T10, không có tuần đệm; lỗi phát hiện ở T9 cần sửa xong trước giữa T10.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Analysis & Design | 6/7 | In Progress|  |
| 2. Platform, RBAC & Topic Management | 6/6 | In Progress|  |
| 3. Outline, Progress, Defense & Archive | 2/7 | In Progress|  |
| 4. AI Similarity Service | 0/TBD | Not started | - |
| 5. System Verification & Defense Package | 0/TBD | Not started | - |
