from jyotisha.panchaanga import temporal
from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.writer.generation_project import dump_summary


def dump_delhi_history():
  c = City.get_city_from_db(name="Delhi")
  for year in range(1150, 1251):
    dump_summary(year=year, city=c)


def dump_mysore_history():
  maisUru = City.get_city_from_db(name="Mysore")
  # dump_summary(year=1797, city=maisUru)
  for year in range(1740, 1810):
    dump_summary(year=year, city=maisUru)


def dump_pune_history():
  city = City.get_city_from_db(name="Pune")
  # dump_summary(year=1797, city=maisUru)
  for year in range(1625, 1850):
    dump_summary(year=year, city=city)


def dump_hampi_history():
  city = City.get_city_from_db(name="Hampi")
  # dump_summary(year=1797, city=maisUru)
  for year in range(1300, 1625):
    dump_summary(year=year, city=city)


def dump_bengaluru_history():
  city = City.get_city_from_db(name="sahakAra nagar, bengaLUru")
  # dump_summary(year=1797, city=maisUru)
  # for year in range(1950, 2020):
  #   dump_summary(year=year, city=city)
  for year in range(2010, 2023):
    # dump_summary(year=year, city=city,computation_system=temporal.get_kauNdinyAyana_bhAskara_gRhya_computation_system(), allow_precomputed=False)
    dump_summary(year=year, city=city, allow_precomputed=False)


if __name__ == '__main__':
  dump_delhi_history()