package apart

import "fmt"

// Apart data struct
type Apart struct {
	departement string
	depart_nb   string
	commune     string
	apply_url   string
}

// create new apart
func New(d_name, d_nbre, cmne, a_u string) Apart {

	return Apart{d_name, d_nbre, cmne, a_u}

}

// show new apart
func (a Apart) Show() {

	fmt.Printf(
		"Departement : %s / %s | Commune : %s | Condidature URL : %s\n",
		a.departement,
		a.depart_nb,
		a.commune,
		a.apply_url,
	)

}
