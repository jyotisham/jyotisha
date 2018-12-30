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


