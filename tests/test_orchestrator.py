"""
Tests unitaires — Projet DS2 : Tourisme Tunisien
Couvre : file_reader, calculator, reporter, critic, planner
Lancer avec : pytest tests/test_orchestrator.py -v
"""

import sys
import os
import pytest
import pandas as pd

# ── Ajout du chemin racine pour les imports ───────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.file_reader import lire_hotels
from tools.calculator import calculer_kpis
from tools.reporter import generer_rapport
from orchestrator.critic import critiquer
from orchestrator.planner import planifier


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures partagées
# ══════════════════════════════════════════════════════════════════════════════

CSV_REEL = "data_synthetic/hotels_tunisie.csv"

@pytest.fixture
def donnees_valides():
    """DataFrame minimal avec toutes les colonnes requises."""
    return pd.DataFrame({
        "hotel":             ["Hotel A", "Hotel B", "Hotel C"],
        "region":            ["Tunis",   "Sousse",  "Djerba"],
        "taux_occupation_pct": [80,       60,        90],
        "revenus_TND":       [50000,     30000,     70000],
        "nb_touristes":      [400,       250,       550],
        "nb_chambres":       [200,       150,       300],
        "saison":            ["ete",     "hiver",   "ete"],
    })

@pytest.fixture
def kpis_valides(donnees_valides):
    return calculer_kpis(donnees_valides)

@pytest.fixture
def rapport_valide(kpis_valides):
    return generer_rapport(kpis_valides)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Tests — file_reader
# ══════════════════════════════════════════════════════════════════════════════

class TestFileReader:

    def test_lecture_csv_reel_succes(self):
        """Le fichier CSV réel doit se lire sans erreur."""
        if not os.path.exists(CSV_REEL):
            pytest.skip(f"Fichier absent : {CSV_REEL}")

        resultat = lire_hotels(CSV_REEL)
        assert "erreur" not in resultat
        assert "donnees" in resultat
        assert isinstance(resultat["donnees"], pd.DataFrame)

    def test_lecture_csv_reel_nb_lignes(self):
        """Le fichier CSV réel contient 15 hôtels."""
        if not os.path.exists(CSV_REEL):
            pytest.skip(f"Fichier absent : {CSV_REEL}")

        resultat = lire_hotels(CSV_REEL)
        assert len(resultat["donnees"]) == 15

    def test_lecture_csv_reel_colonnes(self):
        """Le fichier CSV réel possède toutes les colonnes attendues."""
        if not os.path.exists(CSV_REEL):
            pytest.skip(f"Fichier absent : {CSV_REEL}")

        colonnes_attendues = {
            "hotel", "region", "taux_occupation_pct",
            "revenus_TND", "nb_touristes", "nb_chambres", "saison"
        }
        resultat = lire_hotels(CSV_REEL)
        assert colonnes_attendues.issubset(set(resultat["donnees"].columns))

    def test_lecture_fichier_inexistant(self):
        """Un fichier qui n'existe pas doit retourner une clé 'erreur'."""
        resultat = lire_hotels("fichier_qui_nexiste_pas.csv")
        assert "erreur" in resultat
        assert "donnees" not in resultat

    def test_lecture_csv_temporaire(self, tmp_path):
        """Création d'un CSV temporaire et lecture."""
        chemin = tmp_path / "test.csv"
        chemin.write_text(
            "hotel,region,taux_occupation_pct,revenus_TND,nb_touristes,nb_chambres,saison\n"
            "Hotel Test,Tunis,75,40000,300,180,ete\n",
            encoding="utf-8"
        )
        resultat = lire_hotels(str(chemin))
        assert "erreur" not in resultat
        assert len(resultat["donnees"]) == 1


# ══════════════════════════════════════════════════════════════════════════════
# 2. Tests — calculator
# ══════════════════════════════════════════════════════════════════════════════

class TestCalculator:

    def test_moyenne_occupation(self, donnees_valides):
        """La moyenne d'occupation doit être (80+60+90)/3 = 76.7."""
        kpis = calculer_kpis(donnees_valides)
        assert kpis["moyenne_occupation"] == pytest.approx(76.7, abs=0.1)

    def test_meilleur_hotel(self, donnees_valides):
        """Le meilleur hôtel est celui avec le taux le plus élevé (90 → Hotel C)."""
        kpis = calculer_kpis(donnees_valides)
        assert kpis["meilleur_hotel"] == "Hotel C"

    def test_revenus_totaux(self, donnees_valides):
        """Les revenus totaux doivent être 50000 + 30000 + 70000 = 150000."""
        kpis = calculer_kpis(donnees_valides)
        assert kpis["revenus_totaux"] == 150000

    def test_meilleure_region(self, donnees_valides):
        """La meilleure région est Djerba (revenus 70000 > Tunis 50000 > Sousse 30000)."""
        kpis = calculer_kpis(donnees_valides)
        assert kpis["meilleure_region"] == "Djerba"

    def test_hotels_faibles(self, donnees_valides):
        """Hotel B (60%) est sous la moyenne (76.7%) → doit apparaître dans hotels_faibles."""
        kpis = calculer_kpis(donnees_valides)
        assert "Hotel B" in kpis["hotels_faibles"]
        assert "Hotel A" not in kpis["hotels_faibles"]
        assert "Hotel C" not in kpis["hotels_faibles"]

    def test_kpis_csv_reel(self):
        """Les KPIs calculés sur le CSV réel doivent être dans des plages raisonnables."""
        if not os.path.exists(CSV_REEL):
            pytest.skip(f"Fichier absent : {CSV_REEL}")
        donnees = pd.read_csv(CSV_REEL)
        kpis = calculer_kpis(donnees)
        assert 0 <= kpis["moyenne_occupation"] <= 100
        assert kpis["revenus_totaux"] > 0
        assert isinstance(kpis["hotels_faibles"], list)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Tests — critic
# ══════════════════════════════════════════════════════════════════════════════

class TestCritic:

    def test_rapport_valide_accepte(self, rapport_valide):
        """Un rapport correct doit être validé (True)."""
        assert critiquer(rapport_valide) is True

    def test_rapport_none_rejete(self):
        """None doit être rejeté (False)."""
        assert critiquer(None) is False

    def test_champ_manquant_rejete(self, rapport_valide):
        """Un rapport sans le champ 'statut' doit être rejeté."""
        del rapport_valide["statut"]
        assert critiquer(rapport_valide) is False

    def test_taux_invalide_rejete(self, rapport_valide):
        """Un taux d'occupation de 150% doit être rejeté."""
        rapport_valide["resume"]["taux_occupation_moyen"] = "150%"
        assert critiquer(rapport_valide) is False

    def test_revenus_negatifs_rejetes(self, rapport_valide):
        """Des revenus négatifs doivent être rejetés."""
        rapport_valide["resume"]["revenus_totaux_TND"] = -1000
        assert critiquer(rapport_valide) is False

    def test_revenus_nuls_rejetes(self, rapport_valide):
        """Des revenus nuls doivent être rejetés."""
        rapport_valide["resume"]["revenus_totaux_TND"] = 0
        assert critiquer(rapport_valide) is False

    def test_champ_date_manquant(self, rapport_valide):
        """Un rapport sans 'date' doit être rejeté."""
        del rapport_valide["date"]
        assert critiquer(rapport_valide) is False


# ══════════════════════════════════════════════════════════════════════════════
# 4. Tests — planner
# ══════════════════════════════════════════════════════════════════════════════

class TestPlanner:

    def test_plan_rapport_hotels_nb_etapes(self):
        """Le plan 'rapport_hotels' doit contenir exactement 3 étapes."""
        plan = planifier("rapport_hotels")
        assert len(plan) == 3

    def test_plan_rapport_hotels_outils(self):
        """Les 3 outils doivent être file_reader, calculator, reporter (dans cet ordre)."""
        plan = planifier("rapport_hotels")
        outils = [etape["outil"] for etape in plan]
        assert outils == ["file_reader", "calculator", "reporter"]

    def test_plan_rapport_hotels_numerotation(self):
        """Les étapes doivent être numérotées 1, 2, 3."""
        plan = planifier("rapport_hotels")
        numeros = [etape["etape"] for etape in plan]
        assert numeros == [1, 2, 3]

    def test_plan_tache_inconnue(self):
        """Une tâche inconnue doit retourner une liste vide."""
        plan = planifier("tache_inexistante")
        assert plan == []

    def test_plan_champs_requis(self):
        """Chaque étape doit contenir 'etape', 'outil', 'description'."""
        plan = planifier("rapport_hotels")
        for etape in plan:
            assert "etape" in etape
            assert "outil" in etape
            assert "description" in etape
