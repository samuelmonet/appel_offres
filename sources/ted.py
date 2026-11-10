"""TED (Union européenne) – API v3 officielle, sans clé."""
from datetime import date

import requests

from config import HTTP_TIMEOUT
from .base import Source, Tender, register

API = "https://api.ted.europa.eu/v3/notices/search"


def _pick(v):
    """TED renvoie souvent {langue: texte | [textes]}."""
    if isinstance(v, dict):
        v = v.get("eng") or v.get("fra") or next(iter(v.values()), "")
    if isinstance(v, list):
        v = v[0] if v else ""
    return str(v or "")


def _d(v):
    v = v[0] if isinstance(v, list) and v else v
    try:
        return date.fromisoformat(str(v)[:10])
    except (ValueError, TypeError):
        return None


@register
class TED(Source):
    name = "UE – TED"
    server_side_filter = True

    def fetch(self, keywords):
        terms = " OR ".join(f'"{k}"' for k in keywords)
        body = {
            "query": f"FT ~ ({terms})",
            "fields": ["publication-number", "notice-title", "buyer-name",
                       "publication-date", "deadline-receipt-tender-date-lot"],
            "scope": "ACTIVE",      # avis dont le délai n'est pas échu
            "limit": 100, "page": 1,
        }
        r = requests.post(API, json=body, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        res = []
        for n in r.json().get("notices", []):
            num = n.get("publication-number", "")
            res.append(Tender(
                source=self.name,
                title=_pick(n.get("notice-title")),
                url=f"https://ted.europa.eu/en/notice/-/detail/{num}",
                organisation=_pick(n.get("buyer-name")),
                published=_d(n.get("publication-date")),
                deadline=_d(n.get("deadline-receipt-tender-date-lot")),
            ))
        return res
