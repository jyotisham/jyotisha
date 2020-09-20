import logging

from jyotisha.panchangam.spatio_temporal import City
from jyotisha.panchangam.temporal import Timezone


def test_get_timezone_offset_hours_from_date():
  city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
  offset = city.get_timezone_offset_hours_from_jd(2458447.000000)
  assert offset == -8


def test_get_timezone_offset_hours_from_date():
  offset = Timezone("America/Los_Angeles").get_timezone_offset_hours_from_date(year=2018, month=11, day=11)
  assert offset == -8


def test_get_local_time():
  city = City.from_address_and_timezone(address="Mountain View, CA", timezone_str="America/Los_Angeles")
  logging.info(city)
  local_time = Timezone(city.timezone).julian_day_to_local_time(julian_day=2458418.319444)
  assert local_time[0] == 2018
  assert local_time[1] == 10
  assert local_time[2] == 26
  assert local_time[3] == 12
  assert local_time[4] == 39


def test_jd_from_local_time():
  city = City.from_address_and_timezone('Cupertino, CA', "America/Los_Angeles")
  jd = Timezone(city.timezone).local_time_to_julian_day(year=2018, month=11, day=11, hours=6, minutes=0, seconds=0)
  import numpy.testing
  numpy.testing.assert_approx_equal(actual=jd, desired=2458433.750000, significant=7)


def test_moonrise_time():
  city = City.from_address_and_timezone('Bengaluru', "Asia/Calcutta")
  from jyotisha.panchangam.temporal.body import Graha
  assert city.get_rising_time(julian_day_start=2459107.33, body=Graha.MOON) == 2459107.4296293524
