import logging
import os

from doc_curation.md.file import MdFile

from jyotisha.panchaanga.spatio_temporal.periodical import Panchaanga
from jyotisha.panchaanga.writer import md

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)



TEST_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')


def test_panchanga_chennai_2019():
  panchaanga_2019 = Panchaanga.read_from_file(filename=os.path.join(TEST_DATA_PATH, 'Chennai-2019.json'))
  # We dump to md.txt rather than md to avoid slow checks on intellij ide.
  orig_md_file = os.path.join(TEST_DATA_PATH, 'Chennai-2019-devanagari.md.txt')
  current_md_output = os.path.join(TEST_DATA_PATH, 'Chennai-2019-devanagari.md.txt.local')
  md_file = MdFile(file_path=current_md_output)
  md_file.dump_to_file(metadata={"title": str(2019)}, content=md.make_md(panchaanga=panchaanga_2019), dry_run=False)
  if not os.path.exists(orig_md_file):
    logging.warning("%s not present. Assuming that it was deliberately deleted to update test files.", orig_md_file)
    md_file = MdFile(file_path=orig_md_file)
    md_file.dump_to_file(metadata={"title": str(2019)}, content=md.make_md(panchaanga=panchaanga_2019), dry_run=False)
    

  with open(orig_md_file) as orig_tex:
    with open(current_md_output) as current_tex:
      assert current_tex.read() == orig_tex.read()


if __name__ == '__main__':
  # test_panchanga_chennai_2018()
  test_panchanga_chennai_2019()
