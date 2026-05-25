"""
main_scenario2.py — Scénario 2 complet
API Banque Mondiale (mock) → Transformer → Rapport JSON
Inclut : run normal + run avec panne HTTP 429 injectée + backtracking
"""

import json
import sys
import time

from orchestrator.planner          import planifier
from orchestrator.logger           import journaliser, afficher_journal
from orchestrator.dp_cache         import obtenir_plan_cache, sauvegarder_plan_cache, rapport_cache
from tools.mock_api                import appeler_api_mock
from tools.transformer             import transformer_donnees_api, generer_rapport_scenario2
from orchestrator.critic           import critiquer

INDICATEUR = "ST.INT.ARVL"


# ── Executor Scénario 2 ────────────────────────────────────────────────────────

def executer_scenario2(run_id: str, mode_api: str = "normal") -> dict:
    """
    Exécute le pipeline Scénario 2 :
    api_client → transformer → reporter
    Avec retries sur HTTP 429 et backtracking si timeout.
    """
    from contracts.scenario2 import SCENARIO_2
    MAX_RETRIES = SCENARIO_2["constraints"]["max_retries"]

    print(f"\n{'─'*50}")
    print(f"  SCÉNARIO 2 | run={run_id} | api_mode={mode_api}")
    print(f"{'─'*50}")

    journaliser(run_id, "step_0", "start", "OK",
                {"scenario": "scenario_2", "indicateur": INDICATEUR, "mode_api": mode_api})

    # ── Étape 1 : Appel API avec retries ──────────────────────────────────────
    donnees_api = None
    for tentative in range(1, MAX_RETRIES + 1):
        debut = time.perf_counter()
        res   = appeler_api_mock(INDICATEUR, mode=mode_api)
        ms    = round((time.perf_counter() - debut) * 1000, 1)

        if res.get("succes"):
            donnees_api = res["donnees"]
            journaliser(run_id, "step_1", "api_client", "OK",
                        {"nb_points": len(donnees_api), "source": res.get("source")}, duree_ms=ms)
            break
        elif res.get("erreur") == "rate_limit_429":
            journaliser(run_id, f"step_1_t{tentative}", "api_client", "ATTENTION",
                        {"erreur": "rate_limit_429", "tentative": tentative}, duree_ms=ms, niveau="WARNING")
            print(f"      ↺ HTTP 429 — attente avant retry {tentative}/{MAX_RETRIES}")
            time.sleep(0.3)
        else:
            journaliser(run_id, f"step_1_t{tentative}", "api_client", "ERREUR",
                        {"erreur": res.get("erreur"), "tentative": tentative}, duree_ms=ms, niveau="ERROR")
            break

    if donnees_api is None:
        journaliser(run_id, "step_end", "end", "ERREUR",
                    {"message": "API indisponible après tous les retries"})
        print("❌ Scénario 2 — API indisponible")
        return {"succes": False, "rapport": None}

    # ── Étape 2 : Transformation ───────────────────────────────────────────────
    debut = time.perf_counter()
    donnees_transformees = transformer_donnees_api(donnees_api)
    ms = round((time.perf_counter() - debut) * 1000, 1)

    if "erreur" in donnees_transformees:
        journaliser(run_id, "step_2", "transformer", "ERREUR",
                    {"erreur": donnees_transformees["erreur"]}, duree_ms=ms, niveau="ERROR")
        return {"succes": False, "rapport": None}

    journaliser(run_id, "step_2", "transformer", "OK",
                {"valeur_recente": donnees_transformees["valeur_recente"],
                 "variation_yoy": donnees_transformees["variation_yoy"],
                 "tendance": donnees_transformees["tendance"]}, duree_ms=ms)

    # ── Étape 3 : Rapport ─────────────────────────────────────────────────────
    rapport = generer_rapport_scenario2(donnees_transformees)
    journaliser(run_id, "step_3", "reporter", "OK",
                {"statut": rapport["statut"]}, duree_ms=0.5)

    journaliser(run_id, "step_end", "end", "OK", {"message": "Scénario 2 terminé"})

    return {"succes": True, "rapport": rapport}


def main():
    print("╔" + "═"*58 + "╗")
    print("║   DS2 — Semaine 3 : Scénario 2 (API Mock) + DP Cache     ║")
    print("╚" + "═"*58 + "╝")

    # ── Run C : Scénario 2 normal ──────────────────────────────────────────────
    print("\n\n▶▶ RUN C : Scénario 2 — API normale")
    res_c = executer_scenario2("run_004", mode_api="normal")
    if res_c["succes"]:
        print("\n" + "═"*50)
        print("  RAPPORT SCÉNARIO 2")
        print("═"*50)
        print(json.dumps(res_c["rapport"], indent=4, ensure_ascii=False))
    afficher_journal("run_004")

    # ── Run D : Scénario 2 avec HTTP 429 injecté ──────────────────────────────
    print("\n\n▶▶ RUN D : Scénario 2 — HTTP 429 injecté (rate limit)")
    res_d = executer_scenario2("run_005", mode_api="rate_429")
    afficher_journal("run_005")

    # ── Rapport DP cache ──────────────────────────────────────────────────────
    print("\n" + "═"*50)
    print("  STATISTIQUES DP CACHE")
    print("═"*50)
    print(json.dumps(rapport_cache(), indent=4))

    print(f"\n{'═'*50}")
    print(f"  Run C (normal) : {'✅ SUCCÈS' if res_c['succes'] else '❌ ÉCHEC'}")
    print(f"  Run D (429)    : {'✅ SUCCÈS' if res_d['succes'] else '❌ ÉCHEC (attendu)'}")
    print(f"{'═'*50}\n")


if __name__ == "__main__":
    main()
