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

  @classmethod
  def from_details(cls, month_type, month_number, angam_type, angam_number, kaala, year_start):
    timing = HinduCalendarEventTiming()
    timing.month_type = month_type
    timing.month_number = month_number
    timing.angam_type = angam_type
    timing.angam_number = angam_number
    timing.kaala = kaala
    timing.year_start = year_start
    timing.validate_schema()
    return timing


  @classmethod
  def from_old_style_event(cls, old_style_event):
    timing = HinduCalendarEventTiming()
    if hasattr(old_style_event, "month_type"):
      timing.month_type = old_style_event.month_type
    if hasattr(old_style_event, "month_number"):
      timing.month_number = old_style_event.month_number
    if hasattr(old_style_event, "angam_type"):
      timing.angam_type = old_style_event.angam_type
    if hasattr(old_style_event, "angam_number"):
      timing.angam_number = old_style_event.angam_number
    if hasattr(old_style_event, "kaala"):
      timing.kaala = old_style_event.kaala
    if hasattr(old_style_event, "year_start"):
      timing.year_start = old_style_event.year_start
    timing.validate_schema()
    return timing


class HinduCalendarEventOld(common.JsonObject):
  pass


class HinduCalendarEvent(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["HinduCalendarEvent"]
      },
      "timing": HinduCalendarEventTiming.schema,
      "tags": {
        "type": "array",
        "items": {
          "type": "string"
        },
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
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "shlokas": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "references_primary": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "references_secondary": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
    }
  }))

  @classmethod
  def from_old_style_event(cls, old_style_event):
    event = HinduCalendarEvent()
    event.timing = HinduCalendarEventTiming.from_old_style_event(old_style_event=old_style_event)
    if hasattr(old_style_event, "id"):
      event.id = old_style_event.id
    if hasattr(old_style_event, "tags") and old_style_event.tags is not None:
      event.tags = [x.strip() for x in old_style_event.tags.split(",")]
    if hasattr(old_style_event, "titles") and old_style_event.titles is not None:
      event.titles = [x.strip() for x in old_style_event.titles.split(";")]
    if hasattr(old_style_event, "shlokas"):
      event.shlokas = old_style_event.shlokas
    if hasattr(old_style_event, "priority"):
      event.priority = old_style_event.priority
    if hasattr(old_style_event, "comments"):
      event.comments = old_style_event.comments
    if hasattr(old_style_event, "references_primary"):
      event.references_primary = old_style_event.references_primary
    if hasattr(old_style_event, "references_secondary"):
      event.references_secondary = old_style_event.references_secondary
    if hasattr(old_style_event, "description_short"):
      event.description_short = old_style_event.description_short

    event.validate_schema()
    return event

  def get_storage_file_name(self, base_dir):
    return "%(base_dir)s/%(month_type)s/%(angam_type)s/%(month_number)02d__%(angam_number)02d/%(id)s__info.json" % dict(
      base_dir=base_dir,
      month_type=self.timing.month_type,
      angam_type=self.timing.angam_type,
      month_number=self.timing.month_number,
      angam_number=self.timing.angam_number,
      id=self.id
    )


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
