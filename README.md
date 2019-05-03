# garage2osm
Extracts approved auto repair garages from the Norwegian Public Roads Administration and generates OSM file

### Usage

<code>garage2osm [county id]</code>

### Notes

* The Norwegian Public Roads Administration (Statens Vegvesen) approves garages in various categories in order to secure quality of car repairs and improve traffic safety
* This program loads the current list of approved garages and produces an OSM file for a given county (two digit county id, e.g. *"50"* for Trøndelag county).
* The produced file wil be named *"garages_50.osm"* (for Trøndelag)
* Tagging is attempted based on cues in the name of the garage and on the approval category, e.g. car repair, motorcycle, tyres etc. This tagging needs manual verification.
* The coordinates are based on geocoding, because the source data only contains the post address of the garaage
  * Each address is geocodes using the API of the cadastral register at Kartverket.
  * Due to several mistakes in the source data, a number of addresses will not geocode. These garages will get a (0,0) coordinate and a *GEOCODE=yes* tag.
  * If the produced file is subsequently processed with [geocode2osm](https://github.com/osmno/geocode2osm) it will get more sophisticated geocoding using a number of techniques, and most addresses will be geocoded to the closest possible location.
* A pre-run OSM file is provided [here](https://drive.google.com/drive/folders/1JkIIUxwNh9WZx4lzt7rmqCwa6G_p9MAB?usp=sharing)

### References

* [Statens Vegvesen: Verkstedsregisteret](https://www.vegvesen.no/kjoretoy/Eie+og+vedlikeholde/finn-godkjent-verksted)
* [geocode2osm](https://github.com/osmno/geocode2osm)
* [Available OSM file](https://drive.google.com/drive/folders/1JkIIUxwNh9WZx4lzt7rmqCwa6G_p9MAB?usp=sharing)
