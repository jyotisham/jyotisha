from jyotisha.panchaanga import spatio_temporal, temporal
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.writer import generation_project

bengaLUru = spatio_temporal.City.get_city_from_db("sahakAra nagar, bengaLUru")
today = bengaLUru.get_timezone_obj().current_time()
year = today.year
# year = 2021
generation_project.dump_detailed(year=year, city=bengaLUru, year_type=RulesRepo.ERA_GREGORIAN, computation_system=temporal.get_kauNdinyAyana_bhAskara_gRhya_computation_system())
generation_project.dump_detailed(year=year, city=bengaLUru, year_type=RulesRepo.ERA_GREGORIAN)
