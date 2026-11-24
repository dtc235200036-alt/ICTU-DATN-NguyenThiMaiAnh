# docs/ — Quy ước tài liệu phân tích & thiết kế

Tài liệu này cố định các quy ước áp dụng cho toàn bộ `docs/` (Phase 1 và các phase sau tái sử dụng khi bổ sung tài liệu). Mọi kế hoạch (01-02..01-07 và các phase sau) phải tuân theo quy ước ở đây; nếu cần đổi quy ước, sửa file này trước rồi mới sửa nội dung.

## 1. Bản đồ thư mục

```
docs/
├── README.md                          (file này)
├── truy-vet.md                        Bảng truy vết PI -> tài liệu -> yêu cầu
├── chuong-2-khao-sat-phan-tich/       Chương 2 báo cáo: Khảo sát & phân tích
│   ├── khao-sat/                      Phụ lục A-D: kế hoạch khảo sát, câu hỏi phỏng vấn,
│   │                                   phiếu khảo sát, mẫu biên bản (§2.1)
│   ├── bpmn/                          Nguồn draw.io (.drawio) + PNG cho mọi sơ đồ BPMN
│   ├── uc/                            Nguồn PlantUML (.puml) cho sơ đồ UC + activity
│   ├── 02-quy-trinh-nghiep-vu.md       §2.2 Mô hình hóa quy trình nghiệp vụ (BPMN)
│   ├── 03-yeu-cau-chuc-nang.md         §2.3 Yêu cầu chức năng
│   ├── 04-yeu-cau-phi-chuc-nang.md     §2.4 Yêu cầu phi chức năng (plan 01-04)
│   ├── 05-so-do-use-case.md            §2.5 Sơ đồ UC tổng quát (plan 01-04)
│   ├── 06-dac-ta-uc1-quan-ly-de-tai.md          §2.6.1 Đặc tả UC1
│   ├── 07-dac-ta-uc2-de-cuong.md                §2.6.2 Đặc tả UC2 (plan 01-04)
│   ├── 08-dac-ta-uc3-tien-do.md                 §2.6.3 Đặc tả UC3 (plan 01-04)
│   ├── 09-dac-ta-uc4-bao-ve.md                  §2.6.4 Đặc tả UC4 (plan 01-04)
│   ├── 10-dac-ta-uc5-kho.md                     §2.6.5 Đặc tả UC5 (plan 01-04)
│   └── 11-dac-ta-uc0-chuc-nang-chung.md         §2.6.6 Đặc tả UC0 - Chức năng chung (plan 01-04)
├── chuong-3-thiet-ke/                 Chương 3 báo cáo: Thiết kế
│   ├── so-do-lop/                     Nguồn PlantUML sơ đồ lớp thực thể
│   ├── csdl/                          Nguồn PlantUML ERD
│   ├── mockup/                        Prototype HTML/CSS tĩnh + PNG (D-11)
│   ├── 01-so-do-lop-thuc-the.md        §3.1 Sơ đồ lớp thực thể
│   ├── 02-thiet-ke-csdl.md             §3.2 Thiết kế CSDL
│   ├── 03-kien-truc-he-thong.md        §3.3 Kiến trúc SOA (plan 01-05)
│   └── 04-thiet-ke-giao-dien.md        §3.4 Thiết kế giao diện (mockup)
├── chuong-4-trien-khai/               Chương 4 báo cáo: Triển khai & thử nghiệm
│   └── thu-nghiem-ai/                 Trang đánh giá dịch vụ AI (Phase 4): dữ liệu, so sánh
│                                       mô hình, hiệu chỉnh ngưỡng, hiệu năng & bảo mật, đánh giá kiểu PAN
│                                       (README.md = mục lục)
└── (tai-lieu-goc/ nằm ở gốc repo, không phải trong docs/ — xem README riêng của nó)
```

Mỗi mục lớn của quyển báo cáo là **một file Markdown**, để cuối Phase 5 ghép thẳng thành quyển (RPRT-01). Nguồn sơ đồ (`.puml`, `.drawio`) và ảnh xuất (`.png`, `.svg`) đặt **cạnh** file Markdown tham chiếu chúng, trong thư mục con cùng cấp (`bpmn/`, `uc/`, `so-do-lop/`, `csdl/`, `mockup/`).

## 2. Quy ước mã định danh (ID)

| Loại | Mẫu mã | Ví dụ | Ghi chú |
|---|---|---|---|
| Yêu cầu chức năng | `FR-<module>-NN` | `FR-DT-01` | module ∈ {TK (tài khoản/phân quyền), DT (đề tài), DC (đề cương), TD (tiến độ), BV (bảo vệ), KHO, TB (thông báo), AI} |
| Quy tắc nghiệp vụ | `BR-<nhóm>-NN` | `BR-DT-01`, `BR-PC-01` | Đặt trong đặc tả UC (§2.6); DT = đề tài (UC1), PC = phân công GVHD (UC0.8) |
| Yêu cầu phi chức năng | `NFR-NN` | `NFR-01` | Đánh số liên tục, không theo module |
| Use case con | `UCx.y` | `UC1.1` | x = UC chính (1..5), y = UC con; `UC0.y` dành cho chức năng chung (vd. UC0.6 kiểm tra trùng lặp tên) |
| Bước quy trình BPMN | `<TB|AS>-<module>-NN` | `TB-DT-02`, `AS-DT-01` | TB = TO-BE, AS = AS-IS; NN liên tục trong một trang sơ đồ; hậu tố chữ (`TB-DT-00a`) cho các nhánh của cùng một bước, `TB-DT-00a..00c` là bước phân công GVHD đầu đợt (UC0.8) đặt trước bước 01 |
| Màn hình mockup | `MH-NN` | `MH-06` | NN theo thứ tự danh mục màn hình §3.4.2, không theo vai trò |
| Biểu mẫu khảo sát | `MAU-NN` | `MAU-01` | Biểu mẫu thu thập được hoặc tự thiết kế trong Phụ lục |
| Phát hiện khảo sát | `KS-<module>-NN` | `KS-DT-01` | Ghi nhận từ phỏng vấn/tài liệu, dùng khi viết AS-IS |
| Vấn đề/hạn chế phát hiện | `VD-NN` | `VD-01` | Vấn đề của quy trình hiện tại, làm động lực cho TO-BE |
| Câu hỏi phỏng vấn | `Q-<BM\|GV\|SV>-NN` | `Q-GV-05` | Theo vai trò được phỏng vấn |
| Câu hỏi khảo sát (phiếu) | `P-<BM\|GV\|SV>-NN` | `P-SV-03` | Phụ lục C |
| Biên bản phỏng vấn | `BB-<BM\|GV\|SV>-NN` | `BB-GV-01` | Lưu tại `tai-lieu-goc/phong-van/` |
| Tài liệu gốc thu thập | `TL-NN` | `TL-04` | Theo checklist `tai-lieu-goc/README.md` |

## 3. Dòng gắn mã PI

Mọi file `.md` trong `chuong-2-khao-sat-phan-tich/` và `chuong-3-thiet-ke/` phải có, ngay dưới heading của mục lớn, một dòng:

```
> **Mã PI:** <mã PI> — **Yêu cầu:** <REQ-ID, REQ-ID...>
```

Ví dụ: `> **Mã PI:** 1.1 — **Yêu cầu:** ANLS-02`. Đây là điều kiện `check-docs.py pi-tags` kiểm tra (chỉ cần chuỗi `Mã PI:` xuất hiện, không kiểm tra định dạng chi tiết).

## 4. Nhãn giả định

Khi một nội dung được viết trước khi có phỏng vấn/tài liệu thật xác nhận (D-01, D-02), phải gắn nhãn:

```
GIẢ ĐỊNH — chờ xác nhận
```

Nhãn này chỉ được **gỡ bỏ** khi nội dung đã được đối chiếu với một biên bản phỏng vấn (`BB-*`) hoặc tài liệu gốc (`TL-*`) cụ thể — trích dẫn mã biên bản/tài liệu đó khi gỡ nhãn. Việc đối chiếu và gỡ nhãn thuộc plan 01-07.

## 5. Định dạng đặc tả UC

Mỗi UC con dùng đúng cấu trúc sau (xem ví dụ đầy đủ ở `06-dac-ta-uc1-quan-ly-de-tai.md`):

```
#### UCx.y – <Tên UC>

| Thuộc tính | Nội dung |
|---|---|
| Mã UC | ... |
| Tên UC | ... |
| Tác nhân | ... |
| Mô tả | ... |
| Tiền điều kiện | ... |
| Hậu điều kiện | ... |
| Yêu cầu liên quan | ... |
| Màn hình | ... |

**Luồng sự kiện chính**
1. ...

**Luồng thay thế**
- **A1** (rẽ nhánh từ bước N): ...

**Ngoại lệ**
- **E1**: ...
```

## 6. Quy ước đặt tên lớp ↔ bảng

- Tên lớp thực thể (PlantUML): **PascalCase**, tiếng Việt không dấu (vd. `DeTai`, `KetQuaKiemTraTrungLap`).
- Tên bảng CSDL (ERD/migration): **snake_case**, tiếng Việt không dấu, số nhiều không bắt buộc (vd. `de_tai`, `ket_qua_kiem_tra_trung_lap`).
- Bảng ánh xạ bắt buộc trong mục thiết kế CSDL, header đúng nguyên văn:

  ```
  | Lớp thực thể | Bảng | Ghi chú |
  ```

  Mỗi lớp phải có đúng một dòng ánh xạ tới một bảng. Một bảng không map trực tiếp tới lớp nào (bảng kỹ thuật, bảng liên kết N-N) phải có "Ghi chú" chứa từ "liên kết" hoặc "kỹ thuật" để `check-docs.py class-erd` không báo lỗi.

## 7. Ma trận truy vết chức năng

`docs/truy-vet.md` §3 dùng đúng header:

```
| FR | UC | Bước BPMN (TO-BE) | Lớp | Bảng | Màn hình |
```

Mỗi FR đã có class/bảng/màn hình phải có đúng một dòng. Ô không áp dụng dùng `—` (chỉ hai cột BPMN và Màn hình được phép để `—`).

## 8. Quy ước chú thích hình/bảng

Trong lúc soạn thảo, dùng số thứ tự tạm: `Hình 2.x`, `Hình 3.x`, `Bảng 2.x`... Plan 01-07 đánh số lại tuần tự theo đúng thứ tự xuất hiện trong file khi ghép chương.

## 9. Định dạng nguồn cho pandoc (D-08)

Toàn bộ Markdown phải xuất được sang `.docx` bằng pandoc + template của trường ở Phase 5:

- Dùng bảng dạng pipe (`| a | b |`), không dùng bảng HTML.
- Ảnh nhúng bằng cú pháp Markdown chuẩn (dấu chấm than, ngoặc vuông mô tả, ngoặc đơn đường dẫn tương đối), không dùng thẻ `<img>`.
- Không chèn HTML thô trong nội dung Markdown.

## 10. Quy ước mockup (D-11, D-12, D-13)

- Mỗi màn hình là **một file HTML tĩnh**: `docs/chuong-3-thiet-ke/mockup/mh-NN.html`, dùng chung stylesheet `antd-admin.css` (không có CSS riêng cho từng màn trừ khi thật sự cần).
- Phần `<head>` bắt buộc có: `<meta charset="UTF-8">`, `<meta name="mockup-size" content="1440xH">` (H đủ cao để không cắt nội dung — xem mục render bên dưới), `<title>MH-NN · <tên màn hình></title>`, và link tới `antd-admin.css`.
- **Không** có thẻ `<script>`, **không** có `@import` CSS, **không** có tài nguyên từ xa (CDN, web font, ảnh remote) — icon dùng SVG nhúng trực tiếp hoặc ký tự Unicode.
- Tên class CSS đặt theo tên component Ant Design tương ứng (`ant-btn`, `ant-alert`, `ant-table`...) để lập trình viên Phase 2–4 map 1:1 sang component React.
- Menu sider theo từng vai trò lấy nguyên văn từ §3.4.1 của `04-thiet-ke-giao-dien.md`.
- Trước khi thiết kế bất kỳ màn nào, nạp hai skill đã cài trong môi trường làm việc: `ui-ux-pro-max` và `design-taste-frontend` (skill thứ hai tự khai không dành cho dashboard — D-12 khóa cứng phong cách Ant Design admin nên phần "hệ thống thiết kế" của skill đó bị override, chỉ áp dụng các nguyên tắc anti-slop trung lập của nó).
- Render bằng `bash tools/render-diagrams.sh docs/chuong-3-thiet-ke/mockup` rồi xem lại PNG bằng công cụ đọc ảnh — sửa ngay nếu chữ bị cắt, tràn hoặc nội dung bị cắt ở đáy (tăng H trong `mockup-size`).
- Mỗi màn có một mục `### 3.4.<NN+2>. MH-NN – <tên màn hình>` trong `04-thiet-ke-giao-dien.md`, nhúng ảnh PNG tương ứng.

## 11. Quy tắc riêng tư

Không được xuất hiện số điện thoại thật trong `docs/` hay `tai-lieu-goc/` (kể cả trong mockup). Dữ liệu mẫu trong mockup và tài liệu ví dụ phải là hư cấu (`check-docs.py privacy` quét theo regex số điện thoại Việt Nam).

## 12. Lệnh render và kiểm tra

```bash
# Render tất cả sơ đồ (.puml, .drawio) và mockup (mockup/mh-NN.html) dưới docs/
bash tools/render-diagrams.sh docs

# Chỉ kiểm tra cú pháp, không ghi file (nhanh hơn, dùng trong lúc soạn thảo)
bash tools/render-diagrams.sh --check docs

# Ép render lại dù output đã mới hơn source
bash tools/render-diagrams.sh --force docs

# Kiểm tra tính nhất quán tài liệu
python3 tools/check-docs.py render docs
python3 tools/check-docs.py links docs
python3 tools/check-docs.py pi-tags
python3 tools/check-docs.py privacy
python3 tools/check-docs.py class-erd
python3 tools/check-docs.py trace FR-DT-01 FR-DT-02
python3 tools/check-docs.py req-coverage TOPC-01 TOPC-02
python3 tools/check-docs.py truy-vet
python3 tools/check-docs.py bpmn
python3 tools/check-docs.py mockup MH-06
python3 tools/check-docs.py all
```

## 13. Mục lục tài liệu

Bảng dưới liệt kê mọi file của Chương 2, Chương 3 và Phụ lục khảo sát, cùng mã PI/yêu cầu và trạng thái hoàn thiện (cập nhật bởi plan 01-07).

| Tệp | Mục | Mã PI | Yêu cầu | Trạng thái |
|---|---|---|---|---|
| [chuong-2-khao-sat-phan-tich/00-gioi-thieu-chuong.md](chuong-2-khao-sat-phan-tich/00-gioi-thieu-chuong.md) | Giới thiệu Chương 2 | 1.1, 1.2, 1.3 | ANLS-01..05 | Đạt |
| [chuong-2-khao-sat-phan-tich/khao-sat/ke-hoach-khao-sat.md](chuong-2-khao-sat-phan-tich/khao-sat/ke-hoach-khao-sat.md) | Phụ lục A | 1.1 | ANLS-01 | Đạt |
| [chuong-2-khao-sat-phan-tich/khao-sat/bo-cau-hoi-phong-van.md](chuong-2-khao-sat-phan-tich/khao-sat/bo-cau-hoi-phong-van.md) | Phụ lục B | 1.1 | ANLS-01 | Đạt |
| [chuong-2-khao-sat-phan-tich/khao-sat/phieu-khao-sat.md](chuong-2-khao-sat-phan-tich/khao-sat/phieu-khao-sat.md) | Phụ lục C | 1.1 | ANLS-01 | Đạt |
| [chuong-2-khao-sat-phan-tich/khao-sat/mau-bien-ban-phong-van.md](chuong-2-khao-sat-phan-tich/khao-sat/mau-bien-ban-phong-van.md) | Phụ lục D | 1.1 | ANLS-01 | Đạt |
| [chuong-2-khao-sat-phan-tich/01-khao-sat-hien-trang.md](chuong-2-khao-sat-phan-tich/01-khao-sat-hien-trang.md) | 2.1 | 1.1 | ANLS-01 | Chờ dữ liệu khảo sát thật |
| [chuong-2-khao-sat-phan-tich/02-quy-trinh-nghiep-vu.md](chuong-2-khao-sat-phan-tich/02-quy-trinh-nghiep-vu.md) | 2.2 | 1.1 | ANLS-02 | AS-IS chờ xác nhận, TO-BE Đạt |
| [chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md](chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md) | 2.3 | 1.2 | ANLS-03 | Đạt |
| [chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md](chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md) | 2.4 | 1.2 | ANLS-04 | Đạt |
| [chuong-2-khao-sat-phan-tich/05-so-do-use-case.md](chuong-2-khao-sat-phan-tich/05-so-do-use-case.md) | 2.5 | 1.3 | ANLS-05 | Đạt |
| [chuong-2-khao-sat-phan-tich/06-dac-ta-uc1-quan-ly-de-tai.md](chuong-2-khao-sat-phan-tich/06-dac-ta-uc1-quan-ly-de-tai.md) | 2.6.1 | 1.3 | ANLS-05 | Đạt |
| [chuong-2-khao-sat-phan-tich/07-dac-ta-uc2-quan-ly-de-cuong.md](chuong-2-khao-sat-phan-tich/07-dac-ta-uc2-quan-ly-de-cuong.md) | 2.6.2 | 1.3 | ANLS-05 | Đạt |
| [chuong-2-khao-sat-phan-tich/08-dac-ta-uc3-quan-ly-tien-do.md](chuong-2-khao-sat-phan-tich/08-dac-ta-uc3-quan-ly-tien-do.md) | 2.6.3 | 1.3 | ANLS-05 | Đạt |
| [chuong-2-khao-sat-phan-tich/09-dac-ta-uc4-quan-ly-bao-ve.md](chuong-2-khao-sat-phan-tich/09-dac-ta-uc4-quan-ly-bao-ve.md) | 2.6.4 | 1.3 | ANLS-05 | Đạt |
| [chuong-2-khao-sat-phan-tich/10-dac-ta-uc5-quan-ly-kho-do-an.md](chuong-2-khao-sat-phan-tich/10-dac-ta-uc5-quan-ly-kho-do-an.md) | 2.6.5 | 1.3 | ANLS-05 | Đạt |
| [chuong-2-khao-sat-phan-tich/11-dac-ta-uc0-chuc-nang-chung.md](chuong-2-khao-sat-phan-tich/11-dac-ta-uc0-chuc-nang-chung.md) | 2.6.6 | 1.3 | ANLS-05 | Đạt |
| [chuong-3-thiet-ke/00-gioi-thieu-chuong.md](chuong-3-thiet-ke/00-gioi-thieu-chuong.md) | Giới thiệu Chương 3 | 2.1, 2.2, 2.3 | DSGN-01..04 | Đạt |
| [chuong-3-thiet-ke/01-so-do-lop-thuc-the.md](chuong-3-thiet-ke/01-so-do-lop-thuc-the.md) | 3.1 | 2.1 | DSGN-01 | Đạt |
| [chuong-3-thiet-ke/02-thiet-ke-csdl.md](chuong-3-thiet-ke/02-thiet-ke-csdl.md) | 3.2 | 2.1 | DSGN-02 | Đạt |
| [chuong-3-thiet-ke/03-kien-truc-he-thong.md](chuong-3-thiet-ke/03-kien-truc-he-thong.md) | 3.3 | 2.2 | DSGN-03 | Đạt |
| [chuong-3-thiet-ke/04-thiet-ke-giao-dien.md](chuong-3-thiet-ke/04-thiet-ke-giao-dien.md) | 3.4 | 2.3 | DSGN-04 | Đạt (16/16 màn hình) |
| [truy-vet.md](truy-vet.md) | Bảng truy vết | 1.1–2.3 | ANLS-01..05, DSGN-01..04 | Đang cập nhật (PI 1.1 chờ Task 3) |
