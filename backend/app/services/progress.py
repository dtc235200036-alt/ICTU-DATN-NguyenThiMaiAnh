"""UC3 — Quản lý tiến độ: Bộ môn đặt mốc theo đợt (UC3.1), SV nộp một báo cáo
mỗi mốc kèm tệp tùy chọn (UC3.2), GVHD nhận xét + đánh giá (UC3.3), Bộ môn
theo dõi toàn khoa với cờ trễ mốc TÍNH TỪ NGÀY, không lưu DB (UC3.4, D-05)."""
from dataclasses import dataclass
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser
from app.core.roles import VaiTro
from app.core.timeutil import now_utc, to_vn_date, today_vn
from app.models.de_cuong import DC_CHUA_NOP, DC_DA_DUYET, LOAI_BAO_CAO_TIEN_DO, DeCuong
from app.models.de_tai import DA_PHAN_CONG, DeTai
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.tai_khoan import SinhVien
from app.models.thong_bao import TIEN_DO_NHAN_XET
from app.models.tien_do import (
    CHUA_DEN_HAN,
    DANH_GIA_LABELS,
    DUNG_HAN,
    NOP_TRE,
    TRE_MOC,
    BaoCaoTienDo,
    MocTienDo,
)
from app.schemas.common import nfc
from app.schemas.progress import (
    MilestoneIn,
    MilestoneOut,
    MilestoneStatus,
    MilestoneUpdate,
    MyProgressOut,
    ProgressCellOut,
    ProgressDashboardOut,
    ProgressRowOut,
    ReportOut,
    ReviewIn,
    StudentProgressItem,
    TopicProgressOut,
    TopicRef,
)
from app.schemas.topics import CohortRef, PersonRef
from app.services import documents, notifications
from app.services import dashboard as dashboard_service  # module import: tránh vòng import (03-07)
from app.services.documents import ValidatedFile

_COHORT_NOT_FOUND = "Không tìm thấy đợt đồ án"
_COHORT_CLOSED = "Đợt đồ án đã đóng — không thể thay đổi mốc tiến độ"
_HAN_NOP_OUT_OF_RANGE = "Hạn nộp nằm ngoài thời gian đợt đồ án (UC3.1 - E1)"
_MILESTONE_NOT_FOUND = "Không tìm thấy mốc tiến độ"
_MILESTONE_HAS_REPORTS = "Mốc đã có báo cáo — hãy sửa hạn nộp thay vì xóa (UC3.1 - A1)"
_NO_ASSIGNED_TOPIC = "Bạn chưa có đề tài được phân công GVHD"
_OUTLINE_NOT_APPROVED = "Đề cương chưa được duyệt — chưa thể nộp báo cáo tiến độ (UC3.2)"
_NO_MILESTONES = "Bộ môn chưa thiết lập mốc tiến độ cho đợt đồ án này"
_ALL_REVIEWED = "Tất cả các mốc đã được GVHD nhận xét"
_NOI_DUNG_INVALID = "Nội dung công việc phải từ 1 đến 10000 ký tự"
_ALREADY_REVIEWED = "GVHD đã nhận xét báo cáo mốc này — không thể nộp lại"
_SUBMIT_RACE = "Đang có một lần nộp khác, vui lòng thử lại"
_TOPIC_NOT_FOUND = "Không tìm thấy đề tài"
_VIEW_FORBIDDEN = "Bạn không có quyền xem tiến độ của đề tài này"
_REPORT_NOT_FOUND = "Không tìm thấy báo cáo tiến độ"
_REVIEW_FORBIDDEN = "Chỉ GVHD của đề tài mới nhận xét được báo cáo tiến độ"

_NOI_DUNG_MAX = 10000


# ---------------------------------------------------------------------------
# D-05: quy tắc DUY NHẤT sinh mọi cờ đúng hạn / trễ
# ---------------------------------------------------------------------------
def trang_thai_moc(han_nop: date | None, thoi_diem_nop: datetime | None, today: date) -> str:
    """Có báo cáo → DUNG_HAN nếu ngày nộp (giờ VN) ≤ hạn (hoặc không có hạn),
    ngược lại NOP_TRE. Chưa có báo cáo → CHUA_DEN_HAN khi hôm nay ≤ hạn (hoặc
    không có hạn), ngược lại TRE_MOC. `today` là ngày theo giờ Việt Nam."""
    if thoi_diem_nop is not None:
        if han_nop is None or to_vn_date(thoi_diem_nop) <= han_nop:
            return DUNG_HAN
        return NOP_TRE
    if han_nop is None or today <= han_nop:
        return CHUA_DEN_HAN
    return TRE_MOC


def _so_ngay_tre(han_nop: date | None, thoi_diem_nop: datetime | None, today: date) -> int | None:
    if han_nop is None:
        return None
    ngay = to_vn_date(thoi_diem_nop) if thoi_diem_nop is not None else today
    delta = (ngay - han_nop).days
    return delta if delta > 0 else None


@dataclass
class ProgressCell:
    moc: MocTienDo
    trang_thai: str
    so_ngay_tre: int | None
    bao_cao: BaoCaoTienDo | None


@dataclass
class ProgressRow:
    """Một đề tài × mọi mốc của đợt — dùng lại cho dashboard (plan 03-07)."""

    de_tai: DeTai
    cells: list[ProgressCell]

    @property
    def tre_moc(self) -> bool:
        """SV trễ mốc khi có mốc không có báo cáo tới hạn (NOP_TRE hoặc TRE_MOC)."""
        return any(c.trang_thai in (NOP_TRE, TRE_MOC) for c in self.cells)


def _milestones_by_cohort(db: Session, dot_ids: set[int]) -> dict[int, list[MocTienDo]]:
    result: dict[int, list[MocTienDo]] = {dot_id: [] for dot_id in dot_ids}
    if not dot_ids:
        return result
    rows = (
        db.execute(
            select(MocTienDo)
            .where(MocTienDo.dot_do_an_id.in_(dot_ids))
            .order_by(MocTienDo.dot_do_an_id, MocTienDo.thu_tu, MocTienDo.id)
        )
        .scalars()
        .all()
    )
    for moc in rows:
        result[moc.dot_do_an_id].append(moc)
    return result


def _build_rows(db: Session, topics: list[DeTai], today: date) -> list[ProgressRow]:
    """Hai truy vấn cho cả danh sách: mọi mốc của các đợt liên quan + mọi báo
    cáo của các đề tài (không N+1)."""
    if not topics:
        return []
    moc_by_dot = _milestones_by_cohort(db, {t.dot_do_an_id for t in topics})
    reports = (
        db.execute(
            select(BaoCaoTienDo)
            .where(BaoCaoTienDo.de_tai_id.in_([t.id for t in topics]))
            .options(selectinload(BaoCaoTienDo.tai_lieu))
        )
        .scalars()
        .all()
    )
    by_key = {(r.de_tai_id, r.moc_tien_do_id): r for r in reports}

    rows: list[ProgressRow] = []
    for topic in topics:
        cells = []
        for moc in moc_by_dot.get(topic.dot_do_an_id, []):
            bao_cao = by_key.get((topic.id, moc.id))
            nop = bao_cao.thoi_diem_nop if bao_cao is not None else None
            cells.append(
                ProgressCell(
                    moc=moc,
                    trang_thai=trang_thai_moc(moc.han_nop, nop, today),
                    so_ngay_tre=_so_ngay_tre(moc.han_nop, nop, today),
                    bao_cao=bao_cao,
                )
            )
        rows.append(ProgressRow(de_tai=topic, cells=cells))
    return rows


def compute_cohort_progress(
    db: Session, dot_do_an_id: int
) -> tuple[list[MocTienDo], list[ProgressRow]]:
    """UC3.4: mọi đề tài DA_PHAN_CONG của đợt (theo mã SV) × mọi mốc của đợt."""
    milestones = _milestones_by_cohort(db, {dot_do_an_id})[dot_do_an_id]
    topics = (
        db.execute(
            select(DeTai)
            .outerjoin(SinhVien, SinhVien.id == DeTai.sinh_vien_id)
            .where(DeTai.dot_do_an_id == dot_do_an_id)
            .where(DeTai.trang_thai == DA_PHAN_CONG)
            .options(selectinload(DeTai.sinh_vien), selectinload(DeTai.giang_vien))
            .order_by(SinhVien.ma_so_sinh_vien, DeTai.id)
        )
        .scalars()
        .all()
    )
    return milestones, _build_rows(db, list(topics), today_vn())


# ---------------------------------------------------------------------------
# Chuyển đổi sang schema
# ---------------------------------------------------------------------------
def _sv_ref(sv) -> PersonRef | None:
    if sv is None:
        return None
    return PersonRef(id=sv.id, ho_ten=sv.ho_ten or "", ma=sv.ma_so_sinh_vien)


def _gv_ref(gv) -> PersonRef | None:
    if gv is None:
        return None
    return PersonRef(id=gv.id, ho_ten=gv.ho_ten or "", ma=gv.ma_giang_vien)


def _cohort_ref(cohort: DotDoAn | None) -> CohortRef | None:
    if cohort is None:
        return None
    return CohortRef(
        id=cohort.id, ten_dot=cohort.ten_dot, khoa=cohort.khoa, trang_thai=cohort.trang_thai
    )


def _report_out(bao_cao: BaoCaoTienDo) -> ReportOut:
    return ReportOut(
        id=bao_cao.id,
        noi_dung=bao_cao.noi_dung,
        thoi_diem_nop=bao_cao.thoi_diem_nop,
        nhan_xet=bao_cao.nhan_xet,
        danh_gia=bao_cao.danh_gia,
        tep=documents.to_document_out(bao_cao.tai_lieu) if bao_cao.tai_lieu is not None else None,
    )


def _milestone_status(cell: ProgressCell) -> MilestoneStatus:
    return MilestoneStatus(
        id=cell.moc.id,
        ten_moc=cell.moc.ten_moc,
        thu_tu=cell.moc.thu_tu,
        han_nop=cell.moc.han_nop,
        trang_thai=cell.trang_thai,
        so_ngay_tre=cell.so_ngay_tre,
        bao_cao=_report_out(cell.bao_cao) if cell.bao_cao is not None else None,
    )


def _outline_state(db: Session, de_tai_id: int) -> str:
    state = db.execute(
        select(DeCuong.trang_thai).where(DeCuong.de_tai_id == de_tai_id)
    ).scalar_one_or_none()
    return state or DC_CHUA_NOP


def _topic_view(db: Session, user: CurrentUser, topic: DeTai) -> TopicProgressOut:
    row = _build_rows(db, [topic], today_vn())[0]
    outline = _outline_state(db, topic.id)
    is_owner = user.sinh_vien_id is not None and topic.sinh_vien_id == user.sinh_vien_id

    co_the_nop, ly_do = False, None
    if is_owner:
        if topic.trang_thai != DA_PHAN_CONG:
            ly_do = _NO_ASSIGNED_TOPIC
        elif outline != DC_DA_DUYET:
            ly_do = _OUTLINE_NOT_APPROVED
        elif not row.cells:
            ly_do = _NO_MILESTONES
        elif all(c.bao_cao is not None and c.bao_cao.nhan_xet is not None for c in row.cells):
            ly_do = _ALL_REVIEWED
        else:
            co_the_nop = True

    return TopicProgressOut(
        de_tai_id=topic.id,
        ten_de_tai=topic.ten_de_tai,
        sinh_vien=_sv_ref(topic.sinh_vien),
        giang_vien=_gv_ref(topic.giang_vien),
        dot_do_an=_cohort_ref(topic.dot_do_an),
        trang_thai_de_cuong=outline,
        moc=[_milestone_status(c) for c in row.cells],
        tre_moc=row.tre_moc,
        co_the_nop=co_the_nop,
        ly_do=ly_do,
        co_the_nhan_xet=(
            user.giang_vien_id is not None and topic.giang_vien_id == user.giang_vien_id
        ),
    )


# ---------------------------------------------------------------------------
# UC3.1 — mốc tiến độ (Bộ môn)
# ---------------------------------------------------------------------------
def _milestone_out(moc: MocTienDo, so_bao_cao: int = 0) -> MilestoneOut:
    return MilestoneOut(
        id=moc.id,
        dot_do_an_id=moc.dot_do_an_id,
        ten_moc=moc.ten_moc,
        thu_tu=moc.thu_tu,
        han_nop=moc.han_nop,
        so_bao_cao=so_bao_cao,
    )


def _report_counts(db: Session, moc_ids: list[int]) -> dict[int, int]:
    if not moc_ids:
        return {}
    rows = db.execute(
        select(BaoCaoTienDo.moc_tien_do_id, func.count())
        .where(BaoCaoTienDo.moc_tien_do_id.in_(moc_ids))
        .group_by(BaoCaoTienDo.moc_tien_do_id)
    ).all()
    return {moc_id: count for moc_id, count in rows}


def _cohort_or_default(db: Session, dot_do_an_id: int | None) -> DotDoAn | None:
    if dot_do_an_id is None:
        return dashboard_service._default_cohort(db)
    cohort = db.get(DotDoAn, dot_do_an_id)
    if cohort is None:
        raise HTTPException(status_code=404, detail=_COHORT_NOT_FOUND)
    return cohort


def list_milestones(db: Session, dot_do_an_id: int | None) -> list[MilestoneOut]:
    cohort = _cohort_or_default(db, dot_do_an_id)
    if cohort is None:
        return []
    milestones = _milestones_by_cohort(db, {cohort.id})[cohort.id]
    counts = _report_counts(db, [m.id for m in milestones])
    return [_milestone_out(m, counts.get(m.id, 0)) for m in milestones]


def _open_cohort_locked(db: Session, dot_do_an_id: int) -> DotDoAn:
    cohort = db.execute(
        select(DotDoAn).where(DotDoAn.id == dot_do_an_id).with_for_update()
    ).scalar_one_or_none()
    if cohort is None:
        raise HTTPException(status_code=404, detail=_COHORT_NOT_FOUND)
    if cohort.trang_thai != DANG_MO:
        raise HTTPException(status_code=409, detail=_COHORT_CLOSED)
    return cohort


def _check_han_nop(cohort: DotDoAn, han_nop: date) -> None:
    if han_nop < cohort.ngay_bat_dau or (
        cohort.ngay_ket_thuc is not None and han_nop > cohort.ngay_ket_thuc
    ):
        raise HTTPException(status_code=422, detail=_HAN_NOP_OUT_OF_RANGE)


def _get_milestone_or_404(db: Session, moc_id: int) -> MocTienDo:
    moc = db.get(MocTienDo, moc_id)
    if moc is None:
        raise HTTPException(status_code=404, detail=_MILESTONE_NOT_FOUND)
    return moc


def create_milestone(db: Session, payload: MilestoneIn) -> MilestoneOut:
    """Khóa dòng đợt để thu_tu = MAX + 1 không trùng khi hai lần thêm đồng thời."""
    cohort = _open_cohort_locked(db, payload.dot_do_an_id)
    _check_han_nop(cohort, payload.han_nop)
    max_thu_tu = db.execute(
        select(func.coalesce(func.max(MocTienDo.thu_tu), 0)).where(
            MocTienDo.dot_do_an_id == cohort.id
        )
    ).scalar_one()
    moc = MocTienDo(
        dot_do_an_id=cohort.id,
        ten_moc=payload.ten_moc,
        thu_tu=int(max_thu_tu) + 1,
        han_nop=payload.han_nop,
    )
    db.add(moc)
    db.commit()
    db.refresh(moc)
    return _milestone_out(moc)


def update_milestone(db: Session, moc_id: int, payload: MilestoneUpdate) -> MilestoneOut:
    moc = _get_milestone_or_404(db, moc_id)
    cohort = _open_cohort_locked(db, moc.dot_do_an_id)
    _check_han_nop(cohort, payload.han_nop)
    moc.ten_moc = payload.ten_moc
    moc.han_nop = payload.han_nop
    db.commit()
    db.refresh(moc)
    return _milestone_out(moc, _report_counts(db, [moc.id]).get(moc.id, 0))


def delete_milestone(db: Session, moc_id: int) -> None:
    moc = _get_milestone_or_404(db, moc_id)
    _open_cohort_locked(db, moc.dot_do_an_id)
    if _report_counts(db, [moc.id]).get(moc.id, 0) > 0:
        db.rollback()
        raise HTTPException(status_code=409, detail=_MILESTONE_HAS_REPORTS)
    db.delete(moc)
    db.commit()


# ---------------------------------------------------------------------------
# UC3.2 — SV nộp báo cáo
# ---------------------------------------------------------------------------
def _own_assigned_topic(db: Session, user: CurrentUser, *, lock: bool = False) -> DeTai | None:
    if user.sinh_vien_id is None:
        return None
    stmt = (
        select(DeTai)
        .where(DeTai.sinh_vien_id == user.sinh_vien_id)
        .where(DeTai.trang_thai == DA_PHAN_CONG)
        .order_by(DeTai.id.desc())
        .limit(1)
    )
    if lock:
        stmt = stmt.with_for_update()
    else:
        stmt = stmt.options(
            selectinload(DeTai.sinh_vien),
            selectinload(DeTai.giang_vien),
            selectinload(DeTai.dot_do_an),
        )
    return db.execute(stmt).scalars().first()


def my_progress(db: Session, user: CurrentUser) -> MyProgressOut:
    topic = _own_assigned_topic(db, user)
    if topic is None:
        return MyProgressOut(de_tai=None)
    return MyProgressOut(de_tai=_topic_view(db, user, topic))


def submit_report(
    db: Session, user: CurrentUser, moc_id: int, noi_dung: str, vf: ValidatedFile | None
) -> MyProgressOut:
    """Khóa đề tài của SV (FOR UPDATE) rồi dòng báo cáo hiện có (FOR UPDATE):
    nộp lại trước khi GVHD nhận xét → ghi đè cùng dòng (UC3.2 A1); đã nhận
    xét → 409. Tệp mới luôn là một phiên bản tai_lieu_do_an mới (D-02)."""
    topic = _own_assigned_topic(db, user, lock=True)
    if topic is None:
        raise HTTPException(status_code=409, detail=_NO_ASSIGNED_TOPIC)
    moc = db.get(MocTienDo, moc_id)
    if moc is None or moc.dot_do_an_id != topic.dot_do_an_id:
        db.rollback()
        raise HTTPException(status_code=404, detail=_MILESTONE_NOT_FOUND)
    if _outline_state(db, topic.id) != DC_DA_DUYET:
        db.rollback()
        raise HTTPException(status_code=409, detail=_OUTLINE_NOT_APPROVED)

    text = nfc(noi_dung or "").strip()
    if not text or len(text) > _NOI_DUNG_MAX:
        db.rollback()
        raise HTTPException(status_code=422, detail=_NOI_DUNG_INVALID)

    existing = db.execute(
        select(BaoCaoTienDo)
        .where(BaoCaoTienDo.de_tai_id == topic.id)
        .where(BaoCaoTienDo.moc_tien_do_id == moc.id)
        .with_for_update()
    ).scalar_one_or_none()
    if existing is not None and existing.nhan_xet is not None:
        db.rollback()
        raise HTTPException(status_code=409, detail=_ALREADY_REVIEWED)

    doc = None
    try:
        if vf is not None:
            doc = documents.store(db, de_tai_id=topic.id, loai=LOAI_BAO_CAO_TIEN_DO, vf=vf)
        now = now_utc()
        if existing is not None:
            existing.noi_dung = text
            existing.thoi_diem_nop = now
            if doc is not None:
                existing.tai_lieu_do_an_id = doc.id
        else:
            db.add(
                BaoCaoTienDo(
                    de_tai_id=topic.id,
                    moc_tien_do_id=moc.id,
                    noi_dung=text,
                    thoi_diem_nop=now,
                    tai_lieu_do_an_id=doc.id if doc is not None else None,
                )
            )
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        if doc is not None:
            documents.remove_file_quietly(doc.ten_luu_tru)
        raise HTTPException(status_code=409, detail=_SUBMIT_RACE) from None
    except Exception:
        db.rollback()
        if doc is not None:
            documents.remove_file_quietly(doc.ten_luu_tru)
        raise

    return my_progress(db, user)


# ---------------------------------------------------------------------------
# UC3.3 — GVHD xem và nhận xét
# ---------------------------------------------------------------------------
def list_students(db: Session, user: CurrentUser) -> list[StudentProgressItem]:
    if user.giang_vien_id is None:
        return []
    topics = (
        db.execute(
            select(DeTai)
            .outerjoin(SinhVien, SinhVien.id == DeTai.sinh_vien_id)
            .where(DeTai.giang_vien_id == user.giang_vien_id)
            .where(DeTai.trang_thai == DA_PHAN_CONG)
            .options(selectinload(DeTai.sinh_vien))
            .order_by(SinhVien.ma_so_sinh_vien, DeTai.id)
        )
        .scalars()
        .all()
    )
    rows = _build_rows(db, list(topics), today_vn())
    return [
        StudentProgressItem(
            de_tai_id=row.de_tai.id,
            ten_de_tai=row.de_tai.ten_de_tai,
            sinh_vien=_sv_ref(row.de_tai.sinh_vien),
            so_cho_nhan_xet=sum(
                1 for c in row.cells if c.bao_cao is not None and c.bao_cao.nhan_xet is None
            ),
            tre_moc=row.tre_moc,
        )
        for row in rows
    ]


def _can_view_topic(user: CurrentUser, topic: DeTai) -> bool:
    if user.vai_tro == VaiTro.BO_MON:
        return True
    if user.vai_tro == VaiTro.SINH_VIEN and user.sinh_vien_id is not None:
        return topic.sinh_vien_id == user.sinh_vien_id
    if user.vai_tro == VaiTro.GIANG_VIEN and user.giang_vien_id is not None:
        return topic.giang_vien_id == user.giang_vien_id
    return False


def topic_progress(db: Session, user: CurrentUser, de_tai_id: int) -> TopicProgressOut:
    topic = db.execute(
        select(DeTai)
        .where(DeTai.id == de_tai_id)
        .options(
            selectinload(DeTai.sinh_vien),
            selectinload(DeTai.giang_vien),
            selectinload(DeTai.dot_do_an),
        )
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND)
    if not _can_view_topic(user, topic):
        raise HTTPException(status_code=403, detail=_VIEW_FORBIDDEN)
    return _topic_view(db, user, topic)


def review_report(
    db: Session, user: CurrentUser, bao_cao_id: int, payload: ReviewIn
) -> TopicProgressOut:
    """Khóa dòng báo cáo (FOR UPDATE) — tuần tự hóa với một lần SV nộp lại
    đồng thời; thông báo cho SV trong CÙNG commit (D-08). Sửa nhận xét sau đó
    vẫn được phép và gửi lại thông báo."""
    bao_cao = db.execute(
        select(BaoCaoTienDo).where(BaoCaoTienDo.id == bao_cao_id).with_for_update()
    ).scalar_one_or_none()
    if bao_cao is None:
        raise HTTPException(status_code=404, detail=_REPORT_NOT_FOUND)
    topic = db.get(DeTai, bao_cao.de_tai_id)
    if user.giang_vien_id is None or topic is None or topic.giang_vien_id != user.giang_vien_id:
        db.rollback()
        raise HTTPException(status_code=403, detail=_REVIEW_FORBIDDEN)

    bao_cao.nhan_xet = payload.nhan_xet
    bao_cao.danh_gia = payload.danh_gia
    if topic.sinh_vien is not None:
        notifications.create(
            db,
            topic.sinh_vien.tai_khoan_id,
            TIEN_DO_NHAN_XET,
            f"GVHD đã nhận xét báo cáo {bao_cao.moc.ten_moc}: "
            f"{DANH_GIA_LABELS[payload.danh_gia]}",
            lien_ket="/tien-do",
        )
    db.commit()
    return topic_progress(db, user, topic.id)


# ---------------------------------------------------------------------------
# UC3.4 — Tiến độ toàn khoa (Bộ môn)
# ---------------------------------------------------------------------------
def row_out(r: ProgressRow) -> ProgressRowOut:
    """Một dòng SV × mốc — dùng chung cho /tien-do-toan-khoa và dashboard Bộ môn."""
    return ProgressRowOut(
        sinh_vien=_sv_ref(r.de_tai.sinh_vien),
        giang_vien=_gv_ref(r.de_tai.giang_vien),
        de_tai=TopicRef(id=r.de_tai.id, ten_de_tai=r.de_tai.ten_de_tai),
        o=[
            ProgressCellOut(
                moc_id=c.moc.id,
                trang_thai=c.trang_thai,
                bao_cao_id=c.bao_cao.id if c.bao_cao is not None else None,
            )
            for c in r.cells
        ],
        tre_moc=r.tre_moc,
    )


def dashboard(
    db: Session, dot_do_an_id: int | None, chi_tre_moc: bool, page: int, page_size: int
) -> ProgressDashboardOut:
    cohort = _cohort_or_default(db, dot_do_an_id)
    if cohort is None:
        return ProgressDashboardOut(
            dot_do_an=None, moc=[], items=[], total=0, page=page, page_size=page_size,
            so_sv_tre_moc=0,
        )
    milestones, rows = compute_cohort_progress(db, cohort.id)
    so_sv_tre_moc = sum(1 for r in rows if r.tre_moc)
    if chi_tre_moc:
        rows = [r for r in rows if r.tre_moc]
    total = len(rows)
    page_rows = rows[(page - 1) * page_size : page * page_size]
    counts = _report_counts(db, [m.id for m in milestones])

    return ProgressDashboardOut(
        dot_do_an=_cohort_ref(cohort),
        moc=[_milestone_out(m, counts.get(m.id, 0)) for m in milestones],
        items=[row_out(r) for r in page_rows],
        total=total,
        page=page,
        page_size=page_size,
        so_sv_tre_moc=so_sv_tre_moc,
    )
