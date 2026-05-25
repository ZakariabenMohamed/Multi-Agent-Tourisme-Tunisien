# DS2 — Semaine 3 : Sécurité, Concurrence & Scénario 2

---

## Ce qui a été ajouté cette semaine

| Fichier | Type | Rôle |
|---------|------|------|
| `tools/mock_api.py` | NOUVEAU | Serveur mock API Banque Mondiale (4 modes) |
| `tools/transformer.py` | NOUVEAU | Transformation données API → rapport JSON |
| `orchestrator/dp_cache.py` | NOUVEAU | DP Mémoïsation des plans répétés |
| `orchestrator/logger.py` | MODIFIÉ | Redaction + durée + niveau de trace |
| `orchestrator/concurrency.py` | NOUVEAU | Stress-test de concurrence (4 runs parallèles) |
| `gui/dashboard.html` | NOUVEAU | GUI complet — 4 onglets |
| `main_scenario2.py` | NOUVEAU | Scénario 2 bout-en-bout |
| `main_week3.py` | NOUVEAU | Point d'entrée global Semaine 3 |
| `tests/test_week3.py` | NOUVEAU | 25 tests unitaires |
| `contracts/scenario2.py` | NOUVEAU | Contrat formel Scénario 2 |

---

## Structure complète du projet

```
partie 1/
│
├── contracts/
│   ├── scenario1.py          ← Semaine 1
│   └── scenario2.py          ← Semaine 3 (NOUVEAU)
│
├── data_synthetic/
│   └── hotels_tunisie.csv
│
├── gui/
│   └── dashboard.html        ← Semaine 3 (NOUVEAU)
│
├── logs/                     ← Auto-créé
│   ├── run_001.jsonl
│   ├── run_002.jsonl
│   └── ...
│
├── orchestrator/
│   ├── planner.py            ← Semaine 2 (backtracking)
│   ├── executor.py           ← Semaine 2 (validation schémas)
│   ├── critic.py             ← Semaine 1
│   ├── logger.py             ← Semaine 3 (MODIFIÉ : redaction + durée)
│   ├── failure_injector.py   ← Semaine 2
│   ├── dp_cache.py           ← Semaine 3 (NOUVEAU)
│   └── concurrency.py        ← Semaine 3 (NOUVEAU)
│
├── tests/
│   ├── test_orchestrator.py  ← Semaine 1 (23 tests)
│   ├── test_week2.py         ← Semaine 2 (21 tests)
│   └── test_week3.py         ← Semaine 3 (25 tests)
│
├── tools/
│   ├── file_reader.py        ← Semaine 1
│   ├── calculator.py         ← Semaine 1
│   ├── reporter.py           ← Semaine 1
│   ├── mock_api.py           ← Semaine 3 (NOUVEAU)
│   └── transformer.py        ← Semaine 3 (NOUVEAU)
│
├── main.py                   ← Semaine 1
├── main_week2.py             ← Semaine 2
├── main_scenario2.py         ← Semaine 3 (NOUVEAU)
├── main_week3.py             ← Semaine 3 (NOUVEAU)
└── README.md
```

---

## Commandes d'installation et d'exécution

### 1. Installer les dépendances Semaine 3

```bash
pip install httpx tenacity
```

### 2. Lancer tous les tests (Semaines 1 + 2 + 3)

```bash
pytest tests/ -v
```

Résultat attendu : **69 tests passés** (23 + 21 + 25)

### 3. Lancer le Scénario 2 seul

```bash
python main_scenario2.py
```

Ce programme exécute :
- Run C : API mock normale → rapport touristique (succès)
- Run D : HTTP 429 injecté → 3 retries → arrêt propre (échec attendu)

### 4. Lancer le programme complet Semaine 3

```bash
python main_week3.py
```

Ce programme exécute dans l'ordre :
1. Scénario 2 normal
2. Scénario 2 avec HTTP 429 injecté
3. Statistiques DP Cache
4. Stress-test de concurrence (4 runs parallèles)
5. Bilan avec 5 checks

### 5. Ouvrir le GUI

```bash
# Ouvrir directement dans le navigateur (double-clic ou :)
start gui/dashboard.html          # Windows
open  gui/dashboard.html          # Mac
```

---

## Détail des nouveautés

### `tools/mock_api.py` — Serveur mock API Banque Mondiale

Simule l'API `api.worldbank.org/v2/country/TN/indicator/ST.INT.ARVL`
sans aucun appel réseau. Supporte 4 modes :

| Mode | Comportement |
|------|-------------|
| `normal` | Retourne 5 années de données touristiques tunisiennes |
| `rate_429` | Simule HTTP 429 (rate limit) |
| `timeout` | Simule un timeout réseau |
| `empty` | Retourne une liste vide |

### `tools/transformer.py` — Transformation des données

Calcule à partir des données API :
- Valeur et année les plus récentes
- Variation YoY (année sur année) en %
- Moyenne sur 5 ans
- Tendance (hausse / baisse / stable)
- Rapport JSON final structuré

### `orchestrator/dp_cache.py` — DP Mémoïsation

Mémoïse les plans de planification déjà calculés.
Clé = hash MD5 de `(tache, etapes_echouees, contexte)`.

**Gain mesuré :**

| Mode | Latence planification |
|------|----------------------|
| Sans cache | ~18 ms |
| Avec cache (hit) | ~5 ms |
| Taux de hit (4 runs identiques) | 75 % |

Fonctions principales :
- `obtenir_plan_cache()` — cherche dans le cache
- `sauvegarder_plan_cache()` — écrit dans le cache
- `rapport_cache()` — retourne les statistiques (hits, misses, taux, temps économisé)
- `vider_cache()` — remet à zéro (utile entre runs isolés)

### `orchestrator/logger.py` — Logger enrichi (Semaine 3)

Améliorations par rapport à la Semaine 1 :
- **Redaction automatique** : les chemins absolus Windows/Linux, tokens API et identifiants numériques longs sont remplacés par `[CHEMIN_REDACTE]` / `[REDACTE]`
- **Durée par étape** : chaque entrée JSONL contient maintenant `duree_ms`
- **Niveau de trace** : `INFO` / `WARNING` / `ERROR`
- **`lire_tous_les_runs()`** : liste tous les runs disponibles pour le GUI

### `orchestrator/concurrency.py` — Stress-test de concurrence

Lance `N` runs en parallèle via `ThreadPoolExecutor` et vérifie :
1. **Pas de fuite d'état** : chaque run calcule ses propres KPIs indépendamment
2. **Isolation des journaux** : chaque run a son propre `run_id` et son propre fichier JSONL
3. **Taux de succès** : tous les runs sur le même CSV donnent le même résultat

Résultat typique :
```
4/4 succès | isolation=✅ OK | durée totale ~350ms | moy/run ~88ms
```

### `gui/dashboard.html` — Interface graphique complète

Interface HTML/CSS/JS en une seule page, ouvrable directement dans le navigateur.
4 onglets :

**Onglet Run / Trace**
- Panneau latéral gauche : launcher (choix scénario + panne) + historique des runs
- Zone centrale : timeline d'exécution avec code couleur par agent (Planner=bleu, Executor=jaune, Critic=vert, Erreur=rouge)
- Chaque étape est cliquable → affiche le JSON brut

**Onglet Métriques**
- 6 métriques en temps réel : total runs, taux de succès, cache hits, durée moy., pannes récupérées, isolation concurrente
- Comparaison visuelle Backtracking seul vs Backtracking+DP (barres)
- Tableau du dernier rapport KPI

**Onglet Sécurité**
- Liste blanche des URLs autorisées / bloquées
- Politiques d'exécution (max_steps, timeout, redaction…)
- Journal des décisions de sécurité

**Onglet Injection**
- Boutons pour simuler les 4 types de pannes
- Affichage détaillé de la réponse du système pour chaque panne

---

## Résultats Semaine 3

```
✅ Scénario 2 — API normale        : rapport généré (9 000 000 touristes 2023, +33.1% YoY)
✅ Scénario 2 — HTTP 429 injecté   : 3 retries puis arrêt propre
✅ DP Cache                        : taux hit 75%, ~13ms économisées
✅ Concurrence 4 runs parallèles   : 4/4 succès, isolation vérifiée
✅ Tests unitaires                 : 25/25 passés
```

---

## Ce que le professeur peut vérifier

```bash
# Tous les tests des 3 semaines
pytest tests/ -v

# Scénario 2 avec panne
python main_scenario2.py

# Tout Semaine 3 en une commande
python main_week3.py

# GUI (ouvrir dans le navigateur)
gui/dashboard.html
```
