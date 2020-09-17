import logging
import os
import sys
import traceback
from datetime import datetime
from math import floor
from typing import List

from indic_transliteration import xsanscript as sanscript
from pytz import timezone as tz

import jyotisha.panchangam.temporal.festival.applier
import jyotisha.panchangam.temporal.festival.applier.ecliptic
import jyotisha.panchangam.temporal.festival.applier.solar
import jyotisha.panchangam.temporal.festival.applier.tithi
import jyotisha.panchangam.temporal.festival.applier.vaara
from jyotisha import names
from jyotisha.panchangam import temporal, spatio_temporal
from jyotisha.panchangam.spatio_temporal import CODE_ROOT, daily
from jyotisha.panchangam.temporal import zodiac
from jyotisha.panchangam.temporal.body import Graha
from jyotisha.panchangam.temporal.festival import read_old_festival_rules_dict
from jyotisha.panchangam.temporal.hour import Hour
from jyotisha.panchangam.temporal.month import SiderialSolarBasedAssigner, MonthAssigner
from jyotisha.panchangam.temporal.zodiac import NakshatraDivision, AngaSpan
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject


class Panchangam(common.JsonObject):
  """This class enables the construction of a panchangam for arbitrary periods, with festivals.
    """

  def __init__(self, city, start_date, end_date, lunar_month_assigner_type=MonthAssigner.SIDERIAL_SOLAR_BASED, script=sanscript.DEVANAGARI, fmt='hh:mm',
               ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180,
               compute_lagnams=False):
    """Constructor for the panchangam.
    :param compute_lagnams:
    :param compute_lagnams:
        """
    super(Panchangam, self).__init__()
    self.city = city
    self.start_date = tuple([int(x) for x in start_date.split('-')])  # (tuple of (yyyy, mm, dd))
    self.end_date = tuple([int(x) for x in end_date.split('-')])  # (tuple of (yyyy, mm, dd))
    self.script = script
    self.fmt = fmt

    self.jd_start_utc = temporal.utc_gregorian_to_jd(self.start_date[0], self.start_date[1], self.start_date[2], 0)
    self.jd_end_utc = temporal.utc_gregorian_to_jd(self.end_date[0], self.end_date[1], self.end_date[2], 0)

    self.duration = int(self.jd_end_utc - self.jd_start_utc) + 1
    self.len = int(self.duration + 4)  # some buffer, for various look-ahead calculations

    self.weekday_start = temporal.get_weekday(self.jd_start_utc)

    self.ayanamsha_id = ayanamsha_id

    self.compute_angams(compute_lagnams=compute_lagnams)
    lunar_month_assigner = MonthAssigner.get_assigner(assigner_id=lunar_month_assigner_type, panchaanga=self)
    lunar_month_assigner.assign()

  def compute_angams(self, compute_lagnams=True):
    """Compute the entire panchangam
    """

    nDays = self.len

    # INITIALISE VARIABLES
    self.jd_midnight = [None] * nDays
    self.jd_sunrise = [None] * nDays
    self.jd_sunset = [None] * nDays
    self.jd_moonrise = [None] * nDays
    self.jd_moonset = [None] * nDays
    self.solar_month = [None] * nDays
    self.solar_month_end_time = [None] * nDays
    self.solar_month_day = [None] * nDays
    self.tropical_month = [None] * nDays
    self.tropical_month_end_time = [None] * nDays

    solar_month_sunrise = [None] * nDays

    self.lunar_month = [None] * nDays
    self.tithi_data = [None] * nDays
    self.tithi_sunrise = [None] * nDays
    self.nakshatram_data = [None] * nDays
    self.nakshatram_sunrise = [None] * nDays
    self.yoga_data = [None] * nDays
    self.yoga_sunrise = [None] * nDays
    self.karanam_data = [None] * nDays
    self.rashi_data = [None] * nDays
    self.kaalas = [None] * nDays

    if compute_lagnams:
      self.lagna_data = [None] * nDays

    self.weekday = [None] * nDays
    daily_panchaangas: List[daily.DailyPanchanga] = [None] * nDays

    # Computing solar month details for Dec 31
    # rather than Jan 1, since we have an always increment
    # solar_month_day at the start of the loop across every day in
    # year
    [prev_day_yy, prev_day_mm, prev_day_dd] = temporal.jd_to_utc_gregorian(self.jd_start_utc - 1)[:3]
    daily_panchangam_start = daily.DailyPanchanga(city=self.city, year=prev_day_yy, month=prev_day_mm,
                                                  day=prev_day_dd, ayanamsha_id=self.ayanamsha_id)
    daily_panchangam_start.compute_solar_day()
    self.solar_month[1] = daily_panchangam_start.solar_month
    solar_month_day = daily_panchangam_start.solar_month_day

    solar_month_today_sunset = NakshatraDivision(daily_panchangam_start.jd_sunset,
                                                 ayanamsha_id=self.ayanamsha_id).get_anga(
      zodiac.SOLAR_MONTH)
    solar_month_tmrw_sunrise = NakshatraDivision(daily_panchangam_start.jd_sunrise + 1,
                                                 ayanamsha_id=self.ayanamsha_id).get_anga(
      zodiac.SOLAR_MONTH)
    month_start_after_sunset = solar_month_today_sunset != solar_month_tmrw_sunrise

    #############################################################
    # Compute all parameters -- sun/moon latitude/longitude etc #
    #############################################################

    for d in range(nDays):
      self.weekday[d] = (self.weekday_start + d - 1) % 7

    for d in range(-1, nDays - 1):
      # TODO: Eventually, we are shifting to an array of daily panchangas. Reason: Better modularity.
      # The below block is temporary code to make the transition seamless.
      (year_d, month_d, day_d, _) = temporal.jd_to_utc_gregorian(self.jd_start_utc + d)
      daily_panchaangas[d + 1] = daily.DailyPanchanga(city=self.city, year=year_d, month=month_d, day=day_d,
                                                      ayanamsha_id=self.ayanamsha_id,
                                                      previous_day_panchangam=daily_panchaangas[d])
      daily_panchaangas[d + 1].compute_sun_moon_transitions(previous_day_panchangam=daily_panchaangas[d])
      daily_panchaangas[d + 1].compute_solar_month()
      self.jd_midnight[d + 1] = daily_panchaangas[d + 1].julian_day_start
      self.jd_sunrise[d + 1] = daily_panchaangas[d + 1].jd_sunrise
      self.jd_sunset[d + 1] = daily_panchaangas[d + 1].jd_sunset
      self.jd_moonrise[d + 1] = daily_panchaangas[d + 1].jd_moonrise
      self.jd_moonset[d + 1] = daily_panchaangas[d + 1].jd_moonset
      self.solar_month[d + 1] = daily_panchaangas[d + 1].solar_month_sunset

      solar_month_sunrise[d + 1] = daily_panchaangas[d + 1].solar_month_sunrise

      if (d <= 0):
        continue
        # This is just to initialise, since for a lot of calculations,
        # we require comparing with tomorrow's data. This computes the
        # data for day 0, -1.

      # Solar month calculations
      if month_start_after_sunset is True:
        solar_month_day = 0
        month_start_after_sunset = False

      solar_month_end_jd = None
      if self.solar_month[d] != self.solar_month[d + 1]:
        solar_month_day = solar_month_day + 1
        if self.solar_month[d] != solar_month_sunrise[d + 1]:
          month_start_after_sunset = True
          [_m, solar_month_end_jd] = zodiac.get_angam_data(
            self.jd_sunrise[d], self.jd_sunrise[d + 1], zodiac.SOLAR_MONTH, ayanamsha_id=self.ayanamsha_id)[
            0]
      elif solar_month_sunrise[d] != self.solar_month[d]:
        # sankrAnti!
        # sun moves into next rAshi before sunset
        solar_month_day = 1
        [_m, solar_month_end_jd] = zodiac.get_angam_data(
          self.jd_sunrise[d], self.jd_sunrise[d + 1], zodiac.SOLAR_MONTH, ayanamsha_id=self.ayanamsha_id)[0]
      else:
        solar_month_day = solar_month_day + 1
        solar_month_end_jd = None

      self.solar_month_end_time[d] = solar_month_end_jd

      self.solar_month_day[d] = solar_month_day

      # Compute all the anga datas
      self.tithi_data[d] = daily_panchaangas[d].tithi_data
      self.tithi_sunrise[d] = daily_panchaangas[d].tithi_at_sunrise
      self.nakshatram_data[d] = daily_panchaangas[d].nakshatram_data
      self.nakshatram_sunrise[d] = daily_panchaangas[d].nakshatram_at_sunrise
      self.yoga_data[d] = daily_panchaangas[d].yoga_data
      self.yoga_sunrise[d] = daily_panchaangas[d].yoga_at_sunrise
      self.karanam_data[d] = daily_panchaangas[d].karanam_data
      self.rashi_data[d] = daily_panchaangas[d].rashi_data
      self.kaalas[d] = daily_panchaangas[d].get_kaalas()
      if compute_lagnams:
        self.lagna_data[d] = daily_panchaangas[d].get_lagna_data()


  def get_angams_for_kaalas(self, d, get_angam_func, kaala_type):
    jd_sunrise = self.jd_sunrise[d]
    jd_sunrise_tmrw = self.jd_sunrise[d + 1]
    jd_sunrise_datmrw = self.jd_sunrise[d + 2]
    jd_sunset = self.jd_sunset[d]
    jd_sunset_tmrw = self.jd_sunset[d + 1]
    jd_moonrise = self.jd_moonrise[d]
    jd_moonrise_tmrw = self.jd_moonrise[d + 1]
    if kaala_type == 'sunrise':
      angams = [get_angam_func(jd_sunrise),
                get_angam_func(jd_sunrise),
                get_angam_func(jd_sunrise_tmrw),
                get_angam_func(jd_sunrise_tmrw)]
    elif kaala_type == 'sunset':
      angams = [get_angam_func(jd_sunset),
                get_angam_func(jd_sunset),
                get_angam_func(jd_sunset_tmrw),
                get_angam_func(jd_sunset_tmrw)]
    elif kaala_type == 'praatah':
      angams = [get_angam_func(jd_sunrise),  # praatah1 start
                # praatah1 end
                get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (1.0 / 5.0)),
                get_angam_func(jd_sunrise_tmrw),  # praatah2 start
                # praatah2 end
                get_angam_func(jd_sunrise_tmrw + \
                               (jd_sunset_tmrw - jd_sunrise_tmrw) * (1.0 / 5.0))]
    elif kaala_type == 'sangava':
      angams = [
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (1.0 / 5.0)),
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (2.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw +
                       (jd_sunset_tmrw - jd_sunrise_tmrw) * (1.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw +
                       (jd_sunset_tmrw - jd_sunrise_tmrw) * (2.0 / 5.0))]
    elif kaala_type == 'madhyaahna':
      angams = [
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (2.0 / 5.0)),
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (3.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw +
                       (jd_sunset_tmrw - jd_sunrise_tmrw) * (2.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw + (jd_sunset_tmrw -
                                          jd_sunrise_tmrw) * (3.0 / 5.0))]
    elif kaala_type == 'aparaahna':
      angams = [
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (3.0 / 5.0)),
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (4.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw +
                       (jd_sunset_tmrw - jd_sunrise_tmrw) * (3.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw +
                       (jd_sunset_tmrw - jd_sunrise_tmrw) * (4.0 / 5.0))]
    elif kaala_type == 'saayaahna':
      angams = [
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (4.0 / 5.0)),
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (5.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw +
                       (jd_sunset_tmrw - jd_sunrise_tmrw) * (4.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw +
                       (jd_sunset_tmrw - jd_sunrise_tmrw) * (5.0 / 5.0))]
    elif kaala_type == 'madhyaraatri':
      angams = [
        get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (2.0 / 5.0)),
        get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (3.0 / 5.0)),
        get_angam_func(jd_sunset_tmrw +
                       (jd_sunrise_datmrw - jd_sunset_tmrw) * (2.0 / 5.0)),
        get_angam_func(jd_sunset_tmrw +
                       (jd_sunrise_datmrw - jd_sunset_tmrw) * (3.0 / 5.0))]
    elif kaala_type == 'pradosha':
      # pradOSo.astamayAdUrdhvaM ghaTikAdvayamiShyatE (tithyAdi tattvam, Vrat Parichay p. 25 Gita Press)
      angams = [get_angam_func(jd_sunset),
                get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (1.0 / 15.0)),
                get_angam_func(jd_sunset_tmrw),
                get_angam_func(jd_sunset_tmrw +
                               (jd_sunrise_datmrw - jd_sunset_tmrw) * (1.0 / 15.0))]
    elif kaala_type == 'nishita':
      angams = [
        get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (7.0 / 15.0)),
        get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (8.0 / 15.0)),
        get_angam_func(jd_sunset_tmrw +
                       (jd_sunrise_datmrw - jd_sunset_tmrw) * (7.0 / 15.0)),
        get_angam_func(jd_sunset_tmrw +
                       (jd_sunrise_datmrw - jd_sunset_tmrw) * (8.0 / 15.0))]
    elif kaala_type == 'dinamaana':
      angams = [
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (0.0 / 5.0)),
        get_angam_func(jd_sunrise + (jd_sunset - jd_sunrise) * (5.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw +
                       (jd_sunset_tmrw - jd_sunrise_tmrw) * (0.0 / 5.0)),
        get_angam_func(jd_sunrise_tmrw + (jd_sunset_tmrw -
                                          jd_sunrise_tmrw) * (5.0 / 5.0))]
    elif kaala_type == 'raatrimaana':
      angams = [
        get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (0.0 / 15.0)),
        get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (15.0 / 15.0)),
        get_angam_func(jd_sunset_tmrw +
                       (jd_sunrise_datmrw - jd_sunset_tmrw) * (0.0 / 15.0)),
        get_angam_func(jd_sunset_tmrw +
                       (jd_sunrise_datmrw - jd_sunset_tmrw) * (15.0 / 15.0))]
    elif kaala_type == 'arunodaya':  # deliberately not simplifying expressions involving 15/15
      angams = [
        get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (13.0 / 15.0)),
        get_angam_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (15.0 / 15.0)),
        get_angam_func(jd_sunset_tmrw +
                       (jd_sunrise_datmrw - jd_sunset_tmrw) * (13.0 / 15.0)),
        get_angam_func(jd_sunset_tmrw +
                       (jd_sunrise_datmrw - jd_sunset_tmrw) * (15.0 / 15.0))]
    elif kaala_type == 'moonrise':
      angams = [get_angam_func(jd_moonrise),
                get_angam_func(jd_moonrise),
                get_angam_func(jd_moonrise_tmrw),
                get_angam_func(jd_moonrise_tmrw)]
    else:
      # Error!
      raise ValueError('Unkown kaala "%s" input!' % kaala_type)
    return angams

  def calc_nakshatra_tyajyam(self, debug_tyajyam=False):
    self.tyajyam_data = [[] for _x in range(self.duration + 1)]
    if self.nakshatram_data[0] is None:
      self.nakshatram_data[0] = zodiac.get_angam_data(self.jd_sunrise[0], self.jd_sunrise[1],
                                                      zodiac.NAKSHATRAM, ayanamsha_id=self.ayanamsha_id)
    for d in range(1, self.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.jd_start_utc + d - 1)
      jd = self.jd_midnight[d]
      t_start = self.nakshatram_data[d - 1][-1][1]
      if t_start is not None:
        n, t_end = self.nakshatram_data[d][0]
        if t_end is None:
          t_end = self.nakshatram_data[d + 1][0][1]
        tyajyam_start = t_start + (t_end - t_start) / 60 * (temporal.TYAJYAM_SPANS_REL[n - 1] - 1)
        tyajyam_end = t_start + (t_end - t_start) / 60 * (temporal.TYAJYAM_SPANS_REL[n - 1] + 3)
        if tyajyam_start < self.jd_sunrise[d]:
          self.tyajyam_data[d - 1] += [(tyajyam_start, tyajyam_end)]
          if debug_tyajyam:
            logging.debug('![%3d]%04d-%02d-%02d: %s (>>%s), %s–%s' %
                          (d - 1, y, m, dt - 1, names.NAMES['NAKSHATRAM_NAMES']['hk'][n],
                           Hour(24 * (t_end - self.jd_midnight[d - 1])).toString(format='hh:mm*'),
                           Hour(24 * (tyajyam_start - self.jd_midnight[d - 1])).toString(format='hh:mm*'),
                           Hour(24 * (tyajyam_end - self.jd_midnight[d - 1])).toString(format='hh:mm*')))
        else:
          self.tyajyam_data[d] = [(tyajyam_start, tyajyam_end)]
          if debug_tyajyam:
            logging.debug(' [%3d]%04d-%02d-%02d: %s (>>%s), %s–%s' %
                          (d, y, m, dt, names.NAMES['NAKSHATRAM_NAMES']['hk'][n],
                           Hour(24 * (t_end - jd)).toString(format='hh:mm*'),
                           Hour(24 * (tyajyam_start - jd)).toString(format='hh:mm*'),
                           Hour(24 * (tyajyam_end - jd)).toString(format='hh:mm*')))

      if len(self.nakshatram_data[d]) == 2:
        t_start = t_end
        n2, t_end = self.nakshatram_data[d][1]
        tyajyam_start = t_start + (t_end - t_start) / 60 * (temporal.TYAJYAM_SPANS_REL[n2 - 1] - 1)
        tyajyam_end = t_start + (t_end - t_start) / 60 * (temporal.TYAJYAM_SPANS_REL[n2 - 1] + 3)
        self.tyajyam_data[d] += [(tyajyam_start, tyajyam_end)]
        if debug_tyajyam:
          logging.debug(' [%3d]            %s (>>%s), %s–%s' %
                        (d, names.NAMES['NAKSHATRAM_NAMES']['hk'][n2],
                         Hour(24 * (t_end - jd)).toString(format='hh:mm*'),
                         Hour(24 * (tyajyam_start - jd)).toString(format='hh:mm*'),
                         Hour(24 * (tyajyam_end - jd)).toString(format='hh:mm*')))

  def calc_nakshatra_amrita(self, debug_amrita=False):
    self.amrita_data = [[] for _x in range(self.duration + 1)]
    if self.nakshatram_data[0] is None:
      self.nakshatram_data[0] = zodiac.get_angam_data(self.jd_sunrise[0], self.jd_sunrise[1],
                                                      zodiac.NAKSHATRAM, ayanamsha_id=self.ayanamsha_id)
    for d in range(1, self.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.jd_start_utc + d - 1)
      jd = self.jd_midnight[d]
      t_start = self.nakshatram_data[d - 1][-1][1]
      if t_start is not None:
        n, t_end = self.nakshatram_data[d][0]
        if t_end is None:
          t_end = self.nakshatram_data[d + 1][0][1]
        amrita_start = t_start + (t_end - t_start) / 60 * (temporal.AMRITA_SPANS_REL[n - 1] - 1)
        amrita_end = t_start + (t_end - t_start) / 60 * (temporal.AMRITA_SPANS_REL[n - 1] + 3)
        if amrita_start < self.jd_sunrise[d]:
          self.amrita_data[d - 1] += [(amrita_start, amrita_end)]
          if debug_amrita:
            logging.debug('![%3d]%04d-%02d-%02d: %s (>>%s), %s–%s' %
                          (d - 1, y, m, dt - 1, names.NAMES['NAKSHATRAM_NAMES']['hk'][n],
                           Hour(24 * (t_end - self.jd_midnight[d - 1])).toString(format='hh:mm*'),
                           Hour(24 * (amrita_start - self.jd_midnight[d - 1])).toString(format='hh:mm*'),
                           Hour(24 * (amrita_end - self.jd_midnight[d - 1])).toString(format='hh:mm*')))
        else:
          self.amrita_data[d] = [(amrita_start, amrita_end)]
          if debug_amrita:
            logging.debug(' [%3d]%04d-%02d-%02d: %s (>>%s), %s–%s' %
                          (d, y, m, dt, names.NAMES['NAKSHATRAM_NAMES']['hk'][n],
                           Hour(24 * (t_end - jd)).toString(format='hh:mm*'),
                           Hour(24 * (amrita_start - jd)).toString(format='hh:mm*'),
                           Hour(24 * (amrita_end - jd)).toString(format='hh:mm*')))

      if len(self.nakshatram_data[d]) == 2:
        t_start = t_end
        n2, t_end = self.nakshatram_data[d][1]
        amrita_start = t_start + (t_end - t_start) / 60 * (temporal.AMRITA_SPANS_REL[n2 - 1] - 1)
        amrita_end = t_start + (t_end - t_start) / 60 * (temporal.AMRITA_SPANS_REL[n2 - 1] + 3)
        self.amrita_data[d] += [(amrita_start, amrita_end)]
        if debug_amrita:
          logging.debug(' [%3d]            %s (>>%s), %s–%s' %
                        (d, names.NAMES['NAKSHATRAM_NAMES']['hk'][n2],
                         Hour(24 * (t_end - jd)).toString(format='hh:mm*'),
                         Hour(24 * (amrita_start - jd)).toString(format='hh:mm*'),
                         Hour(24 * (amrita_end - jd)).toString(format='hh:mm*')))

  def compute_festivals(self, debug_festivals=False):
    from jyotisha.panchangam.temporal.festival import applier
    applier.MiscFestivalAssigner(panchaanga=self).assign_all(debug_festivals=debug_festivals)
    applier.ecliptic.EclipticFestivalAssigner(panchaanga=self).assign_all(debug_festivals=debug_festivals)
    applier.tithi.TithiFestivalAssigner(panchaanga=self).assign_all(debug_festivals=debug_festivals)
    applier.solar.SolarFestivalAssigner(panchaanga=self).assign_all(debug_festivals=debug_festivals)
    applier.vaara.VaraFestivalAssigner(panchaanga=self).assign_all(debug_festivals=debug_festivals)
    applier.MiscFestivalAssigner(panchaanga=self).cleanup_festivals(debug_festivals=debug_festivals)
    applier.MiscFestivalAssigner(panchaanga=self).assign_relative_festivals()


  def assign_shraaddha_tithi(self, debug_shraaddha_tithi=False):
    def _assign(self, fday, tithi):
      if self.shraaddha_tithi[fday] == [None] or self.shraaddha_tithi[fday] == [tithi]:
        self.shraaddha_tithi[fday] = [tithi]
      else:
        self.shraaddha_tithi[fday].append(tithi)
        if self.shraaddha_tithi[fday - 1].count(tithi) == 1:
          self.shraaddha_tithi[fday - 1].remove(tithi)

    nDays = self.len
    self.shraaddha_tithi = [[None] for _x in range(nDays)]
    for d in range(1, self.duration + 1):
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(self.jd_start_utc + d - 1)

      def f(x):
        return NakshatraDivision(x, ayanamsha_id=self.ayanamsha_id).get_tithi()

      angams = self.get_angams_for_kaalas(d, f, 'aparaahna')
      angam_start = angams[0]
      next_angam = (angam_start % 30) + 1
      nnext_angam = (next_angam % 30) + 1

      # Calc vyaaptis
      t_start_d, t_end_d = temporal.get_interval(self.jd_sunrise[d], self.jd_sunset[d], 3, 5).to_tuple()
      vyapti_1 = t_end_d - t_start_d
      vyapti_2 = 0
      for [tithi, tithi_end] in self.tithi_data[d]:
        if tithi_end is None:
          pass
        elif t_start_d < tithi_end < t_end_d:
          vyapti_1 = tithi_end - t_start_d
          vyapti_2 = t_end_d - tithi_end

      t_start_d1, t_end_d1 = temporal.get_interval(self.jd_sunrise[d + 1], self.jd_sunset[d + 1], 3, 5).to_tuple()
      vyapti_3 = t_end_d1 - t_start_d1
      for [tithi, tithi_end] in self.tithi_data[d + 1]:
        if tithi_end is None:
          pass
        elif t_start_d1 < tithi_end < t_end_d1:
          vyapti_3 = tithi_end - t_start_d1

      # Combinations
      # <a> 1 1 1 1 - d + 1: 1
      # <b> 1 1 2 2 - d: 1
      # <f> 1 1 2 3 - d: 1, d+1: 2
      # <e> 1 1 1 2 - d, or vyApti (just in case next day aparahna is slightly longer): 1
      # <d> 1 1 3 3 - d: 1, 2
      # <h> 1 2 3 3 - d: 2
      # <c> 1 2 2 2 - d + 1: 2
      # <g> 1 2 2 3 - vyApti: 2
      fday = -1
      reason = '?'
      # if angams[1] == angam_start:
      #     logging.debug('Pre-emptively assign %2d to %3d, can be removed tomorrow if need be.' % (angam_start, d))
      #     _assign(self, d, angam_start)
      if angams[3] == angam_start:  # <a>
        # Full aparaahnas on both days, so second day
        fday = d + 1
        s_tithi = angam_start
        reason = '%2d incident on consecutive days; paraviddhA' % s_tithi
      elif (angams[1] == angam_start) and (angams[2] == next_angam):  # <b>/<f>
        fday = d
        s_tithi = angams[0]
        reason = '%2d not incident on %3d' % (s_tithi, d + 1)
        if angams[3] == nnext_angam:  # <f>
          if debug_shraaddha_tithi:
            logging.debug('%03d [%4d-%02d-%02d]: %s' % (d, y, m, dt,
                                                        'Need to assign %2d to %3d as it is present only at start of aparAhna tomorrow!)' % (
                                                          next_angam, d + 1)))
          _assign(self, d + 1, next_angam)
      elif angams[2] == angam_start:  # <e>
        if vyapti_1 > vyapti_3:
          # Most likely
          fday = d
          s_tithi = angams[2]
          reason = '%2d has more vyApti on day %3d (%f ghatikAs; full?) compared to day %3d (%f ghatikAs)' % (
            s_tithi, d, vyapti_1 * 60, d + 1, vyapti_3 * 60)
        else:
          fday = d + 1
          s_tithi = angams[2]
          reason = '%2d has more vyApti on day %3d (%f ghatikAs) compared to day %3d (%f ghatikAs) --- unusual!' % (
            s_tithi, d + 1, vyapti_3 * 60, d, vyapti_1 * 60)
      elif angams[2] == nnext_angam:  # <d>/<h>
        if angams[1] == next_angam:  # <h>
          fday = d
          s_tithi = angams[1]
          reason = '%2d has some vyApti on day %3d; not incident on day %3d at all' % (s_tithi, d, d + 1)
        else:  # <d>
          s_tithi = angam_start
          fday = d
          reason = '%2d is incident fully at aparAhna today (%3d), and not incident tomorrow (%3d)!' % (
            s_tithi, d, d + 1)
          # Need to check vyApti of next_angam in sAyaMkAla: if it's nearly entire sAyaMkAla ie 5-59-30 or more!
          if debug_shraaddha_tithi:
            logging.debug('%03d [%4d-%02d-%02d]: %s' % (d, y, m, dt,
                                                        '%2d not incident at aparAhna on either day (%3d/%3d); picking second day %3d!' % (
                                                          next_angam, d, d + 1, d + 1)))
          _assign(self, d + 1, next_angam)
          # logging.debug(reason)
      elif angams[1] == angams[2] == angams[3] == next_angam:  # <c>
        s_tithi = next_angam
        fday = d + 1
        reason = '%2d has more vyApti on %3d (full) compared to %3d (part)' % (s_tithi, d + 1, d)
      elif angams[1] == angams[2] == next_angam:  # <g>
        s_tithi = angams[2]
        if vyapti_2 > vyapti_3:
          # Most likely
          fday = d
          reason = '%2d has more vyApti on day %3d (%f ghatikAs) compared to day %3d (%f ghatikAs)' % (
            s_tithi, d, vyapti_2 * 60, d + 1, vyapti_3 * 60)
        else:
          fday = d + 1
          reason = '%2d has more vyApti on day %3d (%f ghatikAs) compared to day %3d (%f ghatikAs)' % (
            s_tithi, d + 1, vyapti_3 * 60, d, vyapti_2 * 60)  # Examine for greater vyApti
      else:
        logging.error('Should not reach here ever! %s' % str(angams))
        reason = '?'
      if debug_shraaddha_tithi:
        logging.debug(
          '%03d [%4d-%02d-%02d]: Assigning tithi %2d to %3d (%s).' % (d, y, m, dt, s_tithi, fday, reason))
      _assign(self, fday, s_tithi)

    if debug_shraaddha_tithi:
      logging.debug(self.shraaddha_tithi)

    self.lunar_tithi_days = {}
    for z in set(self.lunar_month):
      self.lunar_tithi_days[z] = {}
    for d in range(1, self.duration + 1):
      for t in self.shraaddha_tithi[d]:
        self.lunar_tithi_days[self.lunar_month[d]][t] = d

    # Following this primary assignment, we must now "clean" for Sankranti, and repetitions
    # If there are two tithis, take second. However, if the second has sankrAnti dushtam, take
    # first. If both have sankrAnti dushtam, take second.
    self.tithi_days = [{z: [] for z in range(1, 31)} for _x in range(13)]
    for d in range(1, self.duration + 1):
      if self.shraaddha_tithi[d] != [None]:
        if self.solar_month_end_time[d] is not None:
          if debug_shraaddha_tithi:
            logging.debug((d, self.solar_month_end_time[d]))
          aparaahna_start, aparaahna_end = temporal.get_interval(self.jd_sunrise[d], self.jd_sunset[d], 3, 5).to_tuple()
          m1 = self.solar_month[d - 1]  # Previous month
          m2 = self.solar_month[d]  # Current month
          if aparaahna_start < self.solar_month_end_time[d] < aparaahna_end:
            if debug_shraaddha_tithi:
              logging.debug('Sankranti in aparaahna! Assigning to both months!')
            assert self.solar_month_day[d] == 1
            for t in self.shraaddha_tithi[d]:
              # Assigning to both months --- should get eliminated because of a second occurrence
              self.tithi_days[m1][t].extend([d, '*'])
              self.tithi_days[m2][t].extend([d, '*'])
          if self.solar_month_end_time[d] < aparaahna_start:
            if debug_shraaddha_tithi:
              logging.debug('Sankranti before aparaahna!')
            assert self.solar_month_day[d] == 1
            for t in self.shraaddha_tithi[d]:
              self.tithi_days[m2][t].extend([d, '*'])
          if aparaahna_end < self.solar_month_end_time[d]:
            if debug_shraaddha_tithi:
              logging.debug('Sankranti after aparaahna!')
            # Depending on whether sankranti is before or after sunset, m2 may or may not be equal to m1
            # In any case, we wish to assign this tithi to the previous month, where it really occurs.
            for t in self.shraaddha_tithi[d]:
              self.tithi_days[m1][t].extend([d, '*'])
        else:
          for t in self.shraaddha_tithi[d]:
            self.tithi_days[self.solar_month[d]][t].append(d)

    # We have now assigned all tithis. Now, remove duplicates based on the above-mentioned rules.
    # TODO: This is not the best way to clean. Need to examine one month at a time.
    for m in range(1, 13):
      for t in range(1, 31):
        if len(self.tithi_days[m][t]) == 1:
          continue
        elif len(self.tithi_days[m][t]) == 2:
          if self.tithi_days[m][t][1] == '*':
            # Only one tithi available!
            if debug_shraaddha_tithi:
              logging.debug('Only one %2d tithi in month %2d, on day %3d, despite sankrAnti dushtam!' % (
                t, m, self.tithi_days[m][t][0]))
            del self.tithi_days[m][t][1]
            self.tithi_days[m][t][0] = '%d::%d' % (self.tithi_days[m][t][0], m)
            if debug_shraaddha_tithi:
              logging.debug('Note %s' % str(self.tithi_days[m][t]))
          else:
            self.shraaddha_tithi[self.tithi_days[m][t][0]] = [0]  # Shunya
            if debug_shraaddha_tithi:
              logging.debug('Removed %d' % self.tithi_days[m][t][0])
            del self.tithi_days[m][t][0]
            if debug_shraaddha_tithi:
              logging.debug('Two %2d tithis in month %2d: retaining second on %2d!' % (
                t, m, self.tithi_days[m][t][0]))
        elif len(self.tithi_days[m][t]) == 3:
          if debug_shraaddha_tithi:
            logging.debug('Two %2d tithis in month %2d: %s' % (t, m, str(self.tithi_days[m][t])))
          if self.tithi_days[m][t][1] == '*':
            self.shraaddha_tithi[self.tithi_days[m][t][0]] = [0]  # Shunya
            if debug_shraaddha_tithi:
              logging.debug('Removed %d' % self.tithi_days[m][t][0])
            del self.tithi_days[m][t][:2]
          elif self.tithi_days[m][t][2] == '*':
            self.shraaddha_tithi[self.tithi_days[m][t][1]] = [0]  # Shunya
            if debug_shraaddha_tithi:
              logging.debug('Removed %d' % self.tithi_days[m][t][1])
            del self.tithi_days[m][t][1:]
            if debug_shraaddha_tithi:
              logging.debug('     Retaining non-dushta: %s' % (str(self.tithi_days[m][t])))
        elif len(self.tithi_days[m][t]) == 4:
          if debug_shraaddha_tithi:
            logging.debug('Two dushta %2d tithis in month %2d: %s' % (t, m, str(self.tithi_days[m][t])))
          self.shraaddha_tithi[self.tithi_days[m][t][0]] = [0]  # Shunya
          if debug_shraaddha_tithi:
            logging.debug('Removed %d' % self.tithi_days[m][t][0])
          self.tithi_days[m][t][3] = str(m)
          del self.tithi_days[m][t][:2]
          if debug_shraaddha_tithi:
            logging.debug('                    Retaining: %s' % (str(self.tithi_days[m][t])))
          self.tithi_days[m][t][0] = '%d::%d' % (self.tithi_days[m][t][0], m)
          if debug_shraaddha_tithi:
            logging.debug('Note %s' % str(self.tithi_days[m][t]))
        elif len(self.tithi_days[m][t]) == 0:
          logging.warning(
            'Rare issue. No tithi %d in this solar month (%d). Therefore use lunar tithi.' % (t, m))
          # सौरमासे तिथ्यलाभे चान्द्रमानेन कारयेत्
          # self.tithi_days[m][t] = self.lunar_tithi_days[m][t]
        else:
          logging.error('Something weird. len(self.tithi_days[m][t]) is not in 1:4!! : %s (m=%d, t=%d)',
                        str(self.tithi_days[m][t]), m, t)

      if debug_shraaddha_tithi:
        logging.debug(self.tithi_days)

  def write_debug_log(self):
    log_file = open('cal-%4d-%s-log.txt' % (self.year, self.city.name), 'w')
    for d in range(1, self.len - 1):
      jd = self.jd_start_utc - 1 + d
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(jd)
      longitude_sun_sunset = Graha(Graha.SUN).get_longitude(self.jd_sunset[d]) - zodiac.Ayanamsha(
        self.ayanamsha_id).get_offset(self.jd_sunset[d])
      log_data = '%02d-%02d-%4d\t[%3d]\tsun_rashi=%8.3f\ttithi=%8.3f\tsolar_month\
        =%2d\tlunar_month=%4.1f\n' % (dt, m, y, d, (longitude_sun_sunset % 360) / 30.0,
                                      NakshatraDivision(self.jd_sunrise[d],
                                                        ayanamsha_id=self.ayanamsha_id).get_anga_float(zodiac.TITHI),
                                      self.solar_month[d], self.lunar_month[d])
      log_file.write(log_data)

  def update_festival_details(self):
    """

    Festival data may be updated more frequently and a precomputed panchangam may go out of sync. Hence we keep this method separate.
    :return:
    """
    self.reset_festivals()
    self.assign_shraaddha_tithi()
    self.compute_festivals()

  def reset_festivals(self, compute_lagnams=False):
    self.fest_days = {}
    # Pushkaram starting on 31 Jan might not get over till 12 days later
    self.festivals = [[] for _x in range(self.len + 15)]


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])


# logging.debug(common.json_class_index)


def get_panchangam(city, start_date, end_date, script, fmt='hh:mm', compute_lagnams=False,
                   precomputed_json_dir="~/Documents", ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180):
  fname_det = os.path.expanduser(
    '%s/%s-%s-%s-detailed.json' % (precomputed_json_dir, city.name, start_date, end_date))
  fname = os.path.expanduser('%s/%s-%s-%s.json' % (precomputed_json_dir, city.name, start_date, end_date))

  if os.path.isfile(fname) and not compute_lagnams:
    sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    p = JsonObject.read_from_file(filename=fname)
    p.script = script  # Need to force script, in case saved file script is different
    return p
  elif os.path.isfile(fname_det):
    # Load pickle, do not compute!
    sys.stderr.write('Loaded pre-computed panchangam from %s.\n' % fname)
    p = JsonObject.read_from_file(filename=fname_det)
    p.script = script  # Need to force script, in case saved file script is different
    return p
  else:
    sys.stderr.write('No precomputed data available. Computing panchangam...\n')
    panchangam = Panchangam(city=city, start_date=start_date, end_date=end_date, script=script, fmt=fmt,
                            compute_lagnams=compute_lagnams, ayanamsha_id=ayanamsha_id)
    sys.stderr.write('Writing computed panchangam to %s...\n' % fname)

    try:
      if compute_lagnams:
        panchangam.dump_to_file(filename=fname_det)
      else:
        panchangam.dump_to_file(filename=fname)
    except EnvironmentError:
      logging.warning("Not able to save.")
      logging.error(traceback.format_exc())
    # Save without festival details
    # Festival data may be updated more frequently and a precomputed panchangam may go out of sync. Hence we keep this method separate.
    panchangam.update_festival_details()
    return panchangam


if __name__ == '__main__':
  city = spatio_temporal.City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchangam = Panchangam(city=city, start_date='2019-04-14', end_date='2020-04-13', script=sanscript.DEVANAGARI,
                          ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, fmt='hh:mm', compute_lagnams=False)
