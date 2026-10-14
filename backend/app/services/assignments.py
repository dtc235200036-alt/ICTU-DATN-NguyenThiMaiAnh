"""UC0.8 — Phân công GVHD: đầu đợt Bộ môn gán mỗi SV cho đúng MỘT GVHD
(uk_phan_cong_sv_dot); từ đó chỉ GVHD của SV tạo và giao đề tài cho SV đó
(góp ý GVHD mục 1: SV không tự đề xuất/đăng ký đề tài).

Đổi/gỡ GVHD của một SV chỉ bị chặn khi SV đã có đề tài Đã phân công trong đợt
(đề cương/tiến độ/bảo vệ đều bám de_tai.giang_vien_id). Bản nháp của GV cũ định
giao cho SV đó được gỡ SV."""
import csv
import io
from collections import Counter

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.timeutil import now_utc
from app.models.de_tai import DA_PHAN_CONG, GIANG_VIEN, NHAP, DeTai
from app.models.dot_do_an import DANG_MO, DotDoAn
from app.models.phan_cong import PhanCongHuongDan
from app.models.tai_khoan import GiangVien, SinhVien, TaiKhoan
from app.models.thong_bao import PHAN_CONG_GVHD
from app.schemas.assignments import (
    AssignmentItem,
    AssignmentPage,
    AssignmentResult,
    AssignmentRow,
    LecturerLoad,
    MyAdvisorOut,
    MyStudentItem,
    MyStudentsOut,
)
from app.schemas.common import nfc
from app.schemas.topics import CohortRef, PersonRef
from app.services import notifications

_COHORT_NOT_FOUND_DETAIL = "Không tìm thấy đợt đồ án"
NOT_ASSIGNED_DETAIL = "Bạn chưa được Bộ môn phân công giảng viên hướng dẫn trong đợt này"


def _cohort_or_404(db: Session, dot_do_an_id: int) -> DotDoAn:
    cohort = db.get(DotDoAn, dot_do_an_id)
    if cohort is None:
        raise HTTPException(status_code=404, detail=_COHORT_NOT_FOUND_DETAIL)
    return cohort


def _cohort_ref(c: DotDoAn) -> CohortRef:
    return CohortRef(id=c.id, ten_dot=c.ten_dot, khoa=c.khoa, trang_thai=c.trang_thai)


def _sv_ref(sv: SinhVien) -> PersonRef:
    return PersonRef(id=sv.id, ho_ten=sv.ho_ten or "", ma=sv.ma_so_sinh_vien)


def _gv_ref(gv: GiangVien) -> PersonRef:
    return PersonRef(id=gv.id, ho_ten=gv.ho_ten or "", ma=gv.ma_giang_vien)


def _gv_label(gv: GiangVien) -> str:
    return " ".join(part for part in (gv.hoc_vi, gv.ho_ten) if part)


def gvhd_id(db: Session, dot_do_an_id: int, sinh_vien_id: int | None) -> int | None:
    """GVHD của SV trong đợt, hoặc None nếu SV chưa được phân công."""
    if sinh_vien_id is None:
        return None
    return db.execute(
        select(PhanCongHuongDan.giang_vien_id)
        .where(PhanCongHuongDan.dot_do_an_id == dot_do_an_id)
        .where(PhanCongHuongDan.sinh_vien_id == sinh_vien_id)
    ).scalar_one_or_none()


def advisor_pairs(db: Session, sinh_vien_id: int | None) -> set[tuple[int, int]]:
    """Mọi cặp (đợt, GVHD) của một SV — một truy vấn cho cả trang danh sách."""
    if sinh_vien_id is None:
        return set()
    rows = db.execute(
        select(PhanCongHuongDan.dot_do_an_id, PhanCongHuongDan.giang_vien_id).where(
            PhanCongHuongDan.sinh_vien_id == sinh_vien_id
        )
    ).all()
    return {(dot, gv) for dot, gv in rows}


def is_advisor_of(db: Session, giang_vien_id: int | None, dot_do_an_id: int, sinh_vien_id: int) -> bool:
    return giang_vien_id is not None and gvhd_id(db, dot_do_an_id, sinh_vien_id) == giang_vien_id


def _active_topics(
    db: Session, dot_do_an_id: int, sv_ids: list[int], lock: bool = False
) -> dict[int, DeTai]:
    if not sv_ids:
        return {}
    stmt = (
        select(DeTai)
        .where(DeTai.dot_do_an_id == dot_do_an_id)
        .where(DeTai.sinh_vien_id_dang_hoat_dong.in_(sv_ids))
    )
    if lock:
        stmt = stmt.with_for_update()
    return {t.sinh_vien_id: t for t in db.execute(stmt).scalars().all()}


def list_for_cohort(
    db: Session,
    dot_do_an_id: int,
    q: str | None,
    giang_vien_id: int | None,
    loc: str,
    page: int,
    page_size: int,
) -> AssignmentPage:
    """MH-15: mọi SV (tài khoản chưa khóa) kèm GVHD trong đợt, lọc theo từ khóa
    / GVHD / đã-chưa phân công; kèm tải (số SV) của từng GV đang hoạt động."""
    _cohort_or_404(db, dot_do_an_id)

    pc_join = (PhanCongHuongDan.sinh_vien_id == SinhVien.id) & (
        PhanCongHuongDan.dot_do_an_id == dot_do_an_id
    )
    stmt = (
        select(SinhVien, PhanCongHuongDan)
        .join(TaiKhoan, TaiKhoan.id == SinhVien.tai_khoan_id)
        .outerjoin(PhanCongHuongDan, pc_join)
        .where(TaiKhoan.bi_khoa.is_(False))
    )
    if q:
        needle = nfc(q)
        stmt = stmt.where(
            or_(
                SinhVien.ho_ten.contains(needle, autoescape=True),
                SinhVien.ma_so_sinh_vien.contains(needle, autoescape=True),
                SinhVien.lop.contains(needle, autoescape=True),
            )
        )
    if giang_vien_id is not None:
        stmt = stmt.where(PhanCongHuongDan.giang_vien_id == giang_vien_id)
    if loc == "da_phan_cong":
        stmt = stmt.where(PhanCongHuongDan.id.is_not(None))
    elif loc == "chua_phan_cong":
        stmt = stmt.where(PhanCongHuongDan.id.is_(None))

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(
        stmt.order_by(SinhVien.ma_so_sinh_vien.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    gv_ids = {pc.giang_vien_id for _, pc in rows if pc is not None}
    gvs = (
        {gv.id: gv for gv in db.execute(select(GiangVien).where(GiangVien.id.in_(gv_ids))).scalars()}
        if gv_ids
        else {}
    )
    topics = _active_topics(db, dot_do_an_id, [sv.id for sv, _ in rows])

    items = []
    for sv, pc in rows:
        topic = topics.get(sv.id)
        items.append(
            AssignmentRow(
                sinh_vien=_sv_ref(sv),
                lop=sv.lop,
                giang_vien=_gv_ref(gvs[pc.giang_vien_id]) if pc is not None else None,
                de_tai_id=topic.id if topic is not None else None,
                ten_de_tai=topic.ten_de_tai if topic is not None else None,
                trang_thai_de_tai=topic.trang_thai if topic is not None else None,
                doi_duoc=topic is None or topic.trang_thai != DA_PHAN_CONG,
            )
        )

    tong_sinh_vien = db.execute(
        select(func.count())
        .select_from(SinhVien)
        .join(TaiKhoan, TaiKhoan.id == SinhVien.tai_khoan_id)
        .where(TaiKhoan.bi_khoa.is_(False))
    ).scalar_one()
    da_phan_cong = db.execute(
        select(func.count())
        .select_from(PhanCongHuongDan)
        .where(PhanCongHuongDan.dot_do_an_id == dot_do_an_id)
    ).scalar_one()

    so_sv = (
        select(func.count(PhanCongHuongDan.id))
        .where(PhanCongHuongDan.giang_vien_id == GiangVien.id)
        .where(PhanCongHuongDan.dot_do_an_id == dot_do_an_id)
        .correlate(GiangVien)
        .scalar_subquery()
    )
    tai = [
        LecturerLoad(giang_vien=_gv_ref(gv), hoc_vi=gv.hoc_vi, so_sinh_vien=n)
        for gv, n in db.execute(
            select(GiangVien, so_sv)
            .join(TaiKhoan, TaiKhoan.id == GiangVien.tai_khoan_id)
            .where(TaiKhoan.bi_khoa.is_(False))
            .order_by(GiangVien.ho_ten.asc())
        ).all()
    ]

    return AssignmentPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        tong_sinh_vien=tong_sinh_vien,
        da_phan_cong=da_phan_cong,
        tai_giang_vien=tai,
    )


def _apply(
    db: Session, cohort: DotDoAn, items: list[AssignmentItem]
) -> tuple[int, list[str]]:
    """Ghi các phân công hợp lệ (chưa commit), trả (số dòng đổi, lỗi từng SV).
    Khóa các dòng phân công + đề tài đang hoạt động của các SV liên quan để
    không đua với SV đang gửi/đăng ký đề tài cùng lúc."""
    last: dict[int, int | None] = {}
    for item in items:
        last[item.sinh_vien_id] = item.giang_vien_id  # dòng sau cùng thắng
    sv_ids = list(last)

    svs = {sv.id: sv for sv in db.execute(select(SinhVien).where(SinhVien.id.in_(sv_ids))).scalars()}
    wanted_gv = {gv for gv in last.values() if gv is not None}
    gvs = (
        {
            gv.id: gv
            for gv in db.execute(
                select(GiangVien)
                .join(TaiKhoan, TaiKhoan.id == GiangVien.tai_khoan_id)
                .where(GiangVien.id.in_(wanted_gv))
                .where(TaiKhoan.bi_khoa.is_(False))
            ).scalars()
        }
        if wanted_gv
        else {}
    )
    current = {
        pc.sinh_vien_id: pc
        for pc in db.execute(
            select(PhanCongHuongDan)
            .where(PhanCongHuongDan.dot_do_an_id == cohort.id)
            .where(PhanCongHuongDan.sinh_vien_id.in_(sv_ids))
            .with_for_update()
        ).scalars()
    }
    topics = _active_topics(db, cohort.id, sv_ids, lock=True)

    errors: list[str] = []
    changed = 0
    per_gv: Counter[int] = Counter()
    now = now_utc()
    for sv_id, gv_id in last.items():
        sv = svs.get(sv_id)
        if sv is None:
            errors.append(f"Sinh viên #{sv_id} không tồn tại")
            continue
        label = f"{sv.ma_so_sinh_vien} {sv.ho_ten or ''}".strip()
        if gv_id is not None and gv_id not in gvs:
            errors.append(f"{label}: giảng viên không tồn tại hoặc đã bị khóa")
            continue
        pc = current.get(sv_id)
        old_gv = pc.giang_vien_id if pc is not None else None
        if old_gv == gv_id:
            continue
        topic = topics.get(sv_id)
        if topic is not None and topic.trang_thai == DA_PHAN_CONG:
            errors.append(f"{label}: đã có đề tài Đã phân công — không đổi được GVHD")
            continue

        # Nháp GV cũ định giao cho SV này gỡ SV (GVHD mới chọn lại khi giao đề tài).
        # Đề tài Chờ duyệt / nháp SV là trạng thái cũ, hệ thống không còn tạo ra.
        for draft in db.execute(
            select(DeTai)
            .where(DeTai.dot_do_an_id == cohort.id)
            .where(DeTai.sinh_vien_id == sv_id)
            .where(DeTai.trang_thai == NHAP)
        ).scalars():
            if draft.loai_nguoi_de_xuat == GIANG_VIEN and draft.giang_vien_id == old_gv:
                draft.sinh_vien_id = None

        if gv_id is None:
            db.delete(pc)
            notifications.create(
                db,
                sv.tai_khoan_id,
                PHAN_CONG_GVHD,
                f"Bạn chưa có giảng viên hướng dẫn trong '{cohort.ten_dot}' (Bộ môn đã gỡ phân công)",
                lien_ket="/tong-quan",
            )
        else:
            if pc is None:
                db.add(
                    PhanCongHuongDan(
                        dot_do_an_id=cohort.id,
                        sinh_vien_id=sv_id,
                        giang_vien_id=gv_id,
                        thoi_diem=now,
                    )
                )
            else:
                pc.giang_vien_id = gv_id
                pc.thoi_diem = now
            per_gv[gv_id] += 1
            notifications.create(
                db,
                sv.tai_khoan_id,
                PHAN_CONG_GVHD,
                f"Giảng viên hướng dẫn của bạn trong '{cohort.ten_dot}': {_gv_label(gvs[gv_id])}",
                lien_ket="/tong-quan",
            )
        changed += 1

    for gv_id, n in per_gv.items():
        notifications.create(
            db,
            gvs[gv_id].tai_khoan_id,
            PHAN_CONG_GVHD,
            f"Bạn được phân công hướng dẫn thêm {n} sinh viên trong '{cohort.ten_dot}'",
            lien_ket="/sinh-vien-huong-dan",
        )
    db.flush()
    return changed, errors


def update(db: Session, dot_do_an_id: int, items: list[AssignmentItem]) -> AssignmentResult:
    """Lưu từ màn hình: tất cả hoặc không — có lỗi thì 409 kèm danh sách lỗi."""
    cohort = _cohort_or_404(db, dot_do_an_id)
    changed, errors = _apply(db, cohort, items)
    if errors:
        db.rollback()
        raise HTTPException(status_code=409, detail="; ".join(errors))
    db.commit()
    return AssignmentResult(cap_nhat=changed)


def import_csv(db: Session, dot_do_an_id: int, noi_dung: str) -> AssignmentResult:
    """Import `ma_so_sinh_vien,ma_giang_vien` (dấu phẩy hoặc chấm phẩy): ghi
    các dòng hợp lệ, trả lỗi của các dòng còn lại (không tìm thấy mã, …)."""
    cohort = _cohort_or_404(db, dot_do_an_id)
    text = noi_dung.lstrip("﻿")
    delimiter = ";" if text.count(";") > text.count(",") else ","
    pairs: list[tuple[int, str, str]] = []
    for lineno, row in enumerate(csv.reader(io.StringIO(text), delimiter=delimiter), start=1):
        cells = [c.strip() for c in row]
        if len(cells) < 2 or not cells[0]:
            continue
        pairs.append((lineno, cells[0], cells[1]))

    sv_by_ma = {
        sv.ma_so_sinh_vien: sv.id
        for sv in db.execute(
            select(SinhVien).where(SinhVien.ma_so_sinh_vien.in_({p[1] for p in pairs}))
        ).scalars()
    }
    gv_by_ma = {
        gv.ma_giang_vien: gv.id
        for gv in db.execute(
            select(GiangVien).where(GiangVien.ma_giang_vien.in_({p[2] for p in pairs if p[2]}))
        ).scalars()
    }

    errors: list[str] = []
    items: list[AssignmentItem] = []
    for lineno, ma_sv, ma_gv in pairs:
        sv_id = sv_by_ma.get(ma_sv)
        if sv_id is None:
            if lineno > 1:  # dòng 1 không khớp mã nào = dòng tiêu đề
                errors.append(f"Dòng {lineno}: không tìm thấy sinh viên '{ma_sv}'")
            continue
        gv_id = gv_by_ma.get(ma_gv)
        if gv_id is None:
            errors.append(f"Dòng {lineno}: không tìm thấy giảng viên '{ma_gv}'")
            continue
        items.append(AssignmentItem(sinh_vien_id=sv_id, giang_vien_id=gv_id))

    changed = 0
    if items:
        changed, apply_errors = _apply(db, cohort, items)
        errors.extend(apply_errors)
    db.commit()
    return AssignmentResult(cap_nhat=changed, loi=errors)


def _default_cohorts(db: Session, dot_do_an_id: int | None) -> list[DotDoAn]:
    if dot_do_an_id is not None:
        return [_cohort_or_404(db, dot_do_an_id)]
    return list(
        db.execute(
            select(DotDoAn).where(DotDoAn.trang_thai == DANG_MO).order_by(DotDoAn.id.desc())
        ).scalars()
    )


def my_students(db: Session, user: CurrentUser, dot_do_an_id: int | None) -> list[MyStudentsOut]:
    """MH-16: lớp hướng dẫn của GV gọi, theo đợt (mặc định mọi đợt đang mở) —
    mỗi SV kèm đề tài đang hoạt động hoặc gần nhất trong đợt."""
    out: list[MyStudentsOut] = []
    for cohort in _default_cohorts(db, dot_do_an_id):
        svs = (
            db.execute(
                select(SinhVien)
                .join(PhanCongHuongDan, PhanCongHuongDan.sinh_vien_id == SinhVien.id)
                .where(PhanCongHuongDan.dot_do_an_id == cohort.id)
                .where(PhanCongHuongDan.giang_vien_id == user.giang_vien_id)
                .order_by(SinhVien.ma_so_sinh_vien.asc())
            )
            .scalars()
            .all()
        )
        latest: dict[int, DeTai] = {}
        if svs:
            for t in db.execute(
                select(DeTai)
                .where(DeTai.dot_do_an_id == cohort.id)
                .where(DeTai.sinh_vien_id.in_([sv.id for sv in svs]))
                .order_by(DeTai.id.asc())
            ).scalars():
                # Đề tài đang hoạt động thắng; còn lại lấy đề tài mới nhất. Bỏ
                # nháp GV định giao (SV chưa thấy) và nháp SV (GVHD chưa thấy).
                if t.trang_thai == NHAP:
                    continue
                cur = latest.get(t.sinh_vien_id)
                if cur is None or cur.sinh_vien_id_dang_hoat_dong is None:
                    latest[t.sinh_vien_id] = t
        items = []
        for sv in svs:
            t = latest.get(sv.id)
            items.append(
                MyStudentItem(
                    sinh_vien=_sv_ref(sv),
                    lop=sv.lop,
                    email=sv.email,
                    de_tai_id=t.id if t is not None else None,
                    ten_de_tai=t.ten_de_tai if t is not None else None,
                    trang_thai_de_tai=t.trang_thai if t is not None else None,
                )
            )
        out.append(MyStudentsOut(dot_do_an=_cohort_ref(cohort), items=items))
    return out


def my_advisors(db: Session, user: CurrentUser) -> list[MyAdvisorOut]:
    """SV xem GVHD của mình ở mọi đợt (đợt mới nhất trước)."""
    rows = db.execute(
        select(PhanCongHuongDan, DotDoAn, GiangVien)
        .join(DotDoAn, DotDoAn.id == PhanCongHuongDan.dot_do_an_id)
        .join(GiangVien, GiangVien.id == PhanCongHuongDan.giang_vien_id)
        .where(PhanCongHuongDan.sinh_vien_id == user.sinh_vien_id)
        .order_by(DotDoAn.id.desc())
    ).all()
    return [
        MyAdvisorOut(
            dot_do_an=_cohort_ref(cohort),
            giang_vien=_gv_ref(gv),
            hoc_vi=gv.hoc_vi,
            email=gv.email,
            thoi_diem=pc.thoi_diem,
        )
        for pc, cohort, gv in rows
    ]
