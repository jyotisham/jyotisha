import json
import logging
import os
from indic_transliteration import xsanscript as sanscript

from sanskrit_data.schema.common import JsonObject

from jyotisha.panchangam import scripts
from jyotisha.panchangam.spatio_temporal import City, annual

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
  city = City.from_address_and_timezone('Chennai', "Asia/Calcutta")
  panchangam = scripts.get_panchangam(city=city, year=2018, script=sanscript.DEVANAGARI, computeLagnams=False)
  assert panchangam.to_json_map() == panchangam_expected_chennai_18.to_json_map()


