"""CLI: python -m datagen {topics|documents|all|check} [--out DIR | --data DIR] [--only topics|documents]

Một hạt giống duy nhất (SEED) được truyền vào một random.Random riêng cho mỗi giai đoạn,
nên mọi đầu ra giống nhau từng byte giữa các lần chạy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import check as C
from . import topics as T

SEED = 20261116
NGAY_SINH = "2026-09-28"
KHUON_MAU = ("[ASSUMED] khuôn mẫu chung của đồ án CNTT (bìa, lời cam đoan, lời cảm ơn, mục lục, "
             "danh mục hình, chương, tài liệu tham khảo) — thay khi có mẫu chính thức TL-04/TL-05")
META = {"ngay_sinh": NGAY_SINH, "hat_giong": SEED, "khuon_mau": KHUON_MAU}


def _documents(out: Path) -> None:
    from . import documents as D  # nạp muộn: cần python-docx/reportlab
    D.write_documents(out, SEED, META)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="datagen", description="Sinh dữ liệu thử nghiệm AI (DATA-02, DATA-03)")
    ap.add_argument("lenh", choices=["topics", "documents", "all", "check"])
    ap.add_argument("--out", type=Path, default=Path("../../seed-data"), help="thư mục ghi (topics/documents/all)")
    ap.add_argument("--data", type=Path, default=None, help="thư mục kiểm tra (check); mặc định = --out")
    ap.add_argument("--only", choices=["topics", "documents"], default=None, help="check: chỉ một phần")
    a = ap.parse_args(argv)

    if a.lenh in ("topics", "all"):
        rows, queries = T.write_topics(a.out, SEED, META)
        print(f"topics: {len(rows)} đề tài, {len(queries)} truy vấn -> {a.out}")
    if a.lenh in ("documents", "all"):
        _documents(a.out)
    if a.lenh == "check":
        data = a.data or a.out
        loi: list[str] = []
        if a.only in (None, "topics"):
            loi += C.check_topics(data, SEED, META)
        if a.only in (None, "documents"):
            loi += C.check_documents(data, SEED, META)
        if loi:
            print(f"\nFAIL: {len(loi)} vi phạm", file=sys.stderr)
            for x in loi:
                print(f"  - {x}", file=sys.stderr)
            return 1
        print("\nTất cả kiểm tra đạt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
