# ce fichier est le point d'entrée de la Semaine 3. Il lance les différents tests et scénarios dans l'ordre, et affiche un résumé final des résultats.

"""
main_complet.py — Point d'entrée Semaine 3
Lance dans l'ordre :
  1. Scénario 2 (API mock normale + panne 429)
  2. DP Cache stats
  3. Stress-test de concurrence (4 runs parallèles)
  4. Résumé global
"""

import json
import sys

from main_scenario2            import executer_scenario2
from orchestrator.concurrency  import stress_test_concurrence
from orchestrator.dp_cache     import rapport_cache, vider_cache
from orchestrator.logger       import journaliser, afficher_journal

CHEMIN_CSV = "data_synthetic/hotels_tunisie.csv"


def main():
    print("╔" + "═"*58 + "╗")
    print("║   DS2 — SEMAINE 3 : Sécurité + Concurrence + Scénario 2  ║")
    print("╚" + "═"*58 + "╝")

    resultats = {}

    # ════════════════════════════════════════════════════════
    # BLOC 1 — Scénario 2 : API mock normale
    # ════════════════════════════════════════════════════════
    print("\n\n" + "▶"*3 + " BLOC 1 : Scénario 2 — API normale")
    res_normal = executer_scenario2("run_s3_001", mode_api="normal")
    resultats["scenario2_normal"] = res_normal["succes"]

    # ════════════════════════════════════════════════════════
    # BLOC 2 — Scénario 2 : panne HTTP 429 injectée
    # ════════════════════════════════════════════════════════
    print("\n\n" + "▶"*3 + " BLOC 2 : Scénario 2 — HTTP 429 injecté")
    res_429 = executer_scenario2("run_s3_002", mode_api="rate_429")
    resultats["scenario2_429"] = not res_429["succes"]  # attendu en échec

    # ════════════════════════════════════════════════════════
    # BLOC 3 — DP Cache : statistiques
    # ════════════════════════════════════════════════════════
    print("\n\n" + "▶"*3 + " BLOC 3 : Statistiques DP Cache")
    stats_dp = rapport_cache()
    print(json.dumps(stats_dp, indent=4))
    resultats["dp_cache_rapport"] = True

    # ════════════════════════════════════════════════════════
    # BLOC 4 — Stress-test de concurrence
    # ════════════════════════════════════════════════════════
    print("\n\n" + "▶"*3 + " BLOC 4 : Stress-test concurrence (4 runs parallèles)")
    rapport_stress = stress_test_concurrence(
        chemin_csv=CHEMIN_CSV,
        tache="rapport_hotels",
        nb_runs=4,
        max_workers=4,
    )
    resultats["concurrence_succes"]  = rapport_stress["nb_succes"] == rapport_stress["nb_runs"]
    resultats["isolation_verifiee"]  = rapport_stress["isolation_ok"]

    # ════════════════════════════════════════════════════════
    # BILAN FINAL
    # ════════════════════════════════════════════════════════
    print("\n\n" + "═"*60)
    print("  BILAN SEMAINE 3")
    print("═"*60)
    checks = [
        ("Scénario 2 — API normale",         resultats["scenario2_normal"]),
        ("Scénario 2 — 429 géré proprement", resultats["scenario2_429"]),
        ("DP Cache — rapport généré",         resultats["dp_cache_rapport"]),
        ("Concurrence — tous les runs OK",   resultats["concurrence_succes"]),
        ("Isolation — pas de fuite d'état",  resultats["isolation_verifiee"]),
    ]
    for label, ok in checks:
        print(f"  {'✅' if ok else '❌'} {label}")

    total_ok = sum(1 for _, ok in checks if ok)
    print(f"\n  Score : {total_ok}/{len(checks)} — ", end="")
    print("SEMAINE 3 COMPLÈTE ✅" if total_ok == len(checks) else "À corriger ❌")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
