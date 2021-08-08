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
    # self.assign_padmaka_yoga()


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

    PUNYA_KAALA = {1: (10, 10), 2: (16, 16), 3: (0, 60), 4: (30, 0), 5: (16, 16), 6: (0, 60),
                   7: (10, 10), 8: (16, 16), 9: (0, 60), 10: (0, 20), 11: (16, 16), 12: (0, 60)}
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
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition is not None:
        punya_kaala_str = SANKRANTI_PUNYAKALA_NAMES[self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month] + '-puNyakAlaH'
        jd_transition = self.daily_panchaangas[d].solar_sidereal_date_sunset.month_transition
        # TODO: convert carefully to relative nadikas!
        punya_kaala_start_jd = jd_transition - PUNYA_KAALA[self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month][0] * 1/60
        punya_kaala_end_jd = jd_transition + PUNYA_KAALA[self.daily_panchaangas[d + 1].solar_sidereal_date_sunset.month][1] * 1/60
        if punya_kaala_start_jd < self.daily_panchaangas[d].julian_day_start:
          fday = d - 1
        else:
          fday = d
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=punya_kaala_str, interval=Interval(jd_start=punya_kaala_start_jd, jd_end=punya_kaala_end_jd)), date=self.daily_panchaangas[fday].date)


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

    PUNYA_KAALA = {1: (10, 10), 2: (16, 16), 3: (0, 60), 4: (30, 0), 5: (16, 16), 6: (0, 60),
                   7: (10, 10), 8: (16, 16), 9: (0, 60), 10: (0, 20), 11: (16, 16), 12: (0, 60)}
    TROPICAL_SANKRANTI_PUNYAKALA_NAMES = {
        1: "mESa-viSu",
        2: "viSNupadI",
        3: "SaDazIti",
        4: "dakSiNAyana",
        5: "viSNupadI",
        6: "SaDazIti",
        7: "tulA-viSu",
        8: "viSNupadI",
        9: "SaDazIti",
        10: "uttarAyaNa",
        11: "viSNupadI",
        12: "SaDazIti",
    }

    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].tropical_date_sunset.month_transition is not None:
        # Add punyakala
        punya_kaala_str = TROPICAL_SANKRANTI_PUNYAKALA_NAMES[self.daily_panchaangas[d + 1].tropical_date_sunset.month] + '-puNyakAlaH'
        jd_transition = self.daily_panchaangas[d].tropical_date_sunset.month_transition
        # TODO: convert carefully to relative nadikas!
        punya_kaala_start_jd = jd_transition - PUNYA_KAALA[self.daily_panchaangas[d + 1].tropical_date_sunset.month][0] * 1/60
        punya_kaala_end_jd = jd_transition + PUNYA_KAALA[self.daily_panchaangas[d + 1].tropical_date_sunset.month][1] * 1/60
        if punya_kaala_start_jd < self.daily_panchaangas[d].julian_day_start:
          fday = d - 1
        else:
          fday = d
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=punya_kaala_str, interval=Interval(jd_start=punya_kaala_start_jd, jd_end=punya_kaala_end_jd)), date=self.daily_panchaangas[fday].date)


  def assign_tropical_sankranti(self):
    if 'mESa-viSu-puNyakAlaH' not in self.rules_collection.name_to_rule:
      return 
    RTU_MASA_NAMES = {
        1: "madhu-mAsaH",
        2: "mAdhava-mAsaH/vasantaRtuH",
        3: "zukra-mAsaH/uttarAyaNam",
        4: "zuci-mAsaH/grISmaRtuH",
        5: "nabhO-mAsaH",
        6: "nabhasya-mAsaH/varSaRtuH",
        7: "iSa-mAsaH",
        8: "Urja-mAsaH/zaradRtuH",
        9: "sahO-mAsaH/dakSiNAyanam",
        10: "sahasya-mAsaH/hEmantaRtuH",
        11: "tapO-mAsaH",
        12: "tapasya-mAsaH/ziziraRtuH",
    }

    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].tropical_date_sunset.month_transition is not None:
        jd_transition = self.daily_panchaangas[d].tropical_date_sunset.month_transition

        # Add tropical sankranti
        masa_name = RTU_MASA_NAMES[(self.daily_panchaangas[d + 1].tropical_date_sunset.month - 2) % 12 + 1]
        if jd_transition < self.daily_panchaangas[d].jd_sunrise:
          fday = d - 1
        else:
          fday = d
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=masa_name, interval=Interval(jd_start=None, jd_end=jd_transition)), date=self.daily_panchaangas[fday].date)


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
      ####################
      # Festival details #
      ####################

      # KARADAIYAN NOMBU
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
        if daily_panchaanga.solar_sidereal_date_sunset.month_transition is None or daily_panchaanga.solar_sidereal_date_sunset.month_transition < daily_panchaanga.jd_sunrise:
          self.panchaanga.add_festival(fest_id='viSukkan2i', date=daily_panchaanga.date)
        else:
          self.panchaanga.add_festival(fest_id='viSukkan2i', date=self.daily_panchaangas[d + 1].date)

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

    intersect_lists = [((zodiac.AngaType.SOLAR_NAKSH, 13), (zodiac.AngaType.NAKSHATRA, 10), (zodiac.AngaType.TITHI, 28)),
                       ((zodiac.AngaType.SOLAR_NAKSH, 13), (zodiac.AngaType.NAKSHATRA, 13), (zodiac.AngaType.TITHI, 30))]
    for intersect_list in intersect_lists:
      jd_start = self.panchaanga.jd_start
      jd_end = self.panchaanga.jd_end
      anga_list = []
      gc_yoga = True
      for anga_type, target_anga_id in intersect_list:
        finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=anga_type)
        anga = finder.find(jd1 = jd_start, jd2=jd_end, target_anga_id=target_anga_id)
        anga_list.append(anga)
        if anga is None:
            logging.debug('No Gajacchhaya Yoga involving %s %d + %s %d this year!' % (intersect_list[1][0], intersect_list[1][1], intersect_list[2][0], intersect_list[2][1]))
            gc_yoga = False
            break
        if anga.jd_start is not None:
            jd_start = anga.jd_start - 5 
        if anga.jd_end is not None:
            jd_end = anga.jd_end + 5
      if gc_yoga:
        jd_start, jd_end = max([x.jd_start for x in anga_list]), min([x.jd_end for x in anga_list])
        if jd_start > jd_end:
            logging.debug('No Gajacchhaya Yoga involving %s %d + %s %d this year!' % (intersect_list[1][0], intersect_list[1][1], intersect_list[2][0], intersect_list[2][1]))
        else:
          fday = int(floor(jd_start) - floor(self.daily_panchaangas[0].julian_day_start))
          if (jd_start < self.daily_panchaangas[fday].jd_sunrise):
            fday -= 1
          self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='gajacchAyA-yOgaH', interval=Interval(jd_start=jd_start, jd_end=jd_end)), date=self.daily_panchaangas[fday].date)

  def assign_padmaka_yoga(self):
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):
      # यदा विष्टिर्व्यतीपातो भानुवारस्तथैव च॥
      # पद्मको नाम योगोयमयनादेश्चतुर्गुणः॥ (धर्मसिन्धौ पृ ३००)
      VISHTI = [8, 15, 22, 29, 36, 43, 50, 57]
      sunrise_zodiac = NakshatraDivision(daily_panchaanga.jd_sunrise, ayanaamsha_id=self.computation_system.ayanaamsha_id)
      sunset_zodiac = NakshatraDivision(daily_panchaanga.jd_sunset, ayanaamsha_id=self.computation_system.ayanaamsha_id)
      if daily_panchaanga.date.get_weekday() == 0 and \
        (sunrise_zodiac.get_anga(zodiac.AngaType.YOGA).index == 17 or 
            sunset_zodiac.get_anga(zodiac.AngaType.YOGA).index == 17) and \
        (sunrise_zodiac.get_anga(zodiac.AngaType.KARANA).index in VISHTI or \
         sunset_zodiac.get_anga(zodiac.AngaType.KARANA).index in VISHTI):
        # TODO: Check for overlap between VISHTI & Vyatipata!
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='padmaka-yOgaH-1', interval=Interval(jd_start=None, jd_end=None)), date=daily_panchaanga.date)

      if daily_panchaanga.date.get_weekday() == 0 and \
        (sunrise_zodiac.get_anga(zodiac.AngaType.TITHI).index % 30 == 6 and
            sunset_zodiac.get_anga(zodiac.AngaType.TITHI).index % 30 == 7):
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='padmaka-yOgaH-2', interval=Interval(jd_start=None, jd_end=None)), date=daily_panchaanga.date)

    intersect_lists = [((zodiac.AngaType.SOLAR_NAKSH, 16), (zodiac.AngaType.NAKSHATRA, 3))]
    for intersect_list in intersect_lists:
      jd_start = self.panchaanga.jd_start
      jd_end = self.panchaanga.jd_end
      anga_list = []
      pk_yoga_3 = True
      for anga_type, target_anga_id in intersect_list:
        finder = zodiac.AngaSpanFinder.get_cached(ayanaamsha_id=self.computation_system.ayanaamsha_id, anga_type=anga_type)
        anga = finder.find(jd1 = jd_start, jd2=jd_end, target_anga_id=target_anga_id)
        anga_list.append(anga)
        if anga is None:
            logging.debug('No Padmaka Yoga involving %s %d + %s %d this year!' % (intersect_list[1][0], intersect_list[1][1], intersect_list[2][0], intersect_list[2][1]))
            pk_yoga_3 = False
            break
        if anga.jd_start is not None:
            jd_start = anga.jd_start - 5 
        if anga.jd_end is not None:
            jd_end = anga.jd_end + 5
      if pk_yoga_3:
        jd_start, jd_end = max([x.jd_start for x in anga_list]), min([x.jd_end for x in anga_list])
        if jd_start > jd_end:
            logging.debug('No Padmaka Yoga involving %s %d + %s %d this year!' % (intersect_list[1][0], intersect_list[1][1], intersect_list[2][0], intersect_list[2][1]))
        else:
          fday = int(floor(jd_start) - floor(self.daily_panchaangas[0].julian_day_start))
          if (jd_start < self.daily_panchaangas[fday].jd_sunrise):
            fday -= 1
          self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='padmaka-yOgaH-3', interval=Interval(jd_start=jd_start, jd_end=jd_end)), date=self.daily_panchaangas[fday].date)

  def assign_mahodaya_ardhodaya(self):
    for d, daily_panchaanga in enumerate(self.daily_panchaangas):

      # MAHODAYAM
      # Can also refer youtube video https://youtu.be/0DBIwb7iaLE?list=PL_H2LUtMCKPjh63PRk5FA3zdoEhtBjhzj&t=6747
      # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Bhanuvasara = Ardhodayam
      # 4th pada of vyatipatam, 1st pada of Amavasya, 2nd pada of Shravana, Suryodaya, Somavasara = Mahodayam
      sunrise_zodiac = NakshatraDivision(daily_panchaanga.jd_sunrise, ayanaamsha_id=self.computation_system.ayanaamsha_id)
      sunset_zodiac = NakshatraDivision(daily_panchaanga.jd_sunset, ayanaamsha_id=self.computation_system.ayanaamsha_id)
      if daily_panchaanga.lunar_month_sunrise.index in [10, 11] and daily_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == 30 or tithi.get_tithi(daily_panchaanga.jd_sunrise).index == 30:
        if sunrise_zodiac.get_anga(zodiac.AngaType.YOGA).index == 17 or \
            sunset_zodiac.get_anga(zodiac.AngaType.YOGA).index == 17 and \
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
