# Phase 1: Analysis & Design - Context

**Gathered:** 2026-09-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase này làm ra bộ tài liệu phân tích & thiết kế (CLO 1–2, PI 1.1–2.3) cho hệ thống quản lý đồ án Khoa CNTT ICTU. Phải hoàn chỉnh và truy vết được, đủ để các phase 2–4 thi công mà không phải đoán quy trình, schema, kiến trúc hay giao diện. Không có code ứng dụng.

Requirements: ANLS-01..05, DSGN-01..04. Khung thời gian T1–T5 (28/09–01/11/2026):
- T1: khảo sát + BPMN
- T2–T3: bảng yêu cầu + UC
- T4: thiết kế dữ liệu + kiến trúc
- T5: mockup + thu thập kho

</domain>

<decisions>
## Implementation Decisions

### Nguồn khảo sát (ANLS-01, ANLS-02)
- **D-01:** Khảo sát lấy từ **phỏng vấn thật kết hợp tài liệu**.
  - SV (Mai Anh) phỏng vấn bộ môn, GV và SV.
  - Claude soạn bộ câu hỏi phỏng vấn và phiếu khảo sát cho từng vai trò, kèm mẫu biên bản.
  - Sau đó Claude tổng hợp kết quả từ biên bản và quy định của trường.
- **D-02:** **Hiện chưa có tài liệu gốc nào**: không có quy chế, form mẫu hay đồ án khóa trước. Plan phải có task **thu thập**, gồm:
  - Checklist cần xin: quy chế đồ án, phiếu đăng ký, mẫu đề cương/báo cáo chính thức, phiếu chấm, biên bản hội đồng, ~20 đồ án thật.
  - Chỗ lưu trong repo cho các tài liệu đó.
  - Tài liệu mẫu chính thức là đầu vào cho bộ lọc phần mẫu chung (AISV-04) ở Phase 4.
  - Plan phải có **checkpoint chờ người thật**: Claude không tự phỏng vấn được. Nếu chưa có dữ liệu thật thì soạn bản nháp đánh dấu rõ "giả định, chờ xác nhận".
- **D-03:** BPMN gồm **1 sơ đồ tổng quan và 5 quy trình con** khớp 5 UC (Đề tài, Đề cương, Tiến độ, Bảo vệ, Kho). Mỗi sơ đồ có swimlane SV / GV / Bộ môn.
- **D-04:** Mô tả **cả AS-IS lẫn TO-BE**.
  - AS-IS: quy trình hiện tại, làm cơ sở khảo sát (PI 1.1).
  - TO-BE: quy trình trên hệ thống, có các bước kiểm tra trùng lặp bằng AI.

### Công cụ & phạm vi sơ đồ (ANLS-05, DSGN-01..03)
- **D-05:** Sơ đồ UML và ERD (UC, lớp, component/deployment, sequence, activity, sơ đồ CSDL) viết bằng **PlantUML** trong repo, xuất PNG/SVG. **BPMN vẽ bằng draw.io** (file `.drawio` lưu trong repo, xuất PNG), vì PlantUML không hỗ trợ BPMN chuẩn. — **Reversibility:** reversible
- **D-06:** Đặc tả UC gồm **5 UC chính, mỗi UC tách thành UC con** (vd. UC1: Đề xuất đề tài, Đăng ký đề tài, Duyệt đề tài & phân công GVHD).
  - Mỗi UC con có bảng đặc tả: tác nhân, tiền/hậu điều kiện, luồng chính, luồng thay thế/ngoại lệ.
  - Các UC quan trọng có thêm activity hoặc sequence diagram.
- **D-07:** Có **sequence diagram cho luồng AI kiểm tra trùng lặp**: check-title đồng bộ và check-document bất đồng bộ, qua Web API ↔ dịch vụ AI. Sơ đồ này minh chứng cho SOA (PI 2.2).

### Định dạng & tổ chức tài liệu
- **D-08:** Viết bằng **Markdown trong `docs/`**, tiếng Việt. Cuối cùng dùng pandoc cùng template `.docx` của trường để xuất quyển báo cáo (RPRT-01 ở Phase 5). — **Reversibility:** costly — nếu đổi sang viết thẳng Word thì phải chuyển toàn bộ nội dung đã viết
- **D-09:** Cấu trúc thư mục **bám theo chương báo cáo**:
  - `docs/chuong-2-khao-sat-phan-tich/`: khảo sát, BPMN, yêu cầu chức năng/phi chức năng, UC
  - `docs/chuong-3-thiet-ke/`: sơ đồ lớp, CSDL, kiến trúc, mockup
  - Mỗi mục là một file, để sau ghép thẳng thành quyển.
  - Nguồn sơ đồ và ảnh xuất đặt cạnh file markdown tương ứng.
- **D-10:** Có **bảng truy vết** PI → mục tài liệu → requirement ID, để GVHD kiểm tra theo tiêu chí chấm. Vị trí gợi ý: `docs/truy-vet.md`.

### Mockup Figma (DSGN-04)
- **D-11:** **Claude dựng mockup trực tiếp trong Figma qua Figma MCP**, SV chỉnh sửa sau. Link file Figma ghi vào tài liệu chương 3.
- **D-12:** Phong cách là **Ant Design admin** (sidebar + bảng + form), khớp với thư viện sẽ code ở Phase 2–4 để mockup sát sản phẩm thật.
- **D-13:** Thiết kế **chỉ cho desktop**, khung 1440px.
- **D-14:** Khoảng **12–15 màn chính**:
  - đăng nhập
  - dashboard cho từng vai trò (SV, GV, Bộ môn)
  - danh sách/đăng ký/đề xuất đề tài, có cảnh báo tên trùng
  - duyệt đề tài & phân công GVHD
  - nộp đề cương và màn duyệt đề cương có panel kết quả trùng lặp
  - báo cáo tiến độ + nhận xét
  - lập hội đồng/xếp lịch
  - chấm điểm
  - kho đồ án (tìm kiếm)
  - chi tiết kết quả kiểm tra trùng lặp (tỷ lệ tổng, đồ án trùng, highlight đoạn trùng cạnh đoạn nguồn)

### Mang sang từ khởi tạo project (đã chốt)
- 3 vai trò SV / GV / Bộ môn. Hội đồng là GV được phân công, không có role riêng.
- 1 SV : 1 đề tài : 1 GVHD. Cả GV và SV đều đề xuất được đề tài.
- Điểm bảo vệ là trung bình cộng điểm các thành viên. Có thông báo in-app. Bộ môn cấu hình được ngưỡng trùng lặp.
- Stack: FastAPI + SQLAlchemy 2.0 (sync) + MySQL 8 `utf8mb4_vietnamese_ci`; React + Ant Design. Dịch vụ AI là FastAPI riêng, embedding local, không public qua Apache.
- Kiến trúc chốt từ research, cần thể hiện trong DSGN-01..03:
  - Dịch vụ AI có schema MySQL riêng (`thesis_ai`), Web API giữ `thesis_core`.
  - Web API đẩy corpus sang dịch vụ AI qua `/ingest`.
  - Web API gọi dịch vụ AI bằng API key nội bộ; JWT của người dùng dừng ở Web API.
  - Embedding tính sẵn lúc ingest.
  - Chuẩn hóa Unicode NFC ở mọi điểm nhập liệu.
- NFR đề xuất cho ANLS-04: kiểm tra tên đề tài ≤ 5 giây, kiểm tra tài liệu ≤ 30 giây.

### Claude's Discretion
- Câu hỏi phỏng vấn và phiếu khảo sát cụ thể; cách trình bày bảng yêu cầu chức năng/phi chức năng.
- Danh sách thực thể và thuộc tính chi tiết, trạng thái (state machine) của đề tài và đề cương, với điều kiện khớp các quyết định đã chốt.
- Cách chia UC con, chọn UC nào vẽ activity/sequence (bắt buộc có luồng AI theo D-07).
- Bố cục và nội dung chi tiết từng màn mockup trong khuôn Ant Design.
- Tên file và thứ tự mục trong từng chương.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Đề cương & tiêu chí chấm
- `H01.DTC235200036.NguyenThiMaiAnh.docx`: đề cương gốc. Mục 6 là CLO/PI, mục 7b là yêu cầu tối thiểu từng PI, mục 8 là cấu trúc báo cáo 4 chương, mục 9 là tiến độ 10 tuần. Đọc bằng `pandoc -t plain`.

### Project planning
- `.planning/PROJECT.md`: bối cảnh, ràng buộc, Key Decisions
- `.planning/REQUIREMENTS.md`: ANLS-01..05, DSGN-01..04 và toàn bộ 45 req v1 (bảng yêu cầu chức năng phải phủ các req này)
- `.planning/ROADMAP.md` § Phase 1: success criteria và ghi chú T4

### Research (đầu vào cho thiết kế)
- `.planning/research/ARCHITECTURE.md`: ranh giới component, luồng dữ liệu, sync/async, schema ownership (đầu vào cho DSGN-03 và sequence ở D-07)
- `.planning/research/FEATURES.md`: bản đồ vai trò × UC (đầu vào cho UC và mockup)
- `.planning/research/PITFALLS.md`: NFC/utf8mb4, lọc phần mẫu chung, NFR thời gian phản hồi (đầu vào cho ANLS-04, DSGN-02)
- `.planning/research/STACK.md`: công nghệ cho sơ đồ deployment
- `.planning/research/SUMMARY.md`: tổng hợp

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Chưa có code. Repo mới gồm đề cương `.docx` và `.planning/`.

### Established Patterns
- Chưa có. Quy ước tài liệu được đặt ra lần đầu ở phase này (D-08, D-09).

### Integration Points
- Sơ đồ CSDL (DSGN-02) là nguồn cho migration Alembic ở Phase 2 (DEPL-01).
- Mockup (DSGN-04) là nguồn cho UI React ở Phase 2–4.
- Tài liệu mẫu thu thập được (D-02) là nguồn cho bộ lọc phần mẫu chung ở Phase 4.

</code_context>

<specifics>
## Specific Ideas

- Màn kết quả trùng lặp tham khảo kiểu báo cáo Turnitin/Coopy: tỷ lệ tổng, danh sách nguồn trùng, đoạn trùng highlight cạnh đoạn nguồn.
- Mọi tài liệu phải ghi rõ mã PI tương ứng để GVHD chấm theo tiêu chí.

</specifics>

<deferred>
## Deferred Ideas

- Mockup mobile: đã quyết định chỉ làm desktop. Nếu có thời gian, cân nhắc sau Phase 5.
- Mockup đầy đủ mọi màn CRUD phụ (~25+): hiện chỉ làm màn chính.

</deferred>

---

*Phase: 01-analysis-design*
*Context gathered: 2026-09-27*
