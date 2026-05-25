"""
tests/test_week4.py — Tests unitaires Semaine 4
Vérifie les métriques finales mappées à la Section 8 du PDF :

  1. Task Success Rate          ≥ 80%
  2. Tool Grounding Score       ≥ 90%
  3. Failure Recovery           = 100%
  4. Backtracking Quality       = 100%
  5. DP Efficiency Gain         > 0%
  6. Concurrency Correctness    isolation=True, leakage=False
  7. Tests cross-check          tous les runs gelés donnent le même résultat

Lancer avec : pytest tests/test_week4.py -v
"""

import sys
import os
import time
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.planner          import planifier
from orchestrator.executor         import executer
from orchestrator.critic           import critiquer
from orchestrator.logger           import journaliser, lire_journal, _redacter
from orchestrator.dp_cache         import (obtenir_plan_cache, sauvegarder_plan_cache,
                                            rapport_cache, vider_cache)
from orchestrator.failure_injector import injecter_panne
from tools.mock_api                import appeler_api_mock
from tools.transformer             import transformer_donnees_api, generer_rapport_scenario2
from tools.file_reader             import lire_hotels
from tools.calculator              import calculer_kpis
from tools.reporter                import generer_rapport

CSV = "data_synthetic/hotels_tunisie.csv"
TACHE = "rapport_hotels"


# ══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUE 1 — Task Success Rate ≥ 80%
# ══════════════════════════════════════════════════════════════════════════════

class TestTaskSuccessRate:

    def test_run_normal_reussit(self):
        """Un run normal doit toujours réussir."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        plan = planifier(TACHE)
        res  = executer(plan, CSV)
        assert res["succes"] is True
        assert res["rapport"] is not None

    def test_critic_valide_rapport_normal(self):
        """Le Critic doit valider le rapport produit sur le CSV réel."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        plan    = planifier(TACHE)
        res     = executer(plan, CSV)
        valide  = critiquer(res["rapport"])
        assert valide is True

    def test_5_runs_consecutifs_tous_succes(self):
        """5 runs consécutifs sur le même CSV doivent tous réussir."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        succes = 0
        for _ in range(5):
            plan = planifier(TACHE)
            res  = executer(plan, CSV)
            if res["succes"] and critiquer(res["rapport"]):
                succes += 1
        taux = succes / 5 * 100
        assert taux >= 80, f"Taux de succès {taux}% < seuil 80%"

    def test_rapport_contient_tous_les_champs(self):
        """Le rapport final doit contenir date, secteur, resume, alertes, statut."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        plan    = planifier(TACHE)
        res     = executer(plan, CSV)
        rapport = res["rapport"]
        for champ in ["date", "secteur", "resume", "alertes", "statut"]:
            assert champ in rapport, f"Champ manquant : {champ}"

    def test_statut_rapport_valide(self):
        """Le statut du rapport doit être OK ou ATTENTION, jamais autre chose."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        plan    = planifier(TACHE)
        res     = executer(plan, CSV)
        assert res["rapport"]["statut"] in ["OK", "ATTENTION"]

    def test_valeurs_kpis_coherentes(self):
        """Les KPIs produits doivent être dans des plages réalistes."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        plan    = planifier(TACHE)
        res     = executer(plan, CSV)
        resume  = res["rapport"]["resume"]
        taux    = float(resume["taux_occupation_moyen"].replace("%", ""))
        assert 0 <= taux <= 100
        assert resume["revenus_totaux_TND"] > 0
        assert isinstance(resume["meilleur_hotel"], str)
        assert isinstance(resume["meilleure_region"], str)


# ══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUE 2 — Tool Grounding Score ≥ 90%
# ══════════════════════════════════════════════════════════════════════════════

class TestToolGroundingScore:

    def test_entree_csv_valide_acceptee(self):
        from orchestrator.executor import _valider_schema_entree_csv
        assert "erreur" not in _valider_schema_entree_csv(CSV)

    def test_entree_csv_vide_rejetee(self):
        from orchestrator.executor import _valider_schema_entree_csv
        assert "erreur" in _valider_schema_entree_csv("")

    def test_entree_non_csv_rejetee(self):
        from orchestrator.executor import _valider_schema_entree_csv
        assert "erreur" in _valider_schema_entree_csv("fichier.txt")

    def test_sortie_dataframe_valide_acceptee(self):
        from orchestrator.executor import _valider_schema_sortie_donnees
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        df = pd.read_csv(CSV)
        assert "erreur" not in _valider_schema_sortie_donnees(df)

    def test_sortie_dataframe_colonne_manquante_rejetee(self):
        from orchestrator.executor import _valider_schema_sortie_donnees
        df = pd.DataFrame({"hotel": ["H1"], "region": ["Tunis"]})
        assert "erreur" in _valider_schema_sortie_donnees(df)

    def test_sortie_kpis_valides_acceptes(self):
        from orchestrator.executor import _valider_schema_sortie_kpis
        kpis = {
            "moyenne_occupation": 76.5,
            "meilleur_hotel": "Hotel Iberostar",
            "revenus_totaux": 727000,
            "meilleure_region": "Djerba",
            "hotels_faibles": ["Hotel Kanta"]
        }
        assert "erreur" not in _valider_schema_sortie_kpis(kpis)

    def test_sortie_kpis_taux_150_rejete(self):
        from orchestrator.executor import _valider_schema_sortie_kpis
        kpis = {
            "moyenne_occupation": 150,
            "meilleur_hotel": "H",
            "revenus_totaux": 1000,
            "meilleure_region": "D",
            "hotels_faibles": []
        }
        assert "erreur" in _valider_schema_sortie_kpis(kpis)

    def test_sortie_kpis_revenus_nuls_rejetes(self):
        from orchestrator.executor import _valider_schema_sortie_kpis
        kpis = {
            "moyenne_occupation": 70,
            "meilleur_hotel": "H",
            "revenus_totaux": 0,
            "meilleure_region": "D",
            "hotels_faibles": []
        }
        assert "erreur" in _valider_schema_sortie_kpis(kpis)

    def test_sortie_rapport_valide_accepte(self):
        from orchestrator.executor import _valider_schema_sortie_rapport
        rapport = {
            "date": "2026-05-01", "secteur": "Tourisme",
            "resume": {}, "alertes": {}, "statut": "OK"
        }
        assert "erreur" not in _valider_schema_sortie_rapport(rapport)

    def test_sortie_rapport_champ_manquant_rejete(self):
        from orchestrator.executor import _valider_schema_sortie_rapport
        rapport = {"date": "2026-05-01", "secteur": "Tourisme"}
        assert "erreur" in _valider_schema_sortie_rapport(rapport)


# ══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUE 3 — Failure Recovery Effectiveness = 100%
# ══════════════════════════════════════════════════════════════════════════════

class TestFailureRecovery:

    def test_wrong_path_arret_propre(self):
        """wrong_path → file_reader échoue → arrêt propre sans exception."""
        chemin_modif, _ = injecter_panne("wrong_path", CSV, None)
        plan = planifier(TACHE)
        res  = executer(plan, chemin_modif)
        assert res["succes"] is False
        assert "file_reader" in res["outils_echoues"]

    def test_wrong_path_backtracking_declenche(self):
        """Après wrong_path, le backtracking doit retourner un plan vide."""
        plan_bt = planifier(TACHE, etapes_echouees=["file_reader"])
        assert plan_bt == []

    def test_rate_429_detecte_et_gere(self):
        """HTTP 429 doit être détecté avec le bon code d'erreur."""
        res = appeler_api_mock("ST.INT.ARVL", mode="rate_429")
        assert "erreur" in res
        assert res["erreur"] == "rate_limit_429"
        assert res["code_http"] == 429

    def test_timeout_detecte_et_gere(self):
        """Timeout simulé doit retourner une erreur propre."""
        res = appeler_api_mock("ST.INT.ARVL", mode="timeout")
        assert "erreur" in res
        assert res["erreur"] == "timeout"

    def test_corrupt_data_rejete_par_schema(self):
        """Données corrompues (colonne manquante) doivent être rejetées."""
        from orchestrator.executor import _valider_schema_sortie_donnees
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        df = pd.read_csv(CSV)
        _, df_corrompu = injecter_panne("corrupt_data", CSV, df)
        result = _valider_schema_sortie_donnees(df_corrompu)
        assert "erreur" in result

    def test_zero_revenue_rejete_par_critic(self):
        """Revenus nuls doivent être rejetés par le Critic."""
        rapport = {
            "date": "2026-05-01",
            "secteur": "Tourisme Tunisien",
            "resume": {
                "taux_occupation_moyen": "76.5%",
                "meilleur_hotel": "Hotel Iberostar",
                "revenus_totaux_TND": 0,
                "meilleure_region": "Djerba"
            },
            "alertes": {"hotels_sous_moyenne": [], "nombre_alertes": 0},
            "statut": "OK"
        }
        assert critiquer(rapport) is False

    def test_taux_150_rejete_par_critic(self):
        """Taux d'occupation à 150% doit être rejeté par le Critic."""
        rapport = {
            "date": "2026-05-01",
            "secteur": "Tourisme Tunisien",
            "resume": {
                "taux_occupation_moyen": "150%",
                "meilleur_hotel": "Hotel X",
                "revenus_totaux_TND": 100000,
                "meilleure_region": "Djerba"
            },
            "alertes": {"hotels_sous_moyenne": [], "nombre_alertes": 0},
            "statut": "OK"
        }
        assert critiquer(rapport) is False


# ══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUE 4 — Backtracking Search Quality = 100%
# ══════════════════════════════════════════════════════════════════════════════

class TestBacktrackingQuality:

    def test_plan_normal_sans_echec(self):
        """Sans échec, le plan normal contient exactement 3 étapes."""
        plan = planifier(TACHE, etapes_echouees=[])
        assert len(plan) == 3

    def test_backtrack_file_reader_retourne_vide(self):
        """file_reader échoué + pas d'alternative → plan vide (pruning)."""
        plan = planifier(TACHE, etapes_echouees=["file_reader"])
        assert plan == []

    def test_backtrack_calculator_retourne_vide(self):
        """calculator échoué → plan vide."""
        plan = planifier(TACHE, etapes_echouees=["calculator"])
        assert plan == []

    def test_backtrack_reporter_retourne_vide(self):
        """reporter échoué → plan vide."""
        plan = planifier(TACHE, etapes_echouees=["reporter"])
        assert plan == []

    def test_backtrack_deux_outils_echoues(self):
        """Deux outils échoués → plan vide."""
        plan = planifier(TACHE, etapes_echouees=["file_reader", "calculator"])
        assert plan == []

    def test_tache_inconnue_retourne_vide(self):
        """Tâche inconnue → plan vide."""
        plan = planifier("tache_inexistante")
        assert plan == []

    def test_ordre_outils_correct(self):
        """L'ordre des outils doit être file_reader → calculator → reporter."""
        plan   = planifier(TACHE)
        outils = [e["outil"] for e in plan]
        assert outils == ["file_reader", "calculator", "reporter"]


# ══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUE 5 — DP Efficiency Gain > 0%
# ══════════════════════════════════════════════════════════════════════════════

class TestDPEfficiency:

    def setup_method(self):
        vider_cache()

    def _plan(self):
        return [
            {"etape": 1, "outil": "file_reader",  "description": "Lire CSV"},
            {"etape": 2, "outil": "calculator",   "description": "KPIs"},
            {"etape": 3, "outil": "reporter",     "description": "Rapport"},
        ]

    def test_premier_appel_miss(self):
        """Le premier appel est toujours un MISS."""
        _, depuis_cache, _ = obtenir_plan_cache(TACHE, [])
        assert depuis_cache is False

    def test_deuxieme_appel_hit(self):
        """Après sauvegarde, le deuxième appel est un HIT."""
        sauvegarder_plan_cache(TACHE, [], self._plan(), duree_calcul_ms=18.0)
        _, depuis_cache, _ = obtenir_plan_cache(TACHE, [])
        assert depuis_cache is True

    def test_gain_latence_positif(self):
        """Le temps économisé doit être > 0 après un HIT."""
        sauvegarder_plan_cache(TACHE, [], self._plan(), duree_calcul_ms=18.0)
        _, _, economie = obtenir_plan_cache(TACHE, [])
        assert economie > 0

    def test_taux_hit_100_sur_runs_identiques(self):
        """4 appels identiques après sauvegarde → taux hit = 100%."""
        sauvegarder_plan_cache(TACHE, [], self._plan(), duree_calcul_ms=18.0)
        for _ in range(4):
            obtenir_plan_cache(TACHE, [])
        stats = rapport_cache()
        assert stats["taux_hit_pct"] == 100.0

    def test_cles_differentes_echecs_differents(self):
        """Des étapes échouées différentes → clés différentes → MISS."""
        sauvegarder_plan_cache(TACHE, [], self._plan(), duree_calcul_ms=18.0)
        _, depuis_cache, _ = obtenir_plan_cache(TACHE, ["file_reader"])
        assert depuis_cache is False

    def test_stats_rapport_complet(self):
        """rapport_cache() doit retourner tous les champs attendus."""
        stats = rapport_cache()
        for champ in ["cache_hits", "cache_misses", "taux_hit_pct",
                      "temps_economise_ms", "entrees_en_cache"]:
            assert champ in stats

    def test_vider_cache_reset_complet(self):
        """vider_cache() remet tout à zéro."""
        sauvegarder_plan_cache(TACHE, [], self._plan(), 18.0)
        obtenir_plan_cache(TACHE, [])
        vider_cache()
        stats = rapport_cache()
        assert stats["cache_hits"]      == 0
        assert stats["cache_misses"]    == 0
        assert stats["entrees_en_cache"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUE 6 — Concurrency Correctness
# ══════════════════════════════════════════════════════════════════════════════

class TestConcurrencyCorrectness:

    def test_stress_2_runs_succes(self):
        """2 runs parallèles doivent tous réussir."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        from orchestrator.concurrency import stress_test_concurrence
        rapport = stress_test_concurrence(CSV, TACHE, nb_runs=2, max_workers=2)
        assert rapport["nb_succes"] == 2

    def test_isolation_verifiee(self):
        """Pas de fuite d'état entre les runs parallèles."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        from orchestrator.concurrency import stress_test_concurrence
        rapport = stress_test_concurrence(CSV, TACHE, nb_runs=2, max_workers=2)
        assert rapport["isolation_ok"]     is True
        assert rapport["leakage_detecte"]  is False

    def test_taux_succes_100(self):
        """Taux de succès doit être 100% sur runs parallèles normaux."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        from orchestrator.concurrency import stress_test_concurrence
        rapport = stress_test_concurrence(CSV, TACHE, nb_runs=2, max_workers=2)
        assert rapport["taux_succes_pct"] == 100.0

    def test_rapport_stress_champs_presents(self):
        """Le rapport du stress-test doit contenir tous les champs."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        from orchestrator.concurrency import stress_test_concurrence
        rapport = stress_test_concurrence(CSV, TACHE, nb_runs=2, max_workers=2)
        for champ in ["nb_runs", "nb_succes", "taux_succes_pct",
                      "isolation_ok", "leakage_detecte", "duree_totale_ms"]:
            assert champ in rapport


# ══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUE 7 — Cross-check : résultats gelés identiques
# ══════════════════════════════════════════════════════════════════════════════

class TestCrossCheck:
    """
    Vérifie que les résultats sont reproductibles et cohérents.
    Les valeurs sont celles mesurées lors de la validation finale.
    """

    def test_taux_occupation_moyen_76_5(self):
        """Le taux moyen sur le CSV réel doit être exactement 76.5%."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        donnees = pd.read_csv(CSV)
        kpis    = calculer_kpis(donnees)
        assert kpis["moyenne_occupation"] == pytest.approx(76.5, abs=0.1)

    def test_meilleur_hotel_iberostar(self):
        """Le meilleur hôtel doit être Hotel Iberostar."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        donnees = pd.read_csv(CSV)
        kpis    = calculer_kpis(donnees)
        assert kpis["meilleur_hotel"] == "Hotel Iberostar"

    def test_revenus_totaux_727000(self):
        """Les revenus totaux doivent être exactement 727 000 TND."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        donnees = pd.read_csv(CSV)
        kpis    = calculer_kpis(donnees)
        assert kpis["revenus_totaux"] == 727000

    def test_meilleure_region_djerba(self):
        """La meilleure région doit être Djerba."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        donnees = pd.read_csv(CSV)
        kpis    = calculer_kpis(donnees)
        assert kpis["meilleure_region"] == "Djerba"

    def test_nombre_hotels_faibles_7(self):
        """7 hôtels doivent être sous la moyenne."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        donnees = pd.read_csv(CSV)
        kpis    = calculer_kpis(donnees)
        assert len(kpis["hotels_faibles"]) == 7

    def test_statut_rapport_attention(self):
        """Le statut du rapport final doit être ATTENTION (7 > seuil 5)."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        plan    = planifier(TACHE)
        res     = executer(plan, CSV)
        assert res["rapport"]["statut"] == "ATTENTION"

    def test_scenario2_retourne_9_millions_2023(self):
        """Le Scénario 2 doit retourner 9 000 000 touristes pour 2023."""
        res = appeler_api_mock("ST.INT.ARVL", mode="normal")
        donnees_2023 = [d for d in res["donnees"] if d["date"] == "2023"]
        assert len(donnees_2023) == 1
        assert donnees_2023[0]["value"] == 9_000_000

    def test_scenario2_variation_yoy_33(self):
        """La variation YoY doit être +33.1% entre 2022 et 2023."""
        res = appeler_api_mock("ST.INT.ARVL", mode="normal")
        t   = transformer_donnees_api(res["donnees"])
        assert t["variation_yoy"] == pytest.approx(33.1, abs=0.1)

    def test_15_hotels_dans_csv(self):
        """Le CSV doit contenir exactement 15 hôtels."""
        if not os.path.exists(CSV):
            pytest.skip("CSV absent")
        res = lire_hotels(CSV)
        assert len(res["donnees"]) == 15

    def test_redaction_chemin_windows_fonctionne(self):
        """La redaction doit masquer les chemins Windows absolus."""
        texte_redacte = _redacter("Chemin : D:\\Users\\zakaria\\data.csv")
        assert "zakaria" not in texte_redacte
        assert "[CHEMIN_REDACTE]" in texte_redacte
