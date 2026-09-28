---
status: testing
phase: 02-platform-rbac-topic-management
source: [02-VERIFICATION.md]
started: 2026-09-28T08:00:51+07:00
updated: 2026-09-28T08:00:51+07:00
---

## Current Test

number: 1
name: Phiên đăng nhập giữ khi reload và đăng xuất được từ mọi trang (AUTH-02) — trên trình duyệt thật
expected: |
  Mở https://localhost, đăng nhập (vd. tài khoản Bộ môn trong deploy/README.md), bấm F5 ở vài trang khác nhau vẫn còn đăng nhập; bấm "Đăng xuất" ở header từ bất kỳ trang nào → về màn đăng nhập, bấm Back không vào lại được.
awaiting: user response

## Tests

### 1. Phiên đăng nhập giữ khi reload + đăng xuất mọi trang (AUTH-02)
expected: Như trên — tự kiểm bằng trình duyệt thật (executor đã tự kiểm bằng headless Chrome).
result: [pending]

### 2. Giao diện MH-01..MH-07 cho 3 vai trò khớp mockup
expected: Đăng nhập lần lượt SV / GV / Bộ môn; các màn đăng nhập, dashboard, danh sách/đề xuất/đăng ký đề tài, duyệt & phân công GVHD hiển thị tiếng Việt đúng dấu, bố cục giống docs/chuong-3-thiet-ke/mockup/mh-01..07.png, thao tác chạy trơn tru.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
