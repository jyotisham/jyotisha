import json
import os

from jyotisha.panchangam.spatio_temporal import CODE_ROOT


def migrate_db():
  with open(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'), encoding="utf-8") as festivals_data:
    festival_rules = json.load(festivals_data, encoding="utf-8")
    pass

if __name__ == '__main__':
    migrate_db()