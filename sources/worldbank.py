"""Banque mondiale – API publique des avis de passation de marchés (sans clé, CC-BY 4.0).
Souvent ouverts aux ONG, consultants et ESN (projets financés par la BM)."""
import requests

from config import HTTP_TIMEOUT
from .base import Source, Tender, register, sample
from .undp import _parse_date_iso

API = "https://search.worldbank.org/api/v2/procnotices"
DETAIL = "https://projects.worldbank.org/en/projects-operations/procurement-detail/"


@register
class WorldBank(Source):
    name = "Banque mondiale"
    server_side_filter = True
    MAX_KEYWORDS = 8

    def fetch(self, keywords):
        seen, res = set(), []
        for kw in sample(keywords, self.MAX_KEYWORDS):
            r = requests.get(API, params={"format": "json", "qterm": kw, "rows": 100,
                                          "srt": "noticedate", "order": "desc"},
                             timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            for n in data.get("procnotices") or data.get("notices") or []:
                nid = n.get("id")
                ntype = n.get("notice_type", "")
                if not nid or nid in seen or "award" in ntype.lower():
                    continue
                seen.add(nid)
                res.append(Tender(
                    source=self.name,
                    title=n.get("bid_description") or n.get("project_name", ""),
                    url=DETAIL + str(nid),
                    organisation=f"{n.get('project_ctry_name', '')} – {n.get('contact_organization', '')}".strip(" –"),
                    published=_parse_date_iso(n.get("noticedate")),
                    deadline=_parse_date_iso(n.get("submission_deadline_date")),
                    description=f"{n.get('project_name', '')} {ntype}",
                ))
        return res
