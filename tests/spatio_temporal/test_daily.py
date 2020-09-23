import logging
import math

import numpy.testing

from jyotisha.panchangam.spatio_temporal import City
from jyotisha.panchangam.spatio_temporal import daily

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def test_solar_day():
  panchangam = daily.DailyPanchanga.from_city_and_julian_day(
    city=City('Chennai', '13:05:24', '80:16:12', 'Asia/Calcutta'), julian_day=2457023.27)
  panchangam.compute_solar_day()
  logging.debug(str(panchangam))
  assert panchangam.solar_month_day == 16
  assert panchangam.solar_month == 9


def test_sunrise_mtv():
  city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
  panchangam = daily.DailyPanchanga(city=city, year=2018, month=11, day=11)
  panchangam.compute_sun_moon_transitions()
  numpy.testing.assert_approx_equal(panchangam.jd_sunrise, 2458434.11)


def test_tb_muhuurta_blr():
  city = City.from_address_and_timezone('Bangalore', "Asia/Calcutta")
  panchangam = daily.DailyPanchanga(city=city, year=2019, month=9, day=10)
  panchangam.compute_tb_muhuurtas()
  assert len(panchangam.tb_muhuurtas) == 15
  assert panchangam.tb_muhuurtas[0].jd_start == panchangam.jd_sunrise
  for muhurta in panchangam.tb_muhuurtas:
    logging.info(muhurta.to_localized_string(city=city))


def test_jd_start_orinda_ca():
  city = City('Orinda', '37:51:38', '-122:10:59', 'America/Los_Angeles')
  assert daily.DailyPanchanga.from_city_and_julian_day(city=city,
                                                       julian_day=2458551.8333333335).julian_day_start == 2458551.8333333335
  assert daily.DailyPanchanga.from_city_and_julian_day(city=city,
                                                       julian_day=2458552.8333333335).julian_day_start == 2458552.8333333335


def test_get_lagna_float():
  city = City('X', 13.08784, 80.27847, 'Asia/Calcutta')
  numpy.testing.assert_allclose(
    city.get_lagna_float(
      2444961.7125), 10.353595502472984, rtol=1e-4)


def test_get_lagna_data():
  city = City('X', 13.08784, 80.27847, 'Asia/Calcutta')
  from jyotisha.panchangam.temporal import zodiac
  actual = daily.DailyPanchanga.from_city_and_julian_day(city=city, julian_day=2458222.5208333335).get_lagna_data(
    ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180)
  expected = [(12, 2458222.5214310056), (1, 2458222.596420153),
              (2, 2458222.6812926503), (3, 2458222.772619788),
              (4, 2458222.8624254186), (5, 2458222.9478168003),
              (6, 2458223.0322211445), (7, 2458223.1202004547),
              (8, 2458223.211770839), (9, 2458223.3000455885),
              (10, 2458223.3787625884), (11, 2458223.4494649624),
              (12, 2458223.518700759)]
  numpy.testing.assert_allclose(actual, expected, rtol=1e-4) 
