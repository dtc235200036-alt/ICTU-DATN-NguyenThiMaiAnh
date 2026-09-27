import importlib
import pkgutil
from collections.abc import Iterator

from fastapi import APIRouter


def discover_routers() -> Iterator[APIRouter]:
    """Duyệt mọi module trong package này và yield thuộc tính `router` của nó
    (nếu có) — router mới chỉ cần một file trong routers/, không cần sửa main.py."""
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{module_name}")
        router = getattr(module, "router", None)
        if router is not None:
            yield router
