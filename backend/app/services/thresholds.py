"""UC0.4/AISV-07 (D-04): đọc và cập nhật ngưỡng cảnh báo trùng lặp.

KHÔNG cache: title_check (NGUONG_TEN_DE_TAI) và document_check
(NGUONG_TAI_LIEU khi tạo kết quả chờ, NGUONG_DOAN_TRUNG khi chạy) đọc lại chính
các dòng cau_hinh_nguong này ở mỗi request — vì vậy "lần kiểm tra kế tiếp dùng
giá trị mới", còn kết quả đã ghi giữ snapshot nguong_ap_dung của nó.
"""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.timeutil import now_utc
from app.models.cau_hinh_nguong import (
    NGUONG_DOAN_TRUNG,
    NGUONG_TAI_LIEU,
    NGUONG_TEN_DE_TAI,
    CauHinhNguong,
)
from app.models.tai_khoan import TaiKhoan
from app.schemas.thresholds import ThresholdOut, ThresholdUpdate


@dataclass(frozen=True)
class _Definition:
    loai: str
    nhan: str
    mo_ta: str
    gia_tri_de_xuat: float


# Giá trị đề xuất = giá trị hiệu chỉnh ghi ở Alembic 0010, lấy từ
# ai-service/calibration/nguong-de-xuat.json (tập HIEU_CHINH, profile bkai,
# 2026-09-28 — plan 04-04). Hiệu chỉnh lại thì cập nhật cả hai nơi.
DEFINITIONS: tuple[_Definition, ...] = (
    _Definition(
        NGUONG_TEN_DE_TAI,
        "Ngưỡng tên đề tài",
        "Khi đề xuất/đăng ký đề tài, các đề tài và đồ án trong kho có độ tương đồng"
        " ngữ nghĩa về tên từ giá trị này trở lên được liệt kê để cảnh báo.",
        67.80,
    ),
    _Definition(
        NGUONG_TAI_LIEU,
        "Ngưỡng cảnh báo tài liệu (tỷ lệ trùng với một đồ án)",
        "Đề cương/báo cáo có phần trùng với MỘT đồ án nguồn chiếm từ giá trị này"
        " trở lên được hiển thị \"Vượt ngưỡng cảnh báo\" cho GVHD và sinh viên."
        " Tỷ lệ tổng (cộng mọi nguồn) chỉ để tham khảo: các câu khớp rải rác với"
        " nhiều đồ án cùng lĩnh vực không bị coi là sao chép.",
        10.40,
    ),
    _Definition(
        NGUONG_DOAN_TRUNG,
        "Ngưỡng đoạn trùng (độ tương đồng ngữ nghĩa)",
        "Một câu trong tài liệu nộp có độ tương đồng ngữ nghĩa với đồ án đã lưu từ"
        " giá trị này trở lên được tính là đoạn trùng.",
        67.70,
    ),
)


def _display_name(account: TaiKhoan | None) -> str | None:
    """Cùng quy tắc với deps.get_current_user: họ tên SV/GV, không có thì email."""
    if account is None:
        return None
    if account.sinh_vien is not None and account.sinh_vien.ho_ten:
        return account.sinh_vien.ho_ten
    if account.giang_vien is not None and account.giang_vien.ho_ten:
        return account.giang_vien.ho_ten
    return account.email


def list_thresholds(db: Session) -> list[ThresholdOut]:
    rows = {
        row.loai: row
        for row in db.execute(
            select(CauHinhNguong).where(
                CauHinhNguong.loai.in_([d.loai for d in DEFINITIONS])
            )
        ).scalars()
    }
    out: list[ThresholdOut] = []
    for d in DEFINITIONS:
        row = rows.get(d.loai)
        if row is None:
            # IN-02 (04-REVIEW): dòng còn thiếu vẫn được liệt kê với giá trị đề
            # xuất, để form có đủ ba trường và PUT (bắt buộc cả ba) chèn dòng.
            out.append(
                ThresholdOut(
                    loai=d.loai,
                    nhan=d.nhan,
                    mo_ta=d.mo_ta,
                    gia_tri=d.gia_tri_de_xuat,
                    gia_tri_de_xuat=d.gia_tri_de_xuat,
                )
            )
            continue
        out.append(
            ThresholdOut(
                loai=d.loai,
                nhan=d.nhan,
                mo_ta=d.mo_ta,
                gia_tri=float(row.gia_tri),
                gia_tri_de_xuat=d.gia_tri_de_xuat,
                thoi_diem_cap_nhat=row.thoi_diem_cap_nhat,
                # Tài khoản đã xóa (test TRUNCATE, FK tắt) -> db.get trả None.
                nguoi_cap_nhat=_display_name(
                    db.get(TaiKhoan, row.tai_khoan_id) if row.tai_khoan_id is not None else None
                ),
            )
        )
    return out


def update_thresholds(
    db: Session, user: CurrentUser, payload: ThresholdUpdate
) -> list[ThresholdOut]:
    """Ghi đủ ba ngưỡng trong một commit, lưu người sửa và thời điểm (T-04-30,
    chống chối bỏ). Thêm dòng NGUONG_DOAN_TRUNG nếu CSDL chưa có (trước 0010)."""
    now = now_utc()
    rows = {
        row.loai: row
        for row in db.execute(
            select(CauHinhNguong)
            .where(CauHinhNguong.loai.in_([d.loai for d in DEFINITIONS]))
            .with_for_update()
        ).scalars()
    }
    for d in DEFINITIONS:
        value: Decimal = getattr(payload, d.loai)
        row = rows.get(d.loai)
        if row is None:
            row = CauHinhNguong(loai=d.loai, gia_tri=value, thoi_diem_cap_nhat=now)
            db.add(row)
        row.gia_tri = value
        row.tai_khoan_id = user.tai_khoan_id
        row.thoi_diem_cap_nhat = now
    db.commit()
    return list_thresholds(db)
