import os
import sys
from math import floor
import logging

import swisseph as swe

from jyotisha.panchaanga.temporal import names
from jyotisha.panchaanga.temporal import interval
from jyotisha.panchaanga.temporal import zodiac
from jyotisha.panchaanga.temporal.body import Graha, oblique_ascension
from jyotisha.panchaanga.temporal.festival import FestivalInstance, TransitionFestivalInstance
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.interval import Interval
from jyotisha.panchaanga.temporal.zodiac import AngaType
from scipy.optimize import brentq, minimize_scalar
from sanskrit_data.schema import common
from indic_transliteration import sanscript

GRAHA_NAMES = {Graha.SUN: 'sUryaH', Graha.MOON: 'candraH', Graha.VENUS: 'zukraH', Graha.MERCURY: 'budhaH', Graha.MARS: 'aGgArakaH',
    Graha.SATURN: 'zaniH', Graha.JUPITER: 'guruH'}

# Dedicated logger (and log file) for graha-yuddha, maudhya etc. events -- see
# EclipticFestivalAssigner.get_graha_events_log_path()/add_graha_events_log_handler().
graha_events_logger = logging.getLogger('jyotisha.graha_events')
graha_events_logger.setLevel(logging.INFO)


class EclipticFestivalAssigner(FestivalAssigner):
  def assign_all(self):
    self.set_jupiter_transits()
    self.compute_solar_eclipses()
    self.compute_lunar_eclipses()
    self.assign_tropical_sankranti_punyakaala()
    self.assign_tropical_sankranti()
    self.set_other_graha_transits()
    for graha in (Graha.MERCURY, Graha.VENUS, Graha.MARS, Graha.JUPITER, Graha.SATURN):
      self.add_maudhya_events(graha)
    self.add_graha_yuddhas()
    # Force computation, mirroring the old assign_chandra_darshanam_legacy()
    # call in TithiFestivalAssigner: assign_bodhaayana_amaavaasyaa() (which
    # runs later, in TithiFestivalAssigner.assign_all()) needs
    # festival_id_to_days['candra-darzanam'] regardless of whether the user's
    # ruleset actually wants candra-darzanam reported; it deletes the festival
    # again at the end if not.
    self.assign_chandra_darshanam(force_computation=True)


  def assign_tropical_sankranti_punyakaala(self):
    if 'viSu-puNyakAlaH' not in self.rules_collection.name_to_rule:
      return
    
    fname = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/misc_data/sankranti_punyakaala.toml')
    with open(fname) as f:
      import toml
      punyakaala_dict = toml.load(f)

      PUNYA_KAALA = {int(s): punyakaala_dict['PUNYA_KAALA'][s] for s in punyakaala_dict['PUNYA_KAALA']}

    tropical_transition_jds = [self.daily_panchaangas[d].tropical_date_sunset.month_transition for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding) if self.daily_panchaangas[d].tropical_date_sunset.month_transition is not None]

    for jd_transition in tropical_transition_jds:
      if not (self.panchaanga.jd_start <= jd_transition <= self.panchaanga.jd_end):
        continue

      for d_pos in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
        if self.daily_panchaangas[d_pos].jd_sunrise < jd_transition < self.daily_panchaangas[d_pos].jd_next_sunrise:
          d = d_pos
          break

      sankranti_id = (self.daily_panchaangas[d + 1].tropical_date_sunset.month - 2) % 12 + 1
      punya_kaala_str = names.NAMES['TROPICAL_SANKRANTI_PUNYAKALA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][sankranti_id] + '-puNyakAlaH'
      if sankranti_id%3 != 1:
        # Except for Ayana/Vishuva, add sAyana tag!
        punya_kaala_str = 'sAyana-' + punya_kaala_str
      
      # TODO: convert carefully to relative nadikas!
      punya_kaala_start_jd = jd_transition - PUNYA_KAALA[sankranti_id][0] * 1/60
      punya_kaala_end_jd = jd_transition + PUNYA_KAALA[sankranti_id][1] * 1/60

      if jd_transition < self.daily_panchaangas[d].day_length_based_periods.fifteen_fold_division.aahneya.jd_end:
        fday = d
        is_puurva_half_day = jd_transition < self.daily_panchaangas[d].day_length_based_periods.puurvaahna.jd_end
        if sankranti_id == 10: # Uttarayana
          if jd_transition < self.daily_panchaangas[d].jd_sunset:
            fday = d
            is_puurva_half_day = jd_transition < self.daily_panchaangas[d].day_length_based_periods.puurvaahna.jd_end
          else:
            fday = d + 1
            is_puurva_half_day = True
      else:
        if sankranti_id == 4:
          fday = d # Previous day only for Dakshinayana
          is_puurva_half_day = jd_transition < self.daily_panchaangas[d].day_length_based_periods.puurvaahna.jd_end
        else:
          if jd_transition > self.daily_panchaangas[d].day_length_based_periods.fifteen_fold_division.vaidhaatra.jd_end:
            # logging.debug('Crossed vaidhaatra')
            fday = d + 1
            is_puurva_half_day = True
          else:
            # Decide based on tithi at sunset being same as tithi at transit
            # logging.debug('Deciding based on tithi at sunset and transit')
            if sankranti_id % 3 == 0: 
              fday = d + 1
              is_puurva_half_day = True
            else:
              tithi_sunset = self.daily_panchaangas[d].sunrise_day_angas.get_anga_at_jd(jd=self.daily_panchaangas[d].jd_sunset, anga_type=zodiac.AngaType.TITHI).index
              tithi_transit = self.daily_panchaangas[d].sunrise_day_angas.get_anga_at_jd(jd=jd_transition, anga_type=zodiac.AngaType.TITHI).index
              if tithi_sunset == tithi_transit:
                fday = d
                is_puurva_half_day = False
              else:
                fday = d + 1
                is_puurva_half_day = True

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

 
  def compute_maudhya_intervals(self, graha: int, jd_start: float, jd_end: float, step: float = 0.5, use_latitude: bool = False) -> list[tuple[float, float, float, str, str]]:
    """
    Compute combustion (maudhya) intervals for a graha between jd_start and jd_end.
    Each interval includes:
      - setting direction at the start (t_start)
      - rising direction at the end (t_end)

    :param use_latitude: see compute_conjunction_intervals - applies the
      akSAMza (observer-latitude, oblique-ascension) correction rather than
      plain ecliptic longitude. This is the empirically-verified convention
      used by drik-gaNita candra-darzanam tables and is recommended whenever
      self.panchaanga.city is meaningful for the event (definitely for Moon;
      likely appropriate for the other grahas too, though only validated
      against a reference table for Moon so far).
    """
    MAUDHYA_LIMITS = {
        Graha.MERCURY: {'prograde': 14.0, 'retrograde': 12.0},
        Graha.VENUS: {'prograde': 10.0, 'retrograde': 8.0},
        Graha.MARS: {'prograde': 17.0, 'retrograde': 17.0},
        Graha.JUPITER: {'prograde': 11.0, 'retrograde': 11.0},
        Graha.SATURN: {'prograde': 15.0, 'retrograde': 15.0},
        Graha.MOON: {'prograde': 12.0, 'retrograde': 12.0},
    }

    limits = MAUDHYA_LIMITS[graha]
    # Prograde/retrograde state (and hence the applicable delta) can differ
    # from one conjunction to the next within [jd_start, jd_end], so we can't
    # just check it once at jd_start. Scan wide first (using the looser of
    # the two limits) to bracket every conjunction, then re-bracket each one
    # individually with the delta that actually applies to it.
    scan_delta = max(limits['prograde'], limits['retrograde'])
    candidate_intervals = self.compute_conjunction_intervals(
        graha1=graha,
        graha2=Graha.SUN,
        jd_start=jd_start,
        jd_end=jd_end,
        delta=scan_delta,
        step=step,
        use_latitude=use_latitude
    )

    conjunction_intervals = []
    for t_start, t_zero, t_end in candidate_intervals:
        is_retro = self.is_retrograde(graha, t_zero)
        delta = limits["retrograde" if is_retro else "prograde"]
        if delta == scan_delta:
            conjunction_intervals.append((t_start, t_zero, t_end))
            continue
        # delta is narrower than scan_delta: re-bracket within the
        # already-found (wider) window using the correct, narrower delta.
        refined = self.compute_conjunction_intervals(
            graha1=graha,
            graha2=Graha.SUN,
            jd_start=t_start,
            jd_end=t_end,
            delta=delta,
            step=step,
            use_latitude=use_latitude
        )
        if refined:
            conjunction_intervals.append(refined[0])
        else:
            logging.warning(f"Could not refine maudhya interval near jd={t_zero} for {graha} with delta={delta}")

    intervals = []

    for t_start, t_zero, t_end in conjunction_intervals:
        try:
            dir_set = self.get_setting_direction(graha, t_start)
            dir_rise = self.get_rising_direction(graha, t_end)
            intervals.append((t_start, t_zero, t_end, dir_rise, dir_set))
        except Exception as e:
            logging.warning(f"Could not determine directions for maudhya interval ({t_start}, {t_end}): {e}")
    return intervals


  def add_maudhya_events(self, graha: int, log_path=None):
    log_path = self.add_graha_events_log_handler(log_path)
    # use_latitude=True: apply the akSAMza (observer-latitude, oblique-ascension)
    # correction - see compute_conjunction_intervals docstring. This is the
    # empirically-validated convention, and applies uniformly to every graha,
    # Chandra included, not just the five star-planets.
    maudhya_intervals = self.compute_maudhya_intervals(graha, self.panchaanga.jd_start, self.panchaanga.jd_end, use_latitude=True)
    for t_start, t_zero, t_end, dir_rise, dir_set in maudhya_intervals:
        details = self.get_graha_yuddha_details(graha, Graha.SUN, t_zero)
        graha_events_logger.info(self.format_graha_event_report(
            event_label=f"maudhyam ({GRAHA_NAMES[graha]})", graha1=graha, graha2=Graha.SUN, jd=t_zero,
            details=details, include_winner=False))
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

  def assign_chandra_darshanam(self, force_computation=False):
    """
    candra-darzanam (new-crescent visibility): the first evening the Moon
    clears the Sun by the maudhya threshold (12deg, akSAMza/oblique-ascension
    corrected for self.panchaanga.city.latitude) - see compute_maudhya_intervals.
    Empirically validated to the minute against a real drik-gaNita reference
    table. Supersedes TithiFestivalAssigner.assign_chandra_darshanam_legacy()'s
    tithi-at-moonset heuristic, which is retained there for reference.
    """
    if 'candra-darzanam' not in self.rules_collection.name_to_rule and not force_computation:
      return
    maudhya_intervals = self.compute_maudhya_intervals(Graha.MOON, self.panchaanga.jd_start, self.panchaanga.jd_end, use_latitude=True)
    for t_start, t_zero, t_end, dir_rise, dir_set in maudhya_intervals:
      try:
        fday = int(t_end - self.daily_panchaangas[0].julian_day_start)
        if t_end < self.daily_panchaangas[fday].jd_sunrise:
          fday -= 1
        if t_end > self.daily_panchaangas[fday].jd_sunset:
          # This panchaanga-day's sunset has already passed by t_end (the Moon
          # hadn't cleared the akSAMza threshold yet that evening) - the first
          # upcoming viewing opportunity is the following evening.
          fday += 1
        fest_name = 'candra-darzanam'
        if self.daily_panchaangas[fday].lunar_date.month.index == 6:
          fest_name = 'bhAdrapada-' + fest_name
        fest = FestivalInstance(
            name=fest_name,
            interval=Interval(jd_start=self.daily_panchaangas[fday].jd_sunset, jd_end=self.daily_panchaangas[fday].graha_set_jd[Graha.MOON])
        )
        self.panchaanga.add_festival_instance(festival_instance=fest, date=self.daily_panchaangas[fday].date)
      except (ValueError, IndexError):
        logging.warning(f"Could not assign candra-darzanam for maudhya interval ending {t_end}.")

  def compute_conjunction_intervals(
    self,
    graha1: int,
    graha2: int,
    jd_start: float,
    jd_end: float,
    delta: float = 1.0,
    step: float = 0.5,
    debug: bool = False,
    use_latitude: bool = False
    ) -> list[tuple[float, float, float]]:
    """
    Compute intervals where the angular separation between two grahas is less than `delta`.
    Returns a list of (t_start, t_zero, t_end) tuples.

    :param use_latitude: If False (default), separation is just the ecliptic
      longitude difference (kranti-vRtta convention). If True, the entry/exit
      boundaries (t_start/t_end) are instead found using the difference in
      oblique ascension (OA = RA - asin(tan(dec)*tan(observer_latitude))) at
      self.panchaanga.city.latitude - the standard akSAMza (observer-latitude)
      correction for rise/set-relative, site-dependent phenomena like
      combustion visibility. This is NOT the same as correcting for a graha's
      own ecliptic latitude (vikSepa/zara), which is a geocentric, observer-
      independent quantity and is the wrong correction for this purpose - see
      https://groups.io/g/swisseph/message/710 . The conjunction instant
      t_zero is always the same-ecliptic-longitude moment, regardless of this
      flag.
    """
    g1 = Graha.singleton(graha1)
    g2 = Graha.singleton(graha2)
    intervals = []

    def wrapped_longitude_diff(jd):
        # Signed difference in (-180, 180], avoiding the 0deg/360deg wraparound
        # bug that raw subtraction has near conjunction/opposition boundaries.
        diff = g1.get_longitude(jd, ayanaamsha_id=self.ayanaamsha_id) - g2.get_longitude(jd, ayanaamsha_id=self.ayanaamsha_id)
        return (diff + 180) % 360 - 180

    def separation(jd):
        if not use_latitude:
            return abs(wrapped_longitude_diff(jd))
        observer_latitude = self.panchaanga.city.latitude
        ra1, dec1 = g1.get_ra_dec(jd)
        ra2, dec2 = g2.get_ra_dec(jd)
        oa1 = oblique_ascension(ra1, dec1, observer_latitude)
        oa2 = oblique_ascension(ra2, dec2, observer_latitude)
        return abs((oa1 - oa2 + 180) % 360 - 180)

    inside = False
    t_start = None
    jd = jd_start

    while jd <= jd_end:
        sep = separation(jd)

        if not inside and sep < delta:
            try:
                t_start = brentq(lambda x: separation(x) - delta, jd - step, jd)
                inside = True
            except ValueError:
                logging.warning(f"Could not bracket start of proximity at {jd}")
        elif inside and sep > delta:
            try:
                t_end = brentq(lambda x: separation(x) - delta, jd - step, jd)
                # Now compute t_zero (exact conjunction), always longitude-based.
                try:
                    t_zero = brentq(wrapped_longitude_diff, t_start, t_end)
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
  
  def get_angular_separation(self, graha1: int, graha2: int, jd: float) -> float:
    """
    True angular separation (degrees) between two grahas, accounting for both
    longitude and ecliptic latitude. Graha-yuddha (amshu-vimarda) is defined
    by proximity of the two discs, not merely by longitude, so latitude must
    be taken into account to identify the interval and moment of conflict
    correctly.

    Uses topocentric (parallax-corrected, for self.panchaanga.city) positions
    rather than geocentric ones -- graha-yuddha is a locally-observed
    phenomenon, and parallax (mainly affecting the nearer of the two grahas)
    can shift the moment of closest apparent approach measurably.
    """
    g1 = Graha.singleton(graha1)
    g2 = Graha.singleton(graha2)
    city = self.panchaanga.city
    lon1, lat1 = g1.get_topocentric_lon_lat(jd, city.longitude, city.latitude, ayanaamsha_id=self.ayanaamsha_id)
    lon2, lat2 = g2.get_topocentric_lon_lat(jd, city.longitude, city.latitude, ayanaamsha_id=self.ayanaamsha_id)
    dlon = ((lon1 - lon2 + 180) % 360) - 180
    dlat = lat1 - lat2
    return (dlon ** 2 + dlat ** 2) ** 0.5

  def compute_yuddha_intervals(self, graha1: int, graha2: int, jd_start: float, jd_end: float, delta: float = 1.0, step: float = 0.5) -> list[tuple[float, float, float]]:
    """
    Compute intervals during which the true angular separation (see
    get_angular_separation) between two grahas is less than `delta` degrees,
    together with the jd of closest approach (t_zero) within each interval.
    Returns a list of (t_start, t_zero, t_end) tuples.
    """
    intervals = []
    inside = False
    t_start = None
    jd = jd_start

    def sep(x):
      return self.get_angular_separation(graha1, graha2, x)

    while jd <= jd_end:
      d = sep(jd)
      if not inside and d < delta:
        try:
          t_start = brentq(lambda x: sep(x) - delta, jd - step, jd)
          inside = True
        except ValueError:
          logging.warning(f"Could not bracket start of graha-yuddha at {jd}")
      elif inside and d > delta:
        try:
          t_end = brentq(lambda x: sep(x) - delta, jd - step, jd)
          t_zero = minimize_scalar(sep, bounds=(t_start, t_end), method='bounded').x
          intervals.append((t_start, t_zero, t_end))
        except ValueError:
          logging.warning(f"Could not bracket end of graha-yuddha at {jd}")
        inside = False
      jd += step
    return intervals

  @staticmethod
  def format_dms(value_degrees: float) -> str:
    """Format an angle (in degrees) as D°MM′SS.SS″."""
    total_sec = abs(value_degrees) * 3600
    d = int(total_sec // 3600)
    m = int((total_sec % 3600) // 60)
    s = total_sec % 60
    return f"{d}°{m:02d}′{s:05.2f}″"

  @staticmethod
  def format_arcmin(value_degrees: float) -> str:
    """Format an angle (in degrees, expected to be small) as MM′SS.SS″ (arcminutes not wrapped modulo 60)."""
    total_sec = abs(value_degrees) * 3600
    m = int(total_sec // 60)
    s = total_sec % 60
    return f"{m}′{s:05.2f}″"

  def get_graha_yuddha_details(self, graha1: int, graha2: int, jd: float) -> dict:
    """
    Compute the full set of graha-yuddha (amshu-vimarda) details at the
    moment `jd` of closest approach between graha1 and graha2: their
    center-to-center and disc-to-disc (edge-to-edge) separation, and for each
    graha: (topocentric) longitude (with nakshatra/pada/rashi), latitude,
    motion (gati, direct/retrograde), apparent angular diameter (with
    increasing/decreasing trend), apparent magnitude, and elongation from
    the sun.

    The graha with the larger apparent diameter (i.e. nearer the earth, and
    hence brighter/more prominent) is taken to be the victor (jayI) -- per
    the classical criterion that the smaller, fainter graha is defeated.
    """
    details = {'separation': self.get_angular_separation(graha1, graha2, jd)}
    dt = 0.01
    city = self.panchaanga.city
    sun_lon, _ = Graha.singleton(Graha.SUN).get_topocentric_lon_lat(jd, city.longitude, city.latitude, ayanaamsha_id=self.ayanaamsha_id)
    for graha in (graha1, graha2):
      g = Graha.singleton(graha)
      lon, lat = g.get_topocentric_lon_lat(jd, city.longitude, city.latitude, ayanaamsha_id=self.ayanaamsha_id)
      speed = g.get_speed(jd)
      elongation, diameter, magnitude = g.get_phenomena(jd, geo_lon=city.longitude, geo_lat=city.latitude)
      _, diameter_next, _ = g.get_phenomena(jd + dt, geo_lon=city.longitude, geo_lat=city.latitude)
      nak_index = int(lon // zodiac.AngaType.NAKSHATRA.arc_length) + 1
      pada = int((lon % zodiac.AngaType.NAKSHATRA.arc_length) // (zodiac.AngaType.NAKSHATRA.arc_length / 4)) + 1
      rashi_index = int(lon // zodiac.AngaType.RASHI.arc_length) + 1
      elong_diff = ((lon - sun_lon + 180) % 360) - 180
      details[graha] = {
          'longitude': lon,
          'nakshatra': names.NAMES['NAKSHATRA_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][nak_index],
          'pada': pada,
          'rashi': names.NAMES['RASHI_NAMES']['sa'][sanscript.roman.HK_DRAVIDIAN][rashi_index],
          'latitude': lat,
          'lat_dir': 'S' if lat < 0 else 'N',
          'speed': speed,
          'motion': 'vakra' if speed < 0 else 'Rju',
          'diameter': diameter,
          'diameter_trend': 'increasing' if diameter_next > diameter else 'decreasing',
          'magnitude': magnitude,
          'elongation': elongation,
          'elong_dir': 'W' if elong_diff < 0 else 'E',
      }
    # Disc (rim-to-rim) separation: center-to-center separation minus the sum
    # of the two angular radii -- the actual visible gap between the discs,
    # as opposed to 'separation' above (a center-to-center distance).
    details['disc_separation'] = details['separation'] - (details[graha1]['diameter'] + details[graha2]['diameter']) / 2
    details['winner'] = graha1 if details[graha1]['diameter'] >= details[graha2]['diameter'] else graha2
    details['loser'] = graha2 if details['winner'] == graha1 else graha1
    return details

  def get_graha_events_log_path(self) -> str:
    """Default path for the graha-events (maudhya, graha-yuddha, ...) log file."""
    city_str = self.panchaanga.city.name.replace(' ', '_').replace('/', '_')
    fname = f"{city_str}_{self.panchaanga.start_date.year}-{self.panchaanga.end_date.year}_graha_events.log"
    return os.path.join(os.getcwd(), fname)

  def add_graha_events_log_handler(self, log_path: str = None) -> str:
    """
    Ensure graha_events_logger writes to `log_path` (or get_graha_events_log_path()
    if not given), and return the path used. Safe to call repeatedly -- a given
    file is only attached once.
    """
    log_path = os.path.abspath(log_path or self.get_graha_events_log_path())
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_path for h in graha_events_logger.handlers):
      os.makedirs(os.path.dirname(log_path), exist_ok=True)
      handler = logging.FileHandler(log_path)
      handler.setFormatter(logging.Formatter('%(message)s'))
      graha_events_logger.addHandler(handler)
    return log_path

  def format_graha_event_report(self, event_label: str, graha1: int, graha2: int, jd: float, details: dict, include_winner: bool = True) -> str:
    """
    Render `details` (as returned by get_graha_yuddha_details) as a
    human-readable multi-line report, in the spirit of:

      Date: 2021-Mar-05 08:57 -
        Amshuvimarda ,   0°19'42.70" separation
        Guru   , lat:    0°35'08.87" S
                 gati:     13'28.59" riju
                 dia:       0'32.48" increasing
        ...
        Elongation:     27°13'32.29" W
    """
    tz = self.panchaanga.city.get_timezone_obj()
    disc_sep = details['disc_separation']
    disc_sep_str = ("overlapping by " + self.format_dms(disc_sep)) if disc_sep < 0 else self.format_dms(disc_sep)
    lines = [
        f"{event_label}",
        f"Date: {tz.julian_day_to_local_time_str(jd)} -",
        f"  Separation (center-to-center): {self.format_dms(details['separation'])}",
        f"  Separation (disc/edge-to-edge): {disc_sep_str}",
    ]
    for graha in (graha1, graha2):
      d = details[graha]
      name = GRAHA_NAMES.get(graha, graha)
      lines.append(f"  {name}, longitude: {self.format_dms(d['longitude'])} {d['nakshatra']}-{d['pada']} {d['rashi']}")
      lines.append(f"           lat: {self.format_dms(d['latitude'])} {d['lat_dir']}")
      lines.append(f"           gati: {self.format_arcmin(d['speed'])} {d['motion']}")
      lines.append(f"           dia: {self.format_arcmin(d['diameter'])} {d['diameter_trend']}")
      lines.append(f"           magnitude: {d['magnitude']:+.2f}")
      lines.append(f"           elongation: {self.format_dms(d['elongation'])} {d['elong_dir']}")
    if include_winner:
      lines.append(f"  jayI (victor): {GRAHA_NAMES.get(details['winner'], details['winner'])}")
    return "\n".join(lines) + "\n"

  def add_graha_yuddhas(self, log_path=None):
    TARA_GRAHAS = (Graha.MERCURY, Graha.VENUS, Graha.MARS, Graha.JUPITER, Graha.SATURN)
    log_path = self.add_graha_events_log_handler(log_path)

    for graha1 in TARA_GRAHAS:
      for graha2 in TARA_GRAHAS:
        if graha1 < graha2:
          intervals = self.compute_yuddha_intervals(graha1, graha2, self.panchaanga.jd_start, self.panchaanga.jd_end, delta=1.0)
          for t_start, t_zero, t_end in intervals:
            if not (self.panchaanga.jd_start < t_zero < self.panchaanga.jd_end):
              continue
            fday = int(t_zero - self.daily_panchaangas[0].julian_day_start)
            if t_zero < self.daily_panchaangas[fday].jd_sunrise:
              fday -= 1

            details = self.get_graha_yuddha_details(graha1, graha2, t_zero)
            graha_events_logger.info(self.format_graha_event_report(
                event_label=f"graha-yuddhaH ({GRAHA_NAMES[graha1]}-{GRAHA_NAMES[graha2]})", graha1=graha1, graha2=graha2,
                jd=t_zero, details=details))

            fest = FestivalInstance(
                name=f"graha-yuddhaH~(★{GRAHA_NAMES[details['winner']]}-{GRAHA_NAMES[details['loser']]})",
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
            jd_eclipse_solar_end)) < 10:
          grasta = 'rAhumukhagrast'
        else:
          grasta = 'rAhupucchagrast'
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

      if abs (Graha.singleton(Graha.MOON).get_longitude(jd_eclipse_lunar_end) - Graha.singleton(Graha.RAHU).get_longitude(
            jd_eclipse_lunar_end)) < 10:
        grasta = 'rAhumukhagrast'
      else:
        grasta = 'rAhupucchagrast'

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
    
    for graha in Graha.MERCURY, Graha.VENUS, Graha.MARS, Graha.SATURN, Graha.RAHU:
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
