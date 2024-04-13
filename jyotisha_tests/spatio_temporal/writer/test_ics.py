import logging
import os

from indic_transliteration import sanscript
from jyotisha.panchaanga.writer.ics import compute_calendar, write_to_file
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


def test_panchanga_chennai_2019():
  panchaanga_2019 = Panchaanga.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2019.json'))
  orig_ics_file = os.path.join(TEST_DATA_PATH, 'Chennai-2019-devanagari.ics')
  current_ics_output = os.path.join(TEST_DATA_PATH, 'Chennai-2019-devanagari.ics.local')
  ics_calendar = compute_calendar(panchaanga_2019, scripts=[sanscript.ISO], set_sequence=False)
  write_to_file(ics_calendar, current_ics_output)
  if not os.path.exists(orig_ics_file):
    logging.warning("%s not present. Assuming that it was deliberately deleted to update test files.", orig_ics_file)
    write_to_file(ics_calendar, orig_ics_file)

  ics_file_match = True
  with open(orig_ics_file) as orig_ics:
    with open(current_ics_output) as current_ics:
      for line1, line2 in zip(current_ics, orig_ics):
        if line1.startswith("DTSTAMP") and line2.startswith("DTSTAMP"):
          continue
        if line1 != line2:
          ics_file_match = False
          break
  
  assert ics_file_match == True

if __name__ == '__main__':
  # test_panchanga_chennai_2018()
  test_panchanga_chennai_2019()
