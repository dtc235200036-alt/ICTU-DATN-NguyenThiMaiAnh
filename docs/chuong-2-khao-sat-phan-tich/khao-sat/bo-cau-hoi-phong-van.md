# Phụ lục B. Bộ câu hỏi phỏng vấn

> **Mã PI:** 1.1 — **Yêu cầu:** ANLS-01

## Mục đích và cách dùng

Bộ câu hỏi này phục vụ khảo sát quy trình quản lý đồ án/khóa luận tốt nghiệp thực tế của Khoa Công nghệ thông tin (ANLS-01), làm cơ sở cho sơ đồ BPMN AS-IS, bảng yêu cầu chức năng/phi chức năng và thiết kế dữ liệu ở các phần sau của Chương 2–3.

Hình thức phỏng vấn: bán cấu trúc (semi-structured), khoảng 20–30 phút mỗi người, có thể phỏng vấn trực tiếp hoặc trực tuyến. Người phỏng vấn không nhất thiết phải hỏi đúng thứ tự hay đúng từng chữ — có thể hỏi thêm để làm rõ, miễn giữ đúng nội dung cốt lõi của từng câu.

Mỗi câu hỏi được gắn:
- **Mã** — định danh để tra cứu chéo với mẫu biên bản (Phụ lục D);
- **Quy trình** — một trong `DT` (đề tài), `DC` (đề cương), `TD` (tiến độ), `BV` (nộp báo cáo & bảo vệ), `KHO` (kho đồ án), `CHUNG` (chung, không thuộc riêng quy trình nào);
- **Dùng cho** — tài liệu/đầu ra sẽ dùng câu trả lời này (BPMN AS-IS, Yêu cầu chức năng, Yêu cầu phi chức năng, Biểu mẫu dữ liệu, Thiết kế CSDL).

Trước khi hỏi, người phỏng vấn xin phép ghi chép/ghi âm và giải thích câu trả lời sẽ được ẩn danh (chỉ lưu theo mã vai trò, ví dụ `BM-01`, `GV-01`, `SV-01`) — xem thêm Phụ lục A mục A.5 và mẫu biên bản Phụ lục D.

## B.1. Phỏng vấn Bộ môn / Văn phòng Khoa

| Mã | Câu hỏi | Quy trình | Dùng cho |
|----|---------|-----------|----------|
| Q-BM-01 | Xin anh/chị mô tả các mốc thời gian chính của một đợt đồ án tốt nghiệp, từ lúc mở đợt đến khi có kết quả bảo vệ cuối cùng? | DT | BPMN AS-IS |
| Q-BM-02 | Đề tài do ai đề xuất (giảng viên, sinh viên hay cả hai)? Bộ môn duyệt đề tài dựa trên những tiêu chí nào? | DT | BPMN AS-IS |
| Q-BM-03 | Quy tắc phân công GVHD cho sinh viên như thế nào? Mỗi giảng viên được nhận tối đa bao nhiêu sinh viên/đề tài trong một đợt? | DT | Yêu cầu chức năng |
| Q-BM-04 | Đề cương của sinh viên chỉ cần GVHD duyệt, hay Bộ môn cũng phải xác nhận thêm một bước nữa? | DC | BPMN AS-IS |
| Q-BM-05 | Hiện nay Bộ môn theo dõi tiến độ làm đồ án của sinh viên bằng cách nào (báo cáo định kỳ, họp giao ban, email...)? | TD | BPMN AS-IS |
| Q-BM-06 | Báo cáo cuối cùng sinh viên nộp ở định dạng nào (bản cứng/bản mềm)? Ngưỡng kiểm tra trùng lặp/Turnitin hiện đang áp dụng là bao nhiêu phần trăm? | BV | Yêu cầu phi chức năng |
| Q-BM-07 | Hội đồng bảo vệ gồm bao nhiêu thành viên, vai trò của từng người là gì? Hội đồng được thành lập và xếp lịch như thế nào? | BV | BPMN AS-IS |
| Q-BM-08 | Cách chấm điểm bảo vệ hiện nay: dùng phiếu chấm nào, trọng số tính điểm ra sao, ai là người tổng hợp điểm cuối cùng? | BV | Biểu mẫu dữ liệu |
| Q-BM-09 | Đồ án sau khi hoàn thành được lưu trữ ở đâu, dưới định dạng gì, và giữ trong khoảng bao nhiêu khóa? | KHO | Thiết kế CSDL |
| Q-BM-10 | Hiện Bộ môn đang dùng những biểu mẫu giấy/Excel nào trong quy trình (phiếu đăng ký, phiếu chấm, biên bản hội đồng...)? Anh/chị có thể cho em xin bản mẫu (bản photo hoặc file) của những biểu mẫu này không? | CHUNG | Biểu mẫu dữ liệu |
| Q-BM-11 | Công cụ nào đang được dùng để quản lý quy trình hiện nay (Excel, email, Google Drive, Zalo, phần mềm khác...)? | CHUNG | BPMN AS-IS |
| Q-BM-12 | Theo anh/chị, đâu là điểm bất tiện hoặc khó khăn nhất trong quy trình quản lý đồ án hiện nay? | CHUNG | Yêu cầu chức năng |
| Q-BM-13 | Em xin phép được nhận bản sao các văn bản/biểu mẫu chính thức (quy chế, mẫu đề cương, mẫu quyển báo cáo, phiếu chấm...) để đối chiếu khi xây dựng hệ thống — anh/chị hướng dẫn giúp em nên xin ở đâu và như thế nào? (xem thêm danh mục cần thu thập tại `tai-lieu-goc/README.md`) | CHUNG | Biểu mẫu dữ liệu |

## B.2. Phỏng vấn Giảng viên

| Mã | Câu hỏi | Quy trình | Dùng cho |
|----|---------|-----------|----------|
| Q-GV-01 | Thầy/cô đề xuất đề tài vào thời điểm nào trong đợt, và thường đề xuất khoảng bao nhiêu đề tài mỗi đợt? | DT | BPMN AS-IS |
| Q-GV-02 | Khi có nhiều sinh viên muốn đăng ký cùng một đề tài, thầy/cô chọn sinh viên theo tiêu chí nào? | DT | Yêu cầu chức năng |
| Q-GV-03 | Khi duyệt đề cương của sinh viên, thầy/cô kiểm tra những nội dung/mục nào là bắt buộc phải có? | DC | BPMN AS-IS |
| Q-GV-04 | Trung bình một đề cương phải chỉnh sửa lại bao nhiêu lần trước khi được duyệt? | DC | Yêu cầu chức năng |
| Q-GV-05 | Thầy/cô phản hồi nhận xét đề cương/tiến độ cho sinh viên qua kênh nào (viết tay trên giấy, email, gặp trực tiếp...)? | DC | BPMN AS-IS |
| Q-GV-06 | Tần suất sinh viên báo cáo tiến độ là bao lâu một lần, và báo cáo theo mẫu/nội dung như thế nào? | TD | Biểu mẫu dữ liệu |
| Q-GV-07 | Hiện nay thầy/cô kiểm tra trùng lặp/đạo văn của đề cương và báo cáo bằng cách nào (đọc thủ công, dùng phần mềm nào)? | CHUNG | Yêu cầu phi chức năng |
| Q-GV-08 | Khi tham gia hội đồng chấm bảo vệ, thầy/cô nhận báo cáo và phiếu chấm theo hình thức nào? Phiếu chấm gồm những tiêu chí gì? | BV | Biểu mẫu dữ liệu |
| Q-GV-09 | Nếu hệ thống đưa ra cảnh báo trùng lặp, thầy/cô cần thấy những thông tin gì để cảnh báo đó thật sự hữu ích (ví dụ: đoạn trùng cụ thể, đồ án nguồn, tỷ lệ phần trăm)? | CHUNG | Yêu cầu chức năng |
| Q-GV-10 | Với việc kiểm tra trùng tên đề tài, theo thầy/cô thời gian chờ kết quả bao lâu là chấp nhận được (vài giây hay có thể chờ lâu hơn)? | DT | Yêu cầu phi chức năng |
| Q-GV-11 | Với việc kiểm tra trùng nội dung đề cương/báo cáo (file dài hơn, cần thời gian xử lý hơn), thời gian chờ kết quả bao lâu là chấp nhận được? | DC | Yêu cầu phi chức năng |
| Q-GV-12 | Thầy/cô thường dùng công cụ/kênh nào để trao đổi với sinh viên hướng dẫn (email, Zalo, Google Drive...)? | CHUNG | BPMN AS-IS |
| Q-GV-13 | Theo thầy/cô, khó khăn lớn nhất hiện nay khi hướng dẫn hoặc chấm đồ án là gì? | CHUNG | Yêu cầu chức năng |
| Q-GV-14 | Em xin phép được nhận bản mẫu đề cương/báo cáo chính thức và các biểu mẫu liên quan mà thầy/cô đang dùng, để tham chiếu khi xây dựng hệ thống — thầy/cô có thể chia sẻ giúp em không? | CHUNG | Biểu mẫu dữ liệu |

## B.3. Phỏng vấn Sinh viên

| Mã | Câu hỏi | Quy trình | Dùng cho |
|----|---------|-----------|----------|
| Q-SV-01 | Bạn tìm hiểu và đăng ký đề tài như thế nào? Có hạn đăng ký cụ thể không? | DT | BPMN AS-IS |
| Q-SV-02 | Nếu muốn tự đề xuất đề tài của riêng mình, quy trình thực hiện ra sao? | DT | Yêu cầu chức năng |
| Q-SV-03 | Bạn lấy mẫu đề cương từ đâu? Sau khi nộp, thường phải chỉnh sửa lại bao nhiêu lần trước khi được duyệt? | DC | Biểu mẫu dữ liệu |
| Q-SV-04 | Bạn nhận phản hồi/nhận xét đề cương từ giảng viên hướng dẫn qua hình thức nào? | DC | BPMN AS-IS |
| Q-SV-05 | Bạn báo cáo tiến độ thực hiện đồ án theo hình thức/nội dung nào, và bao lâu một lần? | TD | Biểu mẫu dữ liệu |
| Q-SV-06 | Quy trình nộp báo cáo cuối cùng diễn ra như thế nào (nộp ở đâu, nộp bản gì)? | BV | BPMN AS-IS |
| Q-SV-07 | Lịch bảo vệ (ngày, giờ, phòng, hội đồng) được thông báo cho bạn bằng cách nào? | BV | BPMN AS-IS |
| Q-SV-08 | Bạn có thể tra cứu/tham khảo đồ án các khóa trước bằng cách nào hiện nay? | KHO | Yêu cầu chức năng |
| Q-SV-09 | Nếu hệ thống cho xem trước kết quả kiểm tra trùng lặp đề tài/đề cương của mình trước khi nộp chính thức, bạn có muốn dùng tính năng đó không? Vì sao? | CHUNG | Yêu cầu chức năng |
| Q-SV-10 | Bạn thường dùng thiết bị gì để làm việc với các hệ thống học tập/quản lý (máy tính để bàn, laptop, điện thoại)? | CHUNG | Yêu cầu phi chức năng |
| Q-SV-11 | Theo bạn, điều gì bất tiện nhất trong quy trình đăng ký/làm đồ án hiện nay? | CHUNG | Yêu cầu chức năng |
| Q-SV-12 | Bạn có được cấp/thấy mẫu phiếu đăng ký đề tài, mẫu đề cương chính thức không? Bạn có thể cho mình xin bản mẫu đó không? | CHUNG | Biểu mẫu dữ liệu |
| Q-SV-13 | Mình xin phép hỏi thêm: bạn có đồng ý cho mình dùng phần trả lời này (ẩn danh, không ghi tên) để phân tích quy trình cho đồ án tốt nghiệp không? | CHUNG | BPMN AS-IS |

## Ghi chú

Bộ câu hỏi này chỉ là công cụ khảo sát — không chứa câu trả lời mẫu hay dữ liệu phỏng vấn thật. Kết quả phỏng vấn thật được ghi vào bản sao của Phụ lục D (mẫu biên bản phỏng vấn) và lưu tại `tai-lieu-goc/phong-van/`.
