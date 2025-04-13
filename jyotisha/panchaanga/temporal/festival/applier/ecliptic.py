import os
import sys
from math import floor
import logging

import swisseph as swe

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
    self.set_other_graha_transits()
    # for graha in (Graha.MERCURY, Graha.VENUS, Graha.MARS, Graha.JUPITER, Graha.SATURN):
    #   self.add_maudhya_events(graha)
    # self.add_graha_yuddhas()
    
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
    if self.panchaanga.computation_system.festival_options.tropical_month_start == 'mAdhava_at_equinox':
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
    else:
      RTU_MASA_TAGS = {
        1: "/vasantaRtuH",
        2: "",
        3: "/grISmaRtuH",
        4: "/dakSiNAyanam",
        5: "/varSaRtuH",
        6: "",
        7: "/zaradRtuH",
        8: "",
        9: "/hEmantaRtuH",
        10: "/uttarAyaNam",
        11: "/ziziraRtuH",
        12: "",
      }
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      if self.daily_panchaangas[d].tropical_date_sunset.month_transition is not None:
        jd_transition = self.daily_panchaangas[d].tropical_date_sunset.month_transition

        # Addsankranti
        if self.panchaanga.computation_system.festival_options.tropical_month_start == 'mAdhava_at_equinox':
          masa_id = self.daily_panchaangas[d + 1].tropical_date_sunset.month
        else:
          masa_id = (self.daily_panchaangas[d + 1].tropical_date_sunset.month - 2) % 12 + 1
        masa_name = names.NAMES['RTU_MASA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][masa_id] + RTU_MASA_TAGS[masa_id]
        if jd_transition < self.daily_panchaangas[d].jd_sunrise:
          fday = d - 1
        else:
          fday = d
        self.panchaanga.add_festival_instance(festival_instance=FestivalInstance(name=masa_name, interval=Interval(jd_start=jd_transition, jd_end=None)), date=self.daily_panchaangas[fday].date)

  def is_retrograde(self, graha: int, jd: float) -> bool:
    """
    Check if a graha is retrograde at a given Julian day.
    :param graha: Graha constant (e.g., Graha.SUN, Graha.MOON, etc.)
    :param jd: Julian day
    :return: True if the graha is retrograde, False otherwise
    """
    g = Graha.singleton(graha)
    return g.get_speed(jd) < 0

  def get_setting_direction(self, graha: int, jd: float) -> str:
    """
    Get the setting direction of a graha at a given Julian day.
    :param graha: Graha constant (e.g., Graha.VENUS, Graha.JUPITER, etc.)
    :param jd: Julian day
    :return: "prAk" if the graha sets in the east, "pratyak" if it sets in the west
    """
    CALC_SET = swe.CALC_SET | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
    geo_lon = self.panchaanga.city.longitude
    geo_lat = self.panchaanga.city.latitude
    graha = Graha.singleton(graha)._get_swisseph_id()
    rs = swe.rise_trans(jd, body=graha, geopos=[geo_lon, geo_lat, 0], rsmi=CALC_SET)[1]
    az = rs[3]
    #TODO: Fix this!
    return "prAk" if az < 180 else "pratyak"

  def get_rising_direction(self, graha: int, jd: float) -> str:
    """
    Get the rising direction of a graha at a given Julian day.
    :param graha: Graha constant (e.g., Graha.VENUS, Graha.JUPITER, etc.)
    :param jd: Julian day
    :return: "prAk" if the graha rises in the east, "pratyak" if it rises in the west
    """
    CALC_RISE = swe.CALC_RISE | swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION
    geo_lon = self.panchaanga.city.longitude
    geo_lat = self.panchaanga.city.latitude
    graha = Graha.singleton(graha)._get_swisseph_id()
    rs = swe.rise_trans(jd, body=graha, geopos=[geo_lon, geo_lat, 0], rsmi=CALC_RISE)[1]
    az = rs[3]
    #TODO: Fix this!
    return "prAk" if az < 180 else "pratyak"

 
  def compute_maudhya_intervals(self, graha: int, jd_start: float, jd_end: float, step: float = 0.5) -> list[tuple[float, float, str, str]]:
    """
    Compute combustion (maudhya) intervals for a graha between jd_start and jd_end.
    Each interval includes:
      - setting direction at the start (t_start)
      - rising direction at the end (t_end)
    """
    MAUDHYA_LIMITS = {
        Graha.MERCURY: {'prograde': 14.0, 'retrograde': 12.0},
        Graha.VENUS: {'prograde': 10.0, 'retrograde': 8.0},
        Graha.MARS: {'prograde': 17.0, 'retrograde': 17.0},
        Graha.JUPITER: {'prograde': 11.0, 'retrograde': 11.0},
        Graha.SATURN: {'prograde': 15.0, 'retrograde': 15.0},
    }

    is_retro = self.is_retrograde(graha, jd_start)
    delta = MAUDHYA_LIMITS[graha]["retrograde" if is_retro else "prograde"]

    conjunction_intervals = self.compute_conjunction_intervals(
        graha1=graha,
        graha2=Graha.SUN,
        jd_start=jd_start,
        jd_end=jd_end,
        delta=delta,
        step=step
    )
    
    intervals = []
    
    for t_start, t_zero, t_end in conjunction_intervals:
        try:
            dir_set = self.get_setting_direction(graha, t_start)
            dir_rise = self.get_rising_direction(graha, t_end)
            intervals.append((t_start, t_end, dir_rise, dir_set))
        except Exception as e:
            logging.warning(f"Could not determine directions for maudhya interval ({t_start}, {t_end}): {e}")
    return intervals


  def add_maudhya_events(self, graha: int):
    GRAHA_NAMES = {Graha.VENUS: 'zukraH', Graha.MERCURY: 'budhaH', Graha.MARS: 'aGgArakaH', 
        Graha.SATURN: 'zaniH', Graha.JUPITER: 'guruH'}
    maudhya_intervals = self.compute_maudhya_intervals(graha, self.panchaanga.jd_start, self.panchaanga.jd_end)
    for t_start, t_end, dir_rise, dir_set in maudhya_intervals:
        try:
            fday = int(t_start - self.daily_panchaangas[0].julian_day_start)
            if t_start < self.daily_panchaangas[fday].jd_sunrise:
                fday -= 1
            self.panchaanga.add_festival_instance(FestivalInstance(
                name=f"{GRAHA_NAMES[graha]}–astamayaH ({dir_set})",
                interval=Interval(jd_start=t_start, jd_end=None)
            ), date=self.daily_panchaangas[fday].date)
        except ValueError:
            logging.warning("Could not assign festival day for maudhya start event.")
        try:
          fday = int(t_end - self.daily_panchaangas[0].julian_day_start)
          if t_end < self.daily_panchaangas[fday].jd_sunrise:
            fday -= 1
          self.panchaanga.add_festival_instance(FestivalInstance(
              name=f"{GRAHA_NAMES[graha]}–udayaH ({dir_rise})",
              interval=Interval(jd_start=None, jd_end=t_end)
          ), date=self.daily_panchaangas[fday].date)
        except ValueError:
          logging.warning("Could not assign festival day for maudhya end event.")

  def compute_conjunction_intervals(
    self,
    graha1: int,
    graha2: int,
    jd_start: float,
    jd_end: float,
    delta: float = 1.0,
    step: float = 0.5,
    debug: bool = False
    ) -> list[tuple[float, float, float]]:
    """
    Compute intervals where the longitude difference between two grahas is less than `delta`.
    Returns a list of (t_start, t_zero, t_end) tuples.
    """
    g1 = Graha.singleton(graha1)
    g2 = Graha.singleton(graha2)
    intervals = []

    inside = False
    t_start = None
    jd = jd_start

    while jd <= jd_end:
        lon_diff = abs(g1.get_longitude(jd, ayanaamsha_id=self.ayanaamsha_id) - g2.get_longitude(jd, ayanaamsha_id=self.ayanaamsha_id))
        lon_diff = min(lon_diff, 360 - lon_diff)  # shortest arc

        if not inside and lon_diff < delta:
            try:
                t_start = brentq(
                    lambda x: abs(g1.get_longitude(x, ayanaamsha_id=self.ayanaamsha_id) - g2.get_longitude(x, ayanaamsha_id=self.ayanaamsha_id)) - delta,
                    jd - step,
                    jd
                )
                inside = True
            except ValueError:
                logging.warning(f"Could not bracket start of proximity at {jd}")
        elif inside and lon_diff > delta:
            try:
                t_end = brentq(
                    lambda x: abs(g1.get_longitude(x, ayanaamsha_id=self.ayanaamsha_id) - g2.get_longitude(x, ayanaamsha_id=self.ayanaamsha_id)) - delta,
                    jd - step,
                    jd
                )
                # Now compute t_zero (exact conjunction)
                try:
                    t_zero = brentq(
                        lambda x: g1.get_longitude(x, ayanaamsha_id=self.ayanaamsha_id) - g2.get_longitude(x, ayanaamsha_id=self.ayanaamsha_id),
                        t_start,
                        t_end
                    )
                    intervals.append((t_start, t_zero, t_end))
                except ValueError:
                    logging.warning(f"Could not find t_zero between {t_start} and {t_end}")
                inside = False
            except ValueError:
                logging.warning(f"Could not bracket end of proximity at {jd}")
        jd += step

    if debug:
      # Show the longitudes of each graha at the start and end of the interval
      logging.debug(f"Intervals for {graha1} and {graha2}:")
      for t_start, t_zero, t_end in intervals:
          logging.debug(f"  Interval   : {Interval(jd_start=t_start, jd_end=t_end)}")
          logging.debug(f"  Conjunction: {Interval(jd_start=t_zero, jd_end=t_zero)}")
          logging.debug(f"  Start: t_start, {g1.get_longitude(t_start, ayanaamsha_id=self.ayanaamsha_id)}, {g2.get_longitude(t_start, ayanaamsha_id=self.ayanaamsha_id)}")
          logging.debug(f"  End: t_end, {g1.get_longitude(t_end, ayanaamsha_id=self.ayanaamsha_id)}, {g2.get_longitude(t_end, ayanaamsha_id=self.ayanaamsha_id)}")

    return intervals
  
  def add_graha_yuddhas(self):
    TARA_GRAHAS = (Graha.MERCURY, Graha.VENUS, Graha.MARS, Graha.JUPITER, Graha.SATURN)
    GRAHA_NAMES = {Graha.VENUS: 'zukraH', Graha.MERCURY: 'budhaH', Graha.MARS: 'aGgArakaH', 
        Graha.SATURN: 'zaniH', Graha.JUPITER: 'guruH'}

    for graha1 in TARA_GRAHAS:
      for graha2 in TARA_GRAHAS:
        if graha1 < graha2:
          intervals = self.compute_conjunction_intervals(graha1, graha2, self.panchaanga.jd_start, self.panchaanga.jd_end, delta=1.0, debug=False)
          for t_start, t_zero, t_end in intervals:
            # Check for Maudhya!
            if t_start is not None and self.panchaanga.jd_start < t_start < self.panchaanga.jd_end:
              fday = int(t_start - self.daily_panchaangas[0].julian_day_start)
              if t_start < self.daily_panchaangas[fday].jd_sunrise:
                fday -= 1
              fest = FestivalInstance(
                  name=f'graha-yuddhaH ({GRAHA_NAMES[graha1]}–{GRAHA_NAMES[graha2]})',
                  interval=Interval(jd_start=t_start, jd_end=t_end)
              )
              self.panchaanga.add_festival_instance(fest, date=self.daily_panchaangas[fday].date)

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
      # logging.debug(next_eclipse_lun)
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
          if jd_transit < self.daily_panchaangas[fday].jd_sunrise:
            fday -= 1
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

  def set_other_graha_transits(self):
    if 'guru-saGkrAntiH' not in self.rules_collection.name_to_rule:
      return 
    jd_end = self.panchaanga.jd_start + self.panchaanga.duration 
    GRAHA_NAMES = {Graha.VENUS: 'zukraH', Graha.MERCURY: 'budhaH', Graha.MARS: 'aGgArakaH', 
        Graha.SATURN: 'zaniH', Graha.RAHU: 'rAhuH', Graha.KETU: 'kEtuH'}
    
    for graha in Graha.MERCURY, Graha.VENUS, Graha.MARS, Graha.SATURN, Graha.RAHU, Graha.KETU:
      transits = Graha.singleton(graha).get_transits(self.panchaanga.jd_start, jd_end, anga_type=AngaType.RASHI,
                                                           ayanaamsha_id=self.ayanaamsha_id)
      if len(transits) > 0:
        for i, transit in enumerate(transits):
          (jd_transit, rashi1, rashi2) = (transit.jd, transit.value_1, transit.value_2)
          if self.panchaanga.jd_start < jd_transit < jd_end:
            fday = int(jd_transit - self.daily_panchaangas[0].julian_day_start)
            if jd_transit < self.daily_panchaangas[fday].jd_sunrise:
              fday -= 1
            fest = TransitionFestivalInstance(name='%s-saGkrAntiH' % GRAHA_NAMES[graha][:-1],
              status_1_hk=names.NAMES['RASHI_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi1], 
              status_2_hk=names.NAMES['RASHI_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi2], interval
              =Interval(jd_start=jd_transit, jd_end=None))
            self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[fday].date)



MIN_DAYS_NEXT_ECLIPSE = 25

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
