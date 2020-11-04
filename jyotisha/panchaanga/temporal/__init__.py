import logging
import sys

from jyotisha.panchaanga.temporal.zodiac.angas import BoundaryAngas, Anga, AngaType

from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

logging.basicConfig(
  level=logging.DEBUG,
  format="%(levelname)s: %(asctime)s {%(filename)s:%(lineno)d}: %(message)s "
)

MAX_DAYS_PER_YEAR = 366
MAX_SZ = MAX_DAYS_PER_YEAR + 6  # plus one and minus one are usually necessary


class PeriodicPanchaangaApplier(JsonObject):
  """Objects of this type apply various temporal attributes to panchAnga-s."""
  def __init__(self, panchaanga):
    super().__init__()
    self.panchaanga = panchaanga
    self.computation_system = panchaanga.computation_system
    self.daily_panchaangas = self.panchaanga.daily_panchaangas_sorted()
    self.ayanaamsha_id = panchaanga.computation_system.ayanaamsha_id

  def assign_all(self):
    pass


def get_2_day_interval_boundary_angas(kaala, anga_type, p0, p1):
  """
  
  Useful only for tithi, nakShatra or yoga. NOT karaNa (since >2 karaNas may exist within an interval).
  :param kaala: 
  :param anga_type: 
  :return: 
  """
  from jyotisha.panchaanga.temporal.interval import Interval
  (spans0, interval0) = p0.get_interval_anga_spans(name=kaala, anga_type=anga_type)
  (spans1, interval1) = p1.get_interval_anga_spans(name=kaala, anga_type=anga_type)
  if len(spans0) == 1:
    spans0 = spans0 + spans0
  if len(spans1) == 1:
    spans1 = spans1 + spans1
  angas = (BoundaryAngas(start=spans0[0].anga, end=spans0[1].anga, interval=interval0), BoundaryAngas(start=spans1[0].anga, end=spans1[1].anga, interval=interval1))
  return angas


class DailyPanchaangaApplier(JsonObject):
  """Objects of this type apply various temporal attributes to panchAnga-s."""
  def __init__(self, day_panchaanga, previous_day_panchaangas, festival_id_to_days=None):
    super().__init__()
    self.day_panchaanga = day_panchaanga
    self.computation_system = day_panchaanga.computation_system
    self.previous_day_panchaangas = previous_day_panchaangas
    # A running record of festival-day assignments so far - to avoid repeat assignments
    self.festival_id_to_days = festival_id_to_days
    self.ayanaamsha_id = day_panchaanga.computation_system.ayanaamsha_id

  def apply_month_day_events(self, month_type):
    from jyotisha.panchaanga.temporal.festival import rules, priority_decision, FestivalInstance
    rule_set = rules.RulesCollection.get_cached(repos_tuple=tuple(self.computation_system.options.fest_repos))
    day_panchaanga = self.day_panchaanga

    date = day_panchaanga.get_date(month_type=month_type)
    fest_dict = rule_set.get_month_anga_fests(month=date.month, anga=date.day, month_type=month_type, anga_type_id=rules.RulesRepo.DAY_DIR)
    for fest_id, fest in fest_dict.items():
      day_panchaanga.festival_id_to_instance[fest_id] = FestivalInstance(name=fest.id)

  def apply_month_anga_events(self, anga_type, month_type):
    from jyotisha.panchaanga.temporal.festival import rules, priority_decision, FestivalInstance
    rule_set = rules.RulesCollection.get_cached(repos_tuple=tuple(self.computation_system.options.fest_repos))
    panchaangas = self.previous_day_panchaangas + [self.day_panchaanga]
    if panchaangas[1] is None:
      # We require atleast 1 day history.
      return

    anga_type_id = anga_type.name.lower()
    angas_2 = [x.anga for x in panchaangas[2].sunrise_day_angas.get_angas_with_ends(anga_type=anga_type)]
    if anga_type == AngaType.TITHI and angas_2[0].index in (29, 30):
      # We seek festivals based on angas belonging to this month only.
      angas_2 = [anga for anga in angas_2 if anga.index <= 30]

    angas_1 = [x.anga for x in panchaangas[1].sunrise_day_angas.get_angas_with_ends(anga_type=anga_type)]
    if anga_type == AngaType.TITHI and angas_2[0].index in (1, 2):
      angas_1 = [anga for anga in angas_1 if anga.index >= 1]
    angas = set(angas_2 + angas_1)
    # The filtering above avoids the below case (TODO: Check):
    # When applied to month_type = lunar_sideral and anga_type = tithi, this method fails in certain corner cases. Consider the case: target_anga = tithi 1. It appears in the junction with the preceeding month or with the succeeding month. In that case, clearly, the former is salient - tithi 1 in the latter case belongs to the succeeding month. 

    month = self.day_panchaanga.get_date(month_type=month_type).month
    fest_dict = rule_set.get_possibly_relevant_fests(month=month, angas=angas, month_type=month_type, anga_type_id=anga_type_id)
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
        if p_fday.get_date(month_type=month_type).month != month:
          # Example: Suppose festival on tithi 27 of solar siderial month 10; last day of month 9 could have tithi 27, but not day 1 of month 10. 
          continue
        if priority not in ('puurvaviddha', 'vyaapti'):
          p_fday.festival_id_to_instance[fest_id] = FestivalInstance(name=fest_id)
          self.festival_id_to_days[fest_id].add(p_fday.date)
        elif p_fday_minus_1 is None or p_fday_minus_1.date not in self.festival_id_to_days[fest_id]:
          # puurvaviddha or vyaapti fest. More careful condition.
          # p_fday_minus_1 could be None when computing at the beginning of a sequence of days. In that case, we're ok with faulty assignments - since the focus is on getting subsequent days right.
          p_fday.festival_id_to_instance[fest_id] = FestivalInstance(name=fest_id)
          self.festival_id_to_days[fest_id].add(p_fday.date)


class ComputationOptions(JsonObject):
  def __init__(self, set_lagnas=None, no_fests=None, fest_repos=None, fest_ids_included=None, fest_ids_excluded=None,
               fest_tags_included=None, fest_tags_excluded=None, aparaahna_as_second_half=None):
    super().__init__()
    self.set_lagnas = set_lagnas
    self.aparaahna_as_second_half = aparaahna_as_second_half
    self.no_fests = no_fests
    from jyotisha.panchaanga.temporal.festival import rules
    self.fest_repos = fest_repos if fest_repos is not None else rules.rule_repos
    self.fest_ids_excluded = fest_ids_excluded
    self.fest_ids_included = fest_ids_included
    self.fest_tags_excluded = fest_tags_excluded
    self.fest_tags_included = fest_tags_included


class ComputationSystem(JsonObject):
  MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180 = None
  MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__RP = None
  SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180 = None
  SOLSTICE_POST_DARK_10_ADHIKA__RP = None
  MIN_SOLARCOMPUTATION__CHITRA_180 = None
  DEFAULT = None

  def __init__(self, lunar_month_assigner_type, ayanaamsha_id, computation_options=ComputationOptions()):
    super().__init__()
    self.lunar_month_assigner_type = lunar_month_assigner_type
    self.ayanaamsha_id = ayanaamsha_id
    self.options = computation_options

  def __repr__(self):
    return "%s__%s" % (self.lunar_month_assigner_type, self.ayanaamsha_id)


def set_constants():
  from jyotisha.panchaanga.temporal.month import LunarMonthAssigner
  from jyotisha.panchaanga.temporal.zodiac import Ayanamsha
  ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__RP = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA, ayanaamsha_id=Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING)

  ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__RP = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA, ayanaamsha_id=Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING)
  ComputationSystem.MIN_SOLARCOMPUTATION__RP = ComputationSystem(lunar_month_assigner_type=None, ayanaamsha_id=Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING)
  
  ComputationSystem.DEFAULT = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180
  
set_constants()

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
