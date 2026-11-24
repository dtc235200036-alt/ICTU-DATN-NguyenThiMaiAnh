"""Sinh bộ dữ liệu đánh giá kiểu PAN từ đồ án thật trong gói nạp.

    .venv/bin/python -m evaluation.tao_bo chon --goi <goi-nap> --out <pan-eval> \\
        [--seed 20261109] [--so-nghi-van 20] [--so-sach 10]
    .venv/bin/python -m evaluation.tao_bo tao --out <pan-eval>

`chon`: trích xuất mọi PDF bằng đúng hàm production (calibration/extract.py),
loại tài liệu không dùng được, chia thành tài liệu nền (so-nghi-van bị chèn đạo
văn + so-sach sạch) và kho nguồn (phần còn lại). Mỗi tài liệu bị chèn nhận một
ca cho mỗi kiểu biến đổi, mỗi ca lấy từ một nguồn khác nhau. Đoạn = 3–8 câu thân
bài liền nhau (60–250 âm tiết) còn lại sau strip_boilerplate. Ghi ke-hoach.json
và can-llm.jsonl (đoạn gốc của các ca `llm`, chờ LLM diễn đạt lại).
`tao`: đọc kế hoạch + dien-dat-lai-llm.jsonl, áp dụng biến đổi, chèn mỗi đoạn
thành dòng riêng tại ranh giới dòng trong thân bài, ghi nguon/ (chỉ kho nguồn),
nghi-van/, nhan.json rồi tự kiểm offset hai chiều.

Offset là chỉ số str Python trên văn bản đọc bằng Path.read_text(encoding="utf-8").
Dữ liệu là đồ án thật của sinh viên: --out phải nằm ngoài kho git.
"""
import argparse
import json
import random
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

from app.nlp.boilerplate import strip_boilerplate
from app.nlp.chunking import sentences
from app.nlp.normalize import nfc, one_line, syllables
from calibration.extract import extract_text
from evaluation.obfuscate import BIEN_DOI

REPO_DIR = Path(__file__).resolve().parents[2]
KIEU = (*BIEN_DOI, "llm")
SO_CAU = (3, 8)
SO_AM_TIET = (60, 250)
TOI_THIEU = 10  # số đoạn ứng viên tối thiểu để tài liệu dùng được (vị trí chèn: ≥ 4 × số kiểu)
_KET_CAU = re.compile(r"[.!?…][\"”’')\]]*$")
_KY_HIEU = re.compile(r"[{}<>=$#@\\|`•●▪■◆➢✓]")
_CO_DAU = re.compile(r"[^\x00-\x7f]")


def log(msg: str) -> None:
    print(f"[tao_bo] {msg}", file=sys.stderr, flush=True)


def _ngoai_git(out: Path) -> Path:
    out = out.resolve()
    if out == REPO_DIR or REPO_DIR in out.parents:
        raise SystemExit(f"--out {out} nằm trong kho git: dữ liệu đồ án thật không được vào repo")
    return out


def doc_pdf(path: Path) -> str | None:
    text = extract_text(path.read_bytes(), "PDF")
    # Path.read_text đổi \r thành \n → bỏ \r trước khi tính offset và ghi tệp.
    return text and text.replace("\r\n", "\n").replace("\r", "\n")


def _tot(text: str, c: tuple[str, int, int] | None) -> bool:
    """Câu dùng được trong đoạn: văn xuôi tiếng Việt (kết thúc bằng dấu câu, không
    ký hiệu mã nguồn/gạch đầu dòng, ≥ 30 % âm tiết có dấu — loại tiếng Anh, mã
    nguồn, bảng) và không dính tiêu đề/ô bảng: câu bắt đầu ở đầu dòng mà dòng đầu
    < 60 ký tự, không dấu câu (dòng thân bài đầy ~70–95 ký tự; số thứ tự tiêu đề
    nằm ở dòng riêng nên strip_boilerplate không lọc được tên tiêu đề). Đo bằng
    ký tự vì PDF hay dính từ ("hệthống") làm sai số âm tiết."""
    if c is None:
        return False
    s, dau, cuoi = c
    am_tiet = syllables(s)
    co_dau = sum(1 for a in am_tiet if _CO_DAU.search(a))
    e = text.find("\n", dau, cuoi)
    dong_dau = text[dau:e].strip()
    dinh_tieu_de = (
        e >= 0
        and not text[text.rfind("\n", 0, dau) + 1 : dau].strip()
        and len(dong_dau) < 60
        and not dong_dau.endswith((".", "!", "?", "…", ":", ";", ","))
    )
    return (
        bool(_KET_CAU.search(s))
        and not _KY_HIEU.search(s)
        and co_dau >= 0.3 * len(am_tiet)
        and not dinh_tieu_de
    )


def phan_tich(text: str):
    """Câu thân bài (đúng strip_boilerplate + chunking production) kèm vị trí
    [đầu, cuối) trong văn bản gốc; đoạn ứng viên (i, j) = câu i..j-1 liền nhau
    trong văn bản gốc; vị trí chèn = đầu dòng ngay sau một câu thân bài đã kết
    thúc ở cuối dòng (không phải câu cuối)."""
    cau, pos = [], 0
    for s in sentences(strip_boilerplate(text).lines):
        m = re.compile(r"[\s\u200b]+".join(map(re.escape, s.split(" ")))).search(text, pos)
        # Không khớp: câu vắt qua dòng đã bị lọc (header, số trang) → không dùng.
        cau.append((s, m.start(), m.end()) if m else None)
        pos = m.end() if m else pos
    lien = [
        a is not None and b is not None and not text[a[2] : b[1]].strip()
        for a, b in zip(cau, cau[1:])
    ]
    tot = [_tot(text, c) for c in cau]
    n_am = [len(syllables(c[0])) if c else 0 for c in cau]
    doan = [
        (i, j)
        for i in range(len(cau))
        for j in range(i + SO_CAU[0], min(i + SO_CAU[1], len(cau)) + 1)
        if all(tot[i:j]) and all(lien[i : j - 1]) and SO_AM_TIET[0] <= sum(n_am[i:j]) <= SO_AM_TIET[1]
    ]
    chen = []
    for c in cau[:-1]:
        e = text.find("\n", c[2]) if c and _KET_CAU.search(c[0]) else -1
        if e >= 0 and not text[c[2] : e].strip():
            chen.append(e + 1)
    return cau, doan, chen


def _rai_deu(chen: list[int], n: int, rng: random.Random) -> list[int]:
    """n vị trí chèn rải đều thân bài: chia n nhóm liên tiếp, chọn trong nửa giữa
    mỗi nhóm → hai đoạn chèn luôn cách nhau ít nhất một câu của tài liệu nền."""
    out = []
    for g in range(n):
        nhom = chen[g * len(chen) // n : (g + 1) * len(chen) // n]
        out.append(rng.choice(nhom[len(nhom) // 4 : len(nhom) - len(nhom) // 4]))
    return out


def cmd_chon(args: argparse.Namespace) -> int:
    out = _ngoai_git(args.out)
    rng = random.Random(args.seed)
    manifest = json.loads((args.goi / "manifest.json").read_text(encoding="utf-8"))
    tai_lieu, loai_tru = {}, []
    for cap in manifest["cap"]:
        ma = cap["ma_cap"]
        text = doc_pdf(args.goi / cap["A"]["tep"])
        if text is None:
            loai_tru.append({"id": ma, "ly_do": "trích xuất thất bại (PDF lỗi hoặc rỗng)"})
            continue
        cau, doan, chen = phan_tich(text)
        if len(doan) < TOI_THIEU or len(chen) < 4 * len(KIEU):
            loai_tru.append(
                {"id": ma, "ly_do": f"quá ít nội dung thân bài ({len(doan)} đoạn ứng viên, {len(chen)} vị trí chèn)"}
            )
            continue
        tai_lieu[ma] = (cap["A"], cau, doan, chen)
    log(f"{len(tai_lieu)}/{len(manifest['cap'])} PDF dùng được, loại {len(loai_tru)}")
    for x in loai_tru:
        log(f"  loại {x['id']}: {x['ly_do']}")

    so_nen = args.so_nghi_van + args.so_sach
    if len(tai_lieu) < so_nen + len(KIEU):
        raise SystemExit(f"chỉ {len(tai_lieu)} tài liệu dùng được, cần ≥ {so_nen + len(KIEU)}")
    nen = rng.sample(sorted(tai_lieu), so_nen)
    dao_van = set(nen[: args.so_nghi_van])
    kho = sorted(set(tai_lieu) - set(nen))

    nghi_van, can_llm, so_ca = [], [], 0
    for k, ma in enumerate(sorted(nen), start=1):
        ds_ca = []
        if ma in dao_van:
            vi_tri = _rai_deu(tai_lieu[ma][3], len(KIEU), rng)
            # Xáo kiểu để vị trí trong tài liệu không lộ kiểu biến đổi.
            for kieu, nguon, q in zip(rng.sample(KIEU, len(KIEU)), rng.sample(kho, len(KIEU)), vi_tri):
                _, cau, doan, _ = tai_lieu[nguon]
                i, j = rng.choice(doan)
                so_ca += 1
                ca = {
                    "id": f"C{so_ca:03d}",
                    "nguon": nguon,
                    "bien_doi": kieu,
                    "ng_bat_dau": cau[i][1],
                    "ng_do_dai": cau[j - 1][2] - cau[i][1],
                    "van_ban": " ".join(c[0] for c in cau[i:j]),
                    "chen": q,
                }
                ds_ca.append(ca)
                if kieu == "llm":
                    can_llm.append({"id": ca["id"], "nguon": nguon, "text": ca["van_ban"]})
        nghi_van.append(
            {"id": f"S{k:03d}", "tep": f"nghi-van/S{k:03d}.txt", "nen": ma, "co_dao_van": ma in dao_van, "ca": ds_ca}
        )

    ke_hoach = {
        "seed": args.seed,
        "goi": str(args.goi.resolve()),
        "tham_so": {
            "so_nghi_van": args.so_nghi_van,
            "so_sach": args.so_sach,
            "so_cau": list(SO_CAU),
            "so_am_tiet": list(SO_AM_TIET),
            "bien_doi": list(KIEU),
        },
        "loai_tru": loai_tru,
        "nguon": [{"id": ma, "tep": f"nguon/{ma}.txt", "ten_de_tai": tai_lieu[ma][0]["ten_de_tai"]} for ma in kho],
        "nghi_van": nghi_van,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "ke-hoach.json").write_text(json.dumps(ke_hoach, ensure_ascii=False, indent=1), encoding="utf-8")
    tep_llm = out / "can-llm.jsonl"
    tep_llm.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in can_llm), encoding="utf-8")
    log(f"nền: {args.so_nghi_van} có đạo văn + {args.so_sach} sạch; kho nguồn: {len(kho)} tài liệu")
    dem = Counter(ca["bien_doi"] for h in nghi_van for ca in h["ca"])
    log("số ca theo kiểu: " + ", ".join(f"{k}={dem[k]}" for k in KIEU))
    log(f"đã ghi {out / 'ke-hoach.json'} và {tep_llm} ({len(can_llm)} dòng)")
    return 0


def cmd_tao(args: argparse.Namespace) -> int:
    out = _ngoai_git(args.out)
    plan = json.loads((out / "ke-hoach.json").read_text(encoding="utf-8"))
    tep_llm = out / "dien-dat-lai-llm.jsonl"
    dong_llm = tep_llm.read_text(encoding="utf-8").splitlines() if tep_llm.exists() else []
    llm = {d["id"]: d["text"] for d in map(json.loads, filter(str.strip, dong_llm))}
    thieu = [ca["id"] for h in plan["nghi_van"] for ca in h["ca"] if ca["bien_doi"] == "llm" and ca["id"] not in llm]
    if thieu:
        raise SystemExit(f"{tep_llm} thiếu {len(thieu)} ca llm: {', '.join(thieu)}")

    goi = Path(plan["goi"])
    tep_pdf = {
        c["ma_cap"]: goi / c["A"]["tep"]
        for c in json.loads((goi / "manifest.json").read_text(encoding="utf-8"))["cap"]
    }
    can = sorted({n["id"] for n in plan["nguon"]} | {h["nen"] for h in plan["nghi_van"]})
    goc = {ma: doc_pdf(tep_pdf[ma]) for ma in can}
    for thu_muc in ("nguon", "nghi-van"):
        shutil.rmtree(out / thu_muc, ignore_errors=True)
        (out / thu_muc).mkdir()
    for n in plan["nguon"]:
        (out / n["tep"]).write_text(goc[n["id"]], encoding="utf-8")

    nghi_van, mong_doi = [], {}
    for h in plan["nghi_van"]:
        nen, sv, cuoi, ds_ca = goc[h["nen"]], "", 0, []
        for ca in sorted(h["ca"], key=lambda c: c["chen"]):
            if ca["bien_doi"] == "llm":
                doan = llm[ca["id"]]
            else:
                doan = BIEN_DOI[ca["bien_doi"]](ca["van_ban"], random.Random(f"{plan['seed']}-{ca['id']}"))
            doan = nfc(doan).strip()
            sv += nen[cuoi : ca["chen"]]
            ds_ca.append(
                {
                    "id": ca["id"],
                    "nguon": ca["nguon"],
                    "bien_doi": ca["bien_doi"],
                    "nv_bat_dau": len(sv),
                    "nv_do_dai": len(doan),
                    "ng_bat_dau": ca["ng_bat_dau"],
                    "ng_do_dai": ca["ng_do_dai"],
                }
            )
            sv += doan + "\n"
            cuoi = ca["chen"]
            mong_doi[ca["id"]] = (doan, ca["van_ban"])
        sv += nen[cuoi:]
        (out / h["tep"]).write_text(sv, encoding="utf-8")
        nghi_van.append({**{k: h[k] for k in ("id", "tep", "nen", "co_dao_van")}, "ca": ds_ca})

    nhan = {"seed": plan["seed"], "tham_so": plan["tham_so"], "nguon": plan["nguon"], "nghi_van": nghi_van}
    (out / "nhan.json").write_text(json.dumps(nhan, ensure_ascii=False, indent=1), encoding="utf-8")
    _tu_kiem(out, nhan, goc, mong_doi)
    so_ca = sum(len(h["ca"]) for h in nghi_van)
    log(f"đã ghi {len(plan['nguon'])} nguồn, {len(nghi_van)} nghi vấn ({so_ca} ca), nhan.json — tự kiểm đạt")
    return 0


def _tu_kiem(out: Path, nhan: dict, goc: dict[str, str], mong_doi: dict[str, tuple[str, str]]) -> None:
    """Đọc lại tệp đã ghi: mỗi lát cắt nv/ng đúng văn bản mong đợi, đoạn chèn
    còn nguyên sau strip_boilerplate, bỏ các đoạn chèn thì trả lại đúng tài liệu
    nền gốc (tài liệu sạch = bản gốc không đổi)."""
    gop = lambda s: re.sub(r"\s+", " ", s)  # noqa: E731
    nguon = {n["id"]: (out / n["tep"]).read_text(encoding="utf-8") for n in nhan["nguon"]}
    for ma, text in nguon.items():
        assert text == goc[ma], f"nguon/{ma}.txt khác văn bản trích xuất"
    for h in nhan["nghi_van"]:
        assert h["nen"] not in nguon, f"{h['id']}: tài liệu nền {h['nen']} lại nằm trong kho nguồn"
        assert h["co_dao_van"] == bool(h["ca"]), f"{h['id']}: co_dao_van không khớp danh sách ca"
        sv = (out / h["tep"]).read_text(encoding="utf-8")
        than_bai = gop(" ".join(strip_boilerplate(sv).lines))
        con_lai, cuoi = "", 0
        for ca in h["ca"]:
            doan, van_ban = mong_doi[ca["id"]]
            ng = nguon[ca["nguon"]][ca["ng_bat_dau"] : ca["ng_bat_dau"] + ca["ng_do_dai"]]
            assert gop(one_line(ng)) == van_ban, f"{ca['id']}: lát cắt ng_* khác đoạn gốc"
            assert sv[ca["nv_bat_dau"] : ca["nv_bat_dau"] + ca["nv_do_dai"]] == doan, f"{ca['id']}: lát cắt nv_* sai"
            assert gop(doan) in than_bai, f"{ca['id']}: đoạn chèn bị strip_boilerplate lọc mất"
            con_lai += sv[cuoi : ca["nv_bat_dau"]]
            cuoi = ca["nv_bat_dau"] + ca["nv_do_dai"] + 1
        assert con_lai + sv[cuoi:] == goc[h["nen"]], f"{h['id']}: phần ngoài đoạn chèn khác tài liệu nền gốc"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("chon", help="chọn tài liệu nền, nguồn và đoạn; ghi ke-hoach.json + can-llm.jsonl")
    sp.add_argument("--goi", type=Path, required=True, help="thư mục gói nạp (manifest.json + tai-lieu/)")
    sp.add_argument("--out", type=Path, required=True, help="thư mục pan-eval (ngoài git)")
    sp.add_argument("--seed", type=int, default=20261109)
    sp.add_argument("--so-nghi-van", type=int, default=20, help="số tài liệu nền bị chèn đạo văn")
    sp.add_argument("--so-sach", type=int, default=10, help="số tài liệu nền sạch")
    sp = sub.add_parser("tao", help="áp dụng biến đổi; ghi nguon/, nghi-van/, nhan.json rồi tự kiểm")
    sp.add_argument("--out", type=Path, required=True, help="thư mục pan-eval (ngoài git)")
    args = ap.parse_args(argv)
    return cmd_chon(args) if args.cmd == "chon" else cmd_tao(args)


if __name__ == "__main__":
    sys.exit(main())
