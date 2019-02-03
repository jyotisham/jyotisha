import logging
import os
# import swisseph as swe
# from indic_transliteration import xsanscript as sanscript

from sanskrit_data.schema.common import JsonObject

# from jyotisha.panchangam.spatio_temporal import City, annual
# from jyotisha.panchangam.scripts.write_daily_panchangam_tex import writeDailyTeX
from jyotisha.panchangam.scripts.ics import compute_calendar, write_to_file
# from jyotisha.panchangam import scripts
# from jyotisha.panchangam.spatio_temporal import annual

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_panchanga_chennai_2019():
  panchangam_2019 = JsonObject.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2019.json'))
  panchangam_2019.update_festival_details()
  orig_ics_file = os.path.join(TEST_DATA_PATH, 'Chennai-2019-devanagari.ics')
  current_ics_output = os.path.join(TEST_DATA_PATH, 'Chennai-2019-devanagari.ics.local')
  ics_calendar = compute_calendar(panchangam_2019, all_tags=True)
  write_to_file(ics_calendar, current_ics_output)

  with open(orig_ics_file) as orig_tex:
    with open(current_ics_output) as current_tex:
      assert orig_tex.read() == current_tex.read()


# def test_panchanga_chennai_2018():
#   panchangam_2018 = JsonObject.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2018.json'))
#   panchangam_2018.update_festival_details()
#   orig_ics_file = os.path.join(TEST_DATA_PATH, 'daily-cal-2018-Chennai-deva.tex')
#   daily_template_file = open(os.path.join(CODE_ROOT, 'jyotisha/panchangam/data/templates/daily_cal_template.tex'))
#   current_ics_output = os.path.join(TEST_DATA_PATH, 'daily-cal-2018-Chennai-deva.tex.local')
#   writeDailyTeX(panchangam_2018, daily_template_file, compute_lagnams=False, output_stream=open(current_ics_output, 'w'))

#   with open(orig_ics_file) as orig_tex:
#     with open(current_ics_output) as current_tex:
#       assert orig_tex.read() == current_tex.read()


if __name__ == '__main__':
  # test_panchanga_chennai_2018()
  test_panchanga_chennai_2019()
