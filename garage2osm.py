#!/usr/bin/env python
# -*- coding: utf8

# garage2osm
# Extracts garages from Statens Vegvesen list of approved garages and produces OSM file for import/update
# Usage: python garage2osm.py [county]
# County parameter is two digit county number XX
# Writes output file to "garagess.osm"
# Reads postal/municipality codes from Posten and counties from Kartverket


import json
import cgi
import sys
import csv
import urllib
import urllib2
import re


version = "0.1.0"

header = { "User-Agent": "osm-no/garage2osm/" + version }

transform_name = {
	'OG': 'og',
	'Og': 'og',
	'DEKKMANN': 'Dekkmann',
	'DEKKTEAM': 'Dekkteam',
	'DEKKMESTEREN': 'Dekkmesteren',
	'DEKKPROFF': 'Dekkproff',
	'DEKK1': 'Dekk1',
	'VIANOR': 'Vianor',
	'MEKONOMEN': 'Mekonomen',
	'HURTIGRUTA': 'Hurtigruta',
	'AUTOGLASS': 'Autoglass',
	u'FELLESKJØPET': u'Felleskjøpet',
	'AGRI': 'Agri',
	'TESLA': 'Tesla',
	'RIIS': 'Riis',
	'MONTASJE': 'Bilglass',
	'Montasje': 'Bilglass',
	'SCANIA': 'Scania',
	'TRUCKNOR': 'Trucknor',
	'CARGLASS': 'Carglass',
	'BILGLASS': 'Bilglass',
	'SAINT-GOBAIN': 'Saint-Gobain',
	'AUTOVER': 'Autover',
	'RYDS': 'Ryds',
	'STEINSPRUTEN': 'Steinspruten',
	'BILXTRA': 'BilXtra',
	'MOTORS': '',
	'NORWAY': '',
	'NORGE': '',
	'NORSK': '',
	'AUTO': 'Auto',
	'CARAVAN': 'Caravan',
	'SERVIES': 'Services',
	'SERVICE': 'Service',
	'KAROSSERI': 'Karosseri',
	'VERKSTED': 'Verksted',
	'BILSKADE': 'Bilskade',
	'DETALJ': '',
	'DEKK': 'Dekk',
	'DELER': 'Deler',
	'Mc': 'MC',
	'Avdeling': '',
	'avdeling': '',
	'AVD.': '',
	'AVD': '',
	'Avd.': '',
	'avd.': '',
	'Avd': '',
	'avd': '',
	'AS': '',
	'As': '',
	'As.': '',
	'as': '',
	'as.': '',
	'A.S.': '',
	'a.s.': '',
	'A/S': '',
	'a/s': '',
	'SA': '',
	'ANS': '',
	'Ans': '',
	'ans': '',
	'DA': '',
	'Da': '',
	'da': '',
	'ASA': '',
	'Asa': ''
}

transform_address = {
	'sgate ': 's gate ',
	'sgt ': 's gate ',
	'sgt.': 's gate',
	'sveg ': 's veg ',
	'svei ': 's vei ',
	'splass ': 'splass ',
	'storg ': 's torg ',
	'storv ': 's torv ',
	'sbrygge ': 's brygge ',
	'gt ': 'gate ',
	'gt.': 'gate ',
	'pl.': 'plass ',
	'pl ': 'plass ',
	'br.': 'brygge ',
	'v.': 'vei ',
	'vn.': 'veien ',
	u'è': u'é'
}



# Produce a tag for OSM file

def make_osm_line(key,value):

	global file

	if value:
		encoded_value = cgi.escape(value.encode('utf-8'),True)
		file.write ('    <tag k="' + key + '" v="' + encoded_value + '" />\n')


# Output message

def message (line):

	sys.stdout.write (line)
	sys.stdout.flush()


# Concatenate address line

def get_address(street, house_number, postal_code, city):

	address = street

	if house_number:
		address = address + " " + house_number

	if address:
		address = address + ", "

	if postal_code:
		address = address + postal_code + " "

	if city:
		address = address + city

	return address.strip()


# Geocoding with Kartverket Matrikkel/Vegnavn REST service

def geocode (street, house_number, house_letter, city, municipality):

#	time.sleep(1)

	if house_number:

		if street[-1] == "-":  # Avoid Kartverket bug
			street = street[0: len(street) - 1]

		url = "https://ws.geonorge.no/adresser/v1/sok?sok=%s&nummer=%s" % (urllib.quote(street.encode('utf-8')), house_number)

		if house_letter:
			url += "&bokstav=%s" % house_letter

		if municipality:
			url += "&kommunenummer=%s" % municipality
		else:
			url += "&poststed=%s" % urllib.quote(city.encode('utf-8'))

		url += "&treffPerSide=10"

		request = urllib2.Request(url, headers=header)
		file = urllib2.urlopen(request)
		result = json.load(file)
		file.close()

		result = result['adresser']

		if result:
			latitude = result[0]['representasjonspunkt']['lat']
			longitude = result[0]['representasjonspunkt']['lon']
			return (latitude, longitude)
		else:
			return None

	else:
		return None


# Main program

if __name__ == '__main__':

	geocoding = True

	message ("\nAuto repair garages approved by Statens Vegvesen\n")
	
	if len(sys.argv) > 1:
		query_county = sys.argv[1] # County number XX
	else:
		query_county = ""

	# Read county names

	filename = "https://register.geonorge.no/api/sosi-kodelister/fylkesnummer.json?"
	file = urllib2.urlopen(filename)
	county_data = json.load(file)
	file.close()

	county_names = {}
	for county in county_data['containeditems']:
		if county['status'] == "Gyldig":
			county_names[county['codevalue']] = county['label'].strip()

	# Read postal codes and municipality codes from Posten (updated daily)

	file = urllib2.urlopen('https://www.bring.no/postnummerregister-ansi.txt')
	postal_codes = csv.DictReader(file, fieldnames=['zip','post_city','municipality_ref','municipality_name','type'], delimiter="\t")
	postcode_districts = {}
	for row in postal_codes:
		postcode_districts[ row['zip'] ] = {
			'city': row['post_city'].decode("windows-1252").strip().title(),
			'municipality_ref': row['municipality_ref'],
			'municipality_name': row['municipality_name'].decode("windows-1252").strip().title()
		}
	file.close()

	# Load data

	url = "https://www.vegvesen.no/System/CSV/verksted.csv?offset=0&size=10000"
	if query_county:
		url += "&fylkeId=%s" % query_county
	else:
		url += "&query=__ALL__"

	# To-do: KeepAliveTimeout

	file = urllib2.urlopen(url)
	garages = csv.DictReader(file, fieldnames=['name','street','zip','city','approvals','ref_org'], delimiter=";")
	next(garages) # Skip title line

	message ("Geocoding and generating output file...\n")

	# Produce OSM file header

	if query_county:
		filename = "garages_%s.osm" % query_county
	else:
		filename = "garages_all.osm"

	file = open (filename, "w")
	file.write ('<?xml version="1.0" encoding="UTF-8"?>\n')
	file.write ('<osm version="0.6" generator="garage2osm v%s" upload="false">\n' % version)

	node_id = -10000
	count = 0
	all_garages = 0

	# Iterate all restaurants and produce OSM tags

	for row in garages:

		all_garages += 1

		# Decode entries

		original_name = row['name'].decode("iso-8859-1").strip()
		original_street = row['street'].decode("iso-8859-1").strip()
		postcode = row['zip'].strip()
		original_city = row['city'].decode("iso-8859-1").strip()
		approvals = row['approvals'].decode("iso-8859-1").strip()

		# Fix name

		name = original_name.replace(",", "").replace(" - ", " ").replace(u"`", "'").replace(u"´", "'").replace("  ", " ")
		if name == name.upper():
			name = name.title()
		name_split = name.split()
		name = ""
		for word in name_split:
			new_word = word
			for word_from, word_to in transform_name.iteritems():
				if word == word_from:
					new_word = word_to
					break
			name += " " + new_word
		name = name.replace("  ", " ").replace("  ", " ").strip()

		# Find house number, unit/letter and municipality

		original_address = get_address(original_street, "", postcode, original_city)

		street = original_street
		reg = re.search(r'(.*) [0-9]+[ \-\/]+([0-9]+)[ ]*([A-Za-z]?)$', street)
		if not(reg):
			reg = re.search(r'(.*) ([0-9]+)[ ]*([A-Za-z]?)$', street)				
		if reg:
			street = reg.group(1).strip()
			house_number = reg.group(2)
			house_letter = reg.group(3)
		else:
			house_number = ""
			house_letter = ""

		if postcode in postcode_districts:
			municipality = postcode_districts[postcode]['municipality_ref']
			city = ""
		else:
			municipality = ""
			city = original_city

		full_address = get_address(street, house_number + house_letter, postcode, original_city)

		# Attempt to geocode address

		latitude = 0.0
		longitude = 0.0

		if geocoding:
			result = geocode (street, house_number, house_letter, city, municipality)

			if result:
				latitude = result[0]
				longitude = result[1]
				count += 1

			else:
				# Attempt new geocoding after fixing street name

				street += " "
				old_street = street
				for word_from, word_to in transform_address.iteritems():
					street = street.replace(word_from, word_to)
					street = street.replace(word_from.upper(), word_to.upper())

				if street != old_street:
					result = geocode (street, house_number, house_letter, city, municipality)

					if result:
						latitude = result[0]
						longitude = result[1]
						count += 1

		node_id -= 1

		file.write ('  <node id="%i" lat="%f" lon="%f">\n' % (node_id, latitude, longitude))

		# Decide shop type

		approvals_split = approvals.split(", ")

		if (approvals == "HJUL") or (name.lower().find("Dekkmann") >= 0) or (name.find("Vianor") >= 0) or (name.find("Mekonomen") < 0):
			make_osm_line ("shop", "tyres")
		elif approvals == "MOTORSYKKELOGMOPED":
			make_osm_line ("shop", "motorcycle")
		else:
			make_osm_line ("shop", "car_repair")

		if ("BILVERKSTED01" in approvals_split) or ("BILVERKSTED01B" in approvals_split) or\
			 ("BILVERKSTED02" in approvals_split) or ("BILVERKSTEDALLE" in approvals_split):  # Normal size cars
			make_osm_line ("car:repair", "yes")
		if ("BILVERKSTED03" in approvals_split) or ("BILVERKSTED04" in approvals_split):  # Trucks
			make_osm_line ("hgv:repair", "yes")
		if "BILGLASS" in approvals_split:
			make_osm_line ("car:windscreen", "yes")
		if "HJUL" in approvals_split:
			make_osm_line ("car:tyres", "yes")
		if "BILSKADE" in approvals_split:
			make_osm_line ("car:bodywork", "yes")
		if "MTORSYKKELOGMOPED" in approvals_split:
			make_osm_line ("motorcycle:repair", "yes")
		if ("TRAKTOR" in approvals_split) or (name.lower().find("traktor") >= 0):
			make_osm_line ("agricultural:repair", "yes")
		if approvals.find("KONTROLL") >= 0:
			make_osm_line ("vehicle_inspection", "yes")

		# Produce tags

		make_osm_line ("name", name)
		make_osm_line ("ref:gvorg", row['ref_org'])

		make_osm_line ("ADDRESS", original_address)
		make_osm_line ("APPROVALS", approvals)

		if name != original_name:
			make_osm_line ("ORIGINAL_NAME", original_name)

		if (latitude == 0.0) and (longitude ==0.0):  # Tag for geocoding using geocode2osm
			make_osm_line ("GEOCODE", "yes")

		# Find municipality and county from looking up postal code translation

		if postcode in postcode_districts:
			make_osm_line ("MUNICIPALITY", postcode_districts[ postcode ]['municipality_name'])
			make_osm_line ("COUNTY", county_names[ postcode_districts[ postcode ]['municipality_ref'][0:2] ])
		else:
			message ("Postcode not found: %s\n" % postcode)

		# Done with OSM store node

		file.write ('  </node>\n')

		if geocoding and not(result):
			message ("NOT FOUND: %s --> %s" % (original_name, original_address))
			if full_address != original_address:
				message (" (%s)\n" % full_address)
			else:
				message ("\n")

	# Wrap up

	file.write ('</osm>\n')
	file.close()

	message ("\nSuccessfully geocoded %i of %i garages\n" % (count, all_garages))
	message ("Written %i garages to file '%s'\n" % (all_garages, filename))
	if count < all_garages:
		message ("You may geocode the remaining %i garages with 'github.com/osmno/geocode2osm'\n" % (all_garages - count))
