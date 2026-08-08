import logging

from jyotisha.panchaanga.temporal import Anga, get_2_day_interval_boundary_angas
from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival import priority_decision
from jyotisha.panchaanga.temporal.festival.applier import FestivalAssigner
from jyotisha.panchaanga.temporal.zodiac import AngaType
from sanskrit_data.schema import common
import sys

# Lunar masa (month) indices, counting from caitra = 1.
MASA_ASHADHA = 4
MASA_SHRAVANA = 5
MASA_BHADRAPADA = 6
MASA_NAMES = {MASA_ASHADHA: 'ASADha', MASA_SHRAVANA: 'zrAvaNa', MASA_BHADRAPADA: 'bhAdrapada'}

NAKSHATRA_HASTA = 13
NAKSHATRA_SHRAVANA = 22
TITHI_SHUKLA_PANCHAMI = 5
TITHI_PURNIMA = 15


class UpakarmaFestivalAssigner(FestivalAssigner):
  """ Assigns upAkarma (the start-of-term Vedic study rite) for each veda directly in Python, rather than
  relying on the generic TOML-rule engine (`RuleLookupAssigner`).

  The generic engine matches each (yesterday, today) day-pair against a fixed anga/kaala/priority rule
  and, when the same anga recurs a second time within the target month (eg. an anga of period ~27 days
  recurring within a ~29.5 day lunar month), its de-duplication logic in
  `RuleLookupAssigner.apply_month_anga_events` keeps the *later* occurrence -- the opposite of the
  traditional "first occurrence in the month" rule these upAkarma-s follow. The engine also has no way to
  express the eclipse/saGkrAnti/mAudhya-driven fallback chains described in each `assign_*` method below,
  since those require looking beyond a single candidate day. Hence these are hand-coded here instead.
  """

  # Each veda's upAkarma is voided by mAudhya (combustion) of its own governing graha, not a common one:
  # Rgveda <-> guru, (kRSNa/zukla/bOdhAyana) Yajurveda <-> zukra, sAmaveda <-> aGgAraka.
  MAUDHYA_GRAHA_BY_VEDA = {
    'RgvEda-upAkarma': Graha.JUPITER,
    'yajurvEda-upAkarma': Graha.VENUS,
    'zukla-yajurvEda-upAkarma': Graha.VENUS,
    'bOdhAyana-yajurvEda-upAkarma': Graha.VENUS,
    'sAmavEda-upAkarma': Graha.MARS,
  }
  # "Eclipse before midnight" is read as: the eclipse begins before relative ghatikA 45 (ie. within the
  # first half of the following night; ghatikA 30 is sunset, 60 is next sunrise) of the candidate day.
  ECLIPSE_CUTOFF_RELATIVE_GHATIKA = 45

  def __init__(self, panchaanga):
    super().__init__(panchaanga=panchaanga)
    self._maudhya_intervals_cache = {}

  def assign_all(self):
    self.assign_saamopakarma()
    self.assign_rigveda_upakarma()
    self.assign_shukla_yajurveda_upakarma()
    self.assign_yajurveda_upakarma()
    self.assign_bodhaayana_upakarma()

  # ---------------------------------------------------------------------
  # Shared helpers
  # ---------------------------------------------------------------------

  def _first_anga_occurrence_in_masa(self, masa_index, anga_type, anga_index, kaala, priority='paraviddha'):
    """ Returns the Date of the *first* occurrence, within lunar masa `masa_index`, of anga `anga_index`
    (of `anga_type`) prevailing at `kaala` -- decided via the same puurvaviddha/paraviddha/vyaapti
    machinery (`festival.priority_decision`) the generic engine uses, but stopping at the first match
    within the masa instead of accumulating/overwriting with later ones.
    """
    target_anga = Anga.get_cached(index=anga_index, anga_type_id=anga_type.name)
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      if day_panchaanga.lunar_date.month.index != masa_index:
        continue
      next_panchaanga = self.daily_panchaangas[d + 1]
      decision = priority_decision.decide(p0=day_panchaanga, p1=next_panchaanga, target_anga=target_anga,
                                           kaala=kaala, priority=priority, ayanaamsha_id=self.ayanaamsha_id)
      if decision is not None and priority in ('vyaapti', 'paraviddha') and decision.fday == 1:
        # decide() picked "tomorrow" (next_panchaanga) over "today" (day_panchaanga) based on just this
        # pair. Since an anga can never touch 3 consecutive days' kaalas, a look at the day after that
        # settles whether tomorrow's win is final: if the anga doesn't touch that day's kaala at all,
        # tomorrow's win stands; if it does, tomorrow's boundary match may just be the day-after's leading
        # edge bleeding backwards (or a genuine straddle continuing further) -- settle it directly by
        # calling decide() on the (tomorrow, day-after) pair. Mirrors the same look-ahead in
        # `RuleLookupAssigner.apply_month_anga_events` (see the comment there); omitting it is what caused
        # zrAvaNa-pUrNimA 2027 to be mis-resolved as 08-16 instead of the correct 08-17.
        day_after_next = self.daily_panchaangas[d + 2]
        (_, day_after_next_angas) = get_2_day_interval_boundary_angas(kaala=kaala, anga_type=anga_type, p0=next_panchaanga, p1=day_after_next)
        if day_after_next_angas.start == target_anga or day_after_next_angas.end == target_anga:
          decision = priority_decision.decide(p0=next_panchaanga, p1=day_after_next, target_anga=target_anga,
                                               kaala=kaala, priority=priority, ayanaamsha_id=self.ayanaamsha_id)
      if decision is not None and decision.fday is not None and decision.fday != -1:
        return decision.day_panchaanga.date
    return None

  def _first_day_with_sunrise_tithi_in_masa(self, masa_index, tithi_index):
    """ Returns the Date of the first day within lunar masa `masa_index` whose sunrise-tithi is
    `tithi_index` (eg. zukla-paJcamI). Used for switch/fallback days where a paraviddha-style kaala touch
    isn't specified.
    """
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      if day_panchaanga.lunar_date.month.index == masa_index and day_panchaanga.sunrise_day_angas.tithi_at_sunrise.index == tithi_index:
        return day_panchaanga.date
    return None

  def _has_eclipse_flaw(self, date):
    """ True iff a solar/lunar eclipse assigned to `date` (by `EclipticFestivalAssigner`, which must have
    already run) begins before relative ghatikA `ECLIPSE_CUTOFF_RELATIVE_GHATIKA` of that day.
    """
    day_panchaanga = self.panchaanga.date_str_to_panchaanga.get(date.get_date_str(), None)
    if day_panchaanga is None:
      return False
    cutoff_jd = day_panchaanga.day_length_based_periods.fifteen_fold_division.get_relative_ghatika_interval(
      0, self.ECLIPSE_CUTOFF_RELATIVE_GHATIKA).jd_end
    for fest in day_panchaanga.festival_id_to_instance.values():
      if 'grahaNam' in fest.name and fest.interval is not None and fest.interval.jd_start is not None \
          and fest.interval.jd_start < cutoff_jd:
        return True
    return False

  def _has_sankramana_flaw(self, date):
    """ True iff a (sidereal solar) saGkramaNa falls on `date` itself. """
    day_panchaanga = self.panchaanga.date_str_to_panchaanga.get(date.get_date_str(), None)
    return day_panchaanga is not None and day_panchaanga.solar_sidereal_date_sunset.month_transition is not None

  def _maudhya_intervals(self, graha):
    if graha not in self._maudhya_intervals_cache:
      from jyotisha.panchaanga.temporal.festival.applier.ecliptic import EclipticFestivalAssigner
      ecliptic_assigner = EclipticFestivalAssigner(panchaanga=self.panchaanga)
      self._maudhya_intervals_cache[graha] = ecliptic_assigner.compute_maudhya_intervals(
        graha, self.panchaanga.jd_start - 30, self.panchaanga.jd_end + 30)
    return self._maudhya_intervals_cache[graha]

  def _has_maudhya_flaw(self, date, graha):
    """ True iff `graha` is in mAudhya (combust) at any point during the civil day `date`. """
    day_panchaanga = self.panchaanga.date_str_to_panchaanga.get(date.get_date_str(), None)
    if day_panchaanga is None:
      return False
    flawed = any(t_start <= day_panchaanga.jd_sunset and t_end >= day_panchaanga.jd_sunrise
                 for (t_start, t_end, _, _) in self._maudhya_intervals(graha))
    if flawed:
      logging.info('%s mAudhya (combustion) flaw on %s.', graha, date.get_date_str())
    return flawed

  def _has_hard_flaw(self, date):
    """ True iff `date` has an eclipse-before-relative-ghatikA-45 or a saGkramaNa. Unlike mAudhya, neither
    admits a zAntipUrvakam-style remedy, so a hard flaw rules out even the "return to zrAvaNa-pUrNimA,
    performed zAntipUrvakam" fallback in `_assign_purnima_switch_upakarma`.
    """
    return date is not None and (self._has_eclipse_flaw(date) or self._has_sankramana_flaw(date))

  def _has_flaw(self, date, fest_id):
    """ True iff `date` has a hard flaw (see `_has_hard_flaw`) or a mAudhya flaw of `fest_id`'s governing
    graha -- any of which is traditionally grounds to switch the upAkarma day, per the veda-specific rules
    below.
    """
    graha = self.MAUDHYA_GRAHA_BY_VEDA[fest_id]
    return date is not None and (self._has_hard_flaw(date) or self._has_maudhya_flaw(date, graha))

  def _shravana_purnima(self):
    return self._first_anga_occurrence_in_masa(masa_index=MASA_SHRAVANA, anga_type=AngaType.TITHI,
                                                anga_index=TITHI_PURNIMA, kaala='मध्याह्नः', priority='paraviddha')

  def _switch_to_shukla_panchami_or_keep(self, fest_id, date):
    """ If `date` has a flaw, switch (unconditionally, without re-checking the switch date itself) to
    zukla-paJcamI of zrAvaNa; if even that can't be found, log and keep `date` as-is.
    """
    if date is not None and self._has_flaw(date, fest_id):
      switched_date = self._first_day_with_sunrise_tithi_in_masa(MASA_SHRAVANA, TITHI_SHUKLA_PANCHAMI)
      if switched_date is not None:
        return switched_date
      logging.warning('%s: primary date %s is flawed, but no zukla-paJcamI switch date was found; keeping primary.',
                       fest_id, date.get_date_str())
    return date

  # ---------------------------------------------------------------------
  # Rigveda: shrAvaNa-mAsa shrAvaNa-nakSatra (first occurrence). If flawed, switch to zukla-paJcamI of
  # zrAvaNa.
  # ---------------------------------------------------------------------

  def assign_rigveda_upakarma(self):
    fest_id = 'RgvEda-upAkarma'
    if fest_id not in self.rules_collection.name_to_rule:
      return
    self.panchaanga.delete_festival(fest_id=fest_id)

    date = self._first_anga_occurrence_in_masa(masa_index=MASA_SHRAVANA, anga_type=AngaType.NAKSHATRA,
                                                anga_index=NAKSHATRA_SHRAVANA, kaala='मैत्रः', priority='paraviddha')
    date = self._switch_to_shukla_panchami_or_keep(fest_id, date)
    if date is not None:
      self.panchaanga.add_festival(fest_id=fest_id, date=date)

  # ---------------------------------------------------------------------
  # zukla Yajurveda: zrAvaNa-pUrNimA at ghatikA 12 (start of madhyAhna), paraviddha -- same primary as
  # (kRSNa) Yajurveda below, but (like Rgveda) the switch is to zukla-paJcamI of zrAvaNa itself, not a
  # pUrNimA of a different masa.
  # ---------------------------------------------------------------------

  def assign_shukla_yajurveda_upakarma(self):
    fest_id = 'zukla-yajurvEda-upAkarma'
    if fest_id not in self.rules_collection.name_to_rule:
      return
    self.panchaanga.delete_festival(fest_id=fest_id)

    date = self._switch_to_shukla_panchami_or_keep(fest_id, self._shravana_purnima())
    if date is not None:
      self.panchaanga.add_festival(fest_id=fest_id, date=date)

  # ---------------------------------------------------------------------
  # (kRSNa) Yajurveda: shared implementation for the general/non-bOdhAyana zAkhA-s and for bOdhAyana.
  # `masa_chain` is [zrAvaNa, switch_1, switch_2] in priority order (the two zAkhA-groups differ only in
  # whether ASADha or bhAdrapada comes first). Each candidate pUrNimA is checked in turn -- for eclipse,
  # saGkrAnti, and mAudhya of the veda's governing graha -- and the first unflawed one is used.
  #
  # If all three are flawed: mAudhya alone is traditionally remediable (zAntipUrvakam, a preliminary
  # expiatory rite), so if zrAvaNa-pUrNimA's own flaw is *only* mAudhya (no eclipse/saGkrAnti), it is used
  # anyway, performed zAntipUrvakam -- and `fest_id` itself is assigned at that date too (not just the
  # zAntipUrvakam variant), so festivals computed relative to `fest_id` (eg. varalakSmI-vratam, via
  # `RuleLookupAssigner.assign_varalakshmi_vratam`) resolve the same way regardless. But eclipse/saGkrAnti
  # admit no such remedy: if zrAvaNa-pUrNimA itself has one of *those*, the zAntipUrvakam fallback isn't
  # available either, so the first switch candidate is used instead, accepted despite its own (mAudhya)
  # flaw, since it's the least-flawed option left.
  # ---------------------------------------------------------------------

  def _assign_purnima_switch_upakarma(self, fest_id, masa_chain):
    if fest_id not in self.rules_collection.name_to_rule:
      return
    self.panchaanga.delete_festival(fest_id=fest_id)
    self.panchaanga.delete_festival(fest_id=fest_id + '~zAntipUrvakam')

    dates = [self._first_anga_occurrence_in_masa(masa_index=masa_index, anga_type=AngaType.TITHI,
                                                  anga_index=TITHI_PURNIMA, kaala='मध्याह्नः', priority='paraviddha')
             for masa_index in masa_chain]

    for date in dates:
      if date is not None and not self._has_flaw(date, fest_id):
        self.panchaanga.add_festival(fest_id=fest_id, date=date)
        return

    chain_desc = '/'.join(MASA_NAMES[masa_index] for masa_index in masa_chain)
    shravana_purnima = dates[0]
    if shravana_purnima is not None and not self._has_hard_flaw(shravana_purnima):
      logging.info('%s: %s-pUrNimA are all flawed; zrAvaNa-pUrNimA (%s) has only a mAudhya flaw, so '
                    'falling back to it, performed zAntipUrvakam.', fest_id, chain_desc, shravana_purnima.get_date_str())
      self.panchaanga.add_festival(fest_id=fest_id, date=shravana_purnima)
      self.panchaanga.add_festival(fest_id=fest_id + '~zAntipUrvakam', date=shravana_purnima)
      return

    for date in dates[1:]:
      if date is not None:
        logging.info('%s: %s-pUrNimA are all flawed, and zrAvaNa-pUrNimA (%s) itself has an eclipse/'
                      'saGkrAnti flaw (no zAntipUrvakam remedy for that) -- falling through to %s.',
                      fest_id, chain_desc, shravana_purnima.get_date_str() if shravana_purnima else None, date.get_date_str())
        self.panchaanga.add_festival(fest_id=fest_id, date=date)
        return

    logging.error('%s: could not resolve a date -- all of %s were either not found or flawed, with no '
                   'fallback available.', fest_id, chain_desc)

  def assign_yajurveda_upakarma(self):
    """ General/non-bOdhAyana (kRSNa) Yajurveda zAkhA-s (eg. Apastamba, taittirIya): chain is
    zrAvaNa -> bhAdrapada -> ASADha. """
    self._assign_purnima_switch_upakarma(fest_id='yajurvEda-upAkarma', masa_chain=[MASA_SHRAVANA, MASA_BHADRAPADA, MASA_ASHADHA])

  def assign_bodhaayana_upakarma(self):
    """ bOdhAyana zAkhA of the (kRSNa) Yajurveda: chain is zrAvaNa -> ASADha -> bhAdrapada (reversed order
    vs. the general rule above). """
    self._assign_purnima_switch_upakarma(fest_id='bOdhAyana-yajurvEda-upAkarma', masa_chain=[MASA_SHRAVANA, MASA_ASHADHA, MASA_BHADRAPADA])

  # ---------------------------------------------------------------------
  # Samaveda: first hasta-nakSatra in bhAdrapada. Switch rule not yet settled -- see TODO below.
  # ---------------------------------------------------------------------

  def assign_saamopakarma(self):
    fest_id = 'sAmavEda-upAkarma'
    if fest_id not in self.rules_collection.name_to_rule:
      return
    self.panchaanga.delete_festival(fest_id=fest_id)

    date = self._first_anga_occurrence_in_masa(masa_index=MASA_BHADRAPADA, anga_type=AngaType.NAKSHATRA,
                                                anga_index=NAKSHATRA_HASTA, kaala='मध्याह्नः', priority='paraviddha')
    if date is not None and self._has_flaw(date, fest_id):
      date = self._saamopakarma_switch(date)

    if date is not None:
      self.panchaanga.add_festival(fest_id=fest_id, date=date)

  def _saamopakarma_switch(self, primary_date):
    """ TODO(sAmavEda-upAkarma switch rule): unlike Rigveda/Yajurveda, the day to switch to when
    `primary_date` (first hasta in bhAdrapada) has an eclipse/saGkrAnti/mAudhya flaw is not yet settled.
    Until it is, we keep the primary date even when flawed, rather than silently guess at a fallback.
    Revisit once the switch rule for sAmavEda is confirmed.
    """
    logging.warning('sAmavEda-upAkarma on %s has an eclipse/saGkrAnti/mAudhya flaw, but no switch rule is '
                     'defined yet for sAmavEda -- keeping the primary date.', primary_date.get_date_str())
    return primary_date


# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
