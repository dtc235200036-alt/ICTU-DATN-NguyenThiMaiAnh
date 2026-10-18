# Phase 1: Analysis & Design - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-27
**Phase:** 01-analysis-design
**Areas discussed:** Nguồn khảo sát, Công cụ vẽ sơ đồ, Định dạng tài liệu, Mockup Figma

---

## Nguồn khảo sát

| Option | Description | Selected |
|--------|-------------|----------|
| Phỏng vấn + tài liệu | SV phỏng vấn; Developer soạn câu hỏi/phiếu và tổng hợp | ✓ |
| Chỉ từ tài liệu/quy định | Không phỏng vấn | |
| Developer soạn giả định | SV đối chiếu sau | |

Tài liệu có sẵn: **Chưa có gì** (các phương án khác: quy chế, form mẫu, đồ án khóa trước).

| Chia BPMN | | |
|---|---|---|
| 5 quy trình con + 1 tổng | swimlane SV/GV/Bộ môn | ✓ |
| 1 BPMN lớn | | |

| AS-IS / TO-BE | | |
|---|---|---|
| Cả AS-IS và TO-BE | | ✓ |
| Chỉ TO-BE | | |

## Công cụ vẽ sơ đồ

| Option | Description | Selected |
|--------|-------------|----------|
| PlantUML + draw.io | UML/ERD bằng PlantUML, BPMN bằng draw.io | ✓ |
| Toàn bộ draw.io | | |
| StarUML / Visual Paradigm | | |

Đặc tả UC: **5 UC chính + UC con** (thay cho: chỉ 5 UC chính). Sequence cho luồng AI: **Có**.

## Định dạng tài liệu

| Option | Description | Selected |
|--------|-------------|----------|
| Markdown → Word | pandoc + template .docx trường | ✓ |
| Viết thẳng .docx | | |

Cấu trúc: **Bám chương báo cáo** (thay cho: bám mã PI). Bảng truy vết PI: **Có**.

## Mockup Figma

| Question | Selected | Alternatives |
|----------|----------|--------------|
| Ai làm | Developer dựng qua Figma MCP | SV tự vẽ |
| Phong cách | Ant Design admin | Nhận diện ICTU; wireframe đen trắng |
| Thiết bị | Desktop only | Desktop + mobile |
| Phạm vi | ~12–15 màn chính | Đầy đủ ~25+ màn |

## Developer's Discretion

Câu hỏi phỏng vấn; chi tiết thực thể/state machine; cách chia UC con; bố cục từng màn; tên file.

## Deferred Ideas

Mockup mobile; mockup đầy đủ mọi màn CRUD phụ.
