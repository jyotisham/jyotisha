import json
import logging

import os

import sys

from jyotisha.panchangam.spatio_temporal import CODE_ROOT
from sanskrit_data.schema import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

festival_id_to_json = {}


class HinduCalendarEventTiming(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["HinduCalendarEventTiming"]
      },
      "month_type": {
        "type": "string",
        "enum": ["lunar_month", "solar_month"],
        "description": "",
      },
      "month_number": {
        "type": "integer",
        "description": "",
      },
      "angam_type": {
        "type": "string",
        "enum": ["tithi", "nakshatram", "day"],
        "description": "",
      },
      "angam_number": {
        "type": "integer",
        "description": "",
      },
      "kaala": {
        "type": "string",
        "description": "",
      },
      "year_start": {
        "type": "integer",
        "description": "",
      },
    }
  }))


class HinduCalendarEventOld(common.JsonObject):
  pass


class HinduCalendarEvent(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["HinduCalendarEvent"]
      },
      "timing": {
        "type": HinduCalendarEventTiming.schema
      },
      "tags": {
        "type": "array",
        "items": "string",
        "description": "",
      },
      "priority": {
        "type": "string",
        "description": "",
      },
      "comments": {
        "type": "string",
        "description": "",
      },
      "description_short": {
        "type": "object",
        "description": "",
      },
      "titles": {
        "type": "string",
      },
      "shlokas": {
        "type": "array",
        "items": "string"
      },
      "references_primary": {
        "type": "array",
        "items": "string"
      },
      "references_secondary": {
        "type": "array",
        "items": "string"
      },
    }
  }))


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


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)
