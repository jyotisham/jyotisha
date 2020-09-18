#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import logging
import os
import sys
from datetime import datetime
from math import modf

import pytz
import swisseph as swe

from jyotisha.custom_transliteration import sexastr2deci
from jyotisha.panchangam import temporal
from jyotisha.panchangam.temporal import Time
from jyotisha.panchangam.temporal.zodiac import Ayanamsha
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

# from scipy.optimize import brentq

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
CALC_SET = 898  # 512 + 256 + 128 + 2


class City(JsonObject):
  """This class enables the construction of a city object
    """

  def __init__(self, name, latitude, longitude, timezone):
    """Constructor for city"""
    super(City, self).__init__()
    if name is None or name == "":
      self.name = str([latitude, longitude])
    else:
      self.name = name
    if ":" in str(latitude):
      self.latitude = sexastr2deci(latitude)
      self.longitude = sexastr2deci(longitude)
    else:
      self.latitude = float(latitude)
      self.longitude = float(longitude)
    self.timezone = timezone

  @classmethod
  def from_address(cls, address, api_key, timeout=45):
    from geopy import geocoders
    geolocator = geocoders.GoogleV3(api_key=api_key, timeout=timeout)
    location = geolocator.geocode(address)
    city = City(name=address, latitude=location.latitude, longitude=location.longitude,
                timezone=location.timezone().zone)
    return city

  @classmethod
  def from_address_and_timezone(cls, address, timezone_str, timeout=45):
    from geopy import geocoders
    geolocator = geocoders.ArcGIS()
    location = geolocator.geocode(query=address, timeout=timeout)
    city = City(name=address, latitude=location.latitude, longitude=location.longitude, timezone=timezone_str)
    return city

  def get_rising_time(self, julian_day_start, body):
    from jyotisha.panchangam.temporal.body import Graha
    graha = Graha(body)
    # rise_trans expects UT time
    return swe.rise_trans(
      jd_start=julian_day_start, body=graha._get_swisseph_id(),
      lon=self.longitude, lat=self.latitude,
      rsmi=CALC_RISE)[1][0]

  def get_setting_time(self, julian_day_start, body):
    from jyotisha.panchangam.temporal.body import Graha
    graha = Graha(body)
    # rise_trans expects UT time
    return swe.rise_trans(
      jd_start=julian_day_start, body=graha._get_swisseph_id(),
      lon=self.longitude, lat=self.latitude,
      rsmi=CALC_SET)[1][0]

  def get_solar_eclipse_time(self, jd_start):
    return swe.sol_eclipse_when_loc(julday=jd_start, lon=self.longitude, lat=self.latitude)

  def get_lunar_eclipse_time(self, jd_start):
    return swe.lun_eclipse_when_loc(jd_start, lon=self.longitude, lat=self.latitude)

  def get_zodiac_longitude_eastern_horizon(self, jd):
    """ Get the ID of the raashi what is currently rising.
    
    :param jd: 
    :return: 
    """
    return swe.houses_ex(jd, self.latitude, self.longitude)[1][0]

  def get_lagna_float(self, jd, offset=0, ayanamsha_id=Ayanamsha.CHITRA_AT_180, debug=False):
    """Returns the rising rAshi at a given location.

      Args:
        :param jd: The Julian Day at which the lagnam is to be computed
        :param offset: Used by internal functions for bracketing
        :param debug

      Returns:
        float lagna
    """

    lcalc = self.get_zodiac_longitude_eastern_horizon(jd=jd) - Ayanamsha.factory(ayanamsha_id=ayanamsha_id).get_offset(jd=jd)
    lcalc = lcalc % 360

    if offset == 0:
      return lcalc / 30

    else:
      if debug:
        logging.debug(debug)
        logging.debug(('offset:', offset))
        logging.debug(('lcalc/30', lcalc / 30))
        logging.debug(('lcalc/30 + offset = ', lcalc / 30 + offset))

      # The max expected value is somewhere between 2 and -2, with bracketing

      if (lcalc / 30 + offset) >= 3:
        return (lcalc / 30) + offset - 12
      elif (lcalc / 30 + offset) <= -3:
        return (lcalc / 30)
      else:
        return (lcalc / 30) + offset


class Timezone:
  def __init__(self, timezone_id):
    self.timezone_id = timezone_id

  def get_timezone_offset_hours_from_date(self, year, month, day, hour=6, minute=0, seconds=0):
    """Get timezone offset in hours east of UTC (negative west of UTC)

    Timezone offset is dependent both on place and time (yes- time, not just date) - due to Daylight savings time.
    compute offset from UTC in hours
    """
    local_time = pytz.timezone(self.timezone_id).localize(datetime(year, month, day, hour, minute, seconds))
    return (datetime.utcoffset(local_time).days * 86400 +
            datetime.utcoffset(local_time).seconds) / 3600.0

  def julian_day_to_local_time(self, julian_day, round_seconds=False):
    tm = Time(julian_day, format='jd')
    tm.format = "datetime"
    local_datetime = pytz.timezone(self.timezone_id).fromutc(tm.value)
    local_time = (
    local_datetime.year, local_datetime.month, local_datetime.day, local_datetime.hour, local_datetime.minute,
    local_datetime.second + local_datetime.microsecond / 1000000.0)
    if round_seconds:
      (y, m, dt, hours, minutes, seconds) = local_time
      local_time = temporal.sanitize_time(y, m, dt, hours, minutes, int(round(seconds)))
    return local_time

  def local_time_to_julian_day(self, year, month, day, hours, minutes, seconds):
    microseconds, _ = modf(seconds * 1000000)
    local_datetime = pytz.timezone(self.timezone_id).localize(
      datetime(year, month, day, hours, minutes, int(seconds), int(microseconds)))
    tm = Time(local_datetime, format="datetime")
    tm.format = "jd"
    return tm.value


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)

if __name__ == '__main__':
  import doctest

  doctest.testmod(verbose=True)
