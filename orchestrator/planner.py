"""
orchestrator/planner.py — Semaine 2
Planner avec backtracking contraint :
  - Génère un plan initial
  - Si une étape échoue, il cherche une étape alternative (backtracking)
  - Respecte max_steps et max_retries (contrat Scénario 1)
"""

from contracts.scenario1 import SCENARIO_1

# ── Outils alternatifs disponibles pour le backtracking ───────────────────────
# Si un outil échoue, on peut essayer son alternatif (fallback)
OUTILS_ALTERNATIFS = {
    "file_reader": None,       # pas d'alternative pour lire le CSV
    "calculator":  None,       # pas d'alternative pour calculer les KPIs
    "reporter":    None,       # pas d'alternative pour générer le rapport
}

# ── Règles de pruning (sécurité) ─────────────────────────────────────────────
# Ces combinaisons d'outils sont interdites / non sûres
COMBINAISONS_INTERDITES = set()  # extensible en semaine 3


def planifier(tache: str, etapes_echouees: list = None) -> list:
    """
    Génère un plan d'exécution pour la tâche donnée.
    Si etapes_echouees est fourni, le Planner fait du backtracking :
    il retire les étapes qui ont déjà échoué et cherche des alternatives.

    Paramètres
    ----------
    tache           : nom de la tâche ("rapport_hotels")
    etapes_echouees : liste des outils ayant échoué lors d'un run précédent

    Retourne une liste d'étapes ou [] si aucun plan viable n'existe.
    """
    if etapes_echouees is None:
        etapes_echouees = []

    print(f"Planner : je réfléchis au plan... (backtracking={bool(etapes_echouees)})")

    if tache == "rapport_hotels":
        # Plan de base — les 3 étapes canoniques
        plan_base = SCENARIO_1["expected_plan"]

        plan = []
        for etape in plan_base:
            outil = etape["outil"]

            # Backtracking : cet outil a déjà échoué, chercher un alternatif
            if outil in etapes_echouees:
                alternatif = OUTILS_ALTERNATIFS.get(outil)

                if alternatif is None:
                    # Pas d'alternative → on ne peut pas construire de plan
                    print(f"Planner : ❌ outil '{outil}' en échec, aucune alternative → abandon")
                    return []
                else:
                    # Alternative trouvée → on l'utilise
                    print(f"Planner : 🔄 backtrack '{outil}' → alternatif '{alternatif}'")
                    plan.append({
                        "etape":       etape["etape"],
                        "outil":       alternatif,
                        "description": f"[ALTERNATIF] {etape['description']}",
                    })
            else:
                # Outil OK → on garde l'étape normale
                plan.append(etape)

        # Vérification de sécurité — pruning
        outils_plan = tuple(e["outil"] for e in plan)
        if outils_plan in COMBINAISONS_INTERDITES:
            print(f"Planner : ⛔ combinaison interdite {outils_plan} → plan refusé")
            return []

        # Vérification contrainte max_steps
        max_steps = SCENARIO_1["constraints"]["max_steps"]
        if len(plan) > max_steps:
            print(f"Planner : ⛔ plan trop long ({len(plan)} > {max_steps}) → plan refusé")
            return []

        print(f"Planner : ✅ plan créé avec {len(plan)} étape(s)")
        return plan

    else:
        print("Planner : tâche inconnue")
        return []


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Plan normal ===")
    plan = planifier("rapport_hotels")
    for e in plan:
        print(f"   Étape {e['etape']} : {e['outil']} — {e['description']}")

    print("\n=== Backtracking (file_reader en échec) ===")
    plan_bt = planifier("rapport_hotels", etapes_echouees=["file_reader"])
    if plan_bt:
        for e in plan_bt:
            print(f"   Étape {e['etape']} : {e['outil']} — {e['description']}")
    else:
        print("   → Aucun plan viable trouvé (attendu car pas d'alternatif)")
