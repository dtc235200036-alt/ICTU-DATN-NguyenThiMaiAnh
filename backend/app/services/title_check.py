from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cau_hinh_nguong import NGUONG_TEN_DE_TAI, CauHinhNguong
from app.models.de_tai import DeTai
from app.models.trung_lap import (
    HOAN_TAT,
    LOI,
    TEN_DE_TAI,
    ChiTietTrungLap,
    KetQuaKiemTraTrungLap,
)
from app.schemas.common import nfc
from app.services.ai_client import AiServiceError, get_ai_client


@dataclass
class TitleCheckMatch:
    de_tai_id: int
    ten_de_tai: str
    khoa: str
    giang_vien: str | None
    ty_le: float


@dataclass
class TitleCheckResult:
    trang_thai: str
    nguong: float
    matches: list[TitleCheckMatch] = field(default_factory=list)


def _get_threshold(db: Session) -> float:
    gia_tri = db.execute(
        select(CauHinhNguong.gia_tri).where(CauHinhNguong.loai == NGUONG_TEN_DE_TAI)
    ).scalar_one()
    return float(gia_tri)


def kiem_tra_ten(db: Session, ten_de_tai: str, exclude_id: int | None = None) -> TitleCheckResult:
    """UC0.6: so sánh ngữ nghĩa tên đề tài với kho — không bao giờ chặn gửi đề
    xuất (E2): khi AiClient lỗi trả về trang_thai LOI với danh sách rỗng."""
    threshold = _get_threshold(db)
    settings = get_settings()

    try:
        raw = get_ai_client(db).check_title(nfc(ten_de_tai), settings.TITLE_CHECK_TOP_K)
    except AiServiceError:
        return TitleCheckResult(trang_thai=LOI, nguong=threshold, matches=[])

    matches: list[TitleCheckMatch] = []
    for item in raw.get("matches", []):
        ref_id = item["ref_id"]
        ty_le = float(item["ty_le"])
        if exclude_id is not None and ref_id == exclude_id:
            continue
        if ty_le < threshold:
            continue
        topic = db.get(DeTai, ref_id)
        if topic is None:
            continue
        matches.append(
            TitleCheckMatch(
                de_tai_id=topic.id,
                ten_de_tai=topic.ten_de_tai,
                khoa=topic.dot_do_an.khoa if topic.dot_do_an is not None else "",
                giang_vien=topic.giang_vien.ho_ten if topic.giang_vien is not None else None,
                ty_le=ty_le,
            )
        )

    return TitleCheckResult(trang_thai=HOAN_TAT, nguong=threshold, matches=matches)


def luu_ket_qua(
    db: Session, de_tai_id: int, ten_de_tai: str, result: TitleCheckResult
) -> KetQuaKiemTraTrungLap:
    """Lưu 1 dòng ket_qua_kiem_tra_trung_lap + N dòng chi_tiet_trung_lap trong
    transaction hiện tại (caller commit cùng lúc với thay đổi trạng thái đề
    tài — UC1.1 A2/E2)."""
    ty_le_tong = (
        max((m.ty_le for m in result.matches), default=0.00)
        if result.trang_thai == HOAN_TAT
        else None
    )

    ket_qua = KetQuaKiemTraTrungLap(
        de_tai_id=de_tai_id,
        loai_kiem_tra=TEN_DE_TAI,
        trang_thai=result.trang_thai,
        ty_le_tong=ty_le_tong,
        nguong_ap_dung=result.nguong,
        doi_tuong_duoc_kiem_tra=ten_de_tai[:255],
        thoi_diem=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(ket_qua)
    db.flush()

    for match in result.matches:
        db.add(
            ChiTietTrungLap(
                ket_qua_id=ket_qua.id,
                doi_tuong_trung=match.ten_de_tai[:255],
                ty_le=match.ty_le,
            )
        )
    db.flush()
    return ket_qua


def latest_title_check(db: Session, de_tai_id: int) -> KetQuaKiemTraTrungLap | None:
    return (
        db.execute(
            select(KetQuaKiemTraTrungLap)
            .where(KetQuaKiemTraTrungLap.de_tai_id == de_tai_id)
            .where(KetQuaKiemTraTrungLap.loai_kiem_tra == TEN_DE_TAI)
            .order_by(
                KetQuaKiemTraTrungLap.thoi_diem.desc(), KetQuaKiemTraTrungLap.id.desc()
            )
            .limit(1)
        )
        .scalars()
        .first()
    )
