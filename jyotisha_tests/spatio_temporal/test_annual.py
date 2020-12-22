import copy
import logging
import os

from timebudget import timebudget

from jyotisha.panchaanga.spatio_temporal import City, annual, periodical
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha.panchaanga.temporal.time import Date
from jyotisha_tests.spatio_temporal import chennai
from sanskrit_data import testing

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')


def test_timing(caplog):
  # A separate function for convenient profiling.
  # See data/timing_snapshot* for results/ progression.
  caplog.set_level(logging.INFO)
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  annual.get_panchaanga_for_civil_year(city=city, year=2018,
                                       allow_precomputed=False)
  timebudget.report(reset=True)


# noinspection PyUnresolvedReferences
def panchaanga_json_comparer(city, year, computation_system=ComputationSystem.TEST):
  expected_content_path = os.path.join(TEST_DATA_PATH, '%s-%d.json' % (city.name, year))
  panchaanga = annual.get_panchaanga_for_civil_year(city=city, year=year, computation_system=computation_system,
                                                    allow_precomputed=False)
  timebudget.report(reset=True)
  testing.json_compare(actual_object=panchaanga, expected_content_path=expected_content_path)


# def test_panchaanga_chennai_2020(caplog):
#   caplog.set_level(logging.INFO)
#   comp_system = deepcopy(ComputationSystem.DEFAULT)
#   comp_system.options.aparaahna_as_second_half = True
#   panchaanga_json_comparer(city=chennai, year=2020, computation_system=comp_system)


def test_panchaanga_chennai_18(caplog):
  caplog.set_level(logging.INFO)
  panchaanga_json_comparer(city=chennai, year=2018)


def test_panchaanga_chennai_19():
  panchaanga_json_comparer(city=chennai, year=2019)


def test_panchaanga_orinda_19(caplog):
  caplog.set_level(logging.INFO)
  city = City('Orinda', '37:51:38', '-122:10:59', 'America/Los_Angeles')
  panchaanga_json_comparer(city=city, year=2019)


def test_adhika_maasa_computations_2009():
  panchaanga = no_fest_chennai_panchaanga(year=2009)
  expected_lunar_months_2009 = [7] + [8] * 29 + [9] * 30 + [10] * 15
  assert expected_lunar_months_2009 == [x.lunar_month_sunrise.index for x in panchaanga.daily_panchaangas_sorted()[
                                                                             panchaanga.duration_prior_padding + 290:panchaanga.duration_prior_padding + 365]]


def no_fest_chennai_panchaanga(year):
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  computation_system = copy.deepcopy(ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180)
  computation_system.festival_options.repos = []
  panchaanga = annual.get_panchaanga_for_civil_year(city=city, year=year,
                                                         allow_precomputed=False, computation_system=computation_system)
  return panchaanga


def test_adhika_maasa_computations_2010():
  panchaanga = no_fest_chennai_panchaanga(year=2010)
  expected_lunar_months_2010 = [10] * 15 + [11] * 30 + [12] * 29 + [1] * 30 + [1.5] * 30 + [2] * 29 + [3]
  assert expected_lunar_months_2010 == [x.lunar_month_sunrise.index for x in panchaanga.daily_panchaangas_sorted()[
                                                                             panchaanga.duration_prior_padding:panchaanga.duration_prior_padding + 164]]


def test_adhika_maasa_computations_2018():
  from jyotisha_tests.spatio_temporal import get_panchaanga_from_previous_test
  panchaanga = get_panchaanga_from_previous_test(city_name="Chennai", year=2018)
  expected_lunar_months_2018 = [2] + [2.5] * 29 + [3] * 30 + [4]
  assert expected_lunar_months_2018 == [x.lunar_month_sunrise.index for x in panchaanga.daily_panchaangas_sorted()[
                                                                             panchaanga.duration_prior_padding + 134:panchaanga.duration_prior_padding + 195]]


def test_orinda_ca_dst_2019():
  from jyotisha_tests.spatio_temporal import get_panchaanga_from_previous_test
  panchaanga = get_panchaanga_from_previous_test(city_name="Orinda", year=2019)
  # March 10 is the 69th day of the year (70th in leap years) in the Gregorian calendar.
  # Sunrise on that day is around 7:27 AM according to Google, which is JD 2458553.14375 according to https://ssd.jpl.nasa.gov/tc.cgi#top .
  # We use the index 70 below as the annual panchaanga object seems to use the index d + 1.
  assert round(panchaanga.daily_panchaangas_sorted()[panchaanga.duration_prior_padding + 69].jd_sunrise,
               ndigits=4) == round(2458554.104348237, ndigits=4)  # 2019-Mar-10 07:30:15.68
