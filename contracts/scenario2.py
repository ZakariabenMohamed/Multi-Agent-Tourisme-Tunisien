"""
Contrat formel — Scénario 2 : Appel API Banque Mondiale
Projet DS2 — Secure Multi-Agent Tool-Orchestration
"""

SCENARIO_2 = {

    "context": {
        "sector": "Tourisme et Hôtellerie — Tunisie",
        "decision_maker": "Ministère du Tourisme Tunisien",
        "goal": (
            "Récupérer les indicateurs macro-économiques officiels "
            "(arrivées touristiques) depuis l'API publique de la Banque Mondiale "
            "et les intégrer dans le rapport KPI."
        ),
        "scenario_id": "scenario_2",
        "version": "1.0.0",
    },

    "input_contract": {
        "api_url": "https://api.worldbank.org/v2/country/TN/indicator/ST.INT.ARVL",
        "params": {"format": "json", "mrv": 5},
        "allow_list": ["api.worldbank.org"],
        "timeout_seconds": 10,
    },

    "expected_output": {
        "format": "JSON",
        "required_fields": ["date", "secteur", "indicateur", "donnees_api", "statut"],
        "indicateur": "ST.INT.ARVL",
        "statut_values": ["OK", "ERREUR_API", "TIMEOUT"],
    },

    "constraints": {
        "max_steps": 10,
        "max_retries": 3,
        "timeout_seconds": 30,
        "sites_autorises": ["api.worldbank.org"],
    },

    "expected_plan": [
        {"etape": 1, "outil": "api_client",  "description": "Appeler l'API Banque Mondiale"},
        {"etape": 2, "outil": "transformer", "description": "Transformer les données API"},
        {"etape": 3, "outil": "reporter",    "description": "Générer le rapport JSON"},
    ],

    "validation_rules": {
        "url_autorisee": "L'URL doit appartenir à la liste blanche (api.worldbank.org)",
        "reponse_non_nulle": "La réponse API ne doit pas être None ou vide",
        "statut_http_200": "Le code HTTP doit être 200",
        "donnees_valides": "Les données doivent contenir au moins une année avec une valeur non nulle",
    },
}


def afficher_contrat():
    import json
    print("=" * 55)
    print("CONTRAT — Scénario 2 : API Banque Mondiale")
    print("=" * 55)
    print(json.dumps(SCENARIO_2, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    afficher_contrat()
