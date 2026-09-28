"""Tải trước trọng số mô hình của profile đang cấu hình vào HF_HOME.

    python -m app.download_model            # dùng AI_MODEL_PROFILE (mặc định bkai)
    python -m app.download_model --profile e5

Dùng để làm nóng volume /models trên máy chủ không có Internet ra ngoài: chạy
lệnh này ở nơi có mạng, rồi mang volume/cache sang (04-RESEARCH Environment
Availability). Không cần DATABASE_URL hay AI_API_KEY.
"""
import argparse
import os
import sys

from app.embedding import PROFILES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=["bkai", "e5"],
        default=os.environ.get("AI_MODEL_PROFILE", "bkai"),
    )
    args = parser.parse_args()
    if args.profile not in ("bkai", "e5"):
        print(f"Profile không có mô hình để tải: {args.profile}", file=sys.stderr)
        return 2

    from sentence_transformers import SentenceTransformer

    spec = PROFILES[args.profile]
    model_id = spec.model
    # WR-01: đúng commit đã chốt, không phải nhánh main.
    model = SentenceTransformer(model_id, revision=spec.revision, device="cpu")
    if args.profile == "bkai":
        from underthesea import word_tokenize

        word_tokenize("Làm nóng bộ tách từ", format="text")
    print(f"OK {spec.ten_model} -> {os.environ.get('HF_HOME', '~/.cache/huggingface')} ({type(model).__name__})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
