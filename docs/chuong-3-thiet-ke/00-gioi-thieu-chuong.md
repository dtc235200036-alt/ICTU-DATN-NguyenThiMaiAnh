# CHƯƠNG 3. THIẾT KẾ HỆ THỐNG

> **Mã PI:** 2.1, 2.2, 2.3 — **Yêu cầu:** DSGN-01, DSGN-02, DSGN-03, DSGN-04

Chương này trình bày thiết kế dữ liệu, kiến trúc phần mềm và giao diện của hệ thống, dựa trực tiếp trên các yêu cầu chức năng/phi chức năng và use case đã phân tích ở Chương 2. Sơ đồ lớp thực thể và sơ đồ CSDL khớp 1-1 (D-05), kiến trúc SOA tách Web API / dịch vụ AI / client theo ranh giới schema và luồng dữ liệu đã chốt (research/ARCHITECTURE.md), và 14 màn hình mockup HTML/CSS tĩnh (D-11, D-12, D-13) minh họa giao diện Ant Design admin cho cả ba vai trò Sinh viên, Giảng viên, Bộ môn.

Các mục của chương:

- **3.1. Sơ đồ lớp thực thể** — 20 lớp thực thể (PlantUML), state machine của Đề tài/Đề cương/Kết quả kiểm tra trùng lặp.
- **3.2. Thiết kế cơ sở dữ liệu** — lược đồ `thesis_core` (20 bảng) và `thesis_ai`, từ điển dữ liệu, ràng buộc toàn vẹn và xử lý đồng thời (race condition).
- **3.3. Kiến trúc hệ thống** — kiến trúc SOA (component, deployment, sequence luồng kiểm tra trùng lặp đồng bộ/bất đồng bộ).
- **3.4. Thiết kế giao diện** — quy ước giao diện Ant Design admin và 16 màn hình mockup chính (đăng nhập, dashboard 3 vai trò, đề tài, đề cương, tiến độ, bảo vệ, kho đồ án, chi tiết kiểm tra trùng lặp).
