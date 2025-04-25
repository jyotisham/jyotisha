import logging
import os
import sys

import methodtools
import regex
from sanskrit_data.schema import common
from sanskrit_data.schema.common import JsonObject

from jyotisha.panchaanga.temporal.body import Graha
from jyotisha.panchaanga.temporal.festival.rules import RulesCollection, RulesRepo
from jyotisha.panchaanga.temporal.zodiac.angas import BoundaryAngas, Anga, AngaType

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
  def __init__(self, set_lagnas=None, no_fests=None, fest_repos=None, fest_ids_included_unimplemented=None, fest_id_patterns_excluded=None, fest_repos_excluded_patterns=[], aparaahna_as_second_half=False, prefer_eight_fold_day_division=False, set_pancha_paxi_activities=None, julian_handling=RulesCollection.JULIAN_TO_GREGORIAN, tropical_month_start="mAdhava_at_equinox"):
    """
    
    :param set_lagnas: 
    :param no_fests: 
    :param fest_repos: 
    :param fest_ids_included_unimplemented: TODO: rename when actually implemented 
    :param fest_repos_excluded_patterns
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
    self.tropical_month_start = tropical_month_start
    self.fest_repos_excluded_patterns = fest_repos_excluded_patterns
    self.repos = fest_repos
    self.init_repos()

    if self.tropical_month_start == "mAdhava_at_equinox":
      self.repos = [repo for repo in self.repos if "viSuvAdi" not in repo.name]
    else:
      self.repos = [repo for repo in self.repos if "ayanAdi" not in repo.name]

    self.fest_id_patterns_excluded = fest_id_patterns_excluded
    self.fest_ids_included_unimplemented = fest_ids_included_unimplemented

    self.prefer_eight_fold_day_division = prefer_eight_fold_day_division
    self.julian_handling = julian_handling

  @methodtools.lru_cache()
  def get_fest_id_pattern_excluded(self):
    if self.fest_id_patterns_excluded is not None:
      return regex.compile("|".join(self.fest_id_patterns_excluded))
    else:
      return regex.compile("")


  def init_repos(self):
    if not hasattr(self, "repos") or self.repos is None:
      from jyotisha.panchaanga.temporal.festival import rules
      self.repos = rules.rule_repos
    if hasattr(self, "fest_repos_excluded_patterns") and self.fest_repos_excluded_patterns is not None:
      repos = []
      for repo in self.repos:
        include = True
        for x in self.fest_repos_excluded_patterns:
          if regex.fullmatch(x, repo.name):
            include = False
            logging.warning(f'Excluding {repo.name} based on pattern {x}')
            break
        if include:
          repos.append(repo)
      self.repos = repos

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
    super().__init__()
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
  MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180 = None
  MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_PURNIMANTA__CHITRA_180 = None
  MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180 = None
  MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__RP = None
  SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180 = None
  SOLSTICE_POST_DARK_10_ADHIKA__RP = None
  MIN_SOLARCOMPUTATION__CHITRA_180 = None
  DEFAULT = None

  def __init__(self, lunar_month_assigner_type, ayanaamsha_id, short_id=None, festival_options=FestivalOptions()):
    super().__init__()
    self.lunar_month_assigner_type = lunar_month_assigner_type
    self.ayanaamsha_id = ayanaamsha_id
    self.festival_options = festival_options
    self.graha_lopa_measures = GrahaLopaMeasures()
    self.post_load_ops()
    self.short_id = short_id

  def get_short_id_str(self):
    calendar_id = ""
    if self.short_id is not None:
      calendar_id = f"({self.short_id})"
    return calendar_id

  def post_load_ops(self):
    if hasattr(self, "festival_options") and self.festival_options is not None:
      if not hasattr(self.festival_options, "repos") or self.festival_options.repos is None:
        self.festival_options.init_repos()

  def __repr__(self):
    return "%s__%s" % (self.lunar_month_assigner_type, self.ayanaamsha_id)

  def to_md(self):
    system_copy = ComputationSystem(lunar_month_assigner_type=self.lunar_month_assigner_type, ayanaamsha_id=self.ayanaamsha_id, festival_options=None)
    return "#### Basic parameters\n```\n%s\n```\n\n%s" % (system_copy.to_string(format="toml"), self.festival_options.to_md())
     
  def dump_without_repos(self, file_path):
    """Often, one sets repos without listing them - starting off with defaults and then excluding repsositories."""
    if not file_path.startswith("/"):
      from jyotisha.panchaanga.temporal import festival
      file_path = os.path.join(os.path.dirname(festival.__file__, "data/computation_systems", file_path))
    repos = self.festival_options.repos
    self.festival_options.repos = None
    self.dump_to_file(filename=file_path)
    self.festival_options.repos = repos

def set_constants():
  from jyotisha.panchaanga.temporal.month import LunarMonthAssigner
  from jyotisha.panchaanga.temporal.zodiac import Ayanamsha
  ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180, short_id="चि॰")

  # TODO: Exclude tithi festivals only; or alter code to offset festival months to this system.
  ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_PURNIMANTA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_PURNIMANTA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180, short_id="चि॰", festival_options=FestivalOptions(no_fests=True))
  
  # TODO: Exclude tithi festivals only; or alter code to offset festival months to this system.
  ComputationSystem.MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_FULL_MOON_SIDEREAL_MONTH_ADHIKA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180, festival_options=FestivalOptions(no_fests=True))
  ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__RP = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA, ayanaamsha_id=Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING)

  ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__CHITRA_180 = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA, ayanaamsha_id=Ayanamsha.CHITRA_AT_180, short_id="उकौ॰")
  ComputationSystem.SOLSTICE_POST_DARK_10_ADHIKA__RP = ComputationSystem(lunar_month_assigner_type=LunarMonthAssigner.SOLSTICE_POST_DARK_10_ADHIKA, ayanaamsha_id=Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING)
  ComputationSystem.MIN_SOLARCOMPUTATION__RP = ComputationSystem(lunar_month_assigner_type=None, ayanaamsha_id=Ayanamsha.RASHTRIYA_PANCHANGA_NAKSHATRA_TRACKING)

  ComputationSystem.DEFAULT = ComputationSystem.MULTI_NEW_MOON_SIDEREAL_MONTH_ADHIKA_AMAANTA__CHITRA_180


  
set_constants()

# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
