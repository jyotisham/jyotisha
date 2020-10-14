import logging
import sys

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


class DailyPanchaangaApplier(JsonObject):
  """Objects of this type apply various temporal attributes to panchAnga-s."""
  def __init__(self, day_panchaanga, previous_day_panchaanga):
    super().__init__()
    self.day_panchaanga = day_panchaanga
    self.computation_system = day_panchaanga.computation_system
    self.previous_day_panchaanga = previous_day_panchaanga
    self.ayanaamsha_id = day_panchaanga.computation_system.ayanaamsha_id


class ComputationOptions(JsonObject):
  def __init__(self, set_lagnas=None, no_fests=None, fest_repos=None, fest_ids_included=None, fest_ids_excluded=None,
               fest_tags_included=None, fest_tags_excluded=None):
    super().__init__()
    self.set_lagnas = set_lagnas
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
