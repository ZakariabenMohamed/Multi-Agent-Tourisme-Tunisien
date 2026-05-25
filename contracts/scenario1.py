"""
Contrat formel — Scénario 1 : Dashboard KPI Hôtels Tunisiens
Projet DS2 — Secure Multi-Agent Tool-Orchestration
"""

SCENARIO_1 = {

    # ── Contexte métier ───────────────────────────────────────────────────────
    "context": {
        "sector": "Tourisme et Hôtellerie — Tunisie",
        "decision_maker": "Ministère du Tourisme Tunisien",
        "goal": (
            "Produire un rapport KPI hebdomadaire sur les performances "
            "hôtelières (taux d'occupation, revenus, alertes) à partir "
            "d'un fichier CSV synthétique."
        ),
        "scenario_id": "scenario_1",
        "version": "1.0.0",
    },

    # ── Contrat d'entrée ──────────────────────────────────────────────────────
    "input_contract": {
        "file_path": "data_synthetic/hotels_tunisie.csv",
        "format": "CSV",
        "encoding": "utf-8",
        "schema": {
            "columns": [
                "hotel",
                "region",
                "taux_occupation_pct",
                "revenus_TND",
                "nb_touristes",
                "nb_chambres",
                "saison",
            ],
            "types": [
                "string",
                "string",
                "integer",
                "integer",
                "integer",
                "integer",
                "string",
            ],
        },
        "constraints": {
            "min_rows": 1,
            "taux_occupation_pct": {"min": 0, "max": 100},
            "revenus_TND": {"min": 0},
        },
    },

    # ── Contrat de sortie ─────────────────────────────────────────────────────
    "expected_output": {
        "format": "JSON",
        "required_fields": [
            "date",
            "secteur",
            "resume",
            "alertes",
            "statut",
        ],
        "resume_fields": [
            "taux_occupation_moyen",
            "meilleur_hotel",
            "revenus_totaux_TND",
            "meilleure_region",
        ],
        "alertes_fields": [
            "hotels_sous_moyenne",
            "nombre_alertes",
        ],
        "statut_values": ["OK", "ATTENTION"],
    },

    # ── Contraintes d'exécution ───────────────────────────────────────────────
    "constraints": {
        "max_steps": 10,
        "max_retries": 3,
        "timeout_seconds": 30,
    },

    # ── Plan d'exécution attendu ──────────────────────────────────────────────
    "expected_plan": [
        {"etape": 1, "outil": "file_reader", "description": "Lire le fichier CSV des hôtels"},
        {"etape": 2, "outil": "calculator",  "description": "Calculer les KPIs"},
        {"etape": 3, "outil": "reporter",    "description": "Générer le rapport JSON"},
    ],

    # ── Règles de validation (Critic) ─────────────────────────────────────────
    "validation_rules": {
        "rapport_non_nul": "Le rapport ne doit pas être None",
        "champs_obligatoires": "Tous les champs de expected_output.required_fields doivent être présents",
        "taux_valide": "taux_occupation_moyen doit être compris entre 0 % et 100 %",
        "revenus_positifs": "revenus_totaux_TND doit être strictement positif",
    },
}


# ── Utilitaire ────────────────────────────────────────────────────────────────

def afficher_contrat():
    """Affiche un résumé lisible du contrat."""
    import json
    print("=" * 55)
    print("CONTRAT — Scénario 1 : Dashboard KPI Hôtels")
    print("=" * 55)
    print(json.dumps(SCENARIO_1, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    afficher_contrat()
