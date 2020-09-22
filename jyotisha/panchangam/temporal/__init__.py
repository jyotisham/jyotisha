import logging
import sys
from datetime import datetime
from math import modf

import pytz
from astropy.time import Time, TimezoneInfo

from jyotisha.panchangam.temporal import hour
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

MAX_DAYS_PER_YEAR = 366
MAX_SZ = MAX_DAYS_PER_YEAR + 6  # plus one and minus one are usually necessary
MIN_DAYS_NEXT_ECLIPSE = 25
TYAJYAM_SPANS_REL = [51, 25, 31, 41, 15, 22, 31, 21, 33,
                     31, 21, 19, 22, 21, 15, 15, 11, 15,
                     57, 25, 21, 11, 11, 19, 17, 25, 31]
AMRITA_SPANS_REL = [43, 49, 55, 53, 39, 36, 55, 45, 57,
                    55, 45, 43, 46, 45, 39, 39, 35, 39,
                    45, 49, 45, 35, 35, 43, 41, 49, 55]
AMRITADI_YOGA = [[None, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 0, 0, 1, 1, 2, 2, 2, 0, 1, 0, 0, 2, 1, 1, 0, 0],
                 [None, 1, 1, 2, 0, 0, 1, 0, 1, 1, 2, 1, 1, 1, 1, 0, 2, 1, 1, 1, 1, 2, 0, 1, 1, 2, 1, 1],
                 [None, 1, 1, 1, 0, 1, 2, 1, 1, 1, 1, 1, 0, 1, 1, 1, 2, 1, 1, 0, 1, 1, 1, 1, 2, 2, 0, 1],
                 [None, 2, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 2, 1, 1, 1, 1, 1, 2, 0, 0, 1, 2, 1, 0, 1, 2],
                 [None, 0, 1, 2, 2, 2, 2, 0, 0, 1, 0, 1, 2, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1],
                 [None, 0, 1, 1, 2, 1, 1, 1, 2, 2, 2, 1, 1, 0, 1, 1, 1, 1, 2, 0, 1, 1, 2, 1, 1, 1, 1, 0],
                 [None, 1, 1, 0, 0, 1, 1, 1, 1, 2, 0, 1, 2, 2, 2, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 2, 1, 2]]
AMRITADI_YOGA_NAMES = {1: 'siddha', 0: 'amRta', 2: 'maraNa'}
for i in range(7):
  AMRITADI_YOGA[i] = [AMRITADI_YOGA_NAMES.get(n, n) for n in AMRITADI_YOGA[i]]


def jd_to_utc_gregorian(jd):
  tm = Time(jd, format='jd')
  tm.format = "ymdhms"
  return [tm.value["year"], tm.value["month"], tm.value["day"],
          tm.value["hour"] + tm.value["minute"] / 60.0 + tm.value["second"] / 3600.0]


def utc_gregorian_to_jd(year, month, day, fractional_hour):
  (hours, minutes, seconds) = hour.decypher_fractional_hours(fractional_hour)
  tm = Time(
    {"year": year, "month": month, "day": day, "hour": int(fractional_hour), "minute": int(minutes), "second": seconds},
    format='ymdhms')
  tm.format = "jd"
  return tm.value


def get_weekday(jd):
  tm = Time(jd, format='jd')
  tm.format = "datetime"
  # Sunday should be 0.
  return tm.value.isocalendar()[2] % 7


def sanitize_time(year_in, month_in, day_in, hour_in, minute_in, second_in):
  (year, month, day, hour, minute, second) = (year_in, month_in, day_in, hour_in, minute_in, second_in)
  if second >= 60:
    minute = minute + second / 60
    second = second % 60
  if minute >= 60:
    hour = hour + minute / 60
    minute = minute % 60
  if hour >= 24:
    day = day + hour / 24
    hour = hour % 24
  from calendar import monthrange
  (_, final_day) = monthrange(year, month)
  if day > final_day:
    assert day == final_day + 1, "range not supported by this function"
    day = 1
    month = month + 1
  if month >= 13:
    year = year + (month - 1) / 12
    month = ((month - 1) % 12) + 1
  return (year, month, day, hour, minute, second)


class PanchaangaApplier(JsonObject):
  """Objects of this type apply various temporal attributes to panchAnga-s."""
  def __init__(self, panchaanga):
    super().__init__()
    self.panchaanga = panchaanga

  def assign_all(self, debug=False):
    pass


class Timezone:
  def __init__(self, timezone_id):
    self.timezone_id = timezone_id

  def get_timezone_offset_hours_from_jd(self, jd):
    """Get timezone offset in hours east of UTC (negative west of UTC)

    Timezone offset is dependent both on place and time (yes- time, not just date) - due to Daylight savings time.
    compute offset from UTC in hours
    """
    local_datetime = self.julian_day_to_local_datetime(jd=jd)
    return (datetime.utcoffset(local_datetime).days * 86400 +
            datetime.utcoffset(local_datetime).seconds) / 3600.0

  def julian_day_to_local_time(self, julian_day, round_seconds=False):
    local_datetime = self.julian_day_to_local_datetime(jd=julian_day)
    local_time = (
    local_datetime.year, local_datetime.month, local_datetime.day, local_datetime.hour, local_datetime.minute,
    local_datetime.second + local_datetime.microsecond / 1000000.0)
    if round_seconds:
      (y, m, dt, hours, minutes, seconds) = local_time
      local_time = sanitize_time(y, m, dt, hours, minutes, int(round(seconds)))
    return local_time

  def julian_day_to_local_datetime(self, jd):
    tm = Time(jd, format='jd')
    tm.format = "datetime"
    return pytz.timezone(self.timezone_id).fromutc(tm.value)

  def local_time_to_julian_day(self, year, month, day, hours, minutes, seconds):
    microseconds, _ = modf(seconds * 1000000)
    local_datetime = pytz.timezone(self.timezone_id).localize(
      datetime(year, month, day, hours, minutes, int(seconds), int(microseconds)))
    tm = Time(local_datetime, format="datetime")
    tm.format = "jd"
    return tm.value

  def julian_day_to_local_time_str(self, jd):
    tm = Time(jd, format='jd')
    tm.format = "datetime"
    local_datetime = pytz.timezone(self.timezone_id).fromutc(tm.value)
    return str(local_datetime)


# A timezone frequently used for debugging (as most developers are located there.)
ist_timezone = Timezone("Asia/Calcutta")

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
