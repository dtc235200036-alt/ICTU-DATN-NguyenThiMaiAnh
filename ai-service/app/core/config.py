from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình dịch vụ AI, chỉ đọc từ biến môi trường (12-factor).

    Bí mật (DATABASE_URL, AI_API_KEY) KHÔNG có giá trị mặc định. Ngưỡng mặc
    định chỉ dùng khi Web API không gửi ngưỡng trong request (D-04) — plan
    04-04 thay bằng giá trị đã hiệu chỉnh.
    """

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    APP_ENV: str = "production"
    DATABASE_URL: str
    AI_API_KEY: str
    AI_MODEL_PROFILE: Literal["bkai", "e5", "fake"] = "bkai"
    TORCH_THREADS: int = 4

    MAX_TEXT_CHARS: int = 2_000_000
    MAX_BODY_BYTES: int = 8 * 1024 * 1024

    NGUONG_DOAN_MAC_DINH: float = 80.0
    NGUONG_NGUYEN_VAN_MAC_DINH: float = 60.0
    MINHASH_SHINGLE: int = 4
    MINHASH_NUM_PERM: int = 128
    TOP_K_MAC_DINH: int = 5
    CHI_TIET_TOI_DA: int = 50

    @field_validator("AI_API_KEY")
    @classmethod
    def _api_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("AI_API_KEY phải có ít nhất 32 ký tự")
        return v

    @field_validator("AI_MODEL_PROFILE")
    @classmethod
    def _fake_only_in_test(cls, v: str, info) -> str:
        if v == "fake" and info.data.get("APP_ENV", "production") != "test":
            raise ValueError("AI_MODEL_PROFILE=fake chỉ được dùng khi APP_ENV=test")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
