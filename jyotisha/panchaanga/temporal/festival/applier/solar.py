import sys
import os
import logging
from copy import copy
from datetime import datetime
from math import floor

from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.temporal import zodiac, tithi
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.festival import FestivalInstance
from jyotisha.panchaanga.temporal.interval import Interval, get_interval
from jyotisha.panchaanga.temporal.zodiac import Ayanamsha
from jyotisha.panchaanga.temporal.zodiac import NakshatraDivision
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal import time
from pytz import timezone as tz
from sanskrit_data.schema import common
from indic_transliteration import sanscript

logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)


class SolarFestivalAssigner(FestivalAssigner):
  def assign_all(self):
    self.assign_gajachhaya_yoga()
    self.assign_pushkara_yoga()
    self.assign_sidereal_sankranti_punyakaala()
    self.assign_mahodaya_ardhodaya()
    self.assign_month_day_kaaradaiyan()
    self.assign_month_day_muDavan_muzhukku()
    self.assign_month_day_tulA_kAvErI_snAna_ArambhaH()
    self.assign_month_day_kuchela()
    self.assign_month_day_ushah_kaala_festival_period('dhanurmAsa', 'solar_sidereal')
    self.assign_month_day_ushah_kaala_festival_period('sahOmAsa', 'tropical')
    self.assign_month_day_mesha_sankraanti()
    self.assign_vishesha_vyatipata()
    # self.assign_saayana_vyatipata_vaidhrti()
    self.assign_agni_nakshatra()
    self.assign_garbhottam()
    self.assign_padmaka_yoga()
    self.assign_revati_dvadashi_yoga()
    self.assign_ayushmad_bava_saumya_yoga()
    self.assign_anadhyayana_dvadashi_yoga()
    self.assign_vaarunii_trayodashi()

  def assign_pitr_dina(self):
    self.assign_gajachhaya_yoga()
    self.assign_sidereal_sankranti_punyakaala()
    self.assign_mahodaya_ardhodaya()
    self.assign_vishesha_vyatipata()


  def assign_sidereal_sankranti_punyakaala(self, force_computation=False):
    if 'viSu-puNyakAlaH' not in self.rules_collection.name_to_rule and not force_computation:
      return 
    
    sankranti_days = []

    fname = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/misc_data/sankranti_punyakaala.toml')
    with open(fname) as f:
      import toml
      punyakaala_dict = toml.load(f)

      PUNYA_KAALA = {int(s): punyakaala_dict['PUNYA_KAALA'][s] for s in punyakaala_dict['PUNYA_KAALA']}
   
    is_puurva_half_day = True
    for d in range(self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition is not None:
        sankranti_id = self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month
        
        punya_kaala_str = names.NAMES['SANKRANTI_PUNYAKALA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][sankranti_id] + '-puNyakAlaH'
        jd_transition = self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition
        # TODO: convert carefully to relative nadikas!
        punya_kaala_start_jd = jd_transition - PUNYA_KAALA[sankranti_id][0] * 1/60
        punya_kaala_end_jd = jd_transition + PUNYA_KAALA[sankranti_id][1] * 1/60
        
        if jd_transition < self.daily_panchaangas[d].day_length_based_periods.fifteen_fold_division.aahneya.jd_end:
          fday = d
          is_puurva_half_day = jd_transition < self.daily_panchaangas[d].day_length_based_periods.puurvaahna.jd_end
          if sankranti_id == 10:
            if jd_transition < self.daily_panchaangas[d].jd_sunset:
              fday = d
              is_puurva_half_day = jd_transition < self.daily_panchaangas[d].day_length_based_periods.puurvaahna.jd_end
            else:
              fday = d + 1
              is_puurva_half_day = True
        else:
          if sankranti_id == 4:
            fday = d # Previous day only for Kataka Sankramana
            is_puurva_half_day = jd_transition < self.daily_panchaangas[d].day_length_based_periods.puurvaahna.jd_end
          else:
            fday = d + 1
            is_puurva_half_day = True
        
        if is_puurva_half_day:
          half_day = 'pUrvAhNa'
          half_day_interval = self.daily_panchaangas[fday].day_length_based_periods.puurvaahna
        else:
          half_day = 'aparAhNa'
          half_day_interval = self.daily_panchaangas[fday].day_length_based_periods.aparaahna
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='saGkramaNa-dina-%s-puNyakAlaH' % half_day, interval=half_day_interval), date=self.daily_panchaangas[fday].date)

        punya_kaala_start_jd = max(punya_kaala_start_jd, self.daily_panchaangas[fday].jd_sunrise) 
        punya_kaala_end_jd = min(punya_kaala_end_jd, self.daily_panchaangas[fday].jd_sunset) 
        if punya_kaala_end_jd > punya_kaala_start_jd:
          self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=punya_kaala_str, interval=Interval(jd_start=punya_kaala_start_jd, jd_end=punya_kaala_end_jd)),
                                                date=self.daily_panchaangas[fday].date)
        else:
          self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=punya_kaala_str, interval=Interval(jd_start=None, jd_end=None)),
                                                date=self.daily_panchaangas[fday].date)
        sankranti_days.append(self.daily_panchaangas[fday].date)
        if sankranti_id not in [2, 5, 8, 11]: # these cases are redundant!
          saamaanya_punya_kaala_start_jd = jd_transition - 16 * 1/60
          saamaanya_punya_kaala_end_jd = jd_transition + 16 * 1/60
          saamaanya_punya_kaala_start_jd = max(saamaanya_punya_kaala_start_jd, self.daily_panchaangas[fday].jd_sunrise) 
          saamaanya_punya_kaala_end_jd = min(saamaanya_punya_kaala_end_jd, self.daily_panchaangas[fday].jd_sunset) 
          if saamaanya_punya_kaala_end_jd > saamaanya_punya_kaala_start_jd: 
            self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='ravi-saGkramaNa-puNyakAlaH', interval=Interval(jd_start=saamaanya_punya_kaala_start_jd, jd_end=saamaanya_punya_kaala_end_jd)), date=self.daily_panchaangas[fday].date)

    return sankranti_days

  def assign_agni_nakshatra(self):
    if 'agninakSatra-ArambhaH' not in self.rules_collection.name_to_rule:
      return 

    # AGNI nakshatra
    agni_jd_start = agni_jd_end = None
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
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
          if self.daily_panchaangas[d].jd_sunrise < agni_jd_start < self.daily_panchaangas[d + 1].jd_sunrise:
            self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='agninakSatra-ArambhaH', interval=Interval(jd_start=agni_jd_start, jd_end=None)), date=self.daily_panchaangas[d].date)
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 2 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day > 10:
        if agni_jd_end is not None:
          if self.daily_panchaangas[d].jd_sunrise < agni_jd_end < self.daily_panchaangas[d + 1].jd_sunrise:
            self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='agninakSatra-samApanam', interval=Interval(jd_start=None, jd_end=agni_jd_end)), date=self.daily_panchaangas[d].date)

  def assign_nava_nayakas(self):
    if self.panchaanga.duration < 365:
      return
    # चैत्रादि-मेष-हरि-कर्कट-चाप-युग्म-
    # रौद्रर्क्ष-तौल-झष-सङ्क्रमवासरेशाः ।
    # राजा च मन्त्रि-भटनायक-सस्यनाथ-
    # धान्यार्घ-मेघ-रस-नीरसपाः क्रमेण॥
  
    # The adhipatis are the vaasaraadhipati-s of the following events
    # (rashi/nakshatra names refer to the sun's transit into them)
    # (rashi numbers refer to ordinal numbers starting with Mesha = 0)
    #
    # 1) Raja   - Chaitra Shukla Prathama
    # 2) Mantri - Mesha   = 0
    # 3) Sena   - Simha   = 4
    # 4) Sasya  - Kataka  = 3
    # 5) Dhanya - Dhanus  = 8
    # 6) Argha  - Mithuna = 2
    # 7) Megha  - Ardra
    # 8) Rasa   - Tula    = 6
    # 9) Nirasa - Makara  = 9
  
    nava_nayakas = {}
    finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.SOLAR_NAKSH)
    anga = finder.find(jd1 = self.panchaanga.jd_start, jd2=self.panchaanga.jd_end, target_anga_id=5)
    fday = int(floor(anga.jd_start) - floor(self.daily_panchaangas[0].julian_day_start))
    if (anga.jd_start < self.daily_panchaangas[fday].jd_sunrise):
      fday -= 1

    nava_nayakas['mEghAdhipaH'] = names.NAMES['VARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][self.daily_panchaangas[fday].date.get_weekday()]
    
    NAYAKA_MAP = {'mantrI': 1,
                  'sEnAdhipaH': 5,
                  'sasyAdhipaH': 4,
                  'dhAnyAdhipaH': 9,
                  'arghAdhipaH': 3,
                  'rasAdhipaH': 7,
                  'nIrasAdhipaH': 10}

    for d in range(self.panchaanga.duration - 25):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition is not None:
        sankranti_id = self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month
        if sankranti_id == 1:
          mesha_start = self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition
        for nayaka in NAYAKA_MAP:
          if sankranti_id == NAYAKA_MAP[nayaka]:
            nava_nayakas[nayaka] = names.NAMES['VARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][self.daily_panchaangas[d].date.get_weekday()]

    finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.GRAHA_RASHI[Graha.SUN])
    anga = finder.find(jd1 = self.panchaanga.jd_start - 32, jd2=self.panchaanga.jd_start, target_anga_id=12)
    mina_start = anga.jd_start

    finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.TITHI)
    anga = finder.find(jd1 = mina_start, jd2=mesha_start, target_anga_id=30)
    
    nava_nayakas['rAjA'] = names.NAMES['VARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][time.get_weekday(self.panchaanga.city.get_rising_time(julian_day_start=anga.jd_end, body=Graha.SUN))]
    self.panchaanga.nava_nayakas = nava_nayakas

  def assign_garbhottam(self):
    if 'garbhOTTam-Arambham' not in self.rules_collection.name_to_rule:
      return
    finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.SOLAR_NAKSH)
    anga = finder.find(jd1 = self.panchaanga.jd_start, jd2=self.panchaanga.jd_end, target_anga_id=20)

    if anga is None:
      logging.warning('No Garbhottam found in this panchaanga interval!')
      return
    if anga.jd_start is None:
      logging.warning('No Garbhottam start found in this panchaanga interval!')
      return
    if anga.jd_end is None:
      logging.warning('No Garbhottam end found in this panchaanga interval!')
      return

    fday = int(floor(anga.jd_start) - floor(self.daily_panchaangas[0].julian_day_start))
    if (anga.jd_start < self.daily_panchaangas[fday].jd_sunrise):
      fday -= 1
    self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='garbhOTTam-Arambham', interval=Interval(jd_start=anga.jd_start, jd_end=None)), date=self.daily_panchaangas[fday].date)

    fday = int(floor(anga.jd_end) - floor(self.daily_panchaangas[0].julian_day_start))
    if (anga.jd_end < self.daily_panchaangas[fday].jd_sunrise):
      fday -= 1
    self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='garbhOTTam-muDivu', interval=Interval(jd_start=None, jd_end=anga.jd_end)), date=self.daily_panchaangas[fday].date)

  def assign_month_day_kaaradaiyan(self):
    if 'kAraDaiyAn2_nOn2bu' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      if daily_panchaanga.solar_sidereal_date_sunset.month == 12 and daily_panchaanga.solar_sidereal_date_sunset.day == 1:
        festival_name = 'kAraDaiyAn2 nOn2bu'
        if NakshatraDivision(daily_panchaanga.jd_sunrise - (1 / 15.0) * (daily_panchaanga.jd_sunrise - self.daily_panchaangas[d - 1].jd_sunrise),
                             ayanaamsha_id=self.ayanaamsha_id).get_solar_raashi().index == 12:
          # If kumbha prevails two ghatikAs before sunrise, nombu can be done in the early morning itself, else, previous night.
          self.panchaanga.add_festival(
            fest_id=festival_name, date=self.daily_panchaangas[d - 1].date)
        else:
          self.panchaanga.add_festival(
            fest_id=festival_name, date=daily_panchaanga.date)

  def assign_month_day_kuchela(self):
    if 'kucEla-dinam' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      # KUCHELA DINAM
      if daily_panchaanga.solar_sidereal_date_sunset.month == 9 and daily_panchaanga.solar_sidereal_date_sunset.day <= 7 and daily_panchaanga.date.get_weekday() == 3:
        self.panchaanga.add_festival(
          fest_id='kucEla-dinam', date=daily_panchaanga.date)

  def assign_month_day_ushah_kaala_festival_period(self, fest_id, month_type):
    if 'dhanurmAsa-uSaHkAla-pUjA-ArambhaH' not in self.rules_collection.name_to_rule and 'sahOmAsa-uSaHkAla-pUjA-ArambhaH' not in self.rules_collection.name_to_rule:
      return
    date_attr = month_type + '_date_sunset'
    start_fest_id = fest_id + '-uSaHkAla-pUjA-ArambhaH'
    end_fest_id = fest_id + '-uSaHkAla-pUjA-samApanam'
    if start_fest_id not in self.rules_collection.name_to_rule:
      logging.debug('Festival %s not in rules collection!' % start_fest_id)
      return

    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      # DHANURMASA/SAHOMASA PUJA
      # This can start on the first or second day of the masa, not before; depending on the time of the month transition
      # This is for sidereal_solar 9 and tropical 10 as per 6eeec085f56947db5de32d8bfea51957c4dde789
      if getattr(daily_panchaanga, date_attr).month == (9 + int(month_type=='tropical')) and getattr(daily_panchaanga, date_attr).day == 1:
        ushah_kaala = get_interval(start_jd=daily_panchaanga.jd_previous_sunset, end_jd=daily_panchaanga.jd_sunrise, part_index=range(25,28), num_parts=30)
        jd_transition = getattr(daily_panchaanga, date_attr).month_transition
        if jd_transition is None:
          # Transit happened before sunrise; so fetch it from the previous day's panchaanga
          jd_transition = getattr(self.daily_panchaangas[d - 1], date_attr).month_transition
        if jd_transition > ushah_kaala.jd_end:
          self.panchaanga.add_festival(fest_id=start_fest_id, date=self.daily_panchaangas[d + 1].date)
        else:
          self.panchaanga.add_festival(fest_id=start_fest_id, date=daily_panchaanga.date)

      if getattr(daily_panchaanga, date_attr).month_transition and getattr(self.daily_panchaangas[d - 1], date_attr).month == (9 + int(month_type=='tropical')):
        # Makara Sankramana (sidereal_solar) / Uttarayana (tropical)
        # Check if happens before the start of ushah kaala
        ushah_kaala = get_interval(start_jd=daily_panchaanga.jd_sunset, end_jd=daily_panchaanga.jd_next_sunrise, part_index=range(25,28), num_parts=30)
        if getattr(daily_panchaanga, date_attr).month_transition < ushah_kaala.jd_start:
          self.panchaanga.add_festival(fest_id=end_fest_id, date=daily_panchaanga.date)
        else:
          self.panchaanga.add_festival(fest_id=end_fest_id, date=self.daily_panchaangas[d + 1].date)
  
  def assign_month_day_muDavan_muzhukku(self):
    if 'muDavan2_muzhukku' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      if daily_panchaanga.solar_sidereal_date_sunset.month == 8 and daily_panchaanga.solar_sidereal_date_sunset.day == 1:
        if daily_panchaanga.solar_sidereal_date_sunset.month_transition is None or daily_panchaanga.solar_sidereal_date_sunset.month_transition < daily_panchaanga.jd_sunrise:
          self.panchaanga.add_festival(fest_id='muDavan2_muzhukku', date=daily_panchaanga.date)
        else:
          self.panchaanga.add_festival(fest_id='muDavan2_muzhukku', date=self.daily_panchaangas[d + 1].date)

  def assign_month_day_tulA_kAvErI_snAna_ArambhaH(self):
    if 'tulA-kAvErI-snAna-ArambhaH' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      if daily_panchaanga.solar_sidereal_date_sunset.month_transition is not None:
        if daily_panchaanga.solar_sidereal_date_sunset.month == 7 or (daily_panchaanga.solar_sidereal_date_sunset.month == 6 and daily_panchaanga.solar_sidereal_date_sunset.day > 28):
          tula_sankramana_jd = daily_panchaanga.solar_sidereal_date_sunset.month_transition
          fday = d

          if tula_sankramana_jd < self.daily_panchaangas[fday].day_length_based_periods.fifteen_fold_division.braahma.jd_start:
            self.panchaanga.add_festival(fest_id='tulA-kAvErI-snAna-ArambhaH', date=self.daily_panchaangas[fday].date)
          else:
            self.panchaanga.add_festival(fest_id='tulA-kAvErI-snAna-ArambhaH', date=self.daily_panchaangas[fday + 1].date)

          return

  def _assign_yoga(self, yoga_name, intersect_list, jd_start=None, jd_end=None, show_debug_info=True):
    if jd_start is None:
      jd_start = self.panchaanga.jd_start
    if jd_end is None:
      jd_end = self.panchaanga.jd_end
    jd_start_in = jd_start
    jd_end_in = jd_end
    anga_list = []
    yoga_happens = True
    for anga_type, target_anga_id in intersect_list:
      finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=anga_type)
      anga = finder.find(jd1 = jd_start, jd2=jd_end, target_anga_id=target_anga_id)
      if anga is None:
        if show_debug_info:
          msg = ' + '.join(['%s %d' % (intersect_list[i][0], intersect_list[i][1]) for i in range(len(intersect_list))])
          logging.debug('No %s involving %s in span %s!' % (yoga_name, msg, Interval(jd_start=jd_start_in, jd_end=jd_end_in)))
        yoga_happens = False
        break
      else:
        if anga.jd_start is None:
          anga.jd_start = jd_start
        if anga.jd_end is None:
          anga.jd_end = jd_end

      if anga.jd_start is not None:
        jd_start = anga.jd_start
      if anga.jd_end is not None:
        jd_end = anga.jd_end
      anga_list.append(anga)

    if yoga_happens:
      jd_start, jd_end = max([x.jd_start for x in anga_list]), min([x.jd_end for x in anga_list])
      if jd_start > jd_end or jd_start > self.panchaanga.jd_end:
        if show_debug_info:
          msg = ' + '.join(['%s %d' % (intersect_list[i][0], intersect_list[i][1]) for i in range(len(intersect_list))])
          logging.debug('No %s involving %s in span %s!' % (msg, yoga_name, Interval(jd_start=jd_start_in, jd_end=jd_end_in)))
      else:
        fday = int(floor(jd_start) - floor(self.daily_panchaangas[0].julian_day_start))
        if jd_start < self.daily_panchaangas[fday].jd_sunrise:
          fday -= 1
        jd_midnight_local = self.daily_panchaangas[fday + 1].julian_day_start
        if jd_start > jd_midnight_local and jd_end > self.daily_panchaangas[fday + 1].jd_sunrise:
          fday += 1
        if show_debug_info:
          logging.debug(f'Adding {yoga_name} from {Interval(jd_start=jd_start, jd_end=jd_end)} on {self.daily_panchaangas[fday].date}')
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=yoga_name, interval=Interval(jd_start=jd_start, jd_end=jd_end)), date=self.daily_panchaangas[fday].date)

    return yoga_happens

  def assign_month_day_mesha_sankraanti(self):
    if 'sauramAna-saMvatsarArambhaH' not in self.rules_collection.name_to_rule:
      return 
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      # MESHA SANKRANTI
      if daily_panchaanga.solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d - 1].solar_sidereal_date_sunset.month == 12:
        # distance from prabhava
        samvatsara_id = (daily_panchaanga.date.year - 1568) % 60 + 1
        yname = names.NAMES['SAMVATSARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][(samvatsara_id % 60) + 1]
        # Manual cleaning of name - dropping visarga etc.
        yname = yname.rstrip('H')
        if yname[-1] == 'I':
          yname = yname[:-1] + 'i'
        new_yr = 'sauramAna-saMvatsarArambhaH' + '~(' + yname + \
                 '-' + 'saMvatsaraH' + ')'
        # self.panchaanga.festival_id_to_days[new_yr] = [d]
        self.panchaanga.add_festival(fest_id=new_yr, date=self.daily_panchaangas[d].date)
        self.panchaanga.add_festival(fest_id='paJcAGga-paThanam', date=self.daily_panchaangas[d].date)
        self.panchaanga.add_festival(fest_id='viSukkan2i', date=self.daily_panchaangas[d].date)
        # if daily_panchaanga.solar_sidereal_date_sunset.month_transition is None or daily_panchaanga.solar_sidereal_date_sunset.month_transition < daily_panchaanga.jd_sunrise:
        #   self.panchaanga.add_festival(fest_id='viSukkan2i', date=daily_panchaanga.date)
        # else:
        #   self.panchaanga.add_festival(fest_id='viSukkan2i', date=self.daily_panchaangas[d + 1].date)

  def assign_saayana_vyatipata_vaidhrti(self):
    if 'sAyana-vyatIpAtaH' not in self.rules_collection.name_to_rule:
      return 
    saayana_yoga_pada_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=Ayanamsha.VERNAL_EQUINOX_AT_0, anga_type=zodiac.AngaType.YOGA_PADA)
    saayana_yoga_pada_list = saayana_yoga_pada_finder.get_all_angas_in_period(jd1=self.panchaanga.jd_start, jd2=self.panchaanga.jd_end + 1)

    jd_start = jd_end = None

    for saayana_yoga_pada in saayana_yoga_pada_list:
      if saayana_yoga_pada.anga.index in (54, 108):
        jd_end = saayana_yoga_pada.jd_end
        if saayana_yoga_pada.anga.index == 54:
          festival_name = 'sAyana-vyatIpAtaH'
        else:
          festival_name = 'sAyana-vaidhRtiH'

        fday = int(floor(jd_end - 1) - floor(self.daily_panchaangas[0].julian_day_start))
        if jd_end > self.daily_panchaangas[fday + 1].jd_sunrise:
          FI = FestivalInstance(name=festival_name, interval=Interval(jd_start=None, jd_end=jd_end))
          self.panchaanga.add_festival_instance(festival_instance=FI, date=self.daily_panchaangas[fday + 1].date)
        else:
          FI = FestivalInstance(name=festival_name, interval=Interval(jd_start=None, jd_end=jd_end))
          self.panchaanga.add_festival_instance(festival_instance=FI, date=self.daily_panchaangas[fday].date)


  def assign_vishesha_vyatipata(self):
    vs_list = copy(self.panchaanga.festival_id_to_days.get('vyatIpAta-zrAddham', []))
    for date in vs_list:
      if self.panchaanga.date_str_to_panchaanga[date.get_date_str()].solar_sidereal_date_sunset.month == 9:
        self.panchaanga.delete_festival_date(fest_id='vyatIpAta-zrAddham', date=date)
        festival_name = 'mahAdhanurvyatIpAta-zrAddham'
        self.panchaanga.add_festival(fest_id=festival_name, date=date)
      elif self.panchaanga.date_str_to_panchaanga[date.get_date_str()].lunar_date.month.index == 6:
        self.panchaanga.delete_festival_date(fest_id='vyatIpAta-zrAddham', date=date)
        self.panchaanga.add_festival(fest_id='mahAvyatIpAta-zrAddham', date=date)

  def assign_gajachhaya_yoga(self):
    if 'gajacchAyA-yOgaH' not in self.rules_collection.name_to_rule:
      return 
    self._assign_yoga('gajacchAyA-yOgaH', [(zodiac.AngaType.SOLAR_NAKSH, 13), (zodiac.AngaType.NAKSHATRA, 10), (zodiac.AngaType.TITHI, 28)],
                      jd_start=self.panchaanga.jd_start, jd_end=self.panchaanga.jd_end)
    self._assign_yoga('gajacchAyA-yOgaH', [(zodiac.AngaType.SOLAR_NAKSH, 13), (zodiac.AngaType.NAKSHATRA, 13), (zodiac.AngaType.TITHI, 30)],
                      jd_start=self.panchaanga.jd_start, jd_end=self.panchaanga.jd_end)

  def assign_pushkara_yoga(self):
    if 'tripuSkara-yOgaH~0' not in self.rules_collection.name_to_rule:
      return

    PUSHKARA_TITHI = [2, 7, 12, 17, 22, 27]
    TRI_PUSHKARA_NAKSHATRA = [3, 7, 12, 16, 21, 25]
    DVI_PUSHKARA_NAKSHATRA = [5, 14, 23]
    PUSHKARA_WDAY = [0, 2, 6]
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      dp_nakshatra = tp_nakshatra = p_tithi = None
      for nakshatra_span in daily_panchaanga.sunrise_day_angas.nakshatras_with_ends:
        nakshatra_ID = nakshatra_span.anga.index
        if nakshatra_ID in TRI_PUSHKARA_NAKSHATRA:
          tp_nakshatra = nakshatra_ID
        elif nakshatra_ID in DVI_PUSHKARA_NAKSHATRA:
          dp_nakshatra = nakshatra_ID
      
      for tithi_span in daily_panchaanga.sunrise_day_angas.tithis_with_ends:
        tithi_ID = tithi_span.anga.index
        if tithi_ID in PUSHKARA_TITHI:
          p_tithi = tithi_ID
      
      wday = daily_panchaanga.date.get_weekday()
      if p_tithi is not None and wday in PUSHKARA_WDAY:
        if tp_nakshatra is not None:
          self._assign_yoga('tripuSkara-yOgaH~%d' % wday, [(zodiac.AngaType.NAKSHATRA, tp_nakshatra), (zodiac.AngaType.TITHI, p_tithi)],
            jd_start=daily_panchaanga.jd_sunrise, jd_end=daily_panchaanga.jd_next_sunrise, show_debug_info=False)
        if dp_nakshatra is not None:
          self._assign_yoga('dvipuSkara-yOgaH~%d' % wday, [(zodiac.AngaType.NAKSHATRA, dp_nakshatra), (zodiac.AngaType.TITHI, p_tithi)],
            jd_start=daily_panchaanga.jd_sunrise, jd_end=daily_panchaanga.jd_next_sunrise, show_debug_info=False)

  def assign_ayushmad_bava_saumya_yoga(self):
    if 'AyuSmad-bava-saumya-saMyOgaH' not in self.rules_collection.name_to_rule:
      return
    BAVA_KARANA = list(range(2, 52, 7))
    AYUSHMAD_YOGA = 3
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      # AYUSHMAN BAVA SAUMYA
      if self.daily_panchaangas[d].date.get_weekday() == 3:
        for karana_ID in BAVA_KARANA:
          self._assign_yoga('AyuSmad-bava-saumya-saMyOgaH', [(zodiac.AngaType.YOGA, AYUSHMAD_YOGA), (zodiac.AngaType.KARANA, karana_ID)],
                            jd_start=self.daily_panchaangas[d].jd_sunrise, jd_end=self.daily_panchaangas[d].jd_sunset, show_debug_info=False)


  def assign_padmaka_yoga(self):
    if 'padmaka-yOga-puNyakAlaH' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      # यदा विष्टिर्व्यतीपातो भानुवारस्तथैव च॥
      # पद्मको नाम योगोयमयनादेश्चतुर्गुणः॥ (धर्मसिन्धौ पृ ३००)
      VISHTI = list(range(8, 60, 7))
      sunrise_zodiac = NakshatraDivision(daily_panchaanga.jd_sunrise, ayanaamsha_id=self.computation_system.ayanaamsha_id)
      sunset_zodiac = NakshatraDivision(daily_panchaanga.jd_sunset, ayanaamsha_id=self.computation_system.ayanaamsha_id)
      if daily_panchaanga.date.get_weekday() == 0 and \
        (sunrise_zodiac.get_anga(zodiac.AngaType.YOGA).index == 17 or 
         sunset_zodiac.get_anga(zodiac.AngaType.YOGA).index == 17) and \
        (sunrise_zodiac.get_anga(zodiac.AngaType.KARANA).index in VISHTI or \
         sunset_zodiac.get_anga(zodiac.AngaType.KARANA).index in VISHTI):
        if sunrise_zodiac.get_anga(zodiac.AngaType.KARANA).index in VISHTI:
          karana_ID = sunrise_zodiac.get_anga(zodiac.AngaType.KARANA).index
        elif sunset_zodiac.get_anga(zodiac.AngaType.KARANA).index in VISHTI:
          karana_ID = sunset_zodiac.get_anga(zodiac.AngaType.KARANA).index
        self._assign_yoga('padmaka-yOga-puNyakAlaH', [(zodiac.AngaType.KARANA, karana_ID), (zodiac.AngaType.YOGA, 17)],
                          jd_start=daily_panchaanga.jd_sunrise, jd_end=daily_panchaanga.jd_sunset)
        # self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='padmaka-yOga-puNyakAlaH', interval=Interval(jd_start=None, jd_end=None)), date=daily_panchaanga.date)

      if daily_panchaanga.date.get_weekday() == 0 and \
        (sunrise_zodiac.get_anga(zodiac.AngaType.TITHI).index % 30 == 6 and
            sunset_zodiac.get_anga(zodiac.AngaType.TITHI).index % 30 == 7):
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='padmaka-yOgaH-2', interval=Interval(jd_start=None, jd_end=None)), date=daily_panchaanga.date)

    self._assign_yoga('padmaka-yOgaH-3', [(zodiac.AngaType.SOLAR_NAKSH, 16), (zodiac.AngaType.NAKSHATRA, 3)],
                      jd_start=self.panchaanga.jd_start, jd_end=self.panchaanga.jd_end)

  def assign_mahodaya_ardhodaya(self):
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):

      # MAHODAYAM
      # Can also refer youtube video https://youtu.be/0DBIwb7iaLE?list=PL_H2LUtMCKPjh63PRk5FA3zdoEhtBjhzj&t=6747
      # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Bhanuvasara = Ardhodayam
      # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Somavasara = Mahodayam
      sunrise_zodiac = NakshatraDivision(daily_panchaanga.jd_sunrise, ayanaamsha_id=self.computation_system.ayanaamsha_id)
      sunset_zodiac = NakshatraDivision(daily_panchaanga.jd_sunset, ayanaamsha_id=self.computation_system.ayanaamsha_id)
      if daily_panchaanga.lunar_date.month.index in [10, 11] and (daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 30 or tithi.get_tithi(daily_panchaanga.jd_sunrise).index == 30):
        if (sunrise_zodiac.get_anga(zodiac.AngaType.YOGA).index == 17 or sunset_zodiac.get_anga(zodiac.AngaType.YOGA).index == 17) and \
            (sunrise_zodiac.get_anga(zodiac.AngaType.NAKSHATRA).index == 22 or  sunset_zodiac.get_anga(zodiac.AngaType.NAKSHATRA).index == 22):
          if daily_panchaanga.date.get_weekday() == 1:
            festival_name = 'mahOdaya-puNyakAlaH'
            self.panchaanga.add_festival(fest_id=festival_name, date=self.daily_panchaangas[d].date)
            # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))
          elif daily_panchaanga.date.get_weekday() == 0:
            festival_name = 'ardhOdaya-puNyakAlaH'
            self.panchaanga.add_festival(fest_id=festival_name, date=self.daily_panchaangas[d].date)
            # logging.debug('* %d-%02d-%02d> %s!' % (y, m, dt, festival_name))
      
  def assign_revati_dvadashi_yoga(self):
    if 'cAturmAsya-vrata-pAraNa-niSiddha-yOgaH' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      if daily_panchaanga.lunar_date.month.index == 8 and daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index in (11, 12):
        self._assign_yoga('cAturmAsya-vrata-pAraNa-niSiddha-yOgaH', [(zodiac.AngaType.NAKSHATRA_PADA, 108), (zodiac.AngaType.TITHI, 12)],
                      jd_start=daily_panchaanga.jd_sunrise, jd_end=daily_panchaanga.jd_sunset)
  
  def assign_anadhyayana_dvadashi_yoga(self):
    if 'anadhyAyaH~dvAdazI-yOgaH' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
        if daily_panchaanga.lunar_date.month.index in [4, 6, 8]:
          if daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 12 or self.daily_panchaangas[d + 1].sunrise_day_angas.tithi_at_sunrise.index == 12:
            for _nakshatra in [17, 22, 27]:
              self._assign_yoga('anadhyAyaH~dvAdazI-yOgaH', [(zodiac.AngaType.NAKSHATRA, _nakshatra), (zodiac.AngaType.TITHI, 12)], jd_start=daily_panchaanga.jd_sunrise - 1, jd_end=daily_panchaanga.jd_sunset + 2, show_debug_info=False)

  def assign_vaarunii_trayodashi(self):
    if 'vAruNI~trayOdazI' not in self.rules_collection.name_to_rule:
      return
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      tithi_sunrise = day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index
      tithi_sunset = day_panchaanga.sunrise_day_angas.get_anga_at_jd(jd=day_panchaanga.jd_sunset, anga_type=zodiac.AngaType.TITHI).index
      # VARUNI TRAYODASHI
      if day_panchaanga.lunar_date.month.index == 12 and (tithi_sunrise == 28 or tithi_sunset == 28):
        if day_panchaanga.date.get_weekday() == 6:
          if not self._assign_yoga('mahAmahAvAruNI~trayOdazI', [(zodiac.AngaType.NAKSHATRA, 24), (zodiac.AngaType.TITHI, 28), (zodiac.AngaType.YOGA, 23)], jd_start = day_panchaanga.jd_sunrise, jd_end = day_panchaanga.jd_next_sunrise):
            self._assign_yoga('mahAvAruNI~trayOdazI', [(zodiac.AngaType.NAKSHATRA, 24), (zodiac.AngaType.TITHI, 28)], jd_start = day_panchaanga.jd_sunrise, jd_end = day_panchaanga.jd_next_sunrise)
        else:
            self._assign_yoga('vAruNI~trayOdazI', [(zodiac.AngaType.NAKSHATRA, 24), (zodiac.AngaType.TITHI, 28)], jd_start = day_panchaanga.jd_sunrise, jd_end = day_panchaanga.jd_next_sunrise)

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
