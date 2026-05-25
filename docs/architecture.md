# Architecture — DS2 Multi-Agent Tourisme Tunisien

## Diagramme du système

```
┌─────────────────────────────────────────────────────────┐
│                   DONNÉES D'ENTRÉE                       │
│          hotels_tunisie.csv  /  API Banque Mondiale      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    PLANNER                               │
│  - Reçoit : nom de tâche + étapes échouées              │
│  - Produit : plan ordonné [étape1, étape2, étape3]      │
│  - Backtracking si outil échoué                         │
│  - Pruning si aucune alternative disponible             │
│  - Cache DP pour éviter les recalculs                   │
└────────────────────┬────────────────────────────────────┘
                     │ plan
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   EXECUTOR                               │
│  Pour chaque étape du plan :                            │
│    1. Valider schéma ENTRÉE                             │
│    2. Appeler l'outil                                   │
│    3. Valider schéma SORTIE                             │
│    4. Retry si erreur transitoire (max 3)               │
│  Retourne : {succes, rapport, outils_echoues}           │
└──────┬───────────────────────────┬──────────────────────┘
       │ outils_echoues            │ rapport
       │ (backtracking)            ▼
       │              ┌────────────────────────┐
       │              │        CRITIC          │
       │              │  Vérifie 4 règles :    │
       │              │  1. rapport non nul    │
       │              │  2. champs présents    │
       │              │  3. taux 0-100%        │
       │              │  4. revenus > 0        │
       │              │  Retourne : True/False │
       │              └───────────┬────────────┘
       │                          │
       ▼                          ▼
┌─────────────────────────────────────────────────────────┐
│                    LOGGER                                │
│  - Écrit chaque événement en JSONL                      │
│  - Redaction automatique (chemins, tokens)              │
│  - Durée en ms par étape                                │
│  - Niveau INFO / WARNING / ERROR                        │
│  → logs/run_001.jsonl, run_002.jsonl ...                │
└─────────────────────────────────────────────────────────┘
```

## Flux d'exécution Scénario 1

```
main.py
  → planifier("rapport_hotels")
      → [file_reader, calculator, reporter]
  → executer(plan, "data_synthetic/hotels_tunisie.csv")
      → lire_hotels()        : 15 hôtels lus
      → calculer_kpis()      : 5 KPIs calculés
      → generer_rapport()    : rapport JSON produit
  → critiquer(rapport)       : True ✅
  → journaliser(...)         : logs/run_001.jsonl
```

## Flux d'exécution Scénario 2

```
main_scenario2.py
  → appeler_api_mock("ST.INT.ARVL", mode="normal")
      → 5 points de données 2019-2023
  → transformer_donnees_api(donnees)
      → variation_yoy=+33.1%, tendance="baisse"
  → generer_rapport_scenario2(transforme)
      → rapport JSON statut="OK"
  → journaliser(...)
```

## Flux de backtracking (panne injectée)

```
main_week2.py (Run B)
  → injecter_panne("wrong_path")
      → chemin = "fichier_inexistant_PANNE.csv"
  → Tentative 1 :
      planifier() → plan normal
      executer()  → file_reader ÉCHEC (3 retries)
      → outils_echoues = ["file_reader"]
  → Tentative 2 :
      planifier(etapes_echouees=["file_reader"])
      → aucune alternative → retourne []
      → ARRÊT PROPRE
  → journaliser(status="ERREUR")
```

## Composants et responsabilités

| Composant | Fichier | Responsabilité |
|-----------|---------|---------------|
| Planner | orchestrator/planner.py | Décide les étapes, backtracking, pruning |
| Executor | orchestrator/executor.py | Exécute les outils, valide schémas, retries |
| Critic | orchestrator/critic.py | Valide la qualité du rapport final |
| Logger | orchestrator/logger.py | Journal JSONL, redaction, durée, niveaux |
| DP Cache | orchestrator/dp_cache.py | Mémoïsation des plans répétés |
| Concurrency | orchestrator/concurrency.py | Stress-test runs parallèles |
| Failure Injector | orchestrator/failure_injector.py | Injection de pannes contrôlées |
| File Reader | tools/file_reader.py | Lecture CSV avec validation |
| Calculator | tools/calculator.py | Calcul des 5 KPIs hôteliers |
| Reporter | tools/reporter.py | Construction rapport JSON |
| Mock API | tools/mock_api.py | Simulation API Banque Mondiale |
| Transformer | tools/transformer.py | Transformation données API |
