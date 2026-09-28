"""NTMA Phase 4 — D-01 bake-off: bkai-foundation-models/vietnamese-bi-encoder vs intfloat/multilingual-e5-base.

Cach dung (tu thu muc tools/bakeoff):
    uv run python bakeoff.py --validate-pairs      # kiem tra cap-mau.jsonl
    uv run python bakeoff.py --profile bkai         # cham 1 mo hinh trong CHINH tien trinh nay
    uv run python bakeoff.py --profile e5
    uv run python bakeoff.py --all                  # chay lan luot tung profile bang subprocess

Nguyen tac bo nho (may dung chung 16 GB, tung bi OOM): moi tien trinh chi nap DUNG MOT mo hinh;
tien trinh cha (--all) khong bao gio nap mo hinh; truoc khi nap, doi den khi MemAvailable >= 3 GiB.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAIRS_FILE = HERE / "cap-mau.jsonl"

# Hai profile — giong het app/embedding.py cua plan 04-01.
PROFILES = {
    "bkai": {
        "model_id": "bkai-foundation-models/vietnamese-bi-encoder",
        "phan_doan": True,   # tach tu underthesea truoc khi encode
        "tien_to": "",
    },
    "e5": {
        "model_id": "intfloat/multilingual-e5-base",
        "phan_doan": False,
        "tien_to": "query: ",  # tuong dong doi xung: "query: " o CA HAI phia
    },
}

KIEU = ("TIEU_DE", "CAU", "DOAN")
NHOM_NHAN = {"DIEN_DAT_LAI": 1, "CUNG_LINH_VUC": 0, "KHONG_LIEN_QUAN": 0}
# So cap mong doi: kieu -> nhom -> so luong
SO_CAP = {
    "TIEU_DE": {"DIEN_DAT_LAI": 12, "CUNG_LINH_VUC": 12, "KHONG_LIEN_QUAN": 6},
    "CAU": {"DIEN_DAT_LAI": 12, "CUNG_LINH_VUC": 12, "KHONG_LIEN_QUAN": 6},
    "DOAN": {"DIEN_DAT_LAI": 8, "CUNG_LINH_VUC": 8, "KHONG_LIEN_QUAN": 4},
}

TORCH_THREADS = 4
BATCH_SIZE = 32
MIN_AVAILABLE_GIB = 3.0
WAIT_MAX_S = 20 * 60
WAIT_STEP_S = 15

# Hau to ngan (tu soan) de dung 300 cau khac nhau tu cac cau CAU cho phep do toc do.
HAU_TO = [
    "",
    " Nội dung này được trình bày chi tiết ở chương 3.",
    " Đây là yêu cầu bắt buộc của hệ thống.",
    " Chức năng này đã được kiểm thử trên môi trường thử nghiệm.",
    " Giải pháp này phù hợp với quy mô của khoa.",
    " Phần tiếp theo mô tả cách cài đặt cụ thể.",
    " Nhóm đã đối chiếu kết quả với yêu cầu ban đầu.",
    " Hạn chế của cách làm này được nêu ở phần kết luận.",
]

PACKAGES = ("sentence-transformers", "transformers", "tokenizers", "torch", "underthesea",
            "underthesea-core", "scikit-learn", "numpy")


# ---------------------------------------------------------------- du lieu
def load_pairs(path: Path = PAIRS_FILE) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def validate_pairs(rows: list[dict]) -> list[str]:
    errs: list[str] = []
    ids = [r.get("id") for r in rows]
    dup = [i for i, c in Counter(ids).items() if c > 1]
    if dup:
        errs.append(f"id trung: {dup}")
    for r in rows:
        rid = r.get("id")
        if set(r) != {"id", "kieu", "nhom", "nhan", "a", "b"}:
            errs.append(f"{rid}: sai tap truong {sorted(r)}")
            continue
        if r["kieu"] not in KIEU:
            errs.append(f"{rid}: kieu la {r['kieu']}")
        if r["nhom"] not in NHOM_NHAN:
            errs.append(f"{rid}: nhom la {r['nhom']}")
        elif r["nhan"] != NHOM_NHAN[r["nhom"]]:
            errs.append(f"{rid}: nhan {r['nhan']} khong khop nhom {r['nhom']}")
        for side in ("a", "b"):
            s = r[side]
            if not isinstance(s, str) or not s.strip():
                errs.append(f"{rid}.{side}: rong")
            elif not unicodedata.is_normalized("NFC", s):
                errs.append(f"{rid}.{side}: khong phai NFC")
        if r["a"] == r["b"]:
            errs.append(f"{rid}: a == b")
    got = Counter((r.get("kieu"), r.get("nhom")) for r in rows)
    for kieu, by_nhom in SO_CAP.items():
        for nhom, n in by_nhom.items():
            if got[(kieu, nhom)] != n:
                errs.append(f"{kieu}/{nhom}: {got[(kieu, nhom)]} cap, can {n}")
    total = sum(sum(v.values()) for v in SO_CAP.values())
    if len(rows) != total:
        errs.append(f"tong {len(rows)} cap, can {total}")
    return errs


def cau_do_toc_do(rows: list[dict], n: int = 300) -> list[str]:
    """300 cau khac nhau: cac cau CAU (khong trung) x hau to tu soan."""
    base: list[str] = []
    for r in rows:
        if r["kieu"] == "CAU":
            for s in (r["a"], r["b"]):
                if s not in base:
                    base.append(s)
    out: list[str] = []
    for suffix in HAU_TO:
        for s in base:
            out.append(s + suffix)
            if len(out) == n:
                return out
    raise SystemExit(f"khong du cau de dung {n} cau do toc do (chi co {len(out)})")


# ---------------------------------------------------------------- he thong
def mem_available_gib() -> float:
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / (1024 * 1024)
    return 0.0


def wait_for_memory() -> float:
    waited = 0
    while True:
        avail = mem_available_gib()
        if avail >= MIN_AVAILABLE_GIB:
            return avail
        if waited >= WAIT_MAX_S:
            raise SystemExit(f"MemAvailable {avail:.2f} GiB < {MIN_AVAILABLE_GIB} GiB sau {waited}s — dung lai")
        print(f"[bo nho] MemAvailable {avail:.2f} GiB < {MIN_AVAILABLE_GIB} GiB, doi {WAIT_STEP_S}s ...",
              file=sys.stderr, flush=True)
        time.sleep(WAIT_STEP_S)
        waited += WAIT_STEP_S


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0  # Linux: KiB


def versions() -> dict:
    out = {"python": platform.python_version()}
    for p in PACKAGES:
        try:
            out[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            out[p] = None
    return out


# ---------------------------------------------------------------- do luong
def metrics(labels: list[int], scores: list[float]) -> dict:
    import numpy as np
    from sklearn.metrics import roc_auc_score, roc_curve

    y = np.asarray(labels)
    s = np.asarray(scores)
    pos, neg = s[y == 1], s[y == 0]
    auc = float(roc_auc_score(y, s))
    fpr, tpr, thr = roc_curve(y, s)
    j = int(np.argmax(tpr - fpr))
    # Do chinh xac tot nhat tren moi nguong (du doan trung khi cosine >= t).
    best_acc, best_t = 0.0, None
    for t in sorted(set(s.tolist())):
        acc = float(((s >= t).astype(int) == y).mean())
        if acc > best_acc:
            best_acc, best_t = acc, t
    return {
        "n": int(len(y)),
        "n_duong": int(len(pos)),
        "n_am": int(len(neg)),
        "auc": round(auc, 4),
        "tb_duong": round(float(pos.mean()), 4),
        "tb_am": round(float(neg.mean()), 4),
        "gap": round(float(pos.mean() - neg.mean()), 4),
        "margin": round(float(pos.min() - neg.max()), 4),
        "acc": round(best_acc, 4),
        "nguong_acc": round(float(best_t), 4) if best_t is not None else None,
        "nguong_youden": round(float(thr[j]), 4) if np.isfinite(thr[j]) else None,
    }


def run_profile(name: str, out: Path) -> dict:
    prof = PROFILES[name]
    rows = load_pairs()
    errs = validate_pairs(rows)
    if errs:
        raise SystemExit("cap-mau.jsonl khong hop le:\n  " + "\n  ".join(errs))

    result: dict = {
        "profile": name,
        "model_id": prof["model_id"],
        "phan_doan": prof["phan_doan"],
        "tien_to": prof["tien_to"],
        "ngay": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "may": {"cpu_count": os.cpu_count(), "torch_threads": TORCH_THREADS,
                "mem_available_gib_truoc_khi_nap": None, "platform": platform.platform()},
        "phien_ban": versions(),
        "loi": None,
    }
    result["may"]["mem_available_gib_truoc_khi_nap"] = round(wait_for_memory(), 2)

    t0 = time.perf_counter()
    try:
        import torch
        torch.set_num_threads(TORCH_THREADS)
        from sentence_transformers import SentenceTransformer
        if prof["phan_doan"]:
            from underthesea import word_tokenize
            word_tokenize("khởi động")  # nap tu dien truoc, khong tinh vao do tre
        else:
            word_tokenize = None
        model = SentenceTransformer(prof["model_id"], device="cpu")
    except Exception as exc:  # mo hinh khong nap duoc -> ghi loi, van thoat 0
        result["loi"] = f"{type(exc).__name__}: {exc}"
        result["chi_phi"] = {"peak_rss_mb": round(peak_rss_mb(), 1)}
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[{name}] KHONG NAP DUOC: {result['loi']}", file=sys.stderr)
        return result
    load_s = time.perf_counter() - t0
    result["max_seq_length"] = getattr(model, "max_seq_length", None)

    def prep(text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        if word_tokenize is not None:
            text = word_tokenize(text, format="text")
        return prof["tien_to"] + text

    def encode(texts: list[str]):
        return model.encode([prep(t) for t in texts], batch_size=BATCH_SIZE,
                            normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)

    theo_kieu: dict = {}
    cap: list[dict] = []
    for kieu in KIEU:
        sub = [r for r in rows if r["kieu"] == kieu]
        # Mot lan goi encode cho moi kieu (a roi b).
        emb = encode([r["a"] for r in sub] + [r["b"] for r in sub])
        ea, eb = emb[: len(sub)], emb[len(sub):]
        cos = [float((ea[i] * eb[i]).sum()) for i in range(len(sub))]
        m = metrics([r["nhan"] for r in sub], cos)
        # AUC "kho": chi dien dat lai vs cung linh vuc (bo cap khong lien quan).
        hard = [(r["nhan"], c) for r, c in zip(sub, cos) if r["nhom"] != "KHONG_LIEN_QUAN"]
        m["auc_kho"] = metrics([h[0] for h in hard], [h[1] for h in hard])["auc"]
        m["tb_theo_nhom"] = {
            nhom: round(statistics.fmean([c for r, c in zip(sub, cos) if r["nhom"] == nhom]), 4)
            for nhom in NHOM_NHAN
        }
        theo_kieu[kieu] = m
        cap += [{"id": r["id"], "kieu": kieu, "nhom": r["nhom"], "nhan": r["nhan"], "cosine": round(c, 4)}
                for r, c in zip(sub, cos)]

    # Do tre: trung vi 20 lan encode 1 tieu de (gom ca tien xu ly), sau 3 lan khoi dong.
    titles = []
    for r in rows:
        if r["kieu"] == "TIEU_DE":
            for s in (r["a"], r["b"]):
                if s not in titles:
                    titles.append(s)
    for t in titles[:3]:
        encode([t])
    lat = []
    for t in titles[3:23]:
        t1 = time.perf_counter()
        encode([t])
        lat.append((time.perf_counter() - t1) * 1000)

    sents = cau_do_toc_do(rows, 300)
    t2 = time.perf_counter()
    encode(sents)
    encode_300_s = time.perf_counter() - t2

    result["theo_kieu"] = theo_kieu
    result["chi_phi"] = {
        "load_s": round(load_s, 2),
        "title_ms": round(statistics.median(lat), 1),
        "title_ms_so_lan": len(lat),
        "encode_300_s": round(encode_300_s, 2),
        "encode_300_so_cau": len(sents),
        "peak_rss_mb": round(peak_rss_mb(), 1),
    }
    result["cap"] = cap
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"profile": name, "theo_kieu": {k: {x: v[x] for x in ("auc", "auc_kho", "gap", "margin", "acc")}
                                                      for k, v in theo_kieu.items()},
                      "chi_phi": result["chi_phi"]}, ensure_ascii=False, indent=2))
    return result


def run_all() -> int:
    """Tien trinh cha: KHONG nap mo hinh, chay tung profile trong subprocess rieng, lan luot."""
    for name in PROFILES:
        cmd = [sys.executable, str(Path(__file__).resolve()), "--profile", name]
        print(f"[all] {' '.join(cmd)}", flush=True)
        rc = subprocess.run(cmd, check=False).returncode  # doi tien trinh con thoat han
        if rc != 0:
            print(f"[all] profile {name} thoat ma {rc}", file=sys.stderr)
            return rc
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--validate-pairs", action="store_true", help="kiem tra cap-mau.jsonl")
    g.add_argument("--profile", choices=sorted(PROFILES), help="cham mot mo hinh trong tien trinh hien tai")
    g.add_argument("--all", action="store_true", help="chay moi profile bang subprocess, lan luot")
    ap.add_argument("--out", type=Path, help="duong dan ket qua (mac dinh ket-qua-{profile}.json)")
    args = ap.parse_args(argv)

    if args.validate_pairs:
        rows = load_pairs()
        errs = validate_pairs(rows)
        if errs:
            print("KHONG HOP LE:\n  " + "\n  ".join(errs), file=sys.stderr)
            return 1
        c = Counter((r["kieu"], r["nhom"]) for r in rows)
        print(f"OK: {len(rows)} cap — " + ", ".join(f"{k}/{n}={v}" for (k, n), v in sorted(c.items())))
        print(f"OK: dung duoc {len(cau_do_toc_do(rows))} cau do toc do")
        return 0
    if args.profile:
        run_profile(args.profile, args.out or HERE / f"ket-qua-{args.profile}.json")
        return 0
    if args.all:
        return run_all()
    return 2


if __name__ == "__main__":
    sys.exit(main())
