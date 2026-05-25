# L'Executor est l'agent qui exécute concrètement chaque étape du plan :

#Valide l'entrée (schéma)

#Appelle l'outil

#Valide la sortie

#Réessaie en cas d'erreur (retries)

#Remonte les échecs pour le backtracking


"""
orchestrator/executor.py — Semaine 2
Executor avec :
  - Validation stricte des schémas entrée/sortie (tool grounding)
  - Retries bornés (max_retries du contrat)
  - Stop conditions explicites
  - Remontée des outils échoués pour backtracking
"""

import sys
import time
sys.path.append(".")

from tools.file_reader import lire_hotels
from tools.calculator  import calculer_kpis
from tools.reporter    import generer_rapport
from contracts.scenario1 import SCENARIO_1

MAX_RETRIES = SCENARIO_1["constraints"]["max_retries"]   # 3
TIMEOUT     = SCENARIO_1["constraints"]["timeout_seconds"]  # 30


# ══════════════════════════════════════════════════════════════════════════════
# Validation des schémas (tool grounding)
# ══════════════════════════════════════════════════════════════════════════════

def _valider_schema_entree_csv(chemin_fichier: str) -> dict:
    """Vérifie que le chemin est une string non vide."""
    if not isinstance(chemin_fichier, str) or not chemin_fichier.strip():
        return {"erreur": "Schéma invalide : chemin_fichier doit être une chaîne non vide"}
    if not chemin_fichier.endswith(".csv"):
        return {"erreur": f"Schéma invalide : fichier non CSV ({chemin_fichier})"}
    return {"ok": True}

def _valider_schema_sortie_donnees(donnees) -> dict:
    """Vérifie que le DataFrame contient les colonnes requises."""
    import pandas as pd
    if not isinstance(donnees, pd.DataFrame):
        return {"erreur": "Sortie file_reader invalide : pas un DataFrame"}
    colonnes_requises = set(SCENARIO_1["input_contract"]["schema"]["columns"])
    colonnes_presentes = set(donnees.columns)
    manquantes = colonnes_requises - colonnes_presentes
    if manquantes:
        return {"erreur": f"Colonnes manquantes : {manquantes}"}
    if len(donnees) < SCENARIO_1["input_contract"]["constraints"]["min_rows"]:
        return {"erreur": "DataFrame vide"}
    return {"ok": True}

def _valider_schema_sortie_kpis(kpis: dict) -> dict:
    """Vérifie que les KPIs contiennent tous les champs attendus."""
    champs = ["moyenne_occupation", "meilleur_hotel", "revenus_totaux",
              "meilleure_region", "hotels_faibles"]
    for champ in champs:
        if champ not in kpis:
            return {"erreur": f"KPI manquant : {champ}"}
    if not (0 <= kpis["moyenne_occupation"] <= 100):
        return {"erreur": f"Taux occupation hors plage : {kpis['moyenne_occupation']}"}
    if kpis["revenus_totaux"] <= 0:
        return {"erreur": f"Revenus invalides : {kpis['revenus_totaux']}"}
    return {"ok": True}

def _valider_schema_sortie_rapport(rapport: dict) -> dict:
    """Vérifie que le rapport JSON contient tous les champs obligatoires."""
    for champ in SCENARIO_1["expected_output"]["required_fields"]:
        if champ not in rapport:
            return {"erreur": f"Champ rapport manquant : {champ}"}
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════════
# Executor principal
# ══════════════════════════════════════════════════════════════════════════════

def executer(plan: list, chemin_fichier: str) -> dict:
    """
    Exécute le plan étape par étape avec :
    - Validation schéma entrée/sortie à chaque étape
    - Retries bornés (MAX_RETRIES) en cas d'erreur transitoire
    - Stop conditions explicites

    Retourne un dict :
    {
      "rapport":        dict | None,
      "succes":         bool,
      "outils_echoues": list,   ← pour le backtracking du Planner
      "etapes_log":     list,   ← trace interne
    }
    """
    print("\nExecutor : je commence l'exécution...")

    donnees    = None
    kpis       = None
    rapport    = None
    outils_echoues = []
    etapes_log     = []

    for etape in plan:
        numero      = etape["etape"]
        outil       = etape["outil"]
        description = etape["description"]

        print(f"\n   ▶ Étape {numero} : {description}")

        succes_etape = False

        # ── Retry loop ────────────────────────────────────────────────────────
        for tentative in range(1, MAX_RETRIES + 1):
            if tentative > 1:
                print(f"      ↺ Tentative {tentative}/{MAX_RETRIES}...")
                time.sleep(0.5)

            try:
                # ── file_reader ───────────────────────────────────────────────
                if outil == "file_reader":
                    # Validation schéma ENTRÉE
                    v = _valider_schema_entree_csv(chemin_fichier)
                    if "erreur" in v:
                        print(f"      ⛔ Schéma entrée rejeté : {v['erreur']}")
                        break  # Erreur de schéma → inutile de réessayer

                    resultat = lire_hotels(chemin_fichier)

                    if "erreur" in resultat:
                        print(f"      ❌ Erreur : {resultat['erreur']}")
                        continue  # retry

                    # Validation schéma SORTIE
                    v2 = _valider_schema_sortie_donnees(resultat["donnees"])
                    if "erreur" in v2:
                        print(f"      ⛔ Schéma sortie rejeté : {v2['erreur']}")
                        break

                    donnees = resultat["donnees"]
                    print(f"      ✅ Fichier lu : {len(donnees)} hôtels")
                    succes_etape = True
                    break

                # ── calculator ────────────────────────────────────────────────
                elif outil == "calculator":
                    if donnees is None:
                        print("      ⛔ Stop condition : pas de données disponibles")
                        break

                    kpis = calculer_kpis(donnees)

                    # Validation schéma SORTIE
                    v = _valider_schema_sortie_kpis(kpis)
                    if "erreur" in v:
                        print(f"      ⛔ Schéma KPIs rejeté : {v['erreur']}")
                        break

                    print(f"      ✅ KPIs calculés (occupation moy. {kpis['moyenne_occupation']}%)")
                    succes_etape = True
                    break

                # ── reporter ──────────────────────────────────────────────────
                elif outil == "reporter":
                    if kpis is None:
                        print("      ⛔ Stop condition : pas de KPIs disponibles")
                        break

                    rapport = generer_rapport(kpis)

                    # Validation schéma SORTIE
                    v = _valider_schema_sortie_rapport(rapport)
                    if "erreur" in v:
                        print(f"      ⛔ Schéma rapport rejeté : {v['erreur']}")
                        break

                    print(f"      ✅ Rapport généré (statut : {rapport['statut']})")
                    succes_etape = True
                    break

            except Exception as exc:
                print(f"      ⚠️  Exception : {exc}")
                # Continue le retry

        # ── Fin retry loop ────────────────────────────────────────────────────
        etapes_log.append({
            "etape":  numero,
            "outil":  outil,
            "succes": succes_etape,
        })

        if not succes_etape:
            outils_echoues.append(outil)
            print(f"   ❌ Étape {numero} échouée après {MAX_RETRIES} tentative(s)")
            return {
                "rapport":        None,
                "succes":         False,
                "outils_echoues": outils_echoues,
                "etapes_log":     etapes_log,
            }

    return {
        "rapport":        rapport,
        "succes":         True,
        "outils_echoues": [],
        "etapes_log":     etapes_log,
    }


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from orchestrator.planner import planifier

    plan = planifier("rapport_hotels")
    resultat = executer(plan, "data_synthetic/hotels_tunisie.csv")

    if resultat["succes"]:
        r = resultat["rapport"]
        print(f"\nStatut      : {r['statut']}")
        print(f"Meilleur    : {r['resume']['meilleur_hotel']}")
        print(f"Alertes     : {r['alertes']['nombre_alertes']}")
    else:
        print(f"\nÉchec. Outils en erreur : {resultat['outils_echoues']}")
