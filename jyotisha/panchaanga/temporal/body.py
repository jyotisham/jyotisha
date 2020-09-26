import logging
import math
import sys

import methodtools
import swisseph as swe
from scipy.optimize import brentq

from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject


class Transit(JsonObject):
  def __init__(self, body, jd, anga_type, value_1, value_2):
    super().__init__()
    self.body = body
    self.jd = jd
    self.anga_type = anga_type
    self.value_1 = value_1
    self.value_2 = value_2


class Graha(JsonObject):
  SUN = "sun"
  MOON = "moon"
  JUPITER = "jupiter"
  VENUS = "venus"
  MERCURY = "mercury"
  MARS = "mars"
  SATURN = "saturn"

  @methodtools.lru_cache(maxsize=None)
  @classmethod
  def singleton(cls, body_name):
    return cls(body_name=body_name)

  def __init__(self, body_name):
    super().__init__()
    self.body_name = body_name

  def _get_swisseph_id(self):
    body_id = -1
    if self.body_name == Graha.SUN:
      body_id = swe.SUN
    elif self.body_name == Graha.MOON:
      body_id = swe.MOON
    elif self.body_name == Graha.JUPITER:
      body_id = swe.JUPITER
    elif self.body_name == Graha.VENUS:
      body_id = swe.VENUS
    elif self.body_name == Graha.MERCURY:
      body_id = swe.MERCURY
    elif self.body_name == Graha.MARS:
      body_id = swe.MARS
    elif self.body_name == Graha.SATURN:
      body_id = swe.SATURN
    return body_id

  def get_longitude(self, jd):
    return swe.calc_ut(jd, self._get_swisseph_id())[0][0]

  def get_longitude_offset(self, jd, offset, ayanaamsha_id):
    from jyotisha.panchaanga.temporal.zodiac import Ayanamsha
    adjusted_longitude = (self.get_longitude(jd=jd) - Ayanamsha.singleton(ayanaamsha_id).get_offset(jd)) % 360
    # Not doing modulo arithmetic below - we want to allow the offset longitude to be negative, for use with brentq.
    return adjusted_longitude + offset

  def get_next_raashi_transit(self, jd_start, jd_end, ayanaamsha_id):
    """Returns the next transit of the given planet e.g. jupiter

  Args:
    float jd_start, jd_end: The Julian Days between which transits must be computed
    int planet  - e.g. sun, jupiter, ...

  Returns:
    List of tuples [(float jd_transit, int old_rashi, int new_rashi)]

  
"""

    transits = []
    MIN_JUMP = min(15, jd_end-jd_start)  # Random check for a transit every 15 days!
    # Could be tweaked based on planet using a dict?

    curr_L_bracket = jd_start
    curr_R_bracket = jd_start + MIN_JUMP

    while curr_R_bracket <= jd_end:
      L_rashi = math.floor(self.get_longitude_offset(curr_L_bracket, offset=0,
                                                     ayanaamsha_id=ayanaamsha_id) / 30) + 1
      R_rashi = math.floor(self.get_longitude_offset(curr_R_bracket, offset=0,
                                                     ayanaamsha_id=ayanaamsha_id) / 30) + 1

      if L_rashi == R_rashi:
        curr_R_bracket += MIN_JUMP
      else:
        # We have bracketed a transit!
        if L_rashi < R_rashi:
          target = R_rashi
        else:
          # retrograde transit
          target = L_rashi
        try:
          def get_longitude_offset_partially_applied(jd):
            return self.get_longitude_offset(jd=jd, offset=(-target + 1) * 30, ayanaamsha_id=ayanaamsha_id)

          # noinspection PyTypeChecker
          jd_transit = \
            brentq(get_longitude_offset_partially_applied,
                   curr_L_bracket, curr_R_bracket)
          from jyotisha.panchaanga.temporal.zodiac import AngaType
          transits += [Transit(body=self.body_name, jd=jd_transit, anga_type=AngaType.RASHI.name, value_1=L_rashi, value_2=R_rashi)]
          curr_R_bracket += MIN_JUMP
          curr_L_bracket = jd_transit + MIN_JUMP
        except ValueError:
          logging.error('Unable to compute transit of planet;\
                                   possibly could not bracket correctly!\n')
          return None

    if len(transits) == 0:
      from jyotisha.panchaanga.temporal.time import ist_timezone
      logging.info("Could not find a transit of %s between %s (%f) and %s (%f)", self.body_name, ist_timezone.julian_day_to_local_time_str(jd_start), jd_start, ist_timezone.julian_day_to_local_time_str(jd_end), jd_end)
    return transits


def get_star_longitude(star, jd):
  from jyotisha.panchaanga import data
  import os
  swe.set_ephe_path(os.path.dirname(data.__file__))
  (long, lat, _, _, _, _) = swe.fixstar_ut(star, jd)[0]
  return long

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
