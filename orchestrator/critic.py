#C'est lui qui dit : "OK, ce rapport est bon" ou "Non, il y a un problème".


def critiquer(rapport):

    print("\nCritic : je vérifie le rapport...")
    erreurs = []

    # Vérification 1 — Le rapport existe
    if rapport is None:
        print("Rapport vide !")
        return False

    # Vérification 2 — Les champs obligatoires existent
    champs_obligatoires = ["date", "secteur", "resume", "alertes", "statut"]
    for champ in champs_obligatoires:
        if champ not in rapport:
            erreurs.append(f"Champ manquant : {champ}")

    # Vérification 3 — Le taux d'occupation est raisonnable
    taux = rapport["resume"]["taux_occupation_moyen"]
    taux_valeur = float(taux.replace("%", ""))
    if taux_valeur < 0 or taux_valeur > 100:
        erreurs.append(f"Taux d'occupation invalide : {taux}")

    # Vérification 4 — Les revenus sont positifs
    revenus = rapport["resume"]["revenus_totaux_TND"]
    if revenus <= 0:
        erreurs.append(f"Revenus invalides : {revenus}")

    # Résultat
    if erreurs:
        print(f"{len(erreurs)} erreur(s) trouvée(s) :")
        for e in erreurs:
            print(f"      - {e}")
        return False
    else:
        print("Rapport validé ! Tout est correct.")
        return True


# TEST
if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from orchestrator.planner import planifier
    from orchestrator.executor import executer

    plan = planifier("rapport_hotels")
    rapport = executer(plan, "data_synthetic/hotels_tunisie.csv")
    succes = critiquer(rapport)

    if succes:
        print("\nMission accomplie !")
    else:
        print("\nMission échouée !")