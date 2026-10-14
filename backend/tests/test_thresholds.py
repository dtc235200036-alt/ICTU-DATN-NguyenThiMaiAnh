"""UC0.4/AISV-07 (D-04, SC4): Bộ môn cấu hình ngưỡng — RBAC, kiểm tra miền giá
trị (E1), lần kiểm tra KẾ TIẾP dùng giá trị mới, kết quả đã ghi giữ snapshot
nguong_ap_dung. Test chạy trên bộ giả lập (thang Jaccard) và khôi phục nguyên
trạng ba dòng cau_hinh_nguong trong finally (bảng này không bị TRUNCATE giữa
các test — conftest._TRUNCATE_EXCLUDE)."""
from sqlalchemy import text

from app.core.db import engine
from app.core.roles import VaiTro

_DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_LOAI = ("NGUONG_TEN_DE_TAI", "NGUONG_TAI_LIEU", "NGUONG_DOAN_TRUNG")


def _snapshot() -> list[tuple]:
    with engine.connect() as conn:
        return list(
            conn.execute(
                text(
                    "SELECT loai, gia_tri, tai_khoan_id, thoi_diem_cap_nhat FROM cau_hinh_nguong"
                    " WHERE loai IN ('NGUONG_TEN_DE_TAI','NGUONG_TAI_LIEU','NGUONG_DOAN_TRUNG')"
                )
            ).all()
        )


def _restore(rows: list[tuple]) -> None:
    with engine.begin() as conn:
        for loai, gia_tri, tai_khoan_id, thoi_diem in rows:
            conn.execute(
                text(
                    "UPDATE cau_hinh_nguong SET gia_tri = :g, tai_khoan_id = :t,"
                    " thoi_diem_cap_nhat = :d WHERE loai = :l"
                ),
                {"g": gia_tri, "t": tai_khoan_id, "d": thoi_diem, "l": loai},
            )


def test_thresholds_rbac_validation_and_next_check(
    client, make_account, auth_headers, make_assigned_topic, docx_bytes
):
    original = _snapshot()
    try:
        bomon = make_account(VaiTro.BO_MON)
        sv = make_account(VaiTro.SINH_VIEN)
        gv = make_account(VaiTro.GIANG_VIEN)
        bm_h = auth_headers(bomon)

        # T-04-29: SV và GV không đọc/sửa được ngưỡng.
        for actor in (sv, gv):
            h = auth_headers(actor)
            assert client.get("/api/thresholds", headers=h).status_code == 403
            body = {loai: 50 for loai in _LOAI}
            assert client.put("/api/thresholds", headers=h, json=body).status_code == 403

        resp = client.get("/api/thresholds", headers=bm_h)
        assert resp.status_code == 200, resp.text
        rows = {r["loai"]: r for r in resp.json()}
        assert list(rows) == list(_LOAI)
        before = {loai: rows[loai]["gia_tri"] for loai in _LOAI}
        assert rows["NGUONG_TEN_DE_TAI"]["gia_tri_de_xuat"] == 67.8
        assert rows["NGUONG_TAI_LIEU"]["gia_tri_de_xuat"] == 10.4
        assert rows["NGUONG_DOAN_TRUNG"]["gia_tri_de_xuat"] == 67.7

        # UC0.4 - E1: ngoài 0–100 -> 422, không dòng nào đổi.
        for bad in (120, -1):
            body = {**before, "NGUONG_TAI_LIEU": bad}
            resp = client.put("/api/thresholds", headers=bm_h, json=body)
            assert resp.status_code == 422, resp.text
            assert "UC0.4 - E1" in resp.text
        assert {r["loai"]: r["gia_tri"] for r in client.get("/api/thresholds", headers=bm_h).json()} == before

        # Một đề cương nộp TRƯỚC khi đổi ngưỡng (snapshot NGUONG_TAI_LIEU cũ).
        sv_a, gv_a = make_account(VaiTro.SINH_VIEN), make_account(VaiTro.GIANG_VIEN)
        topic_a = make_assigned_topic(sv_a, gv_a)
        resp = client.post(
            f"/api/outlines/{topic_a.id}/submit",
            headers=auth_headers(sv_a),
            files={"file": ("a.docx", docx_bytes(["Nội dung đề cương A trước khi đổi ngưỡng"]), _DOCX_CT)},
        )
        assert resp.status_code == 202, resp.text
        a_doc = resp.json()["phien_ban"][0]["tai_lieu"]["id"]

        # Tiêu đề gần giống "Đề tài kiểm thử đề cương NNNN" (Jaccard stub ≈ 83%).
        query = {"ten_de_tai": "Đề tài kiểm thử đề cương"}
        resp = client.post("/api/topics/check-title", headers=auth_headers(gv_a), json=query)
        assert resp.status_code == 200, resp.text
        assert resp.json()["matches"], resp.text

        new = {"NGUONG_TEN_DE_TAI": 95.5, "NGUONG_TAI_LIEU": 42.25, "NGUONG_DOAN_TRUNG": 81}
        resp = client.put("/api/thresholds", headers=bm_h, json=new)
        assert resp.status_code == 200, resp.text
        saved = {r["loai"]: r for r in resp.json()}
        assert {k: saved[k]["gia_tri"] for k in _LOAI} == {k: float(v) for k, v in new.items()}
        # Tài khoản Bộ môn không có hồ sơ SV/GV -> tên hiển thị là email (như deps).
        assert all(saved[k]["nguoi_cap_nhat"] == bomon.email for k in _LOAI)
        with engine.connect() as conn:
            editors = conn.execute(
                text(
                    "SELECT DISTINCT tai_khoan_id FROM cau_hinh_nguong WHERE loai IN"
                    " ('NGUONG_TEN_DE_TAI','NGUONG_TAI_LIEU','NGUONG_DOAN_TRUNG')"
                )
            ).scalars().all()
            fresh = conn.execute(
                text(
                    "SELECT MIN(thoi_diem_cap_nhat) >= UTC_TIMESTAMP() - INTERVAL 1 MINUTE"
                    " FROM cau_hinh_nguong WHERE loai IN"
                    " ('NGUONG_TEN_DE_TAI','NGUONG_TAI_LIEU','NGUONG_DOAN_TRUNG')"
                )
            ).scalar_one()
        assert editors == [bomon.tai_khoan_id] and fresh == 1

        # Kết quả cũ giữ snapshot; lần nộp kế tiếp dùng giá trị mới.
        old = client.get(f"/api/documents/{a_doc}/check", headers=auth_headers(gv_a)).json()
        assert old["nguong_ap_dung"] == before["NGUONG_TAI_LIEU"]
        sv_b, gv_b = make_account(VaiTro.SINH_VIEN), make_account(VaiTro.GIANG_VIEN)
        topic_b = make_assigned_topic(sv_b, gv_b)
        resp = client.post(
            f"/api/outlines/{topic_b.id}/submit",
            headers=auth_headers(sv_b),
            files={"file": ("b.docx", docx_bytes(["Nội dung đề cương B sau khi đổi ngưỡng"]), _DOCX_CT)},
        )
        assert resp.status_code == 202, resp.text
        b_doc = resp.json()["phien_ban"][0]["tai_lieu"]["id"]
        nxt = client.get(f"/api/documents/{b_doc}/check", headers=auth_headers(gv_b)).json()
        assert nxt["nguong_ap_dung"] == 42.25

        # Kiểm tra tên kế tiếp dùng ngưỡng mới (83% < 95.5% -> không còn cảnh báo) ...
        resp = client.post("/api/topics/check-title", headers=auth_headers(gv_a), json=query)
        assert resp.json()["nguong"] == 95.5 and resp.json()["matches"] == [], resp.text
        # ... và hạ lại thì cảnh báo trở lại.
        resp = client.put("/api/thresholds", headers=bm_h, json={**new, "NGUONG_TEN_DE_TAI": 50})
        assert resp.status_code == 200, resp.text
        resp = client.post("/api/topics/check-title", headers=auth_headers(gv_a), json=query)
        assert resp.json()["nguong"] == 50.0 and resp.json()["matches"], resp.text
    finally:
        _restore(original)
