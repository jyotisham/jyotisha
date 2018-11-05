#!/usr/bin/python3
#  -*- coding: utf-8 -*-

import logging
import swisseph as swe
import sys
from math import floor

from scipy.optimize import brentq

import jyotisha
from jyotisha.panchangam.spatio_temporal import City
from jyotisha.panchangam.temporal import SOLAR_MONTH, get_angam, get_angam_float
from sanskrit_data.schema import common

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")


class Panchangam(common.JsonObject):
  """This class enables the construction of a panchangam
    """

  def __init__(self, city, julian_day, ayanamsha_id=swe.SIDM_LAHIRI):
    """Constructor for the panchangam.
    """
    super().__init__()
    self.city = city
    self.julian_day = julian_day
    self.julian_day_start = None
    self.compute_jd_start()
    self.ayanamsha_id = ayanamsha_id
    swe.set_sid_mode(ayanamsha_id)
    self.jd_sunrise = None
    self.jd_sunset = None
    self.jd_moonrise = None
    self.jd_moonset = None
    self.tb_muhuurtas = None
    self.solar_month_day = None
    self.solar_month_end_jd = None

  def compute_jd_start(self):
    (year, month, day, hours, minutes, seconds) = self.city.julian_day_to_local_time(self.julian_day)
    self.julian_day_start = self.city.local_time_to_julian_day(year=year, month=month, day=day, hours=0, minutes=0, seconds=1)

  @classmethod
  def from_date(cls, city, year, month, day, ayanamsha_id=swe.SIDM_LAHIRI):
    julian_day = city.local_time_to_julian_day(year=year, month=month, day=day, hours=6, minutes=1, seconds=1)
    return Panchangam(city=city, julian_day=julian_day, ayanamsha_id=ayanamsha_id)

  def compute_sun_moon_transitions(self):
    self.jd_sunrise = swe.rise_trans(
      jd_start=self.julian_day_start, body=swe.SUN,
      lon=self.city.longitude, lat=self.city.latitude,
      rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER)[1][0]
    self.jd_sunset = swe.rise_trans(
      jd_start=self.jd_sunrise, body=swe.SUN,
      lon=self.city.longitude, lat=self.city.latitude,
      rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)[1][0]
    if self.jd_sunset == 0.0:
      logging.error('No sunset was computed!')
      raise (ValueError('No sunset was computed. Perhaps the co-ordinates are beyond the polar circle (most likely a LAT-LONG swap! Please check your inputs.'))
      # logging.debug(swe.rise_trans(jd_start=jd_start, body=swe.SUN, lon=city.longitude,
      #                              lat=city.latitude, rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER))

    self.jd_moonrise = swe.rise_trans(
      jd_start=self.jd_sunrise,
      body=swe.MOON, lon=self.city.longitude,
      lat=self.city.latitude,
      rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER)[1][0]
    self.jd_moonset = swe.rise_trans(
      jd_start=self.jd_moonrise, body=swe.MOON,
      lon=self.city.longitude, lat=self.city.latitude,
      rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)[1][0]

  def compute_solar_month(self):
    if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    swe.set_sid_mode(self.ayanamsha_id)
    self.longitude_sun_sunrise = swe.calc_ut(self.jd_sunrise, swe.SUN)[0] - swe.get_ayanamsa(self.jd_sunrise)
    self.longitude_sun_sunset = swe.calc_ut(self.jd_sunset, swe.SUN)[0] - swe.get_ayanamsa(self.jd_sunset)
    
    # Each solar month has 30 days. So, divide the longitude by 30 to get the solar month.
    self.solar_month_sunset = int(1 + floor((self.longitude_sun_sunset % 360) / 30.0))
    self.solar_month_sunrise = int(1 + floor(((self.longitude_sun_sunrise) % 360) / 30.0))
    # if self.solar_month_sunset != self.solar_month_sunrise:
    #   # sankrAnti.
    #   [_m, self.solar_month_end_jd] = jyotisha.panchangam.temporal.get_angam_data(
    #     self.jd_sunrise[d], self.jd_sunrise[d + 1], jyotisha.panchangam.temporal.SOLAR_MONTH,
    #     ayanamsha_id=self.ayanamsha_id)[0]


  def compute_tb_muhuurtas(self):
    """ Computes muhuurta-s according to taittiriiya brAhmaNa.
    """
    if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    day_length_jd = self.jd_sunset - self.jd_sunrise
    muhuurta_length_jd = day_length_jd/(5*3)
    import numpy
    # 15 muhUrta-s in a day.
    muhuurta_starts =  numpy.arange(self.jd_sunrise, self.jd_sunset, muhuurta_length_jd)[0:15]
    from jyotisha.panchangam import spatio_temporal
    self.tb_muhuurtas = [spatio_temporal.TbSayanaMuhuurta(
      city=self.city, jd_start=jd_start, jd_end=jd_start + muhuurta_length_jd,
      muhuurta_id=int((jd_start - self.jd_sunrise + muhuurta_length_jd/10)/muhuurta_length_jd))
                         for jd_start in muhuurta_starts]

  def compute_solar_day(self):
    """Compute the solar month and day for a given Julian day
    """
    # If solar transition happens before the current sunset but after the previous sunset, then that is taken to be solar day 1. Number of sunsets since the past solar month transition gives the solar day number.
    if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    self.solar_month = get_angam(self.jd_sunset, SOLAR_MONTH, ayanamsha_id=self.ayanamsha_id)
    target = floor(get_angam_float(self.jd_sunset, SOLAR_MONTH, ayanamsha_id=self.ayanamsha_id))

    # logging.debug(jd_start)
    # logging.debug(jd_sunset)
    # logging.debug(target)
    # logging.debug(get_angam_float(jd_sunset - 34, SOLAR_MONTH, -target, ayanamsha_id, False))
    # logging.debug(get_angam_float(jd_sunset + 1, SOLAR_MONTH, -target, ayanamsha_id, False))
    jd_masa_transit = brentq(get_angam_float, self.jd_sunrise - 34, self.jd_sunset,
                             args=(SOLAR_MONTH, -target, self.ayanamsha_id, False))

    jd_next_sunset = swe.rise_trans(jd_start=jd_masa_transit, body=swe.SUN,
                                    lon=self.city.longitude, lat=self.city.latitude,
                                    rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER)[1][0]

    jd_next_sunrise = swe.rise_trans(jd_start=jd_masa_transit, body=swe.SUN,
                                     lon=self.city.longitude, lat=self.city.latitude,
                                     rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER)[1][0]

    if jd_next_sunset > jd_next_sunrise:
      # Masa begins after sunset and before sunrise
      # Therefore Masa 1 is on the day when the sun rises next
      solar_month_day = floor(self.jd_sunset - jd_next_sunrise) + 1
    else:
      # Masa has started before sunset
      solar_month_day = round(self.jd_sunset - jd_next_sunset) + 1
    self.solar_month_day = solar_month_day


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
logging.debug(common.json_class_index)


if __name__ == '__main__':
  panchangam = Panchangam(city=City('Chennai', '13:05:24', '80:16:12', 'Asia/Calcutta'), julian_day=2457023.27)
  panchangam.compute_tb_muhuurtas()
  logging.debug(str(panchangam))
