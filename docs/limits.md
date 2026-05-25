# Limites Connues — DS2

## Limites techniques

**1. Pas d'alternatives de backtracking**
Les outils `file_reader`, `calculator` et `reporter` n'ont pas d'outils alternatifs dans `OUTILS_ALTERNATIFS`. Quand l'un d'eux échoue, le plan est vide et le run s'arrête. En production, on ajouterait un `file_reader_backup` ou un `calculator_lite`.

**2. DP cache en mémoire uniquement**
Le cache DP est perdu à chaque redémarrage du programme. Pour persister entre sessions, on utiliserait `shelve` ou `sqlite3`.

**3. GUI statique sans serveur**
Le `dashboard.html` utilise des données simulées codées en JavaScript. Il ne lit pas les vrais fichiers JSONL en temps réel. Pour une version production, on brancherait un serveur Flask/FastAPI qui lirait le dossier `logs/`.

**4. Mock API uniquement**
Le Scénario 2 utilise un mock et non la vraie API Banque Mondiale. Les données (9 000 000 touristes 2023) sont synthétiques et calibrées pour être plausibles mais ne sont pas officielles.

**5. Données synthétiques**
Le fichier `hotels_tunisie.csv` contient 15 hôtels fabriqués. Avec de vraies données, les KPIs seraient différents.

**6. Pas de persistance entre sessions**
Le journal `logs/run_001.jsonl` accumule les entrées à chaque relancement. Pour un vrai système de production, chaque run_id serait unique par timestamp.

## Limites algorithmiques

**Complexité du Planner** : O(n) où n = nombre d'étapes. Pas d'explosion combinatoire car chaque outil n'a qu'une seule alternative possible (ou aucune). Pour un vrai backtracking avec k alternatives par outil, la complexité serait O(k^n).

**DP cache** : pas de politique d'éviction (LRU). Le cache grossit indéfiniment. Pour une utilisation longue, on limiterait à 1000 entrées maximum.

## Ce qui serait amélioré en production

- Vraies données hôtelières via API touristique tunisienne officielle
- Serveur backend (FastAPI) pour le GUI
- Base de données (PostgreSQL) pour les journaux
- Authentification pour accéder aux rapports
- Alertes automatiques (email/SMS) quand statut = ATTENTION
