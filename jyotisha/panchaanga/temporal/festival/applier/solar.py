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
    self.assign_sidereal_sankranti_punyakaala()
    self.assign_tropical_sankranti_punyakaala()
    self.assign_tropical_sankranti()
    self.assign_mahodaya_ardhodaya()
    self.assign_month_day_kaaradaiyan()
    self.assign_month_day_muDavan_muzhukku()
    self.assign_month_day_kuchela()
    self.assign_month_day_mesha_sankraanti()
    self.assign_vishesha_vyatipata()
    self.assign_agni_nakshatra()
    self.assign_garbhottam()
    self.assign_padmaka_yoga()


  def assign_pitr_dina(self):
    self.assign_gajachhaya_yoga()
    self.assign_sidereal_sankranti_punyakaala()
    self.assign_mahodaya_ardhodaya()
    self.assign_vishesha_vyatipata()


  def assign_sidereal_sankranti_punyakaala(self):
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

    PUNYA_KAALA = {1: (10, 10),  2: (16, 16),  3: (0, 60),
                   4: (30,  0),  5: (16, 16),  6: (0, 60),
                   7: (10, 10),  8: (16, 16),  9: (0, 60),
                  10: ( 0, 20), 11: (16, 16), 12: (0, 60)}
    SANKRANTI_PUNYAKALA_NAMES = {
        1: "mESa-saGkramaNa",
        2: "vRSabha-ravi-saGkramaNa-viSNupadI",
        3: "mithuna-ravi-saGkramaNa-SaDazIti",
        4: "karkaTa-saGkramaNa",
        5: "siMha-ravi-saGkramaNa-viSNupadI",
        6: "kanyA-ravi-saGkramaNa-SaDazIti",
        7: "tulA-saGkramaNa",
        8: "vRzcika-ravi-saGkramaNa-viSNupadI",
        9: "dhanUravi-saGkramaNa-SaDazIti",
        10: "makara-saGkramaNa",
        11: "kumbha-ravi-saGkramaNa-viSNupadI",
        12: "mIna-ravi-saGkramaNa-SaDazIti",
    }
    is_puurva_half_day = True
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition is not None:
        sankranti_id = self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month
        
        punya_kaala_str = SANKRANTI_PUNYAKALA_NAMES[sankranti_id] + '-puNyakAlaH'
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
          self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=punya_kaala_str, interval=Interval(jd_start=punya_kaala_start_jd, jd_end=punya_kaala_end_jd)), date=self.daily_panchaangas[fday].date)

        if sankranti_id not in [2, 5, 8, 11]: # these cases are redundant!
          saamaanya_punya_kaala_start_jd = jd_transition - 16 * 1/60
          saamaanya_punya_kaala_end_jd = jd_transition + 16 * 1/60
          saamaanya_punya_kaala_start_jd = max(saamaanya_punya_kaala_start_jd, self.daily_panchaangas[fday].jd_sunrise) 
          saamaanya_punya_kaala_end_jd = min(saamaanya_punya_kaala_end_jd, self.daily_panchaangas[fday].jd_sunset) 
          if saamaanya_punya_kaala_end_jd > saamaanya_punya_kaala_start_jd: 
            self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='ravi-saGkramaNa-puNyakAlaH', interval=Interval(jd_start=saamaanya_punya_kaala_start_jd, jd_end=saamaanya_punya_kaala_end_jd)), date=self.daily_panchaangas[fday].date)


  def assign_tropical_sankranti_punyakaala(self):
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

    PUNYA_KAALA = {1: (10, 10),  2: (16, 16),  3: (0, 60),
                   4: (30,  0),  5: (16, 16),  6: (0, 60),
                   7: (10, 10),  8: (16, 16),  9: (0, 60),
                  10: ( 0, 20), 11: (16, 16), 12: (0, 60)}
    TROPICAL_SANKRANTI_PUNYAKALA_NAMES = {
        1: "(sAyana)~viSu",
        2: "(sAyana)~viSNupadI",
        3: "(sAyana)~SaDazIti",
        4: "(sAyana)~dakSiNAyana",
        5: "(sAyana)~viSNupadI",
        6: "(sAyana)~SaDazIti",
        7: "(sAyana)~viSu",
        8: "(sAyana)~viSNupadI",
        9: "(sAyana)~SaDazIti",
        10: "(sAyana)~uttarAyaNa",
        11: "(sAyana)~viSNupadI",
        12: "(sAyana)~SaDazIti",
    }

    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].tropical_date_sunset.month_transition is not None:
        sankranti_id = self.daily_panchaangas[d + 1].tropical_date_sunset.month
        punya_kaala_str = TROPICAL_SANKRANTI_PUNYAKALA_NAMES[sankranti_id] + '-puNyakAlaH'
        jd_transition = self.daily_panchaangas[d].tropical_date_sunset.month_transition
        # TODO: convert carefully to relative nadikas!
        punya_kaala_start_jd = jd_transition - PUNYA_KAALA[sankranti_id][0] * 1/60
        punya_kaala_end_jd = jd_transition + PUNYA_KAALA[sankranti_id][1] * 1/60
        
        if self.daily_panchaangas[d - 1].jd_sunset < jd_transition < self.daily_panchaangas[d].jd_sunrise:
          fday = d - 1
        else:
          fday = d
        
        if sankranti_id == 10:
          if jd_transition > self.daily_panchaangas[fday].jd_sunset:
            fday += 1
            is_puurva_half_day = True
          else:
            is_puurva_half_day = jd_transition < self.daily_panchaangas[fday].day_length_based_periods.puurvaahna.jd_end
        elif sankranti_id == 4:
          if jd_transition > self.daily_panchaangas[fday].jd_sunset:
            is_puurva_half_day = False
          else:
            is_puurva_half_day = jd_transition < self.daily_panchaangas[fday].day_length_based_periods.puurvaahna.jd_end
        else:
            is_puurva_half_day = jd_transition < self.daily_panchaangas[fday].day_length_based_periods.puurvaahna.jd_end
        
        if is_puurva_half_day:
          half_day = 'pUrvAhNa'
          half_day_interval = self.daily_panchaangas[fday].day_length_based_periods.puurvaahna
        else:
          half_day = 'aparAhNa'
          half_day_interval = self.daily_panchaangas[fday].day_length_based_periods.aparaahna
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='sAyana-saGkramaNa-dina-%s-puNyakAlaH' % half_day, interval=half_day_interval), date=self.daily_panchaangas[fday].date)

        punya_kaala_start_jd = max(punya_kaala_start_jd, self.daily_panchaangas[fday].jd_sunrise) 
        punya_kaala_end_jd = min(punya_kaala_end_jd, self.daily_panchaangas[fday].jd_sunset) 
        if punya_kaala_end_jd > punya_kaala_start_jd:
          self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=punya_kaala_str, interval=Interval(jd_start=punya_kaala_start_jd, jd_end=punya_kaala_end_jd)), date=self.daily_panchaangas[fday].date)

        if sankranti_id not in [2, 5, 8, 11]: # these cases are redundant!
          saamaanya_punya_kaala_start_jd = jd_transition - 16 * 1/60
          saamaanya_punya_kaala_end_jd = jd_transition + 16 * 1/60
          
          saamaanya_punya_kaala_start_jd = max(saamaanya_punya_kaala_start_jd, self.daily_panchaangas[fday].jd_sunrise) 
          # if sankranti_id == 10 and saamaanya_punya_kaala_start_jd < jd_transition < saamaanya_punya_kaala_end_jd:
          #   saamaanya_punya_kaala_start_jd = jd_transition
          
          saamaanya_punya_kaala_end_jd = min(saamaanya_punya_kaala_end_jd, self.daily_panchaangas[fday].jd_sunset) 
          # if sankranti_id == 4 and saamaanya_punya_kaala_start_jd < jd_transition < saamaanya_punya_kaala_end_jd:
          #   saamaanya_punya_kaala_end_jd = jd_transition
          
          if saamaanya_punya_kaala_end_jd > saamaanya_punya_kaala_start_jd:
            self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='ravi-saGkramaNa-puNyakAlaH', interval=Interval(jd_start=saamaanya_punya_kaala_start_jd, jd_end=saamaanya_punya_kaala_end_jd)), date=self.daily_panchaangas[fday].date)

  def assign_tropical_sankranti(self):
    if 'mESa-viSu-puNyakAlaH' not in self.rules_collection.name_to_rule:
      return 
    RTU_MASA_NAMES = {
        1: "madhu-mAsaH/vasantaRtuH",
        2: "mAdhava-mAsaH",
        3: "zukra-mAsaH/grISmaRtuH",
        4: "zuci-mAsaH/dakSiNAyanam",
        5: "nabhO-mAsaH/varSaRtuH",
        6: "nabhasya-mAsaH",
        7: "iSa-mAsaH/zaradRtuH",
        8: "Urja-mAsaH",
        9: "sahO-mAsaH/hEmantaRtuH",
        10: "sahasya-mAsaH/uttarAyaNam",
        11: "tapO-mAsaH/ziziraRtuH",
        12: "tapasya-mAsaH",
    }

    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].tropical_date_sunset.month_transition is not None:
        jd_transition = self.daily_panchaangas[d].tropical_date_sunset.month_transition

        # Addsankranti
        masa_name = RTU_MASA_NAMES[(self.daily_panchaangas[d + 1].tropical_date_sunset.month - 1) % 12 + 1]
        if jd_transition < self.daily_panchaangas[d].jd_sunrise:
          fday = d - 1
        else:
          fday = d
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=masa_name, interval=Interval(jd_start=jd_transition, jd_end=None)), date=self.daily_panchaangas[fday].date)


  def assign_agni_nakshatra(self):
    if 'agninakSatra-ArambhaH' not in self.rules_collection.name_to_rule:
      return 

    # AGNI nakshatra
    # anga_finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.ayanaamsha_id, anga_type=zodiac.AngaType.SOLAR_NAKSH_PADA)

    # agni_jd_start, dummy = anga_finder.find(jd1=self.panchaanga.jd_start, jd2=self.panchaanga.jd_end, target_anga_id=7).to_tuple()
    # dummy, agni_jd_end = anga_finder.find(jd1=agni_jd_start, jd2=agni_jd_start + 30, target_anga_id=13).to_tuple()

    # fday = int(floor(agni_jd_start) - floor(self.daily_panchaangas[0].julian_day_start))
    # if agni_jd_start < self.daily_panchaangas[fday].jd_sunrise:
    #   fday -= 1
    # self.panchaanga.add_festival(fest_id='agninakSatra-ArambhaH', date=self.daily_panchaangas[fday].date)

    # fday = int(floor(agni_jd_end) - floor(self.daily_panchaangas[0].julian_day_start))
    # if agni_jd_end < self.daily_panchaangas[fday].jd_sunrise:
    #   fday -= 1
    # self.panchaanga.add_festival(fest_id='agninakSatra-samApanam', date=self.daily_panchaangas[fday].date)

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
          if self.daily_panchaangas[d].jd_sunset < agni_jd_start < self.daily_panchaangas[d + 1].jd_sunset:
            self.panchaanga.add_festival(fest_id='agninakSatra-ArambhaH', date=self.daily_panchaangas[d].date + 1)
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month == 2 and self.daily_panchaangas[d].solar_sidereal_date_sunset.day > 10:
        if agni_jd_end is not None:
          if self.daily_panchaangas[d].jd_sunrise < agni_jd_end < self.daily_panchaangas[d + 1].jd_sunrise:
            self.panchaanga.add_festival(fest_id='agninakSatra-samApanam', date=self.daily_panchaangas[d].date)

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
    # nava_nayakas['rAjA'] = names.NAMES['VARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][self.daily_panchaangas[self.panchaanga.festival_id_to_days['yugAdiH'][0]].date.get_weekday()]
    
    NAYAKA_MAP = {'mantrI': 1,
                  'sEnAdhipaH': 5,
                  'sasyAdhipaH': 4,
                  'dhAnyAdhipaH': 9,
                  'arghAdhipaH': 3,
                  'rasAdhipaH': 7,
                  'nIrasAdhipaH': 10}

    for d in range(self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition is not None:
        sankranti_id = self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month
        if sankranti_id == 1:
          mesha_start = self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition
        for nayaka in NAYAKA_MAP:
          if sankranti_id == NAYAKA_MAP[nayaka]:
            nava_nayakas[nayaka] = names.NAMES['VARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][self.daily_panchaangas[d].date.get_weekday()]

    finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=zodiac.AngaType.SIDEREAL_MONTH)
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

  def assign_month_day_muDavan_muzhukku(self):
    if 'muDavan2_muzhukku' not in self.rules_collection.name_to_rule:
      return
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      # KUCHELA DINAM
      if daily_panchaanga.solar_sidereal_date_sunset.month == 8 and daily_panchaanga.solar_sidereal_date_sunset.day == 1:
        if daily_panchaanga.solar_sidereal_date_sunset.month_transition is None or daily_panchaanga.solar_sidereal_date_sunset.month_transition < daily_panchaanga.jd_sunrise:
          self.panchaanga.add_festival(fest_id='muDavan2_muzhukku', date=daily_panchaanga.date)
        else:
          self.panchaanga.add_festival(fest_id='muDavan2_muzhukku', date=self.daily_panchaangas[d + 1].date)

  def _assign_yoga(self, yoga_name, intersect_list, jd_start=None, jd_end=None):
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
        msg = ' + '.join(['%s %d' % (intersect_list[i][0], intersect_list[i][1]) for i in range(len(intersect_list))])
        logging.debug('No %s involving %s in span %s!' % (msg, yoga_name, Interval(jd_start=jd_start_in, jd_end=jd_end_in)))
      else:
        fday = int(floor(jd_start) - floor(self.daily_panchaangas[0].julian_day_start))
        if (jd_start < self.daily_panchaangas[fday].jd_sunrise):
          fday -= 1
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=yoga_name, interval=Interval(jd_start=jd_start, jd_end=jd_end)), date=self.daily_panchaangas[fday].date)


  def assign_month_day_mesha_sankraanti(self):
    if 'mESa-saGkrAntiH' not in self.rules_collection.name_to_rule:
      return 
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      # MESHA SANKRANTI
      if daily_panchaanga.solar_sidereal_date_sunset.month == 1 and self.daily_panchaangas[d - 1].solar_sidereal_date_sunset.month == 12:
        # distance from prabhava
        samvatsara_id = (daily_panchaanga.date.year - 1568) % 60 + 1
        new_yr = 'mESa-saGkrAntiH' + '~(' + names.NAMES['SAMVATSARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][
          (samvatsara_id % 60) + 1] + \
                 '-' + 'saMvatsaraH' + ')'
        # self.panchaanga.festival_id_to_days[new_yr] = [d]
        self.panchaanga.add_festival(fest_id=new_yr, date=self.daily_panchaangas[d].date)
        self.panchaanga.add_festival(fest_id='paJcAGga-paThanam', date=self.daily_panchaangas[d].date)
        self.panchaanga.add_festival(fest_id='viSukkan2i', date=self.daily_panchaangas[d].date)
        # if daily_panchaanga.solar_sidereal_date_sunset.month_transition is None or daily_panchaanga.solar_sidereal_date_sunset.month_transition < daily_panchaanga.jd_sunrise:
        #   self.panchaanga.add_festival(fest_id='viSukkan2i', date=daily_panchaanga.date)
        # else:
        #   self.panchaanga.add_festival(fest_id='viSukkan2i', date=self.daily_panchaangas[d + 1].date)

  def assign_vishesha_vyatipata(self):
    vs_list = copy(self.panchaanga.festival_id_to_days.get('vyatIpAta-zrAddham', []))
    for date in vs_list:
      if self.panchaanga.date_str_to_panchaanga[date.get_date_str()].solar_sidereal_date_sunset.month == 9:
        self.panchaanga.delete_festival_date(fest_id='vyatIpAta-zrAddham', date=date)
        festival_name = 'mahAdhanurvyatIpAta-zrAddham'
        self.panchaanga.add_festival(fest_id=festival_name, date=date)
      elif self.panchaanga.date_str_to_panchaanga[date.get_date_str()].lunar_month_sunrise.index == 6:
        self.panchaanga.delete_festival_date(fest_id='vyatIpAta-zrAddham', date=date)
        self.panchaanga.add_festival(fest_id='mahAvyatIpAta-zrAddham', date=date)

  def assign_gajachhaya_yoga(self):
    if 'gajacchAyA-yOgaH' not in self.rules_collection.name_to_rule:
      return 
    self._assign_yoga('gajacchAyA-yOgaH', [(zodiac.AngaType.SOLAR_NAKSH, 13), (zodiac.AngaType.NAKSHATRA, 10), (zodiac.AngaType.TITHI, 28)],
                      jd_start=self.panchaanga.jd_start, jd_end=self.panchaanga.jd_end)
    self._assign_yoga('gajacchAyA-yOgaH', [(zodiac.AngaType.SOLAR_NAKSH, 13), (zodiac.AngaType.NAKSHATRA, 13), (zodiac.AngaType.TITHI, 30)],
                      jd_start=self.panchaanga.jd_start, jd_end=self.panchaanga.jd_end)

  def assign_padmaka_yoga(self):
    if 'padmaka-yOgaH-1' not in self.rules_collection.name_to_rule:
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
        self._assign_yoga('padmaka-yOgaH-1', [(zodiac.AngaType.KARANA, karana_ID), (zodiac.AngaType.YOGA, 17)],
                          jd_start=daily_panchaanga.jd_sunrise, jd_end=daily_panchaanga.jd_sunset)
        # self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='padmaka-yOgaH-1', interval=Interval(jd_start=None, jd_end=None)), date=daily_panchaanga.date)

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
      if daily_panchaanga.lunar_month_sunrise.index in [10, 11] and (daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 30 or tithi.get_tithi(daily_panchaanga.jd_sunrise).index == 30):
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
      

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
