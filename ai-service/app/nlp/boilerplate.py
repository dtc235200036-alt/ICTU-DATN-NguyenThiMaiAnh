"""Lọc phần mẫu chung của đồ án trước khi chia câu (D-03, AISV-04, Pitfall B/C).

[ASSUMED] danh sách mặc định chung cho khuôn mẫu đồ án tiếng Việt — mẫu chính
thức (TL-04/TL-05) chưa thu thập; thay danh sách khi có mẫu (D-03).

Quy tắc (so khớp trên dòng NFC, casefold, khoảng trắng đã gộp), theo thứ tự:
(a) bỏ nguyên mục: dòng tiêu đề (có thể có số thứ tự Ả Rập / La Mã) thuộc
    LỜI CAM ĐOAN, LỜI CẢM ƠN, MỤC LỤC, DANH MỤC HÌNH/HÌNH ẢNH/HÌNH VẼ,
    DANH MỤC BẢNG/BẢNG BIỂU, DANH MỤC (CÁC) TỪ/CHỮ VIẾT TẮT, DANH MỤC KÝ HIỆU,
    TÀI LIỆU THAM KHẢO, PHỤ LỤC, NHẬN XÉT CỦA GIẢNG VIÊN (HƯỚNG DẪN|PHẢN BIỆN)
    bỏ chính nó và mọi dòng tới tiêu đề lớn kế tiếp (MỞ ĐẦU, LỜI MỞ ĐẦU,
    CHƯƠNG n, KẾT LUẬN hoặc một tiêu đề trong danh sách trên);
(b) dòng bìa: TRƯỜNG ĐẠI HỌC…, ĐẠI HỌC THÁI NGUYÊN, KHOA CÔNG NGHỆ THÔNG TIN,
    ĐỒ ÁN TỐT NGHIỆP, ĐỀ CƯƠNG ĐỒ ÁN…, BÁO CÁO ĐỒ ÁN…, nhãn "Sinh viên thực
    hiện", "Giảng viên hướng dẫn", "Mã sinh viên", "Lớp", "Ngành", "Đề tài:"
    và "Thái Nguyên, … năm yyyy"; tên đề tài sau nhãn "Đề tài:" bị PDF bẻ sang
    tối đa 2 dòng tiếp theo (≤ 20 âm tiết, không kết thúc bằng dấu câu) cũng
    bị bỏ (plan 04-04: nếu sót, dòng bìa dính vào câu nội dung đầu tiên);
(c) dòng mục lục: kết thúc bằng dải dấu chấm/… hoặc tab rồi số trang;
(d) dòng tiêu đề: "CHƯƠNG …", tiêu đề đánh số (^\\d+(\\.\\d+)*\\.?\\s) tối đa 15
    âm tiết không kết thúc bằng dấu câu, dòng VIẾT HOA TOÀN BỘ tối đa 20 âm
    tiết (tên đề tài trên bìa, MỞ ĐẦU, KẾT LUẬN…), chú thích "Hình/Bảng/Biểu
    đồ/Sơ đồ" + số;
(e) dòng lặp: dòng tối đa 20 âm tiết, không kết thúc bằng dấu câu, mà dạng
    che-chữ-số xuất hiện ≥ 3 lần trong cùng văn bản (header/footer PDF) — dòng
    kết thúc bằng dấu câu là mảnh cuối đoạn do PDF bẻ dòng (vd. "Quang."),
    không phải header (plan 04-04); số trang trơn và "Trang n" —
    trích xuất PDF naive phía Web API (page.get_text()) không tránh được.
`removed` đếm số dòng đã bỏ; `removed_chars`/`total_chars` đếm ký tự để Web
API báo cho GVHD phần văn bản KHÔNG được kiểm tra.

CR-04 (04-REVIEW) — quy tắc (a) không được dùng để giấu nội dung:
- vị trí: tiêu đề mục mẫu chỉ kích hoạt việc bỏ nguyên mục khi nằm ở phần
  đầu (trước tiêu đề lớn đầu tiên MỞ ĐẦU/CHƯƠNG n/KẾT LUẬN) hoặc phần cuối
  (sau tiêu đề lớn cuối cùng). Một dòng "Phụ lục" chèn giữa hai chương chỉ
  bị bỏ như một dòng tiêu đề, nội dung chương vẫn được kiểm tra;
- độ dài: một mục bỏ tối đa max(40 dòng, 15 % số dòng), toàn bộ các mục bỏ
  tối đa max(80 dòng, 40 % số dòng) — tài liệu không có tiêu đề lớn nào (vd.
  đề cương không chia chương) không thể bị xóa sạch bằng các dòng "Phụ lục";
- dòng VIẾT HOA chỉ coi là tiêu đề khi không kết thúc bằng dấu câu (câu nội
  dung viết hoa toàn bộ vẫn được kiểm tra).
"""
import re
from collections import Counter
from dataclasses import dataclass

from app.nlp.normalize import nfc, syllables

_NUM_PREFIX = r"(?:(?:\d+|[ivxlc]+)[.)]?\s+)?"

_SECTION_RE = re.compile(
    rf"^{_NUM_PREFIX}(?:"
    r"lời cam đoan|lời cảm ơn|mục lục"
    r"|danh mục (?:các )?(?:hình|bảng|từ viết tắt|chữ viết tắt|ký hiệu|kí hiệu)\b.*"
    r"|tài liệu tham khảo"
    r"|phụ lục\b.*"
    r"|nhận xét của giảng viên(?: hướng dẫn| phản biện)?"
    r")[.:]?$"
)
_MAJOR_RE = re.compile(r"^(?:(?:lời )?mở đầu|chương\s+(?:\d+|[ivxlc]+)\b.*|kết luận\b.*)$")

_COVER_RE = re.compile(
    r"^(?:trường đại học\b.*|đại học thái nguyên|khoa công nghệ thông tin"
    r"|đồ án tốt nghiệp|đề cương đồ án\b.*|báo cáo đồ án\b.*"
    r"|thái nguyên,.*năm \d{4}\.?)$"
)
_LABEL_RE = re.compile(r"^(?:sinh viên thực hiện|giảng viên hướng dẫn|mã sinh viên|lớp)\b\s*(:)?")
# Nhãn chỉ nhận dạng khi có dấu ':' (dòng PDF bắt đầu bằng "ngành …" có thể là nội dung).
_LABEL_COLON_RE = re.compile(r"^(?:chuyên )?ngành\s*:")
_COVER_TITLE_RE = re.compile(r"^(?:tên )?đề tài\s*:")
_COVER_TITLE_MAX_CONT = 2

_TOC_RE = re.compile(r"(?:\.{3,}|…+|\t)\s*(?:\d+|[ivxlc]+)$")
_CHUONG_RE = re.compile(r"^chương\s+(?:\d+|[ivxlc]+)\b")
_NUMBERED_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s")
_CAPTION_RE = re.compile(r"^(?:hình|bảng|biểu đồ|sơ đồ)\s+\d+(?:[.\-]\d+)*\b")
_PAGE_RE = re.compile(
    r"^(?:[-–]?\s*\d{1,4}\s*[-–]?|trang\s+\d{1,4}(?:\s*/\s*\d{1,4})?"
    r"|(?=[ivx])x{0,3}(?:ix|iv|v?i{0,3}))$"
)
_DIGITS_RE = re.compile(r"\d+")
_SENTENCE_END = (".", "!", "?", "…", ";")


# CR-04: trần độ dài của việc bỏ nguyên mục (dòng).
_SECTION_MAX_LINES = 40
_SECTION_MAX_SHARE = 0.15
_SECTIONS_MAX_LINES = 80
_SECTIONS_MAX_SHARE = 0.40


@dataclass(frozen=True)
class StripResult:
    lines: list[str]
    removed: int
    removed_chars: int = 0
    total_chars: int = 0


def _key(line: str) -> str:
    return line.casefold()


def _is_section_heading(key: str, n_syl: int) -> bool:
    return n_syl <= 12 and bool(_SECTION_RE.match(key))


def _is_major_heading(key: str, n_syl: int) -> bool:
    return n_syl <= 15 and bool(_MAJOR_RE.match(key))


def _is_toc(key: str) -> bool:
    return bool(_TOC_RE.search(key))


def _is_cover(line: str, key: str, n_syl: int) -> bool:
    if n_syl <= 20 and _COVER_RE.match(key):
        return True
    if _LABEL_COLON_RE.match(key):
        return True
    label = _LABEL_RE.match(key)
    # Nhãn trên bìa: "Lớp: CNTT K22A" — tránh bỏ nhầm câu nội dung bắt đầu
    # bằng "Giảng viên hướng dẫn …" (bắt buộc dấu ':' hoặc dòng rất ngắn).
    return bool(label) and (label.group(1) is not None or n_syl <= 6)


def _is_all_caps(line: str) -> bool:
    letters = [ch for ch in line if ch.isalpha()]
    return len(letters) >= 2 and all(ch.isupper() for ch in letters)


def _is_heading(line: str, key: str, n_syl: int) -> bool:
    if _CHUONG_RE.match(key) and n_syl <= 20:
        return True
    if _NUMBERED_RE.match(key) and n_syl <= 15 and not key.endswith(_SENTENCE_END):
        return True
    if n_syl <= 20 and _is_all_caps(line) and not key.endswith(_SENTENCE_END):
        return True
    return n_syl <= 30 and bool(_CAPTION_RE.match(key))


def strip_boilerplate(text: str) -> StripResult:
    lines = [line for line in nfc(text).split("\n") if line]
    keys = [_key(line) for line in lines]
    n_syls = [len(syllables(line)) for line in lines]
    masked = Counter(
        _DIGITS_RE.sub("#", key) for key, n in zip(keys, n_syls) if n <= 20
    )
    # CR-04: vùng thân = từ tiêu đề lớn đầu tiên tới tiêu đề lớn cuối cùng
    # (không tính dòng mục lục); tiêu đề mục mẫu trong vùng thân không bỏ mục.
    majors = [
        i
        for i, (key, n_syl) in enumerate(zip(keys, n_syls))
        if not _is_toc(key)
        and not _is_section_heading(key, n_syl)
        and _is_major_heading(key, n_syl)
    ]
    body_first = majors[0] if majors else None
    body_last = majors[-1] if majors else None
    section_cap = max(_SECTION_MAX_LINES, int(_SECTION_MAX_SHARE * len(lines)))
    sections_cap = max(_SECTIONS_MAX_LINES, int(_SECTIONS_MAX_SHARE * len(lines)))

    kept: list[str] = []
    removed = removed_chars = 0
    in_section = False
    section_used = sections_used = 0
    title_cont = 0  # số dòng tiếp nối tên đề tài trên bìa còn được bỏ
    for idx, (line, key, n_syl) in enumerate(zip(lines, keys, n_syls)):
        if title_cont:
            title_cont -= 1
            if (
                n_syl <= 20
                and not key.endswith(_SENTENCE_END)
                and not _LABEL_RE.match(key)
                and not _LABEL_COLON_RE.match(key)
            ):
                removed += 1
                removed_chars += len(line)
                continue
            title_cont = 0
        if _COVER_TITLE_RE.match(key):
            title_cont = _COVER_TITLE_MAX_CONT
            removed += 1
            removed_chars += len(line)
            continue
        is_section = _is_section_heading(key, n_syl)
        if in_section and not is_section:
            if not _is_toc(key) and _is_major_heading(key, n_syl):
                in_section = False  # tiêu đề lớn kết thúc mục; bản thân nó bị bỏ
                removed += 1
                removed_chars += len(line)
                continue
            if section_used < section_cap and sections_used < sections_cap:
                section_used += 1
                sections_used += 1
                removed += 1
                removed_chars += len(line)
                continue
            in_section = False  # CR-04: quá trần — dòng này xử lý như bình thường
        if is_section:
            # CR-04: chỉ phần đầu/phần cuối mới bỏ nguyên mục; không có tiêu đề
            # lớn nào thì cả tài liệu là "phần đầu" (trần độ dài giữ an toàn).
            in_front = body_first is None or idx < body_first
            in_back = body_last is not None and idx > body_last
            in_section = in_front or in_back
            section_used = 0
            removed += 1
            removed_chars += len(line)
            continue
        if (
            _is_toc(key)
            or _PAGE_RE.match(key)
            or (
                n_syl <= 20
                and not key.endswith(_SENTENCE_END)
                and masked[_DIGITS_RE.sub("#", key)] >= 3
            )
            or _is_cover(line, key, n_syl)
            or _is_heading(line, key, n_syl)
        ):
            removed += 1
            removed_chars += len(line)
            continue
        kept.append(line)
    return StripResult(
        lines=kept,
        removed=removed,
        removed_chars=removed_chars,
        total_chars=sum(len(line) for line in lines),
    )
