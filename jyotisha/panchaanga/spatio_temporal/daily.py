#!/usr/bin/python3
#  -*- coding: utf-8 -*-
import logging
import sys
from math import floor, modf

from scipy.optimize import brentq

from jyotisha.panchaanga.spatio_temporal import City
from jyotisha.panchaanga.temporal import interval, time
from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.time import Timezone, Hour, Date
from jyotisha.panchaanga.temporal.zodiac import Ayanamsha, NakshatraDivision, AngaType
from sanskrit_data.schema import common

logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s ")


class DayLengthBasedPeriods(common.JsonObject):
  def __init__(self):
    self.braahma = None
    self.praatas_sandhyaa = None
    self.praatas_sandhyaa_end = None
    self.praataH = None
    self.sangava = None
    self.madhyaahna = None
    self.maadhyaahnika_sandhyaa = None
    self.maadhyaahnika_sandhyaa_end = None
    self.aparaahNa = None
    self.saayaahna = None
    self.saayaM_sandhyaa = None
    self.saayaM_sandhyaa_end = None
    self.raatri_yaama_1 = None
    self.dinaanta = None
    self.shayana = None
    self.yama = None
    self.gulika = None
    self.tb_muhuurtas = None


class DayAngas(common.JsonObject):
  def __init__(self):
    self.tithis_with_ends = None
    self.tithi_at_sunrise = None
    self.nakshatras_with_ends = None
    self.nakshatra_at_sunrise = None
    self.yogas_with_ends = None
    self.yoga_at_sunrise = None
    self.karanas_with_ends = None
    self.raashis_with_ends = None


# This class is not named Panchangam in order to be able to disambiguate from annual.Panchangam in serialized objects.
class DailyPanchanga(common.JsonObject):
  """This class enables the construction of a panchaanga
    """

  @classmethod
  def from_city_and_julian_day(cls, city, julian_day, ayanaamsha_id=Ayanamsha.CHITRA_AT_180):
    date = Timezone(city.timezone).julian_day_to_local_time(julian_day)
    return DailyPanchanga(city=city, date=date, ayanaamsha_id=ayanaamsha_id)

  def __init__(self, city: City, date: Date, ayanaamsha_id: str = Ayanamsha.CHITRA_AT_180,
               previous_day_panchaanga=None) -> None:
    """Constructor for the panchaanga.
    """
    super(DailyPanchanga, self).__init__()
    self.city = city
    self.date = date
    date.set_time_to_day_start()
    self.julian_day_start = Timezone(self.city.timezone).local_time_to_julian_day(date=self.date)
    self.ayanaamsha_id = ayanaamsha_id

    self.jd_sunrise = None
    self.jd_sunset = None
    self.jd_previous_sunset = None
    self.jd_next_sunrise = None
    self.jd_moonrise = None
    self.jd_moonset = None

    self.lagna_data = None
    self.day_length_based_periods = None
    self.angas = None

    self.solar_sidereal_date_sunset = None

    self.tropical_date_sunset = None

    self.lunar_month = None

    
    self.shraaddha_tithi = [None]
    self.festivals = []

    self.compute_sun_moon_transitions(previous_day_panchaanga=previous_day_panchaanga)
    self.compute_solar_day_sunset(previous_day_panchaanga=previous_day_panchaanga)
    self.set_tropical_date_sunset(previous_day_panchaanga=previous_day_panchaanga)
    self.get_day_length_based_periods()

  def __lt__(self, other):
    return self.date.get_date_str() < self.date.get_date_str()

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

    if force_recomputation or self.angas is None:
      self.angas = DayAngas()
      self.angas.tithis_with_ends = self.get_angas_today(zodiac.AngaType.TITHI)
      self.angas.tithi_at_sunrise = self.angas.tithis_with_ends[0][0]
      self.angas.nakshatras_with_ends = self.get_angas_today(zodiac.AngaType.NAKSHATRA)
      self.nakshatra_at_sunrise = self.angas.nakshatras_with_ends[0][0]
      self.angas.yogas_with_ends = self.get_angas_today(zodiac.AngaType.NAKSHATRA)
      self.angas.yoga_at_sunrise = self.angas.yogas_with_ends[0][0]
      self.angas.karanas_with_ends = self.get_angas_today(zodiac.AngaType.KARANA)
      self.angas.raashis_with_ends = self.get_angas_today(zodiac.AngaType.RASHI)

  def compute_tb_muhuurtas(self):
    """ Computes muhuurta-s according to taittiriiya brAhmaNa.
    """
    if getattr(self, "jd_sunrise", None) is None:
      self.compute_sun_moon_transitions()
    tb_muhuurtas = []
    for muhuurta_id in range(0, 15):
      (jd_start, jd_end) = interval.get_interval(start_jd=self.jd_sunrise, end_jd=self.jd_sunset,
                                                                              part_index=muhuurta_id, num_parts=15).to_tuple()
      from jyotisha.panchaanga.temporal.interval import TbSayanaMuhuurta
      tb_muhuurtas.append(TbSayanaMuhuurta(
        jd_start=jd_start, jd_end=jd_end,
        muhuurta_id=muhuurta_id))
    self.day_length_based_periods.tb_muhuurtas = tb_muhuurtas

  def compute_solar_day_sunset(self, previous_day_panchaanga=None):
    """Compute the solar month and day for a given Julian day at sunset.
    """
    # If solar transition happens before the current sunset but after the previous sunset, then that is taken to be solar day 1.
    self.compute_sun_moon_transitions(previous_day_panchaanga=previous_day_panchaanga)
    solar_month_sunset = NakshatraDivision(julday=self.jd_sunset, ayanaamsha_id=self.ayanaamsha_id).get_anga(
      anga_type=AngaType.SOLAR_MONTH)

    solar_sidereal_month_end_jd = None
    if previous_day_panchaanga is None or previous_day_panchaanga.solar_sidereal_date_sunset.day > 28 :
      solar_month_sunset_span = zodiac.AngaSpan.find(jd1=self.jd_sunset - 32, jd2=self.jd_sunset + 5, target_anga_id=solar_month_sunset, anga_type=AngaType.SOLAR_MONTH, ayanaamsha_id=self.ayanaamsha_id)
      solar_sidereal_month_day_sunset = len(self.city.get_sunsets_in_period(jd_start=solar_month_sunset_span.jd_start, jd_end=self.jd_sunset + 1/48.0))
      if solar_sidereal_month_day_sunset == 1 and solar_month_sunset_span.jd_start > self.jd_sunrise:
        solar_sidereal_month_end_jd = solar_month_sunset_span.jd_start
      elif solar_sidereal_month_day_sunset == 30 and solar_month_sunset_span.jd_end < self.jd_next_sunrise:
        solar_sidereal_month_end_jd = solar_month_sunset_span.jd_end
    else:
      solar_sidereal_month_day_sunset = previous_day_panchaanga.solar_sidereal_date_sunset.day + 1
    from jyotisha.panchaanga.temporal import time
    self.solar_sidereal_date_sunset = time.BasicDateWithTransitions(month=solar_month_sunset, day=solar_sidereal_month_day_sunset, month_transition=solar_sidereal_month_end_jd)

  def set_tropical_date_sunset(self, previous_day_panchaanga=None):
    month_transition_jd = None
    if previous_day_panchaanga is not None:
      tropical_date_sunset_day = previous_day_panchaanga.tropical_date_sunset.day + 1
      tropical_date_sunset_month = previous_day_panchaanga.tropical_date_sunset.month
    if previous_day_panchaanga is None or previous_day_panchaanga.tropical_date_sunset.day > 28 :
      nd = zodiac.NakshatraDivision(julday=self.jd_sunset, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
      fractional_month = nd.get_fractional_division_for_body(body=Graha.singleton(Graha.SUN), anga_type=AngaType.RASHI)
      (month_fraction, _) = modf(fractional_month)
      approx_day = month_fraction*30
      month_transitions = Graha.singleton(Graha.SUN).get_transits(jd_start=self.jd_sunset-approx_day-5, jd_end=self.jd_sunset + 4, anga_type=AngaType.RASHI, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
      if month_transitions[-1].jd > self.jd_previous_sunset and month_transitions[-1].jd <= self.jd_sunset:
        tropical_date_sunset_day = 1
        tropical_date_sunset_month = month_transitions[-1].value_2
      else:
        tropical_date_sunset_day = len(self.city.get_sunsets_in_period(jd_start=month_transitions[0].jd, jd_end=self.jd_sunset + 1/48.0))
        tropical_date_sunset_month = month_transitions[0].value_2
    self.tropical_date_sunset = time.BasicDateWithTransitions(month=tropical_date_sunset_month, day=tropical_date_sunset_day, month_transition=month_transition_jd)

  def get_lagna_data(self, ayanaamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, debug=False):
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
    if getattr(self, "jd_sunrise", None) is None or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    lagna_sunrise = 1 + floor(self.city.get_lagna_float(self.jd_sunrise, ayanaamsha_id=ayanaamsha_id))

    lagna_list = [(x + lagna_sunrise - 1) % 12 + 1 for x in range(13)]

    lbrack = self.jd_sunrise - 3 / 24
    rbrack = self.jd_sunrise + 3 / 24

    for lagna in lagna_list:
      # print('---\n', lagna)
      if (debug):
        logging.debug(('lagna sunrise', self.city.get_lagna_float(self.jd_sunrise, ayanaamsha_id=ayanaamsha_id)))
        logging.debug(('lbrack', self.city.get_lagna_float(lbrack, int(-lagna), ayanaamsha_id=ayanaamsha_id)))
        logging.debug(('rbrack', self.city.get_lagna_float(rbrack, int(-lagna), ayanaamsha_id=ayanaamsha_id)))

      lagna_end_time = brentq(self.city.get_lagna_float, lbrack, rbrack,
                              args=(-lagna, ayanaamsha_id, debug))
      lbrack = lagna_end_time + 1 / 24
      rbrack = lagna_end_time + 3 / 24
      if lagna_end_time < self.jd_next_sunrise:
        self.lagna_data.append((lagna, lagna_end_time))
    return self.lagna_data

  def get_day_length_based_periods(self):
    # Compute the various day_length_based_periods
    # Sunrise/sunset and related stuff (like rahu, yama)
    if self.day_length_based_periods is not None:
      return self.day_length_based_periods

    if getattr(self, "jd_sunrise", None) is None or self.jd_sunrise is None:
      self.compute_sun_moon_transitions()
    YAMAGANDA_OCTETS = [4, 3, 2, 1, 0, 6, 5]
    RAHUKALA_OCTETS = [7, 1, 6, 4, 5, 3, 2]
    GULIKAKALA_OCTETS = [6, 5, 4, 3, 2, 1, 0]
    weekday = self.date.get_weekday()
    self.day_length_based_periods = DayLengthBasedPeriods()
    self.day_length_based_periods.braahma = interval.get_interval(self.jd_previous_sunset, self.jd_sunrise, 13, 15)
    self.day_length_based_periods.praatas_sandhyaa = interval.get_interval(self.jd_previous_sunset, self.jd_sunrise, 14, 15)
    self.day_length_based_periods.praatas_sandhyaa_end = interval.get_interval(self.jd_sunrise, self.jd_sunset, 4, 15)
    self.day_length_based_periods.praataH = interval.get_interval(self.jd_sunrise, self.jd_sunset, 0, 5)
    self.day_length_based_periods.saangava = interval.get_interval(self.jd_sunrise, self.jd_sunset, 1, 5)
    self.day_length_based_periods.madhyaahna = interval.get_interval(self.jd_sunrise, self.jd_sunset, 2, 5)
    self.day_length_based_periods.maadhyaahnika_sandhyaa = interval.get_interval(self.jd_sunrise, self.jd_sunset, 5, 15)
    self.day_length_based_periods.maadhyaahnika_sandhyaa_end = interval.get_interval(self.jd_sunrise, self.jd_sunset, 13, 15)
    self.day_length_based_periods.aparaahnNa = interval.get_interval(self.jd_sunrise, self.jd_sunset, 3, 5)
    self.day_length_based_periods.saayaahna = interval.get_interval(self.jd_sunrise, self.jd_sunset, 4, 5)
    self.day_length_based_periods.saayaM_sandhyaa = interval.get_interval(self.jd_sunrise, self.jd_sunset, 14, 15)
    self.day_length_based_periods.saayaM_sandhyaa_end = interval.get_interval(self.jd_sunset, self.jd_next_sunrise, 1, 15)
    self.day_length_based_periods.raatri_yaama_1 = interval.get_interval(self.jd_sunset, self.jd_next_sunrise, 1, 4)
    self.day_length_based_periods.shayana = interval.get_interval(self.jd_sunset, self.jd_next_sunrise, 3, 8)
    self.day_length_based_periods.dinaanta = interval.get_interval(self.jd_sunset, self.jd_next_sunrise, 5, 8)
    self.day_length_based_periods.raahu = interval.get_interval(self.jd_sunrise, self.jd_sunset,
                                                               RAHUKALA_OCTETS[weekday], 8)
    self.day_length_based_periods.yama = interval.get_interval(self.jd_sunrise, self.jd_sunset,
                                                               YAMAGANDA_OCTETS[weekday], 8)
    self.day_length_based_periods.gulika = interval.get_interval(self.jd_sunrise, self.jd_sunset,
                                                                 GULIKAKALA_OCTETS[weekday], 8)
    return self.day_length_based_periods

  def get_kaalas_local_time(self, format='hh:mm*'):
    kaalas = self.get_day_length_based_periods()
    return {x: (Hour((kaalas[x].jd_start - self.julian_day_start) * 24).toString(format=format),
                Hour((kaalas[x].jd_end - self.julian_day_start) * 24).toString(format=format)) for x in kaalas.__dict__}

  def get_angas_today(self, anga_type):
    """Computes anga data for angas such as tithi, nakshatra, yoga
    and karana.
  
    Args:
        :param anga_type: TITHI, nakshatra, YOGA, KARANA, SOLAR_MONTH, SOLAR_NAKSH
  
    Returns:
      tuple: A tuple comprising
        anga_sunrise: The anga that prevails as sunrise
        anga_data: a list of (int, float) tuples detailing the angas
        for the day and their end-times (Julian day)
    """
    w_moon = anga_type.weight_moon
    w_sun = anga_type.weight_sun
    arc_len = anga_type.arc_length
  
    num_angas = int(360.0 / arc_len)
  
    # Compute anga details
    anga_now = NakshatraDivision(self.jd_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(anga_type)
    anga_tmrw = NakshatraDivision(self.jd_next_sunrise, ayanaamsha_id=self.ayanaamsha_id).get_anga(anga_type)
  
    angas_list = []
  
    num_angas_today = (anga_tmrw - anga_now) % num_angas
  
    if num_angas_today == 0:
      # The anga does not change until sunrise tomorrow
      return [(anga_now, None)]
    else:
      lmoon = Graha.singleton(Graha.MOON).get_longitude(self.jd_sunrise, ayanaamsha_id=self.ayanaamsha_id)
  
      lsun = Graha.singleton(Graha.SUN).get_longitude(self.jd_sunrise, ayanaamsha_id=self.ayanaamsha_id)
  
      lmoon_tmrw = Graha.singleton(Graha.MOON).get_longitude(self.jd_next_sunrise, ayanaamsha_id=self.ayanaamsha_id)
  
      lsun_tmrw = Graha.singleton(Graha.SUN).get_longitude(self.jd_next_sunrise, ayanaamsha_id=self.ayanaamsha_id)
  
      for i in range(num_angas_today):
        anga_remaining = arc_len * (i + 1) - (((lmoon * w_moon +
                                                lsun * w_sun) % 360) % arc_len)
  
        # First compute approximate end time by essentially assuming
        # the speed of the moon and the sun to be constant
        # throughout the day. Therefore, anga_remaining is computed
        # just based on the difference in longitudes for sun and
        # moon today and tomorrow.
        approx_end = self.jd_sunrise + anga_remaining / (((lmoon_tmrw - lmoon) % 360) * w_moon +
                                                    ((lsun_tmrw - lsun) % 360) * w_sun)
  
        # Initial guess value for the exact end time of the anga
        x0 = approx_end
  
        # What is the target (next) anga? It is needed to be passed
        # to get_anga_float for zero-finding. If the target anga
        # is say, 12, then we need to subtract 12 from the value
        # returned by get_anga_float, so that this function can be
        # passed as is to a zero-finding method like brentq or
        # newton. Since we have a good x0 guess, it is easy to
        # bracket the function in an interval where the function
        # changes sign. Therefore, brenth can be used, as suggested
        # in the scipy documentation.
        target = (anga_now + i - 1) % num_angas + 1
  
        # Approximate error in calculation of end time -- arbitrary
        # used to bracket the root, for brenth
        TDELTA = 0.05
        try:
          def f(x):
            return NakshatraDivision(x, ayanaamsha_id=self.ayanaamsha_id).get_anga_float(anga_type=anga_type) - target
  
          # noinspection PyTypeChecker
          t_act = brentq(f, x0 - TDELTA, x0 + TDELTA)
        except ValueError:
          logging.debug('Unable to bracket! Using approximate t_end itself.')
          # logging.warning(locals())
          t_act = approx_end
        angas_list.extend([((anga_now + i - 1) % num_angas + 1, t_act)])
    return angas_list


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)


if __name__ == '__main__':
  panchaanga = DailyPanchanga.from_city_and_julian_day(city=City('Chennai', '13:05:24', '80:16:12', 'Asia/Calcutta'),
                                                       julian_day=2457023.27)
  panchaanga.compute_tb_muhuurtas()
  logging.debug(str(panchaanga))
