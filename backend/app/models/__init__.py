import importlib
import pkgutil

from app.models.base import Base

__all__ = ["Base"]

for _, _module_name, _ in pkgutil.iter_modules(__path__):
    if _module_name in ("base",):
        continue
    importlib.import_module(f"{__name__}.{_module_name}")
