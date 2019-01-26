import numpy.testing
import json
import logging
import os

from jyotisha.panchangam.spatio_temporal import City
from jyotisha.panchangam.spatio_temporal import daily

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config_local.json')
config = {}
with open(CONFIG_PATH) as config_file:
  # noinspection PyRedeclaration
  config = json.loads(config_file.read())


def test_solar_day():
  panchangam = daily.Panchangam(city=City('Chennai', '13:05:24', '80:16:12', 'Asia/Calcutta'), julian_day=2457023.27)
  panchangam.compute_solar_day()
  logging.debug(str(panchangam))
  assert panchangam.solar_month_day == 16
  assert panchangam.solar_month == 9

def test_sunrise_mtv():
  city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
  panchangam = daily.Panchangam.from_date(city=city, year=2018, month=11, day=11)
  panchangam.compute_sun_moon_transitions()
  numpy.testing.assert_approx_equal(panchangam.jd_sunrise, 2458434.11)

def test_tb_muhuurta_mtv():
  city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
  panchangam = daily.Panchangam.from_date(city=city, year=2018, month=11, day=11)
  panchangam.compute_tb_muhuurtas()
  assert len(panchangam.tb_muhuurtas) == 15
  assert panchangam.tb_muhuurtas[0].jd_start == panchangam.jd_sunrise
  for muhurta in panchangam.tb_muhuurtas:
    logging.info(muhurta.to_localized_string())

def test_jd_start_orinda_ca():
  city = City('Orinda','37:51:38','-122:10:59','America/Los_Angeles')
  assert daily.Panchangam(city=city, julian_day=2458551.8333333335).julian_day_start == 2458551.8333333335
  assert daily.Panchangam(city=city, julian_day=2458552.8333333335).julian_day_start == 2458552.8333333335
