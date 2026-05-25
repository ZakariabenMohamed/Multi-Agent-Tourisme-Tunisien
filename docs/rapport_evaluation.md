# Rapport Final d'Évaluation — DS2
## Secure Multi-Agent Tool-Orchestration for the Tunisian Economy
### Secteur : Tourisme et Hôtellerie — Tunisie

---

## 1. Résumé exécutif

Ce projet implémente un système multi-agents sécurisé pour analyser les performances du secteur hôtelier tunisien. Trois agents spécialisés (Planner, Executor, Critic) coopèrent selon un pipeline contrôlé avec backtracking, validation stricte des schémas, injection de pannes, mémoïsation DP et tests de concurrence.

**Score global : 6/6 métriques atteintes — PROJET COMPLET ✅**

---

## 2. Métriques finales (Section 8 du PDF)

### Métrique 1 — Task Success Rate

| Runs | Succès | Taux |
|------|--------|------|
| 5    | 5      | **100%** |

Le pipeline Planner → Executor → Critic produit un rapport JSON structuré valide sur 100% des runs normaux. Le Critic valide chaque rapport sur 4 règles : non-nul, champs obligatoires, taux entre 0-100%, revenus positifs.

### Métrique 2 — Tool Grounding Score

| Tests schéma | Corrects | Taux |
|--------------|----------|------|
| 6            | 6        | **100%** |

L'Executor valide les schémas d'entrée ET de sortie à chaque étape. Les appels avec des données invalides (chemin vide, taux 150%, revenus nuls) sont rejetés avant exécution.

### Métrique 3 — Failure Recovery Effectiveness

| Pannes injectées | Gérées proprement | Taux |
|-----------------|-------------------|------|
| 2               | 2                 | **100%** |

- **wrong_path** : file_reader échoue → 3 retries → backtracking → arrêt propre
- **rate_429** : HTTP 429 simulé → 3 retries → arrêt propre avec message explicite

Aucune exception non gérée. Chaque panne produit un journal d'erreur structuré.

### Métrique 4 — Backtracking Search Quality

| Scénarios testés | Comportements corrects | Branches élagées |
|-----------------|----------------------|-----------------|
| 5               | 5 (100%)              | 4               |

Le Planner explore les alternatives et élague (pruning) les branches non viables :
- Plan normal → 3 étapes ✅
- file_reader échoué → aucune alternative → plan vide (pruning) ✅
- calculator échoué → aucune alternative → plan vide (pruning) ✅
- reporter échoué → aucune alternative → plan vide (pruning) ✅
- deux outils échoués → plan vide (pruning) ✅

### Métrique 5 — DP Efficiency Gain

| Mode | Latence moyenne |
|------|----------------|
| Sans cache (backtracking seul) | ~18 ms |
| Avec cache DP (hit) | ~5 ms |
| **Gain** | **~72%** |
| Taux de hit (4 runs identiques) | **75%** |

Le cache DP utilise un hash MD5 de (tâche, étapes_échouées, contexte) comme clé. En cas de hit, le plan est retourné sans recalcul.

### Métrique 6 — Concurrency Correctness

| Runs parallèles | Succès | Isolation | Leakage |
|----------------|--------|-----------|---------|
| 4              | 4/4    | ✅ OK     | ❌ Aucun |

4 runs lancés simultanément via ThreadPoolExecutor. Chaque run garde ses propres variables locales (donnees, kpis, rapport) et son propre journal JSONL. Aucune fuite d'état détectée.

---

## 3. Résultats des scénarios

### Scénario 1 — Dashboard KPI local

```json
{
  "date": "2026-04-30",
  "secteur": "Tourisme Tunisien",
  "resume": {
    "taux_occupation_moyen": "76.5%",
    "meilleur_hotel": "Hotel Iberostar",
    "revenus_totaux_TND": 727000,
    "meilleure_region": "Djerba"
  },
  "alertes": {
    "hotels_sous_moyenne": ["Hotel El Mouradi", "Hotel Novotel",
      "Hotel Vincci", "Hotel Laico", "Hotel Palm Beach",
      "Hotel Caribbean", "Hotel Kanta"],
    "nombre_alertes": 7
  },
  "statut": "ATTENTION"
}
```

### Scénario 2 — API Banque Mondiale (mock)

```json
{
  "indicateur": "ST.INT.ARVL — Arrivées touristiques Tunisie",
  "donnees_api": {
    "annee_recente": "2023",
    "valeur_recente": 9000000,
    "variation_yoy": 33.1,
    "moyenne_5ans": 6091000,
    "tendance": "baisse sur 5 ans (impact COVID 2020-2021)"
  },
  "statut": "OK"
}
```

---

## 4. Architecture du système

```
DONNÉES CSV / API MOCK
        ↓
   [PLANNER]          → Génère un plan, fait du backtracking si échec
        ↓                 Cache DP pour éviter les recalculs
   [EXECUTOR]         → Exécute chaque outil avec validation schéma
        ↓                 Retries bornés (max 3), stop conditions
   [CRITIC]           → Valide le rapport sur 4 règles de qualité
        ↓
   [LOGGER]           → Journal JSONL avec redaction + durée + niveau
        ↓
  RAPPORT JSON FINAL
```

### Agents

| Agent | Rôle | Semaine |
|-------|------|---------|
| Planner | Génère un plan ordonné, backtracking sur échec, pruning des branches non viables | 1 → 2 |
| Executor | Exécute les outils, valide schémas entrée/sortie, retries bornés | 1 → 2 |
| Critic | Valide le rapport sur 4 règles, retourne True/False | 1 |
| Logger | Journal JSONL avec redaction automatique, durée, niveau de trace | 1 → 3 |

### Outils

| Outil | Fonction | Scénario |
|-------|----------|---------|
| file_reader | Lit le CSV, vérifie existence | S1 |
| calculator | Calcule 5 KPIs à partir du DataFrame | S1 |
| reporter | Construit le rapport JSON | S1+S2 |
| mock_api | Simule l'API Banque Mondiale (4 modes) | S2 |
| transformer | Transforme données API → structure rapport | S2 |

---

## 5. Sécurité

| Mesure | Implémentation |
|--------|---------------|
| Allow-list URLs | Seul `api.worldbank.org` est autorisé |
| Validation schéma | Entrée ET sortie vérifiées à chaque étape |
| Redaction logs | Chemins, tokens, IDs masqués dans les JSONL |
| Isolation runs | Variables locales, journaux séparés par run_id |
| Max steps | Limité à 10 par le contrat scenario1.py |
| Max retries | Limité à 3 par le contrat scenario1.py |
| Timeout | 30 secondes maximum |

---

## 6. Tests unitaires

| Semaine | Fichier | Tests |
|---------|---------|-------|
| 1 | test_orchestrator.py | 23 |
| 2 | test_week2.py | 21 |
| 3 | test_week3.py | 30 |
| **Total** | | **74/74 PASSED** |

---

## 7. Challenges et solutions

| Challenge | Solution implémentée |
|-----------|---------------------|
| Appels d'outils non validés | Validation schéma entrée/sortie dans l'Executor |
| Boucles infinies possibles | max_steps=10, max_retries=3 dans le contrat |
| Explosion combinatoire du plan | Backtracking avec pruning + cache DP |
| Fuite de secrets dans les logs | Redaction automatique (regex) dans le Logger |
| Race conditions entre runs | Variables locales + journaux isolés par run_id |
| API externe indisponible | Mock server + retries bornés + arrêt propre |

---

## 8. Commandes de validation finale

```bash
# Tous les tests
pytest tests/ -v
# → 74/74 PASSED

# Scénario 1
python main.py

# Scénario 1 + pannes (Semaine 2)
python main_week2.py

# Scénario 2 (Semaine 3)
python main_scenario2.py

# Tout Semaine 3
python main_week3.py

# Métriques finales (Semaine 4)
python main_week4.py

# GUI
start gui\dashboard.html
```
