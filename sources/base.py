from __future__ import annotations
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from config import KEYWORDS

REGISTRY: dict[str, "Source"] = {}


@dataclass
class Tender:
    source: str
    title: str
    url: str
    organisation: str = ""
    published: date | None = None
    deadline: date | None = None
    description: str = ""
    themes: str = ""


def sample(keywords: list[str], n: int) -> list[str]:
    """Choisit n mots-clés répartis sur toute la liste (donc sur tous les thèmes)."""
    if len(keywords) <= n:
        return keywords
    return [keywords[int(i * len(keywords) / n)] for i in range(n)]


def register(cls):
    """Décorateur : enregistre automatiquement la source dans l'appli."""
    if getattr(cls, "enabled", True):
        REGISTRY[cls.name] = cls()
    return cls


def classify(text: str, themes: list[str]) -> list[str]:
    found = []
    for theme in themes:
        for kw in KEYWORDS[theme]:
            # mots courts (SOC, LLM, NLP) : correspondance exacte, sinon sous-chaîne
            short = len(kw) <= 4
            pat = rf"\b{re.escape(kw)}\b" if short else re.escape(kw)
            flags = 0 if (short and kw.isupper()) else re.I   # IA, SOC, SSI… : majuscules exigées
            if re.search(pat, text, flags):
                found.append(theme)
                break
    return found


class Source(ABC):
    name: str = "À définir"
    # True si la source filtre déjà par mots-clés côté serveur
    server_side_filter: bool = False
    scope: str = "international"   # "international" ou "bretagne" (sert au menu de l'appli)
    stats: dict = {}
    enabled: bool = True   # mettre False pour désactiver une source sans la supprimer

    @abstractmethod
    def fetch(self, keywords: list[str]) -> list[Tender]:
        """Retourne les offres brutes (la source fait son appel HTTP + parsing)."""

    def search(self, themes: list[str]) -> list[Tender]:
        keywords = [kw for t in themes for kw in KEYWORDS[t]]
        today = date.today()
        raw = self.fetch(keywords)
        out, n_open = [], 0
        for t in raw:
            if t.deadline and t.deadline < today:      # on ne garde que les offres ouvertes
                continue
            n_open += 1
            found = classify(f"{t.title} {t.description}", themes)
            if not found:
                if not self.server_side_filter:
                    continue
                found = themes
            t.themes = ", ".join(found)
            out.append(t)
        out.sort(key=lambda t: (t.deadline is None, t.deadline or date.max))
        self.stats = {"récupérées": len(raw), "encore ouvertes": n_open, "retenues (thème)": len(out)}
        return out
