import argparse
import os

from jyotisha.panchaanga import spatio_temporal
from jyotisha.panchaanga.temporal import era, festival, ComputationSystem
from jyotisha.panchaanga.writer import generation_project

bengaLUru = spatio_temporal.City.get_city_from_db("sahakAra nagar, bengaLUru")
chennai = spatio_temporal.City.get_city_from_db("Chennai")
today = bengaLUru.get_timezone_obj().current_time()

parser = argparse.ArgumentParser(description='panchAnga generator.')
parser.add_argument('--year', type=int, default=today.year, nargs='?')
args = parser.parse_args()
year = args.year
# year = 2017


kauNdinyaayana_bhaaskara_gRhya_computation_system = ComputationSystem.read_from_file(filename=os.path.join(os.path.dirname(festival.__file__), "data/computation_systems", "kauNdinyaayana_bhaaskara_gRhya.toml"))
vish_bhaaskara_computation_system = ComputationSystem.read_from_file(filename=os.path.join(os.path.dirname(festival.__file__), "data/computation_systems", "vishvAsa_bhAskara.toml"))

# bengaLUru
# Used by https://t.me/bengaluru_panchaanga
generation_project.dump_detailed(year=year, city=bengaLUru, year_type=era.ERA_GREGORIAN, computation_system=vish_bhaaskara_computation_system)
