import logging
import os

# from jyotisha.panchaanga.spatio_temporal import City, annual
from jyotisha.panchaanga.scripts.write_daily_panchaanga_tex import writeDailyTeX
from sanskrit_data.schema.common import JsonObject

# import swisseph as swe
# from indic_transliteration import xsanscript as sanscript

# from jyotisha.panchaanga import scripts
# from jyotisha.panchaanga.spatio_temporal import annual

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_panchanga_chennai_2019():
  panchaanga_2019 = JsonObject.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2019.json'))
  panchaanga_2019.update_festival_details()
  orig_tex_file = os.path.join(TEST_DATA_PATH, 'daily-cal-2019-Chennai-deva.tex')
  daily_template_file = open(os.path.join(CODE_ROOT, 'jyotisha/panchaanga/data/templates/daily_cal_template.tex'))
  current_tex_output = os.path.join(TEST_DATA_PATH, 'daily-cal-2019-Chennai-deva.tex.local')
  writeDailyTeX(panchaanga_2019, daily_template_file, compute_lagnams=False,
                output_stream=open(current_tex_output, 'w'))

  with open(orig_tex_file) as orig_tex:
    with open(current_tex_output) as current_tex:
      assert orig_tex.read() == current_tex.read()


def test_panchaanga_orinda_2019():
  panchaanga_2019 = JsonObject.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Orinda-2019.json'))
  panchaanga_2019.update_festival_details()
  orig_tex_file = os.path.join(TEST_DATA_PATH, 'daily-cal-2019-Orinda-deva.tex')
  daily_template_file = open(os.path.join(CODE_ROOT, 'jyotisha/panchaanga/data/templates/daily_cal_template.tex'))
  current_tex_output = os.path.join(TEST_DATA_PATH, 'daily-cal-2019-Orinda-deva.tex.local')
  writeDailyTeX(panchaanga_2019, daily_template_file, compute_lagnams=False,
                output_stream=open(current_tex_output, 'w'))

  with open(orig_tex_file) as orig_tex:
    with open(current_tex_output) as current_tex:
      assert orig_tex.read() == current_tex.read()


def test_panchaanga_chennai_2018():
  panchaanga_2018 = JsonObject.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2018.json'))
  panchaanga_2018.update_festival_details()
  orig_tex_file = os.path.join(TEST_DATA_PATH, 'daily-cal-2018-Chennai-deva.tex')
  daily_template_file = open(os.path.join(CODE_ROOT, 'jyotisha/panchaanga/data/templates/daily_cal_template.tex'))
  current_tex_output = os.path.join(TEST_DATA_PATH, 'daily-cal-2018-Chennai-deva.tex.local')
  writeDailyTeX(panchaanga_2018, daily_template_file, compute_lagnams=False,
                output_stream=open(current_tex_output, 'w'))

  with open(orig_tex_file) as orig_tex:
    with open(current_tex_output) as current_tex:
      assert orig_tex.read() == current_tex.read()

