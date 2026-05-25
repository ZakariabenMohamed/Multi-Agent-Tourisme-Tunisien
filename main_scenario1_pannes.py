# ce fichier execute 2 runs du Scénario 1 : un run normal sans panne (succès attendu) et un run avec une panne de mauvais chemin de fichier (échec + backtracking + récupération attendus). Il affiche ensuite un bilan des résultats.

"""
main_week2.py — Point d'entrée Semaine 2
Projet DS2 : Secure Multi-Agent Tool-Orchestration — Tourisme Tunisien

Exécute DEUX runs :
  Run A — Scénario 1 normal (succès attendu)
  Run B — Scénario 1 avec panne injectée (échec + backtracking + récupération)
"""

import json
import sys

from orchestrator.planner          import planifier
from orchestrator.executor         import executer
from orchestrator.critic           import critiquer
from orchestrator.logger           import journaliser, afficher_journal
from orchestrator.failure_injector import injecter_panne

CHEMIN_CSV = "data_synthetic/hotels_tunisie.csv"
TACHE      = "rapport_hotels"


# ══════════════════════════════════════════════════════════════════════════════
# Fonction générique : exécuter un run complet avec boucle de backtracking
# ══════════════════════════════════════════════════════════════════════════════

def run_complet(run_id: str, chemin_csv: str, tache: str, type_panne: str = None):
    """
    Lance un run complet avec :
    - Planner → Executor → Critic → Logger
    - Si une panne est injectée : injection → échec → backtracking → nouvel essai
    - Boucle de backtracking bornée à max_retries du contrat
    """
    from contracts.scenario1 import SCENARIO_1
    MAX_TENTATIVES = SCENARIO_1["constraints"]["max_retries"]

    print("\n" + "═" * 60)
    print(f"  RUN : {run_id}")
    if type_panne:
        print(f"  PANNE INJECTÉE : {type_panne}")
    print("═" * 60)

    # Journal de démarrage
    journaliser(run_id, "step_0", "start", "OK", {
        "tache": tache,
        "chemin_csv": chemin_csv,
        "panne": type_panne or "aucune",
    })

    # Injection de panne sur le chemin si demandé
    chemin_effectif = chemin_csv
    if type_panne == "wrong_path":
        chemin_effectif, _ = injecter_panne("wrong_path", chemin_csv, None)

    etapes_echouees = []
    rapport_final   = None

    # ── Boucle de backtracking ─────────────────────────────────────────────────
    for tentative in range(1, MAX_TENTATIVES + 1):
        print(f"\n{'─'*40}")
        print(f"  Tentative {tentative}/{MAX_TENTATIVES}")
        print(f"{'─'*40}")

        # Planner
        plan = planifier(tache, etapes_echouees=etapes_echouees)

        if not plan:
            journaliser(run_id, f"step_1_t{tentative}", "planner", "ERREUR",
                        {"detail": "Aucun plan viable", "etapes_echouees": etapes_echouees})
            print("Planner : aucun plan viable → arrêt")
            break

        journaliser(run_id, f"step_1_t{tentative}", "planner", "OK",
                    {"nb_etapes": len(plan), "backtrack": bool(etapes_echouees)})

        # Executor
        resultat = executer(plan, chemin_effectif)

        if resultat["succes"]:
            # Critic
            rapport = resultat["rapport"]
            valide  = critiquer(rapport)

            if valide:
                journaliser(run_id, f"step_3_t{tentative}", "critic", "OK", {"valide": True})
                journaliser(run_id, f"step_2_t{tentative}", "executor", "OK", {
                    "statut":             rapport.get("statut"),
                    "meilleur_hotel":     rapport["resume"]["meilleur_hotel"],
                    "revenus_totaux_TND": rapport["resume"]["revenus_totaux_TND"],
                })
                rapport_final = rapport
                break
            else:
                journaliser(run_id, f"step_3_t{tentative}", "critic", "ERREUR",
                            {"valide": False, "detail": "Rapport rejeté par le Critic"})
                print("Critic : rapport rejeté → arrêt (pas de backtracking sur validation)")
                break
        else:
            # Executor a échoué → backtracking
            nouveaux_echecs = resultat["outils_echoues"]
            journaliser(run_id, f"step_2_t{tentative}", "executor", "ERREUR",
                        {"outils_echoues": nouveaux_echecs})
            etapes_echouees.extend(nouveaux_echecs)
            print(f"\nBacktracking déclenché. Outils échoués : {etapes_echouees}")

    # ── Résultat final ─────────────────────────────────────────────────────────
    if rapport_final:
        journaliser(run_id, "step_end", "end", "OK", {"message": "Mission accomplie"})
        print("\n" + "═" * 60)
        print("  RAPPORT FINAL")
        print("═" * 60)
        print(json.dumps(rapport_final, indent=4, ensure_ascii=False))
    else:
        journaliser(run_id, "step_end", "end", "ERREUR",
                    {"message": "Run terminé en échec"})
        print("\n❌ Run terminé en ÉCHEC — voir le journal pour le détail")

    # Afficher le journal
    afficher_journal(run_id)
    print(f"\nJournal sauvegardé → logs/{run_id}.jsonl\n")

    return rapport_final is not None


# ══════════════════════════════════════════════════════════════════════════════
# Programme principal
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("╔" + "═" * 58 + "╗")
    print("║   DS2 — Semaine 2 : Backtracking + Injection de pannes    ║")
    print("╚" + "═" * 58 + "╝")

    # ── Run A : exécution normale ──────────────────────────────────────────────
    print("\n\n▶▶ RUN A : Exécution normale (aucune panne)")
    succes_a = run_complet("run_002", CHEMIN_CSV, TACHE, type_panne=None)

    # ── Run B : panne injectée (mauvais chemin CSV) ────────────────────────────
    print("\n\n▶▶ RUN B : Panne injectée — wrong_path (CSV introuvable)")
    succes_b = run_complet("run_003", CHEMIN_CSV, TACHE, type_panne="wrong_path")

    # ── Bilan ──────────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  BILAN DES RUNS — Semaine 2")
    print("═" * 60)
    print(f"  Run A (normal)         : {'✅ SUCCÈS' if succes_a else '❌ ÉCHEC'}")
    print(f"  Run B (panne injectée) : {'✅ SUCCÈS' if succes_b else '❌ ÉCHEC (attendu)'}")
    print("═" * 60)
    print("\nSemaine 2 terminée !\n")


if __name__ == "__main__":
    main()
