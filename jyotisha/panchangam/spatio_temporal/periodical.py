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
from jyotisha.panchangam.temporal import interval
from jyotisha import names
from jyotisha.panchangam import temporal, spatio_temporal
from jyotisha.panchangam.spatio_temporal import CODE_ROOT, daily
from jyotisha.panchangam.temporal import zodiac
from jyotisha.panchangam.temporal.body import Graha
from jyotisha.panchangam.temporal.festival import read_old_festival_rules_dict
from jyotisha.panchangam.temporal.hour import Hour
from jyotisha.panchangam.temporal.month import SiderialSolarBasedAssigner, LunarMonthAssigner
from jyotisha.panchangam.temporal.tithi import TithiAssigner
from jyotisha.panchangam.temporal.zodiac import NakshatraDivision, AngaSpan
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject


class Panchangam(common.JsonObject):
  """This class enables the construction of a panchangam for arbitrary periods, with festivals.
    """

  def __init__(self, city, start_date, end_date, lunar_month_assigner_type=LunarMonthAssigner.SIDERIAL_SOLAR_BASED, script=sanscript.DEVANAGARI, fmt='hh:mm',
               ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180,
               compute_lagnas=False):
    """Constructor for the panchangam.
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

    self.compute_angas(compute_lagnas=compute_lagnas)
    lunar_month_assigner = LunarMonthAssigner.get_assigner(assigner_id=lunar_month_assigner_type, panchaanga=self)
    lunar_month_assigner.assign()

  def compute_angas(self, compute_lagnas=True):
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

    if compute_lagnas:
      self.lagna_data = [None] * nDays

    self.weekday = [None] * nDays
    daily_panchaangas: List[daily.DailyPanchanga] = [None] * nDays

    # Computing solar month details for Dec 31
    # rather than Jan 1, since we have an always increment
    # solar_month_day at the start of the loop across every day in
    # year
    [prev_day_yy, prev_day_mm, prev_day_dd] = temporal.jd_to_utc_gregorian(self.jd_start_utc - 1)[:3]
    daily_panchaanga_start = daily.DailyPanchanga(city=self.city, year=prev_day_yy, month=prev_day_mm,
                                                  day=prev_day_dd, ayanamsha_id=self.ayanamsha_id)
    daily_panchaanga_start.compute_solar_day()
    self.solar_month[1] = daily_panchaanga_start.solar_month
    solar_month_day = daily_panchaanga_start.solar_month_day

    solar_month_today_sunset = NakshatraDivision(daily_panchaanga_start.jd_sunset,
                                                 ayanamsha_id=self.ayanamsha_id).get_anga(
      zodiac.AngaTypes.SOLAR_MONTH)
    solar_month_tmrw_sunrise = NakshatraDivision(daily_panchaanga_start.jd_sunrise + 1,
                                                 ayanamsha_id=self.ayanamsha_id).get_anga(
      zodiac.AngaTypes.SOLAR_MONTH)
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
                                                      previous_day_panchaanga=daily_panchaangas[d])
      daily_panchaangas[d + 1].compute_sun_moon_transitions(previous_day_panchaanga=daily_panchaangas[d])
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
            self.jd_sunrise[d], self.jd_sunrise[d + 1], zodiac.AngaTypes.SOLAR_MONTH, ayanamsha_id=self.ayanamsha_id)[
            0]
      elif solar_month_sunrise[d] != self.solar_month[d]:
        # sankrAnti!
        # sun moves into next rAshi before sunset
        solar_month_day = 1
        [_m, solar_month_end_jd] = zodiac.get_angam_data(
          self.jd_sunrise[d], self.jd_sunrise[d + 1], zodiac.AngaTypes.SOLAR_MONTH, ayanamsha_id=self.ayanamsha_id)[0]
      else:
        solar_month_day = solar_month_day + 1
        solar_month_end_jd = None

      self.solar_month_end_time[d] = solar_month_end_jd

      self.solar_month_day[d] = solar_month_day

      # Compute all the anga datas
      self.tithi_data[d] = daily_panchaangas[d].tithi_data
      self.tithi_sunrise[d] = daily_panchaangas[d].tithi_at_sunrise
      self.nakshatram_data[d] = daily_panchaangas[d].nakshatra_data
      self.nakshatram_sunrise[d] = daily_panchaangas[d].nakshatra_at_sunrise
      self.yoga_data[d] = daily_panchaangas[d].yoga_data
      self.yoga_sunrise[d] = daily_panchaangas[d].yoga_at_sunrise
      self.karanam_data[d] = daily_panchaangas[d].karana_data
      self.rashi_data[d] = daily_panchaangas[d].raashi_data
      self.kaalas[d] = daily_panchaangas[d].get_kaalas()
      if compute_lagnas:
        self.lagna_data[d] = daily_panchaangas[d].get_lagna_data()

  def get_angas_for_interval_boundaries(self, d, get_anga_func, interval_type):
    jd_sunrise = self.jd_sunrise[d]
    jd_sunrise_tmrw = self.jd_sunrise[d + 1]
    jd_sunrise_datmrw = self.jd_sunrise[d + 2]
    jd_sunset = self.jd_sunset[d]
    jd_sunset_tmrw = self.jd_sunset[d + 1]
    jd_moonrise = self.jd_moonrise[d]
    jd_moonrise_tmrw = self.jd_moonrise[d + 1]
    if interval_type == 'sunrise':
      angas = [get_anga_func(jd_sunrise),
                get_anga_func(jd_sunrise),
                get_anga_func(jd_sunrise_tmrw),
                get_anga_func(jd_sunrise_tmrw)]
    elif interval_type == 'sunset':
      angas = [get_anga_func(jd_sunset),
                get_anga_func(jd_sunset),
                get_anga_func(jd_sunset_tmrw),
                get_anga_func(jd_sunset_tmrw)]
    elif interval_type == 'praatah':
      angas = [get_anga_func(jd_sunrise),  # praatah1 start
                # praatah1 end
                get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (1.0 / 5.0)),
                get_anga_func(jd_sunrise_tmrw),  # praatah2 start
                # praatah2 end
                get_anga_func(jd_sunrise_tmrw + \
                              (jd_sunset_tmrw - jd_sunrise_tmrw) * (1.0 / 5.0))]
    elif interval_type == 'sangava':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (1.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (2.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (1.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (2.0 / 5.0))]
    elif interval_type == 'madhyaahna':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (2.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (3.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (2.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw + (jd_sunset_tmrw -
                                         jd_sunrise_tmrw) * (3.0 / 5.0))]
    elif interval_type == 'aparaahna':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (3.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (4.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (3.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (4.0 / 5.0))]
    elif interval_type == 'saayaahna':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (4.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (5.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (4.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (5.0 / 5.0))]
    elif interval_type == 'madhyaraatri':
      angas = [
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (2.0 / 5.0)),
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (3.0 / 5.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (2.0 / 5.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (3.0 / 5.0))]
    elif interval_type == 'pradosha':
      # pradOSo.astamayAdUrdhvaM ghaTikAdvayamiShyatE (tithyAdi tattvam, Vrat Parichay p. 25 Gita Press)
      angas = [get_anga_func(jd_sunset),
                get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (1.0 / 15.0)),
                get_anga_func(jd_sunset_tmrw),
                get_anga_func(jd_sunset_tmrw +
                              (jd_sunrise_datmrw - jd_sunset_tmrw) * (1.0 / 15.0))]
    elif interval_type == 'nishita':
      angas = [
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (7.0 / 15.0)),
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (8.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (7.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (8.0 / 15.0))]
    elif interval_type == 'dinamaana':
      angas = [
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (0.0 / 5.0)),
        get_anga_func(jd_sunrise + (jd_sunset - jd_sunrise) * (5.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw +
                      (jd_sunset_tmrw - jd_sunrise_tmrw) * (0.0 / 5.0)),
        get_anga_func(jd_sunrise_tmrw + (jd_sunset_tmrw -
                                         jd_sunrise_tmrw) * (5.0 / 5.0))]
    elif interval_type == 'raatrimaana':
      angas = [
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (0.0 / 15.0)),
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (15.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (0.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (15.0 / 15.0))]
    elif interval_type == 'arunodaya':  
      # deliberately not simplifying expressions involving 15/15
      angas = [
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (13.0 / 15.0)),
        get_anga_func(jd_sunset + (jd_sunrise_tmrw - jd_sunset) * (15.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (13.0 / 15.0)),
        get_anga_func(jd_sunset_tmrw +
                      (jd_sunrise_datmrw - jd_sunset_tmrw) * (15.0 / 15.0))]
    elif interval_type == 'moonrise':
      angas = [get_anga_func(jd_moonrise),
                get_anga_func(jd_moonrise),
                get_anga_func(jd_moonrise_tmrw),
                get_anga_func(jd_moonrise_tmrw)]
    else:
      # Error!
      raise ValueError('Unkown kaala "%s" input!' % interval_type)
    return angas


  def write_debug_log(self):
    log_file = open('cal-%4d-%s-log.txt' % (self.year, self.city.name), 'w')
    for d in range(1, self.len - 1):
      jd = self.jd_start_utc - 1 + d
      [y, m, dt, t] = temporal.jd_to_utc_gregorian(jd)
      longitude_sun_sunset = Graha.singleton(Graha.SUN).get_longitude(self.jd_sunset[d]) - zodiac.Ayanamsha.singleton(
        self.ayanamsha_id).get_offset(self.jd_sunset[d])
      log_data = '%02d-%02d-%4d\t[%3d]\tsun_rashi=%8.3f\ttithi=%8.3f\tsolar_month\
        =%2d\tlunar_month=%4.1f\n' % (dt, m, y, d, (longitude_sun_sunset % 360) / 30.0,
                                      NakshatraDivision(self.jd_sunrise[d],
                                                        ayanamsha_id=self.ayanamsha_id).get_anga_float(zodiac.AngaTypes.TITHI),
                                      self.solar_month[d], self.lunar_month[d])
      log_file.write(log_data)

  def update_festival_details(self,debug=False):
    """

    Festival data may be updated more frequently and a precomputed panchangam may go out of sync. Hence we keep this method separate.
    :return:
    """
    self._reset_festivals()
    TithiAssigner(self).assign_shraaddha_tithi()
    from jyotisha.panchangam.temporal.festival import applier
    applier.MiscFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    applier.ecliptic.EclipticFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    applier.tithi.TithiFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    applier.solar.SolarFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    applier.vaara.VaraFestivalAssigner(panchaanga=self).assign_all(debug=debug)
    applier.MiscFestivalAssigner(panchaanga=self).cleanup_festivals(debug=debug)
    applier.MiscFestivalAssigner(panchaanga=self).assign_relative_festivals()

  def _reset_festivals(self, compute_lagnams=False):
    self.fest_days = {}
    # Pushkaram starting on 31 Jan might not get over till 12 days later
    self.festivals = [[] for _x in range(self.len + 15)]


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])


# logging.debug(common.json_class_index)


def get_panchaanga(city, start_date, end_date, script, fmt='hh:mm', compute_lagnams=False,
                   precomputed_json_dir="~/Documents", ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180):
  fname_det = os.path.expanduser(
    '%s/%s-%s-%s-detailed.json' % (precomputed_json_dir, city.name, start_date, end_date))
  fname = os.path.expanduser('%s/%s-%s-%s.json' % (precomputed_json_dir, city.name, start_date, end_date))

  if os.path.isfile(fname) and not compute_lagnams:
    sys.stderr.write('Loaded pre-computed panchaanga from %s.\n' % fname)
    p = JsonObject.read_from_file(filename=fname)
    p.script = script  # Need to force script, in case saved file script is different
    return p
  elif os.path.isfile(fname_det):
    # Load pickle, do not compute!
    sys.stderr.write('Loaded pre-computed panchaanga from %s.\n' % fname)
    p = JsonObject.read_from_file(filename=fname_det)
    p.script = script  # Need to force script, in case saved file script is different
    return p
  else:
    sys.stderr.write('No precomputed data available. Computing panchaanga...\n')
    panchaanga = Panchangam(city=city, start_date=start_date, end_date=end_date, script=script, fmt=fmt,
                            compute_lagnas=compute_lagnams, ayanamsha_id=ayanamsha_id)
    sys.stderr.write('Writing computed panchaanga to %s...\n' % fname)

    try:
      if compute_lagnams:
        panchaanga.dump_to_file(filename=fname_det)
      else:
        panchaanga.dump_to_file(filename=fname)
    except EnvironmentError:
      logging.warning("Not able to save.")
      logging.error(traceback.format_exc())
    # Save without festival details
    # Festival data may be updated more frequently and a precomputed panchaanga may go out of sync. Hence we keep this method separate.
    panchaanga.update_festival_details()
    return panchaanga


if __name__ == '__main__':
  city = spatio_temporal.City('Chennai', "13:05:24", "80:16:12", "Asia/Calcutta")
  panchangam = Panchangam(city=city, start_date='2019-04-14', end_date='2020-04-13', script=sanscript.DEVANAGARI,
                          ayanamsha_id=zodiac.Ayanamsha.CHITRA_AT_180, fmt='hh:mm', compute_lagnas=False)
