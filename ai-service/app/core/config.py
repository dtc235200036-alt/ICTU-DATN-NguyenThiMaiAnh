from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình dịch vụ AI, chỉ đọc từ biến môi trường (12-factor).

    Bí mật (DATABASE_URL, AI_API_KEY) KHÔNG có giá trị mặc định. Ngưỡng mặc
    định chỉ dùng khi Web API không gửi ngưỡng trong request (D-04) — plan
    04-04 thay bằng giá trị đã hiệu chỉnh.
    """

    # IN-01 (04-REVIEW): ValidationError không bao giờ in giá trị đầu vào (khóa
    # sai độ dài không lọt vào log container lúc khởi động).
    model_config = SettingsConfigDict(env_file=None, extra="ignore", hide_input_in_errors=True)

    APP_ENV: str = "production"
    DATABASE_URL: str
    AI_API_KEY: SecretStr
    AI_MODEL_PROFILE: Literal["bkai", "e5", "fake"] = "bkai"  # hiệu chỉnh: calibration/nguong-de-xuat.json (2026-10-21)
    TORCH_THREADS: int = 4

    MAX_TEXT_CHARS: int = 2_000_000
    MAX_BODY_BYTES: int = 8 * 1024 * 1024

    NGUONG_DOAN_MAC_DINH: float = 67.7  # hiệu chỉnh: calibration/nguong-de-xuat.json (2026-10-21)
    NGUONG_NGUYEN_VAN_MAC_DINH: float = 56.0  # hiệu chỉnh: calibration/nguong-de-xuat.json (2026-10-21)
    # Vân tay nguyên văn (fingerprint.py): k-gram âm tiết, cửa sổ winnowing w
    # (đoạn chung từ w + k − 1 âm tiết luôn được tìm thấy), cụm có trong từ
    # VAN_TAY_PHO_BIEN nhóm đề tài trở lên là cụm phổ biến (Sorokina và cs. 2006: L = 4).
    VAN_TAY_K: int = 6  # hiệu chỉnh: calibration/nguong-de-xuat.json (2026-10-21)
    VAN_TAY_W: int = 4
    VAN_TAY_PHO_BIEN: int = 4
    TOP_K_MAC_DINH: int = 5
    CHI_TIET_TOI_DA: int = 50

    @field_validator("AI_API_KEY")
    @classmethod
    def _api_key_min_length(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
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
