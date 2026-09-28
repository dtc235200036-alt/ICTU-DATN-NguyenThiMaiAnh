"""Bộ mã hóa embedding (D-01, D-02, AISV-02).

Hai profile thật của bake-off là hạng nhất, chọn bằng AI_MODEL_PROFILE:
- bkai: bkai-foundation-models/vietnamese-bi-encoder, tách từ underthesea trước;
- e5:   intfloat/multilingual-e5-base, tiền tố "query: " cho MỌI đầu vào (so
        sánh tiêu đề/câu là đối xứng nên cả hai phía dùng "query: ").
Profile fake (HashingEncoder) chỉ dùng cho test (Settings từ chối ngoài
APP_ENV=test): tất định, không import torch.

Mỗi lần gọi encode() = MỘT lần mã hóa logic cho cả lô, encode_calls tăng 1
bất kể số văn bản (NFR-11: ingest chỉ mã hóa mục mới, một lần).

CR-02 (04-REVIEW): lô lớn (báo cáo ~2000 câu ≈ 30 s CPU) được mã hóa theo từng
lô con SUB_BATCH câu, mỗi lô con giữ khóa mô hình riêng — một lần kiểm tra tên
(1 câu) chen vào giữa chỉ chờ tối đa một lô con (~0,5 s) thay vì cả tài liệu.
Câu được sắp theo độ dài trước khi chia lô con (ít đệm như khi mã hóa cả lô),
kết quả trả về đúng thứ tự đầu vào.
"""
import hashlib
import threading
from collections import deque
from dataclasses import dataclass

import numpy as np

from app.nlp.normalize import nfc, syllables
from app.nlp.segment import segment


@dataclass(frozen=True)
class Profile:
    model: str
    segment: bool
    prefix: str
    # WR-01 (04-REVIEW): commit Hugging Face đã chốt ở bake-off (04-03) — mô
    # hình KHÔNG bao giờ lấy theo nhánh main. Ngưỡng hiệu chỉnh (04-04) chỉ
    # đúng với đúng trọng số này.
    revision: str | None = None

    @property
    def ten_model(self) -> str:
        """Khóa của embedding trong thesis_ai: repo@12 ký tự đầu của commit.
        Đổi trọng số => đổi tên => rebuild coi vector cũ là thiếu (thieu_embedding
        > 0) và /reindex mã hóa lại, không trộn hai không gian vector."""
        return f"{self.model}@{self.revision[:12]}" if self.revision else self.model


PROFILES: dict[str, Profile] = {
    "bkai": Profile(
        "bkai-foundation-models/vietnamese-bi-encoder",
        True,
        "",
        "84f9d9ada0d1a3c37557398b9ae9fcedcdf40be0",
    ),
    "e5": Profile(
        "intfloat/multilingual-e5-base",
        False,
        "query: ",
        "d128750597153bb5987e10b1c3493a34e5a4502a",
    ),
    "fake": Profile("fake-hashing-256", False, ""),
}


class HashingEncoder:
    """Bộ mã hóa giả tất định cho test: đếm unigram + bigram âm tiết băm
    blake2b vào 256 chiều, chuẩn hóa L2. Không đánh giá được diễn đạt lại —
    chất lượng ngữ nghĩa do plan 04-04 đo trên mô hình thật."""

    dim = 256

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            toks = syllables(text)
            grams = toks + [f"{a} {b}" for a, b in zip(toks, toks[1:])]
            for gram in grams:
                h = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
                out[row, int.from_bytes(h, "little") % self.dim] += 1.0
            norm = np.linalg.norm(out[row])
            if norm > 0:
                out[row] /= norm
        return out


# CR-02: số câu mỗi lô con giữ khóa mô hình (~0,5 s CPU với bkai, 4 luồng).
SUB_BATCH = 32


class FairLock:
    """Khóa FIFO (CR-02): threading.Lock không công bằng — luồng vừa nhả khóa
    giữa hai lô con thường lấy lại ngay, nên một lần kiểm tra tên đang chờ có
    thể đói tới hết cả tài liệu (đo được: ReadTimeout 4 s). Ở đây ai tới trước
    được trước: tài liệu dài xếp lại cuối hàng sau mỗi lô con."""

    def __init__(self) -> None:
        self._cond = threading.Condition()
        self._queue: deque[object] = deque()
        self._locked = False

    def __enter__(self) -> "FairLock":
        ticket = object()
        with self._cond:
            self._queue.append(ticket)
            while self._locked or self._queue[0] is not ticket:
                self._cond.wait()
            self._queue.popleft()
            self._locked = True
        return self

    def __exit__(self, *exc) -> None:
        with self._cond:
            self._locked = False
            self._cond.notify_all()


class Encoder:
    def __init__(self, profile: str, torch_threads: int = 4) -> None:
        if profile not in PROFILES:
            raise ValueError(f"Profile không hợp lệ: {profile}")
        self.profile = profile
        self._spec = PROFILES[profile]
        self.name = self._spec.ten_model
        self.encode_calls = 0
        self._lock = FairLock()
        self._calls_lock = threading.Lock()
        if profile == "fake":
            self._model = HashingEncoder()
            self.dim = HashingEncoder.dim
        else:
            import torch
            from sentence_transformers import SentenceTransformer

            torch.set_num_threads(torch_threads)
            # Trọng số lấy từ cache HF_HOME (volume /models trong container).
            self._model = SentenceTransformer(
                self._spec.model, revision=self._spec.revision, device="cpu"
            )
            get_dim = getattr(self._model, "get_embedding_dimension", None) or getattr(
                self._model, "get_sentence_embedding_dimension"
            )
            self.dim = int(get_dim())

    def preprocess(self, text: str) -> str:
        text = nfc(text)
        if self._spec.segment:
            text = segment(text)
        return self._spec.prefix + text

    def _encode_batch(self, texts: list[str]) -> np.ndarray:
        prepared = [self.preprocess(t) for t in texts]
        if self.profile == "fake":
            return self._model.encode(prepared)
        return self._model.encode(
            prepared,
            batch_size=SUB_BATCH,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def encode(self, texts: list[str]) -> np.ndarray:
        """Mã hóa cả lô (một lần gọi logic); trả float32 (n, dim) đã chuẩn hóa
        L2 theo đúng thứ tự đầu vào. Khóa mô hình chỉ giữ trong từng lô con."""
        if not texts:
            # Lô rỗng không chạm tới mô hình → không tính là một lần gọi.
            return np.zeros((0, self.dim), dtype=np.float32)
        with self._calls_lock:
            self.encode_calls += 1
        order = sorted(range(len(texts)), key=lambda i: -len(texts[i]))
        out = np.empty((len(texts), self.dim), dtype=np.float32)
        for start in range(0, len(order), SUB_BATCH):
            idx = order[start : start + SUB_BATCH]
            with self._lock:
                vectors = self._encode_batch([texts[i] for i in idx])
            out[idx] = np.asarray(vectors, dtype=np.float32)
        return np.ascontiguousarray(out)
