#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import logging
import math
import os
import swisseph as swe
import sys
from datetime import datetime
from math import floor

from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject
from scipy.optimize import brentq

from jyotisha.custom_transliteration import sexastr2deci
from jyotisha.panchangam import temporal

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")

CODE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Defining "bits" for rsmi in swe.rise_trans per documentation on https://www.astro.com/swisseph/swephprg.htm#_Toc505244865

#     The variable rsmi can have the following values:

#     /* for swe_rise_trans() and swe_rise_trans_true_hor() */
#     #define SE_CALC_RISE            1
#     #define SE_CALC_SET             2
#     #define SE_CALC_MTRANSIT   4       /* upper meridian transit (southern for northern geo. latitudes) */
#     #define SE_CALC_ITRANSIT     8       /* lower meridian transit (northern, below the horizon) */
#     /* the following bits can be added (or’ed) to SE_CALC_RISE or SE_CALC_SET */
#     #define SE_BIT_DISC_CENTER         256     /* for rising or setting of disc center */
#     #define SE_BIT_DISC_BOTTOM      8192     /* for rising or setting of lower limb of disc */
#     #define SE_BIT_GEOCTR_NO_ECL_LAT 128 /* use topocentric position of object and ignore its ecliptic latitude */
#     #define SE_BIT_NO_REFRACTION    512      /* if refraction is not to be considered */
#     #define SE_BIT_CIVIL_TWILIGHT    1024    /* in order to calculate civil twilight */
#     #define SE_BIT_NAUTIC_TWILIGHT 2048    /* in order to calculate nautical twilight */
#     #define SE_BIT_ASTRO_TWILIGHT   4096    /* in order to calculate astronomical twilight */
#     #define SE_BIT_FIXED_DISC_SIZE (16*1024) /* neglect the effect of distance on disc size */
#     #define SE_BIT_HINDU_RISING (SE_BIT_DISC_CENTER|SE_BIT_NO_REFRACTION|SE_BIT_GEOCTR_NO_ECL_LAT)
#                                                                      /* risings according to Hindu astrology */

CALC_RISE = 897  # 512 + 256 + 128 + 1
CALC_SET = 898   # 512 + 256 + 128 + 2


def decypher_fractional_hours(time_in_hours):
  hours = math.floor(time_in_hours)
  minutes = math.floor((time_in_hours-hours)*60)
  seconds = math.floor((time_in_hours - hours - minutes / 60.0)*3600)
  return (hours, minutes, seconds)


class City(JsonObject):
  """This class enables the construction of a city object
    """

  def __init__(self, name, latitude, longitude, timezone):
    """Constructor for city"""
    super().__init__()
    if name is None or name == "":
      self.name = str([latitude, longitude])
    else:
      self.name = name
    if ":" in str(latitude):
      self.latitude = sexastr2deci(latitude)
      self.longitude = sexastr2deci(longitude)
    else:
      self.latitude = latitude
      self.longitude = longitude
    self.timezone = timezone

  @classmethod
  def from_address(cls, address, api_key, timeout=45):
    from geopy import geocoders
    geolocator = geocoders.GoogleV3(api_key=api_key, timeout=timeout)
    location = geolocator.geocode(address)
    city = City(name=address, latitude=location.latitude, longitude=location.longitude, timezone=location.timezone().zone)
    return city

  @classmethod
  def from_address_and_timezone(cls, address, timezone_str, timeout=45):
    from geopy import geocoders
    geolocator = geocoders.ArcGIS()
    location = geolocator.geocode(query=address, timeout=timeout)
    city = City(name=address, latitude=location.latitude, longitude=location.longitude, timezone=timezone_str)
    return city

  def get_timezone_offset_hours_from_date(self, year, month, day, hour=6, minute=0, seconds=0):
    """Get timezone offset in hours east of UTC (negative west of UTC)

    Timezone offset is dependent both on place and time (yes- time, not just date) - due to Daylight savings time.
    compute offset from UTC in hours
    """
    import pytz
    local_time = pytz.timezone(self.timezone).localize(datetime(year, month, day, hour, minute, seconds))
    return (datetime.utcoffset(local_time).days * 86400 +
            datetime.utcoffset(local_time).seconds) / 3600.0

  def julian_day_to_local_time(self, julian_day, round_seconds=False):
    [y, m, dt, time_in_hours] = swe.revjul(julian_day)
    (hours, minutes, seconds) = decypher_fractional_hours(time_in_hours=time_in_hours)
    local_time = swe.utc_time_zone(y, m, dt, hours, minutes, seconds, -self.get_timezone_offset_hours_from_date(y, m, dt, hours, minutes, seconds))
    if round_seconds:
      (y, m, dt, hours, minutes, seconds) = local_time
      local_time = (y, m, dt, hours, minutes, int(round(seconds)))
      local_time = temporal.sanitize_time(*local_time)
    return local_time

  def local_time_to_julian_day(self, year, month, day, hours, minutes, seconds):
    offset_hours = self.get_timezone_offset_hours_from_date(year=year, month=month, day=day, hour=hours, minute=minutes, seconds=seconds)
    (year_utc, month_utc, day_utc, hours_utc, minutes_utc, seconds_utc) = swe.utc_time_zone(year, month, day, hours, minutes, seconds, offset_hours)
    julian_dates = swe.utc_to_jd(year_utc, month_utc, day_utc, hours_utc, minutes_utc, seconds_utc, 1)
    return julian_dates[1]


class TbSayanaMuhuurta(JsonObject):
  """ A muhUrta as defined by SayaNa's commentary to TB 5.3
  
  Refer https://archive.org/stream/Anandashram_Samskrita_Granthavali_Anandashram_Sanskrit_Series/ASS_037_Taittiriya_Brahmanam_with_Sayanabhashya_Part_1_-_Narayanasastri_Godbole_1934#page/n239/mode/2up .
  """
  def __init__(self, jd_start, jd_end, muhuurta_id, city):
    super().__init__()
    self.city = city
    self.muhuurta_id = muhuurta_id
    self.jd_start = jd_start
    self.jd_end = jd_end
    self.ahna = floor(self.muhuurta_id/3)
    self.ahna_part = self.muhuurta_id % 3
    self.is_nirviirya = self.muhuurta_id in (2,3, 5,6, 8,9, 11,12)

  def to_localized_string(self):
    return "muhUrta %d (nirvIrya: %s) starts from %s to %s" % (self.muhuurta_id, str(self.is_nirviirya),  self.city.julian_day_to_local_time(julian_day=self.jd_start, round_seconds=True), self.city.julian_day_to_local_time(julian_day=self.jd_end, round_seconds=True))


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)

if __name__ == '__main__':
  import doctest
  doctest.testmod(verbose=True)
