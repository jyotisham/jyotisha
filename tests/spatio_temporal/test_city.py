import logging

from jyotisha.panchangam.spatio_temporal import City
from jyotisha.panchangam.temporal import Timezone


def test_moonrise_time():
  city = City.from_address_and_timezone('Bengaluru', "Asia/Calcutta")
  from jyotisha.panchangam.temporal.body import Graha
  assert city.get_rising_time(julian_day_start=2459107.33, body=Graha.MOON) == 2459107.4296293524
