# cette fonction mock_api.py simule les réponses de l'API Banque Mondiale pour les arrivées touristiques en Tunisie (ST.INT.ARVL).
# Elle permet de tester le scénario 2 sans dépendre de l'API réelle, en fournissant des données réalistes et en simulant différents cas (réponse normale, rate limit, timeout, données vides).
# Les données mock sont basées sur les tendances réelles du tourisme en Tunisie, avec des chiffres d'arrivées touristiques pour les 5 dernières années.    

"""
tools/mock_api.py — Semaine 3
Serveur mock qui simule l'API Banque Mondiale pour le Scénario 2.
Retourne des données touristiques tunisiennes réalistes sans appel réseau externe.

Utilisé quand l'API réelle est indisponible ou pour les tests.
"""

import random

# ── Données mock Tunisie — arrivées touristiques (ST.INT.ARVL) ────────────────
DONNEES_MOCK_TOURISME = [
    {"date": "2023", "value": 9_000_000, "indicator": "ST.INT.ARVL", "country": "TN"},
    {"date": "2022", "value": 6_760_000, "indicator": "ST.INT.ARVL", "country": "TN"},
    {"date": "2021", "value": 2_289_000, "indicator": "ST.INT.ARVL", "country": "TN"},
    {"date": "2020", "value": 2_972_000, "indicator": "ST.INT.ARVL", "country": "TN"},
    {"date": "2019", "value": 9_434_000, "indicator": "ST.INT.ARVL", "country": "TN"},
]

# ── Modes de simulation ───────────────────────────────────────────────────────
MODES_DISPONIBLES = {
    "normal":   "Réponse normale (200 OK)",
    "rate_429": "Simulation HTTP 429 (rate limit)",
    "timeout":  "Simulation timeout",
    "empty":    "Données vides (aucune valeur)",
}


def appeler_api_mock(indicateur: str = "ST.INT.ARVL", mode: str = "normal") -> dict:
    """
    Simule un appel à l'API Banque Mondiale.

    Paramètres
    ----------
    indicateur : code de l'indicateur (ex: ST.INT.ARVL)
    mode       : "normal" | "rate_429" | "timeout" | "empty"

    Retourne un dict avec clés "succes"/"erreur" et "donnees".
    """
    import time

    print(f"   [MOCK API] indicateur={indicateur} | mode={mode}")

    # ── Simulation HTTP 429 ─────Vous avez fait trop de requêtes trop vite. L'API vous dit "calmez-vous, réessayez plus tard".────────────
    if mode == "rate_429":
        print("   [MOCK API] ⚠️  HTTP 429 — Rate limit simulé")
        return {"erreur": "rate_limit_429", "code_http": 429,
                "message": "Trop de requêtes — réessayez plus tard"}

    # ── Simulation timeout ─────────L'API met trop de temps à répondre.──On abandonne avant qu'elle ne réponde.───────────
    if mode == "timeout":
        print("   [MOCK API] ⚠️  Timeout simulé")
        time.sleep(0.1)
        return {"erreur": "timeout", "code_http": None,
                "message": "Délai d'attente dépassé"}

    # ── Simulation données vides ───────────────────────────────────────────────
    if mode == "empty":
        print("   [MOCK API] ⚠️  Données vides simulées")
        return {"succes": True, "code_http": 200, "donnees": []}

    # ── Réponse normale ────────────────────────────────────────────────────────
    donnees = [d.copy() for d in DONNEES_MOCK_TOURISME if d["indicator"] == indicateur]
    print(f"   [MOCK API] ✅  200 OK — {len(donnees)} entrées retournées")
    return {
        "succes": True,
        "code_http": 200,
        "donnees": donnees,
        "source": "mock_worldbank",
    }


def lister_modes():
    print("Modes disponibles :")
    for code, desc in MODES_DISPONIBLES.items():
        print(f"  [{code}] {desc}")


if __name__ == "__main__":
    lister_modes()
    print()
    resultat = appeler_api_mock("ST.INT.ARVL", mode="normal")
    if "donnees" in resultat:
        for d in resultat["donnees"]:
            print(f"  {d['date']} : {d['value']:,} touristes")
