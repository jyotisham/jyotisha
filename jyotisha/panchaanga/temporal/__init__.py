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


class PanchaangaApplier(JsonObject):
  """Objects of this type apply various temporal attributes to panchAnga-s."""
  def __init__(self, panchaanga):
    super().__init__()
    self.panchaanga = panchaanga
    self.daily_panchaangas = self.panchaanga.daily_panchaangas_sorted()
    self.ayanaamsha_id = panchaanga.computation_system.ayanaamsha_id

  def assign_all(self, debug=False):
    pass


class ComputationSystem(JsonObject):
  def __init__(self, lunar_month_assigner_type, ayanaamsha_id):
    self.lunar_month_assigner_type = lunar_month_assigner_type
    self.ayanaamsha_id = ayanaamsha_id



# Essential for depickling to work.
common.update_json_class_index(sys.modules[__name__])
# logging.debug(common.json_class_index)
