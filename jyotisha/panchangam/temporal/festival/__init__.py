import json

import os

from jyotisha.panchangam.spatio_temporal import CODE_ROOT

festival_rules = {}

def load_festival_rules():
  global festival_rules
  with open(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'), encoding="utf-8") as festivals_data:
    festival_rules = json.load(festivals_data, encoding="utf-8")
