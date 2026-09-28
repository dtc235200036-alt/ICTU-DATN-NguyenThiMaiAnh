#!/usr/bin/env python3
"""Hiệu chỉnh và kiểm chứng ngưỡng trùng lặp trên pipeline THẬT (plan 04-04).

    uv run python calibration/calibrate.py tune     --data ../seed-data \
        --profile-from ../tools/bakeoff/ket-qua.json --out calibration
    uv run python calibration/calibrate.py evaluate --data ../seed-data \
        --profile-from ../tools/bakeoff/ket-qua.json --out calibration \
        [--report ../docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md] [--apply]

Nguyên tắc (D-01, D-03, D-04, D-06):
- Chạy TRONG TIẾN TRÌNH trên một SQLite thesis_ai tạm (alembic upgrade head),
  không docker, không MySQL, không import backend. Mô hình = profile đã chốt ở
  tools/bakeoff/ket-qua.json (khóa `chon`), nạp MỘT lần mỗi lệnh.
- Văn bản lấy bằng calibration/extract.py — bản sao hàm extract_text của Web
  API; kho được nạp qua pipeline.ingest_many (đúng đường /ingest, /reindex),
  tài liệu B chỉ được KIỂM TRA (ref_id 0), không bao giờ nạp — như production.
- Id cục bộ: đề tài kho = ARCHIVE 1..300 theo thứ tự CSV (= topics[].stt);
  tài liệu A = DOCUMENT 1..25 theo thứ tự cặp.
- `tune` CHỈ đọc tập HIEU_CHINH. `evaluate` đọc ngưỡng từ nguong-de-xuat.json
  và không có đường nào để khớp lại ngưỡng; KIEM_CHUNG được báo cáo riêng.
- Phương pháp: sklearn roc_curve + chỉ số Youden J = TPR − FPR; khi tín hiệu
  tách hoàn toàn tập hiệu chỉnh → trung điểm giữa âm lớn nhất và dương nhỏ nhất
  (có biên). Ngưỡng tính theo %, một chữ số thập phân; quy tắc gắn cờ là ≥.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
import tempfile
import time
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from functools import partial
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sklearn.metrics import roc_auc_score, roc_curve  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import minhash, pipeline  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.embedding import Encoder  # noqa: E402
from app.index import TAI_LIEU, TIEU_DE, CorpusIndex  # noqa: E402
from app.models import LOAI_ARCHIVE, LOAI_DOCUMENT  # noqa: E402
from app.nlp.boilerplate import StripResult  # noqa: E402
from app.nlp.normalize import nfc  # noqa: E402
from calibration.extract import extract_text  # noqa: E402

HIEU_CHINH = "HIEU_CHINH"
KIEM_CHUNG = "KIEM_CHUNG"
CHEP = "CHEP_NGUYEN_VAN"
DIEN = "DIEN_DAT_LAI"
CUNG = "CUNG_LINH_VUC"
KHONG = "KHONG_LIEN_QUAN"
LOAI_CAP = (CHEP, DIEN, CUNG, KHONG)

# Nhãn câu của tài liệu B (theo provenance đoạn trong manifest).
L_NGUYEN_VAN = "NGUYEN_VAN"
L_DIEN_DAT = "DIEN_DAT"
L_TU_VIET = "TU_VIET"  # đoạn nguon = null
L_KHONG_KHOP = "KHONG_KHOP"  # câu không nằm trong đoạn nội dung nào (vd. dòng bìa còn sót)

SHINGLE_CANDIDATES = (3, 4, 5)
SHINGLE_TIE = 4
NUM_PERM = Settings.model_fields["MINHASH_NUM_PERM"].default
TITLE_TOP_K = 5
ALL = 10**6  # top_k / chi_tiet_toi_da "không giới hạn" khi đo
QUERY_REF_ID = 0  # B chưa được nạp: loại trừ {ref_id} = {0} như Web API
MIN_MEM_GIB = 3.0

NGUONG_FILE = "nguong-de-xuat.json"
KET_QUA_FILE = "ket-qua-chi-tiet.json"


def log(msg: str) -> None:
    print(f"[calibrate] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Bộ nhớ, profile
# ---------------------------------------------------------------------------


def mem_available_gib() -> float:
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / (1024 * 1024)
    return float("inf")


def wait_for_memory(min_gib: float = MIN_MEM_GIB, timeout_s: int = 1800) -> None:
    """Máy dùng chung 16 GB: chỉ nạp mô hình khi MemAvailable ≥ 3 GiB."""
    start = time.monotonic()
    while (avail := mem_available_gib()) < min_gib:
        if time.monotonic() - start > timeout_s:
            raise SystemExit(f"MemAvailable {avail:.1f} GiB < {min_gib} GiB quá {timeout_s} s")
        log(f"MemAvailable {avail:.1f} GiB < {min_gib} GiB — chờ 15 s")
        time.sleep(15)


def load_profile(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    return {"profile": d["chon"], "ten_model": d["ten_model"]}


class CachingEncoder:
    """Bọc Encoder thật: ghi nhớ vector theo văn bản để quét shingle / ablation
    không mã hóa lại cùng một câu B. Vector y hệt (mô hình tất định); KHÔNG
    dùng khi đo thời gian."""

    def __init__(self, inner: Encoder) -> None:
        self.inner = inner
        self.name = inner.name
        self.dim = inner.dim
        self._cache: dict[str, np.ndarray] = {}

    def encode(self, texts: list[str]) -> np.ndarray:
        missing = list(dict.fromkeys(t for t in texts if t not in self._cache))
        if missing:
            for t, v in zip(missing, self.inner.encode(missing)):
                self._cache[t] = v
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self._cache[t] for t in texts]).astype(np.float32)


# ---------------------------------------------------------------------------
# Dữ liệu
# ---------------------------------------------------------------------------


@dataclass
class Pair:
    ma_cap: str
    loai: str
    tap: str
    do_dai: str
    ky_vong: int
    dinh_dang: str  # "DOCX→PDF"
    a_id: int
    a_text: str
    b_text: str
    b_doan: list[dict]


@dataclass
class Data:
    titles: list[str]
    topics: list[dict]
    queries: list[dict]
    pairs: list[Pair]


def load_data(data_dir: Path) -> Data:
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    with open(data_dir / "de-tai-kho.csv", encoding="utf-8-sig", newline="") as f:
        titles = [row["ten_de_tai"] for row in csv.DictReader(f)]
    topics = sorted(manifest["topics"], key=lambda t: t["stt"])
    if len(titles) != len(topics):
        raise SystemExit("de-tai-kho.csv và manifest.topics lệch số dòng")
    for i, (title, topic) in enumerate(zip(titles, topics), start=1):
        if topic["stt"] != i or nfc(topic["ten_de_tai"]) != nfc(title):
            raise SystemExit(f"topics[{i}] không khớp dòng {i} của de-tai-kho.csv")
    with open(data_dir / "truy-van-ten-de-tai.csv", encoding="utf-8-sig", newline="") as f:
        queries = list(csv.DictReader(f))

    pairs: list[Pair] = []
    for a_id, cap in enumerate(manifest["cap"], start=1):
        texts = {}
        for side in ("A", "B"):
            meta = cap[side]
            text = extract_text((data_dir / meta["tep"]).read_bytes(), meta["dinh_dang"])
            if text is None:
                raise SystemExit(f"Không trích xuất được {meta['tep']}")
            texts[side] = text
        pairs.append(
            Pair(
                ma_cap=cap["ma_cap"],
                loai=cap["loai"],
                tap=cap["tap"],
                do_dai=cap["do_dai"],
                ky_vong=int(cap["ky_vong_canh_bao"]),
                dinh_dang=f"{cap['A']['dinh_dang']}→{cap['B']['dinh_dang']}",
                a_id=a_id,
                a_text=texts["A"],
                b_text=texts["B"],
                b_doan=cap["B"]["doan"],
            )
        )
    return Data(titles=titles, topics=topics, queries=queries, pairs=pairs)


# ---------------------------------------------------------------------------
# Kho tạm + chấm điểm
# ---------------------------------------------------------------------------


@dataclass
class Corpus:
    session: Session
    index: CorpusIndex
    shingle: int
    db_path: Path


def _migrate(db_path: Path) -> str:
    url = f"sqlite:///{db_path}"
    cfg = Config(str(SERVICE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(SERVICE_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    return url


def _signer(shingle: int) -> Callable[[str], np.ndarray]:
    # Giống app/main.py: partial(minhash.signature, k=MINHASH_SHINGLE, num_perm=...)
    return partial(minhash.signature, k=shingle, num_perm=NUM_PERM)


def build_corpus(data: Data, encoder, shingle: int, workdir: Path, tag: str = "kho") -> Corpus:
    """SQLite tạm + alembic head; nạp 300 đề tài (ARCHIVE 1..300) và 25 tài
    liệu A (DOCUMENT 1..25) qua pipeline.ingest_many — đường production."""
    db_path = workdir / f"thesis_ai-{tag}.db"
    url = _migrate(db_path)
    session = Session(create_engine(url))
    index = CorpusIndex(encoder.dim, signer=_signer(shingle))
    items = [pipeline.IngestItem(LOAI_ARCHIVE, i, t) for i, t in enumerate(data.titles, start=1)]
    items += [pipeline.IngestItem(LOAI_DOCUMENT, p.a_id, p.a_text) for p in data.pairs]
    pipeline.ingest_many(session, index, encoder, items)
    log(f"kho {tag}: {index.size(TIEU_DE)} tiêu đề, {index.size(TAI_LIEU)} câu tài liệu (shingle {shingle})")
    return Corpus(session=session, index=index, shingle=shingle, db_path=db_path)


def with_shingle(corpus: Corpus, encoder, shingle: int) -> Corpus:
    """Chỉ tính lại chữ ký MinHash: pipeline.rebuild nạp vector từ thesis_ai
    (KHÔNG encode) vào một CorpusIndex có signer k mới."""
    index = CorpusIndex(encoder.dim, signer=_signer(shingle))
    pipeline.rebuild(corpus.session, index, encoder)
    return Corpus(session=corpus.session, index=index, shingle=shingle, db_path=corpus.db_path)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip().casefold()


def label_sentences(chunks, b_doan: list[dict]) -> list[str]:
    """Câu → nhãn theo provenance của đoạn B chứa nó (so khớp chứa-trong sau
    chuẩn hóa khoảng trắng/casefold)."""
    paras = [(_norm(d["text"]), d.get("nguon")) for d in b_doan]
    labels = []
    for c in chunks:
        s = _norm(c.text)
        hit = next((nguon for text, nguon in paras if s in text), "MISSING")
        if hit == "MISSING":
            labels.append(L_KHONG_KHOP)
        elif hit is None:
            labels.append(L_TU_VIET)
        elif hit["kieu"] == "NGUYEN_VAN":
            labels.append(L_NGUYEN_VAN)
        else:
            labels.append(L_DIEN_DAT)
    return labels


@dataclass
class PairScore:
    pair: Pair
    scores: pipeline.DocumentScores
    labels: list[str] = field(default_factory=list)


def score_pair(corpus: Corpus, encoder, pair: Pair, strip: bool = True) -> PairScore:
    scores = pipeline.score_document(
        corpus.index,
        encoder,
        pair.b_text,
        {QUERY_REF_ID},
        strip=strip,
        shingle=corpus.shingle,
        num_perm=NUM_PERM,
    )
    return PairScore(pair, scores, label_sentences(scores.chunks, pair.b_doan))


def apply_thresholds(ps: PairScore, nguong_doan: float, nguong_nguyen_van: float) -> dict:
    res = pipeline.check_document(ps.scores, nguong_doan, nguong_nguyen_van, ALL, ALL)
    share = next((d["ty_le"] for d in res["do_an_trung"] if d["ref_id"] == ps.pair.a_id), 0.0)
    top = res["do_an_trung"][0]["ref_id"] if res["do_an_trung"] else None
    return {"res": res, "ty_le_nguon": share, "top_ref": top}


def best_title(corpus: Corpus, encoder, text: str) -> tuple[float, int | None]:
    matches = pipeline.check_title(corpus.index, encoder, text, TITLE_TOP_K, None)
    if not matches:
        return 0.0, None
    return matches[0]["ty_le"], matches[0]["ref_id"]


# ---------------------------------------------------------------------------
# Khớp ngưỡng
# ---------------------------------------------------------------------------


def _floor1(x: float) -> float:
    return math.floor(x * 10 + 1e-9) / 10


def fit_threshold(pos: list[float], neg: list[float]) -> dict:
    """pos/neg: điểm theo % (0–100). Gắn cờ khi điểm ≥ ngưỡng."""
    if not pos or not neg:
        raise SystemExit("fit_threshold cần cả mẫu dương và âm")
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    s = np.r_[np.asarray(pos, float), np.asarray(neg, float)]
    auc = float(roc_auc_score(y, s))
    max_neg, min_pos = float(max(neg)), float(min(pos))
    interval = [round(max_neg, 2), round(min_pos, 2)]
    if min_pos > max_neg:
        method = "trung_diem"
        value = round((min_pos + max_neg) / 2, 1)
        if value <= max_neg:
            value = _floor1(max_neg) + 0.1
        if value > min_pos:
            value = _floor1(min_pos)
    else:
        method = "youden"
        # drop_intermediate=False: thr = mọi điểm phân biệt, giảm dần (thr[0] = inf).
        fpr, tpr, thr = roc_curve(y, s, drop_intermediate=False)
        j = tpr - fpr
        i = int(np.argmax(j))  # ngưỡng CAO nhất đạt J lớn nhất
        # Mọi ngưỡng trong (thr[i+1], thr[i]] cho cùng một phân loại trên tập
        # hiệu chỉnh (cùng J) → lấy trung điểm của khoảng đó để có biên, giống
        # quy tắc trung điểm khi tách hoàn toàn (vd. câu chép nguyên văn đều có
        # Jaccard 100: ngưỡng không nên nằm sát 100).
        upper = float(thr[i])
        lower = float(thr[i + 1]) if i + 1 < len(thr) else upper
        interval = [round(lower, 2), round(upper, 2)]
        value = round((upper + lower) / 2, 1)
        if value <= lower:
            value = _floor1(lower) + 0.1
        if value > upper:
            value = _floor1(upper)
    value = round(min(max(value, 0.1), 100.0), 1)
    tp = int(np.sum(np.asarray(pos) >= value))
    fp = int(np.sum(np.asarray(neg) >= value))
    return {
        "nguong": value,
        "phuong_phap": method,
        "auc": round(auc, 4),
        "youden_j": round(tp / len(pos) - fp / len(neg), 4),
        "tpr": round(tp / len(pos), 4),
        "fpr": round(fp / len(neg), 4),
        "so_duong": len(pos),
        "so_am": len(neg),
        "min_duong": round(min_pos, 2),
        "max_am": round(max_neg, 2),
        "khoang_chon": interval,
    }


def _split(items, tap: str):
    return [x for x in items if (x.tap if hasattr(x, "tap") else x["tap"]) == tap]


# ---------------------------------------------------------------------------
# tune (chỉ HIEU_CHINH)
# ---------------------------------------------------------------------------


def cmd_tune(args) -> int:
    data = load_data(args.data)
    prof = load_profile(args.profile_from)
    pairs = [p for p in data.pairs if p.tap == HIEU_CHINH]
    queries = [q for q in data.queries if q["tap"] == HIEU_CHINH]
    log(f"tập hiệu chỉnh: {len(pairs)} cặp, {len(queries)} truy vấn tên đề tài")

    wait_for_memory()
    encoder = Encoder(prof["profile"])
    cached = CachingEncoder(encoder)
    with tempfile.TemporaryDirectory(prefix="ntma-calib-") as tmp:
        base = build_corpus(data, encoder, SHINGLE_TIE, Path(tmp))

        # (a) kích thước shingle MinHash: AUC verb_score, dương = câu chép nguyên văn
        per_k: dict[int, list[PairScore]] = {}
        auc_k: dict[int, float] = {}
        for k in SHINGLE_CANDIDATES:
            corpus = base if k == SHINGLE_TIE else with_shingle(base, encoder, k)
            per_k[k] = [score_pair(corpus, cached, p) for p in pairs]
            y, s = [], []
            for ps in per_k[k]:
                for c, lab in zip(ps.scores.chunks, ps.labels):
                    y.append(1 if lab == L_NGUYEN_VAN else 0)
                    s.append(c.verb_score)
            auc_k[k] = round(float(roc_auc_score(y, s)), 6)
            log(f"shingle {k}: AUC nguyên văn = {auc_k[k]}")
        best_auc = max(auc_k.values())
        shingle = SHINGLE_TIE if auc_k[SHINGLE_TIE] >= best_auc else max(
            (k for k in SHINGLE_CANDIDATES if auc_k[k] == best_auc)
        )
        scored = per_k[shingle]

        verb_pos, verb_neg, sem_pos, sem_neg = [], [], [], []
        label_counts = {L_NGUYEN_VAN: 0, L_DIEN_DAT: 0, L_TU_VIET: 0, L_KHONG_KHOP: 0}
        for ps in scored:
            for c, lab in zip(ps.scores.chunks, ps.labels):
                label_counts[lab] += 1
                (verb_pos if lab == L_NGUYEN_VAN else verb_neg).append(c.verb_score * 100)
                if lab == L_DIEN_DAT:
                    sem_pos.append(c.sem_score * 100)
                elif lab == L_TU_VIET:
                    sem_neg.append(c.sem_score * 100)
        # (b) nguyên văn: dương = câu chép, âm = mọi câu còn lại (kể cả diễn đạt lại)
        f_verb = fit_threshold(verb_pos, verb_neg)
        # (c) ngữ nghĩa: dương = câu diễn đạt lại, âm = câu tự viết (nguon null)
        f_sem = fit_threshold(sem_pos, sem_neg)
        # (d) ngưỡng tài liệu trên do_an_trung[A] với (b), (c) cố định
        doc_pos, doc_neg, per_pair = [], [], []
        for ps in scored:
            r = apply_thresholds(ps, f_sem["nguong"], f_verb["nguong"])
            (doc_pos if ps.pair.loai in (CHEP, DIEN) else doc_neg).append(r["ty_le_nguon"])
            per_pair.append(
                {"ma_cap": ps.pair.ma_cap, "loai": ps.pair.loai, "ty_le_nguon": r["ty_le_nguon"],
                 "ty_le_tong": r["res"]["ty_le_tong"]}
            )
        f_doc = fit_threshold(doc_pos, doc_neg)
        # (e) tên đề tài: dương = truy vấn DIEN_DAT_LAI
        t_pos, t_neg = [], []
        for q in queries:
            best, _ = best_title(base, encoder, q["ten_truy_van"])
            (t_pos if q["loai"] == DIEN else t_neg).append(best)
        f_title = fit_threshold(t_pos, t_neg)

    out = {
        "profile": prof["profile"],
        "ten_model": prof["ten_model"],
        "minhash_shingle": shingle,
        "minhash_num_perm": NUM_PERM,
        "nguong_ten_de_tai": f_title["nguong"],
        "nguong_doan": f_sem["nguong"],
        "nguong_nguyen_van": f_verb["nguong"],
        "nguong_tai_lieu": f_doc["nguong"],
        "phuong_phap": {
            "nguong_ten_de_tai": f_title["phuong_phap"],
            "nguong_doan": f_sem["phuong_phap"],
            "nguong_nguyen_van": f_verb["phuong_phap"],
            "nguong_tai_lieu": f_doc["phuong_phap"],
            "minhash_shingle": "auc_lon_nhat",
        },
        "auc": {
            "ten_de_tai": f_title["auc"],
            "ngu_nghia_cau": f_sem["auc"],
            "nguyen_van_cau": f_verb["auc"],
            "tai_lieu": f_doc["auc"],
            "nguyen_van_theo_shingle": {str(k): v for k, v in auc_k.items()},
        },
        "so_mau": {
            "ten_de_tai": {"duong": f_title["so_duong"], "am": f_title["so_am"]},
            "ngu_nghia_cau": {"duong": f_sem["so_duong"], "am": f_sem["so_am"]},
            "nguyen_van_cau": {"duong": f_verb["so_duong"], "am": f_verb["so_am"]},
            "tai_lieu": {"duong": f_doc["so_duong"], "am": f_doc["so_am"]},
        },
        "chi_tiet_khop": {
            "ten_de_tai": f_title,
            "ngu_nghia_cau": f_sem,
            "nguyen_van_cau": f_verb,
            "tai_lieu": f_doc,
            "tai_lieu_theo_cap": per_pair,
            "nhan_cau": label_counts,
        },
        "don_vi": "phan_tram_mot_chu_so_thap_phan; gan_co_khi_diem >= nguong",
        "tap": HIEU_CHINH,
        "ngay": date.today().isoformat(),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / NGUONG_FILE
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(
        f"đã ghi {path}: tên đề tài {out['nguong_ten_de_tai']} | đoạn {out['nguong_doan']} | "
        f"nguyên văn {out['nguong_nguyen_van']} | tài liệu {out['nguong_tai_lieu']} | shingle {shingle}"
    )
    return 0


# ---------------------------------------------------------------------------
# evaluate (ngưỡng cố định, mọi cặp; KIEM_CHUNG báo cáo riêng)
# ---------------------------------------------------------------------------


def _no_strip(text: str) -> StripResult:
    return StripResult(lines=[line for line in nfc(text).split("\n") if line], removed=0)


def _acc(rows: list[dict]) -> dict:
    n = len(rows)
    ok = sum(1 for r in rows if r["dat"])
    return {"dat": ok, "tong": n, "ty_le": round(ok / n, 4) if n else None}


def _p95(values: list[float]) -> float:
    return round(float(np.percentile(values, 95)), 1)


_VI_TRI_RE = re.compile(r"^Câu (\d+)(?:–(\d+))?$")


def flagged_positions(res: dict) -> set[int]:
    """Vị trí câu bị gắn cờ, dựng lại từ chi_tiet của check_document (đủ khi
    chi_tiet_toi_da không giới hạn) — đúng quy tắc production kể cả luật chuỗi."""
    out: set[int] = set()
    for d in res["chi_tiet"]:
        m = _VI_TRI_RE.match(d["vi_tri"])
        first = int(m.group(1))
        out.update(range(first, int(m.group(2) or first) + 1))
    return out


def sentence_rates(scored: list[PairScore], nd: float, nv: float) -> dict:
    """Tỷ lệ câu bị gắn cờ theo nhãn, theo đúng kết quả check_document."""
    counts: dict[str, list[int]] = {}
    for ps in scored:
        flagged_at = flagged_positions(apply_thresholds(ps, nd, nv)["res"])
        for c, lab in zip(ps.scores.chunks, ps.labels):
            flagged = c.vi_tri in flagged_at
            tot = counts.setdefault(lab, [0, 0])
            tot[0] += int(flagged)
            tot[1] += 1
    return {lab: {"gan_co": a, "tong": b, "ty_le": round(a / b, 4)} for lab, (a, b) in sorted(counts.items())}


def cmd_evaluate(args) -> int:
    nguong = json.loads((args.out / NGUONG_FILE).read_text(encoding="utf-8"))
    prof = load_profile(args.profile_from)
    if prof["profile"] != nguong["profile"]:
        raise SystemExit(
            f"Profile đã chốt ({prof['profile']}) khác profile lúc hiệu chỉnh ({nguong['profile']}) — chạy lại tune"
        )
    nd, nv = nguong["nguong_doan"], nguong["nguong_nguyen_van"]
    nt, ntl = nguong["nguong_ten_de_tai"], nguong["nguong_tai_lieu"]
    shingle = nguong["minhash_shingle"]
    data = load_data(args.data)

    wait_for_memory()
    encoder = Encoder(prof["profile"])
    cached = CachingEncoder(encoder)
    with tempfile.TemporaryDirectory(prefix="ntma-calib-") as tmp:
        corpus = build_corpus(data, encoder, shingle, Path(tmp))
        so_tieu_de, so_cau_kho = corpus.index.size(TIEU_DE), corpus.index.size(TAI_LIEU)

        # --- cặp tài liệu ---
        scored = [score_pair(corpus, cached, p) for p in data.pairs]
        cap = []
        for ps in scored:
            p, r = ps.pair, apply_thresholds(ps, nd, nv)
            res = r["res"]
            flagged = r["ty_le_nguon"] >= ntl
            cap.append(
                {
                    "ma_cap": p.ma_cap,
                    "loai": p.loai,
                    "tap": p.tap,
                    "do_dai": p.do_dai,
                    "dinh_dang": p.dinh_dang,
                    "so_cau": res["so_doan"],
                    "so_dong_loai_tru": res["so_doan_loai_tru"],
                    "ty_le_tong": res["ty_le_tong"],
                    "ty_le_nguon": r["ty_le_nguon"],
                    "nguon_dung_dau": r["top_ref"] == p.a_id,
                    "so_doan_trung": len(res["chi_tiet"]),
                    "so_doan_nguyen_van": sum(1 for d in res["chi_tiet"] if d["tin_hieu"] == pipeline.NGUYEN_VAN),
                    "so_doan_ngu_nghia": sum(1 for d in res["chi_tiet"] if d["tin_hieu"] == pipeline.NGU_NGHIA),
                    "bi_canh_bao": flagged,
                    "ky_vong": bool(p.ky_vong),
                    "dat": flagged == bool(p.ky_vong),
                    "max_ngu_nghia_cau_tu_viet": round(
                        max([c.sem_score * 100 for c, lab in zip(ps.scores.chunks, ps.labels) if lab == L_TU_VIET],
                            default=0.0), 2),
                }
            )

        # --- truy vấn tên đề tài ---
        truy_van = []
        for q in data.queries:
            best, ref = best_title(corpus, encoder, q["ten_truy_van"])
            flagged = best >= nt
            top_obj = data.topics[ref - 1]["ma_doi_tuong"] if ref else None
            truy_van.append(
                {
                    "ma_truy_van": q["ma_truy_van"],
                    "loai": q["loai"],
                    "tap": q["tap"],
                    "ty_le_cao_nhat": best,
                    "top1_ref": ref,
                    "top1_dung_doi_tuong": (top_obj == q["ma_doi_tuong"]) if q["loai"] == DIEN else None,
                    "bi_canh_bao": flagged,
                    "ky_vong": q["ky_vong_canh_bao"] == "1",
                    "dat": flagged == (q["ky_vong_canh_bao"] == "1"),
                }
            )

        # --- cổng ---
        chep = [c for c in cap if c["loai"] == CHEP]
        khong = [c for c in cap if c["loai"] == KHONG]
        g1 = all(c["bi_canh_bao"] for c in chep)
        g2 = all(c["ty_le_nguon"] < ntl and c["ty_le_tong"] < ntl for c in khong)
        acc_kc = _acc(_split(cap, KIEM_CHUNG))
        acc_hc = _acc(_split(cap, HIEU_CHINH))
        g3 = acc_kc["ty_le"] is not None and acc_kc["ty_le"] >= 0.85

        acc_theo_loai = {
            tap: {loai: _acc([c for c in _split(cap, tap) if c["loai"] == loai]) for loai in LOAI_CAP}
            for tap in (HIEU_CHINH, KIEM_CHUNG)
        }
        title_acc = {}
        for tap in (HIEU_CHINH, KIEM_CHUNG):
            rows = _split(truy_van, tap)
            dien = [r for r in rows if r["loai"] == DIEN]
            title_acc[tap] = {
                "chung": _acc(rows),
                DIEN: _acc([r for r in rows if r["loai"] == DIEN]),
                CUNG: _acc([r for r in rows if r["loai"] == CUNG]),
                "top1_dung_doi_tuong": {
                    "dat": sum(1 for r in dien if r["top1_dung_doi_tuong"]),
                    "tong": len(dien),
                    "ty_le": round(sum(1 for r in dien if r["top1_dung_doi_tuong"]) / len(dien), 4),
                },
            }
        cau = {tap: sentence_rates([ps for ps in scored if ps.pair.tap == tap], nd, nv)
               for tap in (HIEU_CHINH, KIEM_CHUNG)}

        # --- ablation: tắt lọc phần mẫu chung ---
        abl_pairs = [ps.pair for ps in scored if ps.pair.loai in (CUNG, KHONG)]
        ablation = []
        # (i) chỉ tài liệu nộp không lọc, kho vẫn nạp như production
        only_query = {p.ma_cap: apply_thresholds(score_pair(corpus, cached, p, strip=False), nd, nv)
                      for p in abl_pairs}
        # (ii) không lọc ở CẢ kho lẫn tài liệu nộp (hệ thống không có bước lọc)
        original = pipeline.strip_boilerplate
        pipeline.strip_boilerplate = _no_strip
        try:
            raw = build_corpus(data, cached, shingle, Path(tmp), tag="khong-loc")
        finally:
            pipeline.strip_boilerplate = original
        both = {p.ma_cap: apply_thresholds(score_pair(raw, cached, p, strip=False), nd, nv) for p in abl_pairs}
        by_code = {c["ma_cap"]: c for c in cap}
        for p in abl_pairs:
            c = by_code[p.ma_cap]
            ablation.append(
                {
                    "ma_cap": p.ma_cap,
                    "loai": p.loai,
                    "tap": p.tap,
                    "so_dong_loai_tru": c["so_dong_loai_tru"],
                    "ty_le_tong_co_loc": c["ty_le_tong"],
                    "ty_le_tong_khong_loc_tai_lieu_nop": only_query[p.ma_cap]["res"]["ty_le_tong"],
                    "ty_le_tong_khong_loc_ca_kho": both[p.ma_cap]["res"]["ty_le_tong"],
                    "ty_le_nguon_co_loc": c["ty_le_nguon"],
                    "ty_le_nguon_khong_loc_ca_kho": both[p.ma_cap]["ty_le_nguon"],
                    "tang_them_khong_loc_ca_kho": round(
                        both[p.ma_cap]["res"]["ty_le_tong"] - c["ty_le_tong"], 2),
                    "bi_canh_bao_khong_loc_ca_kho": both[p.ma_cap]["ty_le_nguon"] >= ntl,
                }
            )
        raw.session.close()

        # --- độ trễ trong tiến trình (encoder thật, không cache) ---
        pipeline.check_title(corpus.index, encoder, data.queries[-1]["ten_truy_van"], TITLE_TOP_K, nt)  # khởi động
        t_title = []
        for q in data.queries[:20]:
            t0 = time.perf_counter()
            pipeline.check_title(corpus.index, encoder, q["ten_truy_van"], TITLE_TOP_K, nt)
            t_title.append((time.perf_counter() - t0) * 1000)
        t_doc = []
        for p in data.pairs[:20]:
            t0 = time.perf_counter()
            s = pipeline.score_document(corpus.index, encoder, p.b_text, {QUERY_REF_ID},
                                        shingle=shingle, num_perm=NUM_PERM)
            pipeline.check_document(s, nd, nv, Settings.model_fields["TOP_K_MAC_DINH"].default,
                                    Settings.model_fields["CHI_TIET_TOI_DA"].default)
            t_doc.append((time.perf_counter() - t0) * 1000)
        latency = {
            "moi_truong": "trong tiến trình, máy phát triển (dùng chung), CPU; không gồm HTTP/Web API",
            "so_cpu": os.cpu_count(),
            "torch_threads": 4,
            "kho": {"tieu_de": so_tieu_de, "cau_tai_lieu": so_cau_kho},
            "check_title_ms": {"n": len(t_title), "p50": round(float(np.median(t_title)), 1),
                               "p95": _p95(t_title), "max": round(max(t_title), 1)},
            "check_document_ms": {"n": len(t_doc), "p50": round(float(np.median(t_doc)), 1),
                                  "p95": _p95(t_doc), "max": round(max(t_doc), 1)},
            "nfr": {"NFR-08_check_title_p95_ms": 5000, "NFR-09_check_document_p95_ms": 30000},
        }
        corpus.session.close()

    out = {
        "nguong": {k: nguong[k] for k in ("profile", "ten_model", "minhash_shingle", "nguong_ten_de_tai",
                                          "nguong_doan", "nguong_nguyen_van", "nguong_tai_lieu", "phuong_phap",
                                          "auc", "so_mau", "ngay")},
        "gates": {
            "g1": g1,
            "g2": g2,
            "g3": g3,
            "accuracy_kiem_chung": acc_kc["ty_le"],
            "accuracy_hieu_chinh": acc_hc["ty_le"],
            "mo_ta": {
                "g1": "mọi cặp CHEP_NGUYEN_VAN bị cảnh báo (cứng)",
                "g2": "mọi cặp KHONG_LIEN_QUAN có tỷ lệ theo đồ án nguồn và tỷ lệ tổng < ngưỡng tài liệu (cứng)",
                "g3": "độ chính xác cặp trên KIEM_CHUNG ≥ 0.85 (mềm)",
            },
        },
        "accuracy_theo_tap_loai": acc_theo_loai,
        "cap": cap,
        "truy_van": truy_van,
        "title_accuracy": title_acc,
        "cau": cau,
        "ablation": ablation,
        "latency": latency,
        "ngay": date.today().isoformat(),
    }
    path = args.out / KET_QUA_FILE
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"đã ghi {path}: G1={g1} G2={g2} G3={g3} (KIEM_CHUNG {acc_kc['dat']}/{acc_kc['tong']}, "
        f"HIEU_CHINH {acc_hc['dat']}/{acc_hc['tong']})")

    if args.report:
        args.report.write_text(render_report(nguong, out), encoding="utf-8")
        log(f"đã ghi {args.report}")
    if args.apply:
        apply_defaults(nguong)
    return 0 if (g1 and g2) else 1


# ---------------------------------------------------------------------------
# --apply: mặc định của dịch vụ AI = giá trị hiệu chỉnh (D-04)
# ---------------------------------------------------------------------------

README_START = "<!-- hieu-chinh:start -->"
README_END = "<!-- hieu-chinh:end -->"


def _sub_once(pattern: str, repl: str, text: str, what: str) -> str:
    new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        raise SystemExit(f"--apply: không tìm thấy {what}")
    return new


def apply_defaults(nguong: dict) -> None:
    note = f"# hiệu chỉnh: calibration/{NGUONG_FILE} ({nguong['ngay']})"
    cfg = SERVICE_DIR / "app" / "core" / "config.py"
    text = cfg.read_text(encoding="utf-8")
    text = _sub_once(r'^(\s*AI_MODEL_PROFILE: Literal\[[^\]]*\] = )"[^"]*".*$',
                     rf'\g<1>"{nguong["profile"]}"  {note}', text, "AI_MODEL_PROFILE")
    text = _sub_once(r"^(\s*NGUONG_DOAN_MAC_DINH: float = )[0-9.]+.*$",
                     rf"\g<1>{nguong['nguong_doan']}  {note}", text, "NGUONG_DOAN_MAC_DINH")
    text = _sub_once(r"^(\s*NGUONG_NGUYEN_VAN_MAC_DINH: float = )[0-9.]+.*$",
                     rf"\g<1>{nguong['nguong_nguyen_van']}  {note}", text, "NGUONG_NGUYEN_VAN_MAC_DINH")
    text = _sub_once(r"^(\s*MINHASH_SHINGLE: int = )[0-9]+.*$",
                     rf"\g<1>{nguong['minhash_shingle']}  {note}", text, "MINHASH_SHINGLE")
    cfg.write_text(text, encoding="utf-8")

    readme = SERVICE_DIR / "README.md"
    text = readme.read_text(encoding="utf-8")
    src = f"hiệu chỉnh — `calibration/{NGUONG_FILE}` ({nguong['ngay']})"
    rows = {
        "AI_MODEL_PROFILE": (f"`{nguong['profile']}`", f"`bkai` \\| `e5` \\| `fake` (chỉ khi `APP_ENV=test`); {src}"),
        "NGUONG_DOAN_MAC_DINH": (f"`{nguong['nguong_doan']}`",
                                 f"Ngưỡng ngữ nghĩa (cosine×100) khi request không gửi; {src}"),
        "NGUONG_NGUYEN_VAN_MAC_DINH": (f"`{nguong['nguong_nguyen_van']}`",
                                       f"Ngưỡng nguyên văn (Jaccard×100) khi request không gửi; {src}"),
        "MINHASH_SHINGLE": (f"`{nguong['minhash_shingle']}`", f"k của k-gram âm tiết cho MinHash; {src}"),
    }
    for var, (val, desc) in rows.items():
        text = _sub_once(rf"^\| `{var}` \|[^\n]*$", f"| `{var}` | {val} | | {desc} |", text, f"dòng README {var}")
    text = re.sub(r"k-gram âm tiết \(k = \d+, ", f"k-gram âm tiết (k = {nguong['minhash_shingle']}, ", text)
    block = "\n".join(
        [
            README_START,
            f"Giá trị do `calibration/calibrate.py tune` khớp trên tập HIEU_CHINH ({nguong['ngay']}, "
            f"mô hình `{nguong['ten_model']}`), kiểm chứng bằng `evaluate`:",
            "",
            "| Ngưỡng | Giá trị (%) | Phương pháp | Dùng ở |",
            "|---|---:|---|---|",
            f"| `nguong_ten_de_tai` | {nguong['nguong_ten_de_tai']} | {nguong['phuong_phap']['nguong_ten_de_tai']} "
            "| Web API gửi trong `/check-title` (`cau_hinh_nguong`, plan 04-05) |",
            f"| `nguong_doan` | {nguong['nguong_doan']} | {nguong['phuong_phap']['nguong_doan']} "
            "| `/check-document`; mặc định `NGUONG_DOAN_MAC_DINH` |",
            f"| `nguong_nguyen_van` | {nguong['nguong_nguyen_van']} | {nguong['phuong_phap']['nguong_nguyen_van']} "
            "| `/check-document`; mặc định `NGUONG_NGUYEN_VAN_MAC_DINH` |",
            f"| `nguong_tai_lieu` | {nguong['nguong_tai_lieu']} | {nguong['phuong_phap']['nguong_tai_lieu']} "
            "| Web API: cảnh báo khi tỷ lệ theo một đồ án ≥ ngưỡng (plan 04-05) |",
            f"| `MINHASH_SHINGLE` | {nguong['minhash_shingle']} | AUC lớn nhất trong {{3, 4, 5}} | chữ ký MinHash |",
            "",
            "Chạy lại (từ `ai-service/`, cần ≥ 3 GiB RAM trống, không cần docker/MySQL):",
            "",
            "```bash",
            "uv run python calibration/calibrate.py tune --data ../seed-data \\",
            "  --profile-from ../tools/bakeoff/ket-qua.json --out calibration",
            "uv run python calibration/calibrate.py evaluate --data ../seed-data \\",
            "  --profile-from ../tools/bakeoff/ket-qua.json --out calibration \\",
            "  --report ../docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md --apply",
            "```",
            README_END,
        ]
    )
    if README_START in text:
        text = re.sub(re.escape(README_START) + r".*?" + re.escape(README_END), lambda _: block, text, flags=re.S)
    else:
        raise SystemExit("--apply: README thiếu khối <!-- hieu-chinh:start --> … <!-- hieu-chinh:end -->")
    readme.write_text(text, encoding="utf-8")
    log(f"--apply: đã cập nhật {cfg.relative_to(SERVICE_DIR)} và README.md")


# ---------------------------------------------------------------------------
# Báo cáo chương 4 — mọi con số lấy từ JSON
# ---------------------------------------------------------------------------

TEN_LOAI = {
    CHEP: "Chép nguyên văn",
    DIEN: "Diễn đạt lại",
    CUNG: "Cùng lĩnh vực",
    KHONG: "Không liên quan",
}
TEN_PP = {"youden": "Youden J (roc_curve)", "trung_diem": "Trung điểm (tách hoàn toàn)",
          "auc_lon_nhat": "AUC lớn nhất"}


def _yn(b: bool) -> str:
    return "Có" if b else "Không"


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f}"


def _acc_str(a: dict) -> str:
    return "—" if not a["tong"] else f"{a['dat']}/{a['tong']} ({a['ty_le']:.3f})"


def render_report(nguong: dict, kq: dict) -> str:
    g = kq["gates"]
    ck = nguong["chi_tiet_khop"]
    L: list[str] = []
    a = L.append
    a("## 4.x.3 Hiệu chỉnh và kiểm chứng ngưỡng cảnh báo trùng lặp")
    a("")
    a("> **Mã PI:** 3.4 — **Yêu cầu:** DATA-03, AISV-03, AISV-04")
    a("")
    a("<!-- Tệp này do `ai-service/calibration/calibrate.py evaluate --report` sinh ra từ "
      "`calibration/nguong-de-xuat.json` và `calibration/ket-qua-chi-tiet.json`; không sửa tay. -->")
    a("")
    a("### Mục tiêu")
    a("")
    a("Dịch vụ AI cảnh báo trùng lặp dựa trên bốn ngưỡng: ngưỡng tên đề tài khi sinh viên đăng ký (AISV-03), "
      "ngưỡng ngữ nghĩa và ngưỡng nguyên văn ở mức câu, và ngưỡng tài liệu quyết định một bài nộp có bị cảnh báo "
      "trùng với một đồ án trong kho hay không (AISV-04). Theo quyết định D-04, giá trị mặc định của các ngưỡng "
      "**phải đến từ hiệu chỉnh** chứ không đặt theo cảm tính. Theo D-06, ngưỡng chỉ được khớp trên tập hiệu chỉnh "
      "(`HIEU_CHINH`) rồi giữ nguyên để kiểm chứng trên tập giữ lại (`KIEM_CHUNG`). Mục này cung cấp bảng kiểm chứng "
      "theo từng cặp tài liệu mà DATA-03 và tiêu chí thành công số 3 của Phase 4 yêu cầu.")
    a("")
    a("### Dữ liệu và mô hình")
    a("")
    n_tv = {tap: sum(1 for r in kq["truy_van"] if r["tap"] == tap) for tap in (HIEU_CHINH, KIEM_CHUNG)}
    n_cap = {tap: sum(1 for r in kq["cap"] if r["tap"] == tap) for tap in (HIEU_CHINH, KIEM_CHUNG)}
    a(f"- Bộ dữ liệu tổng hợp mô tả ở [mục 4.x.1](01-du-lieu-thu-nghiem.md): kho {kq['latency']['kho']['tieu_de']} "
      f"đề tài khóa K18–K22, 25 cặp tài liệu A/B (DOCX/PDF) và {len(kq['truy_van'])} truy vấn tên đề tài có nhãn.")
    a(f"- Tập hiệu chỉnh: {n_cap[HIEU_CHINH]} cặp, {n_tv[HIEU_CHINH]} truy vấn. "
      f"Tập kiểm chứng (giữ lại, không dùng để khớp): {n_cap[KIEM_CHUNG]} cặp, {n_tv[KIEM_CHUNG]} truy vấn.")
    a(f"- Mô hình embedding đã chốt ở [mục 4.x.2](02-so-sanh-mo-hinh-embedding.md): `{nguong['ten_model']}` "
      f"(profile `{nguong['profile']}`).")
    a("- Văn bản được trích xuất bằng bản sao đúng từng dòng của hàm `extract_text` phía Web API, rồi đi qua đúng "
      "pipeline của dịch vụ AI (`ingest` → `score_document` → `check_document`, `check_title`). Kho được dựng trên "
      "một cơ sở dữ liệu SQLite tạm theo cùng migration với MySQL. Tài liệu A được nạp vào kho; tài liệu B chỉ được "
      "kiểm tra, giống như bài nộp mới được kiểm tra trước khi vào kho.")
    a("")
    a("### Phương pháp")
    a("")
    a("1. **Mức câu.** Mỗi câu của tài liệu B (sau khi lọc phần mẫu chung) có hai điểm: cosine embedding tốt nhất "
      "(ngữ nghĩa) và Jaccard MinHash tốt nhất trên k-gram âm tiết (nguyên văn) so với mọi câu trong kho. Nhãn của câu "
      "lấy từ nguồn gốc đoạn văn ghi trong manifest: *chép nguyên văn*, *diễn đạt lại* hoặc *tự viết*.")
    a("2. **Ngưỡng nguyên văn**: dương = câu chép nguyên văn, âm = mọi câu còn lại (kể cả câu diễn đạt lại, vốn để "
      "tín hiệu ngữ nghĩa xử lý). **Ngưỡng đoạn (ngữ nghĩa)**: dương = câu diễn đạt lại, âm = câu tự viết.")
    a("3. **Ngưỡng tài liệu**: với hai ngưỡng câu đã cố định, `check_document` cho tỷ lệ ký tự của B bị gán cho "
      "đồ án nguồn A (*tỷ lệ theo đồ án nguồn*). Cặp bị cảnh báo khi tỷ lệ này ≥ ngưỡng tài liệu. Dương = cặp chép "
      "nguyên văn và diễn đạt lại. *Tỷ lệ tổng* (phần của B khớp với bất kỳ tài liệu nào trong kho) được báo cáo kèm.")
    a("4. **Ngưỡng tên đề tài**: điểm cao nhất của `check_title` trên kho 300 đề tài; dương = truy vấn diễn đạt lại "
      "một đề tài có trong kho.")
    a("5. **Cách chọn ngưỡng**: `sklearn.metrics.roc_curve` và chỉ số **Youden J = TPR − FPR**. Mọi ngưỡng nằm "
      "giữa điểm đạt J lớn nhất và điểm liền dưới nó cho cùng một kết quả phân loại trên tập hiệu chỉnh, nên ngưỡng "
      "được đặt ở **trung điểm của khoảng đó** (cột *Khoảng chọn*). Khi tín hiệu tách hoàn toàn tập hiệu chỉnh, dùng "
      "**trung điểm** giữa điểm âm lớn nhất và điểm dương nhỏ nhất để có biên an toàn. Ngưỡng tính theo %, một chữ số "
      "thập phân; gắn cờ khi điểm ≥ ngưỡng. Kích thước shingle MinHash chọn trong {3, 4, 5} theo AUC nguyên văn lớn "
      "nhất (hòa → 4).")
    a(f"6. **Luật đoạn cho tín hiệu ngữ nghĩa**: `check_document` chỉ giữ cờ ngữ nghĩa của một câu khi câu đó nằm trong "
      f"chuỗi ít nhất {pipeline.MIN_RUN_NGU_NGHIA} câu liên tiếp bị gắn cờ cùng một đồ án nguồn; cờ nguyên văn đứng "
      "một mình vẫn được giữ. Lý do (quan sát trên tập hiệu chỉnh): câu tự viết theo khuôn câu chung của lĩnh vực "
      "thường có cosine cao với *một câu lẻ* của đồ án khác, trong khi phần diễn đạt lại luôn đi thành đoạn liền nhau.")
    a("")
    a("### Ngưỡng đã chốt (khớp trên tập HIEU_CHINH)")
    a("")
    a("| Ngưỡng | Giá trị (%) | Phương pháp | AUC tập hiệu chỉnh | Số mẫu (dương / âm) | Dương nhỏ nhất | Âm lớn nhất | "
      "Khoảng chọn | TPR / FPR tại ngưỡng |")
    a("|---|---:|---|---:|---|---:|---:|---|---|")
    for key, sig, ten in (
        ("nguong_ten_de_tai", "ten_de_tai", "Tên đề tài"),
        ("nguong_doan", "ngu_nghia_cau", "Đoạn — ngữ nghĩa (câu)"),
        ("nguong_nguyen_van", "nguyen_van_cau", "Đoạn — nguyên văn (câu)"),
        ("nguong_tai_lieu", "tai_lieu", "Tài liệu (theo đồ án nguồn)"),
    ):
        f = ck[sig]
        a(f"| {ten} (`{key}`) | {nguong[key]} | {TEN_PP[nguong['phuong_phap'][key]]} | {f['auc']:.4f} | "
          f"{f['so_duong']} / {f['so_am']} | {f['min_duong']:.2f} | {f['max_am']:.2f} | "
          f"({f['khoang_chon'][0]:.2f}; {f['khoang_chon'][1]:.2f}] | {f['tpr']:.3f} / {f['fpr']:.3f} |")
    auc_k = nguong["auc"]["nguyen_van_theo_shingle"]
    a("")
    a(f"Shingle MinHash: **k = {nguong['minhash_shingle']}** (AUC nguyên văn trên tập hiệu chỉnh: "
      + ", ".join(f"k = {k}: {v:.4f}" for k, v in auc_k.items()) + f"; {nguong['minhash_num_perm']} hoán vị).")
    nh = ck["nhan_cau"]
    a(f"Số câu B của tập hiệu chỉnh theo nhãn: chép nguyên văn {nh[L_NGUYEN_VAN]}, diễn đạt lại {nh[L_DIEN_DAT]}, "
      f"tự viết {nh[L_TU_VIET]}, không khớp đoạn nội dung nào {nh[L_KHONG_KHOP]}.")
    a("")
    a("### Kết quả kiểm chứng theo cặp tài liệu (ngưỡng cố định)")
    a("")
    a(f"Ngưỡng áp dụng: đoạn {nguong['nguong_doan']} %, nguyên văn {nguong['nguong_nguyen_van']} %, "
      f"tài liệu {nguong['nguong_tai_lieu']} %. Cột *Đoạn trùng* đếm các đoạn trùng mà `check_document` trả về "
      "(nguyên văn / ngữ nghĩa).")
    for tap, ten in ((HIEU_CHINH, "Tập hiệu chỉnh (HIEU_CHINH) — dùng để khớp ngưỡng"),
                     (KIEM_CHUNG, "Tập kiểm chứng (KIEM_CHUNG) — giữ lại, không dùng để khớp")):
        a("")
        a(f"#### {ten}")
        a("")
        a("| Mã cặp | Loại | Tập | Định dạng A→B | Tỷ lệ tổng (%) | Tỷ lệ theo đồ án nguồn (%) | A dẫn đầu? | "
          "Đoạn trùng (nguyên văn / ngữ nghĩa) | Bị cảnh báo? | Kỳ vọng | Kết quả |")
        a("|---|---|---|---|---:|---:|---|---|---|---|---|")
        for c in _split(kq["cap"], tap):
            a(f"| {c['ma_cap']} | {TEN_LOAI[c['loai']]} | {c['tap']} | {c['dinh_dang']} | {_pct(c['ty_le_tong'])} | "
              f"{_pct(c['ty_le_nguon'])} | {_yn(c['nguon_dung_dau'])} | {c['so_doan_nguyen_van']} / "
              f"{c['so_doan_ngu_nghia']} | {_yn(c['bi_canh_bao'])} | {'Cảnh báo' if c['ky_vong'] else 'Không cảnh báo'} | "
              f"{'Đạt' if c['dat'] else 'Không đạt'} |")
    a("")
    a("#### Độ chính xác theo tập và loại cặp")
    a("")
    a("| Loại cặp | HIEU_CHINH | KIEM_CHUNG |")
    a("|---|---|---|")
    for loai in LOAI_CAP:
        a(f"| {TEN_LOAI[loai]} | {_acc_str(kq['accuracy_theo_tap_loai'][HIEU_CHINH][loai])} | "
          f"{_acc_str(kq['accuracy_theo_tap_loai'][KIEM_CHUNG][loai])} |")
    acc_all = {tap: _acc(_split(kq["cap"], tap)) for tap in (HIEU_CHINH, KIEM_CHUNG)}
    a(f"| **Tất cả** | **{_acc_str(acc_all[HIEU_CHINH])}** | **{_acc_str(acc_all[KIEM_CHUNG])}** |")
    a("")
    a("| Cổng | Điều kiện | Kết quả |")
    a("|---|---|---|")
    a(f"| G1 (cứng) | {g['mo_ta']['g1']} | {'Đạt' if g['g1'] else 'Không đạt'} |")
    a(f"| G2 (cứng) | {g['mo_ta']['g2']} | {'Đạt' if g['g2'] else 'Không đạt'} |")
    a(f"| G3 (mềm) | {g['mo_ta']['g3']} — thực tế {g['accuracy_kiem_chung']:.3f} | "
      f"{'Đạt' if g['g3'] else 'Không đạt'} |")
    a("")
    a("#### Tỷ lệ câu bị gắn cờ theo nhãn (mức câu)")
    a("")
    a("| Nhãn câu | HIEU_CHINH | KIEM_CHUNG |")
    a("|---|---|---|")
    ten_nhan = {L_NGUYEN_VAN: "Chép nguyên văn", L_DIEN_DAT: "Diễn đạt lại", L_TU_VIET: "Tự viết (dương tính giả)",
                L_KHONG_KHOP: "Không khớp đoạn nội dung"}
    for lab in (L_NGUYEN_VAN, L_DIEN_DAT, L_TU_VIET, L_KHONG_KHOP):
        cells = []
        for tap in (HIEU_CHINH, KIEM_CHUNG):
            r = kq["cau"][tap].get(lab)
            cells.append("—" if r is None else f"{r['gan_co']}/{r['tong']} ({r['ty_le']:.3f})")
        a(f"| {ten_nhan[lab]} | {cells[0]} | {cells[1]} |")
    a("")
    a("### Kết quả kiểm tra tên đề tài")
    a("")
    a(f"Ngưỡng tên đề tài {nguong['nguong_ten_de_tai']} %: truy vấn bị cảnh báo khi điểm cao nhất ≥ ngưỡng. "
      "*Top-1 đúng đối tượng* = đề tài đứng đầu có cùng đối tượng nghiệp vụ với đề tài gốc (chỉ xét truy vấn "
      "diễn đạt lại).")
    a("")
    a("| Chỉ số | HIEU_CHINH | KIEM_CHUNG |")
    a("|---|---|---|")
    ta = kq["title_accuracy"]
    a(f"| Độ chính xác chung | {_acc_str(ta[HIEU_CHINH]['chung'])} | {_acc_str(ta[KIEM_CHUNG]['chung'])} |")
    a(f"| Diễn đạt lại → cảnh báo | {_acc_str(ta[HIEU_CHINH][DIEN])} | {_acc_str(ta[KIEM_CHUNG][DIEN])} |")
    a(f"| Cùng lĩnh vực → không cảnh báo | {_acc_str(ta[HIEU_CHINH][CUNG])} | {_acc_str(ta[KIEM_CHUNG][CUNG])} |")
    a(f"| Top-1 đúng đối tượng | {_acc_str(ta[HIEU_CHINH]['top1_dung_doi_tuong'])} | "
      f"{_acc_str(ta[KIEM_CHUNG]['top1_dung_doi_tuong'])} |")
    a("")
    a("### Ảnh hưởng của bước lọc phần mẫu chung (ablation, AISV-04)")
    a("")
    a("Các cặp cùng lĩnh vực và không liên quan được chấm lại khi **tắt** bước lọc phần mẫu chung (bìa, lời cam đoan, "
      "lời cảm ơn, mục lục, tiêu đề mục, tài liệu tham khảo, header/footer). Cột *chỉ tài liệu nộp* tắt lọc ở phía "
      "bài nộp, kho giữ nguyên như production. Cột *cả kho* tắt lọc ở cả hai phía, tức là một hệ thống không có "
      "bước lọc. Ngưỡng giữ nguyên.")
    a("")
    a("| Mã cặp | Loại | Tập | Dòng bị lọc | Tỷ lệ tổng khi lọc (%) | Không lọc — chỉ tài liệu nộp (%) | "
      "Không lọc — cả kho (%) | Tăng thêm (điểm %) | Tỷ lệ theo đồ án nguồn khi không lọc (%) | Bị cảnh báo khi không lọc? |")
    a("|---|---|---|---:|---:|---:|---:|---:|---:|---|")
    for r in kq["ablation"]:
        a(f"| {r['ma_cap']} | {TEN_LOAI[r['loai']]} | {r['tap']} | {r['so_dong_loai_tru']} | "
          f"{_pct(r['ty_le_tong_co_loc'])} | {_pct(r['ty_le_tong_khong_loc_tai_lieu_nop'])} | "
          f"{_pct(r['ty_le_tong_khong_loc_ca_kho'])} | {r['tang_them_khong_loc_ca_kho']:+.2f} | "
          f"{_pct(r['ty_le_nguon_khong_loc_ca_kho'])} | {_yn(r['bi_canh_bao_khong_loc_ca_kho'])} |")
    extra = [r["tang_them_khong_loc_ca_kho"] for r in kq["ablation"]]
    a("")
    a(f"Trung bình tỷ lệ tổng tăng thêm khi không lọc: **{sum(extra) / len(extra):+.2f} điểm %** "
      f"(nhỏ nhất {min(extra):+.2f}, lớn nhất {max(extra):+.2f}). Đây là phần mà mẫu chung sẽ bị tính nhầm là trùng "
      "nếu không có bước lọc. Cột *chỉ tài liệu nộp* có thể thấp hơn cả khi lọc: kho đã được lọc nên phần mẫu chung "
      "của bài nộp không khớp với gì mà chỉ làm tăng mẫu số, đồng thời có thể cắt ngang chuỗi câu trùng.")
    a("")
    lat = kq["latency"]
    a("### Thời gian xử lý (trong tiến trình, máy phát triển)")
    a("")
    a(f"Đo trực tiếp các hàm pipeline, không qua HTTP, trên máy phát triển dùng chung ({lat['so_cpu']} CPU logic, "
      f"{lat['torch_threads']} luồng torch). Kho gồm {lat['kho']['tieu_de']} tiêu đề và {lat['kho']['cau_tai_lieu']} "
      "câu tài liệu. Đây chưa phải số đo NFR-08/NFR-09: plan 04-06 đo trong container, Phase 5 đo trên server.")
    a("")
    a("| Thao tác | Số lần | P50 (ms) | P95 (ms) | Lớn nhất (ms) | Giới hạn NFR (P95) |")
    a("|---|---:|---:|---:|---:|---|")
    ct, cd = lat["check_title_ms"], lat["check_document_ms"]
    a(f"| `check_title` (kho 300 đề tài) | {ct['n']} | {ct['p50']} | {ct['p95']} | {ct['max']} | ≤ 5 000 ms (NFR-08) |")
    a(f"| `score_document` + `check_document` (một tệp B) | {cd['n']} | {cd['p50']} | {cd['p95']} | {cd['max']} | "
      "≤ 30 000 ms toàn luồng nộp (NFR-09) |")
    a("")
    a("### Giới hạn")
    a("")
    a("- **Dữ liệu tổng hợp.** Toàn bộ kho và tài liệu do chương trình sinh (mục 4.x.1), không phải đồ án thật của "
      "khoa. Cách diễn đạt lại và mẫu câu của bộ sinh có thể dễ hoặc khó hơn văn bản thật; ngưỡng cần được hiệu "
      "chỉnh lại khi có kho thật.")
    a("- **[ASSUMED] Danh sách mẫu chung.** Bước lọc dùng danh sách mặc định (bìa, lời cam đoan, lời cảm ơn, mục lục, "
      "tài liệu tham khảo, phụ lục…) vì mẫu đề cương/báo cáo chính thức của khoa chưa được thu thập. Khi có mẫu chính "
      "thức phải cập nhật `app/nlp/boilerplate.py` rồi chạy lại `tune` và `evaluate`.")
    a(f"- **Mẫu nhỏ.** Ngưỡng tài liệu được khớp trên {ck['tai_lieu']['so_duong'] + ck['tai_lieu']['so_am']} cặp; "
      f"tập kiểm chứng chỉ có {n_cap[KIEM_CHUNG]} cặp, nên mỗi cặp sai làm độ chính xác giảm "
      f"{1 / max(n_cap[KIEM_CHUNG], 1):.3f}.")
    a("- **Độ trễ đo trên máy phát triển**, trong tiến trình và trên máy dùng chung; con số chính thức cho NFR-08/"
      "NFR-09 do plan 04-06 (container) và Phase 5 (server) đo.")
    neg_pairs = [c for c in kq["cap"] if not c["ky_vong"]]
    worst = max(neg_pairs, key=lambda c: c["ty_le_tong"])
    a(f"- **Tỷ lệ tổng khác tỷ lệ theo đồ án nguồn.** Cặp không được kỳ vọng cảnh báo có tỷ lệ tổng cao nhất là "
      f"{worst['ma_cap']} ({TEN_LOAI[worst['loai']].lower()}, {worst['tap']}): {worst['ty_le_tong']:.2f} % tổng nhưng "
      f"chỉ {worst['ty_le_nguon']:.2f} % theo đồ án nguồn, vì các đoạn khớp rải rác trên nhiều đồ án khác cùng lĩnh "
      "vực. Vì vậy quyết định cảnh báo dựa trên tỷ lệ theo **từng** đồ án (`do_an_trung`) so với ngưỡng tài liệu, còn "
      "tỷ lệ tổng chỉ để hiển thị kèm.")
    cau = kq["cau"]
    a(f"- **Mức câu còn yếu với diễn đạt lại.** AUC của tín hiệu ngữ nghĩa ở mức câu trên tập hiệu chỉnh chỉ "
      f"{ck['ngu_nghia_cau']['auc']:.4f}. Với ngưỡng cố định, tỷ lệ câu diễn đạt lại bị gắn cờ là "
      f"{cau[HIEU_CHINH][L_DIEN_DAT]['ty_le']:.3f} (hiệu chỉnh) và {cau[KIEM_CHUNG][L_DIEN_DAT]['ty_le']:.3f} (kiểm "
      f"chứng); tỷ lệ câu tự viết bị gắn cờ là {cau[HIEU_CHINH][L_TU_VIET]['ty_le']:.3f} và "
      f"{cau[KIEM_CHUNG][L_TU_VIET]['ty_le']:.3f}. Phát hiện ở mức tài liệu vẫn đúng vì phần diễn đạt lại dồn thành "
      "đoạn liền nhau cùng nguồn, nhưng từng đoạn trùng ngữ nghĩa nên được giảng viên đọc lại trước khi kết luận.")
    tit_fail = [r for r in kq["truy_van"] if r["tap"] == KIEM_CHUNG and not r["dat"]]
    if tit_fail:
        a(f"- **Tên đề tài trên tập kiểm chứng:** {len(tit_fail)} truy vấn phân loại sai ("
          + ", ".join(f"{r['ma_truy_van']} {TEN_LOAI[r['loai']].lower()} {r['ty_le_cao_nhat']:.2f} %" for r in tit_fail)
          + "). Đề tài cùng lĩnh vực có khuôn tên giống nhau nên cảnh báo tên đề tài chỉ là **gợi ý** để giảng viên "
            "xem lại, không phải kết luận (khớp với nhận xét ở mục 4.x.2).")
    wrong = [c for c in kq["cap"] if c["tap"] == KIEM_CHUNG and not c["dat"]]
    if not g["g3"] or wrong:
        a(f"- **Cặp kiểm chứng phân loại sai** (độ chính xác {g['accuracy_kiem_chung']:.3f}"
          f"{'' if g['g3'] else ', dưới mức 0.85'}); ngưỡng **không** được khớp lại trên tập này:")
        for c in wrong:
            if c["ky_vong"]:
                cause = ("tỷ lệ theo đồ án nguồn thấp hơn ngưỡng tài liệu: một phần câu diễn đạt lại có cosine dưới "
                         "ngưỡng đoạn nên không được tính")
            else:
                cause = ("câu tự viết cùng lĩnh vực có cosine cao với A (mẫu câu chung của lĩnh vực), đẩy tỷ lệ theo "
                         "đồ án nguồn vượt ngưỡng tài liệu")
            a(f"  - {c['ma_cap']} ({TEN_LOAI[c['loai']]}, {c['dinh_dang']}): tỷ lệ tổng {c['ty_le_tong']:.2f} %, "
              f"theo đồ án nguồn {c['ty_le_nguon']:.2f} % so với ngưỡng {nguong['nguong_tai_lieu']} %, "
              f"đoạn trùng {c['so_doan_nguyen_van']} nguyên văn / {c['so_doan_ngu_nghia']} ngữ nghĩa, cosine lớn nhất "
              f"của câu tự viết {c['max_ngu_nghia_cau_tu_viet']:.2f} %. Nguyên nhân có thể: {cause}.")
    a("")
    a("### Chạy lại")
    a("")
    a("Từ thư mục `ai-service/` (cần ≥ 3 GiB RAM trống; không cần docker hay MySQL):")
    a("")
    a("```bash")
    a("uv run python calibration/calibrate.py tune --data ../seed-data \\")
    a("  --profile-from ../tools/bakeoff/ket-qua.json --out calibration")
    a("uv run python calibration/calibrate.py evaluate --data ../seed-data \\")
    a("  --profile-from ../tools/bakeoff/ket-qua.json --out calibration \\")
    a("  --report ../docs/chuong-4-trien-khai/thu-nghiem-ai/03-hieu-chinh-nguong.md --apply")
    a("```")
    a("")
    a(f"Kết quả chi tiết theo từng cặp, truy vấn và câu nằm trong `ai-service/calibration/{KET_QUA_FILE}`; ngưỡng, "
      f"phương pháp và AUC trong `ai-service/calibration/{NGUONG_FILE}` (plan 04-05 đọc tệp này để đặt giá trị mặc "
      "định phía Web API).")
    a("")
    return "\n".join(L)


# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("tune", "evaluate"):
        sp = sub.add_parser(name)
        sp.add_argument("--data", type=Path, required=True, help="thư mục seed-data")
        sp.add_argument("--profile-from", type=Path, required=True, help="tools/bakeoff/ket-qua.json")
        sp.add_argument("--out", type=Path, required=True, help="thư mục calibration")
        if name == "evaluate":
            sp.add_argument("--report", type=Path, help="đường dẫn trang chương 4 cần sinh")
            sp.add_argument("--apply", action="store_true", help="ghi giá trị hiệu chỉnh vào Settings + README")
    args = ap.parse_args(argv)
    return cmd_tune(args) if args.cmd == "tune" else cmd_evaluate(args)


if __name__ == "__main__":
    sys.exit(main())
