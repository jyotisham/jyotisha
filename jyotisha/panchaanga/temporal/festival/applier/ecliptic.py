import sys
from datetime import datetime
from math import floor

from pytz import timezone as tz

from jyotisha import names
from jyotisha.panchaanga.temporal import interval
from jyotisha.panchaanga.temporal import time
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival import FestivalInstance, TransitionFestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.time import Hour, Date
from jyotisha.panchaanga.temporal.zodiac import AngaType, Ayanamsha
from sanskrit_data.schema import common


class EclipticFestivalAssigner(FestivalAssigner):
  def assign_all(self, debug=False):
    self.set_jupiter_transits()
    self.compute_solar_eclipses()
    self.compute_lunar_eclipses()
    # self.assign_ayanam()

  def assign_tropical_months(self):
    last_d_assigned = 0
    transits = Graha.singleton(Graha.SUN).get_transits(self.panchaanga.jd_start, self.panchaanga.jd_end, anga_type=AngaType.RASHI, ayanaamsha_id=Ayanamsha.ASHVINI_STARTING_0)
    timezone = self.panchaanga.city.timezone
    month_1_start_date =  self.daily_panchaangas[0].date
    month_end_date =  self.daily_panchaangas[-1].date
    for i, transit in enumerate(transits):
      fest = FestivalInstance(name=names.NAMES['RTU_MASA_NAMES']["hk"][transit.value_2], interval=Interval(jd_start=transit.jd, jd_end=None))

      month_2_start_panchaanga = self.panchaanga.pre_sunset_daily_panchaanga_for_jd(julian_day=transit.jd)
      month_1_end_date = month_2_start_panchaanga.date - 1 if month_2_start_panchaanga is None else  self.daily_panchaangas[-1].date
      if month_2_start_panchaanga is None:
        month_2_start_panchaanga = self.daily_panchaangas[-1]
      # month_end_date_actual
      # month_end_date_actual.set_time_to_day_start()
      # if month_end_date_actual <= month_end_date:
      #   month_end_date = month_end_date_actual
      # else:
      #   month_end_date =  self.daily_panchaangas[-1].date
      # if self.panchaanga.daily_panchaangas[month_end_day.get_date_str()]
      # if transit.value_1 == 3:
      #   time.jd_to_utc_gregorian()
      # # Reduce fday by 1 if ayana time precedes sunrise and change increment _t by 24
      # fday_nirayana = int(ayana_jd_start - self.panchaanga.jd_start + 1)
      # if fday_nirayana > self.panchaanga.duration:
      #   continue
      # 
      # self.daily_panchaangas[fday_nirayana].tropical_date.month_end_time = ayana_jd_start
      # for i in range(last_d_assigned + 1, fday_nirayana + 1):
      #   self.daily_panchaangas[i].tropical_date.month = self.daily_panchaangas[d].solar_sidereal_date_sunset.month
      # last_d_assigned = fday_nirayana
      # if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 3:
      #   if self.daily_panchaangas[fday_nirayana].jd_sunset < ayana_jd_start < self.daily_panchaangas[fday_nirayana + 1].jd_sunset:
      #     self.daily_panchaangas[fday_nirayana].append('dakSiNAyana-puNyakAlaH')
      #   else:
      #     self.daily_panchaangas[fday_nirayana - 1].append('dakSiNAyana-puNyakAlaH')
      # if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 9:
      #   if self.daily_panchaangas[fday_nirayana].jd_sunset < ayana_jd_start < self.daily_panchaangas[fday_nirayana + 1].jd_sunset:
      #     self.daily_panchaangas[fday_nirayana + 1].append('uttarAyaNa-puNyakAlaH/mitrOtsavaH')
      #   else:
      #     self.daily_panchaangas[fday_nirayana].append('uttarAyaNa-puNyakAlaH/mitrOtsavaH')

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
        if (jd < (self.daily_panchaangas[fday].jd_sunrise + tz_off / 24.0)):
          fday -= 1
        eclipse_solar_start = time.jd_to_utc_gregorian(jd_eclipse_solar_start).get_fractional_hour()
        if (jd_eclipse_solar_start - (tz_off / 24.0)) == 0.0 or \
            (jd_eclipse_solar_end - (tz_off / 24.0)) == 0.0:
          # Move towards the next eclipse... at least the next new
          # moon (>=25 days away)
          jd += MIN_DAYS_NEXT_ECLIPSE
          continue
        solar_eclipse_str = 'sUrya-grahaNam'
        if self.daily_panchaangas[fday].date.get_weekday() == 0:
          solar_eclipse_str = '★cUDAmaNi-' + solar_eclipse_str
        self.daily_panchaangas[fday]. festivals.append(FestivalInstance(name=solar_eclipse_str, interval=Interval(jd_start=jd_eclipse_solar_start, jd_end=jd_eclipse_solar_end)))
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
        if (jd_eclipse_lunar_start - (tz_off / 24.0)) == 0.0 or \
            (jd_eclipse_lunar_end - (tz_off / 24.0)) == 0.0:
          # Move towards the next eclipse... at least the next full
          # moon (>=25 days away)
          jd += MIN_DAYS_NEXT_ECLIPSE
          continue
        fday = int(floor(jd_eclipse_lunar_start) - floor(self.panchaanga.jd_start) + 1)
        # print '%%', jd, fday, self.daily_panchaangas[fday].jd_sunrise,
        # self.daily_panchaangas[fday-1].jd_sunrise
        if (jd < (self.daily_panchaangas[fday].jd_sunrise + tz_off / 24.0)):
          fday -= 1
        # print '%%', jd, fday, self.daily_panchaangas[fday].jd_sunrise,
        # self.daily_panchaangas[fday-1].jd_sunrise, eclipse_lunar_start,
        # eclipse_lunar_end
        jd_moonrise_eclipse_day = self.panchaanga.city.get_rising_time(julian_day_start=self.daily_panchaangas[fday].jd_sunrise,
                                                            body=Graha.MOON) + (tz_off / 24.0)

        jd_moonset_eclipse_day = self.panchaanga.city.get_rising_time(julian_day_start=jd_moonrise_eclipse_day,
                                                           body=Graha.MOON) + (tz_off / 24.0)

        if jd_eclipse_lunar_end < jd_moonrise_eclipse_day or \
            jd_eclipse_lunar_start > jd_moonset_eclipse_day:
          # Move towards the next eclipse... at least the next full
          # moon (>=25 days away)
          jd += MIN_DAYS_NEXT_ECLIPSE
          continue

        if Graha.singleton(Graha.MOON).get_longitude(jd_eclipse_lunar_end) < Graha.singleton(Graha.SUN).get_longitude(
            jd_eclipse_lunar_end):
          grasta = 'rAhugrasta'
        else:
          grasta = 'kEtugrasta'

        lunar_eclipse_str = 'candra-grahaNam~(' + grasta + ')'
        if self.daily_panchaangas[fday].date.get_weekday() == 1:
          lunar_eclipse_str = '★cUDAmaNi-' + lunar_eclipse_str

        self.daily_panchaangas[fday].festivals.append(FestivalInstance(name=lunar_eclipse_str, interval=Interval(jd_start=jd_eclipse_lunar_start, jd_end=jd_eclipse_lunar_end)))
      jd += MIN_DAYS_NEXT_ECLIPSE

  def set_jupiter_transits(self):
    jd_end = self.panchaanga.jd_start + self.panchaanga.duration
    check_window = 400  # Max t between two Jupiter transits is ~396 (checked across 180y)
    # Let's check for transitions in a relatively large window
    # to finalise what is the FINAL transition post retrograde movements
    transits = Graha.singleton(Graha.JUPITER).get_transits(self.panchaanga.jd_start, jd_end + check_window, anga_type=AngaType.RASHI,
                                                           ayanaamsha_id=self.ayanaamsha_id)
    if len(transits) > 0:
      for i, transit in enumerate(transits):
        (jd_transit, rashi1, rashi2) = (transit.jd, transit.value_1, transit.value_2)
        if self.panchaanga.jd_start < jd_transit < jd_end:
          fday = int(floor(jd_transit) - floor(self.panchaanga.jd_start) + 1)
          self.daily_panchaangas[fday].festivals.append(TransitionFestivalInstance(name='guru-saGkrAntiH', status_1_hk=names.NAMES['RASHI_NAMES']['hk'][rashi1], status_2_hk=names.NAMES['RASHI_NAMES']['hk'][rashi2]))
          if rashi1 < rashi2 and transits[i + 1].value_1 < transits[i + 1].value_2:
            # Considering only non-retrograde transits for pushkara computations
            # logging.debug('Non-retrograde transit; we have a pushkaram!')
            (madhyanha_start, madhyaahna_end) = interval.get_interval(self.daily_panchaangas[fday].jd_sunrise,
                                                                                                   self.daily_panchaangas[fday].jd_sunset, 2, 5).to_tuple()
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
