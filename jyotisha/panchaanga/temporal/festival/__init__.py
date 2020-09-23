import json
import logging
import os
import re
import sys

from indic_transliteration import xsanscript as sanscript

from jyotisha import custom_transliteration
from jyotisha.names import get_chandra_masa, NAMES
from jyotisha.panchaanga.spatio_temporal import CODE_ROOT
from sanskrit_data.schema import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

festival_id_to_json = {}


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
        "enum": ["lunar_month", "solar_month"],
        "description": "",
      },
      "month_number": {
        "type": "integer",
        "description": "",
      },
      "angam_type": {
        "type": "string",
        "enum": ["tithi", "nakshatram", "yoga", "day"],
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

  def get_description_string(self, script, include_url=False, include_images=False, use_markup=False,
                             include_shlokas=False, is_brief=False, truncate=False):
    # Get the Blurb
    blurb = ''
    month = ''
    angam = ''
    if hasattr(self, "month_type"):
      if self.month_type == 'lunar_month':
        if self.month_number == 0:
          month = ' of every lunar month'
        else:
          month = ' of ' + get_chandra_masa(self.month_number, NAMES, sanscript.IAST) + ' (lunar) month'
      elif self.month_type == 'solar_month':
        if self.month_number == 0:
          month = ' of every solar month'
        else:
          month = ' of ' + NAMES['RASHI_NAMES'][sanscript.IAST][self.month_number] + ' (solar) month'
    if hasattr(self, "angam_type"):
      # logging.debug(self.id)
      # if self.id.startswith("ta:"):
      #   angam = custom_transliteration.tr(self.id[3:], sanscript.TAMIL).replace("~", " ").strip("{}") + ' is observed on '
      # else:
      #   angam = custom_transliteration.tr(self.id, sanscript.DEVANAGARI).replace("~", " ") + ' is observed on '
      angam = 'Observed on '

      if self.angam_type == 'tithi':
        angam += NAMES['TITHI_NAMES'][sanscript.IAST][self.angam_number] + ' tithi'
      elif self.angam_type == 'nakshatram':
        angam += NAMES['NAKSHATRAM_NAMES'][sanscript.IAST][self.angam_number] + ' nakṣhatram day'
      elif self.angam_type == 'day':
        angam += 'day %d' % self.angam_number
    else:
      if not hasattr(self, "description"):
        logging.debug("No angam_type in %s or description even!!", self.id)
    if hasattr(self, "kaala"):
      kaala = self.kaala
    else:
      kaala = "sunrise (default)"
    if hasattr(self, "priority"):
      priority = self.priority
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
      base_url = 'https://github.com/sanskrit-coders/adyatithi/tree/master/data'
      if hasattr(self, "angam_type"):
        url = "%(base_dir)s/%(month_type)s/%(angam_type)s/%(month_number)02d/%(angam_number)02d#%(id)s" % dict(
          base_dir=base_url,
          month_type=self.month_type,
          angam_type=self.angam_type,
          month_number=self.month_number,
          angam_number=self.angam_number,
          id=custom_transliteration.tr(self.id, sanscript.IAST).replace('Ta__', '').replace('~', ' ').replace(' ',
                                                                                                              '-').replace(
            '(', '').replace(')', '').strip('{}').lower())
      elif hasattr(self, "anchor_festival_id"):
        url = "%(base_dir)s/relative_event/%(anchor_festival_id)s/offset__%(offset)02d#%(id)s" % dict(
          base_dir=base_url,
          anchor_festival_id=self.anchor_festival_id.replace('/', '__'),
          offset=self.offset,
          id=custom_transliteration.tr(self.id, sanscript.IAST).replace('Ta__', '').replace('~', ' ').replace(' ',
                                                                                                              '-').strip(
            '{}').lower())
      else:
        tag_list = '/'.join([re.sub('([a-z])([A-Z])', r'\1-\2', t).lower() for t in self.tags.split(',')])
        url = "%(base_dir)s/other/%(tags)s#%(id)s" % dict(
          base_dir=base_url,
          tags=tag_list,
          id=custom_transliteration.tr(self.id, sanscript.IAST).replace('Ta__', '').replace('~', ' ').replace(' ',
                                                                                                              '-').strip(
            '{}').lower())

    # Get the description
    description_string = ''
    if hasattr(self, "description"):
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

    if hasattr(self, "shlokas") and include_shlokas:
      if use_markup:
        description_string = description_string + '\n\n```\n' + custom_transliteration.tr(", ".join(self.shlokas),
                                                                                          script, False) + '\n```'
      else:
        description_string = description_string + '\n\n' + custom_transliteration.tr(", ".join(self.shlokas), script,
                                                                                     False) + '\n\n'

    if include_images:
      if hasattr(self, "image"):
        image_string = '![](https://github.com/sanskrit-coders/adyatithi/blob/master/images/%s)\n\n' % self.image

    ref_list = ''
    if hasattr(self, "references_primary") or hasattr(self, "references_secondary"):
      ref_list = '\n### References\n'
      if hasattr(self, "references_primary"):
        for ref in self.references_primary:
          ref_list += '* %s\n' % transliterate_quoted_text(ref, sanscript.IAST)
      elif hasattr(self, "references_secondary"):
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
      final_description_string += ('\n\n%s\n' % url) + '\n' + ' '.join(['#' + x for x in self.tags.split(',')])
    # else:
    #   final_description_string += ('\n\n%s\n' % url) + '\n' + ' '.join(['#' + x for x in self.tags.split(',')])

    # if use_markup:
    #   final_description_string = final_description_string.replace('\n', '<br/><br/>')

    return final_description_string


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
      "image": {
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
    if hasattr(old_style_event, "image"):
      event.image = old_style_event.image
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

  def get_description_string(self, script, include_url=False, include_images=False, use_markup=False,
                             include_shlokas=False, is_brief=False):
    # Get the Blurb
    blurb = ''
    month = ''
    angam = ''
    if hasattr(self, "month_type"):
      if self.month_type == 'lunar_month':
        if self.month_number == 0:
          month = ' of every lunar month'
        else:
          month = ' of ' + get_chandra_masa(self.month_number, NAMES, sanscript.IAST) + ' (lunar) month'
      elif self.month_type == 'solar_month':
        if self.month_number == 0:
          month = ' of every solar month'
        else:
          month = ' of ' + NAMES['RASHI_NAMES'][sanscript.IAST][self.month_number] + ' (solar) month'
    if hasattr(self, "angam_type"):
      logging.debug(self.id)
      if self.id[:4] == "ta__":
        angam = custom_transliteration.tr(self.id[4:], sanscript.TAMIL).replace("~", " ").strip(
          "{}") + ' is observed on '
      else:
        angam = custom_transliteration.tr(self.id, sanscript.DEVANAGARI).replace("~", " ") + ' is observed on '

      if self.angam_type == 'tithi':
        angam += NAMES['TITHI_NAMES'][sanscript.IAST][self.angam_number] + ' tithi'
      elif self.angam_type == 'nakshatram':
        angam += NAMES['NAKSHATRAM_NAMES'][sanscript.IAST][self.angam_number] + ' nakṣhatram day'
      elif self.angam_type == 'day':
        angam += 'day %d' % self.angam_number
    else:
      if not hasattr(self, "description"):
        logging.debug("No angam_type in %s or description even!!", self.id)
    if hasattr(self, "kaala"):
      kaala = self.kaala
    else:
      kaala = "sunrise (default)"
    if hasattr(self, "priority"):
      priority = self.priority
    else:
      priority = 'puurvaviddha (default)'
    if angam is not None:
      blurb += angam
    if month is not None:
      blurb += month
    if blurb != '':
      blurb += ' (%s/%s).\n' % (kaala, priority)

    # Get the URL
    if include_url:
      base_url = 'https://github.com/sanskrit-coders/adyatithi/tree/master/data'
      if hasattr(self, "angam_type"):
        url = "%(base_dir)s/%(month_type)s/%(angam_type)s/%(month_number)02d/%(angam_number)02d#%(id)s" % dict(
          base_dir=base_url,
          month_type=self.month_type,
          angam_type=self.angam_type,
          month_number=self.month_number,
          angam_number=self.angam_number,
          id=custom_transliteration.tr(self.id, sanscript.IAST).replace('Ta__', '').replace('~', ' ').replace(' ',
                                                                                                              '-').replace(
            '(', '').replace(')', '').strip('{}').lower())
      elif hasattr(self, "anchor_festival_id"):
        url = "%(base_dir)s/relative_event/%(anchor_festival_id)s/offset__%(offset)02d#%(id)s" % dict(
          base_dir=base_url,
          anchor_festival_id=self.anchor_festival_id.replace('/', '__'),
          offset=self.offset,
          id=custom_transliteration.tr(self.id, sanscript.IAST).replace('Ta__', '').replace('~', ' ').replace(' ',
                                                                                                              '-').strip(
            '{}').lower())
      else:
        tag_list = '/'.join([re.sub('([a-z])([A-Z])', r'\1-\2', t).lower() for t in self.tags.split(',')])
        url = "%(base_dir)s/other/%(tags)s#%(id)s" % dict(
          base_dir=base_url,
          tags=tag_list,
          id=custom_transliteration.tr(self.id, sanscript.IAST).replace('Ta__', '').replace('~', ' ').replace(' ',
                                                                                                              '-').strip(
            '{}').lower())

    # Get the description
    description_string = ''
    if hasattr(self, "description"):
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

    if hasattr(self, "shlokas") and include_shlokas:
      if use_markup:
        description_string = description_string + '\n\n```\n' + custom_transliteration.tr(", ".join(self.shlokas),
                                                                                          script, False) + '\n```'
      else:
        description_string = description_string + '\n\n' + custom_transliteration.tr(", ".join(self.shlokas), script,
                                                                                     False) + '\n\n'

    if include_images:
      if hasattr(self, "image"):
        image_string = '![](https://github.com/sanskrit-coders/adyatithi/blob/master/images/%s)\n\n' % self.image

    if hasattr(self, "references_primary") or hasattr(self, "references_secondary"):
      ref_list = '### References\n'
      if hasattr(self, "references_primary"):
        for ref in self.references_primary:
          ref_list += '* %s\n' % transliterate_quoted_text(ref, sanscript.IAST)
      elif hasattr(self, "references_secondary"):
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

    if not is_brief and include_url:
      if use_markup:
        final_description_string += ('\n\n[+++](%s)\n' % url) + '\n' + ' '.join(['#' + x for x in self.tags.split(',')])
      else:
        final_description_string += ('\n\n%s\n' % url) + '\n' + ' '.join(['#' + x for x in self.tags.split(',')])

    # if use_markup:
    #   final_description_string = final_description_string.replace('\n', '<br/><br/>')

    return final_description_string

  # def get_description_string(self, script, includeShloka=False):
  #   # When used for README.md generation, shloka is included differently
  #   # When used for ICS generation, shloka can be included right here
  #   description_string = ""
  #   logging.debug('get_description_string')
  #   if hasattr(self, "description"):
  #     # description_string = json.dumps(self.description)
  #     description_string = self.description["en"]
  #     pieces = description_string.split('`')
  #     if len(pieces) > 1:
  #       if len(pieces) % 2 == 1:
  #         # We much have matching backquotes, the contents of which can be neatly transliterated
  #         for i, piece in enumerate(pieces):
  #           if (i % 2) == 1:
  #             pieces[i] = custom_transliteration.tr(piece, script, False)
  #         description_string = ''.join(pieces)
  #       else:
  #         logging.warning('Unmatched backquotes in description string: %s' % description_string)
  #   if includeShloka and hasattr(self, "shlokas"):
  #     description_string = description_string + '\n\n' + \
  #                          custom_transliteration.tr(", ".join(self.shlokas), script, False) + '\n\n'
  #   return description_string

  def get_storage_file_name(self, base_dir, only_descriptions=False):
    if hasattr(self.timing, "anchor_festival_id"):
      return "%(base_dir)s/relative_event/%(anchor_festival_id)s/offset__%(offset)02d/%(id)s__info.json" % dict(
        base_dir=base_dir,
        anchor_festival_id=self.timing.anchor_festival_id.replace('/', '__'),
        offset=self.timing.offset,
        id=self.id.replace('/', '__').strip('{}')
      )
    else:
      if only_descriptions:
        tag_list = '/'.join([re.sub('([a-z])([A-Z])', r'\1-\2', t).lower() for t in self.tags])
        return "%(base_dir)s/other/%(tags)s/%(id)s__info.json" % dict(
          base_dir=base_dir,
          tags=tag_list,
          id=self.id.replace('/', '__').strip('{}')
        )
      else:
        return "%(base_dir)s/%(month_type)s/%(angam_type)s/%(month_number)02d/%(angam_number)02d/%(id)s__info.json" % dict(
          base_dir=base_dir,
          month_type=self.timing.month_type,
          angam_type=self.timing.angam_type,
          month_number=self.timing.month_number,
          angam_number=self.timing.angam_number,
          id=self.id.replace('/', '__').strip('{}')
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
    festival_rules = read_old_festival_rules_dict(os.path.join(CODE_ROOT, 'panchaanga/data/festival_rules.json'))
    festival_id_to_json.update(festival_rules)
    festival_rules = read_old_festival_rules_dict(
      os.path.join(CODE_ROOT, 'panchaanga/data/relative_festival_rules.json'))
    festival_id_to_json.update(festival_rules)
    festival_rules = read_old_festival_rules_dict(
      os.path.join(CODE_ROOT, 'panchaanga/data/festival_rules_desc_only.json'))
    festival_id_to_json.update(festival_rules)


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
