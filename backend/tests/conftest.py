import os
import secrets
import tempfile
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY_ENV_FILE = REPO_ROOT / "deploy" / ".env"


def _read_deploy_env() -> dict[str, str]:
    values: dict[str, str] = {}
    if not DEPLOY_ENV_FILE.exists():
        return values
    for line in DEPLOY_ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def _configure_test_environment() -> None:
    os.environ.setdefault("APP_ENV", "test")
    os.environ["APP_ENV"] = "test"
    os.environ.setdefault("BCRYPT_ROUNDS", "4")
    os.environ["BCRYPT_ROUNDS"] = "4"
    os.environ.setdefault("JWT_SECRET", secrets.token_hex(32))
    os.environ.setdefault("COOKIE_SECURE", "true")
    # Phase 3: host pytest không ghi được /data/uploads (container-only) — mỗi
    # phiên test dùng một thư mục tạm riêng, tự dọn khi tiến trình pytest thoát.
    os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="ntma-uploads-")

    if os.environ.get("TEST_DATABASE_URL"):
        os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
        return

    if os.environ.get("DATABASE_URL"):
        return

    env_values = _read_deploy_env()
    user = env_values.get("MYSQL_USER", "thesis_api")
    password = env_values.get("MYSQL_PASSWORD", "")
    port = env_values.get("MYSQL_HOST_PORT", "3307")
    os.environ["DATABASE_URL"] = (
        f"mysql+pymysql://{user}:{password}@127.0.0.1:{port}/thesis_core_test?charset=utf8mb4"
    )


_configure_test_environment()

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.db import SessionLocal, engine  # noqa: E402
from app.core.roles import VaiTro  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.core.throttle import login_throttle  # noqa: E402
from app.main import app  # noqa: E402
from app.models.tai_khoan import GiangVien, SinhVien, TaiKhoan  # noqa: E402

_TRUNCATE_EXCLUDE = {"alembic_version", "cau_hinh_nguong"}

# WR-05: chỉ là dữ liệu test — test_every_api_route_declares_roles dùng để bỏ
# qua các endpoint cố ý công khai (AUTH-03) khi kiểm tra mọi route còn lại đều
# khai báo Depends(require_role(...)). KHÔNG có allow-list/middleware nào
# trong app đọc set này; giữ ở đây (thay vì app/core/deps.py) để không ai
# tưởng nhầm nó có hiệu lực runtime.
PUBLIC_ROUTES: set[tuple[str, str]] = {
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/refresh"),
    ("POST", "/api/auth/logout"),
    ("GET", "/api/health"),
    ("GET", "/api/docs"),
    ("HEAD", "/api/docs"),
    ("GET", "/api/openapi.json"),
    ("HEAD", "/api/openapi.json"),
}


def _check_db_reachable() -> None:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.exit(
            "Start MySQL first: docker compose -f deploy/docker-compose.yml up -d --wait mysql"
            f" ({exc})"
        )


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    _check_db_reachable()

    alembic_cfg = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    command.upgrade(alembic_cfg, "head")
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.connect() as conn:
        tables = conn.execute(text("SHOW TABLES")).scalars().all()
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in tables:
            if table in _TRUNCATE_EXCLUDE:
                continue
            conn.execute(text(f"TRUNCATE TABLE `{table}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        conn.commit()
    login_throttle.reset_all()


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client


@dataclass
class SeededAccount:
    tai_khoan_id: int
    vai_tro: VaiTro
    ma_dang_nhap: str
    email: str
    password: str
    sinh_vien_id: int | None
    giang_vien_id: int | None


_counter = {"n": 0}


def _next_suffix() -> str:
    _counter["n"] += 1
    return f"{_counter['n']:04d}"


@pytest.fixture
def make_account(db):
    def _make(
        vai_tro: VaiTro,
        *,
        ma: str | None = None,
        email: str | None = None,
        ho_ten: str | None = None,
        bi_khoa: bool = False,
    ) -> SeededAccount:
        suffix = _next_suffix()
        password = "MatKhau@123"
        ma_dang_nhap = ma or f"user{suffix}"
        email_value = email or f"user{suffix}@ictu.edu.vn"
        ho_ten_value = ho_ten or f"Người dùng {suffix}"

        account = TaiKhoan(
            ma_dang_nhap=ma_dang_nhap,
            email=email_value,
            mat_khau_bam=hash_password(password),
            vai_tro=vai_tro,
            bi_khoa=bi_khoa,
        )
        db.add(account)
        db.flush()

        sinh_vien_id = None
        giang_vien_id = None

        if vai_tro == VaiTro.SINH_VIEN:
            sv = SinhVien(
                tai_khoan_id=account.id,
                ma_so_sinh_vien=f"SV{suffix}",
                ho_ten=ho_ten_value,
                email=email_value,
                lop=f"K{suffix}",
                khoa="CNTT",
            )
            db.add(sv)
            db.flush()
            sinh_vien_id = sv.id
        elif vai_tro == VaiTro.GIANG_VIEN:
            gv = GiangVien(
                tai_khoan_id=account.id,
                ma_giang_vien=f"GV{suffix}",
                ho_ten=ho_ten_value,
                email=email_value,
                hoc_vi="Thạc sĩ",
            )
            db.add(gv)
            db.flush()
            giang_vien_id = gv.id

        db.commit()

        return SeededAccount(
            tai_khoan_id=account.id,
            vai_tro=vai_tro,
            ma_dang_nhap=ma_dang_nhap,
            email=email_value,
            password=password,
            sinh_vien_id=sinh_vien_id,
            giang_vien_id=giang_vien_id,
        )

    return _make


@pytest.fixture
def auth_headers():
    def _headers(account: SeededAccount) -> dict[str, str]:
        token = create_access_token(account.tai_khoan_id, account.vai_tro)
        return {"Authorization": f"Bearer {token}"}

    return _headers


@pytest.fixture
def make_assigned_topic(db):
    """Phase 3/UC2: một DeTai ở DA_PHAN_CONG (SV + GVHD đã gán) qua một
    DotDoAn đang mở tự tạo — điểm vào bắt buộc cho mọi nộp đề cương."""

    def _make(sv: SeededAccount, gv: SeededAccount):
        from app.models.de_tai import DA_PHAN_CONG, GIANG_VIEN, DeTai
        from app.models.dot_do_an import DANG_MO, DotDoAn

        suffix = _next_suffix()
        cohort = DotDoAn(
            ten_dot=f"Đợt kiểm thử đề cương {suffix}",
            khoa="KTEST",
            nam_hoc="2026-2027",
            ngay_bat_dau=date(2026, 1, 1),
            trang_thai=DANG_MO,
        )
        db.add(cohort)
        db.flush()

        topic = DeTai(
            dot_do_an_id=cohort.id,
            giang_vien_id=gv.giang_vien_id,
            sinh_vien_id=sv.sinh_vien_id,
            ten_de_tai=f"Đề tài kiểm thử đề cương {suffix}",
            trang_thai=DA_PHAN_CONG,
            loai_nguoi_de_xuat=GIANG_VIEN,
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)
        return topic

    return _make


@pytest.fixture
def docx_bytes():
    def _make(paragraphs: list[str]) -> bytes:
        from docx import Document

        doc = Document()
        for p in paragraphs:
            doc.add_paragraph(p)
        buf = BytesIO()
        doc.save(buf)
        return buf.getvalue()

    return _make


@pytest.fixture
def pdf_bytes():
    def _make(lines: list[str]) -> bytes:
        # ASCII only — font PDF mặc định của PyMuPDF không có glyph tiếng Việt.
        import pymupdf

        pdf = pymupdf.open()
        page = pdf.new_page()
        y = 72
        for line in lines:
            page.insert_text((72, y), line)
            y += 20
        data = pdf.tobytes()
        pdf.close()
        return data

    return _make
