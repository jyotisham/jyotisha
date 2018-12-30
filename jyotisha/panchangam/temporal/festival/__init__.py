import json
import logging

import os

import sys

from jyotisha import custom_transliteration
from jyotisha.panchangam.spatio_temporal import CODE_ROOT
from sanskrit_data.schema import common
from indic_transliteration import xsanscript as sanscript

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
        "enum": ["tithi", "nakshatram", "yogam", "day"],
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
      "anchor_festival_id": {
        "type": "string",
        "description": "A festival may be (say) 8 days before some other event xyz. The xyz is stored here.",
      },
      "offset": {
        "type": "integer",
        "description": "A festival may be 8 days before some other event xyz. The 8 is stored here.",
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
    if hasattr(old_style_event, "anchor_festival_id"):
      import regex
      timing.anchor_festival_id = regex.sub(":", "__", old_style_event.anchor_festival_id)
    if hasattr(old_style_event, "offset"):
      timing.offset = old_style_event.offset
    timing.validate_schema()
    return timing


class HinduCalendarEventOld(common.JsonObject):
  pass

  @classmethod
  def from_legacy_event(cls, event_id, legacy_event_dict):
    event = HinduCalendarEventOld()
    event.id = event_id
    if (legacy_event_dict.get("Month Type", "") != ""):
      event.month_type = legacy_event_dict["Month Type"]
    if (legacy_event_dict.get("Month Number", "") != ""):
      event.month_number = legacy_event_dict["Month Number"]
    if (legacy_event_dict.get("Angam Type", "") != ""):
      event.angam_type = legacy_event_dict["Angam Type"]
    if (legacy_event_dict.get("Angam Number", "") != ""):
      event.angam_number = legacy_event_dict["Angam Number"]
    if (legacy_event_dict.get("Tags", "") != ""):
      event.tags = legacy_event_dict["Tags"]
    if (legacy_event_dict.get("Short Description", "") != ""):
      event.description = {
        "en": legacy_event_dict["Short Description"]
      }
    if (legacy_event_dict.get("priority", "") != ""):
      event.priority = legacy_event_dict["priority"].replace("purvaviddha", "puurvaviddha")
    if (legacy_event_dict.get("kala", "") != ""):
      event.kaala = legacy_event_dict["kala"].replace("madhyahna", "madhyaahna")
    if (legacy_event_dict.get("Shloka", "") != ""):
      event.shlokas = [legacy_event_dict["Shloka"]]
    if (legacy_event_dict.get("Comments", "") != ""):
      event.comments = legacy_event_dict["Comments"]
    if (legacy_event_dict.get("Secondary Reference", "") != ""):
      event.references_secondary = [legacy_event_dict["Secondary Reference"]]
    if (legacy_event_dict.get("Primary Reference", "") != ""):
      event.references_primary = [legacy_event_dict["Primary Reference"]]
    if (legacy_event_dict.get("Other Names", "") != ""):
      event.titles = legacy_event_dict["Other Names"]
    if (legacy_event_dict.get("offset", "") != ""):
      event.offset = legacy_event_dict["offset"]
    if (legacy_event_dict.get("Start Year", "") != ""):
      event.year_start = legacy_event_dict["Start Year"]
    if (legacy_event_dict.get("Relative Festival", "") != ""):
      event.anchor_festival_id = legacy_event_dict["Relative Festival"]
    return event

  def get_description_string(self, script):
    description_string = ""
    if hasattr(self, "description"):
      # description_string = json.dumps(self.description)
      description_string = self.description["en"]
      pieces = description_string.split('`')
      if len(pieces) > 1:
        if len(pieces) % 2 == 1:
          # We much have matching backquotes, the contents of which can be neatly transliterated
          for i, piece in enumerate(pieces):
            if (i % 2) == 1:
              pieces[i] = custom_transliteration.tr(piece, script, False)
          description_string = ''.join(pieces)
        else:
          logging.warning('Unmatched backquotes in description string: %s' % description_string)
    if hasattr(self, "shlokas"):
      description_string = description_string + '\n\n' + \
                           custom_transliteration.tr(", ".join(self.shlokas), script, False) + '\n\n'
    return description_string


# noinspection PyUnresolvedReferences
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
      import regex
      event.id = regex.sub(":", "__", old_style_event.id)
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
    if hasattr(old_style_event, "description"):
      event.description = old_style_event.description

    event.validate_schema()
    return event

  def get_description_string(self, script, includeShloka=False):
    description_string = ""
    if hasattr(self, "description"):
      # description_string = json.dumps(self.description)
      description_string = self.description["en"]
      pieces = description_string.split('`')
      if len(pieces) > 1:
        if len(pieces) % 2 == 1:
          # We much have matching backquotes, the contents of which can be neatly transliterated
          for i, piece in enumerate(pieces):
            if (i % 2) == 1:
              pieces[i] = custom_transliteration.tr(piece, script, False)
          description_string = ''.join(pieces)
        else:
          logging.warning('Unmatched backquotes in description string: %s' % description_string)
    if includeShloka and hasattr(self, "shlokas"):
      description_string = description_string + '\n\n' + \
                           custom_transliteration.tr(", ".join(self.shlokas), script, False) + '\n\n'
    return description_string

  def get_storage_file_name(self, base_dir, only_descriptions=False):
    if hasattr(self.timing, "anchor_festival_id"):
      return "%(base_dir)s/relative_event/%(anchor_festival_id)s/offset__%(offset)02d/%(id)s__info.json" % dict(
        base_dir=base_dir,
        anchor_festival_id=self.timing.anchor_festival_id.replace('/','__'),
        offset=self.timing.offset,
        id=self.id.replace('/','__')
      )
    else:
      if only_descriptions:
        return "%(base_dir)s/other/%(id)s__info.json" % dict(
          base_dir=base_dir,
          id=self.id.replace('/','__')
        )
      else:
        return "%(base_dir)s/%(month_type)s/%(angam_type)s/%(month_number)02d__%(angam_number)02d/%(id)s__info.json" % dict(
          base_dir=base_dir,
          month_type=self.timing.month_type,
          angam_type=self.timing.angam_type,
          month_number=self.timing.month_number,
          angam_number=self.timing.angam_number,
          id=self.id.replace('/','__')
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
