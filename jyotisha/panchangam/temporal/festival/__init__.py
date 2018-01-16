import json

import os

from jyotisha.panchangam.spatio_temporal import CODE_ROOT

def read_old_festival_rules_dict(file_name):
  with open(file_name, encoding="utf-8") as festivals_data:
    festival_rules_dict = json.load(festivals_data, encoding="utf-8")
    festival_rules = {}
    for festival_rule in festival_rules_dict:
      festival_rules[festival_rule["id"]] = festival_rule
    return festival_rules
