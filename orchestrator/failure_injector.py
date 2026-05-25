#Ce module simule volontairement des pannes pour vérifier que le système réagit correctement :
#Ne plante pas/Fait des retries/Active le backtracking/S'arrête proprement


"""
orchestrator/failure_injector.py — Semaine 2
Module d'injection de pannes contrôlées pour tester la robustesse du système.

Pannes supportées :
  - "wrong_path"   : chemin CSV incorrect → file_reader échoue
  - "corrupt_data" : données corrompues (colonnes manquantes)
  - "zero_revenue" : revenus nuls → Critic rejette
  - "bad_rate"     : taux d'occupation impossible (150%)

Usage :
    from orchestrator.failure_injector import injecter_panne
    chemin, donnees = injecter_panne("wrong_path", chemin_original, donnees)
"""

import pandas as pd
import copy

# ── Types de pannes disponibles ───────────────────────────────────────────────
PANNES_DISPONIBLES = {
    "wrong_path":   "Chemin de fichier CSV incorrect",
    "corrupt_data": "Colonnes manquantes dans le DataFrame",
    "zero_revenue": "Revenus forcés à 0 → Critic rejette",
    "bad_rate":     "Taux d'occupation forcé à 150% → Critic rejette",
}


def injecter_panne(type_panne: str, chemin_fichier: str = None, donnees=None):
    """
    Injecte une panne dans les paramètres d'entrée.

    Retourne (chemin_fichier_modifié, donnees_modifiées)
    """
    if type_panne not in PANNES_DISPONIBLES:
        raise ValueError(
            f"Panne inconnue : '{type_panne}'. "
            f"Disponibles : {list(PANNES_DISPONIBLES.keys())}"
        )

    print(f"\n💥 INJECTION DE PANNE : [{type_panne}] — {PANNES_DISPONIBLES[type_panne]}")

    # ── Panne 1 : mauvais chemin de fichier ───────────────────────────────────
    if type_panne == "wrong_path":
        chemin_modifie = "fichier_inexistant_PANNE.csv"
        print(f"   Chemin original : {chemin_fichier}")
        print(f"   Chemin injecté  : {chemin_modifie}")
        return chemin_modifie, donnees

    # ── Panne 2 : données corrompues (colonne supprimée) ──────────────────────
    elif type_panne == "corrupt_data":
        if donnees is not None:
            donnees_corrompues = donnees.copy()
            if "revenus_TND" in donnees_corrompues.columns:
                donnees_corrompues = donnees_corrompues.drop(columns=["revenus_TND"])
                print("   Colonne 'revenus_TND' supprimée")
            return chemin_fichier, donnees_corrompues
        return chemin_fichier, donnees

    # ── Panne 3 : revenus forcés à zéro ──────────────────────────────────────
    elif type_panne == "zero_revenue":
        if donnees is not None:
            donnees_modifiees = donnees.copy()
            donnees_modifiees["revenus_TND"] = 0
            print("   Tous les revenus forcés à 0")
            return chemin_fichier, donnees_modifiees
        return chemin_fichier, donnees

    # ── Panne 4 : taux d'occupation impossible ────────────────────────────────
    elif type_panne == "bad_rate":
        if donnees is not None:
            donnees_modifiees = donnees.copy()
            donnees_modifiees["taux_occupation_pct"] = 150
            print("   Tous les taux d'occupation forcés à 150%")
            return chemin_fichier, donnees_modifiees
        return chemin_fichier, donnees


def lister_pannes():
    """Affiche toutes les pannes disponibles."""
    print("\nPannes disponibles :")
    for code, description in PANNES_DISPONIBLES.items():
        print(f"   [{code}] {description}")


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    lister_pannes()

    chemin_test = "data_synthetic/hotels_tunisie.csv"

    print("\n--- Test panne wrong_path ---")
    c, d = injecter_panne("wrong_path", chemin_test, None)
    print(f"Chemin résultant : {c}")
