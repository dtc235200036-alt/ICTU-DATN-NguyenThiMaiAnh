# Dịch vụ AI kiểm tra trùng lặp — `ai-service/`

Thành phần thứ ba của kiến trúc SOA (§3.3): một ứng dụng FastAPI độc lập, chỉ
Web API gọi tới, kiểm tra trùng lặp **tên đề tài** (ngữ nghĩa) và **nội dung đề
cương/báo cáo** (từng câu, ngữ nghĩa + nguyên văn) trong phạm vi kho đồ án của
Khoa CNTT (AISV-01..05).

## Ranh giới SOA

- Chỉ nhận **văn bản** (Web API đã trích xuất từ DOCX/PDF) — không bao giờ nhận file.
- Chỉ nằm trên mạng nội bộ (compose network / `127.0.0.1:8002`), **không có
  route Apache**, không publish cổng ra host.
- Mọi endpoint trừ `/health` yêu cầu header `X-API-Key` đúng; thiếu hoặc sai →
  `401 {"detail": "Thiếu hoặc sai API key nội bộ"}`. So sánh hằng thời gian
  (`hmac.compare_digest`) trong MỘT dependency cấp router; giá trị khóa không
  bao giờ được ghi log hay trả lại.
- Sở hữu schema riêng `thesis_ai` (bảng `chunk`, `embedding`,
  `index_metadata`) với lịch sử Alembic riêng; không đọc `thesis_core`.
- Không lưu chính sách: ngưỡng do Web API gửi theo từng request (D-04).

## Biến môi trường

| Biến | Mặc định | Bí mật | Ý nghĩa |
|------|----------|--------|---------|
| `APP_ENV` | `production` | | `test` bật `/docs` và cho phép profile `fake` |
| `DATABASE_URL` | — (bắt buộc) | **có** | URL SQLAlchemy của `thesis_ai` (vd. `mysql+pymysql://ai:***@mysql/thesis_ai?charset=utf8mb4`) |
| `AI_API_KEY` | — (bắt buộc, ≥ 32 ký tự) | **có** | Khóa nội bộ mà Web API gửi trong `X-API-Key` |
| `AI_MODEL_PROFILE` | `bkai` | | `bkai` \| `e5` \| `fake` (chỉ khi `APP_ENV=test`); hiệu chỉnh — `calibration/nguong-de-xuat.json` (2026-09-28) |
| `TORCH_THREADS` | `4` | | Số luồng CPU của torch |
| `MAX_TEXT_CHARS` | `2000000` | | Trần độ dài trường `text` (422 khi vượt) |
| `MAX_BODY_BYTES` | `8388608` | | Trần thân request (413 khi vượt, đếm byte thật) |
| `NGUONG_DOAN_MAC_DINH` | `67.7` | | Ngưỡng ngữ nghĩa (cosine×100) khi request không gửi; hiệu chỉnh — `calibration/nguong-de-xuat.json` (2026-09-28) |
| `NGUONG_NGUYEN_VAN_MAC_DINH` | `88.7` | | Ngưỡng nguyên văn (Jaccard×100) khi request không gửi; hiệu chỉnh — `calibration/nguong-de-xuat.json` (2026-09-28) |
| `MINHASH_SHINGLE` | `4` | | k của k-gram âm tiết cho MinHash; hiệu chỉnh — `calibration/nguong-de-xuat.json` (2026-09-28) |
| `MINHASH_NUM_PERM` | `128` | | Số hoán vị MinHash |
| `TOP_K_MAC_DINH` | `5` | | `top_k` mặc định của `/check-document` |
| `CHI_TIET_TOI_DA` | `50` | | Số đoạn trùng tối đa trả về |
| `HF_HOME` | `/models` (image) | | Cache trọng số Hugging Face |

## Chạy cục bộ

```bash
cd ai-service
uv sync                     # torch lấy từ https://download.pytorch.org/whl/cpu
uv run pytest               # 5 test, profile fake, SQLite tạm — không cần torch/mô hình
uv run python scripts/smoke_real_model.py --profile bkai   # mô hình thật + đo CPU
DATABASE_URL=sqlite:///./thesis_ai.db AI_API_KEY=$(openssl rand -hex 24) \
  sh -c 'uv run alembic upgrade head && uv run uvicorn app.main:app --host 127.0.0.1 --port 8002 --workers 1'
```

Image và smoke container (không đụng compose `ntma`):

```bash
docker build -t ntma-ai:test ai-service
bash ai-service/scripts/container_smoke.sh ntma-ai:test
python -m app.download_model --profile bkai   # làm nóng cache khi máy chủ không có Internet
```

## API (§3.3.5 + trường bổ sung)

Không gian id (`ref_id`/`id`) theo loại nguồn:

| `type`/`loai` | id là | Nội dung ingest | Được tìm bởi |
|---------------|-------|-----------------|--------------|
| `TOPIC` | `de_tai.id` | tên đề tài hiện hành | `/check-title` |
| `ARCHIVE` | `do_an_kho.id` | tên đồ án trong kho | `/check-title` |
| `DOCUMENT` | `tai_lieu_do_an.id` | văn bản đã trích xuất của đề cương/báo cáo | `/check-document` |

### `POST /ingest`

```json
{"id": 12, "type": "TOPIC" | "ARCHIVE" | "DOCUMENT", "text": "..."}
→ {"chunk_count": 1, "indexed": true}
```

Ngữ nghĩa **REPLACE** theo `(type, id)`: ingest lại thay toàn bộ chunk cũ của
nguồn đó; `text` không sinh chunk nào (vd. chuỗi rỗng) để lại nguồn không còn
chunk (xóa khỏi chỉ mục). Nội dung không đổi → không encode lại. Mỗi lần ingest
có thay đổi = đúng một lần gọi mô hình cho mọi chunk mới (NFR-11).

### `POST /check-title`

```json
{"text": "Phát triển phần mềm quản lý thư viện trường THPT", "top_k": 5, "nguong": 70.0}
→ {"matches": [{"ref_id": 1, "loai": "ARCHIVE", "ty_le": 85.16}]}
```

`ty_le` = cosine × 100 (2 chữ số); `nguong` (tùy chọn, 0–100) lọc kết quả thấp
hơn; tìm trên TOPIC + ARCHIVE, mỗi nguồn một dòng (điểm cao nhất).

### `POST /check-document`

```json
{"ref_id": 34, "text": "...", "top_k": 5,
 "nguong_doan": 80.0, "nguong_nguyen_van": 60.0, "loai_tru": [30, 31]}
→ {"ty_le_tong": 42.5,
   "do_an_trung": [{"ref_id": 10, "ty_le": 42.5}],
   "chi_tiet": [{"ref_id": 10, "doan_nguon": "...", "doan_trung": "...",
                 "vi_tri": "Câu 3–5", "ty_le": 100.0, "tin_hieu": "NGUYEN_VAN",
                 "diem_ngu_nghia": 99.1, "diem_nguyen_van": 100.0}],
   "so_doan": 120, "so_doan_loai_tru": 57}
```

- `ref_id` = tài liệu đang kiểm tra (`0` nếu chưa nằm trong kho); tập loại trừ
  = `{ref_id} ∪ loai_tru` (≤ 2000 id, vd. các phiên bản trước của cùng đề tài)
  — không bao giờ được so khớp.
- `nguong_doan`, `nguong_nguyen_van` (0–100, tùy chọn): thiếu → giá trị mặc định
  của dịch vụ; ngoài khoảng → 422.
- `ty_le_tong` = 100 × số ký tự thuộc câu bị gắn cờ / tổng ký tự các câu nội dung.
- `do_an_trung` = tỷ lệ ký tự quy cho từng tài liệu nguồn, giảm dần, tối đa `top_k`.
- `chi_tiet` = các **đoạn trùng**: chuỗi câu liên tiếp bị gắn cờ cùng một nguồn
  (tối đa 6 câu/đoạn); `doan_nguon` là câu của tài liệu đang kiểm tra,
  `doan_trung` là các câu nguồn khớp (theo thứ tự trong nguồn), `vi_tri` là số
  thứ tự câu, `ty_le` là trung bình (trọng số ký tự) của điểm kích hoạt,
  `tin_hieu` là `NGUYEN_VAN` khi ≥ nửa số ký tự bị gắn cờ do MinHash, ngược
  lại `NGU_NGHIA`; `diem_ngu_nghia`/`diem_nguyen_van` là trung bình trọng số
  điểm tốt nhất từng tín hiệu (chỉ để giải thích). Sắp xếp theo `ty_le` giảm
  dần, tối đa `CHI_TIET_TOI_DA`.
- `so_doan` = số câu nội dung; `so_doan_loai_tru` = số dòng mẫu chung đã lọc.

### `POST /reindex`

```json
{"items": [{"id": 1, "type": "ARCHIVE", "text": "..."}, ...]}   → {"indexed_count": 2}
(thân rỗng hoặc {})                                              → {"indexed_count": 5321}
```

Có `items` (≤ 500): ingest cả lô (REPLACE) với MỘT lần encode. Không có `items`:
encode (một lần) mọi chunk còn thiếu embedding cho mô hình hiện tại (vd. sau
khi đổi `AI_MODEL_PROFILE`), rồi dựng lại chỉ mục bộ nhớ; trả tổng số vector.

### `GET /health` (không cần khóa)

```json
{"status": "ok", "model_loaded": true, "index_size": 5321,
 "index_size_tieu_de": 301, "index_size_tai_lieu": 5020,
 "ten_model": "bkai-foundation-models/vietnamese-bi-encoder",
 "encode_calls": 17, "thieu_embedding": 0}
```

## Phương pháp phát hiện

1. **Chuẩn hóa** (AISV-02): NFC, bỏ NUL, gộp khoảng trắng; profile `bkai` tách
   từ bằng `underthesea.word_tokenize(format="text")`; profile `e5` thêm
   `"query: "` cho mọi đầu vào (so sánh đối xứng).
2. **Lọc phần mẫu chung** (`app/nlp/boilerplate.py`, D-03): danh sách
   **[ASSUMED]** chung cho khuôn mẫu đồ án tiếng Việt (bìa, lời cam đoan, lời
   cảm ơn, mục lục và dòng dẫn chấm, danh mục hình/bảng/từ viết tắt, tiêu đề
   chương/mục, chú thích hình/bảng, tài liệu tham khảo, phụ lục, nhận xét GV)
   **cộng** nhãn bìa "Đề tài:"/"Ngành:" (kể cả tên đề tài bị PDF bẻ dòng),
   bộ phát hiện dòng ngắn lặp ≥ 3 lần không kết thúc bằng dấu câu và số trang (header/footer mà
   trích xuất PDF `page.get_text()` phía Web API để lọt). **Thay danh sách khi
   có mẫu chính thức TL-04/TL-05.**
3. **Chia câu** (`app/nlp/chunking.py`): nối các dòng còn lại thành một dòng
   chảy (đoạn PDF bị bẻ dòng được nối lại — DOCX và PDF cho cùng câu), tách tại
   `. ! ? …` + chữ hoa/số/ngoặc mở (giữ TS., ThS., PGS., GS., Tp., v.v.), bỏ câu
   < 6 âm tiết, cắt câu > 120 âm tiết tại `; ` rồi `, `.
4. **Hai tín hiệu** cho mỗi câu, so với kho DOCUMENT (trừ tập loại trừ):
   cosine tốt nhất qua FAISS `IndexFlatIP` (chính xác, vector chuẩn hóa L2) và
   Jaccard MinHash tốt nhất trên k-gram âm tiết (k = 4, 128 hoán vị). Gắn cờ
   `NGUYEN_VAN` khi Jaccard×100 ≥ `nguong_nguyen_van` (bằng chứng mạnh hơn nên
   thắng), ngược lại `NGU_NGHIA` khi cosine×100 ≥ `nguong_doan`. Cờ
   `NGU_NGHIA` chỉ được giữ khi câu nằm trong chuỗi ≥ 2 câu liên tiếp gắn cờ
   cùng một nguồn (`MIN_RUN_NGU_NGHIA`, plan 04-04): câu tự viết theo khuôn câu
   chung của lĩnh vực hay trùng ngữ nghĩa với một câu lẻ của đồ án khác, còn
   phần diễn đạt lại đi thành đoạn liền nhau. Cờ `NGUYEN_VAN` đứng lẻ vẫn giữ.
5. Chỉ mục FAISS và ma trận MinHash nằm trong bộ nhớ, **dựng lại từ
   `thesis_ai` lúc khởi động** (không encode lại; `index_metadata` phát hiện
   lệch); embedding chỉ tính khi ingest.

## Ngưỡng đã hiệu chỉnh (plan 04-04)

Khối dưới đây do `calibration/calibrate.py evaluate --apply` ghi lại — không sửa tay.
Kết quả kiểm chứng đầy đủ: `docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md`.

<!-- hieu-chinh:start -->
Giá trị do `calibration/calibrate.py tune` khớp trên tập HIEU_CHINH (2026-09-28, mô hình `bkai-foundation-models/vietnamese-bi-encoder`), kiểm chứng bằng `evaluate`:

| Ngưỡng | Giá trị (%) | Phương pháp | Dùng ở |
|---|---:|---|---|
| `nguong_ten_de_tai` | 67.8 | youden | Web API gửi trong `/check-title` (`cau_hinh_nguong`, plan 04-05) |
| `nguong_doan` | 67.7 | youden | `/check-document`; mặc định `NGUONG_DOAN_MAC_DINH` |
| `nguong_nguyen_van` | 88.7 | youden | `/check-document`; mặc định `NGUONG_NGUYEN_VAN_MAC_DINH` |
| `nguong_tai_lieu` | 10.4 | trung_diem | Web API: cảnh báo khi tỷ lệ theo một đồ án ≥ ngưỡng (plan 04-05) |
| `MINHASH_SHINGLE` | 4 | AUC lớn nhất trong {3, 4, 5} | chữ ký MinHash |

Chạy lại (từ `ai-service/`, cần ≥ 3 GiB RAM trống, không cần docker/MySQL):

```bash
uv run python calibration/calibrate.py tune --data ../seed-data \
  --profile-from ../tools/bakeoff/ket-qua.json --out calibration
uv run python calibration/calibrate.py evaluate --data ../seed-data \
  --profile-from ../tools/bakeoff/ket-qua.json --out calibration \
  --report ../docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md --apply
```
<!-- hieu-chinh:end -->

## Ghi chú vận hành

- **Đúng một worker uvicorn** (`--workers 1`): chỉ mục là trạng thái trong tiến
  trình mà `/ingest` sửa tại chỗ — worker thứ hai sẽ phục vụ chỉ mục cũ.
- **torch chỉ từ index CPU** (`[tool.uv.sources]` → `pytorch-cpu`, lock mang
  `torch 2.14.0+cpu`, không gói `nvidia-*`); torch mặc định trên PyPI kéo CUDA.
- **datasketch 2.x** dùng lược đồ hoán vị `affine32` (giá trị băm khác 1.x) —
  không ảnh hưởng vì chữ ký MinHash không được lưu, luôn dựng lại từ `chunk.noi_dung`.
- **faiss-cpu ≥ 1.15** chỉ phát hành một wheel `cp310-abi3` (không có tên
  `cp312`) — bình thường.
- Kích thước mô hình: bkai ≈ 515 MiB, multilingual-e5-base ≈ 1.06 GiB. Mục
  tiêu bộ nhớ container: **≤ 2 GiB** (smoke đo với `--memory=2g`).
- Máy chủ không có Internet: chạy `python -m app.download_model` ở nơi có mạng
  để làm nóng cache/volume `/models`, rồi đặt `HF_HUB_OFFLINE=1`.
- Endpoint là `def` thường — FastAPI chạy trong threadpool, suy luận không chặn
  event loop; lời gọi mô hình được tuần tự hóa bằng một khóa.
- `/docs` và `/openapi.json` chỉ bật khi `APP_ENV=test`.
