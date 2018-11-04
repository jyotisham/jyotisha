import json
import logging
import os

from sanskrit_data.schema.common import JsonObject

from jyotisha.panchangam.spatio_temporal import CODE_ROOT
from jyotisha.panchangam.temporal import festival
from jyotisha.panchangam.temporal.festival import HinduCalendarEventOld, HinduCalendarEvent

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def migrate_db(old_db_file):
  old_style_events = HinduCalendarEventOld.read_from_file(old_db_file)
  for old_style_event in old_style_events:
    event = HinduCalendarEvent.from_old_style_event(old_style_event=old_style_event)
    logging.debug(str(event))
    event_file_name = event.get_storage_file_name(base_dir=os.path.join(CODE_ROOT, 'panchangam/temporal/festival/data'))
    logging.debug(event_file_name)
    event.dump_to_file(filename=event_file_name)


def migrate_relative_db():
  old_style_events = HinduCalendarEventOld.read_from_file(os.path.join(CODE_ROOT, 'panchangam/data/relative_festival_rules.json'))
  for old_style_event in old_style_events:
    event = HinduCalendarEvent.from_old_style_event(old_style_event=old_style_event)
    logging.debug(str(event))
    event_file_name = event.get_storage_file_name(base_dir=os.path.join(CODE_ROOT, 'panchangam/temporal/festival/data'))
    logging.debug(event_file_name)
    event.dump_to_file(filename=event_file_name)


def legacy_dict_to_HinduCalendarEventOld_list(old_db_file, new_db_file):
  with open(old_db_file, 'r') as f:
    legacy_event_dict = json.load(f)
  old_style_events = []
  for id, legacy_event in legacy_event_dict.items():
    event_old_style = HinduCalendarEventOld.from_legacy_event(id, legacy_event)
    old_style_events.append(event_old_style)
  json_map_list = JsonObject.get_json_map_list(old_style_events)
  with open(new_db_file, 'w') as f:
    json.dump(json_map_list, f, indent=4, sort_keys=True)


if __name__ == '__main__':
  # migrate_db(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'))
  # migrate_db(os.path.join(CODE_ROOT, 'panchangam/data/kanchi_aradhana_rules.json'))
  # migrate_relative_db()
  legacy_dict_to_HinduCalendarEventOld_list(os.path.join(CODE_ROOT, 'panchangam/data/legacy/festival_rules.json'), os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'))
  legacy_dict_to_HinduCalendarEventOld_list(os.path.join(CODE_ROOT, 'panchangam/data/legacy/festival_rules_desc_only.json'), os.path.join(CODE_ROOT, 'panchangam/data/festival_rules_desc_only.json'))
  legacy_dict_to_HinduCalendarEventOld_list(os.path.join(CODE_ROOT, 'panchangam/data/legacy/relative_festival_rules.json'), os.path.join(CODE_ROOT, 'panchangam/data/relative_festival_rules.json'))
  pass