import importlib
import pkgutil

from .base import REGISTRY, Source, Tender  # noqa: F401


def load_sources() -> dict[str, Source]:
    """Importe tous les fichiers de ce dossier : chacun s'enregistre via @register."""
    for m in pkgutil.iter_modules(__path__):
        if m.name != "base":
            importlib.import_module(f"{__name__}.{m.name}")
    return REGISTRY
