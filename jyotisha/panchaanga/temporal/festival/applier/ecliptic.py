import sys
from math import floor

from jyotisha import names
from jyotisha.panchaanga.temporal import interval
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival import FestivalInstance, TransitionFestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import AngaType
from sanskrit_data.schema import common


class EclipticFestivalAssigner(FestivalAssigner):
  def assign_all(self):
    self.set_jupiter_transits()
    self.compute_solar_eclipses()
    self.compute_lunar_eclipses()
    # self.assign_ayanam()

  def compute_solar_eclipses(self):
    if 'sUrya-grahaNam' not in self.rules_collection.name_to_rule:
      return 
    jd = self.panchaanga.jd_start
    while 1:
      next_eclipse_sol = self.panchaanga.city.get_solar_eclipse_time(jd_start=jd)
      # compute offset from UTC
      jd = next_eclipse_sol[1][0]
      jd_eclipse_solar_start = next_eclipse_sol[1][1]
      jd_eclipse_solar_end = next_eclipse_sol[1][4]
      # -1 is to not miss an eclipse that occurs after sunset on 31-Dec!
      if jd_eclipse_solar_start > self.panchaanga.jd_end + 1:
        break
      else:
        fday = int(floor(jd) - floor(self.daily_panchaangas[0].julian_day_start))
        if (jd < self.daily_panchaangas[fday].jd_sunrise):
          fday -= 1
        if (jd_eclipse_solar_start) == 0.0 or jd_eclipse_solar_end == 0.0:
          # Move towards the next eclipse... at least the next new
          # moon (>=25 days away)
          jd += MIN_DAYS_NEXT_ECLIPSE
          continue
        solar_eclipse_str = 'sUrya-grahaNam'
        if self.daily_panchaangas[fday].date.get_weekday() == 0:
          solar_eclipse_str = '★cUDAmaNi-' + solar_eclipse_str
        self.daily_panchaangas[fday]. festival_id_to_instance[solar_eclipse_str] = ( FestivalInstance(name=solar_eclipse_str, interval=Interval(jd_start=jd_eclipse_solar_start, jd_end=jd_eclipse_solar_end)))
      jd = jd + MIN_DAYS_NEXT_ECLIPSE

  def compute_lunar_eclipses(self):
    if '★cUDAmaNi-candra-grahaNam' not in self.rules_collection.name_to_rule:
      return
      # Set location
    jd = self.panchaanga.jd_start
    while 1:
      next_eclipse_lun = self.panchaanga.city.get_lunar_eclipse_time(jd)
      jd = next_eclipse_lun[1][0]
      jd_eclipse_lunar_start = next_eclipse_lun[1][2]
      jd_eclipse_lunar_end = next_eclipse_lun[1][3]
      # -1 is to not miss an eclipse that occurs after sunset on 31-Dec!
      if jd_eclipse_lunar_start > self.panchaanga.jd_end:
        break
      else:
        if jd_eclipse_lunar_start == 0.0 or jd_eclipse_lunar_end == 0.0:
          # 0.0 is returned in case of eclipses when the moon is below the horizon.
          # Move towards the next eclipse... at least the next full
          # moon (>=25 days away)
          jd += MIN_DAYS_NEXT_ECLIPSE
          continue
        fday = int(floor(jd_eclipse_lunar_start) - floor(self.panchaanga.jd_start) + 1)
        # print '%%', jd, fday, self.date_str_to_panchaanga[fday].jd_sunrise,
        # self.date_str_to_panchaanga[fday-1].jd_sunrise
        if jd < self.daily_panchaangas[fday].jd_sunrise:
          fday -= 1
        # print '%%', jd, fday, self.date_str_to_panchaanga[fday].jd_sunrise,
        # self.date_str_to_panchaanga[fday-1].jd_sunrise, eclipse_lunar_start,
        # eclipse_lunar_end
        jd_moonrise_eclipse_day = self.panchaanga.city.get_rising_time(julian_day_start=self.daily_panchaangas[fday].jd_sunrise, body=Graha.MOON)

        jd_moonset_eclipse_day = self.panchaanga.city.get_setting_time(julian_day_start=jd_moonrise_eclipse_day, body=Graha.MOON)

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

        self.daily_panchaangas[fday].festival_id_to_instance[lunar_eclipse_str] = ( FestivalInstance(name=lunar_eclipse_str, interval=Interval(jd_start=jd_eclipse_lunar_start, jd_end=jd_eclipse_lunar_end)))
      jd += MIN_DAYS_NEXT_ECLIPSE

  def set_jupiter_transits(self):
    if 'guru-saGkrAntiH' not in self.rules_collection.name_to_rule:
      return 
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
          fday = int(floor(jd_transit) - floor(self.daily_panchaangas[0].julian_day_start))
          fest = TransitionFestivalInstance(name='guru-saGkrAntiH', status_1_hk=names.NAMES['RASHI_NAMES']['hk'][rashi1], status_2_hk=names.NAMES['RASHI_NAMES']['hk'][rashi2])
          self.daily_panchaangas[fday].festival_id_to_instance[fest.name] =  fest
          if rashi1 < rashi2 and transits[i + 1].value_1 < transits[i + 1].value_2:
            # Considering only non-retrograde transits for pushkara computations
            # logging.debug('Non-retrograde transit; we have a pushkaram!')
            (madhyanha_start, madhyaahna_end) = interval.get_interval(self.daily_panchaangas[fday].jd_sunrise,
                                                                                                   self.daily_panchaangas[fday].jd_sunset, 2, 5).to_tuple()
            if jd_transit < madhyaahna_end:
              fday_pushkara = fday
            else:
              fday_pushkara = fday + 1
            self.festival_id_to_days[
              '%s-Adi-puSkara-ArambhaH' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi2]].add(self.daily_panchaangas[fday_pushkara].date)
            self.festival_id_to_days[
              '%s-Adi-puSkara-samApanam' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi2]].add(self.daily_panchaangas[fday_pushkara].date + 11)
            self.festival_id_to_days[
              '%s-antya-puSkara-samApanam' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi1]].add(self.daily_panchaangas[fday_pushkara].date - 1)
            self.festival_id_to_days[
              '%s-antya-puSkara-ArambhaH' % names.NAMES['PUSHKARA_NAMES']['hk'][rashi1]].add(self.daily_panchaangas[fday_pushkara].date - 12)


MIN_DAYS_NEXT_ECLIPSE = 25

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
