import logging
import sys

from jyotisha import custom_transliteration
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


class FestivalInstance(common.JsonObject):
  def __init__(self, name, days=None, interval=None):
    self.name = name
    self.days = [] if days is None else days
    self.interval = interval

  def tex_code(self, script, timezone):
    name = custom_transliteration.tr(text=self.name, scr=script).replace('★', '$^\\star$')

    if self.interval is None:
      return name
    else:
      from jyotisha.panchaanga.temporal.time import Hour
      start_time_str = "" if self.interval.jd_start is None else Hour(timezone.julian_day_to_local_time(self.interval.jd_start).get_fractional_hour()).toString()
      end_time_str = "" if self.interval.jd_end is None else Hour(timezone.julian_day_to_local_time(self.interval.jd_end).get_fractional_hour()).toString()
      return custom_transliteration.tr("%s\\textsf{%s}{\\RIGHTarrow}\\textsf{%s}" % (name, start_time_str, end_time_str), scr=script)

  def __lt__(self, other):
    return self.name < other.name

  def __hash__(self):
    return hash(self.name)


class TransitionFestivalInstance(FestivalInstance):
  def __init__(self, name, status_1_hk, status_2_hk):
    super(TransitionFestivalInstance, self).__init__(name=name)
    self.status_1_hk = status_1_hk
    self.status_2_hk = status_2_hk

  def tex_code(self, script, timezone=None):
    return custom_transliteration.tr("%s~%s##\\To{}##%s" % (self.name, self.status_1_hk, self.status_2_hk), scr=script)

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
