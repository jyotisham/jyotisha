import logging
import os

# from jyotisha.panchaanga.spatio_temporal import City, annual
# from jyotisha.panchaanga.scripts.write_daily_panchaanga_tex import writeDailyTeX
from jyotisha.panchaanga.scripts.ics import compute_calendar, write_to_file
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga

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


def test_panchanga_chennai_2019():
  panchaanga_2019 = Panchaanga.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2019.json'))
  panchaanga_2019.update_festival_details()
  orig_ics_file = os.path.join(TEST_DATA_PATH, 'Chennai-2019-devanagari.ics')
  current_ics_output = os.path.join(TEST_DATA_PATH, 'Chennai-2019-devanagari.ics.local')
  ics_calendar = compute_calendar(panchaanga_2019, all_tags=True)
  write_to_file(ics_calendar, current_ics_output)

  with open(orig_ics_file) as orig_tex:
    with open(current_ics_output) as current_tex:
      assert current_tex.read() == orig_tex.read()


if __name__ == '__main__':
  # test_panchanga_chennai_2018()
  test_panchanga_chennai_2019()
