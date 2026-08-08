import logging

from jyotisha.panchaanga.temporal import Anga
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

  # Traditionally, it is guru (Jupiter) mAudhya (combustion) that voids Vedic adhyayana-related rites.
  MAUDHYA_GRAHA = Graha.JUPITER
  # "Eclipse before midnight" is read as: the eclipse begins before relative ghatikA 45 (ie. within the
  # first half of the following night; ghatikA 30 is sunset, 60 is next sunrise) of the candidate day.
  ECLIPSE_CUTOFF_RELATIVE_GHATIKA = 45

  def __init__(self, panchaanga):
    super().__init__(panchaanga=panchaanga)
    self._guru_maudhya_intervals_cache = None

  def assign_all(self):
    self.assign_saamopakarma()
    self.assign_rigveda_upakarma()
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

    Note: unlike `RuleLookupAssigner.apply_month_anga_events`, this does not re-confirm a paraviddha/vyaapti
    "today" pick by also looking a day further ahead (see the comment there on why that look-ahead
    matters near month boundaries). For a first-occurrence-in-masa search that edge case is rare enough
    to accept for now; revisit if it turns out to matter in practice.
    """
    target_anga = Anga.get_cached(index=anga_index, anga_type_id=anga_type.name)
    for d in range(self.panchaanga.duration_prior_padding, self.panchaanga.duration + self.panchaanga.duration_prior_padding):
      day_panchaanga = self.daily_panchaangas[d]
      if day_panchaanga.lunar_date.month.index != masa_index:
        continue
      next_panchaanga = self.daily_panchaangas[d + 1]
      decision = priority_decision.decide(p0=day_panchaanga, p1=next_panchaanga, target_anga=target_anga,
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
    """ True iff a (sidereal solar) saGkramaNa falls on `date`. """
    day_panchaanga = self.panchaanga.date_str_to_panchaanga.get(date.get_date_str(), None)
    return day_panchaanga is not None and day_panchaanga.solar_sidereal_date_sunset.month_transition is not None

  def _guru_maudhya_intervals(self):
    if self._guru_maudhya_intervals_cache is None:
      from jyotisha.panchaanga.temporal.festival.applier.ecliptic import EclipticFestivalAssigner
      ecliptic_assigner = EclipticFestivalAssigner(panchaanga=self.panchaanga)
      self._guru_maudhya_intervals_cache = ecliptic_assigner.compute_maudhya_intervals(
        self.MAUDHYA_GRAHA, self.panchaanga.jd_start - 30, self.panchaanga.jd_end + 30)
    return self._guru_maudhya_intervals_cache

  def _has_maudhya_flaw(self, date):
    """ True iff guru is in mAudhya (combust) at any point during the civil day `date`. """
    day_panchaanga = self.panchaanga.date_str_to_panchaanga.get(date.get_date_str(), None)
    if day_panchaanga is None:
      return False
    return any(t_start <= day_panchaanga.jd_sunset and t_end >= day_panchaanga.jd_sunrise
               for (t_start, t_end, _, _) in self._guru_maudhya_intervals())

  def _has_flaw(self, date):
    """ True iff `date` has an eclipse-before-relative-ghatikA-45, a saGkramaNa, or a guru-mAudhya flaw --
    any of which is traditionally grounds to switch the upAkarma day, per the veda-specific rules below.
    """
    return date is not None and (
      self._has_eclipse_flaw(date) or self._has_sankramana_flaw(date) or self._has_maudhya_flaw(date))

  def _select_first_unflawed_purnima(self, masa_order, kaala='मध्याह्नः'):
    """ Returns the Date of the first (in `masa_order`) unflawed zrAvaNI-style pUrNimA -- ie. the first
    masa in the list whose paraviddha pUrNimA at `kaala` has no eclipse/saGkrAnti/mAudhya flaw.
    """
    for masa_index in masa_order:
      date = self._first_anga_occurrence_in_masa(masa_index=masa_index, anga_type=AngaType.TITHI,
                                                   anga_index=TITHI_PURNIMA, kaala=kaala, priority='paraviddha')
      if date is not None and not self._has_flaw(date):
        return date
    return None

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
    if date is not None and self._has_flaw(date):
      switched_date = self._first_day_with_sunrise_tithi_in_masa(MASA_SHRAVANA, TITHI_SHUKLA_PANCHAMI)
      if switched_date is not None:
        date = switched_date
      else:
        logging.warning('%s: primary date %s is flawed, but no zukla-paJcamI switch date was found; keeping primary.',
                         fest_id, date.get_date_str())

    if date is not None:
      self.panchaanga.add_festival(fest_id=fest_id, date=date)

  # ---------------------------------------------------------------------
  # Krishna/Shukla Yajurveda: zrAvaNa pUrNimA at ghatikA 12 (start of madhyAhna), paraviddha. If flawed,
  # try bhAdrapada pUrNimA, then ASADha pUrNimA. If all three are flawed, fall back to zrAvaNI pUrNimA
  # itself, done zAntipUrvakam (with a preliminary expiatory rite).
  # ---------------------------------------------------------------------

  def assign_yajurveda_upakarma(self):
    fest_id = 'yajurvEda-upAkarma'
    if fest_id not in self.rules_collection.name_to_rule:
      return
    self.panchaanga.delete_festival(fest_id=fest_id)
    self.panchaanga.delete_festival(fest_id=fest_id + '~zAntipUrvakam')

    date = self._select_first_unflawed_purnima(masa_order=[MASA_SHRAVANA, MASA_BHADRAPADA, MASA_ASHADHA])
    if date is not None:
      self.panchaanga.add_festival(fest_id=fest_id, date=date)
      return

    # All 3 candidate pUrNimA-s are flawed -- return to zrAvaNI pUrNimA, performed zAntipUrvakam.
    shravana_purnima = self._first_anga_occurrence_in_masa(masa_index=MASA_SHRAVANA, anga_type=AngaType.TITHI,
                                                            anga_index=TITHI_PURNIMA, kaala='मध्याह्नः', priority='paraviddha')
    if shravana_purnima is not None:
      self.panchaanga.add_festival(fest_id=fest_id + '~zAntipUrvakam', date=shravana_purnima)

  # ---------------------------------------------------------------------
  # bOdhAyana zAkhA of the (kRSNa) Yajurveda: same base rule, but the first switch is to ASADha (not
  # bhAdrapada).
  # ---------------------------------------------------------------------

  def assign_bodhaayana_upakarma(self):
    fest_id = 'bOdhAyana-yajurvEda-upAkarma'
    if fest_id not in self.rules_collection.name_to_rule:
      return
    self.panchaanga.delete_festival(fest_id=fest_id)
    self.panchaanga.delete_festival(fest_id=fest_id + '~zAntipUrvakam')

    date = self._select_first_unflawed_purnima(masa_order=[MASA_SHRAVANA, MASA_ASHADHA, MASA_BHADRAPADA])
    if date is not None:
      self.panchaanga.add_festival(fest_id=fest_id, date=date)
      return

    shravana_purnima = self._first_anga_occurrence_in_masa(masa_index=MASA_SHRAVANA, anga_type=AngaType.TITHI,
                                                            anga_index=TITHI_PURNIMA, kaala='मध्याह्नः', priority='paraviddha')
    if shravana_purnima is not None:
      self.panchaanga.add_festival(fest_id=fest_id + '~zAntipUrvakam', date=shravana_purnima)

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
    if date is not None and self._has_flaw(date):
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
