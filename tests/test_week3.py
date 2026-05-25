"""
tests/test_week3.py — Tests unitaires Semaine 3
Couvre :
  - Mock API (modes normal / 429 / timeout / empty)
  - Transformer (transformation + rapport Scénario 2)
  - DP Cache (hit / miss / stats)
  - Logger enrichi (redaction, durée, niveau)
  - Concurrence (isolation des runs)

Lancer avec : pytest tests/test_week3.py -v
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.mock_api       import appeler_api_mock
from tools.transformer    import transformer_donnees_api, generer_rapport_scenario2
from orchestrator.dp_cache import (obtenir_plan_cache, sauvegarder_plan_cache,
                                    rapport_cache, vider_cache)
from orchestrator.logger   import journaliser, lire_journal, _redacter


# ══════════════════════════════════════════════════════════════════════════════
# 1. Tests — Mock API
# ══════════════════════════════════════════════════════════════════════════════

class TestMockAPI:

    def test_mode_normal_retourne_succes(self):
        res = appeler_api_mock("ST.INT.ARVL", mode="normal")
        assert res.get("succes") is True
        assert "donnees" in res
        assert len(res["donnees"]) > 0

    def test_mode_normal_5_annees(self):
        res = appeler_api_mock("ST.INT.ARVL", mode="normal")
        assert len(res["donnees"]) == 5

    def test_mode_normal_code_http_200(self):
        res = appeler_api_mock("ST.INT.ARVL", mode="normal")
        assert res["code_http"] == 200

    def test_mode_429_retourne_erreur(self):
        res = appeler_api_mock("ST.INT.ARVL", mode="rate_429")
        assert "erreur" in res
        assert res["erreur"] == "rate_limit_429"
        assert res["code_http"] == 429

    def test_mode_timeout_retourne_erreur(self):
        res = appeler_api_mock("ST.INT.ARVL", mode="timeout")
        assert "erreur" in res
        assert res["erreur"] == "timeout"

    def test_mode_empty_liste_vide(self):
        res = appeler_api_mock("ST.INT.ARVL", mode="empty")
        assert res.get("succes") is True
        assert res["donnees"] == []

    def test_donnees_ont_les_bons_champs(self):
        res = appeler_api_mock("ST.INT.ARVL", mode="normal")
        for d in res["donnees"]:
            assert "date" in d
            assert "value" in d
            assert "indicator" in d


# ══════════════════════════════════════════════════════════════════════════════
# 2. Tests — Transformer
# ══════════════════════════════════════════════════════════════════════════════

class TestTransformer:

    def _donnees_valides(self):
        return [
            {"date": "2023", "value": 9_000_000, "indicator": "ST.INT.ARVL", "country": "TN"},
            {"date": "2022", "value": 6_760_000, "indicator": "ST.INT.ARVL", "country": "TN"},
            {"date": "2021", "value": 2_289_000, "indicator": "ST.INT.ARVL", "country": "TN"},
        ]

    def test_transformer_retourne_valeur_recente(self):
        t = transformer_donnees_api(self._donnees_valides())
        assert t["valeur_recente"] == 9_000_000
        assert t["annee_recente"] == "2023"

    def test_transformer_calcule_variation_yoy(self):
        t = transformer_donnees_api(self._donnees_valides())
        assert t["variation_yoy"] is not None
        assert isinstance(t["variation_yoy"], float)

    def test_transformer_calcule_tendance(self):
        t = transformer_donnees_api(self._donnees_valides())
        assert t["tendance"] in ["hausse", "baisse", "stable"]

    def test_transformer_donnees_vides_retourne_erreur(self):
        t = transformer_donnees_api([])
        assert "erreur" in t

    def test_rapport_scenario2_structure_complete(self):
        t = transformer_donnees_api(self._donnees_valides())
        r = generer_rapport_scenario2(t)
        for champ in ["date", "secteur", "indicateur", "donnees_api", "statut"]:
            assert champ in r

    def test_rapport_scenario2_statut_ok(self):
        t = transformer_donnees_api(self._donnees_valides())
        r = generer_rapport_scenario2(t)
        assert r["statut"] == "OK"

    def test_rapport_scenario2_erreur_si_donnees_vides(self):
        t = transformer_donnees_api([])
        r = generer_rapport_scenario2(t)
        assert r["statut"] == "ERREUR_API"


# ══════════════════════════════════════════════════════════════════════════════
# 3. Tests — DP Cache
# ══════════════════════════════════════════════════════════════════════════════

class TestDPCache:

    def setup_method(self):
        vider_cache()

    def _plan(self):
        return [{"etape": 1, "outil": "file_reader", "description": "Lire"},
                {"etape": 2, "outil": "calculator",  "description": "Calculer"},
                {"etape": 3, "outil": "reporter",     "description": "Rapport"}]

    def test_premier_appel_est_miss(self):
        _, depuis_cache, _ = obtenir_plan_cache("rapport_hotels", [])
        assert depuis_cache is False

    def test_deuxieme_appel_est_hit(self):
        sauvegarder_plan_cache("rapport_hotels", [], self._plan(), duree_calcul_ms=10.0)
        _, depuis_cache, _ = obtenir_plan_cache("rapport_hotels", [])
        assert depuis_cache is True

    def test_cle_differente_si_etapes_echouees_differentes(self):
        sauvegarder_plan_cache("rapport_hotels", [], self._plan(), 10.0)
        p, depuis_cache, _ = obtenir_plan_cache("rapport_hotels", ["file_reader"])
        assert depuis_cache is False

    def test_stats_hits_et_misses(self):
        obtenir_plan_cache("rapport_hotels", [])         # miss
        sauvegarder_plan_cache("rapport_hotels", [], self._plan(), 10.0)
        obtenir_plan_cache("rapport_hotels", [])         # hit
        stats = rapport_cache()
        assert stats["cache_hits"]   == 1
        assert stats["cache_misses"] == 1

    def test_taux_hit_correct(self):
        sauvegarder_plan_cache("rapport_hotels", [], self._plan(), 10.0)
        obtenir_plan_cache("rapport_hotels", [])   # hit
        obtenir_plan_cache("rapport_hotels", [])   # hit
        stats = rapport_cache()
        assert stats["taux_hit_pct"] == 100.0

    def test_vider_cache_remet_a_zero(self):
        sauvegarder_plan_cache("rapport_hotels", [], self._plan(), 10.0)
        vider_cache()
        stats = rapport_cache()
        assert stats["entrees_en_cache"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# 4. Tests — Logger enrichi + Redaction
# ══════════════════════════════════════════════════════════════════════════════

class TestLoggerWeek3:

    def test_redaction_chemin_windows(self):
        result = _redacter("Fichier : D:\\Users\\zakaria\\data.csv")
        assert "D:\\" not in result
        assert "[CHEMIN_REDACTE]" in result

    def test_redaction_token(self):
        result = _redacter("Authorization token=abc123xyz")
        assert "abc123xyz" not in result

    def test_journal_contient_duree_ms(self, tmp_path):
        os.environ["LOGS_DIR_OVERRIDE"] = str(tmp_path)
        import orchestrator.logger as lg
        ancien_dir = lg.LOGS_DIR
        lg.LOGS_DIR = str(tmp_path)

        lg.journaliser("run_test_dur", "step_1", "test", "OK", {}, duree_ms=42.5)
        entrees = lg.lire_journal("run_test_dur")
        lg.LOGS_DIR = ancien_dir

        assert len(entrees) == 1
        assert entrees[0]["duree_ms"] == 42.5

    def test_journal_contient_niveau(self, tmp_path):
        import orchestrator.logger as lg
        ancien_dir = lg.LOGS_DIR
        lg.LOGS_DIR = str(tmp_path)

        lg.journaliser("run_test_niv", "step_1", "test", "ERREUR", {}, niveau="ERROR")
        entrees = lg.lire_journal("run_test_niv")
        lg.LOGS_DIR = ancien_dir

        assert entrees[0]["niveau"] == "ERROR"


# ══════════════════════════════════════════════════════════════════════════════
# 5. Tests — Concurrence
# ══════════════════════════════════════════════════════════════════════════════

class TestConcurrence:

    CSV = "data_synthetic/hotels_tunisie.csv"

    def test_stress_test_retourne_rapport(self):
        if not os.path.exists(self.CSV):
            pytest.skip("CSV absent")
        from orchestrator.concurrency import stress_test_concurrence
        rapport = stress_test_concurrence(self.CSV, nb_runs=2, max_workers=2)
        assert "nb_runs" in rapport
        assert "taux_succes_pct" in rapport

    def test_isolation_verifiee(self):
        if not os.path.exists(self.CSV):
            pytest.skip("CSV absent")
        from orchestrator.concurrency import stress_test_concurrence
        rapport = stress_test_concurrence(self.CSV, nb_runs=2, max_workers=2)
        assert rapport["isolation_ok"] is True
        assert rapport["leakage_detecte"] is False

    def test_tous_les_runs_reussissent(self):
        if not os.path.exists(self.CSV):
            pytest.skip("CSV absent")
        from orchestrator.concurrency import stress_test_concurrence
        rapport = stress_test_concurrence(self.CSV, nb_runs=2, max_workers=2)
        assert rapport["nb_succes"] == rapport["nb_runs"]
