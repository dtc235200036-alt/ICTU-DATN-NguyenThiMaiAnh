"""NTMA Phase 4 — D-01 bake-off: bkai-foundation-models/vietnamese-bi-encoder vs intfloat/multilingual-e5-base.

Cach dung (tu thu muc tools/bakeoff):
    uv run python bakeoff.py --validate-pairs      # kiem tra cap-mau.jsonl
    uv run python bakeoff.py --profile bkai         # cham 1 mo hinh trong CHINH tien trinh nay
    uv run python bakeoff.py --profile e5
    uv run python bakeoff.py --all                  # chay lan luot tung profile bang subprocess
    uv run python bakeoff.py --decide               # ap dung quy tac dang ky truoc -> ket-qua.json
    uv run python bakeoff.py --bang                 # in bang Markdown cho chuong 4 (tu cac file ket qua)

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


# ---------------------------------------------------------------- quyet dinh (dang ky truoc)
NGUONG_AUC = 0.05          # e5 phai hon bkai it nhat 0.05 AUC ...
KIEU_QUYET_DINH = ("CAU", "DOAN")  # ... tren CA HAI tap nay
TRAN_ENCODE_300_S = 20.0   # cong do tre: encode 300 cau <= 20 s
TRAN_RSS_MB = 2560         # cong bo nho: peak RSS <= 2.5 GiB

QUY_TAC = (
    "Chon e5 chi khi e5 nap duoc va AUC cua e5 vuot bkai >= 0.05 tren CA tap CAU va tap DOAN, "
    "dong thoi e5 encode 300 cau <= 20 s va peak RSS <= 2560 MB (2.5 GiB). "
    "Neu bkai khong nap duoc hoac truot cong 20 s trong khi e5 qua ca cong do tre va cong bo nho -> chon e5. "
    "Neu ca hai truot cong do tre -> chon bkai va ghi ro rui ro (du phong: backend ONNX, 04-RESEARCH Pattern 2). "
    "Moi truong hop con lai -> chon bkai (nho hon, 515 MiB; uu tien vi may dung chung bo nho)."
)


def _load_result(name: str) -> dict:
    path = HERE / f"ket-qua-{name}.json"
    if not path.exists():
        raise SystemExit(f"thieu {path.name} — chay --profile {name} truoc")
    return json.loads(path.read_text(encoding="utf-8"))


def _nap_duoc(r: dict) -> bool:
    return not r.get("loi") and "theo_kieu" in r


def _qua_do_tre(r: dict) -> bool:
    return _nap_duoc(r) and r["chi_phi"]["encode_300_s"] <= TRAN_ENCODE_300_S


def _qua_bo_nho(r: dict) -> bool:
    return _nap_duoc(r) and r["chi_phi"]["peak_rss_mb"] <= TRAN_RSS_MB


def apply_rule(bkai: dict, e5: dict) -> tuple[str, str, str]:
    """Tra ve (chon, nhanh, ly_do) theo dung quy tac QUY_TAC."""
    if not _nap_duoc(bkai) and not _nap_duoc(e5):
        raise SystemExit("ca hai mo hinh deu khong nap duoc — khong co lua chon hop le")
    chenh = {}
    if _nap_duoc(bkai) and _nap_duoc(e5):
        chenh = {k: round(e5["theo_kieu"][k]["auc"] - bkai["theo_kieu"][k]["auc"], 4) for k in KIEU_QUYET_DINH}
    chenh_txt = ", ".join(f"{k} {v:+.4f}" for k, v in chenh.items())

    # Nhanh 1: e5 vuot troi ro rang va qua ca hai cong.
    if chenh and all(v >= NGUONG_AUC for v in chenh.values()) and _qua_do_tre(e5) and _qua_bo_nho(e5):
        return "e5", "E5_VUOT_NGUONG", (
            f"e5 hon bkai >= {NGUONG_AUC} AUC tren ca CAU va DOAN ({chenh_txt}), "
            f"encode 300 cau {e5['chi_phi']['encode_300_s']} s <= {TRAN_ENCODE_300_S:g} s, "
            f"peak RSS {e5['chi_phi']['peak_rss_mb']} MB <= {TRAN_RSS_MB} MB.")
    # Nhanh 2: bkai hong (khong nap / qua cham) trong khi e5 qua ca hai cong.
    if (not _nap_duoc(bkai) or not _qua_do_tre(bkai)) and _qua_do_tre(e5) and _qua_bo_nho(e5):
        why = f"khong nap duoc ({bkai.get('loi')})" if not _nap_duoc(bkai) else \
            f"truot cong do tre ({bkai['chi_phi']['encode_300_s']} s > {TRAN_ENCODE_300_S:g} s)"
        return "e5", "BKAI_HONG", f"bkai {why}, trong khi e5 qua cong do tre va cong bo nho."
    # Nhanh 3: ca hai truot cong do tre.
    if _nap_duoc(bkai) and _nap_duoc(e5) and not _qua_do_tre(bkai) and not _qua_do_tre(e5):
        return "bkai", "CA_HAI_CHAM", (
            f"ca hai truot cong {TRAN_ENCODE_300_S:g} s (bkai {bkai['chi_phi']['encode_300_s']} s, "
            f"e5 {e5['chi_phi']['encode_300_s']} s) -> chon bkai (nho hon); RUI RO do tre NFR, "
            "du phong: backend ONNX cua sentence-transformers (04-RESEARCH Pattern 2).")
    # Nhanh 4: mac dinh bkai.
    if not _nap_duoc(e5):
        return "bkai", "E5_KHONG_NAP", f"e5 khong nap duoc ({e5.get('loi')}) -> chon bkai."
    ly_do = [f"chenh AUC e5 - bkai: {chenh_txt} (can >= {NGUONG_AUC} tren CA HAI)"]
    if not all(v >= NGUONG_AUC for v in chenh.values()):
        thieu = [k for k, v in chenh.items() if v < NGUONG_AUC]
        ly_do.append(f"e5 KHONG dat nguong tren {', '.join(thieu)}")
    if not _qua_do_tre(e5):
        ly_do.append(f"e5 truot cong do tre ({e5['chi_phi']['encode_300_s']} s)")
    if not _qua_bo_nho(e5):
        ly_do.append(f"e5 truot cong bo nho ({e5['chi_phi']['peak_rss_mb']} MB)")
    return "bkai", "MAC_DINH_BKAI", "; ".join(ly_do) + " -> giu mac dinh bkai (nho hon, 515 MiB)."


def decide() -> dict:
    res = {name: _load_result(name) for name in PROFILES}
    chon, nhanh, ly_do = apply_rule(res["bkai"], res["e5"])
    prof = PROFILES[chon]
    out = {
        "chon": chon,
        "ten_model": prof["model_id"],
        "phan_doan": prof["phan_doan"],
        "tien_to": prof["tien_to"],
        "ly_do": ly_do,
        "nhanh_quy_tac": nhanh,
        "quy_tac": QUY_TAC,
        "so_sanh": {
            name: ({k: {x: r["theo_kieu"][k][x] for x in ("auc", "gap", "margin", "acc")} for k in KIEU}
                   if _nap_duoc(r) else {"loi": r.get("loi")})
            for name, r in res.items()
        },
        "chi_phi": {
            name: {x: r.get("chi_phi", {}).get(x) for x in ("load_s", "title_ms", "encode_300_s", "peak_rss_mb")}
            for name, r in res.items()
        },
        "ngay": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (HERE / "ket-qua.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"chon = {chon} ({prof['model_id']}), nhanh = {nhanh}\nly_do: {ly_do}")
    return out


def bang_markdown() -> str:
    """In bang Markdown lay truc tiep tu cac file ket qua (dung cho chuong 4, khong go tay so lieu)."""
    res = {name: _load_result(name) for name in PROFILES}
    ten = {"TIEU_DE": "Tên đề tài", "CAU": "Câu", "DOAN": "Đoạn"}
    chi_so = [("auc", "AUC"), ("auc_kho", "AUC (chỉ diễn đạt lại vs cùng lĩnh vực)"), ("tb_duong", "TB cosine cặp trùng"),
              ("tb_am", "TB cosine cặp không trùng"), ("gap", "Gap (TB trùng − TB không trùng)"),
              ("margin", "Margin (min trùng − max không trùng)"), ("acc", "Độ chính xác tại ngưỡng tốt nhất"),
              ("nguong_acc", "Ngưỡng tốt nhất (cosine)")]
    lines = ["| Loại cặp | Chỉ số | bkai | e5 |", "|---|---|---:|---:|"]
    for k in KIEU:
        for key, label in chi_so:
            vals = [f"{r['theo_kieu'][k][key]:.4f}" if _nap_duoc(r) and r["theo_kieu"][k][key] is not None else "—"
                    for r in (res["bkai"], res["e5"])]
            lines.append(f"| {ten[k]} | {label} | {vals[0]} | {vals[1]} |")
    lines += ["", "| Nhóm cặp (TB cosine) | Loại | bkai | e5 |", "|---|---|---:|---:|"]
    for k in KIEU:
        for nhom in NHOM_NHAN:
            vals = [f"{r['theo_kieu'][k]['tb_theo_nhom'][nhom]:.4f}" if _nap_duoc(r) else "—"
                    for r in (res["bkai"], res["e5"])]
            lines.append(f"| {nhom} | {ten[k]} | {vals[0]} | {vals[1]} |")
    cp = [("load_s", "Nạp mô hình (s, từ cache)", "{:.2f}"), ("title_ms", "Encode 1 tên đề tài (ms, trung vị 20 lần)", "{:.1f}"),
          ("encode_300_s", "Encode 300 câu (s)", "{:.2f}"), ("peak_rss_mb", "RSS đỉnh của tiến trình (MB)", "{:.1f}")]
    lines += ["", "| Chi phí trên máy phát triển | bkai | e5 | Cổng |", "|---|---:|---:|---|"]
    gate = {"encode_300_s": f"≤ {TRAN_ENCODE_300_S:g} s", "peak_rss_mb": f"≤ {TRAN_RSS_MB} MB"}
    for key, label, fmt in cp:
        vals = [fmt.format(r["chi_phi"][key]) if r.get("chi_phi", {}).get(key) is not None else "—"
                for r in (res["bkai"], res["e5"])]
        lines.append(f"| {label} | {vals[0]} | {vals[1]} | {gate.get(key, '—')} |")
    b, e = res["bkai"], res["e5"]
    lines += ["", f"Máy đo: {b['may']['cpu_count']} CPU logic, torch {b['phien_ban']['torch']} "
                  f"({b['may']['torch_threads']} luồng), sentence-transformers {b['phien_ban']['sentence-transformers']}, "
                  f"transformers {b['phien_ban']['transformers']}, underthesea {b['phien_ban']['underthesea']}, "
                  f"Python {b['phien_ban']['python']}. Đo ngày {b['ngay'][:10]} (bkai) và {e['ngay'][:10]} (e5)."]
    if (HERE / "ket-qua.json").exists():
        d = json.loads((HERE / "ket-qua.json").read_text(encoding="utf-8"))
        lines += ["", f"Quyết định: **{d['ten_model']}** (`{d['chon']}`), nhánh quy tắc `{d['nhanh_quy_tac']}` — {d['ly_do']}"]
    return "\n".join(lines)


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
    g.add_argument("--decide", action="store_true", help="doc ket-qua-{bkai,e5}.json, ap dung quy tac, ghi ket-qua.json")
    g.add_argument("--bang", action="store_true", help="in bang Markdown tu cac file ket qua (cho chuong 4)")
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
    if args.decide:
        decide()
        return 0
    if args.bang:
        print(bang_markdown())
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
