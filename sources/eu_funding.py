"""UE – Funding & Tenders Portal (SEDIA) : appels à propositions (Horizon Europe, Digital Europe…).
API publique (clé publique 'SEDIA'). Très pertinent pour trouver des consortiums / partenaires."""
import json
from datetime import date

import requests

from config import HTTP_TIMEOUT
from .base import Source, Tender, register, sample

API = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
TOPIC = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/"


def _first(md, key):
    v = md.get(key)
    return (v[0] if isinstance(v, list) and v else v) or ""


def _d(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


@register
class EUFunding(Source):
    name = "UE – Funding & Tenders (appels à propositions)"
    server_side_filter = True
    MAX_KEYWORDS = 6

    def fetch(self, keywords):
        query = {"bool": {"must": [
            {"terms": {"type": ["1", "2", "8"]}},        # appels à propositions
            {"terms": {"status": ["31094502"]}},         # 31094502 = ouvert
        ]}}
        seen, res = set(), []
        for kw in sample(keywords, self.MAX_KEYWORDS):
            r = requests.post(
                API, params={"apiKey": "SEDIA", "text": kw, "pageSize": 50, "pageNumber": 1},
                files={"query": (None, json.dumps(query), "application/json"),
                       "sort": (None, json.dumps({"order": "DESC", "field": "startDate"}), "application/json"),
                       "languages": (None, '["en"]', "application/json")},
                timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            for it in r.json().get("results", []):
                md = it.get("metadata", {})
                ident = _first(md, "identifier")
                if ident in seen:
                    continue
                seen.add(ident)
                title = it.get("title") or _first(md, "title") or _first(md, "callTitle") or ident
                res.append(Tender(
                    source=self.name, title=title,
                    url=TOPIC + ident.lower() if ident else it.get("url", ""),
                    organisation=_first(md, "programmeDivision") or _first(md, "frameworkProgramme"),
                    published=_d(_first(md, "startDate")),
                    deadline=_d(_first(md, "deadlineDate")),
                    description=(it.get("summary") or "")[:2000],
                ))
        return res
