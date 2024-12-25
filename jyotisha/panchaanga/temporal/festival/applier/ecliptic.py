import os
import sys
from math import floor
import logging
from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.temporal import interval
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival import FestivalInstance, TransitionFestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import AngaType
from scipy.optimize import brentq
from sanskrit_data.schema import common
from indic_transliteration import sanscript

class EclipticFestivalAssigner(FestivalAssigner):
  def assign_all(self):
    self.set_jupiter_transits()
    self.compute_solar_eclipses()
    self.compute_lunar_eclipses()
    self.assign_tropical_sankranti_punyakaala()
    self.assign_tropical_sankranti()
    # for graha1 in [Graha.MOON, Graha.JUPITER, Graha.VENUS, Graha.MERCURY, Graha.MARS, Graha.SATURN, Graha.RAHU]:
    #   for graha2 in [Graha.MOON, Graha.JUPITER, Graha.VENUS, Graha.MERCURY, Graha.MARS, Graha.SATURN, Graha.RAHU]:
    #     if graha1 > graha2:
    #       self.compute_conjunctions(graha1, graha2)

  def assign_tropical_sankranti_punyakaala(self):
    if 'viSu-puNyakAlaH' not in self.rules_collection.name_to_rule:
      return

    fname = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/misc_data/sankranti_punyakaala.toml')
    with open(fname) as f:
      import toml
      punyakaala_dict = toml.load(f)

      PUNYA_KAALA = {int(s): punyakaala_dict['PUNYA_KAALA'][s] for s in punyakaala_dict['PUNYA_KAALA']}

    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].tropical_date_sunset.month_transition is not None:
        sankranti_id = (self.daily_panchaangas[d + 1].tropical_date_sunset.month - 2) % 12 + 1
        punya_kaala_str = names.NAMES['TROPICAL_SANKRANTI_PUNYAKALA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][sankranti_id] + '-puNyakAlaH'
        if sankranti_id%3 != 1:
          # Except for Ayana/Vishuva, add sAyana tag!
          punya_kaala_str = 'sAyana-' + punya_kaala_str
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
        else:
          self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=punya_kaala_str, interval=Interval(jd_start=None, jd_end=None)),
                                                date=self.daily_panchaangas[fday].date)

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
            self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name='sAyana-ravi-saGkramaNa-puNyakAlaH', interval=Interval(jd_start=saamaanya_punya_kaala_start_jd, jd_end=saamaanya_punya_kaala_end_jd)), date=self.daily_panchaangas[fday].date)

  def assign_tropical_sankranti(self):
    if 'viSu-puNyakAlaH' not in self.rules_collection.name_to_rule:
      return
    RTU_MASA_TAGS = {
      1: "/vasantaRtuH",
      2: "",
      3: "/grISmaRtuH",
      4: "",
      5: "/varSaRtuH/dakSiNAyanam",
      6: "",
      7: "/zaradRtuH",
      8: "",
      9: "/hEmantaRtuH",
      10: "",
      11: "/ziziraRtuH/uttarAyaNam",
      12: "",
    }

    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].tropical_date_sunset.month_transition is not None:
        jd_transition = self.daily_panchaangas[d].tropical_date_sunset.month_transition

        # Addsankranti
        masa_id = (self.daily_panchaangas[d + 1].tropical_date_sunset.month - 1) % 12 + 1
        masa_name = names.NAMES['RTU_MASA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][masa_id] + RTU_MASA_TAGS[masa_id]
        if jd_transition < self.daily_panchaangas[d].jd_sunrise:
          fday = d - 1
        else:
          fday = d
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=masa_name, interval=Interval(jd_start=jd_transition, jd_end=None)), date=self.daily_panchaangas[fday].date)

  def compute_conjunctions(self, Graha1, Graha2, delta=0.0):
    # Compute the time of conjunction between Graha1 and Graha2
    GRAHA_NAMES = {Graha.SUN: 'sUryaH', Graha.MOON: 'candraH', Graha.JUPITER: 'guruH',
        Graha.VENUS: 'zukraH', Graha.MERCURY: 'budhaH', Graha.MARS: 'aGgArakaH', 
        Graha.SATURN: 'zanaizcaraH', Graha.RAHU: 'rAhuH'}
    if delta == 0.0:
      try:
        t = brentq(lambda jd: Graha.singleton(Graha1).get_longitude(jd) - Graha.singleton(Graha2).get_longitude(jd),
                 self.panchaanga.jd_start, self.panchaanga.jd_end)
      except ValueError:
        t = None
        logging.error('Not able to bracket!')
        
      if t is not None and self.panchaanga.jd_start < t < self.panchaanga.jd_end:
        fday = [self.daily_panchaangas[i].jd_sunrise < t < self.daily_panchaangas[i + 1].jd_sunrise for i in range(self.panchaanga.duration)].index(True)
        fest = FestivalInstance(name='graha-yuddhaH (%s–%s)' % (GRAHA_NAMES[Graha1], GRAHA_NAMES[Graha2]), interval=Interval(jd_start=None, jd_end=t))
        self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[fday].date)
    else:
      # mauDhya / combustion with some degrees assigned
      try:
        t_start = brentq(lambda jd: Graha.singleton(Graha1).get_longitude(jd) - Graha.singleton(Graha2).get_longitude(jd) - delta,
                 self.panchaanga.jd_start, self.panchaanga.jd_end)
      except ValueError:
        t_start = None
        logging.error('Not able to bracket!')

      try:
        t_end = brentq(lambda jd: Graha.singleton(Graha1).get_longitude(jd) - Graha.singleton(Graha2).get_longitude(jd) + delta,
                 self.panchaanga.jd_start, self.panchaanga.jd_end)
      except ValueError:
        t_end = None
        logging.error('Not able to bracket!')

      if t_start is not None and self.panchaanga.jd_start < t_start < self.panchaanga.jd_end:
        fday = [self.daily_panchaangas[i].jd_sunrise < t_start < self.daily_panchaangas[i + 1].jd_sunrise for i in range(self.panchaanga.duration)].index(True)
        fest = FestivalInstance(name='%s–mauDhya' % GRAHA_NAMES[Graha1], interval=Interval(jd_start=t_start, jd_end=None))
        self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[fday].date)

      if t_end is not None and self.panchaanga.jd_start < t_end < self.panchaanga.jd_end:
        fday = [self.daily_panchaangas[i].jd_sunrise < t_end < self.daily_panchaangas[i + 1].jd_sunrise for i in range(self.panchaanga.duration)].index(True)
        fest = FestivalInstance(name='%s–mauDhya' % GRAHA_NAMES[Graha1], interval=Interval(jd_start=None, jd_end=t_end))
        self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[fday].date)


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
        fday = int(jd_eclipse_solar_end - self.daily_panchaangas[0].julian_day_start)
        suff = 'a'
        if (jd_eclipse_solar_start < self.daily_panchaangas[fday].jd_sunrise):
          # Grastodaya
          suff = 'Odaya'
          jd_eclipse_solar_start = self.daily_panchaangas[fday].jd_sunrise
        if jd_eclipse_solar_end > self.daily_panchaangas[fday].jd_sunset:
          # Grastastamana
          suff = 'Astamana'
          jd_eclipse_solar_end = self.daily_panchaangas[fday].jd_sunset
        if jd_eclipse_solar_start == 0.0 or jd_eclipse_solar_end == 0.0:
          # Move towards the next eclipse... at least the next new
          # moon (>=25 days away)
          jd += MIN_DAYS_NEXT_ECLIPSE
          continue
        if abs (Graha.singleton(Graha.SUN).get_longitude(jd_eclipse_solar_end) - Graha.singleton(Graha.RAHU).get_longitude(
            jd_eclipse_solar_end)) < 5:
          grasta = 'rAhugrast'
        else:
          grasta = 'kEtugrast'
        solar_eclipse_str = 'sUrya-grahaNaM~(' + grasta + suff + ')'
        if self.daily_panchaangas[fday].date.get_weekday() == 0:
          solar_eclipse_str = '★cUDAmaNi-' + solar_eclipse_str
        fest = FestivalInstance(name=solar_eclipse_str, interval=Interval(jd_start=jd_eclipse_solar_start, jd_end=jd_eclipse_solar_end))
      self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[fday].date)
      jd = jd + MIN_DAYS_NEXT_ECLIPSE

  def compute_lunar_eclipses(self):
    if '★cUDAmaNi-candra-grahaNam' not in self.rules_collection.name_to_rule:
      return
      # Set location
    jd = self.panchaanga.jd_start
    
    while 1:
      next_eclipse_lun = self.panchaanga.city.get_lunar_eclipse_time(jd)
      logging.debug(next_eclipse_lun)
      jd = next_eclipse_lun[1][0]
      jd_eclipse_lunar_start = next_eclipse_lun[1][2]
      jd_eclipse_lunar_end = next_eclipse_lun[1][3]

      if jd > self.panchaanga.jd_end:
        break

      if jd_eclipse_lunar_start == 0.0 and jd_eclipse_lunar_end == 0.0:
        # 0.0 is returned in case of eclipses when the moon is below the horizon.
        # Move towards the next eclipse... at least the next full
        # moon (>=25 days away)
        jd += MIN_DAYS_NEXT_ECLIPSE
        continue

      suff = 'a'
      if jd_eclipse_lunar_start != 0.0 and jd_eclipse_lunar_end != 0.0:
        # Regular eclipse
        # fday = int(floor(jd_eclipse_lunar_start) - floor(self.panchaanga.jd_start) + 1)
        fday = int(jd_eclipse_lunar_start - self.daily_panchaangas[0].julian_day_start)
      elif jd_eclipse_lunar_start == 0.0:
        # Grastodaya
        suff = 'Odaya'
        jd_eclipse_lunar_start = self.panchaanga.city.get_rising_time(julian_day_start=jd_eclipse_lunar_end - 0.5, body=Graha.MOON)
      elif jd_eclipse_lunar_end == 0.0:
        # Grastastamana
        suff = 'Astamana'
        jd_eclipse_lunar_end = self.panchaanga.city.get_setting_time(julian_day_start=jd_eclipse_lunar_start, body=Graha.MOON)

      # fday = int(floor(jd_eclipse_lunar_start) - floor(self.panchaanga.jd_start) + 1)
      fday = int(jd_eclipse_lunar_start - self.daily_panchaangas[0].julian_day_start)
      if jd_eclipse_lunar_start < self.daily_panchaangas[fday].jd_sunrise:
        fday -= 1
      
      # print '%%', jd, fday, self.date_str_to_panchaanga[fday].jd_sunrise,
      # self.date_str_to_panchaanga[fday-1].jd_sunrise, eclipse_lunar_start,
      # eclipse_lunar_end
      
      if Graha.singleton(Graha.MOON).get_longitude(jd_eclipse_lunar_end) < Graha.singleton(Graha.SUN).get_longitude(
          jd_eclipse_lunar_end):
        grasta = 'rAhugrast'
      else:
        grasta = 'kEtugrast'

      grasta += suff

      lunar_eclipse_str = 'candra-grahaNam~(' + grasta + ')'
      if self.daily_panchaangas[fday].date.get_weekday() == 1:
        lunar_eclipse_str = '★cUDAmaNi-' + lunar_eclipse_str

      fest = FestivalInstance(name=lunar_eclipse_str, interval=Interval(jd_start=jd_eclipse_lunar_start, jd_end=jd_eclipse_lunar_end))
      logging.warning(f'Lunar eclipse: {jd_eclipse_lunar_start} → {jd_eclipse_lunar_end}')
      self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[fday].date)
      jd += MIN_DAYS_NEXT_ECLIPSE

  def set_jupiter_transits(self):
    if 'guru-saGkrAntiH' not in self.rules_collection.name_to_rule:
      return 
    jd_end = self.panchaanga.jd_start + self.panchaanga.duration + 13
    check_window = 400  # Max t between two Jupiter transits is ~396 (checked across 180y)
    # Let's check for transitions in a relatively large window
    # to finalise what is the FINAL transition post retrograde movements
    transits = Graha.singleton(Graha.JUPITER).get_transits(self.panchaanga.jd_start - 13, jd_end + check_window, anga_type=AngaType.RASHI,
                                                           ayanaamsha_id=self.ayanaamsha_id)
    if len(transits) > 0:
      for i, transit in enumerate(transits):
        (jd_transit, rashi1, rashi2) = (transit.jd, transit.value_1, transit.value_2)
        if self.panchaanga.jd_start - 13 < jd_transit < jd_end:
          fday = int(jd_transit - self.daily_panchaangas[0].julian_day_start)
          # if jd_transit < self.daily_panchaangas[fday].julian_day_start:
          #   fday -= 1
          fest = TransitionFestivalInstance(name='guru-saGkrAntiH', 
            status_1_hk=names.NAMES['RASHI_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi1], 
            status_2_hk=names.NAMES['RASHI_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi2], interval
            =Interval(jd_start=jd_transit, jd_end=None))
          self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[fday].date)
          if (rashi1 % 12 + 1) == rashi2 and ((transits[i + 1].value_1 % 12) + 1) == transits[i + 1].value_2:
            # Considering only non-retrograde transits for pushkara computations
            # logging.debug('Non-retrograde transit; we have a pushkaram!')
            (madhyanha_start, madhyaahna_end) = interval.get_interval(self.daily_panchaangas[fday].jd_sunrise,
                                                                                                   self.daily_panchaangas[fday].jd_sunset, 2, 5).to_tuple()
            if jd_transit < madhyaahna_end:
              fday_pushkara = fday
            else:
              fday_pushkara = fday + 1
            self.panchaanga.add_festival(
              fest_id='%s-Adya-puSkara-ArambhaH' % names.NAMES['PUSHKARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi2], date=self.daily_panchaangas[fday_pushkara].date)
            self.panchaanga.add_festival(
              fest_id='%s-Adya-puSkara-samApanam' % names.NAMES['PUSHKARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi2], date=self.daily_panchaangas[fday_pushkara].date + 11)
            self.panchaanga.add_festival(
              fest_id='%s-antya-puSkara-samApanam' % names.NAMES['PUSHKARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi1], date=self.daily_panchaangas[fday_pushkara].date - 1)
            self.panchaanga.add_festival(
              fest_id='%s-antya-puSkara-ArambhaH' % names.NAMES['PUSHKARA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi1], date=self.daily_panchaangas[fday_pushkara].date - 12)


MIN_DAYS_NEXT_ECLIPSE = 25

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
