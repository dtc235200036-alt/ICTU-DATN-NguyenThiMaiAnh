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
        in_fence = False
        for lineno, line in enumerate(text.splitlines(), start=1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
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
# req-coverage (Task 2)
# ---------------------------------------------------------------------------
def cmd_req_coverage(args):
    fr_md = "docs/chuong-2-khao-sat-phan-tich/03-yeu-cau-chuc-nang.md"
    nfr_md = "docs/chuong-2-khao-sat-phan-tich/04-yeu-cau-phi-chuc-nang.md"
    fr_text = read_text(fr_md) if os.path.isfile(fr_md) else ""
    nfr_text = read_text(nfr_md) if os.path.isfile(nfr_md) else ""
    for req_id in args.ids:
        if req_id not in fr_text and req_id not in nfr_text:
            fail(rel(fr_md), 0,
                 f"{req_id}: khong xuat hien trong 03-yeu-cau-chuc-nang.md hoac 04-yeu-cau-phi-chuc-nang.md")


# ---------------------------------------------------------------------------
# truy-vet (Task 2)
# ---------------------------------------------------------------------------
PI_CODES = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "3.1", "3.2", "3.3", "3.4", "4.1", "4.2"]
PHASE1_PI_CODES = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3"]
REQ_ANLS_DSGN_CODES = ["ANLS-01", "ANLS-02", "ANLS-03", "ANLS-04", "ANLS-05",
                       "DSGN-01", "DSGN-02", "DSGN-03", "DSGN-04"]
PI_TABLE_HEADER = "| Mã PI | Nội dung PI | Yêu cầu | Mục tài liệu (minh chứng) | Trạng thái |"
REQ_TABLE_HEADER = "| Yêu cầu | Mô tả | Tài liệu | Plan |"


def _parse_pipe_table(lines, header):
    rows = {}
    in_table = False
    for lineno, line in enumerate(lines, start=1):
        if line.strip() == header:
            in_table = True
            continue
        if in_table:
            s = line.strip()
            if not s.startswith("|"):
                if rows:
                    break
                continue
            if set(s.replace("|", "").strip()) <= {"-", " "}:
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if cells and cells[0]:
                rows[cells[0]] = (lineno, cells)
    return rows


def cmd_truy_vet(args):
    path = "docs/truy-vet.md"
    if not os.path.isfile(path):
        fail(rel(path), 0, "khong tim thay docs/truy-vet.md")
        return
    lines = read_text(path).splitlines()

    pi_rows = _parse_pipe_table(lines, PI_TABLE_HEADER)
    for code in PI_CODES:
        if code not in pi_rows:
            fail(rel(path), 0, f"thieu dong PI {code} trong muc 1 (Truy vết theo tiêu chí PI)")

    req_rows = _parse_pipe_table(lines, REQ_TABLE_HEADER)
    for code in REQ_ANLS_DSGN_CODES:
        if code not in req_rows:
            fail(rel(path), 0, f"thieu dong yeu cau {code} trong muc 2 (Truy vết theo yêu cầu)")

    for lineno, line in enumerate(lines, start=1):
        for m in LINK_RE.finditer(line):
            target = m.group(1)
            if target.startswith("#"):
                continue
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target) or target.startswith("mailto:"):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), path_part))
            if not os.path.isfile(resolved) and not os.path.isdir(resolved):
                fail(rel(path), lineno, f"lien ket hong: {target}")

    if args.complete:
        for code in PHASE1_PI_CODES:
            if code not in pi_rows:
                continue
            lineno, cells = pi_rows[code]
            status = cells[4] if len(cells) > 4 else ""
            mucdoc = cells[3] if len(cells) > 3 else ""
            if status != "Đạt":
                fail(rel(path), lineno, f"PI {code}: trang thai phai la 'Đạt' khi --complete, hien tai '{status}'")
            if not LINK_RE.findall(mucdoc):
                fail(rel(path), lineno, f"PI {code}: muc tai lieu chua lien ket file nao")
        for code in REQ_ANLS_DSGN_CODES:
            if code not in req_rows:
                continue
            lineno, cells = req_rows[code]
            tailieu = cells[2] if len(cells) > 2 else ""
            if not tailieu.strip():
                fail(rel(path), lineno, f"{code}: cot Tai lieu dang trong")


# ---------------------------------------------------------------------------
# bpmn (Task 2)
# ---------------------------------------------------------------------------
def _default_drawio_files():
    found = []
    if os.path.isdir("docs"):
        for root, _dirs, files in os.walk("docs"):
            if os.path.basename(root) == "bpmn":
                for f in files:
                    if f.endswith(".drawio"):
                        found.append(os.path.join(root, f))
    return sorted(found)


def cmd_bpmn(args):
    files = args.files if args.files else _default_drawio_files()
    if not files:
        fail(rel("docs"), 0, "khong tim thay file .drawio nao trong docs/**/bpmn/")
        return
    for path in files:
        if not os.path.isfile(path):
            fail(rel(path), 0, "khong tim thay file")
            continue
        try:
            pages = load_drawio_pages(path)
        except ET.ParseError as exc:
            fail(rel(path), 0, f"khong parse duoc XML: {exc}")
            continue
        names = {name for name, _xml in pages}
        for required in ("AS-IS", "TO-BE"):
            if required not in names:
                fail(rel(path), 0, f"thieu trang '{required}'")
        for name, xml_root in pages:
            if xml_root is None:
                fail(rel(path), 0, f"trang '{name}': khong doc duoc noi dung (co the do nen chua ho tro)")
                continue
            lane_labels = []
            has_start = False
            has_end = False
            for cell in xml_root.iter("mxCell"):
                style = cell.get("style") or ""
                value = cell.get("value") or ""
                if "swimlane" in style and cell.get("vertex") == "1":
                    lane_labels.append(value.strip())
                if "mxgraph.bpmn.event" in style:
                    if "outline=standard" in style:
                        has_start = True
                    if "outline=end" in style:
                        has_end = True
            for required_lane in ("Sinh viên", "Giảng viên", "Bộ môn"):
                if not any(lbl == required_lane for lbl in lane_labels):
                    fail(rel(path), 0, f"trang '{name}': thieu lane '{required_lane}'")
            if not has_start:
                fail(rel(path), 0, f"trang '{name}': khong co start event")
            if not has_end:
                fail(rel(path), 0, f"trang '{name}': khong co end event")
            if name == "TO-BE" and not any(lbl.startswith("Hệ thống") for lbl in lane_labels):
                fail(rel(path), 0, f"trang '{name}': thieu lane bat dau bang 'Hệ thống'")


# ---------------------------------------------------------------------------
# mockup (Task 2)
# ---------------------------------------------------------------------------
INVENTORY_HEADER = "| Mã MH | Tên màn hình | Vai trò | UC | Tệp nguồn | Ảnh | Trạng thái |"


def _parse_inventory(path):
    lines = read_text(path).splitlines()
    rows = {}
    in_table = False
    for line in lines:
        if line.strip() == INVENTORY_HEADER:
            in_table = True
            continue
        if in_table:
            s = line.strip()
            if not s.startswith("|"):
                if rows:
                    break
                continue
            if set(s.replace("|", "").strip()) <= {"-", " "}:
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 7 and cells[0]:
                rows[cells[0]] = cells
    return rows


def cmd_mockup(args):
    giao_dien_md = "docs/chuong-3-thiet-ke/04-thiet-ke-giao-dien.md"
    if not os.path.isfile(giao_dien_md):
        fail(rel(giao_dien_md), 0, "khong tim thay 04-thiet-ke-giao-dien.md")
        return
    rows = _parse_inventory(giao_dien_md)
    gd_text = read_text(giao_dien_md)

    if args.all:
        ids = [f"MH-{i:02d}" for i in range(1, 15)]
    elif args.mh_ids:
        ids = list(args.mh_ids)
    else:
        ids = [mh for mh, cells in rows.items() if len(cells) > 6 and cells[6] == "Đã dựng"]

    for mh_id in ids:
        cells = rows.get(mh_id)
        if not cells:
            fail(rel(giao_dien_md), 0, f"{mh_id}: khong co dong trong danh muc man hinh")
            continue
        status = cells[6] if len(cells) > 6 else ""
        if status != "Đã dựng":
            fail(rel(giao_dien_md), 0, f"{mh_id}: trang thai phai la 'Đã dựng', hien tai '{status}'")
            continue

        html_m = re.search(r"\[[^\]]*\]\(([^)]*\.html)\)", cells[4]) if len(cells) > 4 else None
        png_m = re.search(r"\[[^\]]*\]\(([^)]*\.png)\)", cells[5]) if len(cells) > 5 else None
        if not html_m or not png_m:
            fail(rel(giao_dien_md), 0, f"{mh_id}: dong khong lien ket ca html va png")
            continue

        html_path = os.path.normpath(os.path.join(os.path.dirname(giao_dien_md), html_m.group(1)))
        png_path = os.path.normpath(os.path.join(os.path.dirname(giao_dien_md), png_m.group(1)))

        if not os.path.isfile(html_path):
            fail(rel(giao_dien_md), 0, f"{mh_id}: khong tim thay {html_m.group(1)}")
            continue
        html_text = read_text(html_path)

        title_m = re.search(r"<title>([^<]*)</title>", html_text)
        if not title_m or not title_m.group(1).strip().upper().startswith(mh_id.upper()):
            fail(rel(html_path), 0, f"title phai bat dau bang {mh_id}")
        if "antd-admin.css" not in html_text:
            fail(rel(html_path), 0, "khong lien ket antd-admin.css")

        size_m = re.search(r'name="mockup-size"[^>]*content="(\d+)x(\d+)"', html_text)
        if not size_m:
            fail(rel(html_path), 0, "thieu meta mockup-size")
        else:
            mw, mh_height = int(size_m.group(1)), int(size_m.group(2))
            if mw != 1440:
                fail(rel(html_path), 0, f"mockup-size width phai la 1440, hien tai {mw}")
            if mh_height < 900:
                fail(rel(html_path), 0, f"mockup-size height phai >= 900, hien tai {mh_height}")

        if re.search(r"<script", html_text, re.IGNORECASE):
            fail(rel(html_path), 0, "co <script>, khong duoc phep")
        if "@import" in html_text:
            fail(rel(html_path), 0, "co CSS import rule, khong duoc phep")
        if re.search(r'(src|href)\s*=\s*"https?:', html_text, re.IGNORECASE) or \
           re.search(r'url\(\s*"?https?:', html_text, re.IGNORECASE):
            fail(rel(html_path), 0, "co tai nguyen tu xa (http/https), khong duoc phep")

        if not os.path.isfile(png_path) or os.path.getsize(png_path) == 0:
            fail(rel(giao_dien_md), 0, f"{mh_id}: khong tim thay hoac rong {png_m.group(1)}")
        else:
            with open(png_path, "rb") as fh:
                header = fh.read(24)
            if header[1:4] != b"PNG":
                fail(rel(png_path), 0, "khong phai file PNG hop le")
            else:
                png_w, png_h = struct.unpack(">II", header[16:24])
                if png_w != 1440:
                    fail(rel(png_path), 0, f"PNG width phai la 1440, hien tai {png_w}")
                if size_m and png_h != int(size_m.group(2)):
                    fail(rel(png_path), 0,
                         f"PNG height ({png_h}) khong khop mockup-size height ({size_m.group(2)})")

        heading_re = re.compile(rf"^###\s*3\.4\.\d+\.\s*{re.escape(mh_id)}\s*[–-]", re.MULTILINE)
        if not heading_re.search(gd_text):
            fail(rel(giao_dien_md), 0, f"{mh_id}: khong co heading '### 3.4.<n>. {mh_id} - ...'")
        img_re = re.compile(rf"!\[[^\]]*\]\({re.escape(png_m.group(1))}\)")
        if not img_re.search(gd_text):
            fail(rel(giao_dien_md), 0, f"{mh_id}: khong nhung anh {png_m.group(1)} bang cu phap Markdown")


# ---------------------------------------------------------------------------
# all (Task 2)
# ---------------------------------------------------------------------------
def cmd_all(args):
    N = argparse.Namespace
    cmd_render(N(paths=[]))
    cmd_links(N(paths=[]))
    cmd_pi_tags(N(paths=[]))
    cmd_privacy(N(paths=[]))
    cmd_class_erd(N())
    cmd_bpmn(N(files=[]))
    cmd_mockup(N(all=True, mh_ids=[]))
    cmd_truy_vet(N(complete=True))
    cmd_trace(N(fr_ids=[], all=True))


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

    sp = sub.add_parser("req-coverage", help="Kiem tra ID yeu cau xuat hien trong bang yeu cau chuc nang/phi chuc nang")
    sp.add_argument("ids", nargs="*")
    sp.set_defaults(func=cmd_req_coverage)

    sp = sub.add_parser("truy-vet", help="Kiem tra docs/truy-vet.md day du PI va yeu cau, lien ket hop le")
    sp.add_argument("--complete", action="store_true")
    sp.set_defaults(func=cmd_truy_vet)

    sp = sub.add_parser("bpmn", help="Kiem tra file .drawio co trang AS-IS/TO-BE, du lane, start/end event")
    sp.add_argument("files", nargs="*")
    sp.set_defaults(func=cmd_bpmn)

    sp = sub.add_parser("mockup", help="Kiem tra man hinh mockup: trang thai, lien ket, meta, PNG, muc luc")
    sp.add_argument("mh_ids", nargs="*")
    sp.add_argument("--all", action="store_true")
    sp.set_defaults(func=cmd_mockup)

    sp = sub.add_parser("all", help="Chay toan bo: render, links, pi-tags, privacy, class-erd, bpmn, mockup, truy-vet, trace")
    sp.set_defaults(func=cmd_all)

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
