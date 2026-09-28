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
            ("dat_ve_xe", "đặt vé xe khách", "bán vé xe liên tỉnh qua mạng", "DV"),
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
            ("thu_cung", "chăm sóc thú cưng", "đặt lịch dịch vụ cho vật nuôi", "DV"),
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
            ("bien_so", "nhận dạng biển số xe", "đọc biển kiểm soát phương tiện", "DV"),
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
            ("bai_do_xe", "quản lý bãi đỗ xe thông minh", "hướng dẫn chỗ đỗ xe còn trống", "DV"),
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
        ("trường mầm non {xa}", "trường mẫu giáo {xa}"),
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
        ("bến xe khách {tinh}", "bến xe liên tỉnh {tinh}"),
        ("khu du lịch {huyen}", "điểm du lịch {huyen}"),
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
