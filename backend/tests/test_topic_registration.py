import threading
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.roles import VaiTro
from app.core.db import SessionLocal
from app.main import app
from app.models.de_tai import CHO_DUYET, DA_DUYET, DeTai, GIANG_VIEN
from app.models.dot_do_an import DANG_MO, DotDoAn

# ROADMAP SC4/D-05/§3.2.5: hai bất biến concurrency của UC1.2 — Race A (một đề
# tài không thể có hai SV thắng cùng lúc) và Race B (một SV không thể có hai
# đề tài đang hoạt động cùng lúc). Không thêm test nào khác ngoài hai cái này.


def _make_open_cohort(db) -> DotDoAn:
    cohort = DotDoAn(
        ten_dot="Đợt đồ án test UC1.2",
        khoa="K22",
        nam_hoc="2026-2027",
        ngay_bat_dau=date(2026, 1, 1),
        trang_thai=DANG_MO,
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)
    return cohort


def _make_open_gv_topic(db, cohort_id: int, giang_vien_id: int, title: str) -> DeTai:
    topic = DeTai(
        dot_do_an_id=cohort_id,
        giang_vien_id=giang_vien_id,
        sinh_vien_id=None,
        ten_de_tai=title,
        linh_vuc="Hệ thống thông tin",
        trang_thai=DA_DUYET,
        loai_nguoi_de_xuat=GIANG_VIEN,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def _register_concurrently(requests: list[tuple[int, dict]]) -> tuple[list[int], list[str | None]]:
    """Chạy N request POST /register cùng lúc (mỗi thread một TestClient +
    threading.Barrier riêng), trả (status_codes, details) theo đúng thứ tự
    `requests`."""
    barrier = threading.Barrier(len(requests))
    statuses: list[int | None] = [None] * len(requests)
    details: list[str | None] = [None] * len(requests)

    def _worker(idx: int, topic_id: int, headers: dict) -> None:
        with TestClient(app, base_url="https://testserver") as client:
            barrier.wait()
            resp = client.post(f"/api/topics/{topic_id}/register", headers=headers)
            statuses[idx] = resp.status_code
            try:
                details[idx] = resp.json().get("detail")
            except ValueError:
                details[idx] = None

    threads = [
        threading.Thread(target=_worker, args=(idx, topic_id, headers))
        for idx, (topic_id, headers) in enumerate(requests)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return statuses, details  # type: ignore[return-value]


def test_register_topic_race_one_winner_per_topic(make_account, auth_headers, db):
    """Race A (UC1.2 E1, §3.2.5-b): hai SV đăng ký cùng lúc MỘT đề tài — đúng 1
    người thắng (200, sinh_vien_id của người thắng, CHO_DUYET), người còn lại
    409 với đúng thông điệp E1. Lặp lại 5 lần, mỗi lần một cặp SV MỚI (người
    thắng vòng trước đã có đề tài hoạt động nên không thể tham gia vòng sau)."""
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN)

    for i in range(5):
        topic = _make_open_gv_topic(db, cohort.id, gv.giang_vien_id, f"Đề tài đăng ký đồng thời {i}")
        sv_a = make_account(VaiTro.SINH_VIEN)
        sv_b = make_account(VaiTro.SINH_VIEN)

        statuses, details = _register_concurrently(
            [
                (topic.id, auth_headers(sv_a)),
                (topic.id, auth_headers(sv_b)),
            ]
        )

        assert sorted(statuses) == [200, 409]
        loser_detail = details[statuses.index(409)]
        assert loser_detail == "Đề tài vừa được người khác đăng ký hoặc không còn trống"

        winner = sv_a if statuses[0] == 200 else sv_b

        with SessionLocal() as fresh_session:
            fresh = fresh_session.execute(select(DeTai).where(DeTai.id == topic.id)).scalar_one()
            assert fresh.trang_thai == CHO_DUYET
            assert fresh.sinh_vien_id == winner.sinh_vien_id


def test_register_topic_race_one_active_topic_per_student(make_account, auth_headers, db):
    """Race B (UC1.2 A1, §3.2.5-a): một SV đăng ký đồng thời HAI đề tài khác
    nhau — đúng 1 request thắng (200), request còn lại 409 với đúng thông điệp
    A1; sau cùng SV đó có đúng 1 đề tài đang hoạt động. Lặp lại 3 lần, mỗi lần
    một SV MỚI."""
    cohort = _make_open_cohort(db)
    gv = make_account(VaiTro.GIANG_VIEN)

    for i in range(3):
        topic_a = _make_open_gv_topic(db, cohort.id, gv.giang_vien_id, f"Đề tài A đồng thời {i}")
        topic_b = _make_open_gv_topic(db, cohort.id, gv.giang_vien_id, f"Đề tài B đồng thời {i}")
        sv = make_account(VaiTro.SINH_VIEN)
        headers = auth_headers(sv)

        statuses, details = _register_concurrently(
            [
                (topic_a.id, headers),
                (topic_b.id, headers),
            ]
        )

        assert sorted(statuses) == [200, 409]
        loser_detail = details[statuses.index(409)]
        assert loser_detail == (
            "Bạn đã có một đề tài đang hoạt động (chờ duyệt, đã duyệt hoặc đã phân công)"
        )

        with SessionLocal() as fresh_session:
            active_ids = (
                fresh_session.execute(
                    select(DeTai.id).where(DeTai.sinh_vien_id_dang_hoat_dong == sv.sinh_vien_id)
                )
                .scalars()
                .all()
            )
            assert len(active_ids) == 1
