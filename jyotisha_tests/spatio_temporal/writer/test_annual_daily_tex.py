import logging
import os

from indic_transliteration import sanscript
from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga

from jyotisha.panchaanga.writer.tex.daily_tex_writer import emit

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


def daily_tex_comparer(city_name, year):
  from jyotisha_tests.spatio_temporal import get_panchaanga_from_previous_test
  panchaanga = get_panchaanga_from_previous_test(city_name=city_name, year=year)
  panchaanga.update_festival_details()
  orig_tex_file = os.path.join(TEST_DATA_PATH, 'daily-cal-%s-%s-deva.tex' % (year, city_name))
  current_tex_output = os.path.join(TEST_DATA_PATH, 'daily-cal-%s-%s-deva.tex.local' % (year, city_name))
  emit(panchaanga,
       output_stream=open(current_tex_output, 'w'), languages=["sa", "ta"], scripts=[sanscript.DEVANAGARI, sanscript.TAMIL])

  if not os.path.exists(orig_tex_file):
    logging.warning("Files must have been deliberately deleted due to changed expectation. We'll just set it for future tests.")
    emit(panchaanga,
       output_stream=open(orig_tex_file, 'w'), languages=["sa", "ta"], scripts=[sanscript.DEVANAGARI, sanscript.TAMIL])
  else:
    with open(orig_tex_file) as orig_tex:
      with open(current_tex_output) as current_tex:
        assert current_tex.read() == orig_tex.read()


def test_panchaanga_chennai_2019():
  daily_tex_comparer(city_name="Chennai", year=2019)


def test_panchaanga_orinda_2019():
  daily_tex_comparer(city_name="Orinda", year=2019)


def test_panchaanga_chennai_2018():
  daily_tex_comparer(city_name="Chennai", year=2018)

