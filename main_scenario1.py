"""
main.py — Point d'entrée principal
Projet DS2 : Secure Multi-Agent Tool-Orchestration — Tourisme Tunisien

Exécute le Scénario 1 :
  Planner → Executor → Critic → Journal → Affichage rapport
"""

import json
import sys

# ── Imports des agents et du journal ─────────────────────────────────────────
from orchestrator.planner  import planifier
from orchestrator.executor import executer
from orchestrator.critic   import critiquer
from orchestrator.logger   import journaliser, afficher_journal

# ── Configuration ─────────────────────────────────────────────────────────────
RUN_ID       = "run_001"
CHEMIN_CSV   = "data_synthetic/hotels_tunisie.csv"
TACHE        = "rapport_hotels"


def main():
    print("=" * 55)
    print("  DS2 — Multi-Agent Tourisme Tunisien")
    print(f"  Run : {RUN_ID}")
    print("=" * 55)

    # ── Étape 0 : Démarrage ───────────────────────────────────────────────────
    journaliser(RUN_ID, "step_0", "start", "OK", {"tache": TACHE, "fichier": CHEMIN_CSV})

    # ── Étape 1 : Planner ─────────────────────────────────────────────────────
    plan = planifier(TACHE)

    if not plan:
        journaliser(RUN_ID, "step_1", "planner", "ERREUR", {"detail": "Plan vide"})
        print("Erreur : le Planner n'a pas pu créer de plan.")
        sys.exit(1)

    journaliser(RUN_ID, "step_1", "planner", "OK", {"nb_etapes": len(plan)})

    # ── Étapes 2-4 : Executor (file_reader → calculator → reporter) ───────────
    rapport = executer(plan, CHEMIN_CSV)


    resultat = executer(plan, CHEMIN_CSV)

    if not resultat["succes"]:
        journaliser(RUN_ID, "step_2", "executor", "ERREUR", {"detail": "Rapport None"})
        print("\nErreur : l'Executor n'a pas produit de rapport.")
        sys.exit(1)

    rapport = resultat["rapport"]

    journaliser(RUN_ID, "step_2", "executor", "OK", {
        "statut":            rapport.get("statut"),
        "meilleur_hotel":    rapport["resume"]["meilleur_hotel"],
        "revenus_totaux_TND": rapport["resume"]["revenus_totaux_TND"],
    })

    valide = critiquer(rapport)
    if valide:
        journaliser(RUN_ID, "step_3", "critic", "OK", {"valide": True})
    else:
        journaliser(RUN_ID, "step_3", "critic", "ERREUR", {"valide": False})
        print("\nErreur : le Critic a rejeté le rapport.")
        sys.exit(1)

    # ── Étape 6 : Fin ─────────────────────────────────────────────────────────
    journaliser(RUN_ID, "step_4", "end", "OK", {"message": "Mission accomplie"})

    # ── Affichage du rapport ───────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  RAPPORT FINAL")
    print("=" * 55)
    print(json.dumps(rapport, indent=4, ensure_ascii=False))

    # ── Affichage du journal ───────────────────────────────────────────────────
    afficher_journal(RUN_ID)

    print(f"\nJournal sauvegardé → logs/{RUN_ID}.jsonl")
    print("Mission accomplie !\n")


if __name__ == "__main__":
    main()
