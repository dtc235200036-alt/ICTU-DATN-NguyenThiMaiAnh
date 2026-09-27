import pytest

from app.core.roles import VaiTro
from app.models.tai_khoan import TaiKhoan

# T-02-12/T-02-13: mọi endpoint /api/accounts chỉ Bộ môn được gọi; SV/GV luôn
# nhận 403 và không có hàng nào trong DB bị thay đổi bởi lời gọi bị từ chối.
ACCOUNT_ENDPOINTS = [
    ("GET", "/api/accounts?vai_tro=SINH_VIEN", None),
    (
        "POST",
        "/api/accounts",
        {
            "vai_tro": "SINH_VIEN",
            "ma": "sv999zz",
            "email": "sv999zz@ictu.edu.vn",
            "ho_ten": "Test SV",
            "mat_khau": "MatKhau@123",
        },
    ),
    ("PUT", "/api/accounts/{id}", {"ho_ten": "Đổi tên trái phép"}),
    ("POST", "/api/accounts/{id}/lock", None),
    ("POST", "/api/accounts/{id}/unlock", None),
]


@pytest.mark.parametrize("actor_role", [VaiTro.SINH_VIEN, VaiTro.GIANG_VIEN])
@pytest.mark.parametrize("method,path_template,body", ACCOUNT_ENDPOINTS)
def test_non_bomon_gets_403_on_every_account_endpoint(
    client, make_account, auth_headers, db, actor_role, method, path_template, body
):
    target = make_account(VaiTro.SINH_VIEN)
    actor = make_account(actor_role)

    path = path_template.format(id=target.tai_khoan_id)
    resp = client.request(method, path, json=body, headers=auth_headers(actor))

    assert resp.status_code == 403

    row = db.get(TaiKhoan, target.tai_khoan_id)
    assert row is not None
    assert row.bi_khoa is False
    assert row.ma_dang_nhap == target.ma_dang_nhap
    assert row.email == target.email


def test_bomon_lock_blocks_login_and_unlock_restores_it(client, make_account, auth_headers):
    bomon = make_account(VaiTro.BO_MON)
    sv = make_account(VaiTro.SINH_VIEN)

    lock_resp = client.post(f"/api/accounts/{sv.tai_khoan_id}/lock", headers=auth_headers(bomon))
    assert lock_resp.status_code == 200

    locked_login = client.post(
        "/api/auth/login", json={"dang_nhap": sv.ma_dang_nhap, "mat_khau": sv.password}
    )
    assert locked_login.status_code == 401

    unlock_resp = client.post(f"/api/accounts/{sv.tai_khoan_id}/unlock", headers=auth_headers(bomon))
    assert unlock_resp.status_code == 200

    restored_login = client.post(
        "/api/auth/login", json={"dang_nhap": sv.ma_dang_nhap, "mat_khau": sv.password}
    )
    assert restored_login.status_code == 200
