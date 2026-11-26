from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cau_hinh_nguong import NGUONG_TEN_DE_TAI, CauHinhNguong
from app.models.de_tai import NHAP, DeTai
from app.models.kho import DoAnKho
from app.models.trung_lap import (
    HOAN_TAT,
    LOI,
    TEN_DE_TAI,
    ChiTietTrungLap,
    KetQuaKiemTraTrungLap,
)
from app.schemas.common import nfc
from app.services.ai_client import AiServiceError, get_ai_client


# Nguồn của một kết quả kiểm tra tên (AISV-03): đề tài hiện hành (TOPIC,
# de_tai.id) hoặc đồ án trong kho (ARCHIVE, do_an_kho.id) — 04-01 id namespaces.
NGUON_DE_TAI = "DE_TAI"
NGUON_KHO = "KHO"
LOAI_TOPIC = "TOPIC"
LOAI_ARCHIVE = "ARCHIVE"


@dataclass
class TitleCheckMatch:
    de_tai_id: int | None
    ten_de_tai: str
    khoa: str
    giang_vien: str | None
    ty_le: float
    nguon: str = NGUON_DE_TAI
    do_an_kho_id: int | None = None


@dataclass
class TitleCheckResult:
    trang_thai: str
    nguong: float
    matches: list[TitleCheckMatch] = field(default_factory=list)


# WR-02: chỉ dùng để LƯU VẾT khi bảng cau_hinh_nguong thiếu dòng
# NGUONG_TEN_DE_TAI (bị xóa qua truy cập DB trực tiếp, migration 0004's seed
# bị bỏ qua/rollback, DB mới...) — KHÔNG dùng để so khớp (kiem_tra_ten trả về
# LOI ngay, không thực hiện so khớp) nên giá trị này chỉ cần hợp lệ để ghi
# vào cột nguong_ap_dung, không cần đúng ngưỡng nghiệp vụ hiện hành. Khớp giá
# trị dòng seed NGUONG_TEN_DE_TAI trong migration 0004 để nhất quán tài liệu.
_FALLBACK_NGUONG_TEN_DE_TAI = 50.00


def _get_threshold(db: Session) -> float:
    gia_tri = db.execute(
        select(CauHinhNguong.gia_tri).where(CauHinhNguong.loai == NGUONG_TEN_DE_TAI)
    ).scalar_one()
    return float(gia_tri)


def _resolve_match(
    db: Session, loai: str, ref_id: int, ty_le: float, exclude_id: int | None
) -> tuple[tuple[str, int], TitleCheckMatch] | None:
    """Ánh xạ một match của dịch vụ AI về bản ghi thesis_core. Trả (khóa gộp,
    match) — khóa gộp là đề tài gốc khi bản ghi kho liên kết một đề tài, để
    một đồ án không xuất hiện hai lần (TOPIC + ARCHIVE). Ref không còn tồn tại
    thì bỏ qua — phòng thủ: xóa bản ghi kho và chốt bảo vệ đã gỡ vector tương
    ứng (WR-04), còn sót chỉ khi lần gỡ nền đó lỗi."""
    if loai == LOAI_ARCHIVE:
        kho = db.get(DoAnKho, ref_id)
        if kho is None:
            return None
        if exclude_id is not None and kho.de_tai_id == exclude_id:
            return None
        key = (NGUON_DE_TAI, kho.de_tai_id) if kho.de_tai_id is not None else (NGUON_KHO, kho.id)
        return key, TitleCheckMatch(
            de_tai_id=kho.de_tai_id,
            ten_de_tai=kho.ten_de_tai,
            khoa=kho.khoa or "",
            giang_vien=kho.giang_vien.ho_ten if kho.giang_vien is not None else None,
            ty_le=ty_le,
            nguon=NGUON_KHO,
            do_an_kho_id=kho.id,
        )

    if exclude_id is not None and ref_id == exclude_id:
        return None
    topic = db.get(DeTai, ref_id)
    # Đề tài bị thu hồi về Nháp còn vector cũ trong chỉ mục AI — bỏ qua như kho từ vựng.
    if topic is None or topic.trang_thai == NHAP:
        return None
    return (NGUON_DE_TAI, topic.id), TitleCheckMatch(
        de_tai_id=topic.id,
        ten_de_tai=topic.ten_de_tai,
        khoa=topic.dot_do_an.khoa if topic.dot_do_an is not None else "",
        giang_vien=topic.giang_vien.ho_ten if topic.giang_vien is not None else None,
        ty_le=ty_le,
        nguon=NGUON_DE_TAI,
    )


def kiem_tra_ten(db: Session, ten_de_tai: str, exclude_id: int | None = None) -> TitleCheckResult:
    """UC0.6/AISV-03: so sánh ngữ nghĩa tên đề tài với đề tài hiện hành (TOPIC)
    và kho đồ án (ARCHIVE) — không bao giờ chặn gửi đề xuất (E2): khi dịch vụ AI
    lỗi trả về trang_thai LOI với danh sách rỗng. D-04: Web API gửi ngưỡng hiện
    hành của Bộ môn theo từng request."""
    try:
        threshold = _get_threshold(db)
    except NoResultFound:
        # WR-02: thiếu cấu hình ngưỡng cũng là một dạng "hạ tầng kiểm tra
        # trùng không khả dụng" giống hệt AiServiceError — không được để lộ
        # ra thành lỗi 500 không xử lý, phải suy biến giống E2.
        return TitleCheckResult(
            trang_thai=LOI, nguong=_FALLBACK_NGUONG_TEN_DE_TAI, matches=[]
        )
    settings = get_settings()

    try:
        # Lấy dư (×2) vì một đồ án có thể trả về hai lần (TOPIC + ARCHIVE) và
        # ref đã xóa bị bỏ qua.
        raw = get_ai_client(db).check_title(
            nfc(ten_de_tai), settings.TITLE_CHECK_TOP_K * 2, nguong=threshold
        )
    except AiServiceError:
        return TitleCheckResult(trang_thai=LOI, nguong=threshold, matches=[])

    best: dict[tuple[str, int], TitleCheckMatch] = {}
    for item in raw.get("matches", []):
        ty_le = float(item["ty_le"])
        if ty_le < threshold:
            continue
        resolved = _resolve_match(
            db, item.get("loai", LOAI_TOPIC), int(item["ref_id"]), ty_le, exclude_id
        )
        if resolved is None:
            continue
        key, match = resolved
        current = best.get(key)
        if current is None or match.ty_le > current.ty_le:
            best[key] = match

    matches = sorted(best.values(), key=lambda m: -m.ty_le)[: settings.TITLE_CHECK_TOP_K]
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
        if match.nguon == NGUON_KHO and match.khoa:
            doi_tuong = f"{match.ten_de_tai} ({match.khoa})"
        else:
            doi_tuong = match.ten_de_tai
        db.add(
            ChiTietTrungLap(
                ket_qua_id=ket_qua.id,
                doi_tuong_trung=doi_tuong[:255],
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
