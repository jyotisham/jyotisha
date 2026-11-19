import copy
import datetime
import logging
import os

from sanskrit_data import collection_helper, testing
from sanskrit_data.schema.common import JsonObject
from timebudget import timebudget

from jyotisha.panchaanga.spatio_temporal import City, annual
from jyotisha.panchaanga.temporal import ComputationSystem
from jyotisha_tests.spatio_temporal import chennai

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
def panchaanga_json_comparer(city, year):
  test_computation_system = ComputationSystem.read_from_file(filename=os.path.join(TEST_DATA_PATH, "test_computation_system.toml"))
  expected_content_path = os.path.join(TEST_DATA_PATH, '%s-%d.json' % (city.name, year))
  panchaanga = annual.get_panchaanga_for_civil_year(city=city, year=year, computation_system=test_computation_system,
                                                    allow_precomputed=False)
  timebudget.report(reset=True)
  # collection_helper.assert_approx_equals() does not apply floating_point_precision rounding to
  # values nested inside sets (only dicts/lists/JsonObjects), so festival_id_to_days (a dict of sets)
  # must be converted to sorted lists first, else tiny cross-environment float noise in slow-moving
  # festivals (e.g. vArdhakya-prArambhaH) spuriously fails the comparison.
  panchaanga.festival_id_to_days = collection_helper.sets_to_lists(panchaanga.festival_id_to_days)
  if os.path.exists(expected_content_path):
    _match_festival_times(actual=panchaanga, expected=JsonObject.read_from_file(filename=expected_content_path))
  testing.json_compare(actual_object=panchaanga, expected_content_path=expected_content_path)


# Festival times found by a numerical search (eg. a planet's combustion, vArdhakya-prArambhaH) carry
# float noise across platforms of around 1e-4 s. json_compare rounds to 4 places and then demands
# equality, so noise straddling a rounding boundary fails it (13.22414 vs 13.22421 s). Times within
# this many seconds of the expected ones are taken as equal.
FESTIVAL_TIME_TOLERANCE_SECONDS = 0.01


def _as_datetime(date):
  return datetime.datetime(date.year, date.month, date.day, date.hour or 0, date.minute or 0) + \
    datetime.timedelta(seconds=date.second or 0)


def _match_festival_times(actual, expected):
  """Where an actual festival time is within the tolerance of the expected one, copy the expected
  time over, so that json_compare passes for it; anything further off is left for json_compare to
  report."""
  expected_days = getattr(expected, "festival_id_to_days", None) or {}
  for fest_id, days in actual.festival_id_to_days.items():
    expected_list = expected_days.get(fest_id)
    if isinstance(expected_list, set):
      expected_list = sorted(expected_list)
    if not isinstance(days, list) or not isinstance(expected_list, list) or len(days) != len(expected_list):
      continue
    for day, expected_day in zip(days, expected_list):
      if (day.hour is None) != (getattr(expected_day, "hour", None) is None):
        continue
      if abs((_as_datetime(day) - _as_datetime(expected_day)).total_seconds()) <= FESTIVAL_TIME_TOLERANCE_SECONDS:
        day.hour, day.minute, day.second = expected_day.hour, expected_day.minute, expected_day.second


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


def test_load_panchaanga_recomputes_on_deserialization_failure(tmp_path):
  # Simulates a cache file written by a different jyotisha version: its
  # jsonClass ("NoSuchFestivalInstance") isn't registered in this process's
  # json_class_index, so deserialization raises a bare KeyError. This used
  # to propagate and crash the caller; it should instead be treated like an
  # obsolete-version cache and trigger fallback_fn (recompute).
  fname = os.path.join(tmp_path, "poisoned.json")
  with open(fname, 'w') as f:
    f.write('{"jsonClass": "NoSuchFestivalInstance"}')
  sentinel = object()
  assert annual.load_panchaanga(fname=fname, fallback_fn=lambda: sentinel) is sentinel


def test_adhika_maasa_computations_2009():
  panchaanga = no_fest_chennai_panchaanga(year=2009)
  expected_lunar_months_2009 = [7] + [8] * 29 + [9] * 30 + [10] * 15
  assert expected_lunar_months_2009 == [x.lunar_date.month.index for x in panchaanga.daily_panchaangas_sorted()[
                                                                             panchaanga.duration_prior_padding + 290:panchaanga.duration_prior_padding + 365]]


def no_fest_chennai_panchaanga(year):
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  computation_system = copy.deepcopy(ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180)
  computation_system.festival_options.repos = []
  panchaanga = annual.get_panchaanga_for_civil_year(city=city, year=year,
                                                         allow_precomputed=False, computation_system=computation_system)
  return panchaanga


def test_adhika_maasa_computations_2010():
  panchaanga = no_fest_chennai_panchaanga(year=2010)
  expected_lunar_months_2010 = [10] * 15 + [11] * 30 + [12] * 29 + [1] * 30 + [1.5] * 30 + [2] * 29 + [3]
  assert expected_lunar_months_2010 == [x.lunar_date.month.index for x in panchaanga.daily_panchaangas_sorted()[
                                                                             panchaanga.duration_prior_padding:panchaanga.duration_prior_padding + 164]]


def test_adhika_maasa_computations_2018():
  from jyotisha_tests.spatio_temporal import get_panchaanga_from_previous_test
  panchaanga = get_panchaanga_from_previous_test(city_name="Chennai", year=2018)
  expected_lunar_months_2018 = [2] + [2.5] * 29 + [3] * 30 + [4]
  assert expected_lunar_months_2018 == [x.lunar_date.month.index for x in panchaanga.daily_panchaangas_sorted()[
                                                                             panchaanga.duration_prior_padding + 134:panchaanga.duration_prior_padding + 195]]


def test_orinda_ca_dst_2019():
  from jyotisha_tests.spatio_temporal import get_panchaanga_from_previous_test
  panchaanga = get_panchaanga_from_previous_test(city_name="Orinda", year=2019)
  # March 10 is the 69th day of the year (70th in leap years) in the Gregorian calendar.
  # Sunrise on that day is around 7:27 AM according to Google, which is JD 2458553.14375 according to https://ssd.jpl.nasa.gov/tc.cgi#top .
  # We use the index 70 below as the annual panchaanga object seems to use the index d + 1.
  assert round(panchaanga.daily_panchaangas_sorted()[panchaanga.duration_prior_padding + 69].jd_sunrise,
               ndigits=4) == round(2458554.104348237, ndigits=4)  # 2019-Mar-10 07:30:15.68
