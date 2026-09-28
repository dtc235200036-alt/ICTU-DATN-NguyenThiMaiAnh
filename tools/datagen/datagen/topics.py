"""DATA-02 (D-05): kho 300 đề tài khóa cũ K18–K22 + 80 truy vấn tên đề tài có nhãn.

Định dạng CSV bám đúng quy tắc import kho đồ án (plan 03-05 / UC5.4):
khoa,ten_de_tai,ma_so_sinh_vien,ho_ten_sinh_vien,ma_giang_vien,tu_khoa,diem
"""

from __future__ import annotations

import csv
import json
import random
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from . import vocab

KHOA = ["K18", "K19", "K20", "K21", "K22"]
SO_DE_TAI_MOI_KHOA = 60
CSV_HEADER = ["khoa", "ten_de_tai", "ma_so_sinh_vien", "ho_ten_sinh_vien", "ma_giang_vien", "tu_khoa", "diem"]
QUERY_HEADER = ["ma_truy_van", "loai", "cum", "ma_doi_tuong", "ten_truy_van", "tieu_de_goc", "ky_vong_canh_bao", "tap"]
MA_GV_HOP_LE = [f"GV{i:03d}" for i in range(1, 23)]  # GV023–GV029 dành cho e2e, không dùng
SO_TRUY_VAN_MOI_LOAI = 40
SO_KIEM_CHUNG_MOI_LOAI = 12  # 28 HIEU_CHINH / 12 KIEM_CHUNG (~30% giữ lại)


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


# ---------------------------------------------------------------------------
# Tra cứu đối tượng
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DoiTuong:
    cum: str
    khoa_ngan: str
    dien_dat: tuple[str, str]
    nhom: str
    chi_so: int

    @property
    def ma(self) -> str:
        return f"{self.cum}.{self.khoa_ngan}"

    @property
    def du_tru(self) -> bool:
        return self.chi_so >= len(vocab.CUM[self.cum]["doi_tuong"]) - vocab.SO_DOI_TUONG_DU_TRU


def tat_ca_doi_tuong() -> list[DoiTuong]:
    out = []
    for cum, info in vocab.CUM.items():
        for i, (k, p1, p2, nhom) in enumerate(info["doi_tuong"]):
            out.append(DoiTuong(cum, k, (p1, p2), nhom, i))
    return out


def doi_tuong_theo_ma() -> dict[str, DoiTuong]:
    return {d.ma: d for d in tat_ca_doi_tuong()}


# ---------------------------------------------------------------------------
# Tên người, đơn vị, tiêu đề
# ---------------------------------------------------------------------------
def ho_ten(rng: random.Random) -> str:
    while True:
        nu = rng.random() < 0.5
        ten = " ".join([
            rng.choice(vocab.HO),
            rng.choice(vocab.DEM_NU if nu else vocab.DEM_NAM),
            rng.choice(vocab.TEN_NU if nu else vocab.TEN_NAM),
        ])
        if ten not in vocab.TEN_CAM:
            return nfc(ten)


@dataclass(frozen=True)
class DonVi:
    tat: str   # dạng viết tắt
    day: str   # dạng đầy đủ
    nhom: str

    def dang(self, day_du: bool) -> str:
        return self.day if day_du else self.tat


def sinh_don_vi(rng: random.Random, nhom: str, tranh: set[str] | None = None) -> DonVi:
    tranh = tranh or set()
    for _ in range(200):
        tat, day = rng.choice(vocab.DON_VI[nhom])
        loai = re.search(r"\{(\w+)\}", tat).group(1)
        ten = rng.choice(vocab.TEN_RIENG[loai])
        dv = DonVi(tat.format(**{loai: ten}), day.format(**{loai: ten}), nhom)
        if dv.tat not in tranh:
            return dv
    raise RuntimeError(f"không sinh được đơn vị mới cho nhóm {nhom}")


@dataclass
class TieuDe:
    """Các thành phần tạo nên một tiêu đề — giữ lại để diễn đạt lại / sinh tài liệu."""
    kieu: str            # "thuong" | "ho_tro" | "ung_dung"
    dong_tu: str
    san_pham: tuple[str, str]
    doi_tuong: DoiTuong
    dien_dat: int        # 0/1: cách diễn đạt đối tượng dùng trong tiêu đề
    tu_noi: str
    don_vi: DonVi
    day_du: bool         # đơn vị ở dạng đầy đủ hay viết tắt
    cong_nghe: str | None
    hau_to: int          # chỉ số HAU_TO_CONG_NGHE

    @property
    def dt(self) -> str:
        return self.doi_tuong.dien_dat[self.dien_dat]

    @property
    def dv(self) -> str:
        return self.don_vi.dang(self.day_du)

    def van_ban(self) -> str:
        if self.kieu == "ung_dung":
            s = f"Ứng dụng {self.cong_nghe} trong {self.dt} {self.tu_noi} {self.dv}"
        elif self.kieu == "su_dung":
            s = f"Sử dụng {self.cong_nghe} để {self.dt} {self.tu_noi} {self.dv}"
        else:
            giua = f"{self.san_pham[0]} hỗ trợ {self.dt}" if self.kieu == "ho_tro" else f"{self.san_pham[0]} {self.dt}"
            s = f"{self.dong_tu} {giua} {self.tu_noi} {self.dv}"
            if self.cong_nghe:
                s += " " + vocab.HAU_TO_CONG_NGHE[self.hau_to].format(cg=self.cong_nghe)
        s = re.sub(r"\s+", " ", s).strip()
        return nfc(s[0].upper() + s[1:])


def chon_tu_noi(rng: random.Random, nhom: str) -> str:
    return "cho" if nhom in vocab.NHOM_CHI_DUNG_CHO else rng.choice(vocab.TU_NOI)


def sinh_tieu_de(rng: random.Random, dt: DoiTuong, *, dien_dat: int, don_vi: DonVi,
                 cong_nghe_tranh: set[str] | None = None, dong_tu_tranh: set[str] | None = None) -> TieuDe:
    info = vocab.CUM[dt.cum]
    r = rng.random()
    kieu = "thuong" if r < 0.62 else ("ho_tro" if r < 0.85 else "ung_dung")
    phu_hop = vocab.cong_nghe_cua(dt.cum, dt.ma)
    cn_ung = [c for c in phu_hop if c not in (cong_nghe_tranh or set())] or phu_hop
    if not cn_ung and kieu == "ung_dung":
        kieu = "thuong"
    cong_nghe = None
    if cn_ung and (kieu == "ung_dung" or rng.random() < 0.45):
        cong_nghe = rng.choice(cn_ung)
    dong_tu_ung = [v for v in vocab.DONG_TU_TIEU_DE if v not in (dong_tu_tranh or set())] or vocab.DONG_TU_TIEU_DE
    return TieuDe(
        kieu=kieu,
        dong_tu=rng.choice(dong_tu_ung),
        san_pham=rng.choice(info["san_pham"]),
        doi_tuong=dt,
        dien_dat=dien_dat,
        tu_noi=chon_tu_noi(rng, dt.nhom),
        don_vi=don_vi,
        day_du=rng.random() < 0.35,
        cong_nghe=cong_nghe,
        hau_to=rng.randrange(len(vocab.HAU_TO_CONG_NGHE)),
    )


def dien_dat_lai(rng: random.Random, td: TieuDe) -> TieuDe:
    """Diễn đạt lại tiêu đề: cách gọi đối tượng khác, động từ/sản phẩm đồng nghĩa,
    đơn vị ở dạng còn lại, đổi từ nối — cùng một đề tài, khác câu chữ."""
    info = vocab.CUM[td.doi_tuong.cum]
    if td.kieu in ("ung_dung", "su_dung"):
        kieu = "su_dung" if td.kieu == "ung_dung" else "ung_dung"
    else:
        kieu = "ho_tro" if td.kieu == "thuong" else "thuong"
    tu_noi = td.tu_noi
    if td.doi_tuong.nhom not in vocab.NHOM_CHI_DUNG_CHO:
        tu_noi = "cho" if td.tu_noi == "tại" else "tại"
    # sản phẩm: dùng dạng đồng nghĩa (đảo cặp)
    san_pham = (td.san_pham[1], td.san_pham[0])
    cong_nghe = td.cong_nghe
    if kieu not in ("ung_dung", "su_dung") and cong_nghe and rng.random() < 0.4:
        cong_nghe = None
    return TieuDe(
        kieu=kieu,
        dong_tu=rng.choice(vocab.DONG_NGHIA_DONG_TU[td.dong_tu]),
        san_pham=san_pham,
        doi_tuong=td.doi_tuong,
        dien_dat=1 - td.dien_dat,
        tu_noi=tu_noi,
        don_vi=td.don_vi,
        day_du=not td.day_du,
        cong_nghe=cong_nghe,
        hau_to=1 - td.hau_to,
    )


# ---------------------------------------------------------------------------
# Kho 300 đề tài
# ---------------------------------------------------------------------------
@dataclass
class DongKho:
    stt: int
    khoa: str
    tieu_de: TieuDe
    ma_so_sinh_vien: str
    ho_ten_sinh_vien: str
    ma_giang_vien: str
    tu_khoa: str
    diem: str
    ten_de_tai: str = field(init=False)

    def __post_init__(self) -> None:
        self.ten_de_tai = self.tieu_de.van_ban()

    @property
    def doi_tuong(self) -> DoiTuong:
        return self.tieu_de.doi_tuong

    def csv_row(self) -> list[str]:
        return [self.khoa, self.ten_de_tai, self.ma_so_sinh_vien, self.ho_ten_sinh_vien,
                self.ma_giang_vien, self.tu_khoa, self.diem]


def _phan_khoa(rng: random.Random, so_lan: dict[str, int]) -> dict[str, list[str]]:
    """Gán mỗi đối tượng vào `so_lan` khóa KHÁC NHAU sao cho mỗi khóa đúng 60 đề tài."""
    for _ in range(100):
        con = {k: SO_DE_TAI_MOI_KHOA for k in KHOA}
        gan: dict[str, list[str]] = {}
        ok = True
        for ma in sorted(so_lan, key=lambda m: (-so_lan[m], rng.random())):
            ung = sorted(KHOA, key=lambda k: (-con[k], rng.random()))[: so_lan[ma]]
            if any(con[k] <= 0 for k in ung):
                ok = False
                break
            for k in ung:
                con[k] -= 1
            gan[ma] = sorted(ung)
        if ok and all(v == 0 for v in con.values()):
            return gan
    raise RuntimeError("không phân bổ được đối tượng vào các khóa")


def generate_topics(rng: random.Random) -> list[DongKho]:
    kho_dt = [d for d in tat_ca_doi_tuong() if not d.du_tru]
    assert len(kho_dt) == 96
    thu_tu = kho_dt[:]
    rng.shuffle(thu_tu)
    so_lan = {d.ma: (4 if i < 12 else 3) for i, d in enumerate(thu_tu)}
    assert sum(so_lan.values()) == len(KHOA) * SO_DE_TAI_MOI_KHOA
    gan = _phan_khoa(rng, so_lan)
    theo_ma = {d.ma: d for d in kho_dt}

    da_co: set[str] = set()
    theo_khoa: dict[str, list[TieuDe]] = {k: [] for k in KHOA}
    for d in kho_dt:  # thứ tự cố định theo vocab
        khoa_list = gan[d.ma]
        dien_dat0 = rng.randrange(2)
        don_vi_da: set[str] = set()
        cn_da: set[str] = set()
        for j, khoa in enumerate(khoa_list):
            for _ in range(200):
                dv = sinh_don_vi(rng, d.nhom, don_vi_da)
                td = sinh_tieu_de(rng, theo_ma[d.ma], dien_dat=(dien_dat0 + j) % 2, don_vi=dv,
                                  cong_nghe_tranh=cn_da)
                t = td.van_ban().casefold()
                if t not in da_co and len(td.van_ban()) <= 255:
                    break
            else:
                raise RuntimeError("không sinh được tiêu đề duy nhất")
            da_co.add(t)
            don_vi_da.add(dv.tat)
            if td.cong_nghe:
                cn_da.add(td.cong_nghe)
            theo_khoa[khoa].append(td)

    rows: list[DongKho] = []
    stt = 0
    for khoa in KHOA:
        ds = theo_khoa[khoa]
        assert len(ds) == SO_DE_TAI_MOI_KHOA, (khoa, len(ds))
        rng.shuffle(ds)
        yy = khoa[1:]
        for n, td in enumerate(ds, start=1):
            stt += 1
            tk = vocab.tu_khoa_cua(td.doi_tuong.cum, td.doi_tuong.ma)
            tu_khoa = ", ".join(rng.sample(tk, rng.randint(2, min(4, len(tk)))))
            rows.append(DongKho(
                stt=stt,
                khoa=khoa,
                tieu_de=td,
                ma_so_sinh_vien=f"DTC{yy}5290{n:03d}",
                ho_ten_sinh_vien=ho_ten(rng),
                ma_giang_vien=rng.choice(MA_GV_HOP_LE),
                tu_khoa=nfc(tu_khoa),
                diem=f"{rng.randint(50, 95) / 10:.1f}",
            ))
    return rows


# ---------------------------------------------------------------------------
# 80 truy vấn tên đề tài có nhãn
# ---------------------------------------------------------------------------
@dataclass
class TruyVan:
    ma_truy_van: str
    loai: str
    cum: str
    ma_doi_tuong: str
    ten_truy_van: str
    tieu_de_goc: str
    ky_vong_canh_bao: int
    tap: str

    def csv_row(self) -> list[str]:
        return [self.ma_truy_van, self.loai, self.cum, self.ma_doi_tuong, self.ten_truy_van,
                self.tieu_de_goc, str(self.ky_vong_canh_bao), self.tap]


def generate_title_queries(rng: random.Random, rows: list[DongKho]) -> list[TruyVan]:
    tieu_de_kho = {r.ten_de_tai.casefold() for r in rows}
    cum_list = list(vocab.CUM)
    moi_cum = SO_TRUY_VAN_MOI_LOAI // len(cum_list)  # 5
    tam: list[tuple[str, str, str, str, str]] = []  # (loai, cum, ma_dt, ten, goc)

    # DIEN_DAT_LAI: 5 đối tượng khác nhau mỗi cụm, diễn đạt lại một tiêu đề trong kho.
    for cum in cum_list:
        theo_dt: dict[str, list[DongKho]] = {}
        for r in rows:
            if r.doi_tuong.cum == cum:
                theo_dt.setdefault(r.doi_tuong.ma, []).append(r)
        chon = rng.sample(sorted(theo_dt), moi_cum)
        for ma in chon:
            goc = rng.choice(theo_dt[ma])
            for _ in range(50):
                ten = dien_dat_lai(rng, goc.tieu_de).van_ban()
                if ten.casefold() not in tieu_de_kho:
                    break
            else:
                raise RuntimeError("diễn đạt lại trùng tiêu đề kho")
            tam.append(("DIEN_DAT_LAI", cum, ma, ten, goc.ten_de_tai))

    # CUNG_LINH_VUC: đối tượng dự trữ (không có trong kho) của từng cụm.
    da_co = set(tieu_de_kho)
    for cum in cum_list:
        du_tru = [d for d in tat_ca_doi_tuong() if d.cum == cum and d.du_tru]
        ke_hoach = [du_tru[i % len(du_tru)] for i in range(moi_cum)]
        for i, d in enumerate(ke_hoach):
            for _ in range(50):
                dv = sinh_don_vi(rng, d.nhom)
                ten = sinh_tieu_de(rng, d, dien_dat=(i // len(du_tru)) % 2, don_vi=dv).van_ban()
                if ten.casefold() not in da_co:
                    break
            da_co.add(ten.casefold())
            tam.append(("CUNG_LINH_VUC", cum, d.ma, ten, ""))

    # Tách tập: 12/40 mỗi loại là KIEM_CHUNG (không dùng để hiệu chỉnh ngưỡng).
    tap: list[str] = []
    for loai in ("DIEN_DAT_LAI", "CUNG_LINH_VUC"):
        idx = [i for i, t in enumerate(tam) if t[0] == loai]
        kc = set(rng.sample(idx, SO_KIEM_CHUNG_MOI_LOAI))
        tap.extend("KIEM_CHUNG" if i in kc else "HIEU_CHINH" for i in idx)
    thu_tu = list(range(len(tam)))
    rng.shuffle(thu_tu)
    out = []
    for n, i in enumerate(thu_tu, start=1):
        loai, cum, ma, ten, goc = tam[i]
        out.append(TruyVan(f"TV{n:03d}", loai, cum, ma, nfc(ten), nfc(goc),
                           1 if loai == "DIEN_DAT_LAI" else 0, tap[i]))
    return out


# ---------------------------------------------------------------------------
# Ghi tệp
# ---------------------------------------------------------------------------
def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
        w.writerow(header)
        w.writerows(rows)


def topics_manifest(rows: list[DongKho]) -> list[dict]:
    return [{"stt": r.stt, "khoa": r.khoa, "ten_de_tai": r.ten_de_tai, "cum": r.doi_tuong.cum,
             "ma_doi_tuong": r.doi_tuong.ma} for r in rows]


def update_manifest(path: Path, sections: dict) -> None:
    data: dict = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    data.update(sections)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def build_topics(seed: int) -> tuple[list[DongKho], list[TruyVan]]:
    rng = random.Random(seed)
    rows = generate_topics(rng)
    queries = generate_title_queries(rng, rows)
    return rows, queries


def write_topics(out: Path, seed: int, meta: dict) -> tuple[list[DongKho], list[TruyVan]]:
    rows, queries = build_topics(seed)
    write_csv(out / "de-tai-kho.csv", CSV_HEADER, [r.csv_row() for r in rows])
    write_csv(out / "truy-van-ten-de-tai.csv", QUERY_HEADER, [q.csv_row() for q in queries])
    update_manifest(out / "manifest.json", {**meta, "topics": topics_manifest(rows)})
    return rows, queries
