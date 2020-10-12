import logging
import os
import traceback

import sanskrit_data.collection_helper
from jyotisha.panchaanga.spatio_temporal import City, annual, periodical
# from jyotisha.panchaanga import scripts
# from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga
from jyotisha.panchaanga.temporal.time import Date
from timebudget import timebudget

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
  expected_content_path=os.path.join(TEST_DATA_PATH, '%s-%d.json' % (city.name, year))
  panchaanga = annual.get_panchaanga_for_civil_year(city=city, year=year,
                                                    allow_precomputed=False)
  timebudget.report(reset=True)
  if not os.path.exists(expected_content_path):
    logging.warning("File must have been deliberately deleted as obsolete. So, will dump a new file for future tests.")
    panchaanga.dump_to_file(filename=expected_content_path,
                            floating_point_precision=4)
  panchaanga_expected = Panchaanga.read_from_file(filename=expected_content_path)
  timebudget.report(reset=True)
  try:
    # The below would be actually slower (1min+), and leads to bug output dump in case of failure.
    # assert str_actual == str_expected 
    # The below is better, but still slower (35s and leads to bug output dump in case of failure.
    # assert actual == expected
    
    # The below is faster - 20s and produces concise difference.
    sanskrit_data.collection_helper.assert_approx_equals(x=panchaanga, y=panchaanga_expected, floating_point_precision=4)
  except:
    # firefox does not identify files not ending with .json as json. Hence not naming .json.local.
    actual_content_path = expected_content_path.replace(".json", "_actual.local.json")
    panchaanga.dump_to_file(filename=actual_content_path, floating_point_precision=4)
    traceback.print_exc()
    raise


def test_panchanga_chennai_18(caplog):
  caplog.set_level(logging.INFO)

  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga_json_comparer(city=city, year=2018)


def test_panchanga_chennai_19():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga_json_comparer(city=city, year=2019)


def test_panchanga_orinda(caplog):
  caplog.set_level(logging.INFO)
  city = City('Orinda', '37:51:38', '-122:10:59', 'America/Los_Angeles')
  panchaanga_json_comparer(city=city, year=2019)


def test_adhika_maasa_computations_2009():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga_2009 = annual.get_panchaanga_for_civil_year(city=city, year=2009,
                                                         allow_precomputed=False)
  expected_lunar_months_2009 = [7] + [8] * 29 + [9] * 30 + [10] * 15
  assert expected_lunar_months_2009 == [x.lunar_month_sunrise for x in panchaanga_2009.daily_panchaangas_sorted()[291:366]]


def test_adhika_maasa_computations_2010():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga_2010 = annual.get_panchaanga_for_civil_year(city=city, year=2010,
                                                         allow_precomputed=False)
  expected_lunar_months_2010 = [10] * 15 + [11] * 30 + [12] * 29 + [1] * 30 + [1.5] * 30 + [2] * 29 + [3]
  assert expected_lunar_months_2010 == [x.lunar_month_sunrise for x in panchaanga_2010.daily_panchaangas_sorted()[1:165]]


def test_adhika_maasa_computations_2018():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga_2018 = annual.get_panchaanga_for_civil_year(city=city, year=2018,
                                                         allow_precomputed=False)
  expected_lunar_months_2018 = [2] + [2.5] * 29 + [3] * 30 + [4]
  assert expected_lunar_months_2018 == [x.lunar_month_sunrise for x in panchaanga_2018.daily_panchaangas_sorted()[135:196]]


def test_orinda_ca_dst_2019():
  city = City('Orinda', '37:51:38', '-122:10:59', 'America/Los_Angeles')
  panchaanga = panchaanga = periodical.Panchaanga(city=city, start_date=Date(2019, 1, 1), end_date=Date(2019, 5, 1))
  # March 10 is the 69th day of the year (70th in leap years) in the Gregorian calendar.
  # Sunrise on that day is around 7:27 AM according to Google, which is JD 2458553.14375 according to https://ssd.jpl.nasa.gov/tc.cgi#top .
  # We use the index 70 below as the annual panchanga object seems to use the index d + 1.
  assert round(panchaanga.daily_panchaangas_sorted()[70].jd_sunrise, ndigits=4) == round(2458554.104348237, ndigits=4)  # 2019-Mar-10 07:30:15.68
