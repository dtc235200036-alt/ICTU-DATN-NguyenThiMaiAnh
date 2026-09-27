#!/usr/bin/env python3
"""Kiểm tra tên cột giữa docs/chuong-3-thiet-ke/csdl/erd.puml và schema thesis_core thật.

Dùng: python3 tools/check-erd-db.py
Thoát 0 nếu khớp, thoát 1 và in mỗi dòng "table.column: message" nếu có sai lệch.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ERD_PATH = REPO_ROOT / "docs" / "chuong-3-thiet-ke" / "csdl" / "erd.puml"
SQL_SCRIPT = REPO_ROOT / "deploy" / "sql.sh"

ENTITY_RE = re.compile(r'^entity\s+"([a-z_0-9]+)"\s+as\s+[a-z_0-9]+\s*\{')
COLUMN_RE = re.compile(r"^\*?([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*\S")


def parse_erd(text: str) -> dict[str, set[str]]:
    entities: dict[str, set[str]] = {}
    current: str | None = None
    in_note = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        entity_match = ENTITY_RE.match(line)
        if entity_match:
            current = entity_match.group(1)
            entities[current] = set()
            in_note = False
            continue
        if current is None:
            continue
        if line == "}":
            current = None
            continue
        if in_note:
            if ".." in line:
                in_note = False
            continue
        if line.startswith(".."):
            if line.count("..") >= 2:
                # single-line ..note.. (opens and closes on the same line)
                continue
            in_note = True
            continue
        if line == "--":
            continue
        col_match = COLUMN_RE.match(line)
        if col_match:
            entities[current].add(col_match.group(1))
    return entities


def fetch_db_columns() -> dict[str, set[str]]:
    query = (
        "SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA='thesis_core' AND TABLE_NAME<>'alembic_version'"
    )
    result = subprocess.run(
        ["bash", str(SQL_SCRIPT), query],
        capture_output=True,
        text=True,
        check=True,
    )
    db_tables: dict[str, set[str]] = {}
    for line in result.stdout.splitlines():
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        table, column = parts
        db_tables.setdefault(table, set()).add(column)
    return db_tables


def main() -> int:
    erd_entities = parse_erd(ERD_PATH.read_text(encoding="utf-8"))
    db_tables = fetch_db_columns()

    errors: list[str] = []

    for table, columns in db_tables.items():
        if table not in erd_entities:
            errors.append(f"{table}: bảng có trong DB nhưng không phải entity trong erd.puml")
            continue
        missing_in_erd = columns - erd_entities[table]
        for col in sorted(missing_in_erd):
            errors.append(f"{table}.{col}: cột có trong DB nhưng thiếu trong erd.puml")

    for entity, columns in erd_entities.items():
        if entity not in db_tables:
            continue
        missing_in_db = columns - db_tables[entity]
        for col in sorted(missing_in_db):
            errors.append(f"{entity}.{col}: cột có trong erd.puml nhưng thiếu trong bảng DB")

    if errors:
        for err in errors:
            print(err)
        return 1

    print("OK: schema thesis_core khớp erd.puml cho các bảng đã tạo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
