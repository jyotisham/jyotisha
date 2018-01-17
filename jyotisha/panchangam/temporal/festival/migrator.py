import logging
import os

from jyotisha.panchangam.spatio_temporal import CODE_ROOT
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


if __name__ == '__main__':
  # migrate_db(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'))
  # migrate_db(os.path.join(CODE_ROOT, 'panchangam/data/kanchi_aradhana_rules.json'))
  migrate_relative_db()