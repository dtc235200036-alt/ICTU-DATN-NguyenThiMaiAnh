#!/usr/bin/env python3
"""tools/check-docs.py - documentation consistency checker (stdlib only).

Subcommands (Task 1 of 01-02-PLAN.md): render, links, pi-tags, privacy,
class-erd, trace. (Task 2 adds: req-coverage, truy-vet, bpmn, mockup, all.)

Every subcommand: exit 0 on pass, exit 1 with one `path:line: message` per
failure (line 0 when no specific line applies), exit 2 on usage error.
Every PATH argument may be a file or a directory (scanned recursively); a
nonexistent PATH is reported as a failure, not a crash.
"""
import argparse
import base64
import os
import re
import struct
import sys
import zlib
from urllib.parse import unquote
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PHONE_RE = re.compile(r"\b0[0-9]{3}[ .]?[0-9]{3}[ .]?[0-9]{3}\b")

FAILURES = []


def fail(path, line, message):
    FAILURES.append((path, line, message))


def rel(path):
    ap = os.path.abspath(path)
    if ap.startswith(REPO_ROOT + os.sep):
        return os.path.relpath(ap, REPO_ROOT)
    return path


def iter_files(paths, exts=None, default_dirs=None):
    """Yield existing files under the given PATH args (file or dir,
    recursive). Nonexistent paths are reported via `fail` and skipped."""
    targets = list(paths) if paths else (list(default_dirs) if default_dirs else [])
    for p in targets:
        if os.path.isfile(p):
            yield p
        elif os.path.isdir(p):
            for root, _dirs, files in sorted(os.walk(p)):
                for f in sorted(files):
                    full = os.path.join(root, f)
                    if exts is None or os.path.splitext(f)[1] in exts:
                        yield full
        else:
            fail(rel(p), 0, f"duong dan khong ton tai: {p}")


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def newer(a, b):
    """True if file a's mtime is >= file b's mtime (a not older than b)."""
    try:
        return os.path.getmtime(a) >= os.path.getmtime(b)
    except OSError:
        return False


# ---------------------------------------------------------------------------
# draw.io content decoding (handles compressed payloads: base64 -> raw
# inflate -> URL-decode) wherever .drawio content is parsed.
# ---------------------------------------------------------------------------
def drawio_diagram_xml(diagram_el):
    """Return the inner mxGraphModel Element for a <diagram>, decompressing
    the base64/deflate/urlencode payload if the content is compressed
    (text content present instead of an <mxGraphModel> child)."""
    child = diagram_el.find("mxGraphModel")
    if child is not None:
        return child
    text = (diagram_el.text or "").strip()
    if not text:
        return None
    try:
        raw = base64.b64decode(text)
        inflated = zlib.decompress(raw, -zlib.MAX_WBITS)
        xml_text = unquote(inflated.decode("utf-8"))
        return ET.fromstring(xml_text)
    except Exception:
        return None


def load_drawio_pages(path):
    """Return list of (page_name, mxGraphModel Element or None)."""
    tree = ET.parse(path)
    root = tree.getroot()
    pages = []
    for d in root.findall(".//diagram"):
        name = d.get("name") or d.get("id") or ""
        pages.append((name, drawio_diagram_xml(d)))
    return pages


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------
def cmd_render(args):
    for puml in iter_files(args.paths, exts={".puml"}, default_dirs=["docs"]):
        png = os.path.splitext(puml)[0] + ".png"
        svg = os.path.splitext(puml)[0] + ".svg"
        if not os.path.isfile(png) or not newer(png, puml):
            fail(rel(puml), 0, f"thieu hoac cu hon PNG: {rel(png)}")
        if not os.path.isfile(svg) or not newer(svg, puml):
            fail(rel(puml), 0, f"thieu hoac cu hon SVG: {rel(svg)}")

    for drawio in iter_files(args.paths, exts={".drawio"}, default_dirs=["docs"]):
        try:
            pages = load_drawio_pages(drawio)
        except ET.ParseError as exc:
            fail(rel(drawio), 0, f"khong parse duoc XML: {exc}")
            continue
        base = os.path.splitext(drawio)[0]
        for name, _xml in pages:
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            png = f"{base}-{slug}.png"
            if not os.path.isfile(png) or not newer(png, drawio):
                fail(rel(drawio), 0, f"trang '{name}': thieu hoac cu hon PNG: {rel(png)}")

    for html in iter_files(args.paths, exts={".html"}, default_dirs=["docs"]):
        if os.path.basename(os.path.dirname(html)) != "mockup":
            continue
        base = os.path.splitext(os.path.basename(html))[0]
        if not re.fullmatch(r"mh-\d\d", base):
            continue
        png = os.path.join(os.path.dirname(html), base + ".png")
        css = os.path.join(os.path.dirname(html), "antd-admin.css")
        if not os.path.isfile(png) or os.path.getsize(png) == 0:
            fail(rel(html), 0, f"thieu hoac rong PNG: {rel(png)}")
            continue
        if not newer(png, html):
            fail(rel(html), 0, f"PNG cu hon HTML: {rel(png)}")
        if os.path.isfile(css) and not newer(png, css):
            fail(rel(html), 0, f"PNG cu hon stylesheet dung chung: {rel(css)}")


# ---------------------------------------------------------------------------
# links
# ---------------------------------------------------------------------------
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def cmd_links(args):
    for md in iter_files(args.paths, exts={".md"}, default_dirs=["docs"]):
        text = read_text(md)
        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in LINK_RE.finditer(line):
                target = m.group(1)
                if target.startswith("#"):
                    continue
                if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target) or target.startswith("mailto:"):
                    continue
                path_part = target.split("#", 1)[0]
                if not path_part:
                    continue
                resolved = os.path.normpath(os.path.join(os.path.dirname(md), path_part))
                if not os.path.isfile(resolved) and not os.path.isdir(resolved):
                    fail(rel(md), lineno, f"lien ket hong: {target}")


# ---------------------------------------------------------------------------
# pi-tags
# ---------------------------------------------------------------------------
def cmd_pi_tags(args):
    default_dirs = ["docs/chuong-2-khao-sat-phan-tich", "docs/chuong-3-thiet-ke"]
    for md in iter_files(args.paths, exts={".md"}, default_dirs=default_dirs):
        text = read_text(md)
        if "Mã PI:" not in text:
            fail(rel(md), 0, "thieu dong 'Mã PI:'")


# ---------------------------------------------------------------------------
# privacy
# ---------------------------------------------------------------------------
TEXT_EXTS = {".md", ".html", ".css", ".puml", ".drawio", ".csv", ".txt", ".py", ".sh"}


def cmd_privacy(args):
    default_dirs = ["docs", "tai-lieu-goc"]
    for f in iter_files(args.paths, exts=None, default_dirs=default_dirs):
        ext = os.path.splitext(f)[1]
        if ext not in TEXT_EXTS:
            continue
        try:
            text = read_text(f)
        except Exception:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            m = PHONE_RE.search(line)
            if m:
                fail(rel(f), lineno, f"co the la so dien thoai that: '{m.group(0)}'")


# ---------------------------------------------------------------------------
# class-erd
# ---------------------------------------------------------------------------
CLASS_RE = re.compile(r'class\s+(?:"[^"]*"\s+as\s+)?(\w+)')
ENTITY_RE = re.compile(r'entity\s+(?:"[^"]*"\s+as\s+)?(\w+)')


def cmd_class_erd(args):
    class_path = "docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml"
    erd_path = "docs/chuong-3-thiet-ke/csdl/erd.puml"
    csdl_md = "docs/chuong-3-thiet-ke/02-thiet-ke-csdl.md"

    if not os.path.isfile(class_path):
        fail(rel(class_path), 0, "khong tim thay file lop thuc the")
        return
    if not os.path.isfile(erd_path):
        fail(rel(erd_path), 0, "khong tim thay file ERD")
        return
    if not os.path.isfile(csdl_md):
        fail(rel(csdl_md), 0, "khong tim thay file thiet ke CSDL")
        return

    classes = set(CLASS_RE.findall(read_text(class_path)))
    entities = set(ENTITY_RE.findall(read_text(erd_path)))
    md_text = read_text(csdl_md)

    header = "| Lớp thực thể | Bảng | Ghi chú |"
    if header not in md_text:
        fail(rel(csdl_md), 0, f"thieu dong header bang anh xa dung: {header}")
        return

    rows = []
    in_table = False
    for lineno, line in enumerate(md_text.splitlines(), start=1):
        if line.strip() == header:
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            if set(line.replace("|", "").strip()) <= {"-", " "}:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3:
                rows.append((lineno, cells[0], cells[1], cells[2]))

    mapped_classes = set()
    mapped_entities = set()
    for lineno, cls, table, note in rows:
        mapped_classes.add(cls)
        mapped_entities.add(table)
        if cls and cls not in classes:
            fail(rel(csdl_md), lineno, f"lop '{cls}' khong ton tai trong lop-thuc-the.puml")
        if table and table not in entities:
            fail(rel(csdl_md), lineno, f"bang '{table}' khong ton tai trong erd.puml")

    for cls in sorted(classes):
        if cls not in mapped_classes:
            fail(rel(class_path), 0, f"lop '{cls}' khong co dong anh xa trong {rel(csdl_md)}")

    for ent in sorted(entities):
        if ent in mapped_entities:
            continue
        note = ""
        for _lineno, _cls, table, n in rows:
            if table == ent:
                note = n
                break
        if "liên kết" not in note and "kỹ thuật" not in note:
            fail(rel(erd_path), 0,
                 f"bang '{ent}' chua duoc anh xa va Ghi chu khong giai thich ('liên kết'/'kỹ thuật')")


# ---------------------------------------------------------------------------
# trace
# ---------------------------------------------------------------------------
MATRIX_HEADER = "| FR | UC | Bước BPMN (TO-BE) | Lớp | Bảng | Màn hình |"


def _find_files(pattern_dir, name_substr):
    out = []
    for root, _dirs, files in os.walk(pattern_dir):
        for f in files:
            if name_substr in f and f.endswith(".md"):
                out.append(os.path.join(root, f))
    return out


def _parse_matrix(truy_vet_path):
    text = read_text(truy_vet_path)
    lines = text.splitlines()
    rows = {}
    in_table = False
    for line in lines:
        if line.strip() == MATRIX_HEADER:
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith("|"):
                if rows:
                    break
                continue
            if set(line.replace("|", "").strip()) <= {"-", " "}:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 6 and cells[0]:
                rows[cells[0]] = {
                    "UC": cells[1],
                    "BPMN": cells[2],
                    "Lớp": cells[3],
                    "Bảng": cells[4],
                    "Màn hình": cells[5],
                }
    return rows


def _check_fr_row(fr_id, row, truy_vet_path):
    fr_md = "docs/chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md"
    if not os.path.isfile(fr_md) or re.search(rf"\|\s*{re.escape(fr_id)}\s*\|", read_text(fr_md)) is None:
        fail(rel(fr_md), 0, f"khong tim thay dong '{fr_id}' trong bang yeu cau chuc nang")

    uc_cell = row.get("UC", "")
    uc_ids = [u.strip() for u in re.split(r"[,/]", uc_cell) if u.strip() and u.strip() != "—"]
    uc_dir = "docs/chuong-2-khao-sat-phan-tich"
    uc_files = _find_files(uc_dir, "dac-ta-uc") if os.path.isdir(uc_dir) else []
    for uc_id in uc_ids:
        found = False
        for uf in uc_files:
            text = read_text(uf)
            if re.search(rf"^####\s*{re.escape(uc_id)}\s", text, re.MULTILINE) and fr_id in text:
                found = True
                break
        if not found:
            fail(rel(truy_vet_path), 0,
                 f"{fr_id}: khong tim thay heading '#### {uc_id} ' co nhac den {fr_id} trong dac ta UC")

    bpmn_cell = row.get("BPMN", "")
    if bpmn_cell and bpmn_cell != "—":
        qtnv = "docs/chuong-2-khao-sat-phan-tich/02-quy-trinh-nghiep-vu.md"
        for step in [s.strip() for s in re.split(r"[,/]", bpmn_cell) if s.strip()]:
            if not os.path.isfile(qtnv) or step not in read_text(qtnv):
                fail(rel(truy_vet_path), 0, f"{fr_id}: buoc BPMN '{step}' khong xuat hien trong {rel(qtnv)}")

    class_cell = row.get("Lớp", "")
    class_path = "docs/chuong-3-thiet-ke/so-do-lop/lop-thuc-the.puml"
    if class_cell and class_cell != "—":
        classes = set(CLASS_RE.findall(read_text(class_path))) if os.path.isfile(class_path) else set()
        for c in [c.strip() for c in re.split(r"[,/]", class_cell) if c.strip()]:
            if c not in classes:
                fail(rel(truy_vet_path), 0, f"{fr_id}: lop '{c}' khong ton tai trong {rel(class_path)}")

    table_cell = row.get("Bảng", "")
    erd_path = "docs/chuong-3-thiet-ke/csdl/erd.puml"
    if table_cell and table_cell != "—":
        entities = set(ENTITY_RE.findall(read_text(erd_path))) if os.path.isfile(erd_path) else set()
        for t in [t.strip() for t in re.split(r"[,/]", table_cell) if t.strip()]:
            if t not in entities:
                fail(rel(truy_vet_path), 0, f"{fr_id}: bang '{t}' khong ton tai trong {rel(erd_path)}")

    mh_cell = row.get("Màn hình", "")
    giao_dien_md = "docs/chuong-3-thiet-ke/04-thiet-ke-giao-dien.md"
    if mh_cell and mh_cell != "—":
        gd_text = read_text(giao_dien_md) if os.path.isfile(giao_dien_md) else ""
        for mh_id in [m.strip() for m in re.split(r"[,/]", mh_cell) if m.strip()]:
            mh_lower = mh_id.lower()
            row_re = re.compile(
                rf"\|\s*{re.escape(mh_id)}\s*\|.*\|.*\|.*\|\s*\[[^\]]*\]\(([^)]*{re.escape(mh_lower)}\.html)\)\s*\|"
                rf"\s*\[[^\]]*\]\(([^)]*{re.escape(mh_lower)}\.png)\)\s*\|\s*Đã dựng\s*\|"
            )
            m = row_re.search(gd_text)
            if not m:
                fail(rel(giao_dien_md), 0,
                     f"{fr_id}: mh '{mh_id}' khong co dong 'Đã dựng' voi lien ket html+png trong bang muc man hinh")
                continue
            html_link = os.path.normpath(os.path.join(os.path.dirname(giao_dien_md), m.group(1)))
            png_link = os.path.normpath(os.path.join(os.path.dirname(giao_dien_md), m.group(2)))
            if not os.path.isfile(html_link) or os.path.getsize(html_link) == 0:
                fail(rel(giao_dien_md), 0, f"{fr_id}: file html '{m.group(1)}' khong ton tai hoac rong")
            if not os.path.isfile(png_link) or os.path.getsize(png_link) == 0:
                fail(rel(giao_dien_md), 0, f"{fr_id}: file png '{m.group(2)}' khong ton tai hoac rong")


def cmd_trace(args):
    truy_vet_path = "docs/truy-vet.md"
    if not os.path.isfile(truy_vet_path):
        fail(rel(truy_vet_path), 0, "khong tim thay docs/truy-vet.md")
        return
    rows = _parse_matrix(truy_vet_path)
    if not rows:
        fail(rel(truy_vet_path), 0, f"khong tim thay bang voi header: {MATRIX_HEADER}")
        return

    if args.all:
        fr_md = "docs/chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md"
        fr_ids = []
        if os.path.isfile(fr_md):
            fr_ids = re.findall(r"\|\s*(FR-[A-Z]+-\d+)\s*\|", read_text(fr_md))
        for fr_id in fr_ids:
            if fr_id not in rows:
                fail(rel(truy_vet_path), 0, f"{fr_id}: khong co dong trong ma tran truy vet")
            else:
                _check_fr_row(fr_id, rows[fr_id], truy_vet_path)
    else:
        for fr_id in args.fr_ids:
            if fr_id not in rows:
                fail(rel(truy_vet_path), 0, f"{fr_id}: khong co dong trong ma tran truy vet")
                continue
            _check_fr_row(fr_id, rows[fr_id], truy_vet_path)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(prog="check-docs.py", description="Kiem tra tinh nhat quan cua tai lieu")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("render", help="Kiem tra moi so do/mockup da duoc render")
    sp.add_argument("paths", nargs="*")
    sp.set_defaults(func=cmd_render)

    sp = sub.add_parser("links", help="Kiem tra lien ket Markdown tuong doi")
    sp.add_argument("paths", nargs="*")
    sp.set_defaults(func=cmd_links)

    sp = sub.add_parser("pi-tags", help="Kiem tra moi file .md co dong Mã PI:")
    sp.add_argument("paths", nargs="*")
    sp.set_defaults(func=cmd_pi_tags)

    sp = sub.add_parser("privacy", help="Kiem tra khong co so dien thoai that")
    sp.add_argument("paths", nargs="*")
    sp.set_defaults(func=cmd_privacy)

    sp = sub.add_parser("class-erd", help="Kiem tra khop lop thuc the <-> bang CSDL")
    sp.set_defaults(func=cmd_class_erd)

    sp = sub.add_parser("trace", help="Kiem tra truy vet FR -> UC -> BPMN -> lop -> bang -> man hinh")
    sp.add_argument("fr_ids", nargs="*")
    sp.add_argument("--all", action="store_true")
    sp.set_defaults(func=cmd_trace)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

    if FAILURES:
        for path, line, message in FAILURES:
            print(f"{path}:{line}: {message}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
