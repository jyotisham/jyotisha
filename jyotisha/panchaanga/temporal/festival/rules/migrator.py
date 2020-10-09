import json
import logging
import os

from jyotisha import custom_transliteration
# from jyotisha.panchaanga.temporal import festival
from jyotisha.panchaanga.temporal.festival import rules
from jyotisha.util import default_if_none
from sanskrit_data.schema.common import JsonObject

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def transliterate_quoted_text(text, script):
  transliterated_text = text
  pieces = transliterated_text.split('`')
  if len(pieces) > 1:
    if len(pieces) % 2 == 1:
      # We much have matching backquotes, the contents of which can be neatly transliterated
      for i, piece in enumerate(pieces):
        if (i % 2) == 1:
          pieces[i] = custom_transliteration.tr(piece, script, titled=True)
      transliterated_text = ''.join(pieces)
    else:
      logging.warning('Unmatched backquotes in string: %s' % transliterated_text)
  return transliterated_text


def migrate_db(dir_path):
  festival_rules_dict = rules.get_festival_rules_map(dir_path)
  output_dir = os.path.join(os.path.dirname(__file__), 'data')
  # import shutil
  # shutil.rmtree(output_dir)
  for event in festival_rules_dict.values():
    logging.info("Migrating %s", event.id)
    event.names = default_if_none(x=event.names, default={})
    sa_names = event.names.get("sa", [])
    ta_names = event.names.get("ta", [])
    if "Mahapurusha" not in ",".join(event.tags):
      event_file_name = event.get_storage_file_name(base_dir=os.path.join(output_dir, "migrated/general"))
    elif "Mahapurusha" in ",".join(event.tags):
      event_file_name = event.get_storage_file_name(base_dir=os.path.join(output_dir, "Mahapurusha/general"))
    logging.debug(event_file_name)
    event.dump_to_file(filename=event_file_name)
    # append_to_event_group_README(event, event_file_name)


def clear_output_dirs():
  import shutil
  for dir in ["lunar_month", "other", "relative_event", "sidereal_solar_month"]:
    shutil.rmtree(os.path.join(os.path.dirname(__file__), 'data', dir), ignore_errors=True)


if __name__ == '__main__':
  clear_output_dirs()
  migrate_db(os.path.join(os.path.dirname(__file__), 'data/general'))
  # migrate_db(os.path.join(os.path.dirname(__file__), 'data/tamil'))
  pass
