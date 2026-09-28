"""Tách từ tiếng Việt (AISV-02) — bắt buộc trước khi đưa vào bkai
(PhoBERT-v2 được huấn luyện trên văn bản đã tách từ kiểu `vui_tính`).

underthesea được import lười: chỉ profile bkai gọi tới, test (profile fake)
không bao giờ tải nó.
"""


def segment(text: str) -> str:
    from underthesea import word_tokenize

    return word_tokenize(text, format="text")
