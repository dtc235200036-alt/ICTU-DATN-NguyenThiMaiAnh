"""Các kiểm tra tự động trước khi đề cương được nộp lên Bộ môn (góp ý GVHD,
mục "Lưu ý"):

- tên file đúng quy tắc <Mã định hướng>.<MSSV>.<Họ tên>.<Lớp>.<pdf|docx>;
- định hướng trong tên file khớp định hướng của đề tài;
- nội dung: kết quả kiểm tra trùng lặp của phiên bản."""
import re
import unicodedata
from dataclasses import dataclass

from app.models.de_cuong import TaiLieuDoAn
from app.models.de_tai import DeTai
from app.models.tai_khoan import SinhVien
from app.schemas.outlines import CheckItem
from app.services import document_check

_DUOI_HOP_LE = ("pdf", "docx")
_MA_DINH_HUONG_RE = re.compile(r"^H\d{2}$", re.IGNORECASE)
# Hậu tố Word/Windows tự thêm vào tên file: "(Repaired)", "(1)", "- Copy",
# "- Bản sao (2)"... — bỏ trước khi so khớp, các phần còn lại vẫn phải đúng.
_HAU_TO_RE = re.compile(
    r"(?:\s*(?:\((?:repaired|đã sửa chữa|đã sửa|\d+)\)|-\s*(?:copy|bản sao)(?:\s*\(\d+\))?))+$",
    re.IGNORECASE,
)


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
    goc = _HAU_TO_RE.sub("", goc)
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
    if tom_tat.ly_do_vuot_nguong == document_check.LY_DO_TONG_NGUON:
        return CheckItem(
            ma="NOI_DUNG",
            ten=ten,
            dat=False,
            chi_tiet=(
                f"Vượt ngưỡng cảnh báo: trùng tổng {tom_tat.ty_le_tong or 0:.1f}% với nhiều đồ án"
                f" (ngưỡng tổng {tom_tat.nguong_tong_ap_dung or 0:.1f}%)"
            ),
        )
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
