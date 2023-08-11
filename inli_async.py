from datetime import datetime as dt
import re, time
from bs4 import BeautifulSoup
import aiohttp, asyncio

# Interval de temps pour chaque (valeur min à mettre 30 ou plus)
SCRAPING_INTERVAL: int = 60


PRICE_MAX: int = 820 # prix max ou budget
AREA_MIN: int = 35 # superficie min de l'appartement
AREA_MAX: int = 50 # superficie max de l'appartement
CONDIDATS_LIMIT : int = 50 # nombre de condidiats max pour le bien
APPARTS_CNT: int = 0 # compteurs d'apparatements trouvés (variable globale)

# reference des departement ile de france dans l'url de recherche
REGIONS_STR= [

    "seine-et-marne-departement_d:77", "yvelines-departement_d:78",
    "essonne-departement_d:91", "hauts-de-seine-departement_d:92",
    "seine-saint-denis-departement_d:93", "val-de-marne-departement_d:94",
    "val-d-oise-departement_d:95"

]
BASE_URL: str = "https://www.inli.fr" # url de base

# url de recherche par departement
SEARCH_URL: str = "/locations/offres/{depart}/?price_min=0&price_max={price_max}&area_min={area_min}&area_max={area_max}&room_min=0&room_max=5&bedroom_min=0&bedroom_max=5&lat=&lng=&zoom=&radius="

HTTP_PROXY = ""
HTTPS_PROXY = ""

# os.environ['HTTP_PROXY'] = HTTP_PROXY 
# os.environ['HTTPS_PROXY'] = HTTP_PROXY 

USE_PROXY: bool=False # boolean pour definir l'utilisation d'un proxy

# definir dict proxies si USE_PROXY est True sinon le laisser vide
proxies: dict={"http": HTTP_PROXY, "https": HTTPS_PROXY} if USE_PROXY else {}


def add_to_apparts_cnt(cnt: int):
    """
    Cette fonction permet d'ajouter le nombre cnt a la variable globale APPARTS_CNT 
    """ 
    global APPARTS_CNT
    APPARTS_CNT+=cnt

   

async def get_depart_search_result_pages(depart_str)->list:
    """
    Cette fonction s'attend a un elment str d'un departement avec son identifiant (voir REGIONS_STR et SEARCH_URL)
    elle retourne la liste d'urls vers les toutes les pages trouvés selon le deppartement 
    """
    URL = BASE_URL + SEARCH_URL.format(depart=depart_str, price_max=PRICE_MAX, area_min=AREA_MIN, area_max=AREA_MAX)
    pages_urls = [{"page":1, "departement_nb": depart_str.split(":")[1], "page_url": URL }]
    async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(URL, proxy=HTTP_PROXY) as resp:
                body = await resp.text()
                soup = BeautifulSoup(body, 'html5lib')
                nb_apparts = soup.find("ui-list-filter-bien") # filtrer la partie html contenue dans la div id='ui-list-filter-bien'
                nb_apparts = int(re.search(r'\d+',nb_apparts['label']).group()) if nb_apparts else 0 # trouver le chiffre contenu dans la div id='label'
                add_to_apparts_cnt(nb_apparts) # ajouter le nombre d'appartement a la variable globale
                pag_nav = soup.find("nav", {"class": "pagination-holder"}) # filtrer la div de pagination
                # si une div de pafination existe
                if pag_nav:
                    # recuperer tous les urls dans chaque balise a
                    pages_hrefs = list(set([a['href'] for a in pag_nav.find_all('a', href=True)]))
                    # stocker les infos de chaque page dans un dict et l'ajouter dans la liste des pages
                    for i, page_href in enumerate(pages_hrefs):
                        pages_urls.append({"page":i+2, "departement_nb": depart_str.split(":")[1], "page_url":  BASE_URL+page_href})
    
    return pages_urls


async def get_page_apparts_hrefs(page_def: dict) -> list:
    """
    Cette fonction retourne le href sans l'url de base !
    Elle permet de recuperer les infos des appartement d'une page de recherche
    """
    biens_hrefs = []
    async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(page_def.get("page_url"), proxy=HTTP_PROXY) as resp:
                body = await resp.text()
                soup = BeautifulSoup(body, 'html5lib')
                # recuperer tous les hrefs des appartements
                appart_hrefs = [ div.find("a")['href'] for div in soup.find_all("div", {"class": "thumbnail"})]
                
                # supprimer les hrefs duplicés
                filtred_hrefs = list(set(appart_hrefs))
                
                # pour chaque href 
                for href in filtred_hrefs:
                    # recuperer les infos de l'appartement
                    tmpdict: dict = { 
                                "appart_href": href,
                                "commune": get_commune_from_href_url(href),
                                "appart_ref_id": get_apart_ref_from_href_url(href),
                                "appart_url": BASE_URL + href
                    }
                    # ajouter les infos au dict de difinition de la page
                    biens_hrefs.append({**page_def, **tmpdict})
    
    return biens_hrefs


def get_commune_from_href_url(url: str) -> str:
    """
    Cette fonction s'attend au href uniquement sans l'url de base
    elle permet de recuperer le nom de la commune dans l'url en entrée
    """
    return url.split("/")[3]

def get_apart_ref_from_href_url(url: str) -> str:
    """
    Cette fonction s'attend au href uniquement sans l'url de base
    elle permet de recuperer la reference d'un appartement dans l'url en entrée
    """
    return url.split("/")[4]

async def add_appart_condidature_nb(appart_def: dict) -> dict:
    """
    Cette fonction permet de recuperer le nbre de condidature pour un appartement
    """
    condidature_nb: int = None
    async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(appart_def.get("appart_url"), proxy=HTTP_PROXY) as resp:
                body = await resp.text()
                soup = BeautifulSoup(body, 'html5lib')
                if soup:
                    condidature_nb_span=soup.find("span", {"class": "page-bien__nb-deposit__text"})
                    available = soup.body.findAll(string="Ça m’intéresse !")
                    
                    if available:
                        condidature_nb = int(re.search(r'\d+', condidature_nb_span.text).group()) if condidature_nb_span else 0
    
    return {**appart_def, **{"condidatures_nb":condidature_nb}}


async def get_data():
    """
    Cette fonction permet d'executer le code de récuperation des données étape par étape puis afficher le resultat
    """
    # 1- Récupérer les urls vers les pages
    pages = []; tasks = [] 
    for region in REGIONS_STR: tasks.append(asyncio.create_task(get_depart_search_result_pages(region)))
    results = await asyncio.gather(*tasks)
    pages = [item for sublist in results for item in sublist]
    
    # 2- Récupérer les infos des appartements de chaque page
    apparts = []; tasks = []
    for page_url in pages: tasks.append(asyncio.create_task(get_page_apparts_hrefs(page_url)))
    results = await asyncio.gather(*tasks)
    apparts = [item for sublist in results for item in sublist]

    # 3- Récupérer le nombre de condidature pour chaque appartement
    apparts_all_data = []; tasks = [] 
    for appart in apparts: tasks.append(asyncio.create_task(add_appart_condidature_nb(appart)))
    results = await asyncio.gather(*tasks)
    apparts_all_data = [item for item in results]
    
    # Filtrer les données qui ont un nombre de condidature non definit et superieur à la limite voulue 
    data = [item for item in apparts_all_data 
                    if item.get('condidatures_nb') is not None 
                        and item.get('condidatures_nb') < CONDIDATS_LIMIT
    ]

    sorted_data = sorted(data, key=lambda d: d['condidatures_nb']) # ordonner le resultat par le nbr croissant de condidature
    show_results(sorted_data) # afficher le resultat


def show_results(data: list):
    """
    Cette fonction permet d'afficher le resultat de la recherche
    """
    line_str = "Nb Condidats : {nb_cond} | Departement : {depar} {depar_nb} | Commune : {commune} | Condidature URL : {url}"
    global APPARTS_CNT
    now_date_str: str = dt.strftime(dt.now(), "le %d-%m-%Y à %H:%M:%S")
    print('----------------------------------------------------------------------------------------')
    print(f"Appartements trouvés {now_date_str} : {APPARTS_CNT} | Appartements filtrés : {len(data)} ")
    for item in data:
        print(
            
            line_str.format(
                                nb_cond=item.get("condidatures_nb"), 
                                depar=item.get("departement_name"), 
                                depar_nb=item.get("departement_nb"), 
                                commune=item.get("commune"),
                                url=item.get("appart_url")
            )
        
        )
    print('----------------------------------------------------------------------------------------')

# fonction main
async def main():
    start_time = time.time()
    await get_data()
    print(f"{(time.time() - start_time):.2f} seconds")

if __name__ == "__main__":
    try:
        while True:
            
            asyncio.run(main()) # lancer le scraping
            time.sleep(SCRAPING_INTERVAL) # pause d'un intervalle SCRAPING_INTERVAL seconds
    
    # arreter la boucle infinie si ctrl + c
    except KeyboardInterrupt: print('Inli Scraping loop interrupted!')
    
    
    