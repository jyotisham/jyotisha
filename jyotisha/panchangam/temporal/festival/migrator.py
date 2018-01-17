import json
import logging
import os

from jyotisha.panchangam.spatio_temporal import CODE_ROOT
from jyotisha.panchangam.temporal.festival import HinduCalendarEventOld

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def migrate_db():
  events = HinduCalendarEventOld.read_from_file(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'))
  for event in events:
    logging.debug(str(event))


if __name__ == '__main__':
    migrate_db()