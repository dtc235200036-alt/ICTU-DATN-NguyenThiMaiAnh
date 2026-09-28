"""DATA-03 (D-06): 25 cặp tài liệu A/B với phổ trùng lặp chủ đích và nguồn gốc từng đoạn.

A = một đề tài trong kho 300 (tên, khóa, GVHD, SV lấy từ dòng kho).
B = bài nộp cần kiểm tra, theo 4 loại:
  CHEP_NGUYEN_VAN  — chép nguyên văn một dải đoạn liên tiếp của A (40–60% nội dung B)
  DIEN_DAT_LAI     — cùng dải đó nhưng viết lại từng câu (câu anh em + đồng nghĩa, đảo thứ tự câu)
  CUNG_LINH_VUC    — đối tượng dự trữ cùng cụm, không chép/diễn đạt đoạn nào
  KHONG_LIEN_QUAN  — đối tượng của cụm khác
"""

from __future__ import annotations

import collections
import hashlib
import random
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from . import render, vocab
from . import topics as T

MUC = ["mo_dau", "ly_thuyet", "phan_tich", "cai_dat", "ket_luan"]
LOAI = [("CHEP_NGUYEN_VAN", 7), ("DIEN_DAT_LAI", 7), ("CUNG_LINH_VUC", 6), ("KHONG_LIEN_QUAN", 5)]
KY_VONG = {"CHEP_NGUYEN_VAN": 1, "DIEN_DAT_LAI": 1, "CUNG_LINH_VUC": 0, "KHONG_LIEN_QUAN": 0}
DO_DAI = {"DE_CUONG": (16, 22), "BAO_CAO": (55, 62)}
SO_BAO_CAO_MOI_LOAI = 2
SO_KIEM_CHUNG_MOI_LOAI = 2
TY_LE_CHEP = (0.42, 0.58)   # mục tiêu an toàn bên trong khoảng 40–60% của kế hoạch
MAX_DUNG_MAU = 2            # một mẫu câu dùng tối đa 2 lần mỗi tài liệu
MAX_AM_TIET = 90
SO_CAU = [2, 3, 4, 5]
TRONG_SO_CAU = [0.42, 0.40, 0.14, 0.04]
NAM_HIEN_TAI = 2026


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def viet_hoa_dau(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


# ---------------------------------------------------------------------------
# Thay đồng nghĩa một lượt (theo ranh giới âm tiết), giữ chữ hoa đầu.
# ---------------------------------------------------------------------------
_DN_MAP: dict[str, str] = {}
for _a, _b in vocab.DONG_NGHIA:
    _DN_MAP[_a.lower()] = _b
    _DN_MAP[_b.lower()] = _a
_DN_RE = re.compile(r"(?<!\w)(" + "|".join(re.escape(k) for k in sorted(_DN_MAP, key=len, reverse=True)) + r")(?!\w)",
                    re.IGNORECASE)


def thay_dong_nghia(s: str) -> str:
    def rep(m: re.Match) -> str:
        goc = m.group(0)
        moi = _DN_MAP[goc.lower()]
        return viet_hoa_dau(moi) if goc[:1].isupper() else moi
    return _DN_RE.sub(rep, s)


# ---------------------------------------------------------------------------
# Ngữ cảnh tài liệu, câu, đoạn
# ---------------------------------------------------------------------------
@dataclass
class NguCanh:
    doi_tuong: T.DoiTuong
    dt: tuple[str, str]
    sp: tuple[str, str]
    dv: tuple[str, str]
    cong_nghe: list[str]

    @property
    def lv(self) -> tuple[str, str]:
        return vocab.CUM[self.doi_tuong.cum]["linh_vuc"]

    @property
    def ho_so(self) -> tuple[list[str], list[str], list[str]]:
        a, f, d = vocab.HO_SO[self.doi_tuong.ma]
        return a.split("|"), f.split("|"), d.split("|")


@dataclass
class Cau:
    muc: str          # khóa MAU_CAU ("cong_nghe" cho dữ kiện công nghệ)
    mau: int
    dang: int         # 0 = câu gốc, 1 = câu anh em
    gt: dict[str, tuple[str, str]]

    def _ve(self, dang: int, alt: bool) -> str:
        tpl = vocab.MAU_CAU[self.muc][self.mau][dang]
        s = tpl.format(**{k: (v[1] if alt else v[0]) for k, v in self.gt.items()})
        s = viet_hoa_dau(re.sub(r"\s+", " ", s).strip())
        return nfc(s)

    def van_ban(self) -> str:
        return self._ve(self.dang, alt=False)

    def dien_dat_lai(self) -> str:
        return nfc(viet_hoa_dau(thay_dong_nghia(self._ve(1 - self.dang, alt=True))))


@dataclass
class Doan:
    muc: str
    cau: list[Cau]
    text: str = ""

    def __post_init__(self) -> None:
        if not self.text:
            self.text = " ".join(c.van_ban() for c in self.cau)


def kiem_cau(s: str) -> None:
    assert s.endswith("."), s
    assert ". " not in s, s
    assert len(s.split()) <= MAX_AM_TIET, s


class BoSinhDoan:
    """Sinh đoạn cho MỘT tài liệu, giữ giới hạn dùng mẫu câu."""

    def __init__(self, rng: random.Random, ctx: NguCanh) -> None:
        self.rng = rng
        self.ctx = ctx
        self.dung: collections.Counter = collections.Counter()

    def _gia_tri(self, cg: str | None = None) -> dict[str, tuple[str, str]]:
        rng, ctx = self.rng, self.ctx
        tac_nhan, chuc_nang, du_lieu = ctx.ho_so
        tn, tn2 = rng.sample(tac_nhan, 2)
        cn, cn2 = rng.sample(chuc_nang, 2)
        dl, dl2 = rng.sample(du_lieu, 2)
        cg = cg or rng.choice(ctx.cong_nghe)
        f = vocab.CONG_NGHE[cg]
        so = lambda x: (x, x)  # noqa: E731
        return {
            "dt": ctx.dt, "sp": ctx.sp, "dv": ctx.dv, "lv": ctx.lv,
            "tn": so(tn), "tn2": so(tn2), "cn": so(cn), "cn2": so(cn2), "dl": so(dl), "dl2": so(dl2),
            "cg": so(cg), "cgl": (f[0], f[1]), "cgm": (f[2], f[3]), "cgu": (f[4], f[5]),
            "n1": so(str(rng.randint(120, 950))), "n2": so(str(rng.choice([15, 20, 30, 45, 60]))),
            "n3": so(str(rng.randint(3, 18))), "pt": so(str(rng.randint(20, 60))),
            "gs": so(f"{rng.randint(4, 25) / 10:.1f}".replace(".", ",")),
            "diem": so(f"{rng.randint(38, 47) / 10:.1f}".replace(".", ",")),
        }

    def _con_lai(self, muc: str) -> int:
        return sum(MAX_DUNG_MAU - self.dung[(muc, i)] for i in range(len(vocab.MAU_CAU[muc])))

    def _chon_mau(self, muc: str, k: int) -> list[int]:
        ung = [i for i in range(len(vocab.MAU_CAU[muc])) if self.dung[(muc, i)] < MAX_DUNG_MAU]
        if len(ung) < k:
            raise RuntimeError(f"hết mẫu câu mục {muc}")
        # ưu tiên mẫu chưa dùng để câu trong tài liệu đa dạng
        self.rng.shuffle(ung)
        ung.sort(key=lambda i: self.dung[(muc, i)])
        chon = ung[:k]
        for i in chon:
            self.dung[(muc, i)] += 1
        return chon

    def _cau(self, muc: str, mau: int, cg: str | None = None) -> Cau:
        c = Cau(muc, mau, self.rng.randrange(2), self._gia_tri(cg))
        kiem_cau(c.van_ban())
        kiem_cau(c.dien_dat_lai())
        return c

    def doan(self, muc: str, doan_con_sau: int = 0) -> Doan:
        k = self.rng.choices(SO_CAU, TRONG_SO_CAU)[0]
        k = max(2, min(k, self._con_lai(muc) - 2 * doan_con_sau))
        return Doan(muc, [self._cau(muc, i) for i in self._chon_mau(muc, k)])

    def doan_cong_nghe(self, cg: str) -> Doan:
        """Đoạn giới thiệu một công nghệ: 2 câu dữ kiện + 0–1 câu lý thuyết chung."""
        cau = [self._cau("cong_nghe", i, cg) for i in self._chon_mau("cong_nghe", 2)]
        if self.rng.random() < 0.5 and self._con_lai("ly_thuyet") > 0:
            cau.append(self._cau("ly_thuyet", self._chon_mau("ly_thuyet", 1)[0], cg))
        return Doan("ly_thuyet", cau)

    def muc(self, muc: str, n: int) -> list[Doan]:
        if muc != "ly_thuyet":
            return [self.doan(muc, n - 1 - j) for j in range(n)]
        so_cn = min(len(self.ctx.cong_nghe), max(1, n // 3)) if n > 0 else 0
        chung = [self.doan(muc, n - so_cn - 1 - j) for j in range(n - so_cn)]
        return chung + [self.doan_cong_nghe(cg) for cg in self.ctx.cong_nghe[:so_cn]]


def phan_bo(n: int) -> dict[str, int]:
    mo = max(2, round(n * 0.14))
    ly = max(2, min(int(n * 0.15), round(n * 0.13)))
    kl = max(2, round(n * 0.12))
    con = n - mo - ly - kl
    return {"mo_dau": mo, "ly_thuyet": ly, "phan_tich": (con + 1) // 2, "cai_dat": con // 2, "ket_luan": kl}


# ---------------------------------------------------------------------------
# Tài liệu và cặp
# ---------------------------------------------------------------------------
@dataclass
class TaiLieu:
    tep: str
    dinh_dang: str
    ten_de_tai: str
    ho_ten_sinh_vien: str
    giang_vien: str
    nam: int
    do_dai: str
    ctx: NguCanh
    doan: list[Doan] = field(default_factory=list)
    nguon: list[dict | None] = field(default_factory=list)

    @property
    def noi_dung(self) -> list[str]:
        return [d.text for d in self.doan]

    def bam(self) -> str:
        return hashlib.sha256("\n".join(nfc(t) for t in self.noi_dung).encode("utf-8")).hexdigest()


@dataclass
class Cap:
    ma_cap: str
    loai: str
    tap: str
    do_dai: str
    A: TaiLieu
    B: TaiLieu
    dong_kho: T.DongKho
    ty_le_sao_chep: float = 0.0


def _ten_gv(rng: random.Random) -> dict[str, str]:
    """Tên GVHD tổng hợp cho trang bìa (mã GV001–GV022 → tên cố định)."""
    return {ma: f"{vocab.HOC_VI[i % len(vocab.HOC_VI)]} {T.ho_ten(rng)}" for i, ma in enumerate(T.MA_GV_HOP_LE)}


def _cong_nghe_tai_lieu(rng: random.Random, dt: T.DoiTuong, so: int, uu_tien: str | None,
                        tranh: set[str]) -> list[str]:
    ung = [c for c in vocab.cong_nghe_cua(dt.cum, dt.ma) if c not in tranh]
    if not ung:
        ung = [c for c in vocab.CUM[dt.cum]["cong_nghe"] if c not in tranh]
    out: list[str] = []
    if uu_tien and uu_tien in ung:
        out.append(uu_tien)
    rest = [c for c in ung if c not in out]
    rng.shuffle(rest)
    return (out + rest)[:so]


def _ctx_tu_tieu_de(td: T.TieuDe, cong_nghe: list[str], doi_tuong: T.DoiTuong | None = None,
                    dien_dat: int | None = None) -> NguCanh:
    dt = doi_tuong or td.doi_tuong
    i = td.dien_dat if dien_dat is None else dien_dat
    return NguCanh(
        doi_tuong=dt,
        dt=(dt.dien_dat[i], dt.dien_dat[1 - i]),
        sp=td.san_pham,
        dv=(td.dv, td.don_vi.dang(not td.day_du)),
        cong_nghe=cong_nghe,
    )


def _ke_hoach(rng: random.Random, rows: list[T.DongKho]):
    """Chọn cụm/đối tượng cho 25 cặp, thử lại (tất định) tới khi thỏa mọi ràng buộc."""
    dts = T.tat_ca_doi_tuong()
    theo_cum = {c: [d for d in dts if d.cum == c] for c in vocab.CUM}
    co_ho_so = lambda d: d.ma in vocab.HO_SO  # noqa: E731
    loai_list = [lo for lo, n in LOAI for _ in range(n)]
    cum_list = list(vocab.CUM)
    for _ in range(500):
        dem = [3] * len(cum_list)
        dem[rng.randrange(len(cum_list))] += 1
        slots = [c for c, n in zip(cum_list, dem) for _ in range(n)]
        rng.shuffle(slots)
        cung = [slots[i] for i, lo in enumerate(loai_list) if lo == "CUNG_LINH_VUC"]
        if len(set(cung)) != len(cung):
            continue
        dung: set[str] = set()
        ke: list[list] = []
        ok = True
        for lo, cum in zip(loai_list, slots):
            ung = [d for d in theo_cum[cum] if not d.du_tru and co_ho_so(d) and d.ma not in dung]
            if not ung:
                ok = False
                break
            a = rng.choice(ung)
            dung.add(a.ma)
            ke.append([lo, a, None])
        if not ok:
            continue
        for item in ke:  # B cho CHEP/DIEN/CUNG
            lo, a, _ = item
            if lo in ("CHEP_NGUYEN_VAN", "DIEN_DAT_LAI"):
                ung = [d for d in theo_cum[a.cum] if not d.du_tru and co_ho_so(d) and d.ma not in dung]
            elif lo == "CUNG_LINH_VUC":
                ung = [d for d in theo_cum[a.cum] if d.du_tru and co_ho_so(d) and d.ma not in dung]
            else:
                continue
            if not ung:
                ok = False
                break
            item[2] = rng.choice(ung)
            dung.add(item[2].ma)
        if not ok:
            continue
        for item in ke:  # B cho KHONG_LIEN_QUAN: cụm khác
            lo, a, _ = item
            if lo != "KHONG_LIEN_QUAN":
                continue
            ung = [d for d in dts if d.cum != a.cum and not d.du_tru and co_ho_so(d) and d.ma not in dung]
            if not ung:
                ok = False
                break
            item[2] = rng.choice(ung)
            dung.add(item[2].ma)
        if ok:
            return ke
    raise RuntimeError("không lập được kế hoạch cặp")


def _chon_dong_kho(rng: random.Random, rows: list[T.DongKho], a: T.DoiTuong, dem_khoa: collections.Counter) -> T.DongKho:
    ung = [r for r in rows if r.doi_tuong.ma == a.ma]
    ung.sort(key=lambda r: (dem_khoa[r.khoa], rng.random()))
    r = ung[0]
    dem_khoa[r.khoa] += 1
    return r


def _tao_A(rng: random.Random, ma_cap: str, r: T.DongKho, dinh_dang: str, do_dai: str, ten_gv: dict) -> TaiLieu:
    so_cn = 1 if do_dai == "DE_CUONG" else 2
    cn = _cong_nghe_tai_lieu(rng, r.doi_tuong, so_cn, r.tieu_de.cong_nghe, set())
    ctx = _ctx_tu_tieu_de(r.tieu_de, cn)
    tl = TaiLieu(tep=f"tai-lieu/{ma_cap}-A.{dinh_dang.lower()}", dinh_dang=dinh_dang, ten_de_tai=r.ten_de_tai,
                 ho_ten_sinh_vien=r.ho_ten_sinh_vien, giang_vien=ten_gv[r.ma_giang_vien],
                 nam=2000 + int(r.khoa[1:]) + 4, do_dai=do_dai, ctx=ctx)
    bs = BoSinhDoan(rng, ctx)
    n = rng.randint(*DO_DAI[do_dai])
    for muc, k in phan_bo(n).items():
        tl.doan += bs.muc(muc, k)
    tl.nguon = [None] * len(tl.doan)
    return tl


def _tieu_de_B(rng: random.Random, loai: str, r: T.DongKho, b_dt: T.DoiTuong) -> T.TieuDe:
    if loai == "DIEN_DAT_LAI":
        return T.dien_dat_lai(rng, r.tieu_de)
    if loai == "CHEP_NGUYEN_VAN":
        # đổi tên: cùng đối tượng (cùng cách gọi), khác động từ và khác đơn vị
        dv = T.sinh_don_vi(rng, r.doi_tuong.nhom, {r.tieu_de.don_vi.tat})
        for _ in range(50):
            td = T.sinh_tieu_de(rng, r.doi_tuong, dien_dat=r.tieu_de.dien_dat, don_vi=dv,
                                dong_tu_tranh={r.tieu_de.dong_tu})
            if td.kieu != "ung_dung" or td.cong_nghe != r.tieu_de.cong_nghe:
                return td
        return td
    return T.sinh_tieu_de(rng, b_dt, dien_dat=rng.randrange(2), don_vi=T.sinh_don_vi(rng, b_dt.nhom))


def _chia_do(doan: dict[str, list]) -> list:
    return [x for m in MUC for x in doan[m]]


def _tao_B(rng: random.Random, cap_loai: str, ma_cap: str, A: TaiLieu, r: T.DongKho, b_dt: T.DoiTuong,
           dinh_dang: str, do_dai: str, ten_gv: dict) -> tuple[TaiLieu, float]:
    td = _tieu_de_B(rng, cap_loai, r, b_dt)
    so_cn = 1 if do_dai == "DE_CUONG" else 2
    cn = _cong_nghe_tai_lieu(rng, b_dt, so_cn, None, set(A.ctx.cong_nghe))
    if cap_loai in ("CHEP_NGUYEN_VAN", "DIEN_DAT_LAI"):
        # tiêu đề nói về đối tượng của A, phần tự viết nói về đối tượng riêng của B (cùng cụm)
        ctx = _ctx_tu_tieu_de(td, cn, doi_tuong=b_dt, dien_dat=rng.randrange(2))
    else:
        ctx = _ctx_tu_tieu_de(td, cn)
    B = TaiLieu(tep=f"tai-lieu/{ma_cap}-B.{dinh_dang.lower()}", dinh_dang=dinh_dang, ten_de_tai=td.van_ban(),
                ho_ten_sinh_vien=T.ho_ten(rng), giang_vien=ten_gv[rng.choice(T.MA_GV_HOP_LE)],
                nam=NAM_HIEN_TAI, do_dai=do_dai, ctx=ctx)
    bs = BoSinhDoan(rng, ctx)
    n_b = rng.randint(*DO_DAI[do_dai])
    muc_tieu = phan_bo(n_b)

    if cap_loai in ("CUNG_LINH_VUC", "KHONG_LIEN_QUAN"):
        for muc, k in muc_tieu.items():
            B.doan += bs.muc(muc, k)
        B.nguon = [None] * len(B.doan)
        return B, 0.0

    # CHEP / DIEN: một dải đoạn liên tiếp của A
    n_a = len(A.doan)
    k = min(n_a - 2, max(2, round(n_b * rng.uniform(0.45, 0.55))))
    s = rng.randint(0, n_a - k)
    kieu = "NGUYEN_VAN" if cap_loai == "CHEP_NGUYEN_VAN" else "DIEN_DAT"
    lay: dict[str, list[tuple[Doan, dict]]] = {m: [] for m in MUC}
    for i in range(s, s + k):
        da = A.doan[i]
        if kieu == "NGUYEN_VAN":
            moi = Doan(da.muc, da.cau, text=da.text)
        else:
            cau = [c.dien_dat_lai() for c in da.cau]
            dau, sau = cau[0], cau[1:]
            rng.shuffle(sau)
            moi = Doan(da.muc, da.cau, text=" ".join([dau] + sau))
        lay[da.muc].append((moi, {"nguon": "A", "chi_so": i, "kieu": kieu}))
    rieng: dict[str, list[Doan]] = {}
    for muc in MUC:
        rieng[muc] = bs.muc(muc, max(0, muc_tieu[muc] - len(lay[muc])))

    def ty_le() -> float:
        c = sum(len(d.text) for m in MUC for d, _ in lay[m])
        t = c + sum(len(d.text) for m in MUC for d in rieng[m])
        return c / t

    xoay = ["phan_tich", "cai_dat", "mo_dau", "ket_luan"]
    for buoc in range(60):
        tl = ty_le()
        if tl > TY_LE_CHEP[1]:
            m = xoay[buoc % len(xoay)]
            rieng[m].append(bs.doan(m))
        elif tl < TY_LE_CHEP[0]:
            m = max((x for x in MUC if rieng[x]), key=lambda x: (len(rieng[x]), -MUC.index(x)))
            rieng[m].pop()
        else:
            break
    else:
        raise RuntimeError(f"{ma_cap}: không đạt tỷ lệ chép {ty_le():.2f}")

    for muc in MUC:
        ds_rieng = [(d, None) for d in rieng[muc]]
        vt = rng.randint(0, len(ds_rieng))
        ds = ds_rieng[:vt] + lay[muc] + ds_rieng[vt:]
        B.doan += [d for d, _ in ds]
        B.nguon += [n for _, n in ds]
    return B, ty_le()


def generate_pairs(rng: random.Random, rows: list[T.DongKho]) -> list[Cap]:
    ten_gv = _ten_gv(rng)
    ke = _ke_hoach(rng, rows)
    # đánh chỉ số trong từng loại để chọn định dạng/độ dài/tập
    chi_so_loai: dict[str, list[int]] = collections.defaultdict(list)
    for i, (lo, _, _) in enumerate(ke):
        chi_so_loai[lo].append(i)
    bao_cao: set[int] = set()
    kiem_chung: set[int] = set()
    for lo, idx in chi_so_loai.items():
        bao_cao |= set(rng.sample(idx, SO_BAO_CAO_MOI_LOAI))
        chan = [x for j, x in enumerate(idx) if j % 2 == 0]
        le = [x for j, x in enumerate(idx) if j % 2 == 1]
        kiem_chung |= {rng.choice(chan), rng.choice(le)}  # một cặp mỗi chiều định dạng

    dem_khoa: collections.Counter = collections.Counter()
    caps: list[Cap] = []
    for i, (lo, a_dt, b_dt) in enumerate(ke):
        ma = f"P{i + 1:02d}"
        j = chi_so_loai[lo].index(i)
        dd_a, dd_b = ("DOCX", "PDF") if j % 2 == 0 else ("PDF", "DOCX")
        do_dai = "BAO_CAO" if i in bao_cao else "DE_CUONG"
        r = _chon_dong_kho(rng, rows, a_dt, dem_khoa)
        A = _tao_A(rng, ma, r, dd_a, do_dai, ten_gv)
        B, tl = _tao_B(rng, lo, ma, A, r, b_dt, dd_b, do_dai, ten_gv)
        caps.append(Cap(ma, lo, "KIEM_CHUNG" if i in kiem_chung else "HIEU_CHINH", do_dai, A, B, r, tl))
    assert len(dem_khoa) == 5, f"cặp chưa phủ đủ 5 khóa: {dict(dem_khoa)}"
    return caps


# ---------------------------------------------------------------------------
# Khối trình bày (dùng chung cho DOCX và PDF)
# ---------------------------------------------------------------------------
def khoi_tai_lieu(tl: TaiLieu, rng: random.Random) -> list[tuple[str, str, str]]:
    """Danh sách khối có thứ tự: (loại, văn bản, phụ) — render.py vẽ ra DOCX/PDF."""
    km = vocab
    trang = km.TRANG[tl.do_dai]
    b: list[tuple[str, str, str]] = [
        ("bia", km.BIA["truong"], ""),
        ("bia", km.BIA["khoa"], ""),
        ("bia_trong", "", ""),
        ("bia_lon", km.BIA["loai"][tl.do_dai], ""),
        ("bia", f"Đề tài: {tl.ten_de_tai}", ""),
        ("bia_trong", "", ""),
        ("bia", km.BIA["nganh"], ""),
        ("bia", f"Sinh viên thực hiện: {tl.ho_ten_sinh_vien}", ""),
        ("bia", f"Giảng viên hướng dẫn: {tl.giang_vien}", ""),
        ("bia_trong", "", ""),
        ("bia", f"Thái Nguyên, năm {tl.nam}", ""),
        ("tieu_de_1", "LỜI CAM ĐOAN", ""),
        ("van_ban", km.LOI_CAM_DOAN.format(ten_de_tai=tl.ten_de_tai), ""),
        ("phai", f"Thái Nguyên, ngày 20 tháng 5 năm {tl.nam}", ""),
        ("phai", "Sinh viên thực hiện", ""),
        ("phai", tl.ho_ten_sinh_vien, ""),
        ("tieu_de_1", "LỜI CẢM ƠN", ""),
    ]
    b += [("van_ban", p, "") for p in km.LOI_CAM_ON]
    b.append(("tieu_de_1", "MỤC LỤC", ""))
    muc_luc = [("LỜI CAM ĐOAN", "LỜI CAM ĐOAN"), ("LỜI CẢM ƠN", "LỜI CẢM ƠN")]
    for m in MUC:
        muc_luc.append((km.CHUONG[m], km.CHUONG[m].split(".")[0]))
        for con in km.MUC_CON.get(m, ()):
            muc_luc.append(("    " + con, km.CHUONG[m].split(".")[0]))
    muc_luc.append(("TÀI LIỆU THAM KHẢO", "TÀI LIỆU THAM KHẢO"))
    b += [("muc_luc", nhan.strip(), trang[k]) for nhan, k in muc_luc]
    b.append(("tieu_de_1", "DANH MỤC HÌNH ẢNH", ""))
    for m in ("phan_tich", "cai_dat"):
        for h in km.HINH[m]:
            b.append(("muc_luc", h, trang[" ".join(h.split()[:2]).rstrip(".")]))

    theo_muc: dict[str, list[Doan]] = {m: [] for m in MUC}
    for d in tl.doan:
        theo_muc[d.muc].append(d)
    for m in MUC:
        b.append(("tieu_de_1", km.CHUONG[m], ""))
        ds = theo_muc[m]
        if m in km.MUC_CON:
            h = (len(ds) + 1) // 2
            con1, con2 = km.MUC_CON[m]
            hinh = km.HINH.get(m, [])
            b.append(("tieu_de_2", con1, ""))
            b += [("doan", d.text, "") for d in ds[:h]]
            if hinh:
                b.append(("chu_thich", hinh[0], ""))
            b.append(("tieu_de_2", con2, ""))
            b += [("doan", d.text, "") for d in ds[h:]]
            b += [("chu_thich", x, "") for x in hinh[1:]]
        else:
            b += [("doan", d.text, "") for d in ds]
    b.append(("tieu_de_1", "TÀI LIỆU THAM KHẢO", ""))
    refs = rng.sample(km.TAI_LIEU_THAM_KHAO, rng.randint(8, 12))
    b += [("tltk", f"[{i}] {x}", "") for i, x in enumerate(refs, start=1)]
    return b


# ---------------------------------------------------------------------------
# Ghi tệp + manifest
# ---------------------------------------------------------------------------
def cap_manifest(c: Cap) -> dict:
    A, B, r = c.A, c.B, c.dong_kho
    return {
        "ma_cap": c.ma_cap,
        "loai": c.loai,
        "tap": c.tap,
        "ky_vong_canh_bao": KY_VONG[c.loai],
        "do_dai": c.do_dai,
        "ty_le_sao_chep": round(c.ty_le_sao_chep, 4),
        "A": {
            "tep": A.tep, "dinh_dang": A.dinh_dang, "stt_kho": r.stt, "khoa": r.khoa,
            "ten_de_tai": r.ten_de_tai, "ma_giang_vien": r.ma_giang_vien,
            "ma_so_sinh_vien": r.ma_so_sinh_vien, "ho_ten_sinh_vien": r.ho_ten_sinh_vien,
            "cum": r.doi_tuong.cum, "ma_doi_tuong": r.doi_tuong.ma,
            "doan": A.noi_dung, "bam_noi_dung": A.bam(),
        },
        "B": {
            "tep": B.tep, "dinh_dang": B.dinh_dang, "ten_de_tai": B.ten_de_tai,
            "ho_ten_sinh_vien": B.ho_ten_sinh_vien,
            "cum": B.ctx.doi_tuong.cum, "ma_doi_tuong_noi_dung": B.ctx.doi_tuong.ma,
            "doan": [{"text": t, "nguon": n} for t, n in zip(B.noi_dung, B.nguon)],
            "bam_noi_dung": B.bam(),
        },
    }


def build_pairs(seed: int) -> list[Cap]:
    rows, _ = T.build_topics(seed)
    rng = random.Random(seed + 1)
    return generate_pairs(rng, rows)


def write_documents(out: Path, seed: int, meta: dict) -> list[Cap]:
    rows, _ = T.build_topics(seed)
    rng = random.Random(seed + 1)
    caps = generate_pairs(rng, rows)
    thu_muc = out / "tai-lieu"
    thu_muc.mkdir(parents=True, exist_ok=True)
    for old in sorted(thu_muc.glob("P*-[AB].*")):
        old.unlink()
    for c in caps:
        for tl in (c.A, c.B):
            khoi = khoi_tai_lieu(tl, rng)
            render.ve(out / tl.tep, tl.dinh_dang, khoi, tieu_de=tl.ten_de_tai)
    T.update_manifest(out / "manifest.json", {**meta, "topics": T.topics_manifest(rows),
                                              "cap": [cap_manifest(c) for c in caps]})
    dem = collections.Counter(c.loai for c in caps)
    print(f"documents: {len(caps)} cặp / {2 * len(caps)} tệp -> {thu_muc} ({dict(dem)})")
    return caps
