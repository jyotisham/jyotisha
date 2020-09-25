import logging

from jyotisha.panchaanga.temporal.time import Date, Timezone
from jyotisha.panchaanga.temporal import time

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


def test_sanitize_time():
  assert Date(2018, 11, 11, 10, 8, 60).sanitize() == (2018, 11, 11, 10, 9, 00)
  assert Date(2018, 12, 31, 23, 60, 00).sanitize() == (2019, 1, 1, 00, 00, 00)


def test_jd_to_utc():
  assert time.jd_to_utc_gregorian(2458434.083333251).to_date_fractional_hour_tuple() == [2018, 11, 11, 13.99999802559611]


def test_utc_to_jd():
  assert abs(
    time.utc_gregorian_to_jd(Date(2018, 11, 11, 14, 0, 0)) - 2458434.083333251) < .001



def test_get_local_time():
  local_time = Timezone("America/Los_Angeles").julian_day_to_local_time(julian_day=2458418.319444).as_tuple()
  assert local_time[0] == 2018
  assert local_time[1] == 10
  assert local_time[2] == 26
  assert local_time[3] == 12
  assert local_time[4] == 39


def test_jd_from_local_time():
  jd = Timezone("America/Los_Angeles").local_time_to_julian_day(date=Date(year=2018, month=11, day=11, hour=6, minute=0, second=0))
  import numpy.testing
  numpy.testing.assert_approx_equal(actual=jd, desired=2458433.750000, significant=7)


def test_get_timezone_offset_hours_from_jd():
  tz = Timezone("America/Los_Angeles")
  assert tz.get_timezone_offset_hours_from_jd(2458447) == -8


def test_get_weekday():
  # 2018, 11, 11 was sunday
  assert time.get_weekday(2458434.083333251) == 0
