"""ReliefWeb – API v2. Nécessite un appname approuvé : https://apidoc.reliefweb.int
export RELIEFWEB_APPNAME=xxxx
Les appels d'offres / consultances sont publiés dans l'endpoint 'jobs'."""
import os
from datetime import date

import requests

from config import HTTP_TIMEOUT
from .base import Source, Tender, register

ENDPOINT = "jobs"


def _d(s):
    try:
        return date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


@register
class ReliefWeb(Source):
    name = "ReliefWeb"
    server_side_filter = True

    def fetch(self, keywords):
        appname = os.getenv("RELIEFWEB_APPNAME")
        if not appname:
            raise RuntimeError("Variable d'environnement RELIEFWEB_APPNAME manquante")
        body = {
            "query": {"value": " OR ".join(f'"{k}"' for k in keywords), "operator": "AND"},
            "fields": {"include": ["title", "url", "date.created", "date.closing", "source.name", "body"]},
            "sort": ["date.created:desc"], "limit": 100,
        }
        r = requests.post(f"https://api.reliefweb.int/v2/{ENDPOINT}",
                          params={"appname": appname}, json=body, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        res = []
        for item in r.json().get("data", []):
            f = item["fields"]
            res.append(Tender(
                source=self.name, title=f.get("title", ""), url=f.get("url", ""),
                organisation=", ".join(s["name"] for s in f.get("source", [])),
                published=_d(f.get("date", {}).get("created")),
                deadline=_d(f.get("date", {}).get("closing")),
                description=(f.get("body") or "")[:3000],
            ))
        return res
