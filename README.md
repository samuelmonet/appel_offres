# Tender Radar
pip install -r requirements.txt
streamlit run app.py

## Ajouter une source
Crée `sources/ma_source.py` :

    from .base import Source, Tender, register
    @register
    class MaSource(Source):
        name = "Ma source"
        def fetch(self, keywords): return [Tender(source=self.name, title=..., url=...)]

Elle apparaît seule dans le menu. Mots-clés/thèmes : `config.py`.
Prévu pour le RAG : ajouter un module `rag/` qui consomme les `Tender` (champ `description`).
