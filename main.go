package main

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"example.com/inli-scraping/apart"
	"github.com/gocolly/colly"
)

const PRICE_MAX int = 1000     //  prix max ou budget
const AREA_MIN int = 35        // superficie min de l'appartement
const AREA_MAX int = 50        // superficie max de l'appartement
const CONDIDATS_LIMIT int = 50 // nombre de condidiats max pour le bien
// var APPARTS_CNT int64 = 0      // compteurs d'apparatements trouvés (variable globale)

// reference des departement ile de france dans l'url de recherche
var regions = []string{
	"seine-et-marne-departement_d:77", "yvelines-departement_d:78",
	"essonne-departement_d:91", "hauts-de-seine-departement_d:92",
	"seine-saint-denis-departement_d:93", "val-de-marne-departement_d:94",
	"val-d-oise-departement_d:95",
}

// url de base
const BASE_URL string = "https://www.inli.fr"

// url de recherche par departement
const SEARCH_URL string = "/locations/offres/%s/?price_min=0&price_max=%d&area_min=%d&area_max=%d&room_min=0&room_max=5&bedroom_min=0&bedroom_max=5&lat=&lng=&zoom=&radius="

func getRegionAparts(region string, wg *sync.WaitGroup, resultChan chan<- []apart.Apart) {

	defer wg.Done() // notifier le wait groupe global la fin de la routine
	// url de recherche
	URL := BASE_URL + fmt.Sprintf(SEARCH_URL, region, PRICE_MAX, AREA_MIN, AREA_MAX)
	regionAndNbre := strings.Split(region, ":")

	c := colly.NewCollector(colly.Async(true)) // Mode asynchrone activé
	regionAparts := []apart.Apart{}

	// afficher l'erreur si la requete echoue
	c.OnError(func(r *colly.Response, err error) {
		fmt.Println("Request URL:", r.Request.URL, "failed with response:", r, "\nError:", err)
	})

	// si element html avec le nom de la classe thumbnail__text
	c.OnHTML(".thumbnail__text", func(e *colly.HTMLElement) {
		link := e.Attr("href")
		departName := regionAndNbre[0]
		departNbre := regionAndNbre[1]
		commune := strings.Split(link, "/")[3]
		apply_url := BASE_URL + link
		apart := apart.New(departName, departNbre, commune, apply_url)
		regionAparts = append(regionAparts, apart)
	})

	c.Visit(URL)
	c.Wait() // Attendre la fin de toutes les requêtes si mode async
	resultChan <- regionAparts

}
func main() {
	start := time.Now()   // compter le temp d'execution
	var wg sync.WaitGroup // waitgroup pour attendre la fin d'execution de tous les goroutines

	resultChan := make(chan []apart.Apart) // un channel pour collecter les results

	for _, region := range regions {
		wg.Add(1)
		go getRegionAparts(region, &wg, resultChan)
	}

	// Patientez jusqu'a ce que toutes routines soient terminées
	go func() {
		wg.Wait()
		close(resultChan)
	}()

	// allouer un nombre initial pour éviter la reallocation de memoire à chaque append
	foundedAparts := make([]apart.Apart, 0, len(regions)*5)

	// grouper le resultat de chaque routine dans le tableau foundedAparts
	for results := range resultChan {

		foundedAparts = append(foundedAparts, results...)

	}

	// compter le temps d'execution
	fmt.Println(time.Since(start))

	// afficher le resultat
	for _, apart := range foundedAparts {
		apart.Show()
	}
}
