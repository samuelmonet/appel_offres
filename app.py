import pandas as pd
import streamlit as st

from config import KEYWORDS
from sources import load_sources

st.set_page_config(page_title="Tender Radar", page_icon="📡", layout="wide")
SOURCES = load_sources()
ALL = "Toutes les sources"
SCOPES = {"🌍 International": "international", "📍 Bretagne": "bretagne"}


@st.cache_data(ttl=3600, show_spinner=False)
def run(scope: str, source_name: str, themes: tuple[str, ...]):
    """Retourne (offres, erreurs). Un échec de source n'interrompt pas les autres."""
    names = [n for n, s in SOURCES.items() if s.scope == scope]
    if source_name != ALL:
        names = [source_name]
    tenders, errors, stats = [], {}, {}
    for n in names:
        try:
            tenders += SOURCES[n].search(list(themes))
            stats[n] = dict(SOURCES[n].stats)
        except Exception as e:
            errors[n] = f"{type(e).__name__}: {e}"
    return tenders, errors, stats


st.title("📡 Tender Radar — Cyber & IA")
scope = SCOPES[st.radio("Périmètre", list(SCOPES), horizontal=True)]
names = [n for n, s in SOURCES.items() if s.scope == scope]

c1, c2, c3 = st.columns([2, 2, 1])
source = c1.selectbox("Source", [ALL, *names])
themes = c2.multiselect("Thématiques", list(KEYWORDS), default=["Cyber", "IA"])
c3.write("")
go = c3.button("🔍 Rechercher", type="primary", use_container_width=True)

if go and themes:
    with st.spinner("Interrogation des sources…"):
        st.session_state["res"] = run(scope, source, tuple(themes))

if "res" in st.session_state:
    tenders, errors, stats = st.session_state["res"]
    for n, e in errors.items():
        st.warning(f"**{n}** a échoué : {e}")
    if tenders:
        df = pd.DataFrame([t.__dict__ for t in tenders])
        st.success(f"{len(df)} offre(s) ouverte(s)")
        st.dataframe(
            df[["source", "title", "organisation", "themes", "published", "deadline", "url"]],
            use_container_width=True, hide_index=True,
            column_config={
                "url": st.column_config.LinkColumn("Lien", display_text="Ouvrir"),
                "title": "Titre", "source": "Source", "organisation": "Organisme",
                "themes": "Thème", "published": "Publiée", "deadline": "Date limite",
            },
        )
        st.download_button("⬇️ Export CSV", df.to_csv(index=False).encode(), "offres.csv")
    elif not errors:
        st.info("Aucune offre ouverte trouvée.")
    if stats:
        with st.expander("🔎 Détails par source (diagnostic)"):
            st.dataframe(pd.DataFrame(stats).T, use_container_width=True)
