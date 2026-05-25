"""
tests/test_week2.py — Tests unitaires Semaine 2
Couvre :
  - Planner avec backtracking
  - Executor avec validation de schéma
  - Failure injector
  - Boucle de retry

Lancer avec : pytest tests/test_week2.py -v
"""

import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orchestrator.planner          import planifier
from orchestrator.executor         import executer, _valider_schema_entree_csv, _valider_schema_sortie_donnees, _valider_schema_sortie_kpis
from orchestrator.failure_injector import injecter_panne, PANNES_DISPONIBLES

CSV_REEL = "data_synthetic/hotels_tunisie.csv"


# ══════════════════════════════════════════════════════════════════════════════
# 1. Tests — Planner avec backtracking
# ══════════════════════════════════════════════════════════════════════════════

class TestPlannerBacktracking:

    def test_plan_normal_3_etapes(self):
        """Plan normal sans backtracking = 3 étapes."""
        plan = planifier("rapport_hotels")
        assert len(plan) == 3

    def test_backtracking_file_reader_echoue(self):
        """Si file_reader échoue et pas d'alternatif → plan vide."""
        plan = planifier("rapport_hotels", etapes_echouees=["file_reader"])
        assert plan == []

    def test_backtracking_calculator_echoue(self):
        """Si calculator échoue et pas d'alternatif → plan vide."""
        plan = planifier("rapport_hotels", etapes_echouees=["calculator"])
        assert plan == []

    def test_backtracking_reporter_echoue(self):
        """Si reporter échoue et pas d'alternatif → plan vide."""
        plan = planifier("rapport_hotels", etapes_echouees=["reporter"])
        assert plan == []

    def test_tache_inconnue_retourne_liste_vide(self):
        """Tâche inconnue → liste vide."""
        plan = planifier("tache_inconnue")
        assert plan == []

    def test_plan_sans_echec_retourne_outils_corrects(self):
        """Sans échec, les outils sont dans le bon ordre."""
        plan = planifier("rapport_hotels", etapes_echouees=[])
        outils = [e["outil"] for e in plan]
        assert outils == ["file_reader", "calculator", "reporter"]

    def test_chaque_etape_a_les_bons_champs(self):
        """Chaque étape contient etape, outil, description."""
        plan = planifier("rapport_hotels")
        for etape in plan:
            assert "etape" in etape
            assert "outil" in etape
            assert "description" in etape


# ══════════════════════════════════════════════════════════════════════════════
# 2. Tests — Validation des schémas (Executor)
# ══════════════════════════════════════════════════════════════════════════════

class TestValidationSchema:

    def test_schema_entree_csv_valide(self):
        """Chemin CSV valide → pas d'erreur."""
        result = _valider_schema_entree_csv("data_synthetic/hotels_tunisie.csv")
        assert "erreur" not in result

    def test_schema_entree_csv_vide(self):
        """Chemin vide → erreur."""
        result = _valider_schema_entree_csv("")
        assert "erreur" in result

    def test_schema_entree_csv_pas_csv(self):
        """Fichier non-CSV → erreur."""
        result = _valider_schema_entree_csv("fichier.txt")
        assert "erreur" in result

    def test_schema_sortie_donnees_valide(self):
        """DataFrame avec toutes les colonnes → OK."""
        df = pd.DataFrame({
            "hotel": ["H1"], "region": ["Tunis"],
            "taux_occupation_pct": [80], "revenus_TND": [50000],
            "nb_touristes": [300], "nb_chambres": [150], "saison": ["ete"]
        })
        result = _valider_schema_sortie_donnees(df)
        assert "erreur" not in result

    def test_schema_sortie_donnees_colonne_manquante(self):
        """DataFrame sans 'revenus_TND' → erreur."""
        df = pd.DataFrame({
            "hotel": ["H1"], "region": ["Tunis"],
            "taux_occupation_pct": [80],
            "nb_touristes": [300], "nb_chambres": [150], "saison": ["ete"]
        })
        result = _valider_schema_sortie_donnees(df)
        assert "erreur" in result

    def test_schema_sortie_kpis_valide(self):
        """KPIs complets et valides → OK."""
        kpis = {
            "moyenne_occupation": 76.5,
            "meilleur_hotel": "Hotel A",
            "revenus_totaux": 727000,
            "meilleure_region": "Djerba",
            "hotels_faibles": ["Hotel B"]
        }
        result = _valider_schema_sortie_kpis(kpis)
        assert "erreur" not in result

    def test_schema_sortie_kpis_taux_invalide(self):
        """Taux d'occupation à 150% → erreur."""
        kpis = {
            "moyenne_occupation": 150,
            "meilleur_hotel": "Hotel A",
            "revenus_totaux": 727000,
            "meilleure_region": "Djerba",
            "hotels_faibles": []
        }
        result = _valider_schema_sortie_kpis(kpis)
        assert "erreur" in result

    def test_schema_sortie_kpis_revenus_nuls(self):
        """Revenus nuls → erreur."""
        kpis = {
            "moyenne_occupation": 70,
            "meilleur_hotel": "Hotel A",
            "revenus_totaux": 0,
            "meilleure_region": "Djerba",
            "hotels_faibles": []
        }
        result = _valider_schema_sortie_kpis(kpis)
        assert "erreur" in result


# ══════════════════════════════════════════════════════════════════════════════
# 3. Tests — Executor complet
# ══════════════════════════════════════════════════════════════════════════════

class TestExecutorWeek2:

    def test_executor_succes_csv_reel(self):
        """Executor réussit sur le CSV réel."""
        if not os.path.exists(CSV_REEL):
            pytest.skip(f"Fichier absent : {CSV_REEL}")
        plan = planifier("rapport_hotels")
        resultat = executer(plan, CSV_REEL)
        assert resultat["succes"] is True
        assert resultat["rapport"] is not None
        assert resultat["outils_echoues"] == []

    def test_executor_echoue_mauvais_chemin(self):
        """Executor échoue si le chemin est mauvais → outils_echoues contient file_reader."""
        plan = planifier("rapport_hotels")
        resultat = executer(plan, "chemin_inexistant.csv")
        assert resultat["succes"] is False
        assert "file_reader" in resultat["outils_echoues"]

    def test_executor_retourne_rapport_structure(self):
        """Le rapport retourné contient tous les champs requis."""
        if not os.path.exists(CSV_REEL):
            pytest.skip(f"Fichier absent : {CSV_REEL}")
        plan = planifier("rapport_hotels")
        resultat = executer(plan, CSV_REEL)
        rapport = resultat["rapport"]
        for champ in ["date", "secteur", "resume", "alertes", "statut"]:
            assert champ in rapport


# ══════════════════════════════════════════════════════════════════════════════
# 4. Tests — Failure Injector
# ══════════════════════════════════════════════════════════════════════════════

class TestFailureInjector:

    def test_panne_wrong_path_change_le_chemin(self):
        """wrong_path doit retourner un chemin différent de l'original."""
        chemin_original = "data_synthetic/hotels_tunisie.csv"
        chemin_modifie, _ = injecter_panne("wrong_path", chemin_original, None)
        assert chemin_modifie != chemin_original

    def test_panne_wrong_path_chemin_inexistant(self):
        """Le chemin retourné par wrong_path ne doit pas exister."""
        c, _ = injecter_panne("wrong_path", "data_synthetic/hotels_tunisie.csv", None)
        assert not os.path.exists(c)

    def test_panne_corrupt_data_supprime_colonne(self):
        """corrupt_data doit supprimer la colonne revenus_TND."""
        df = pd.DataFrame({
            "hotel": ["H"], "region": ["T"],
            "taux_occupation_pct": [80], "revenus_TND": [50000],
            "nb_touristes": [300], "nb_chambres": [150], "saison": ["ete"]
        })
        _, df_corrompu = injecter_panne("corrupt_data", "chemin.csv", df)
        assert "revenus_TND" not in df_corrompu.columns

    def test_panne_zero_revenue_force_zero(self):
        """zero_revenue doit mettre tous les revenus à 0."""
        df = pd.DataFrame({
            "hotel": ["H"], "region": ["T"],
            "taux_occupation_pct": [80], "revenus_TND": [50000],
            "nb_touristes": [300], "nb_chambres": [150], "saison": ["ete"]
        })
        _, df_modifie = injecter_panne("zero_revenue", "chemin.csv", df)
        assert (df_modifie["revenus_TND"] == 0).all()

    def test_panne_inconnue_leve_exception(self):
        """Une panne inconnue doit lever une ValueError."""
        with pytest.raises(ValueError):
            injecter_panne("panne_inexistante", "chemin.csv", None)

    def test_toutes_les_pannes_sont_documentees(self):
        """Toutes les pannes doivent avoir une description dans PANNES_DISPONIBLES."""
        for code, desc in PANNES_DISPONIBLES.items():
            assert isinstance(code, str) and len(code) > 0
            assert isinstance(desc, str) and len(desc) > 0
