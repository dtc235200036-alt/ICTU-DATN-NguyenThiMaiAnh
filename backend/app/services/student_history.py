"""Lịch sử đề tài (mọi vai trò xem được đề tài) và "Lịch sử nộp" của sinh viên —
tổng hợp từ các bảng sẵn có, không lưu bảng riêng."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import CurrentUser
from app.models.de_cuong import (
    DC_CHUA_NOP,
    KET_QUA_DA_DUYET,
    LOAI_BAO_CAO_CUOI,
    LOAI_DE_CUONG,
    LOAI_DE_TAI,
    DeCuong,
    LuotDuyetBoMon,
    LuotDuyetDeCuong,
    TaiLieuDoAn,
)
from app.models.de_tai import DA_PHAN_CONG, DeTai
from app.models.tien_do import BaoCaoTienDo
from app.schemas.history import SubmissionRow, TopicEvent
from app.services import progress, title_check
from app.services import topics as topics_service

_TOPIC_NOT_FOUND = "Không tìm thấy đề tài"
_FORBIDDEN = "Bạn không có quyền xem đề tài này"

_DE_CUONG_LABEL = {
    "CHUA_NOP": "Chưa nộp",
    "CHO_DUYET": "Chờ GVHD duyệt",
    "YEU_CAU_SUA": "Yêu cầu sửa",
    "GVHD_DA_DUYET": "GVHD đã duyệt",
    "CHO_BO_MON_DUYET": "Chờ Bộ môn duyệt",
    "DA_DUYET": "Đã duyệt",
}
_MOC_LABEL = {
    "DUNG_HAN": "Đúng hạn",
    "NOP_TRE": "Nộp trễ",
    "TRE_MOC": "Trễ mốc",
    "CHUA_DEN_HAN": "Chưa nộp",
}


def _topic_or_error(db: Session, user: CurrentUser, topic_id: int) -> DeTai:
    topic = db.execute(
        select(DeTai)
        .where(DeTai.id == topic_id)
        .options(selectinload(DeTai.sinh_vien), selectinload(DeTai.giang_vien))
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=_TOPIC_NOT_FOUND)
    if not topics_service.can_view(db, user, topic):
        raise HTTPException(status_code=403, detail=_FORBIDDEN)
    return topic


def _docs(db: Session, topic_id: int, loai: str) -> list[TaiLieuDoAn]:
    return list(
        db.execute(
            select(TaiLieuDoAn)
            .where(TaiLieuDoAn.de_tai_id == topic_id)
            .where(TaiLieuDoAn.loai == loai)
            .order_by(TaiLieuDoAn.so_phien_ban)
        )
        .scalars()
        .all()
    )


def topic_history(db: Session, user: CurrentUser, topic_id: int) -> list[TopicEvent]:
    topic = _topic_or_error(db, user, topic_id)
    sv = (topic.sinh_vien.ho_ten if topic.sinh_vien else None) or "Sinh viên"
    gv = (topic.giang_vien.ho_ten if topic.giang_vien else None) or "GVHD"
    events: list[TopicEvent] = []

    giao = title_check.latest_title_check(db, topic.id)
    if giao is not None and topic.trang_thai == DA_PHAN_CONG:
        events.append(TopicEvent(thoi_diem=giao.thoi_diem, noi_dung="Giao đề tài cho sinh viên", nguoi_thuc_hien=gv))
    for doc in _docs(db, topic.id, LOAI_DE_TAI):
        events.append(
            TopicEvent(thoi_diem=doc.thoi_diem_nop, noi_dung=f"Đính kèm file {doc.ten_goc}", nguoi_thuc_hien=gv)
        )
    for doc in _docs(db, topic.id, LOAI_DE_CUONG):
        events.append(
            TopicEvent(
                thoi_diem=doc.thoi_diem_nop,
                noi_dung=f"Nộp đề cương phiên bản {doc.so_phien_ban}",
                nguoi_thuc_hien=sv,
            )
        )

    de_cuong = db.execute(select(DeCuong).where(DeCuong.de_tai_id == topic.id)).scalar_one_or_none()
    if de_cuong is not None:
        for lv in db.execute(
            select(LuotDuyetDeCuong)
            .where(LuotDuyetDeCuong.de_cuong_id == de_cuong.id)
            .options(selectinload(LuotDuyetDeCuong.tai_lieu))
        ).scalars():
            ver = lv.tai_lieu.so_phien_ban if lv.tai_lieu else "?"
            if lv.ket_qua == KET_QUA_DA_DUYET:
                noi_dung = f"GVHD duyệt đề cương phiên bản {ver}"
            else:
                noi_dung = f"GVHD yêu cầu sửa đề cương phiên bản {ver}"
            if lv.nhan_xet:
                noi_dung += f": {lv.nhan_xet}"
            events.append(TopicEvent(thoi_diem=lv.thoi_diem, noi_dung=noi_dung, nguoi_thuc_hien=gv))
        if de_cuong.nop_bo_mon_luc is not None:
            events.append(
                TopicEvent(
                    thoi_diem=de_cuong.nop_bo_mon_luc,
                    noi_dung="Nộp đề cương lên Bộ môn",
                    nguoi_thuc_hien=gv,
                )
            )
        for bm in db.execute(
            select(LuotDuyetBoMon).where(LuotDuyetBoMon.de_cuong_id == de_cuong.id)
        ).scalars():
            if bm.ket_qua == KET_QUA_DA_DUYET:
                noi_dung = "Bộ môn phê duyệt đề cương, nộp về khoa"
            else:
                noi_dung = "Bộ môn trả lại đề cương"
            if bm.nhan_xet:
                noi_dung += f": {bm.nhan_xet}"
            events.append(TopicEvent(thoi_diem=bm.thoi_diem, noi_dung=noi_dung, nguoi_thuc_hien="Bộ môn"))

    for bc in db.execute(
        select(BaoCaoTienDo).where(BaoCaoTienDo.de_tai_id == topic.id).options(selectinload(BaoCaoTienDo.moc))
    ).scalars():
        events.append(
            TopicEvent(
                thoi_diem=bc.thoi_diem_nop,
                noi_dung=f"Nộp báo cáo tiến độ — {bc.moc.ten_moc}",
                nguoi_thuc_hien=sv,
            )
        )
    for doc in _docs(db, topic.id, LOAI_BAO_CAO_CUOI):
        events.append(
            TopicEvent(
                thoi_diem=doc.thoi_diem_nop,
                noi_dung=f"Nộp báo cáo cuối phiên bản {doc.so_phien_ban}",
                nguoi_thuc_hien=sv,
            )
        )
    # DATETIME chỉ tới giây: hai sự kiện cùng giây giữ thứ tự nghiệp vụ (sự kiện
    # thêm sau xếp trên) — sắp theo (thời điểm, thứ tự thêm) giảm dần.
    order = {id(e): i for i, e in enumerate(events)}
    events.sort(key=lambda e: (e.thoi_diem, order[id(e)]), reverse=True)
    return events


def my_submissions(db: Session, user: CurrentUser) -> list[SubmissionRow]:
    """"Lịch sử nộp" của SV: nhận đề tài, các phiên bản đề cương, báo cáo tiến độ
    theo mốc (kể cả mốc chưa nộp, kèm hạn cuối) và báo cáo cuối."""
    if user.sinh_vien_id is None:
        return []
    topic = db.execute(
        select(DeTai)
        .where(DeTai.sinh_vien_id_dang_hoat_dong == user.sinh_vien_id)
        .limit(1)
    ).scalar_one_or_none()
    if topic is None:
        return []

    rows: list[SubmissionRow] = []
    giao = title_check.latest_title_check(db, topic.id)
    rows.append(
        SubmissionRow(
            loai="DE_TAI",
            noi_dung=f"Nhận đề tài: {topic.ten_de_tai}",
            thoi_diem_nop=giao.thoi_diem if giao is not None else None,
            trang_thai=topic.trang_thai,
            trang_thai_label="Đã giao" if topic.trang_thai == DA_PHAN_CONG else "Chưa giao",
        )
    )

    de_cuong = db.execute(select(DeCuong).where(DeCuong.de_tai_id == topic.id)).scalar_one_or_none()
    outline_docs = _docs(db, topic.id, LOAI_DE_CUONG)
    reviews = {}
    if de_cuong is not None:
        reviews = {
            lv.tai_lieu_do_an_id: lv.ket_qua
            for lv in db.execute(
                select(LuotDuyetDeCuong).where(LuotDuyetDeCuong.de_cuong_id == de_cuong.id)
            ).scalars()
        }
    if not outline_docs:
        rows.append(
            SubmissionRow(
                loai="DE_CUONG",
                noi_dung="Nộp đề cương",
                trang_thai=DC_CHUA_NOP,
                trang_thai_label=_DE_CUONG_LABEL[DC_CHUA_NOP],
            )
        )
    for idx, doc in enumerate(outline_docs):
        newest = idx == len(outline_docs) - 1
        if newest and de_cuong is not None:
            trang_thai = de_cuong.trang_thai
        else:
            trang_thai = "GVHD_DA_DUYET" if reviews.get(doc.id) == KET_QUA_DA_DUYET else "YEU_CAU_SUA"
        rows.append(
            SubmissionRow(
                loai="DE_CUONG",
                noi_dung=f"Nộp đề cương (phiên bản {doc.so_phien_ban})",
                thoi_diem_nop=doc.thoi_diem_nop,
                trang_thai=trang_thai,
                trang_thai_label=_DE_CUONG_LABEL.get(trang_thai, trang_thai),
                tai_lieu_id=doc.id,
            )
        )

    my = progress.my_progress(db, user).de_tai
    if my is not None:
        for m in my.moc:
            rows.append(
                SubmissionRow(
                    loai="TIEN_DO",
                    noi_dung=f"Báo cáo tiến độ — {m.ten_moc}",
                    thoi_diem_nop=m.bao_cao.thoi_diem_nop if m.bao_cao else None,
                    han_cuoi=m.han_nop,
                    trang_thai=m.trang_thai,
                    trang_thai_label=_MOC_LABEL.get(m.trang_thai, m.trang_thai)
                    if m.bao_cao is None or m.trang_thai != "CHUA_DEN_HAN"
                    else "Đã nộp",
                    tai_lieu_id=m.bao_cao.tep.id if m.bao_cao and m.bao_cao.tep else None,
                )
            )

    for doc in _docs(db, topic.id, LOAI_BAO_CAO_CUOI):
        rows.append(
            SubmissionRow(
                loai="BAO_CAO_CUOI",
                noi_dung=f"Nộp báo cáo cuối (phiên bản {doc.so_phien_ban})",
                thoi_diem_nop=doc.thoi_diem_nop,
                trang_thai="DA_NOP",
                trang_thai_label="Đã nộp",
                tai_lieu_id=doc.id,
            )
        )
    return rows
