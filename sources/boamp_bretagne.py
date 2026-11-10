"""BOAMP (Bulletin officiel des annonces de marchés publics) – Bretagne.
API Opendatasoft publique de la DILA, sans clé. Couvre les profils acheteurs (dont Mégalis Bretagne)
puisque les acheteurs publient leurs avis au BOAMP.
On récupère tous les avis ouverts de la région, le filtre Cyber/IA est fait localement (base.py)."""
from datetime import date

import requests

from config import BRETAGNE_DEPARTEMENTS, HTTP_TIMEOUT
from .base import Source, Tender, register

API = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"
PAGE = 100
MAX_PAGES = 5   # 500 avis max par département


def _s(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v if x)
    return str(v or "")


def _d(v):
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


@register
class BOAMPBretagne(Source):
    name = "BOAMP – Bretagne"
    scope = "bretagne"
    server_side_filter = False   # filtre Cyber/IA local

    def _get(self, params):
        r = requests.get(API, params=params, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        return r.json().get("results", [])

    def fetch(self, keywords):
        seen, res = set(), []
        for dep in BRETAGNE_DEPARTEMENTS:
            for page in range(MAX_PAGES):
                params = {"limit": PAGE, "offset": page * PAGE, "order_by": "dateparution desc",
                          "refine": f'code_departement:"{dep}"',
                          "where": f"datelimitereponse >= date'{date.today().isoformat()}'"}
                try:
                    rows = self._get(params)
                except requests.HTTPError:
                    params.pop("where")   # repli : filtre de date fait côté Python (base.py)
                    rows = self._get(params)
                for row in rows:
                    key = row.get("idweb") or row.get("id")
                    nature = (_s(row.get("nature_libelle")) + " " + _s(row.get("famille_libelle"))).lower()
                    if not key or key in seen or "attribution" in nature:
                        continue
                    seen.add(key)
                    res.append(Tender(
                        source=self.name,
                        title=_s(row.get("objet")) or key,
                        url=_s(row.get("url_avis")) or f"https://www.boamp.fr/pages/avis/?q=idweb:{key}",
                        organisation=_s(row.get("nomacheteur")),
                        published=_d(row.get("dateparution")),
                        deadline=_d(row.get("datelimitereponse")),
                        description=_s(row.get("descripteur_libelle")),
                    ))
                if len(rows) < PAGE:
                    break
        return res
