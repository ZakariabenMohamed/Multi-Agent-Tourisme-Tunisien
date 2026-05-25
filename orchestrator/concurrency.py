#Ce module lance plusieurs runs en parallèle (simultanément) et vérifie :
#Qu'ils ne se mélangent pas (pas de fuite d'état)
#Qu'ils réussissent tous (taux de succès 100%)
#Qu'aucune exception ne traverse les threads

"""
orchestrator/concurrency.py — Semaine 3
Stress-test de concurrence : lance plusieurs runs en parallèle
et vérifie qu'il n'y a pas de fuite d'état entre les runs.

Principe :
  - Chaque run possède son propre journal (run_id unique)
  - Les états (donnees, kpis, rapport) sont locaux à chaque appel d'executer()
  - On vérifie que run_i ne lit pas les résultats de run_j
"""

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed


def _run_isole(run_id: str, chemin_csv: str, tache: str,
               resultats: dict, verrou: threading.Lock):
    """
    Exécute un run complet dans un thread isolé.
    Sauvegarde le résultat dans le dict partagé sous run_id.
    """
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    from orchestrator.planner  import planifier
    from orchestrator.executor import executer
    from orchestrator.critic   import critiquer
    from orchestrator.logger   import journaliser

    debut = time.perf_counter()

    try:
        plan     = planifier(tache)
        resultat = executer(plan, chemin_csv)
        valide   = critiquer(resultat["rapport"]) if resultat["succes"] else False

        duree_ms = round((time.perf_counter() - debut) * 1000, 1)

        sortie = {
            "run_id":   run_id,
            "succes":   resultat["succes"] and valide,
            "duree_ms": duree_ms,
            "rapport":  resultat.get("rapport"),
        }

        journaliser(run_id, "step_end", "run_concurrent", "OK" if sortie["succes"] else "ERREUR",
                    {"duree_ms": duree_ms}, duree_ms=duree_ms)

    except Exception as exc:
        sortie = {
            "run_id":   run_id,
            "succes":   False,
            "erreur":   str(exc),
            "duree_ms": round((time.perf_counter() - debut) * 1000, 1),
        }

    with verrou:
        resultats[run_id] = sortie


def stress_test_concurrence(
    chemin_csv: str,
    tache: str = "rapport_hotels",
    nb_runs: int = 4,
    max_workers: int = 4,
) -> dict:
    """
    Lance nb_runs runs en parallèle et vérifie :
    1. Qu'aucun run ne partage d'état avec un autre
    2. Que tous les rapports sont identiques (même données → même résultat)
    3. Qu'aucune exception n'a traversé les threads

    Retourne un rapport de stress-test.
    """
    print(f"\n{'═'*55}")
    print(f"  STRESS-TEST CONCURRENCE — {nb_runs} runs / {max_workers} workers")
    print(f"{'═'*55}")

    resultats: dict = {}
    verrou = threading.Lock()
    run_ids = [f"run_concurrent_{i+1:03d}" for i in range(nb_runs)]

    debut_global = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_run_isole, rid, chemin_csv, tache, resultats, verrou): rid
            for rid in run_ids
        }
        for future in as_completed(futures):
            rid = futures[future]
            try:
                future.result()
                print(f"  ✅ {rid} terminé")
            except Exception as exc:
                print(f"  ❌ {rid} exception : {exc}")

    duree_totale_ms = round((time.perf_counter() - debut_global) * 1000, 1)

    # ── Analyse des résultats ─────────────────────────────────────────────────
    nb_succes   = sum(1 for r in resultats.values() if r.get("succes"))
    nb_echecs   = nb_runs - nb_succes
    durees      = [r["duree_ms"] for r in resultats.values() if "duree_ms" in r]
    duree_moy   = round(sum(durees) / len(durees), 1) if durees else 0

    # Vérification d'isolation : tous les rapports doivent être identiques
    rapports = [
        r["rapport"]["resume"]["taux_occupation_moyen"]
        for r in resultats.values()
        if r.get("rapport")
    ]
    isolation_ok = len(set(rapports)) <= 1  # tous identiques → pas de fuite d'état

    rapport_stress = {
        "nb_runs":         nb_runs,
        "nb_succes":       nb_succes,
        "nb_echecs":       nb_echecs,
        "taux_succes_pct": round(nb_succes / nb_runs * 100, 1),
        "duree_totale_ms": duree_totale_ms,
        "duree_moy_ms":    duree_moy,
        "isolation_ok":    isolation_ok,
        "leakage_detecte": not isolation_ok,
    }

    print(f"\n{'─'*55}")
    print(f"  Résultat : {nb_succes}/{nb_runs} succès | isolation={'✅ OK' if isolation_ok else '❌ FUITE!'}")
    print(f"  Durée totale : {duree_totale_ms}ms | Moy/run : {duree_moy}ms")
    print(f"{'─'*55}")

    return rapport_stress


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    rapport = stress_test_concurrence(
        chemin_csv="data_synthetic/hotels_tunisie.csv",
        nb_runs=4,
        max_workers=4,
    )
    print("\nRapport stress-test :")
    print(json.dumps(rapport, indent=2, ensure_ascii=False))
