import argparse

from jyotisha.panchaanga import spatio_temporal, temporal
from jyotisha.panchaanga.temporal import era
from jyotisha.panchaanga.writer import generation_project


bengaLUru = spatio_temporal.City.get_city_from_db("sahakAra nagar, bengaLUru")
today = bengaLUru.get_timezone_obj().current_time()

parser = argparse.ArgumentParser(description='panchAnga generator.')
parser.add_argument('--year', type=int, default=today.year, nargs='?')
args = parser.parse_args()
year = args.year
# year = 2017

# bengaLUru
# Used by https://t.me/bengaluru_panchaanga
generation_project.dump_detailed(year=year, city=bengaLUru, year_type=era.ERA_GREGORIAN, computation_system=temporal.get_kauNdinyAyana_bhAskara_gRhya_computation_system())
generation_project.dump_detailed(year=year, city=bengaLUru, year_type=era.ERA_GREGORIAN)

# chennai
# Requested for bAlAsubrahmaNya's father. And kArtik potentially.
# chennai = spatio_temporal.City.get_city_from_db("Chennai")
# generation_project.dump_detailed(year=year, city=chennai, year_type=era.ERA_GREGORIAN)
