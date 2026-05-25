# Ce fichier transforme les données brutes de mock_api.py de l'API en structure JSON exploitable pour le rapport.
# Il calcule : variation YoY, moyenne 5 ans, tendance. 

"""
tools/transformer.py — Semaine 3
Transforme les données brutes de l'API en structure JSON exploitable pour le rapport.
Calcule : variation YoY, moyenne 5 ans, tendance.
"""

from datetime import date


def transformer_donnees_api(donnees: list) -> dict:
    """
    Transforme une liste de points API en structure de rapport enrichie.

    Entrée  : [{"date": "2023", "value": 9000000, ...}, ...]
    Sortie  : dict avec serie, variation_yoy, moyenne_5ans, tendance
    """
    if not donnees:
        return {"erreur": "Données vides — impossible de transformer"}

    # Trier par année décroissante
    serie = sorted(
        [d for d in donnees if d.get("value") is not None], #Garde seulement les valeurs non nulles
        key=lambda x: x["date"], # Trie par année
        reverse=True,
    )

    if not serie:
        return {"erreur": "Toutes les valeurs sont nulles"}

    valeurs = [d["value"] for d in serie]  # liste des valeurs (ex: [9 000 000, 6 760 000, 2 289 000, ...])

    # Variation année sur année (YoY)
    variation_yoy = None
    if len(serie) >= 2:
        v_recent = serie[0]["value"] # valeur la plus récente (année la plus récente)    2023 : 9 000 000
        v_prec   = serie[1]["value"]# valeur de l'année précédente (deuxième point de la série) 2022 : 6 760 000
        if v_prec and v_prec != 0:
            variation_yoy = round(((v_recent - v_prec) / v_prec) * 100, 1) # calcul de la variation en pourcentage entre les deux années ________(9 000 000 - 6 760 000) / 6 760 000 × 100 = 33.1%

    # Moyenne sur 5 ans
    moyenne_5ans = round(sum(valeurs[:5]) / min(len(valeurs), 5)) # calcul de la moyenne des 5 dernières années (ou moins si la série est plus courte)

    # Tendance simple
    if len(valeurs) >= 2: # si on a au moins 2 points, on peut déterminer la tendance
        tendance = "hausse" if valeurs[0] > valeurs[-1] else "baisse"
    else:
        tendance = "stable"

    return {
        "indicateur":    serie[0].get("indicator", "ST.INT.ARVL"),
        "pays":          serie[0].get("country", "TN"),
        "annee_recente": serie[0]["date"],
        "valeur_recente": serie[0]["value"],
        "variation_yoy": variation_yoy,
        "moyenne_5ans":  moyenne_5ans,
        "tendance":      tendance,
        "serie":         serie,
    }


def generer_rapport_scenario2(donnees_transformees: dict) -> dict:
    """Génère le rapport JSON final pour le Scénario 2."""
    if "erreur" in donnees_transformees:
        return {
            "date":       str(date.today()),
            "secteur":    "Tourisme Tunisien",
            "indicateur": "ST.INT.ARVL",
            "statut":     "ERREUR_API",
            "donnees_api": None,
            "erreur":     donnees_transformees["erreur"],
        }

    return {
        "date":       str(date.today()),
        "secteur":    "Tourisme Tunisien",
        "indicateur": "Arrivées touristiques (ST.INT.ARVL) — Banque Mondiale",
        "donnees_api": {
            "annee_recente":  donnees_transformees["annee_recente"],
            "valeur_recente": donnees_transformees["valeur_recente"],
            "variation_yoy":  donnees_transformees["variation_yoy"],
            "moyenne_5ans":   donnees_transformees["moyenne_5ans"],
            "tendance":       donnees_transformees["tendance"],
            "source":         "mock_worldbank / api.worldbank.org",
        },
        "statut": "OK",
    }


if __name__ == "__main__":
    import json
    from tools.mock_api import appeler_api_mock

    res = appeler_api_mock("ST.INT.ARVL", "normal")
    if "donnees" in res:
        transforme = transformer_donnees_api(res["donnees"])
        rapport    = generer_rapport_scenario2(transforme)
        print(json.dumps(rapport, indent=4, ensure_ascii=False))
