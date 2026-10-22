# CHƯƠNG 1. CƠ SỞ LÝ THUYẾT

> **Mã PI:** — — **Yêu cầu:** —

Chương này trình bày cơ sở lý thuyết của các công nghệ chính được sử dụng để phân tích, thiết kế và thi công Hệ thống quản lý đồ án sinh viên Khoa Công nghệ thông tin (Trường Đại học Công nghệ thông tin và Truyền thông – ICTU), theo đúng yêu cầu tại mục 8 của đề cương đồ án ("Chương 1. Cơ sở lý thuyết — Những công nghệ chính sử dụng trong đồ án"). Hệ thống được thiết kế theo kiến trúc hướng dịch vụ (SOA) gồm ba thành phần triển khai độc lập: client Web (React), Web API (FastAPI) và một dịch vụ AI kiểm tra trùng lặp (FastAPI riêng), cùng đứng sau Apache làm reverse proxy và một cơ sở dữ liệu MySQL. Mỗi mục của chương giới thiệu khái niệm nền tảng của một nhóm công nghệ, sau đó có mục "Áp dụng trong đồ án" nêu cụ thể công nghệ đó được dùng ở đâu, cho mục đích gì trong hệ thống đang xây dựng — làm cơ sở tham chiếu khi trình bày khảo sát/phân tích (Chương 2), thiết kế (Chương 3) và triển khai (Chương 4).

Các mục của chương:

- **1.1. Kiến trúc hướng dịch vụ (SOA) và RESTful API** — nguyên lý SOA, REST, xác thực JWT và kiểm soát truy cập theo vai trò (RBAC).
- **1.2. Python, FastAPI, Pydantic, SQLAlchemy 2.0 và Alembic** — nền tảng xây dựng Web API và dịch vụ AI.
- **1.3. Hệ quản trị cơ sở dữ liệu MySQL 8** — bảng mã `utf8mb4`, collation tiếng Việt và chuẩn hóa Unicode NFC.
- **1.4. React, TypeScript, Vite, Ant Design và TanStack Query** — nền tảng xây dựng client Web.
- **1.5. Apache HTTP Server, HTTPS/TLS và Docker Compose** — hạ tầng triển khai phía server.
- **1.6. Xử lý ngôn ngữ tiếng Việt: tách từ và embedding câu** — nền tảng NLP cho tính năng kiểm tra tương đồng ngữ nghĩa.
- **1.7. Tìm kiếm vector và phát hiện trùng lặp văn bản** — FAISS, vân tay văn bản (winnowing) và chiến lược phát hiện trùng lặp ở mức đoạn văn.
- **1.8. Công cụ mô hình hóa và thiết kế** — BPMN, UML/PlantUML, draw.io và HTML prototype thay Figma.
- **1.9. Kết luận chương** — tổng hợp và danh mục tài liệu tham khảo.
