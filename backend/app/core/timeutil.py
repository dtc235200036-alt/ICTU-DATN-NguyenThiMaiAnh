"""Tiện ích thời gian dùng chung cho Phase 3 (D-06/NFR-14).

Việt Nam không có DST và image `python:3.12-slim` có thể thiếu dữ liệu
tzdata đầy đủ, nên dùng múi giờ cố định UTC+7 thay vì `ZoneInfo("Asia/Ho_Chi_Minh")`.
Quy ước lưu trữ toàn dự án: mọi datetime lưu DB là UTC naive (không tzinfo);
chuyển đổi hiển thị sang giờ Việt Nam chỉ thực hiện ở tầng đọc/hiển thị.
"""
from datetime import date, datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))


def now_utc() -> datetime:
    """Thời điểm hiện tại, UTC naive (không tzinfo) — khớp quy ước lưu DB."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def today_vn() -> date:
    """Ngày hiện tại theo giờ Việt Nam (UTC+7)."""
    return datetime.now(VN_TZ).date()


def to_vn_date(naive_utc_dt: datetime) -> date:
    """Chuyển một datetime UTC naive (đã lưu DB) sang ngày theo giờ Việt Nam."""
    aware = naive_utc_dt.replace(tzinfo=timezone.utc)
    return aware.astimezone(VN_TZ).date()
