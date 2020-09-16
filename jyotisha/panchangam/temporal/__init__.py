import logging
import sys

from astropy.time import Time

from jyotisha.panchangam.temporal import hour
from jyotisha.panchangam.temporal.body import Graha
from jyotisha.panchangam.temporal.zodiac import Ayanamsha
from sanskrit_data.schema import common

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
    return [tm.value["year"], tm.value["month"], tm.value["day"], tm.value["hour"] + tm.value["minute"] / 60.0 + tm.value["second"] / 3600.0]


def utc_gregorian_to_jd(year, month, day, fractional_hour):
    (hours, minutes, seconds) = hour.decypher_fractional_hours(fractional_hour) 
    tm = Time({"year": year, "month": month, "day": day, "hour": int(fractional_hour), "minute": int(minutes), "second": seconds}, format='ymdhms')
    tm.format = "jd"
    return tm.value


def get_weekday(jd):
    tm = Time(jd, format='jd')
    tm.format = "datetime"
    # Sunday should be 0.
    return tm.value.isocalendar()[2] % 7


def get_interval(start_jd, end_jd, part_index, num_parts):
    """Get start and end time of a given interval in a given span with specified fractions

    Args:
      :param start_jd float (jd)
      :param end_jd float (jd)
      :param part_index int, minimum/ start value 0
      :param num_parts

    Returns:
       tuple (start_time_jd, end_time_jd)

    Examples:

    """
    start_fraction = part_index / num_parts
    end_fraction = (part_index + 1) / num_parts

    start_time = start_jd + (end_jd - start_jd) * start_fraction
    end_time = start_jd + (end_jd - start_jd) * end_fraction

    return (start_time, end_time)


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


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
