import json
import logging
import os
import re
import sys
from pathlib import Path

from indic_transliteration import xsanscript as sanscript
from sanskrit_data.schema import common

from jyotisha import custom_transliteration
from jyotisha.names import get_chandra_masa, NAMES


def transliterate_quoted_text(text, script):
  transliterated_text = text
  pieces = transliterated_text.split('`')
  if len(pieces) > 1:
    if len(pieces) % 2 == 1:
      # We much have matching backquotes, the contents of which can be neatly transliterated
      for i, piece in enumerate(pieces):
        if (i % 2) == 1:
          pieces[i] = custom_transliteration.tr(piece, script, titled=True)
      transliterated_text = ''.join(pieces)
    else:
      logging.warning('Unmatched backquotes in string: %s' % transliterated_text)
  return transliterated_text



class HinduCalendarEventTiming(common.JsonObject):
  schema = common.recursively_merge_json_schemas(common.JsonObject.schema, ({
    "type": "object",
    "properties": {
      common.TYPE_FIELD: {
        "enum": ["HinduCalendarEventTiming"]
      },
      "month_type": {
        "type": "string",
        "enum": ["lunar_month", "sidereal_solar_month", "tropical_month"],
        "description": "",
      },
      "month_number": {
        "type": "integer",
        "description": "",
      },
      "anga_type": {
        "type": "string",
        "enum": ["tithi", "nakshatra", "yoga", "day"],
        "description": "",
      },
      "anga_number": {
        "type": "integer",
        "description": "",
      },
      "kaala": {
        "type": "string",
        "description": "",
      },
      "priority": {
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
  def from_details(cls, month_type, month_number, anga_type, anga_number, kaala, year_start):
    timing = HinduCalendarEventTiming()
    timing.month_type = month_type
    timing.month_number = month_number
    timing.anga_type = anga_type
    timing.anga_number = anga_number
    timing.kaala = kaala
    timing.year_start = year_start
    timing.validate_schema()
    return timing

  @classmethod
  def from_old_style_event(cls, old_style_event):
    timing = HinduCalendarEventTiming()
    if getattr(old_style_event, "month_type", None) is not None:
      timing.month_type = old_style_event.month_type
    if getattr(old_style_event, "priority", None) is not None:
      timing.priority = old_style_event.priority
    if getattr(old_style_event, "month_number", None) is not None:
      timing.month_number = old_style_event.month_number
    if getattr(old_style_event, "anga_type", None) is not None:
      timing.anga_type = old_style_event.anga_type
    if getattr(old_style_event, "anga_number", None) is not None:
      timing.anga_number = old_style_event.anga_number
    if getattr(old_style_event, "kaala", None) is not None:
      timing.kaala = old_style_event.kaala
    if getattr(old_style_event, "year_start", None) is not None:
      timing.year_start = old_style_event.year_start
    if getattr(old_style_event, "anchor_festival_id", None) is not None:
      import regex
      timing.anchor_festival_id = regex.sub(":", "__", old_style_event.anchor_festival_id)
    if getattr(old_style_event, "offset", None) is not None:
      timing.offset = old_style_event.offset
    timing.validate_schema()
    return timing


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
      "comments": {
        "type": "string",
        "description": "",
      },
      "image": {
        "type": "string",
        "description": "",
      },
      "description": {
        "type": "object",
        "description": "Language code to text mapping.",
      },
      "names": {
        "type": "object",
        "description": "Language code to text array mapping.",
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
    if getattr(old_style_event, "id", None) is not None:
      import regex
      event.id = regex.sub(":", "__", old_style_event.id)
      id_parts = event.id.split("__")
      if len(id_parts) > 1:
        event.script_priority = id_parts[0]
    if getattr(old_style_event, "tags", None) is not None and old_style_event.tags is not None:
      event.tags = [x.strip() for x in old_style_event.tags.split(",")]
    if getattr(old_style_event, "titles", None) is not None and old_style_event.titles is not None:
      event.titles = [x.strip() for x in old_style_event.titles.split(";")]
    if getattr(old_style_event, "shlokas", None) is not None:
      event.shlokas = old_style_event.shlokas
    if getattr(old_style_event, "comments", None) is not None:
      event.comments = old_style_event.comments
    if getattr(old_style_event, "image", None) is not None:
      event.image = old_style_event.image
    if getattr(old_style_event, "references_primary", None) is not None:
      event.references_primary = old_style_event.references_primary
    if getattr(old_style_event, "references_secondary", None) is not None:
      event.references_secondary = old_style_event.references_secondary
    if getattr(old_style_event, "description_short", None) is not None:
      event.description_short = old_style_event.description_short
    if getattr(old_style_event, "description", None) is not None:
      event.description = old_style_event.description

    event.validate_schema()
    return event

  def get_storage_file_name(self, base_dir, only_descriptions=False):
    if self.timing.anchor_festival_id is not None:
      return "%(base_dir)s/relative_event/%(anchor_festival_id)s/offset__%(offset)02d/%(id)s__info.toml" % dict(
        base_dir=base_dir,
        anchor_festival_id=self.timing.anchor_festival_id.replace('/','__'),
        offset=self.timing.offset,
        id=self.id.replace('/','__').strip('{}')
      )
    else:
      if only_descriptions:
        tag_list = '/'.join(self.tags)
        return "%(base_dir)s/other/%(tags)s/%(id)s__info.toml" % dict(
          base_dir=base_dir,
          tags=tag_list,
          id=self.id.replace('/','__').strip('{}')
        )
      else:
        return "%(base_dir)s/%(month_type)s/%(anga_type)s/%(month_number)02d/%(anga_number)02d/%(id)s__info.toml" % dict(
          base_dir=base_dir,
          month_type=self.timing.month_type,
          anga_type=self.timing.anga_type,
          month_number=self.timing.month_number,
          anga_number=self.timing.anga_number,
          id=self.id.replace('/','__').strip('{}')
        )

  def get_description_string(self, script, include_url=False, include_images=False, use_markup=False,
                             include_shlokas=False, is_brief=False, truncate=False):
    # Get the Blurb
    blurb = ''
    month = ''
    angam = ''
    if self.timing is not None and self.timing.month_type is not None:
      if self.timing.month_type == 'lunar_month':
        if self.timing.month_number == 0:
          month = ' of every lunar month'
        else:
          month = ' of ' + get_chandra_masa(self.timing.month_number, NAMES, sanscript.IAST) + ' (lunar) month'
      elif self.timing.month_type == 'sidereal_solar_month':
        if self.timing.month_number == 0:
          month = ' of every solar month'
        else:
          month = ' of ' + NAMES['RASHI_NAMES'][sanscript.IAST][self.timing.month_number] + ' (solar) month'
    if self.timing is not None and self.timing.anga_type is not None:
      # logging.debug(self.id)
      # if self.id.startswith("ta:"):
      #   anga = custom_transliteration.tr(self.id[3:], sanscript.TAMIL).replace("~", " ").strip("{}") + ' is observed on '
      # else:
      #   anga = custom_transliteration.tr(self.id, sanscript.DEVANAGARI).replace("~", " ") + ' is observed on '
      angam = 'Observed on '

      if self.timing.anga_type == 'tithi':
        angam += NAMES['TITHI_NAMES'][sanscript.IAST][self.timing.anga_number] + ' tithi'
      elif self.timing.anga_type == 'nakshatra':
        angam += NAMES['NAKSHATRA_NAMES'][sanscript.IAST][self.timing.anga_number] + ' nakṣhatram day'
      elif self.timing.anga_type == 'day':
        angam += 'day %d' % self.timing.anga_number
    else:
      if self.description is None:
        logging.debug("No anga_type in %s or description even!!", self.id)
    if self.timing is not None and self.timing.kaala is not None:
      kaala = self.timing.kaala
    else:
      kaala = "sunrise (default)"
    if self.timing is not None and self.timing.priority is not None:
      priority = self.timing.priority
    else:
      priority = 'puurvaviddha (default)'
    if angam is not None:
      blurb += angam
    if month is not None:
      blurb += month
    if blurb != '':
      blurb += ' (%s/%s).\n' % (kaala, priority)
      # logging.debug(blurb)

    # Get the URL
    if include_url:
      base_url = 'https://github.com/sanskrit-coders/adyatithi/tree/master'
      if self.timing is not None and self.timing.anga_type is not None:
        url = "%(base_dir)s/%(month_type)s/%(anga_type)s/%(month_number)02d/%(anga_number)02d#%(id)s" % dict(
          base_dir=base_url,
          month_type=self.timing.month_type,
          anga_type=self.timing.anga_type,
          month_number=self.timing.month_number,
          anga_number=self.timing.anga_number,
          id=custom_transliteration.tr(self.id, sanscript.IAST).replace('Ta__', '').replace('~', ' ').replace(' ',
                                                                                                              '-').replace(
            '(', '').replace(')', '').strip('{}').lower())
      elif self.timing is not None and self.timing.anchor_festival_id is not None:
        url = "%(base_dir)s/relative_event/%(anchor_festival_id)s/offset__%(offset)02d#%(id)s" % dict(
          base_dir=base_url,
          anchor_festival_id=self.timing.anchor_festival_id.replace('/', '__'),
          offset=self.timing.offset,
          id=custom_transliteration.tr(self.id, sanscript.IAST).replace('Ta__', '').replace('~', ' ').replace(' ',
                                                                                                              '-').strip(
            '{}').lower())
      else:
        tag_list = '/'.join([re.sub('([a-z])([A-Z])', r'\1-\2', t).lower() for t in self.tags])
        url = "%(base_dir)s/other/%(tags)s#%(id)s" % dict(
          base_dir=base_url,
          tags=tag_list,
          id=custom_transliteration.tr(self.id, sanscript.IAST).replace('Ta__', '').replace('~', ' ').replace(' ',
                                                                                                              '-').strip(
            '{}').lower())

    # Get the description
    description_string = ''
    if self.description is not None:
      # description_string = json.dumps(self.description)
      description_string += self.description["en"]
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

    if self.shlokas is not None and include_shlokas:
      if use_markup:
        description_string = description_string + '\n\n```\n' + custom_transliteration.tr(", ".join(self.shlokas),
                                                                                          script, False) + '\n```'
      else:
        description_string = description_string + '\n\n' + custom_transliteration.tr(", ".join(self.shlokas), script,
                                                                                     False) + '\n\n'

    if include_images:
      if self.image is not None:
        image_string = '![](https://github.com/sanskrit-coders/adyatithi/blob/master/images/%s)\n\n' % self.image

    ref_list = ''
    if self.references_primary is not None or self.references_secondary is not None:
      ref_list = '\n### References\n'
      if self.references_primary is not None:
        for ref in self.references_primary:
          ref_list += '* %s\n' % transliterate_quoted_text(ref, sanscript.IAST)
      elif self.references_secondary is not None:
        for ref in self.references_secondary:
          ref_list += '* %s\n' % transliterate_quoted_text(ref, sanscript.IAST)

    # Now compose the description string based on the values of
    # include_url, include_images, use_markup, is_brief
    if not is_brief:
      final_description_string = blurb
    else:
      if include_url:
        final_description_string = url
      else:
        final_description_string = ''

    final_description_string += description_string

    if include_images:
      final_description_string += image_string

    if truncate:
      if len(final_description_string) > 450:
        # Truncate
        final_description_string = ' '.join(final_description_string[:450].split(' ')[:-1]) + ' ...\n'

    if not is_brief:
      final_description_string += ref_list

    if not is_brief and include_url:
      # if use_markup:
      final_description_string += ('\n\n%s\n' % url) + '\n' + ' '.join(['#' + x for x in self.tags])
    # else:
    #   final_description_string += ('\n\n%s\n' % url) + '\n' + ' '.join(['#' + x for x in self.tags])

    # if use_markup:
    #   final_description_string = final_description_string.replace('\n', '<br/><br/>')

    return final_description_string



def get_festival_rules_map(dir_path):
  toml_file_paths = sorted(Path(dir_path).glob("**/*.toml"))
  if len(toml_file_paths) == 0:
    raise ValueError
  festival_rules = {}
  for file_path in toml_file_paths:
    event = HinduCalendarEvent.read_from_file(filename=str(file_path))
    festival_rules[event.id] = event
  return festival_rules


def read_old_festival_rules_dict(file_name):
  with open(file_name, encoding="utf-8") as festivals_data:
    festival_rules_dict = json.load(festivals_data)
    for festival_rule in festival_rules_dict:
      festival_rules = {}
      festival_rules[festival_rule.id] = festival_rule
    return festival_rules


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
      event.anga_type = legacy_event_dict["Angam Type"]
    if (legacy_event_dict.get("Angam Number", "") != ""):
      event.anga_number = legacy_event_dict["Angam Number"]
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


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)


DATA_ROOT = os.path.join(os.path.dirname(__file__), "data")
festival_rules_lunar = get_festival_rules_map(
  os.path.join(DATA_ROOT, 'lunar_month'))
festival_rules_solar = get_festival_rules_map(
  os.path.join(DATA_ROOT, 'sidereal_solar_month'))
festival_rules_rel = get_festival_rules_map(
  os.path.join(DATA_ROOT, 'relative_event'))
festival_rules_desc_only = get_festival_rules_map(
  os.path.join(DATA_ROOT, 'other'))
festival_rules_all = {**festival_rules_solar, **festival_rules_lunar, **festival_rules_rel, **festival_rules_desc_only}

