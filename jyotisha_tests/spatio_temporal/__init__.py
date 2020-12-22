import os

from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga

chennai = City.get_city_from_db("Chennai")


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')


def get_panchaanga_from_previous_test(city_name, year):
  panchaanga = Panchaanga.read_from_file(filename=os.path.join(TEST_DATA_PATH, '%s-%s.json' % (city_name, year)))
  return panchaanga
