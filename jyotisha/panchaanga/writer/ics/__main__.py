import argparse
import os

from indic_transliteration import sanscript

from jyotisha.panchaanga import spatio_temporal
from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.writer import ics

bengaLUru = spatio_temporal.City.get_city_from_db("sahakAra nagar, bengaLUru")
today = bengaLUru.get_timezone_obj().current_time()

parser = argparse.ArgumentParser(description='panchAnga generator.')
parser.add_argument('--city', type=str, default="Bengaluru", nargs='?')
parser.add_argument('--year', type=int, default=today.year, nargs='?')
args = parser.parse_args()
year = args.year
city_str = args.city
city = spatio_temporal.City.get_city_from_db(city_str)

scripts = [sanscript.ISO]  # Default language is ISO for writing calendar

panchaanga = annual.get_panchaanga_for_civil_year(city=city, year=year)

ics_calendar = ics.compute_calendar(panchaanga)
output_file = os.path.expanduser('%s/%s__%d_%s.ics' % ("~/Documents/jyotisha", city.name, year, "-".join(scripts)))
ics.write_to_file(ics_calendar, output_file)
