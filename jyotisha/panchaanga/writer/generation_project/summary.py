from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.writer.generation_project import dump_summary


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
  for year in range(1950, 2020):
    dump_summary(year=year, city=city)


if __name__ == '__main__':
  dump_mysore_history()