import logging
import math

import numpy.testing

import tests.spatio_temporal
from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.spatio_temporal import daily
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.zodiac import AngaType

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def test_solar_day():

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 12, 31)))
  assert panchaanga.solar_sidereal_date_sunset.month_transition is None

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 1, 14)))
  assert panchaanga.solar_sidereal_date_sunset.day == 1
  assert panchaanga.solar_sidereal_date_sunset.month == 10
  assert panchaanga.solar_sidereal_date_sunset.month_transition == 2458132.8291680976

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 2, 12)))
  numpy.testing.assert_approx_equal(panchaanga.solar_sidereal_date_sunset.month_transition, 2458162.3747)


  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 4, 13)))
  assert panchaanga.solar_sidereal_date_sunset.month_transition is None

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2017, 12, 16)))
  assert panchaanga.solar_sidereal_date_sunset.day == 1
  assert panchaanga.solar_sidereal_date_sunset.month == 9

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=2457023.27)
  logging.debug(str(panchaanga))
  assert panchaanga.solar_sidereal_date_sunset.day == 16
  assert panchaanga.solar_sidereal_date_sunset.month == 9

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2017, 12, 31)))
  assert panchaanga.solar_sidereal_date_sunset.day == 16
  assert panchaanga.solar_sidereal_date_sunset.month == 9


def test_sunrise_mtv():
  city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2018, month=11, day=11))
  panchaanga.compute_sun_moon_transitions()
  numpy.testing.assert_approx_equal(panchaanga.jd_sunrise, 2458434.11)


def test_tb_muhuurta_blr():
  city = City.from_address_and_timezone('Bangalore', "Asia/Calcutta")
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2019, month=9, day=10))
  panchaanga.compute_tb_muhuurtas()
  assert len(panchaanga.day_length_based_periods.tb_muhuurtas) == 15
  assert panchaanga.day_length_based_periods.tb_muhuurtas[0].jd_start == panchaanga.jd_sunrise
  for muhurta in panchaanga.day_length_based_periods.tb_muhuurtas:
    logging.info(muhurta.to_localized_string(city=city))


def test_get_previous_solstice():
  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 1, 14)))
  solstice = panchaanga.get_previous_solstice()
  expected_jd_start = time.utc_gregorian_to_jd(date=Date(year=2017, month=12, day=21, hour=16, minute=28))
  numpy.testing.assert_approx_equal(solstice.jd_start, expected_jd_start, significant=4)

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 3, 14)))
  solstice = panchaanga.get_previous_solstice()
  expected_jd_start = time.utc_gregorian_to_jd(date=Date(year=2017, month=12, day=21, hour=16, minute=28))
  numpy.testing.assert_approx_equal(solstice.jd_start, expected_jd_start, significant=4)

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 7, 14)))
  solstice = panchaanga.get_previous_solstice()
  expected_jd_start = time.utc_gregorian_to_jd(date=Date(year=2018, month=6, day=20, hour=21, minute=44))
  numpy.testing.assert_approx_equal(solstice.jd_start, expected_jd_start, significant=4)


def test_jd_start_orinda_ca():
  city = City('Orinda', '37:51:38', '-122:10:59', 'America/Los_Angeles')
  assert daily.DailyPanchaanga.from_city_and_julian_day(city=city,
                                                        julian_day=2458551.8333333335).julian_day_start == 2458551.8333333335
  assert daily.DailyPanchaanga.from_city_and_julian_day(city=city,
                                                        julian_day=2458552.8333333335).julian_day_start == 2458552.8333333335


def test_get_lagna_float():
  city = City('X', 13.08784, 80.27847, 'Asia/Calcutta')
  numpy.testing.assert_allclose(
    city.get_lagna_float(
      2444961.7125), 10.353595502472984, rtol=1e-4)


def test_get_anga_data():
  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=tests.spatio_temporal.chennai, julian_day=2444961.54042)
  assert panchaanga.get_sunrise_day_anga_spans(AngaType.TITHI) == [
    Interval(name=27, jd_end=2444961.5992132244, jd_start=None)]
  assert panchaanga.get_sunrise_day_anga_spans(AngaType.NAKSHATRA) == [Interval(name=16, jd_end=2444961.746925843, jd_start=None)]
  assert panchaanga.get_sunrise_day_anga_spans(AngaType.YOGA) == [
    Interval(name=8, jd_end=2444962.18276057, jd_start=None)]
  assert panchaanga.get_sunrise_day_anga_spans(AngaType.KARANA) == [
    Interval(name=54, jd_end=2444961.5992132244, jd_start=None), Interval(name=55, jd_end=2444962.1544454526, jd_start=None)]


def test_get_lagna_data():
  city = City('X', 13.08784, 80.27847, 'Asia/Calcutta')
  from jyotisha.panchaanga.temporal import zodiac
  actual = daily.DailyPanchaanga.from_city_and_julian_day(city=city, julian_day=2458222.5208333335).get_lagna_data(
    ayanaamsha_id=zodiac.Ayanamsha.CHITRA_AT_180)
  expected = [(12, 2458222.5214310056), (1, 2458222.596420153),
              (2, 2458222.6812926503), (3, 2458222.772619788),
              (4, 2458222.8624254186), (5, 2458222.9478168003),
              (6, 2458223.0322211445), (7, 2458223.1202004547),
              (8, 2458223.211770839), (9, 2458223.3000455885),
              (10, 2458223.3787625884), (11, 2458223.4494649624),
              (12, 2458223.518700759)]
  numpy.testing.assert_allclose(actual, expected, rtol=1e-4) 
