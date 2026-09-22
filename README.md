# Secure Multi-Agent Tool-Orchestration
## Secteur : Tourisme et Hôtellerie en Tunisie

---

## 1. Vue d'ensemble

Ce projet implémente un système multi-agents pour analyser les performances
hôtelières tunisiennes à partir de données synthétiques.  
Trois agents coopèrent de façon séquentielle :

```
[Planner] → [Executor] → [Critic]
               ↓
        [Logger (JSONL)]
```

---

## 2. Structure du projet

```
projet_ds2/
├── contracts/
│   └── scenario1.py          # Contrat formel du Scénario 1
├── data_synthetic/
│   └── hotels_tunisie.csv    # Données synthétiques (15 hôtels)
├── logs/                     # Journaux d'exécution (auto-créé)
│   └── run_001.jsonl
├── orchestrator/
│   ├── planner.py            # Décide les étapes à suivre
│   ├── executor.py           # Exécute chaque étape dans l'ordre
│   ├── critic.py             # Valide le rapport produit
│   └── logger.py             # Journal d'exécution structuré (JSONL)
├── tests/
│   └── test_orchestrator.py  # Tests unitaires pytest
├── tools/
│   ├── file_reader.py        # Lecture du fichier CSV
│   ├── calculator.py         # Calcul des KPIs
│   └── reporter.py           # Génération du rapport JSON
├── main.py                   # Point d'entrée principal
└── README.md
```

---

## 3. Données synthétiques

**Fichier :** `data_synthetic/hotels_tunisie.csv`

| Colonne             | Type    | Description                         |
|---------------------|---------|-------------------------------------|
| hotel               | string  | Nom de l'hôtel                      |
| region              | string  | Gouvernorat (Tunis, Sousse, Djerba…)|
| taux_occupation_pct | integer | Taux d'occupation en %              |
| revenus_TND         | integer | Revenus en dinars tunisiens         |
| nb_touristes        | integer | Nombre de touristes                 |
| nb_chambres         | integer | Nombre de chambres                  |
| saison              | string  | ete / printemps / hiver             |

---

## 4. KPIs calculés

- **Taux d'occupation moyen** — moyenne de `taux_occupation_pct`
- **Meilleur hôtel** — hôtel avec le taux le plus élevé
- **Revenus totaux** — somme de `revenus_TND`
- **Meilleure région** — région avec les revenus cumulés les plus élevés
- **Hôtels en alerte** — hôtels sous la moyenne (→ alertes dans le rapport)

---

## 5. Rôle des agents

### 5.1 Planner
- **Rôle :** décide le plan d'exécution (liste d'étapes ordonnées)
- **Entrée :** nom de la tâche (`"rapport_hotels"`)
- **Sortie :** liste de dictionnaires `{etape, outil, description}`
- **Règle :** retourne `[]` pour une tâche inconnue

### 5.2 Executor
- **Rôle :** exécute chaque étape du plan dans l'ordre
- **Entrée :** plan (liste d'étapes) + chemin du fichier CSV
- **Sortie :** rapport JSON ou `None` en cas d'erreur
- **Comportement :** s'arrête et retourne `None` si une étape échoue

### 5.3 Critic
- **Rôle :** valide la qualité du rapport produit
- **Entrée :** rapport JSON
- **Sortie :** `True` (rapport valide) ou `False` (rapport invalide)
- **Vérifie :**
  - Le rapport n'est pas `None`
  - Tous les champs obligatoires sont présents (`date`, `secteur`, `resume`, `alertes`, `statut`)
  - Le taux d'occupation est compris entre 0 % et 100 %
  - Les revenus sont strictement positifs

### 5.4 Logger
- **Rôle :** trace chaque événement dans un fichier JSONL
- **Fichier :** `logs/run_{run_id}.jsonl`
- **Format de chaque ligne :**

```json
{
  "timestamp": "2026-04-11T10:00:00+00:00",
  "run_id":    "run_001",
  "step_id":   "step_1",
  "action":    "file_reader",
  "status":    "OK",
  "resultat":  {"nb_hotels": 15}
}
```

---

## 6. Conventions de nommage

| Concept   | Format              | Exemples                      |
|-----------|---------------------|-------------------------------|
| `run_id`  | `run_NNN`           | `run_001`, `run_002`          |
| `step_id` | `step_N`            | `step_0`, `step_1`, `step_2`  |
| `status`  | Valeur fixe         | `OK`, `ATTENTION`, `ERREUR`   |
| `statut` (rapport) | Valeur fixe | `OK`, `ATTENTION`          |

---

## 7. Scénarios

| Scénario | Description                                    | Statut       |
|----------|------------------------------------------------|--------------|
| 1        | Dashboard KPI depuis fichier CSV local         | ✅ Implémenté |
| 2        | Appel API Banque Mondiale (indicateurs Tunisie)| 🔜 Semaine 2  |

---

## 8. Installation et commandes

### Installer les dépendances

```bash
pip install pandas pytest
```

### Lancer les tests unitaires

```bash
# Depuis la racine du projet
pytest tests/test_orchestrator.py -v
```

Exemple de sortie attendue :

```
tests/test_orchestrator.py::TestFileReader::test_lecture_csv_reel_succes   PASSED
tests/test_orchestrator.py::TestCalculator::test_moyenne_occupation        PASSED
tests/test_orchestrator.py::TestCritic::test_rapport_valide_accepte        PASSED
tests/test_orchestrator.py::TestPlanner::test_plan_rapport_hotels_nb_etapes PASSED
...
```

### Exécuter le programme principal

```bash
python main.py
```

Le programme va :
1. Créer le plan (Planner)
2. Lire le CSV, calculer les KPIs, générer le rapport (Executor)
3. Valider le rapport (Critic)
4. Sauvegarder le journal dans `logs/run_001.jsonl`
5. Afficher le rapport final et le journal

---

## 9. Contrat formel (Scénario 1)

Le fichier `contracts/scenario1.py` définit de façon formelle :
- Le contexte métier
- Le schéma d'entrée (colonnes, types, contraintes)
- Le format de sortie (champs obligatoires)
- Les contraintes d'exécution (max_steps, timeout…)
- Les règles de validation du Critic

---

## 10. Auteurs

Projet réalisé dans le cadre du cours DS2 — 2026.  
Secteur : Tourisme Tunisien.



## explication
C'est quoi une "Injection de panne" ?
C'est simuler volontairement un problème pour tester que le système réagit correctement.
Aucune          → tout marche normalement         → résultat vert ✅
─────────────────────────────────────────────────────────────────
wrong_path      → le fichier CSV est introuvable  → résultat rouge ❌
corrupt_data    → le CSV a des colonnes manquantes → résultat rouge ❌
zero_revenue    → tous les revenus forcés à 0      → résultat rouge ❌
bad_rate        → taux d'occupation forcé à 150%  → résultat rouge ❌



## Le script ------------------------------------------------------------------------------------------------------------------------------------
# En ouvrant le dashboard
"Voici notre interface graphique. Elle montre visuellement comment les 3 agents travaillent ensemble."


# Tu pointes la colonne gauche

"À gauche, on a l'historique de tous nos runs. Un point vert = le run a réussi. Un point rouge = le run a échoué intentionnellement à cause d'une panne qu'on a injectée pour tester le système."


# Tu cliques sur run_001

"Voici un run normal — Scénario 1 sur notre fichier CSV des hôtels tunisiens. La timeline montre les 7 étapes dans l'ordre.
D'abord le Planner en bleu — il crée le plan de 3 étapes.
Ensuite l'Executor en jaune — il lit le CSV, calcule les KPIs, génère le rapport.
Ensuite le Critic en vert — il valide que le rapport est correct.
Tout est vert — mission accomplie en 312ms."


# Tu cliques sur run_003

"Voici maintenant une panne injectée — wrong_path. On a volontairement donné un mauvais chemin de fichier CSV pour tester la robustesse.
Le file_reader échoue 3 fois — on voit les 3 retries.
Le Planner fait du backtracking — il cherche une alternative.
Il n'en trouve pas — le système s'arrête proprement.
C'est exactement le comportement attendu — pas de crash, arrêt contrôlé avec un message clair."


# Tu cliques sur l'onglet MÉTRIQUES

"L'onglet Métriques montre nos résultats finaux : taux de succès, comparaison Backtracking seul vs Backtracking avec DP, et le tableau des KPIs — Hotel Iberostar meilleur avec 94%, Djerba meilleure région, 727 000 TND de revenus."


# Tu cliques sur l'onglet SÉCURITÉ

"L'onglet Sécurité montre nos politiques : seul api.worldbank.org est autorisé, les autres URLs sont bloquées. On a aussi des limites — maximum 10 étapes, 3 retries, 30 secondes. Et la redaction automatique des données sensibles dans les logs."


# Tu cliques sur l'onglet INJECTION

"Et ici on peut simuler n'importe quelle panne en un clic — sans toucher au code. Le système explique exactement comment il réagit à chaque panne."


# Pour terminer

"Ce dashboard est alimenté par les vrais journaux JSONL que le système génère à chaque run. Chaque ligne de la timeline correspond exactement à une ligne dans les fichiers logs."

