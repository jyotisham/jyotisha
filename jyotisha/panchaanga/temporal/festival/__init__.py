import logging
import re
import sys

from indic_transliteration import sanscript, language_code_to_script, xsanscript
from jyotisha import custom_transliteration
from jyotisha.util import default_if_none
from sanskrit_data.schema import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

festival_id_to_json = {}


class FestivalInstance(common.JsonObject):
  def __init__(self, name, interval=None, ordinal=None, exclude=None):
    super(FestivalInstance, self).__init__()
    self.name = name
    self.interval = interval
    self.exclude = exclude
    self.ordinal = ordinal

  def get_human_names(self, fest_details_dict):
    festival_rules = fest_details_dict
    from jyotisha.panchaanga.temporal.festival import rules
    fest_details = festival_rules.get(self.name, rules.HinduCalendarEvent())
    if fest_details.names is None:
      fest_details.names = {"sa": [xsanscript.transliterate(self.name.replace("~", "-"), sanscript.HK, sanscript.DEVANAGARI)]}
    import copy
    names = copy.deepcopy(fest_details.names)
    return names

  def get_best_transliterated_name(self, languages, scripts, fest_details_dict):
    names = self.get_human_names(fest_details_dict=fest_details_dict)
    for language in languages:
      if language in names.keys():
        if language_code_to_script[language] in scripts:
          transliterated_text = custom_transliteration.transliterate_from_language(language=language, text=names[language][0], script=language_code_to_script[language])
          return {"language": language_code_to_script[language], "text": transliterated_text}
        else:
          transliterated_text = custom_transliteration.transliterate_from_language(language=language, text=names[language][0], script=scripts[0])
          return {"language": scripts[0], "text": transliterated_text}

    # No language text matching the input scripts was found.
    if "sa" in names:
      language = "sa"
    else:
      language = list(names.keys())[0]
    transliterated_text = custom_transliteration.transliterate_from_language(language=language, text=names[language][0], script=scripts[0])
    return {"language": scripts[0], "text": transliterated_text}

  def tex_code(self, languages, scripts, timezone, fest_details_dict):
    name_details = self.get_best_transliterated_name(languages=languages, scripts=scripts, fest_details_dict=fest_details_dict)
    if name_details["language"] == sanscript.TAMIL:
      name = '\\tamil{%s}' % name_details["text"]
    else:
      name = name_details["text"]

    if self.ordinal is not None:
      name = name + "~\\#{%s}" % custom_transliteration.tr(str(self.ordinal), script=scripts[0])

    if self.interval is None:
      return name
    else:
      from jyotisha.panchaanga.temporal.time import Hour
      start_time_str = "" if self.interval.jd_start is None else Hour(timezone.julian_day_to_local_time(self.interval.jd_start).get_fractional_hour()).to_string()
      end_time_str = "" if self.interval.jd_end is None else Hour(timezone.julian_day_to_local_time(self.interval.jd_end).get_fractional_hour()).to_string()
      if start_time_str != "":
        start_time_str = "~\\textsf{%s}" % start_time_str
      if end_time_str != "":
        end_time_str = "\\textsf{%s}" % end_time_str
      return "%s%s{\\RIGHTarrow}%s" % (name, start_time_str, end_time_str)

  def md_code(self, languages, scripts, timezone, fest_details_dict):
    name_details = self.get_best_transliterated_name(languages=languages, scripts=scripts, fest_details_dict=fest_details_dict)
    ordinal_str = " #%s" % custom_transliteration.tr(str(self.ordinal), script=scripts[0]) if self.ordinal is not None else ""
    name = "#### %s" % name_details["text"].replace("~", "-")

    if self.interval is None:
      md = name
    else:
      from jyotisha.panchaanga.temporal.time import Hour
      start_time_str = "" if self.interval.jd_start is None else timezone.julian_day_to_local_time(self.interval.jd_start).get_hour_str()
      end_time_str = "" if self.interval.jd_end is None else timezone.julian_day_to_local_time(self.interval.jd_end).get_hour_str()
      md = "%s%s\n- %s→%s" % (name, ordinal_str, start_time_str, end_time_str)
    description = get_description(festival_instance=self, fest_details_dict=fest_details_dict, script=scripts[0], truncate=False)
    if description != "":
      md = "%s\n\n%s" % (md, description)
    return md

  def __lt__(self, other):
    return self.name < other.name

  def __hash__(self):
    return hash(self.name)

  def __repr__(self):
    return "%s %s %s" % (self.name, str(default_if_none(self.ordinal, "")), str(default_if_none(self.interval, "")))


class TransitionFestivalInstance(FestivalInstance):
  def __init__(self, name, status_1_hk, status_2_hk):
    super(TransitionFestivalInstance, self).__init__(name=name)
    self.status_1_hk = status_1_hk
    self.status_2_hk = status_2_hk

  def tex_code(self, languages, scripts, timezone, fest_details_dict):
    name_details = self.get_best_transliterated_name(languages=languages, scripts=scripts, fest_details_dict=fest_details_dict)
    if name_details["language"] == sanscript.TAMIL:
      name = '\\tamil{%s}' % name_details["text"]
    else:
      name = name_details["text"]
    return custom_transliteration.tr("%s~(%s##\\To{}##%s)" % (name, self.status_1_hk, self.status_2_hk), script=scripts[0])


def get_description(festival_instance, fest_details_dict, script, truncate=True):
  fest_id = festival_instance.name
  desc = None
  if re.match('aGgArakI.*saGkaTahara-caturthI-vratam', fest_id):
    fest_id = fest_id.replace('aGgArakI~', '')
    if fest_id in fest_details_dict:
      desc = fest_details_dict[fest_id].get_description_string(
        script=script)
      desc += 'When `caturthI` occurs on a Tuesday, it is known as `aGgArakI` and is even more sacred.'
    else:
      logging.warning('No description found for caturthI festival %s!' % fest_id)
  elif re.match('.*-.*-EkAdazI', fest_id) is not None:
    # Handle ekaadashii descriptions differently
    ekad = '-'.join(fest_id.split('-')[1:])  # get rid of sarva etc. prefix!
    ekad_suff_pos = ekad.find(' (')
    if ekad_suff_pos != -1:
      # ekad_suff = ekad[ekad_suff_pos + 1:-1]
      ekad = ekad[:ekad_suff_pos]
    if ekad in fest_details_dict:
      desc = fest_details_dict[ekad].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=truncate)
    else:
      logging.warning('No description found for Ekadashi festival %s (%s)!' % (ekad, fest_id))
  elif fest_id.find('saGkrAntiH') != -1:
    # Handle Sankranti descriptions differently
    planet_trans = fest_id.split('~')[0]  # get rid of ~(rAshi name) etc.
    if planet_trans in fest_details_dict:
      desc = fest_details_dict[planet_trans].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=truncate)
    else:
      logging.warning('No description found for festival %s!' % planet_trans)
  elif fest_id in fest_details_dict:
      desc = fest_details_dict[fest_id].get_description_string(
        script=script, include_url=True, include_shlokas=True, truncate=truncate, include_images=False)


  if desc is None:
      # Check approx. match
      matched_festivals = []
      for fest_key in fest_details_dict:
        if fest_id.startswith(fest_key):
          matched_festivals += [fest_key]
      if matched_festivals == []:
        logging.warning('No description found for festival %s!' % fest_id)
      elif len(matched_festivals) > 1:
        logging.warning('No exact match found for festival %s! Found more than one approximate match: %s' % (
          fest_id, str(matched_festivals)))
      else:
        desc = fest_details_dict[matched_festivals[0]].get_description_string(script=script,
                                                                              include_url=True, include_shlokas=True,
                                                                              truncate=True)
  return default_if_none(desc, "")


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
