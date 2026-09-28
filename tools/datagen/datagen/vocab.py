"""Từ vựng tự soạn cho bộ dữ liệu thử nghiệm (D-05, D-06).

Toàn bộ nội dung trong tệp này là văn bản tự soạn cho mục đích thử nghiệm —
không sao chép câu chữ của bất kỳ đồ án/sinh viên thật nào (T-04-08).

Phần 1 (DATA-02): cụm chủ đề, đối tượng nghiệp vụ, sản phẩm, công nghệ, từ khóa,
đơn vị, cụm động từ tiêu đề, bản đồ đồng nghĩa và tên người.
Phần 2 (DATA-03): hồ sơ đối tượng, mẫu câu theo mục, dữ kiện công nghệ và
khuôn mẫu chung (boilerplate) của đồ án — xem nửa sau tệp.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Cụm chủ đề. Mỗi đối tượng: (khóa ngắn, cách diễn đạt 1, cách diễn đạt 2, nhóm đơn vị).
# 3 đối tượng CUỐI mỗi cụm là DỰ TRỮ: không bao giờ xuất hiện trong kho 300 đề tài,
# chỉ dùng cho truy vấn phủ định (CUNG_LINH_VUC) và tài liệu cùng lĩnh vực.
# ---------------------------------------------------------------------------
SO_DOI_TUONG_DU_TRU = 3

CUM: dict[str, dict] = {
    "WEB": {
        "ten": "Ứng dụng web",
        "linh_vuc": ("phát triển ứng dụng web", "lập trình web"),
        "san_pham": [
            ("website", "trang web"),
            ("hệ thống thông tin", "hệ thống thông tin trên nền web"),
            ("ứng dụng web", "ứng dụng chạy trên trình duyệt"),
            ("cổng thông tin", "cổng điện tử"),
            ("phần mềm trực tuyến", "phần mềm chạy trên web"),
        ],
        "cong_nghe": ["ReactJS", "VueJS", "Laravel", "Django", "Spring Boot", "NodeJS"],
        "tu_khoa": ["ứng dụng web", "quản lý", "cơ sở dữ liệu", "giao diện người dùng", "RESTful API"],
        "doi_tuong": [
            ("thu_vien", "quản lý thư viện", "quản lý sách và mượn trả tài liệu", "GD"),
            ("ban_hang_online", "bán hàng trực tuyến", "kinh doanh bán lẻ qua mạng", "TM"),
            ("dat_phong_ks", "đặt phòng khách sạn", "đặt chỗ lưu trú trực tuyến", "DV"),
            ("tuyen_sinh", "tuyển sinh trực tuyến", "tiếp nhận hồ sơ xét tuyển qua mạng", "GD"),
            ("dat_ban_nh", "đặt bàn nhà hàng", "đặt chỗ và gọi món tại nhà hàng", "DV"),
            ("viec_lam", "tìm kiếm việc làm", "kết nối nhà tuyển dụng và người tìm việc", "DN"),
            ("tin_tuc", "quản lý tin tức", "đăng tải tin bài trên cổng điện tử", "CQ"),
            ("ho_so_hs", "quản lý hồ sơ học sinh", "lưu trữ và tra cứu hồ sơ học sinh", "GD"),
            ("dat_ve_xe", "đặt vé xe khách", "bán vé xe liên tỉnh qua mạng", "GT"),
            ("dich_vu_cong", "tiếp nhận thủ tục hành chính trực tuyến", "giải quyết hồ sơ một cửa điện tử", "CQ"),
            ("bat_dong_san", "đăng tin rao vặt bất động sản", "mua bán nhà đất qua tin đăng", "DN"),
            ("dat_san", "đặt sân thể thao", "cho thuê sân bóng theo khung giờ", "DV"),
            ("quyen_gop", "quản lý quyên góp từ thiện", "tiếp nhận và công khai ủng hộ từ thiện", "CQ"),
            ("tour", "đặt tour du lịch", "bán chương trình du lịch trọn gói", "DV"),
            ("su_kien", "quản lý sự kiện và bán vé hội thảo", "đăng ký tham dự sự kiện trực tuyến", "DN"),
        ],
    },
    "MOBILE": {
        "ten": "Ứng dụng di động",
        "linh_vuc": ("lập trình ứng dụng di động", "phát triển phần mềm cho thiết bị di động"),
        "san_pham": [
            ("ứng dụng di động", "ứng dụng trên điện thoại thông minh"),
            ("ứng dụng Android", "ứng dụng cho hệ điều hành Android"),
            ("ứng dụng đa nền tảng", "ứng dụng chạy trên cả Android và iOS"),
            ("ứng dụng điện thoại", "app di động"),
        ],
        "cong_nghe": ["Flutter", "React Native", "Kotlin", "Swift", "Firebase"],
        "tu_khoa": ["ứng dụng di động", "Android", "iOS", "đa nền tảng", "thông báo đẩy"],
        "doi_tuong": [
            ("kham_benh", "đặt lịch khám bệnh", "hẹn giờ khám chữa bệnh", "YT"),
            ("giao_do_an", "đặt và giao đồ ăn", "gọi món giao tận nơi", "DV"),
            ("chi_tieu", "quản lý chi tiêu cá nhân", "theo dõi thu chi cá nhân", "CN"),
            ("diem_danh", "điểm danh sinh viên", "ghi nhận chuyên cần của người học", "GD"),
            ("goi_xe", "gọi xe công nghệ", "đặt xe đưa đón theo yêu cầu", "CN"),
            ("suc_khoe", "theo dõi sức khỏe cá nhân", "ghi nhận chỉ số sức khỏe hằng ngày", "YT"),
            ("tu_vung", "học từ vựng tiếng Anh", "ghi nhớ từ mới tiếng Anh", "GD"),
            ("uong_thuoc", "nhắc lịch uống thuốc", "quản lý đơn thuốc và giờ dùng thuốc", "YT"),
            ("nha_tro", "tìm phòng trọ", "thuê nhà trọ cho sinh viên", "CN"),
            ("du_lich", "hướng dẫn du lịch", "giới thiệu điểm tham quan", "DV"),
            ("phan_anh", "phản ánh hiện trường đô thị", "tiếp nhận kiến nghị của người dân", "CQ"),
            ("nong_san", "kết nối tiêu thụ nông sản", "mua bán nông sản trực tiếp", "NN"),
            ("the_duc", "hướng dẫn luyện tập thể dục tại nhà", "lập kế hoạch tập luyện thể thao", "CN"),
            ("thu_cung", "chăm sóc thú cưng", "đặt lịch dịch vụ cho vật nuôi", "TM"),
            ("xe_buyt", "tra cứu lộ trình xe buýt", "tìm tuyến xe buýt nội tỉnh", "CQ"),
        ],
    },
    "AI_ML": {
        "ten": "Trí tuệ nhân tạo / học máy",
        "linh_vuc": ("trí tuệ nhân tạo và học máy", "học máy"),
        "san_pham": [
            ("hệ thống", "hệ thống thông minh"),
            ("mô hình học sâu", "mô hình mạng nơ-ron sâu"),
            ("ứng dụng trí tuệ nhân tạo", "ứng dụng AI"),
            ("công cụ", "phần mềm"),
            ("mô hình học máy", "mô hình máy học"),
        ],
        "cong_nghe": ["TensorFlow", "PyTorch", "YOLOv8", "OpenCV", "scikit-learn", "PhoBERT"],
        "tu_khoa": ["học máy", "học sâu", "xử lý ảnh", "xử lý ngôn ngữ tự nhiên", "trí tuệ nhân tạo"],
        "doi_tuong": [
            ("bien_so", "nhận dạng biển số xe", "đọc biển kiểm soát phương tiện", "GT"),
            ("khuon_mat", "điểm danh bằng nhận diện khuôn mặt", "chấm công qua khuôn mặt", "GD"),
            ("cam_xuc", "phân tích cảm xúc bình luận", "phân loại ý kiến khách hàng theo sắc thái", "TM"),
            ("chatbot", "tư vấn tuyển sinh bằng chatbot", "giải đáp thắc mắc tuyển sinh qua trợ lý ảo", "GD"),
            ("benh_la", "phát hiện bệnh trên lá cây trồng", "chẩn đoán bệnh cây qua ảnh lá", "NN"),
            ("doanh_thu", "dự báo doanh thu bán hàng", "ước lượng doanh số theo thời gian", "TM"),
            ("goi_y", "gợi ý sản phẩm", "đề xuất mặt hàng theo sở thích", "TM"),
            ("te_nga", "phát hiện té ngã ở người cao tuổi", "cảnh báo ngã cho người già", "YT"),
            ("chu_viet", "nhận dạng chữ viết tay", "chuyển ảnh chữ viết tay thành văn bản", "GD"),
            ("phan_loai_rac", "phân loại rác thải qua hình ảnh", "nhận biết loại rác bằng camera", "CQ"),
            ("tom_tat", "tóm tắt văn bản tiếng Việt", "rút gọn nội dung tài liệu tiếng Việt", "CQ"),
            ("x_quang", "hỗ trợ chẩn đoán ảnh X-quang phổi", "phân tích phim chụp X-quang ngực", "YT"),
            ("dem_xe", "đếm lưu lượng phương tiện giao thông", "thống kê số xe qua camera", "CQ"),
            ("giong_noi", "chuyển giọng nói tiếng Việt thành văn bản", "nhận dạng tiếng nói tiếng Việt", "CQ"),
            ("tin_gia", "phát hiện tin giả trên mạng xã hội", "nhận diện thông tin sai lệch trực tuyến", "CQ"),
        ],
    },
    "IOT": {
        "ten": "Internet vạn vật (IoT)",
        "linh_vuc": ("Internet vạn vật", "IoT"),
        "san_pham": [
            ("hệ thống", "hệ thống nhúng"),
            ("thiết bị IoT", "thiết bị kết nối Internet"),
            ("hệ thống IoT", "hệ thống Internet vạn vật"),
            ("bộ điều khiển", "mạch điều khiển"),
            ("giải pháp IoT", "giải pháp kết nối vạn vật"),
        ],
        "cong_nghe": ["ESP32", "Arduino", "Raspberry Pi", "MQTT", "Node-RED"],
        "tu_khoa": ["IoT", "cảm biến", "vi điều khiển", "giám sát từ xa", "hệ thống nhúng"],
        "doi_tuong": [
            ("nha_kinh", "giám sát nhiệt độ nhà kính", "theo dõi vi khí hậu trong nhà màng", "NN"),
            ("tuoi_cay", "tưới cây tự động", "điều khiển tưới tiêu thông minh", "NN"),
            ("nha_thong_minh", "điều khiển nhà thông minh", "tự động hóa thiết bị gia đình", "CN"),
            ("khong_khi", "quan trắc chất lượng không khí", "đo bụi mịn và khí thải môi trường", "CQ"),
            ("bai_do_xe", "quản lý bãi đỗ xe thông minh", "hướng dẫn chỗ đỗ xe còn trống", "GT"),
            ("ao_nuoi", "giám sát ao nuôi thủy sản", "đo chất lượng nước ao nuôi cá", "NN"),
            ("dien_nang", "giám sát điện năng tiêu thụ", "đo đếm công suất điện từ xa", "DN"),
            ("bao_chay", "cảnh báo cháy sớm", "phát hiện khói và nhiệt bất thường", "DN"),
            ("chuong_trai", "giám sát chuồng trại chăn nuôi", "theo dõi môi trường chuồng nuôi", "NN"),
            ("dinh_vi", "định vị và giám sát phương tiện", "theo dõi hành trình xe bằng GPS", "DN"),
            ("kho_lanh", "giám sát nhiệt độ kho lạnh", "cảnh báo nhiệt độ kho bảo quản", "DN"),
            ("muc_nuoc", "cảnh báo mực nước lũ", "đo mực nước sông suối từ xa", "CQ"),
            ("den_duong", "điều khiển chiếu sáng công cộng", "bật tắt đèn đường theo lịch", "CQ"),
            ("sinh_hieu", "giám sát nhịp tim bệnh nhân từ xa", "theo dõi sinh hiệu người bệnh qua cảm biến", "YT"),
            ("khoa_cua", "điều khiển khóa cửa thông minh", "mở cửa bằng thẻ từ và vân tay", "CN"),
        ],
    },
    "DU_LIEU": {
        "ten": "Khoa học dữ liệu",
        "linh_vuc": ("khoa học dữ liệu", "phân tích dữ liệu"),
        "san_pham": [
            ("hệ thống", "hệ thống phân tích"),
            ("ứng dụng phân tích dữ liệu", "công cụ phân tích số liệu"),
            ("mô hình", "mô hình dự báo"),
            ("bảng điều khiển", "dashboard"),
            ("hệ thống báo cáo", "hệ thống thống kê"),
        ],
        "cong_nghe": ["Power BI", "Apache Spark", "Pandas", "Apache Airflow", "Metabase"],
        "tu_khoa": ["phân tích dữ liệu", "khai phá dữ liệu", "trực quan hóa", "kho dữ liệu", "dự báo"],
        "doi_tuong": [
            ("ket_qua_hoc", "phân tích kết quả học tập", "thống kê điểm số của người học", "GD"),
            ("hanh_vi_mua", "phân tích hành vi mua sắm", "khai phá thói quen mua hàng", "TM"),
            ("du_lieu_ban", "tổng hợp dữ liệu bán hàng", "tích hợp dữ liệu kinh doanh", "TM"),
            ("dieu_hanh", "trực quan hóa báo cáo điều hành", "hiển thị số liệu quản trị trên bảng điều khiển", "DN"),
            ("thoi_hoc", "dự đoán nguy cơ thôi học", "cảnh báo sớm người học bỏ học", "GD"),
            ("dich_benh", "phân tích số liệu dịch bệnh", "thống kê ca bệnh truyền nhiễm", "YT"),
            ("gia_nong_san", "phân tích biến động giá nông sản", "theo dõi giá cả mặt hàng nông nghiệp", "NN"),
            ("roi_bo", "dự đoán khách hàng rời bỏ", "nhận diện khách hàng có nguy cơ ngừng dùng dịch vụ", "DN"),
            ("tai_nan", "phân tích dữ liệu tai nạn giao thông", "thống kê vụ va chạm giao thông", "CQ"),
            ("tuyen_dung", "phân tích nhu cầu tuyển dụng", "khai phá tin tuyển dụng việc làm", "CQ"),
            ("tieu_thu_dien", "phân tích dữ liệu tiêu thụ điện", "thống kê sản lượng điện sử dụng", "DN"),
            ("khach_du_lich", "phân tích lượt khách du lịch", "thống kê lượng du khách theo mùa", "DV"),
            ("dan_so", "phân tích dữ liệu dân cư", "thống kê biến động dân số", "CQ"),
            ("khi_tuong", "phân tích dữ liệu khí tượng", "thống kê lượng mưa và nhiệt độ", "NN"),
            ("mang_xa_hoi", "phân tích dữ liệu mạng xã hội", "khai phá bài đăng trên mạng xã hội", "DN"),
        ],
    },
    "AN_TOAN": {
        "ten": "An toàn thông tin",
        "linh_vuc": ("an toàn thông tin", "bảo mật thông tin"),
        "san_pham": [
            ("hệ thống", "hệ thống bảo mật"),
            ("giải pháp", "phương án kỹ thuật"),
            ("công cụ", "phần mềm hỗ trợ"),
            ("mô hình", "mô hình bảo mật"),
        ],
        "cong_nghe": ["Snort", "Suricata", "Wazuh", "OpenVAS", "Keycloak", "OpenSSL", "pfSense"],
        "tu_khoa": ["an toàn thông tin", "bảo mật", "mã hóa", "phát hiện tấn công", "xác thực"],
        "doi_tuong": [
            ("xam_nhap", "phát hiện xâm nhập mạng", "giám sát và cảnh báo tấn công mạng", "DN"),
            ("lo_hong_web", "rà quét lỗ hổng ứng dụng web", "kiểm thử bảo mật website", "DN"),
            ("xac_thuc", "xác thực hai lớp", "đăng nhập bằng mật khẩu và mã OTP", "DN"),
            ("chu_ky_so", "ký số văn bản điện tử", "chứng thực tài liệu bằng chữ ký số", "CQ"),
            ("ma_doc", "phát hiện mã độc", "nhận diện phần mềm độc hại", "DN"),
            ("email_lua_dao", "phát hiện thư điện tử lừa đảo", "lọc email giả mạo", "DN"),
            ("nhat_ky", "thu thập và phân tích nhật ký hệ thống", "tập trung hóa log máy chủ", "DN"),
            ("ma_hoa", "mã hóa dữ liệu lưu trữ", "bảo vệ tệp tin bằng mật mã", "DN"),
            ("phan_quyen", "quản lý định danh và phân quyền truy cập", "kiểm soát quyền người dùng tập trung", "DN"),
            ("sao_luu", "sao lưu và phục hồi dữ liệu", "dự phòng dữ liệu tự động", "DN"),
            ("tuong_lua", "cấu hình tường lửa", "thiết lập bộ lọc lưu lượng mạng", "GD"),
            ("vpn", "kết nối chi nhánh qua mạng riêng ảo", "thiết lập kênh truyền bảo mật giữa các văn phòng", "DN"),
            ("bay_tan_cong", "giăng bẫy thu hút kẻ tấn công", "triển khai mồi nhử kẻ tấn công", "DN"),
            ("ddos", "phòng chống tấn công từ chối dịch vụ", "giảm thiểu tấn công làm nghẽn máy chủ", "DN"),
            ("wifi", "kiểm soát truy cập mạng không dây", "xác thực người dùng Wi-Fi", "GD"),
        ],
    },
    "ERP": {
        "ten": "ERP / hệ thống doanh nghiệp",
        "linh_vuc": ("hệ thống thông tin quản lý doanh nghiệp", "quản trị nguồn lực doanh nghiệp"),
        "san_pham": [
            ("phần mềm", "chương trình"),
            ("hệ thống", "hệ thống thông tin quản lý"),
            ("phân hệ ERP", "mô-đun hoạch định nguồn lực doanh nghiệp"),
            ("ứng dụng", "ứng dụng quản lý"),
        ],
        "cong_nghe": ["Odoo", "ERPNext", "SQL Server", "Spring Boot", "Laravel"],
        "tu_khoa": ["ERP", "quản trị doanh nghiệp", "quản lý", "báo cáo", "quy trình nghiệp vụ"],
        "doi_tuong": [
            ("nhan_su", "quản lý nhân sự và tiền lương", "tính lương và theo dõi hồ sơ nhân viên", "DN"),
            ("kho_hang", "quản lý kho hàng", "theo dõi nhập xuất tồn kho", "DN"),
            ("ban_hang_quay", "quản lý bán hàng tại quầy", "thu ngân và lập hóa đơn bán lẻ", "TM"),
            ("crm", "quản lý quan hệ khách hàng", "chăm sóc và theo dõi khách hàng", "DN"),
            ("san_xuat", "quản lý sản xuất", "lập kế hoạch và theo dõi đơn hàng sản xuất", "KCN"),
            ("tai_san", "quản lý tài sản cố định", "theo dõi thiết bị và khấu hao tài sản", "CQ"),
            ("ke_toan", "quản lý kế toán", "hạch toán thu chi doanh nghiệp", "DN"),
            ("mua_hang", "quản lý mua hàng", "đặt hàng nhà cung cấp", "DN"),
            ("van_ban", "quản lý văn bản đi đến", "luân chuyển công văn nội bộ", "CQ"),
            ("cham_cong", "chấm công và quản lý ca làm việc", "theo dõi giờ công nhân viên", "KCN"),
            ("nha_thuoc", "quản lý nhà thuốc", "bán thuốc và theo dõi hạn dùng", "YT"),
            ("van_tai", "quản lý vận tải hàng hóa", "điều phối xe giao hàng", "DN"),
            ("phong_kham", "quản lý phòng khám tư nhân", "tiếp đón và thu phí khám bệnh", "YT"),
            ("van_hanh_ks", "quản lý vận hành khách sạn", "điều phối buồng phòng và dịch vụ lưu trú", "DV"),
            ("ky_tuc_xa", "quản lý ký túc xá", "xếp phòng và thu phí nội trú", "GD"),
        ],
    },
    "HOC_TAP": {
        "ten": "Học tập số",
        "linh_vuc": ("công nghệ giáo dục", "chuyển đổi số trong giáo dục"),
        "san_pham": [
            ("website", "trang web"),
            ("hệ thống", "hệ thống học tập trực tuyến"),
            ("nền tảng", "nền tảng số"),
            ("ứng dụng", "ứng dụng học tập"),
        ],
        "cong_nghe": ["Moodle", "WebRTC", "ReactJS", "NodeJS", "Django"],
        "tu_khoa": ["e-learning", "học trực tuyến", "giáo dục", "đánh giá", "LMS"],
        "doi_tuong": [
            ("trac_nghiem", "thi trắc nghiệm trực tuyến", "tổ chức kiểm tra trắc nghiệm qua mạng", "GD"),
            ("khoa_hoc", "quản lý khóa học trực tuyến", "tổ chức lớp học qua mạng", "GD"),
            ("ngan_hang_cau_hoi", "quản lý ngân hàng câu hỏi", "biên soạn đề thi từ kho câu hỏi", "GD"),
            ("lop_ao", "tổ chức lớp học ảo", "giảng dạy trực tuyến có tương tác", "GD"),
            ("video_bai_giang", "chia sẻ bài giảng video", "phát lại bài giảng đã ghi hình", "GD"),
            ("luyen_thi", "luyện thi tốt nghiệp THPT", "ôn tập thi trung học phổ thông", "GD"),
            ("lap_trinh", "học lập trình có chấm bài tự động", "luyện tập lập trình với trình chấm tự động", "GD"),
            ("so_lien_lac", "trao đổi thông tin qua sổ liên lạc điện tử", "kết nối nhà trường với phụ huynh", "GD"),
            ("thoi_khoa_bieu", "xếp thời khóa biểu", "lập lịch giảng dạy tự động", "GD"),
            ("hoc_lieu", "chia sẻ học liệu số", "khai thác kho học liệu điện tử", "GD"),
            ("ngoai_ngu", "học tiếng Anh giao tiếp", "luyện nói tiếng Anh trực tuyến", "GD"),
            ("the_ghi_nho", "ôn tập bằng thẻ ghi nhớ", "ghi nhớ kiến thức theo phương pháp lặp lại ngắt quãng", "GD"),
            ("khao_sat", "khảo sát ý kiến người học về giảng dạy", "lấy phản hồi của sinh viên về học phần", "GD"),
            ("dien_dan", "tổ chức diễn đàn hỏi đáp học tập", "xây dựng cộng đồng trao đổi bài tập", "GD"),
            ("nang_luc", "lưu trữ hồ sơ năng lực của sinh viên", "quản lý sản phẩm học tập cá nhân", "GD"),
        ],
    },
}

# Công nghệ phù hợp theo đối tượng (chỉ khai báo khi không phải mọi công nghệ của cụm
# đều hợp lý). Danh sách rỗng = tiêu đề không nêu công nghệ.
_ANH = ["YOLOv8", "OpenCV", "TensorFlow", "PyTorch"]
_VAN_BAN = ["PhoBERT", "TensorFlow", "PyTorch"]
_BANG = ["scikit-learn", "TensorFlow", "PyTorch"]
CONG_NGHE_PHU_HOP: dict[str, list[str]] = {
    "AI_ML.bien_so": _ANH, "AI_ML.khuon_mat": _ANH, "AI_ML.benh_la": _ANH, "AI_ML.te_nga": _ANH,
    "AI_ML.chu_viet": _ANH, "AI_ML.phan_loai_rac": _ANH, "AI_ML.x_quang": _ANH, "AI_ML.dem_xe": _ANH,
    "AI_ML.cam_xuc": _VAN_BAN, "AI_ML.chatbot": _VAN_BAN, "AI_ML.tom_tat": _VAN_BAN, "AI_ML.tin_gia": _VAN_BAN,
    "AI_ML.doanh_thu": _BANG, "AI_ML.goi_y": _BANG, "AI_ML.giong_noi": ["TensorFlow", "PyTorch"],
    "AN_TOAN.xam_nhap": ["Snort", "Suricata", "Wazuh"],
    "AN_TOAN.lo_hong_web": ["OpenVAS"],
    "AN_TOAN.xac_thuc": ["Keycloak"],
    "AN_TOAN.chu_ky_so": ["OpenSSL"],
    "AN_TOAN.ma_doc": ["Wazuh", "Suricata"],
    "AN_TOAN.email_lua_dao": ["Wazuh"],
    "AN_TOAN.nhat_ky": ["Wazuh"],
    "AN_TOAN.ma_hoa": ["OpenSSL"],
    "AN_TOAN.phan_quyen": ["Keycloak"],
    "AN_TOAN.sao_luu": [],
    "AN_TOAN.tuong_lua": ["pfSense", "Suricata"],
    "AN_TOAN.vpn": ["pfSense", "OpenSSL"],
    "AN_TOAN.bay_tan_cong": ["Snort", "Suricata"],
    "AN_TOAN.ddos": ["pfSense", "Suricata"],
    "AN_TOAN.wifi": ["pfSense", "Keycloak"],
}


def cong_nghe_cua(cum: str, ma_doi_tuong: str) -> list[str]:
    return CONG_NGHE_PHU_HOP.get(ma_doi_tuong, CUM[cum]["cong_nghe"])


# Từ khóa (tu_khoa) riêng cho các cụm mà không phải mọi từ khóa đều hợp với mọi đối tượng.
TU_KHOA_PHU_HOP: dict[str, list[str]] = {
    "AI_ML.anh": ["học máy", "học sâu", "xử lý ảnh", "thị giác máy tính", "trí tuệ nhân tạo"],
    "AI_ML.van_ban": ["học máy", "học sâu", "xử lý ngôn ngữ tự nhiên", "trí tuệ nhân tạo"],
    "AI_ML.bang": ["học máy", "dự báo", "khai phá dữ liệu", "trí tuệ nhân tạo"],
}


def tu_khoa_cua(cum: str, ma_doi_tuong: str) -> list[str]:
    cn = CONG_NGHE_PHU_HOP.get(ma_doi_tuong)
    if cum == "AI_ML" and cn is not None:
        if cn is _ANH:
            return TU_KHOA_PHU_HOP["AI_ML.anh"]
        if cn is _BANG:
            return TU_KHOA_PHU_HOP["AI_ML.bang"]
        return TU_KHOA_PHU_HOP["AI_ML.van_ban"]
    return CUM[cum]["tu_khoa"]


# ---------------------------------------------------------------------------
# Cụm động từ mở đầu tiêu đề và đồng nghĩa (dùng khi diễn đạt lại tiêu đề).
# ---------------------------------------------------------------------------
DONG_TU_TIEU_DE: list[str] = [
    "Xây dựng",
    "Phát triển",
    "Thiết kế và xây dựng",
    "Nghiên cứu và phát triển",
    "Xây dựng và triển khai",
    "Thiết kế và cài đặt",
]
DONG_NGHIA_DONG_TU: dict[str, list[str]] = {
    "Xây dựng": ["Phát triển", "Thiết kế và cài đặt"],
    "Phát triển": ["Xây dựng", "Thiết kế và xây dựng"],
    "Thiết kế và xây dựng": ["Phát triển", "Nghiên cứu và phát triển"],
    "Nghiên cứu và phát triển": ["Xây dựng", "Thiết kế và cài đặt"],
    "Xây dựng và triển khai": ["Phát triển", "Thiết kế và xây dựng"],
    "Thiết kế và cài đặt": ["Xây dựng", "Phát triển"],
}

# ---------------------------------------------------------------------------
# Đơn vị ứng dụng: (dạng viết tắt, dạng đầy đủ) — {…} là danh sách tên riêng.
# Mỗi nhóm đơn vị ứng với "nhóm" của đối tượng ở trên.
# ---------------------------------------------------------------------------
DON_VI: dict[str, list[tuple[str, str]]] = {
    "GD": [
        ("trường THPT {truong}", "trường trung học phổ thông {truong}"),
        ("trường THCS {truong}", "trường trung học cơ sở {truong}"),
        ("trung tâm GDTX {huyen}", "trung tâm giáo dục thường xuyên {huyen}"),
        ("trung tâm ngoại ngữ {dn}", "trung tâm đào tạo ngoại ngữ {dn}"),
        ("trường CĐ nghề {tinh}", "trường cao đẳng nghề {tinh}"),
    ],
    "YT": [
        ("bệnh viện đa khoa tỉnh {tinh}", "bệnh viện tuyến tỉnh {tinh}"),
        ("phòng khám đa khoa {dn}", "cơ sở khám chữa bệnh đa khoa {dn}"),
        ("TTYT huyện {huyen}", "trung tâm y tế huyện {huyen}"),
        ("trạm y tế xã {xa}", "trạm y tế cấp xã {xa}"),
    ],
    "DN": [
        ("công ty TNHH {dn}", "công ty trách nhiệm hữu hạn {dn}"),
        ("công ty CP {dn}", "công ty cổ phần {dn}"),
        ("DNTN {dn}", "doanh nghiệp tư nhân {dn}"),
    ],
    "TM": [
        ("cửa hàng tiện lợi {dn}", "cửa hiệu tiện lợi {dn}"),
        ("siêu thị mini {dn}", "siêu thị quy mô nhỏ {dn}"),
        ("chuỗi cửa hàng {dn}", "hệ thống cửa hàng {dn}"),
    ],
    "CQ": [
        ("UBND xã {xa}", "ủy ban nhân dân xã {xa}"),
        ("UBND huyện {huyen}", "ủy ban nhân dân huyện {huyen}"),
        ("sở TT&TT tỉnh {tinh}", "sở thông tin và truyền thông tỉnh {tinh}"),
    ],
    "NN": [
        ("HTX nông nghiệp {xa}", "hợp tác xã nông nghiệp {xa}"),
        ("trang trại {dn}", "nông trại {dn}"),
        ("vùng chè {xa}", "vùng trồng chè {xa}"),
    ],
    "DV": [
        ("khách sạn {dn}", "cơ sở lưu trú {dn}"),
        ("nhà hàng {dn}", "quán ăn {dn}"),
        ("khu du lịch {huyen}", "điểm du lịch {huyen}"),
        ("trung tâm thể thao {dn}", "câu lạc bộ thể thao {dn}"),
    ],
    "GT": [
        ("bến xe khách {tinh}", "bến xe liên tỉnh {tinh}"),
        ("bãi đỗ xe {dn}", "bãi giữ xe {dn}"),
        ("công ty vận tải {dn}", "doanh nghiệp vận tải {dn}"),
    ],
    "KCN": [
        ("nhà máy may {dn}", "xưởng may {dn}"),
        ("KCN {huyen}", "khu công nghiệp {huyen}"),
        ("xưởng cơ khí {dn}", "cơ sở cơ khí {dn}"),
    ],
    "CN": [
        ("hộ gia đình tại {huyen}", "các gia đình ở {huyen}"),
        ("người dân TP {tinh}", "cư dân thành phố {tinh}"),
        ("người thuê trọ tại {huyen}", "người ở trọ tại {huyen}"),
    ],
}
# Nhóm đơn vị chỉ đi với từ nối "cho" (không nói "tại người dân…").
NHOM_CHI_DUNG_CHO = {"CN"}

TEN_RIENG: dict[str, list[str]] = {
    "tinh": ["Thái Nguyên", "Bắc Kạn", "Tuyên Quang", "Lạng Sơn", "Bắc Giang", "Cao Bằng",
             "Hà Giang", "Yên Bái", "Lào Cai", "Phú Thọ", "Vĩnh Phúc", "Hòa Bình"],
    "huyen": ["Đại Từ", "Phú Lương", "Đồng Hỷ", "Võ Nhai", "Định Hóa", "Phú Bình",
              "Phổ Yên", "Sông Công", "Chợ Mới", "Ba Bể", "Na Rì", "Yên Sơn"],
    "xa": ["Quyết Thắng", "Phúc Hà", "Tân Cương", "Gia Sàng", "Tích Lương", "Cam Giá",
           "Đồng Bẩm", "Phúc Xuân", "Hóa Thượng", "Sơn Cẩm"],
    "dn": ["Minh Phát", "An Khang", "Tân Tiến", "Hưng Thịnh", "Phúc An", "Thành Công",
           "Việt Tiến", "Đại Phát", "Hoàng Long", "Bắc Sơn", "Trường Thịnh", "Nam Việt"],
    "truong": ["Chu Văn An", "Lê Quý Đôn", "Nguyễn Trãi", "Trần Phú", "Lý Tự Trọng",
               "Ngô Quyền", "Hoàng Văn Thụ", "Quang Trung", "Lê Hồng Phong", "Nguyễn Huệ"],
}

# Từ nối giữa đối tượng và đơn vị trong tiêu đề.
TU_NOI = ["cho", "tại"]
# Hậu tố công nghệ (tùy chọn) trong tiêu đề.
HAU_TO_CONG_NGHE = ["sử dụng {cg}", "trên nền tảng {cg}"]

# ---------------------------------------------------------------------------
# Bản đồ đồng nghĩa (hai chiều, thay một lượt theo ranh giới âm tiết) dùng khi
# diễn đạt lại câu (DIEN_DAT_LAI). Chỉ gồm cặp an toàn về ngữ pháp.
# ---------------------------------------------------------------------------
DONG_NGHIA: list[tuple[str, str]] = [
    ("người dùng", "người sử dụng"),
    ("nhanh chóng", "mau lẹ"),
    ("thuận tiện", "tiện lợi"),
    ("khoảng", "chừng"),
    ("nhằm", "với mục đích"),
    ("tuy nhiên", "dù vậy"),
    ("hiện nay", "ngày nay"),
    ("theo dõi", "giám sát"),
    ("tra cứu", "tìm kiếm"),
    ("thống kê", "tổng hợp"),
    ("khách hàng", "người mua"),
    ("sinh viên", "người học"),
    ("học sinh", "học trò"),
    ("giảng viên", "người dạy"),
    ("bác sĩ", "thầy thuốc"),
    ("người bệnh", "bệnh nhân"),
    ("cảnh báo", "báo động"),
    ("đăng nhập", "vào tài khoản"),
    ("lưu trữ", "lưu giữ"),
    ("dự báo", "dự đoán"),
    ("phát hiện", "nhận biết"),
    ("nhận dạng", "nhận diện"),
    ("kiểm tra", "rà soát"),
    ("đơn hàng", "đơn mua"),
    ("sản phẩm", "mặt hàng"),
    ("doanh nghiệp", "công ty"),
    ("dễ dàng", "thuận lợi"),
    ("mã OTP", "mật mã dùng một lần"),
    ("tài liệu", "văn bản"),
    ("trực tuyến", "qua mạng"),
    ("hỗ trợ", "trợ giúp"),
    ("thực hiện", "tiến hành"),
    ("mục tiêu", "mục đích"),
    ("khó khăn", "trở ngại"),
    ("thường xuyên", "liên tục"),
    ("hằng ngày", "mỗi ngày"),
    ("hằng tháng", "mỗi tháng"),
    ("định kỳ", "theo chu kỳ"),
    ("cơ bản", "căn bản"),
    ("đáng kể", "rõ rệt"),
    ("ghi nhận", "ghi lại"),
    ("máy chủ", "server"),
    ("ứng viên", "người ứng tuyển"),
    ("nhà tuyển dụng", "bên tuyển dụng"),
    ("thí sinh", "người dự thi"),
    ("phụ huynh", "cha mẹ học sinh"),
    ("khách lưu trú", "khách thuê phòng"),
    ("tài xế", "bác tài"),
    ("hành khách", "người đi xe"),
    ("thủ thư", "cán bộ thư viện"),
    ("bạn đọc", "độc giả"),
    ("thu ngân", "nhân viên thu tiền"),
    ("thủ kho", "người giữ kho"),
    ("lễ tân", "nhân viên tiếp đón"),
]

# ---------------------------------------------------------------------------
# Tên người (ghép theo thứ tự Việt Nam: Họ + đệm + tên, như backend/app/seed.py).
# ---------------------------------------------------------------------------
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi",
      "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đinh", "Ma", "Hà", "Lương", "Nông", "Triệu"]
DEM_NAM = ["Văn", "Đức", "Minh", "Quang", "Hữu", "Thành", "Trung", "Công", "Tuấn", "Mạnh", "Xuân", "Duy"]
DEM_NU = ["Thị", "Thu", "Thanh", "Ngọc", "Phương", "Mai", "Khánh", "Hồng", "Bích", "Thùy"]
TEN_NAM = ["An", "Bình", "Cường", "Dũng", "Đạt", "Hải", "Hiếu", "Hoàng", "Hùng", "Huy", "Khánh",
           "Long", "Nam", "Phong", "Quân", "Sơn", "Thắng", "Toàn", "Tú", "Vinh", "Kiên", "Lâm"]
TEN_NU = ["Anh", "Châu", "Diệp", "Dung", "Giang", "Hà", "Hạnh", "Hằng", "Hoa", "Huyền", "Lan",
          "Linh", "Loan", "Ngân", "Nhung", "Oanh", "Phương", "Quỳnh", "Thảo", "Trang", "Uyên", "Yến"]
# Tên người thật liên quan tới đồ án — không bao giờ được sinh ra (T-04-08).
TEN_CAM = {"Nguyễn Thị Mai Anh", "Hà Thị Thanh", "Nguyễn Mai Anh"}

HOC_VI = ["ThS.", "TS.", "ThS.", "PGS.TS."]


# ===========================================================================
# PHẦN 2 (DATA-03, D-06): nội dung tài liệu
# ===========================================================================

# ---------------------------------------------------------------------------
# Hồ sơ đối tượng dùng trong tài liệu: "tác nhân 1|tác nhân 2", "4 chức năng", "3 thực thể dữ liệu".
# Có hồ sơ: 6 đối tượng đầu (không dự trữ) + 2 đối tượng dự trữ đầu tiên của mỗi cụm = 64.
# Đơn vị của tài liệu được lấy theo nhóm đơn vị của đối tượng (vocab.DON_VI).
# ---------------------------------------------------------------------------
HO_SO: dict[str, tuple[str, str, str]] = {
    # WEB
    "WEB.thu_vien": ("thủ thư|bạn đọc", "tra cứu đầu sách|lập phiếu mượn|ghi nhận trả sách|thống kê sách quá hạn", "phiếu mượn|đầu sách|thẻ bạn đọc"),
    "WEB.ban_hang_online": ("chủ cửa hàng|khách mua hàng", "đặt hàng trực tuyến|quản lý giỏ hàng|theo dõi đơn giao|áp dụng mã giảm giá", "đơn hàng|sản phẩm|phiếu giao hàng"),
    "WEB.dat_phong_ks": ("lễ tân|khách lưu trú", "tìm phòng trống|đặt cọc giữ phòng|làm thủ tục nhận phòng|xuất hóa đơn lưu trú", "phòng nghỉ|phiếu đặt phòng|hóa đơn lưu trú"),
    "WEB.tuyen_sinh": ("cán bộ tuyển sinh|thí sinh", "nộp hồ sơ xét tuyển|tải minh chứng học bạ|duyệt hồ sơ|công bố kết quả trúng tuyển", "hồ sơ xét tuyển|ngành đào tạo|nguyện vọng"),
    "WEB.dat_ban_nh": ("nhân viên phục vụ|thực khách", "đặt bàn trước|chọn món theo thực đơn|chuyển phiếu xuống bếp|thanh toán hóa đơn", "bàn ăn|thực đơn|phiếu gọi món"),
    "WEB.viec_lam": ("nhà tuyển dụng|ứng viên", "đăng tin tuyển dụng|tìm việc theo ngành nghề|nộp hồ sơ ứng tuyển|lên lịch phỏng vấn", "tin tuyển dụng|hồ sơ ứng viên|lịch phỏng vấn"),
    "WEB.quyen_gop": ("ban vận động|nhà hảo tâm", "tạo đợt quyên góp|ghi nhận khoản ủng hộ|công khai sao kê|phân bổ tiền hỗ trợ", "đợt quyên góp|khoản ủng hộ|hộ được hỗ trợ"),
    "WEB.tour": ("điều hành tour|du khách", "tra cứu lịch khởi hành|đặt chỗ tour|thanh toán đặt cọc|đánh giá chuyến đi", "chương trình tour|lịch khởi hành|phiếu đặt tour"),
    # MOBILE
    "MOBILE.kham_benh": ("bác sĩ|người bệnh", "chọn chuyên khoa|đặt giờ khám|nhận số thứ tự|xem kết quả khám", "lịch khám|phiếu hẹn|hồ sơ bệnh án"),
    "MOBILE.giao_do_an": ("chủ quán|người giao hàng", "duyệt thực đơn|đặt món|ghép đơn giao|theo dõi vị trí người giao", "món ăn|đơn đặt món|chuyến giao"),
    "MOBILE.chi_tieu": ("người dùng|thành viên gia đình", "ghi khoản chi|đặt hạn mức ngân sách|phân loại giao dịch|xem biểu đồ thu chi", "khoản chi|hạn mức ngân sách|danh mục chi tiêu"),
    "MOBILE.diem_danh": ("giảng viên|sinh viên", "tạo buổi học|quét mã QR điểm danh|ghi nhận vắng mặt|tổng hợp chuyên cần", "buổi học|lượt điểm danh|danh sách lớp"),
    "MOBILE.goi_xe": ("tài xế|hành khách", "đặt chuyến đi|ước tính cước phí|ghép tài xế gần nhất|đánh giá chuyến xe", "chuyến đi|bảng giá cước|vị trí tài xế"),
    "MOBILE.suc_khoe": ("người dùng|chuyên gia dinh dưỡng", "ghi chỉ số cân nặng|đếm bước chân|nhắc uống nước|xem báo cáo tuần", "chỉ số sức khỏe|nhật ký vận động|mục tiêu cá nhân"),
    "MOBILE.the_duc": ("học viên|huấn luyện viên", "chọn bài tập|hẹn giờ luyện tập|ghi nhận lượng calo|theo dõi tiến bộ", "bài tập|buổi tập|lịch luyện tập"),
    "MOBILE.thu_cung": ("chủ vật nuôi|nhân viên chăm sóc", "đặt lịch tắm tỉa|ghi sổ tiêm phòng|nhắc lịch tẩy giun|mua thức ăn cho vật nuôi", "hồ sơ vật nuôi|lịch hẹn chăm sóc|sổ tiêm phòng"),
    # AI_ML
    "AI_ML.bien_so": ("nhân viên bảo vệ|chủ phương tiện", "phát hiện vùng biển số|nhận dạng ký tự|đối chiếu xe ra vào|lưu ảnh lượt gửi xe", "ảnh biển số|lượt xe ra vào|vé gửi xe"),
    "AI_ML.khuon_mat": ("giáo viên|học sinh", "đăng ký ảnh khuôn mặt|phát hiện khuôn mặt|so khớp đặc trưng|xuất danh sách vắng", "ảnh khuôn mặt|vector đặc trưng|buổi điểm danh"),
    "AI_ML.cam_xuc": ("nhân viên chăm sóc khách hàng|khách hàng", "thu thập bình luận|tiền xử lý văn bản|gán nhãn cảm xúc|thống kê ý kiến tiêu cực", "bình luận|nhãn cảm xúc|tập huấn luyện"),
    "AI_ML.chatbot": ("cán bộ tư vấn|thí sinh", "nhận câu hỏi|xác định ý định người hỏi|trả lời tự động|chuyển câu hỏi khó cho cán bộ", "câu hỏi|kịch bản hội thoại|kho tri thức tuyển sinh"),
    "AI_ML.benh_la": ("nông dân|kỹ sư nông nghiệp", "chụp ảnh lá|phân loại bệnh|đề xuất cách xử lý|ghi nhật ký đồng ruộng", "ảnh lá cây|loại bệnh|khuyến cáo xử lý"),
    "AI_ML.doanh_thu": ("quản lý cửa hàng|nhân viên kinh doanh", "tổng hợp doanh số|làm sạch chuỗi thời gian|huấn luyện mô hình dự báo|so sánh sai số dự báo", "chuỗi doanh số|đặc trưng mùa vụ|kết quả dự báo"),
    "AI_ML.dem_xe": ("cán bộ điều hành giao thông|người tham gia giao thông", "phát hiện phương tiện|theo vết đối tượng|đếm lượt qua vạch|xuất báo cáo lưu lượng", "khung hình camera|loại phương tiện|số liệu lưu lượng"),
    "AI_ML.giong_noi": ("người dùng|biên tập viên", "ghi âm giọng nói|tách đoạn âm thanh|chuyển thành văn bản|chỉnh sửa bản chép lời", "tệp âm thanh|bản chép lời|từ điển phát âm"),
    # IOT
    "IOT.nha_kinh": ("kỹ thuật viên|chủ nhà kính", "đo nhiệt độ và độ ẩm|bật quạt thông gió|cảnh báo vượt ngưỡng|xem lịch sử cảm biến", "cảm biến nhiệt ẩm|ngưỡng cảnh báo|bản ghi đo"),
    "IOT.tuoi_cay": ("chủ vườn|kỹ thuật viên", "đo độ ẩm đất|mở van tưới|hẹn lịch tưới|báo lượng nước đã dùng", "cảm biến độ ẩm đất|van điện từ|lịch tưới"),
    "IOT.nha_thong_minh": ("chủ nhà|thành viên gia đình", "bật tắt đèn từ xa|điều khiển điều hòa|tạo kịch bản tự động|nhận cảnh báo mở cửa", "thiết bị điện|kịch bản tự động|trạng thái thiết bị"),
    "IOT.khong_khi": ("cán bộ môi trường|người dân", "đo nồng độ bụi mịn|tính chỉ số AQI|hiển thị bản đồ ô nhiễm|gửi cảnh báo sức khỏe", "trạm quan trắc|chỉ số AQI|bản tin chất lượng không khí"),
    "IOT.bai_do_xe": ("nhân viên trông xe|người lái xe", "phát hiện chỗ trống|hiển thị sơ đồ bãi|thu phí gửi xe|báo bãi đầy", "ô đỗ xe|cảm biến siêu âm|lượt gửi xe"),
    "IOT.ao_nuoi": ("chủ ao|kỹ thuật viên thủy sản", "đo pH và oxy hòa tan|bật máy sục khí|cảnh báo nước bẩn|ghi nhật ký cho ăn", "chỉ số chất lượng nước|máy sục khí|nhật ký ao nuôi"),
    "IOT.den_duong": ("cán bộ đô thị|công nhân vận hành", "lập lịch bật tắt|điều chỉnh độ sáng|phát hiện đèn hỏng|thống kê điện năng chiếu sáng", "tủ điều khiển|tuyến đèn|lịch chiếu sáng"),
    "IOT.sinh_hieu": ("điều dưỡng|người bệnh", "đo nhịp tim|đo nồng độ oxy máu|báo động bất thường|lưu biểu đồ sinh hiệu", "thiết bị đeo|chỉ số sinh hiệu|cảnh báo y tế"),
    # DU_LIEU
    "DU_LIEU.ket_qua_hoc": ("cán bộ đào tạo|cố vấn học tập", "tổng hợp bảng điểm|phân nhóm học lực|phát hiện học phần khó|lập báo cáo theo lớp", "bảng điểm|học phần|kết quả học kỳ"),
    "DU_LIEU.hanh_vi_mua": ("nhân viên tiếp thị|quản lý bán hàng", "khai phá luật kết hợp|phân khúc khách hàng|tìm sản phẩm hay mua kèm|đề xuất chương trình khuyến mại", "giao dịch mua|giỏ hàng|nhóm khách hàng"),
    "DU_LIEU.du_lieu_ban": ("kỹ sư dữ liệu|nhà quản lý", "trích xuất dữ liệu nguồn|chuẩn hóa bảng giao dịch|nạp dữ liệu định kỳ|truy vấn đa chiều", "bảng sự kiện bán hàng|bảng chiều thời gian|khối dữ liệu"),
    "DU_LIEU.dieu_hanh": ("ban giám đốc|chuyên viên phân tích", "kết nối nguồn số liệu|tạo biểu đồ chỉ tiêu|lọc theo kỳ báo cáo|chia sẻ bảng điều khiển", "chỉ tiêu kinh doanh|biểu đồ|kỳ báo cáo"),
    "DU_LIEU.thoi_hoc": ("cố vấn học tập|sinh viên", "thu thập dữ liệu học vụ|chọn đặc trưng dự đoán|chấm điểm rủi ro|gửi cảnh báo sớm", "hồ sơ học vụ|điểm rủi ro|danh sách cảnh báo"),
    "DU_LIEU.dich_benh": ("cán bộ y tế dự phòng|lãnh đạo ngành y tế", "nhập số ca mắc|vẽ bản đồ ổ dịch|tính tốc độ lây lan|dự báo số ca mới", "ca bệnh|ổ dịch|chuỗi số liệu theo ngày"),
    "DU_LIEU.dan_so": ("cán bộ thống kê|lãnh đạo địa phương", "tổng hợp số hộ|phân tích cơ cấu tuổi|theo dõi di cư|lập tháp dân số", "nhân khẩu|hộ gia đình|địa bàn thống kê"),
    "DU_LIEU.khi_tuong": ("cán bộ khí tượng|người sản xuất nông nghiệp", "thu thập số liệu trạm đo|làm sạch giá trị thiếu|phát hiện xu hướng mưa|dự báo nhiệt độ theo mùa", "trạm đo|lượng mưa|nhiệt độ trung bình"),
    # AN_TOAN
    "AN_TOAN.xam_nhap": ("quản trị mạng|chuyên viên an ninh", "bắt gói tin|so khớp luật phát hiện|gửi cảnh báo tấn công|tổng hợp sự kiện an ninh", "gói tin|bộ luật phát hiện|cảnh báo an ninh"),
    "AN_TOAN.lo_hong_web": ("kiểm thử viên|lập trình viên", "dò tìm đường dẫn ẩn|kiểm tra lỗi SQL injection|đánh giá mức độ rủi ro|lập báo cáo khắc phục", "lỗ hổng|mức độ nghiêm trọng|báo cáo kiểm thử"),
    "AN_TOAN.xac_thuc": ("người dùng|quản trị hệ thống", "đăng nhập bằng mật khẩu|sinh mã OTP|xác minh thiết bị tin cậy|khóa tài khoản đáng ngờ", "mã OTP|phiên đăng nhập|thiết bị tin cậy"),
    "AN_TOAN.chu_ky_so": ("văn thư|lãnh đạo đơn vị", "tạo cặp khóa|ký văn bản|xác minh chữ ký|thu hồi chứng thư", "chứng thư số|văn bản điện tử|khóa bí mật"),
    "AN_TOAN.ma_doc": ("chuyên viên an ninh|người dùng cuối", "trích đặc trưng tệp|phân loại tệp nghi ngờ|cách ly tệp độc hại|cập nhật mẫu nhận diện", "tệp thực thi|mẫu mã độc|kết quả quét"),
    "AN_TOAN.email_lua_dao": ("nhân viên văn phòng|quản trị thư điện tử", "phân tích tiêu đề thư|kiểm tra đường dẫn đáng ngờ|chấm điểm lừa đảo|chuyển thư vào vùng cách ly", "thư điện tử|đường dẫn|điểm lừa đảo"),
    "AN_TOAN.bay_tan_cong": ("quản trị mạng|chuyên viên phân tích mối đe dọa", "giả lập dịch vụ dễ tổn thương|ghi lại thao tác xâm nhập|phân tích hành vi tấn công|chia sẻ dấu hiệu nhận diện", "dịch vụ mồi|phiên tấn công|dấu hiệu nhận diện"),
    "AN_TOAN.ddos": ("quản trị hệ thống|khách truy cập", "đo lưu lượng bất thường|giới hạn tốc độ yêu cầu|chặn địa chỉ nguồn xấu|chuyển hướng lưu lượng sạch", "lưu lượng truy cập|ngưỡng yêu cầu|danh sách chặn"),
    # ERP
    "ERP.nhan_su": ("cán bộ nhân sự|nhân viên", "lưu hồ sơ nhân viên|tính lương hằng tháng|quản lý hợp đồng lao động|duyệt đơn nghỉ phép", "hồ sơ nhân viên|bảng lương|hợp đồng lao động"),
    "ERP.kho_hang": ("thủ kho|nhân viên mua hàng", "lập phiếu nhập kho|lập phiếu xuất kho|kiểm kê định kỳ|cảnh báo tồn kho thấp", "phiếu nhập|phiếu xuất|mặt hàng"),
    "ERP.ban_hang_quay": ("thu ngân|quản lý ca", "quét mã vạch|tính tiền và in hóa đơn|chốt doanh thu ca|đổi trả hàng", "hóa đơn bán lẻ|ca bán hàng|mã vạch"),
    "ERP.crm": ("nhân viên kinh doanh|trưởng phòng kinh doanh", "ghi nhận khách hàng tiềm năng|lên lịch chăm sóc|theo dõi cơ hội bán hàng|đo mức độ hài lòng", "khách hàng tiềm năng|cơ hội bán hàng|lịch chăm sóc"),
    "ERP.san_xuat": ("quản đốc xưởng|công nhân", "lập lệnh sản xuất|tính định mức nguyên liệu|ghi nhận sản lượng|kiểm tra chất lượng thành phẩm", "lệnh sản xuất|định mức nguyên liệu|thành phẩm"),
    "ERP.tai_san": ("cán bộ quản trị|kế toán tài sản", "ghi tăng tài sản|điều chuyển thiết bị|tính khấu hao|kiểm kê cuối năm", "thẻ tài sản|biên bản bàn giao|mức khấu hao"),
    "ERP.phong_kham": ("nhân viên đón tiếp|bác sĩ", "tiếp đón người bệnh|kê đơn thuốc|thu phí khám|in phiếu chỉ định", "phiếu khám|đơn thuốc|biên lai thu phí"),
    "ERP.van_hanh_ks": ("quản lý buồng phòng|nhân viên phục vụ phòng", "phân công dọn phòng|ghi dịch vụ phát sinh|cập nhật tình trạng phòng|lập báo cáo công suất", "tình trạng phòng|dịch vụ phát sinh|báo cáo công suất"),
    # HOC_TAP
    "HOC_TAP.trac_nghiem": ("giáo viên|thí sinh", "tạo đề thi ngẫu nhiên|giới hạn thời gian làm bài|chấm điểm tự động|phân tích độ khó câu hỏi", "đề thi|bài làm|câu hỏi trắc nghiệm"),
    "HOC_TAP.khoa_hoc": ("giảng viên|học viên", "tạo khóa học|đăng tải bài học|giao bài tập|theo dõi tiến độ học", "khóa học|bài học|bài tập"),
    "HOC_TAP.ngan_hang_cau_hoi": ("tổ trưởng chuyên môn|giáo viên", "nhập câu hỏi theo chương|gắn mức độ nhận thức|sinh đề theo ma trận|kiểm tra câu hỏi trùng", "câu hỏi|ma trận đề|mức độ nhận thức"),
    "HOC_TAP.lop_ao": ("giảng viên|người học", "mở phòng học trực tuyến|chia sẻ màn hình|chia nhóm thảo luận|ghi hình buổi học", "phòng học ảo|buổi học trực tuyến|bản ghi hình"),
    "HOC_TAP.video_bai_giang": ("giảng viên|sinh viên", "tải lên video bài giảng|chèn câu hỏi giữa video|ghi nhận thời lượng xem|bình luận theo mốc thời gian", "video bài giảng|mốc thời gian|lượt xem"),
    "HOC_TAP.luyen_thi": ("học sinh|giáo viên chủ nhiệm", "làm đề thi thử|xem lời giải chi tiết|thống kê câu sai|gợi ý chuyên đề cần ôn", "đề thi thử|lời giải|chuyên đề ôn tập"),
    "HOC_TAP.khao_sat": ("phòng đảm bảo chất lượng|sinh viên", "tạo phiếu khảo sát|thu thập ý kiến ẩn danh|tổng hợp điểm hài lòng|gửi kết quả cho giảng viên", "phiếu khảo sát|câu trả lời|điểm hài lòng"),
    "HOC_TAP.dien_dan": ("người học|người điều hành diễn đàn", "đăng câu hỏi|trả lời và bình chọn|gắn thẻ chủ đề|kiểm duyệt bài viết", "bài đăng|câu trả lời|thẻ chủ đề"),
}

# ---------------------------------------------------------------------------
# Dữ kiện công nghệ: (loại, loại diễn đạt lại, mục đích, mục đích diễn đạt lại, ưu điểm, ưu điểm diễn đạt lại)
# ---------------------------------------------------------------------------
CONG_NGHE: dict[str, tuple[str, str, str, str, str, str]] = {
    "ReactJS": ("thư viện JavaScript mã nguồn mở", "thư viện lập trình giao diện viết bằng JavaScript",
                "xây dựng giao diện theo các thành phần tái sử dụng", "chia giao diện thành những khối nhỏ dùng lại được",
                "cập nhật giao diện nhanh nhờ DOM ảo", "hiển thị thay đổi mượt mà nhờ cơ chế DOM ảo"),
    "VueJS": ("framework JavaScript lũy tiến", "bộ khung phát triển giao diện web gọn nhẹ",
              "xây dựng giao diện có ràng buộc dữ liệu hai chiều", "liên kết dữ liệu với giao diện theo cả hai hướng",
              "dễ học và dễ tích hợp dần vào dự án", "có đường cong học tập thấp, dễ đưa vào dự án sẵn có"),
    "Laravel": ("framework PHP theo mô hình MVC", "bộ khung lập trình PHP tách lớp mô hình, khung nhìn và điều khiển",
                "xây dựng phần xử lý phía máy chủ", "phát triển phần nghiệp vụ chạy trên máy chủ",
                "có sẵn ORM Eloquent và cơ chế định tuyến rõ ràng", "cung cấp Eloquent để thao tác cơ sở dữ liệu cùng bộ định tuyến gọn gàng"),
    "Django": ("framework Python bậc cao", "bộ khung phát triển web viết bằng Python",
               "xây dựng nhanh ứng dụng có trang quản trị", "tạo nhanh website kèm giao diện quản trị dựng sẵn",
               "tích hợp sẵn xác thực và bảo vệ trước nhiều kiểu tấn công", "đi kèm cơ chế đăng nhập và các lớp phòng vệ bảo mật mặc định"),
    "Spring Boot": ("framework Java cho ứng dụng doanh nghiệp", "nền tảng lập trình Java hướng tới hệ thống doanh nghiệp",
                    "xây dựng dịch vụ REST chạy độc lập", "tạo các API REST có thể khởi chạy riêng rẽ",
                    "tự cấu hình và có hệ sinh thái thư viện phong phú", "giảm cấu hình thủ công và sở hữu nhiều thư viện hỗ trợ"),
    "NodeJS": ("môi trường chạy JavaScript phía máy chủ", "nền tảng thực thi JavaScript bên ngoài trình duyệt",
               "xây dựng API xử lý nhiều kết nối đồng thời", "phục vụ lượng lớn yêu cầu cùng lúc qua giao diện lập trình",
               "có mô hình vào ra bất đồng bộ không chặn", "xử lý bất đồng bộ giúp tiết kiệm tài nguyên"),
    "Flutter": ("bộ công cụ giao diện đa nền tảng của Google", "nền tảng phát triển ứng dụng chạy trên nhiều hệ điều hành do Google phát hành",
                "viết một mã nguồn cho cả Android và iOS", "dùng chung một bộ mã cho hai hệ điều hành di động",
                "có hiệu năng gần với ứng dụng gốc và hỗ trợ tải lại nóng", "chạy mượt gần như ứng dụng thuần và cho phép xem thay đổi tức thì"),
    "React Native": ("framework di động dựa trên JavaScript", "bộ khung lập trình ứng dụng điện thoại bằng JavaScript",
                     "tạo ứng dụng di động từ các thành phần React", "dựng giao diện điện thoại bằng những khối React quen thuộc",
                     "tận dụng được kiến thức lập trình web sẵn có", "cho phép lập trình viên web chuyển sang di động dễ dàng"),
    "Kotlin": ("ngôn ngữ lập trình hiện đại cho Android", "ngôn ngữ được Google khuyến nghị cho nền tảng Android",
               "phát triển ứng dụng Android thuần", "viết ứng dụng chạy trực tiếp trên Android",
               "có cú pháp ngắn gọn và an toàn với giá trị rỗng", "giúp viết mã gọn hơn Java và hạn chế lỗi tham chiếu rỗng"),
    "Swift": ("ngôn ngữ lập trình của Apple", "ngôn ngữ do Apple phát triển cho các thiết bị của hãng",
              "xây dựng ứng dụng chạy trên iPhone", "phát triển phần mềm cho điện thoại iPhone",
              "có tốc độ cao và kiểm tra kiểu chặt chẽ", "thực thi nhanh cùng hệ thống kiểu dữ liệu nghiêm ngặt"),
    "Firebase": ("nền tảng dịch vụ đám mây của Google", "bộ dịch vụ backend trên đám mây do Google cung cấp",
                 "lưu trữ dữ liệu thời gian thực và gửi thông báo đẩy", "đồng bộ dữ liệu tức thời và phát thông báo tới thiết bị",
                 "không cần tự vận hành máy chủ", "giúp nhóm phát triển khỏi phải quản trị máy chủ riêng"),
    "TensorFlow": ("thư viện học máy mã nguồn mở của Google", "bộ công cụ học sâu do Google phát hành",
                   "huấn luyện và triển khai mạng nơ-ron", "xây dựng, đào tạo và đưa mô hình nơ-ron vào sử dụng",
                   "hỗ trợ tốt việc triển khai trên thiết bị di động", "dễ chuyển mô hình sang chạy trên điện thoại"),
    "PyTorch": ("thư viện học sâu linh hoạt", "bộ khung học sâu có đồ thị tính toán động",
                "thử nghiệm và huấn luyện mô hình nơ-ron", "nghiên cứu và đào tạo các kiến trúc mạng nơ-ron",
                "có cú pháp gần với Python và dễ gỡ lỗi", "cho phép viết mã tự nhiên như Python thông thường và thuận tiện khi tìm lỗi"),
    "YOLOv8": ("mô hình phát hiện đối tượng một giai đoạn", "kiến trúc nhận diện vật thể chỉ qua một lần suy luận",
               "định vị và phân loại đối tượng trong ảnh", "xác định vị trí cùng nhãn của vật thể trên khung hình",
               "có tốc độ suy luận cao, phù hợp thời gian thực", "xử lý đủ nhanh để chạy trực tiếp trên luồng camera"),
    "OpenCV": ("thư viện thị giác máy tính mã nguồn mở", "bộ công cụ xử lý ảnh và video miễn phí",
               "tiền xử lý ảnh và trích xuất đặc trưng", "làm sạch hình ảnh và rút ra các đặc điểm quan trọng",
               "có hàng nghìn thuật toán được tối ưu sẵn", "cung cấp số lượng lớn hàm xử lý ảnh đã tối ưu"),
    "scikit-learn": ("thư viện học máy cho Python", "gói công cụ máy học viết bằng Python",
                     "xây dựng mô hình phân loại, hồi quy và phân cụm", "huấn luyện các thuật toán phân lớp, dự báo và gom nhóm",
                     "có giao diện thống nhất và tài liệu đầy đủ", "có cách gọi hàm nhất quán cùng hướng dẫn chi tiết"),
    "PhoBERT": ("mô hình ngôn ngữ tiền huấn luyện cho tiếng Việt", "mô hình biểu diễn văn bản tiếng Việt được huấn luyện trước",
                "biểu diễn ngữ nghĩa câu tiếng Việt", "mã hóa ý nghĩa của câu văn tiếng Việt thành vector",
                "cho kết quả tốt trên nhiều bài toán xử lý tiếng Việt", "đạt độ chính xác cao ở nhiều tác vụ ngôn ngữ tiếng Việt"),
    "ESP32": ("vi điều khiển tích hợp Wi-Fi và Bluetooth", "chip vi xử lý có sẵn kết nối không dây",
              "đọc cảm biến và gửi dữ liệu lên máy chủ", "thu thập số liệu cảm biến rồi truyền lên hệ thống trung tâm",
              "có giá thành thấp và tiêu thụ ít điện năng", "rẻ và tiết kiệm năng lượng"),
    "Arduino": ("nền tảng phần cứng mã nguồn mở", "bo mạch lập trình phổ biến trong giới kỹ thuật",
                "điều khiển cảm biến và cơ cấu chấp hành", "vận hành các cảm biến cùng rơ-le, động cơ",
                "có cộng đồng lớn và nhiều thư viện mẫu", "có nhiều ví dụ sẵn cùng cộng đồng hỗ trợ đông đảo"),
    "Raspberry Pi": ("máy tính nhúng cỡ nhỏ", "bo mạch máy tính đơn kích thước bằng thẻ tín dụng",
                     "làm cổng trung gian xử lý dữ liệu tại chỗ", "đóng vai trò gateway tổng hợp dữ liệu tại hiện trường",
                     "chạy được hệ điều hành Linux đầy đủ", "có thể cài hệ điều hành Linux như máy tính thông thường"),
    "MQTT": ("giao thức truyền thông điệp nhẹ", "chuẩn trao đổi tin nhắn gọn nhẹ theo cơ chế xuất bản và đăng ký",
             "truyền dữ liệu giữa thiết bị và máy chủ", "chuyển số liệu từ các nút cảm biến tới máy chủ trung tâm",
             "tốn ít băng thông, phù hợp mạng không ổn định", "tiết kiệm đường truyền và chịu được kết nối chập chờn"),
    "Node-RED": ("công cụ lập trình luồng trực quan", "môi trường ghép nối luồng xử lý bằng kéo thả",
                 "kết nối thiết bị với các dịch vụ", "liên kết phần cứng với dịch vụ trực tuyến",
                 "giúp xây dựng nhanh luồng xử lý mà ít phải viết mã", "cho phép dựng quy trình xử lý nhanh chóng với lượng mã tối thiểu"),
    "Power BI": ("công cụ phân tích nghiệp vụ của Microsoft", "phần mềm trực quan hóa số liệu do Microsoft phát triển",
                 "tạo báo cáo và bảng điều khiển tương tác", "dựng biểu đồ và dashboard có thể lọc trực tiếp",
                 "kết nối được với nhiều nguồn dữ liệu", "lấy số liệu từ đa dạng nguồn khác nhau"),
    "Apache Spark": ("nền tảng xử lý dữ liệu phân tán", "bộ máy tính toán song song cho dữ liệu lớn",
                     "xử lý khối lượng dữ liệu lớn trong bộ nhớ", "tính toán trên tập dữ liệu khổng lồ ngay trong RAM",
                     "nhanh hơn nhiều so với xử lý trên đĩa", "cho tốc độ vượt trội so với các phương pháp dựa vào ổ đĩa"),
    "Pandas": ("thư viện thao tác dữ liệu dạng bảng cho Python", "gói công cụ Python xử lý bảng số liệu",
               "làm sạch, biến đổi và tổng hợp dữ liệu", "chuẩn hóa, chuyển dạng và gom nhóm số liệu",
               "có cú pháp ngắn gọn cho các phép lọc và nhóm", "cho phép lọc, gộp dữ liệu chỉ với vài dòng lệnh"),
    "Apache Airflow": ("nền tảng điều phối luồng công việc", "công cụ lập lịch và quản lý tác vụ dữ liệu",
                       "lập lịch các bước trích xuất, biến đổi và nạp dữ liệu", "tự động chạy quy trình ETL theo thời gian định trước",
                       "theo dõi được trạng thái từng tác vụ", "hiển thị rõ tình trạng thực thi của mỗi bước"),
    "Metabase": ("công cụ báo cáo mã nguồn mở", "phần mềm dựng báo cáo miễn phí",
                 "truy vấn và trực quan hóa dữ liệu không cần viết SQL", "hỏi đáp dữ liệu và vẽ biểu đồ mà không phải lập trình",
                 "dễ cài đặt và thân thiện với người dùng nghiệp vụ", "triển khai nhanh, phù hợp cả người không chuyên kỹ thuật"),
    "Snort": ("hệ thống phát hiện xâm nhập mã nguồn mở", "phần mềm IDS miễn phí được dùng rộng rãi",
              "phân tích lưu lượng mạng theo tập luật", "kiểm tra gói tin dựa trên các luật nhận diện",
              "có cộng đồng cập nhật luật thường xuyên", "có bộ luật được cộng đồng bổ sung liên tục"),
    "Suricata": ("công cụ phát hiện và ngăn chặn xâm nhập", "phần mềm IDS và IPS hiệu năng cao",
                 "kiểm tra gói tin đa luồng", "phân tích lưu lượng song song trên nhiều nhân xử lý",
                 "tương thích với bộ luật của Snort", "dùng lại được các luật viết cho Snort"),
    "Wazuh": ("nền tảng giám sát an ninh mã nguồn mở", "giải pháp SIEM miễn phí",
              "thu thập và phân tích nhật ký từ các máy trạm", "tập trung log từ nhiều máy để phát hiện bất thường",
              "có tác tử cài được trên nhiều hệ điều hành", "hỗ trợ agent cho Windows, Linux và macOS"),
    "OpenVAS": ("bộ công cụ quét lỗ hổng mã nguồn mở", "phần mềm dò điểm yếu bảo mật miễn phí",
                "phát hiện lỗ hổng trên máy chủ và dịch vụ", "tìm các điểm yếu tồn tại ở máy chủ cùng dịch vụ mạng",
                "có cơ sở dữ liệu lỗ hổng cập nhật hằng ngày", "có kho mẫu kiểm tra được làm mới mỗi ngày"),
    "Keycloak": ("máy chủ quản lý định danh mã nguồn mở", "giải pháp xác thực tập trung miễn phí",
                 "cung cấp đăng nhập một lần và phân quyền", "cho phép đăng nhập một lần và kiểm soát quyền truy cập",
                 "hỗ trợ chuẩn OAuth2 và OpenID Connect", "tương thích các giao thức OAuth2, OpenID Connect"),
    "OpenSSL": ("thư viện mật mã mã nguồn mở", "bộ công cụ mã hóa miễn phí được dùng rộng rãi",
                "tạo khóa, chứng thư và mã hóa dữ liệu", "sinh cặp khóa, cấp chứng chỉ số và bảo vệ dữ liệu bằng mật mã",
                "hỗ trợ đầy đủ các thuật toán mật mã phổ biến", "có sẵn hầu hết giải thuật mã hóa thông dụng"),
    "pfSense": ("hệ điều hành tường lửa mã nguồn mở", "nền tảng firewall miễn phí dựa trên FreeBSD",
                "lọc lưu lượng và thiết lập mạng riêng ảo", "kiểm soát gói tin ra vào và dựng kênh VPN",
                "được quản trị hoàn toàn qua giao diện web", "cấu hình được mọi chức năng bằng trình duyệt"),
    "Odoo": ("bộ phần mềm ERP mã nguồn mở", "hệ thống hoạch định nguồn lực doanh nghiệp miễn phí",
             "quản lý bán hàng, kho và kế toán trên một nền tảng", "tích hợp các nghiệp vụ kinh doanh vào một hệ thống",
             "có nhiều phân hệ có thể cài thêm", "mở rộng linh hoạt bằng các mô-đun bổ sung"),
    "ERPNext": ("hệ thống ERP mã nguồn mở viết bằng Python", "giải pháp quản trị doanh nghiệp miễn phí dựa trên Python",
                "quản lý toàn diện hoạt động doanh nghiệp vừa và nhỏ", "hỗ trợ điều hành các mảng nghiệp vụ của doanh nghiệp nhỏ",
                "có giao diện web thân thiện và dễ tùy biến", "có giao diện trực quan, cho phép tùy chỉnh biểu mẫu"),
    "SQL Server": ("hệ quản trị cơ sở dữ liệu quan hệ của Microsoft", "phần mềm quản lý CSDL quan hệ do Microsoft phát triển",
                   "lưu trữ và truy vấn dữ liệu nghiệp vụ", "ghi nhận và khai thác số liệu giao dịch",
                   "hỗ trợ thủ tục lưu trữ và sao lưu tự động", "có stored procedure cùng cơ chế sao lưu định kỳ"),
    "Moodle": ("hệ thống quản lý học tập mã nguồn mở", "nền tảng LMS miễn phí được nhiều trường sử dụng",
               "tổ chức khóa học và bài kiểm tra trực tuyến", "vận hành lớp học cùng các bài thi qua mạng",
               "có kho plugin phong phú", "mở rộng được nhờ nhiều plugin"),
    "WebRTC": ("chuẩn giao tiếp thời gian thực trên trình duyệt", "công nghệ truyền âm thanh và hình ảnh trực tiếp giữa các trình duyệt",
               "truyền video và âm thanh trực tiếp", "phát hình ảnh cùng tiếng nói theo thời gian thực",
               "không cần cài thêm phần mềm phía người dùng", "giúp người dùng không phải cài đặt ứng dụng bổ sung"),
}

# ---------------------------------------------------------------------------
# Mẫu câu theo mục: (câu gốc, câu anh em diễn đạt lại). Ô: {dt} đối tượng, {sp} sản phẩm,
# {dv} đơn vị, {tn}/{tn2} tác nhân, {cn}/{cn2} chức năng, {dl}/{dl2} dữ liệu, {cg} công nghệ,
# {cgl}/{cgm}/{cgu} dữ kiện công nghệ, {lv} lĩnh vực, {n1}/{n2}/{n3}/{pt}/{gs}/{diem} số liệu.
# ---------------------------------------------------------------------------
MAU_CAU: dict[str, list[tuple[str, str]]] = {
    "mo_dau": [
        ("Hiện nay, việc {dt} tại {dv} vẫn chủ yếu dựa vào sổ sách và bảng tính do {tn} tự cập nhật.",
         "Tại {dv}, {tn} hiện vẫn phải tự ghi chép trên giấy tờ và bảng tính mỗi khi thực hiện {dt}."),
        ("Cách làm thủ công khiến {tn} mất nhiều thời gian để {cn} và dễ nhầm lẫn khi đối chiếu {dl}.",
         "Do làm bằng tay nên mỗi lần {cn}, {tn} tốn khá nhiều công sức và thường sai sót lúc so khớp {dl}."),
        ("Bên cạnh đó, {tn2} khó theo dõi thông tin về {dl} một cách kịp thời nếu không có công cụ hỗ trợ.",
         "Ngoài ra, nếu thiếu phần mềm trợ giúp thì {tn2} rất khó nắm bắt kịp thời tình hình {dl}."),
        ("Xuất phát từ thực tế đó, em lựa chọn đề tài xây dựng {sp} {dt} cho {dv}.",
         "Từ những hạn chế nêu trên, đồ án đặt ra nhiệm vụ phát triển {sp} phục vụ {dt} tại {dv}."),
        ("Mục tiêu của đồ án là giúp {tn} {cn} nhanh hơn và giúp {tn2} {cn2} ngay trên {sp}.",
         "Đồ án hướng tới việc để {tn2} có thể {cn2} trực tiếp qua {sp}, đồng thời rút ngắn thời gian {tn} {cn}."),
        ("Phạm vi của đề tài giới hạn ở các nghiệp vụ {cn}, {cn2} và quản lý {dl} tại {dv}.",
         "Đề tài chỉ tập trung vào quản lý {dl} cùng hai nghiệp vụ {cn2} và {cn} trong phạm vi {dv}."),
        ("Để thực hiện đề tài, em khảo sát quy trình {dt} thực tế và phỏng vấn {tn} về các khó khăn thường gặp.",
         "Phương pháp thực hiện gồm tìm hiểu quy trình {dt} đang áp dụng và trao đổi trực tiếp với {tn} để nắm rõ vướng mắc."),
        ("Kết quả khảo sát cho thấy {tn2} mong muốn được {cn2} mọi lúc mà không phải đến trực tiếp {dv}.",
         "Qua khảo sát, phần lớn {tn2} đều muốn có thể {cn2} bất cứ khi nào thay vì phải tới {dv}."),
        ("Đối tượng nghiên cứu của đồ án là quy trình {dt} cùng dữ liệu {dl} và {dl2} phát sinh hằng ngày.",
         "Đồ án nghiên cứu quy trình {dt} và các loại dữ liệu phát sinh hằng ngày như {dl2}, {dl}."),
        ("Về mặt thực tiễn, {sp} giúp {dv} chuẩn hóa dữ liệu {dl} và giảm phụ thuộc vào giấy tờ.",
         "Xét về ý nghĩa thực tiễn, nhờ có {sp} mà {dv} thống nhất được cách lưu {dl} và bớt dùng giấy tờ."),
        ("Về mặt khoa học, đồ án vận dụng kiến thức {lv} vào bài toán {dt}, cụ thể là tự động hóa khâu {cn}.",
         "Ý nghĩa khoa học của đồ án nằm ở việc áp dụng hiểu biết về {lv} cho bài toán {dt}, trọng tâm là {cn}."),
        ("Sản phẩm dự kiến là {sp} cho phép {tn} {cn} và theo dõi {dl2} trên một giao diện thống nhất.",
         "Kết quả mong đợi là một {sp} mà ở đó {tn} vừa {cn} vừa quan sát được {dl2} trên cùng giao diện."),
        ("Nhu cầu {cn} của {tn2} tại {dv} tăng nhanh trong những năm gần đây, trong khi số lượng {tn} không thay đổi.",
         "Trong vài năm trở lại đây, {tn2} ở {dv} ngày càng cần {cn}, nhưng đội ngũ {tn} vẫn giữ nguyên."),
        ("Nhiều đơn vị tương tự {dv} đã bắt đầu dùng {sp} để {cn2} và bước đầu đạt hiệu quả tích cực.",
         "Một số cơ sở có quy mô giống {dv} đã triển khai {sp} nhằm {cn2} và thu được kết quả khả quan."),
        ("Trong bối cảnh chuyển đổi số, {dv} đặt yêu cầu tin học hóa khâu {cn} và lưu trữ {dl2} tập trung.",
         "Chuyển đổi số khiến {dv} cần đưa việc {cn} lên máy tính và gom {dl2} về một nơi."),
        ("Đề tài hướng tới hai nhóm người dùng chính của {sp} là {tn} và {tn2} với nhu cầu khác nhau.",
         "{tn} và {tn2} là hai nhóm đối tượng chính mà {sp} phục vụ, mỗi nhóm có yêu cầu riêng."),
    ],
    "ly_thuyet": [
        ("Bài toán {dt} thuộc nhóm ứng dụng {lv}, trong đó dữ liệu {dl} là đối tượng xử lý trung tâm.",
         "Trong lĩnh vực {lv}, {dt} là một bài toán điển hình lấy {dl} làm dữ liệu xử lý chính."),
        ("Mô hình khách chủ cho phép {tn} gửi yêu cầu {cn} tới máy chủ và nhận kết quả qua mạng.",
         "Theo kiến trúc client-server, mỗi lần {tn} muốn {cn} thì phía máy khách gửi yêu cầu lên server rồi chờ phản hồi."),
        ("Cơ sở dữ liệu quan hệ được dùng để lưu {dl}, {dl2} và mối liên kết giữa chúng trong {sp}.",
         "Các bảng quan hệ trong cơ sở dữ liệu của {sp} lưu giữ {dl2}, {dl} cùng những khóa ngoại nối chúng với nhau."),
        ("Ngôn ngữ mô hình hóa UML hỗ trợ mô tả tác nhân {tn}, {tn2} và các ca sử dụng của {sp}.",
         "Với UML, người phân tích có thể biểu diễn các ca sử dụng của {sp} cùng những tác nhân như {tn2} và {tn}."),
        ("Giao diện lập trình ứng dụng dạng REST giúp {sp} tách phần hiển thị khỏi phần xử lý {cn}.",
         "Nhờ API theo phong cách REST, nghiệp vụ {cn} trong {sp} được xử lý độc lập với tầng giao diện."),
        ("Cơ chế xác thực bằng mã thông báo bảo đảm chỉ {tn} đã đăng nhập mới được {cn}.",
         "Chức năng {cn} chỉ mở cho {tn} sau khi đăng nhập thành công, dựa trên cơ chế token."),
        ("Các nghiên cứu về {dt} thường nhấn mạnh vai trò của việc chuẩn hóa {dl} trước khi xử lý.",
         "Nhiều công trình liên quan tới {dt} đều cho rằng {dl} cần được chuẩn hóa trước tiên."),
        ("Phân quyền theo vai trò tách biệt thao tác của {tn} với thao tác của {tn2} trong {sp}.",
         "Trong {sp}, cơ chế phân quyền dựa trên vai trò giúp {tn2} và {tn} chỉ thấy những chức năng của mình."),
        ("Một số sản phẩm hiện có đã hỗ trợ {cn} nhưng chưa phù hợp với quy mô của {dv}.",
         "Những phần mềm đang có trên thị trường tuy cho phép {cn} song lại không vừa với quy mô {dv}."),
        ("Công nghệ cho {sp} {dt} được chọn dựa trên chi phí, khả năng mở rộng và mức độ quen thuộc với {tn}.",
         "Khi chọn công nghệ cho {sp}, em cân nhắc giá thành, khả năng phát triển thêm và sự thân thuộc của {tn} với bài toán {dt}."),
        ("Dữ liệu {dl2} cần được sao lưu định kỳ để {tn} có thể khôi phục khi xảy ra sự cố.",
         "Để {tn} phục hồi được thông tin lúc gặp sự cố, {dl2} phải được sao lưu theo chu kỳ."),
        ("Trải nghiệm người dùng tốt giúp {tn2} làm quen với thao tác {cn2} chỉ sau vài lần sử dụng.",
         "Khi giao diện được thiết kế hợp lý, {tn2} chỉ cần dùng thử vài lần là thành thạo việc {cn2}."),
        ("Kiểm thử phần mềm bảo đảm chức năng {cn} hoạt động đúng với dữ liệu {dl} thực tế.",
         "Nhờ kiểm thử, có thể khẳng định {cn} chạy chính xác trên những bộ {dl} lấy từ thực tế."),
        ("Mô hình dữ liệu cho {dt} cần phản ánh đúng mối quan hệ giữa {tn}, {dl} và {dl2}.",
         "Khi mô hình hóa dữ liệu của bài toán {dt}, phải thể hiện chính xác liên hệ giữa {dl2}, {dl} với {tn}."),
    ],
    "cong_nghe": [
        ("{cg} là {cgl}, được lựa chọn để {cgm} cho {sp} {dt}.",
         "Để {cgm} trong {sp} phục vụ {dt}, đồ án sử dụng {cg}, vốn là {cgl}."),
        ("Ưu điểm nổi bật của {cg} là {cgu}, điều này phù hợp với yêu cầu {cn} của {dv}.",
         "Công cụ {cg} được đánh giá cao vì {cgu}, đáp ứng tốt nhu cầu {cn} tại {dv}."),
        ("Trong đồ án, {cg} đảm nhận việc {cgm} phục vụ chức năng {cn}.",
         "Chức năng {cn} dựa vào {cg} để {cgm}."),
        ("So với các lựa chọn khác, {cg} có lợi thế là {cgu} khi áp dụng cho bài toán {dt}.",
         "Khi giải quyết bài toán {dt}, {cg} tỏ ra vượt trội vì {cgu}."),
    ],
    "phan_tich": [
        ("Tác nhân {tn} có nhiệm vụ {cn} và {cn2} trong {sp}.",
         "Trong {sp}, {tn} đảm nhận hai công việc chính là {cn2} và {cn}."),
        ("Tác nhân {tn2} sử dụng {sp} chủ yếu để {cn} và tra cứu {dl}.",
         "Mục đích chính khi {tn2} dùng {sp} là tra cứu {dl} và {cn}."),
        ("Ca sử dụng {cn} bắt đầu khi {tn} chọn mục {dl} trên màn hình chính của {sp}.",
         "Khi {tn} bấm vào mục {dl} ở trang chính của {sp}, ca sử dụng {cn} được khởi động."),
        ("Hệ thống kiểm tra tính hợp lệ của {dl} trước khi lưu và thông báo lỗi cho {tn} nếu thiếu thông tin.",
         "Nếu {dl} còn thiếu trường bắt buộc, {sp} báo lỗi để {tn} bổ sung trước khi ghi vào cơ sở dữ liệu."),
        ("Mỗi {dl} gắn với đúng một {dl2}, còn một {dl2} có thể liên quan tới nhiều {dl}.",
         "Quan hệ giữa {dl2} và {dl} là một nhiều, tức mỗi {dl} chỉ thuộc về một {dl2} duy nhất."),
        ("Sơ đồ hoạt động của nghiệp vụ {cn} gồm các bước nhập thông tin, kiểm tra và cập nhật {dl}.",
         "Nghiệp vụ {cn} được mô tả bằng sơ đồ hoạt động với ba bước nhập liệu, xác minh rồi ghi nhận {dl}."),
        ("Yêu cầu phi chức năng đặt ra là {sp} phản hồi thao tác {cn2} trong vòng hai giây.",
         "Về hiệu năng, thao tác {cn2} trên {sp} phải có kết quả trả về không quá hai giây."),
        ("Bảng {dl} lưu mã định danh, thời điểm tạo và người tạo là {tn}.",
         "Trong cơ sở dữ liệu, {dl} được lưu cùng mã riêng, thời gian khởi tạo và thông tin {tn} đã lập."),
        ("Khi {tn2} thực hiện {cn2}, hệ thống tự động gửi thông báo tới {tn} để xử lý tiếp.",
         "Mỗi lần {cn2} được {tn2} thực hiện xong, {tn} sẽ nhận được thông báo tự động để làm bước kế tiếp."),
        ("Luồng ngoại lệ xảy ra khi {dl} đã bị thay đổi bởi {tn} khác trong lúc đang {cn}.",
         "Trường hợp bất thường là trong lúc {cn}, {dl} lại bị một {tn} khác chỉnh sửa trước."),
        ("Kiến trúc {sp} gồm tầng giao diện cho {tn2}, tầng xử lý nghiệp vụ {cn} và tầng dữ liệu {dl2}.",
         "{sp} được tổ chức ba tầng gồm phần hiển thị phục vụ {tn2}, phần nghiệp vụ {cn} và phần lưu trữ {dl2}."),
        ("Màn hình quản lý {dl} hiển thị danh sách có phân trang, bộ lọc và nút {cn}.",
         "Danh sách {dl} được trình bày theo trang, kèm bộ lọc và nút bấm để {cn}."),
        ("Quyền {cn} chỉ được cấp cho {tn}, còn {tn2} chỉ có quyền xem {dl2}.",
         "{tn2} chỉ được phép xem {dl2}, trong khi thao tác {cn} dành riêng cho {tn}."),
        ("Thiết kế cơ sở dữ liệu cho bài toán {dt} gồm các bảng chính {dl}, {dl2} và bảng người dùng.",
         "Để phục vụ {dt}, cơ sở dữ liệu có bảng người dùng cùng các bảng cốt lõi là {dl2} và {dl}."),
        ("Biểu đồ tuần tự của ca {cn2} thể hiện trao đổi giữa {tn2}, giao diện và máy chủ.",
         "Trao đổi qua lại giữa {tn2} với giao diện và server trong ca {cn2} được thể hiện bằng biểu đồ tuần tự."),
        ("Dữ liệu {dl2} được tổng hợp theo ngày để {tn} nắm được tình hình {dt} tại {dv}.",
         "Nhờ tổng hợp {dl2} hằng ngày, {tn} theo dõi được diễn biến {dt} ở {dv}."),
        ("Trạng thái của {dl} thay đổi từ mới tạo sang đã xử lý sau khi {tn} {cn}.",
         "Sau bước {cn} của {tn}, {dl} chuyển trạng thái từ khởi tạo sang hoàn tất."),
        ("Yêu cầu bảo mật gồm mã hóa mật khẩu của {tn2} và ghi nhật ký mọi lần {cn}.",
         "Về an toàn, mật khẩu {tn2} phải được băm và từng thao tác {cn} đều cần lưu vết."),
        ("Yêu cầu chức năng quan trọng nhất đối với {tn2} là có thể {cn2} mà không cần hướng dẫn.",
         "Với {tn2}, điều cần thiết nhất là tự mình {cn2} được ngay mà không phải nhờ trợ giúp."),
        ("Thông tin {dl2} được liên kết với {dl} thông qua khóa ngoại để bảo đảm toàn vẹn dữ liệu.",
         "Để giữ toàn vẹn, mỗi bản ghi {dl2} tham chiếu tới {dl} bằng một khóa ngoại."),
        ("Khi {tn} hủy thao tác {cn}, các thay đổi trên {dl} được hoàn tác và ghi lại lý do.",
         "Nếu {tn} bỏ ngang việc {cn}, {dl} trở về trạng thái cũ kèm ghi chú nguyên nhân."),
        ("Chức năng tìm kiếm cho phép {tn2} lọc {dl} theo nhiều tiêu chí như thời gian và trạng thái.",
         "{tn2} có thể tìm {dl} bằng cách kết hợp các điều kiện về trạng thái, thời điểm."),
        ("Mỗi tác nhân chỉ nhìn thấy các mục phù hợp với vai trò, ví dụ {tn} thấy mục {cn} còn {tn2} thấy mục {cn2}.",
         "Menu được hiển thị theo vai trò, nên {tn2} có mục {cn2} trong khi {tn} có mục {cn}."),
        ("Báo cáo tổng hợp về {dl2} được xuất ra tệp bảng tính để {tn} gửi lên cấp trên của {dv}.",
         "{tn} có thể tải báo cáo {dl2} dưới dạng bảng tính rồi chuyển cho lãnh đạo {dv}."),
        ("Quy trình {dt} hiện tại gồm nhiều bước lặp lại mà {tn} phải ghi chép bằng tay vào sổ {dl}.",
         "Hiện nay, trong quy trình {dt}, {tn} vẫn chép tay nhiều lần vào sổ {dl}."),
    ],
    "cai_dat": [
        ("{sp} được cài đặt bằng {cg} cho phần xử lý nghiệp vụ {cn}.",
         "Phần nghiệp vụ {cn} của {sp} được lập trình với {cg}."),
        ("Chức năng {cn} được kiểm thử với {n3} bộ dữ liệu {dl} và đều cho kết quả đúng.",
         "Toàn bộ {n3} bộ {dl} dùng để kiểm thử {cn} đều trả về kết quả chính xác."),
        ("Giao diện {cn2} dành cho {tn2} được thiết kế đáp ứng trên cả máy tính và điện thoại.",
         "Màn hình {cn2} của {tn2} tự co giãn để hiển thị tốt trên điện thoại lẫn máy tính."),
        ("Sau khi triển khai thử tại {dv}, thời gian {cn} của {tn} giảm khoảng {pt} phần trăm.",
         "Kết quả chạy thử ở {dv} cho thấy {tn} rút ngắn được chừng {pt} phần trăm thời gian {cn}."),
        ("Dữ liệu mẫu gồm {n1} bản ghi {dl} được nhập để kiểm tra hiệu năng của {sp}.",
         "Để đánh giá hiệu năng {sp}, em đã nạp {n1} bản ghi {dl} làm dữ liệu thử."),
        ("Mã nguồn phân hệ {cn} của {sp} được đóng gói và triển khai trên máy chủ Linux của {dv}.",
         "{dv} cung cấp máy chủ Linux để chạy bản đóng gói phân hệ {cn} viết bằng {cg}."),
        ("Kiểm thử chấp nhận được thực hiện cùng {tn} với kịch bản {cn} và {cn2}.",
         "Cùng với {tn}, em chạy kiểm thử chấp nhận theo hai kịch bản {cn2} và {cn}."),
        ("Khi {tn2} {cn2}, {sp} phản hồi trung bình trong {gs} giây.",
         "Thời gian đáp ứng trung bình cho thao tác {cn2} của {tn2} đo được là {gs} giây."),
        ("Lỗi phát sinh khi {tn} nhập {dl} trùng mã đã được xử lý bằng ràng buộc duy nhất trong cơ sở dữ liệu.",
         "Tình trạng {tn} lỡ tạo {dl} trùng mã được khắc phục nhờ khai báo ràng buộc unique ở tầng dữ liệu."),
        ("Màn hình thống kê hiển thị biểu đồ {dl2} theo tháng giúp {tn} đánh giá hiệu quả {dt}.",
         "Nhờ biểu đồ {dl2} theo từng tháng trên trang thống kê, {tn} dễ dàng nhận xét hiệu quả {dt}."),
        ("Phần giao diện sử dụng {cg} kết hợp bộ thành phần có sẵn để hiển thị {dl}.",
         "Để trình bày {dl}, giao diện được dựng bằng {cg} cùng các thành phần dựng sẵn."),
        ("{tn2} tham gia dùng thử chức năng {cn2} đánh giá {sp} dễ sử dụng với điểm trung bình {diem} trên 5.",
         "Sau khi dùng thử chức năng {cn2}, {tn2} chấm {sp} trung bình {diem} trên thang 5 về độ dễ sử dụng."),
        ("Mã nguồn được quản lý bằng Git và chia thành các mô-đun {cn}, {cn2} và quản trị.",
         "Kho Git của dự án tách thành từng mô-đun riêng cho quản trị, {cn2} và {cn}."),
        ("Quy trình {cn} sau khi cài đặt chỉ còn ba bước thay vì năm bước như trước tại {dv}.",
         "So với cách làm cũ ở {dv}, thao tác {cn} giờ chỉ gồm ba bước thay cho năm bước."),
        ("Các trường hợp nhập sai định dạng {dl2} đều được {sp} cảnh báo rõ ràng cho {tn}.",
         "Mỗi khi {tn} điền {dl2} không đúng định dạng, {sp} đều hiện thông báo lỗi dễ hiểu."),
        ("Hệ thống ghi nhận {n1} lượt {cn2} trong hai tuần chạy thử tại {dv}.",
         "Trong hai tuần vận hành thử ở {dv}, có {n1} lượt {cn2} được ghi lại."),
        ("Chức năng sao lưu tự động sao chép dữ liệu {dl} sang máy chủ dự phòng của {dv} vào cuối mỗi ngày.",
         "Cuối ngày, {dl} được tự động nhân bản lên máy chủ dự phòng đặt tại {dv}."),
        ("Kết quả kiểm thử cho thấy {sp} đáp ứng các yêu cầu chính về {cn} và {cn2}.",
         "Qua kiểm thử, {sp} đã thỏa mãn các yêu cầu cốt lõi liên quan tới {cn2} và {cn}."),
        ("Cơ sở dữ liệu được khởi tạo bằng tệp di trú, gồm các bảng {dl}, {dl2} và dữ liệu mẫu của {dv}.",
         "Các bảng {dl2}, {dl} cùng dữ liệu mẫu lấy từ {dv} được tạo tự động qua tệp migration."),
        ("Để bảo vệ {dl}, mật khẩu của {tn} được băm trước khi lưu và phiên làm việc hết hạn sau {n2} phút.",
         "Phiên đăng nhập của {tn} tự hết hạn sau {n2} phút, còn mật khẩu luôn được băm để giữ an toàn cho {dl}."),
        ("Chức năng {cn2} được tối ưu bằng chỉ mục trên bảng {dl2} nên thời gian truy vấn giảm rõ rệt.",
         "Nhờ tạo index cho bảng {dl2}, truy vấn phục vụ {cn2} chạy nhanh hơn hẳn."),
        ("Trong quá trình kiểm thử, {n3} lỗi giao diện ở màn hình {cn} đã được phát hiện và sửa.",
         "Kiểm thử phát hiện {n3} lỗi hiển thị trên màn hình {cn} và tất cả đã được khắc phục."),
        ("{tn} được hướng dẫn sử dụng {sp} trong một buổi tập huấn ngắn tại {dv}.",
         "Tại {dv}, em tổ chức một buổi tập huấn ngắn để {tn} làm quen với {sp}."),
        ("Nhật ký hệ thống ghi lại mọi thao tác {cn} của {tn} để phục vụ tra soát khi cần.",
         "Mỗi lần {tn} {cn} đều được lưu vết trong nhật ký để có thể kiểm tra lại về sau."),
    ],
    "ket_luan": [
        ("Đồ án đã xây dựng được {sp} {dt} đáp ứng nhu cầu cơ bản của {dv}.",
         "Kết quả của đồ án là một {sp} phục vụ {dt}, đáp ứng những nhu cầu thiết yếu tại {dv}."),
        ("{sp} cho phép {tn} {cn} thuận tiện và chính xác hơn so với cách làm cũ.",
         "So với trước đây, {tn} giờ có thể {cn} dễ dàng và ít sai sót hơn nhờ {sp}."),
        ("Tuy nhiên, chức năng {cn2} mới dừng ở mức cơ bản và chưa được kiểm chứng với số lượng lớn {tn2}.",
         "Dù vậy, phần {cn2} vẫn còn đơn giản và chưa được thử với lượng {tn2} lớn."),
        ("Trong thời gian tới, em dự kiến bổ sung khả năng phân tích {dl2} để hỗ trợ {tn} ra quyết định.",
         "Hướng mở rộng tiếp theo là thêm tính năng phân tích {dl2} giúp {tn} đưa ra quyết định tốt hơn."),
        ("Quá trình thực hiện giúp em hiểu rõ hơn quy trình {dt} và cách áp dụng {cg} vào thực tế.",
         "Thông qua đồ án, em nắm vững hơn nghiệp vụ {dt} cũng như cách vận dụng {cg} vào bài toán thật."),
        ("Kết quả chạy thử chức năng {cn} tại {dv} cho thấy {sp} có thể đưa vào sử dụng sau khi hoàn thiện thêm.",
         "Sau đợt thử nghiệm {cn} ở {dv}, có thể thấy {sp} đủ điều kiện áp dụng nếu được bổ sung thêm một số phần."),
        ("Hạn chế lớn nhất của đồ án là dữ liệu {dl} thu thập tại {dv} còn ít và chưa đa dạng.",
         "Điểm yếu chính là lượng {dl} lấy từ {dv} phục vụ kiểm thử vẫn còn hạn chế về số lượng lẫn chủng loại."),
        ("Em mong muốn mở rộng {sp} để trao đổi dữ liệu {dl} với các hệ thống khác mà {dv} đang sử dụng.",
         "Một định hướng khác là liên thông {sp} với những phần mềm quản lý {dl} sẵn có tại {dv}."),
        ("Việc tự động hóa {cn} đã giảm đáng kể khối lượng công việc giấy tờ của {tn}.",
         "Nhờ {cn} được tự động hóa, {tn} bớt được phần lớn công việc sổ sách."),
        ("Ý kiến phản hồi của {tn2} là cơ sở để em tiếp tục cải tiến giao diện {cn2}.",
         "Em sẽ dựa trên góp ý của {tn2} để điều chỉnh màn hình {cn2} cho hợp lý hơn."),
        ("Các mục tiêu đặt ra ở phần mở đầu về {sp} {dt} cơ bản đã được hoàn thành.",
         "Nhìn chung, những mục tiêu liên quan tới {sp} {dt} nêu ở phần đầu báo cáo đều đã đạt được."),
        ("Nếu được triển khai rộng, {sp} có thể áp dụng cho nhiều đơn vị có quy trình {dt} tương tự {dv}.",
         "Trong trường hợp nhân rộng, {sp} hoàn toàn dùng được ở các nơi có cách {dt} giống như {dv}."),
        ("Em xin chân thành cảm ơn {tn} tại {dv} đã hỗ trợ cung cấp dữ liệu {dl} trong quá trình khảo sát.",
         "Trong lúc khảo sát, em đã nhận được sự giúp đỡ nhiệt tình của {tn} ở {dv} về dữ liệu {dl}."),
        ("Đồ án cũng đề xuất quy trình {cn2} mới giúp {tn2} tiết kiệm thời gian đi lại.",
         "Một đóng góp khác là cách {cn2} mới, nhờ đó {tn2} không phải di chuyển nhiều."),
        ("Về lâu dài, dữ liệu {dl} tích lũy trong {sp} sẽ là nguồn thông tin quý cho {dv}.",
         "Theo thời gian, lượng {dl} được lưu trong {sp} sẽ trở thành tài nguyên có giá trị với {dv}."),
    ],
}

# ---------------------------------------------------------------------------
# Khuôn mẫu chung [ASSUMED] — giống hệt nhau ở mọi tài liệu (chỉ thay tên/đề tài/năm),
# để plan 04-04 chứng minh phần khuôn mẫu không bị tính là trùng lặp.
# ---------------------------------------------------------------------------
KHUON_MAU_GHI_CHU = "[ASSUMED] khuôn mẫu chung — thay khi có mẫu chính thức"
DAU_TRANG = "Đồ án tốt nghiệp - Khoa Công nghệ thông tin"
BIA = {
    "truong": "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG",
    "khoa": "KHOA CÔNG NGHỆ THÔNG TIN",
    "loai": {"DE_CUONG": "ĐỀ CƯƠNG ĐỒ ÁN TỐT NGHIỆP", "BAO_CAO": "ĐỒ ÁN TỐT NGHIỆP"},
    "nganh": "Ngành: Công nghệ thông tin",
}
LOI_CAM_DOAN = (
    "Em xin cam đoan đồ án tốt nghiệp với đề tài “{ten_de_tai}” là kết quả nghiên cứu của riêng em "
    "dưới sự hướng dẫn của giảng viên hướng dẫn. Các số liệu, kết quả nêu trong đồ án là trung thực "
    "và chưa từng được công bố trong bất kỳ công trình nào khác. Mọi tài liệu tham khảo đều được trích "
    "dẫn đầy đủ trong danh mục tài liệu tham khảo. Nếu có sai phạm, em xin chịu hoàn toàn trách nhiệm "
    "trước Khoa và Nhà trường."
)
LOI_CAM_ON = [
    "Em xin gửi lời cảm ơn chân thành tới các thầy cô giáo Khoa Công nghệ thông tin, Trường Đại học "
    "Công nghệ Thông tin và Truyền thông đã truyền đạt những kiến thức quý báu trong suốt quá trình học tập.",
    "Em đặc biệt cảm ơn giảng viên hướng dẫn đã tận tình chỉ bảo, góp ý để em hoàn thành đồ án này. "
    "Em cũng xin cảm ơn gia đình và bạn bè đã luôn động viên, tạo điều kiện cho em trong thời gian thực hiện đề tài.",
    "Do thời gian và kiến thức còn hạn chế, đồ án không tránh khỏi thiếu sót, em rất mong nhận được "
    "ý kiến đóng góp của quý thầy cô để đồ án được hoàn thiện hơn.",
]
CHUONG = {
    "mo_dau": "MỞ ĐẦU",
    "ly_thuyet": "CHƯƠNG 1. CƠ SỞ LÝ THUYẾT",
    "phan_tich": "CHƯƠNG 2. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG",
    "cai_dat": "CHƯƠNG 3. CÀI ĐẶT VÀ THỬ NGHIỆM",
    "ket_luan": "KẾT LUẬN",
}
MUC_CON = {
    "ly_thuyet": ("1.1. Tổng quan về bài toán", "1.2. Công nghệ sử dụng"),
    "phan_tich": ("2.1. Phân tích yêu cầu", "2.2. Thiết kế hệ thống"),
    "cai_dat": ("3.1. Cài đặt chương trình", "3.2. Kiểm thử và đánh giá"),
}
HINH = {
    "phan_tich": ["Hình 2.1. Sơ đồ use case tổng quát", "Hình 2.2. Sơ đồ lớp thực thể", "Hình 2.3. Sơ đồ cơ sở dữ liệu"],
    "cai_dat": ["Hình 3.1. Giao diện đăng nhập", "Hình 3.2. Giao diện chức năng chính"],
}
# Số trang trong mục lục/danh mục hình (cố định theo độ dài tài liệu).
TRANG = {
    "DE_CUONG": {"LỜI CAM ĐOAN": "i", "LỜI CẢM ƠN": "ii", "MỞ ĐẦU": "1", "CHƯƠNG 1": "3", "CHƯƠNG 2": "5",
                 "CHƯƠNG 3": "8", "KẾT LUẬN": "11", "TÀI LIỆU THAM KHẢO": "12",
                 "Hình 2.1": "6", "Hình 2.2": "7", "Hình 2.3": "7", "Hình 3.1": "9", "Hình 3.2": "10"},
    "BAO_CAO": {"LỜI CAM ĐOAN": "i", "LỜI CẢM ƠN": "ii", "MỞ ĐẦU": "1", "CHƯƠNG 1": "5", "CHƯƠNG 2": "14",
                "CHƯƠNG 3": "32", "KẾT LUẬN": "50", "TÀI LIỆU THAM KHẢO": "53",
                "Hình 2.1": "16", "Hình 2.2": "22", "Hình 2.3": "25", "Hình 3.1": "34", "Hình 3.2": "38"},
}
TAI_LIEU_THAM_KHAO = [
    "Ian Sommerville (2016), Software Engineering, 10th edition, Pearson.",
    "Roger S. Pressman, Bruce R. Maxim (2019), Software Engineering: A Practitioner's Approach, 9th edition, McGraw-Hill.",
    "Ramez Elmasri, Shamkant B. Navathe (2016), Fundamentals of Database Systems, 7th edition, Pearson.",
    "Abraham Silberschatz, Henry F. Korth, S. Sudarshan (2019), Database System Concepts, 7th edition, McGraw-Hill.",
    "Martin Fowler (2003), UML Distilled, 3rd edition, Addison-Wesley.",
    "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides (1994), Design Patterns, Addison-Wesley.",
    "Robert C. Martin (2008), Clean Code, Prentice Hall.",
    "Len Bass, Paul Clements, Rick Kazman (2021), Software Architecture in Practice, 4th edition, Addison-Wesley.",
    "Sam Newman (2021), Building Microservices, 2nd edition, O'Reilly Media.",
    "Ian Goodfellow, Yoshua Bengio, Aaron Courville (2016), Deep Learning, MIT Press.",
    "Stuart Russell, Peter Norvig (2020), Artificial Intelligence: A Modern Approach, 4th edition, Pearson.",
    "Aurélien Géron (2022), Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow, 3rd edition, O'Reilly Media.",
    "Jiawei Han, Micheline Kamber, Jian Pei (2011), Data Mining: Concepts and Techniques, 3rd edition, Morgan Kaufmann.",
    "Ralph Kimball, Margy Ross (2013), The Data Warehouse Toolkit, 3rd edition, Wiley.",
    "Andrew S. Tanenbaum, David J. Wetherall (2011), Computer Networks, 5th edition, Pearson.",
    "James F. Kurose, Keith W. Ross (2021), Computer Networking: A Top-Down Approach, 8th edition, Pearson.",
    "William Stallings (2017), Cryptography and Network Security, 7th edition, Pearson.",
    "David Hanes và cộng sự (2017), IoT Fundamentals, Cisco Press.",
    "Jakob Nielsen (1993), Usability Engineering, Morgan Kaufmann.",
    "Donald A. Norman (2013), The Design of Everyday Things, Basic Books.",
]
