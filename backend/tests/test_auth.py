import time

import jwt

from app.core.config import get_settings
from app.core.roles import VaiTro
from app.models.tai_khoan import TaiKhoan


def test_login_by_code_and_email_sets_refresh_cookie(client, make_account, db):
    sv = make_account(VaiTro.SINH_VIEN)
    resp_sv = client.post(
        "/api/auth/login",
        json={"dang_nhap": sv.ma_dang_nhap, "mat_khau": sv.password},
    )
    assert resp_sv.status_code == 200
    body_sv = resp_sv.json()
    assert body_sv["access_token"]

    set_cookie_sv = resp_sv.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_sv
    assert "Secure" in set_cookie_sv
    assert "samesite=strict" in set_cookie_sv.lower()
    assert "Path=/api/auth" in set_cookie_sv

    gv = make_account(VaiTro.GIANG_VIEN)
    resp_gv = client.post(
        "/api/auth/login",
        json={"dang_nhap": gv.email, "mat_khau": gv.password},
    )
    assert resp_gv.status_code == 200
    assert resp_gv.json()["access_token"]
    set_cookie_gv = resp_gv.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_gv
    assert "Secure" in set_cookie_gv
    assert "Path=/api/auth" in set_cookie_gv


def test_locked_account_cannot_login_or_refresh(client, make_account, db):
    account = make_account(VaiTro.SINH_VIEN)

    login_resp = client.post(
        "/api/auth/login",
        json={"dang_nhap": account.ma_dang_nhap, "mat_khau": account.password},
    )
    assert login_resp.status_code == 200

    wrong_password_resp = client.post(
        "/api/auth/login",
        json={"dang_nhap": account.ma_dang_nhap, "mat_khau": "sai-mat-khau"},
    )
    assert wrong_password_resp.status_code == 401
    wrong_password_detail = wrong_password_resp.json()["detail"]

    # Khóa tài khoản trực tiếp trong DB (mô phỏng Bộ môn khóa tài khoản)
    row = db.get(TaiKhoan, account.tai_khoan_id)
    row.bi_khoa = True
    db.commit()

    refresh_resp = client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 401

    locked_login_resp = client.post(
        "/api/auth/login",
        json={"dang_nhap": account.ma_dang_nhap, "mat_khau": account.password},
    )
    assert locked_login_resp.status_code == 401
    assert locked_login_resp.json()["detail"] == wrong_password_detail


def test_expired_or_refresh_token_rejected_as_bearer(client, make_account, auth_headers):
    account = make_account(VaiTro.GIANG_VIEN)
    settings = get_settings()

    now = int(time.time())
    expired_access = jwt.encode(
        {
            "sub": str(account.tai_khoan_id),
            "vai_tro": str(account.vai_tro),
            "typ": "access",
            "iat": now - 3600,
            "exp": now - 1800,
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    resp_expired = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {expired_access}"}
    )
    assert resp_expired.status_code == 401

    refresh_typed_token = jwt.encode(
        {
            "sub": str(account.tai_khoan_id),
            "typ": "refresh",
            "iat": now,
            "exp": now + 3600,
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    resp_refresh_as_bearer = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {refresh_typed_token}"}
    )
    assert resp_refresh_as_bearer.status_code == 401

    resp_valid = client.get("/api/auth/me", headers=auth_headers(account))
    assert resp_valid.status_code == 200
    assert resp_valid.json()["ma_dang_nhap"] == account.ma_dang_nhap


def test_every_api_route_declares_roles():
    from app.main import app
    from conftest import PUBLIC_ROUTES

    def _dependant_has_allowed_roles(dependant) -> bool:
        if getattr(dependant.call, "allowed_roles", None) is not None:
            return True
        return any(
            _dependant_has_allowed_roles(sub) for sub in dependant.dependencies
        )

    offenders: list[str] = []
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api"):
            continue
        methods = getattr(route, "methods", None) or set()
        dependant = getattr(route, "dependant", None)
        for method in methods:
            if (method, path) in PUBLIC_ROUTES:
                continue
            if dependant is None or not _dependant_has_allowed_roles(dependant):
                offenders.append(f"{method} {path}")

    assert not offenders, f"Routes missing role declaration: {offenders}"
