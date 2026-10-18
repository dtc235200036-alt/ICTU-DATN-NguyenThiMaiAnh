"""Các kiểm tra tự động trước khi đề cương được nộp lên Bộ môn và khi Lãnh đạo
bộ môn phê duyệt (góp ý GVHD, mục "Lưu ý"):

- tên file đúng quy tắc <Mã định hướng>.<MSSV>.<Họ tên>.<Lớp>.<pdf|docx>;
- định hướng trong tên file khớp định hướng của đề tài;
- nội dung: kết quả kiểm tra trùng lặp của phiên bản;
- file phê duyệt có chữ ký số (PDF, chữ ký PKCS#7 nhúng trong file).

Kiểm tra chữ ký số chỉ xác định file CÓ chữ ký, đọc người ký/thời điểm ký và
phạm vi ký phủ toàn bộ file (không bị sửa sau khi ký); không xác thực chuỗi
chứng thư tới CA gốc."""
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.x509.oid import NameOID

from app.models.de_cuong import TaiLieuDoAn
from app.models.de_tai import DeTai
from app.models.tai_khoan import SinhVien
from app.schemas.outlines import CheckItem
from app.services import document_check

_DUOI_HOP_LE = ("pdf", "docx")
_MA_DINH_HUONG_RE = re.compile(r"^H\d{2}$", re.IGNORECASE)


def _chuan_hoa(value: str | None) -> str:
    """So khớp không phân biệt hoa thường, khoảng trắng và dạng Unicode."""
    if not value:
        return ""
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", value)).casefold()


def ten_file_mau(sv: SinhVien | None, ma_dinh_huong: str | None, duoi: str = "pdf") -> str:
    """Tên file đúng quy tắc cho SV và định hướng của đề tài (hiển thị hướng dẫn)."""
    ma = ma_dinh_huong or "Hxx"
    mssv = (sv.ma_so_sinh_vien if sv else None) or "MSSV"
    ho_ten = (sv.ho_ten if sv else None) or "Họ tên"
    lop = (sv.lop if sv else None) or "Lớp"
    return f"{ma}.{mssv}.{ho_ten}.{lop}.{duoi}"


@dataclass
class TenFile:
    ma_dinh_huong: str
    mssv: str
    ho_ten: str
    lop: str


def tach_ten_file(ten_goc: str) -> TenFile | None:
    ten = unicodedata.normalize("NFC", ten_goc).strip()
    if "." not in ten:
        return None
    goc, duoi = ten.rsplit(".", 1)
    if duoi.lower() not in _DUOI_HOP_LE:
        return None
    phan = [p.strip() for p in goc.split(".")]
    if len(phan) != 4 or not all(phan):
        return None
    if not _MA_DINH_HUONG_RE.match(phan[0]):
        return None
    return TenFile(ma_dinh_huong=phan[0].upper(), mssv=phan[1], ho_ten=phan[2], lop=phan[3])


def kiem_tra_ten_file(doc: TaiLieuDoAn | None, topic: DeTai) -> CheckItem:
    sv = topic.sinh_vien
    ma_dh = topic.dinh_huong.ma if topic.dinh_huong is not None else None
    mau = ten_file_mau(sv, ma_dh)
    if doc is None:
        return CheckItem(ma="TEN_FILE", ten="Tên file đúng quy tắc", dat=False, chi_tiet="Chưa có file")
    tach = tach_ten_file(doc.ten_goc)
    if tach is None:
        return CheckItem(
            ma="TEN_FILE",
            ten="Tên file đúng quy tắc",
            dat=False,
            chi_tiet=f"'{doc.ten_goc}' không theo mẫu {mau}",
        )
    sai: list[str] = []
    if sv is not None:
        if _chuan_hoa(tach.mssv) != _chuan_hoa(sv.ma_so_sinh_vien):
            sai.append("mã SV")
        if _chuan_hoa(tach.ho_ten) != _chuan_hoa(sv.ho_ten):
            sai.append("họ tên")
        if _chuan_hoa(tach.lop) != _chuan_hoa(sv.lop):
            sai.append("lớp")
    if sai:
        return CheckItem(
            ma="TEN_FILE",
            ten="Tên file đúng quy tắc",
            dat=False,
            chi_tiet=f"Sai {', '.join(sai)} so với hồ sơ sinh viên — mẫu đúng: {mau}",
        )
    return CheckItem(ma="TEN_FILE", ten="Tên file đúng quy tắc", dat=True, chi_tiet=doc.ten_goc)


def kiem_tra_dinh_huong(doc: TaiLieuDoAn | None, topic: DeTai) -> CheckItem:
    ten = "Định hướng khớp danh sách tổng hợp"
    if topic.dinh_huong is None:
        return CheckItem(ma="DINH_HUONG", ten=ten, dat=False, chi_tiet="Đề tài chưa có định hướng")
    tach = tach_ten_file(doc.ten_goc) if doc is not None else None
    if tach is None:
        return CheckItem(
            ma="DINH_HUONG",
            ten=ten,
            dat=False,
            chi_tiet=f"Không đọc được mã định hướng từ tên file (đề tài: {topic.dinh_huong.ma})",
        )
    if tach.ma_dinh_huong != topic.dinh_huong.ma.upper():
        return CheckItem(
            ma="DINH_HUONG",
            ten=ten,
            dat=False,
            chi_tiet=(
                f"Tên file ghi {tach.ma_dinh_huong}, đề tài thuộc "
                f"{topic.dinh_huong.ma} — {topic.dinh_huong.ten}"
            ),
        )
    return CheckItem(
        ma="DINH_HUONG",
        ten=ten,
        dat=True,
        chi_tiet=f"{topic.dinh_huong.ma} — {topic.dinh_huong.ten}",
    )


def kiem_tra_noi_dung(doc: TaiLieuDoAn | None) -> CheckItem:
    """Thông tin cho người duyệt — không chặn việc nộp lên (GVHD/Bộ môn quyết định)."""
    ten = "Kiểm tra nội dung (trùng lặp)"
    ket_qua = doc.ket_qua_kiem_tra if doc is not None else None
    if ket_qua is None:
        return CheckItem(ma="NOI_DUNG", ten=ten, dat=False, chi_tiet="Chưa kiểm tra")
    tom_tat = document_check.summary(ket_qua)
    if tom_tat.vuot_nguong is None:
        return CheckItem(ma="NOI_DUNG", ten=ten, dat=False, chi_tiet="Chưa có kết quả kiểm tra")
    ty_le = tom_tat.ty_le_nguon_cao_nhat or 0
    if tom_tat.vuot_nguong:
        return CheckItem(
            ma="NOI_DUNG",
            ten=ten,
            dat=False,
            chi_tiet=f"Vượt ngưỡng cảnh báo: trùng {ty_le:.1f}% với một đồ án (ngưỡng {tom_tat.nguong_ap_dung:.1f}%)",
        )
    return CheckItem(
        ma="NOI_DUNG",
        ten=ten,
        dat=True,
        chi_tiet=f"Trùng cao nhất {ty_le:.1f}% (ngưỡng {tom_tat.nguong_ap_dung:.1f}%)",
    )


# --- Chữ ký số PDF -----------------------------------------------------------

_BYTE_RANGE_RE = re.compile(rb"/ByteRange\s*\[\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*\]")
_M_RE = re.compile(rb"/M\s*\(D:(\d{14})")


@dataclass
class ChuKySo:
    nguoi_ky: str | None
    thoi_diem_ky: datetime | None
    phu_toan_bo_file: bool


def _do_dai_der(data: bytes) -> int | None:
    """Độ dài SEQUENCE DER ở đầu `data` (bỏ phần đệm 0 sau chữ ký)."""
    if len(data) < 2 or data[0] != 0x30:
        return None
    first = data[1]
    if first < 0x80:
        return 2 + first
    n = first & 0x7F
    if n == 0 or n > 4 or len(data) < 2 + n:
        return None
    return 2 + n + int.from_bytes(data[2 : 2 + n], "big")


def _ten_nguoi_ky(der: bytes) -> str | None:
    try:
        certs = pkcs7.load_der_pkcs7_certificates(der)
    except ValueError:
        return None
    if not certs:
        return None

    def _la_ca(cert: x509.Certificate) -> bool:
        try:
            return cert.extensions.get_extension_for_class(x509.BasicConstraints).value.ca
        except x509.ExtensionNotFound:
            return False

    cert = next((c for c in certs if not _la_ca(c)), certs[0])
    cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    return str(cn[0].value) if cn else cert.subject.rfc4514_string()


def doc_chu_ky_so(content: bytes) -> ChuKySo | None:
    """Chữ ký cuối cùng trong file PDF (None nếu không có chữ ký nào hợp lệ)."""
    matches = list(_BYTE_RANGE_RE.finditer(content))
    for m in reversed(matches):
        a, b, c, d = (int(x) for x in m.groups())
        if a != 0 or b <= 0 or c <= b or c + d > len(content):
            continue
        contents = content[b:c].strip()
        if not (contents.startswith(b"<") and contents.endswith(b">")):
            continue
        try:
            raw = bytes.fromhex(contents[1:-1].decode("ascii"))
        except ValueError:
            continue
        do_dai = _do_dai_der(raw)
        if do_dai is None or do_dai > len(raw):
            continue
        nguoi_ky = _ten_nguoi_ky(raw[:do_dai])
        if nguoi_ky is None:
            continue
        thoi_diem = None
        vung = content[max(0, m.start() - 4096) : m.end() + 4096]
        m_time = _M_RE.search(vung)
        if m_time is not None:
            try:
                thoi_diem = datetime.strptime(m_time.group(1).decode(), "%Y%m%d%H%M%S")
            except ValueError:
                thoi_diem = None
        return ChuKySo(
            nguoi_ky=nguoi_ky,
            thoi_diem_ky=thoi_diem,
            phu_toan_bo_file=(c + d == len(content.rstrip(b"\r\n")) or c + d == len(content)),
        )
    return None


def mo_ta_chu_ky(chu_ky: ChuKySo) -> str:
    parts = [f"Người ký: {chu_ky.nguoi_ky}"]
    if chu_ky.thoi_diem_ky is not None:
        parts.append(f"lúc {chu_ky.thoi_diem_ky:%d/%m/%Y %H:%M}")
    return ", ".join(parts)
