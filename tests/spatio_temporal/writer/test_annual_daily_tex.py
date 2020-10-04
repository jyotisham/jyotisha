import logging
import os

# from jyotisha.panchaanga.spatio_temporal import City, annual
from indic_transliteration import sanscript

from jyotisha.panchaanga.writer.tex.write_daily_panchaanga_tex import emit
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga
from sanskrit_data.schema.common import JsonObject

# import swisseph as swe
# from indic_transliteration import xsanscript as sanscript

# from jyotisha.panchaanga import scripts
# from jyotisha.panchaanga.spatio_temporal import annual

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TEST_DATA_PATH = os.path.join(CODE_ROOT, 'tests/spatio_temporal/data')


def daily_tex_comparer(city_name, year):
  panchaanga = Panchaanga.read_from_file(filename=os.path.join(TEST_DATA_PATH, '%s-%s.json' % (city_name, year)))
  panchaanga.update_festival_details()
  orig_tex_file = os.path.join(TEST_DATA_PATH, 'daily-cal-%s-%s-deva.tex' % (year, city_name))
  daily_template_file = open(os.path.join(CODE_ROOT, 'jyotisha/panchaanga/data/templates/daily_cal_template.tex'))
  current_tex_output = os.path.join(TEST_DATA_PATH, 'daily-cal-%s-%s-deva.tex.local' % (year, city_name))
  emit(panchaanga, daily_template_file, compute_lagnams=False,
       output_stream=open(current_tex_output, 'w'), scripts=[sanscript.DEVANAGARI, sanscript.TAMIL])

  with open(orig_tex_file) as orig_tex:
    with open(current_tex_output) as current_tex:
      assert current_tex.read() == orig_tex.read()


def test_panchanga_chennai_2019():
  daily_tex_comparer(city_name="Chennai", year=2019)


def test_panchaanga_orinda_2019():
  daily_tex_comparer(city_name="Orinda", year=2019)


def test_panchaanga_chennai_2018():
  daily_tex_comparer(city_name="Chennai", year=2018)

