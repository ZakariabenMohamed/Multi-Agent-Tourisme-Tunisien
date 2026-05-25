# ce fichier permet d'enregistrer les étapes d'exécution, les résultats, les erreurs, et d'afficher les journaux de manière structurée.

"""
orchestrator/logger.py — Semaine 3
Journal enrichi avec :
  - Redaction automatique des données sensibles (chemins, clés, valeurs PII)
  - Niveau de trace (INFO / WARNING / ERROR)
  - Durée de chaque étape (latence)
  - Format JSONL compatible avec le GUI
"""

import json # pour sérialiser les entrées de journal en JSONL
import os # pour gérer les fichiers et dossiers de logs
import re # pour les expressions régulières de redaction
from datetime import datetime, timezone # pour les timestamps ISO 8601
from typing import Optional # pour les annotations de type optionnel

LOGS_DIR = "logs"

# ── Patterns de redaction ─────────────────────────────────────────────────────
_PATTERNS_SENSIBLES = [
    (re.compile(r"[A-Za-z]:\\[^\s\"']+"),          "[CHEMIN_REDACTE]"), # chemins Windows
    (re.compile(r"/[a-zA-Z0-9_/.-]{10,}"),         "[CHEMIN_REDACTE]"), # chemins Unix
    (re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.I), "api_key=[REDACTE]"), # clés API
    (re.compile(r"token\s*[:=]\s*\S+", re.I),       "token=[REDACTE]"), # tokens d'authentification
    (re.compile(r"\b\d{8,}\b"),                     "[ID_REDACTE]"), # IDs numériques longs (ex: user_id, order_id)
]


def _redacter(valeur: str) -> str: # redacte une chaîne de caractères en appliquant les règles définies dans _PATTERNS_SENSIBLES
    """Applique les règles de redaction sur une chaîne."""
    for pattern, remplacement in _PATTERNS_SENSIBLES:
        valeur = pattern.sub(remplacement, valeur)
    return valeur


def _redacter_dict(obj, profondeur: int = 0) -> object:
    """Redacte récursivement un dictionnaire ou une valeur."""
    if profondeur > 5:
        return obj
    if isinstance(obj, str):
        return _redacter(obj)
    if isinstance(obj, dict):
        return {k: _redacter_dict(v, profondeur + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redacter_dict(i, profondeur + 1) for i in obj]
    return obj
#donnees = {
 #   "chemin": "D:\\projet\\data.csv",
   # "config": {"api_key": "abc123"}
#}
#_redacter_dict(donnees)
# → {"chemin": "[CHEMIN_REDACTE]", "config": {"api_key": "api_key=[REDACTE]"}}

def _timestamp() -> str: # retourne le timestamp actuel au format ISO 8601 en UTC (YYYY-MM-DDTHH:MM:SS.mmmZ)
    return datetime.now(timezone.utc).isoformat()


def _chemin_journal(run_id: str) -> str: # retourne le chemin du fichier de journal pour un run donné, en s'assurant que le dossier de logs existe
    os.makedirs(LOGS_DIR, exist_ok=True)
    return os.path.join(LOGS_DIR, f"run_{run_id}.jsonl")


# ══════════════════════════════════════════════════════════════════════════════
# Fonction principale
# ══════════════════════════════════════════════════════════════════════════════

def journaliser(
    run_id: str,
    step_id: str,
    action: str,
    status: str,
    resultat=None,
    duree_ms: Optional[float] = None,
    niveau: str = "INFO",
) -> dict:
    """
    Écrit une ligne JSONL enrichie dans le journal du run.

    Paramètres supplémentaires (Semaine 3)
    --------------------------------------
    duree_ms : durée de l'étape en millisecondes
    niveau   : "INFO" | "WARNING" | "ERROR"
    """
    # Redaction du résultat avant écriture
    resultat_redacte = _redacter_dict(resultat) if resultat is not None else None

    entree = {
        "timestamp":  _timestamp(),
        "run_id":     run_id,
        "step_id":    step_id,
        "action":     action,
        "status":     status,
        "niveau":     niveau,
        "duree_ms":   round(duree_ms, 2) if duree_ms is not None else None,
        "resultat":   resultat_redacte,
    }

    chemin = _chemin_journal(run_id)
    with open(chemin, "a", encoding="utf-8") as f:
        f.write(json.dumps(entree, ensure_ascii=False) + "\n")

    return entree


def lire_journal(run_id: str) -> list:
    chemin = _chemin_journal(run_id)
    if not os.path.exists(chemin):
        return []
    entrees = []
    with open(chemin, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if ligne:
                entrees.append(json.loads(ligne))
    return entrees


def afficher_journal(run_id: str) -> None:
    entrees = lire_journal(run_id)
    if not entrees:
        print(f"Aucun journal trouvé pour {run_id}")
        return

    print(f"\nJournal — {run_id} ({len(entrees)} entrée(s))")
    print("─" * 65)
    for e in entrees:
        icone = {"OK": "✅", "ERREUR": "❌", "ATTENTION": "⚠️ "}.get(e["status"], "ℹ️ ")
        duree = f" [{e['duree_ms']}ms]" if e.get("duree_ms") is not None else ""
        print(f"{icone} [{e['timestamp'][:19]}] {e['step_id']} | {e['action']} → {e['status']}{duree}")
        if e.get("resultat") is not None:
            print(f"     {e['resultat']}")
    print("─" * 65)


def lire_tous_les_runs() -> list:
    """Retourne la liste de tous les run_id disponibles dans le dossier logs/."""
    if not os.path.exists(LOGS_DIR):
        return []
    runs = []
    for fichier in sorted(os.listdir(LOGS_DIR)):
        if fichier.endswith(".jsonl") and fichier.startswith("run_"):
            run_id = fichier.replace("run_", "").replace(".jsonl", "")
            entrees = lire_journal(run_id)
            if entrees:
                debut  = entrees[0]["timestamp"]
                fin    = entrees[-1]["timestamp"]
                statut = entrees[-1]["status"]
                runs.append({
                    "run_id": run_id,
                    "debut":  debut,
                    "fin":    fin,
                    "statut": statut,
                    "nb_etapes": len(entrees),
                })
    return runs


# ── TEST ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    RUN = "run_test_s3"
    journaliser(RUN, "step_0", "start",       "OK",     {"tache": "rapport_hotels"}, duree_ms=1.2)
    journaliser(RUN, "step_1", "file_reader", "OK",     {"nb_hotels": 15, "chemin": "D:\\projet\\data.csv"}, duree_ms=45.3)
    journaliser(RUN, "step_2", "calculator",  "OK",     {"moyenne": 76.5}, duree_ms=12.1)
    journaliser(RUN, "step_3", "reporter",    "ERREUR", {"detail": "timeout"}, duree_ms=30001.0, niveau="ERROR")
    afficher_journal(RUN)
