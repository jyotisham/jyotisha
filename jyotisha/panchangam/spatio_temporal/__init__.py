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


def decypher_fractional_hours(time_in_hours):
  hours = math.floor(time_in_hours)
  minutes = math.floor((time_in_hours-hours)*60)
  seconds = math.floor((time_in_hours - hours - minutes * 60)*3600)
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

  def get_timezone_offset_hours_from_jd(self, julian_day):
    """Get timezone offset in hours east of UTC (negative west of UTC)

    Timezone offset is dependent both on place and time - due to Daylight savings time.
    compute offset from UTC in hours
    """
    [y, m, dt, t] = swe.revjul(julian_day)
    return self.get_timezone_offset_hours_from_date(year=y, month=m, day=dt)


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
    local_time = swe.utc_time_zone(y, m, dt, hours, minutes, seconds, -self.get_timezone_offset_hours_from_jd(julian_day))
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



def get_lagna_float(jd, lat, lon, offset=0, ayanamsha_id=swe.SIDM_LAHIRI, debug=False):
  """Returns the angam

    Args:
      :param jd: The Julian Day at which the lagnam is to be computed
      :param lat: Latitude of the place where the lagnam is to be computed
      :param lon: Longitude of the place where the lagnam is to be computed
      :param offset: Used by internal functions for bracketing
      :param ayanamsha_id
      :param debug

    Returns:
      float lagna

    Examples:
      >>> get_lagna_float(2444961.7125,13.08784, 80.27847)
      10.353595502472984
  """
  swe.set_sid_mode(ayanamsha_id)
  lcalc = swe.houses_ex(jd, lat, lon)[1][0] - swe.get_ayanamsa_ut(jd)
  lcalc = lcalc % 360

  if offset == 0:
    return lcalc / 30

  else:
    if (debug):
      print('offset:', offset)
      print('lcalc/30', lcalc / 30)
      print('lcalc/30 + offset = ', lcalc / 30 + offset)

    # The max expected value is somewhere between 2 and -2, with bracketing

    if (lcalc / 30 + offset) >= 3:
      return (lcalc / 30) + offset - 12
    elif (lcalc / 30 + offset) <= -3:
      return (lcalc / 30)
    else:
      return (lcalc / 30) + offset


def get_lagna_data(jd_sunrise, lat, lon, tz_off, ayanamsha_id=swe.SIDM_LAHIRI, debug=False):
  """Returns the lagna data

      Args:
        float jd: The Julian Day at which the lagnam is to be computed
        lat: Latitude of the place where the lagnam is to be computed
        lon: Longitude of the place where the lagnam is to be computed
        tz_off: Used by internal functions for bracketing

      Returns:
        tuples detailing the end time of each lagna, beginning with the one
        prevailing at sunrise

      Examples:
        >>> get_lagna_data(2458222.5208333335, lat=13.08784, lon=80.27847, tz_off=5.5)
        [(12, 2458222.5214310056), (1, 2458222.596420153), (2, 2458222.6812926503), (3, 2458222.772619788), (4, 2458222.8624254186), (5, 2458222.9478168003), (6, 2458223.0322211445), (7, 2458223.1202004547), (8, 2458223.211770839), (9, 2458223.3000455885), (10, 2458223.3787625884), (11, 2458223.4494649624)]
    """
  lagna_sunrise = 1 + floor(get_lagna_float(jd_sunrise, lat, lon, ayanamsha_id=ayanamsha_id))

  lagna_list = [(x + lagna_sunrise - 1) % 12 + 1 for x in range(12)]

  lbrack = jd_sunrise - 3 / 24
  rbrack = jd_sunrise + 3 / 24
  lagna_data = []

  for lagna in lagna_list:
    # print('---\n', lagna)
    if (debug):
      print('lagna sunrise', get_lagna_float(jd_sunrise, lat, lon, ayanamsha_id=ayanamsha_id))
      print('lbrack', get_lagna_float(lbrack, lat, lon, int(-lagna), ayanamsha_id=ayanamsha_id))
      print('rbrack', get_lagna_float(rbrack, lat, lon, int(-lagna), ayanamsha_id=ayanamsha_id))

    lagna_end_time = brentq(get_lagna_float, lbrack, rbrack,
                            args=(lat, lon, -lagna, debug))
    lbrack = lagna_end_time + 1 / 24
    rbrack = lagna_end_time + 3 / 24
    lagna_data.append((lagna, lagna_end_time))
  return lagna_data


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)

if __name__ == '__main__':
  import doctest
  doctest.testmod(verbose=True)
