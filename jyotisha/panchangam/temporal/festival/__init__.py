import json

import os

from jyotisha.panchangam.spatio_temporal import CODE_ROOT

festival_id_to_json = {}


def read_old_festival_rules_dict(file_name):
  with open(file_name, encoding="utf-8") as festivals_data:
    festival_rules_dict = json.load(festivals_data, encoding="utf-8")
    festival_rules = {}
    for festival_rule in festival_rules_dict:
      festival_rules[festival_rule["id"]] = festival_rule
    return festival_rules


def fill_festival_id_to_json():
  global festival_id_to_json
  if len(festival_id_to_json) == 0:
    festival_rules = read_old_festival_rules_dict(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules.json'))
    festival_id_to_json.update(festival_rules)
    festival_rules = read_old_festival_rules_dict(os.path.join(CODE_ROOT, 'panchangam/data/relative_festival_rules.json'))
    festival_id_to_json.update(festival_rules)
    festival_rules = read_old_festival_rules_dict(os.path.join(CODE_ROOT, 'panchangam/data/festival_rules_desc_only.json'))
    festival_id_to_json.update(festival_rules)