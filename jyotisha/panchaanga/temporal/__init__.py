import logging
import sys
from copy import deepcopy, copy

from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival.rules import RulesCollection, RulesRepo
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
  (spans0, interval0) = p0.get_interval_anga_spans(interval_id=kaala, anga_type=anga_type)
  (spans1, interval1) = p1.get_interval_anga_spans(interval_id=kaala, anga_type=anga_type)
  if len(spans0) == 1:
    spans0 = spans0 + spans0
  if len(spans1) == 1:
    spans1 = spans1 + spans1
  angas = (BoundaryAngas(start=spans0[0].anga, end=spans0[1].anga, interval=interval0), BoundaryAngas(start=spans1[0].anga, end=spans1[1].anga, interval=interval1))
  return angas


class FestivalOptions(JsonObject):
  def __init__(self, set_lagnas=None, no_fests=None, fest_repos=None, fest_ids_included_unimplemented=None, fest_ids_excluded_unimplemented=None, aparaahna_as_second_half=False, prefer_eight_fold_day_division=False, set_pancha_paxi_activities=None, julian_handling=RulesCollection.JULIAN_TO_GREGORIAN):
    """
    
    :param set_lagnas: 
    :param no_fests: 
    :param fest_repos: 
    :param fest_ids_included_unimplemented: TODO: rename when actually implemented 
    :param fest_ids_excluded_unimplemented:  TODO: rename when actually implemented 
    :param aparaahna_as_second_half: 
    :param prefer_eight_fold_day_division: 
    :param set_pancha_paxi_activities: 
    :param julian_handling: 
    """
    super().__init__()
    self.set_lagnas = set_lagnas
    self.set_pancha_paxi_activities = set_pancha_paxi_activities
    self.aparaahna_as_second_half = aparaahna_as_second_half
    self.no_fests = no_fests
    from jyotisha.panchaanga.temporal.festival import rules
    self.repos = fest_repos if fest_repos is not None else rules.rule_repos
    self.fest_ids_excluded_unimplemented = fest_ids_excluded_unimplemented
    self.fest_ids_included_unimplemented = fest_ids_included_unimplemented
    self.prefer_eight_fold_day_division = prefer_eight_fold_day_division
    self.julian_handling = julian_handling

  def get_repo_mds(self):
    return ["[%s](%s)" % (repo.name, repo.base_url) for repo in self.repos]

  def to_md(self):
    fest_repos_md = ", ".join(self.get_repo_mds())
    fest_repos = self.repos
    self.repos = None
    md = "#### Event options\n ```\n%s\n```\n- Repos: %s\n" % (self.to_string(format="toml"), fest_repos_md)
    self.repos = fest_repos
    return md


class GrahaLopaMeasures(JsonObject):
  def __init__(self):
    self.graha_id_to_lopa_measure = {
      # For Jupiter Lope Surya Siddhanta suggests angular separation of 11° on both sides of the Sun.
      Graha.JUPITER: 11,
      # Surya Siddhanta suggests angular separation of 10° on both sides of the Sun when Venus is in the forward motion and 8° when Venus is in the retrograde motion.
      Graha.VENUS: 9,
      #  Surya Siddhanta suggests angular separation of 14° on both sides of the Sun when Mercury is in the forward motion and 12° when Mercury is in the retrograde motion.
      Graha.MERCURY: 13,
      # Surya Siddhanta suggests angular separation of 17° on both sides of the Sun.
      Graha.MARS: 17,
      # Surya Siddhanta suggests angular separation of 15° on both sides of the Sun.
      Graha.SATURN: 15,
    }


class ComputationSystem(JsonObject):
  MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180 = None
  MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180 = None
  MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__RP = None
  SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180 = None
  SOLSTICE_POST_DARK_10_ADHIKA__RP = None
  MIN_SOLARCOMPUTATION__CHITRA_180 = None
  DEFAULT = None
  TEST = None

  def __init__(self, lunar_month_assigner_type, ayanaamsha_id, festival_options=FestivalOptions()):
    super().__init__()
    self.lunar_month_assigner_type = lunar_month_assigner_type
    self.ayanaamsha_id = ayanaamsha_id
    self.festival_options = festival_options
    self.graha_lopa_measures = GrahaLopaMeasures()

  def __repr__(self):
    return "%s__%s" % (self.lunar_month_assigner_type, self.ayanaamsha_id)

  def to_md(self):
    system_copy = ComputationSystem(lunar_month_assigner_type=self.lunar_month_assigner_type, ayanaamsha_id=self.ayanaamsha_id, festival_options=None)
    return "#### Basic parameters\n```\n%s\n```\n\n%s" % (system_copy.to_string(format="toml"), self.festival_options.to_md())
     


def get_kauNdinyAyana_bhAskara_gRhya_computation_system():
  computation_system = deepcopy(ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180)
  computation_system.festival_options.repos = [RulesRepo(name="gRhya/general"), RulesRepo(name="gRhya/Apastamba")]
  computation_system.festival_options.aparaahna_as_second_half = True
  computation_system.festival_options.prefer_eight_fold_day_division = True
  return computation_system


def set_constants():
  from jyotisha.panchaanga.temporal.month import LunarMonthAssigner
  from jyotisha.panchaanga.temporal.zodiac import Ayanamsha
  ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  ComputationSystem.MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__RP = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA, ayanaamsha_id=Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING)

  ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180)
  ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__RP = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA, ayanaamsha_id=Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING)
  ComputationSystem.MIN_SOLARCOMPUTATION__RP = ComputationSystem(lunar_month_assigner_type=None, ayanaamsha_id=Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING)

  ComputationSystem.DEFAULT = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180

  festival_options = FestivalOptions()
  festival_options.repos = [r for r in festival_options.repos if r.name not in ["mahApuruSha/xatra-later", "mahApuruSha/sci-tech", "mahApuruSha/general-indic-non-tropical"]]
  ComputationSystem.TEST = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180, festival_options=festival_options)

  
set_constants()

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
