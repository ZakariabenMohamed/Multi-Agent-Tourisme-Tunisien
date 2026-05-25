#Ce fichier est l'outil qui calcule les 5 indicateurs clés (KPIs) à partir des données hôtelières.


def calculer_kpis(donnees):

    # Taux d'occupation moyen
    moyenne_occupation = donnees["taux_occupation_pct"].mean() # calcul de la moyenne du taux d'occupation en pourcentage

    # Meilleur hôtel
    meilleur_hotel = donnees.loc[donnees["taux_occupation_pct"].idxmax(), "hotel"]

    # Revenus totaux
    revenus_totaux = donnees["revenus_TND"].sum()

    # Meilleure région
    meilleure_region = donnees.groupby("region")["revenus_TND"].sum().idxmax()

    # Hôtels en dessous de la moyenne
    hotels_faibles = donnees[donnees["taux_occupation_pct"] < moyenne_occupation]["hotel"].tolist()

    kpis = {
        "moyenne_occupation": round(moyenne_occupation, 1),
        "meilleur_hotel": meilleur_hotel,
        "revenus_totaux": revenus_totaux,
        "meilleure_region": meilleure_region,
        "hotels_faibles": hotels_faibles
    }

    return kpis


# TEST
if __name__ == "__main__":
    import pandas as pd
    donnees = pd.read_csv("data_synthetic/hotels_tunisie.csv")
    kpis = calculer_kpis(donnees)

    print("KPIs du secteur touristique tunisien")
    print(f"   Taux occupation moyen  : {kpis['moyenne_occupation']}%")
    print(f"   Meilleur hôtel         : {kpis['meilleur_hotel']}")
    print(f"   Revenus totaux         : {kpis['revenus_totaux']} TND")
    print(f"   Meilleure région       : {kpis['meilleure_region']}")
    print(f"   Hôtels sous la moyenne : {kpis['hotels_faibles']}")