from functools import lru_cache

from pydantic import field_validator
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
