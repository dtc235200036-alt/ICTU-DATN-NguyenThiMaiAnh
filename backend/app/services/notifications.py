"""Thông báo in-app dùng chung cho toàn Phase 3 (D-08, UC0.5). `create()`
KHÔNG BAO GIỜ commit — luôn được gọi bởi service khác, trong CÙNG transaction
với thay đổi trạng thái mà nó loan báo (title_check.luu_ket_qua's add+flush
pattern)."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.timeutil import now_utc
from app.models.thong_bao import ThongBao
from app.schemas.notifications import NotificationOut, NotificationPage


def create(
    db: Session,
    tai_khoan_id: int,
    loai: str,
    noi_dung: str,
    lien_ket: str | None = None,
) -> ThongBao:
    tb = ThongBao(
        tai_khoan_id=tai_khoan_id,
        loai=loai,
        noi_dung=noi_dung,
        lien_ket=lien_ket,
        da_doc=False,
        thoi_diem=now_utc(),
    )
    db.add(tb)
    db.flush()
    return tb


def list_for_user(
    db: Session, user: CurrentUser, page: int, page_size: int
) -> NotificationPage:
    """UC0.5/T-03-08: chỉ thông báo của chính người gọi (không tham số id)."""
    own = ThongBao.tai_khoan_id == user.tai_khoan_id
    stmt = select(ThongBao).where(own)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    chua_doc = db.execute(
        select(func.count())
        .select_from(ThongBao)
        .where(own)
        .where(ThongBao.da_doc.is_(False))
    ).scalar_one()

    rows = (
        db.execute(
            stmt.order_by(ThongBao.thoi_diem.desc(), ThongBao.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    items = [
        NotificationOut(
            id=row.id,
            loai=row.loai,
            noi_dung=row.noi_dung,
            lien_ket=row.lien_ket,
            da_doc=row.da_doc,
            thoi_diem=row.thoi_diem,
        )
        for row in rows
    ]
    return NotificationPage(
        items=items, total=total, page=page, page_size=page_size, chua_doc=chua_doc
    )
