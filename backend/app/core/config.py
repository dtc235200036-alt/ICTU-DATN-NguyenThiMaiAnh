from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình đọc từ biến môi trường (12-factor). Không có bí mật nào có giá trị mặc định."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    APP_ENV: str = "production"
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 480
    BCRYPT_ROUNDS: int = 12
    COOKIE_SECURE: bool = True
    SEED_DEFAULT_PASSWORD: str | None = None
    BO_MON_DISPLAY_NAME: str = "Bộ môn CNTT"

    # AUTH-01 throttle (Task 2)
    LOGIN_MAX_FAILURES: int = 5
    LOGIN_WINDOW_MINUTES: int = 15

    # D-10/UC0.6 + D-07 (Phase 4): AI client seam — "http" gọi dịch vụ AI thật
    # (AiClientHttp), "stub" giữ bộ giả lập Phase 2/3 làm phương án dự phòng
    # (AI_STUB_MODE chỉ có hiệu lực khi AI_CLIENT="stub").
    AI_CLIENT: Literal["stub", "http"] = "stub"
    AI_STUB_MODE: str = "normal"
    AI_SERVICE_URL: str | None = None
    AI_API_KEY: str | None = None
    # 04-RESEARCH Open Question 3: NFR title ≤ 5 s, tài liệu ≤ 30 s (chạy nền),
    # ingest chạy nền sau commit nên được phép lâu hơn.
    AI_TITLE_TIMEOUT_SECONDS: float = 4.0
    AI_DOCUMENT_TIMEOUT_SECONDS: float = 24.0
    AI_INGEST_TIMEOUT_SECONDS: float = 60.0
    # CR-02 (04-REVIEW): mã hóa tài liệu tốn ~0,12 s CPU / 1000 ký tự (báo cáo
    # ~100 trang ≈ 350 000 ký tự ≈ 40 s trên máy phát triển) nên timeout
    # /check-document và /ingest DOCUMENT tăng theo độ dài — hệ số gấp đôi để
    # hai tài liệu dài chạy cùng lúc vẫn kịp — chặn trên bởi
    # AI_DOCUMENT_TIMEOUT_MAX_SECONDS < DOCUMENT_CHECK_TIMEOUT_SECONDS (lần
    # chạy quá hạn đó bị expire_if_stale chuyển LOI).
    AI_DOCUMENT_TIMEOUT_PER_1K_CHARS: float = 0.25
    AI_DOCUMENT_TIMEOUT_MAX_SECONDS: float = 240.0
    # WR-05 (04-REVIEW): văn bản trích xuất dài hơn mức này không được gửi sang
    # dịch vụ AI (trần của AI: 2 000 000 ký tự / 8 MiB thân request) — kết quả
    # LOI không thử lại được, kèm thông báo rõ. 800 000 ký tự ≈ 230 trang, mã
    # hóa ~100 s — vẫn dưới timeout theo độ dài (24 + 0,25 × 800 = 224 s).
    AI_DOCUMENT_MAX_CHARS: int = 800_000
    TITLE_CHECK_TOP_K: int = 5

    # D-02/D-03/D-04 (Phase 3): tài liệu đề cương/báo cáo lưu ngoài DocumentRoot
    # của Apache, trên named volume riêng của container api.
    UPLOAD_DIR: str = "/data/uploads"
    MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024
    DOCUMENT_CHECK_TIMEOUT_SECONDS: int = 300

    @field_validator("JWT_SECRET")
    @classmethod
    def _jwt_secret_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET phải có ít nhất 32 ký tự")
        return v

    @field_validator("BCRYPT_ROUNDS")
    @classmethod
    def _bcrypt_rounds_floor(cls, v: int, info) -> int:
        app_env = info.data.get("APP_ENV", "production")
        if app_env != "test" and v < 12:
            raise ValueError("BCRYPT_ROUNDS phải >= 12 ngoài môi trường test")
        return v


    @model_validator(mode="after")
    def _http_client_requires_url_and_key(self) -> "Settings":
        if self.AI_CLIENT == "http":
            if not self.AI_SERVICE_URL:
                raise ValueError("AI_CLIENT=http cần AI_SERVICE_URL")
            if not self.AI_API_KEY or len(self.AI_API_KEY) < 32:
                raise ValueError("AI_CLIENT=http cần AI_API_KEY có ít nhất 32 ký tự")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
