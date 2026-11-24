# Bảng truy vết PI – tài liệu – yêu cầu

Bảng này giúp GVHD kiểm tra tiến độ theo đúng tiêu chí PI của đề cương (`H01.DTC235200036.NguyenThiMaiAnh.docx`, mục 6). Cập nhật bởi mọi kế hoạch của Phase 1 (01-02..01-07); mục 1 và 3 hoàn thiện dần, mục 2 phủ toàn bộ yêu cầu v1 khi Phase 1 kết thúc.

## 1. Truy vết theo tiêu chí PI

| Mã PI | Nội dung PI | Yêu cầu | Mục tài liệu (minh chứng) | Trạng thái |
|---|---|---|---|---|
| 1.1 | Mô tả được quy trình nghiệp vụ | ANLS-01, ANLS-02 | [khao-sat/](chuong-2-khao-sat-phan-tich/khao-sat/) (Phụ lục A–D); [01-khao-sat-hien-trang.md](chuong-2-khao-sat-phan-tich/01-khao-sat-hien-trang.md), [02-quy-trinh-nghiep-vu.md](chuong-2-khao-sat-phan-tich/02-quy-trinh-nghiep-vu.md) (AS-IS + TO-BE đầy đủ 1 tổng quan + 5 quy trình con — bản nháp gắn nhãn GIẢ ĐỊNH — chờ xác nhận, đối chiếu với biên bản phỏng vấn thật ở Task 3 của kế hoạch này) | Chờ dữ liệu khảo sát thật |
| 1.2 | Mô tả được yêu cầu chức năng và phi chức năng | ANLS-03, ANLS-04 | [03-yeu-cau-chuc-nang.md](chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md) (8 module: TK, DT, DC, TD, BV, KHO, TB, AI); [04-yeu-cau-phi-chuc-nang.md](chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md) | Đạt |
| 1.3 | Xây dựng được sơ đồ UC và đặc tả UC | ANLS-05 | [05-so-do-use-case.md](chuong-2-khao-sat-phan-tich/05-so-do-use-case.md) (sơ đồ UC tổng quát 5 UC chính + UC0); [06](chuong-2-khao-sat-phan-tich/06-dac-ta-uc1-quan-ly-de-tai.md)/[07](chuong-2-khao-sat-phan-tich/07-dac-ta-uc2-quan-ly-de-cuong.md)/[08](chuong-2-khao-sat-phan-tich/08-dac-ta-uc3-quan-ly-tien-do.md)/[09](chuong-2-khao-sat-phan-tich/09-dac-ta-uc4-quan-ly-bao-ve.md)/[10](chuong-2-khao-sat-phan-tich/10-dac-ta-uc5-quan-ly-kho-do-an.md)/[11](chuong-2-khao-sat-phan-tich/11-dac-ta-uc0-chuc-nang-chung.md) (đặc tả UC1..UC5 và UC0) | Đạt |
| 2.1 | Thiết kế được cấu trúc dữ liệu | DSGN-01, DSGN-02 | [01-so-do-lop-thuc-the.md](chuong-3-thiet-ke/01-so-do-lop-thuc-the.md) (20 lớp thực thể), [02-thiet-ke-csdl.md](chuong-3-thiet-ke/02-thiet-ke-csdl.md) (20 bảng `thesis_core` + lược đồ `thesis_ai`) | Đạt |
| 2.2 | Thiết kế được kiến trúc phần mềm | DSGN-03 | [03-kien-truc-he-thong.md](chuong-3-thiet-ke/03-kien-truc-he-thong.md) (kiến trúc SOA, component/deployment/sequence) | Đạt |
| 2.3 | Thiết kế mockup được giao diện | DSGN-04 | [04-thiet-ke-giao-dien.md](chuong-3-thiet-ke/04-thiet-ke-giao-dien.md) (16/16 màn hình đã dựng, xem [mockup/](chuong-3-thiet-ke/mockup/)) | Đạt |
| 3.1 | Thi công được phần dữ liệu | DEPL-01 | (Phase 2) | Chưa thực hiện |
| 3.2 | Thi công đủ các thành phần theo kiến trúc | — | (Phase 2, Web API/client/dịch vụ AI) | Chưa thực hiện |
| 3.3 | Thi công được các UC / yêu cầu chức năng | TOPC-\*, OUTL-\*, PROG-\*, DEFN-\*, REPO-\* | (Phase 2–3) | Chưa thực hiện |
| 3.4 | Thi công được các yêu cầu phi chức năng | AISV-\*, AUTH-\* | (Phase 2, 4) | Chưa thực hiện |
| 4.1 | Triển khai được phần mềm ra ngoài môi trường dev | DEPL-02 | (Phase 2) | Chưa thực hiện |
| 4.2 | Tạo được dữ liệu thử nghiệm với số lượng phù hợp | DATA-01, DATA-02, DATA-03 | (Phase 2, 4) | Chưa thực hiện |

## 2. Truy vết theo yêu cầu

| Yêu cầu | Mô tả | Tài liệu | Plan |
|---|---|---|---|
| ANLS-01 | Kết quả khảo sát quy trình quản lý đồ án thực tế kèm form mẫu | khao-sat/ (Phụ lục A–D), 01-khao-sat-hien-trang.md | 01-01, 01-03, 01-07 |
| ANLS-02 | Sơ đồ BPMN và mô tả chi tiết quy trình nghiệp vụ | 02-quy-trinh-nghiep-vu.md, bpmn/*.drawio | 01-02, 01-03, 01-07 |
| ANLS-03 | Bảng yêu cầu chức năng chi tiết | 03-yeu-cau-chuc-nang.md | 01-02, 01-04 |
| ANLS-04 | Bảng yêu cầu phi chức năng (bảo mật, phân quyền, hiệu năng, ngưỡng đo được) | 04-yeu-cau-phi-chuc-nang.md | 01-04 |
| ANLS-05 | Sơ đồ UC tổng quát 5 UC chính + đặc tả từng UC | 05-so-do-use-case.md, 06..11-dac-ta-uc\*.md | 01-02, 01-04 |
| DSGN-01 | Sơ đồ lớp thực thể | 01-so-do-lop-thuc-the.md, so-do-lop/lop-thuc-the.puml | 01-02, 01-05 |
| DSGN-02 | Sơ đồ CSDL khớp với sơ đồ lớp thực thể | 02-thiet-ke-csdl.md, csdl/erd.puml | 01-02, 01-05 |
| DSGN-03 | Thiết kế kiến trúc SOA bằng UML | 03-kien-truc-he-thong.md | 01-05 |
| DSGN-04 | Mockup giao diện HTML prototype | 04-thiet-ke-giao-dien.md, mockup/ | 01-02, 01-06, 01-07 |

## 3. Ma trận truy vết chức năng

| FR | UC | Bước BPMN (TO-BE) | Lớp | Bảng | Màn hình |
|----|----|--------------------|-----|------|----------|
| FR-TK-01 | UC0.1 | — | TaiKhoan | tai_khoan | MH-01 |
| FR-TK-02 | UC0.1 | — | TaiKhoan | tai_khoan | MH-01 |
| FR-TK-03 | UC0.1 | — | TaiKhoan | tai_khoan | MH-01 |
| FR-TK-04 | UC0.2 | — | TaiKhoan | tai_khoan | — |
| FR-TK-05 | UC0.3 | TB-TQ-01 | DotDoAn | dot_do_an | — |
| FR-DT-01 | UC1.1 | TB-DT-01, TB-DT-02, TB-DT-09 | DeTai, PhanCongHuongDan | de_tai, phan_cong_huong_dan | MH-06 |
| FR-DT-02 | UC1.1 | TB-DT-03, TB-DT-04, TB-DT-05, TB-DT-06 | KetQuaKiemTraTrungLap, ChiTietTrungLap | ket_qua_kiem_tra_trung_lap, chi_tiet_trung_lap | MH-06 |
| FR-DT-03 | UC1.2 | TB-DT-11 | DeTai | de_tai | MH-07, MH-02 |
| FR-DT-04 | UC1.1 | TB-DT-02, TB-DT-07, TB-DT-08, TB-DT-10 | DeTai, PhanCongHuongDan | de_tai, phan_cong_huong_dan | MH-06 |
| FR-DT-05 | UC0.8 | TB-TQ-01, TB-DT-00a, TB-DT-00c | PhanCongHuongDan | phan_cong_huong_dan | MH-15 |
| FR-DT-06 | UC1.1 | TB-DT-07, TB-DT-08, TB-DT-09, TB-DT-10 | DeTai | de_tai | — |
| FR-DT-07 | UC1.2 | TB-DT-12 | DeTai | de_tai | MH-05 |
| FR-DT-08 | UC0.8 | TB-DT-00a, TB-DT-00b | PhanCongHuongDan | phan_cong_huong_dan | MH-15 |
| FR-DT-09 | UC0.8 | TB-DT-00b | PhanCongHuongDan, DeTai | phan_cong_huong_dan, de_tai | MH-15 |
| FR-DT-10 | UC1.1 | TB-DT-02, TB-DT-06, TB-DT-09 | DeTai, PhanCongHuongDan | de_tai, phan_cong_huong_dan | MH-06 |
| FR-DT-11 | UC0.8 | TB-DT-00c | PhanCongHuongDan | phan_cong_huong_dan | MH-16, MH-02 |
| FR-DC-01 | UC2.1 | TB-DC-01 | DeCuong, TaiLieuDoAn | de_cuong, tai_lieu_do_an | MH-08 |
| FR-DC-02 | UC2.1 | TB-DC-02 | TaiLieuDoAn | tai_lieu_do_an | MH-08 |
| FR-DC-03 | UC2.2 | TB-DC-05 | DeCuong, KetQuaKiemTraTrungLap | de_cuong, ket_qua_kiem_tra_trung_lap | MH-09 |
| FR-DC-04 | UC2.2 | TB-DC-06, TB-DC-07, TB-DC-08, TB-DC-09 | LuotDuyetDeCuong | luot_duyet_de_cuong | MH-09 |
| FR-DC-05 | UC2.3 | — | TaiLieuDoAn, LuotDuyetDeCuong | tai_lieu_do_an, luot_duyet_de_cuong | MH-08 |
| FR-TD-01 | UC3.1 | TB-TD-01 | MocTienDo | moc_tien_do | MH-04 |
| FR-TD-02 | UC3.2 | TB-TD-02 | BaoCaoTienDo | bao_cao_tien_do | MH-10 |
| FR-TD-03 | UC3.3 | TB-TD-03 | BaoCaoTienDo | bao_cao_tien_do | MH-10 |
| FR-TD-04 | UC3.4 | TB-TD-05, TB-TD-06 | BaoCaoTienDo | bao_cao_tien_do | MH-04 |
| FR-BV-01 | UC4.1 | TB-BV-01, TB-BV-02 | TaiLieuDoAn | tai_lieu_do_an | MH-08 |
| FR-BV-02 | UC4.2 | TB-BV-03 | HoiDong, ThanhVienHoiDong | hoi_dong, thanh_vien_hoi_dong | MH-11 |
| FR-BV-03 | UC4.2 | TB-BV-03 | LichBaoVe | lich_bao_ve | MH-11 |
| FR-BV-04 | UC4.3 | TB-BV-05 | DiemBaoVe | diem_bao_ve | MH-12 |
| FR-BV-05 | UC4.4 | TB-BV-06 | LichBaoVe | lich_bao_ve | MH-11 |
| FR-BV-06 | UC4.4 | TB-BV-07 | LichBaoVe | lich_bao_ve | MH-11 |
| FR-BV-07 | UC4.5 | TB-BV-08 | LichBaoVe | lich_bao_ve | MH-02 |
| FR-KHO-01 | UC5.2 | TB-KHO-01 | DoAnKho | do_an_kho | — |
| FR-KHO-02 | UC5.1 | TB-KHO-05, TB-KHO-06 | DoAnKho | do_an_kho | MH-13 |
| FR-KHO-03 | UC5.3 | TB-KHO-03 | DoAnKho | do_an_kho | MH-13 |
| FR-KHO-04 | UC5.4 | TB-KHO-03 | DoAnKho | do_an_kho | MH-13 |
| FR-KHO-05 | UC5.2, UC5.4 | TB-KHO-02, TB-KHO-04 | DoAnKho | do_an_kho | — |
| FR-TB-01 | UC0.5 | TB-TQ-08 | ThongBao | thong_bao | MH-02 |
| FR-AI-01 | UC0.6 | TB-DT-02 | KetQuaKiemTraTrungLap | ket_qua_kiem_tra_trung_lap | MH-06 |
| FR-AI-02 | UC0.7 | TB-DC-03 | ChiTietTrungLap | chi_tiet_trung_lap | MH-14 |
| FR-AI-03 | UC0.7 | TB-DC-04 | KetQuaKiemTraTrungLap, ChiTietTrungLap | ket_qua_kiem_tra_trung_lap, chi_tiet_trung_lap | MH-14 |
| FR-AI-04 | UC0.7 | TB-DC-03 | KetQuaKiemTraTrungLap | ket_qua_kiem_tra_trung_lap | MH-08 |
| FR-AI-05 | UC0.4 | — | CauHinhNguong | cau_hinh_nguong | — |
| FR-AI-06 | UC0.7 (A2) | — | KetQuaKiemTraTrungLap, ChiTietTrungLap, TaiKhoan | ket_qua_kiem_tra_trung_lap, chi_tiet_trung_lap | Kiểm tra đạo văn (bổ sung sau thiết kế, không có mã MH) |
