import logging

from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal.time import Timezone


def test_moonrise_time():
  city = City.from_address_and_timezone('Bengaluru', "Asia/Calcutta")
  from jyotisha.panchaanga.temporal.body import Graha
  assert city.get_rising_time(julian_day_start=2459107.33, body=Graha.MOON) == 2459107.4296293524
