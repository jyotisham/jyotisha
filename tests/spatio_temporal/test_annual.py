import json
import logging
import math
import os
import traceback

from indic_transliteration import xsanscript as sanscript

import sanskrit_data.collection_helper
from jyotisha.panchaanga.spatio_temporal import City, annual
# from jyotisha.panchaanga import scripts
# from jyotisha.panchaanga.spatio_temporal import annual
from jyotisha.panchaanga.temporal import zodiac
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')


def test_panchanga_chennai_18(caplog):
  caplog.set_level(logging.INFO)

  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga = annual.get_panchaanga(city=city, year=2018, script=sanscript.DEVANAGARI,
                                     ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, compute_lagnas=False,
                                     allow_precomputed=False)
  # Set the initial panchaanga. Should be generally commented out.
  # panchaanga.dump_to_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2018.json'),
  #                         floating_point_precision=4, sort_keys=False)

  panchaanga_expected_chennai_18 = JsonObject.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2018.json'))

  if panchaanga.to_json_map(floating_point_precision=4) != panchaanga_expected_chennai_18.to_json_map(
      floating_point_precision=4):
    panchaanga.dump_to_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2018-actual.json.local'),
                            floating_point_precision=4, sort_keys=False)
    panchaanga_expected_chennai_18.dump_to_file(
      filename=os.path.join(TEST_DATA_PATH, 'Chennai-2018-expected.json.local'), floating_point_precision=4,
      sort_keys=False)
  assert panchaanga.to_json_map(floating_point_precision=4) == panchaanga_expected_chennai_18.to_json_map(
    floating_point_precision=4)


def test_panchanga_chennai_19():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga = annual.get_panchaanga(city=city, year=2019, script=sanscript.DEVANAGARI,
                                     ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, compute_lagnas=False,
                                     allow_precomputed=False)
  # Set the initial panchaanga. SHould be generally commented out.
  # panchaanga.dump_to_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2019.json'),
  #                         floating_point_precision=4, sort_keys=False)
  panchaanga_expected_chennai_19 = JsonObject.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2019.json'))

  if panchaanga.to_json_map(floating_point_precision=4) != panchaanga_expected_chennai_19.to_json_map(
      floating_point_precision=4):
    panchaanga.dump_to_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2019-actual.json.local'),
                            floating_point_precision=4, sort_keys=False)
    panchaanga_expected_chennai_19.dump_to_file(
      filename=os.path.join(TEST_DATA_PATH, 'Chennai-2019-expected.json.local'), floating_point_precision=4, sort_keys=False)
  assert panchaanga.to_json_map(floating_point_precision=4) == panchaanga_expected_chennai_19.to_json_map(
    floating_point_precision=4)


def test_panchanga_orinda(caplog):
  caplog.set_level(logging.INFO)
  city = City('Orinda', '37:51:38', '-122:10:59', 'America/Los_Angeles')
  panchaanga = annual.get_panchaanga(city=city, year=2019, script=sanscript.DEVANAGARI,
                                     ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, compute_lagnas=False,
                                     allow_precomputed=False)
  # Set the initial panchaanga. SHould be generally commented out.
  # panchaanga.dump_to_file(filename=os.path.join(TEST_DATA_PATH, 'Orinda-2019.json'),
                          # floating_point_precision=4, sort_keys=False)

  panchaanga_expected_orinda_19 = JsonObject.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Orinda-2019.json'))

  if panchaanga.to_json_map(floating_point_precision=4) != panchaanga_expected_orinda_19.to_json_map(
      floating_point_precision=4):
    panchaanga.dump_to_file(filename=os.path.join(TEST_DATA_PATH, 'Orinda-2019-actual.json.local'),
                            floating_point_precision=4, sort_keys=False)
    panchaanga_expected_orinda_19.dump_to_file(filename=os.path.join(TEST_DATA_PATH, 'Orinda-2019-expected.json.local'),
                                               floating_point_precision=4, sort_keys=False)
  # assert json.dumps(panchaanga.to_flat_json_map(floating_point_precision=4), sort_keys=True) == json.dumps(panchaanga_expected_orinda_19.to_flat_json_map(
  #   floating_point_precision=4), sort_keys=True)
    try:
      sanskrit_data.collection_helper.assert_dict_equality(x=panchaanga.to_json_map(), y=panchaanga_expected_orinda_19.to_json_map(), floating_point_precision=4)
    except:
      traceback.print_exc() 
      raise 
    # assert panchaanga.to_flat_json_map(floating_point_precision=4) == panchaanga_expected_orinda_19.to_flat_json_map(floating_point_precision=4)


def test_adhika_maasa_computations_2009():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga_2009 = annual.get_panchaanga(city=city, year=2009, script=sanscript.DEVANAGARI,
                                          ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, compute_lagnas=False,
                                          allow_precomputed=False)
  expected_lunar_months_2009 = [7] + [8] * 29 + [9] * 30 + [10] * 15
  assert expected_lunar_months_2009 == panchaanga_2009.lunar_month[291:366]


def test_adhika_maasa_computations_2010():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga_2010 = annual.get_panchaanga(city=city, year=2010, script=sanscript.DEVANAGARI,
                                          ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, compute_lagnas=False,
                                          allow_precomputed=False)
  expected_lunar_months_2010 = [10] * 15 + [11] * 30 + [12] * 29 + [1] * 30 + [1.5] * 30 + [2] * 29 + [3]
  assert expected_lunar_months_2010 == panchaanga_2010.lunar_month[1:165]


def test_adhika_maasa_computations_2018():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchaanga_2018 = annual.get_panchaanga(city=city, year=2018, script=sanscript.DEVANAGARI,
                                          ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, compute_lagnas=False,
                                          allow_precomputed=False)
  expected_lunar_months_2018 = [2] + [2.5] * 29 + [3] * 30 + [4]
  assert expected_lunar_months_2018 == panchaanga_2018.lunar_month[135:196]


def test_orinda_ca_dst_2019():
  city = City('Orinda', '37:51:38', '-122:10:59', 'America/Los_Angeles')
  panchaanga = annual.get_panchaanga(city=city, year=2019, script=sanscript.DEVANAGARI,
                                     ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, compute_lagnas=False,
                                     allow_precomputed=False)
  # March 10 is the 69th day of the year (70th in leap years) in the Gregorian calendar.
  # Sunrise on that day is around 7:27 AM according to Google, which is JD 2458553.14375 according to https://ssd.jpl.nasa.gov/tc.cgi#top .
  # We use the index 70 below as the annual panchanga object seems to use the index d + 1.
  assert round(panchaanga.jd_sunrise[70], ndigits=4) == round(2458554.104348237, ndigits=4)  # 2019-Mar-10 07:30:15.68
