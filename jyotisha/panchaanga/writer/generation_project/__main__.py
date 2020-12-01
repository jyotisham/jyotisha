from jyotisha.panchaanga import spatio_temporal
from jyotisha.panchaanga.writer import generation_project

bengaLUru = spatio_temporal.City.get_city_from_db("sahakAra nagar, bengaLUru")
generation_project.dump_common(year=1942, city=bengaLUru)
generation_project.dump_kauNDinyAyana(year=1942, city=bengaLUru)