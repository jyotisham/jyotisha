import sys
import logging
from copy import copy
from datetime import datetime
from math import floor

from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.temporal import zodiac, tithi
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision
from pytz import timezone as tz
from sanskrit_data.schema import common

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class SolarFestivalAssigner(FestivalAssigner):
  def assign_all(self):
    # self.assign_gajachhaya_yoga(debug_festivals=debug)
    self.assign_sankranti_punyakaala()
    self.assign_mahodaya_ardhodaya()
    self.assign_month_day_kaaradaiyan()
    self.assign_month_day_kuchela()
    self.assign_month_day_mesha_sankraanti()
    self.assign_vishesha_vyatipata()
    self.assign_agni_nakshatra()


  def assign_sankranti_punyakaala(self):
    if 'mESa-viSu-puNyakAlaH' not in self.rules_collection.name_to_rule:
      return 

    # Reference
    # ---------
    #
    # अतीतानागते पुण्ये द्वे उदग्दक्षिणायने। त्रिंशत्कर्कटके नाड्यो मकरे विंशतिः स्मृताः॥
    # वर्तमाने तुलामेषे नाड्यस्तूभयतो दश। षडशीत्यामतीतायां षष्टिरुक्तास्तु नाडिकाः॥
    # पुण्यायां विष्णुपद्यां च प्राक् पश्चादपि षोडशः॥
    # —वैद्यनाथ-दीक्षितीये स्मृतिमुक्ताफले आह्निक-काण्डः
    #
    # The times before and/or after any given sankranti (tropical/sidereal) are sacred for snanam & danam
    # with specific times specified. For Mesha and Tula, 10 nAdikas before and after are special,
    # while for Shadashiti, an entire 60 nAdikas following the sankramaNam are special, and so on.

    PUNYA_KAALA = {1: (10, 10), 2: (16, 16), 3: (0, 60), 4: (30, 0), 5: (16, 16), 6: (0, 60),
                   7: (10, 10), 8: (16, 16), 9: (0, 60), 10: (0, 20), 11: (16, 16), 12: (0, 60)}
    SANKRANTI_PUNYAKALA_NAMES = {1: "mESa-viSu", 2: "viSNupadI", 3: "SaDazIti", 4: "kaTaka-saGkrAnti",
      5: "viSNupadI", 6: "SaDazIti", 7: "tulA-viSu", 8: "viSNupadI",
      9: "SaDazIti", 10: "makara-saGkrAnti", 11: "viSNupadI", 12: "SaDazIti"}
    TROPICAL_SANKRANTI_PUNYAKALA_NAMES = {1: "mESa-viSu", 2: "viSNupadI", 3: "SaDazIti", 4: "dakSiNAyana",
      5: "viSNupadI", 6: "SaDazIti", 7: "tulA-viSu", 8: "viSNupadI",
      9: "SaDazIti", 10: "uttarAyaNa", 11: "viSNupadI", 12: "SaDazIti"}

    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + 1):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition is not None:
        punya_kaala_str = SANKRANTI_PUNYAKALA_NAMES[self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month] + '-puNyakAlaH'
        jd_transition = self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition
        # TODO: convert carefully to relative nadikas!
        punya_kaala_start_jd = jd_transition - PUNYA_KAALA[self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month][0] * 1/60
        punya_kaala_end_jd = jd_transition + PUNYA_KAALA[self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month][1] * 1/60
        self.daily_panchaangas[d].festival_id_to_instance[punya_kaala_str] = ( FestivalInstance(name=punya_kaala_str, interval=Interval(jd_start=punya_kaala_start_jd, jd_end=punya_kaala_end_jd)))

      if self.daily_panchaangas[d].tropical_date_sunset.month_transition is not None:
        logging.debug(d)
        punya_kaala_str = TROPICAL_SANKRANTI_PUNYAKALA_NAMES[self.daily_panchaangas[d + 1].tropical_date_sunset.month] + '-puNyakAlaH'
        jd_transition = self.daily_panchaangas[d].tropical_date_sunset.month_transition
        # TODO: convert carefully to relative nadikas!
        punya_kaala_start_jd = jd_transition - PUNYA_KAALA[self.daily_panchaangas[d + 1].tropical_date_sunset.month][0] * 1/60
        punya_kaala_end_jd = jd_transition + PUNYA_KAALA[self.daily_panchaangas[d + 1].tropical_date_sunset.month][1] * 1/60
        self.daily_panchaangas[d].festival_id_to_instance[punya_kaala_str] = ( FestivalInstance(name=punya_kaala_str, interval=Interval(jd_start=punya_kaala_start_jd, jd_end=punya_kaala_end_jd)))
        masa_name = names.NAMES['RTU_MASA_NAMES']['sa']['hk'][self.daily_panchaangas[d + 1].tropical_date_sunset.month]
        self.daily_panchaangas[d].festival_id_to_instance[masa_name] = (FestivalInstance(name=masa_name, interval=Interval(jd_start=None, jd_end=jd_transition)))

  def assign_agni_nakshatra(self):
    if 'agninakSatra-ArambhaH' not in self.rules_collection.name_to_rule:
      return 
    agni_jd_start = agni_jd_end = None
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + 1):
      # AGNI nakshatra
      # Arbitrarily checking after Mesha 10! Agni Nakshatram can't start earlier...
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day == 10:
        anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.ayanaamsha_id, anga_type=zodiac.AngaType.SOLAR_NAKSH_PADA)
        agni_jd_start, dummy = anga_finder.find(
          jd1=self.daily_panchaangas[d].jd_sunrise, jd2=self.daily_panchaangas[d].jd_sunrise + 30,
          target_anga_id=7).to_tuple()
        dummy, agni_jd_end = anga_finder.find(
          jd1=agni_jd_start, jd2=agni_jd_start + 30,
          target_anga_id=13).to_tuple()

      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day > 10:
        if agni_jd_start is not None:
          if self.daily_panchaangas[d].jd_sunset < agni_jd_start < self.daily_panchaangas[d + 1].jd_sunset:
            self.panchaanga.add_festival(fest_id='agninakSatra-ArambhaH', date=self.daily_panchaangas[d].date + 1)
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 2 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day > 10:
        if agni_jd_end is not None:
          if self.daily_panchaangas[d].jd_sunset < agni_jd_end < self.daily_panchaangas[d + 1].jd_sunset:
            self.panchaanga.add_festival(fest_id='agninakSatra-samApanam', date=self.daily_panchaangas[d].date + 1)

  def assign_month_day_kaaradaiyan(self):
    if 'kAraDaiyAn2 nOn2bu' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      ####################
      # Festival details #
      ####################

      # KARADAIYAN NOMBU
      if daily_panchaanga.solar_sidereal_date_sunset.month == 12 and daily_panchaanga.solar_sidereal_date_sunset.day == 1:
        festival_name = 'kAraDaiyAn2 nOn2bu'
        if NakshatraDivision(daily_panchaanga.jd_sunrise - (1 / 15.0) * (daily_panchaanga.jd_sunrise - self.daily_panchaangas[d - 1].jd_sunrise),
                             ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi().index == 12:
          # If kumbha prevails two ghatikAs before sunrise, nombu can be done in the early morning itself, else, previous night.
          self.panchaanga.festival_id_to_days[festival_name] = {self.daily_panchaangas[d - 1].date}
        else:
          self.panchaanga.festival_id_to_days[festival_name] = {daily_panchaanga.date}

  def assign_month_day_kuchela(self):
    if 'kucEla-dinam' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      # KUCHELA DINAM
      if daily_panchaanga.solar_sidereal_date_sunset.month == 9 and daily_panchaanga.solar_sidereal_date_sunset.day <= 7 and daily_panchaanga.date.get_weekday() == 3:
        self.panchaanga.festival_id_to_days['kucEla-dinam'] = {daily_panchaanga.date}

  def assign_month_day_mesha_sankraanti(self):
    if 'mESa-saGkrAntiH' not in self.rules_collection.name_to_rule:
      return 
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      # MESHA SANKRANTI
      if daily_panchaanga.solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d - 1].solar_sidereal_date_sunset.month == 12:
        # distance from prabhava
        samvatsara_id = (daily_panchaanga.date.year - 1568) % 60 + 1
        new_yr = 'mESa-saGkrAntiH' + '~(' + names.NAMES['SAMVATSARA_NAMES']['sa']['hk'][
          (samvatsara_id % 60) + 1] + \
                 '-' + 'saMvatsaraH' + ')'
        # self.panchaanga.festival_id_to_days[new_yr] = [d]
        self.panchaanga.add_festival(fest_id=new_yr, date=self.daily_panchaangas[d].date)
        self.panchaanga.add_festival(fest_id='paJcAGga-paThanam', date=self.daily_panchaangas[d].date)

  def assign_vishesha_vyatipata(self):
    vs_list = copy(self.panchaanga.festival_id_to_days.get('vyatIpAta-zrAddham', []))
    for date in vs_list:
      if self.panchaanga.date_str_to_panchaanga[date.get_date_str()].solar_sidereal_date_sunset.month == 9:
        self.panchaanga.delete_festival_date(fest_id='vyatIpAta-zrAddham', date=date)
        festival_name = 'mahAdhanurvyatIpAta-zrAddham'
        self.panchaanga.add_festival(fest_id=festival_name, date=date)
      elif self.panchaanga.date_str_to_panchaanga[date.get_date_str()].solar_sidereal_date_sunset.month == 6:
        self.panchaanga.festival_id_to_days['vyatIpAta-zrAddham'].remove(date)
        festival_name = 'mahAvyatIpAta-zrAddham'
        self.panchaanga.add_festival(fest_id=festival_name, date=date)

  def assign_gajachhaya_yoga(self):
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
            self.panchaanga.add_festival(fest_id=festival_name, date=self.daily_panchaangas[d].date)
            # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))
          elif daily_panchaanga.date.get_weekday() == 0:
            festival_name = 'ardhOdaya-puNyakAlaH'
            self.panchaanga.add_festival(fest_id=festival_name, date=self.daily_panchaangas[d].date)
            # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))
      


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
