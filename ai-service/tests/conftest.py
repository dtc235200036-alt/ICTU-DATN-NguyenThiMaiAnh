"""Môi trường test: profile fake (không torch), SQLite dưới tmp_path, alembic
upgrade head chạy bằng code. Không bao giờ chạm MySQL/compose `ntma`."""
import os
from pathlib import Path

os.environ["APP_ENV"] = "test"
os.environ["AI_MODEL_PROFILE"] = "fake"
os.environ["AI_API_KEY"] = "k" * 20 + "test-key-0123456789"  # 40 ký tự
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402

SERVICE_DIR = Path(__file__).resolve().parents[1]
API_KEY = os.environ["AI_API_KEY"]
HEADERS = {"X-API-Key": API_KEY}


def migrate(db_path: Path) -> str:
    url = f"sqlite:///{db_path}"
    cfg = Config(str(SERVICE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(SERVICE_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    return url


def make_client(db_path: Path) -> TestClient:
    """Một instance ứng dụng mới trên cùng file DB (mô phỏng khởi động lại)."""
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    get_settings.cache_clear()
    from app.main import create_app

    return TestClient(create_app())


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "thesis_ai.db"
    migrate(path)
    return path


@pytest.fixture
def client(db_path: Path):
    with make_client(db_path) as c:
        yield c
    get_settings.cache_clear()
