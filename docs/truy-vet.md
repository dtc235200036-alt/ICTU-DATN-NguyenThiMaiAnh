# Bảng truy vết PI – tài liệu – yêu cầu

Bảng này giúp GVHD kiểm tra tiến độ theo đúng tiêu chí PI của đề cương (`H01.DTC235200036.NguyenThiMaiAnh.docx`, mục 6). Cập nhật bởi mọi kế hoạch của Phase 1 (01-02..01-07); mục 1 và 3 hoàn thiện dần, mục 2 phủ toàn bộ yêu cầu v1 khi Phase 1 kết thúc.

## 1. Truy vết theo tiêu chí PI

| Mã PI | Nội dung PI | Yêu cầu | Mục tài liệu (minh chứng) | Trạng thái |
|---|---|---|---|---|
| 1.1 | Mô tả được quy trình nghiệp vụ | ANLS-01, ANLS-02 | [khao-sat/](chuong-2-khao-sat-phan-tich/khao-sat/) (Phụ lục A–D, plan 01-01); [02-quy-trinh-nghiep-vu.md](chuong-2-khao-sat-phan-tich/02-quy-trinh-nghiep-vu.md) (AS-IS giả định + TO-BE đầy đủ UC1; 4 quy trình còn lại ở plan 01-03) | Đang thực hiện |
| 1.2 | Mô tả được yêu cầu chức năng và phi chức năng | ANLS-03, ANLS-04 | [03-yeu-cau-chuc-nang.md](chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md) (module DT; các module khác ở plan 01-04; yêu cầu phi chức năng ở plan 01-04) | Đang thực hiện |
| 1.3 | Xây dựng được sơ đồ UC và đặc tả UC | ANLS-05 | [06-dac-ta-uc1-quan-ly-de-tai.md](chuong-2-khao-sat-phan-tich/06-dac-ta-uc1-quan-ly-de-tai.md) (UC1); [05-so-do-use-case.md](chuong-2-khao-sat-phan-tich/05-so-do-use-case.md) (sơ đồ UC tổng quát 5 UC); [07](chuong-2-khao-sat-phan-tich/07-dac-ta-uc2-quan-ly-de-cuong.md)/[08](chuong-2-khao-sat-phan-tich/08-dac-ta-uc3-quan-ly-tien-do.md) (UC2, UC3, plan 01-04 Task 2; UC4/UC5/UC0 ở Task 3) | Đang thực hiện |
| 2.1 | Thiết kế được cấu trúc dữ liệu | DSGN-01, DSGN-02 | [01-so-do-lop-thuc-the.md](chuong-3-thiet-ke/01-so-do-lop-thuc-the.md), [02-thiet-ke-csdl.md](chuong-3-thiet-ke/02-thiet-ke-csdl.md) (lát cắt UC1.1; đầy đủ ở plan 01-05) | Đang thực hiện |
| 2.2 | Thiết kế được kiến trúc phần mềm | DSGN-03 | (chưa có tài liệu — plan 01-05) | Chưa thực hiện |
| 2.3 | Thiết kế mockup được giao diện | DSGN-04 | [04-thiet-ke-giao-dien.md](chuong-3-thiet-ke/04-thiet-ke-giao-dien.md) (MH-06/14 màn đã dựng; 13 màn còn lại ở plan 01-06) | Đang thực hiện |
| 3.1 | Thi công được phần dữ liệu | DEPL-01 | (Phase 2) | Chưa thực hiện |
| 3.2 | Thi công đủ các thành phần theo kiến trúc | — | (Phase 2, Web API/client/dịch vụ AI) | Chưa thực hiện |
| 3.3 | Thi công được các UC / yêu cầu chức năng | TOPC-\*, OUTL-\*, PROG-\*, DEFN-\*, REPO-\* | (Phase 2–3) | Chưa thực hiện |
| 3.4 | Thi công được các yêu cầu phi chức năng | AISV-\*, AUTH-\* | (Phase 2, 4) | Chưa thực hiện |
| 4.1 | Triển khai được phần mềm ra ngoài môi trường dev | DEPL-02 | (Phase 2) | Chưa thực hiện |
| 4.2 | Tạo được dữ liệu thử nghiệm với số lượng phù hợp | DATA-01, DATA-02, DATA-03 | (Phase 2, 4) | Chưa thực hiện |

## 2. Truy vết theo yêu cầu

| Yêu cầu | Mô tả | Tài liệu | Plan |
|---|---|---|---|
| ANLS-01 | Kết quả khảo sát quy trình quản lý đồ án thực tế kèm form mẫu | khao-sat/ (Phụ lục A–D) | 01-01, 01-03 |
| ANLS-02 | Sơ đồ BPMN và mô tả chi tiết quy trình nghiệp vụ | 02-quy-trinh-nghiep-vu.md, bpmn/01-de-tai.drawio | 01-02, 01-03 |
| ANLS-03 | Bảng yêu cầu chức năng chi tiết | 03-yeu-cau-chuc-nang.md | 01-02, 01-04 |
| ANLS-04 | Bảng yêu cầu phi chức năng (bảo mật, phân quyền, hiệu năng, ngưỡng đo được) | 04-yeu-cau-phi-chuc-nang.md | 01-04 |
| ANLS-05 | Sơ đồ UC tổng quát 5 UC chính + đặc tả từng UC | 05-so-do-use-case.md, 06..11-dac-ta-uc\*.md | 01-02, 01-04 |
| DSGN-01 | Sơ đồ lớp thực thể | 01-so-do-lop-thuc-the.md, so-do-lop/lop-thuc-the.puml | 01-02, 01-05 |
| DSGN-02 | Sơ đồ CSDL khớp với sơ đồ lớp thực thể | 02-thiet-ke-csdl.md, csdl/erd.puml | 01-02, 01-05 |
| DSGN-03 | Thiết kế kiến trúc SOA bằng UML | 03-kien-truc-he-thong.md | 01-05 |
| DSGN-04 | Mockup giao diện HTML prototype | 04-thiet-ke-giao-dien.md, mockup/ | 01-02, 01-06 |

## 3. Ma trận truy vết chức năng

| FR | UC | Bước BPMN (TO-BE) | Lớp | Bảng | Màn hình |
|----|----|--------------------|-----|------|----------|
| FR-DT-01 | UC1.1 | TB-DT-01a, TB-DT-01b | DeTai | de_tai | MH-06 |
| FR-DT-02 | UC1.1 | TB-DT-02, TB-DT-03, TB-DT-04 | KetQuaKiemTraTrungLap, ChiTietTrungLap | ket_qua_kiem_tra_trung_lap, chi_tiet_trung_lap | MH-06 |

*(UC0.6 — kiểm tra trùng lặp tên đề tài — được đặc tả bởi plan 01-04 và thêm vào ma trận này bởi plan 01-07. FR-DT-03..07 được thêm ở Task 2 của kế hoạch này, chưa có lớp/bảng/màn hình riêng nên chưa vào ma trận.)*
