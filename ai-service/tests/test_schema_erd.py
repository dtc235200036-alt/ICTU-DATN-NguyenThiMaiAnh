import re

from sqlalchemy import create_engine, inspect

from conftest import SERVICE_DIR

ERD = SERVICE_DIR.parent / "docs" / "chuong-3-thiet-ke" / "csdl" / "erd-thesis-ai.puml"
_ENTITY_RE = re.compile(r'entity\s+"(\w+)"[^{]*\{(.*?)\n\}', re.S)
_ATTR_RE = re.compile(r"^\s*\*?(\w+)\s*:", re.M)


def test_migrated_columns_match_erd(db_path):
    erd = {name: set(_ATTR_RE.findall(body)) for name, body in _ENTITY_RE.findall(ERD.read_text(encoding="utf-8"))}
    insp = inspect(create_engine(f"sqlite:///{db_path}"))
    for table in ("chunk", "embedding", "index_metadata"):
        columns = {c["name"] for c in insp.get_columns(table)}
        assert columns == erd[table], table
