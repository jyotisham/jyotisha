import logging
import os

import numpy.testing
from indic_transliteration import sanscript

from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.spatio_temporal import daily
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal.festival.rules import RulesRepo
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.time import Date
from jyotisha.panchaanga.temporal.zodiac import AngaType
from timebudget import timebudget

from sanskrit_data import testing

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

chennai = City.get_city_from_db("Chennai")
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')


# noinspection PyUnresolvedReferences
def panchaanga_json_comparer(city, date):
  expected_content_path=os.path.join(TEST_DATA_PATH, '%s-%s.json' % (city.name, date.get_date_str()))
  panchaanga = daily.DailyPanchaanga(city=city, date=date)
  timebudget.report(reset=True)
  testing.json_compare(actual_object=panchaanga, expected_content_path=expected_content_path)
  return panchaanga


def test_solar_day():

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 12, 31)))
  assert panchaanga.solar_sidereal_date_sunset.month_transition is None

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 1, 14)))
  assert panchaanga.solar_sidereal_date_sunset.day == 1
  assert panchaanga.solar_sidereal_date_sunset.month == 10
  numpy.testing.assert_approx_equal(panchaanga.solar_sidereal_date_sunset.month_transition, 2458132.8291680976)

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 2, 12)))
  numpy.testing.assert_approx_equal(panchaanga.solar_sidereal_date_sunset.month_transition, 2458162.3747)


  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=chennai, julian_day=time.utc_gregorian_to_jd(Date(2018, 4, 13)))
  assert panchaanga.solar_sidereal_date_sunset.month_transition is None

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=chennai, julian_day=time.utc_gregorian_to_jd(Date(2017, 12, 16)))
  assert panchaanga.solar_sidereal_date_sunset.day == 1
  assert panchaanga.solar_sidereal_date_sunset.month == 9

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=chennai, julian_day=2457023.27)
  logging.debug(str(panchaanga))
  assert panchaanga.solar_sidereal_date_sunset.day == 16
  assert panchaanga.solar_sidereal_date_sunset.month == 9

  panchaanga = daily.DailyPanchaanga.from_city_and_julian_day(
    city=chennai, julian_day=time.utc_gregorian_to_jd(Date(2017, 12, 31)))
  assert panchaanga.solar_sidereal_date_sunset.day == 16
  assert panchaanga.solar_sidereal_date_sunset.month == 9


def test_sunrise_mtv():
  city = City.get_city_from_db('Cupertino') 
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2018, month=11, day=11))
  panchaanga.compute_sun_moon_transitions()
  numpy.testing.assert_approx_equal(panchaanga.jd_sunrise, 2458434.11)


def test_tb_muhuurta_blr():
  city = City.get_city_from_db('Bangalore')   
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2019, month=9, day=10))
  assert len(panchaanga.day_length_based_periods.fifteen_fold_division.tb_muhuurtas) == 15
  assert panchaanga.day_length_based_periods.fifteen_fold_division.tb_muhuurtas[0].jd_start == panchaanga.jd_sunrise
  for muhurta in panchaanga.day_length_based_periods.fifteen_fold_division.tb_muhuurtas:
    logging.info(muhurta.to_localized_string(city=city))


def test_jd_start_orinda_ca():
  city = City('Orinda', '37:51:38', '-122:10:59', 'America/Los_Angeles')
  assert daily.DailyPanchaanga.from_city_and_julian_day(city=city,
                                                        julian_day=2458551.8333333335).julian_day_start == 2458551.8333333335
  assert daily.DailyPanchaanga.from_city_and_julian_day(city=city,
                                                        julian_day=2458552.8333333335).julian_day_start == 2458552.8333333335


def test_get_lagna_float():
  city = City.get_city_from_db('Chennai') 
  numpy.testing.assert_allclose(
    city.get_lagna_float(
      2444961.7125), 10.353595502472984, rtol=1e-4)


def test_get_anga_data_1981_12_23():
  panchaanga = panchaanga_json_comparer(chennai, date=Date(1981, 12, 23))
  angas = [s.anga.index for s in panchaanga.sunrise_day_angas.get_anga_spans_in_interval(interval=panchaanga.day_length_based_periods.puurvaahna, anga_type=AngaType.NAKSHATRA)]
  assert angas == [16, 17]

  angas = [s.anga.index for s in panchaanga.sunrise_day_angas.get_anga_spans_in_interval(interval=Interval(jd_start=panchaanga.jd_sunrise, jd_end=panchaanga.jd_sunrise), anga_type=AngaType.NAKSHATRA)]
  assert angas == [16]

  angas = [s.anga.index for s in panchaanga.sunrise_day_angas.get_anga_spans_in_interval(interval=Interval(jd_start=panchaanga.jd_sunrise, jd_end=panchaanga.jd_next_sunrise), anga_type=AngaType.NAKSHATRA)]
  assert angas == [16, 17]


def test_get_pancha_paxi_activities():
  city = City.get_city_from_db('Chennai')
  from jyotisha.panchaanga.temporal import zodiac
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2022, month=1, day=2))
  paxi_activities = panchaanga.get_pancha_paxi_activities()
  assert paxi_activities.cock[0].name == 1
  assert paxi_activities.cock[23].name == 4

def test_get_lagna_data():
  city = City.get_city_from_db('Chennai') 
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

def test_get_samvatsara():
  city = City.get_city_from_db('Bangalore')
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2019, month=9, day=10))
  assert panchaanga.get_samvatsara(month_type=RulesRepo.LUNAR_MONTH_DIR).get_name(script=sanscript.DEVANAGARI) == "विकारी"
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2020, month=2, day=10))
  assert panchaanga.get_samvatsara(month_type=RulesRepo.LUNAR_MONTH_DIR).get_name(script=sanscript.DEVANAGARI) == "विकारी"
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2020, month=4, day=10))
  assert panchaanga.get_samvatsara(month_type=RulesRepo.LUNAR_MONTH_DIR).get_name(script=sanscript.DEVANAGARI) == "शार्वरी"
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2020, month=4, day=10))
  assert panchaanga.get_samvatsara(month_type=RulesRepo.TROPICAL_MONTH_DIR).get_name(script=sanscript.DEVANAGARI) == "शार्वरी"
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2020, month=4, day=10))
  assert panchaanga.get_samvatsara(month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR).get_name(script=sanscript.DEVANAGARI) == "विकारी"
  panchaanga = daily.DailyPanchaanga(city=city, date=Date(year=2020, month=4, day=20))
  assert panchaanga.get_samvatsara(month_type=RulesRepo.SIDEREAL_SOLAR_MONTH_DIR).get_name(script=sanscript.DEVANAGARI) == "शार्वरी"
