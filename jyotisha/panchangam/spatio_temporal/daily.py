#!/usr/bin/python3
#  -*- coding: utf-8 -*-
import datetime
import logging
import sys
from math import floor

from scipy.optimize import brentq

import jyotisha.panchangam.temporal
from jyotisha.panchangam.spatio_temporal import City
from jyotisha.panchangam.temporal import interval, Timezone
from jyotisha.panchangam.temporal import zodiac
from jyotisha.panchangam.temporal.body import Graha
from jyotisha.panchangam.temporal.hour import Hour
from jyotisha.panchangam.temporal.zodiac import Ayanamsha, NakshatraDivision, AngaTypes
from sanskrit_data.schema import common

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")


# This class is not named Panchangam in order to be able to disambiguate from annual.Panchangam in serialized objects.
class DailyPanchanga(common.JsonObject):
  """This class enables the construction of a panchangam
    """

  @classmethod
  def from_city_and_julian_day(cls, city, julian_day, ayanamsha_id=Ayanamsha.CHITRA_AT_180):
    (year, month, day, hours, minutes, seconds) = Timezone(city.timezone).julian_day_to_local_time(julian_day)
    return DailyPanchanga(city=city, year=year, month=month, day=day, ayanamsha_id=ayanamsha_id)

  def __init__(self, city: City, year: int, month: int, day: int, ayanamsha_id: str = Ayanamsha.CHITRA_AT_180,
               previous_day_panchaanga=None) -> None:
    """Constructor for the panchangam.
    """
    super(DailyPanchanga, self).__init__()
    self.city = city
    (self.year, self.month, self.day) = (year, month, day)
    self.julian_day_start = Timezone(self.city.timezone).local_time_to_julian_day(year=self.year, month=self.month,
                                                                                  day=self.day, hours=0, minutes=0,
                                                                                  seconds=0)

    self.weekday = datetime.date(year=self.year, month=self.month, day=self.day).isoweekday() % 7
    self.ayanamsha_id = ayanamsha_id

    self.jd_sunrise = None
    self.jd_sunset = None
    self.jd_previous_sunset = None
    self.jd_next_sunrise = None
    self.jd_moonrise = None
    self.jd_moonset = None
    self.compute_sun_moon_transitions(previous_day_panchaanga=previous_day_panchaanga)

    self.tb_muhuurtas = None
    self.lagna_data = None
    self.kaalas = None

    self.solar_month_day = None
    self.solar_month_end_jd = None

    self.tithi_data = None
    self.tithi_at_sunrise = None
    self.nakshatra_data = None
    self.nakshatra_at_sunrise = None
    self.yoga_data = None
    self.yoga_at_sunrise = None
    self.karana_data = None
    self.raashi_data = None

    self.festivals = []

  def compute_sun_moon_transitions(self, previous_day_panchaanga=None, force_recomputation=False):
    """

    :param previous_day_panchaanga: Panchangam for previous day, to avoid unnecessary calculations. (rise_trans calculations can be time consuming.)
    :param force_recomputation: Boolean indicating if the transitions should be recomputed. (rise_trans calculations can be time consuming.)
    :return:
    """
    if force_recomputation or self.jd_sunrise is None:
      if previous_day_panchaanga is not None and previous_day_panchaanga.jd_next_sunrise is not None:
        self.jd_sunrise = previous_day_panchaanga.jd_next_sunrise
      else:
        self.jd_sunrise = self.city.get_rising_time(julian_day_start=self.julian_day_start, body=Graha.SUN)
    if force_recomputation or self.jd_sunset is None:
      self.jd_sunset = self.city.get_setting_time(julian_day_start=self.jd_sunrise, body=Graha.SUN)
    if force_recomputation or self.jd_previous_sunset is None:
      if previous_day_panchaanga is not None and previous_day_panchaanga.jd_sunset is not None:
        self.jd_previous_sunset = previous_day_panchaanga.jd_sunset
      else:
        self.jd_previous_sunset = self.city.get_setting_time(julian_day_start=self.jd_sunrise - 1,
                                                             body=Graha.SUN)
    if force_recomputation or self.jd_next_sunrise is None:
      self.jd_next_sunrise = self.city.get_rising_time(julian_day_start=self.jd_sunset, body=Graha.SUN)
    if self.jd_sunset == 0.0:
      logging.error('No sunset was computed!')
      raise (ValueError(
        'No sunset was computed. Perhaps the co-ordinates are beyond the polar circle (most likely a LAT-LONG swap! Please check your inputs.'))

    if force_recomputation or self.jd_moonrise is None:
      self.jd_moonrise = self.city.get_rising_time(julian_day_start=self.jd_sunrise, body=Graha.MOON)
    if force_recomputation or self.jd_moonset is None:
      self.jd_moonset = self.city.get_setting_time(julian_day_start=self.jd_sunrise, body=Graha.MOON)

    self.tithi_data = zodiac.get_angam_data(self.jd_sunrise, self.jd_next_sunrise,
                                            zodiac.AngaTypes.TITHI, ayanamsha_id=self.ayanamsha_id)
    self.tithi_at_sunrise = self.tithi_data[0][0]
    self.nakshatra_data = zodiac.get_angam_data(self.jd_sunrise, self.jd_next_sunrise,
                                                zodiac.AngaTypes.NAKSHATRA, ayanamsha_id=self.ayanamsha_id)
    self.nakshatra_at_sunrise = self.nakshatra_data[0][0]
    self.yoga_data = zodiac.get_angam_data(self.jd_sunrise, self.jd_next_sunrise,
                                           zodiac.AngaTypes.NAKSHATRA, ayanamsha_id=self.ayanamsha_id)
    self.yoga_at_sunrise = self.yoga_data[0][0]
    self.karana_data = zodiac.get_angam_data(self.jd_sunrise, self.jd_next_sunrise,
                                             zodiac.AngaTypes.KARANA, ayanamsha_id=self.ayanamsha_id)
    self.raashi_data = zodiac.get_angam_data(self.jd_sunrise, self.jd_next_sunrise,
                                             zodiac.AngaTypes.NAKSHATRA, ayanamsha_id=self.ayanamsha_id)

  def compute_solar_month(self):
    if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()

    self.longitude_sun_sunrise = Graha.singleton(Graha.SUN).get_longitude(self.jd_sunrise) - Ayanamsha.singleton(
      self.ayanamsha_id).get_offset(self.jd_sunrise)
    self.longitude_sun_sunset = Graha.singleton(Graha.SUN).get_longitude(self.jd_sunset) - Ayanamsha.singleton(
      self.ayanamsha_id).get_offset(self.jd_sunset)

    # Each solar month has 30 days. So, divide the longitude by 30 to get the solar month.
    self.solar_month_sunset = int(1 + floor((self.longitude_sun_sunset % 360) / 30.0))
    self.solar_month_sunrise = int(1 + floor(((self.longitude_sun_sunrise) % 360) / 30.0))
    # if self.solar_month_sunset != self.solar_month_sunrise:
    #   # sankrAnti.
    #   [_m, self.solar_month_end_jd] = temporal.get_angam_data(
    #     self.jd_sunrise, self.jd_next_sunrise, temporal.SOLAR_MONTH,
    #     ayanamsha_id=self.ayanamsha_id)[0]

  def compute_tb_muhuurtas(self):
    """ Computes muhuurta-s according to taittiriiya brAhmaNa.
    """
    if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    from jyotisha.panchangam import spatio_temporal
    self.tb_muhuurtas = []
    for muhuurta_id in range(0, 15):
      (jd_start, jd_end) = interval.get_interval(start_jd=self.jd_sunrise, end_jd=self.jd_sunset,
                                                                              part_index=muhuurta_id, num_parts=15).to_tuple()
      self.tb_muhuurtas.append(jyotisha.panchangam.temporal.interval.TbSayanaMuhuurta(
        city=self.city, jd_start=jd_start, jd_end=jd_end,
        muhuurta_id=muhuurta_id))

  def compute_solar_day(self):
    """Compute the solar month and day for a given Julian day
    """
    # If solar transition happens before the current sunset but after the previous sunset, then that is taken to be solar day 1. Number of sunsets since the past solar month transition gives the solar day number.
    if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    self.solar_month = NakshatraDivision(self.jd_sunset, ayanamsha_id=self.ayanamsha_id).get_anga(AngaTypes.SOLAR_MONTH)
    target = ((floor(NakshatraDivision(self.jd_sunset, ayanamsha_id=self.ayanamsha_id).get_anga_float(
      AngaTypes.SOLAR_MONTH)) - 1) % 12) + 1

    # logging.debug(jd_start)
    # logging.debug(jd_sunset)
    # logging.debug(target)
    # logging.debug(get_angam_float(jd_sunset - 34, SOLAR_MONTH, -target, ayanamsha_id, False))
    # logging.debug(get_angam_float(jd_sunset + 1, SOLAR_MONTH, -target, ayanamsha_id, False))

    jd_masa_transit = brentq(
      lambda x: NakshatraDivision(x, ayanamsha_id=self.ayanamsha_id).get_anga_float(AngaTypes.SOLAR_MONTH, -target, False),
      self.jd_sunrise - 34, self.jd_sunset)

    jd_sunset_after_masa_transit = self.city.get_setting_time(julian_day_start=jd_masa_transit, body=Graha.SUN)

    jd_sunrise_after_masa_transit = self.city.get_rising_time(julian_day_start=jd_masa_transit, body=Graha.SUN)

    if jd_sunset_after_masa_transit > jd_sunrise_after_masa_transit:
      # Masa begins after sunset and before sunrise
      # Therefore Masa 1 is on the day when the sun rises next
      solar_month_day = floor(self.jd_sunset - jd_sunrise_after_masa_transit) + 1
    else:
      # Masa has started before sunset
      solar_month_day = round(self.jd_sunset - jd_sunset_after_masa_transit) + 1
    self.solar_month_day = solar_month_day

  def get_lagna_data(self, ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, debug=False):
    """Returns the lagna data

        Args:
          debug

        Returns:
          tuples detailing the end time of each lagna, beginning with the one
          prevailing at sunrise
        """
    if self.lagna_data is not None:
      return self.lagna_data

    self.lagna_data = []
    if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    lagna_sunrise = 1 + floor(self.city.get_lagna_float(self.jd_sunrise, ayanamsha_id=ayanamsha_id))

    lagna_list = [(x + lagna_sunrise - 1) % 12 + 1 for x in range(13)]

    lbrack = self.jd_sunrise - 3 / 24
    rbrack = self.jd_sunrise + 3 / 24

    for lagna in lagna_list:
      # print('---\n', lagna)
      if (debug):
        logging.debug(('lagna sunrise', self.city.get_lagna_float(self.jd_sunrise, ayanamsha_id=ayanamsha_id)))
        logging.debug(('lbrack', self.city.get_lagna_float(lbrack, int(-lagna), ayanamsha_id=ayanamsha_id)))
        logging.debug(('rbrack', self.city.get_lagna_float(rbrack, int(-lagna), ayanamsha_id=ayanamsha_id)))

      lagna_end_time = brentq(self.city.get_lagna_float, lbrack, rbrack,
                              args=(-lagna, ayanamsha_id, debug))
      lbrack = lagna_end_time + 1 / 24
      rbrack = lagna_end_time + 3 / 24
      if lagna_end_time < self.jd_next_sunrise:
        self.lagna_data.append((lagna, lagna_end_time))
    return self.lagna_data

  def get_kaalas(self):
    # Compute the various kaalas
    # Sunrise/sunset and related stuff (like rahu, yama)
    if self.kaalas is not None:
      return self.kaalas

    if not hasattr(self, "jd_sunrise") or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    YAMAGANDA_OCTETS = [4, 3, 2, 1, 0, 6, 5]
    RAHUKALA_OCTETS = [7, 1, 6, 4, 5, 3, 2]
    GULIKAKALA_OCTETS = [6, 5, 4, 3, 2, 1, 0]
    self.kaalas = {
      'braahma': interval.get_interval(self.jd_previous_sunset, self.jd_sunrise, 13, 15).to_tuple(),
      'prAtaH sandhyA': interval.get_interval(self.jd_previous_sunset, self.jd_sunrise, 14, 15).to_tuple(),
      'prAtaH sandhyA end': interval.get_interval(self.jd_sunrise, self.jd_sunset, 4, 15).to_tuple(),
      'prAtah': interval.get_interval(self.jd_sunrise, self.jd_sunset, 0, 5).to_tuple(),
      'saGgava': interval.get_interval(self.jd_sunrise, self.jd_sunset, 1, 5).to_tuple(),
      'madhyAhna': interval.get_interval(self.jd_sunrise, self.jd_sunset, 2, 5).to_tuple(),
      'mAdhyAhnika sandhyA': interval.get_interval(self.jd_sunrise, self.jd_sunset, 5, 15).to_tuple(),
      'mAdhyAhnika sandhyA end': interval.get_interval(self.jd_sunrise, self.jd_sunset, 13, 15).to_tuple(),
      'aparAhna': interval.get_interval(self.jd_sunrise, self.jd_sunset, 3, 5).to_tuple(),
      'sAyAhna': interval.get_interval(self.jd_sunrise, self.jd_sunset, 4, 5).to_tuple(),
      'sAyaM sandhyA': interval.get_interval(self.jd_sunrise, self.jd_sunset, 14, 15).to_tuple(),
      'sAyaM sandhyA end': interval.get_interval(self.jd_sunset, self.jd_next_sunrise, 1, 15).to_tuple(),
      'rAtri yAma 1': interval.get_interval(self.jd_sunset, self.jd_next_sunrise, 1, 4).to_tuple(),
      'zayana': interval.get_interval(self.jd_sunset, self.jd_next_sunrise, 3, 8).to_tuple(),
      'dinAnta': interval.get_interval(self.jd_sunset, self.jd_next_sunrise, 5, 8).to_tuple(),
      'rahu': interval.get_interval(self.jd_sunrise, self.jd_sunset,
                                                                 RAHUKALA_OCTETS[self.weekday], 8).to_tuple(),
      'yama': interval.get_interval(self.jd_sunrise, self.jd_sunset,
                                                                 YAMAGANDA_OCTETS[self.weekday], 8).to_tuple(),
      'gulika': interval.get_interval(self.jd_sunrise, self.jd_sunset,
                                                                   GULIKAKALA_OCTETS[self.weekday], 8).to_tuple()
    }
    return self.kaalas

  def get_kaalas_local_time(self, format='hh:mm*'):
    kaalas = self.get_kaalas()
    return {x: (Hour((kaalas[x][0] - self.julian_day_start) * 24).toString(format=format),
                Hour((kaalas[x][1] - self.julian_day_start) * 24).toString(format=format)) for x in kaalas}

  def update_festival_details(self):
    pass


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)


if __name__ == '__main__':
  panchangam = DailyPanchanga.from_city_and_julian_day(city=City('Chennai', '13:05:24', '80:16:12', 'Asia/Calcutta'),
                                                       julian_day=2457023.27)
  panchangam.compute_tb_muhuurtas()
  logging.debug(str(panchangam))
