# Sécurité & Modèle de Menaces — DS2

## Menaces identifiées et contrôles

| # | Menace | Description | Contrôle implémenté |
|---|--------|-------------|---------------------|
| T1 | Exfiltration via URL | Un agent appelle une URL non autorisée | Allow-list dans `api_client.py` : seul `api.worldbank.org` autorisé |
| T2 | Path traversal | Un agent accède à des fichiers hors sandbox | Validation extension `.csv` et format chemin dans `_valider_schema_entree_csv` |
| T3 | Fuite de secrets dans logs | Chemins absolus, tokens exposés dans JSONL | Redaction automatique regex dans `logger.py` |
| T4 | Race condition | Deux runs parallèles modifient le même état | Variables locales dans `executer()`, journaux isolés par `run_id` |
| T5 | Boucle infinie | Agent boucle sans fin | `max_steps=10`, `max_retries=3`, `timeout=30s` dans le contrat |
| T6 | Données invalides | Rapport avec taux 150% ou revenus nuls accepté | Validation schéma Executor + règles Critic |

## Allow-list URLs

```python
SITES_AUTORISES = ["api.worldbank.org"]
```

Toute URL hors de cette liste retourne immédiatement `{"erreur": "Site non autorisé"}` sans appel réseau.

## Redaction dans les logs

Patterns masqués automatiquement :

| Pattern | Exemple | Remplacé par |
|---------|---------|-------------|
| Chemin Windows | `D:\Users\zakaria\data.csv` | `[CHEMIN_REDACTE]` |
| Chemin Linux | `/home/user/secret/data.csv` | `[CHEMIN_REDACTE]` |
| Token API | `token=abc123xyz` | `token=[REDACTE]` |
| ID numérique long | `12345678` | `[ID_REDACTE]` |

## Isolation des runs concurrents

Chaque run garde ses propres variables :
- `donnees` : DataFrame local
- `kpis` : dict local
- `rapport` : dict local
- Journal : `logs/run_{run_id}.jsonl` unique

Vérification : stress-test 4 runs parallèles → `isolation_ok=True`, `leakage_detecte=False`.

## Politiques d'exécution

```python
max_steps       = 10    # jamais plus de 10 étapes par run
max_retries     = 3     # jamais plus de 3 tentatives par outil
timeout_seconds = 30    # timeout global du run
```
