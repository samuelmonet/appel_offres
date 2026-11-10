"""Thématiques et mots-clés. Ajoute une clé pour ajouter un domaine (ex: "Cloud")."""
KEYWORDS = {
    "Cyber": ["cybersecurity", "cyber security", "cyber-security", "information security",
              "penetration testing", "SOC", "SIEM", "cyber resilience",
              "cybersécurité", "cyber-sécurité", "sécurité informatique",
              "sécurité des systèmes d'information", "SSI", "PSSI", "test d'intrusion", "pentest"],
    "IA": ["artificial intelligence", "machine learning", "generative AI", "LLM",
           "deep learning", "NLP", "computer vision",
           "intelligence artificielle", "IA", "apprentissage automatique",
           "IA générative", "agent conversationnel", "chatbot"],
    # Thème large, à cocher en plus si Cyber/IA donne trop peu de résultats
    "Numérique": ["informatique", "logiciel", "numérique", "système d'information",
                  "cloud", "hébergement", "infogérance", "application web", "développement logiciel",
                  "data", "donnée", "software", "information system"],
}
HTTP_TIMEOUT = 30

# Flux RSS génériques : une ligne = une nouvelle source (voir sources/rss_generic.py)
RSS_FEEDS = {
    "RSS – FundsforNGOs": "https://www2.fundsforngos.org/feed/",   # URL à vérifier
}

# Région Bretagne : 22 Côtes-d'Armor, 29 Finistère, 35 Ille-et-Vilaine, 56 Morbihan
BRETAGNE_DEPARTEMENTS = ["22", "29", "35", "56"]
