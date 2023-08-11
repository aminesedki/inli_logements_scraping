## Script scraping site demande logements inli
Ce script permet de chercher des logements disponibles dans le site inli https://www.inli.fr/ selon quatres critéres principals :

    1- Le nombre de condidats maximale (variable CONDIDATS_LIMIT)

    2- Une superficie minimal (variable AREA_MIN)

    3- Une superficie maximal (variable AREA_MAX)

    4- Le prix du loyer maximal (variable PRICE_MAX)






###  Utilisation du script


Afin d'utiliser le script, il faut :

    installer les librairies nécessaires via la commande : pip install -r requirements.txt

    lancer le script avec la commande: python inli_async.py

L'intervalle de scraping par defaut est à 60 seconds, il est conseillé d'utiliser une valeurs superieur à 20 seconds pour eviter un eventuel blocage


### Remarques : 

    Dernier test du script : le 11/08/2023
    
    Temps moyen d'un scraping de tout le site est de 10 seconds
    
    Si un proxy est nécessaire il faut le renseigner dans les variables HTTP_PROXY & HTTPS_PROXY et mettre USE_PROXY=True 