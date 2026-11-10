"""ONU – UNDP Procurement Notices (https://procurement-notices.undp.org).
1) flux RSS officiels (RSS 1.0/RDF), découverts automatiquement depuis la page des flux ;
2) repli : parsing du tableau HTML de la page d'accueil."""
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import HTTP_TIMEOUT
from .base import Source, Tender, register

BASE = "https://procurement-notices.undp.org/"
FEEDS_PAGE = BASE + "proc_notices_rss_feed.cfm"
HEADERS = {"User-Agent": "Mozilla/5.0 (tender-radar)"}
DATE_RE = re.compile(r"\d{2}-[A-Za-z]{3}-\d{2,4}")


def _parse_date(s):
    for fmt in ("%d-%b-%y", "%d-%b-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            pass
    return None


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def parse_rss(xml_text: str, source: str) -> list[Tender]:
    root = ET.fromstring(xml_text.encode() if isinstance(xml_text, str) else xml_text)
    res = []
    for item in root.iter():
        if _local(item.tag) != "item":
            continue
        f = {_local(c.tag): (c.text or "").strip() for c in item}
        text = f"{f.get('title', '')} {f.get('description', '')}"
        dates = [_parse_date(d) for d in DATE_RE.findall(text)]
        dates = [d for d in dates if d]
        res.append(Tender(
            source=source, title=f.get("title", ""), url=f.get("link", ""),
            description=BeautifulSoup(f.get("description", ""), "html.parser").get_text(" ", strip=True),
            published=_parse_date_iso(f.get("date")),
            deadline=max(dates) if dates else None,   # à affiner selon le contenu réel du flux
        ))
    return res


def _parse_date_iso(s):
    try:
        return date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


def parse_html(html: str, source: str) -> list[Tender]:
    soup = BeautifulSoup(html, "html.parser")
    res = []
    for tr in soup.select("tr"):
        a = tr.select_one("a[href]")
        cells = [td.get_text(" ", strip=True) for td in tr.select("td")]
        if not a or len(cells) < 6:
            continue
        dates = [_parse_date(d) for d in DATE_RE.findall(" ".join(cells))]
        dates = [d for d in dates if d]
        res.append(Tender(
            source=source, title=a.get_text(" ", strip=True) or cells[2],
            url=urljoin(BASE, a["href"]),
            organisation=" / ".join(c for c in cells if c.startswith("UNDP"))[:100],
            published=dates[1] if len(dates) > 1 else None,
            deadline=dates[0] if dates else None,
        ))
    return res


@register
class UNDP(Source):
    name = "ONU – UNDP"

    def fetch(self, keywords):
        s = requests.Session()
        s.headers.update(HEADERS)
        # 1) flux RSS
        try:
            page = s.get(FEEDS_PAGE, timeout=HTTP_TIMEOUT)
            page.raise_for_status()
            links = [urljoin(FEEDS_PAGE, a["href"]) for a in
                     BeautifulSoup(page.text, "html.parser").select("a[href]")
                     if re.search(r"rss|\.xml|feed", a["href"], re.I)
                     and "proc_notices_rss_feed" not in a["href"]]
            if links:
                r = s.get(links[0], timeout=HTTP_TIMEOUT)   # 1er flux = « All UNDP Procurement Notices »
                r.raise_for_status()
                items = parse_rss(r.content, self.name)
                if items:
                    return items
        except Exception:
            pass
        # 2) repli HTML
        r = s.get(BASE + "index.cfm", timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        return parse_html(r.text, self.name)
