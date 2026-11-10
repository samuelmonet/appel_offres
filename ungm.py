"""UN Global Marketplace – pas d'API publique : scraping best-effort (le plus fragile)."""
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import HTTP_TIMEOUT
from .base import Source, Tender, register

BASE = "https://www.ungm.org"
DATE_RE = re.compile(r"\d{2}-[A-Za-z]{3}-\d{4}")


def _parse(s):
    try:
        return datetime.strptime(s, "%d-%b-%Y").date()
    except (ValueError, TypeError):
        return None


@register
class UNGM(Source):
    name = "ONU – UNGM"
    server_side_filter = True
    MAX_KEYWORDS = 8   # 1 requête par mot-clé

    def fetch(self, keywords):
        s = requests.Session()
        s.headers["User-Agent"] = "Mozilla/5.0 (tender-radar)"
        seen, res = set(), []
        for kw in keywords[: self.MAX_KEYWORDS]:
            payload = {"PageIndex": 0, "PageSize": 50, "Title": kw, "Description": "",
                       "Reference": "", "PublishedFrom": "", "PublishedTo": "",
                       "DeadlineFrom": "", "DeadlineTo": "", "Countries": [], "Agencies": [],
                       "UNSPSCs": [], "NoticeTypes": [], "SortField": "DatePublished",
                       "SortAscending": False, "isPicker": False, "IsSustainable": False,
                       "NoticeDisplayType": "", "NoticeSearchTotalLabelId": "noticeSearchTotal",
                       "TypeOfCompetitions": []}
            r = s.post(f"{BASE}/Public/Notice/Search", json=payload, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for row in soup.select("[data-noticeid]"):
                nid = row["data-noticeid"]
                if nid in seen:
                    continue
                seen.add(nid)
                a = row.select_one("a[href*='/Public/Notice/']")
                dates = [_parse(d) for d in DATE_RE.findall(row.get_text(" "))]
                res.append(Tender(
                    source=self.name,
                    title=(a.get_text(strip=True) if a else row.get_text(" ", strip=True)[:150]),
                    url=f"{BASE}/Public/Notice/{nid}",
                    published=dates[1] if len(dates) > 1 else None,
                    deadline=dates[0] if dates else None,   # à vérifier selon le HTML réel
                ))
        return res
