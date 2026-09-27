# Hệ thống quản lý đồ án sinh viên — Khoa CNTT, ICTU

## What This Is

Hệ thống quản lý đồ án/khóa luận tốt nghiệp của Khoa Công nghệ thông tin (Trường ĐH CNTT&TT Thái Nguyên), phục vụ Sinh viên, Giảng viên hướng dẫn và Bộ môn/Khoa trong toàn bộ quy trình: đề xuất/đăng ký đề tài → duyệt đề cương → theo dõi tiến độ → nộp báo cáo → phân công hội đồng và tổ chức bảo vệ, đồng thời lưu kho đồ án của khoa qua các khóa. Hệ thống tích hợp dịch vụ AI kiểm tra trùng lặp (tên đề tài theo ngữ nghĩa; đoạn nội dung đề cương/báo cáo) trong phạm vi kho đồ án của khoa. Đây là đồ án tốt nghiệp của SV Nguyễn Thị Mai Anh (DTC235200036, CN CNTT K22A), GVHD: Hà Thị Thanh.

## Core Value

Quy trình đồ án 5 UC chính chạy trọn vẹn end-to-end trên Web, và khi sinh viên đăng ký đề tài hoặc nộp đề cương/báo cáo, hệ thống cảnh báo trùng lặp kèm đề tài/đồ án trùng, đoạn trùng và tỷ lệ tương đồng — đủ để demo và đạt toàn bộ tiêu chí CLO/PI khi bảo vệ.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Tài liệu phân tích & thiết kế (CLO 1–2):**
- [ ] Khảo sát quy trình thực tế + sơ đồ BPMN + mô tả chi tiết quy trình (PI 1.1)
- [ ] Bảng yêu cầu chức năng và phi chức năng (bảo mật, phân quyền, hiệu năng, thời gian phản hồi kiểm tra trùng lặp) (PI 1.2)
- [ ] Sơ đồ UC tổng quát ≥5 UC chính + đặc tả từng UC (PI 1.3)
- [ ] Sơ đồ lớp thực thể + sơ đồ CSDL tương ứng (PI 2.1)
- [ ] Thiết kế kiến trúc SOA bằng UML: Web API, client, dịch vụ AI (PI 2.2)
- [ ] Mockup Figma cho các giao diện chính (PI 2.3)

**Phần mềm (CLO 3):**
- [ ] CSDL MySQL (PI 3.1)
- [ ] 3 thành phần: Web API (FastAPI), client Web (React), dịch vụ AI trùng lặp (FastAPI riêng) (PI 3.2)
- [ ] UC Quản lý đề tài: GV/SV đề xuất, SV đăng ký, bộ môn duyệt/phân công GVHD (PI 3.3)
- [ ] UC Quản lý đề cương: SV nộp, GVHD duyệt/yêu cầu sửa (PI 3.3)
- [ ] UC Quản lý tiến độ thực hiện: SV nộp báo cáo tiến độ, GVHD nhận xét (PI 3.3)
- [ ] UC Quản lý bảo vệ: bộ môn lập hội đồng (GV làm thành viên), xếp lịch, nhập điểm/kết quả (PI 3.3)
- [ ] UC Quản lý kho dữ liệu đồ án: lưu trữ, tra cứu đồ án các khóa (PI 3.3)
- [ ] AI: so sánh ngữ nghĩa tên đề tài khi SV đăng ký, cảnh báo đề tài tương tự kèm tỷ lệ (PI 3.4)
- [ ] AI: phát hiện trùng lặp đề cương/báo cáo (DOCX + PDF), chỉ rõ đoạn trùng, đồ án trùng, tỷ lệ tương đồng (PI 3.4)
- [ ] Phân quyền theo 3 vai trò: Sinh viên, Giảng viên, Bộ môn/Khoa (admin) (PI 3.4)

**Triển khai & dữ liệu (CLO 4):**
- [ ] Triển khai server sau Apache (reverse proxy) với HTTPS + phân quyền người dùng (PI 4.1)
- [ ] Seed dữ liệu: 100 SV, 30 GV, 300 đề tài các khóa (PI 4.2)
- [ ] 50 file đề cương/báo cáo thử nghiệm, có các cặp trùng lặp chủ đích để kiểm chứng (PI 4.2)

**Báo cáo:**
- [ ] Quyển báo cáo 4 chương (Cơ sở lý thuyết; Khảo sát & phân tích; Thiết kế; Triển khai) + slide bảo vệ

### Out of Scope

- Thay thế Turnitin — tính năng AI chỉ bổ sung, phạm vi so sánh là đồ án trong khoa
- So sánh với nguồn Internet/ngoài khoa — ngoài phạm vi đề cương
- Role "thành viên hội đồng" riêng — hội đồng dùng tài khoản Giảng viên được phân công
- Tích hợp SSO/hệ thống đào tạo của trường — mục tiêu là demo bảo vệ, không phải vận hành thật
- Ứng dụng mobile native — đề cương chỉ yêu cầu ứng dụng Web
- Chịu tải production — chỉ cần chạy tốt với tập dữ liệu thử nghiệm

## Context

- Đề cương gốc: `H01.DTC235200036.NguyenThiMaiAnh.docx` (trong repo). Mọi deliverable phải truy vết được về mã PI (1.1 … 4.2).
- Mức hoàn thiện: demo bảo vệ đồ án, chạy tốt với dữ liệu thử nghiệm.
- Dữ liệu tiếng Việt → cần model embedding hỗ trợ tiếng Việt cho so sánh ngữ nghĩa và phân đoạn văn bản.
- AI chạy local (sentence-transformers hoặc tương đương + vector search), không phụ thuộc API trả phí.
- Tiến độ 10 tuần trong đề cương: T1 khảo sát/BPMN · T2–3 yêu cầu/UC · T4 dữ liệu & kiến trúc · T5 mockup + thu thập kho · T6 CSDL + API · T7 5 UC · T8 AI · T9 triển khai/seed/kiểm thử · T10 báo cáo + slide.

## Constraints

- **Timeline**: 28/09/2026 → 07/12/2026 (10 tuần) — cố định theo đề cương
- **Tech stack**: Backend Python FastAPI, frontend React, CSDL MySQL — người dùng chọn; MySQL bắt buộc theo PI 3.1
- **Kiến trúc**: SOA — Web API, client và dịch vụ AI là các thành phần tách biệt (PI 2.2, 3.2)
- **Triển khai**: phía server sau Apache (hoặc IIS) với HTTPS và phân quyền (PI 4.1)
- **Phạm vi AI**: chỉ các đồ án trong Khoa CNTT (PI 3.4)
- **Định dạng file**: DOCX và PDF cho đề cương/báo cáo

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI (Web API) + React (client) | Chọn của người dùng; Python đồng bộ với dịch vụ AI | — Pending |
| Dịch vụ AI = FastAPI riêng, model embedding local | Không tốn phí, đáp ứng SOA tách dịch vụ | — Pending |
| Apache làm reverse proxy + HTTPS | Đề cương yêu cầu IIS/Apache; FastAPI chạy uvicorn phía sau | — Pending |
| 3 role: SV, GV, Bộ môn; hội đồng = GV được phân công | Người dùng xác nhận | — Pending |
| Roadmap gồm cả tài liệu và code | Đồ án chấm cả phân tích/thiết kế lẫn thi công | — Pending |
| Repo git riêng tại NTMA (không dùng repo ~) | Tránh commit vào repo home | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-27 after initialization*
