from datetime import date

import pytest

from app.core.roles import VaiTro
from app.models.dot_do_an import DANG_MO, DotDoAn

# T-02-18: mọi endpoint ghi trên /api/cohorts chỉ Bộ môn được gọi; SV/GV luôn
# nhận 403 và hàng đợt đồ án không bị thay đổi bởi lời gọi bị từ chối.
COHORT_WRITE_ENDPOINTS = [
    (
        "POST",
        "/api/cohorts",
        {
            "ten_dot": "Đợt thử nghiệm K23",
            "khoa": "K23",
            "nam_hoc": "2026-2027",
            "ngay_bat_dau": "2026-09-28",
        },
    ),
    (
        "PUT",
        "/api/cohorts/{id}",
        {
            "ten_dot": "Đổi tên trái phép",
            "khoa": "K23",
            "nam_hoc": "2026-2027",
            "ngay_bat_dau": "2026-09-28",
        },
    ),
    ("POST", "/api/cohorts/{id}/open", None),
    ("POST", "/api/cohorts/{id}/close", None),
]


def _make_cohort(db) -> DotDoAn:
    cohort = DotDoAn(
        ten_dot="Đợt gốc",
        khoa="K22",
        nam_hoc="2025-2026",
        ngay_bat_dau=date(2026, 1, 1),
        trang_thai=DANG_MO,
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)
    return cohort


@pytest.mark.parametrize("actor_role", [VaiTro.SINH_VIEN, VaiTro.GIANG_VIEN])
@pytest.mark.parametrize("method,path_template,body", COHORT_WRITE_ENDPOINTS)
def test_non_bomon_gets_403_on_every_cohort_write(
    client, make_account, auth_headers, db, actor_role, method, path_template, body
):
    cohort = _make_cohort(db)
    actor = make_account(actor_role)

    path = path_template.format(id=cohort.id)
    resp = client.request(method, path, json=body, headers=auth_headers(actor))

    assert resp.status_code == 403

    row = db.get(DotDoAn, cohort.id)
    assert row is not None
    assert row.ten_dot == "Đợt gốc"
    assert row.trang_thai == DANG_MO


def test_any_role_can_list_cohorts(client, make_account, auth_headers, db):
    cohort = _make_cohort(db)
    sv = make_account(VaiTro.SINH_VIEN)

    resp = client.get("/api/cohorts", headers=auth_headers(sv))

    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()]
    assert cohort.id in ids
