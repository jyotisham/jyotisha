import json
import logging
import os
import swisseph as swe
from indic_transliteration import xsanscript as sanscript

from sanskrit_data.schema.common import JsonObject

import jyotisha.panchangam.spatio_temporal.annual
from jyotisha.panchangam.spatio_temporal import City
# from jyotisha.panchangam import scripts
# from jyotisha.panchangam.spatio_temporal import annual

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config_local.json')
config = {}
with open(CONFIG_PATH) as config_file:
  # noinspection PyRedeclaration
  config = json.loads(config_file.read())


TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')


def test_panchanga_chennai():
  panchangam_expected_chennai_18 = JsonObject.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2018.json'))
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchangam = jyotisha.panchangam.spatio_temporal.annual.Panchangam(city=city, year=2018, script=sanscript.DEVANAGARI, ayanamsha_id=swe.SIDM_LAHIRI, compute_lagnams=False)
  if str(panchangam) != str(panchangam_expected_chennai_18):
    panchangam.dump_to_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2018-actual.json.local'))
  assert str(panchangam) == str(panchangam_expected_chennai_18)


def test_adhika_maasa_computations():
  assert test_adhika_maasa_computations_2009()
  assert test_adhika_maasa_computations_2010()
  assert test_adhika_maasa_computations_2018()


def test_adhika_maasa_computations_2009():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchangam_2009 = jyotisha.panchangam.spatio_temporal.annual.Panchangam(city=city, year=2009, script=sanscript.DEVANAGARI, ayanamsha_id=swe.SIDM_LAHIRI, compute_lagnams=False)
  panchangam_2009.assignLunarMonths()
  expected_lunar_months_2009 = [7] + [8]*29 + [9]*30 + [10]*15
  assert expected_lunar_months_2009 == panchangam_2009.lunar_month[291:366]
  return True


def test_adhika_maasa_computations_2010():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchangam_2010 = jyotisha.panchangam.spatio_temporal.annual.Panchangam(city=city, year=2010, script=sanscript.DEVANAGARI, ayanamsha_id=swe.SIDM_LAHIRI, compute_lagnams=False)
  panchangam_2010.assignLunarMonths()
  expected_lunar_months_2010 = [10]*15 + [11]*30 + [12]*29 + [1]*30 + [1.5]*30 + [2]*29 + [3]
  assert expected_lunar_months_2010 == panchangam_2010.lunar_month[1:165]
  return True


def test_adhika_maasa_computations_2018():
  city = City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchangam_2018 = jyotisha.panchangam.spatio_temporal.annual.Panchangam(city=city, year=2018, script=sanscript.DEVANAGARI, ayanamsha_id=swe.SIDM_LAHIRI, compute_lagnams=False)
  panchangam_2018.assignLunarMonths()
  expected_lunar_months_2018 = [2] + [2.5]*29 + [3]*30 + [4]
  assert expected_lunar_months_2018 == panchangam_2018.lunar_month[135:196]
  return True
