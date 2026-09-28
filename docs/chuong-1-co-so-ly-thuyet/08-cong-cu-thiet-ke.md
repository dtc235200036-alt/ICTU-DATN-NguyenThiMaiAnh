## 1.8. Công cụ mô hình hóa và thiết kế: BPMN, UML/PlantUML, draw.io và HTML prototype

> **Mã PI:** — — **Yêu cầu:** —

### 1.8.1. BPMN

BPMN (Business Process Model and Notation) là một chuẩn ký hiệu đồ họa (do Object Management Group — OMG duy trì) để mô hình hóa **quy trình nghiệp vụ**: các bước xử lý (task), sự kiện bắt đầu/kết thúc (event), điểm rẽ nhánh quyết định (gateway), và các "làn bơi" (pool/lane) phân định tác nhân nào (Sinh viên, Giảng viên hướng dẫn, Bộ môn...) chịu trách nhiệm cho bước nào trong quy trình. Một cách dùng phổ biến khi khảo sát cải tiến quy trình là vẽ hai phiên bản song song: **AS-IS** (quy trình đang vận hành trong thực tế, thường thủ công) và **TO-BE** (quy trình sau khi có hệ thống hỗ trợ) — đặt cạnh nhau để làm rõ hệ thống mới thay đổi/tự động hóa cụ thể bước nào của quy trình cũ.

### 1.8.2. UML và PlantUML

UML (Unified Modeling Language) là một họ ký hiệu đồ họa chuẩn hóa (cũng do OMG duy trì) để mô hình hóa các khía cạnh khác nhau của một hệ thống phần mềm, trong đó đồ án này dùng: **sơ đồ use case** (tác nhân và các chức năng hệ thống cung cấp cho từng tác nhân, cùng bản đặc tả luồng sự kiện chi tiết cho mỗi use case), **sơ đồ lớp (class diagram)** để mô hình hóa các thực thể dữ liệu và quan hệ giữa chúng, **sơ đồ thành phần (component diagram)** và **sơ đồ triển khai (deployment diagram)** để thể hiện kiến trúc SOA (ranh giới dịch vụ, tiến trình nào chạy ở đâu), và **sơ đồ tuần tự (sequence diagram)** để thể hiện thứ tự trao đổi thông điệp giữa các thành phần theo thời gian — đặc biệt hữu ích khi cần phân biệt một luồng xử lý đồng bộ với một luồng bất đồng bộ. PlantUML là một công cụ mã nguồn mở dựng các sơ đồ UML (và một số loại sơ đồ khác) từ một đoạn văn bản mô tả theo cú pháp riêng, thay vì kéo-thả hình vẽ bằng chuột — cách tiếp cận "diagram-as-code" này cho phép lưu sơ đồ dưới dạng văn bản thuần trong hệ thống quản lý phiên bản (Git), dễ so sánh (diff) và tái tạo lại chính xác khi cần chỉnh sửa.

### 1.8.3. draw.io

draw.io (còn gọi là diagrams.net) là một công cụ vẽ sơ đồ dạng kéo-thả trực quan, hỗ trợ sẵn bộ ký hiệu chuẩn BPMN, lưu định dạng file `.drawio` (XML) đồng thời xuất được ảnh PNG/SVG để nhúng vào tài liệu. So với PlantUML (phù hợp cho sơ đồ có cấu trúc quan hệ rõ ràng, sinh tự động từ văn bản), draw.io phù hợp hơn cho sơ đồ quy trình nghiệp vụ (BPMN) nơi cách bố trí không gian của các làn bơi và luồng rẽ nhánh mang nhiều ý nghĩa trực quan, thường cần tinh chỉnh vị trí thủ công để dễ đọc.

### 1.8.4. HTML prototype thay thế Figma

Figma là công cụ thiết kế giao diện (UI design) phổ biến để dựng mockup/wireframe có độ trung thực cao trước khi lập trình. Trong phạm vi đồ án này, mockup các màn hình chính được dựng thay thế bằng các trang **HTML/CSS tĩnh**, dùng chung một stylesheet mô phỏng đúng ngôn ngữ thiết kế và tên class của Ant Design (§1.4.4) — cách làm này đạt được mục tiêu cốt lõi của một bản mockup (thể hiện đúng bố cục, thành phần giao diện và luồng thao tác của từng màn hình để trao đổi trước khi lập trình) mà không cần công cụ thiết kế chuyên dụng, đồng thời có lợi thế phụ là tên class trong bản mockup trùng khớp trực tiếp với tên component sẽ dùng khi lập trình viên chuyển sang React thật, giảm sai lệch giữa bản thiết kế và bản thi công.

### 1.8.5. Áp dụng trong đồ án

Bộ công cụ trên được dùng đúng theo từng loại sơ đồ mà nó phù hợp nhất, tương ứng với các mục ở Chương 2 và Chương 3: draw.io cho toàn bộ sơ đồ BPMN AS-IS/TO-BE (một sơ đồ tổng quan và năm quy trình con — Đề tài, Đề cương, Tiến độ, Bảo vệ, Kho dữ liệu đồ án — lưu tại `docs/chuong-2-khao-sat-phan-tich/bpmn/`); PlantUML cho sơ đồ use case và sơ đồ hoạt động (`docs/chuong-2-khao-sat-phan-tich/uc/`), sơ đồ lớp thực thể (`docs/chuong-3-thiet-ke/so-do-lop/`), sơ đồ thực thể-quan hệ CSDL — ERD (`docs/chuong-3-thiet-ke/csdl/erd.puml`) — và sơ đồ kiến trúc (thành phần, triển khai, tuần tự cho hai luồng kiểm tra trùng lặp đồng bộ/bất đồng bộ, tại `docs/chuong-3-thiet-ke/kien-truc/`); và 14 trang HTML/CSS tĩnh dùng quy ước tên class Ant Design thay cho Figma (`docs/chuong-3-thiet-ke/mockup/mh-01.html` … `mh-14.html`, cùng stylesheet `antd-admin.css`) cho các màn hình chính của cả ba vai trò. Toàn bộ sơ đồ và mockup được render và kiểm tra tự động bằng script `tools/render-diagrams.sh` (xuất PNG từ `.puml`/`.drawio`, chụp ảnh các trang mockup) để phát hiện sớm lỗi cú pháp hoặc nội dung bị tràn/cắt trước khi đưa vào quyển báo cáo.
