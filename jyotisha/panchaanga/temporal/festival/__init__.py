import logging
import sys

from indic_transliteration import sanscript, language_code_to_script

from jyotisha import custom_transliteration
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
      fest_details.names = {"sa": [self.name]}
    import copy
    names = copy.deepcopy(fest_details.names)
    return names

  def get_best_transliterated_name(self, scripts, fest_details_dict):
    names = self.get_human_names(fest_details_dict=fest_details_dict)
    languages = list(names.keys())
    language_scripts = [language_code_to_script.get(language, scripts[0]) for language in languages]
    for script in scripts:
      try:
        i = language_scripts.index(script)
        return {"script": script, "text": custom_transliteration.tr(text=names[languages[i]][0], script=script)}
      except ValueError:
        continue
    return None

  def tex_code(self, scripts, timezone, fest_details_dict):
    name_details = self.get_best_transliterated_name(scripts=scripts, fest_details_dict=fest_details_dict)
    if name_details["script"] == sanscript.TAMIL:
      name = '\\tamil{%s}' % name_details["text"]
    else:
      name = name_details["text"]

    if self.ordinal is not None:
      name = name + "~\\#{%s}" % custom_transliteration.tr(str(self.ordinal), script=scripts[0])

    if self.interval is None:
      return name
    else:
      from jyotisha.panchaanga.temporal.time import Hour
      start_time_str = "" if self.interval.jd_start is None else Hour(timezone.julian_day_to_local_time(self.interval.jd_start).get_fractional_hour()).toString()
      end_time_str = "" if self.interval.jd_end is None else Hour(timezone.julian_day_to_local_time(self.interval.jd_end).get_fractional_hour()).toString()
      start_time_str = custom_transliteration.tr(text=start_time_str, script=scripts[0])
      start_time_str = sanscript.transliterate(data=start_time_str, _from=sanscript.HK, _to=scripts[0])
      if start_time_str != "":
        start_time_str = "\\textsf{%s}" % start_time_str
      end_time_str = sanscript.transliterate(data=end_time_str, _from=sanscript.HK, _to=scripts[0])
      if end_time_str != "":
        end_time_str = "\\textsf{%s}" % end_time_str
      return "%s%s{\\RIGHTarrow}%s" % (name, start_time_str, end_time_str)

  def __lt__(self, other):
    return self.name < other.name

  def __hash__(self):
    return hash(self.name)


class TransitionFestivalInstance(FestivalInstance):
  def __init__(self, name, status_1_hk, status_2_hk):
    super(TransitionFestivalInstance, self).__init__(name=name)
    self.status_1_hk = status_1_hk
    self.status_2_hk = status_2_hk

  def tex_code(self, scripts, timezone, fest_details_dict):
    name_details = self.get_best_transliterated_name(scripts=scripts, fest_details_dict=fest_details_dict)
    if name_details["script"] == sanscript.TAMIL:
      name = '\\tamil{%s}' % name_details["text"]
    else:
      name = name_details["text"]
    return custom_transliteration.tr("%s~%s##\\To{}##%s" % (name, self.status_1_hk, self.status_2_hk), script=scripts[0])

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
