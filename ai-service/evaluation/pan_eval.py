"""Đánh giá kiểu PAN-PC (Potthast và cs. 2010) cho kiểm tra trùng lặp tài liệu.

    .venv/bin/python -m evaluation.pan_eval --data DIR --out DIR [--nhan TEN] \
        [--nguong-doan 67.7] [--nguong-nguyen-van 56.0]

Dữ liệu: <data>/nhan.json + nguon/*.txt + nghi-van/*.txt (bộ sinh evaluation/tao_bo.py).
Chạy TRONG TIẾN TRÌNH như calibration/calibrate.py: SQLite thesis_ai tạm
(alembic head), mọi nguồn được nạp là DOCUMENT (ma_nguon = nhom = phần số
của id) qua pipeline.ingest_many; mỗi tài liệu nghi vấn qua score_document →
flag_chunks (đúng quy tắc gắn cờ của check_document).
Phát hiện = chuỗi tối đa các câu liên tiếp gắn cờ cùng một nguồn (KHÔNG cắt
6 câu như phần hiển thị): phía nghi vấn từ đầu câu đầu tới cuối câu cuối,
phía nguồn từ đầu tới cuối các câu nguồn khớp. Vector câu lưu đĩa ở
<data>/cache-vector/<mô hình>/ nên chạy lại (sau khi sửa thuật toán, đổi
ngưỡng) không mã hóa lại.
"""
import argparse
import hashlib
import json
import re
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import fmean

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import pipeline
from app.core.config import Settings
from app.embedding import Encoder
from app.index import TAI_LIEU, CorpusIndex
from app.models import LOAI_DOCUMENT
from app.nlp.boilerplate import strip_boilerplate
from app.nlp.normalize import _SPACES_RE, nfc
from calibration.calibrate import ALL, _migrate, canh_bao, fit_threshold, wait_for_memory
from evaluation.pan_metrics import case_recall, detection_precision, pan_scores

# (ngưỡng tài liệu, ngưỡng tổng): giá trị hiệu chỉnh (nguong-de-xuat.json) và giá trị production.
CAP_NGUONG = [(10.4, 14.8), (25.0, 25.0)]
SO_NHIEU = 10
SHARD = 2048  # số câu mới mỗi tệp cache: lần chạy bị ngắt vẫn giữ các lô đã mã hóa


def log(msg: str) -> None:
    print(f"[pan_eval] {msg}", file=sys.stderr, flush=True)


class DiskCacheEncoder:
    """Bọc Encoder: vector câu lưu đĩa theo sha1 của câu, mỗi lô một tệp .npz
    (ghi xong mới đổi tên nên tệp dở dang không bao giờ được đọc)."""

    def __init__(self, inner: Encoder, folder: Path) -> None:
        self.inner, self.name, self.dim = inner, inner.name, inner.dim
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, np.ndarray] = {}
        for f in sorted(folder.glob("*.npz")):
            with np.load(f) as z:
                self._cache.update(zip(z["keys"].tolist(), z["vectors"]))
        log(f"cache vector: {len(self._cache)} câu ({folder})")

    def encode(self, texts: list[str]) -> np.ndarray:
        keys = [hashlib.sha1(t.encode("utf-8")).hexdigest() for t in texts]
        todo = list({k: t for k, t in zip(keys, texts) if k not in self._cache}.items())
        for start in range(0, len(todo), SHARD):
            part = todo[start : start + SHARD]
            vectors = self.inner.encode([t for _, t in part])
            self._cache.update(zip((k for k, _ in part), vectors))
            tmp = self.folder / f"{time.time_ns()}.npz.tmp"
            with open(tmp, "wb") as f:
                np.savez(f, keys=np.array([k for k, _ in part]), vectors=vectors)
            tmp.rename(tmp.with_suffix(""))
            log(f"đã mã hóa {start + len(part)}/{len(todo)} câu mới")
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self._cache[k] for k in keys])


def _ma(id_: str) -> int:
    return int(re.sub(r"\D", "", id_))


def _align(raw: str, line: str) -> list[int]:
    """Vị trí trong raw của từng ký tự của line = dòng tương ứng của nfc(raw).
    Trong một dòng nfc() chỉ thay ký tự 1:1, gộp mỗi dãy _SPACES_RE thành một
    dấu cách và strip; thay đổi độ dài khác (tổ hợp NFC, NUL) bị assert bắt."""
    i = 0
    while i < len(raw) and (raw[i].isspace() or _SPACES_RE.match(raw, i)):
        i += 1
    out = []
    for ch in line:
        out.append(i)
        m = _SPACES_RE.match(raw, i) if ch == " " else None
        i = m.end() if m else i + 1
    assert i <= len(raw) and all(c.isspace() or _SPACES_RE.match(c) for c in raw[i:]), "nfc() đổi độ dài dòng"
    return out


def _stream(text: str) -> tuple[str, list[int]]:
    """Dòng chảy đúng như chunking.sentences thấy (dòng giữ lại sau
    strip_boilerplate nối bằng dấu cách, mọi dãy \\s+ gộp thành một dấu cách)
    và vị trí trong text của từng ký tự."""
    raw_lines, norm_lines = text.split("\n"), nfc(text).split("\n")
    assert len(raw_lines) == len(norm_lines), "nfc() đổi số dòng (có CR?)"
    kept = strip_boilerplate(text).lines
    parts: list[str] = []
    pos: list[int] = []
    k = off = 0
    # shortcut: dòng giữ lại được dò tiến theo nội dung — nếu một dòng bị bỏ
    # trùng chữ với dòng giữ lại phía sau thì dòng đó lấy nhầm vị trí; sửa khi
    # strip_boilerplate trả chỉ số dòng.
    for raw, line in zip(raw_lines, norm_lines):
        if k < len(kept) and line == kept[k]:
            if parts:
                parts.append(" ")
                pos.append(off - 1)
            parts.append(line)
            pos += [off + i for i in _align(raw, line)]
            k += 1
        off += len(raw) + 1
    assert k == len(kept), "không dò được dòng giữ lại trong văn bản gốc"
    joined = "".join(parts)
    stream: list[str] = []
    smap: list[int] = []
    last = 0
    for m in re.finditer(r"\s+", joined):
        stream += [joined[last : m.start()], " "]
        smap += pos[last : m.start() + 1]
        last = m.end()
    stream.append(joined[last:])
    smap += pos[last:]
    return "".join(stream), smap


def locate(text: str, sents: list[str]) -> tuple[list[tuple[int, int] | None], int]:
    """(khoảng ký tự của từng câu trong văn bản gốc, số câu phải dùng regex dự
    phòng). Câu của chunking là chuỗi con của dòng chảy (_stream) nên tìm
    chính xác, tiến từ cuối câu trước; khoảng có thể chứa các dòng bị lọc ở
    giữa (số trang, header). Không thấy → regex token nối \\s+ trên văn bản gốc."""
    stream, smap = _stream(text)
    spans: list[tuple[int, int] | None] = []
    du_phong = pos = goc = 0
    for s in sents:
        i = stream.find(s, pos)
        if i >= 0:
            span = (smap[i], smap[i + len(s) - 1] + 1)
            pos = i + len(s)
        else:
            du_phong += 1
            pat = re.compile(r"\s+".join(map(re.escape, s.split())))
            m = pat.search(text, goc) or pat.search(text)
            span = m.span() if m else None
        spans.append(span)
        if span:
            goc = max(goc, span[1])
    return spans, du_phong


def detections(susp_id, flags, spans, src_spans, ten_nguon, key) -> list[tuple]:
    """Chuỗi tối đa các câu liên tiếp gắn cờ cùng key(cờ) → phát hiện (susp_id,
    src_id, đầu, cuối phía nghi vấn, đầu, cuối phía nguồn, tín hiệu chiếm đa số ký tự)."""
    runs: list[list[tuple[int, tuple]]] = []
    prev = None
    for i, f in enumerate(flags):
        if f is not None and prev is not None and key(prev) == key(f):
            runs[-1].append((i, f))
        elif f is not None:
            runs.append([(i, f)])
        prev = f
    out = []
    for run in runs:
        ref = run[0][1][2]
        s = [spans[i] for i, _ in run if spans[i]]
        r = [x for _, f in run if (x := src_spans[ref].get(f[3][0]))]
        if not s or not r:
            continue
        chars = sum(f[0].n_chars for _, f in run)
        verbatim = sum(f[0].n_chars for _, f in run if f[1] == pipeline.NGUYEN_VAN)
        signal = pipeline.NGUYEN_VAN if 2 * verbatim >= chars else pipeline.NGU_NGHIA
        out.append((susp_id, ten_nguon[ref], min(a for a, _ in s), max(b for _, b in s),
                    min(a for a, _ in r), max(b for _, b in r), signal))
    return out


def evaluate(data_dir: Path, nd: float, nv: float) -> dict:
    bo = json.loads((data_dir / "nhan.json").read_text(encoding="utf-8"))
    # Chỉ cần profile mô hình và tham số vân tay; hai khóa bí mật không dùng tới.
    settings = Settings(DATABASE_URL="sqlite://", AI_API_KEY="0" * 32)
    if settings.AI_MODEL_PROFILE != "fake":
        wait_for_memory()
    inner = Encoder(settings.AI_MODEL_PROFILE, settings.TORCH_THREADS)
    encoder = DiskCacheEncoder(inner, data_dir / "cache-vector" / re.sub(r"[^\w.@-]", "_", inner.name))

    ten_nguon = {_ma(n["id"]): n["id"] for n in bo["nguon"]}
    texts = {_ma(n["id"]): (data_dir / n["tep"]).read_text(encoding="utf-8") for n in bo["nguon"]}
    index = CorpusIndex(encoder.dim, van_tay=(settings.VAN_TAY_K, settings.VAN_TAY_W))
    with tempfile.TemporaryDirectory(prefix="ntma-pan-") as tmp:
        with Session(create_engine(_migrate(Path(tmp) / "thesis_ai.db"))) as session:
            items = [pipeline.IngestItem(LOAI_DOCUMENT, ma, t, nhom=ma) for ma, t in texts.items()]
            pipeline.ingest_many(session, index, encoder, items)

    rows = defaultdict(list)
    for row in index.partition(TAI_LIEU).rows.values():
        rows[row.ma_nguon].append(row)
    dinh_vi = {phia: Counter(so_cau=0, du_phong=0, khong_dinh_vi=0) for phia in ("nghi_van", "nguon")}
    src_spans: dict[int, dict[int, tuple[int, int] | None]] = {}
    for ma, rs in rows.items():
        rs.sort(key=lambda r: r.thu_tu)
        spans, du_phong = locate(texts[ma], [r.noi_dung for r in rs])
        dinh_vi["nguon"].update(so_cau=len(spans), du_phong=du_phong, khong_dinh_vi=spans.count(None))
        src_spans[ma] = dict(zip((r.thu_tu for r in rs), spans))
    log(f"kho: {len(texts)} nguồn, định vị câu {dict(dinh_vi['nguon'])}")

    cases, ca_meta, dets, dets_tin_hieu, tai_lieu, susp_texts = [], [], [], [], [], {}
    # Mức câu / đoạn → kiểu biến đổi → độ phủ vân tay×100 trong ca.
    phu = {"cau": defaultdict(list), "doan": defaultdict(list)}
    for n, d in enumerate(bo["nghi_van"], start=1):
        text = susp_texts[d["id"]] = (data_dir / d["tep"]).read_text(encoding="utf-8")
        # Nền là chính bài của sinh viên: nếu có trong kho thì loại trừ (như loai_tru của Web API).
        exclude = {_ma(d["nen"])} if d.get("nen") in ten_nguon.values() else set()
        scores = pipeline.score_document(index, encoder, text, exclude, pho_bien=settings.VAN_TAY_PHO_BIEN)
        flags = pipeline.flag_chunks(scores.chunks, nd, nv)
        spans, du_phong = locate(text, [c.text for c in scores.chunks])
        dinh_vi["nghi_van"].update(so_cau=len(spans), du_phong=du_phong, khong_dinh_vi=spans.count(None))
        dets += detections(d["id"], flags, spans, src_spans, ten_nguon, lambda f: f[2])
        dets_tin_hieu += detections(d["id"], flags, spans, src_spans, ten_nguon, lambda f: (f[2], f[1]))
        res = pipeline.check_document(scores, nd, nv, ALL, ALL)
        tai_lieu.append({
            "id": d["id"],
            "co_dao_van": d["co_dao_van"],
            "ty_le_tong": res["ty_le_tong"],
            "ty_le_nguon_cao_nhat": res["do_an_trung"][0]["ty_le"] if res["do_an_trung"] else 0.0,
        })
        for c in d["ca"]:
            # Câu nằm trọn trong khoảng của ca, câu nguồn vân tay khớp nhất thuộc đúng nguồn của ca.
            a, b = c["nv_bat_dau"], c["nv_bat_dau"] + c["nv_do_dai"]
            phu["cau"][c["bien_doi"]] += [
                ch.verb_score * 100 for ch, sp in zip(scores.chunks, spans)
                if sp and a <= sp[0] and sp[1] <= b and ch.verb_ref is not None and ten_nguon[ch.verb_ref] == c["nguon"]
            ]
            # Đoạn hiển thị đa số ký tự do vân tay, cùng nguồn, chồng lên ca. Từ 24/11/2026 nhãn SUA_NHE
            # dùng tỷ lệ khớp chữ (pipeline._ty_le_khop_chu), không còn so diem_nguyen_van với ngưỡng.
            for p in res["chi_tiet"]:
                dau, _, cuoi = p["vi_tri"].removeprefix("Câu ").partition("–")
                ss = [sp for sp in spans[int(dau) - 1 : int(cuoi or dau)] if sp]
                if (p["tin_hieu"] != pipeline.NGU_NGHIA and ten_nguon[p["ref_id"]] == c["nguon"]
                        and ss and min(x for x, _ in ss) < b and max(y for _, y in ss) > a):
                    phu["doan"][c["bien_doi"]].append(p["diem_nguyen_van"])
            cases.append((d["id"], c["nguon"], c["nv_bat_dau"], c["nv_bat_dau"] + c["nv_do_dai"],
                          c["ng_bat_dau"], c["ng_bat_dau"] + c["ng_do_dai"]))
            ca_meta.append(c)
        log(f"nghi vấn {n}/{len(bo['nghi_van'])} {d['id']}: {sum(f is not None for f in flags)} câu gắn cờ")

    rc = case_recall(cases, dets)
    rc_tin_hieu = {
        s: case_recall(cases, [x for x in dets_tin_hieu if x[6] == s])
        for s in (pipeline.NGUYEN_VAN, pipeline.NGU_NGHIA)
    }
    theo_bien_doi = {}
    for loai in dict.fromkeys(c["bien_doi"] for c in ca_meta):
        idx = [i for i, c in enumerate(ca_meta) if c["bien_doi"] == loai]
        theo_bien_doi[loai] = {
            "so_ca": len(idx),
            "recall": round(fmean(rc[i] for i in idx), 4),
            "ty_le_phat_hien": round(fmean(rc[i] > 0 for i in idx), 4),
            "recall_nguyen_van": round(fmean(rc_tin_hieu[pipeline.NGUYEN_VAN][i] for i in idx), 4),
            "recall_ngu_nghia": round(fmean(rc_tin_hieu[pipeline.NGU_NGHIA][i] for i in idx), 4),
        }

    def phan_bo(v: list[float]) -> dict:
        p = np.percentile(v, [5, 10, 50, 90, 95]).round(2).tolist() if v else [None] * 5
        return {"so_luong": len(v), **dict(zip(("p5", "p10", "trung_vi", "p90", "p95"), p))}

    phan_bo_phu = {muc: {loai: phan_bo(v[loai]) for loai in theo_bien_doi} for muc, v in phu.items()}
    # Biên Youden J trên diem_nguyen_van giữa nguyen_van và sua_nhe (tham khảo; nhãn không còn dùng đại lượng này).
    bien_sua_nhe = {
        muc: fit_threshold(v["nguyen_van"], v["sua_nhe"]) if v["nguyen_van"] and v["sua_nhe"] else None
        for muc, v in phu.items()
    }

    bang_canh_bao = []
    for ntl, ntt in CAP_NGUONG:
        m = {"tp": 0, "fn": 0, "fp": 0, "tn": 0}
        for t in tai_lieu:
            bao = canh_bao(t["ty_le_nguon_cao_nhat"], t["ty_le_tong"], ntl, ntt) is not None
            m[("tp" if bao else "fn") if t["co_dao_van"] else ("fp" if bao else "tn")] += 1
        bang_canh_bao.append({"nguong_tai_lieu": ntl, "nguong_tong": ntt, **m})

    nhieu = sorted(
        (x for x, p in zip(dets, detection_precision(cases, dets)) if p == 0), key=lambda x: x[3] - x[2], reverse=True
    )
    return {
        "du_lieu": str(data_dir),
        "mo_hinh": encoder.name,
        "nguong_doan": nd,
        "nguong_nguyen_van": nv,
        "so_nguon": len(texts),
        "so_nghi_van": len(tai_lieu),
        "so_co_dao_van": sum(t["co_dao_van"] for t in tai_lieu),
        "so_ca": len(cases),
        "so_phat_hien": len(dets),
        "dinh_vi": dinh_vi,
        "tong": {k: round(v, 4) for k, v in pan_scores(cases, dets).items()},
        "theo_bien_doi": theo_bien_doi,
        "phan_bo_phu_van_tay": phan_bo_phu,
        "bien_sua_nhe": bien_sua_nhe,
        "canh_bao": bang_canh_bao,
        "tai_lieu": tai_lieu,
        "ca": [
            {"id": c["id"], "nghi_van": s[0], "nguon": s[1], "bien_doi": c["bien_doi"], "recall": round(r, 4)}
            for c, s, r in zip(ca_meta, cases, rc)
        ],
        "nhieu": {
            "so_phat_hien": len(nhieu),
            "dai_nhat": [
                {"nghi_van": x[0], "nguon": x[1], "tin_hieu": x[6], "do_dai": x[3] - x[2],
                 "trich": " ".join(susp_texts[x[0]][x[2] : x[3]].split())[:80]}
                for x in nhieu[:SO_NHIEU]
            ],
        },
    }


def render(kq: dict) -> str:
    t, dv = kq["tong"], kq["dinh_vi"]
    L = [
        f"# Đánh giá kiểu PAN — {kq['nhan']}",
        "",
        f"- Dữ liệu `{kq['du_lieu']}`: {kq['so_nguon']} nguồn, {kq['so_nghi_van']} tài liệu nghi vấn "
        f"({kq['so_co_dao_van']} có đạo văn), {kq['so_ca']} ca, {kq['so_phat_hien']} phát hiện.",
        f"- Mô hình `{kq['mo_hinh']}`; ngưỡng đoạn {kq['nguong_doan']}, ngưỡng nguyên văn {kq['nguong_nguyen_van']}.",
        *(
            f"- Định vị câu {ten} trong văn bản gốc: {dv[phia]['so_cau']} câu, {dv[phia]['du_phong']} phải dùng "
            f"regex dự phòng, {dv[phia]['khong_dinh_vi']} không định vị được."
            for phia, ten in (("nghi_van", "nghi vấn"), ("nguon", "nguồn"))
        ),
        "",
        "## Chỉ số tổng (PAN-PC, Potthast và cs. 2010)",
        "",
        "| Precision | Recall | Granularity | Plagdet |",
        "|---:|---:|---:|---:|",
        f"| {t['precision']:.4f} | {t['recall']:.4f} | {t['granularity']:.4f} | {t['plagdet']:.4f} |",
        "",
        "## Theo kiểu biến đổi",
        "",
        "Tỷ lệ phát hiện = tỷ lệ ca có recall > 0. Recall nguyên văn / ngữ nghĩa = recall khi chỉ giữ "
        "phần phát hiện do câu gắn cờ NGUYEN_VAN / NGU_NGHIA.",
        "",
        "| Kiểu | Số ca | Recall | Tỷ lệ phát hiện | Recall nguyên văn | Recall ngữ nghĩa |",
        "|---|---:|---:|---:|---:|---:|",
        *(
            f"| {k} | {v['so_ca']} | {v['recall']:.4f} | {v['ty_le_phat_hien']:.4f} | "
            f"{v['recall_nguyen_van']:.4f} | {v['recall_ngu_nghia']:.4f} |"
            for k, v in kq["theo_bien_doi"].items()
        ),
        "",
        "## Độ phủ vân tay trong ca (×100)",
        "",
        "Câu: câu nghi vấn nằm trọn trong khoảng của ca, câu nguồn vân tay khớp nhất thuộc đúng nguồn của ca. "
        "Đoạn: đoạn hiển thị đa số ký tự do vân tay, cùng nguồn, chồng lên ca — `diem_nguyen_van` (trung bình "
        "độ phủ theo ký tự), đại lượng check_document so với biên sửa nhẹ.",
        "",
        "| Mức | Kiểu | Số lượng | p5 | p10 | Trung vị | p90 | p95 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
        *(
            f"| {muc} | {k} | {v['so_luong']} | {v['p5']} | {v['p10']} | {v['trung_vi']} | {v['p90']} | {v['p95']} |"
            for muc, bang in kq["phan_bo_phu_van_tay"].items()
            for k, v in bang.items()
        ),
        "",
        *(
            f"- Biên nguyen_van / sua_nhe mức {muc} ({b['phuong_phap']}): **{b['nguong']}** — J = {b['youden_j']}, "
            f"TPR = {b['tpr']}, FPR = {b['fpr']}, AUC = {b['auc']}, khoảng chọn {b['khoang_chon']}."
            for muc, b in kq["bien_sua_nhe"].items()
            if b
        ),
        "",
        "## Mức tài liệu",
        "",
        "Cảnh báo khi tỷ lệ theo nguồn cao nhất ≥ ngưỡng tài liệu hoặc tỷ lệ tổng ≥ ngưỡng tổng.",
        "",
        "| Ngưỡng tài liệu / tổng (%) | Đạo văn, cảnh báo | Đạo văn, bỏ sót | Sạch, cảnh báo nhầm | Sạch, không cảnh báo |",
        "|---|---:|---:|---:|---:|",
        *(
            f"| {c['nguong_tai_lieu']} / {c['nguong_tong']} | {c['tp']} | {c['fn']} | {c['fp']} | {c['tn']} |"
            for c in kq["canh_bao"]
        ),
        "",
        "Tài liệu sạch:",
        "",
        "| Tài liệu | Tỷ lệ tổng (%) | Tỷ lệ nguồn cao nhất (%) |",
        "|---|---:|---:|",
        *(
            f"| {d['id']} | {d['ty_le_tong']:.2f} | {d['ty_le_nguon_cao_nhat']:.2f} |"
            for d in kq["tai_lieu"]
            if not d["co_dao_van"]
        ),
        "",
        "## Phát hiện không trùng ca nào",
        "",
        f"{kq['nhieu']['so_phat_hien']} phát hiện. Nền là đồ án thật nên có thể là chép thật giữa các đồ án "
        f"— cần xem tay {SO_NHIEU} phát hiện dài nhất:",
        "",
        "| Nghi vấn | Nguồn | Tín hiệu | Độ dài | Trích đoạn |",
        "|---|---|---|---:|---|",
        *(
            f"| {x['nghi_van']} | {x['nguon']} | {x['tin_hieu']} | {x['do_dai']} | {x['trich'].replace('|', '\\|')} |"
            for x in kq["nhieu"]["dai_nhat"]
        ),
    ]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, required=True, help="thư mục bộ dữ liệu (có nhan.json)")
    ap.add_argument("--out", type=Path, required=True, help="thư mục ghi ket-qua-<nhan>.json/.md")
    ap.add_argument("--nhan", default="mac-dinh", help="nhãn của lần chạy (tên tệp kết quả)")
    ap.add_argument("--nguong-doan", type=float, default=Settings.model_fields["NGUONG_DOAN_MAC_DINH"].default)
    ap.add_argument(
        "--nguong-nguyen-van", type=float, default=Settings.model_fields["NGUONG_NGUYEN_VAN_MAC_DINH"].default
    )
    args = ap.parse_args(argv)
    kq = {"nhan": args.nhan, **evaluate(args.data, args.nguong_doan, args.nguong_nguyen_van)}
    md = render(kq)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"ket-qua-{args.nhan}.json").write_text(json.dumps(kq, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / f"ket-qua-{args.nhan}.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
