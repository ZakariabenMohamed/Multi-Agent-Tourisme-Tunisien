import pandas as pd
import os

def lire_hotels(chemin_fichier):
    
    # Vérifier que le fichier existe
    if not os.path.exists(chemin_fichier):
        return {"erreur": f"Fichier introuvable : {chemin_fichier}"}
    
    # Lire le fichier CSV
    try:
        donnees = pd.read_csv(chemin_fichier)
        print(f"Fichier lu avec succès : {len(donnees)} hôtels trouvés")
        return {"succes": True, "donnees": donnees}
    
    except Exception as e:
        return {"erreur": f"Impossible de lire le fichier : {str(e)}"}


# TEST — pour vérifier que ça marche
if __name__ == "__main__":
    resultat = lire_hotels("data_synthetic/hotels_tunisie.csv")
    
    if "erreur" in resultat:
        print(f"Erreur : {resultat['erreur']}")
    else:
        print(resultat["donnees"])