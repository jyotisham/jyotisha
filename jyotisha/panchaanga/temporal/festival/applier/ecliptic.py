import sys
from datetime import datetime
from math import floor

from pytz import timezone as tz

from jyotisha import names
from jyotisha.panchaanga.temporal import interval
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.time import Hour, Date
from sanskrit_data.schema import common


class EclipticFestivalAssigner(FestivalAssigner):
  def assign_all(self, debug=False):
    self.computeTransits()
    self.compute_solar_eclipses()
    self.compute_lunar_eclipses()
    # self.assign_ayanam()

  def assign_ayanam(self):
    last_d_assigned = 0
    for d in range(1, self.panchaanga.duration + 1):

      [y, m, dt, t] = time.jd_to_utc_gregorian(self.panchaanga.jd_start + d - 1).to_date_fractional_hour_tuple()

      # checking @ 6am local - can we do any better?
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # compute offset from UTC in hours
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0

      # TROPICAL AYANAMS
      if self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.day == 1:
        transits = \
          Graha.singleton(Graha.SUN).get_next_raashi_transit(jd_start=self.panchaanga.daily_panchaangas[d].jd_sunrise,
                                                   jd_end=self.panchaanga.daily_panchaangas[d].jd_sunrise + 15,
                                                   ayanaamsha_id=self.ayanaamsha_id)
        ayana_jd_start = transits[0].jd
        [_y, _m, _d, _t] = time.jd_to_utc_gregorian(ayana_jd_start + (tz_off / 24.0)).to_date_fractional_hour_tuple()
        # Reduce fday by 1 if ayana time precedes sunrise and change increment _t by 24
        fday_nirayana = int(
          time.utc_gregorian_to_jd(Date(_y, _m, _d)) - self.panchaanga.jd_start + 1)
        if fday_nirayana > self.panchaanga.duration:
          continue
        if ayana_jd_start < self.panchaanga.daily_panchaangas[fday_nirayana].jd_sunrise:
          fday_nirayana -= 1
          _t += 24
        ayana_time = Hour(_t).toString()

        self.panchaanga.daily_panchaangas[fday_nirayana].festivals.append(FestivalInstance(name='%s\\textsf{%s}{\\RIGHTarrow}\\textsf{%s}' % (
          names.NAMES['RTU_MASA_NAMES']["hk"][self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month], '', ayana_time)))
        self.panchaanga.daily_panchaangas[fday_nirayana].tropical_date.month_end_time = ayana_jd_start
        for i in range(last_d_assigned + 1, fday_nirayana + 1):
          self.panchaanga.daily_panchaangas[i].tropical_date.month = self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month
        last_d_assigned = fday_nirayana
        if self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month == 3:
          if self.panchaanga.daily_panchaangas[fday_nirayana].jd_sunset < ayana_jd_start < self.panchaanga.daily_panchaangas[fday_nirayana + 1].jd_sunset:
            self.panchaanga.daily_panchaangas[fday_nirayana].append('dakSiNAyana-puNyakAlaH')
          else:
            self.panchaanga.daily_panchaangas[fday_nirayana - 1].append('dakSiNAyana-puNyakAlaH')
        if self.panchaanga.daily_panchaangas[d].solar_sidereal_date_sunset.month == 9:
          if self.panchaanga.daily_panchaangas[fday_nirayana].jd_sunset < ayana_jd_start < self.panchaanga.daily_panchaangas[fday_nirayana + 1].jd_sunset:
            self.panchaanga.daily_panchaangas[fday_nirayana + 1].append('uttarAyaNa-puNyakAlaH/mitrOtsavaH')
          else:
            self.panchaanga.daily_panchaangas[fday_nirayana].append('uttarAyaNa-puNyakAlaH/mitrOtsavaH')
    for i in range(last_d_assigned + 1, self.panchaanga.duration + 1):
      self.panchaanga.daily_panchaangas[i].tropical_date.month = (self.panchaanga.daily_panchaangas[last_d_assigned].solar_sidereal_date_sunset.month % 12) + 1

  def compute_solar_eclipses(self):
    jd = self.panchaanga.jd_start
    while 1:
      next_eclipse_sol = self.panchaanga.city.get_solar_eclipse_time(jd_start=jd)
      [y, m, dt, t] = time.jd_to_utc_gregorian(next_eclipse_sol[1][0]).to_date_fractional_hour_tuple()
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # checking @ 6am local - can we do any better?
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0
      # compute offset from UTC
      jd = next_eclipse_sol[1][0] + (tz_off / 24.0)
      jd_eclipse_solar_start = next_eclipse_sol[1][1] + (tz_off / 24.0)
      jd_eclipse_solar_end = next_eclipse_sol[1][4] + (tz_off / 24.0)
      # -1 is to not miss an eclipse that occurs after sunset on 31-Dec!
      if jd_eclipse_solar_start > self.panchaanga.jd_end + 1:
        break
      else:
        fday = int(floor(jd) - floor(self.panchaanga.jd_start) + 1)
        if (jd < (self.panchaanga.daily_panchaangas[fday].jd_sunrise + tz_off / 24.0)):
          fday -= 1
        eclipse_solar_start = time.jd_to_utc_gregorian(jd_eclipse_solar_start).to_date_fractional_hour_tuple()[3]
        eclipse_solar_end = time.jd_to_utc_gregorian(jd_eclipse_solar_end).to_date_fractional_hour_tuple()[3]
        if (jd_eclipse_solar_start - (tz_off / 24.0)) == 0.0 or \
            (jd_eclipse_solar_end - (tz_off / 24.0)) == 0.0:
          # Move towards the next eclipse... at least the next new
          # moon (>=25 days away)
          jd += MIN_DAYS_NEXT_ECLIPSE
          continue
        if eclipse_solar_end < eclipse_solar_start:
          eclipse_solar_end += 24
        sunrise_eclipse_day = time.jd_to_utc_gregorian(self.panchaanga.daily_panchaangas[fday].jd_sunrise + (tz_off / 24.0)).to_date_fractional_hour_tuple()[3]
        sunset_eclipse_day = time.jd_to_utc_gregorian(self.panchaanga.daily_panchaangas[fday].jd_sunset + (tz_off / 24.0)).to_date_fractional_hour_tuple()[3]
        if eclipse_solar_start < sunrise_eclipse_day:
          eclipse_solar_start = sunrise_eclipse_day
        if eclipse_solar_end > sunset_eclipse_day:
          eclipse_solar_end = sunset_eclipse_day
        solar_eclipse_str = 'sUrya-grahaNam' + \
                            '~\\textsf{' + Hour(eclipse_solar_start).toString() + \
                            '}{\\RIGHTarrow}\\textsf{' + Hour(eclipse_solar_end).toString() + '}'
        if self.panchaanga.daily_panchaangas[fday].date.get_weekday() == 0:
          solar_eclipse_str = '★cUDAmaNi-' + solar_eclipse_str
        self.panchaanga.daily_panchaangas[fday]. festivals.append(FestivalInstance(name=solar_eclipse_str))
      jd = jd + MIN_DAYS_NEXT_ECLIPSE

  def compute_lunar_eclipses(self):
    # Set location
    jd = self.panchaanga.jd_start
    while 1:
      next_eclipse_lun = self.panchaanga.city.get_lunar_eclipse_time(jd)
      [y, m, dt, t] = time.jd_to_utc_gregorian(next_eclipse_lun[1][0]).to_date_fractional_hour_tuple()
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # checking @ 6am local - can we do any better? This is crucial,
      # since DST changes before 6 am
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0
      # compute offset from UTC
      jd = next_eclipse_lun[1][0] + (tz_off / 24.0)
      jd_eclipse_lunar_start = next_eclipse_lun[1][2] + (tz_off / 24.0)
      jd_eclipse_lunar_end = next_eclipse_lun[1][3] + (tz_off / 24.0)
      # -1 is to not miss an eclipse that occurs after sunset on 31-Dec!
      if jd_eclipse_lunar_start > self.panchaanga.jd_end:
        break
      else:
        eclipse_lunar_start = time.jd_to_utc_gregorian(jd_eclipse_lunar_start).to_date_fractional_hour_tuple()[3]
        eclipse_lunar_end = time.jd_to_utc_gregorian(jd_eclipse_lunar_end).to_date_fractional_hour_tuple()[3]
        if (jd_eclipse_lunar_start - (tz_off / 24.0)) == 0.0 or \
            (jd_eclipse_lunar_end - (tz_off / 24.0)) == 0.0:
          # Move towards the next eclipse... at least the next full
          # moon (>=25 days away)
          jd += MIN_DAYS_NEXT_ECLIPSE
          continue
        fday = int(floor(jd_eclipse_lunar_start) - floor(self.panchaanga.jd_start) + 1)
        # print '%%', jd, fday, self.panchaanga.daily_panchaangas[fday].jd_sunrise,
        # self.panchaanga.daily_panchaangas[fday-1].jd_sunrise
        if (jd < (self.panchaanga.daily_panchaangas[fday].jd_sunrise + tz_off / 24.0)):
          fday -= 1
        if eclipse_lunar_start < time.jd_to_utc_gregorian(self.panchaanga.daily_panchaangas[fday + 1].jd_sunrise + tz_off / 24.0).to_date_fractional_hour_tuple()[3]:
          eclipse_lunar_start += 24
        # print '%%', jd, fday, self.panchaanga.daily_panchaangas[fday].jd_sunrise,
        # self.panchaanga.daily_panchaangas[fday-1].jd_sunrise, eclipse_lunar_start,
        # eclipse_lunar_end
        jd_moonrise_eclipse_day = self.panchaanga.city.get_rising_time(julian_day_start=self.panchaanga.daily_panchaangas[fday].jd_sunrise,
                                                            body=Graha.MOON) + (tz_off / 24.0)

        jd_moonset_eclipse_day = self.panchaanga.city.get_rising_time(julian_day_start=jd_moonrise_eclipse_day,
                                                           body=Graha.MOON) + (tz_off / 24.0)

        if eclipse_lunar_end < eclipse_lunar_start:
          eclipse_lunar_end += 24

        if jd_eclipse_lunar_end < jd_moonrise_eclipse_day or \
            jd_eclipse_lunar_start > jd_moonset_eclipse_day:
          # Move towards the next eclipse... at least the next full
          # moon (>=25 days away)
          jd += MIN_DAYS_NEXT_ECLIPSE
          continue

        moonrise_eclipse_day = time.jd_to_utc_gregorian(jd_moonrise_eclipse_day).to_date_fractional_hour_tuple()[3]
        moonset_eclipse_day = time.jd_to_utc_gregorian(jd_moonset_eclipse_day).to_date_fractional_hour_tuple()[3]

        if jd_eclipse_lunar_start < jd_moonrise_eclipse_day:
          eclipse_lunar_start = moonrise_eclipse_day
        if jd_eclipse_lunar_end > jd_moonset_eclipse_day:
          eclipse_lunar_end = moonset_eclipse_day

        if Graha.singleton(Graha.MOON).get_longitude(jd_eclipse_lunar_end) < Graha.singleton(Graha.SUN).get_longitude(
            jd_eclipse_lunar_end):
          grasta = 'rAhugrasta'
        else:
          grasta = 'kEtugrasta'

        lunar_eclipse_str = 'candra-grahaNam~(' + grasta + ')' + \
                            '~\\textsf{' + Hour(eclipse_lunar_start).toString() + \
                            '}{\\RIGHTarrow}\\textsf{' + Hour(eclipse_lunar_end).toString() + '}'
        if self.panchaanga.daily_panchaangas[fday].date.get_weekday() == 1:
          lunar_eclipse_str = '★cUDAmaNi-' + lunar_eclipse_str

        self.panchaanga.daily_panchaangas[fday].festivals.append(FestivalInstance(name=lunar_eclipse_str))
      jd += MIN_DAYS_NEXT_ECLIPSE

  def computeTransits(self):
    jd_end = self.panchaanga.jd_start + self.panchaanga.duration
    check_window = 400  # Max t between two Jupiter transits is ~396 (checked across 180y)
    # Let's check for transitions in a relatively large window
    # to finalise what is the FINAL transition post retrograde movements
    transits = Graha.singleton(Graha.JUPITER).get_next_raashi_transit(self.panchaanga.jd_start, jd_end + check_window,
                                                                      ayanaamsha_id=self.ayanaamsha_id)
    if len(transits) > 0:
      for i, transit in enumerate(transits):
        (jd_transit, rashi1, rashi2) = (transit.jd, transit.value_1, transit.value_2)
        if self.panchaanga.jd_start < jd_transit < jd_end:
          fday = int(floor(jd_transit) - floor(self.panchaanga.jd_start) + 1)
          self.panchaanga.daily_panchaangas[fday].festivals.append(FestivalInstance(name='guru-saGkrAntiH~(%s##\\To{}##%s)' %
                                      (names.NAMES['RASHI_NAMES']['hk'][rashi1],
                                       names.NAMES['RASHI_NAMES']['hk'][rashi2])))
          if rashi1 < rashi2 and transits[i + 1].value_1 < transits[i + 1].value_2:
            # Considering only non-retrograde transits for pushkara computations
            # logging.debug('Non-retrograde transit; we have a pushkaram!')
            (madhyanha_start, madhyaahna_end) = interval.get_interval(self.panchaanga.daily_panchaangas[fday].jd_sunrise,
                                                                                                   self.panchaanga.daily_panchaangas[fday].jd_sunset, 2, 5).to_tuple()
            if jd_transit < madhyaahna_end:
              fday_pushkara = fday
            else:
              fday_pushkara = fday + 1
            self.add_festival(
              '%s-Adi-puSkara-ArambhaH' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi2],
              fday_pushkara, debug=False)
            self.add_festival(
              '%s-Adi-puSkara-samApanam' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi2],
              fday_pushkara + 11, debug=False)
            self.add_festival(
              '%s-antya-puSkara-samApanam' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi1],
              fday_pushkara - 1, debug=False)
            self.add_festival(
              '%s-antya-puSkara-ArambhaH' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi1],
              fday_pushkara - 12, debug=False)


MIN_DAYS_NEXT_ECLIPSE = 25

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
