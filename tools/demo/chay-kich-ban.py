#!/usr/bin/env python3
"""Chạy một kịch bản JSON trên giao diện thật qua Chrome headless (CDP).

Dùng:
    python3 tools/demo/chay-kich-ban.py tools/demo/kich-ban-anh.json \
        --out-dir docs/chuong-4-trien-khai/anh \
        --json docs/chuong-4-trien-khai/ket-qua-kiem-thu/anh-chup.json
    python3 tools/demo/chay-kich-ban.py tools/demo/kich-ban-demo.json \
        --out-dir /tmp/ntma-tap-duot --log docs/chuong-4-trien-khai/ket-qua-kiem-thu/tap-duot-demo.md

Kịch bản: {"ten": ..., "buoc": [{"id", "mo_ta", "vai_tro" (mã đăng nhập hoặc null),
"hanh_dong": [...], "man_hinh_mong_doi", "cho_phep_http": [mã]}]}.
Hành động (mỗi phần tử một khóa):
    {"mo": "/duong-dan"}                 điều hướng + chờ load/mạng rảnh
    {"cho_chu": "...", "toi_da_giay": N} chờ chữ xuất hiện
    {"cho_het_chu": "...", "toi_da_giay": N}
    {"go": {"o": nhãn|selector|placeholder, "chu": "...", "enter": false}}
    {"bam": "chữ"} | {"bam": {"chu", "pham_vi", "hang"}}
    {"tai_len": {"o": selector input[type=file], "tep": đường dẫn (tương đối gốc repo)}}
    {"cuon": "chữ" | số}  {"phim": "Escape"}  {"cho": giây}  {"cho_on_dinh": true}
    {"mo_http": "/duong-dan"}            mở bằng http://<host>:${HTTP_PORT:-80} (kiểm chuyển hướng sang HTTPS)
    {"url_bat_dau": "https://"}          khẳng định URL hiện tại (vd. sau chuyển hướng HTTP -> HTTPS)
    {"chup": true | "ten-tep.png" | {"tep", "toan_trang": true}}

Bước có "ghi_du_lieu": true (thay đổi dữ liệu, hoặc cần bước ghi trước nó) bị
bỏ qua khi chạy với --chi-doc (verify-all đo NFR-16 mà không đụng trạng thái demo).

Một bước FAIL khi: hết giờ chờ/không thấy phần tử, có exception JS hoặc lỗi
console, có HTTP >= 400 không nằm trong cho_phep_http, hoặc trang tràn ngang
(scrollWidth > 1440). Mật khẩu lấy từ NTMA_MAT_KHAU, rồi SEED_DEFAULT_PASSWORD
trong deploy/.env, rồi giá trị dev mặc định — không bao giờ được in/ghi ra.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cdp import LoiTrinhDuyet, TrinhDuyet  # noqa: E402

MAT_KHAU_DEV = "DoAn@2026"


def doc_mat_khau() -> str:
    if os.environ.get("NTMA_MAT_KHAU"):
        return os.environ["NTMA_MAT_KHAU"]
    env = GOC / "deploy" / ".env"
    if env.is_file():
        for dong in env.read_text(encoding="utf-8").splitlines():
            if dong.startswith("SEED_DEFAULT_PASSWORD="):
                gt = dong.split("=", 1)[1].strip().strip('"').strip("'")
                if gt:
                    return gt
    return MAT_KHAU_DEV


def duong_dan_hien_thi(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(p)


async def chay_hanh_dong(td: TrinhDuyet, hd: dict, buoc: dict, out_dir: Path, anh: list[str]) -> None:
    if "mo" in hd:
        await td.mo(hd["mo"])
    elif "mo_http" in hd:
        host = urllib.parse.urlparse(td.base_url).hostname or "localhost"
        await td.mo(f"http://{host}:{os.environ.get('HTTP_PORT', '80')}{hd['mo_http']}")
    elif "cho_chu" in hd:
        await td.cho_chu(hd["cho_chu"], float(hd.get("toi_da_giay", 15)))
    elif "cho_het_chu" in hd:
        await td.cho_het_chu(hd["cho_het_chu"], float(hd.get("toi_da_giay", 15)))
    elif "go" in hd:
        await td.go(hd["go"]["o"], hd["go"]["chu"], enter=bool(hd["go"].get("enter")))
    elif "bam" in hd:
        b = hd["bam"]
        if isinstance(b, str):
            await td.bam(b)
        else:
            await td.bam(b["chu"], b.get("pham_vi"), b.get("hang"), float(b.get("toi_da_giay", 10)))
    elif "tai_len" in hd:
        tep = Path(hd["tai_len"]["tep"])
        await td.tai_len(hd["tai_len"]["o"], str(tep if tep.is_absolute() else GOC / tep))
    elif "cuon" in hd:
        await td.cuon(hd["cuon"])
    elif "phim" in hd:
        await td.phim(hd["phim"])
    elif "cho" in hd:
        await asyncio.sleep(float(hd["cho"]))
    elif "url_bat_dau" in hd:
        u = await td.url()
        if not u.startswith(hd["url_bat_dau"]):
            raise LoiTrinhDuyet(f"URL hiện tại {u!r} không bắt đầu bằng {hd['url_bat_dau']!r}")
    elif "cho_on_dinh" in hd:
        await td.cho_on_dinh()
    elif "chup" in hd:
        c = hd["chup"]
        ten = f"{buoc['id']}.png"
        toan_trang = False
        if isinstance(c, str):
            ten = c
        elif isinstance(c, dict):
            ten = c.get("tep", ten)
            toan_trang = bool(c.get("toan_trang"))
        await td.cho_on_dinh()
        await asyncio.sleep(0.4)  # hiệu ứng antd (fade/slide) kết thúc
        p = out_dir / ten
        await td.chup(str(p), toan_trang)
        anh.append(duong_dan_hien_thi(p))
    else:
        raise LoiTrinhDuyet(f"Hành động không hỗ trợ: {sorted(hd)}")


async def chay(args: argparse.Namespace) -> int:
    kich_ban = json.loads(Path(args.kich_ban).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    mat_khau = doc_mat_khau()
    bat_dau = time.monotonic()
    thoi_diem = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ket_qua: list[dict] = []
    that_bai = False
    cac_buoc = [b for b in kich_ban["buoc"] if not (args.chi_doc and b.get("ghi_du_lieu"))]
    bo_qua = [b["id"] for b in kich_ban["buoc"] if b not in cac_buoc]

    async with TrinhDuyet(args.base_url) as td:
        vai_tro_hien_tai: object = object()
        for buoc in cac_buoc:
            t0 = time.monotonic()
            anh: list[str] = []
            loi: list[str] = []
            do_rong = None
            cho_phep = set(buoc.get("cho_phep_http", []))
            try:
                vt = buoc.get("vai_tro")
                if vt != vai_tro_hien_tai:
                    if vt:
                        await td.dang_nhap(vt, mat_khau)
                    else:
                        await td.gui("Network.clearBrowserCookies")
                    vai_tro_hien_tai = vt
                td.xoa_bo_thu()
                for hd in buoc["hanh_dong"]:
                    await chay_hanh_dong(td, hd, buoc, out_dir, anh)
                await td.cho_on_dinh()
                do_rong = await td.do_rong()
                if do_rong > td.rong:
                    loi.append(f"tràn ngang: scrollWidth {do_rong} > {td.rong}")
            except (LoiTrinhDuyet, asyncio.TimeoutError) as e:
                loi.append(str(e) or type(e).__name__)
                vai_tro_hien_tai = object()  # đăng nhập lại ở bước sau cho chắc
            loi += [f"exception JS: {x}" for x in td.loi_js]
            loi += [f"console: {x}" for x in td.loi_console]
            http_loi = [h for h in td.http_loi if h["status"] not in cho_phep]
            if http_loi:
                loi.append("HTTP lỗi: " + ", ".join(f"{h['status']} {h['url']}" for h in http_loi))
            giay = round(time.monotonic() - t0, 1)
            kq = "OK" if not loi else "FAIL"
            if loi:
                p_loi = Path(tempfile.gettempdir()) / f"ntma-loi-{buoc['id']}.png"
                try:
                    await td.chup(str(p_loi))
                    loi.append(f"(ảnh lúc lỗi: {p_loi})")
                except Exception:
                    pass
            ket_qua.append({
                "id": buoc["id"], "mo_ta": buoc.get("mo_ta", ""), "vai_tro": buoc.get("vai_tro"),
                "man_hinh": buoc.get("man_hinh"), "man_hinh_mong_doi": buoc.get("man_hinh_mong_doi"),
                "giay": giay, "ket_qua": kq, "loi": loi,
                "http_loi": td.http_loi[:], "do_rong": do_rong,
                "anh": anh[0] if anh else None, "anh_them": anh[1:],
            })
            print(f"{kq}: {buoc['id']} ({giay} s)" + ("" if not loi else " — " + " | ".join(loi)), flush=True)
            if loi:
                that_bai = True
                if not args.tiep_tuc_khi_loi:
                    break

    tong = round(time.monotonic() - bat_dau, 1)
    tom_tat = {
        "ten": kich_ban.get("ten", Path(args.kich_ban).stem),
        "kich_ban": duong_dan_hien_thi(Path(args.kich_ban)),
        "thoi_diem_utc": thoi_diem,
        "base_url": args.base_url,
        "khung_nhin": f"{1440}x{900}",
        "buoc": ket_qua,
        "bo_qua_ghi_du_lieu": bo_qua,
        "so_buoc": len(cac_buoc),
        "so_buoc_ok": sum(1 for b in ket_qua if b["ket_qua"] == "OK"),
        "tong_giay": tong,
        "ket_qua": "OK" if not that_bai and len(ket_qua) == len(cac_buoc) else "FAIL",
    }
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(tom_tat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.log:
        ghi_log(Path(args.log), tom_tat, kich_ban)
    print(f"{tom_tat['ket_qua']}: {tom_tat['so_buoc_ok']}/{tom_tat['so_buoc']} bước, {tong} s")
    return 0 if tom_tat["ket_qua"] == "OK" else 1


def ghi_log(p: Path, tt: dict, kich_ban: dict) -> None:
    mo_ta = {b["id"]: b.get("mo_ta", "") for b in kich_ban["buoc"]}
    dong = [
        "",
        f"### Lần chạy {tt['thoi_diem_utc']} — {tt['ten']}",
        "",
        f"- Kịch bản: `{tt['kich_ban']}` · URL: `{tt['base_url']}` · khung nhìn {tt['khung_nhin']}",
        f"- Kết quả: **{tt['ket_qua']}** — {tt['so_buoc_ok']}/{tt['so_buoc']} bước OK, tổng {tt['tong_giay']} s",
        "",
        "| Bước | Mô tả | Thời gian (s) | Kết quả |",
        "|---|---|---:|---|",
    ]
    for b in tt["buoc"]:
        kq = b["ket_qua"] if not b["loi"] else f"{b['ket_qua']}: {'; '.join(b['loi'])}"
        dong.append(f"| {b['id']} | {mo_ta.get(b['id'], '').replace('|', '/')} | {b['giay']} | {kq.replace('|', '/')} |")
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("", encoding="utf-8")
    with p.open("a", encoding="utf-8") as f:
        f.write("\n".join(dong) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kich_ban")
    ap.add_argument("--base-url", default=os.environ.get(
        "BASE_URL", f"https://localhost:{os.environ.get('HTTPS_PORT') or '443'}"))
    ap.add_argument("--out-dir", default=str(Path(tempfile.gettempdir()) / "ntma-kich-ban"))
    ap.add_argument("--json")
    ap.add_argument("--log")
    ap.add_argument("--tiep-tuc-khi-loi", action="store_true")
    ap.add_argument("--chi-doc", action="store_true", help="bỏ qua các bước ghi_du_lieu")
    return asyncio.run(chay(ap.parse_args()))


if __name__ == "__main__":
    sys.exit(main())
