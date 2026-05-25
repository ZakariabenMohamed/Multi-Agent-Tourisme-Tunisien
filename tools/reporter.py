# Ce fichier construit le rapport JSON final à partir des KPIs calculés par calculator.py. C'est la sortie finale du Scénario 1.

import json #	Convertir le rapport en chaîne JSON (pour l'affichage, les logs, le GUI)
from datetime import date

def generer_rapport(kpis):

    rapport = {
        "date": str(date.today()),
        "secteur": "Tourisme Tunisien",
        "resume": {
            "taux_occupation_moyen": f"{kpis['moyenne_occupation']}%",
            "meilleur_hotel": kpis["meilleur_hotel"],
            "revenus_totaux_TND": int(kpis["revenus_totaux"]),
            "meilleure_region": kpis["meilleure_region"]
        },
        "alertes": {
            "hotels_sous_moyenne": kpis["hotels_faibles"],
            "nombre_alertes": len(kpis["hotels_faibles"])
        },
        "statut": "OK" if len(kpis["hotels_faibles"]) < 5 else "ATTENTION"
    }

    return rapport


# TEST
if __name__ == "__main__":
    import pandas as pd
    from calculator import calculer_kpis

    donnees = pd.read_csv("data_synthetic/hotels_tunisie.csv")
    kpis = calculer_kpis(donnees)
    rapport = generer_rapport(kpis)

    print("📋 RAPPORT FINAL")
    print(json.dumps(rapport, indent=4, ensure_ascii=False))