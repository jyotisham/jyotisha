import logging
import sys

from sanskrit_util.transliterate import sanscript

from jyotisha import custom_transliteration
from sanskrit_data.schema import common

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

festival_id_to_json = {}



class FestivalInstance(common.JsonObject):
  def __init__(self, name, days=None, interval=None):
    self.name = name
    # A single festival may span multiple days.
    self.days = [] if days is None else days
    self.interval = interval

  def transliterate_names(self, scripts):
    # TODO: Not perfect. Misses corner cases, not general.
    from jyotisha.panchaanga.temporal.festival import rules
    festival_rules = rules.festival_rules_all
    fest_details = festival_rules.get(self.name, rules.HinduCalendarEvent())
    if fest_details.names is None:
      fest_details.names = {"sa": [self.name]}
    def get_best_transliteration(language, name):
      if language == "ta" and sanscript.TAMIL in scripts:
        return custom_transliteration.tr(text=name, script=sanscript.TAMIL)
      if language == "sa" and sanscript.DEVANAGARI in scripts:
        return custom_transliteration.tr(text=name, script=sanscript.DEVANAGARI)
      return custom_transliteration.tr(text=name, script=scripts[0])

    import copy
    names = copy.deepcopy(fest_details.names)
    for language in names:
      names[language] = [get_best_transliteration(language=language, name=name) for name in names[language]]
    return names

  def get_best_transliterated_name(self, scripts):
    names = self.transliterate_names(scripts=scripts)
    if "ta" in names and sanscript.TAMIL in scripts:
      return {"script": sanscript.TAMIL, "text": names["ta"][0]}
    else:
      return {"script": scripts[0], "text": names["sa"][0]}

  def tex_code(self, scripts, timezone):
    name_details = self.get_best_transliterated_name(scripts=scripts)
    if name_details["script"] == sanscript.TAMIL:
      name = '\\tamil{%s}' % name_details["text"]
    else:
      name = name_details["text"]

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

  def tex_code(self, scripts, timezone=None):
    return custom_transliteration.tr("%s~%s##\\To{}##%s" % (self.name, self.status_1_hk, self.status_2_hk), script=scripts[0])

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
