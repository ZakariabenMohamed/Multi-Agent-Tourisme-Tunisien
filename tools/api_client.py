import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

# Liste blanche des sites autorisés
SITES_AUTORISES = ["api.worldbank.org"]

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def appeler_api(url):

    print(f"Appel API : {url}")

    # Vérifier que le site est autorisé
    site_autorise = any(site in url for site in SITES_AUTORISES)
    if not site_autorise:
        return {"erreur": f"Site non autorisé : {url}"}

    # Appeler l'API avec timeout
    try:
        response = httpx.get(url, timeout=10)

        if response.status_code == 200:
            print("Réponse reçue avec succès")
            return {"succes": True, "donnees": response.json()}

        elif response.status_code == 429:
            print("Trop de requêtes, on réessaie...")
            raise Exception("Rate limit 429")

        else:
            return {"erreur": f"Erreur HTTP : {response.status_code}"}

    except Exception as e:
        print(f"Erreur : {str(e)}")
        raise


# TEST
if __name__ == "__main__":

    # URL Banque Mondiale — arrivées touristiques en Tunisie
    url = "https://api.worldbank.org/v2/country/TN/indicator/ST.INT.ARVL?format=json&mrv=5"

    resultat = appeler_api(url)

    if "erreur" in resultat:
        print(f"{resultat['erreur']}")
    else:
        donnees = resultat["donnees"]
        print("\nDonnées tourisme Tunisie (Banque Mondiale) :")
        for item in donnees[1]:
            if item["value"] is not None:
                print(f"   {item['date']} : {int(item['value']):,} touristes")