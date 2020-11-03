import sys
from copy import copy
from datetime import datetime
from math import floor

from pytz import timezone as tz

from jyotisha import names
from jyotisha.panchaanga.temporal import DailyPanchaangaApplier
from jyotisha.panchaanga.temporal import zodiac, tithi
from jyotisha.panchaanga.temporal.festival import rules, FestivalInstance, priority_decision
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision, Anga
from sanskrit_data.schema import common


class SolarFestivalAssigner(FestivalAssigner):
  def assign_all(self):
    # self.assign_gajachhaya_yoga(debug_festivals=debug)
    self.assign_mahodaya_ardhodaya()
    self.assign_month_day_festivals()
    self.assign_vishesha_vyatipata()

  def assign_month_day_festivals(self):
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      y = daily_panchaanga.date.year
      ####################
      # Festival details #
      ####################

      # KARADAIYAN NOMBU
      if daily_panchaanga.solar_sidereal_date_sunset.month == 12 and daily_panchaanga.solar_sidereal_date_sunset.day == 1:
        festival_name = 'kAraDaiyAn2 nOn2bu'
        if NakshatraDivision(daily_panchaanga.jd_sunrise - (1 / 15.0) * (daily_panchaanga.jd_sunrise - self.daily_panchaangas[d - 1].jd_sunrise),
                             ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi().index == 12:
          # If kumbha prevails two ghatikAs before sunrise, nombu can be done in the early morning itself, else, previous night.
          self.panchaanga.festival_id_to_days[festival_name] =  set([self.daily_panchaangas[d - 1].date])
        else:
          self.panchaanga.festival_id_to_days[festival_name] = set([daily_panchaanga.date])

      # KUCHELA DINAM
      if daily_panchaanga.solar_sidereal_date_sunset.month == 9 and daily_panchaanga.solar_sidereal_date_sunset.day <= 7 and daily_panchaanga.date.get_weekday() == 3:
        self.panchaanga.festival_id_to_days['kucEla-dinam'] = set([daily_panchaanga.date])

      # MESHA SANKRANTI
      if daily_panchaanga.solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d - 1].solar_sidereal_date_sunset.month == 12:
        # distance from prabhava
        samvatsara_id = (y - 1568) % 60 + 1
        new_yr = 'mESa-saGkrAntiH' + '~(' + names.NAMES['SAMVATSARA_NAMES']['hk'][
          (samvatsara_id % 60) + 1] + \
                 '-' + 'saMvatsaraH' + ')'
        # self.panchaanga.festival_id_to_days[new_yr] = [d]
        self.festival_id_to_days[new_yr].add(self.daily_panchaangas[d].date)
        self.festival_id_to_days['paJcAGga-paThanam'].add(self.daily_panchaangas[d].date)

  def assign_vishesha_vyatipata(self):
    vs_list = copy(self.panchaanga.festival_id_to_days.get('vyatIpAta-zrAddham', []))
    for date in vs_list:
      if self.panchaanga.date_str_to_panchaanga[date.get_date_str()].solar_sidereal_date_sunset.month == 9:
        self.panchaanga.festival_id_to_days['vyatIpAta-zrAddham'].remove(date)
        festival_name = 'mahAdhanurvyatIpAta-zrAddham'
        self.festival_id_to_days[festival_name].add(date)
      elif self.panchaanga.date_str_to_panchaanga[date.get_date_str()].solar_sidereal_date_sunset.month == 6:
        self.panchaanga.festival_id_to_days['vyatIpAta-zrAddham'].remove(date)
        festival_name = 'mahAvyatIpAta-zrAddham'
        self.festival_id_to_days[festival_name].add(date)

  def assign_gajachhaya_yoga(self, debug_festivals=False):
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      [y, m, dt] = [daily_panchaanga.date.year, daily_panchaanga.date.month, daily_panchaanga.date.day]

      # checking @ 6am local - can we do any better?
      local_time = tz(self.panchaanga.city.timezone).localize(datetime(y, m, dt, 6, 0, 0))
      # compute offset from UTC in hours
      tz_off = (datetime.utcoffset(local_time).days * 86400 +
                datetime.utcoffset(local_time).seconds) / 3600.0
      # GAJACHHAYA YOGA
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 6 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day == 1:
        moon_magha_jd_start = moon_magha_jd_start = t28_start = None
        moon_magha_jd_end = moon_magha_jd_end = t28_end = None
        moon_hasta_jd_start = moon_hasta_jd_start = t30_start = None
        moon_hasta_jd_end = moon_hasta_jd_end = t30_end = None

        anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.SIDEREAL_MONTH)
        sun_hasta_jd_start, sun_hasta_jd_end = anga_finder.find(
          jd1=self.daily_panchaangas[d].jd_sunrise, jd2=self.daily_panchaangas[d].jd_sunrise + 30, target_anga_id=13).to_tuple()

        moon_magha_jd_start, moon_magha_jd_end = anga_finder.find(
          sun_hasta_jd_start - 2, sun_hasta_jd_end + 2, 10).to_tuple()
        if all([moon_magha_jd_start, moon_magha_jd_end]):
          anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.TITHI)
          t28_start, t28_end = anga_finder.find(
            moon_magha_jd_start - 3, moon_magha_jd_end + 3, 28).to_tuple()

        anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.NAKSHATRA)
        moon_hasta_jd_start, moon_hasta_jd_end = anga_finder.find(
          sun_hasta_jd_start - 1, sun_hasta_jd_end + 1, 13).to_tuple()
        if all([moon_hasta_jd_start, moon_hasta_jd_end]):
          anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.TITHI)
          t30_start, t30_end = anga_finder.find(
            sun_hasta_jd_start - 1, sun_hasta_jd_end + 1, 30).to_tuple()

        gc_28 = gc_30 = False

        if all([sun_hasta_jd_start, moon_magha_jd_start, t28_start]):
          # We have a GC yoga
          gc_28_start = max(sun_hasta_jd_start, moon_magha_jd_start, t28_start)
          gc_28_end = min(sun_hasta_jd_end, moon_magha_jd_end, t28_end)

          if gc_28_start < gc_28_end:
            gc_28 = True

        if all([sun_hasta_jd_start, moon_hasta_jd_start, t30_start]):
          # We have a GC yoga
          gc_30_start = max(sun_hasta_jd_start, moon_hasta_jd_start, t30_start)
          gc_30_end = min(sun_hasta_jd_end, moon_hasta_jd_end, t30_end)

          if gc_30_start < gc_30_end:
            gc_30 = True

      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 6 and (gc_28 or gc_30):
        if gc_28:
          gc_28_d = 1 + floor(gc_28_start - self.panchaanga.jd_start)
          # sys.stderr.write('gajacchhaya %d\n' % gc_28_d)
          # gajacchaayaa_fest = FestivalInstance(name='gajacchAyA-yOgaH', interval=Interval(jd_start=gc_28_start, jd_end=gc_28_end), days=[self.daily_panchaangas[gc_28_d].date])
          # self.panchaanga.festival_id_to_days[gajacchaayaa_fest.name] = gajacchaayaa_fest
          gc_28 = False
        if gc_30:
          # sys.stderr.write('30: (%f, %f)\n' % (gc_30_start, gc_30_end))
          gc_30_d = 1 + floor(gc_30_start - self.panchaanga.jd_start)
          # gajacchaayaa_fest = FestivalInstance(name='gajacchAyA-yOgaH', interval=Interval(jd_start=gc_30_start, jd_end=gc_30_end), days=[self.daily_panchaangas[gc_30_d].date])
          # self.panchaanga.festival_id_to_days[gajacchaayaa_fest.name] = gajacchaayaa_fest
          gc_30 = False

  def assign_mahodaya_ardhodaya(self):
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):

      # MAHODAYAM
      # Can also refer youtube video https://youtu.be/0DBIwb7iaLE?list=PL_H2LUtMCKPjh63PRk5FA3zdoEhtBjhzj&t=6747
      # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Bhanuvasara = Ardhodayam
      # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Somavasara = Mahodayam
      sunrise_zodiac = NakshatraDivision(daily_panchaanga.jd_sunrise, ayanaamsha_id=self.ayanaamsha_id)
      sunset_zodiac = NakshatraDivision(daily_panchaanga.jd_sunset, ayanaamsha_id=self.ayanaamsha_id)
      if daily_panchaanga.lunar_month_sunrise.index in [10, 11] and daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 30 or tithi.get_tithi(daily_panchaanga.jd_sunrise).index == 30:
        if sunrise_zodiac.get_anga(zodiac.AngaType.NAKSHATRA).index == 17 or \
            sunset_zodiac.get_anga(zodiac.AngaType.NAKSHATRA).index == 17 and \
            sunrise_zodiac.get_anga(zodiac.AngaType.NAKSHATRA).index == 22 or \
            sunset_zodiac.get_anga(zodiac.AngaType.NAKSHATRA).index == 22:
          if daily_panchaanga.date.get_weekday() == 1:
            festival_name = 'mahOdaya-puNyakAlaH'
            self.festival_id_to_days[festival_name].add(self.daily_panchaangas[d].date)
            # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))
          elif daily_panchaanga.date.get_weekday() == 0:
            festival_name = 'ardhOdaya-puNyakAlaH'
            self.festival_id_to_days[festival_name].add(self.daily_panchaangas[d].date)
            # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))


class DailySolarAssigner(DailyPanchaangaApplier):
  def apply_month_day_events(self):
    rule_set = rules.RulesCollection.get_cached(repos=tuple(self.computation_system.options.fest_repos))
    day_panchaanga = self.day_panchaanga

    # Assign sunrise solar sidereal day fests.
    fest_dict = rule_set.get_month_anga_fests(month=day_panchaanga.solar_sidereal_date_sunset.month, anga=day_panchaanga.solar_sidereal_date_sunset.day, month_type=rules.RulesRepo.SIDEREAL_SOLAR_MONTH_DIR, anga_type_id=rules.RulesRepo.DAY_DIR)
    for fest_id, fest in fest_dict.items():
      day_panchaanga.festival_id_to_instance[fest_id] = FestivalInstance(name=fest.id)


  def apply_month_anga_events(self, anga_type):
    rule_set = rules.RulesCollection.get_cached(repos=tuple(self.computation_system.options.fest_repos))
    panchaangas = self.previous_day_panchaangas + [self.day_panchaanga]

    anga_type_id = anga_type.name.lower()
    angas = [x.anga for x in panchaangas[2].sunrise_day_angas.get_angas_with_ends(anga_type=anga_type)]
    if panchaangas[1] is not None:
      angas = angas + [x.anga for x in panchaangas[1].sunrise_day_angas.get_angas_with_ends(anga_type=anga_type)]
    angas = set(angas)
    month = self.day_panchaanga.solar_sidereal_date_sunset.month
    fest_dict = rule_set.get_possibly_relevant_fests(month=month, angas=angas, month_type=rules.RulesRepo.SIDEREAL_SOLAR_MONTH_DIR, anga_type_id=anga_type_id)
    for fest_id, fest_rule in fest_dict.items():
      kaala = fest_rule.timing.get_kaala()
      priority = fest_rule.timing.get_priority()
      anga_type_str = fest_rule.timing.anga_type
      target_anga = Anga.get_cached(index=fest_rule.timing.anga_number, anga_type_id=anga_type_str.upper())
      fday_1_vs_2 = priority_decision.decide(p0=panchaangas[1], p1=panchaangas[2], target_anga=target_anga, kaala=kaala, ayanaamsha_id=self.ayanaamsha_id, priority=priority)
      if fday_1_vs_2 is not None:
        fday = fday_1_vs_2 + 1
        p_fday = panchaangas[fday]
        p_fday_minus_1 = panchaangas[fday - 1]
        if p_fday.solar_sidereal_date_sunset.month != month:
          # Example: festival on tithi 27 of month 10; last day of month 9 has tithi 27, but not day one of month 10. 
          continue
        if priority not in ('puurvaviddha', 'vyaapti'):
          p_fday.festival_id_to_instance[fest_id] = FestivalInstance(name=fest_id)
          self.festival_id_to_days[fest_id].add(p_fday.date)
        elif p_fday_minus_1 is None or p_fday_minus_1.date not in self.festival_id_to_days[fest_id]:
          # p_fday_minus_1 could be None when computing at the beginning of a sequence of days. In that case, we're ok with faulty assignments - since the focus is on getting subsequent days right.
          # puurvaviddha or vyaapti fest. More careful condition.
          p_fday.festival_id_to_instance[fest_id] = FestivalInstance(name=fest_id)
          self.festival_id_to_days[fest_id].add(p_fday.date)
      


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
