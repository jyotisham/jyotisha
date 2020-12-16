from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.writer.generation_project import dump_history

if __name__ == '__main__':
  maisUru = City.get_city_from_db(name="Mysore")
  dump_history(year=1799, city=maisUru)
